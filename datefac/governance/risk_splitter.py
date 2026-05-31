from __future__ import annotations

from typing import Dict, Iterable, List, Set

from datefac.domain.metric_candidate import MetricCandidate


GENERIC_OTHER_METRICS = {"other_operating_cf"}
STRICT_REJECT_TAGS = {
    "NOISE_LEAK_BBOX_HTML",
    "INVALID_YEAR",
}
STRICT_REVIEW_TAGS = {
    "NUMERIC_COUNT_MISMATCH",
    "VALUE_CONFLICT",
    "ROW_REPAIR_AMBIGUOUS",
    "LOW_CONFIDENCE",
    "UNKNOWN_METRIC_CODE",
    "UNIT_UNKNOWN",
    "YEAR_MISSING",
    "VALUE_MISSING",
}


def split_candidates_for_sandbox_preview(
    candidates: Iterable[MetricCandidate],
    smoke_passed_candidate_source_ids: Set[str],
) -> Dict[str, List[MetricCandidate]]:
    trusted: List[MetricCandidate] = []
    review_required: List[MetricCandidate] = []
    rejected: List[MetricCandidate] = []

    for c in candidates:
        tags = set(c.risk_tags)
        src_id = str(c.provenance_json.get("source_candidate_row_id", ""))

        if any(t in tags for t in STRICT_REJECT_TAGS):
            c.split_decision = "rejected_preview"
            c.split_reason = "STRICT_REJECT_TAG"
            rejected.append(c)
            continue

        if c.metric_code in GENERIC_OTHER_METRICS:
            c.split_decision = "review_required_preview"
            c.split_reason = "GENERIC_OTHER_METRIC"
            review_required.append(c)
            continue

        if c.normalized_value is None:
            c.split_decision = "rejected_preview"
            c.split_reason = "VALUE_MISSING_OR_INVALID"
            rejected.append(c)
            continue

        repaired_like = ("ROW_REPAIRED_CONTINUATION" in tags) or ("ROW_REPAIRED_VALUES_BEFORE_LABEL" in tags)
        if repaired_like and (c.confidence < 0.90 or src_id not in smoke_passed_candidate_source_ids):
            c.split_decision = "review_required_preview"
            c.split_reason = "REPAIRED_ROW_NOT_SMOKE_PROVEN"
            review_required.append(c)
            continue

        if any(t in tags for t in STRICT_REVIEW_TAGS):
            c.split_decision = "review_required_preview"
            c.split_reason = "HAS_REVIEW_RISK_TAG"
            review_required.append(c)
            continue

        if c.confidence < 0.80:
            c.split_decision = "review_required_preview"
            c.split_reason = "LOW_CONFIDENCE_GATE"
            review_required.append(c)
            continue

        c.split_decision = "trusted_preview"
        c.split_reason = "PASS_STRICT_SANDBOX_GATES"
        trusted.append(c)

    return {
        "trusted_preview": trusted,
        "review_required_preview": review_required,
        "rejected_preview": rejected,
    }
