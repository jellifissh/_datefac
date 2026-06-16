"""Period and year alignment checks for the 348A pilot."""

from __future__ import annotations

import re

from datefac_agent.schemas.audit_models import AuditIssue, SpreadsheetRow

PERIOD_LABEL_RE = re.compile(r"^(?P<year>(?:19|20)\d{2})(?P<suffix>A|E|Q[1-4])?$", re.IGNORECASE)


def detect_period_labels(column_names: list[str]) -> list[str]:
    """Extract normalized period labels from header names."""

    labels: list[str] = []
    for name in column_names:
        text = str(name).strip()
        match = PERIOD_LABEL_RE.match(text)
        if match:
            suffix = (match.group("suffix") or "").upper()
            labels.append(f"{match.group('year')}{suffix}")
    return labels


def audit_period_alignment(row: SpreadsheetRow) -> list[AuditIssue]:
    """Flag missing or suspicious period structure for strict financial rows only."""

    issues: list[AuditIssue] = []
    if row.row_type != "STRICT_FINANCIAL_TABLE_ROW":
        return issues

    labels = detect_period_labels(list(row.period_values.keys()) or row.column_names)

    if not labels:
        issues.append(
            AuditIssue(
                code="period_context_missing",
                severity="warning",
                category="period",
                checker="period_alignment_checker",
                message=f"Financial row '{row.metric_name}' has no detected period labels.",
            )
        )
        return issues

    years: list[int] = []
    for label in labels:
        match = PERIOD_LABEL_RE.match(label)
        if match:
            years.append(int(match.group("year")))

    if years and years != sorted(years):
        issues.append(
            AuditIssue(
                code="period_order_suspicious",
                severity="warning",
                category="period",
                checker="period_alignment_checker",
                message=f"Detected period labels for '{row.metric_name}' are not in ascending order.",
            )
        )

    if len(labels) >= 2 and not row.period_values:
        issues.append(
            AuditIssue(
                code="period_values_missing",
                severity="warning",
                category="period",
                checker="period_alignment_checker",
                message=f"Financial row '{row.metric_name}' has detected period columns but no populated values.",
            )
        )

    return issues
