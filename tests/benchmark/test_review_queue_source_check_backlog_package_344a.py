from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from datefac.benchmark.review_queue_source_check_backlog_package_344a import (
    NOT_READY_DECISION_344A,
    WAITING_DECISION_344A,
    build_review_queue_source_check_backlog_package_344a,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_343O_DIR = PROJECT_ROOT / "output" / "review_queue_demo_audit_snapshot_343o"
DEMO_343N_DIR = PROJECT_ROOT / "output" / "review_queue_limited_demo_export_package_343n"
SIM_343M_DIR = PROJECT_ROOT / "output" / "review_queue_human_confirmed_sidecar_simulation_343m"
AUDIT_343H_DIR = PROJECT_ROOT / "output" / "review_queue_audit_summary_343h"
INGEST_343G_DIR = PROJECT_ROOT / "output" / "review_queue_spot_check_ingestion_343g"
PACKAGE_343F_DIR = PROJECT_ROOT / "output" / "review_queue_spot_check_package_343f"
SCHEMA_343A_DIR = PROJECT_ROOT / "output" / "review_queue_schema_343a"


def _make_output_dir() -> Path:
    tmp_root = Path(tempfile.mkdtemp(prefix="codex_344a_", dir=str(Path(tempfile.gettempdir()))))
    output_dir = tmp_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_artifacts(*, demo_audit_snapshot_343o_dir: Path, output_dir: Path):
    return build_review_queue_source_check_backlog_package_344a(
        demo_audit_snapshot_343o_dir=demo_audit_snapshot_343o_dir,
        limited_demo_export_package_343n_dir=DEMO_343N_DIR,
        human_confirmed_sidecar_simulation_343m_dir=SIM_343M_DIR,
        audit_summary_343h_dir=AUDIT_343H_DIR,
        spot_check_ingestion_343g_dir=INGEST_343G_DIR,
        spot_check_package_343f_dir=PACKAGE_343F_DIR,
        review_queue_schema_343a_dir=SCHEMA_343A_DIR,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )


def test_344a_waiting_ready_path() -> None:
    output_dir = _make_output_dir()
    try:
        artifacts = _build_artifacts(
            demo_audit_snapshot_343o_dir=DEMO_343O_DIR,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == WAITING_DECISION_344A
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["input_remaining_source_check_backlog_count"] == 19
        assert summary["source_check_backlog_item_count"] == 19
        assert summary["deduplicated_backlog_item_count"] == 19
        assert summary["evidence_resolved_count"] == 0
        assert summary["evidence_partial_count"] == 0
        assert summary["evidence_unresolved_count"] == 19
        assert summary["source_pdf_name_available_count"] == 0
        assert summary["source_text_snippet_available_count"] == 0
        assert summary["source_check_backlog_package_generated"] is True
        assert summary["review_template_generated"] is True
        assert summary["reviewer_instructions_generated"] is True
        assert summary["fill_guide_generated"] is True
        assert summary["expected_import_contract_generated"] is True
        assert summary["waiting_for_source_check_review"] is True
        assert summary["source_check_result_ingested"] is False
        assert summary["source_check_backlog_resolved"] is False
        assert summary["demo_arc_closed"] is True
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["ready_for_344b"] is False
        assert summary["recommended_344b_scope"] == "source_check_backlog_result_ingestion_after_user_fills_workbook"
        assert summary["qa_fail_count"] == 0
        assert summary["no_write_back_proof_passed"] is True
        assert all(item["source_check_decision"] == "" for item in artifacts["backlog_items"])
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)


def test_344a_not_ready_if_343o_decision_invalid() -> None:
    output_dir = _make_output_dir()
    tmp_dir = Path(tempfile.mkdtemp(prefix="codex_344a_invalid_", dir=str(Path(tempfile.gettempdir()))))
    try:
        copied_343o_dir = tmp_dir / "review_queue_demo_audit_snapshot_343o"
        shutil.copytree(DEMO_343O_DIR, copied_343o_dir)
        summary_path = copied_343o_dir / "review_queue_demo_audit_snapshot_343o_summary.json"
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        payload["decision"] = "BROKEN"
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        artifacts = _build_artifacts(
            demo_audit_snapshot_343o_dir=copied_343o_dir,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == NOT_READY_DECISION_344A
        assert summary["qa_fail_count"] > 0
        assert summary["source_check_backlog_package_generated"] is False
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
