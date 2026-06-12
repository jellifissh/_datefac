from __future__ import annotations

from pathlib import Path

from datefac.review_queue.source_check_backlog_package_344a import (
    NOT_READY_DECISION_344A,
    TEMPLATE_WORKBOOK_SHEETS_344A,
    WAITING_DECISION_344A,
    WORKBOOK_SHEETS_344A,
    build_review_queue_source_check_backlog_package_344a,
)


DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR = Path(
    r"D:\_datefac\output\review_queue_demo_audit_snapshot_343o"
)
DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR = Path(
    r"D:\_datefac\output\review_queue_limited_demo_export_package_343n"
)
DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR = Path(
    r"D:\_datefac\output\review_queue_human_confirmed_sidecar_simulation_343m"
)
DEFAULT_AUDIT_SUMMARY_343H_DIR = Path(
    r"D:\_datefac\output\review_queue_audit_summary_343h"
)
DEFAULT_SPOT_CHECK_INGESTION_343G_DIR = Path(
    r"D:\_datefac\output\review_queue_spot_check_ingestion_343g"
)
DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR = Path(
    r"D:\_datefac\output\review_queue_spot_check_package_343f"
)
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(
    r"D:\_datefac\output\review_queue_schema_343a"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_backlog_package_344a"
)

SUMMARY_FILE_NAME = "review_queue_source_check_backlog_package_344a_summary.json"
MANIFEST_FILE_NAME = "review_queue_source_check_backlog_package_344a_manifest.json"
QA_FILE_NAME = "review_queue_source_check_backlog_package_344a_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_source_check_backlog_package_344a_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_source_check_backlog_package_344a_report.md"
WORKBOOK_FILE_NAME = "review_queue_source_check_backlog_package_344a.xlsx"
REVIEW_TEMPLATE_FILE_NAME = "review_queue_source_check_backlog_package_344a_review_template.xlsx"
BACKLOG_ITEMS_FILE_NAME = "review_queue_source_check_backlog_package_344a_backlog_items.jsonl"
EVIDENCE_MAP_FILE_NAME = "review_queue_source_check_backlog_package_344a_evidence_map.json"
REVIEWER_INSTRUCTIONS_FILE_NAME = "review_queue_source_check_backlog_package_344a_reviewer_instructions.md"
FILL_GUIDE_FILE_NAME = "review_queue_source_check_backlog_package_344a_fill_guide.md"
EXPECTED_IMPORT_CONTRACT_FILE_NAME = "review_queue_source_check_backlog_package_344a_expected_import_contract.json"
SCOPE_BOUNDARY_FILE_NAME = "review_queue_source_check_backlog_package_344a_scope_boundary.md"
PRIORITY_PLAN_FILE_NAME = "review_queue_source_check_backlog_package_344a_priority_plan.json"


__all__ = [
    "BACKLOG_ITEMS_FILE_NAME",
    "DEFAULT_AUDIT_SUMMARY_343H_DIR",
    "DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR",
    "DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR",
    "DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR",
    "DEFAULT_SPOT_CHECK_INGESTION_343G_DIR",
    "DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR",
    "EVIDENCE_MAP_FILE_NAME",
    "EXPECTED_IMPORT_CONTRACT_FILE_NAME",
    "FILL_GUIDE_FILE_NAME",
    "MANIFEST_FILE_NAME",
    "NOT_READY_DECISION_344A",
    "NO_WRITE_BACK_FILE_NAME",
    "PRIORITY_PLAN_FILE_NAME",
    "QA_FILE_NAME",
    "REPORT_FILE_NAME",
    "REVIEWER_INSTRUCTIONS_FILE_NAME",
    "REVIEW_TEMPLATE_FILE_NAME",
    "SCOPE_BOUNDARY_FILE_NAME",
    "SUMMARY_FILE_NAME",
    "TEMPLATE_WORKBOOK_SHEETS_344A",
    "WAITING_DECISION_344A",
    "WORKBOOK_FILE_NAME",
    "WORKBOOK_SHEETS_344A",
    "build_review_queue_source_check_backlog_package_344a",
]
