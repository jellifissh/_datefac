from __future__ import annotations

from pathlib import Path

from datefac.review_queue.pure_human_attestation_package_343k import (
    ALLOWED_HUMAN_ATTESTATION_DECISIONS,
    EDITABLE_HUMAN_ATTESTATION_COLUMNS,
    HUMAN_CORRECT_REQUIRED_COLUMNS,
    NOT_READY_DECISION_343K,
    READY_DECISION_343K,
    RECOMMENDED_343L_SCOPE_343K,
    WORKBOOK_SHEETS_343K,
    build_review_queue_pure_human_attestation_package_343k,
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
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_pure_human_attestation_package_343k"
)

SUMMARY_FILE_NAME = "review_queue_pure_human_attestation_package_343k_summary.json"
MANIFEST_FILE_NAME = "review_queue_pure_human_attestation_package_343k_manifest.json"
QA_FILE_NAME = "review_queue_pure_human_attestation_package_343k_qa.json"
NO_WRITE_BACK_FILE_NAME = (
    "review_queue_pure_human_attestation_package_343k_no_write_back_proof.json"
)
REPORT_FILE_NAME = "review_queue_pure_human_attestation_package_343k_report.md"
WORKBOOK_FILE_NAME = "review_queue_pure_human_attestation_package_343k.xlsx"
ATTESTATION_TEMPLATE_FILE_NAME = (
    "review_queue_pure_human_attestation_package_343k_attestation_template.xlsx"
)
ATTESTATION_ITEMS_FILE_NAME = (
    "review_queue_pure_human_attestation_package_343k_attestation_items.jsonl"
)
REVIEWER_INSTRUCTIONS_FILE_NAME = (
    "review_queue_pure_human_attestation_package_343k_reviewer_instructions.md"
)
FILL_GUIDE_FILE_NAME = "review_queue_pure_human_attestation_package_343k_fill_guide.md"
EXPECTED_IMPORT_CONTRACT_FILE_NAME = (
    "review_queue_pure_human_attestation_package_343k_expected_import_contract.json"
)
CLIENT_EXPORT_BOUNDARY_FILE_NAME = (
    "review_queue_pure_human_attestation_package_343k_client_export_boundary.md"
)


__all__ = [
    "ALLOWED_HUMAN_ATTESTATION_DECISIONS",
    "ATTESTATION_ITEMS_FILE_NAME",
    "ATTESTATION_TEMPLATE_FILE_NAME",
    "CLIENT_EXPORT_BOUNDARY_FILE_NAME",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR",
    "DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR",
    "DEFAULT_STRICT_REVIEW_INGESTION_343J_DIR",
    "EDITABLE_HUMAN_ATTESTATION_COLUMNS",
    "EXPECTED_IMPORT_CONTRACT_FILE_NAME",
    "FILL_GUIDE_FILE_NAME",
    "HUMAN_CORRECT_REQUIRED_COLUMNS",
    "MANIFEST_FILE_NAME",
    "NOT_READY_DECISION_343K",
    "NO_WRITE_BACK_FILE_NAME",
    "QA_FILE_NAME",
    "READY_DECISION_343K",
    "RECOMMENDED_343L_SCOPE_343K",
    "REPORT_FILE_NAME",
    "REVIEWER_INSTRUCTIONS_FILE_NAME",
    "SUMMARY_FILE_NAME",
    "WORKBOOK_FILE_NAME",
    "WORKBOOK_SHEETS_343K",
    "build_review_queue_pure_human_attestation_package_343k",
]
