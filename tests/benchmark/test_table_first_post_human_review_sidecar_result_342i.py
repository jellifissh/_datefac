from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.table_first_post_human_review_sidecar_result_342i import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_table_first_post_human_review_sidecar_result_342i,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _seed_342h_ready(root: Path) -> Path:
    output_dir = root / "output" / "table_first_human_review_apply_simulation_342h"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "decision": "TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_READY",
        "ready_for_342i": True,
        "input_review_template_row_count": 5,
        "reviewed_row_count": 3,
        "pending_review_count": 2,
        "confirmed_cell_count": 2,
        "corrected_cell_count": 1,
        "rejected_cell_count": 0,
        "still_review_required_count": 0,
        "needs_source_check_count": 0,
        "validation_error_count": 0,
        "qa_fail_count": 0,
    }
    _write_json(output_dir / "table_first_human_review_apply_simulation_342h_summary.json", summary)
    _write_json(output_dir / "table_first_human_review_apply_simulation_342h_qa.json", {"qa_fail_count": 0, "checks": []})
    _write_json(
        output_dir / "table_first_human_review_apply_simulation_342h_no_write_back_proof.json",
        {"upstream_workbooks_unchanged": True, "no_official_asset_modification_during_342h": True},
    )
    (output_dir / "table_first_human_review_apply_simulation_342h_report.md").write_text("342H report", encoding="utf-8")

    confirmed_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_1",
                "human_status": "HUMAN_CONFIRMED_CELL",
                "reviewer_decision": "CONFIRM_CELL",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "metric_raw": "Revenue",
                "metric_standardized": "revenue",
                "year_standardized": "2024A",
                "value_numeric": 100.0,
                "normalized_unit": "百万元",
                "final_metric_standardized": "revenue",
                "final_year_standardized": "2024A",
                "final_value_numeric": 100.0,
                "final_normalized_unit": "百万元",
                "reviewer_note": "ok",
                "reviewer_id": "r1",
                "reviewed_at": "2026-06-10 11:15:10 UTC",
                "source_html_snippet": "<table>rev</table>",
            },
            {
                "review_item_id": "item_2",
                "human_status": "HUMAN_CONFIRMED_CELL",
                "reviewer_decision": "CONFIRM_CELL",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "metric_raw": "ROE",
                "metric_standardized": "ROE",
                "year_standardized": "2025A",
                "value_numeric": 10.5,
                "normalized_unit": "%",
                "final_metric_standardized": "ROE",
                "final_year_standardized": "2025A",
                "final_value_numeric": 10.5,
                "final_normalized_unit": "%",
                "reviewer_note": "ok",
                "reviewer_id": "r1",
                "reviewed_at": "2026-06-10 11:15:10 UTC",
                "source_html_snippet": "<table>roe</table>",
            },
        ]
    )
    corrected_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_3",
                "human_status": "HUMAN_CORRECTED_CONFIRMED_CELL",
                "reviewer_decision": "CORRECT_AND_CONFIRM",
                "corpus_pdf_id": "pdf_2",
                "file_name": "doc2.pdf",
                "table_id": "t2",
                "table_type": "INCOME_STATEMENT",
                "source_page": 2,
                "bbox": "[2,3,4,5]",
                "image_path": "img2.jpg",
                "metric_raw": "收入增长",
                "metric_standardized": "revenue",
                "year_standardized": "2024A",
                "value_numeric": 46.0,
                "normalized_unit": "",
                "reviewer_metric_standardized": "revenue_yoy",
                "reviewer_year_standardized": "2024A",
                "reviewer_value_numeric": 46.0,
                "reviewer_normalized_unit": "%",
                "final_metric_standardized": "revenue_yoy",
                "final_year_standardized": "2024A",
                "final_value_numeric": 46.0,
                "final_normalized_unit": "%",
                "reviewer_note": "fix",
                "reviewer_id": "r2",
                "reviewed_at": "2026-06-10 11:15:10 UTC",
                "source_html_snippet": "<table>growth</table>",
            }
        ]
    )
    pending_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_4",
                "review_priority": "HIGH",
                "review_bucket": "DUPLICATE_REVIEW",
                "metric_raw": "PE",
                "metric_standardized": "",
                "year_standardized": "2024A",
                "normalized_unit": "",
                "risk_flags": "UNIT_MISSING|DUPLICATE_DROPPED",
                "review_reason": "REVIEW_REQUIRED_DUPLICATE",
                "human_status": "PENDING_REVIEW",
            },
            {
                "review_item_id": "item_5",
                "review_priority": "MEDIUM",
                "review_bucket": "GROWTH_ROW_REVIEW",
                "metric_raw": "收入增长",
                "metric_standardized": "",
                "year_standardized": "",
                "normalized_unit": "",
                "risk_flags": "UNIT_MISSING",
                "review_reason": "REVIEW_REQUIRED_UNIT_MISSING",
                "human_status": "PENDING_REVIEW",
            },
        ]
    )

    before_after_df = pd.DataFrame([{"input_review_template_row_count": 5, "reviewed_row_count": 3, "pending_review_count": 2}])
    trace_columns = [
        "review_item_id",
        "corpus_pdf_id",
        "file_name",
        "table_id",
        "table_type",
        "source_page",
        "bbox",
        "image_path",
        "source_html_snippet",
        "reviewer_decision",
        "human_status",
    ]
    source_trace_df = pd.concat(
        [
            confirmed_df[trace_columns],
            corrected_df[trace_columns],
        ],
        ignore_index=True,
    )
    readiness_df = pd.DataFrame([{"ready_for_342i": True, "recommended_342i_scope": "table_first_post_human_review_sidecar_result"}])
    no_write_back_df = pd.DataFrame([{"path": "x", "before_hash": "a", "after_hash": "a", "unchanged": True}])

    _write_excel(
        output_dir / "table_first_human_review_apply_simulation_342h.xlsx",
        {
            "01_APPLY_SUMMARY": pd.DataFrame([summary]),
            "03_VALIDATED_DECISIONS": pd.concat([confirmed_df, corrected_df], ignore_index=True),
            "04_CONFIRMED_CELLS": confirmed_df,
            "05_CORRECTED_CELLS": corrected_df,
            "06_REJECTED_CELLS": pd.DataFrame(),
            "07_STILL_REVIEW": pd.DataFrame(),
            "08_NEEDS_SOURCE_CHECK": pd.DataFrame(),
            "09_PENDING_REVIEW": pending_df,
            "10_REVIEW_ERRORS": pd.DataFrame(),
            "11_BEFORE_AFTER": before_after_df,
            "12_SOURCE_TRACE": source_trace_df,
            "13_342I_READINESS": readiness_df,
            "14_NO_WRITE_BACK": no_write_back_df,
        },
    )
    return output_dir


def test_build_342i_ready_with_partial_reviewed_batch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    human_review_342h_dir = _seed_342h_ready(repo_root)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_post_human_review_sidecar_result_342i(
        human_review_342h_dir=human_review_342h_dir,
        output_dir=repo_root / "output" / "table_first_post_human_review_sidecar_result_342i",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["final_confirmed_cell_count"] == 2
    assert summary["final_corrected_cell_count"] == 1
    assert summary["final_rejected_cell_count"] == 0
    assert summary["post_human_confirmed_count"] == 3
    assert summary["metric_covered_after_human_count"] == 3
    assert summary["metric_year_pair_after_human_count"] == 3
    assert summary["remaining_review_count"] == 2
    assert summary["duplicate_remaining_count"] == 1
    assert summary["growth_row_remaining_count"] == 1
    assert summary["ready_for_342j"] is True


def test_build_342i_not_ready_when_342h_is_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    human_review_342h_dir = _seed_342h_ready(repo_root)
    summary_path = human_review_342h_dir / "table_first_human_review_apply_simulation_342h_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["decision"] = "TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_WAITING_FOR_HUMAN_REVIEW"
    summary["ready_for_342i"] = False
    summary["reviewed_row_count"] = 0
    _write_json(summary_path, summary)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_post_human_review_sidecar_result_342i(
        human_review_342h_dir=human_review_342h_dir,
        output_dir=repo_root / "output" / "table_first_post_human_review_sidecar_result_342i",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == NOT_READY_DECISION
    assert summary["ready_for_342j"] is False
    assert summary["post_human_reviewed_cell_count"] == 0
