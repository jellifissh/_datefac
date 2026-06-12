from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from datefac.benchmark.review_queue_pure_human_attestation_package_343k import (
    NOT_READY_DECISION_343K,
    READY_DECISION_343K,
    build_review_queue_pure_human_attestation_package_343k,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRICT_REVIEW_INGESTION_343J_DIR = (
    PROJECT_ROOT / "output" / "review_queue_strict_review_ingestion_343j"
)
SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR = (
    PROJECT_ROOT / "output" / "review_queue_source_evidence_enrichment_343i2"
)
REVIEW_QUEUE_SCHEMA_343A_DIR = PROJECT_ROOT / "output" / "review_queue_schema_343a"


def _make_output_dir() -> Path:
    tmp_root = Path(
        tempfile.mkdtemp(prefix="codex_343k_", dir=str(Path(tempfile.gettempdir())))
    )
    output_dir = tmp_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_artifacts(
    *,
    strict_review_ingestion_343j_dir: Path,
    source_evidence_enrichment_343i2_dir: Path,
    review_queue_schema_343a_dir: Path,
    output_dir: Path,
):
    return build_review_queue_pure_human_attestation_package_343k(
        strict_review_ingestion_343j_dir=strict_review_ingestion_343j_dir,
        source_evidence_enrichment_343i2_dir=source_evidence_enrichment_343i2_dir,
        review_queue_schema_343a_dir=review_queue_schema_343a_dir,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )


def test_343k_ready_path() -> None:
    output_dir = _make_output_dir()
    try:
        artifacts = _build_artifacts(
            strict_review_ingestion_343j_dir=STRICT_REVIEW_INGESTION_343J_DIR,
            source_evidence_enrichment_343i2_dir=SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR,
            review_queue_schema_343a_dir=REVIEW_QUEUE_SCHEMA_343A_DIR,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION_343K
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["input_ai_assisted_strict_review_confirm_count"] == 10
        assert summary["attestation_item_count"] == 10
        assert summary["evidence_resolved_count"] == 10
        assert summary["source_pdf_name_available_count"] == 10
        assert summary["source_text_snippet_available_count"] == 10
        assert summary["pure_human_attestation_package_generated"] is True
        assert summary["attestation_template_generated"] is True
        assert summary["reviewer_instructions_generated"] is True
        assert summary["fill_guide_generated"] is True
        assert summary["expected_import_contract_generated"] is True
        assert summary["waiting_for_pure_human_attestation"] is True
        assert summary["pure_human_attestation_result_ingested"] is False
        assert summary["pure_strict_human_confirm_count"] == 0
        assert summary["ai_assisted_strict_review_confirm_count"] == 10
        assert summary["pure_strict_human_review_completed"] is False
        assert summary["strict_human_review_completed"] is False
        assert summary["requires_pure_human_confirmation"] is True
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["ready_for_343l"] is False
        assert (
            summary["recommended_343l_scope"]
            == "pure_human_confirmation_attestation_result_ingestion_after_user_fills_workbook"
        )
        assert summary["qa_fail_count"] == 0
        assert summary["no_write_back_proof_passed"] is True
        assert artifacts["attestation_items"][0]["human_attestation_decision"] == ""
        assert artifacts["attestation_items"][0]["strict_review_decision"] == "STRICT_CONFIRM"
        assert artifacts["attestation_items"][0]["source_pdf_name"] != ""
        assert (
            artifacts["expected_import_contract"]["required_sheet_name"]
            == "04_ATTESTATION_TEMPLATE"
        )
        assert (
            "independently inspect source evidence"
            in artifacts["reviewer_instructions_markdown"]
        )
        assert "03_ATTESTATION_ITEMS" in artifacts["workbook_sheets"]
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)


def test_343k_not_ready_if_343j_summary_not_ready() -> None:
    output_dir = _make_output_dir()
    tmp_dir = Path(
        tempfile.mkdtemp(prefix="codex_343k_invalid_", dir=str(Path(tempfile.gettempdir())))
    )
    try:
        copied_343j_dir = tmp_dir / "review_queue_strict_review_ingestion_343j"
        shutil.copytree(STRICT_REVIEW_INGESTION_343J_DIR, copied_343j_dir)
        summary_path = (
            copied_343j_dir / "review_queue_strict_review_ingestion_343j_summary.json"
        )
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
        summary_payload["decision"] = "AI_ASSISTED_STRICT_REVIEW_INGESTION_343J_NOT_READY"
        summary_payload["ready_for_343k"] = False
        summary_path.write_text(
            json.dumps(summary_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        artifacts = _build_artifacts(
            strict_review_ingestion_343j_dir=copied_343j_dir,
            source_evidence_enrichment_343i2_dir=SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR,
            review_queue_schema_343a_dir=REVIEW_QUEUE_SCHEMA_343A_DIR,
            output_dir=output_dir,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == NOT_READY_DECISION_343K
        assert summary["attestation_item_count"] == 10
        assert summary["qa_fail_count"] > 0
        failed_checks = {
            check["check_name"]: check["status"] for check in artifacts["qa_json"]["checks"]
        }
        assert failed_checks["inputs::343j_input_exists_and_ready"] == "FAIL"
    finally:
        shutil.rmtree(output_dir.parent, ignore_errors=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
