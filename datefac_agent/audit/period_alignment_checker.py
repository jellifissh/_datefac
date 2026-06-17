"""Period and year alignment checks for the 348A pilot."""

from __future__ import annotations

import re

from datefac_agent.schemas.audit_models import AuditIssue, SpreadsheetRow

PERIOD_LABEL_RE = re.compile(
    r"^(?:FY)?(?P<year>(?:19|20)\d{2})(?P<suffix>A|E|Q[1-4]|FY)?$|^(?P<year2>(?:19|20)\d{2})\s+Q(?P<quarter>[1-4])$",
    re.IGNORECASE,
)
EMBEDDED_PERIOD_LABEL_RE = re.compile(
    r"(?P<year2>(?:19|20)\d{2})\s+Q(?P<quarter>[1-4])|FY(?P<fy_year>(?:19|20)\d{2})|(?P<year>(?:19|20)\d{2})(?P<suffix>A|E|Q[1-4]|FY)?",
    re.IGNORECASE,
)


def _normalize_period_match(match: re.Match[str]) -> str | None:
    if match.group("year2") and match.group("quarter"):
        return f"{match.group('year2')}Q{match.group('quarter')}"

    if match.groupdict().get("fy_year"):
        return match.group("fy_year")

    year = match.groupdict().get("year")
    if not year:
        return None

    suffix = (match.groupdict().get("suffix") or "").upper()
    if suffix == "FY":
        suffix = ""
    return f"{year}{suffix}"


def detect_period_labels(column_names: list[str]) -> list[str]:
    """Extract normalized period labels from header names."""

    labels: list[str] = []
    for name in column_names:
        text = str(name).strip()
        for match in EMBEDDED_PERIOD_LABEL_RE.finditer(text):
            normalized = _normalize_period_match(match)
            if normalized:
                labels.append(normalized)
    deduped_labels: list[str] = []
    for label in labels:
        if label not in deduped_labels:
            deduped_labels.append(label)
    return deduped_labels


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
            normalized = _normalize_period_match(match)
            if normalized:
                years.append(int(normalized[:4]))

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
