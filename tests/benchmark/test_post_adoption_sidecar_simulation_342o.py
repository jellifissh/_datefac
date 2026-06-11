from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.post_adoption_sidecar_simulation_342o import (  # noqa: E402
    EXPECTED_ADOPTION_SIM_TOTAL_COUNT,
    EXPECTED_CORRECTION_ADOPT_COUNT,
    EXPECTED_DIRECT_ADOPT_COUNT,
    EXPECTED_INPUT_ADOPTION_CANDIDATE_COUNT,
    EXPECTED_PENDING_REVIEW_COUNT,
    EXPECTED_STILL_HUMAN_REQUIRED_COUNT,
    NOT_READY_DECISION,
    READY_DECISION,
    build_post_adoption_sidecar_simulation_342o,
)
from datefac.benchmark.post_adoption_sidecar_simulation_342o_report import WORKBOOK_SHEETS  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _direct_row(index: int) -> dict[str, object]:
    if index <= 40:
        metric, unit = "ROE", "%"
    elif index <= 70:
        metric, unit = "EPS", "元"
    else:
        metric, unit = "gross_margin", "%"
    year = ["2024A", "2025A", "2026E", "2027E", "2028E"][(index - 1) % 5]
    return {
        "review_item_id": f"direct_{index:03d}",
        "rule_suggested_decision": "CONFIRM_CELL",
        "dry_run_suggested_decision": "CONFIRM_CELL",
        "suggested_metric_standardized": metric,
        "suggested_year_standardized": year,
        "suggested_value_numeric": float(index),
        "suggested_normalized_unit": unit,
        "suggested_confidence": 0.96,
        "candidate_reason": "safe_pair",
        "risk_flags": "",
        "not_final_confirmation": True,
        "source_page": 1,
        "bbox": "[1,2,3,4]",
        "image_path": f"direct_{index:03d}.jpg",
        "source_html_snippet": "<table>direct</table>",
        "simulation_status": "DIRECT_ADOPT_SIMULATION",
        "simulated_metric_standardized": metric,
        "simulated_year_standardized": year,
        "simulated_value_numeric": float(index),
        "simulated_normalized_unit": unit,
        "adoption_evidence": "safe metric/unit pair with no explicit correction pattern required",
        "adoption_confidence": 0.96,
    }


def _correction_row(index: int) -> dict[str, object]:
    if index <= 58:
        original_metric, original_unit = "revenue_yoy", "亿元"
        simulated_metric, simulated_unit = "revenue", "亿元"
        pattern = "REVENUE_AMOUNT_NOT_YOY"
        reason = "Spot-check pattern shows amount rows with unit 亿元 should map to revenue, not revenue_yoy."
    elif index <= 68:
        original_metric, original_unit = "revenue", "%"
        simulated_metric, simulated_unit = "revenue_yoy", "%"
        pattern = "REVENUE_YOY_PERCENT"
        reason = "Spot-check pattern shows revenue rows with % unit should map to revenue_yoy."
    else:
        original_metric, original_unit = "net_profit", "%"
        simulated_metric, simulated_unit = "net_profit_yoy", "%"
        pattern = "NET_PROFIT_YOY_PERCENT"
        reason = "Spot-check pattern shows net_profit rows with % unit should map to net_profit_yoy."
    year = ["2024A", "2025A", "2026E", "2027E", "2028E"][(index - 1) % 5]
    return {
        "review_item_id": f"corr_{index:03d}",
        "rule_suggested_decision": "CONFIRM_CELL",
        "dry_run_suggested_decision": "CONFIRM_CELL",
        "suggested_metric_standardized": original_metric,
        "suggested_year_standardized": year,
        "suggested_value_numeric": float(index) + 0.5,
        "suggested_normalized_unit": original_unit,
        "suggested_confidence": 0.96,
        "candidate_reason": "pattern_match",
        "risk_flags": "",
        "not_final_confirmation": True,
        "source_page": 2,
        "bbox": "[2,3,4,5]",
        "image_path": f"corr_{index:03d}.jpg",
        "source_html_snippet": "<table>correction</table>",
        "simulation_status": "CORRECTION_AWARE_ADOPT_SIMULATION",
        "simulated_metric_standardized": simulated_metric,
        "simulated_year_standardized": year,
        "simulated_value_numeric": float(index) + 0.5,
        "simulated_normalized_unit": simulated_unit,
        "correction_pattern": pattern,
        "adoption_evidence": f"{pattern} matched spot-check correction pattern.",
        "adoption_confidence": 0.96,
        "_correction_reason": reason,
    }


def _still_human_row(index: int) -> dict[str, object]:
    return {
        "review_item_id": f"human_{index:03d}",
        "human_required_reason": "no_safe_metric_unit_pair",
        "failed_pattern_reason": "UNRESOLVED_PATTERN",
        "recommended_human_action": "manual review required for unresolved metric/unit pattern",
        "auto_apply_allowed": False,
    }


def _seed_342o_inputs(root: Path, *, ready_342n: bool = True) -> tuple[Path, Path, Path, Path]:
    dir_342n = root / "output" / "correction_aware_adoption_simulation_342n"
    dir_342m = root / "output" / "llm_suggestion_spot_check_gate_342m"
    dir_342j = root / "output" / "table_first_reviewed_client_preview_pilot_342j"
    dir_342i = root / "output" / "table_first_post_human_review_sidecar_result_342i"
    for path in [dir_342n, dir_342m, dir_342j, dir_342i]:
        path.mkdir(parents=True, exist_ok=True)

    summary_342m = {
        "decision": "LLM_SUGGESTION_SPOT_CHECK_APPLY_342M_READY",
        "reviewed_spot_check_count": 50,
        "spot_check_correct_count": 33,
        "client_ready": False,
        "production_ready": False,
    }
    summary_342j = {
        "decision": "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY",
        "reviewed_preview_row_count": 41,
        "client_ready": False,
        "production_ready": False,
    }
    summary_342i = {
        "decision": "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY",
        "post_human_confirmed_count": 41,
        "client_ready": False,
        "production_ready": False,
    }
    _write_json(dir_342m / "llm_suggestion_spot_check_gate_342m_summary.json", summary_342m)
    _write_json(dir_342j / "table_first_reviewed_client_preview_pilot_342j_summary.json", summary_342j)
    _write_json(dir_342i / "table_first_post_human_review_sidecar_result_342i_summary.json", summary_342i)

    direct_rows = [_direct_row(index) for index in range(1, EXPECTED_DIRECT_ADOPT_COUNT + 1)]
    correction_rows = [_correction_row(index) for index in range(1, EXPECTED_CORRECTION_ADOPT_COUNT + 1)]
    still_human_rows = [_still_human_row(index) for index in range(1, EXPECTED_STILL_HUMAN_REQUIRED_COUNT + 1)]
    before_after_rows = [
        {
            "review_item_id": row["review_item_id"],
            "original_suggested_metric_standardized": row["suggested_metric_standardized"],
            "simulated_metric_standardized": row["simulated_metric_standardized"],
            "original_suggested_year_standardized": row["suggested_year_standardized"],
            "simulated_year_standardized": row["simulated_year_standardized"],
            "original_suggested_value_numeric": row["suggested_value_numeric"],
            "simulated_value_numeric": row["simulated_value_numeric"],
            "original_suggested_normalized_unit": row["suggested_normalized_unit"],
            "simulated_normalized_unit": row["simulated_normalized_unit"],
            "correction_pattern": row["correction_pattern"],
            "correction_reason": row["_correction_reason"],
        }
        for row in correction_rows
    ]

    summary_342n = {
        "decision": "CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY" if ready_342n else "CORRECTION_AWARE_ADOPTION_SIMULATION_342N_NOT_READY",
        "pending_review_count": EXPECTED_PENDING_REVIEW_COUNT,
        "input_adoption_candidate_count": EXPECTED_INPUT_ADOPTION_CANDIDATE_COUNT if ready_342n else 0,
        "spot_check_sample_count": 50,
        "spot_check_confirm_count": 17,
        "spot_check_correct_count": 33,
        "spot_check_reject_count": 0,
        "spot_check_correction_rate": 0.66,
        "direct_adopt_sim_count": EXPECTED_DIRECT_ADOPT_COUNT if ready_342n else 0,
        "correction_adopt_sim_count": EXPECTED_CORRECTION_ADOPT_COUNT if ready_342n else 0,
        "still_human_required_count": EXPECTED_STILL_HUMAN_REQUIRED_COUNT if ready_342n else 0,
        "adoption_sim_total_count": EXPECTED_ADOPTION_SIM_TOTAL_COUNT if ready_342n else 0,
        "REVENUE_AMOUNT_NOT_YOY_count": 58,
        "REVENUE_YOY_PERCENT_count": 10,
        "NET_PROFIT_YOY_PERCENT_count": 10,
        "risk_adjusted_reduction_count": EXPECTED_ADOPTION_SIM_TOTAL_COUNT if ready_342n else 0,
        "required_human_review_after_342n": 887 if ready_342n else EXPECTED_PENDING_REVIEW_COUNT,
        "conservative_reduction_rate_after_342n": 0.174884 if ready_342n else 0.0,
        "ready_for_342o": ready_342n,
        "recommended_342o_scope": "post_adoption_sidecar_simulation_or_review_template_generation" if ready_342n else "",
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0 if ready_342n else 1,
        "no_write_back_proof_passed": True,
    }
    _write_json(dir_342n / "correction_aware_adoption_simulation_342n_summary.json", summary_342n)
    _write_json(dir_342n / "correction_aware_adoption_simulation_342n_qa.json", {"qa_fail_count": 0 if ready_342n else 1, "checks": []})
    (dir_342n / "correction_aware_adoption_simulation_342n_report.md").write_text("342N report", encoding="utf-8")

    workbook_sheets = {
        "01_ADOPTION_SUMMARY": pd.DataFrame([summary_342n]),
        "03_SPOT_CHECK_PATTERNS": pd.DataFrame([{"pattern_name": "REVENUE_AMOUNT_NOT_YOY", "pattern_reason": "test"}]),
        "04_ADOPTION_INPUT": pd.DataFrame(
            [{"review_item_id": row["review_item_id"]} for row in direct_rows + correction_rows + still_human_rows]
        ),
        "05_DIRECT_ADOPT_SIM": pd.DataFrame(direct_rows),
        "06_CORRECTION_ADOPT_SIM": pd.DataFrame(
            [{key: value for key, value in row.items() if not key.startswith("_")} for row in correction_rows]
        ),
        "07_STILL_HUMAN_REQUIRED": pd.DataFrame(still_human_rows),
        "08_PATTERN_APPLICATION": pd.DataFrame([{"pattern_name": "REVENUE_AMOUNT_NOT_YOY", "applied_candidate_count": 58}]),
        "09_RISK_REVIEW": pd.DataFrame([{"risk": "simulation_only"}]),
        "10_BEFORE_AFTER_SIM": pd.DataFrame(before_after_rows),
        "11_REDUCTION_SIM": pd.DataFrame([{"required_human_review_after_342n": 887 if ready_342n else EXPECTED_PENDING_REVIEW_COUNT}]),
        "12_342O_READINESS": pd.DataFrame([{"ready_for_342o": ready_342n, "decision": summary_342n["decision"]}]),
        "13_NO_WRITE_BACK": pd.DataFrame([{"proof": True}]),
    }
    _write_excel(dir_342n / "correction_aware_adoption_simulation_342n.xlsx", workbook_sheets)

    alias_asset = root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})
    return dir_342n, dir_342m, dir_342j, dir_342i


def test_build_342o_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    dir_342n, dir_342m, dir_342j, dir_342i = _seed_342o_inputs(repo_root, ready_342n=True)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    artifacts = build_post_adoption_sidecar_simulation_342o(
        adoption_simulation_342n_dir=dir_342n,
        spot_check_gate_342m_dir=dir_342m,
        reviewed_preview_342j_dir=dir_342j,
        post_human_sidecar_342i_dir=dir_342i,
        output_dir=repo_root / "output" / "post_adoption_sidecar_simulation_342o",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["pending_review_count"] == EXPECTED_PENDING_REVIEW_COUNT
    assert summary["input_adoption_candidate_count"] == EXPECTED_INPUT_ADOPTION_CANDIDATE_COUNT
    assert summary["direct_adopted_count"] == EXPECTED_DIRECT_ADOPT_COUNT
    assert summary["corrected_adopted_count"] == EXPECTED_CORRECTION_ADOPT_COUNT
    assert summary["simulated_adopted_cell_count"] == EXPECTED_ADOPTION_SIM_TOTAL_COUNT
    assert summary["still_human_required_count"] == EXPECTED_STILL_HUMAN_REQUIRED_COUNT
    assert summary["remaining_review_count"] == 887
    assert summary["reduction_rate_after_342o"] == 0.174884
    assert summary["ready_for_342p"] is True
    assert summary["qa_fail_count"] == 0
    assert summary["no_write_back_proof_passed"] is True

    corrected_df = artifacts["workbook_sheets"]["05_CORRECTED_ADOPTED"]
    assert {
        ("revenue_yoy", "亿元", "revenue", "亿元"),
        ("revenue", "%", "revenue_yoy", "%"),
        ("net_profit", "%", "net_profit_yoy", "%"),
    }.issubset(
        {
            (
                str(row["original_suggested_metric_standardized"]),
                str(row["original_suggested_normalized_unit"]),
                str(row["simulated_metric_standardized"]),
                str(row["simulated_normalized_unit"]),
            )
            for row in corrected_df.to_dict(orient="records")
        }
    )
    assert all(name in WORKBOOK_SHEETS for name in artifacts["workbook_sheets"])


def test_build_342o_not_ready_when_342n_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    dir_342n, dir_342m, dir_342j, dir_342i = _seed_342o_inputs(repo_root, ready_342n=False)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    artifacts = build_post_adoption_sidecar_simulation_342o(
        adoption_simulation_342n_dir=dir_342n,
        spot_check_gate_342m_dir=dir_342m,
        reviewed_preview_342j_dir=dir_342j,
        post_human_sidecar_342i_dir=dir_342i,
        output_dir=repo_root / "output" / "post_adoption_sidecar_simulation_342o",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == NOT_READY_DECISION
    assert summary["ready_for_342p"] is False
    assert summary["simulated_adopted_cell_count"] == 0
    assert summary["qa_fail_count"] > 0


def test_build_342o_count_equalities_hold(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    dir_342n, dir_342m, dir_342j, dir_342i = _seed_342o_inputs(repo_root, ready_342n=True)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    artifacts = build_post_adoption_sidecar_simulation_342o(
        adoption_simulation_342n_dir=dir_342n,
        spot_check_gate_342m_dir=dir_342m,
        reviewed_preview_342j_dir=dir_342j,
        post_human_sidecar_342i_dir=dir_342i,
        output_dir=repo_root / "output" / "post_adoption_sidecar_simulation_342o",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["direct_adopted_count"] + summary["corrected_adopted_count"] == summary["simulated_adopted_cell_count"]
    assert summary["simulated_adopted_cell_count"] + summary["still_human_required_count"] == summary["input_adoption_candidate_count"]
    assert summary["remaining_review_count"] == summary["pending_review_count"] - summary["simulated_adopted_cell_count"]
    assert artifacts["qa_json"]["qa_fail_count"] == 0
