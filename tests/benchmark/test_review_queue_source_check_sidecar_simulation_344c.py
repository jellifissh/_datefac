from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from datefac.benchmark.review_queue_source_check_sidecar_simulation_344c import (
    NOT_READY_DECISION_344C,
    READY_DECISION_344C,
    build_review_queue_source_check_sidecar_simulation_344c,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_CHECK_INGESTION_344B_DIR = (
    PROJECT_ROOT / "output" / "review_queue_source_check_evidence_review_ingestion_344b"
)
SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR = (
    PROJECT_ROOT / "output" / "review_queue_source_check_evidence_enrichment_344a2"
)
DEMO_AUDIT_SNAPSHOT_343O_DIR = (
    PROJECT_ROOT / "output" / "review_queue_demo_audit_snapshot_343o"
)
LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR = (
    PROJECT_ROOT / "output" / "review_queue_limited_demo_export_package_343n"
)
HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR = (
    PROJECT_ROOT / "output" / "review_queue_human_confirmed_sidecar_simulation_343m"
)
PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR = (
    PROJECT_ROOT / "output" / "review_queue_pure_human_attestation_ingestion_343l"
)
REVIEW_QUEUE_SCHEMA_343A_DIR = PROJECT_ROOT / "output" / "review_queue_schema_343a"


def _make_output_dir() -> Path:
    tmp_root = Path(
        tempfile.mkdtemp(prefix="codex_344c_", dir=str(Path(tempfile.gettempdir())))
    )
    output_dir = tmp_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_artifacts(
    *,
    source_check_ingestion_344b_dir: Path,
    output_dir: Path,
):
    return build_review_queue_source_check_sidecar_simulation_344c(
        source_check_ingestion_344b_dir=source_check_ingestion_344b_dir,
        source_check_evidence_enrichment_344a2_dir=SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR,
        demo_audit_snapshot_343o_dir=DEMO_AUDIT_SNAPSHOT_343O_DIR,
        limited_demo_export_package_343n_dir=LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR,
        human_confirmed_sidecar_simulation_343m_dir=HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR,
        pure_human_attestation_ingestion_343l_dir=PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR,
        review_queue_schema_343a_dir=REVIEW_QUEUE_SCHEMA_343A_DIR,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )


def test_344c_ready_path() -> None:
    output_dir = _make_output_dir()
    try:
        artifacts = _build_artifacts(
            source_check_ingestion_344b_dir=SOURCE_CHECK_INGESTION_344B_DIR,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION_344C
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["source_check_input_sidecar_row_count"] == 19
        assert summary["source_check_apply_plan_row_count"] == 19
        assert summary["source_check_apply_confirm_count"] == 10
        assert summary["source_check_apply_correct_count"] == 9
        assert summary["source_check_apply_blocked_count"] == 0
        assert summary["source_check_applied_sidecar_row_count"] == 19
        assert summary["corrections_applied_count"] == 9
        assert summary["prior_demo_trusted_row_count"] == 10
        assert summary["source_check_trusted_row_count"] == 19
        assert summary["expanded_trusted_candidate_count"] == 29
        assert summary["deduplicated_expanded_trusted_candidate_count"] == 29
        assert summary["dedup_conflict_count"] == 0
        assert (
            summary["expanded_trusted_scope"]
            == "343O_DEMO_PLUS_344B_SOURCE_CHECK_RESOLVED"
        )
        assert summary["source_check_sidecar_apply_simulation_completed"] is True
        assert summary["source_check_applied_sidecar_generated"] is True
        assert summary["expanded_trusted_candidates_generated"] is True
        assert summary["expanded_trust_gate_evaluated"] is True
        assert summary["dedup_audit_generated"] is True
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["global_strict_human_review_completed"] is False
        assert summary["ready_for_344d"] is True
        assert (
            summary["recommended_344d_scope"]
            == "expanded_trusted_export_package_generation_for_review_demo_only"
        )
        assert summary["qa_fail_count"] == 0
        assert summary["no_write_back_proof_passed"] is True
        assert len(artifacts["source_check_apply_plan_rows"]) == 19
        assert len(artifacts["source_check_applied_sidecar_rows"]) == 19
        assert len(artifacts["corrections_applied_rows"]) == 9
        assert len(artifacts["expanded_trusted_candidate_rows"]) == 29
        assert artifacts["expanded_trust_gate"]["expanded_trusted_candidate_count"] == 29
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)


def test_344c_not_ready_if_344b_not_ready() -> None:
    output_dir = _make_output_dir()
    tmp_dir = Path(
        tempfile.mkdtemp(prefix="codex_344c_invalid_", dir=str(Path(tempfile.gettempdir())))
    )
    try:
        copied_344b_dir = tmp_dir / "review_queue_source_check_evidence_review_ingestion_344b"
        shutil.copytree(SOURCE_CHECK_INGESTION_344B_DIR, copied_344b_dir)
        summary_path = copied_344b_dir / "review_queue_source_check_evidence_review_ingestion_344b_summary.json"
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        payload["decision"] = "SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_NOT_READY"
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        artifacts = _build_artifacts(
            source_check_ingestion_344b_dir=copied_344b_dir,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == NOT_READY_DECISION_344C
        assert summary["ready_for_344d"] is False
        assert summary["qa_fail_count"] > 0
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)

