"""Internal clean-data candidate policy for the 348A pilot."""

from __future__ import annotations

from datefac_agent.schemas.audit_models import AuditIssue, AuditRowResult, CleanCandidateType


def _has_error_issue(issues: list[AuditIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)


def _has_category_issue(issues: list[AuditIssue], category: str) -> bool:
    return any(issue.category == category for issue in issues)


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
        return "INTERNAL_CLEAN_CANDIDATE"

    if result.row_type == "MARKET_REFERENCE_ROW":
        if _has_category_issue(result.issues, "unit"):
            return "REVIEW_REQUIRED"
        return "INTERNAL_REFERENCE_CANDIDATE"

    return "REVIEW_REQUIRED"
