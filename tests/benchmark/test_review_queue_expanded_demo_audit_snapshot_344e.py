from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from datefac.benchmark.review_queue_expanded_demo_audit_snapshot_344e import (
    NOT_READY_DECISION_344E,
    READY_DECISION_344E,
    build_review_queue_expanded_demo_audit_snapshot_344e,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_344D_DIR = PROJECT_ROOT / "output" / "review_queue_expanded_trusted_demo_export_package_344d"
SIM_344C_DIR = PROJECT_ROOT / "output" / "review_queue_source_check_sidecar_simulation_344c"
INGEST_344B_DIR = PROJECT_ROOT / "output" / "review_queue_source_check_evidence_review_ingestion_344b"
ENRICH_344A2_DIR = PROJECT_ROOT / "output" / "review_queue_source_check_evidence_enrichment_344a2"
SNAP_343O_DIR = PROJECT_ROOT / "output" / "review_queue_demo_audit_snapshot_343o"
DEMO_343N_DIR = PROJECT_ROOT / "output" / "review_queue_limited_demo_export_package_343n"
SCHEMA_343A_DIR = PROJECT_ROOT / "output" / "review_queue_schema_343a"


def _make_output_dir() -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="codex_344e_", dir=str(Path(tempfile.gettempdir()))))
    output_dir = tmp_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_artifacts(*, expanded_trusted_demo_export_package_344d_dir: Path, output_dir: Path):
    return build_review_queue_expanded_demo_audit_snapshot_344e(
        expanded_trusted_demo_export_package_344d_dir=expanded_trusted_demo_export_package_344d_dir,
        source_check_sidecar_simulation_344c_dir=SIM_344C_DIR,
        source_check_ingestion_344b_dir=INGEST_344B_DIR,
        source_check_evidence_enrichment_344a2_dir=ENRICH_344A2_DIR,
        demo_audit_snapshot_343o_dir=SNAP_343O_DIR,
        limited_demo_export_package_343n_dir=DEMO_343N_DIR,
        review_queue_schema_343a_dir=SCHEMA_343A_DIR,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )


def test_344e_ready_path() -> None:
    output_dir = _make_output_dir()
    try:
        artifacts = _build_artifacts(
            expanded_trusted_demo_export_package_344d_dir=PACKAGE_344D_DIR,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION_344E
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["input_expanded_export_row_count"] == 29
        assert summary["audit_label_row_count"] == 29
        assert summary["prior_demo_trusted_row_count"] == 10
        assert summary["source_check_trusted_row_count"] == 19
        assert summary["source_check_confirmed_row_count"] == 10
        assert summary["source_check_corrected_row_count"] == 9
        assert summary["correction_row_count"] == 9
        assert summary["expanded_export_scope"] == "343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED"
        assert summary["export_usage"] == "REVIEW_DEMO_ONLY"
        assert summary["expanded_demo_audit_snapshot_generated"] is True
        assert summary["final_handoff_summary_generated"] is True
        assert summary["executive_summary_generated"] is True
        assert summary["trust_chain_report_generated"] is True
        assert summary["artifact_index_generated"] is True
        assert summary["final_export_gate_snapshot_generated"] is True
        assert summary["lineage_audit_summary_generated"] is True
        assert summary["metric_distribution_generated"] is True
        assert summary["expanded_demo_arc_closed"] is True
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["global_strict_human_review_completed"] is False
        assert summary["ready_for_345a"] is True
        assert summary["recommended_345a_scope"] == "formal_export_readiness_gap_assessment"
        assert summary["qa_fail_count"] == 0
        assert summary["no_write_back_proof_passed"] is True
        assert len(artifacts["trust_chain_rows"]) >= 12
        assert len(artifacts["artifact_index_rows"]) >= 10
        assert artifacts["lineage_audit_summary"]["source_check_corrected_row_count"] == 9
        assert artifacts["metric_distribution"]["metric_counts"]["YOY"] == 9
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)


def test_344e_not_ready_if_344d_scope_invalid() -> None:
    output_dir = _make_output_dir()
    tmp_dir = Path(tempfile.mkdtemp(prefix="codex_344e_invalid_", dir=str(Path(tempfile.gettempdir()))))
    try:
        copied_344d_dir = tmp_dir / "review_queue_expanded_trusted_demo_export_package_344d"
        shutil.copytree(PACKAGE_344D_DIR, copied_344d_dir)

        summary_path = copied_344d_dir / "review_queue_expanded_trusted_demo_export_package_344d_summary.json"
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        payload["expanded_export_scope"] = "BROKEN_SCOPE"
        payload["ready_for_344e"] = False
        summary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        artifacts = _build_artifacts(
            expanded_trusted_demo_export_package_344d_dir=copied_344d_dir,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == NOT_READY_DECISION_344E
        assert summary["qa_fail_count"] > 0
        assert summary["expanded_demo_arc_closed"] is False
        assert summary["ready_for_345a"] is False
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
