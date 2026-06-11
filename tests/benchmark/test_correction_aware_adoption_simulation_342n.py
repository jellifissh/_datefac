from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.correction_aware_adoption_simulation_342n import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    UNIT_MILLION_CNY,
    UNIT_PERCENT,
    UNIT_YI_CNY,
    build_correction_aware_adoption_simulation_342n,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)


def _spot_template_row(index: int) -> dict[str, object]:
    return {
        "spot_check_id": f"spot_{index:03d}",
        "review_item_id": f"spot_item_{index:03d}",
        "spot_check_reason": "policy_sample",
        "original_suggestion": "CONFIRM_CELL",
        "rule_suggested_decision": "CONFIRM_CELL",
        "dry_run_suggested_decision": "CONFIRM_CELL",
        "suggested_metric_standardized": "revenue_yoy" if index <= 31 else ("revenue" if index == 32 else ("net_profit" if index == 33 else "ROE")),
        "suggested_year_standardized": "2025A",
        "suggested_value_numeric": float(index),
        "suggested_normalized_unit": UNIT_YI_CNY if index <= 31 else UNIT_PERCENT,
        "suggested_confidence": 0.99,
        "source_page": 1,
        "bbox": "[1,2,3,4]",
        "image_path": "img.jpg",
        "source_html_snippet": "<table>spot</table>",
        "risk_flags": "",
        "review_reason": "sample",
    }


def _spot_apply_row(index: int) -> dict[str, object]:
    if index <= 31:
        decision = "CORRECT_SUGGESTION"
        metric = "revenue"
        unit = UNIT_YI_CNY
    elif index == 32:
        decision = "CORRECT_SUGGESTION"
        metric = "revenue_yoy"
        unit = UNIT_PERCENT
    elif index == 33:
        decision = "CORRECT_SUGGESTION"
        metric = "net_profit_yoy"
        unit = UNIT_PERCENT
    else:
        decision = "CONFIRM_SUGGESTION"
        metric = ""
        unit = ""
    return {
        "review_item_id": f"spot_item_{index:03d}",
        "reviewer_decision": decision,
        "reviewer_metric_standardized": metric,
        "reviewer_year_standardized": "2025A" if decision == "CORRECT_SUGGESTION" else "",
        "reviewer_value_numeric": float(index) if decision == "CORRECT_SUGGESTION" else "",
        "reviewer_normalized_unit": unit,
        "reviewer_note": "reviewed",
        "reviewer_id": "tester",
        "reviewed_at": f"2026-06-11T09:{index % 60:02d}:00",
        "validation_status": "PASS",
        "validation_detail": "",
    }


def _adoption_candidate_row(index: int) -> dict[str, object]:
    if index <= 58:
        metric = "revenue_yoy"
        unit = UNIT_YI_CNY
    elif index <= 68:
        metric = "revenue"
        unit = UNIT_PERCENT
    elif index <= 78:
        metric = "net_profit"
        unit = UNIT_PERCENT
    elif index <= 185:
        metric = "ROE"
        unit = UNIT_PERCENT
    else:
        metric = "gross_margin"
        unit = UNIT_YI_CNY
    return {
        "review_item_id": f"candidate_{index:03d}",
        "adoption_status": "ELIGIBLE_FOR_NEXT_STAGE_SIMULATION",
        "rule_suggested_decision": "CONFIRM_CELL",
        "dry_run_suggested_decision": "CONFIRM_CELL",
        "suggested_metric_standardized": metric,
        "suggested_year_standardized": "2025A",
        "suggested_value_numeric": float(index),
        "suggested_normalized_unit": unit,
        "suggested_confidence": 0.99,
        "candidate_reason": "clean_case",
        "risk_flags": "",
        "not_final_confirmation": True,
    }


def _auto_candidate_row(index: int) -> dict[str, object]:
    return {
        "review_item_id": f"candidate_{index:03d}",
        "source_page": 1,
        "bbox": "[1,2,3,4]",
        "image_path": f"img_{index:03d}.jpg",
        "source_html_snippet": "<table>candidate</table>",
        "file_name": "doc.pdf",
        "table_id": f"t_{index:03d}",
        "table_type": "INCOME_STATEMENT",
    }


def _seed_342n_inputs(root: Path, *, ready_342m: bool = True) -> tuple[Path, Path, Path, Path]:
    spot_check_gate_342m_dir = root / "output" / "llm_suggestion_spot_check_gate_342m"
    llm_suggestion_342l_dir = root / "output" / "llm_suggestion_apply_simulation_342l"
    llm_review_342k_dir = root / "output" / "llm_assisted_review_adjudication_342k"
    reviewed_preview_342j_dir = root / "output" / "table_first_reviewed_client_preview_pilot_342j"
    for path in [
        spot_check_gate_342m_dir,
        llm_suggestion_342l_dir,
        llm_review_342k_dir,
        reviewed_preview_342j_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    summary_342m = {
        "decision": "LLM_SUGGESTION_SPOT_CHECK_APPLY_342M_READY" if ready_342m else "LLM_SUGGESTION_SPOT_CHECK_GATE_342M_WAITING_FOR_EVIDENCE",
        "pending_review_count": 1075,
        "auto_confirm_candidate_count": 254,
        "spot_check_sample_count": 50,
        "reviewed_spot_check_count": 50 if ready_342m else 0,
        "spot_check_confirm_count": 17 if ready_342m else 0,
        "spot_check_correct_count": 33 if ready_342m else 0,
        "spot_check_reject_count": 0,
        "spot_check_validation_error_count": 0,
        "response_count": 0,
        "valid_llm_response_count": 0,
        "adoption_candidate_count": 254,
        "blocked_candidate_count": 0,
        "risk_adjusted_reduction_count": 254,
        "required_human_review_after_gate": 821,
        "conservative_reduction_rate_after_gate": 0.236279,
        "waiting_for_human_spot_check": not ready_342m,
        "waiting_for_real_llm_responses": True,
        "ready_for_342n": ready_342m,
        "recommended_342n_scope": "spot_check_adoption_simulation_or_real_llm_response_apply" if ready_342m else "collect_spot_check_or_real_llm_responses",
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0 if ready_342m else 1,
    }
    _write_json(spot_check_gate_342m_dir / "llm_suggestion_spot_check_gate_342m_summary.json", summary_342m)
    _write_json(spot_check_gate_342m_dir / "llm_suggestion_spot_check_gate_342m_qa.json", {"qa_fail_count": 0 if ready_342m else 1, "checks": []})
    _write_json(spot_check_gate_342m_dir / "llm_suggestion_spot_check_gate_342m_no_write_back_proof.json", {"upstream_workbooks_unchanged": True})
    (spot_check_gate_342m_dir / "llm_suggestion_spot_check_gate_342m_report.md").write_text("342M report", encoding="utf-8")

    spot_template_df = pd.DataFrame([_spot_template_row(index) for index in range(1, 51)])
    spot_apply_df = pd.DataFrame([_spot_apply_row(index) for index in range(1, 51)])
    adoption_candidates_df = pd.DataFrame([_adoption_candidate_row(index) for index in range(1, 255)])
    _write_excel(
        spot_check_gate_342m_dir / "llm_suggestion_spot_check_gate_342m.xlsx",
        {
            "01_GATE_SUMMARY": pd.DataFrame([summary_342m]),
            "03_SPOT_CHECK_TEMPLATE": spot_template_df,
            "04_SPOT_CHECK_APPLY": spot_apply_df,
            "09_ADOPTION_CANDIDATES": adoption_candidates_df,
            "12_REDUCTION_AFTER_GATE": pd.DataFrame([{"risk_adjusted_reduction_count": 254}]),
            "13_342N_READINESS": pd.DataFrame([{"ready_for_342n": ready_342m}]),
            "14_NO_WRITE_BACK": pd.DataFrame([{"proof": True}]),
        },
    )

    summary_342l = {
        "decision": "LLM_SUGGESTION_APPLY_SIMULATION_342L_READY",
        "pending_review_count": 1075,
        "auto_confirm_candidate_count": 254,
        "spot_check_sample_count": 50,
        "human_required_count": 717,
        "conflict_count": 763,
        "qa_fail_count": 0,
        "client_ready": False,
        "production_ready": False,
    }
    _write_json(llm_suggestion_342l_dir / "llm_suggestion_apply_simulation_342l_summary.json", summary_342l)
    _write_json(llm_suggestion_342l_dir / "llm_suggestion_apply_simulation_342l_qa.json", {"qa_fail_count": 0, "checks": []})
    _write_excel(
        llm_suggestion_342l_dir / "llm_suggestion_apply_simulation_342l.xlsx",
        {"03_AUTO_CANDIDATES": pd.DataFrame([_auto_candidate_row(index) for index in range(1, 255)])},
    )

    _write_json(llm_review_342k_dir / "llm_assisted_review_adjudication_342k_summary.json", {"decision": "LLM_ASSISTED_REVIEW_ADJUDICATION_342K_READY", "qa_fail_count": 0})
    _write_json(llm_review_342k_dir / "llm_assisted_review_adjudication_342k_qa.json", {"qa_fail_count": 0, "checks": []})
    _write_excel(llm_review_342k_dir / "llm_assisted_review_adjudication_342k.xlsx", {"01_PLACEHOLDER": pd.DataFrame([{"ok": True}])})

    summary_342j = {
        "decision": "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY",
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
    }
    _write_json(reviewed_preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_summary.json", summary_342j)

    alias_asset = root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})
    return (
        spot_check_gate_342m_dir,
        llm_suggestion_342l_dir,
        llm_review_342k_dir,
        reviewed_preview_342j_dir,
    )


def test_build_342n_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    spot_check_gate_342m_dir, llm_suggestion_342l_dir, llm_review_342k_dir, reviewed_preview_342j_dir = _seed_342n_inputs(repo_root)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    artifacts = build_correction_aware_adoption_simulation_342n(
        spot_check_gate_342m_dir=spot_check_gate_342m_dir,
        llm_suggestion_342l_dir=llm_suggestion_342l_dir,
        llm_review_342k_dir=llm_review_342k_dir,
        reviewed_preview_342j_dir=reviewed_preview_342j_dir,
        output_dir=repo_root / "output" / "correction_aware_adoption_simulation_342n",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["pending_review_count"] == 1075
    assert summary["input_adoption_candidate_count"] == 254
    assert summary["spot_check_sample_count"] == 50
    assert summary["spot_check_confirm_count"] == 17
    assert summary["spot_check_correct_count"] == 33
    assert summary["spot_check_correction_rate"] == 0.66
    assert summary["direct_adopt_sim_count"] == 107
    assert summary["correction_adopt_sim_count"] == 78
    assert summary["still_human_required_count"] == 69
    assert summary["adoption_sim_total_count"] == 185
    assert summary["REVENUE_AMOUNT_NOT_YOY_count"] == 31
    assert summary["REVENUE_YOY_PERCENT_count"] == 1
    assert summary["NET_PROFIT_YOY_PERCENT_count"] == 1
    assert summary["risk_adjusted_reduction_count"] == 185
    assert summary["required_human_review_after_342n"] == 890
    assert summary["conservative_reduction_rate_after_342n"] == 0.172093
    assert summary["ready_for_342o"] is True
    assert summary["qa_fail_count"] == 0
    assert summary["no_write_back_proof_passed"] is True

    direct_df = artifacts["workbook_sheets"]["05_DIRECT_ADOPT_SIM"]
    correction_df = artifacts["workbook_sheets"]["06_CORRECTION_ADOPT_SIM"]
    human_df = artifacts["workbook_sheets"]["07_STILL_HUMAN_REQUIRED"]
    assert direct_df["not_final_confirmation"].astype(bool).all()
    assert correction_df["correction_pattern"].astype(str).isin(
        ["REVENUE_AMOUNT_NOT_YOY", "REVENUE_YOY_PERCENT", "NET_PROFIT_YOY_PERCENT"]
    ).all()
    assert human_df["auto_apply_allowed"].astype(bool).eq(False).all()


def test_build_342n_not_ready_when_342m_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    spot_check_gate_342m_dir, llm_suggestion_342l_dir, llm_review_342k_dir, reviewed_preview_342j_dir = _seed_342n_inputs(
        repo_root,
        ready_342m=False,
    )
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    artifacts = build_correction_aware_adoption_simulation_342n(
        spot_check_gate_342m_dir=spot_check_gate_342m_dir,
        llm_suggestion_342l_dir=llm_suggestion_342l_dir,
        llm_review_342k_dir=llm_review_342k_dir,
        reviewed_preview_342j_dir=reviewed_preview_342j_dir,
        output_dir=repo_root / "output" / "correction_aware_adoption_simulation_342n",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == NOT_READY_DECISION
    assert summary["ready_for_342o"] is False
    assert summary["input_adoption_candidate_count"] == 0
    assert summary["adoption_sim_total_count"] == 0
    assert summary["qa_fail_count"] > 0
