from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping

from datefac.trust.risk_registry import (
    SEVERITY_BLOCKING,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    derive_risk_buckets,
    get_risk_definition,
    normalize_risk_flags,
)
from datefac.trust.routing_policy import confidence_level_from_score, route_trust_record


SCORING_MODEL_VERSION = "330B_v1"
SCORING_COMPONENTS = [
    "evidence_score",
    "semantic_score",
    "unit_year_score",
    "parser_agreement_score",
    "risk_penalty",
    "confidence_score",
    "confidence_level",
]

MAX_EVIDENCE_SCORE = 35
MAX_SEMANTIC_SCORE = 35
MAX_UNIT_YEAR_SCORE = 30
MAX_PARSER_AGREEMENT_SCORE = 20

SPECIAL_RISK_PENALTIES = {
    "ADJUSTED_METRIC_RISK": -35,
    "DILUTED_EPS_RISK": -35,
    "OFFICIAL_RULE_CONFLICT": -45,
    "VALUE_PARSE_FAILED": -40,
    "TARGET_METRIC_AMBIGUOUS": -30,
    "UNIT_CONFLICT": -30,
    "YEAR_MISMATCH": -30,
}


def _to_payload(record: Any) -> Dict[str, Any]:
    if isinstance(record, Mapping):
        return dict(record)
    if hasattr(record, "to_dict") and callable(record.to_dict):
        return dict(record.to_dict())
    if is_dataclass(record):
        return asdict(record)
    raise TypeError(f"Unsupported trust record payload: {type(record)!r}")


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _norm_text(value).lower()
    return text in {"1", "true", "yes", "y", "pass", "passed"}


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, round(float(value), 4)))


def _unit_resolved(unit: Any) -> bool:
    text = _norm_text(unit).lower()
    return bool(text) and text not in {"unknown", "unk", "n/a", "na", "none", "null"}


def _year_resolved(year: Any) -> bool:
    text = _norm_text(year).lower()
    return bool(text) and text not in {"unknown", "unk", "n/a", "na", "none", "null"}


def _value_parse_success(payload: Mapping[str, Any], risk_flags: Iterable[str]) -> bool:
    if _safe_bool(payload.get("value_parse_success")):
        return True
    if "VALUE_PARSE_FAILED" in set(risk_flags):
        return False
    value = payload.get("value")
    if value in ("", None):
        return False
    try:
        float(value)
        return True
    except Exception:
        return False


def _has_page_table_row_reference(payload: Mapping[str, Any], evidence_refs: List[str]) -> bool:
    if any(_norm_text(payload.get(key)) for key in ["source_page", "source_table", "source_row", "page_ref", "table_ref", "row_ref"]):
        return True
    haystacks = evidence_refs + [str(payload.get("provenance", ""))]
    return any(any(token in item.lower() for token in ["page", "table", "row"]) for item in haystacks if isinstance(item, str))


def _has_official_match_signal(payload: Mapping[str, Any]) -> bool:
    return any(
        _safe_bool(payload.get(key))
        for key in [
            "official_alias_match_signal",
            "official_rule_match_signal",
            "official_match_signal",
            "official_alias_match",
            "official_rule_match",
        ]
    )


def _semantic_target_unambiguous(payload: Mapping[str, Any], risk_flags: Iterable[str]) -> bool:
    if "TARGET_METRIC_AMBIGUOUS" in set(risk_flags):
        return False
    explicit = payload.get("semantic_target_unambiguous")
    if explicit not in ("", None):
        return _safe_bool(explicit)
    return bool(_norm_text(payload.get("normalized_metric")))


def _explicit_parser_agreement(payload: Mapping[str, Any]) -> bool:
    return any(
        _safe_bool(payload.get(key))
        for key in ["parser_agreement_signal", "explicit_parser_agreement", "parser_sources_agree"]
    )


def calculate_evidence_score(payload: Mapping[str, Any]) -> Dict[str, Any]:
    evidence_refs = [_norm_text(item) for item in _as_list(payload.get("evidence_refs")) if _norm_text(item)]
    score = 0
    reasons: List[str] = []
    if evidence_refs:
        score += 20
        reasons.append("source_evidence_present")
    if _has_page_table_row_reference(payload, evidence_refs):
        score += 10
        reasons.append("source_page_table_row_reference_present")
    if len(evidence_refs) >= 2:
        score += 5
        reasons.append("multiple_evidence_refs_present")
    return {
        "evidence_score": min(score, MAX_EVIDENCE_SCORE),
        "evidence_refs_count": len(evidence_refs),
        "evidence_reasons": reasons,
    }


def calculate_semantic_score(payload: Mapping[str, Any], risk_flags: Iterable[str]) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []
    if _norm_text(payload.get("normalized_metric")):
        score += 15
        reasons.append("normalized_metric_present")
    if _has_official_match_signal(payload):
        score += 10
        reasons.append("official_alias_or_rule_match_signal")
    if _semantic_target_unambiguous(payload, risk_flags):
        score += 10
        reasons.append("semantic_target_unambiguous")
    return {
        "semantic_score": min(score, MAX_SEMANTIC_SCORE),
        "semantic_reasons": reasons,
    }


def calculate_unit_year_score(payload: Mapping[str, Any], risk_flags: Iterable[str]) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []
    unit_ok = _unit_resolved(payload.get("unit"))
    year_ok = _year_resolved(payload.get("year"))
    value_ok = _value_parse_success(payload, risk_flags)
    if unit_ok:
        score += 10
    if year_ok:
        score += 10
    if value_ok:
        score += 10
    if unit_ok and year_ok:
        reasons.append("unit_year_resolved")
    if value_ok:
        reasons.append("value_parse_success")
    return {
        "unit_year_score": min(score, MAX_UNIT_YEAR_SCORE),
        "unit_year_reasons": reasons,
    }


def calculate_parser_agreement_score(payload: Mapping[str, Any]) -> Dict[str, Any]:
    parser_sources = [_norm_text(item) for item in _as_list(payload.get("parser_sources")) if _norm_text(item)]
    score = 0
    reasons: List[str] = []
    if len(parser_sources) == 1:
        score += 5
        reasons.append("single_parser_source_present")
    elif len(parser_sources) >= 2:
        score += 10
        reasons.append("multiple_parser_sources_present")
    if _explicit_parser_agreement(payload):
        score += 10
        reasons.append("parser_agreement_present")
    return {
        "parser_agreement_score": min(score, MAX_PARSER_AGREEMENT_SCORE),
        "parser_agreement_reasons": reasons,
        "parser_source_count": len(parser_sources),
    }


def calculate_risk_penalty(risk_flags: Iterable[str]) -> Dict[str, Any]:
    normalized = normalize_risk_flags(risk_flags)
    total = 0
    detail_rows: List[Dict[str, Any]] = []
    info_count = 0
    warning_count = 0
    blocking_count = 0
    for code in normalized:
        definition = get_risk_definition(code)
        if code in SPECIAL_RISK_PENALTIES:
            penalty = SPECIAL_RISK_PENALTIES[code]
        elif definition.severity == SEVERITY_BLOCKING:
            penalty = -30
        elif definition.severity == SEVERITY_WARNING:
            penalty = -8
        else:
            penalty = -2
        total += penalty
        if definition.severity == SEVERITY_BLOCKING:
            blocking_count += 1
        elif definition.severity == SEVERITY_WARNING:
            warning_count += 1
        elif definition.severity == SEVERITY_INFO:
            info_count += 1
        detail_rows.append(
            {
                "risk_code": code,
                "severity": definition.severity,
                "blocking": definition.blocking,
                "penalty": penalty,
            }
        )
    return {
        "risk_penalty": total,
        "risk_penalty_details": detail_rows,
        "info_risk_count": info_count,
        "warning_risk_count": warning_count,
        "blocking_risk_count": blocking_count,
    }


def calculate_confidence_score(payload: Mapping[str, Any]) -> Dict[str, Any]:
    normalized_risks = normalize_risk_flags(_as_list(payload.get("risk_flags")))
    evidence = calculate_evidence_score(payload)
    semantic = calculate_semantic_score(payload, normalized_risks)
    unit_year = calculate_unit_year_score(payload, normalized_risks)
    parser = calculate_parser_agreement_score(payload)
    penalties = calculate_risk_penalty(normalized_risks)
    raw_score = (
        float(evidence["evidence_score"])
        + float(semantic["semantic_score"])
        + float(unit_year["unit_year_score"])
        + float(parser["parser_agreement_score"])
        + float(penalties["risk_penalty"])
    )
    confidence_score = _clamp_score(raw_score)
    confidence_level = confidence_level_from_score(confidence_score)
    decision_reasons: List[str] = []
    for token in [
        "source_evidence_present",
        "normalized_metric_present",
        "unit_year_resolved",
        "parser_agreement_present",
    ]:
        if token in evidence["evidence_reasons"] or token in semantic["semantic_reasons"] or token in unit_year["unit_year_reasons"] or token in parser["parser_agreement_reasons"]:
            decision_reasons.append(token)
    if penalties["warning_risk_count"] > 0 or penalties["info_risk_count"] > 0:
        decision_reasons.append("warning_risk_penalty_applied")
    if penalties["blocking_risk_count"] > 0:
        decision_reasons.append("blocking_risk_penalty_applied")
    return {
        "risk_flags": normalized_risks,
        "evidence_score": evidence["evidence_score"],
        "semantic_score": semantic["semantic_score"],
        "unit_year_score": unit_year["unit_year_score"],
        "parser_agreement_score": parser["parser_agreement_score"],
        "risk_penalty": penalties["risk_penalty"],
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "decision_reasons_from_scoring": decision_reasons,
        "score_component_details": {
            **evidence,
            **semantic,
            **unit_year,
            **parser,
            **penalties,
            "scoring_model_version": SCORING_MODEL_VERSION,
        },
    }


def score_trust_record(
    record: Any,
    *,
    blocking_policy: str = "review",
    low_score_policy: str = "needs_more_info",
) -> Dict[str, Any]:
    payload = _to_payload(record)
    buckets = derive_risk_buckets(_as_list(payload.get("risk_flags")))
    scored = calculate_confidence_score({**payload, "risk_flags": buckets["risk_flags"]})
    routed = route_trust_record(
        scored["confidence_score"],
        buckets["risk_flags"],
        blocking_policy=blocking_policy,
        low_score_policy=low_score_policy,
    )
    decision_reasons = list(scored["decision_reasons_from_scoring"])
    for item in routed["decision_reasons"]:
        if item not in decision_reasons:
            decision_reasons.append(item)
    result = dict(payload)
    result.update(
        {
            "risk_flags": buckets["risk_flags"],
            "blocking_risks": buckets["blocking_risks"],
            "warning_risks": buckets["warning_risks"],
            "evidence_score": scored["evidence_score"],
            "semantic_score": scored["semantic_score"],
            "unit_year_score": scored["unit_year_score"],
            "parser_agreement_score": scored["parser_agreement_score"],
            "risk_penalty": scored["risk_penalty"],
            "confidence_score": scored["confidence_score"],
            "confidence_level": scored["confidence_level"],
            "routing_decision": routed["routing_decision"],
            "decision_reasons": decision_reasons,
            "next_action": routed["next_action"],
            "score_component_details": scored["score_component_details"],
            "scoring_model_version": SCORING_MODEL_VERSION,
            "routing_policy_reused": True,
        }
    )
    if "provenance" not in result or not isinstance(result.get("provenance"), dict):
        result["provenance"] = {}
    result["provenance"] = dict(result["provenance"])
    result["provenance"]["scoring_stage"] = "330B"
    result["provenance"]["scoring_model_version"] = SCORING_MODEL_VERSION
    return result


def scoring_model_summary() -> Dict[str, Any]:
    return {
        "scoring_model_version": SCORING_MODEL_VERSION,
        "scoring_model_component_count": len(SCORING_COMPONENTS),
        "scoring_components": list(SCORING_COMPONENTS),
        "special_risk_penalty_count": len(SPECIAL_RISK_PENALTIES),
        "special_risk_penalties": dict(SPECIAL_RISK_PENALTIES),
    }
