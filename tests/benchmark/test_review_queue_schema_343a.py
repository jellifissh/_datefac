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

from datefac.benchmark.review_queue_schema_343a import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_review_queue_schema_343a,
)
from datefac.review_queue.schema_343a import field_count as schema_field_count  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_schema_343a"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343a_inputs(root: Path) -> tuple[Path, Path, Path, Path]:
    dir_342s = root / "output" / "package_audit_snapshot_demo_handoff_342s"
    dir_342r = root / "output" / "audit_labeled_export_candidate_package_342r"
    dir_342q = root / "output" / "preview_audit_export_readiness_gate_342q"
    dir_342p = root / "output" / "reviewed_plus_simulated_client_preview_342p"

    dir_342s.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_342s / "package_audit_snapshot_demo_handoff_342s_summary.json",
        {
            "decision": "PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_READY",
            "ready_for_343a": True,
            "qa_fail_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "current_mainline": "MinerU-first / table-first",
            "latest_commit_sha_before_342s": "abc123def456",
            "still_human_required_count": 6,
            "remaining_review_count": 18,
            "collision_logged_count": 3,
            "severe_collision_count": 1,
        },
    )
    _write_json(dir_342s / "package_audit_snapshot_demo_handoff_342s_qa.json", {"qa_fail_count": 0, "checks": []})
    (dir_342s / "package_audit_snapshot_demo_handoff_342s_report.md").write_text("ok", encoding="utf-8")
    (dir_342s / "package_audit_snapshot_demo_handoff_342s_demo_readme.md").write_text("ok", encoding="utf-8")
    (dir_342s / "package_audit_snapshot_demo_handoff_342s_handoff_checklist.md").write_text("ok", encoding="utf-8")

    dir_342q.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_342q / "preview_audit_export_readiness_gate_342q_summary.json",
        {
            "decision": "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY",
            "simulated_final_confirmed_true_count": 0,
            "qa_fail_count": 0,
        },
    )
    _write_json(dir_342q / "preview_audit_export_readiness_gate_342q_qa.json", {"qa_fail_count": 0, "checks": []})

    dir_342p.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_342p / "reviewed_plus_simulated_client_preview_342p_summary.json",
        {
            "decision": "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY",
            "qa_fail_count": 0,
        },
    )
    _write_json(dir_342p / "reviewed_plus_simulated_client_preview_342p_qa.json", {"qa_fail_count": 0, "checks": []})

    candidate_rows = []
    for idx in range(1, 4):
        candidate_rows.append(
            {
                "export_candidate_row_id": f"row_h_{idx}",
                "review_item_id": f"review_h_{idx}",
                "metric_standardized": "ROE",
                "year_standardized": f"202{idx}A",
                "value_numeric": 9.0 + idx,
                "normalized_unit": "%",
                "data_trust_level": "HUMAN_REVIEWED",
                "required_disclaimer": False,
                "requires_later_audit": False,
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
                "final_confirmed": False,
                "source_stage": "342Q",
                "preview_source_type": "HUMAN_REVIEWED",
                "audit_label": "AUDIT_LABEL_HUMAN_REVIEWED",
                "package_warning_level": "MEDIUM",
                "corpus_pdf_id": "pdf_h",
                "file_name": "h.pdf",
                "table_id": "table_h",
                "source_page": idx,
                "bbox": "[1,2,3,4]",
                "image_path": "img_h.jpg",
                "evidence": "<table>roe</table>",
                "display_warning": "spot check only",
                "package_note": "human row",
                "collision_key": "",
            }
        )
    for idx in range(1, 5):
        candidate_rows.append(
            {
                "export_candidate_row_id": f"row_d_{idx}",
                "review_item_id": f"review_d_{idx}",
                "metric_standardized": "EPS",
                "year_standardized": f"202{idx}A",
                "value_numeric": 1.0 + idx,
                "normalized_unit": "元",
                "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
                "required_disclaimer": True,
                "requires_later_audit": True,
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
                "final_confirmed": False,
                "source_stage": "342Q",
                "preview_source_type": "SIMULATED_DIRECT",
                "audit_label": "AUDIT_LABEL_SIMULATED_DIRECT",
                "package_warning_level": "HIGH",
                "corpus_pdf_id": "pdf_d",
                "file_name": "d.pdf",
                "table_id": "table_d",
                "source_page": idx,
                "bbox": "[1,2,3,4]",
                "image_path": "img_d.jpg",
                "evidence": "<table>eps</table>",
                "display_warning": "simulation only",
                "package_note": "later audit required",
                "collision_key": f"collision_d_{idx}",
                "adoption_confidence": 0.97,
            }
        )
    for idx in range(1, 5):
        candidate_rows.append(
            {
                "export_candidate_row_id": f"row_c_{idx}",
                "review_item_id": f"review_c_{idx}",
                "metric_standardized": "revenue",
                "year_standardized": f"202{idx}E",
                "value_numeric": 10.0 + idx,
                "normalized_unit": "CNY100M",
                "data_trust_level": "SIMULATED_CORRECTION_ADOPTED",
                "required_disclaimer": True,
                "requires_later_audit": True,
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
                "final_confirmed": False,
                "source_stage": "342Q",
                "preview_source_type": "SIMULATED_CORRECTED",
                "audit_label": "AUDIT_LABEL_SIMULATED_CORRECTED",
                "package_warning_level": "HIGH",
                "corpus_pdf_id": "pdf_c",
                "file_name": "c.pdf",
                "table_id": "table_c",
                "source_page": idx,
                "bbox": "[1,2,3,4]",
                "image_path": "img_c.jpg",
                "evidence": "<table>rev</table>",
                "display_warning": "simulation corrected only",
                "package_note": "later audit required",
                "collision_key": "",
                "adoption_confidence": 0.91,
                "original_metric_standardized": "revenue_yoy",
                "original_normalized_unit": "CNY100M",
                "correction_pattern": "REVENUE_AMOUNT_NOT_YOY",
                "correction_reason": "use corrected row",
            }
        )

    candidate_df = pd.DataFrame(candidate_rows)
    collision_df = pd.DataFrame(
        [
            {
                "collision_type": "DUPLICATE_METRIC_YEAR_SOURCE",
                "collision_key": "collision_d_1",
                "review_item_id": "review_d_1",
                "winner_review_item_id": "review_d_1",
                "collision_severity": "HIGH",
            }
        ]
    )
    backlog_df = pd.DataFrame(
        [
            {
                "remaining_review_count": 18,
                "still_human_required_count": 6,
                "backlog_note": "summary only",
                "recommended_next_review_action": "continue queue expansion",
            }
        ]
    )
    dir_342r.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_342r / "audit_labeled_export_candidate_package_342r_summary.json",
        {
            "decision": "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY",
            "ready_for_342s": True,
            "qa_fail_count": 0,
            "export_candidate_package_row_count": len(candidate_df),
            "human_reviewed_candidate_count": 3,
            "simulated_candidate_count": 8,
            "simulated_direct_candidate_count": 4,
            "simulated_corrected_candidate_count": 4,
            "collision_logged_count": 1,
            "severe_collision_count": 1,
            "still_human_required_count": 6,
            "remaining_review_count": 18,
        },
    )
    _write_json(dir_342r / "audit_labeled_export_candidate_package_342r_qa.json", {"qa_fail_count": 0, "checks": []})
    _write_excel(
        dir_342r / "audit_labeled_export_candidate_package_342r.xlsx",
        {
            "03_EXPORT_CANDIDATES": candidate_df,
            "10_COLLISION_CONTEXT": collision_df,
            "11_BACKLOG_CONTEXT": backlog_df,
        },
    )
    return dir_342s, dir_342r, dir_342q, dir_342p


def test_343a_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_342s, dir_342r, dir_342q, dir_342p = _seed_343a_inputs(case_root)
        artifacts = build_review_queue_schema_343a(
            snapshot_342s_dir=dir_342s,
            audit_labeled_package_342r_dir=dir_342r,
            preview_audit_342q_dir=dir_342q,
            reviewed_plus_preview_342p_dir=dir_342p,
            output_dir=case_root / "output" / "review_queue_schema_343a",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["ready_for_343b"] is True
        assert summary["field_count"] == schema_field_count()
        assert summary["human_reviewed_sample_count"] == 3
        assert summary["simulated_sample_count"] == 8
        assert summary["summary_derived_sample_count"] == 1
        assert summary["sample_queue_item_count"] == 12
        assert summary["argilla_mapping_generated"] is True
        assert summary["no_write_back_proof_passed"] is True
        placeholder_rows = [row for row in artifacts["sample_items"] if row["source_detail_level"] == "SUMMARY_DERIVED"]
        assert len(placeholder_rows) == 1
        assert placeholder_rows[0]["queue_reason_code"] == "BACKLOG_REVIEW"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343a_not_ready_if_342s_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_342s, dir_342r, dir_342q, dir_342p = _seed_343a_inputs(case_root)
        summary_path = dir_342s / "package_audit_snapshot_demo_handoff_342s_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["decision"] = "PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_NOT_READY"
        summary["ready_for_343a"] = False
        _write_json(summary_path, summary)

        artifacts = build_review_queue_schema_343a(
            snapshot_342s_dir=dir_342s,
            audit_labeled_package_342r_dir=dir_342r,
            preview_audit_342q_dir=dir_342q,
            reviewed_plus_preview_342p_dir=dir_342p,
            output_dir=case_root / "output" / "review_queue_schema_343a",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["ready_for_343b"] is False
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
