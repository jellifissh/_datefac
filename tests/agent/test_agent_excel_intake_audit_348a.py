"""Focused tests for the 348A Excel intake audit pilot."""

from __future__ import annotations

import json
from pathlib import Path

from datefac_agent.audit.evidence_checker import audit_evidence_presence
from datefac_agent.audit.period_alignment_checker import audit_period_alignment, detect_period_labels
from datefac_agent.audit.row_type_classifier import classify_row_type
from datefac_agent.audit.unit_semantic_checker import audit_unit_semantics
from datefac_agent.audit.valuation_metric_checker import classify_valuation_metric
from datefac_agent.intake.excel_intake import (
    _find_key_value_start,
    _refine_third_workbook_row_type,
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


def test_market_reference_weak_evidence_row_becomes_internal_reference_candidate() -> None:
    row = _make_row("总市值（亿元）", unit_hint="亿元")
    row.sheet_name = "市场与基础数据"
    row.row_type = "MARKET_REFERENCE_ROW"
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, evidence_issues, evidence_refs, evidence_level)
    assert result.clean_candidate_type == "INTERNAL_REFERENCE_CANDIDATE"


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


def test_explicit_evidence_ref_is_strong_evidence() -> None:
    row = _make_row("营业收入(百万元)")
    row.explicit_evidence_ref = "page=12"
    issues, _, evidence_level = audit_evidence_presence(row, "demo.pdf")
    assert evidence_level == "STRONG_EVIDENCE"
    assert issues == []


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

        assert result.clean_candidate_type == case["expected_clean_candidate_type"], case["case_id"]
        assert result.evidence_level == case["expected_evidence_level"], case["case_id"]
        assert result.decision is not None
        assert result.decision.decision == case["expected_decision"], case["case_id"]
        assert [row["clean_candidate_type"] for row in queue_rows] == case["expected_review_queue_candidate_types"], case["case_id"]
