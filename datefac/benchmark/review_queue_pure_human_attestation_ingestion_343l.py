from __future__ import annotations

from pathlib import Path

from datefac.review_queue.ingest_pure_human_attestation_343l import (
    NOT_READY_DECISION_343L,
    READY_DECISION_343L,
    REMEDIATION_REQUIRED_DECISION_343L,
    RECOMMENDED_343M_SCOPE_343L,
    WORKBOOK_SHEETS_343L,
    build_review_queue_pure_human_attestation_ingestion_343l,
)


DEFAULT_PURE_HUMAN_ATTESTATION_PACKAGE_343K_DIR = Path(
    r"D:\_datefac\output\review_queue_pure_human_attestation_package_343k"
)
DEFAULT_STRICT_REVIEW_INGESTION_343J_DIR = Path(
    r"D:\_datefac\output\review_queue_strict_review_ingestion_343j"
)
DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR = Path(
    r"D:\_datefac\output\review_queue_source_evidence_enrichment_343i2"
)
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(
    r"D:\_datefac\output\review_queue_schema_343a"
)
DEFAULT_FILLED_WORKBOOK = Path(
    r"D:\_datefac\input\review_queue_pure_human_attestation_343k_filled\review_queue_pure_human_attestation_package_343k_attestation_template_filled.xlsx"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_pure_human_attestation_ingestion_343l"
)

SUMMARY_FILE_NAME = "review_queue_pure_human_attestation_ingestion_343l_summary.json"
MANIFEST_FILE_NAME = "review_queue_pure_human_attestation_ingestion_343l_manifest.json"
QA_FILE_NAME = "review_queue_pure_human_attestation_ingestion_343l_qa.json"
NO_WRITE_BACK_FILE_NAME = (
    "review_queue_pure_human_attestation_ingestion_343l_no_write_back_proof.json"
)
REPORT_FILE_NAME = "review_queue_pure_human_attestation_ingestion_343l_report.md"
WORKBOOK_FILE_NAME = "review_queue_pure_human_attestation_ingestion_343l.xlsx"
RESULT_FILE_NAME = "review_queue_pure_human_attestation_ingestion_343l_result.jsonl"
VALIDATION_ERRORS_FILE_NAME = (
    "review_queue_pure_human_attestation_ingestion_343l_validation_errors.json"
)
DECISION_SUMMARY_FILE_NAME = (
    "review_queue_pure_human_attestation_ingestion_343l_decision_summary.json"
)
CLIENT_EXPORT_GATE_FILE_NAME = (
    "review_queue_pure_human_attestation_ingestion_343l_client_export_gate.json"
)
SCOPE_BOUNDARY_FILE_NAME = (
    "review_queue_pure_human_attestation_ingestion_343l_scope_boundary.md"
)


__all__ = [
    "CLIENT_EXPORT_GATE_FILE_NAME",
    "DECISION_SUMMARY_FILE_NAME",
    "DEFAULT_FILLED_WORKBOOK",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_PURE_HUMAN_ATTESTATION_PACKAGE_343K_DIR",
    "DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR",
    "DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR",
    "DEFAULT_STRICT_REVIEW_INGESTION_343J_DIR",
    "MANIFEST_FILE_NAME",
    "NOT_READY_DECISION_343L",
    "NO_WRITE_BACK_FILE_NAME",
    "QA_FILE_NAME",
    "READY_DECISION_343L",
    "RECOMMENDED_343M_SCOPE_343L",
    "REMEDIATION_REQUIRED_DECISION_343L",
    "REPORT_FILE_NAME",
    "RESULT_FILE_NAME",
    "SCOPE_BOUNDARY_FILE_NAME",
    "SUMMARY_FILE_NAME",
    "VALIDATION_ERRORS_FILE_NAME",
    "WORKBOOK_FILE_NAME",
    "WORKBOOK_SHEETS_343L",
    "build_review_queue_pure_human_attestation_ingestion_343l",
]
