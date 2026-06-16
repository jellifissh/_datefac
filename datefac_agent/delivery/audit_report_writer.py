"""Audit report writing for the 348A pilot."""

from __future__ import annotations

from pathlib import Path

from datefac_agent.schemas.audit_models import AuditRowResult, AuditSummary, WorkbookIntakeResult


def _top_issue_lines(row_results: list[AuditRowResult], limit: int = 10) -> list[str]:
    lines: list[str] = []
    for result in row_results:
        for issue in result.issues:
            lines.append(
                f"- `{result.row.sheet_name}:{result.row.row_index}` `{result.row.metric_name}` `{issue.code}`: {issue.message}"
            )
            if len(lines) >= limit:
                return lines
    return lines


def write_audit_report(
    output_path: str | Path,
    intake_result: WorkbookIntakeResult,
    summary: AuditSummary,
    row_results: list[AuditRowResult],
    pdf_path: str,
    excel_path: str,
    decision: str,
) -> None:
    """Write a concise Markdown audit report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 348A Excel Intake Audit Report",
        "",
        "## Scope",
        "",
        f"- decision: `{decision}`",
        f"- source_pdf_path: `{pdf_path}`",
        f"- source_excel_path: `{excel_path}`",
        f"- sheet_count: `{intake_result.sheet_count}`",
        f"- row_count_total: `{intake_result.row_count_total}`",
        "",
        "## Summary",
        "",
        f"- row_count_audited: `{summary.row_count_audited}`",
        f"- pass_count: `{summary.pass_count}`",
        f"- review_count: `{summary.review_count}`",
        f"- fail_count: `{summary.fail_count}`",
        f"- issue_count_total: `{summary.issue_count_total}`",
        f"- unit_issue_count: `{summary.unit_issue_count}`",
        f"- period_issue_count: `{summary.period_issue_count}`",
        f"- valuation_issue_count: `{summary.valuation_issue_count}`",
        f"- evidence_issue_count: `{summary.evidence_issue_count}`",
        f"- strong_evidence_count: `{summary.strong_evidence_count}`",
        f"- weak_evidence_count: `{summary.weak_evidence_count}`",
        f"- missing_evidence_count: `{summary.missing_evidence_count}`",
        f"- not_applicable_evidence_count: `{summary.not_applicable_evidence_count}`",
        f"- weak_evidence_issue_count: `{summary.weak_evidence_issue_count}`",
        f"- missing_evidence_issue_count: `{summary.missing_evidence_issue_count}`",
        "",
        "## Boundary",
        "",
        "- This pilot audited an already extracted Excel workbook.",
        "- No PDF re-extraction, MinerU, OCR, or LLM/VLM API call was used.",
        "- This output is review-oriented evidence, not client or production delivery.",
        "- Weak workbook lineage is separated from true missing evidence in this R1 run.",
        "",
        "## Sample Issues",
        "",
    ]
    lines.extend(_top_issue_lines(row_results) or ["- No issues detected."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
