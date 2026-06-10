from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.table_first_reviewed_client_preview_pilot_342j import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_table_first_reviewed_client_preview_pilot_342j,
)
from datefac.benchmark.table_first_reviewed_client_preview_pilot_342j_report import WORKBOOK_SHEETS  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _seed_342i_ready(root: Path, *, source_trace_missing: bool = False) -> Path:
    output_dir = root / "output" / "table_first_post_human_review_sidecar_result_342i"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "decision": "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY",
        "ready_for_342j": True,
        "input_review_template_row_count": 5,
        "reviewed_row_count": 3,
        "pending_review_count": 2,
        "final_confirmed_cell_count": 1,
        "final_corrected_cell_count": 1,
        "final_rejected_cell_count": 1,
        "post_human_confirmed_count": 2,
        "metric_covered_after_human_count": 2,
        "metric_year_pair_after_human_count": 2,
        "remaining_review_count": 2,
        "unit_year_remaining_count": 1,
        "duplicate_remaining_count": 1,
        "growth_row_remaining_count": 0,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": True,
    }
    _write_json(output_dir / "table_first_post_human_review_sidecar_result_342i_summary.json", summary)
    _write_json(output_dir / "table_first_post_human_review_sidecar_result_342i_qa.json", {"qa_fail_count": 0, "checks": []})
    _write_json(
        output_dir / "table_first_post_human_review_sidecar_result_342i_no_write_back_proof.json",
        {"upstream_workbooks_unchanged": True, "no_official_asset_modification_during_342i": True},
    )
    (output_dir / "table_first_post_human_review_sidecar_result_342i_report.md").write_text("342I report", encoding="utf-8")

    confirmed_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_1",
                "review_priority": "MEDIUM",
                "review_bucket": "UNIT_YEAR_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "" if source_trace_missing else "img1.jpg",
                "metric_raw": "ROE",
                "metric_standardized": "ROE",
                "year_standardized": "2024A",
                "value_numeric": 10.5,
                "normalized_unit": "%",
                "final_metric_standardized": "ROE",
                "final_year_standardized": "2024A",
                "final_value_numeric": 10.5,
                "final_normalized_unit": "%",
                "reviewer_decision": "CONFIRM_CELL",
                "reviewer_note": "ok",
                "reviewer_id": "r1",
                "reviewed_at": "2026-06-10 11:15:10 UTC",
                "source_html_snippet": "" if source_trace_missing else "<table>roe</table>",
                "human_status": "HUMAN_CONFIRMED_CELL",
                "final_status": "POST_HUMAN_CONFIRMED",
            }
        ]
    )
    corrected_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_2",
                "review_priority": "MEDIUM",
                "review_bucket": "UNIT_YEAR_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t1",
                "table_type": "INCOME_STATEMENT",
                "source_page": 2,
                "bbox": "[2,3,4,5]",
                "image_path": "img2.jpg",
                "metric_raw": "收入增长",
                "metric_standardized": "revenue",
                "year_standardized": "2024A",
                "value_numeric": 46.0,
                "normalized_unit": "",
                "final_metric_standardized": "revenue_yoy",
                "final_year_standardized": "2024A",
                "final_value_numeric": 46.0,
                "final_normalized_unit": "%",
                "reviewer_decision": "CORRECT_AND_CONFIRM",
                "reviewer_note": "fix",
                "reviewer_id": "r2",
                "reviewed_at": "2026-06-10 11:15:10 UTC",
                "source_html_snippet": "<table>growth</table>",
                "human_status": "HUMAN_CORRECTED_CONFIRMED_CELL",
                "final_status": "POST_HUMAN_CORRECTED_CONFIRMED",
            }
        ]
    )
    rejected_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_3",
                "review_priority": "HIGH",
                "review_bucket": "NOT_CORE_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t2",
                "table_type": "UNKNOWN_TABLE",
                "source_page": 3,
                "bbox": "[3,4,5,6]",
                "image_path": "img3.jpg",
                "metric_raw": "评级",
                "metric_standardized": "",
                "year_standardized": "",
                "value_numeric": "",
                "normalized_unit": "",
                "final_metric_standardized": "",
                "final_year_standardized": "",
                "final_value_numeric": "",
                "final_normalized_unit": "",
                "reviewer_decision": "NOT_A_CORE_METRIC",
                "reviewer_note": "reject",
                "reviewer_id": "r3",
                "reviewed_at": "2026-06-10 11:15:10 UTC",
                "source_html_snippet": "<table>reject</table>",
                "human_status": "HUMAN_REJECTED_NOT_CORE",
                "final_status": "POST_HUMAN_REJECTED",
            }
        ]
    )
    pending_df = pd.DataFrame(
        [
            {"review_item_id": "item_4", "review_priority": "HIGH", "human_status": "PENDING_REVIEW"},
            {"review_item_id": "item_5", "review_priority": "MEDIUM", "human_status": "PENDING_REVIEW"},
        ]
    )
    before_after_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_1",
                "human_status": "HUMAN_CONFIRMED_CELL",
                "reviewer_decision": "CONFIRM_CELL",
                "original_metric_standardized": "ROE",
                "final_metric_standardized": "ROE",
                "original_year_standardized": "2024A",
                "final_year_standardized": "2024A",
                "original_value_numeric": 10.5,
                "final_value_numeric": 10.5,
                "original_normalized_unit": "%",
                "final_normalized_unit": "%",
                "change_type": "UNCHANGED_CONFIRMED",
            },
            {
                "review_item_id": "item_2",
                "human_status": "HUMAN_CORRECTED_CONFIRMED_CELL",
                "reviewer_decision": "CORRECT_AND_CONFIRM",
                "original_metric_standardized": "revenue",
                "final_metric_standardized": "revenue_yoy",
                "original_year_standardized": "2024A",
                "final_year_standardized": "2024A",
                "original_value_numeric": 46.0,
                "final_value_numeric": 46.0,
                "original_normalized_unit": "",
                "final_normalized_unit": "%",
                "change_type": "MULTI_FIELD_CORRECTED",
            },
            {
                "review_item_id": "item_3",
                "human_status": "HUMAN_REJECTED_NOT_CORE",
                "reviewer_decision": "NOT_A_CORE_METRIC",
                "original_metric_standardized": "",
                "final_metric_standardized": "",
                "original_year_standardized": "",
                "final_year_standardized": "",
                "original_value_numeric": "",
                "final_value_numeric": "",
                "original_normalized_unit": "",
                "final_normalized_unit": "",
                "change_type": "REJECTED",
            },
        ]
    )
    source_trace_df = pd.concat([confirmed_df, corrected_df, rejected_df], ignore_index=True)[
        [
            "review_item_id",
            "corpus_pdf_id",
            "file_name",
            "table_id",
            "table_type",
            "source_page",
            "bbox",
            "image_path",
            "source_html_snippet",
            "final_status",
            "reviewer_decision",
        ]
    ]
    metric_coverage_df = pd.DataFrame(
        [
            {
                "final_metric_standardized": "ROE",
                "confirmed_count": 1,
                "corrected_count": 0,
                "total_post_human_confirmed_count": 1,
                "year_covered_count": 1,
                "year_list": "2024A",
                "pdf_covered_count": 1,
                "table_covered_count": 1,
            },
            {
                "final_metric_standardized": "revenue_yoy",
                "confirmed_count": 0,
                "corrected_count": 1,
                "total_post_human_confirmed_count": 1,
                "year_covered_count": 1,
                "year_list": "2024A",
                "pdf_covered_count": 1,
                "table_covered_count": 1,
            },
        ]
    )
    remaining_risks_df = pd.DataFrame(
        [
            {
                "pending_review_count": 2,
                "still_review_required_count": 0,
                "needs_source_check_count": 0,
                "unit_year_remaining_count": 1,
                "duplicate_remaining_count": 1,
                "growth_row_remaining_count": 0,
                "source_check_remaining_count": 0,
                "high_priority_remaining_count": 1,
                "medium_priority_remaining_count": 1,
                "low_priority_remaining_count": 0,
            }
        ]
    )
    readiness_df = pd.DataFrame(
        [{"ready_for_342j": True, "recommended_342j_scope": "table_first_reviewed_client_preview_pilot", "decision": summary["decision"]}]
    )
    no_write_back_df = pd.DataFrame([{"path": "x", "before_hash": "a", "after_hash": "a", "unchanged": True}])

    _write_excel(
        output_dir / "table_first_post_human_review_sidecar_result_342i.xlsx",
        {
            "01_RESULT_SUMMARY": pd.DataFrame([summary]),
            "03_HUMAN_REVIEWED_CELLS": pd.concat([confirmed_df, corrected_df, rejected_df], ignore_index=True),
            "04_FINAL_CONFIRMED": confirmed_df,
            "05_FINAL_CORRECTED": corrected_df,
            "06_FINAL_REJECTED": rejected_df,
            "07_PENDING_REVIEW": pending_df,
            "08_BEFORE_AFTER": before_after_df,
            "09_SOURCE_TRACE": source_trace_df,
            "10_METRIC_COVERAGE_AFTER": metric_coverage_df,
            "11_UNIT_YEAR_AFTER": pd.DataFrame(),
            "12_REMAINING_RISKS": remaining_risks_df,
            "13_342J_READINESS": readiness_df,
            "14_NO_WRITE_BACK": no_write_back_df,
        },
    )
    return output_dir


def test_build_342j_ready_with_preview_rows_only(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    post_human_review_342i_dir = _seed_342i_ready(repo_root)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_reviewed_client_preview_pilot_342j(
        post_human_review_342i_dir=post_human_review_342i_dir,
        output_dir=repo_root / "output" / "table_first_reviewed_client_preview_pilot_342j",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["reviewed_preview_row_count"] == 2
    assert summary["confirmed_preview_row_count"] == 1
    assert summary["corrected_preview_row_count"] == 1
    assert summary["rejected_in_batch_count"] == 1
    assert summary["metric_covered_count"] == 2
    assert summary["metric_year_pair_count"] == 2
    assert summary["remaining_review_count"] == 2
    assert summary["ready_for_342k"] is True
    preview_df = artifacts["workbook_sheets"]["03_REVIEWED_PREVIEW"]
    assert "NOT_A_CORE_METRIC" not in set(preview_df["reviewer_decision"].astype(str))
    assert set(preview_df["preview_confidence_label"].astype(str)) == {"HUMAN_CONFIRMED", "HUMAN_CORRECTED"}
    assert all(name in WORKBOOK_SHEETS for name in artifacts["workbook_sheets"])


def test_build_342j_not_ready_when_342i_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    post_human_review_342i_dir = _seed_342i_ready(repo_root)
    summary_path = post_human_review_342i_dir / "table_first_post_human_review_sidecar_result_342i_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["decision"] = "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_NOT_READY"
    summary["ready_for_342j"] = False
    summary["post_human_confirmed_count"] = 0
    _write_json(summary_path, summary)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_reviewed_client_preview_pilot_342j(
        post_human_review_342i_dir=post_human_review_342i_dir,
        output_dir=repo_root / "output" / "table_first_reviewed_client_preview_pilot_342j",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary_out = artifacts["summary"]
    assert summary_out["decision"] == NOT_READY_DECISION
    assert summary_out["ready_for_342k"] is False
    assert summary_out["reviewed_preview_row_count"] == 0


def test_build_342j_allows_source_trace_warning(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    post_human_review_342i_dir = _seed_342i_ready(repo_root, source_trace_missing=True)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_reviewed_client_preview_pilot_342j(
        post_human_review_342i_dir=post_human_review_342i_dir,
        output_dir=repo_root / "output" / "table_first_reviewed_client_preview_pilot_342j",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["source_trace_missing_count"] == 1
    assert summary["ready_for_342k"] is True
    assert artifacts["qa_json"]["qa_fail_count"] == 0
