"""Internal clean-data candidate policy for the 348A pilot."""

from __future__ import annotations

from datefac_agent.schemas.audit_models import AuditIssue, AuditRowResult, CleanCandidateType

# R7S: generic strict-table scaffolding labels. These metric names name a block /
# column header or a comparison axis rather than a financial metric. They are
# structural signals only; the period_values shape check below is the primary
# discriminator so normal numeric fact rows are never blocked by label alone.
STRICT_TABLE_SCAFFOLDING_METRIC_LABELS = frozenset(
    {
        "市场数据",
        "厂商",
        "对比维度",
        "订单日期",
        "项目",
        "指标",
    }
)


def _has_error_issue(issues: list[AuditIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)


def _has_category_issue(issues: list[AuditIssue], category: str) -> bool:
    return any(issue.category == category for issue in issues)


def _is_numeric_value(value: object) -> bool:
    """Return True when a period value carries a numeric fact.

    bool is rejected explicitly: although bool is an int subclass in Python, a
    bare True/False is not a financial fact. int/float and numeric strings such
    as "4356" or "-991.03" count; everything else (None, "", "数值", "型号") does
    not.
    """

    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        try:
            float(text)
        except ValueError:
            return False
        return True
    return False


def _period_values_carry_no_numeric_fact(result: AuditRowResult) -> bool:
    """Return True when no period value carries a numeric fact.

    An empty period_values dict is treated as no numeric fact: a strict-table
    row with no period values at all is not a stable financial fact and should
    not become a clean candidate on weak evidence.
    """

    period_values = result.row.period_values
    if not period_values:
        return True
    return not any(_is_numeric_value(value) for value in period_values.values())


def _period_values_echo_period_labels(result: AuditRowResult) -> bool:
    """Return True when every period value merely echoes its own period label.

    Example: {"2025A": "2025A", "2026E": "2026E"} for a row whose metric is a
    block header like 项目 / 指标. These rows carry no fact content; the value
    cells just repeat the column headers.
    """

    period_values = result.row.period_values
    if not period_values:
        return False
    return all(str(value).strip() == str(label).strip() for label, value in period_values.items())


def _looks_like_strict_table_scaffolding(result: AuditRowResult) -> bool:
    """Deterministic pseudo-header / comparison-dimension detector.

    A STRICT_FINANCIAL_TABLE_ROW on WEAK_EVIDENCE is treated as scaffolding
    when it carries no numeric fact content. The primary signal is period_values
    shape: if no period value is numeric, or every value merely echoes its
    period label, the row is structure, not a fact. The metric-label set is a
    secondary reinforcing signal only; it never blocks a row whose period_values
    are numeric.
    """

    if _period_values_carry_no_numeric_fact(result):
        return True
    if _period_values_echo_period_labels(result):
        return True
    metric_text = result.row.metric_name.strip()
    if metric_text in STRICT_TABLE_SCAFFOLDING_METRIC_LABELS and _period_values_carry_no_numeric_fact(result):
        return True
    return False


def classify_clean_candidate(result: AuditRowResult) -> CleanCandidateType:
    """Assign an internal-only clean candidate classification."""

    if _has_error_issue(result.issues):
        return "EXCLUDED_FROM_CLEAN_DATA"

    if result.evidence_level == "MISSING_EVIDENCE":
        return "EXCLUDED_FROM_CLEAN_DATA"

    if result.row_type == "NARRATIVE_ASSERTION":
        return "NARRATIVE_REVIEW"

    if result.row_type == "NORMALIZED_TESTSET_RECORD_ROW":
        return "REVIEW_REQUIRED"

    if result.row_type == "TESTSET_SUPPORTING_ROW":
        return "REVIEW_REQUIRED"

    if result.evidence_level != "WEAK_EVIDENCE":
        return "REVIEW_REQUIRED"

    if result.row_type == "STRICT_FINANCIAL_TABLE_ROW":
        if _has_category_issue(result.issues, "unit"):
            return "REVIEW_REQUIRED"
        if _has_category_issue(result.issues, "period"):
            return "REVIEW_REQUIRED"
        if _has_category_issue(result.issues, "valuation"):
            return "REVIEW_REQUIRED"
        if _looks_like_strict_table_scaffolding(result):
            return "REVIEW_REQUIRED"
        return "INTERNAL_CLEAN_CANDIDATE"

    if result.row_type == "MARKET_REFERENCE_ROW":
        return "REVIEW_REQUIRED"

    return "REVIEW_REQUIRED"
