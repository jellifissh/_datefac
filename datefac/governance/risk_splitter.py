from __future__ import annotations

from typing import Dict, Iterable, List, Set

from datefac.domain.metric_candidate import MetricCandidate


GENERIC_OTHER_METRICS = {"other_operating_cf"}
STRICT_REJECT_TAGS = {"NOISE_LEAK_BBOX_HTML", "INVALID_YEAR"}
STRICT_REVIEW_TAGS = {
    "NUMERIC_COUNT_MISMATCH",
    "VALUE_CONFLICT",
    "YEAR_MISSING",
    "UNKNOWN_METRIC_CODE",
    "VALUE_MISSING",
}
UNUSUAL_NEGATIVE_METRICS = {
    "cash_beginning_balance",
    "cash_ending_balance",
}
UNITLESS_OR_RATIO_METRICS = {"roe", "gross_margin", "revenue_growth", "net_profit_growth", "debt_ratio", "pe", "pb", "ev_ebitda"}


def split_candidates_for_sandbox_preview(
    candidates: Iterable[MetricCandidate],
    smoke_passed_candidate_source_ids: Set[str],
) -> Dict[str, List[MetricCandidate]]:
    trusted: List[MetricCandidate] = []
    review_required: List[MetricCandidate] = []
    rejected: List[MetricCandidate] = []
    trust_audit: List[Dict[str, str]] = []

    for c in candidates:
        tags = set(c.risk_tags)
        src_id = str(c.provenance_json.get("source_candidate_row_id", ""))
        repaired_like = ("ROW_REPAIRED_CONTINUATION" in tags) or ("ROW_REPAIRED_VALUES_BEFORE_LABEL" in tags)
        smoke_ok = c.smoke_check_status == "PASSED" or src_id in smoke_passed_candidate_source_ids or ("SMOKE_VERIFIED_ROW" in tags)
        row_text_only = "ROW_TEXT_ONLY" in tags

        def _final(decision: str, reason: str) -> None:
            c.split_decision = decision
            c.split_reason = reason
            trust_audit.append(
                {
                    "candidate_id": c.candidate_id,
                    "metric_code": c.metric_code,
                    "year": c.year,
                    "confidence": f"{c.confidence:.3f}",
                    "year_source": c.year_source,
                    "unit_source": c.unit_source,
                    "smoke_check_status": c.smoke_check_status,
                    "decision": decision,
                    "reason": reason,
                    "risk_tags": "|".join(c.risk_tags),
                }
            )

        if any(t in tags for t in STRICT_REJECT_TAGS):
            _final("rejected_preview", "STRICT_REJECT_TAG")
            rejected.append(c)
            continue

        if c.normalized_value is None:
            _final("rejected_preview", "VALUE_MISSING_OR_INVALID")
            rejected.append(c)
            continue

        if c.metric_code in GENERIC_OTHER_METRICS and not smoke_ok:
            _final("review_required_preview", "GENERIC_OTHER_NOT_SMOKE_VERIFIED")
            review_required.append(c)
            continue

        if any(t in tags for t in STRICT_REVIEW_TAGS):
            _final("review_required_preview", "HAS_STRICT_REVIEW_TAG")
            review_required.append(c)
            continue

        if c.year_source == "INFERRED_SEQUENCE":
            _final("review_required_preview", "YEAR_SOURCE_INFERRED_SEQUENCE")
            review_required.append(c)
            continue

        if (c.metric_code not in UNITLESS_OR_RATIO_METRICS) and (not c.unit):
            _final("review_required_preview", "MONETARY_METRIC_UNIT_UNKNOWN")
            review_required.append(c)
            continue

        if c.metric_code in UNUSUAL_NEGATIVE_METRICS and c.normalized_value < 0:
            _final("review_required_preview", "UNUSUAL_NEGATIVE_VALUE")
            review_required.append(c)
            continue

        if c.confidence < 0.80:
            _final("review_required_preview", "LOW_CONFIDENCE_GATE")
            review_required.append(c)
            continue

        if repaired_like and not smoke_ok:
            _final("review_required_preview", "REPAIRED_ROW_NOT_SMOKE_VERIFIED")
            review_required.append(c)
            continue

        if repaired_like and smoke_ok and c.confidence < 0.80:
            _final("review_required_preview", "REPAIRED_LOW_CONFIDENCE")
            review_required.append(c)
            continue

        if ("SMOKE_CHECK_FAILED" in tags) and repaired_like:
            _final("review_required_preview", "REPAIRED_SMOKE_FAILED")
            review_required.append(c)
            continue

        # ROW_TEXT_ONLY no longer blocks when context complete.
        if row_text_only and smoke_ok and c.year_source in {"TABLE_HEADER", "SMOKE_CHECK_CONTEXT"}:
            _final("trusted_preview", "ROW_TEXT_ONLY_BUT_CONTEXT_COMPLETE")
            trusted.append(c)
            continue

        _final("trusted_preview", "PASS_CALIBRATED_TRUST_GATE")
        trusted.append(c)

    return {
        "trusted_preview": trusted,
        "review_required_preview": review_required,
        "rejected_preview": rejected,
        "trust_gate_audit_rows": trust_audit,
    }
