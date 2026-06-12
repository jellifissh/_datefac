from __future__ import annotations

from pathlib import Path

from datefac.review_queue.demo_audit_snapshot_343o import (
    NOT_READY_DECISION_343O,
    READY_DECISION_343O,
    RECOMMENDED_344A_SCOPE_343O,
    WORKBOOK_SHEETS_343O,
    build_review_queue_demo_audit_snapshot_343o,
)


DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR = Path(
    r"D:\_datefac\output\review_queue_limited_demo_export_package_343n"
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
    r"D:\_datefac\output\review_queue_demo_audit_snapshot_343o"
)

SUMMARY_FILE_NAME = "review_queue_demo_audit_snapshot_343o_summary.json"
MANIFEST_FILE_NAME = "review_queue_demo_audit_snapshot_343o_manifest.json"
QA_FILE_NAME = "review_queue_demo_audit_snapshot_343o_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_demo_audit_snapshot_343o_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_demo_audit_snapshot_343o_report.md"
WORKBOOK_FILE_NAME = "review_queue_demo_audit_snapshot_343o.xlsx"
HANDOFF_SUMMARY_FILE_NAME = "review_queue_demo_audit_snapshot_343o_handoff_summary.md"
EXECUTIVE_SUMMARY_FILE_NAME = "review_queue_demo_audit_snapshot_343o_executive_summary.md"
TRUST_CHAIN_FILE_NAME = "review_queue_demo_audit_snapshot_343o_trust_chain.md"
SCOPE_BOUNDARY_FILE_NAME = "review_queue_demo_audit_snapshot_343o_scope_boundary.md"
EXPORT_GATE_SNAPSHOT_FILE_NAME = "review_queue_demo_audit_snapshot_343o_export_gate_snapshot.json"
ARTIFACT_INDEX_JSON_FILE_NAME = "review_queue_demo_audit_snapshot_343o_artifact_index.json"
ARTIFACT_INDEX_MD_FILE_NAME = "review_queue_demo_audit_snapshot_343o_artifact_index.md"
BACKLOG_SUMMARY_FILE_NAME = "review_queue_demo_audit_snapshot_343o_backlog_summary.json"
NEXT_ACTION_PLAN_FILE_NAME = "review_queue_demo_audit_snapshot_343o_next_action_plan.json"


__all__ = [
    "ARTIFACT_INDEX_JSON_FILE_NAME",
    "ARTIFACT_INDEX_MD_FILE_NAME",
    "BACKLOG_SUMMARY_FILE_NAME",
    "DEFAULT_AUDIT_SUMMARY_343H_DIR",
    "DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR",
    "DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR",
    "DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR",
    "EXECUTIVE_SUMMARY_FILE_NAME",
    "EXPORT_GATE_SNAPSHOT_FILE_NAME",
    "HANDOFF_SUMMARY_FILE_NAME",
    "MANIFEST_FILE_NAME",
    "NEXT_ACTION_PLAN_FILE_NAME",
    "NOT_READY_DECISION_343O",
    "NO_WRITE_BACK_FILE_NAME",
    "QA_FILE_NAME",
    "READY_DECISION_343O",
    "RECOMMENDED_344A_SCOPE_343O",
    "REPORT_FILE_NAME",
    "SCOPE_BOUNDARY_FILE_NAME",
    "SUMMARY_FILE_NAME",
    "TRUST_CHAIN_FILE_NAME",
    "WORKBOOK_FILE_NAME",
    "WORKBOOK_SHEETS_343O",
    "build_review_queue_demo_audit_snapshot_343o",
]
