"""Focused tests for the 348A Excel intake audit pilot."""

from __future__ import annotations

import json
from pathlib import Path

from datefac_agent.audit.evidence_checker import audit_evidence_presence
from datefac_agent.audit.period_alignment_checker import audit_period_alignment, detect_period_labels
from datefac_agent.audit.unit_semantic_checker import audit_unit_semantics
from datefac_agent.audit.valuation_metric_checker import audit_valuation_metrics, classify_valuation_metric
from datefac_agent.review.review_queue_builder import build_audit_decision, build_row_audit_result, build_review_queue_rows
from datefac_agent.schemas.audit_models import SpreadsheetRow
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


def test_period_checker_detects_expected_labels() -> None:
    labels = detect_period_labels(["会计年度", "2024A", "2025E", "2026Q1"])
    assert labels == ["2024A", "2025E", "2026Q1"]


def test_valuation_checker_classifies_multiple_like_metrics() -> None:
    assert classify_valuation_metric("PE(倍)") == "PE"
    assert classify_valuation_metric("PB(倍)") == "PB"
    assert classify_valuation_metric("EV/EBITDA") == "EV/EBITDA"


def test_review_queue_returns_review_when_issues_exist() -> None:
    row = _make_row("YoY", unit_hint=None)
    issues = audit_unit_semantics(row)
    evidence_issues, evidence_refs = audit_evidence_presence(row, "demo.pdf")
    result = build_row_audit_result(row, issues + evidence_issues, evidence_refs)
    assert result.decision is not None
    assert result.decision.decision == "REVIEW"
    queue_rows = build_review_queue_rows([result])
    assert queue_rows[0]["decision"] == "REVIEW"


def test_runner_helper_manifest_contains_zero_external_calls() -> None:
    row = _make_row("营业收入(百万元)")
    result = build_row_audit_result(row, [], [])
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
                "clean_data_row_count": 1,
                "review_queue_row_count": 0,
            },
        )(),
        pdf_path="demo.pdf",
        excel_path="demo.xlsx",
        output_dir="demo_out",
    )
    assert manifest["llm_api_call_count"] == 0
    assert manifest["mineru_run_count"] == 0
    assert manifest["ocr_run_count"] == 0


def test_period_checker_flags_missing_periods_on_financial_sheet() -> None:
    row = SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="利润表",
        row_index=3,
        column_names=["指标", "值1", "值2"],
        raw_values={"指标": "营业收入", "值1": 1, "值2": 2},
        metric_name="营业收入",
        period_values={},
    )
    issues = audit_period_alignment(row)
    assert any(issue.code == "period_context_missing" for issue in issues)


def test_build_audit_decision_fail_on_error() -> None:
    issues = audit_unit_semantics(_make_row("营业收入(%)", unit_hint="%"))
    decision = build_audit_decision(issues)
    assert decision.decision == "FAIL"
