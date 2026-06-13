from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_strict_human_review_package_344f import (  # noqa: E402
    NOT_READY_DECISION_344F,
    READY_DECISION_344F,
    build_review_queue_strict_human_review_package_344f,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_strict_human_review_package_344f"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_344f_inputs(root: Path) -> Path:
    dir_344e = root / "output" / "review_queue_expanded_demo_audit_snapshot_344e"
    dir_344d = root / "output" / "review_queue_expanded_trusted_demo_export_package_344d"
    dir_344e.mkdir(parents=True, exist_ok=True)
    dir_344d.mkdir(parents=True, exist_ok=True)

    summary_344e = {
        "decision": "EXPANDED_TRUSTED_DEMO_AUDIT_SNAPSHOT_344E_READY",
        "review_queue_schema_version": "343A.review_queue.v1",
        "input_expanded_export_row_count": 29,
        "audit_label_row_count": 29,
        "prior_demo_trusted_row_count": 10,
        "source_check_trusted_row_count": 19,
        "source_check_confirmed_row_count": 10,
        "source_check_corrected_row_count": 9,
        "correction_row_count": 9,
        "expanded_review_demo_package_generated": True,
        "expanded_demo_handoff_ready": True,
        "expanded_demo_audit_snapshot_generated": True,
        "expanded_demo_arc_closed": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": True,
    }
    final_gate_344e = {
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
    }

    export_rows: list[dict] = []
    for index in range(1, 30):
        is_demo = index <= 10
        export_rows.append(
            {
                "queue_item_id": f"343a::queue::{index:04d}",
                "review_item_id": f"review::{index:04d}",
                "metric_standardized": "EPS" if is_demo else ("YOY" if index % 2 == 1 else "Revenue"),
                "year_standardized": f"202{(index % 5) + 4}A",
                "value_numeric": f"{index * 1.1:.1f}",
                "normalized_unit": "%" if not is_demo and index > 20 else "元",
                "source_pdf_name": f"pdf_{index:03d}.pdf",
                "page_number": (index % 5) + 1,
                "table_id": f"table_{index:03d}",
                "bbox": f"[{index}, {index + 1}, {index + 2}, {index + 3}]",
                "image_path": f"D:\\fake\\images\\image_{index:03d}.jpg",
                "source_text_snippet": f"source text {index}",
                "source_html_snippet": f"<table><tr><td>{index}</td></tr></table>",
                "source_check_status": "" if is_demo else ("CONFIRMED" if index <= 20 else "CORRECTED"),
                "audit_labels": ["DEMO_ONLY", "NOT_FORMAL_CLIENT_EXPORT"],
                "source_lineage_stage": "343N_DEMO" if is_demo else "344B_SOURCE_CHECK",
                "expanded_trust_source": "PRIOR_DEMO_TRUSTED_ARC" if is_demo else "SOURCE_CHECK_RESOLVED",
                "expanded_export_scope": "343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED",
                "source_lineage_summary": "Prior demo trusted arc" if is_demo else "Source-check resolved row",
                "export_usage": "REVIEW_DEMO_ONLY",
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
            }
        )

    artifact_index = [
        {
            "artifact_name": "344D export rows",
            "path": str(
                dir_344d
                / "review_queue_expanded_trusted_demo_export_package_344d_export_rows.jsonl"
            ),
            "role": "Machine-readable 29-row expanded trusted package",
        }
    ]

    _write_json(
        dir_344e / "review_queue_expanded_demo_audit_snapshot_344e_summary.json",
        summary_344e,
    )
    _write_json(
        dir_344e / "review_queue_expanded_demo_audit_snapshot_344e_final_export_gate_snapshot.json",
        final_gate_344e,
    )
    _write_json(
        dir_344e / "review_queue_expanded_demo_audit_snapshot_344e_artifact_index.json",
        artifact_index,
    )
    _write_jsonl(
        dir_344d / "review_queue_expanded_trusted_demo_export_package_344d_export_rows.jsonl",
        export_rows,
    )
    return dir_344e


def test_344f_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_344e = _seed_344f_inputs(case_root)
        artifacts = build_review_queue_strict_human_review_package_344f(
            expanded_demo_audit_snapshot_344e_dir=dir_344e,
            output_dir=case_root / "output" / "review_queue_strict_human_review_package_344f",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        manifest = artifacts["manifest"]
        final_gate = artifacts["final_gate_snapshot"]
        review_rows = artifacts["review_rows"]
        assert summary["decision"] == READY_DECISION_344F
        assert summary["strict_review_row_count"] == 29
        assert summary["prior_demo_trusted_row_count"] == 10
        assert summary["source_check_trusted_row_count"] == 19
        assert summary["source_check_confirmed_row_count"] == 10
        assert summary["corrected_row_count"] == 9
        assert summary["qa_fail_count"] == 0
        assert summary["no_write_back_proof_passed"] is True
        assert manifest["decision"] == READY_DECISION_344F
        assert manifest["strict_review_row_count"] == 29
        assert manifest["qa_fail_count"] == 0
        assert manifest["no_write_back_proof_passed"] is True
        assert manifest["upstream_workbooks_unchanged"] is True
        assert final_gate["strict_human_review_package_generated"] is True
        assert final_gate["global_strict_human_review_completed"] is False
        assert final_gate["formal_client_export_allowed"] is False
        assert final_gate["client_ready"] is False
        assert final_gate["production_ready"] is False
        assert final_gate["export_usage"] == "STRICT_HUMAN_REVIEW_ONLY"
        assert len(review_rows) == 29
        assert all(row["needs_strict_human_review"] is True for row in review_rows)
        assert all(row["client_export_allowed"] is False for row in review_rows)
        assert all(row["strict_human_review_decision"] == "" for row in review_rows)
        assert all(row["strict_human_reviewer"] == "" for row in review_rows)
        assert all(row["strict_human_reviewed_at"] == "" for row in review_rows)
        assert all(row["strict_human_review_notes"] == "" for row in review_rows)
        assert len(artifacts["artifact_index_rows"]) >= 7
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_344f_not_ready_if_344e_gate_turns_true() -> None:
    case_root = _make_case_root()
    try:
        dir_344e = _seed_344f_inputs(case_root)
        gate_path = (
            dir_344e
            / "review_queue_expanded_demo_audit_snapshot_344e_final_export_gate_snapshot.json"
        )
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        gate["formal_client_export_allowed"] = True
        _write_json(gate_path, gate)
        artifacts = build_review_queue_strict_human_review_package_344f(
            expanded_demo_audit_snapshot_344e_dir=dir_344e,
            output_dir=case_root / "output" / "review_queue_strict_human_review_package_344f",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION_344F
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
