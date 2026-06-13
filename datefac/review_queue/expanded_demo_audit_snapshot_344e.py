from __future__ import annotations

from pathlib import Path

from datefac.review_queue.expanded_trusted_demo_export_package_344d import (
    EXPANDED_EXPORT_SCOPE_344D,
    EXPORT_USAGE_344D,
)


READY_DECISION_344E = "EXPANDED_TRUSTED_DEMO_AUDIT_SNAPSHOT_344E_READY"
NOT_READY_DECISION_344E = "EXPANDED_TRUSTED_DEMO_AUDIT_SNAPSHOT_344E_NOT_READY"
RECOMMENDED_345A_SCOPE_344E = "formal_export_readiness_gap_assessment"

WORKBOOK_SHEETS_344E = [
    "00_README",
    "01_SNAPSHOT_SUMMARY",
    "02_INPUT_344D_SUMMARY",
    "03_EXPANDED_PACKAGE",
    "04_TRUST_CHAIN",
    "05_LINEAGE_AUDIT",
    "06_ARTIFACT_INDEX",
    "07_FINAL_GATE",
    "08_SCOPE_BOUNDARY",
    "09_NEXT_ACTION_PLAN",
    "10_NO_WRITE_BACK",
]

DEFAULT_EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_DIR = Path(
    r"D:\_datefac\output\review_queue_expanded_trusted_demo_export_package_344d"
)
DEFAULT_SOURCE_CHECK_SIDECAR_SIMULATION_344C_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_sidecar_simulation_344c"
)
DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_evidence_review_ingestion_344b"
)
DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_evidence_enrichment_344a2"
)
DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR = Path(
    r"D:\_datefac\output\review_queue_demo_audit_snapshot_343o"
)
DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR = Path(
    r"D:\_datefac\output\review_queue_limited_demo_export_package_343n"
)
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(
    r"D:\_datefac\output\review_queue_schema_343a"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_expanded_demo_audit_snapshot_344e"
)

SUMMARY_FILE_NAME = "review_queue_expanded_demo_audit_snapshot_344e_summary.json"
MANIFEST_FILE_NAME = "review_queue_expanded_demo_audit_snapshot_344e_manifest.json"
QA_FILE_NAME = "review_queue_expanded_demo_audit_snapshot_344e_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_expanded_demo_audit_snapshot_344e_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_expanded_demo_audit_snapshot_344e_report.md"
WORKBOOK_FILE_NAME = "review_queue_expanded_demo_audit_snapshot_344e.xlsx"
FINAL_HANDOFF_SUMMARY_FILE_NAME = (
    "review_queue_expanded_demo_audit_snapshot_344e_final_handoff_summary.md"
)
EXECUTIVE_SUMMARY_FILE_NAME = (
    "review_queue_expanded_demo_audit_snapshot_344e_executive_summary.md"
)
TRUST_CHAIN_REPORT_FILE_NAME = (
    "review_queue_expanded_demo_audit_snapshot_344e_trust_chain_report.md"
)
ARTIFACT_INDEX_JSON_FILE_NAME = (
    "review_queue_expanded_demo_audit_snapshot_344e_artifact_index.json"
)
ARTIFACT_INDEX_MD_FILE_NAME = (
    "review_queue_expanded_demo_audit_snapshot_344e_artifact_index.md"
)
FINAL_EXPORT_GATE_SNAPSHOT_FILE_NAME = (
    "review_queue_expanded_demo_audit_snapshot_344e_final_export_gate_snapshot.json"
)
LINEAGE_AUDIT_SUMMARY_FILE_NAME = (
    "review_queue_expanded_demo_audit_snapshot_344e_lineage_audit_summary.json"
)
METRIC_DISTRIBUTION_FILE_NAME = (
    "review_queue_expanded_demo_audit_snapshot_344e_metric_distribution.json"
)
SCOPE_BOUNDARY_FILE_NAME = "review_queue_expanded_demo_audit_snapshot_344e_scope_boundary.md"
NEXT_ACTION_PLAN_FILE_NAME = "review_queue_expanded_demo_audit_snapshot_344e_next_action_plan.json"


__all__ = [
    "ARTIFACT_INDEX_JSON_FILE_NAME",
    "ARTIFACT_INDEX_MD_FILE_NAME",
    "DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR",
    "DEFAULT_EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_DIR",
    "DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR",
    "DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR",
    "DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR",
    "DEFAULT_SOURCE_CHECK_SIDECAR_SIMULATION_344C_DIR",
    "EXECUTIVE_SUMMARY_FILE_NAME",
    "EXPANDED_EXPORT_SCOPE_344D",
    "EXPORT_USAGE_344D",
    "FINAL_EXPORT_GATE_SNAPSHOT_FILE_NAME",
    "FINAL_HANDOFF_SUMMARY_FILE_NAME",
    "LINEAGE_AUDIT_SUMMARY_FILE_NAME",
    "MANIFEST_FILE_NAME",
    "METRIC_DISTRIBUTION_FILE_NAME",
    "NEXT_ACTION_PLAN_FILE_NAME",
    "NOT_READY_DECISION_344E",
    "NO_WRITE_BACK_FILE_NAME",
    "QA_FILE_NAME",
    "READY_DECISION_344E",
    "RECOMMENDED_345A_SCOPE_344E",
    "REPORT_FILE_NAME",
    "SCOPE_BOUNDARY_FILE_NAME",
    "SUMMARY_FILE_NAME",
    "TRUST_CHAIN_REPORT_FILE_NAME",
    "WORKBOOK_FILE_NAME",
    "WORKBOOK_SHEETS_344E",
]
