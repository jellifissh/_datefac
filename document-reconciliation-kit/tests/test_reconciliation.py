from __future__ import annotations

from copy import deepcopy

import pytest

from document_reconciliation import __version__
from document_reconciliation.models import NormalizedRecord, UNPARSEABLE as PARSE_STATUS_UNPARSEABLE
from document_reconciliation.reconciliation import CONFLICT, LEFT_ONLY, MATCH, PUBLIC_IDENTITY_FIELDS, RIGHT_ONLY, UNIT_REVIEW, UNPARSEABLE, compare_records, comparison_summary, reconcile_records


MAPPING_NON_STRING_IDENTITY_VALUES = (123, 1.5, True, [], object())
MAPPING_BLANK_OR_MISSING_IDENTITY_VALUES = (None, "", "   ", b"2026E", (), {}, set())


def _record(**overrides: object) -> NormalizedRecord:
    values: dict[str, object] = {
        "source": "left",
        "context": "income",
        "metric_key": "revenue",
        "metric_display_name": "Revenue",
        "period": "2026E",
        "normalized_value": "100",
        "normalized_unit": "million",
        "evidence_preview": "small preview",
        "source_trace": {"locator": "x"},
        "parse_status": "PARSED",
    }
    values.update(overrides)
    return NormalizedRecord(**values)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (_record(), _record(source="right"), MATCH),
        (_record(), _record(source="right", normalized_value="101"), CONFLICT),
        (_record(), None, LEFT_ONLY),
        (None, _record(source="right"), RIGHT_ONLY),
        (_record(parse_status=PARSE_STATUS_UNPARSEABLE, normalized_value=None), _record(source="right"), UNPARSEABLE),
        (_record(), _record(source="right", normalized_unit="percent"), UNIT_REVIEW),
    ],
)
def test_status_matrix(left: NormalizedRecord | None, right: NormalizedRecord | None, expected: str) -> None:
    rows = compare_records([] if left is None else [left], [] if right is None else [right])
    assert rows[0].status == expected
    assert rows[0].review_required is (expected != MATCH)


def test_context_separation_prevents_false_match() -> None:
    rows = compare_records([_record(context="income")], [_record(source="right", context="balance")])
    assert [row.status for row in rows] == [RIGHT_ONLY, LEFT_ONLY]


def test_duplicate_identity_is_unparseable() -> None:
    rows = compare_records([_record(), _record(evidence_preview="other")], [_record(source="right")])
    assert rows[0].status == UNPARSEABLE


def test_input_mappings_are_not_mutated() -> None:
    left = [_record().to_dict()]
    right = [_record(source="right").to_dict()]
    before_left, before_right = deepcopy(left), deepcopy(right)
    compare_records(left, right)
    assert left == before_left
    assert right == before_right


def test_output_order_is_deterministic() -> None:
    left = [_record(metric_key="z", metric_display_name="Z"), _record(metric_key="a", metric_display_name="A")]
    right = [_record(source="right", metric_key="z", metric_display_name="Z"), _record(source="right", metric_key="a", metric_display_name="A")]
    assert [row.metric_key for row in compare_records(left, right)] == ["a", "z"]


def test_custom_identity_key_can_ignore_context() -> None:
    rows = compare_records([_record(context="one")], [_record(source="right", context="two")], identity_fields=("metric_key", "period"))
    assert rows[0].status == MATCH


def test_summary_counts_each_status() -> None:
    rows = compare_records([_record(), _record(metric_key="left")], [_record(source="right", normalized_value="101"), _record(source="right", metric_key="right")])
    summary = comparison_summary(rows)
    assert summary["conflict_count"] == 1
    assert summary["left_only_count"] == 1
    assert summary["right_only_count"] == 1


def test_reconcile_records_is_json_boundary() -> None:
    result = reconcile_records([_record()], [_record(source="right")])
    assert result["comparison_rows"][0]["status"] == MATCH
    assert result["identity_fields"] == ["context", "metric_key", "period"]


@pytest.mark.parametrize(
    "identity_fields",
    [
        ("unknown_identity_field",),
        "context",
        b"context",
        (),
        ("",),
        ("context", "context"),
        (1,),
        ("normalized_value",),
    ],
)
def test_invalid_identity_configuration_raises_before_consuming_records(identity_fields: object) -> None:
    def records() -> object:
        raise AssertionError("records must not be consumed for invalid identity configuration")
        yield None

    with pytest.raises(ValueError):
        compare_records(records(), records(), identity_fields=identity_fields)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["context", "metric_key", "period"])
def test_blank_default_identity_value_is_rejected_before_pairing(field: str) -> None:
    left = _record(**{field: " "})
    with pytest.raises(ValueError, match=rf"left record 0 has blank identity field: {field}"):
        compare_records([left], [_record(source="right")])


def test_explicit_null_mapping_identity_stays_blank_and_is_rejected() -> None:
    left = _record().to_dict()
    left["context"] = None
    normalized = NormalizedRecord.from_mapping(left)
    assert normalized.context == ""
    with pytest.raises(ValueError, match="left record 0 has blank identity field: context"):
        compare_records([left], [_record(source="right").to_dict()])


@pytest.mark.parametrize("field", sorted(PUBLIC_IDENTITY_FIELDS))
@pytest.mark.parametrize("invalid_value", MAPPING_NON_STRING_IDENTITY_VALUES)
@pytest.mark.parametrize("invalid_side", ["left", "right"])
def test_mapping_non_string_identity_values_are_rejected_before_pairing(
    field: str,
    invalid_value: object,
    invalid_side: str,
) -> None:
    left = _record(evidence_preview="private preview").to_dict()
    right = _record(source="right", evidence_preview="private preview").to_dict()
    target = left if invalid_side == "left" else right
    target[field] = invalid_value
    before_left, before_right = dict(left), dict(right)

    with pytest.raises(
        ValueError,
        match=rf"{invalid_side} record 0 has non-string identity field: {field}",
    ) as error:
        compare_records([left], [right], identity_fields=(field,))

    assert "private preview" not in str(error.value)
    assert left == before_left
    assert right == before_right


@pytest.mark.parametrize("field", sorted(PUBLIC_IDENTITY_FIELDS))
@pytest.mark.parametrize("invalid_value", MAPPING_BLANK_OR_MISSING_IDENTITY_VALUES)
def test_mapping_blank_or_non_string_identity_values_are_rejected(field: str, invalid_value: object) -> None:
    left = _record().to_dict()
    left[field] = invalid_value

    reason = "blank" if invalid_value is None or isinstance(invalid_value, str) else "non-string"
    with pytest.raises(ValueError, match=rf"left record 0 has {reason} identity field: {field}"):
        compare_records([left], [_record(source="right").to_dict()], identity_fields=(field,))


@pytest.mark.parametrize("field", sorted(PUBLIC_IDENTITY_FIELDS))
def test_mapping_missing_identity_field_is_rejected_without_overconsuming_input(field: str) -> None:
    invalid = _record().to_dict()
    del invalid[field]

    def left_records() -> object:
        yield invalid
        raise AssertionError("records must not be consumed after an invalid mapping")

    with pytest.raises(ValueError, match=rf"left record 0 has missing identity field: {field}"):
        compare_records(left_records(), [], identity_fields=(field,))


def test_equal_invalid_mapping_identity_values_cannot_return_match() -> None:
    left = _record().to_dict()
    right = _record(source="right").to_dict()
    left["context"] = 123
    right["context"] = 123

    with pytest.raises(ValueError, match="left record 0 has non-string identity field: context"):
        compare_records([left], [right])


def test_blank_custom_metric_display_name_is_rejected_when_selected() -> None:
    left = _record(metric_display_name=" ")
    with pytest.raises(ValueError, match="left record 0 has blank identity field: metric_display_name"):
        compare_records([left], [_record(source="right")], identity_fields=("context", "metric_display_name"))


def test_public_identity_allowlist_excludes_comparison_payload_fields() -> None:
    assert PUBLIC_IDENTITY_FIELDS == frozenset({"context", "metric_key", "metric_display_name", "period"})


def test_version_is_exported_from_package() -> None:
    assert __version__ == "0.1.2"
