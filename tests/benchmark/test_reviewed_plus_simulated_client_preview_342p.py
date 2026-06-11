from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.reviewed_plus_simulated_client_preview_342p import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_reviewed_plus_simulated_client_preview_342p,
)
from datefac.benchmark.reviewed_plus_simulated_client_preview_342p_report import WORKBOOK_SHEETS  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _seed_ready_inputs(root: Path, *, with_collisions: bool = False) -> tuple[Path, Path, Path, Path]:
    dir_342o = root / "output" / "post_adoption_sidecar_simulation_342o"
    dir_342j = root / "output" / "table_first_reviewed_client_preview_pilot_342j"
    dir_342i = root / "output" / "table_first_post_human_review_sidecar_result_342i"
    dir_342n = root / "output" / "correction_aware_adoption_simulation_342n"
    for path in [dir_342o, dir_342j, dir_342i, dir_342n]:
        path.mkdir(parents=True, exist_ok=True)

    sim_total_count = 4 if with_collisions else 2
    summary_342o = {
        "decision": "POST_ADOPTION_SIDECAR_SIMULATION_342O_READY",
        "simulated_adopted_cell_count": sim_total_count,
        "direct_adopted_count": 3 if with_collisions else 2,
        "corrected_adopted_count": 1 if with_collisions else 0,
        "still_human_required_count": 1,
        "remaining_review_count": 9,
        "ready_for_342p": True,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
    }
    summary_342j = {
        "decision": "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY",
        "reviewed_preview_row_count": 1,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
    }
    summary_342i = {
        "decision": "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY",
        "post_human_confirmed_count": 1,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
    }
    summary_342n = {
        "decision": "CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY",
        "adoption_sim_total_count": sim_total_count,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
    }
    for path, payload in [
        (dir_342o / "post_adoption_sidecar_simulation_342o_summary.json", summary_342o),
        (dir_342o / "post_adoption_sidecar_simulation_342o_qa.json", {"qa_fail_count": 0, "checks": []}),
        (dir_342j / "table_first_reviewed_client_preview_pilot_342j_summary.json", summary_342j),
        (dir_342j / "table_first_reviewed_client_preview_pilot_342j_qa.json", {"qa_fail_count": 0, "checks": []}),
        (dir_342i / "table_first_post_human_review_sidecar_result_342i_summary.json", summary_342i),
        (dir_342i / "table_first_post_human_review_sidecar_result_342i_qa.json", {"qa_fail_count": 0, "checks": []}),
        (dir_342n / "correction_aware_adoption_simulation_342n_summary.json", summary_342n),
        (dir_342n / "correction_aware_adoption_simulation_342n_qa.json", {"qa_fail_count": 0, "checks": []}),
    ]:
        _write_json(path, payload)
    for path in [
        dir_342o / "post_adoption_sidecar_simulation_342o_report.md",
        dir_342j / "table_first_reviewed_client_preview_pilot_342j_report.md",
        dir_342i / "table_first_post_human_review_sidecar_result_342i_report.md",
        dir_342n / "correction_aware_adoption_simulation_342n_report.md",
    ]:
        path.write_text("ok", encoding="utf-8")

    human_preview_df = pd.DataFrame(
        [
            {
                "preview_row_id": "342j::preview::0001",
                "review_item_id": "human_1",
                "final_status": "POST_HUMAN_CONFIRMED",
                "reviewer_decision": "CONFIRM_CELL",
                "corpus_pdf_id": "342b_pdf_001",
                "file_name": "a.pdf",
                "table_id": "342b_pdf_001_content_list_001",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,1,1,1]",
                "image_path": "img1.jpg",
                "metric_raw": "ROE",
                "metric_standardized": "ROE",
                "year_standardized": "2024A",
                "value_numeric": 10.0,
                "normalized_unit": "%",
                "final_metric_standardized": "ROE",
                "final_year_standardized": "2024A",
                "final_value_numeric": 10.0,
                "final_normalized_unit": "%",
                "reviewer_note": "ok",
                "reviewer_id": "r1",
                "reviewed_at": "2026-06-11",
                "source_html_snippet": "<table>human</table>",
                "preview_confidence_label": "HUMAN_CONFIRMED",
                "preview_limit_note": "pilot",
            }
        ]
    )
    _write_excel(
        dir_342j / "table_first_reviewed_client_preview_pilot_342j.xlsx",
        {
            "00_README": pd.DataFrame(),
            "01_PREVIEW_SUMMARY": pd.DataFrame([summary_342j]),
            "02_INPUT_342I_SUMMARY": pd.DataFrame([summary_342i]),
            "03_REVIEWED_PREVIEW": human_preview_df,
        },
    )

    sim_adopted_rows = [
        {
            "sidecar_cell_id": "342o::sim::0001",
            "source_stage": "342N",
            "review_item_id": "sim_1",
            "simulation_status": "DIRECT_ADOPT_SIMULATION",
            "adoption_type": "DIRECT",
            "suggested_metric_standardized": "ROE" if with_collisions else "EPS",
            "suggested_year_standardized": "2024A",
            "suggested_value_numeric": 10.0 if with_collisions else 2.5,
            "suggested_normalized_unit": "%" if with_collisions else "元",
            "simulated_metric_standardized": "ROE" if with_collisions else "EPS",
            "simulated_year_standardized": "2024A",
            "simulated_value_numeric": 10.0 if with_collisions else 2.5,
            "simulated_normalized_unit": "%" if with_collisions else "元",
            "correction_pattern": "",
            "adoption_evidence": "safe",
            "adoption_confidence": 0.96,
            "not_final_confirmation": True,
            "final_confirmed": False,
            "human_confirmed": False,
            "client_ready": False,
            "production_ready": False,
            "source_page": 1 if with_collisions else 2,
            "bbox": "[1,1,1,1]" if with_collisions else "[2,2,2,2]",
            "image_path": "img2.jpg",
            "source_html_snippet": "<table>sim1</table>",
        },
        {
            "sidecar_cell_id": "342o::sim::0002",
            "source_stage": "342N",
            "review_item_id": "sim_2",
            "simulation_status": "DIRECT_ADOPT_SIMULATION" if not with_collisions else "CORRECTION_AWARE_ADOPT_SIMULATION",
            "adoption_type": "DIRECT" if not with_collisions else "CORRECTION_AWARE",
            "suggested_metric_standardized": "revenue_yoy" if with_collisions else "revenue",
            "suggested_year_standardized": "2024A",
            "suggested_value_numeric": 18.0 if with_collisions else 100.0,
            "suggested_normalized_unit": "亿元",
            "simulated_metric_standardized": "revenue" if with_collisions else "revenue",
            "simulated_year_standardized": "2024A",
            "simulated_value_numeric": 18.0 if with_collisions else 100.0,
            "simulated_normalized_unit": "亿元",
            "correction_pattern": "REVENUE_AMOUNT_NOT_YOY" if with_collisions else "",
            "adoption_evidence": "pattern" if with_collisions else "safe",
            "adoption_confidence": 0.96,
            "not_final_confirmation": True,
            "final_confirmed": False,
            "human_confirmed": False,
            "client_ready": False,
            "production_ready": False,
            "source_page": 4 if with_collisions else 3,
            "bbox": "[4,4,4,4]" if with_collisions else "[3,3,3,3]",
            "image_path": "img3.jpg",
            "source_html_snippet": "<table>sim2</table>",
        },
    ]
    if with_collisions:
        sim_adopted_rows.append(
            {
                "sidecar_cell_id": "342o::sim::0003",
                "source_stage": "342N",
                "review_item_id": "sim_3",
                "simulation_status": "DIRECT_ADOPT_SIMULATION",
                "adoption_type": "DIRECT",
                "suggested_metric_standardized": "revenue",
                "suggested_year_standardized": "2024A",
                "suggested_value_numeric": 18.0,
                "suggested_normalized_unit": "亿元",
                "simulated_metric_standardized": "revenue",
                "simulated_year_standardized": "2024A",
                "simulated_value_numeric": 18.0,
                "simulated_normalized_unit": "亿元",
                "correction_pattern": "",
                "adoption_evidence": "safe",
                "adoption_confidence": 0.96,
                "not_final_confirmation": True,
                "final_confirmed": False,
                "human_confirmed": False,
                "client_ready": False,
                "production_ready": False,
                "source_page": 4,
                "bbox": "[4,4,4,4]",
                "image_path": "img4.jpg",
                "source_html_snippet": "<table>sim3</table>",
            }
        )
        sim_adopted_rows.append(
            {
                "sidecar_cell_id": "342o::sim::0004",
                "source_stage": "342N",
                "review_item_id": "sim_4",
                "simulation_status": "DIRECT_ADOPT_SIMULATION",
                "adoption_type": "DIRECT",
                "suggested_metric_standardized": "EPS",
                "suggested_year_standardized": "2025A",
                "suggested_value_numeric": 3.0,
                "suggested_normalized_unit": "元",
                "simulated_metric_standardized": "EPS",
                "simulated_year_standardized": "2025A",
                "simulated_value_numeric": 3.0,
                "simulated_normalized_unit": "元",
                "correction_pattern": "",
                "adoption_evidence": "safe",
                "adoption_confidence": 0.96,
                "not_final_confirmation": True,
                "final_confirmed": False,
                "human_confirmed": False,
                "client_ready": False,
                "production_ready": False,
                "source_page": 5,
                "bbox": "[5,5,5,5]",
                "image_path": "img5.jpg",
                "source_html_snippet": "<table>sim4</table>",
            }
        )
    direct_df = pd.DataFrame([row for row in sim_adopted_rows if row["adoption_type"] == "DIRECT"])[
        [
            "review_item_id",
            "simulated_metric_standardized",
            "simulated_year_standardized",
            "simulated_value_numeric",
            "simulated_normalized_unit",
            "adoption_confidence",
            "adoption_evidence",
            "not_final_confirmation",
        ]
    ]
    corrected_df = pd.DataFrame([row for row in sim_adopted_rows if row["adoption_type"] == "CORRECTION_AWARE"])
    if corrected_df.empty:
        corrected_preview_df = pd.DataFrame(
            columns=[
                "review_item_id",
                "original_suggested_metric_standardized",
                "simulated_metric_standardized",
                "original_suggested_normalized_unit",
                "simulated_normalized_unit",
                "simulated_year_standardized",
                "simulated_value_numeric",
                "correction_pattern",
                "correction_reason",
                "adoption_evidence",
                "adoption_confidence",
                "not_final_confirmation",
            ]
        )
    else:
        corrected_preview_df = corrected_df.assign(
            original_suggested_metric_standardized="revenue_yoy",
            original_suggested_normalized_unit="亿元",
            correction_reason="pattern",
        )[
            [
                "review_item_id",
                "original_suggested_metric_standardized",
                "simulated_metric_standardized",
                "original_suggested_normalized_unit",
                "simulated_normalized_unit",
                "simulated_year_standardized",
                "simulated_value_numeric",
                "correction_pattern",
                "correction_reason",
                "adoption_evidence",
                "adoption_confidence",
                "not_final_confirmation",
            ]
        ]
    _write_excel(
        dir_342o / "post_adoption_sidecar_simulation_342o.xlsx",
        {
            "01_SIDECAR_SUMMARY": pd.DataFrame([summary_342o]),
            "03_SIM_ADOPTED_CELLS": pd.DataFrame(sim_adopted_rows),
            "04_DIRECT_ADOPTED": direct_df,
            "05_CORRECTED_ADOPTED": corrected_preview_df,
            "06_STILL_HUMAN_REQUIRED": pd.DataFrame(
                [{"review_item_id": "human_required_1", "human_required_reason": "manual", "failed_pattern_reason": "UNRESOLVED", "recommended_human_action": "review", "auto_apply_allowed": False}]
            ),
            "07_BEFORE_AFTER_TRACE": pd.DataFrame(),
            "08_METRIC_COVERAGE": pd.DataFrame(),
            "09_REMAINING_REVIEW": pd.DataFrame(),
            "10_RISK_BOUNDARY": pd.DataFrame(),
            "11_342P_READINESS": pd.DataFrame(),
            "12_NO_WRITE_BACK": pd.DataFrame(),
        },
    )

    adoption_input_rows = [
        {
            "review_item_id": "sim_1",
            "source_page": 1 if with_collisions else 2,
            "bbox": "[1,1,1,1]" if with_collisions else "[2,2,2,2]",
            "image_path": "img2.jpg",
            "source_html_snippet": "<table>sim1</table>",
            "file_name": "b.pdf",
            "table_id": "342b_pdf_002_content_list_002",
            "table_type": "VALUATION_METRICS",
        },
        {
            "review_item_id": "sim_2",
            "source_page": 4 if with_collisions else 3,
            "bbox": "[4,4,4,4]" if with_collisions else "[3,3,3,3]",
            "image_path": "img3.jpg",
            "source_html_snippet": "<table>sim2</table>",
            "file_name": "c.pdf",
            "table_id": "342b_pdf_003_content_list_003",
            "table_type": "INCOME_STATEMENT",
        },
    ]
    if with_collisions:
        adoption_input_rows.append(
            {
                "review_item_id": "sim_3",
                "source_page": 4,
                "bbox": "[4,4,4,4]",
                "image_path": "img4.jpg",
                "source_html_snippet": "<table>sim3</table>",
                "file_name": "d.pdf",
                "table_id": "342b_pdf_004_content_list_004",
                "table_type": "INCOME_STATEMENT",
            }
        )
        adoption_input_rows.append(
            {
                "review_item_id": "sim_4",
                "source_page": 5,
                "bbox": "[5,5,5,5]",
                "image_path": "img5.jpg",
                "source_html_snippet": "<table>sim4</table>",
                "file_name": "e.pdf",
                "table_id": "342b_pdf_005_content_list_005",
                "table_type": "VALUATION_METRICS",
            }
        )
    before_after_rows = []
    if with_collisions:
        before_after_rows.append(
            {
                "review_item_id": "sim_2",
                "original_suggested_metric_standardized": "revenue_yoy",
                "simulated_metric_standardized": "revenue",
                "original_suggested_year_standardized": "2024A",
                "simulated_year_standardized": "2024A",
                "original_suggested_value_numeric": 18.0,
                "simulated_value_numeric": 18.0,
                "original_suggested_normalized_unit": "亿元",
                "simulated_normalized_unit": "亿元",
                "correction_pattern": "REVENUE_AMOUNT_NOT_YOY",
                "correction_reason": "pattern",
            }
        )
    _write_excel(
        dir_342n / "correction_aware_adoption_simulation_342n.xlsx",
        {
            "04_ADOPTION_INPUT": pd.DataFrame(adoption_input_rows),
            "05_DIRECT_ADOPT_SIM": pd.DataFrame(
                [
                    {
                        "review_item_id": row["review_item_id"],
                        "simulated_metric_standardized": row["simulated_metric_standardized"],
                        "simulated_year_standardized": row["simulated_year_standardized"],
                        "simulated_value_numeric": row["simulated_value_numeric"],
                        "simulated_normalized_unit": row["simulated_normalized_unit"],
                    }
                    for row in sim_adopted_rows
                    if row["adoption_type"] == "DIRECT"
                ]
            ),
            "06_CORRECTION_ADOPT_SIM": pd.DataFrame(
                [
                    {
                        "review_item_id": row["review_item_id"],
                        "simulated_metric_standardized": row["simulated_metric_standardized"],
                        "simulated_year_standardized": row["simulated_year_standardized"],
                        "simulated_value_numeric": row["simulated_value_numeric"],
                        "simulated_normalized_unit": row["simulated_normalized_unit"],
                        "correction_pattern": row["correction_pattern"],
                    }
                    for row in sim_adopted_rows
                    if row["adoption_type"] == "CORRECTION_AWARE"
                ]
            ),
            "07_STILL_HUMAN_REQUIRED": pd.DataFrame(
                [{"review_item_id": "human_required_1", "human_required_reason": "manual", "failed_pattern_reason": "UNRESOLVED", "recommended_human_action": "review", "auto_apply_allowed": False}]
            ),
            "10_BEFORE_AFTER_SIM": pd.DataFrame(before_after_rows),
        },
    )

    _write_excel(
        dir_342i / "table_first_post_human_review_sidecar_result_342i.xlsx",
        {
            "03_HUMAN_REVIEWED_CELLS": pd.DataFrame([{"review_item_id": "human_1"}]),
            "04_FINAL_CONFIRMED": pd.DataFrame([{"review_item_id": "human_1"}]),
        },
    )
    return dir_342o, dir_342j, dir_342i, dir_342n


def test_build_342p_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    dir_342o, dir_342j, dir_342i, dir_342n = _seed_ready_inputs(repo_root, with_collisions=False)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_reviewed_plus_simulated_client_preview_342p(
        post_adoption_sidecar_342o_dir=dir_342o,
        reviewed_preview_342j_dir=dir_342j,
        post_human_sidecar_342i_dir=dir_342i,
        adoption_simulation_342n_dir=dir_342n,
        output_dir=repo_root / "output" / "reviewed_plus_simulated_client_preview_342p",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["human_reviewed_preview_count"] == 1
    assert summary["simulated_preview_count"] == 2
    assert summary["combined_preview_row_count"] == 3
    assert summary["still_human_required_count"] == 1
    assert summary["ready_for_342q"] is True
    assert summary["qa_fail_count"] == 0
    assert summary["no_write_back_proof_passed"] is True
    assert all(name in WORKBOOK_SHEETS for name in artifacts["workbook_sheets"])


def test_build_342p_not_ready_when_342o_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    dir_342o, dir_342j, dir_342i, dir_342n = _seed_ready_inputs(repo_root, with_collisions=False)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    summary_path = dir_342o / "post_adoption_sidecar_simulation_342o_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["decision"] = "POST_ADOPTION_SIDECAR_SIMULATION_342O_NOT_READY"
    summary["ready_for_342p"] = False
    summary["qa_fail_count"] = 1
    _write_json(summary_path, summary)

    artifacts = build_reviewed_plus_simulated_client_preview_342p(
        post_adoption_sidecar_342o_dir=dir_342o,
        reviewed_preview_342j_dir=dir_342j,
        post_human_sidecar_342i_dir=dir_342i,
        adoption_simulation_342n_dir=dir_342n,
        output_dir=repo_root / "output" / "reviewed_plus_simulated_client_preview_342p",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    assert artifacts["summary"]["decision"] == NOT_READY_DECISION
    assert artifacts["summary"]["ready_for_342q"] is False
    assert artifacts["summary"]["combined_preview_row_count"] == 0
    assert artifacts["qa_json"]["qa_fail_count"] > 0


def test_build_342p_collision_handling_prefers_human_then_corrected(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    dir_342o, dir_342j, dir_342i, dir_342n = _seed_ready_inputs(repo_root, with_collisions=True)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_reviewed_plus_simulated_client_preview_342p(
        post_adoption_sidecar_342o_dir=dir_342o,
        reviewed_preview_342j_dir=dir_342j,
        post_human_sidecar_342i_dir=dir_342i,
        adoption_simulation_342n_dir=dir_342n,
        output_dir=repo_root / "output" / "reviewed_plus_simulated_client_preview_342p",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    combined_df = artifacts["workbook_sheets"]["04_COMBINED_PREVIEW"]
    collision_df = artifacts["workbook_sheets"]["09_COLLISION_CHECK"]
    assert summary["decision"] == READY_DECISION
    assert summary["human_over_simulation_override_count"] == 1
    assert summary["simulated_duplicate_dropped_count"] == 1
    assert summary["combined_preview_row_count"] == 3
    assert "HUMAN_REVIEWED" in set(combined_df["preview_source_type"].astype(str))
    assert "SIMULATED_CORRECTED" in set(combined_df["preview_source_type"].astype(str))
    assert len(collision_df) >= 1
