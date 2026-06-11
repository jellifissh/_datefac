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

from datefac.benchmark.audit_labeled_export_candidate_package_342r import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_audit_labeled_export_candidate_package_342r,
)
from datefac.benchmark.audit_labeled_export_candidate_package_342r_report import WORKBOOK_SHEETS  # noqa: E402


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


def _seed_342r_inputs(root: Path) -> tuple[Path, Path, Path, Path]:
    dir_342q = root / "output" / "preview_audit_export_readiness_gate_342q"
    dir_342p = root / "output" / "reviewed_plus_simulated_client_preview_342p"
    dir_342o = root / "output" / "post_adoption_sidecar_simulation_342o"
    dir_342j = root / "output" / "table_first_reviewed_client_preview_pilot_342j"

    _seed_support_dir(
        dir_342o,
        summary_name="post_adoption_sidecar_simulation_342o_summary.json",
        qa_name="post_adoption_sidecar_simulation_342o_qa.json",
        report_name="post_adoption_sidecar_simulation_342o_report.md",
        workbook_name="post_adoption_sidecar_simulation_342o.xlsx",
        summary={
            "decision": "POST_ADOPTION_SIDECAR_SIMULATION_342O_READY",
            "simulated_adopted_cell_count": 2,
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

    combined_preview_df = pd.DataFrame(
        [
            {
                "preview_row_id": "342j::preview::0001",
                "review_item_id": "human_1",
                "source_stage": "342J",
                "preview_source_type": "HUMAN_REVIEWED",
                "data_trust_level": "HUMAN_REVIEWED",
                "review_status_for_client_display": "REVIEWED",
                "display_warning": "human reviewed pilot row; not full client export",
                "corpus_pdf_id": "pdf_001",
                "file_name": "sample_1.pdf",
                "table_id": "table_1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "D:/img_1.jpg",
                "metric_standardized": "ROE",
                "year_standardized": "2024A",
                "value_numeric": 10.0,
                "normalized_unit": "%",
                "evidence": "<table>roe</table>",
                "adoption_confidence": "",
                "adoption_evidence": "",
                "correction_pattern": "",
                "correction_reason": "",
                "not_final_confirmation": False,
                "client_ready": False,
                "production_ready": False,
                "included_in_combined_preview": True,
                "dropped_reason": "",
                "winner_preview_row_id": "342j::preview::0001",
                "collision_key": "ROE||2024A||10||%",
                "original_metric_standardized": "",
                "original_normalized_unit": "",
            },
            {
                "preview_row_id": "342p::sim_direct::0001",
                "review_item_id": "sim_1",
                "source_stage": "342O",
                "preview_source_type": "SIMULATED_DIRECT",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "review_status_for_client_display": "SIMULATED",
                "display_warning": "simulation only; requires later audit before client delivery",
                "corpus_pdf_id": "pdf_001",
                "file_name": "sample_1.pdf",
                "table_id": "table_1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "D:/img_1.jpg",
                "metric_standardized": "EPS",
                "year_standardized": "2025A",
                "value_numeric": 1.2,
                "normalized_unit": "元",
                "evidence": "<table>eps</table>",
                "adoption_confidence": 0.97,
                "adoption_evidence": "safe metric/unit pair",
                "correction_pattern": "",
                "correction_reason": "",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "included_in_combined_preview": True,
                "dropped_reason": "",
                "winner_preview_row_id": "342p::sim_direct::0001",
                "collision_key": "EPS||2025A||1.2||元",
                "original_metric_standardized": "",
                "original_normalized_unit": "",
            },
            {
                "preview_row_id": "342p::sim_corrected::0001",
                "review_item_id": "sim_2",
                "source_stage": "342O",
                "preview_source_type": "SIMULATED_CORRECTED",
                "data_trust_level": "SIMULATED_CORRECTION_ADOPTED",
                "review_status_for_client_display": "SIMULATED_CORRECTED",
                "display_warning": "simulation only; requires later audit before client delivery",
                "corpus_pdf_id": "pdf_002",
                "file_name": "sample_2.pdf",
                "table_id": "table_2",
                "table_type": "INCOME_STATEMENT",
                "source_page": 2,
                "bbox": "[5,6,7,8]",
                "image_path": "D:/img_2.jpg",
                "metric_standardized": "revenue",
                "year_standardized": "2024A",
                "value_numeric": 18.69,
                "normalized_unit": "亿元",
                "evidence": "<table>revenue</table>",
                "adoption_confidence": 0.96,
                "adoption_evidence": "correction pattern matched",
                "correction_pattern": "REVENUE_AMOUNT_NOT_YOY",
                "correction_reason": "amount row should map to revenue",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "included_in_combined_preview": True,
                "dropped_reason": "",
                "winner_preview_row_id": "342p::sim_corrected::0001",
                "collision_key": "revenue||2024A||18.69||亿元",
                "original_metric_standardized": "revenue_yoy",
                "original_normalized_unit": "亿元",
            },
        ]
    )
    human_df = combined_preview_df[combined_preview_df["data_trust_level"] == "HUMAN_REVIEWED"].copy()
    sim_direct_df = combined_preview_df[combined_preview_df["data_trust_level"] == "SIMULATED_DIRECT_ADOPTED"].copy()
    sim_corrected_df = combined_preview_df[combined_preview_df["data_trust_level"] == "SIMULATED_CORRECTION_ADOPTED"].copy()
    collision_df = pd.DataFrame(
        [
            {
                "collision_type": "DUPLICATE_METRIC_YEAR_VALUE_SOURCE",
                "collision_key": "ROE||2024A||10||%",
                "review_item_id": "human_dup",
                "winner_review_item_id": "human_1",
                "preview_row_id": "342j::preview::0009",
                "winner_preview_row_id": "342j::preview::0001",
                "source_type": "HUMAN_REVIEWED",
                "winner_source_type": "HUMAN_REVIEWED",
                "collision_severity": "HIGH",
                "recommended_action": "keep highest trust row",
                "collision_unresolved": False,
                "human_priority_violation": False,
                "audit_status": "PASS",
            }
        ]
    )

    summary_342p = {
        "decision": "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY",
        "human_reviewed_preview_count": 1,
        "simulated_preview_count": 2,
        "simulated_direct_preview_count": 1,
        "simulated_corrected_preview_count": 1,
        "combined_preview_row_count": 3,
        "still_human_required_count": 1,
        "remaining_review_count": 4,
        "duplicate_metric_year_source_count": 1,
        "human_over_simulation_override_count": 0,
        "simulated_duplicate_dropped_count": 0,
        "collision_logged_count": 1,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
        "ready_for_342q": True,
    }
    dir_342p.mkdir(parents=True, exist_ok=True)
    _write_json(dir_342p / "reviewed_plus_simulated_client_preview_342p_summary.json", summary_342p)
    _write_json(dir_342p / "reviewed_plus_simulated_client_preview_342p_qa.json", {"qa_fail_count": 0, "checks": []})
    (dir_342p / "reviewed_plus_simulated_client_preview_342p_report.md").write_text("ok", encoding="utf-8")
    _write_excel(
        dir_342p / "reviewed_plus_simulated_client_preview_342p.xlsx",
        {
            "04_COMBINED_PREVIEW": combined_preview_df,
            "05_HUMAN_REVIEWED": human_df,
            "06_SIM_DIRECT": sim_direct_df,
            "07_SIM_CORRECTED": sim_corrected_df,
            "09_COLLISION_CHECK": collision_df,
        },
    )

    preview_audit_df = pd.DataFrame(
        [
            {
                "preview_row_id": "342j::preview::0001",
                "review_item_id": "human_1",
                "preview_source_type": "HUMAN_REVIEWED",
                "data_trust_level": "HUMAN_REVIEWED",
                "review_status_for_client_display": "REVIEWED",
                "metric_standardized": "ROE",
                "year_standardized": "2024A",
                "value_numeric": 10.0,
                "normalized_unit": "%",
                "display_warning": "human reviewed pilot row; not full client export",
                "not_final_confirmation": False,
                "client_ready": False,
                "production_ready": False,
                "audit_status": "PASS",
                "audit_reason": "human row passed audit gate",
                "included_in_export_candidate_scope": True,
                "export_candidate_allowed": True,
                "requires_disclaimer": False,
                "requires_later_audit": False,
            },
            {
                "preview_row_id": "342p::sim_direct::0001",
                "review_item_id": "sim_1",
                "preview_source_type": "SIMULATED_DIRECT",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "review_status_for_client_display": "SIMULATED",
                "metric_standardized": "EPS",
                "year_standardized": "2025A",
                "value_numeric": 1.2,
                "normalized_unit": "元",
                "display_warning": "simulation only; requires later audit before client delivery",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "audit_status": "WARN",
                "audit_reason": "simulation-only preview candidate; later audit required",
                "included_in_export_candidate_scope": True,
                "export_candidate_allowed": True,
                "requires_disclaimer": True,
                "requires_later_audit": True,
            },
            {
                "preview_row_id": "342p::sim_corrected::0001",
                "review_item_id": "sim_2",
                "preview_source_type": "SIMULATED_CORRECTED",
                "data_trust_level": "SIMULATED_CORRECTION_ADOPTED",
                "review_status_for_client_display": "SIMULATED_CORRECTED",
                "metric_standardized": "revenue",
                "year_standardized": "2024A",
                "value_numeric": 18.69,
                "normalized_unit": "亿元",
                "display_warning": "simulation only; requires later audit before client delivery",
                "not_final_confirmation": True,
                "client_ready": False,
                "production_ready": False,
                "audit_status": "WARN",
                "audit_reason": "simulation-only preview candidate; later audit required",
                "included_in_export_candidate_scope": True,
                "export_candidate_allowed": True,
                "requires_disclaimer": True,
                "requires_later_audit": True,
            },
        ]
    )
    candidate_scope_df = pd.DataFrame(
        [
            {
                "export_candidate_row_id": "342q::export_candidate::0001",
                "source_preview_row_id": "342j::preview::0001",
                "review_item_id": "human_1",
                "metric_standardized": "ROE",
                "year_standardized": "2024A",
                "value_numeric": 10.0,
                "normalized_unit": "%",
                "data_trust_level": "HUMAN_REVIEWED",
                "export_scope_status": "AUDIT_LABELED_HUMAN_SCOPE",
                "display_warning": "human reviewed pilot row; not full client export",
                "required_disclaimer": False,
                "not_formal_client_export": True,
                "client_ready": False,
                "production_ready": False,
            },
            {
                "export_candidate_row_id": "342q::export_candidate::0002",
                "source_preview_row_id": "342p::sim_direct::0001",
                "review_item_id": "sim_1",
                "metric_standardized": "EPS",
                "year_standardized": "2025A",
                "value_numeric": 1.2,
                "normalized_unit": "元",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "export_scope_status": "AUDIT_LABELED_SIMULATION_SCOPE",
                "display_warning": "simulation only; requires later audit before client delivery",
                "required_disclaimer": True,
                "not_formal_client_export": True,
                "client_ready": False,
                "production_ready": False,
            },
            {
                "export_candidate_row_id": "342q::export_candidate::0003",
                "source_preview_row_id": "342p::sim_corrected::0001",
                "review_item_id": "sim_2",
                "metric_standardized": "revenue",
                "year_standardized": "2024A",
                "value_numeric": 18.69,
                "normalized_unit": "亿元",
                "data_trust_level": "SIMULATED_CORRECTION_ADOPTED",
                "export_scope_status": "AUDIT_LABELED_SIMULATION_SCOPE",
                "display_warning": "simulation only; requires later audit before client delivery",
                "required_disclaimer": True,
                "not_formal_client_export": True,
                "client_ready": False,
                "production_ready": False,
            },
        ]
    )
    summary_342q = {
        "decision": "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY",
        "human_reviewed_preview_count": 1,
        "simulated_preview_count": 2,
        "simulated_direct_preview_count": 1,
        "simulated_corrected_preview_count": 1,
        "combined_preview_row_count": 3,
        "export_candidate_row_count": 3,
        "unknown_trust_level_count": 0,
        "trust_level_mismatch_count": 0,
        "simulated_final_confirmed_true_count": 0,
        "simulated_client_ready_true_count": 0,
        "simulated_production_ready_true_count": 0,
        "missing_display_warning_count": 0,
        "collision_logged_count": 1,
        "duplicate_metric_year_source_count": 1,
        "human_over_simulation_override_count": 0,
        "simulated_duplicate_dropped_count": 0,
        "unresolved_collision_count": 0,
        "severe_collision_count": 1,
        "formal_client_export_allowed": False,
        "export_candidate_scope_allowed": True,
        "export_risk_level": "HIGH",
        "still_human_required_count": 1,
        "remaining_review_count": 4,
        "ready_for_342r": True,
        "recommended_342r_scope": "audit_labeled_export_candidate_package",
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
        "decision_path": "ready",
        "no_write_back_proof_passed": True,
    }
    dir_342q.mkdir(parents=True, exist_ok=True)
    _write_json(dir_342q / "preview_audit_export_readiness_gate_342q_summary.json", summary_342q)
    _write_json(dir_342q / "preview_audit_export_readiness_gate_342q_qa.json", {"qa_fail_count": 0, "checks": []})
    (dir_342q / "preview_audit_export_readiness_gate_342q_report.md").write_text("ok", encoding="utf-8")
    _write_excel(
        dir_342q / "preview_audit_export_readiness_gate_342q.xlsx",
        {
            "01_AUDIT_SUMMARY": pd.DataFrame([summary_342q]),
            "03_PREVIEW_AUDIT": preview_audit_df,
            "04_TRUST_LEVEL_AUDIT": pd.DataFrame([{"audit_item": "ok", "status": "PASS"}]),
            "05_SIM_BOUNDARY_AUDIT": pd.DataFrame([{"audit_item": "ok", "status": "PASS"}]),
            "06_COLLISION_AUDIT": collision_df,
            "09_EXPORT_RISK_GATE": pd.DataFrame(
                [
                    {
                        "export_candidate_scope_allowed": True,
                        "formal_client_export_allowed": False,
                        "client_ready": False,
                        "production_ready": False,
                        "export_risk_level": "HIGH",
                        "risk_reasons": "simulated rows present | backlog remains",
                        "required_disclaimers": "not formal client export | later audit required",
                    }
                ]
            ),
            "10_EXPORT_CANDIDATE_SCOPE": candidate_scope_df,
            "11_REMAINING_BACKLOG": pd.DataFrame(
                [
                    {
                        "still_human_required_count": 1,
                        "remaining_review_count": 4,
                        "remaining_backlog_note": "current preview remains partial and bounded",
                        "recommended_backlog_action": "continue review",
                    }
                ]
            ),
            "12_342R_READINESS": pd.DataFrame(
                [
                    {
                        "ready_for_342r": True,
                        "recommended_342r_scope": "audit_labeled_export_candidate_package",
                        "formal_client_export_allowed": False,
                        "client_ready": False,
                        "production_ready": False,
                        "decision": "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY",
                    }
                ]
            ),
            "13_NO_WRITE_BACK": pd.DataFrame([{"no_write_back": True}]),
        },
    )
    return dir_342q, dir_342p, dir_342o, dir_342j


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_audit_labeled_export_candidate_package_342r"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def test_342r_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_342q, dir_342p, dir_342o, dir_342j = _seed_342r_inputs(case_root)

        artifacts = build_audit_labeled_export_candidate_package_342r(
            preview_audit_342q_dir=dir_342q,
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            output_dir=case_root / "output" / "audit_labeled_export_candidate_package_342r",
            repo_root=case_root,
        )

        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["ready_for_342s"] is True
        assert summary["export_candidate_package_row_count"] == 3
        assert summary["human_reviewed_candidate_count"] == 1
        assert summary["simulated_direct_candidate_count"] == 1
        assert summary["simulated_corrected_candidate_count"] == 1
        assert summary["formal_client_export_allowed"] is False
        assert "03_EXPORT_CANDIDATES" in WORKBOOK_SHEETS
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_342r_not_ready_if_342q_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_342q, dir_342p, dir_342o, dir_342j = _seed_342r_inputs(case_root)
        summary_path = dir_342q / "preview_audit_export_readiness_gate_342q_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["decision"] = "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_NOT_READY"
        summary["ready_for_342r"] = False
        _write_json(summary_path, summary)

        artifacts = build_audit_labeled_export_candidate_package_342r(
            preview_audit_342q_dir=dir_342q,
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            output_dir=case_root / "output" / "audit_labeled_export_candidate_package_342r",
            repo_root=case_root,
        )

        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["ready_for_342s"] is False
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_342r_invalid_trust_level_fails() -> None:
    case_root = _make_case_root()
    try:
        dir_342q, dir_342p, dir_342o, dir_342j = _seed_342r_inputs(case_root)
        workbook_path = dir_342q / "preview_audit_export_readiness_gate_342q.xlsx"
        candidate_scope_df = pd.read_excel(workbook_path, sheet_name="10_EXPORT_CANDIDATE_SCOPE")
        candidate_scope_df.loc[candidate_scope_df["review_item_id"] == "sim_1", "data_trust_level"] = "UNKNOWN_TRUST"
        with pd.ExcelWriter(workbook_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            candidate_scope_df.to_excel(writer, sheet_name="10_EXPORT_CANDIDATE_SCOPE", index=False)

        artifacts = build_audit_labeled_export_candidate_package_342r(
            preview_audit_342q_dir=dir_342q,
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            output_dir=case_root / "output" / "audit_labeled_export_candidate_package_342r",
            repo_root=case_root,
        )

        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["package_row_fail_count"] == 1
        assert artifacts["summary"]["ready_for_342s"] is False
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_342r_missing_later_audit_warning_fails() -> None:
    case_root = _make_case_root()
    try:
        dir_342q, dir_342p, dir_342o, dir_342j = _seed_342r_inputs(case_root)
        workbook_path = dir_342q / "preview_audit_export_readiness_gate_342q.xlsx"
        candidate_scope_df = pd.read_excel(workbook_path, sheet_name="10_EXPORT_CANDIDATE_SCOPE")
        candidate_scope_df.loc[candidate_scope_df["review_item_id"] == "sim_1", "display_warning"] = "simulation only"
        with pd.ExcelWriter(workbook_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            candidate_scope_df.to_excel(writer, sheet_name="10_EXPORT_CANDIDATE_SCOPE", index=False)

        artifacts = build_audit_labeled_export_candidate_package_342r(
            preview_audit_342q_dir=dir_342q,
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            output_dir=case_root / "output" / "audit_labeled_export_candidate_package_342r",
            repo_root=case_root,
        )

        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["package_row_fail_count"] == 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_342r_client_ready_true_fails() -> None:
    case_root = _make_case_root()
    try:
        dir_342q, dir_342p, dir_342o, dir_342j = _seed_342r_inputs(case_root)
        workbook_path = dir_342q / "preview_audit_export_readiness_gate_342q.xlsx"
        candidate_scope_df = pd.read_excel(workbook_path, sheet_name="10_EXPORT_CANDIDATE_SCOPE")
        candidate_scope_df.loc[candidate_scope_df["review_item_id"] == "human_1", "client_ready"] = True
        with pd.ExcelWriter(workbook_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            candidate_scope_df.to_excel(writer, sheet_name="10_EXPORT_CANDIDATE_SCOPE", index=False)

        artifacts = build_audit_labeled_export_candidate_package_342r(
            preview_audit_342q_dir=dir_342q,
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            output_dir=case_root / "output" / "audit_labeled_export_candidate_package_342r",
            repo_root=case_root,
        )

        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
