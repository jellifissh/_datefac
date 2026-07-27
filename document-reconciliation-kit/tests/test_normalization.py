from __future__ import annotations

import pytest

from document_reconciliation.normalization import bounded_preview, compact_text, normalize_metric_key, normalize_numeric, normalize_period, normalize_unit, stable_hash


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        ("  Revenue\n  Growth ", "Revenue Growth"),
        ("a\t b", "a b"),
    ],
)
def test_compact_text(value: object, expected: str) -> None:
    assert compact_text(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2025A", "2025A"),
        ("2026E", "2026E"),
        ("2027F", "2027F"),
        ("FY2024", "2024"),
        ("2024 年 Q3", "2024Q3"),
        ("2024H1", "2024H1"),
        ("period unknown", None),
        (None, None),
    ],
)
def test_normalize_period_preserves_suffixes(value: object, expected: str | None) -> None:
    assert normalize_period(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (100, "100"),
        ("1,234.00", "1234"),
        ("(40)", "-40"),
        ("12.50%", "12.5"),
        ("-0", "0"),
        ("1e3", "1000"),
        ("—", None),
        ("not numeric", None),
        (True, None),
        (None, None),
    ],
)
def test_normalize_numeric(value: object, expected: str | None) -> None:
    assert normalize_numeric(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("%", "percent"),
        ("％", "percent"),
        ("倍", "times"),
        ("亿元", "hundred_million_yuan"),
        ("百万元", "million_yuan"),
        ("元", "yuan"),
        ("custom unit", "custom_unit"),
        (None, None),
    ],
)
def test_normalize_unit(value: object, expected: str | None) -> None:
    assert normalize_unit(value) == expected


def test_generic_metric_key_is_source_neutral() -> None:
    assert normalize_metric_key("Revenue / growth") == "revenue_growth"


def test_preview_is_bounded() -> None:
    assert bounded_preview("abcdefgh", limit=5) == "abcd…"
    assert bounded_preview("abc", limit=0) == ""


def test_hash_is_stable_across_mapping_order() -> None:
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})
