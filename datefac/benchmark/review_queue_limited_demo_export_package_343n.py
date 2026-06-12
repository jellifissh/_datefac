from __future__ import annotations

from pathlib import Path

from datefac.review_queue.limited_demo_export_package_343n import (
    NOT_READY_DECISION_343N,
    READY_DECISION_343N,
    RECOMMENDED_343O_SCOPE_343N,
    WORKBOOK_SHEETS_343N,
    build_review_queue_limited_demo_export_package_343n,
)


DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR = Path(
    r"D:\_datefac\output\review_queue_human_confirmed_sidecar_simulation_343m"
)
DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR = Path(
    r"D:\_datefac\output\review_queue_pure_human_attestation_ingestion_343l"
)
DEFAULT_AUDIT_SUMMARY_343H_DIR = Path(
    r"D:\_datefac\output\review_queue_audit_summary_343h"
)
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(
    r"D:\_datefac\output\review_queue_schema_343a"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_limited_demo_export_package_343n"
)

SUMMARY_FILE_NAME = "review_queue_limited_demo_export_package_343n_summary.json"
MANIFEST_FILE_NAME = "review_queue_limited_demo_export_package_343n_manifest.json"
QA_FILE_NAME = "review_queue_limited_demo_export_package_343n_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_limited_demo_export_package_343n_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_limited_demo_export_package_343n_report.md"
WORKBOOK_FILE_NAME = "review_queue_limited_demo_export_package_343n.xlsx"
DEMO_README_FILE_NAME = "review_queue_limited_demo_export_package_343n_demo_readme.md"
EXPORT_ROWS_JSONL_FILE_NAME = "review_queue_limited_demo_export_package_343n_export_rows.jsonl"
EXPORT_ROWS_CSV_FILE_NAME = "review_queue_limited_demo_export_package_343n_export_rows.csv"
AUDIT_LABELS_FILE_NAME = "review_queue_limited_demo_export_package_343n_audit_labels.jsonl"
EXPORT_GATE_FILE_NAME = "review_queue_limited_demo_export_package_343n_export_gate.json"
SCOPE_BOUNDARY_FILE_NAME = "review_queue_limited_demo_export_package_343n_scope_boundary.md"
REMAINING_BACKLOG_FILE_NAME = "review_queue_limited_demo_export_package_343n_remaining_backlog.jsonl"
HANDOFF_SUMMARY_FILE_NAME = "review_queue_limited_demo_export_package_343n_handoff_summary.md"


__all__ = [
    "AUDIT_LABELS_FILE_NAME",
    "DEFAULT_AUDIT_SUMMARY_343H_DIR",
    "DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR",
    "DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR",
    "DEMO_README_FILE_NAME",
    "EXPORT_GATE_FILE_NAME",
    "EXPORT_ROWS_CSV_FILE_NAME",
    "EXPORT_ROWS_JSONL_FILE_NAME",
    "HANDOFF_SUMMARY_FILE_NAME",
    "MANIFEST_FILE_NAME",
    "NOT_READY_DECISION_343N",
    "NO_WRITE_BACK_FILE_NAME",
    "QA_FILE_NAME",
    "READY_DECISION_343N",
    "RECOMMENDED_343O_SCOPE_343N",
    "REMAINING_BACKLOG_FILE_NAME",
    "REPORT_FILE_NAME",
    "SCOPE_BOUNDARY_FILE_NAME",
    "SUMMARY_FILE_NAME",
    "WORKBOOK_FILE_NAME",
    "WORKBOOK_SHEETS_343N",
    "build_review_queue_limited_demo_export_package_343n",
]
