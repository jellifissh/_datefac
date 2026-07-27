from __future__ import annotations

import json
from pathlib import Path

import pytest

from document_reconciliation.benchmark import REVIEW_PACK_COLUMNS, write_review_pack
from document_reconciliation.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


def _right_records(path: Path) -> Path:
    source = json.loads((FIXTURES / "original_rows_sample.json").read_text(encoding="utf-8"))
    path.write_text(json.dumps(source), encoding="utf-8")
    return path


def test_cli_help_succeeds() -> None:
    with pytest.raises(SystemExit) as result:
        main(["--help"])
    assert result.value.code == 0


def test_cli_missing_input_fails_nonzero(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as result:
        main(["compare", "--left", str(tmp_path / "missing.json"), "--right", str(tmp_path / "missing.json"), "--output", str(tmp_path / "out.json")])
    assert result.value.code != 0


def test_cli_compare_writes_new_json(tmp_path: Path) -> None:
    left = FIXTURES / "mineru_table_sample.json"
    right = _right_records(tmp_path / "right.json")
    output = tmp_path / "comparison.json"
    assert main(["compare", "--left", str(left), "--right", str(right), "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["summary"]["comparison_row_count"] > 0


def test_cli_compare_refuses_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "comparison.json"
    output.write_text("keep", encoding="utf-8")
    with pytest.raises(SystemExit) as result:
        main(["compare", "--left", str(FIXTURES / "mineru_table_sample.json"), "--right", str(_right_records(tmp_path / "right.json")), "--output", str(output)])
    assert result.value.code != 0


def test_cli_report_requires_comparison_rows(tmp_path: Path) -> None:
    comparison = tmp_path / "bad.json"
    comparison.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit) as result:
        main(["report", "--comparison", str(comparison), "--output-dir", str(tmp_path / "report")])
    assert result.value.code != 0


def test_cli_report_writes_compact_review_files(tmp_path: Path) -> None:
    comparison = tmp_path / "comparison.json"
    comparison.write_text(
        json.dumps(
            {
                "comparison_rows": [
                    {
                        "context": "income",
                        "metric_key": "revenue",
                        "metric_display_name": "Revenue",
                        "period": "2026E",
                        "status": "CONFLICT",
                        "reason": "values differ",
                        "review_required": True,
                        "evidence_preview": "compact",
                        "source_trace": {"left": {"locator": "p1"}, "right": {"locator": "s1"}},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "report"
    assert main(["report", "--comparison", str(comparison), "--output-dir", str(output)]) == 0
    assert (output / "discrepancy_report.md").is_file()


def test_cli_benchmark_writes_summary_files(tmp_path: Path) -> None:
    review_pack = tmp_path / "review.xlsx"
    row = {column: "" for column in REVIEW_PACK_COLUMNS}
    row.update({"review_id": "review-1", "ground_truth_review_status": "VERIFIED", "left_value": "1", "right_value": "1", "ground_truth_value": "1", "comparison_status": "MATCH"})
    write_review_pack(review_pack, [row])
    output = tmp_path / "benchmark"
    assert main(["benchmark", "--review-pack", str(review_pack), "--output-dir", str(output)]) == 0
    assert (output / "benchmark_summary.json").is_file()
