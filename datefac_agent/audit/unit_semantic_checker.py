"""Minimal unit semantic checks for the 348A pilot."""

from __future__ import annotations

from datefac_agent.schemas.audit_models import AuditIssue, SpreadsheetRow

PERCENT_TERMS = ("%", "yoy", "同比", "毛利率", "净利率", "roe", "roa", "利润率")
VALUATION_TERMS = ("p/e", "pe", "市盈率", "p/b", "pb", "市净率", "ev/ebitda", "ev ebitda")
PER_SHARE_TERMS = ("eps", "每股", "元/股")
MONEY_TERMS = (
    "营业收入",
    "收入",
    "净利润",
    "利润",
    "资产",
    "负债",
    "现金",
    "费用",
    "成本",
    "市值",
    "百万元",
    "亿元",
)
MULTIPLE_TERMS = ("倍",)


def _normalize_metric_text(row: SpreadsheetRow) -> str:
    return f"{row.metric_name} {row.unit_hint or ''}".strip().lower()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def audit_unit_semantics(row: SpreadsheetRow) -> list[AuditIssue]:
    """Flag obvious unit mismatches with conservative heuristics."""

    normalized = _normalize_metric_text(row)
    issues: list[AuditIssue] = []

    is_valuation = _contains_any(normalized, VALUATION_TERMS)
    is_per_share = _contains_any(normalized, PER_SHARE_TERMS)
    is_percent = _contains_any(normalized, PERCENT_TERMS)
    is_monetary = _contains_any(normalized, MONEY_TERMS)

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

    if is_per_share and (_contains_any(normalized, MULTIPLE_TERMS) or "百万元" in normalized or "亿元" in normalized):
        issues.append(
            AuditIssue(
                code="per_share_unit_mismatch",
                severity="error",
                category="unit",
                checker="unit_semantic_checker",
                message=f"Per-share metric '{row.metric_name}' looks mixed with total-amount or multiple units.",
            )
        )

    if is_percent and not ("%" in normalized):
        issues.append(
            AuditIssue(
                code="percentage_unit_missing",
                severity="warning",
                category="unit",
                checker="unit_semantic_checker",
                message=f"Percentage-like metric '{row.metric_name}' is missing an explicit percent marker.",
            )
        )

    if is_monetary and ("%" in normalized or _contains_any(normalized, MULTIPLE_TERMS)):
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
