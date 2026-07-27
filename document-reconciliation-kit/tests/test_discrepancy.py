from __future__ import annotations

import json
from pathlib import Path

import pytest

from document_reconciliation.discrepancy import build_discrepancy_cases, build_discrepancy_report, render_json_report, render_markdown_report, write_review_report
from document_reconciliation.reconciliation import CONFLICT, LEFT_ONLY, RIGHT_ONLY, UNIT_REVIEW, UNPARSEABLE


def _row(status: str, **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "context": "income",
        "metric_key": "revenue",
        "metric_display_name": "Revenue",
        "period": "2026E",
        "left_value": "100",
        "right_value": "101",
        "left_unit": "million",
        "right_unit": "million",
        "status": status,
        "reason": "test reason",
        "review_required": True,
        "evidence_preview": "evidence " * 80,
        "source_trace": {"left": {"locator": "p1"}, "right": {"locator": "s1"}},
    }
    values.update(overrides)
    return values


def test_related_rows_group_into_one_deterministic_case() -> None:
    rows = [_row(LEFT_ONLY), _row(UNPARSEABLE)]
    first = build_discrepancy_cases(rows)
    second = build_discrepancy_cases(list(reversed(rows)))
    assert len(first) == 1
    assert first[0]["case_id"] == second[0]["case_id"]
    assert first[0]["statuses"] == [LEFT_ONLY, UNPARSEABLE]


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (CONFLICT, "VALUE_CONFLICT"),
        (LEFT_ONLY, "MISSING_RIGHT_RECORD"),
        (RIGHT_ONLY, "MISSING_LEFT_RECORD"),
        (UNPARSEABLE, "PARSE_FAILURE"),
        (UNIT_REVIEW, "UNIT_MISMATCH"),
    ],
)
def test_status_diagnosis_categories(status: str, expected: str) -> None:
    assert build_discrepancy_cases([_row(status)])[0]["diagnosis_category"] == expected


def test_case_preview_is_bounded_and_trace_is_compact() -> None:
    case = build_discrepancy_cases([_row(CONFLICT)])[0]
    assert len(case["evidence_preview"]) <= 240
    assert case["source_trace"]["left"] == [{"locator": "p1"}]


def test_json_and_markdown_rendering_are_deterministic() -> None:
    report = build_discrepancy_report([_row(CONFLICT)])
    assert render_json_report(report) == render_json_report(report)
    assert render_markdown_report(report) == render_markdown_report(report)
    assert json.loads(render_json_report(report))["discrepancy_case_count"] == 1


def test_write_report_creates_only_compact_report_files(tmp_path: Path) -> None:
    output = tmp_path / "report"
    paths = write_review_report([_row(CONFLICT)], output)
    assert {Path(value).name for value in paths.values()} == {"discrepancy_report.json", "discrepancy_report.md"}


def test_write_report_rejects_nonempty_directory(tmp_path: Path) -> None:
    output = tmp_path / "report"
    output.mkdir()
    (output / "unrelated.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="not empty"):
        write_review_report([_row(CONFLICT)], output)
