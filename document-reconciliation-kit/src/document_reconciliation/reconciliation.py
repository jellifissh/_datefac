"""Source-neutral deterministic record comparison."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .models import ComparisonRecord, NormalizedRecord, PARSED
from .normalization import bounded_preview


MATCH = "MATCH"
CONFLICT = "CONFLICT"
LEFT_ONLY = "LEFT_ONLY"
RIGHT_ONLY = "RIGHT_ONLY"
UNPARSEABLE = "UNPARSEABLE"
UNIT_REVIEW = "UNIT_REVIEW"
REVIEW_REQUIRED_STATUSES = frozenset({CONFLICT, LEFT_ONLY, RIGHT_ONLY, UNPARSEABLE, UNIT_REVIEW})
DEFAULT_IDENTITY_FIELDS = ("context", "metric_key", "period")
PUBLIC_IDENTITY_FIELDS = frozenset({"context", "metric_key", "metric_display_name", "period"})


def reconcile_records(
    left_records: Iterable[NormalizedRecord | Mapping[str, Any]],
    right_records: Iterable[NormalizedRecord | Mapping[str, Any]],
    *,
    identity_fields: Sequence[str] = DEFAULT_IDENTITY_FIELDS,
    left_label: str = "left",
    right_label: str = "right",
) -> dict[str, Any]:
    validated_identity_fields = validate_identity_fields(identity_fields)
    rows = compare_records(
        left_records,
        right_records,
        identity_fields=validated_identity_fields,
        left_label=left_label,
        right_label=right_label,
    )
    return {
        "comparison_rows": [row.to_dict() for row in rows],
        "summary": comparison_summary(rows),
        "identity_fields": list(validated_identity_fields),
        "left_label": left_label,
        "right_label": right_label,
    }


def compare_records(
    left_records: Iterable[NormalizedRecord | Mapping[str, Any]],
    right_records: Iterable[NormalizedRecord | Mapping[str, Any]],
    *,
    identity_fields: Sequence[str] = DEFAULT_IDENTITY_FIELDS,
    left_label: str = "left",
    right_label: str = "right",
) -> list[ComparisonRecord]:
    validated_identity_fields = validate_identity_fields(identity_fields)
    left_index = _index_records(left_records, validated_identity_fields, side="left")
    right_index = _index_records(right_records, validated_identity_fields, side="right")
    comparisons: list[ComparisonRecord] = []
    for key in sorted(set(left_index) | set(right_index)):
        left_group = left_index.get(key, [])
        right_group = right_index.get(key, [])
        left_record = left_group[0] if left_group else None
        right_record = right_group[0] if right_group else None
        if len(left_group) > 1 or len(right_group) > 1:
            comparisons.append(
                _comparison(
                    UNPARSEABLE,
                    "duplicate records share the same comparison identity",
                    left_record,
                    right_record,
                    left_label=left_label,
                    right_label=right_label,
                )
            )
        elif left_record is not None and right_record is not None:
            comparisons.append(_compare_pair(left_record, right_record, left_label=left_label, right_label=right_label))
        elif left_record is not None:
            comparisons.append(
                _comparison(
                    LEFT_ONLY,
                    "comparison identity appears only in the left input",
                    left_record,
                    None,
                    left_label=left_label,
                    right_label=right_label,
                )
            )
        elif right_record is not None:
            comparisons.append(
                _comparison(
                    RIGHT_ONLY,
                    "comparison identity appears only in the right input",
                    None,
                    right_record,
                    left_label=left_label,
                    right_label=right_label,
                )
            )
    return sorted(comparisons, key=_comparison_sort_key)


def comparison_summary(rows: Iterable[ComparisonRecord | Mapping[str, Any]]) -> dict[str, int]:
    values = [row.to_dict() if isinstance(row, ComparisonRecord) else dict(row) for row in rows]
    summary = {
        "comparison_row_count": len(values),
        "match_count": 0,
        "conflict_count": 0,
        "left_only_count": 0,
        "right_only_count": 0,
        "unparseable_count": 0,
        "unit_review_count": 0,
        "review_required_count": 0,
    }
    labels = {
        MATCH: "match_count",
        CONFLICT: "conflict_count",
        LEFT_ONLY: "left_only_count",
        RIGHT_ONLY: "right_only_count",
        UNPARSEABLE: "unparseable_count",
        UNIT_REVIEW: "unit_review_count",
    }
    for row in values:
        status = str(row.get("status", ""))
        if status in labels:
            summary[labels[status]] += 1
        if bool(row.get("review_required")):
            summary["review_required_count"] += 1
    return summary


def validate_identity_fields(identity_fields: Sequence[str]) -> tuple[str, ...]:
    if isinstance(identity_fields, (str, bytes)) or not isinstance(identity_fields, Sequence):
        raise ValueError("identity_fields must be a sequence of allowed field names")
    fields = tuple(identity_fields)
    if not fields:
        raise ValueError("identity_fields must contain at least one field")
    seen_fields: set[str] = set()
    for field in fields:
        if not isinstance(field, str):
            raise ValueError("identity_fields must contain only string field names")
        if not field.strip():
            raise ValueError("identity_fields must not contain blank field names")
        if field in seen_fields:
            raise ValueError(f"identity_fields contains duplicate field: {field}")
        if field not in PUBLIC_IDENTITY_FIELDS:
            raise ValueError(f"identity_fields contains unsupported field: {field}")
        seen_fields.add(field)
    return fields


def _index_records(
    records: Iterable[NormalizedRecord | Mapping[str, Any]], identity_fields: Sequence[str], *, side: str
) -> dict[tuple[str, ...], list[NormalizedRecord]]:
    index: dict[tuple[str, ...], list[NormalizedRecord]] = defaultdict(list)
    for position, raw_record in enumerate(records):
        if isinstance(raw_record, NormalizedRecord):
            record = raw_record
        else:
            _validate_mapping_identity_values(raw_record, identity_fields, side=side, position=position)
            record = NormalizedRecord.from_mapping(raw_record)
        key = _identity_key(record, identity_fields, side=side, position=position)
        index[key].append(record)
    return index


def _validate_mapping_identity_values(
    record: Mapping[str, Any],
    identity_fields: Sequence[str],
    *,
    side: str,
    position: int,
) -> None:
    for field in identity_fields:
        if field not in record:
            raise ValueError(f"{side} record {position} has missing identity field: {field}")
        value = record[field]
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"{side} record {position} has blank identity field: {field}")
        if not isinstance(value, str):
            raise ValueError(f"{side} record {position} has non-string identity field: {field}")


def _identity_key(
    record: NormalizedRecord,
    identity_fields: Sequence[str],
    *,
    side: str,
    position: int,
) -> tuple[str, ...]:
    values: list[str] = []
    for field in identity_fields:
        value = getattr(record, field)
        if value is None or not isinstance(value, str) or not value.strip():
            raise ValueError(f"{side} record {position} has blank identity field: {field}")
        values.append(value)
    return tuple(values)


def _compare_pair(
    left: NormalizedRecord,
    right: NormalizedRecord,
    *,
    left_label: str,
    right_label: str,
) -> ComparisonRecord:
    if left.parse_status != PARSED or right.parse_status != PARSED or left.normalized_value is None or right.normalized_value is None:
        return _comparison(
            UNPARSEABLE,
            "at least one matched record cannot be parsed into a normalized value",
            left,
            right,
            left_label=left_label,
            right_label=right_label,
        )
    if _units_differ(left.normalized_unit, right.normalized_unit):
        return _comparison(
            UNIT_REVIEW,
            "normalized units differ for the same comparison identity",
            left,
            right,
            left_label=left_label,
            right_label=right_label,
        )
    if left.normalized_value == right.normalized_value:
        return _comparison(
            MATCH,
            "normalized values match for the same comparison identity",
            left,
            right,
            left_label=left_label,
            right_label=right_label,
        )
    return _comparison(
        CONFLICT,
        "normalized values differ for the same comparison identity",
        left,
        right,
        left_label=left_label,
        right_label=right_label,
    )


def _comparison(
    status: str,
    reason: str,
    left: NormalizedRecord | None,
    right: NormalizedRecord | None,
    *,
    left_label: str,
    right_label: str,
) -> ComparisonRecord:
    representative = left or right
    if representative is None:
        raise ValueError("comparison requires at least one record")
    preview = " | ".join(
        item
        for item in (
            f"{left_label}: {bounded_preview(left.evidence_preview)}" if left else "",
            f"{right_label}: {bounded_preview(right.evidence_preview)}" if right else "",
        )
        if item
    )
    trace = {
        left_label: {} if left is None else dict(left.source_trace),
        right_label: {} if right is None else dict(right.source_trace),
    }
    return ComparisonRecord(
        context=representative.context,
        metric_key=representative.metric_key,
        metric_display_name=representative.metric_display_name,
        period=representative.period,
        left_value=None if left is None else left.normalized_value,
        right_value=None if right is None else right.normalized_value,
        left_unit=None if left is None else left.normalized_unit,
        right_unit=None if right is None else right.normalized_unit,
        status=status,
        reason=reason,
        review_required=status in REVIEW_REQUIRED_STATUSES,
        evidence_preview=bounded_preview(preview),
        source_trace=trace,
    )


def _units_differ(left_unit: str | None, right_unit: str | None) -> bool:
    return bool(left_unit and right_unit and left_unit != right_unit)


def _comparison_sort_key(row: ComparisonRecord) -> tuple[str, str, str, str]:
    return (row.context, row.metric_key, row.period, row.status)
