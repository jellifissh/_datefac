from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
from uuid import uuid4

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.preview_audit_export_readiness_gate_342q import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_preview_audit_export_readiness_gate_342q,
)
from datefac.benchmark.preview_audit_export_readiness_gate_342q_report import WORKBOOK_SHEETS  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _seed_support_dir(base_dir: Path, *, summary_name: str, qa_name: str, report_name: str, workbook_name: str, summary: dict) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    _write_json(base_dir / summary_name, summary)
    _write_json(base_dir / qa_name, {"qa_fail_count": 0, "checks": []})
    (base_dir / report_name).write_text("ok", encoding="utf-8")
    _write_excel(base_dir / workbook_name, {"Sheet1": pd.DataFrame([{"ok": True}])})


def _seed_342q_inputs(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    dir_342p = root / "output" / "reviewed_plus_simulated_client_preview_342p"
    dir_342o = root / "output" / "post_adoption_sidecar_simulation_342o"
    dir_342j = root / "output" / "table_first_reviewed_client_preview_pilot_342j"
    dir_342i = root / "output" / "table_first_post_human_review_sidecar_result_342i"
    dir_342n = root / "output" / "correction_aware_adoption_simulation_342n"

    _seed_support_dir(
        dir_342o,
        summary_name="post_adoption_sidecar_simulation_342o_summary.json",
        qa_name="post_adoption_sidecar_simulation_342o_qa.json",
        report_name="post_adoption_sidecar_simulation_342o_report.md",
        workbook_name="post_adoption_sidecar_simulation_342o.xlsx",
        summary={
            "decision": "POST_ADOPTION_SIDECAR_SIMULATION_342O_READY",
            "simulated_adopted_cell_count": 3,
            "direct_adopted_count": 2,
            "corrected_adopted_count": 1,
            "still_human_required_count": 1,
            "remaining_review_count": 4,
            "client_ready": False,
            "production_ready": False,
            "qa_fail_count": 0,
        },
    )
    _seed_support_dir(
        dir_342j,
        summary_name="table_first_reviewed_client_preview_pilot_342j_summary.json",
        qa_name="table_first_reviewed_client_preview_pilot_342j_qa.json",
        report_name="table_first_reviewed_client_preview_pilot_342j_report.md",
        workbook_name="table_first_reviewed_client_preview_pilot_342j.xlsx",
        summary={
            "decision": "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY",
            "reviewed_preview_row_count": 1,
            "client_ready": False,
            "production_ready": False,
            "qa_fail_count": 0,
        },
    )
    _seed_support_dir(
        dir_342i,
        summary_name="table_first_post_human_review_sidecar_result_342i_summary.json",
        qa_name="table_first_post_human_review_sidecar_result_342i_qa.json",
        report_name="table_first_post_human_review_sidecar_result_342i_report.md",
        workbook_name="table_first_post_human_review_sidecar_result_342i.xlsx",
        summary={
            "decision": "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY",
            "post_human_confirmed_count": 1,
            "client_ready": False,
            "production_ready": False,
            "qa_fail_count": 0,
        },
    )
    _seed_support_dir(
        dir_342n,
        summary_name="correction_aware_adoption_simulation_342n_summary.json",
        qa_name="correction_aware_adoption_simulation_342n_qa.json",
        report_name="correction_aware_adoption_simulation_342n_report.md",
        workbook_name="correction_aware_adoption_simulation_342n.xlsx",
        summary={
            "decision": "CORRECTION_AWARE_ADOPTION_SIMULATION_342N_READY",
            "adoption_sim_total_count": 3,
            "client_ready": False,
            "production_ready": False,
            "qa_fail_count": 0,
        },
    )

    combined_preview_df = pd.DataFrame(
        [
            {
                "preview_row_id": "342j::preview::0001",
                "review_item_id": "human_1",
                "preview_source_type": "HUMAN_REVIEWED",
                "data_trust_level": "HUMAN_REVIEWED",
                "review_status_for_client_display": "REVIEWED",
                "display_warning": "human reviewed pilot row; not full client export",
                "metric_standardized": "ROE",
                "year_standardized": "2024A",
                "value_numeric": 10.0,
                "normalized_unit": "%",
                "not_final_confirmation": False,
                "client_ready": False,
                "production_ready": False,
                "included_in_combined_preview": False,
            },
            {
                "preview_row_id": "342p::sim_direct::0001",
                "review_item_id": "sim_1",
                "preview_source_type": "SIMULATED_DIRECT",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "review_status_for_client_display": "SIMULATED",
                "display_warning": "simulation only; requires later audit before client delivery",
                "metric_standardized": "EPS",
                "year_standardized": "2025A",
                "value_numeric": 2.5,
                "normalized_unit": "元",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "included_in_combined_preview": False,
            },
            {
                "preview_row_id": "342p::sim_corrected::0001",
                "review_item_id": "sim_2",
                "preview_source_type": "SIMULATED_CORRECTED",
                "data_trust_level": "SIMULATED_CORRECTION_ADOPTED",
                "review_status_for_client_display": "SIMULATED_CORRECTED",
                "display_warning": "simulation only; requires later audit before client delivery",
                "metric_standardized": "revenue",
                "year_standardized": "2025A",
                "value_numeric": 100.0,
                "normalized_unit": "亿元",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "included_in_combined_preview": False,
            },
        ]
    )
    human_df = combined_preview_df[combined_preview_df["preview_source_type"] == "HUMAN_REVIEWED"].copy()
    sim_direct_df = pd.DataFrame(
        [
            {
                "preview_row_id": "342p::sim_direct::0001",
                "review_item_id": "sim_1",
                "preview_source_type": "SIMULATED_DIRECT",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "review_status_for_client_display": "SIMULATED",
                "display_warning": "simulation only; requires later audit before client delivery",
                "metric_standardized": "EPS",
                "year_standardized": "2025A",
                "value_numeric": 2.5,
                "normalized_unit": "元",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "dropped_reason": "",
                "winner_preview_row_id": "342p::sim_direct::0001",
                "collision_key": "EPS||2025A||2.5||元",
            },
            {
                "preview_row_id": "342p::sim_direct::0002",
                "review_item_id": "sim_dup",
                "preview_source_type": "SIMULATED_DIRECT",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "review_status_for_client_display": "SIMULATED",
                "display_warning": "simulation only; requires later audit before client delivery",
                "metric_standardized": "ROE",
                "year_standardized": "2024A",
                "value_numeric": 10.0,
                "normalized_unit": "%",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "dropped_reason": "DUPLICATE_METRIC_YEAR_VALUE_SOURCE",
                "winner_preview_row_id": "342j::preview::0001",
                "collision_key": "ROE||2024A||10||%",
            },
            {
                "preview_row_id": "342p::sim_direct::0003",
                "review_item_id": "sim_dup_sim",
                "preview_source_type": "SIMULATED_DIRECT",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "review_status_for_client_display": "SIMULATED",
                "display_warning": "simulation only; requires later audit before client delivery",
                "metric_standardized": "revenue",
                "year_standardized": "2025A",
                "value_numeric": 100.0,
                "normalized_unit": "亿元",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "dropped_reason": "DUPLICATE_METRIC_YEAR_VALUE_SOURCE",
                "winner_preview_row_id": "342p::sim_corrected::0001",
                "collision_key": "revenue||2025A||100||亿元",
            },
        ]
    )
    sim_corrected_df = pd.DataFrame(
        [
            {
                "preview_row_id": "342p::sim_corrected::0001",
                "review_item_id": "sim_2",
                "preview_source_type": "SIMULATED_CORRECTED",
                "data_trust_level": "SIMULATED_CORRECTION_ADOPTED",
                "review_status_for_client_display": "SIMULATED_CORRECTED",
                "display_warning": "simulation only; requires later audit before client delivery",
                "metric_standardized": "revenue",
                "year_standardized": "2025A",
                "value_numeric": 100.0,
                "normalized_unit": "亿元",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "dropped_reason": "",
                "winner_preview_row_id": "342p::sim_corrected::0001",
                "collision_key": "revenue||2025A||100||亿元",
                "original_metric_standardized": "revenue_yoy",
                "original_normalized_unit": "亿元",
            }
        ]
    )
    still_human_df = pd.DataFrame(
        [
            {
                "review_item_id": "human_required_1",
                "human_required_reason": "needs_human_review",
                "failed_pattern_reason": "UNRESOLVED_PATTERN",
                "recommended_human_action": "manual review",
                "auto_apply_allowed": False,
                "included_in_preview": False,
            }
        ]
    )
    collision_df = pd.DataFrame(
        [
            {
                "collision_type": "DUPLICATE_METRIC_YEAR_VALUE_SOURCE",
                "collision_key": "ROE||2024A||10||%",
                "review_item_id": "sim_dup",
                "winner_review_item_id": "human_1",
                "preview_row_id": "342p::sim_direct::0002",
                "winner_preview_row_id": "342j::preview::0001",
                "source_type": "SIMULATED_DIRECT",
                "winner_source_type": "HUMAN_REVIEWED",
                "collision_severity": "HIGH",
                "recommended_action": "keep highest trust metric/year/value/source row",
            },
            {
                "collision_type": "DUPLICATE_METRIC_YEAR_VALUE_SOURCE",
                "collision_key": "revenue||2025A||100||亿元",
                "review_item_id": "sim_dup_sim",
                "winner_review_item_id": "sim_2",
                "preview_row_id": "342p::sim_direct::0003",
                "winner_preview_row_id": "342p::sim_corrected::0001",
                "source_type": "SIMULATED_DIRECT",
                "winner_source_type": "SIMULATED_CORRECTED",
                "collision_severity": "MEDIUM",
                "recommended_action": "keep highest trust metric/year/value/source row",
            }
        ]
    )
    summary_342p = {
        "decision": "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY",
        "ready_for_342q": True,
        "qa_fail_count": 0,
        "human_reviewed_preview_count": 1,
        "simulated_preview_count": 2,
        "simulated_direct_preview_count": 1,
        "simulated_corrected_preview_count": 1,
        "combined_preview_row_count": 3,
        "still_human_required_count": 1,
        "remaining_review_count": 4,
        "duplicate_metric_year_source_count": 2,
        "human_over_simulation_override_count": 1,
        "simulated_duplicate_dropped_count": 1,
        "collision_logged_count": 2,
        "client_ready": False,
        "production_ready": False,
    }
    qa_342p = {"qa_fail_count": 0, "checks": []}
    dir_342p.mkdir(parents=True, exist_ok=True)
    _write_json(dir_342p / "reviewed_plus_simulated_client_preview_342p_summary.json", summary_342p)
    _write_json(dir_342p / "reviewed_plus_simulated_client_preview_342p_qa.json", qa_342p)
    (dir_342p / "reviewed_plus_simulated_client_preview_342p_report.md").write_text("ok", encoding="utf-8")
    _write_excel(
        dir_342p / "reviewed_plus_simulated_client_preview_342p.xlsx",
        {
            "00_README": pd.DataFrame([{"section": "readme", "message": "ok"}]),
            "01_PREVIEW_SUMMARY": pd.DataFrame([summary_342p]),
            "02_INPUT_342O_SUMMARY": pd.DataFrame(),
            "03_INPUT_342J_SUMMARY": pd.DataFrame(),
            "04_COMBINED_PREVIEW": combined_preview_df,
            "05_HUMAN_REVIEWED": human_df,
            "06_SIM_DIRECT": sim_direct_df,
            "07_SIM_CORRECTED": sim_corrected_df,
            "08_STILL_HUMAN_REQUIRED": still_human_df,
            "09_COLLISION_CHECK": collision_df,
            "10_METRIC_COVERAGE": pd.DataFrame([{"metric_standardized": "ROE"}]),
            "11_PREVIEW_BOUNDARY": pd.DataFrame([{"message": "not formal client export"}]),
            "12_342Q_READINESS": pd.DataFrame([{"ready_for_342q": True}]),
            "13_NO_WRITE_BACK": pd.DataFrame([{"ok": True}]),
            "14_NEXT_STEPS": pd.DataFrame([{"next_step": "342Q"}]),
        },
    )
    return dir_342p, dir_342o, dir_342j, dir_342i, dir_342n


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_preview_audit_export_readiness_gate_342q"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def test_342q_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_342p, dir_342o, dir_342j, dir_342i, dir_342n = _seed_342q_inputs(case_root)

        artifacts = build_preview_audit_export_readiness_gate_342q(
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            post_human_sidecar_342i_dir=dir_342i,
            adoption_simulation_342n_dir=dir_342n,
            output_dir=case_root / "output" / "preview_audit_export_readiness_gate_342q",
            repo_root=case_root,
        )

        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["ready_for_342r"] is True
        assert summary["export_candidate_row_count"] == 3
        assert summary["simulated_duplicate_dropped_count"] == 1
        assert summary["human_over_simulation_override_count"] == 1
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert "10_EXPORT_CANDIDATE_SCOPE" in WORKBOOK_SHEETS
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_342q_not_ready_if_342p_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_342p, dir_342o, dir_342j, dir_342i, dir_342n = _seed_342q_inputs(case_root)
        summary_path = dir_342p / "reviewed_plus_simulated_client_preview_342p_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["decision"] = "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_NOT_READY"
        summary["ready_for_342q"] = False
        _write_json(summary_path, summary)

        artifacts = build_preview_audit_export_readiness_gate_342q(
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            post_human_sidecar_342i_dir=dir_342i,
            adoption_simulation_342n_dir=dir_342n,
            output_dir=case_root / "output" / "preview_audit_export_readiness_gate_342q",
            repo_root=case_root,
        )

        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["ready_for_342r"] is False
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_342q_invalid_trust_level_fails() -> None:
    case_root = _make_case_root()
    try:
        dir_342p, dir_342o, dir_342j, dir_342i, dir_342n = _seed_342q_inputs(case_root)
        workbook_path = dir_342p / "reviewed_plus_simulated_client_preview_342p.xlsx"
        combined_preview_df = pd.read_excel(workbook_path, sheet_name="04_COMBINED_PREVIEW")
        combined_preview_df.loc[combined_preview_df["preview_source_type"] == "SIMULATED_DIRECT", "data_trust_level"] = "UNKNOWN_TRUST"
        with pd.ExcelWriter(workbook_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            combined_preview_df.to_excel(writer, sheet_name="04_COMBINED_PREVIEW", index=False)

        artifacts = build_preview_audit_export_readiness_gate_342q(
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            post_human_sidecar_342i_dir=dir_342i,
            adoption_simulation_342n_dir=dir_342n,
            output_dir=case_root / "output" / "preview_audit_export_readiness_gate_342q",
            repo_root=case_root,
        )

        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["trust_level_mismatch_count"] == 1
        assert artifacts["summary"]["ready_for_342r"] is False
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_342q_dropped_duplicate_excluded_and_override_preserved() -> None:
    case_root = _make_case_root()
    try:
        dir_342p, dir_342o, dir_342j, dir_342i, dir_342n = _seed_342q_inputs(case_root)

        artifacts = build_preview_audit_export_readiness_gate_342q(
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            post_human_sidecar_342i_dir=dir_342i,
            adoption_simulation_342n_dir=dir_342n,
            output_dir=case_root / "output" / "preview_audit_export_readiness_gate_342q",
            repo_root=case_root,
        )

        dropped_df = artifacts["workbook_sheets"]["07_DROPPED_DUP_AUDIT"]
        override_df = artifacts["workbook_sheets"]["08_OVERRIDE_AUDIT"]
        export_df = artifacts["workbook_sheets"]["10_EXPORT_CANDIDATE_SCOPE"]

        assert len(dropped_df) == 1
        assert dropped_df.iloc[0]["drop_audit_status"] == "PASS"
        assert len(override_df) == 1
        assert override_df.iloc[0]["winner_source_type"] == "HUMAN_REVIEWED"
        assert "342p::sim_direct::0002" not in set(export_df["source_preview_row_id"].tolist())
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
