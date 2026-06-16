"""Valuation metric checks for the 348A pilot."""

from __future__ import annotations

from datefac_agent.schemas.audit_models import AuditIssue, SpreadsheetRow

VALUATION_LABELS = {
    "p/e": "PE",
    "pe": "PE",
    "市盈率": "PE",
    "p/b": "PB",
    "pb": "PB",
    "市净率": "PB",
    "ev/ebitda": "EV/EBITDA",
    "ev ebitda": "EV/EBITDA",
}


def classify_valuation_metric(metric_name: str) -> str | None:
    """Return the normalized valuation metric class when recognized."""

    normalized = metric_name.strip().lower()
    for label, canonical in VALUATION_LABELS.items():
        if label in normalized:
            return canonical
    return None


def audit_valuation_metrics(row: SpreadsheetRow) -> list[AuditIssue]:
    """Flag suspicious valuation metric semantics."""

    issues: list[AuditIssue] = []
    normalized = f"{row.metric_name} {row.unit_hint or ''}".strip().lower()
    classification = classify_valuation_metric(normalized)

    if not classification:
        if "倍" in normalized and "%" in normalized:
            issues.append(
                AuditIssue(
                    code="mixed_multiple_and_percentage",
                    severity="warning",
                    category="valuation",
                    checker="valuation_metric_checker",
                    message=f"Metric '{row.metric_name}' mixes multiple and percentage markers.",
                )
            )
        return issues

    if "%" in normalized or "元/股" in normalized or "百万元" in normalized or "亿元" in normalized:
        issues.append(
            AuditIssue(
                code="valuation_metric_unit_suspicious",
                severity="warning",
                category="valuation",
                checker="valuation_metric_checker",
                message=f"Valuation metric '{row.metric_name}' has a non-multiple unit marker.",
                metadata={"classification": classification},
            )
        )

    return issues
