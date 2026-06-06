from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping

from datefac.trust.risk_registry import derive_risk_buckets, normalize_risk_flags
from datefac.trust.routing_policy import confidence_level_from_score, route_trust_record


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except Exception:
        numeric = default
    return max(0.0, min(100.0, numeric))


def derive_confidence_score(
    *,
    evidence_score: Any,
    semantic_score: Any,
    unit_year_score: Any,
    parser_agreement_score: Any,
    risk_penalty: Any,
) -> float:
    score = (
        _safe_float(evidence_score)
        + _safe_float(semantic_score)
        + _safe_float(unit_year_score)
        + _safe_float(parser_agreement_score)
    ) / 4.0 - _safe_float(risk_penalty)
    return max(0.0, min(100.0, round(score, 4)))


@dataclass(frozen=True)
class TrustRecord:
    candidate_id: str
    metric_label_raw: str
    normalized_metric: str
    value: Any
    unit: str
    year: str
    parser_sources: List[str]
    evidence_refs: List[str]
    risk_flags: List[str]
    blocking_risks: List[str]
    warning_risks: List[str]
    confidence_score: float
    confidence_level: str
    evidence_score: float
    semantic_score: float
    unit_year_score: float
    parser_agreement_score: float
    risk_penalty: float
    routing_decision: str
    decision_reasons: List[str]
    next_action: str
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        blocking_policy: str = "review",
        low_score_policy: str = "needs_more_info",
    ) -> "TrustRecord":
        risk_flags = normalize_risk_flags(_as_list(payload.get("risk_flags")))
        buckets = derive_risk_buckets(risk_flags)
        evidence_score = _safe_float(payload.get("evidence_score"))
        semantic_score = _safe_float(payload.get("semantic_score"))
        unit_year_score = _safe_float(payload.get("unit_year_score"))
        parser_agreement_score = _safe_float(payload.get("parser_agreement_score"))
        risk_penalty = _safe_float(payload.get("risk_penalty"))
        explicit_score = payload.get("confidence_score")
        confidence_score = (
            _safe_float(explicit_score)
            if explicit_score not in ("", None)
            else derive_confidence_score(
                evidence_score=evidence_score,
                semantic_score=semantic_score,
                unit_year_score=unit_year_score,
                parser_agreement_score=parser_agreement_score,
                risk_penalty=risk_penalty,
            )
        )
        routing = route_trust_record(
            confidence_score,
            risk_flags,
            blocking_policy=blocking_policy,
            low_score_policy=low_score_policy,
        )
        return cls(
            candidate_id=str(payload.get("candidate_id", "")).strip(),
            metric_label_raw=str(payload.get("metric_label_raw", "")).strip(),
            normalized_metric=str(payload.get("normalized_metric", "")).strip(),
            value=payload.get("value"),
            unit=str(payload.get("unit", "")).strip(),
            year=str(payload.get("year", "")).strip(),
            parser_sources=[str(item).strip() for item in _as_list(payload.get("parser_sources")) if str(item).strip()],
            evidence_refs=[str(item).strip() for item in _as_list(payload.get("evidence_refs")) if str(item).strip()],
            risk_flags=buckets["risk_flags"],
            blocking_risks=buckets["blocking_risks"],
            warning_risks=buckets["warning_risks"],
            confidence_score=routing["confidence_score"],
            confidence_level=confidence_level_from_score(confidence_score),
            evidence_score=evidence_score,
            semantic_score=semantic_score,
            unit_year_score=unit_year_score,
            parser_agreement_score=parser_agreement_score,
            risk_penalty=risk_penalty,
            routing_decision=routing["routing_decision"],
            decision_reasons=routing["decision_reasons"],
            next_action=routing["next_action"],
            provenance=dict(payload.get("provenance") or {}),
        )


def build_trust_record(
    payload: Mapping[str, Any],
    *,
    blocking_policy: str = "review",
    low_score_policy: str = "needs_more_info",
) -> Dict[str, Any]:
    return TrustRecord.from_dict(
        payload,
        blocking_policy=blocking_policy,
        low_score_policy=low_score_policy,
    ).to_dict()
