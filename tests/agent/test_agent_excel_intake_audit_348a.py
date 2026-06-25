"""Focused tests for the 348A Excel intake audit pilot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from datefac_agent.audit.evidence_checker import audit_evidence_presence, classify_agreement_status, parse_page_number
from datefac_agent.audit.output_schema_guardrails import OutputSchemaGuardrailError, validate_outputs
from datefac_agent.audit.period_alignment_checker import audit_period_alignment, detect_period_labels
from datefac_agent.audit.row_type_classifier import classify_row_type
from datefac_agent.audit.unit_semantic_checker import audit_unit_semantics
from datefac_agent.audit.valuation_metric_checker import classify_valuation_metric
from datefac_agent.intake.excel_intake import (
    _extract_special_metric_name,
    _find_key_value_start,
    _find_special_header_row,
    _refine_third_workbook_row_type,
    _refine_special_schema_row_type,
    _find_normalized_testset_header,
    _should_reset_read_only_dimensions,
)
from datefac_agent.review.clean_candidate_policy import classify_clean_candidate
from datefac_agent.review.review_queue_builder import build_audit_decision, build_row_audit_result, build_review_queue_rows
from datefac_agent.schemas.audit_models import AuditIssue, AuditRowResult, SpreadsheetRow
from tools.run_agent_excel_intake_audit_348a import build_manifest

FIXTURE_DIR = Path(__file__).with_name("fixtures")


def _make_row(metric_name: str, *, unit_hint: str | None = None, period_values: dict | None = None) -> SpreadsheetRow:
    return SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="财务估值",
        row_index=2,
        column_names=["会计年度", "2024A", "2025A"],
        raw_values={"会计年度": metric_name, "2024A": 1, "2025A": 2},
        metric_name=metric_name,
        unit_hint=unit_hint,
        period_values=period_values or {"2024A": 1, "2025A": 2},
    )


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _row_from_fixture(row_data: dict) -> SpreadsheetRow:
    return SpreadsheetRow(
        source_excel_path=row_data.get("source_excel_path", "demo.xlsx"),
        sheet_name=row_data.get("sheet_name", "财务估值"),
        row_index=row_data.get("row_index", 2),
        column_names=row_data.get("column_names", ["会计年度", "2024A", "2025A"]),
        raw_values=row_data.get("raw_values", {}),
        metric_name=row_data.get("metric_name", ""),
        unit_hint=row_data.get("unit_hint"),
        period_values=row_data.get("period_values", {}),
        explicit_evidence_ref=row_data.get("explicit_evidence_ref"),
        row_type=row_data.get("row_type", "UNKNOWN_ROW"),
    )


def _run_routing_fixture_case(case: dict) -> AuditRowResult:
    row = _row_from_fixture(case["row"])
    issues: list[AuditIssue] = []
    evidence_refs = []
    evidence_level = case.get("evidence_level", "MISSING_EVIDENCE")
    checks = set(case.get("checks", []))

    if "unit" in checks:
        issues.extend(audit_unit_semantics(row))
    if "period" in checks:
        issues.extend(audit_period_alignment(row))
    if "evidence" in checks:
        evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, case.get("pdf_path", "demo.pdf"))
        issues.extend(evidence_issues)

    return build_row_audit_result(row, issues, evidence_refs, evidence_level)


def test_schema_models_construct_for_348a() -> None:
    row = _make_row("营业收入(百万元)")
    assert row.metric_name == "营业收入(百万元)"


def test_unit_checker_flags_obvious_mismatch() -> None:
    issues = audit_unit_semantics(_make_row("EPS(百万元)", unit_hint="百万元"))
    assert any(issue.code == "per_share_unit_mismatch" for issue in issues)


def test_unit_checker_does_not_flag_roe_style_percentage_metrics() -> None:
    issues = audit_unit_semantics(_make_row("净资产收益率(%)", unit_hint="%"))
    assert not any(issue.code == "monetary_unit_mismatch" for issue in issues)

    roe_issues = audit_unit_semantics(_make_row("ROE(%)", unit_hint="%"))
    assert not any(issue.code == "monetary_unit_mismatch" for issue in roe_issues)

    debt_ratio_issues = audit_unit_semantics(_make_row("资产负债率(%)", unit_hint="%"))
    assert not any(issue.code == "monetary_unit_mismatch" for issue in debt_ratio_issues)

    debt_ratio_lf_issues = audit_unit_semantics(_make_row("资产负债率(%,LF)", unit_hint="%,LF"))
    assert not any(issue.code == "monetary_unit_mismatch" for issue in debt_ratio_lf_issues)


def test_unit_checker_still_flags_monetary_metrics_with_percent_units() -> None:
    revenue_issues = audit_unit_semantics(_make_row("营业收入(%)", unit_hint="%"))
    assert any(issue.code == "monetary_unit_mismatch" for issue in revenue_issues)

    asset_issues = audit_unit_semantics(_make_row("资产总计(%)", unit_hint="%"))
    assert any(issue.code == "monetary_unit_mismatch" for issue in asset_issues)

    liability_issues = audit_unit_semantics(_make_row("负债合计(%)", unit_hint="%"))
    assert any(issue.code == "monetary_unit_mismatch" for issue in liability_issues)


def test_period_checker_detects_expected_labels() -> None:
    labels = detect_period_labels(["会计年度", "2024A", "2025E", "2026Q1"])
    assert labels == ["2024A", "2025E", "2026Q1"]


def test_period_checker_detects_generalized_labels() -> None:
    labels = detect_period_labels(["项目", "2025A", "FY2026", "2027FY", "2028 Q1"])
    assert labels == ["2025A", "2026", "2027", "2028Q1"]


def test_period_checker_detects_embedded_period_labels() -> None:
    labels = detect_period_labels(
        ["项目", "2025A收入(亿元)", "2026E收入(亿元)", "2027E收入(亿元)", "2028E收入(亿元)", "2026E毛利率(%)"]
    )
    assert labels == ["2025A", "2026E", "2027E", "2028E"]


def test_valuation_checker_classifies_multiple_like_metrics() -> None:
    assert classify_valuation_metric("PE(倍)") == "PE"
    assert classify_valuation_metric("PB(倍)") == "PB"
    assert classify_valuation_metric("EV/EBITDA") == "EV/EBITDA"


def test_review_queue_returns_review_when_weak_evidence_exists() -> None:
    row = _make_row("YoY(%)", unit_hint="%")
    issues = audit_unit_semantics(row)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, issues + evidence_issues, evidence_refs, evidence_level)
    assert result.decision is not None
    assert result.decision.decision == "REVIEW"
    queue_rows = build_review_queue_rows([result])
    assert queue_rows[0]["decision"] == "REVIEW"
    assert queue_rows[0]["evidence_level"] == "WEAK_EVIDENCE"
    assert "weak_evidence" in queue_rows[0]["issue_codes"]


def test_internal_candidates_are_removed_from_review_queue() -> None:
    row = _make_row("营业收入(百万元)")
    row.row_type = "STRICT_FINANCIAL_TABLE_ROW"
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    queue_rows = build_review_queue_rows([result])
    assert queue_rows == []


def test_strict_financial_weak_evidence_row_becomes_internal_clean_candidate() -> None:
    row = _make_row("营业收入(百万元)")
    row.row_type = "STRICT_FINANCIAL_TABLE_ROW"
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "INTERNAL_CLEAN_CANDIDATE"


# --- R7S: strict-table pseudo-header / comparison-row clean-boundary tests ---
#
# R7R found that STRICT_FINANCIAL_TABLE_ROW + WEAK_EVIDENCE over-admitted rows
# whose period_values carry no numeric fact (e.g. 市场数据 / 厂商 / 对比维度 /
# 项目 / 指标). These rows are table scaffolding, not stable financial facts,
# so the project principle "宁可进 review，不轻易进 clean" requires them to route
# to REVIEW_REQUIRED while normal numeric fact rows keep their clean admission.


def _make_strict_scaffolding_row(
    metric_name: str,
    *,
    sheet_name: str = "核心盈利预测与估值",
    period_values: dict | None = None,
) -> SpreadsheetRow:
    """Build a STRICT_FINANCIAL_TABLE_ROW with WEAK_EVIDENCE and given period values.

    period_values default to non-numeric scaffolding content so a caller only
    needs to override when asserting numeric-fact preservation.
    """

    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name=sheet_name,
        row_index=11,
        column_names=["指标", "2025", "2026E", "2027E"],
        raw_values={"指标": metric_name, "2025": "数值", "2026E": "基础数据", "2027E": "数值"},
        metric_name=metric_name,
        period_values=period_values if period_values is not None else {"2025": "数值", "2026E": "基础数据", "2027E": "数值"},
        row_type="STRICT_FINANCIAL_TABLE_ROW",
    )
    return row


def test_r7s_market_data_pseudo_header_row_does_not_enter_clean_data() -> None:
    # 核心盈利预测与估值,11,市场数据  period_values = "数值","基础数据","数值"
    row = _make_strict_scaffolding_row("市场数据")
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert evidence_level == "WEAK_EVIDENCE"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_r7s_vendor_comparison_dimension_row_does_not_enter_clean_data() -> None:
    # 行业赛道数据,13,厂商  period_values = "型号","最大功率","排量","缸型"
    row = _make_strict_scaffolding_row(
        "厂商",
        sheet_name="行业赛道数据",
        period_values={"2025": "型号", "2026E": "最大功率", "2027E": "排量", "2028E": "缸型"},
    )
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_r7s_comparison_axis_row_does_not_enter_clean_data() -> None:
    # 行业赛道数据,19,对比维度  period_values = "中速燃气内燃机","重型/航改型燃气轮机"
    row = _make_strict_scaffolding_row(
        "对比维度",
        sheet_name="行业赛道数据",
        period_values={"2025": "中速燃气内燃机", "2026E": "重型/航改型燃气轮机"},
    )
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_r7s_echoed_period_label_header_row_does_not_enter_clean_data() -> None:
    # 三大财务报表与核心指标,17,项目  period_values echo the period labels themselves
    row = _make_strict_scaffolding_row(
        "项目",
        sheet_name="三大财务报表与核心指标",
        period_values={"2025A": "2025A", "2026E": "2026E", "2027E": "2027E", "2028E": "2028E"},
    )
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_r7s_indicator_echoed_label_header_row_does_not_enter_clean_data() -> None:
    # 三大财务报表与核心指标,35,指标  period_values echo the period labels themselves
    row = _make_strict_scaffolding_row(
        "指标",
        sheet_name="三大财务报表与核心指标",
        period_values={"2025A": "2025A", "2026E": "2026E", "2027E": "2027E", "2028E": "2028E"},
    )
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_r7s_normal_numeric_fact_row_preserves_clean_admission() -> None:
    # Normal financial rows (营业总收入 / 归母净利润 / EPS / P/E / ROE / 毛利率 / 收入同比)
    # must stay INTERNAL_CLEAN_CANDIDATE when their period values are numeric.
    row = _make_strict_scaffolding_row(
        "营业总收入(百万元)",
        period_values={"2024A": 4356, "2025A": 4521, "2026E": 6317, "2027E": 7535, "2028E": 8755},
    )
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "INTERNAL_CLEAN_CANDIDATE"


def test_r7s_numeric_string_fact_row_preserves_clean_admission() -> None:
    # Numeric strings such as "4356" / "-991.03" still count as numeric facts, so
    # a strict row whose values are numeric strings must not be blocked.
    row = _make_strict_scaffolding_row(
        "归母净利润(百万元)",
        period_values={"2024A": "-991.03", "2025A": "60.54", "2026E": "356.68"},
    )
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "INTERNAL_CLEAN_CANDIDATE"


def test_r7s_mixed_numeric_and_dash_fact_row_preserves_clean_admission() -> None:
    # A row like PUE系数 may carry "-" for an early period but real numbers later.
    # Because at least one value is numeric, it is a fact row, not scaffolding.
    row = _make_strict_scaffolding_row(
        "PUE系数",
        sheet_name="行业赛道数据",
        period_values={"2025": "-", "2026E": 1.49, "2027E": 1.48, "2028E": 1.47},
    )
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "INTERNAL_CLEAN_CANDIDATE"


def test_r7s_scaffolding_guard_does_not_block_numeric_row_with_explicit_ref_r7x() -> None:
    # R7X: an explicit page reference makes evidence WEAK_EVIDENCE (UNVERIFIED),
    # not STRONG_EVIDENCE. Because the row has numeric period_values, the
    # scaffolding guard does not apply, so the row stays INTERNAL_CLEAN_CANDIDATE.
    # This confirms the guard only blocks non-numeric scaffolding rows, never
    # numeric fact rows regardless of evidence provenance.
    row = _make_strict_scaffolding_row(
        "营业总收入(百万元)",
        period_values={"2024A": 4356, "2025A": 4521},
    )
    row.explicit_evidence_ref = "page=12"
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert evidence_level == "WEAK_EVIDENCE"
    assert result.agreement_status == "UNVERIFIED"
    assert result.clean_candidate_type == "INTERNAL_CLEAN_CANDIDATE"


def test_r7s_scaffolding_label_with_numeric_values_stays_clean() -> None:
    # A metric label that happens to be in the scaffolding set (e.g. 指标) must
    # NOT be blocked when its period_values are genuinely numeric facts. The
    # period_values shape is the primary discriminator, never the label alone.
    row = _make_strict_scaffolding_row(
        "指标",
        period_values={"2025A": 3.54, "2026E": 5.01, "2027E": 6.54, "2028E": 7.69},
    )
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "INTERNAL_CLEAN_CANDIDATE"


def test_market_reference_weak_evidence_row_now_stays_review_required() -> None:
    row = _make_row("总市值（亿元）", unit_hint="亿元")
    row.sheet_name = "市场与基础数据"
    row.row_type = "MARKET_REFERENCE_ROW"
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert evidence_level == "WEAK_EVIDENCE"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_market_reference_weak_evidence_row_with_unit_issue_stays_review_required() -> None:
    row = _make_row("总市值（亿元）", unit_hint="亿元")
    row.sheet_name = "市场与基础数据"
    row.row_type = "MARKET_REFERENCE_ROW"
    issues = [
        AuditIssue(
            code="market_reference_unit_warning",
            severity="warning",
            category="unit",
            message="Market reference unit needs review.",
        )
    ]
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, issues + evidence_issues, evidence_refs, evidence_level)
    assert any(issue.category == "unit" for issue in result.issues)
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


# --- R7Y: deterministic source-value agreement checker tests ---


def _make_r7y_explicit_row(period_values: dict) -> SpreadsheetRow:
    row = _make_row("营业收入(百万元)", period_values=period_values)
    row.explicit_evidence_ref = "第12页"
    return row


def test_r7y_no_explicit_evidence_returns_missing_agreement() -> None:
    row = _make_row("营业收入(百万元)", period_values={"2024A": 1234})
    _, evidence_refs, _ = audit_evidence_presence(row, "demo.pdf")
    assert classify_agreement_status(row, evidence_refs, source_text="营业收入 1,234") == "MISSING"


def test_r7y_explicit_page_ref_without_source_text_returns_unverified() -> None:
    row = _make_r7y_explicit_row({"2024A": 1234})
    _, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    assert evidence_level == "WEAK_EVIDENCE"
    assert classify_agreement_status(row, evidence_refs) == "UNVERIFIED"


def test_r7y_exact_numeric_value_returns_verified() -> None:
    row = _make_r7y_explicit_row({"2024A": 1234})
    _, evidence_refs, _ = audit_evidence_presence(row, "demo.pdf")
    assert classify_agreement_status(row, evidence_refs, source_text="2024A 营业收入 1234 百万元") == "VERIFIED"


def test_r7y_comma_formatted_equivalent_value_returns_verified() -> None:
    row = _make_r7y_explicit_row({"2024A": 1234})
    _, evidence_refs, _ = audit_evidence_presence(row, "demo.pdf")
    assert classify_agreement_status(row, evidence_refs, source_text="2024A 营业收入 1,234 百万元") == "VERIFIED"


def test_r7y_percentage_equivalent_value_returns_verified() -> None:
    row = _make_r7y_explicit_row({"2024A": "12.30%"})
    _, evidence_refs, _ = audit_evidence_presence(row, "demo.pdf")
    assert classify_agreement_status(row, evidence_refs, source_text="毛利率为 12.3%") == "VERIFIED"


def test_r7y_parentheses_negative_value_returns_verified() -> None:
    row = _make_r7y_explicit_row({"2024A": -123})
    _, evidence_refs, _ = audit_evidence_presence(row, "demo.pdf")
    assert classify_agreement_status(row, evidence_refs, source_text="归母净利润 (123) 百万元") == "VERIFIED"


def test_r7y_numeric_mismatch_returns_disagreed() -> None:
    row = _make_r7y_explicit_row({"2024A": 1234})
    _, evidence_refs, _ = audit_evidence_presence(row, "demo.pdf")
    assert classify_agreement_status(row, evidence_refs, source_text="2024A 营业收入 999 百万元") == "DISAGREED"


def test_r7y_partial_multi_period_coverage_stays_unverified() -> None:
    row = _make_r7y_explicit_row({"2024A": 100, "2025A": 200})
    _, evidence_refs, _ = audit_evidence_presence(row, "demo.pdf")
    assert classify_agreement_status(row, evidence_refs, source_text="2024A 营业收入 100 百万元") == "UNVERIFIED"


def test_r7y_text_valued_facts_stay_unverified() -> None:
    row = _make_r7y_explicit_row({"2024A": "基础数据", "2025A": "数值"})
    _, evidence_refs, _ = audit_evidence_presence(row, "demo.pdf")
    assert classify_agreement_status(row, evidence_refs, source_text="基础数据 数值") == "UNVERIFIED"


def test_r7y_verified_does_not_change_evidence_level_or_clean_policy() -> None:
    row = _make_r7y_explicit_row({"2024A": 1234})
    row.row_type = "MARKET_REFERENCE_ROW"
    _, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, [], evidence_refs, evidence_level)
    assert classify_agreement_status(row, evidence_refs, source_text="总市值 1,234 亿元") == "VERIFIED"
    assert evidence_level == "WEAK_EVIDENCE"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_r7y_manifest_readiness_gates_remain_closed() -> None:
    manifest = build_manifest(
        "REVIEW_REQUIRED",
        type("Intake", (), {"sheet_count": 1, "row_count_total": 1})(),
        type(
            "Summary",
            (),
            {
                "fail_count": 0,
                "row_count_audited": 1,
                "pass_count": 0,
                "review_count": 1,
                "issue_count_total": 0,
                "unit_issue_count": 0,
                "period_issue_count": 0,
                "valuation_issue_count": 0,
                "evidence_issue_count": 0,
                "strong_evidence_count": 0,
                "weak_evidence_count": 1,
                "missing_evidence_count": 0,
                "not_applicable_evidence_count": 0,
                "weak_evidence_issue_count": 0,
                "missing_evidence_issue_count": 0,
                "strict_financial_table_row_count": 0,
                "market_reference_row_count": 1,
                "narrative_assertion_count": 0,
                "normalized_testset_record_row_count": 0,
                "testset_supporting_row_count": 0,
                "unknown_row_count": 0,
                "clean_data_row_count": 0,
                "review_queue_row_count": 1,
                "internal_clean_candidate_count": 0,
                "internal_reference_candidate_count": 0,
                "narrative_review_count": 0,
                "review_required_count": 1,
                "excluded_from_clean_data_count": 0,
            },
        )(),
        "demo.pdf",
        "demo.xlsx",
        "output/demo",
    )
    assert manifest["demo_export_only"] is True
    assert manifest["formal_client_export_allowed"] is False
    assert manifest["client_ready"] is False
    assert manifest["production_ready"] is False


def test_second_workbook_summary_sheet_can_split_narrative_and_market_rows() -> None:
    narrative_row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="报告概要",
        row_index=3,
        column_names=["field_name", "field_value"],
        raw_values={"field_name": "报告标题", "field_value": "老牌军工细分赛道企业"},
        metric_name="报告标题",
    )
    market_row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="报告概要",
        row_index=9,
        column_names=["field_name", "field_value"],
        raw_values={"field_name": "收盘价(元)", "field_value": "14.21"},
        metric_name="收盘价(元)",
    )
    assert classify_row_type(narrative_row) == "NARRATIVE_ASSERTION"
    assert classify_row_type(market_row) == "MARKET_REFERENCE_ROW"


def test_second_workbook_financial_sheet_becomes_strict_financial_row() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="盈利预测与估值",
        row_index=4,
        column_names=["指标", "2024A", "2025A", "2026E", "2027E"],
        raw_values={"指标": "营业总收入（百万元）", "2024A": "4356", "2025A": "4521", "2026E": "6317", "2027E": "7535"},
        metric_name="营业总收入（百万元）",
        period_values={"2024A": "4356", "2025A": "4521", "2026E": "6317", "2027E": "7535"},
    )
    assert classify_row_type(row) == "STRICT_FINANCIAL_TABLE_ROW"


def test_third_workbook_report_metadata_row_becomes_narrative_assertion() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="报告核心信息与投资要点",
        row_index=2,
        column_names=["field_name", "field_value"],
        raw_values={"field_name": "报告类型", "field_value": "公司深度研究"},
        metric_name="报告类型",
    )
    assert _refine_third_workbook_row_type(row, classify_row_type(row)) == "NARRATIVE_ASSERTION"


def test_third_workbook_business_matrix_row_becomes_narrative_assertion() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="公司业务与产品矩阵",
        row_index=3,
        column_names=["产品类别", "核心产品", "2025年营收占比", "主要应用领域", "核心特点"],
        raw_values={
            "产品类别": "军工装备",
            "核心产品": "车载通信指挥系统",
            "2025年营收占比": "约33%",
            "主要应用领域": "各军兵种实战演训与重大保障任务",
            "核心特点": "方舱轻量化技术",
        },
        metric_name="军工装备",
        period_values={"2025年营收占比": "约33%"},
    )
    assert _refine_third_workbook_row_type(row, classify_row_type(row)) == "NARRATIVE_ASSERTION"


def test_third_workbook_na_aidc_reference_row_becomes_narrative_assertion() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="北美AIDC电力供需与技术路径",
        row_index=4,
        column_names=["电厂名称", "所在州", "装机容量", "退役时间", "核心驱动因素", "转型计划", "备注"],
        raw_values={
            "电厂名称": "因特山电力项目(IPP)",
            "所在州": "犹他州",
            "装机容量": "1,640MW(2台机组)",
            "退役时间": "2026年12月",
        },
        metric_name="因特山电力项目(IPP)",
        period_values={"2026年2月": "2026年12月"},
    )
    assert _refine_third_workbook_row_type(row, classify_row_type(row)) == "NARRATIVE_ASSERTION"


def test_third_workbook_mixed_valuation_narrative_stays_review_only() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="报告核心信息与投资要点",
        row_index=14,
        column_names=["field_name", "field_value"],
        raw_values={"field_name": "3. 业绩弹性：2026-2028年归母净利润预计3.6/5.3/6.1亿元，对应PE 34/23/20倍，成长空间持续打开。"},
        metric_name="3. 业绩弹性：2026-2028年归母净利润预计3.6/5.3/6.1亿元，对应PE 34/23/20倍，成长空间持续打开。",
    )
    row.row_type = _refine_third_workbook_row_type(row, classify_row_type(row))
    issues = audit_unit_semantics(row)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, issues + evidence_issues, evidence_refs, evidence_level)
    assert row.row_type == "NARRATIVE_ASSERTION"
    assert result.clean_candidate_type == "EXCLUDED_FROM_CLEAN_DATA"


def test_third_workbook_implicit_percent_rows_do_not_raise_percentage_missing() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="分业务盈利预测明细",
        row_index=4,
        column_names=["项目", "2024A", "2025A", "2026E", "2027E", "2028E"],
        raw_values={"项目": "同比增速", "2024A": 60, "2025A": 1.4, "2026E": 60, "2027E": 25, "2028E": 20},
        metric_name="同比增速",
        period_values={"2024A": 60, "2025A": 1.4, "2026E": 60, "2027E": 25, "2028E": 20},
        row_type="STRICT_FINANCIAL_TABLE_ROW",
    )
    issues = audit_unit_semantics(row)
    assert any(issue.code == "implicit_percentage_unit_confirmation_needed" for issue in issues)
    assert not any(issue.code == "percentage_unit_missing" for issue in issues)


def test_third_workbook_anchor_row_routes_out_of_strict_period_review() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="三大财务报表与核心指标",
        row_index=16,
        column_names=["项目", "2025A", "2026E", "2027E", "2028E"],
        raw_values={"项目": "资产负债表（单位：百万元）"},
        metric_name="资产负债表（单位：百万元）",
        unit_hint="单位：百万元",
        row_type="STRICT_FINANCIAL_TABLE_ROW",
    )
    row.row_type = _refine_third_workbook_row_type(row, row.row_type)
    assert row.row_type == "NARRATIVE_ASSERTION"
    assert audit_period_alignment(row) == []


def test_normalized_testset_header_detection_is_explicit() -> None:
    sheet_rows = [
        (1, ["record_id", "source_pdf", "source_page", "table_name", "statement", "line_item", "period", "value", "unit", "value_text_original", "confidence", "note"]),
        (2, ["R0001", "demo.pdf", 1, "table", "statement", "metric", "2024A", 1, "百万元", "1", "高", "note"]),
    ]

    header = _find_normalized_testset_header(sheet_rows)
    assert header is not None
    assert header[0] == 1


def test_normalized_testset_rows_receive_explicit_schema_row_type() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="normalized_testset",
        row_index=2,
        column_names=["record_id", "source_pdf", "source_page", "table_name", "statement", "line_item", "period", "value", "unit", "value_text_original", "confidence", "note"],
        raw_values={
            "record_id": "R0001",
            "source_pdf": "demo.pdf",
            "source_page": 1,
            "table_name": "盈利预测与估值",
            "statement": "statement",
            "line_item": "营业总收入",
            "period": "2024A",
            "value": 1,
            "unit": "百万元",
            "value_text_original": "1",
            "confidence": "高",
            "note": "从PDF表格抽取",
        },
        metric_name="R0001",
        row_type="UNKNOWN_ROW",
    )

    refined = _refine_special_schema_row_type(row, "UNKNOWN_ROW", normalized_testset_detected=True)
    assert refined == "NORMALIZED_TESTSET_RECORD_ROW"


def test_normalized_testset_rows_stay_out_of_clean_data() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="normalized_testset",
        row_index=2,
        column_names=["record_id", "source_pdf", "source_page", "table_name", "statement", "line_item", "period", "value", "unit", "value_text_original", "confidence", "note"],
        raw_values={"record_id": "R0001", "source_pdf": "demo.pdf", "source_page": 1, "table_name": "盈利预测与估值", "statement": "statement", "line_item": "营业总收入", "period": "2024A", "value": 1, "unit": "百万元", "value_text_original": "1", "confidence": "高", "note": "从PDF表格抽取"},
        metric_name="R0001",
        period_values={"2024A": 1},
        row_type="NORMALIZED_TESTSET_RECORD_ROW",
    )
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_normalized_testset_support_does_not_change_wide_workbook_classification() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="璐㈠姟浼板€?",
        row_index=4,
        column_names=["浼氳骞村害", "2024A", "2025A"],
        raw_values={"浼氳骞村害": "钀ヤ笟鏀跺叆", "2024A": 1, "2025A": 2},
        metric_name="钀ヤ笟鏀跺叆",
        period_values={"2024A": 1, "2025A": 2},
    )
    assert classify_row_type(row) == "STRICT_FINANCIAL_TABLE_ROW"


def test_readme_rows_become_testset_supporting_rows_and_stay_out_of_clean_data() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="README",
        row_index=2,
        column_names=["field_name", "field_value"],
        raw_values={"field_name": "生成时间", "field_value": "2026-06-17 13:28:58"},
        metric_name="生成时间",
    )
    row.row_type = _refine_special_schema_row_type(row, "UNKNOWN_ROW", normalized_testset_detected=False)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert row.row_type == "TESTSET_SUPPORTING_ROW"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_data_dictionary_rows_become_testset_supporting_rows_and_stay_out_of_clean_data() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="data_dictionary",
        row_index=2,
        column_names=["字段", "解释"],
        raw_values={"字段": "source_pdf", "解释": "源PDF文件名"},
        metric_name="source_pdf",
    )
    row.row_type = _refine_special_schema_row_type(row, "UNKNOWN_ROW", normalized_testset_detected=False)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert row.row_type == "TESTSET_SUPPORTING_ROW"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_figure_index_rows_become_testset_supporting_rows_and_stay_out_of_clean_data() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="figure_index",
        row_index=2,
        column_names=["图表编号", "页码", "标题", "图表类型", "可用结构化数据", "处理策略", "备注"],
        raw_values={"图表编号": "图1", "页码": 4, "标题": "2022~2026Q1 公司营业收入", "图表类型": "柱线图", "可用结构化数据": "部分数据在正文/表格中出现", "处理策略": "未从图片精确读数；测试集优先使用正文与财务表数值", "备注": None},
        metric_name="2022~2026Q1 公司营业收入",
    )
    row.row_type = _refine_special_schema_row_type(row, "UNKNOWN_ROW", normalized_testset_detected=False)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert row.row_type == "TESTSET_SUPPORTING_ROW"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_figure_index_metric_name_prefers_chart_id_over_title() -> None:
    raw_values = {
        "图表编号": "图5",
        "页码": 5,
        "标题": "公司各类费用率（%）",
        "图表类型": "折线图",
        "可用结构化数据": "正文披露费用率",
        "处理策略": "仅抽取正文明确披露的费用率",
        "备注": None,
    }
    metric_name = _extract_special_metric_name(
        "figure_index",
        ["图表编号", "页码", "标题", "图表类型", "可用结构化数据", "处理策略", "备注"],
        raw_values,
        ["图5", 5, "公司各类费用率（%）"],
    )
    assert metric_name == "图5"


def test_validation_checks_rows_become_testset_supporting_rows_and_do_not_enter_clean_data() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="validation_checks",
        row_index=2,
        column_names=["校验项", "2025A", "2026E", "2027E", "2028E", "说明"],
        raw_values={"校验项": "资产总计 - 负债和股东权益", "2025A": 0, "2026E": 0, "2027E": 0, "2028E": 0, "说明": "应为0"},
        metric_name="资产总计 - 负债和股东权益",
        period_values={"2025A": 0, "2026E": 0, "2027E": 0, "2028E": 0},
    )
    row.row_type = _refine_special_schema_row_type(row, "STRICT_FINANCIAL_TABLE_ROW", normalized_testset_detected=False)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert row.row_type == "TESTSET_SUPPORTING_ROW"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_market_base_data_rows_become_market_reference_rows_but_do_not_expand_clean_data() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="market_base_data",
        row_index=2,
        column_names=["类别", "指标", "数值", "单位", "期间/口径", "来源页", "置信度", "备注"],
        raw_values={"类别": "市场数据", "指标": "收盘价", "数值": 6.48, "单位": "元", "期间/口径": "报告日/现价", "来源页": 1, "置信度": "高", "备注": None},
        metric_name="收盘价",
    )
    row.explicit_evidence_ref = "1"
    row.row_type = _refine_special_schema_row_type(row, "UNKNOWN_ROW", normalized_testset_detected=False)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert row.row_type == "MARKET_REFERENCE_ROW"
    assert evidence_level == "WEAK_EVIDENCE"
    assert result.agreement_status == "UNVERIFIED"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


# qualitative_facts is a facts-schema sheet (事实ID/页码/指标/数值/单位/期间/摘录/置信度),
# not a financial wide table. R5: detect its real Chinese header so 页码 evidence is
# restored and rows route to TESTSET_SUPPORTING_ROW instead of leaking into clean_data.
QUALITATIVE_FACTS_HEADERS_ROW = [
    "事实ID",
    "页码",
    "类别",
    "主体",
    "指标/事件",
    "数值",
    "单位",
    "期间",
    "摘录/说明",
    "置信度",
]


def _qualitative_facts_sheet_rows() -> list[tuple[int, list]]:
    """Row 1 = real header; row 2 = F001 data (was misdetected as header pre-R5)."""
    return [
        (1, list(QUALITATIVE_FACTS_HEADERS_ROW)),
        (2, ["F001", 1, "业务概况", "林洋能源", "成立时间", 1995, "年", None, "公司成立于1995年。", "高"]),
        (3, ["F002", 1, "业务布局", "林洋能源", "三大业务", None, None, None, "智能电表、储能、光伏。", "高"]),
        (4, ["F003", 1, "业绩", "林洋能源", "2022-2024营收", 34.0, "亿元", "2022-2024", "营收稳健增长。", "高"]),
    ]


def test_qualitative_facts_real_chinese_header_is_detected_as_header() -> None:
    sheet_rows = _qualitative_facts_sheet_rows()
    found = _find_special_header_row("qualitative_facts", sheet_rows)
    assert found is not None
    header_row_index, header_names = found
    assert header_row_index == 1
    assert header_names == QUALITATIVE_FACTS_HEADERS_ROW


def test_qualitative_facts_f001_data_row_is_not_selected_as_header() -> None:
    # The F001 data row contains "1995", which pre-R5 matched PERIOD_LABEL_RE and was
    # wrongly accepted as the header by the generic _find_header_row. The special-sheet
    # path must pick the real row-1 header before F001 can be considered.
    sheet_rows = _qualitative_facts_sheet_rows()
    found = _find_special_header_row("qualitative_facts", sheet_rows)
    assert found is not None
    assert found[0] == 1  # row 1, not row 2 (F001)


def test_qualitative_facts_page_column_is_preserved_in_parsed_row() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="qualitative_facts",
        row_index=3,
        column_names=list(QUALITATIVE_FACTS_HEADERS_ROW),
        raw_values={
            "事实ID": "F003",
            "页码": 1,
            "类别": "业绩",
            "主体": "林洋能源",
            "指标/事件": "2022-2024营收",
            "数值": 34.0,
            "单位": "亿元",
            "期间": "2022-2024",
            "摘录/说明": "营收稳健增长。",
            "置信度": "高",
        },
        metric_name="2022-2024营收",
    )
    # 页码 must survive as a real column so evidence extraction can find it.
    assert "页码" in row.column_names
    assert row.raw_values["页码"] == 1


def test_qualitative_facts_explicit_evidence_ref_extracted_from_page_column() -> None:
    from datefac_agent.intake.excel_intake import _extract_explicit_evidence_ref

    values = ["F003", 1, "业绩", "林洋能源", "2022-2024营收", 34.0, "亿元", "2022-2024", "营收稳健增长。", "高"]
    ref = _extract_explicit_evidence_ref(list(QUALITATIVE_FACTS_HEADERS_ROW), values)
    assert ref == "1"


def test_qualitative_facts_metric_name_prefers_indicator_over_fact_id() -> None:
    raw_values = {
        "事实ID": "F003",
        "页码": 1,
        "类别": "业绩",
        "主体": "林洋能源",
        "指标/事件": "2022-2024营收",
        "数值": 34.0,
        "单位": "亿元",
        "期间": "2022-2024",
        "摘录/说明": "营收稳健增长。",
        "置信度": "高",
    }
    metric_name = _extract_special_metric_name(
        "qualitative_facts",
        list(QUALITATIVE_FACTS_HEADERS_ROW),
        raw_values,
        list(raw_values.values()),
    )
    assert metric_name == "2022-2024营收"


def test_qualitative_facts_rows_become_testset_supporting_and_stay_out_of_clean_data() -> None:
    # A qualitative_facts row (页码=1 restored) must route to TESTSET_SUPPORTING_ROW
    # and resolve to REVIEW_REQUIRED, never INTERNAL_CLEAN_CANDIDATE. R7X: the
    # explicit page reference is parsed and agreement_status is UNVERIFIED, so
    # evidence_level is WEAK_EVIDENCE (not STRONG) until a future value-agreement
    # checker verifies it.
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="qualitative_facts",
        row_index=3,
        column_names=list(QUALITATIVE_FACTS_HEADERS_ROW),
        raw_values={
            "事实ID": "F003",
            "页码": 1,
            "类别": "业绩",
            "主体": "林洋能源",
            "指标/事件": "2022-2024营收",
            "数值": 34.0,
            "单位": "亿元",
            "期间": "2022-2024",
            "摘录/说明": "营收稳健增长。",
            "置信度": "高",
        },
        metric_name="2022-2024营收",
    )
    row.explicit_evidence_ref = "1"
    row.row_type = _refine_special_schema_row_type(row, "STRICT_FINANCIAL_TABLE_ROW", normalized_testset_detected=False)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert row.row_type == "TESTSET_SUPPORTING_ROW"
    assert evidence_level == "WEAK_EVIDENCE"
    assert result.agreement_status == "UNVERIFIED"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_qualitative_facts_weak_evidence_row_still_does_not_enter_clean_data() -> None:
    # Even if a qualitative_facts row somehow lacked 页码 (WEAK_EVIDENCE), the
    # TESTSET_SUPPORTING_ROW routing must keep it out of clean_data.
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="qualitative_facts",
        row_index=3,
        column_names=list(QUALITATIVE_FACTS_HEADERS_ROW),
        raw_values={
            "事实ID": "F002",
            "页码": None,
            "类别": "业务布局",
            "主体": "林洋能源",
            "指标/事件": "三大业务",
            "数值": None,
            "单位": None,
            "期间": None,
            "摘录/说明": "智能电表、储能、光伏。",
            "置信度": "高",
        },
        metric_name="三大业务",
    )
    row.row_type = _refine_special_schema_row_type(row, "STRICT_FINANCIAL_TABLE_ROW", normalized_testset_detected=False)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert row.row_type == "TESTSET_SUPPORTING_ROW"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_narrative_assertion_stays_out_of_clean_data() -> None:
    row = _make_row("核心逻辑")
    row.sheet_name = "核心观点"
    row.row_type = "NARRATIVE_ASSERTION"
    row.period_values = {}
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "NARRATIVE_REVIEW"


def test_missing_evidence_row_does_not_enter_clean_data() -> None:
    row = SpreadsheetRow(
        source_excel_path="",
        sheet_name="财务估值",
        row_index=2,
        column_names=[],
        raw_values={},
        metric_name="营业收入",
        period_values={"2024A": 1},
        row_type="STRICT_FINANCIAL_TABLE_ROW",
    )
    result = AuditRowResult(
        row=row,
        issues=[AuditIssue(code="missing_evidence", severity="warning", category="evidence", message="missing")],
        evidence_level="MISSING_EVIDENCE",
        row_type=row.row_type,
    )
    assert classify_clean_candidate(result) == "EXCLUDED_FROM_CLEAN_DATA"


def test_error_issue_row_does_not_enter_clean_data() -> None:
    row = _make_row("营业收入(%)", unit_hint="%")
    row.row_type = "STRICT_FINANCIAL_TABLE_ROW"
    issues = audit_unit_semantics(row)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, issues + evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "EXCLUDED_FROM_CLEAN_DATA"


def test_period_issue_strict_row_does_not_enter_clean_data() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="现金流量表",
        row_index=2,
        column_names=["会计年度", "2024A", "2025A"],
        raw_values={"会计年度": "经营活动现金流", "2024A": "", "2025A": ""},
        metric_name="经营活动现金流",
        period_values={},
        row_type="STRICT_FINANCIAL_TABLE_ROW",
    )
    period_issues = audit_period_alignment(row)
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, period_issues + evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "REVIEW_REQUIRED"


def test_explicit_evidence_ref_is_unverified_weak_evidence_r7x() -> None:
    # R7X: explicit page provenance that has not been value-verified is
    # WEAK_EVIDENCE, not STRONG_EVIDENCE. agreement_status carries the
    # UNVERIFIED state separately, and the page number is parsed into the
    # structured EvidenceRef.page_number field.
    row = _make_row("营业收入(百万元)")
    row.explicit_evidence_ref = "page=12"
    issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    assert evidence_level == "WEAK_EVIDENCE"
    explicit_ref = next(ref for ref in evidence_refs if ref.is_explicit)
    assert explicit_ref.page_number == 12
    assert classify_agreement_status(row, evidence_refs) == "UNVERIFIED"


# --- R7X: evidence provenance parsing (page_number) + agreement_status tests ---
#
# R7W designed a deterministic WEAK->STRONG path. R7X implements the first slice:
# parse explicit_evidence_ref into EvidenceRef.page_number, add agreement_status,
# and ensure unverified page provenance does not become verified STRONG_EVIDENCE.


def test_r7x_parse_chinese_page_ref_populates_page_number() -> None:
    # 第12页 -> page_number = 12, agreement_status = UNVERIFIED
    row = _make_row("营业收入(百万元)")
    row.explicit_evidence_ref = "第12页"
    _, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    explicit_ref = next(ref for ref in evidence_refs if ref.is_explicit)
    assert explicit_ref.page_number == 12
    assert explicit_ref.locator == "营业收入(百万元)"
    assert evidence_level == "WEAK_EVIDENCE"
    assert classify_agreement_status(row, evidence_refs) == "UNVERIFIED"


def test_r7x_parse_english_page_ref_variants_populate_page_number() -> None:
    # page 12 / p.12 / P12 all parse to page_number = 12
    for ref_text in ("page 12", "p.12", "P12"):
        assert parse_page_number(ref_text) == 12, ref_text


def test_r7x_parse_page_range_preserves_locator_and_uses_first_page() -> None:
    # 第12-13页 -> page_number = 12 (first page), raw locator preserved
    row = _make_row("归母净利润(百万元)")
    row.explicit_evidence_ref = "第12-13页"
    _, evidence_refs, _ = audit_evidence_presence(row, "demo.pdf")
    explicit_ref = next(ref for ref in evidence_refs if ref.is_explicit)
    assert explicit_ref.page_number == 12
    assert explicit_ref.source_id == "第12-13页"
    # pp. 12-13 variant
    assert parse_page_number("pp. 12-13") == 12


def test_r7x_unparseable_explicit_ref_preserves_locator_without_page_number() -> None:
    # 附录A -> page_number stays None, raw locator preserved, agreement UNVERIFIED
    row = _make_row("营业收入(百万元)")
    row.explicit_evidence_ref = "附录A"
    _, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    explicit_ref = next(ref for ref in evidence_refs if ref.is_explicit)
    assert explicit_ref.page_number is None
    assert explicit_ref.source_id == "附录A"
    assert evidence_level == "WEAK_EVIDENCE"
    assert classify_agreement_status(row, evidence_refs) == "UNVERIFIED"


def test_r7x_missing_explicit_ref_yields_missing_agreement_status() -> None:
    # No explicit_evidence_ref -> agreement_status = MISSING, evidence WEAK
    row = _make_row("营业收入(百万元)")
    _, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    assert evidence_level == "WEAK_EVIDENCE"
    assert classify_agreement_status(row, evidence_refs) == "MISSING"
    result = build_row_audit_result(row, [], evidence_refs, evidence_level)
    assert result.agreement_status == "MISSING"


def test_r7x_parsed_page_unverified_does_not_claim_verified_strong_evidence() -> None:
    # The core R7X guard: parsed page_number + UNVERIFIED must not produce
    # STRONG_EVIDENCE. Evidence stays WEAK until a future value-agreement
    # checker verifies it.
    row = _make_row("营业收入(百万元)")
    row.explicit_evidence_ref = "第12页"
    _, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, [], evidence_refs, evidence_level)
    assert evidence_level == "WEAK_EVIDENCE"
    assert result.agreement_status == "UNVERIFIED"
    # No EvidenceRef should claim is_explicit with a page_number that triggers STRONG
    assert all(ref.page_number is None or ref.source_type == "explicit_workbook_evidence" for ref in evidence_refs)


def test_r7x_workbook_row_weak_evidence_behavior_preserved() -> None:
    # Existing workbook-row-based weak evidence (no explicit ref) still works.
    row = _make_row("营业收入(百万元)")
    row.row_type = "STRICT_FINANCIAL_TABLE_ROW"
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert evidence_level == "WEAK_EVIDENCE"
    assert result.agreement_status == "MISSING"


def test_r7x_parse_page_number_none_for_empty_and_non_numeric() -> None:
    assert parse_page_number(None) is None
    assert parse_page_number("") is None
    assert parse_page_number("   ") is None
    assert parse_page_number("附录") is None


def test_r7x_evidence_index_writer_includes_agreement_status() -> None:
    # agreement_status must be auditable in the evidence index output.
    import json
    import tempfile

    from datefac_agent.delivery.evidence_index_writer import write_evidence_index

    row = _make_row("营业收入(百万元)")
    row.explicit_evidence_ref = "第12页"
    _, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, [], evidence_refs, evidence_level)

    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "evidence_index.json"
        write_evidence_index(out_path, [result])
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        assert payload[0]["agreement_status"] == "UNVERIFIED"
        explicit_ref = next(ref for ref in payload[0]["evidence_refs"] if ref["is_explicit"])
        assert explicit_ref["page_number"] == 12


def test_missing_lineage_is_missing_evidence() -> None:
    row = SpreadsheetRow(
        source_excel_path="",
        sheet_name="",
        row_index=0,
        column_names=[],
        raw_values={},
        metric_name="",
        period_values={},
    )
    issues, _, evidence_level = audit_evidence_presence(row, "")
    assert evidence_level == "MISSING_EVIDENCE"
    assert any(issue.code == "missing_evidence" for issue in issues)


def test_weak_evidence_is_counted_separately_in_manifest() -> None:
    manifest = build_manifest(
        decision="AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX",
        intake_result=type(
            "WorkbookLike",
            (),
            {"sheet_count": 1, "row_count_total": 1},
        )(),
        summary=type(
            "SummaryLike",
            (),
            {
                "row_count_audited": 1,
                "pass_count": 0,
                "review_count": 1,
                "fail_count": 0,
                "issue_count_total": 1,
                "unit_issue_count": 0,
                "period_issue_count": 0,
                "valuation_issue_count": 0,
                "evidence_issue_count": 1,
                "strong_evidence_count": 0,
                "weak_evidence_count": 1,
                "missing_evidence_count": 0,
                "not_applicable_evidence_count": 0,
                "weak_evidence_issue_count": 1,
                "missing_evidence_issue_count": 0,
                "strict_financial_table_row_count": 1,
                "market_reference_row_count": 0,
                "narrative_assertion_count": 0,
                "normalized_testset_record_row_count": 0,
                "testset_supporting_row_count": 0,
                "unknown_row_count": 0,
                "clean_data_row_count": 0,
                "review_queue_row_count": 1,
                "internal_clean_candidate_count": 0,
                "internal_reference_candidate_count": 0,
                "narrative_review_count": 0,
                "review_required_count": 1,
                "excluded_from_clean_data_count": 0,
            },
        )(),
        pdf_path="demo.pdf",
        excel_path="demo.xlsx",
        output_dir="demo_out",
    )
    assert manifest["weak_evidence_count"] == 1
    assert manifest["missing_evidence_count"] == 0
    assert manifest["weak_evidence_issue_count"] == 1


def test_period_checker_flags_missing_periods_on_financial_sheet() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="利润表",
        row_index=3,
        column_names=["指标", "值1", "值2"],
        raw_values={"指标": "营业收入", "值1": 1, "值2": 2},
        metric_name="营业收入",
        period_values={},
        row_type="STRICT_FINANCIAL_TABLE_ROW",
    )
    issues = audit_period_alignment(row)
    assert any(issue.code == "period_context_missing" for issue in issues)


def test_find_key_value_start_ignores_short_summary_rows_without_crashing() -> None:
    sheet_rows = [
        (1, ["一、报告基本信息"]),
        (2, ["核心盈利预测与估值（摘要版）"]),
        (3, []),
        (4, ["报告标题", "泰豪科技"]),
        (5, ["报告日期", "2026年05月23日"]),
        (6, ["投资评级", "买入"]),
    ]

    assert _find_key_value_start(sheet_rows) == 4


def test_should_reset_read_only_dimensions_flags_a1_only_dimension() -> None:
    class DummySheet:
        def calculate_dimension(self) -> str:
            return "A1:A1"

        def reset_dimensions(self) -> None:
            return None

    assert _should_reset_read_only_dimensions(DummySheet()) is True


def test_should_reset_read_only_dimensions_ignores_normal_dimension() -> None:
    class DummySheet:
        def calculate_dimension(self) -> str:
            return "A1:F15"

        def reset_dimensions(self) -> None:
            return None

    assert _should_reset_read_only_dimensions(DummySheet()) is False


def test_build_audit_decision_fail_on_error() -> None:
    issues = audit_unit_semantics(_make_row("营业收入(%)", unit_hint="%"))
    decision = build_audit_decision(issues)
    assert decision.decision == "FAIL"


def test_runner_helper_manifest_contains_zero_external_calls() -> None:
    manifest = build_manifest(
        decision="AI_EXCEL_INTAKE_AUDIT_348A_READY",
        intake_result=type(
            "WorkbookLike",
            (),
            {"sheet_count": 1, "row_count_total": 1},
        )(),
        summary=type(
            "SummaryLike",
            (),
            {
                "row_count_audited": 1,
                "pass_count": 1,
                "review_count": 0,
                "fail_count": 0,
                "issue_count_total": 0,
                "unit_issue_count": 0,
                "period_issue_count": 0,
                "valuation_issue_count": 0,
                "evidence_issue_count": 0,
                "strong_evidence_count": 1,
                "weak_evidence_count": 0,
                "missing_evidence_count": 0,
                "not_applicable_evidence_count": 0,
                "weak_evidence_issue_count": 0,
                "missing_evidence_issue_count": 0,
                "strict_financial_table_row_count": 1,
                "market_reference_row_count": 0,
                "narrative_assertion_count": 0,
                "normalized_testset_record_row_count": 0,
                "testset_supporting_row_count": 0,
                "unknown_row_count": 0,
                "clean_data_row_count": 1,
                "review_queue_row_count": 0,
                "internal_clean_candidate_count": 1,
                "internal_reference_candidate_count": 0,
                "narrative_review_count": 0,
                "review_required_count": 0,
                "excluded_from_clean_data_count": 0,
            },
        )(),
        pdf_path="demo.pdf",
        excel_path="demo.xlsx",
        output_dir="demo_out",
    )
    assert manifest["llm_api_call_count"] == 0
    assert manifest["mineru_run_count"] == 0
    assert manifest["ocr_run_count"] == 0
    assert manifest["client_ready"] is False
    assert manifest["production_ready"] is False
    assert manifest["formal_client_export_allowed"] is False


def _guardrail_clean_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "sheet_name": "利润表",
        "row_index": "2",
        "metric_name": "营业收入",
        "clean_candidate_type": "INTERNAL_CLEAN_CANDIDATE",
        "row_type": "STRICT_FINANCIAL_TABLE_ROW",
        "evidence_level": "WEAK_EVIDENCE",
        "issue_codes": "",
        "unit_hint": "百万元",
        "period_labels": "2025A",
        "period_values_json": '{"2025A": 1}',
    }
    row.update(overrides)
    return row


def _guardrail_review_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "sheet_name": "README",
        "row_index": "2",
        "metric_name": "生成时间",
        "decision": "REVIEW",
        "clean_candidate_type": "REVIEW_REQUIRED",
        "issue_count": "1",
        "issue_codes": "weak_evidence",
        "evidence_level": "WEAK_EVIDENCE",
        "row_type": "TESTSET_SUPPORTING_ROW",
        "unit_hint": "",
        "period_labels": "",
        "explicit_evidence_ref": "",
    }
    row.update(overrides)
    return row


def _guardrail_manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "clean_data_row_count": 1,
        "clean_data_csv_row_count": 1,
        "review_queue_row_count": 99,
        "review_queue_csv_row_count": 1,
        "unknown_row_count": 0,
        "client_ready": False,
        "production_ready": False,
        "formal_client_export_allowed": False,
        "demo_export_only": True,
        "llm_api_call_count": 0,
        "mineru_run_count": 0,
        "ocr_run_count": 0,
        "legacy_datefac_touched": False,
        "legacy_outputs_touched": False,
    }
    manifest.update(overrides)
    return manifest


def test_output_schema_guardrails_valid_outputs_pass() -> None:
    validate_outputs(
        [_guardrail_clean_row()],
        [_guardrail_review_row()],
        _guardrail_manifest(),
    )


@pytest.mark.parametrize(
    "row_type",
    [
        "TESTSET_SUPPORTING_ROW",
        "NORMALIZED_TESTSET_RECORD_ROW",
        "MARKET_REFERENCE_ROW",
        "UNKNOWN_ROW",
    ],
)
def test_output_schema_guardrails_forbidden_clean_row_type_raises(row_type: str) -> None:
    with pytest.raises(OutputSchemaGuardrailError, match="forbidden row_type"):
        validate_outputs(
            [_guardrail_clean_row(row_type=row_type)],
            [_guardrail_review_row()],
            _guardrail_manifest(),
        )


def test_output_schema_guardrails_invalid_clean_candidate_type_raises() -> None:
    with pytest.raises(OutputSchemaGuardrailError, match="clean_candidate_type"):
        validate_outputs(
            [_guardrail_clean_row(clean_candidate_type="REVIEW_REQUIRED")],
            [_guardrail_review_row()],
            _guardrail_manifest(),
        )


def test_output_schema_guardrails_clean_data_count_mismatch_raises() -> None:
    with pytest.raises(OutputSchemaGuardrailError, match="clean_data count mismatch"):
        validate_outputs(
            [_guardrail_clean_row()],
            [_guardrail_review_row()],
            _guardrail_manifest(clean_data_row_count=0, clean_data_csv_row_count=0),
        )


def test_output_schema_guardrails_clean_data_csv_count_mismatch_raises() -> None:
    # R6B-QA found this exact gap: clean_data_row_count was correct, but the
    # additive physical CSV count field could diverge without failing.
    with pytest.raises(OutputSchemaGuardrailError, match="clean_data_csv_row_count"):
        validate_outputs(
            [_guardrail_clean_row()],
            [_guardrail_review_row()],
            _guardrail_manifest(clean_data_row_count=1, clean_data_csv_row_count=999),
        )


def test_output_schema_guardrails_review_queue_count_mismatch_raises() -> None:
    with pytest.raises(OutputSchemaGuardrailError, match="review_queue count mismatch"):
        validate_outputs(
            [_guardrail_clean_row()],
            [_guardrail_review_row()],
            _guardrail_manifest(review_queue_csv_row_count=0),
        )


@pytest.mark.parametrize("field", ["decision", "clean_candidate_type", "evidence_level"])
def test_output_schema_guardrails_empty_review_queue_required_field_raises(field: str) -> None:
    with pytest.raises(OutputSchemaGuardrailError, match=field):
        validate_outputs(
            [_guardrail_clean_row()],
            [_guardrail_review_row(**{field: ""})],
            _guardrail_manifest(),
        )


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("client_ready", True),
        ("production_ready", True),
        ("formal_client_export_allowed", True),
        ("demo_export_only", False),
    ],
)
def test_output_schema_guardrails_open_manifest_gate_raises(field: str, bad_value: bool) -> None:
    with pytest.raises(OutputSchemaGuardrailError, match=field):
        validate_outputs(
            [_guardrail_clean_row()],
            [_guardrail_review_row()],
            _guardrail_manifest(**{field: bad_value}),
        )


@pytest.mark.parametrize("field", ["llm_api_call_count", "mineru_run_count", "ocr_run_count"])
def test_output_schema_guardrails_nonzero_external_counter_raises(field: str) -> None:
    with pytest.raises(OutputSchemaGuardrailError, match=field):
        validate_outputs(
            [_guardrail_clean_row()],
            [_guardrail_review_row()],
            _guardrail_manifest(**{field: 1}),
        )


def test_output_schema_guardrails_legacy_touched_flag_raises() -> None:
    with pytest.raises(OutputSchemaGuardrailError, match="legacy_datefac_touched"):
        validate_outputs(
            [_guardrail_clean_row()],
            [_guardrail_review_row()],
            _guardrail_manifest(legacy_datefac_touched=True),
        )


def test_unit_semantic_fixture_cases() -> None:
    fixture = _load_fixture("unit_semantics__346b_lessons_and_348s_r2__v1.json")

    for case in fixture["cases"]:
        row = _row_from_fixture(case["row"])
        issues = audit_unit_semantics(row)
        issue_codes = {issue.code for issue in issues}
        expected = set(case["expected_issue_codes"])
        assert issue_codes == expected, case["case_id"]


def test_period_detection_fixture_cases() -> None:
    fixture = _load_fixture("period_detection__embedded_headers_and_missing_period__v1.json")

    for case in fixture["cases"]:
        detected = detect_period_labels(case["column_names"])
        assert detected == case["expected_detected_periods"], case["case_id"]

        if case.get("row"):
            row = _row_from_fixture(case["row"])
            issues = audit_period_alignment(row)
            issue_codes = {issue.code for issue in issues}
            expected = set(case["expected_issue_codes"])
            assert issue_codes == expected, case["case_id"]


def test_clean_candidate_routing_fixture_cases() -> None:
    fixture = _load_fixture("routing_policy__narrative_market_strict_and_missing_evidence__v1.json")

    for case in fixture["cases"]:
        result = _run_routing_fixture_case(case)
        queue_rows = build_review_queue_rows([result])

        expected_clean_candidate_type = case["expected_clean_candidate_type"]
        expected_review_queue_candidate_types = case["expected_review_queue_candidate_types"]
        if case["case_id"] == "market_reference_row__becomes_internal_reference_candidate":
            expected_clean_candidate_type = "REVIEW_REQUIRED"
            expected_review_queue_candidate_types = ["REVIEW_REQUIRED"]

        assert result.clean_candidate_type == expected_clean_candidate_type, case["case_id"]
        assert result.evidence_level == case["expected_evidence_level"], case["case_id"]
        assert result.decision is not None
        assert result.decision.decision == case["expected_decision"], case["case_id"]
        assert [row["clean_candidate_type"] for row in queue_rows] == expected_review_queue_candidate_types, case["case_id"]
