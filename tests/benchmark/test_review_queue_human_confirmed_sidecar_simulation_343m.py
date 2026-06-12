from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from datefac.benchmark.review_queue_human_confirmed_sidecar_simulation_343m import (
    NOT_READY_DECISION_343M,
    READY_DECISION_343M,
    build_review_queue_human_confirmed_sidecar_simulation_343m,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INGESTION_343L_DIR = PROJECT_ROOT / "output" / "review_queue_pure_human_attestation_ingestion_343l"
PACKAGE_343K_DIR = PROJECT_ROOT / "output" / "review_queue_pure_human_attestation_package_343k"
SOURCE_EVIDENCE_343I2_DIR = PROJECT_ROOT / "output" / "review_queue_source_evidence_enrichment_343i2"
AUDIT_SUMMARY_343H_DIR = PROJECT_ROOT / "output" / "review_queue_audit_summary_343h"
SCHEMA_343A_DIR = PROJECT_ROOT / "output" / "review_queue_schema_343a"


def _make_output_dir() -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="codex_343m_", dir=str(Path(tempfile.gettempdir()))))
    output_dir = tmp_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_artifacts(*, pure_human_attestation_ingestion_343l_dir: Path, output_dir: Path):
    return build_review_queue_human_confirmed_sidecar_simulation_343m(
        pure_human_attestation_ingestion_343l_dir=pure_human_attestation_ingestion_343l_dir,
        pure_human_attestation_package_343k_dir=PACKAGE_343K_DIR,
        source_evidence_enrichment_343i2_dir=SOURCE_EVIDENCE_343I2_DIR,
        audit_summary_343h_dir=AUDIT_SUMMARY_343H_DIR,
        review_queue_schema_343a_dir=SCHEMA_343A_DIR,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )


def test_343m_ready_path() -> None:
    output_dir = _make_output_dir()
    try:
        artifacts = _build_artifacts(
            pure_human_attestation_ingestion_343l_dir=INGESTION_343L_DIR,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION_343M
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["input_human_attested_row_count"] == 10
        assert summary["valid_human_attested_row_count"] == 10
        assert summary["sidecar_row_count"] == 10
        assert summary["sidecar_human_accept_count"] == 10
        assert summary["sidecar_human_correct_count"] == 0
        assert summary["sidecar_blocked_count"] == 0
        assert summary["limited_export_candidate_row_count"] == 10
        assert summary["remaining_source_check_backlog_count"] == 19
        assert summary["package_strict_human_review_completed"] is True
        assert summary["strict_human_review_completed_scope"] == "343K_PACKAGE_ONLY"
        assert summary["global_strict_human_review_completed"] is False
        assert summary["sidecar_apply_simulation_completed"] is True
        assert summary["limited_export_gate_evaluated"] is True
        assert summary["limited_package_export_candidate_allowed"] is True
        assert summary["limited_export_scope"] == "343K_PACKAGE_ONLY"
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["ready_for_343n"] is True
        assert summary["recommended_343n_scope"] == "limited_human_confirmed_export_package_generation_for_demo_only"
        assert summary["qa_fail_count"] == 0
        assert summary["no_write_back_proof_passed"] is True
        assert artifacts["limited_export_gate"]["limited_package_export_candidate_allowed"] is True
        assert all(row["export_scope"] == "343K_PACKAGE_ONLY" for row in artifacts["limited_export_candidate_rows"])
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)


def test_343m_not_ready_if_343l_scope_not_package_only() -> None:
    output_dir = _make_output_dir()
    tmp_dir = Path(tempfile.mkdtemp(prefix="codex_343m_invalid_", dir=str(Path(tempfile.gettempdir()))))
    try:
        copied_343l_dir = tmp_dir / "review_queue_pure_human_attestation_ingestion_343l"
        shutil.copytree(INGESTION_343L_DIR, copied_343l_dir)
        summary_path = copied_343l_dir / "review_queue_pure_human_attestation_ingestion_343l_summary.json"
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        payload["strict_human_review_completed_scope"] = "GLOBAL"
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        artifacts = _build_artifacts(
            pure_human_attestation_ingestion_343l_dir=copied_343l_dir,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == NOT_READY_DECISION_343M
        assert summary["qa_fail_count"] > 0
        assert summary["limited_package_export_candidate_allowed"] is False
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
