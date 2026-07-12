from __future__ import annotations

import json
from pathlib import Path

import pytest

from datefac_agent.benchmark.project_necessity_benchmark_348n import (
    AMBIGUOUS_PAIRING,
    BENCHMARK_METHOD_INVALID,
    MATCH,
    MISSING_MINERU_ARTIFACT,
    NEEDS_MORE_VERIFIED_CELLS,
    ONE_REPORT_SUGGESTS_LIGHTWEIGHT_QA_VALUE,
    ONE_REPORT_SUGGESTS_LOW_VALUE,
    READY,
    REVIEW_PACK_COLUMNS,
    build_benchmark_summary,
    calculate_benchmark_metrics,
    classify_report_package,
    decide_provisional_project_value,
    inventory_report_packages,
    is_forbidden_committed_benchmark_artifact,
    read_review_pack,
    resolve_canonical_report_package,
    sample_high_value_cells,
    validate_review_pack_schema,
    write_review_pack,
)


def _touch(path: Path, content: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _review_row(
    *,
    status: str = MATCH,
    ground_truth_status: str = "VERIFIED",
    truth: str = "100",
    mineru: str = "100",
    original: str = "100",
    severity: str = "",
) -> dict:
    row = {column: "" for column in REVIEW_PACK_COLUMNS}
    row.update(
        {
            "report_id": "H3_AP202600000000000001_1",
            "pdf_basename": "H3_AP202600000000000001_1.pdf",
            "statement_context": "financial_data_valuation",
            "metric": "revenue",
            "period": "2026E",
            "unit": "cny_million",
            "mineru_value": mineru,
            "original_value": original,
            "datefac_status": status,
            "pdf_ground_truth_value": truth,
            "pdf_ground_truth_unit": "cny_million",
            "ground_truth_review_status": ground_truth_status,
            "error_severity": severity,
        }
    )
    return row


def test_package_readiness_classification_and_missing_artifact_handling(tmp_path: Path) -> None:
    report_id = "H3_AP202600000000000001_1"
    pdf_path = tmp_path / f"{report_id}.pdf"
    mineru_path = tmp_path / "auto" / f"{report_id}_content_list_v2.json"
    original_path = tmp_path / f"{report_id}_提取结果.xlsx"

    ready = classify_report_package(
        report_id,
        pdf_paths=[pdf_path],
        mineru_paths=[mineru_path],
        original_paths=[original_path],
    )
    missing = classify_report_package(
        report_id,
        pdf_paths=[pdf_path],
        mineru_paths=[],
        original_paths=[original_path],
    )

    assert ready.status == READY
    assert ready.selected_pdf_path is not None
    assert missing.status == MISSING_MINERU_ARTIFACT


def test_inventory_rejects_ambiguous_pairing(tmp_path: Path) -> None:
    report_id = "H3_AP202600000000000002_1"
    _touch(tmp_path / f"{report_id}.pdf")
    _touch(tmp_path / "duplicates" / f"{report_id}_copy.pdf")
    _touch(tmp_path / "auto" / f"{report_id}_content_list_v2.json", "[]")
    _touch(tmp_path / f"{report_id}_original.xlsx")

    candidates = inventory_report_packages([tmp_path])

    assert len(candidates) == 1
    assert candidates[0].status == AMBIGUOUS_PAIRING
    assert "multiple possible files" in candidates[0].reason


def test_deterministic_sampling_prioritizes_high_value_cells() -> None:
    rows = [
        {"statement_context": "cash_flow", "metric_key": "operating_cash_flow", "period": "2024A", "status": MATCH},
        {"statement_context": "financial_data_valuation", "metric_key": "revenue", "period": "2026E", "status": MATCH},
        {"statement_context": "financial_data_valuation", "metric_key": "pe", "period": "2026E", "status": MATCH},
        {"statement_context": "balance_sheet", "metric_key": "unknown_metric", "period": "2025A", "status": MATCH},
    ]

    first = sample_high_value_cells(rows, sample_size=3)
    second = sample_high_value_cells(list(reversed(rows)), sample_size=3)

    assert [row["metric_key"] for row in first] == ["revenue", "pe", "operating_cash_flow"]
    assert first == second


def test_unverified_rows_are_excluded_from_metrics() -> None:
    rows = [
        _review_row(ground_truth_status="", truth="100", mineru="0", original="0"),
        _review_row(ground_truth_status="REVIEW_REQUIRED", truth="100", mineru="0", original="0"),
    ]

    metrics = calculate_benchmark_metrics(rows)

    assert metrics["sampled_cell_count"] == 2
    assert metrics["verified_cell_count"] == 0
    assert metrics["mineru_error_count"] == 0
    assert metrics["original_error_count"] == 0


def test_both_systems_same_wrong_value_is_counted_as_datefac_false_negative() -> None:
    metrics = calculate_benchmark_metrics([
        _review_row(status=MATCH, truth="100", mineru="90", original="90", severity="HIGH")
    ])

    assert metrics["mineru_error_count"] == 1
    assert metrics["original_error_count"] == 1
    assert metrics["both_wrong_same_value_count"] == 1
    assert metrics["both_wrong_different_value_count"] == 0
    assert metrics["datefac_false_negative_count"] == 1
    assert metrics["high_severity_error_count"] == 1


def test_datefac_false_positive_and_false_negative_accounting() -> None:
    rows = [
        _review_row(status="CONFLICT", truth="100", mineru="90", original="100"),
        _review_row(status="CONFLICT", truth="100", mineru="100", original="100"),
        _review_row(status=MATCH, truth="100", mineru="90", original="90"),
        _review_row(status=MATCH, truth="100", mineru="100", original="100"),
    ]

    metrics = calculate_benchmark_metrics(rows)

    assert metrics["datefac_true_positive_count"] == 1
    assert metrics["datefac_false_positive_count"] == 1
    assert metrics["datefac_false_negative_count"] == 1
    assert metrics["datefac_true_negative_count"] == 1
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["false_positive_rate"] == 0.5


def test_zero_division_safe_metrics_and_decision_rules() -> None:
    empty_metrics = calculate_benchmark_metrics([])

    assert empty_metrics["precision"] == 0.0
    assert empty_metrics["recall"] == 0.0
    assert empty_metrics["false_positive_rate"] == 0.0
    assert decide_provisional_project_value(empty_metrics, ready_report_package_count=0) == BENCHMARK_METHOD_INVALID
    assert decide_provisional_project_value(empty_metrics, ready_report_package_count=1) == NEEDS_MORE_VERIFIED_CELLS


def test_one_report_decision_rules_are_conservative() -> None:
    useful_rows = [
        _review_row(status="CONFLICT", truth="100", mineru="90", original="100")
        for _ in range(20)
    ]
    low_value_rows = [_review_row(status=MATCH, truth="100", mineru="100", original="100") for _ in range(20)]

    useful_summary = build_benchmark_summary(
        useful_rows,
        candidate_report_package_count=1,
        ready_report_package_count=1,
    )
    low_value_summary = build_benchmark_summary(
        low_value_rows,
        candidate_report_package_count=1,
        ready_report_package_count=1,
    )

    assert useful_summary["provisional_project_value_result"] == ONE_REPORT_SUGGESTS_LIGHTWEIGHT_QA_VALUE
    assert low_value_summary["provisional_project_value_result"] == ONE_REPORT_SUGGESTS_LOW_VALUE


def test_review_pack_schema_round_trip(tmp_path: Path) -> None:
    output_path = tmp_path / "review_pack.xlsx"
    source_row = _review_row()

    write_review_pack(output_path, [source_row])
    rows = read_review_pack(output_path)

    assert rows[0]["report_id"] == source_row["report_id"]
    assert rows[0]["datefac_status"] == MATCH
    validate_review_pack_schema(REVIEW_PACK_COLUMNS)
    with pytest.raises(ValueError, match="schema mismatch"):
        validate_review_pack_schema(("report_id", "unexpected"))


def test_no_real_input_or_generated_artifact_should_be_committed() -> None:
    forbidden = [
        Path("output/benchmark/r7cf_anjing_foods_ground_truth_review_pack.xlsx"),
        Path("input/H3_AP202606081823352906_1.pdf"),
        Path("E:/mineru_lab/output_new/H3_AP202606081823352906_1/auto/H3_AP202606081823352906_1_content_list_v2.json"),
    ]
    allowed = [
        Path("datefac_agent/benchmark/project_necessity_benchmark_348n.py"),
        Path("tests/benchmark/test_project_necessity_benchmark_348n.py"),
    ]

    assert all(is_forbidden_committed_benchmark_artifact(path) for path in forbidden)
    assert not any(is_forbidden_committed_benchmark_artifact(path) for path in allowed)


def test_canonical_selection_prefers_anjing_trio_over_duplicates() -> None:
    candidate = classify_report_package(
        "H3_AP202606081823352906_1",
        pdf_paths=[
            r"D:\_datefac\input\real_test\H3_AP202606081823352906_1.pdf",
            r"E:\mineru_lab\input\H3_AP202606081823352906_1.pdf",
        ],
        mineru_paths=[
            r"D:\_datefac\output\mineru_real_test_337a\mineru_outputs\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list_v2.json",
            r"E:\mineru_lab\output_new\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list_v2.json",
        ],
        original_paths=[
            r"D:\_datefac\output\mineru_real_test_337a\datefac_debug\H3_AP202606081823352906_1\client_preview.xlsx",
            r"D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx",
        ],
    )
    resolved = resolve_canonical_report_package([candidate])

    assert candidate.status == AMBIGUOUS_PAIRING
    assert resolved is not None
    assert resolved.status == READY
    assert resolved.selected_pdf_path == r"E:\mineru_lab\input\H3_AP202606081823352906_1.pdf"
    assert resolved.selected_original_artifact_path == r"D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx"


def test_summary_markdown_json_payload_is_compact_and_metadata_only(tmp_path: Path) -> None:
    rows = [_review_row()]
    summary = build_benchmark_summary(rows, candidate_report_package_count=1, ready_report_package_count=1)
    payload = json.dumps(summary, ensure_ascii=False)

    assert "full_source_text" not in payload
    assert "clean_data" not in payload
    assert summary["readiness_gates"]["client_ready"] is False
