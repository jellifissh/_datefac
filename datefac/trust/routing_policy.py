from __future__ import annotations

from typing import Any, Dict, Iterable, List

from datefac.trust.risk_registry import derive_risk_buckets


ROUTING_TRUSTED = "TRUSTED"
ROUTING_REVIEW_REQUIRED = "REVIEW_REQUIRED"
ROUTING_REJECTED = "REJECTED"
ROUTING_NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
ROUTING_OUT_OF_SCOPE = "OUT_OF_SCOPE"


def confidence_level_from_score(score: Any) -> str:
    try:
        numeric = float(score)
    except Exception:
        return "UNKNOWN"
    if numeric >= 85:
        return "HIGH"
    if numeric >= 60:
        return "MEDIUM"
    if numeric >= 0:
        return "LOW"
    return "UNKNOWN"


def route_trust_record(
    confidence_score: Any,
    risk_flags: Iterable[Any],
    *,
    blocking_policy: str = "review",
    low_score_policy: str = "needs_more_info",
) -> Dict[str, Any]:
    try:
        score = float(confidence_score)
    except Exception:
        score = 0.0

    buckets = derive_risk_buckets(risk_flags)
    blocking = buckets["blocking_risks"]
    warnings = buckets["warning_risks"]
    reasons: List[str] = []

    if blocking:
        decision = ROUTING_REJECTED if str(blocking_policy).strip().lower() == "reject" else ROUTING_REVIEW_REQUIRED
        reasons.append(f"blocking_risks_present:{','.join(blocking)}")
        next_action = (
            "Resolve blocking risks before any trust promotion."
            if decision == ROUTING_REJECTED
            else "Escalate for deterministic review because blocking risks are present."
        )
    elif score >= 85:
        decision = ROUTING_TRUSTED
        reasons.append(f"confidence_score_high:{score:.2f}")
        next_action = "Eligible for trusted routing under current policy."
    elif score >= 60:
        decision = ROUTING_REVIEW_REQUIRED
        reasons.append(f"confidence_score_medium:{score:.2f}")
        if warnings:
            reasons.append(f"warning_risks_present:{','.join(warnings)}")
        next_action = "Review before trust promotion."
    else:
        decision = ROUTING_REJECTED if str(low_score_policy).strip().lower() == "reject" else ROUTING_NEEDS_MORE_INFO
        reasons.append(f"confidence_score_low:{score:.2f}")
        next_action = (
            "Reject under current low-score policy."
            if decision == ROUTING_REJECTED
            else "Collect more evidence before making a trust decision."
        )

    return {
        "routing_decision": decision,
        "decision_reasons": reasons,
        "next_action": next_action,
        "blocking_risks": blocking,
        "warning_risks": warnings,
        "confidence_level": confidence_level_from_score(score),
        "confidence_score": max(0.0, min(100.0, score)),
    }


def routing_policy_smoke_cases() -> List[Dict[str, Any]]:
    cases = [
        {
            "case_id": "trusted_high_confidence",
            "input": {"confidence_score": 92, "risk_flags": []},
            "policy": {"blocking_policy": "review", "low_score_policy": "needs_more_info"},
            "expected_decision": ROUTING_TRUSTED,
        },
        {
            "case_id": "review_warning_only",
            "input": {"confidence_score": 71, "risk_flags": ["LOW_EVIDENCE_STRENGTH", "LONG_NARRATIVE_LABEL"]},
            "policy": {"blocking_policy": "review", "low_score_policy": "needs_more_info"},
            "expected_decision": ROUTING_REVIEW_REQUIRED,
        },
        {
            "case_id": "rejected_blocking_risk",
            "input": {"confidence_score": 54, "risk_flags": ["OFFICIAL_RULE_CONFLICT"]},
            "policy": {"blocking_policy": "reject", "low_score_policy": "reject"},
            "expected_decision": ROUTING_REJECTED,
        },
    ]
    results: List[Dict[str, Any]] = []
    for case in cases:
        routed = route_trust_record(
            case["input"]["confidence_score"],
            case["input"]["risk_flags"],
            blocking_policy=case["policy"]["blocking_policy"],
            low_score_policy=case["policy"]["low_score_policy"],
        )
        results.append(
            {
                "case_id": case["case_id"],
                "expected_decision": case["expected_decision"],
                "actual_decision": routed["routing_decision"],
                "passed": routed["routing_decision"] == case["expected_decision"],
                "decision_reasons": routed["decision_reasons"],
            }
        )
    return results
