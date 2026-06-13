from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from datefac.benchmark.review_queue_expanded_trusted_demo_export_package_344d import (
    NOT_READY_DECISION_344D,
    READY_DECISION_344D,
    build_review_queue_expanded_trusted_demo_export_package_344d,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIM_344C_DIR = PROJECT_ROOT / "output" / "review_queue_source_check_sidecar_simulation_344c"
INGEST_344B_DIR = PROJECT_ROOT / "output" / "review_queue_source_check_evidence_review_ingestion_344b"
AUDIT_343O_DIR = PROJECT_ROOT / "output" / "review_queue_demo_audit_snapshot_343o"
DEMO_343N_DIR = PROJECT_ROOT / "output" / "review_queue_limited_demo_export_package_343n"
SCHEMA_343A_DIR = PROJECT_ROOT / "output" / "review_queue_schema_343a"


def _make_output_dir() -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="codex_344d_", dir=str(Path(tempfile.gettempdir()))))
    output_dir = tmp_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_artifacts(*, source_check_sidecar_simulation_344c_dir: Path, output_dir: Path):
    return build_review_queue_expanded_trusted_demo_export_package_344d(
        source_check_sidecar_simulation_344c_dir=source_check_sidecar_simulation_344c_dir,
        source_check_ingestion_344b_dir=INGEST_344B_DIR,
        demo_audit_snapshot_343o_dir=AUDIT_343O_DIR,
        limited_demo_export_package_343n_dir=DEMO_343N_DIR,
        review_queue_schema_343a_dir=SCHEMA_343A_DIR,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )


def test_344d_ready_path() -> None:
    output_dir = _make_output_dir()
    try:
        artifacts = _build_artifacts(
            source_check_sidecar_simulation_344c_dir=SIM_344C_DIR,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION_344D
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["input_expanded_trusted_candidate_count"] == 29
        assert summary["expanded_export_row_count"] == 29
        assert summary["audit_label_row_count"] == 29
        assert summary["prior_demo_trusted_row_count"] == 10
        assert summary["source_check_trusted_row_count"] == 19
        assert summary["source_check_confirmed_row_count"] == 10
        assert summary["source_check_corrected_row_count"] == 9
        assert summary["correction_row_count"] == 9
        assert summary["dedup_conflict_count"] == 0
        assert summary["expanded_export_scope"] == "343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED"
        assert summary["export_usage"] == "REVIEW_DEMO_ONLY"
        assert summary["expanded_review_demo_package_generated"] is True
        assert summary["expanded_demo_handoff_ready"] is True
        assert summary["expanded_export_gate_generated"] is True
        assert summary["lineage_summary_generated"] is True
        assert summary["audit_labels_generated"] is True
        assert summary["source_check_backlog_resolved"] is True
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["global_strict_human_review_completed"] is False
        assert summary["ready_for_344e"] is True
        assert (
            summary["recommended_344e_scope"]
            == "expanded_trusted_demo_audit_snapshot_and_final_handoff_summary"
        )
        assert summary["qa_fail_count"] == 0
        assert summary["no_write_back_proof_passed"] is True

        export_rows = artifacts["export_rows"]
        assert len(export_rows) == 29
        assert sum(1 for row in export_rows if row["source_lineage_stage"] == "343N_DEMO") == 10
        assert sum(1 for row in export_rows if row["source_lineage_stage"] == "344B_SOURCE_CHECK") == 19
        corrected_rows = [
            row for row in export_rows if row.get("source_check_status") == "CORRECTED"
        ]
        assert len(corrected_rows) == 9
        assert all(row["metric_standardized"] == "YOY" for row in corrected_rows)
        assert all(row["normalized_unit"] == "%" for row in corrected_rows)
        assert all(row["export_usage"] == "REVIEW_DEMO_ONLY" for row in export_rows)
        assert all(row["formal_client_export_allowed"] is False for row in export_rows)
        assert all("REVIEW_DEMO_ONLY" in row["audit_labels"] for row in artifacts["audit_label_rows"])
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)


def test_344d_not_ready_if_344c_has_dedup_conflict() -> None:
    output_dir = _make_output_dir()
    tmp_dir = Path(tempfile.mkdtemp(prefix="codex_344d_invalid_", dir=str(Path(tempfile.gettempdir()))))
    try:
        copied_344c_dir = tmp_dir / "review_queue_source_check_sidecar_simulation_344c"
        shutil.copytree(SIM_344C_DIR, copied_344c_dir)

        summary_path = copied_344c_dir / "review_queue_source_check_sidecar_simulation_344c_summary.json"
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
        summary_payload["dedup_conflict_count"] = 1
        summary_payload["ready_for_344d"] = False
        summary_path.write_text(
            json.dumps(summary_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        dedup_path = copied_344c_dir / "review_queue_source_check_sidecar_simulation_344c_dedup_audit.jsonl"
        lines = [json.loads(line) for line in dedup_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        lines[0]["dedup_status"] = "CONFLICT"
        dedup_path.write_text(
            "\n".join(json.dumps(line, ensure_ascii=False) for line in lines),
            encoding="utf-8",
        )

        artifacts = _build_artifacts(
            source_check_sidecar_simulation_344c_dir=copied_344c_dir,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == NOT_READY_DECISION_344D
        assert summary["qa_fail_count"] > 0
        assert summary["expanded_review_demo_package_generated"] is False
        assert summary["ready_for_344e"] is False
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
