from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from datefac.review_queue.ingest_strict_review_343j import (
    NOT_READY_DECISION_343J,
    READY_DECISION_343J,
    RECOMMENDED_343K_SCOPE_343J,
    WORKBOOK_SHEETS_343J,
    build_review_queue_strict_review_ingestion_343j,
)


DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR = Path(
    r"D:\_datefac\output\review_queue_source_evidence_enrichment_343i2"
)
DEFAULT_STRICT_HUMAN_REVIEW_PACKAGE_343I_DIR = Path(
    r"D:\_datefac\output\review_queue_strict_human_review_package_343i"
)
DEFAULT_AUDIT_SUMMARY_343H_DIR = Path(r"D:\_datefac\output\review_queue_audit_summary_343h")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_FILLED_WORKBOOK = Path(
    r"D:\_datefac\input\review_queue_strict_human_review_343i2_filled\review_queue_source_evidence_enrichment_343i2_enriched_review_template_filled.xlsx"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_strict_review_ingestion_343j")

SUMMARY_FILE_NAME = "review_queue_strict_review_ingestion_343j_summary.json"
MANIFEST_FILE_NAME = "review_queue_strict_review_ingestion_343j_manifest.json"
QA_FILE_NAME = "review_queue_strict_review_ingestion_343j_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_strict_review_ingestion_343j_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_strict_review_ingestion_343j_report.md"
WORKBOOK_FILE_NAME = "review_queue_strict_review_ingestion_343j.xlsx"
RESULT_FILE_NAME = "review_queue_strict_review_ingestion_343j_result.jsonl"
VALIDATION_ERRORS_FILE_NAME = "review_queue_strict_review_ingestion_343j_validation_errors.json"
DECISION_SUMMARY_FILE_NAME = "review_queue_strict_review_ingestion_343j_decision_summary.json"
CLIENT_EXPORT_GATE_FILE_NAME = "review_queue_strict_review_ingestion_343j_client_export_gate.json"
REVIEWER_SOURCE_DISCLOSURE_FILE_NAME = (
    "review_queue_strict_review_ingestion_343j_reviewer_source_disclosure.md"
)


__all__ = [
    "CLIENT_EXPORT_GATE_FILE_NAME",
    "DECISION_SUMMARY_FILE_NAME",
    "DEFAULT_AUDIT_SUMMARY_343H_DIR",
    "DEFAULT_FILLED_WORKBOOK",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR",
    "DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR",
    "DEFAULT_STRICT_HUMAN_REVIEW_PACKAGE_343I_DIR",
    "MANIFEST_FILE_NAME",
    "NOT_READY_DECISION_343J",
    "NO_WRITE_BACK_FILE_NAME",
    "QA_FILE_NAME",
    "READY_DECISION_343J",
    "RECOMMENDED_343K_SCOPE_343J",
    "REPORT_FILE_NAME",
    "RESULT_FILE_NAME",
    "REVIEWER_SOURCE_DISCLOSURE_FILE_NAME",
    "SUMMARY_FILE_NAME",
    "VALIDATION_ERRORS_FILE_NAME",
    "WORKBOOK_FILE_NAME",
    "WORKBOOK_SHEETS_343J",
    "build_review_queue_strict_review_ingestion_343j",
]
