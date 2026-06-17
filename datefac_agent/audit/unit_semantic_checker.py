"""Minimal unit semantic checks for the 348A pilot."""

from __future__ import annotations

from datefac_agent.schemas.audit_models import AuditIssue, SpreadsheetRow

PERCENT_TERMS = (
    "%",
    "yoy",
    "\u540c\u6bd4",
    "\u589e\u957f\u7387",
    "\u589e\u901f",
    "\u6536\u76ca\u7387",
    "\u56de\u62a5\u7387",
    "\u6bdb\u5229\u7387",
    "\u51c0\u5229\u7387",
    "\u5229\u6da6\u7387",
    "roe",
    "roa",
)
RATE_OVERRIDE_TERMS = (
    "\u8d44\u4ea7\u8d1f\u503a\u7387",
    "\u8d1f\u503a\u7387",
)
VALUATION_TERMS = ("p/e", "pe", "\u5e02\u76c8\u7387", "p/b", "pb", "\u5e02\u51c0\u7387", "ev/ebitda", "ev ebitda")
PER_SHARE_TERMS = ("eps", "\u6bcf\u80a1", "\u5143/\u80a1")
MONEY_TERMS = (
    "\u8425\u4e1a\u6536\u5165",
    "\u6536\u5165",
    "\u51c0\u5229\u6da6",
    "\u5229\u6da6",
    "\u8d44\u4ea7",
    "\u8d1f\u503a",
    "\u73b0\u91d1",
    "\u8d39\u7528",
    "\u6210\u672c",
    "\u5e02\u503c",
    "\u767e\u4e07\u5143",
    "\u4ebf\u5143",
)
MULTIPLE_TERMS = ("\u500d",)
IMPLICIT_PERCENT_METRICS = (
    "\u540c\u6bd4\u589e\u901f",
    "\u6bdb\u5229\u7387",
    "\u7efc\u5408\u6bdb\u5229\u7387",
    "\u51c0\u5229\u6da6\u589e\u901f",
)
IMPLICIT_PERCENT_SHEETS = {"\u5206\u4e1a\u52a1\u76c8\u5229\u9884\u6d4b\u660e\u7ec6"}


def _normalize_metric_text(row: SpreadsheetRow) -> str:
    return f"{row.metric_name} {row.unit_hint or ''}".strip().lower()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _is_supported_implicit_percent_row(row: SpreadsheetRow, normalized: str) -> bool:
    if row.sheet_name not in IMPLICIT_PERCENT_SHEETS:
        return False
    if not row.period_values:
        return False
    return _contains_any(normalized, IMPLICIT_PERCENT_METRICS)


def _is_clear_rate_metric(text: str) -> bool:
    """Return True when the metric is semantically a rate/percentage concept."""

    rate_terms = (
        "yoy",
        "\u540c\u6bd4",
        "\u589e\u957f\u7387",
        "\u589e\u901f",
        "\u6536\u76ca\u7387",
        "\u51c0\u8d44\u4ea7\u6536\u76ca\u7387",
        "\u8d44\u4ea7\u6536\u76ca\u7387",
        "\u56de\u62a5\u7387",
        "\u6bdb\u5229\u7387",
        "\u51c0\u5229\u7387",
        "\u5229\u6da6\u7387",
        "roe",
        "roa",
    )
    return _contains_any(text, RATE_OVERRIDE_TERMS + rate_terms)


def audit_unit_semantics(row: SpreadsheetRow) -> list[AuditIssue]:
    """Flag obvious unit mismatches with conservative heuristics."""

    normalized = _normalize_metric_text(row)
    issues: list[AuditIssue] = []

    is_valuation = _contains_any(normalized, VALUATION_TERMS)
    is_per_share = _contains_any(normalized, PER_SHARE_TERMS)
    is_percent = _contains_any(normalized, PERCENT_TERMS)
    is_monetary = _contains_any(normalized, MONEY_TERMS)
    is_clear_rate_metric = _is_clear_rate_metric(normalized)
    is_supported_implicit_percent = _is_supported_implicit_percent_row(row, normalized)

    if is_valuation and (_contains_any(normalized, PERCENT_TERMS) or _contains_any(normalized, PER_SHARE_TERMS)):
        issues.append(
            AuditIssue(
                code="valuation_unit_mismatch",
                severity="error",
                category="unit",
                checker="unit_semantic_checker",
                message=f"Valuation metric '{row.metric_name}' looks mixed with percent or per-share units.",
            )
        )

    if is_per_share and (_contains_any(normalized, MULTIPLE_TERMS) or "\u767e\u4e07\u5143" in normalized or "\u4ebf\u5143" in normalized):
        issues.append(
            AuditIssue(
                code="per_share_unit_mismatch",
                severity="error",
                category="unit",
                checker="unit_semantic_checker",
                message=f"Per-share metric '{row.metric_name}' looks mixed with total-amount or multiple units.",
            )
        )

    if is_percent and "%" not in normalized:
        if is_supported_implicit_percent:
            issues.append(
                AuditIssue(
                    code="implicit_percentage_unit_confirmation_needed",
                    severity="warning",
                    category="unit",
                    checker="unit_semantic_checker",
                    message=f"Percentage-like metric '{row.metric_name}' is implicitly percentage-based and still requires review confirmation.",
                )
            )
        else:
            issues.append(
                AuditIssue(
                    code="percentage_unit_missing",
                    severity="warning",
                    category="unit",
                    checker="unit_semantic_checker",
                    message=f"Percentage-like metric '{row.metric_name}' is missing an explicit percent marker.",
                )
            )

    if is_monetary and ("%" in normalized or _contains_any(normalized, MULTIPLE_TERMS)) and not is_clear_rate_metric:
        issues.append(
            AuditIssue(
                code="monetary_unit_mismatch",
                severity="error",
                category="unit",
                checker="unit_semantic_checker",
                message=f"Monetary metric '{row.metric_name}' looks mixed with percent or multiple units.",
            )
        )

    return issues
