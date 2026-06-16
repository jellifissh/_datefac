"""Review queue helpers for the 348A pilot."""

from __future__ import annotations

from datefac_agent.schemas.audit_models import AuditDecision, AuditIssue, AuditRowResult, EvidenceLevel, SpreadsheetRow


def build_audit_decision(issues: list[AuditIssue]) -> AuditDecision:
    """Assign a conservative decision from row-level issues."""

    if any(issue.severity == "error" for issue in issues):
        decision = "FAIL"
    elif issues:
        decision = "REVIEW"
    else:
        decision = "PASS"
    return AuditDecision(
        decision=decision,
        reason_codes=[issue.code for issue in issues],
        issue_count=len(issues),
    )


def build_row_audit_result(
    row: SpreadsheetRow,
    issues: list[AuditIssue],
    evidence_refs: list,
    evidence_level: EvidenceLevel,
) -> AuditRowResult:
    """Bundle a row, issues, evidence, row type, and decision."""

    return AuditRowResult(
        row=row,
        issues=issues,
        evidence_refs=list(evidence_refs),
        evidence_level=evidence_level,
        row_type=row.row_type,
        decision=build_audit_decision(issues),
    )


def build_review_queue_rows(row_results: list[AuditRowResult]) -> list[dict[str, str]]:
    """Return delivery-ready review queue rows for REVIEW and FAIL decisions."""

    rows: list[dict[str, str]] = []
    for result in row_results:
        if result.decision is None or result.decision.decision == "PASS":
            continue
        rows.append(
            {
                "sheet_name": result.row.sheet_name,
                "row_index": str(result.row.row_index),
                "metric_name": result.row.metric_name,
                "decision": result.decision.decision,
                "issue_count": str(result.decision.issue_count),
                "issue_codes": ";".join(result.decision.reason_codes),
                "evidence_level": result.evidence_level,
                "row_type": result.row_type,
                "unit_hint": result.row.unit_hint or "",
                "period_labels": ";".join(result.row.period_values.keys()),
                "explicit_evidence_ref": result.row.explicit_evidence_ref or "",
            }
        )
    return rows
