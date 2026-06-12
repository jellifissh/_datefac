from __future__ import annotations

from pathlib import Path

from datefac.review_queue.human_confirmed_sidecar_simulation_343m import (
    NOT_READY_DECISION_343M,
    READY_DECISION_343M,
    REMEDIATION_REQUIRED_DECISION_343M,
    RECOMMENDED_343N_SCOPE_343M,
    WORKBOOK_SHEETS_343M,
    build_review_queue_human_confirmed_sidecar_simulation_343m,
)


DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR = Path(
    r"D:\_datefac\output\review_queue_pure_human_attestation_ingestion_343l"
)
DEFAULT_PURE_HUMAN_ATTESTATION_PACKAGE_343K_DIR = Path(
    r"D:\_datefac\output\review_queue_pure_human_attestation_package_343k"
)
DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR = Path(
    r"D:\_datefac\output\review_queue_source_evidence_enrichment_343i2"
)
DEFAULT_AUDIT_SUMMARY_343H_DIR = Path(
    r"D:\_datefac\output\review_queue_audit_summary_343h"
)
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(
    r"D:\_datefac\output\review_queue_schema_343a"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_human_confirmed_sidecar_simulation_343m"
)

SUMMARY_FILE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_summary.json"
MANIFEST_FILE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_manifest.json"
QA_FILE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_qa.json"
NO_WRITE_BACK_FILE_NAME = (
    "review_queue_human_confirmed_sidecar_simulation_343m_no_write_back_proof.json"
)
REPORT_FILE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_report.md"
WORKBOOK_FILE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m.xlsx"
SIDECAR_FILE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_sidecar.jsonl"
APPLY_PLAN_FILE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_apply_plan.jsonl"
LIMITED_EXPORT_GATE_FILE_NAME = (
    "review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate.json"
)
LIMITED_EXPORT_CANDIDATE_FILE_NAME = (
    "review_queue_human_confirmed_sidecar_simulation_343m_limited_export_candidate.jsonl"
)
REMAINING_BACKLOG_FILE_NAME = (
    "review_queue_human_confirmed_sidecar_simulation_343m_remaining_backlog.jsonl"
)
SCOPE_BOUNDARY_FILE_NAME = (
    "review_queue_human_confirmed_sidecar_simulation_343m_scope_boundary.md"
)


__all__ = [
    "APPLY_PLAN_FILE_NAME",
    "DEFAULT_AUDIT_SUMMARY_343H_DIR",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR",
    "DEFAULT_PURE_HUMAN_ATTESTATION_PACKAGE_343K_DIR",
    "DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR",
    "DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR",
    "LIMITED_EXPORT_CANDIDATE_FILE_NAME",
    "LIMITED_EXPORT_GATE_FILE_NAME",
    "MANIFEST_FILE_NAME",
    "NOT_READY_DECISION_343M",
    "NO_WRITE_BACK_FILE_NAME",
    "QA_FILE_NAME",
    "READY_DECISION_343M",
    "REMAINING_BACKLOG_FILE_NAME",
    "RECOMMENDED_343N_SCOPE_343M",
    "REMEDIATION_REQUIRED_DECISION_343M",
    "REPORT_FILE_NAME",
    "SIDECAR_FILE_NAME",
    "SCOPE_BOUNDARY_FILE_NAME",
    "SUMMARY_FILE_NAME",
    "WORKBOOK_FILE_NAME",
    "WORKBOOK_SHEETS_343M",
    "build_review_queue_human_confirmed_sidecar_simulation_343m",
]
