"""Run the minimal 348A Excel intake audit pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac_agent.audit.evidence_checker import audit_evidence_presence
from datefac_agent.audit.period_alignment_checker import audit_period_alignment
from datefac_agent.audit.unit_semantic_checker import audit_unit_semantics
from datefac_agent.audit.valuation_metric_checker import audit_valuation_metrics
from datefac_agent.delivery.audit_report_writer import write_audit_report
from datefac_agent.delivery.evidence_index_writer import write_csv_rows, write_evidence_index
from datefac_agent.intake.excel_intake import read_excel_workbook
from datefac_agent.review.review_queue_builder import build_review_queue_rows, build_row_audit_result
from datefac_agent.schemas.audit_models import AuditRowResult, AuditSummary, SpreadsheetRow, WorkbookIntakeResult


def resolve_input_path(path_arg: str, suffix: str) -> Path:
    """Resolve an existing path, with a single-file fallback for Unicode shell issues."""

    candidate = Path(path_arg)
    if candidate.exists():
        return candidate

    input_dir = Path(r"D:\_datefac_agent\input")
    matches = sorted(path for path in input_dir.glob(f"*{suffix}") if path.exists())
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f"Unable to resolve input path: {path_arg}")


def _summarize_issues(row_results: list[AuditRowResult]) -> AuditSummary:
    summary = AuditSummary(row_count_audited=len(row_results))
    for result in row_results:
        if result.decision is None:
            continue
        if result.decision.decision == "PASS":
            summary.pass_count += 1
        elif result.decision.decision == "REVIEW":
            summary.review_count += 1
        elif result.decision.decision == "FAIL":
            summary.fail_count += 1

        if result.evidence_level == "STRONG_EVIDENCE":
            summary.strong_evidence_count += 1
        elif result.evidence_level == "WEAK_EVIDENCE":
            summary.weak_evidence_count += 1
        elif result.evidence_level == "MISSING_EVIDENCE":
            summary.missing_evidence_count += 1
        elif result.evidence_level == "NOT_APPLICABLE":
            summary.not_applicable_evidence_count += 1

        summary.issue_count_total += len(result.issues)
        for issue in result.issues:
            if issue.category == "unit":
                summary.unit_issue_count += 1
            elif issue.category == "period":
                summary.period_issue_count += 1
            elif issue.category == "valuation":
                summary.valuation_issue_count += 1
            elif issue.category == "evidence":
                summary.evidence_issue_count += 1
                if issue.code == "weak_evidence":
                    summary.weak_evidence_issue_count += 1
                elif issue.code == "missing_evidence":
                    summary.missing_evidence_issue_count += 1

    summary.clean_data_row_count = summary.pass_count
    summary.review_queue_row_count = summary.review_count + summary.fail_count
    return summary


def _row_to_clean_csv(row: SpreadsheetRow) -> dict[str, str]:
    return {
        "sheet_name": row.sheet_name,
        "row_index": str(row.row_index),
        "metric_name": row.metric_name,
        "unit_hint": row.unit_hint or "",
        "period_labels": ";".join(row.period_values.keys()),
        "period_values_json": json.dumps(row.period_values, ensure_ascii=False),
    }


def audit_workbook(pdf_path: str | Path, excel_path: str | Path) -> tuple[WorkbookIntakeResult, list[AuditRowResult], AuditSummary]:
    """Run the full 348A in-memory audit flow."""

    intake_result = read_excel_workbook(excel_path)
    row_results: list[AuditRowResult] = []

    for row in intake_result.rows:
        issues = []
        issues.extend(audit_unit_semantics(row))
        issues.extend(audit_period_alignment(row))
        issues.extend(audit_valuation_metrics(row))
        evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, pdf_path)
        issues.extend(evidence_issues)
        row_results.append(build_row_audit_result(row, issues, evidence_refs, evidence_level))

    summary = _summarize_issues(row_results)
    return intake_result, row_results, summary


def build_manifest(
    decision: str,
    intake_result: WorkbookIntakeResult,
    summary: AuditSummary,
    pdf_path: str,
    excel_path: str,
    output_dir: str,
) -> dict[str, Any]:
    """Build the 348A manifest payload."""

    return {
        "decision": decision,
        "input_stage": "AI_EXTRACTED_EXCEL_INTAKE_AUDIT_PILOT_348A",
        "qa_fail_count": summary.fail_count,
        "source_pdf_path": pdf_path,
        "source_excel_path": excel_path,
        "output_dir": output_dir,
        "sheet_count": intake_result.sheet_count,
        "row_count_total": intake_result.row_count_total,
        "row_count_audited": summary.row_count_audited,
        "pass_count": summary.pass_count,
        "review_count": summary.review_count,
        "fail_count": summary.fail_count,
        "issue_count_total": summary.issue_count_total,
        "unit_issue_count": summary.unit_issue_count,
        "period_issue_count": summary.period_issue_count,
        "valuation_issue_count": summary.valuation_issue_count,
        "evidence_issue_count": summary.evidence_issue_count,
        "strong_evidence_count": summary.strong_evidence_count,
        "weak_evidence_count": summary.weak_evidence_count,
        "missing_evidence_count": summary.missing_evidence_count,
        "not_applicable_evidence_count": summary.not_applicable_evidence_count,
        "weak_evidence_issue_count": summary.weak_evidence_issue_count,
        "missing_evidence_issue_count": summary.missing_evidence_issue_count,
        "clean_data_row_count": summary.clean_data_row_count,
        "review_queue_row_count": summary.review_queue_row_count,
        "llm_api_call_count": 0,
        "mineru_run_count": 0,
        "ocr_run_count": 0,
        "legacy_datefac_touched": False,
        "legacy_outputs_touched": False,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_export_generated": False,
        "demo_export_only": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "recommended_next_step": "348A-QA Excel Intake Audit Result Review",
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_pilot(pdf_path_arg: str, excel_path_arg: str, output_dir_arg: str) -> dict[str, Any]:
    """Execute the 348A pilot and return the manifest."""

    pdf_path = resolve_input_path(pdf_path_arg, ".pdf")
    excel_path = resolve_input_path(excel_path_arg, ".xlsx")
    output_dir = Path(output_dir_arg)
    output_dir.mkdir(parents=True, exist_ok=True)

    intake_result, row_results, summary = audit_workbook(pdf_path, excel_path)
    decision = "AI_EXCEL_INTAKE_AUDIT_348A_READY"
    if summary.fail_count > 0 or summary.review_count > 0:
        decision = "AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX"

    review_rows = build_review_queue_rows(row_results)
    clean_rows = [_row_to_clean_csv(result.row) for result in row_results if result.decision and result.decision.decision == "PASS"]

    write_audit_report(
        output_path=output_dir / "audit_report.md",
        intake_result=intake_result,
        summary=summary,
        row_results=row_results,
        pdf_path=str(pdf_path),
        excel_path=str(excel_path),
        decision=decision,
    )
    write_evidence_index(output_dir / "evidence_index.json", row_results)
    write_csv_rows(output_dir / "review_queue.csv", review_rows)
    write_csv_rows(output_dir / "clean_data.csv", clean_rows)

    manifest = build_manifest(
        decision=decision,
        intake_result=intake_result,
        summary=summary,
        pdf_path=str(pdf_path),
        excel_path=str(excel_path),
        output_dir=str(output_dir),
    )
    run_summary = {
        "decision": decision,
        "sheet_count": intake_result.sheet_count,
        "row_count_total": intake_result.row_count_total,
        "row_count_audited": summary.row_count_audited,
        "review_queue_row_count": summary.review_queue_row_count,
        "clean_data_row_count": summary.clean_data_row_count,
        "issue_count_total": summary.issue_count_total,
        "strong_evidence_count": summary.strong_evidence_count,
        "weak_evidence_count": summary.weak_evidence_count,
        "missing_evidence_count": summary.missing_evidence_count,
        "not_applicable_evidence_count": summary.not_applicable_evidence_count,
    }
    _write_json(output_dir / "agent_excel_intake_audit_348a_manifest.json", manifest)
    _write_json(output_dir / "agent_excel_intake_audit_348a_run_summary.json", run_summary)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the 348A Excel intake audit pilot.")
    parser.add_argument("--pdf-path", required=True)
    parser.add_argument("--excel-path", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    manifest = run_pilot(args.pdf_path, args.excel_path, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
