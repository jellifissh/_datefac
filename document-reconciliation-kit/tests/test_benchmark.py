from __future__ import annotations

from pathlib import Path

import pytest

from document_reconciliation.benchmark import REVIEW_PACK_COLUMNS, build_review_pack_rows, calculate_benchmark_metrics, read_review_pack, render_benchmark_markdown, validate_review_pack_schema, write_benchmark_summary, write_review_pack


def _row(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "ground_truth_review_status": "VERIFIED",
        "left_value": "10",
        "right_value": "10",
        "ground_truth_value": "10",
        "unit": "million",
        "ground_truth_unit": "million",
        "left_correct": "",
        "right_correct": "",
        "comparison_status": "MATCH",
    }
    values.update(overrides)
    return values


def test_only_verified_rows_count_toward_metrics() -> None:
    metrics = calculate_benchmark_metrics([_row(), _row(ground_truth_review_status="PENDING", left_value="1")])
    assert metrics["sampled_cell_count"] == 2
    assert metrics["verified_cell_count"] == 1
    assert metrics["left_error_count"] == 0


@pytest.mark.parametrize(
    ("left_value", "right_value", "same_count", "different_count"),
    [("9", "9", 1, 0), ("9", "8", 0, 1)],
)
def test_both_wrong_counts(left_value: str, right_value: str, same_count: int, different_count: int) -> None:
    metrics = calculate_benchmark_metrics([_row(left_value=left_value, right_value=right_value, comparison_status="CONFLICT")])
    assert metrics["both_wrong_same_value_count"] == same_count
    assert metrics["both_wrong_different_value_count"] == different_count


def test_true_positive_false_positive_false_negative_true_negative_accounting() -> None:
    rows = [
        _row(left_value="9", comparison_status="CONFLICT"),
        _row(comparison_status="CONFLICT"),
        _row(left_value="9", comparison_status="MATCH"),
        _row(comparison_status="MATCH"),
    ]
    metrics = calculate_benchmark_metrics(rows)
    assert [metrics[key] for key in ("comparison_true_positive_count", "comparison_false_positive_count", "comparison_false_negative_count", "comparison_true_negative_count")] == [1, 1, 1, 1]


def test_zero_division_metrics_are_safe() -> None:
    metrics = calculate_benchmark_metrics([])
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["false_positive_rate"] == 0.0


def test_build_review_pack_rows_leaves_truth_blank() -> None:
    rows = build_review_pack_rows([{"context": "income", "metric_key": "revenue", "metric_display_name": "Revenue", "period": "2026E", "left_value": "10", "right_value": "11", "status": "CONFLICT"}])
    assert rows[0]["ground_truth_value"] == ""
    assert rows[0]["ground_truth_review_status"] == ""


def test_review_pack_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "review.xlsx"
    rows = [{column: _row().get(column, "") for column in REVIEW_PACK_COLUMNS}]
    write_review_pack(path, rows)
    assert read_review_pack(path)[0]["ground_truth_review_status"] == "VERIFIED"


def test_review_pack_schema_is_strict() -> None:
    with pytest.raises(ValueError, match="schema mismatch"):
        validate_review_pack_schema(["wrong"])


def test_review_pack_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "review.xlsx"
    path.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        write_review_pack(path, [])


def test_benchmark_summary_writes_compact_files_only(tmp_path: Path) -> None:
    paths = write_benchmark_summary([_row()], tmp_path / "summary")
    assert {Path(value).name for value in paths.values()} == {"benchmark_summary.json", "benchmark_summary.md"}
    assert "verified_cell_count" in render_benchmark_markdown(calculate_benchmark_metrics([_row()]))
