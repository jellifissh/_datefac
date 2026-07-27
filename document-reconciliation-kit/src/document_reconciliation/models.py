"""Public record models for the standalone reconciliation kit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


PARSED = "PARSED"
UNPARSEABLE = "UNPARSEABLE"


def _compact_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not value:
        return {}
    return {str(key): value[key] for key in sorted(value)}


@dataclass(frozen=True)
class NormalizedRecord:
    source: str
    context: str
    metric_key: str
    metric_display_name: str
    period: str
    normalized_value: str | None
    normalized_unit: str | None
    evidence_preview: str = ""
    source_trace: Mapping[str, Any] = field(default_factory=dict)
    parse_status: str = PARSED

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "NormalizedRecord":
        return cls(
            source=str(value.get("source", "")),
            context=str(value.get("context", "")),
            metric_key=str(value.get("metric_key", "")),
            metric_display_name=str(value.get("metric_display_name", value.get("metric_key", ""))),
            period=str(value.get("period", "")),
            normalized_value=None if value.get("normalized_value") is None else str(value.get("normalized_value")),
            normalized_unit=None if value.get("normalized_unit") is None else str(value.get("normalized_unit")),
            evidence_preview=str(value.get("evidence_preview", "")),
            source_trace=_compact_mapping(value.get("source_trace") if isinstance(value.get("source_trace"), Mapping) else None),
            parse_status=str(value.get("parse_status", PARSED)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "context": self.context,
            "metric_key": self.metric_key,
            "metric_display_name": self.metric_display_name,
            "period": self.period,
            "normalized_value": self.normalized_value,
            "normalized_unit": self.normalized_unit,
            "evidence_preview": self.evidence_preview,
            "source_trace": _compact_mapping(self.source_trace),
            "parse_status": self.parse_status,
        }


@dataclass(frozen=True)
class ComparisonRecord:
    context: str
    metric_key: str
    metric_display_name: str
    period: str
    left_value: str | None
    right_value: str | None
    left_unit: str | None
    right_unit: str | None
    status: str
    reason: str
    review_required: bool
    evidence_preview: str = ""
    source_trace: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context,
            "metric_key": self.metric_key,
            "metric_display_name": self.metric_display_name,
            "period": self.period,
            "left_value": self.left_value,
            "right_value": self.right_value,
            "left_unit": self.left_unit,
            "right_unit": self.right_unit,
            "status": self.status,
            "reason": self.reason,
            "review_required": self.review_required,
            "evidence_preview": self.evidence_preview,
            "source_trace": _compact_mapping(self.source_trace),
        }
