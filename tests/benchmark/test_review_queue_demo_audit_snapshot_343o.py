from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from datefac.benchmark.review_queue_demo_audit_snapshot_343o import (
    NOT_READY_DECISION_343O,
    READY_DECISION_343O,
    build_review_queue_demo_audit_snapshot_343o,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_343N_DIR = PROJECT_ROOT / "output" / "review_queue_limited_demo_export_package_343n"
SIM_343M_DIR = PROJECT_ROOT / "output" / "review_queue_human_confirmed_sidecar_simulation_343m"
INGEST_343L_DIR = PROJECT_ROOT / "output" / "review_queue_pure_human_attestation_ingestion_343l"
AUDIT_343H_DIR = PROJECT_ROOT / "output" / "review_queue_audit_summary_343h"
SCHEMA_343A_DIR = PROJECT_ROOT / "output" / "review_queue_schema_343a"


def _make_output_dir() -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="codex_343o_", dir=str(Path(tempfile.gettempdir()))))
    output_dir = tmp_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_artifacts(*, limited_demo_export_package_343n_dir: Path, output_dir: Path):
    return build_review_queue_demo_audit_snapshot_343o(
        limited_demo_export_package_343n_dir=limited_demo_export_package_343n_dir,
        human_confirmed_sidecar_simulation_343m_dir=SIM_343M_DIR,
        pure_human_attestation_ingestion_343l_dir=INGEST_343L_DIR,
        audit_summary_343h_dir=AUDIT_343H_DIR,
        review_queue_schema_343a_dir=SCHEMA_343A_DIR,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )


def test_343o_ready_path() -> None:
    output_dir = _make_output_dir()
    try:
        artifacts = _build_artifacts(
            limited_demo_export_package_343n_dir=DEMO_343N_DIR,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION_343O
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["input_demo_export_row_count"] == 10
        assert summary["audit_label_row_count"] == 10
        assert summary["limited_export_scope"] == "343K_PACKAGE_ONLY"
        assert summary["export_usage"] == "DEMO_ONLY"
        assert summary["remaining_source_check_backlog_count"] == 19
        assert summary["package_strict_human_review_completed"] is True
        assert summary["global_strict_human_review_completed"] is False
        assert summary["demo_only_export_package_generated"] is True
        assert summary["demo_handoff_ready"] is True
        assert summary["demo_audit_snapshot_generated"] is True
        assert summary["handoff_summary_generated"] is True
        assert summary["executive_summary_generated"] is True
        assert summary["trust_chain_generated"] is True
        assert summary["artifact_index_generated"] is True
        assert summary["export_gate_snapshot_generated"] is True
        assert summary["demo_arc_closed"] is True
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["ready_for_344a"] is True
        assert summary["recommended_344a_scope"] == "source_check_backlog_resolution_package"
        assert summary["qa_fail_count"] == 0
        assert summary["no_write_back_proof_passed"] is True
        assert len(artifacts["trust_chain_rows"]) >= 6
        assert len(artifacts["artifact_index_rows"]) >= 8
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)


def test_343o_not_ready_if_343n_decision_invalid() -> None:
    output_dir = _make_output_dir()
    tmp_dir = Path(tempfile.mkdtemp(prefix="codex_343o_invalid_", dir=str(Path(tempfile.gettempdir()))))
    try:
        copied_343n_dir = tmp_dir / "review_queue_limited_demo_export_package_343n"
        shutil.copytree(DEMO_343N_DIR, copied_343n_dir)
        summary_path = copied_343n_dir / "review_queue_limited_demo_export_package_343n_summary.json"
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        payload["decision"] = "BROKEN"
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        artifacts = _build_artifacts(
            limited_demo_export_package_343n_dir=copied_343n_dir,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == NOT_READY_DECISION_343O
        assert summary["qa_fail_count"] > 0
        assert summary["demo_arc_closed"] is False
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
