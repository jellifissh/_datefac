from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from datefac_agent.reconciliation.discrepancy_diagnosis_348n import (
    MISSING_MINERU_EVIDENCE,
    MISSING_ORIGINAL_VALUE,
    REPORT_JSON_NAME,
    REPORT_MARKDOWN_NAME,
    SOURCE_PARSE_FAILURE,
    UNIT_MISMATCH,
    UNRESOLVED_MULTI_CAUSE,
    VALUE_CONFLICT,
    build_discrepancy_cases,
    build_discrepancy_report,
    diagnose_case_category,
    main,
    render_json_report,
    render_markdown_report,
)
from datefac_agent.reconciliation.real_artifact_compatibility_348n import load_and_reconcile_real_artifacts

REAL_MINERU_JSON = Path(r"E:\mineru_lab\output_new\H3_AP202606081823352906_1\auto\H3_AP202606081823352906_1_content_list_v2.json")
REAL_ORIGINAL_XLSX = Path(r"D:\_datefac_agent\output\datefac_raw_material_anjing_foods.xlsx")


def _comparison_row(**overrides: object) -> dict[str, object]:
    row = {
        "statement_context": "ratios_per_share",
        "statement_context_display": "Ratios & Per Share",
        "metric_key": "total_asset_turnover",
        "metric": "总资产周转率",
        "period": "2026E",
        "mineru_value": None,
        "original_value": None,
        "mineru_unit": "times",
        "original_unit": "times",
        "status": "UNPARSEABLE",
        "reason": "MinerU row could not be normalized",
        "review_required": True,
        "blocked_delivery_reason": "unparseable_row_requires_review",
        "evidence_preview": "preview",
        "source_trace": {"mineru": None, "original": None},
    }
    row.update(overrides)
    return row


def _real_report() -> dict[str, object]:
    reconciliation = load_and_reconcile_real_artifacts(REAL_MINERU_JSON, REAL_ORIGINAL_XLSX)
    cases = build_discrepancy_cases(reconciliation["comparison_rows"])
    return build_discrepancy_report(
        reconciliation=reconciliation,
        cases=cases,
        mineru_json_path=REAL_MINERU_JSON,
        original_xlsx_path=REAL_ORIGINAL_XLSX,
    ).report


def test_group_review_rows_by_statement_context_metric_period() -> None:
    cases = build_discrepancy_cases(
        [
            _comparison_row(status="ORIGINAL_ONLY", blocked_delivery_reason="original_only_requires_review"),
            _comparison_row(status="UNPARSEABLE", blocked_delivery_reason="unparseable_row_requires_review"),
        ]
    )

    assert len(cases) == 1
    assert cases[0]["statement_context"] == "ratios_per_share"
    assert cases[0]["metric"] == "total_asset_turnover"
    assert cases[0]["period"] == "2026E"
    assert cases[0]["raw_statuses"] == ["ORIGINAL_ONLY", "UNPARSEABLE"]


def test_real_rows_collapse_into_one_case_and_use_parse_failure_diagnosis() -> None:
    report = _real_report()

    assert report["raw_review_required_count"] == 2
    assert report["discrepancy_case_count"] == 1
    case = report["cases"][0]
    assert case["statement_context"] == "ratios_per_share"
    assert case["metric"] == "total_asset_turnover"
    assert case["period"] == "2026E"
    assert case["diagnosis_category"] == SOURCE_PARSE_FAILURE
    assert case["original_value"] == "0.8"
    assert case["clean_data_eligible"] is False
    assert case["readiness_gates"] == {"client_ready": False, "production_ready": False, "formal_client_export_allowed": False, "demo_export_only": True}


def test_case_id_is_deterministic() -> None:
    rows = [
        _comparison_row(status="ORIGINAL_ONLY", blocked_delivery_reason="original_only_requires_review"),
        _comparison_row(status="UNPARSEABLE", blocked_delivery_reason="unparseable_row_requires_review"),
    ]
    first = build_discrepancy_cases(rows)
    second = build_discrepancy_cases(deepcopy(rows))

    assert first == second
    assert first[0]["case_id"].startswith("r7ce:")


def test_diagnosis_category_mapping_covers_core_status_patterns() -> None:
    assert diagnose_case_category(["CONFLICT"]) == VALUE_CONFLICT
    assert diagnose_case_category(["UNIT_REVIEW"]) == UNIT_MISMATCH
    assert diagnose_case_category(["ORIGINAL_ONLY"]) == MISSING_MINERU_EVIDENCE
    assert diagnose_case_category(["MINERU_ONLY"]) == MISSING_ORIGINAL_VALUE
    assert diagnose_case_category(["ORIGINAL_ONLY", "UNPARSEABLE"]) == SOURCE_PARSE_FAILURE
    assert diagnose_case_category(["ORIGINAL_ONLY", "UNPARSEABLE", "CONFLICT"]) == UNRESOLVED_MULTI_CAUSE


def test_bounded_previews_and_raw_artifact_exclusion() -> None:
    report = _real_report()
    case = report["cases"][0]
    serialized = json.dumps(report, ensure_ascii=False)

    assert len(case["mineru_evidence_preview"]) <= 180
    assert len(case["original_evidence_preview"]) <= 180
    assert "<table" not in serialized
    assert "input_paths" not in report
    assert "source_text" not in serialized
    assert all("html" not in raw_row for raw_row in case["raw_rows"])


def test_markdown_and_json_rendering_are_deterministic() -> None:
    report = _real_report()

    assert render_json_report(report) == render_json_report(deepcopy(report))
    assert render_markdown_report(report) == render_markdown_report(deepcopy(report))


def test_cli_writes_exactly_two_expected_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "demo"
    exit_code = main(
        [
            "--mineru-json",
            str(REAL_MINERU_JSON),
            "--original-xlsx",
            str(REAL_ORIGINAL_XLSX),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert sorted(path.name for path in output_dir.iterdir()) == [
        REPORT_JSON_NAME,
        REPORT_MARKDOWN_NAME,
    ]


def test_cli_refuses_unrelated_existing_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "unsafe"
    output_dir.mkdir()
    (output_dir / "unrelated.txt").write_text("keep", encoding="utf-8")

    exit_code = main(
        [
            "--mineru-json",
            str(REAL_MINERU_JSON),
            "--original-xlsx",
            str(REAL_ORIGINAL_XLSX),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 1
    assert (output_dir / "unrelated.txt").exists()


def test_input_objects_are_not_mutated() -> None:
    reconciliation = load_and_reconcile_real_artifacts(REAL_MINERU_JSON, REAL_ORIGINAL_XLSX)
    comparison_rows = reconciliation["comparison_rows"]
    before = deepcopy(comparison_rows)

    _ = build_discrepancy_cases(comparison_rows)

    assert comparison_rows == before


def test_readiness_gates_remain_closed() -> None:
    report = _real_report()

    assert report["readiness_gates"] == {"client_ready": False, "production_ready": False, "formal_client_export_allowed": False, "demo_export_only": True}
