"""Focused tests for the 348A Excel intake audit pilot."""

from __future__ import annotations

from datefac_agent.audit.evidence_checker import audit_evidence_presence
from datefac_agent.audit.period_alignment_checker import audit_period_alignment, detect_period_labels
from datefac_agent.audit.unit_semantic_checker import audit_unit_semantics
from datefac_agent.audit.valuation_metric_checker import classify_valuation_metric
from datefac_agent.review.clean_candidate_policy import classify_clean_candidate
from datefac_agent.review.review_queue_builder import build_audit_decision, build_row_audit_result, build_review_queue_rows
from datefac_agent.schemas.audit_models import AuditIssue, AuditRowResult, SpreadsheetRow
from tools.run_agent_excel_intake_audit_348a import build_manifest


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


def test_unit_checker_still_flags_monetary_metrics_with_percent_units() -> None:
    revenue_issues = audit_unit_semantics(_make_row("营业收入(%)", unit_hint="%"))
    assert any(issue.code == "monetary_unit_mismatch" for issue in revenue_issues)

    asset_issues = audit_unit_semantics(_make_row("资产总计(%)", unit_hint="%"))
    assert any(issue.code == "monetary_unit_mismatch" for issue in asset_issues)


def test_period_checker_detects_expected_labels() -> None:
    labels = detect_period_labels(["会计年度", "2024A", "2025E", "2026Q1"])
    assert labels == ["2024A", "2025E", "2026Q1"]


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
