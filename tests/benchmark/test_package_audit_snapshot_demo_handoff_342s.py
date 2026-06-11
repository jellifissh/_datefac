from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.package_audit_snapshot_demo_handoff_342s import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_package_audit_snapshot_demo_handoff_342s,
)
from datefac.benchmark.package_audit_snapshot_demo_handoff_342s_report import WORKBOOK_SHEETS  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _seed_support_dir(
    base_dir: Path,
    *,
    summary_name: str,
    qa_name: str,
    report_name: str,
    workbook_name: str,
    summary: dict,
) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    _write_json(base_dir / summary_name, summary)
    _write_json(base_dir / qa_name, {"qa_fail_count": 0, "checks": []})
    (base_dir / report_name).write_text("ok", encoding="utf-8")
    _write_excel(base_dir / workbook_name, {"Sheet1": pd.DataFrame([{"ok": True}])})


def _seed_342s_inputs(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    dir_342r = root / "output" / "audit_labeled_export_candidate_package_342r"
    dir_342q = root / "output" / "preview_audit_export_readiness_gate_342q"
    dir_342p = root / "output" / "reviewed_plus_simulated_client_preview_342p"
    dir_342o = root / "output" / "post_adoption_sidecar_simulation_342o"
    dir_342j = root / "output" / "table_first_reviewed_client_preview_pilot_342j"

    _seed_support_dir(
        dir_342q,
        summary_name="preview_audit_export_readiness_gate_342q_summary.json",
        qa_name="preview_audit_export_readiness_gate_342q_qa.json",
        report_name="preview_audit_export_readiness_gate_342q_report.md",
        workbook_name="preview_audit_export_readiness_gate_342q.xlsx",
        summary={
            "decision": "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY",
            "export_candidate_row_count": 3,
            "ready_for_342r": True,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "export_risk_level": "HIGH",
            "collision_logged_count": 1,
            "duplicate_metric_year_source_count": 1,
            "severe_collision_count": 1,
            "human_over_simulation_override_count": 0,
            "simulated_duplicate_dropped_count": 0,
            "still_human_required_count": 1,
            "remaining_review_count": 4,
            "unresolved_collision_count": 0,
            "qa_fail_count": 0,
        },
    )
    _seed_support_dir(
        dir_342p,
        summary_name="reviewed_plus_simulated_client_preview_342p_summary.json",
        qa_name="reviewed_plus_simulated_client_preview_342p_qa.json",
        report_name="reviewed_plus_simulated_client_preview_342p_report.md",
        workbook_name="reviewed_plus_simulated_client_preview_342p.xlsx",
        summary={
            "decision": "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY",
            "combined_preview_row_count": 3,
            "human_reviewed_preview_count": 1,
            "simulated_preview_count": 2,
            "qa_fail_count": 0,
        },
    )
    _seed_support_dir(
        dir_342o,
        summary_name="post_adoption_sidecar_simulation_342o_summary.json",
        qa_name="post_adoption_sidecar_simulation_342o_qa.json",
        report_name="post_adoption_sidecar_simulation_342o_report.md",
        workbook_name="post_adoption_sidecar_simulation_342o.xlsx",
        summary={
            "decision": "POST_ADOPTION_SIDECAR_SIMULATION_342O_READY",
            "simulated_adopted_cell_count": 2,
            "still_human_required_count": 1,
            "remaining_review_count": 4,
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
            "confirmed_preview_row_count": 1,
            "corrected_preview_row_count": 0,
            "qa_fail_count": 0,
        },
    )

    candidate_rows = pd.DataFrame(
        [
            {
                "export_candidate_row_id": "342r::row::0001",
                "source_preview_row_id": "342j::preview::0001",
                "review_item_id": "human_1",
                "metric_standardized": "ROE",
                "year_standardized": "2024A",
                "value_numeric": 10.0,
                "normalized_unit": "%",
                "data_trust_level": "HUMAN_REVIEWED",
                "export_scope_status": "IN_SCOPE",
                "display_warning": "human reviewed pilot row; not formal client export",
                "required_disclaimer": False,
                "required_disclaimer_text": "",
                "not_formal_client_export": True,
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
                "final_confirmed": False,
                "package_row_status": "INCLUDED_IN_AUDIT_LABELED_PACKAGE",
                "package_warning_level": "MEDIUM",
                "requires_later_audit": False,
                "source_stage": "342Q",
                "upstream_source_stage": "342J",
                "preview_source_type": "HUMAN_REVIEWED",
                "review_status_for_client_display": "REVIEWED",
                "audit_status": "PASS",
                "audit_reason": "ok",
                "audit_label": "AUDIT_LABEL_HUMAN_REVIEWED",
                "display_badge": "REVIEWED_PILOT",
                "package_note": "human-reviewed pilot row",
                "corpus_pdf_id": "pdf_001",
                "file_name": "sample_1.pdf",
                "table_id": "table_1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "D:/img_1.jpg",
                "evidence": "<table>roe</table>",
                "adoption_confidence": "",
                "adoption_evidence": "",
                "correction_pattern": "",
                "correction_reason": "",
                "original_metric_standardized": "",
                "original_normalized_unit": "",
                "collision_key": "ROE||2024A||10||%",
            },
            {
                "export_candidate_row_id": "342r::row::0002",
                "source_preview_row_id": "342p::sim_direct::0001",
                "review_item_id": "sim_1",
                "metric_standardized": "EPS",
                "year_standardized": "2025A",
                "value_numeric": 1.2,
                "normalized_unit": "yuan",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "export_scope_status": "IN_SCOPE",
                "display_warning": "simulation only; requires later audit before client delivery",
                "required_disclaimer": True,
                "required_disclaimer_text": "simulation only",
                "not_formal_client_export": True,
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
                "final_confirmed": False,
                "package_row_status": "INCLUDED_IN_AUDIT_LABELED_PACKAGE",
                "package_warning_level": "HIGH",
                "requires_later_audit": True,
                "source_stage": "342Q",
                "upstream_source_stage": "342O",
                "preview_source_type": "SIMULATED_DIRECT",
                "review_status_for_client_display": "SIMULATED",
                "audit_status": "WARN",
                "audit_reason": "simulation boundary",
                "audit_label": "AUDIT_LABEL_SIMULATED_DIRECT",
                "display_badge": "SIMULATION_ONLY",
                "package_note": "simulation-only direct adopted row",
                "corpus_pdf_id": "pdf_001",
                "file_name": "sample_1.pdf",
                "table_id": "table_2",
                "table_type": "VALUTION",
                "source_page": 2,
                "bbox": "[1,2,3,4]",
                "image_path": "D:/img_2.jpg",
                "evidence": "<table>eps</table>",
                "adoption_confidence": 0.97,
                "adoption_evidence": "safe pair",
                "correction_pattern": "",
                "correction_reason": "",
                "original_metric_standardized": "",
                "original_normalized_unit": "",
                "collision_key": "EPS||2025A||1.2||yuan",
            },
            {
                "export_candidate_row_id": "342r::row::0003",
                "source_preview_row_id": "342p::sim_corrected::0001",
                "review_item_id": "sim_2",
                "metric_standardized": "revenue",
                "year_standardized": "2024A",
                "value_numeric": 18.69,
                "normalized_unit": "CNY100M",
                "data_trust_level": "SIMULATED_CORRECTION_ADOPTED",
                "export_scope_status": "IN_SCOPE",
                "display_warning": "simulation only; requires later audit before client delivery",
                "required_disclaimer": True,
                "required_disclaimer_text": "simulation only",
                "not_formal_client_export": True,
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
                "final_confirmed": False,
                "package_row_status": "INCLUDED_IN_AUDIT_LABELED_PACKAGE",
                "package_warning_level": "HIGH",
                "requires_later_audit": True,
                "source_stage": "342Q",
                "upstream_source_stage": "342O",
                "preview_source_type": "SIMULATED_CORRECTED",
                "review_status_for_client_display": "SIMULATED_CORRECTED",
                "audit_status": "WARN",
                "audit_reason": "simulation boundary",
                "audit_label": "AUDIT_LABEL_SIMULATED_CORRECTED",
                "display_badge": "SIMULATION_CORRECTED_ONLY",
                "package_note": "simulation-only corrected adopted row",
                "corpus_pdf_id": "pdf_002",
                "file_name": "sample_2.pdf",
                "table_id": "table_3",
                "table_type": "INCOME_STATEMENT",
                "source_page": 3,
                "bbox": "[1,2,3,4]",
                "image_path": "D:/img_3.jpg",
                "evidence": "<table>revenue</table>",
                "adoption_confidence": 0.95,
                "adoption_evidence": "corrected pair",
                "correction_pattern": "REVENUE_AMOUNT_NOT_YOY",
                "correction_reason": "use corrected row",
                "original_metric_standardized": "revenue_yoy",
                "original_normalized_unit": "CNY100M",
                "collision_key": "revenue||2024A||18.69||CNY100M",
            },
        ]
    )
    audit_labels = pd.DataFrame(
        [
            {"audit_label_row_id": "342r::audit::0001", "review_item_id": "human_1", "data_trust_level": "HUMAN_REVIEWED", "audit_label": "AUDIT_LABEL_HUMAN_REVIEWED", "audit_label_reason": "human", "display_badge": "REVIEWED_PILOT"},
            {"audit_label_row_id": "342r::audit::0002", "review_item_id": "sim_1", "data_trust_level": "SIMULATED_DIRECT_ADOPTED", "audit_label": "AUDIT_LABEL_SIMULATED_DIRECT", "audit_label_reason": "sim", "display_badge": "SIMULATION_ONLY"},
            {"audit_label_row_id": "342r::audit::0003", "review_item_id": "sim_2", "data_trust_level": "SIMULATED_CORRECTION_ADOPTED", "audit_label": "AUDIT_LABEL_SIMULATED_CORRECTED", "audit_label_reason": "sim", "display_badge": "SIMULATION_CORRECTED_ONLY"},
        ]
    )
    warnings_df = pd.DataFrame(
        [
            {"warning_row_id": "342r::warn::0001", "review_item_id": "sim_1", "data_trust_level": "SIMULATED_DIRECT_ADOPTED", "warning_text": "later audit required", "disclaimer_required": True, "later_audit_required": True, "formal_export_blocker": True},
            {"warning_row_id": "342r::warn::0002", "review_item_id": "sim_2", "data_trust_level": "SIMULATED_CORRECTION_ADOPTED", "warning_text": "later audit required", "disclaimer_required": True, "later_audit_required": True, "formal_export_blocker": True},
        ]
    )
    risk_df = pd.DataFrame(
        [
            {
                "export_risk_level": "HIGH",
                "risk_reasons": "simulated rows present | backlog remains",
                "formal_client_export_allowed": False,
                "export_candidate_scope_allowed": True,
                "client_ready": False,
                "production_ready": False,
                "recommended_usage": "demo only",
            }
        ]
    )
    collision_df = pd.DataFrame(
        [
            {
                "collision_type": "DUPLICATE_METRIC_YEAR_SOURCE",
                "collision_key": "ROE||2024A||10||%",
                "review_item_id": "human_1",
                "winner_review_item_id": "human_1",
                "preview_row_id": "342j::preview::0001",
                "winner_preview_row_id": "342j::preview::0001",
                "source_type": "HUMAN_REVIEWED",
                "winner_source_type": "HUMAN_REVIEWED",
                "collision_severity": "HIGH",
                "recommended_action": "keep human-reviewed row",
                "collision_unresolved": False,
                "human_priority_violation": False,
                "audit_status": "PASS",
                "collision_logged_count": 1,
                "duplicate_metric_year_source_count": 1,
                "human_over_simulation_override_count": 0,
                "simulated_duplicate_dropped_count": 0,
                "unresolved_collision_count": 0,
                "severe_collision_count": 1,
                "collision_note": "logged and handled",
            }
        ]
    )
    backlog_df = pd.DataFrame(
        [
            {
                "remaining_review_count": 4,
                "still_human_required_count": 1,
                "backlog_note": "bounded package only",
                "recommended_next_review_action": "continue review queue design",
            }
        ]
    )
    readiness_df = pd.DataFrame(
        [
            {
                "ready_for_342s": True,
                "recommended_342s_scope": "package_audit_snapshot_or_demo_handoff",
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
                "decision": "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY",
            }
        ]
    )
    no_write_back_df = pd.DataFrame([{"no_write_back": True}])
    summary_342r = {
        "decision": "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY",
        "export_candidate_package_row_count": 3,
        "human_reviewed_candidate_count": 1,
        "simulated_candidate_count": 2,
        "simulated_direct_candidate_count": 1,
        "simulated_corrected_candidate_count": 1,
        "formal_client_export_allowed": False,
        "export_candidate_scope_allowed": True,
        "export_risk_level": "HIGH",
        "collision_logged_count": 1,
        "duplicate_metric_year_source_count": 1,
        "severe_collision_count": 1,
        "human_over_simulation_override_count": 0,
        "simulated_duplicate_dropped_count": 0,
        "still_human_required_count": 1,
        "remaining_review_count": 4,
        "disclaimer_required_count": 2,
        "later_audit_required_count": 2,
        "package_row_fail_count": 0,
        "ready_for_342s": True,
        "recommended_342s_scope": "package_audit_snapshot_or_demo_handoff",
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
        "decision_path": "ready",
        "no_write_back_proof_passed": True,
    }
    dir_342r.mkdir(parents=True, exist_ok=True)
    _write_json(dir_342r / "audit_labeled_export_candidate_package_342r_summary.json", summary_342r)
    _write_json(dir_342r / "audit_labeled_export_candidate_package_342r_qa.json", {"qa_fail_count": 0, "checks": []})
    (dir_342r / "audit_labeled_export_candidate_package_342r_report.md").write_text("ok", encoding="utf-8")
    _write_json(dir_342r / "audit_labeled_export_candidate_package_342r_metadata.json", {"source": "test"})
    candidate_rows.to_csv(dir_342r / "audit_labeled_export_candidate_package_342r_candidates.csv", index=False, encoding="utf-8-sig")
    _write_excel(
        dir_342r / "audit_labeled_export_candidate_package_342r.xlsx",
        {
            "01_PACKAGE_SUMMARY": pd.DataFrame([summary_342r]),
            "03_EXPORT_CANDIDATES": candidate_rows,
            "04_HUMAN_REVIEWED": candidate_rows[candidate_rows["data_trust_level"] == "HUMAN_REVIEWED"].copy(),
            "05_SIMULATED_DIRECT": candidate_rows[candidate_rows["data_trust_level"] == "SIMULATED_DIRECT_ADOPTED"].copy(),
            "06_SIMULATED_CORRECTED": candidate_rows[candidate_rows["data_trust_level"] == "SIMULATED_CORRECTION_ADOPTED"].copy(),
            "07_AUDIT_LABELS": audit_labels,
            "08_REQUIRED_WARNINGS": warnings_df,
            "09_RISK_DISCLOSURE": risk_df,
            "10_COLLISION_CONTEXT": collision_df,
            "11_BACKLOG_CONTEXT": backlog_df,
            "12_342S_READINESS": readiness_df,
            "13_NO_WRITE_BACK": no_write_back_df,
        },
    )
    return dir_342r, dir_342q, dir_342p, dir_342o, dir_342j


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_package_audit_snapshot_demo_handoff_342s"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def test_342s_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_342r, dir_342q, dir_342p, dir_342o, dir_342j = _seed_342s_inputs(case_root)
        ledger_dir = case_root / "docs" / "project_milestones"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        (ledger_dir / "PROJECT_MILESTONE_LEDGER_test.md").write_text("ledger", encoding="utf-8")

        artifacts = build_package_audit_snapshot_demo_handoff_342s(
            audit_labeled_package_342r_dir=dir_342r,
            preview_audit_342q_dir=dir_342q,
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            output_dir=case_root / "output" / "package_audit_snapshot_demo_handoff_342s",
            repo_root=case_root,
        )

        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["demo_handoff_ready"] is True
        assert summary["ready_for_343a"] is True
        assert summary["latest_completed_milestone"] == "342R"
        assert summary["current_milestone"] == "342S"
        assert summary["current_mainline"] == "MinerU-first / table-first"
        assert "03_KEY_ARTIFACTS" in WORKBOOK_SHEETS
        assert artifacts["artifact_index_json"][0]["artifact_name"] == "342R workbook"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_342s_not_ready_if_342r_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_342r, dir_342q, dir_342p, dir_342o, dir_342j = _seed_342s_inputs(case_root)
        ledger_dir = case_root / "docs" / "project_milestones"
        ledger_dir.mkdir(parents=True, exist_ok=True)
        (ledger_dir / "PROJECT_MILESTONE_LEDGER_test.md").write_text("ledger", encoding="utf-8")

        summary_path = dir_342r / "audit_labeled_export_candidate_package_342r_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["decision"] = "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_NOT_READY"
        summary["ready_for_342s"] = False
        _write_json(summary_path, summary)

        artifacts = build_package_audit_snapshot_demo_handoff_342s(
            audit_labeled_package_342r_dir=dir_342r,
            preview_audit_342q_dir=dir_342q,
            reviewed_plus_preview_342p_dir=dir_342p,
            post_adoption_sidecar_342o_dir=dir_342o,
            reviewed_preview_342j_dir=dir_342j,
            output_dir=case_root / "output" / "package_audit_snapshot_demo_handoff_342s",
            repo_root=case_root,
        )

        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["ready_for_343a"] is False
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
