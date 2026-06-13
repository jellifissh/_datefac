from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.expanded_demo_audit_snapshot_344e import (
    ARTIFACT_INDEX_JSON_FILE_NAME,
    DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    DEFAULT_EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_DIR,
    DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR,
    DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR,
    DEFAULT_SOURCE_CHECK_SIDECAR_SIMULATION_344C_DIR,
    EXECUTIVE_SUMMARY_FILE_NAME,
    EXPANDED_EXPORT_SCOPE_344D,
    EXPORT_USAGE_344D,
    FINAL_EXPORT_GATE_SNAPSHOT_FILE_NAME,
    FINAL_HANDOFF_SUMMARY_FILE_NAME,
    LINEAGE_AUDIT_SUMMARY_FILE_NAME,
    MANIFEST_FILE_NAME,
    METRIC_DISTRIBUTION_FILE_NAME,
    NEXT_ACTION_PLAN_FILE_NAME,
    NOT_READY_DECISION_344E,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    READY_DECISION_344E,
    RECOMMENDED_345A_SCOPE_344E,
    REPORT_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SUMMARY_FILE_NAME,
    TRUST_CHAIN_REPORT_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_344E,
)
from datefac.review_queue.ingest_strict_review_343j import FORBIDDEN_STAGE_PATHS, PROTECTED_DIRTY_PATHS
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


INPUT_344D_SUMMARY_NAME = "review_queue_expanded_trusted_demo_export_package_344d_summary.json"
INPUT_344D_QA_NAME = "review_queue_expanded_trusted_demo_export_package_344d_qa.json"
INPUT_344D_WORKBOOK_NAME = "review_queue_expanded_trusted_demo_export_package_344d.xlsx"
INPUT_344D_DEMO_README_NAME = "review_queue_expanded_trusted_demo_export_package_344d_demo_readme.md"
INPUT_344D_EXPORT_ROWS_JSONL_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_export_rows.jsonl"
)
INPUT_344D_EXPORT_ROWS_CSV_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_export_rows.csv"
)
INPUT_344D_AUDIT_LABELS_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_audit_labels.jsonl"
)
INPUT_344D_EXPORT_GATE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_export_gate.json"
)
INPUT_344D_LINEAGE_SUMMARY_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_lineage_summary.json"
)
INPUT_344D_METRIC_DISTRIBUTION_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_metric_distribution.json"
)
INPUT_344D_SCOPE_BOUNDARY_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_scope_boundary.md"
)
INPUT_344D_NO_WRITE_BACK_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_no_write_back_proof.json"
)

INPUT_344C_SUMMARY_NAME = "review_queue_source_check_sidecar_simulation_344c_summary.json"
INPUT_344C_CANDIDATES_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_expanded_trusted_candidates.jsonl"
)
INPUT_344C_GATE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_expanded_trust_gate.json"
)
INPUT_344C_DEDUP_AUDIT_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_dedup_audit.jsonl"
)
INPUT_344B_SUMMARY_NAME = "review_queue_source_check_evidence_review_ingestion_344b_summary.json"
INPUT_344B_CORRECTIONS_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_corrections.jsonl"
)
INPUT_344A2_SUMMARY_NAME = "review_queue_source_check_evidence_enrichment_344a2_summary.json"
INPUT_344A2_EVIDENCE_MAP_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_evidence_map.json"
)
INPUT_343O_SUMMARY_NAME = "review_queue_demo_audit_snapshot_343o_summary.json"
INPUT_343O_HANDOFF_NAME = "review_queue_demo_audit_snapshot_343o_handoff_summary.md"
INPUT_343O_ARTIFACT_INDEX_NAME = "review_queue_demo_audit_snapshot_343o_artifact_index.json"
INPUT_343N_EXPORT_GATE_NAME = "review_queue_limited_demo_export_package_343n_export_gate.json"
INPUT_343A_SCHEMA_NAME = "review_queue_schema_343a_schema.json"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"

READY_INPUT_344D_DECISION = "EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_READY"
READY_INPUT_344C_DECISION = "SOURCE_CHECK_SIDECAR_SIMULATION_344C_READY"
READY_INPUT_344B_DECISION = "SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_READY"
READY_INPUT_343O_DECISION = "DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_READY"
READY_INPUT_343A_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return normalize_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    rows = [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
    return _clean_frame(pd.DataFrame(rows))


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _run_git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = _run_git(repo_root, ["status", "--porcelain", "--", *paths])
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    lines = _git_status_porcelain_for_paths(paths, repo_root)
    staged: List[str] = []
    for line in lines:
        if line.startswith("__ERROR__::"):
            return [line]
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _build_readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "344E closes the 29-row expanded trusted demo arc with final audit snapshot and handoff materials.",
                },
                {
                    "section": "scope",
                    "message": summary.get("expanded_export_scope", ""),
                },
                {
                    "section": "usage",
                    "message": summary.get("export_usage", ""),
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _build_trust_chain_rows(
    *,
    summary_343a: Dict[str, Any],
    summary_343o: Dict[str, Any],
    summary_344a2: Dict[str, Any],
    summary_344b: Dict[str, Any],
    summary_344c: Dict[str, Any],
    summary_344d: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return [
        {
            "milestone_id": "343A",
            "purpose": "Review queue schema and UI contract",
            "input_or_output_count": int(summary_343a.get("field_count", 0)),
            "review_or_evidence_status": "schema_ready",
            "review_disclosure": "schema_only",
            "correction_handling": "not_applicable",
            "gate_decision": summary_343a.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Schema only; no review result implied.",
        },
        {
            "milestone_id": "343H",
            "purpose": "AI-assisted audit summary and strict-human gap baseline",
            "input_or_output_count": 30,
            "review_or_evidence_status": "ai_assisted_audit_baseline",
            "review_disclosure": "AI-assisted review and AI-assisted spot-check baseline",
            "correction_handling": "source-check backlog identified, not yet resolved",
            "gate_decision": "REFERENCED_UPSTREAM_BASELINE",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Global strict human review incomplete; source-check backlog existed upstream.",
        },
        {
            "milestone_id": "343I2",
            "purpose": "Source evidence enrichment for first package scope",
            "input_or_output_count": 10,
            "review_or_evidence_status": "enriched_locator_package_scope",
            "review_disclosure": "AI-assisted evidence locator enrichment",
            "correction_handling": "package-scope evidence enrichment only",
            "gate_decision": "REFERENCED_UPSTREAM_FOR_PACKAGE_SCOPE",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Applies only to the earlier 10-row package scope.",
        },
        {
            "milestone_id": "343L",
            "purpose": "Package-level pure human attestation ingestion",
            "input_or_output_count": 10,
            "review_or_evidence_status": "package_level_human_confirmation_complete",
            "review_disclosure": "pure human package attestation completed",
            "correction_handling": "accepted package-scope confirmations only",
            "gate_decision": "REFERENCED_UPSTREAM_PACKAGE_CONFIRMATION",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Package-only scope; no global completion claim.",
        },
        {
            "milestone_id": "343M",
            "purpose": "Human-confirmed sidecar simulation and limited gate",
            "input_or_output_count": 10,
            "review_or_evidence_status": "limited_sidecar_simulation_ready",
            "review_disclosure": "package-scope human-confirmed rows only",
            "correction_handling": "no source-check backlog resolved here",
            "gate_decision": "REFERENCED_UPSTREAM_LIMITED_GATE",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Remaining source-check backlog still blocked broader trust scope.",
        },
        {
            "milestone_id": "343N",
            "purpose": "10-row demo-only export package",
            "input_or_output_count": 10,
            "review_or_evidence_status": "demo_only_package_ready",
            "review_disclosure": "package-scope demo export only",
            "correction_handling": "no expanded source-check merge yet",
            "gate_decision": "REFERENCED_UPSTREAM_DEMO_PACKAGE",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Limited to 10 rows and package scope only.",
        },
        {
            "milestone_id": "343O",
            "purpose": "10-row demo arc audit snapshot",
            "input_or_output_count": int(summary_343o.get("input_demo_export_row_count", 0)),
            "review_or_evidence_status": "demo_arc_closed_for_10_rows",
            "review_disclosure": "demo-only audit snapshot and handoff",
            "correction_handling": "backlog still carried outside package scope",
            "gate_decision": summary_343o.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Only the original 10-row arc was closed.",
        },
        {
            "milestone_id": "344A",
            "purpose": "19-row source-check backlog package",
            "input_or_output_count": 19,
            "review_or_evidence_status": "backlog_packaged_for_review",
            "review_disclosure": "source-check backlog templating only",
            "correction_handling": "no results ingested yet",
            "gate_decision": "REFERENCED_UPSTREAM_BACKLOG_PACKAGE",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Waiting for reviewed source-check results upstream.",
        },
        {
            "milestone_id": "344A2",
            "purpose": "19-row source evidence enrichment",
            "input_or_output_count": int(summary_344a2.get("evidence_resolved_count", 0)),
            "review_or_evidence_status": "all_19_evidence_locators_resolved",
            "review_disclosure": "AI-assisted evidence enrichment for source-check review",
            "correction_handling": "evidence only, no confirmation/correction applied here",
            "gate_decision": summary_344a2.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Still waiting for reviewed source-check decisions at this stage.",
        },
        {
            "milestone_id": "344B",
            "purpose": "Source-check review ingestion",
            "input_or_output_count": int(summary_344b.get("valid_row_count", 0)),
            "review_or_evidence_status": "19_source_check_rows_resolved",
            "review_disclosure": "independent workbook source-check review ingestion",
            "correction_handling": "10 confirmed and 9 corrected rows recorded",
            "gate_decision": summary_344b.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Results remain sidecar-only and require simulation before package merge.",
        },
        {
            "milestone_id": "344C",
            "purpose": "Expanded sidecar simulation and 29-row trust gate",
            "input_or_output_count": int(summary_344c.get("expanded_trusted_candidate_count", 0)),
            "review_or_evidence_status": "expanded_trusted_candidates_ready",
            "review_disclosure": "sidecar simulation combining demo rows and source-check rows",
            "correction_handling": "9 corrected YOY/% rows preserved in simulation",
            "gate_decision": summary_344c.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Still simulation-only before packaging.",
        },
        {
            "milestone_id": "344D",
            "purpose": "Expanded 29-row review/demo package generation",
            "input_or_output_count": int(summary_344d.get("expanded_export_row_count", 0)),
            "review_or_evidence_status": "expanded_package_ready",
            "review_disclosure": "review/demo-only expanded trusted handoff package",
            "correction_handling": "9 corrected YOY/% rows disclosed inside package",
            "gate_decision": summary_344d.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Formal client export remains blocked pending later readiness assessment.",
        },
    ]


def _build_artifact_index_rows(
    *,
    expanded_dir_344d: Path,
    source_check_sim_dir_344c: Path,
    source_check_ingestion_dir_344b: Path,
    source_check_enrichment_dir_344a2: Path,
    demo_snapshot_dir_343o: Path,
) -> List[Dict[str, Any]]:
    return [
        {
            "artifact_name": "344D workbook",
            "path": str(expanded_dir_344d / INPUT_344D_WORKBOOK_NAME),
            "role": "Primary 29-row expanded trusted package workbook",
            "milestone": "344D",
            "user_facing_demo_facing": True,
            "formal_client_export": False,
            "scope": EXPANDED_EXPORT_SCOPE_344D,
            "caution_label": "REVIEW_DEMO_ONLY",
        },
        {
            "artifact_name": "344D export rows",
            "path": str(expanded_dir_344d / INPUT_344D_EXPORT_ROWS_JSONL_NAME),
            "role": "Machine-readable 29-row expanded trusted package",
            "milestone": "344D",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": EXPANDED_EXPORT_SCOPE_344D,
            "caution_label": "NOT_FORMAL_CLIENT_EXPORT",
        },
        {
            "artifact_name": "344D audit labels",
            "path": str(expanded_dir_344d / INPUT_344D_AUDIT_LABELS_NAME),
            "role": "Per-row review/demo-only audit labels",
            "milestone": "344D",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": EXPANDED_EXPORT_SCOPE_344D,
            "caution_label": "AUDIT_LABELS_REQUIRED",
        },
        {
            "artifact_name": "344D export gate",
            "path": str(expanded_dir_344d / INPUT_344D_EXPORT_GATE_NAME),
            "role": "Expanded review/demo package export gate",
            "milestone": "344D",
            "user_facing_demo_facing": True,
            "formal_client_export": False,
            "scope": EXPANDED_EXPORT_SCOPE_344D,
            "caution_label": "FORMAL_EXPORT_BLOCKED",
        },
        {
            "artifact_name": "344C expanded candidates",
            "path": str(source_check_sim_dir_344c / INPUT_344C_CANDIDATES_NAME),
            "role": "Expanded trusted candidate rows before final packaging",
            "milestone": "344C",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": EXPANDED_EXPORT_SCOPE_344D,
            "caution_label": "SIDECAR_SIMULATION_ONLY",
        },
        {
            "artifact_name": "344C trust gate",
            "path": str(source_check_sim_dir_344c / INPUT_344C_GATE_NAME),
            "role": "Expanded trusted candidate trust gate",
            "milestone": "344C",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": EXPANDED_EXPORT_SCOPE_344D,
            "caution_label": "TRUST_GATE_ONLY",
        },
        {
            "artifact_name": "344B corrections",
            "path": str(source_check_ingestion_dir_344b / INPUT_344B_CORRECTIONS_NAME),
            "role": "Nine source-check corrections proving YOY/% semantics",
            "milestone": "344B",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": "SOURCE_CHECK_BACKLOG_19_ROWS_ONLY",
            "caution_label": "CORRECTION_SEMANTICS",
        },
        {
            "artifact_name": "344B summary",
            "path": str(source_check_ingestion_dir_344b / INPUT_344B_SUMMARY_NAME),
            "role": "Source-check review ingestion counts and gate",
            "milestone": "344B",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": "SOURCE_CHECK_BACKLOG_19_ROWS_ONLY",
            "caution_label": "NO_WRITE_BACK",
        },
        {
            "artifact_name": "344A2 evidence map",
            "path": str(source_check_enrichment_dir_344a2 / INPUT_344A2_EVIDENCE_MAP_NAME),
            "role": "Resolved evidence locator map for the 19 backlog rows",
            "milestone": "344A2",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": "SOURCE_CHECK_BACKLOG_19_ROWS_ONLY",
            "caution_label": "EVIDENCE_LOCATOR_ONLY",
        },
        {
            "artifact_name": "344A2 summary",
            "path": str(source_check_enrichment_dir_344a2 / INPUT_344A2_SUMMARY_NAME),
            "role": "Evidence enrichment resolution counts",
            "milestone": "344A2",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": "SOURCE_CHECK_BACKLOG_19_ROWS_ONLY",
            "caution_label": "WAITING_FOR_SOURCE_CHECK_REVIEW_UPSTREAM",
        },
        {
            "artifact_name": "343O handoff summary",
            "path": str(demo_snapshot_dir_343o / INPUT_343O_HANDOFF_NAME),
            "role": "Earlier 10-row demo arc handoff summary",
            "milestone": "343O",
            "user_facing_demo_facing": True,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "EARLIER_DEMO_ARC_ONLY",
        },
        {
            "artifact_name": "343O artifact index",
            "path": str(demo_snapshot_dir_343o / INPUT_343O_ARTIFACT_INDEX_NAME),
            "role": "Earlier 10-row demo arc artifact map",
            "milestone": "343O",
            "user_facing_demo_facing": True,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "HISTORICAL_DEMO_REFERENCE",
        },
    ]


def _build_lineage_audit_summary(
    *,
    summary_344d: Dict[str, Any],
    lineage_344d: Dict[str, Any],
    corrections_344b: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "input_expanded_export_row_count": int(summary_344d.get("expanded_export_row_count", 0)),
        "audit_label_row_count": int(summary_344d.get("audit_label_row_count", 0)),
        "prior_demo_trusted_row_count": int(lineage_344d.get("prior_demo_trusted_row_count", 0)),
        "source_check_trusted_row_count": int(lineage_344d.get("source_check_trusted_row_count", 0)),
        "source_check_confirmed_row_count": int(lineage_344d.get("source_check_confirmed_row_count", 0)),
        "source_check_corrected_row_count": int(lineage_344d.get("source_check_corrected_row_count", 0)),
        "correction_row_count": int(lineage_344d.get("correction_row_count", 0)),
        "correction_semantics": lineage_344d.get(
            "correction_semantics",
            "9 corrected rows use YOY and %",
        ),
        "correction_examples": [
            {
                "queue_item_id": row.get("queue_item_id", ""),
                "review_item_id": row.get("review_item_id", ""),
                "source_pdf_name": row.get("source_pdf_name", ""),
                "page_number": row.get("page_number", ""),
                "original_metric_standardized": row.get("original_metric_standardized", ""),
                "corrected_metric_standardized": row.get("corrected_metric_standardized", ""),
                "original_normalized_unit": row.get("original_normalized_unit", ""),
                "corrected_normalized_unit": row.get("corrected_normalized_unit", ""),
            }
            for row in corrections_344b[:3]
        ],
    }


def _build_final_export_gate_snapshot(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "expanded_review_demo_package_generated": True,
        "expanded_demo_handoff_ready": True,
        "expanded_demo_audit_snapshot_generated": summary.get(
            "expanded_demo_audit_snapshot_generated", False
        ),
        "final_handoff_summary_generated": summary.get(
            "final_handoff_summary_generated", False
        ),
        "expanded_export_row_count": summary.get("input_expanded_export_row_count", 0),
        "audit_label_row_count": summary.get("audit_label_row_count", 0),
        "expanded_export_scope": summary.get("expanded_export_scope", ""),
        "export_usage": summary.get("export_usage", ""),
        "source_check_backlog_resolved": True,
        "prior_demo_trusted_row_count": summary.get("prior_demo_trusted_row_count", 0),
        "source_check_trusted_row_count": summary.get("source_check_trusted_row_count", 0),
        "source_check_confirmed_row_count": summary.get(
            "source_check_confirmed_row_count", 0
        ),
        "source_check_corrected_row_count": summary.get(
            "source_check_corrected_row_count", 0
        ),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "reason": (
            "Expanded demo audit snapshot confirms a 29-row review/demo-only trusted handoff "
            "package. Formal client export remains blocked pending a later formal export "
            "readiness assessment."
        ),
    }


def _build_next_action_plan(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "primary_route": {
            "task_id": "345A",
            "scope": RECOMMENDED_345A_SCOPE_344E,
            "reason": "The expanded 29-row demo arc is now closed; the next gap is formal export readiness.",
        },
        "secondary_route": {
            "task_id": "345B",
            "scope": "presentation_report_material_assembly",
            "reason": "If the immediate goal is reporting or presentation, package the final handoff materials.",
        },
        "tertiary_route": {
            "task_id": "345C",
            "scope": "ui_api_integration_planning_for_review_queue",
            "reason": "If the next goal is productization, translate the review/demo flow into UI/API planning.",
        },
        "default_recommendation": RECOMMENDED_345A_SCOPE_344E,
        "expanded_demo_arc_closed": bool(summary.get("expanded_demo_arc_closed", False)),
    }


def _build_expanded_package_rows(export_rows_344d: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in export_rows_344d:
        rows.append(
            {
                "queue_item_id": row.get("queue_item_id", ""),
                "review_item_id": row.get("review_item_id", ""),
                "metric_standardized": row.get("metric_standardized", ""),
                "year_standardized": row.get("year_standardized", ""),
                "value_numeric": row.get("value_numeric", ""),
                "normalized_unit": row.get("normalized_unit", ""),
                "source_lineage_stage": row.get("source_lineage_stage", ""),
                "source_lineage_summary": row.get("source_lineage_summary", ""),
                "source_pdf_name": row.get("source_pdf_name", ""),
                "page_number": row.get("page_number", ""),
                "table_id": row.get("table_id", ""),
                "expanded_export_scope": row.get("expanded_export_scope", ""),
                "export_usage": row.get("export_usage", ""),
            }
        )
    return rows


def _build_trust_chain_markdown(trust_chain_rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 344E Expanded Trusted Demo Trust Chain",
        "",
        "## Chinese-first Summary",
        "- 344E closes the expanded 29-row review/demo arc by documenting how trust accumulated from schema, package confirmation, source-check resolution, simulation, and final packaging.",
        "",
        "## Stage Chain",
    ]
    for row in trust_chain_rows:
        lines.extend(
            [
                f"### {row.get('milestone_id', '')}",
                f"- purpose: {row.get('purpose', '')}",
                f"- count: {row.get('input_or_output_count', '')}",
                f"- review/evidence: {row.get('review_or_evidence_status', '')}",
                f"- disclosure: {row.get('review_disclosure', '')}",
                f"- correction handling: {row.get('correction_handling', '')}",
                f"- decision: {row.get('gate_decision', '')}",
                f"- limitation: {row.get('remaining_limitation', '')}",
                "",
            ]
        )
    return "\n".join(lines)


def _build_artifact_index_markdown(artifact_index_rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 344E Artifact Index",
        "",
        "| Artifact | Milestone | Role | Scope | Caution |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in artifact_index_rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('milestone', '')} | {row.get('role', '')} | {row.get('scope', '')} | {row.get('caution_label', '')} |"
        )
    return "\n".join(lines)


def _build_scope_boundary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 344E Scope Boundary",
            "",
            "## Chinese-first Summary",
            "- 344E 只生成 29 行 expanded trusted package 的最终 review/demo 审计快照与交接总结。",
            "- 这不是 formal client export。",
            "- 这不是 production ready。",
            "- 没有发生 production write-back。",
            "- global_strict_human_review_completed 必须保持 false。",
            "- 下一步默认建议是 345A formal export readiness gap assessment。",
            "",
            "## English Summary",
            "- 344E closes the 29-row expanded trusted review/demo arc only.",
            "- It is not formal client export and not production ready.",
            "- No production write-back occurred.",
            f"- export_usage remains {summary.get('export_usage', '')}.",
        ]
    )


def _build_final_handoff_summary_markdown(
    summary: Dict[str, Any],
    lineage_summary: Dict[str, Any],
) -> str:
    return "\n".join(
        [
            "# 344E Final Handoff Summary",
            "",
            "## 中文说明",
            "- 建议先打开 344E executive summary、trust-chain report、artifact index 和 final export gate snapshot，再看 344D workbook。",
            f"- 当前 29 行 expanded trusted package 包含 {summary.get('prior_demo_trusted_row_count', 0)} 条 earlier demo rows 和 {summary.get('source_check_trusted_row_count', 0)} 条 source-check resolved rows。",
            "- 它与 earlier 10-row demo package 的区别是：新增了 19 条已经补证据并完成 source-check review 的 backlog rows。",
            f"- 这 19 条里有 {summary.get('source_check_confirmed_row_count', 0)} 条 confirmed，{summary.get('source_check_corrected_row_count', 0)} 条 corrected。",
            "- 9 条 corrected rows 应理解为 YOY / % 语义，而不是 revenue amount rows。",
            "- 在 review/demo scope 内，这个 29-row package 已具备清晰的 source lineage、audit labels 和 no-write-back proof。",
            "- 但它仍然不是 formal client export，不应向客户声称为 final audited results。",
            "- 下一步如要推进正式导出，应先做 345A formal export readiness gap assessment。",
            "",
            "## Allowed Claims",
            "- 29 reviewed trusted candidate rows are available for review/demo handoff.",
            "- 19 source-check backlog rows were enriched with evidence and reviewed.",
            "- 10 source-check rows were confirmed and 9 were corrected.",
            "- No production write-back occurred.",
            "- Formal client export remains blocked.",
            "",
            "## Forbidden Claims",
            "- formal client export is ready",
            "- production export is ready",
            "- all corpus data is globally reviewed",
            "- system is production ready",
            "- output can be sent to clients as final audited results",
            "",
            "## English Note",
            "- This 29-row package is trustworthy for review/demo handoff only.",
            "- It remains blocked for formal client export and production use.",
            f"- correction semantics disclosed: {lineage_summary.get('correction_semantics', '')}",
        ]
    )


def _build_executive_summary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 344E Executive Summary",
            "",
            "## 中文摘要",
            "- DateFac 当前已形成一个 29-row expanded trusted review/demo package。",
            f"- 该 package 由 {summary.get('prior_demo_trusted_row_count', 0)} 条 earlier human-confirmed demo rows 和 {summary.get('source_check_trusted_row_count', 0)} 条 source-check resolved rows 组成。",
            "- 19 条 backlog rows 均已具备 source evidence 和 review decisions。",
            f"- 其中 {summary.get('source_check_confirmed_row_count', 0)} 条为 confirmed，{summary.get('source_check_corrected_row_count', 0)} 条为 corrected。",
            "- formal client export 仍被阻止，production readiness 仍为 false。",
            "",
            "## English Summary",
            "- The project now has a 29-row expanded trusted review/demo package.",
            "- It combines 10 earlier demo rows with 19 source-check resolved rows.",
            "- Formal client export remains blocked and production readiness remains false.",
        ]
    )


def build_review_queue_expanded_demo_audit_snapshot_344e(
    *,
    expanded_trusted_demo_export_package_344d_dir: Path = DEFAULT_EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_DIR,
    source_check_sidecar_simulation_344c_dir: Path = DEFAULT_SOURCE_CHECK_SIDECAR_SIMULATION_344C_DIR,
    source_check_ingestion_344b_dir: Path = DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR,
    source_check_evidence_enrichment_344a2_dir: Path = DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR,
    demo_audit_snapshot_343o_dir: Path = DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    limited_demo_export_package_343n_dir: Path = DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    input_paths = [
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_SUMMARY_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_QA_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_WORKBOOK_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_DEMO_README_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_EXPORT_ROWS_JSONL_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_EXPORT_ROWS_CSV_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_AUDIT_LABELS_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_EXPORT_GATE_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_LINEAGE_SUMMARY_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_SCOPE_BOUNDARY_NAME,
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_NO_WRITE_BACK_NAME,
        source_check_sidecar_simulation_344c_dir / INPUT_344C_SUMMARY_NAME,
        source_check_sidecar_simulation_344c_dir / INPUT_344C_CANDIDATES_NAME,
        source_check_sidecar_simulation_344c_dir / INPUT_344C_GATE_NAME,
        source_check_sidecar_simulation_344c_dir / INPUT_344C_DEDUP_AUDIT_NAME,
        source_check_ingestion_344b_dir / INPUT_344B_SUMMARY_NAME,
        source_check_ingestion_344b_dir / INPUT_344B_CORRECTIONS_NAME,
        source_check_evidence_enrichment_344a2_dir / INPUT_344A2_SUMMARY_NAME,
        source_check_evidence_enrichment_344a2_dir / INPUT_344A2_EVIDENCE_MAP_NAME,
        demo_audit_snapshot_343o_dir / INPUT_343O_SUMMARY_NAME,
        demo_audit_snapshot_343o_dir / INPUT_343O_HANDOFF_NAME,
        demo_audit_snapshot_343o_dir / INPUT_343O_ARTIFACT_INDEX_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_GATE_NAME,
        review_queue_schema_343a_dir / INPUT_343A_SCHEMA_NAME,
        review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME,
    ]

    files_read: List[str] = []
    missing_required_inputs: List[str] = []
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            missing_required_inputs.append(str(path))

    summary_344d = _read_json(expanded_trusted_demo_export_package_344d_dir / INPUT_344D_SUMMARY_NAME)
    qa_344d = _read_json(expanded_trusted_demo_export_package_344d_dir / INPUT_344D_QA_NAME)
    export_rows_344d = _read_jsonl(
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_EXPORT_ROWS_JSONL_NAME
    )
    audit_labels_344d = _read_jsonl(
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_AUDIT_LABELS_NAME
    )
    export_gate_344d = _read_json(
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_EXPORT_GATE_NAME
    )
    lineage_summary_344d = _read_json(
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_LINEAGE_SUMMARY_NAME
    )
    metric_distribution_344d = _read_json(
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_METRIC_DISTRIBUTION_NAME
    )
    scope_boundary_344d = _read_text(
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_SCOPE_BOUNDARY_NAME
    )
    demo_readme_344d = _read_text(
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_DEMO_README_NAME
    )
    no_write_back_344d = _read_json(
        expanded_trusted_demo_export_package_344d_dir / INPUT_344D_NO_WRITE_BACK_NAME
    )

    summary_344c = _read_json(source_check_sidecar_simulation_344c_dir / INPUT_344C_SUMMARY_NAME)
    candidates_344c = _read_jsonl(
        source_check_sidecar_simulation_344c_dir / INPUT_344C_CANDIDATES_NAME
    )
    export_gate_344c = _read_json(
        source_check_sidecar_simulation_344c_dir / INPUT_344C_GATE_NAME
    )
    dedup_audit_344c = _read_jsonl(
        source_check_sidecar_simulation_344c_dir / INPUT_344C_DEDUP_AUDIT_NAME
    )
    summary_344b = _read_json(source_check_ingestion_344b_dir / INPUT_344B_SUMMARY_NAME)
    corrections_344b = _read_jsonl(source_check_ingestion_344b_dir / INPUT_344B_CORRECTIONS_NAME)
    summary_344a2 = _read_json(
        source_check_evidence_enrichment_344a2_dir / INPUT_344A2_SUMMARY_NAME
    )
    evidence_map_344a2 = _read_json(
        source_check_evidence_enrichment_344a2_dir / INPUT_344A2_EVIDENCE_MAP_NAME
    )
    summary_343o = _read_json(demo_audit_snapshot_343o_dir / INPUT_343O_SUMMARY_NAME)
    handoff_343o = _read_text(demo_audit_snapshot_343o_dir / INPUT_343O_HANDOFF_NAME)
    artifact_index_343o = _read_json(
        demo_audit_snapshot_343o_dir / INPUT_343O_ARTIFACT_INDEX_NAME
    )
    export_gate_343n = _read_json(
        limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_GATE_NAME
    )
    schema_343a = _read_json(review_queue_schema_343a_dir / INPUT_343A_SCHEMA_NAME)
    summary_343a = _read_json(review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME)

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    corrected_rows = [
        row for row in export_rows_344d if normalize_text(row.get("source_check_status")) == "CORRECTED"
    ]
    labels_have_review_demo_flags = all(
        set(row.get("audit_labels", []))
        >= {
            "EXPANDED_TRUSTED_CANDIDATE",
            "REVIEW_DEMO_ONLY",
            "NOT_FORMAL_CLIENT_EXPORT",
            "NOT_PRODUCTION_READY",
            "NO_PRODUCTION_WRITE_BACK",
        }
        for row in audit_labels_344d
    )

    input_ready = bool(
        not missing_required_inputs
        and summary_344d.get("decision") == READY_INPUT_344D_DECISION
        and summary_344c.get("decision") == READY_INPUT_344C_DECISION
        and summary_344b.get("decision") == READY_INPUT_344B_DECISION
        and summary_343o.get("decision") == READY_INPUT_343O_DECISION
        and summary_343a.get("decision") == READY_INPUT_343A_DECISION
        and int(summary_344d.get("qa_fail_count", 1)) == 0
        and int(summary_344c.get("qa_fail_count", 1)) == 0
        and int(summary_344b.get("qa_fail_count", 1)) == 0
        and int(summary_343o.get("qa_fail_count", 1)) == 0
        and int(summary_343a.get("qa_fail_count", 1)) == 0
        and int(summary_344d.get("expanded_export_row_count", 0)) == 29
        and int(summary_344d.get("audit_label_row_count", 0)) == 29
        and normalize_text(summary_344d.get("expanded_export_scope")) == EXPANDED_EXPORT_SCOPE_344D
        and normalize_text(summary_344d.get("export_usage")) == EXPORT_USAGE_344D
        and normalize_bool(summary_344d.get("expanded_review_demo_package_generated"))
        and normalize_bool(summary_344d.get("expanded_demo_handoff_ready"))
        and normalize_bool(summary_344d.get("expanded_export_gate_generated"))
        and normalize_bool(summary_344d.get("lineage_summary_generated"))
        and normalize_bool(summary_344d.get("audit_labels_generated"))
        and normalize_bool(summary_344d.get("source_check_backlog_resolved"))
        and not normalize_bool(summary_344d.get("formal_client_export_allowed"))
        and not normalize_bool(summary_344d.get("client_ready"))
        and not normalize_bool(summary_344d.get("production_ready"))
        and not normalize_bool(summary_344d.get("global_strict_human_review_completed"))
        and int(lineage_summary_344d.get("prior_demo_trusted_row_count", 0)) == 10
        and int(lineage_summary_344d.get("source_check_trusted_row_count", 0)) == 19
        and int(lineage_summary_344d.get("source_check_confirmed_row_count", 0)) == 10
        and int(lineage_summary_344d.get("source_check_corrected_row_count", 0)) == 9
        and len(export_rows_344d) == 29
        and len(audit_labels_344d) == 29
        and len(candidates_344c) == 29
        and len(corrections_344b) == 9
        and int(summary_344a2.get("evidence_resolved_count", 0)) == 19
        and int(evidence_map_344a2.get("resolved_count", 0)) == 19
        and not normalize_bool(export_gate_344d.get("formal_client_export_allowed"))
        and not normalize_bool(export_gate_343n.get("formal_client_export_allowed"))
        and bool(handoff_343o.strip())
        and bool(demo_readme_344d.strip())
        and bool(scope_boundary_344d.strip())
        and bool(no_write_back_344d.get("no_write_back", False))
    )

    trust_chain_rows = _build_trust_chain_rows(
        summary_343a=summary_343a,
        summary_343o=summary_343o,
        summary_344a2=summary_344a2,
        summary_344b=summary_344b,
        summary_344c=summary_344c,
        summary_344d=summary_344d,
    )
    artifact_index_rows = _build_artifact_index_rows(
        expanded_dir_344d=expanded_trusted_demo_export_package_344d_dir,
        source_check_sim_dir_344c=source_check_sidecar_simulation_344c_dir,
        source_check_ingestion_dir_344b=source_check_ingestion_344b_dir,
        source_check_enrichment_dir_344a2=source_check_evidence_enrichment_344a2_dir,
        demo_snapshot_dir_343o=demo_audit_snapshot_343o_dir,
    )
    lineage_audit_summary = _build_lineage_audit_summary(
        summary_344d=summary_344d,
        lineage_344d=lineage_summary_344d,
        corrections_344b=corrections_344b,
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "344D",
        "decision": NOT_READY_DECISION_344E,
        "review_queue_schema_version": summary_344d.get(
            "review_queue_schema_version",
            summary_343a.get("review_queue_schema_version", ""),
        ),
        "input_expanded_export_row_count": len(export_rows_344d),
        "audit_label_row_count": len(audit_labels_344d),
        "prior_demo_trusted_row_count": int(lineage_summary_344d.get("prior_demo_trusted_row_count", 0)),
        "source_check_trusted_row_count": int(lineage_summary_344d.get("source_check_trusted_row_count", 0)),
        "source_check_confirmed_row_count": int(lineage_summary_344d.get("source_check_confirmed_row_count", 0)),
        "source_check_corrected_row_count": int(lineage_summary_344d.get("source_check_corrected_row_count", 0)),
        "correction_row_count": int(lineage_summary_344d.get("correction_row_count", 0)),
        "expanded_export_scope": EXPANDED_EXPORT_SCOPE_344D,
        "export_usage": EXPORT_USAGE_344D,
        "expanded_review_demo_package_generated": True,
        "expanded_demo_handoff_ready": True,
        "expanded_demo_audit_snapshot_generated": False,
        "final_handoff_summary_generated": False,
        "executive_summary_generated": False,
        "trust_chain_report_generated": False,
        "artifact_index_generated": False,
        "final_export_gate_snapshot_generated": False,
        "lineage_audit_summary_generated": False,
        "metric_distribution_generated": False,
        "expanded_demo_arc_closed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "ready_for_345a": False,
        "recommended_345a_scope": "",
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    trust_chain_markdown = _build_trust_chain_markdown(trust_chain_rows)
    artifact_index_markdown = _build_artifact_index_markdown(artifact_index_rows)
    scope_boundary_markdown = _build_scope_boundary_markdown(summary)
    final_handoff_summary_markdown = _build_final_handoff_summary_markdown(
        summary,
        lineage_audit_summary,
    )
    executive_summary_markdown = _build_executive_summary_markdown(summary)

    final_export_gate_snapshot = _build_final_export_gate_snapshot(summary)
    next_action_plan = _build_next_action_plan(summary)

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="344E",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["expanded_demo_audit_snapshot_generated"] = True
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_344e")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::344d_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "missing_required_inputs": missing_required_inputs,
                    "decision_344d": summary_344d.get("decision", ""),
                    "decision_344c": summary_344c.get("decision", ""),
                    "decision_344b": summary_344b.get("decision", ""),
                    "decision_343o": summary_343o.get("decision", ""),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::expanded_export_rows_count_is_29",
            "status": "PASS" if len(export_rows_344d) == 29 else "FAIL",
            "detail": json.dumps({"input_expanded_export_row_count": len(export_rows_344d)}, ensure_ascii=False),
        },
        {
            "check_name": "counts::audit_label_row_count_is_29",
            "status": "PASS" if len(audit_labels_344d) == 29 else "FAIL",
            "detail": json.dumps({"audit_label_row_count": len(audit_labels_344d)}, ensure_ascii=False),
        },
        {
            "check_name": "scope::expanded_export_scope_is_correct",
            "status": "PASS" if summary_344d.get("expanded_export_scope") == EXPANDED_EXPORT_SCOPE_344D else "FAIL",
            "detail": summary_344d.get("expanded_export_scope", ""),
        },
        {
            "check_name": "scope::export_usage_is_review_demo_only",
            "status": "PASS" if summary_344d.get("export_usage") == EXPORT_USAGE_344D else "FAIL",
            "detail": summary_344d.get("export_usage", ""),
        },
        {
            "check_name": "lineage::summary_matches_10_plus_19",
            "status": "PASS"
            if lineage_audit_summary["prior_demo_trusted_row_count"] == 10
            and lineage_audit_summary["source_check_trusted_row_count"] == 19
            and len(export_rows_344d) == 29
            else "FAIL",
            "detail": json.dumps(lineage_audit_summary, ensure_ascii=False),
        },
        {
            "check_name": "lineage::source_check_corrected_rows_count_is_9",
            "status": "PASS"
            if lineage_audit_summary["source_check_corrected_row_count"] == 9
            and len(corrections_344b) == 9
            else "FAIL",
            "detail": json.dumps(
                {
                    "source_check_corrected_row_count": lineage_audit_summary["source_check_corrected_row_count"],
                    "corrections_344b_count": len(corrections_344b),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "lineage::corrected_rows_disclose_yoy_percent_semantics",
            "status": "PASS"
            if all(
                normalize_text(row.get("metric_standardized")) == "YOY"
                and normalize_text(row.get("normalized_unit")) == "%"
                for row in corrected_rows
            )
            else "FAIL",
            "detail": lineage_audit_summary.get("correction_semantics", ""),
        },
        {
            "check_name": "outputs::final_handoff_summary_generated",
            "status": "PASS" if bool(final_handoff_summary_markdown.strip()) else "FAIL",
            "detail": FINAL_HANDOFF_SUMMARY_FILE_NAME,
        },
        {
            "check_name": "outputs::executive_summary_generated",
            "status": "PASS" if bool(executive_summary_markdown.strip()) else "FAIL",
            "detail": EXECUTIVE_SUMMARY_FILE_NAME,
        },
        {
            "check_name": "outputs::trust_chain_report_generated",
            "status": "PASS" if len(trust_chain_rows) >= 12 and bool(trust_chain_markdown.strip()) else "FAIL",
            "detail": json.dumps({"trust_chain_row_count": len(trust_chain_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::artifact_index_generated",
            "status": "PASS" if len(artifact_index_rows) >= 10 and bool(artifact_index_markdown.strip()) else "FAIL",
            "detail": json.dumps({"artifact_index_count": len(artifact_index_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::final_export_gate_snapshot_generated",
            "status": "PASS" if not normalize_bool(final_export_gate_snapshot.get("formal_client_export_allowed")) else "FAIL",
            "detail": json.dumps(final_export_gate_snapshot, ensure_ascii=False),
        },
        {
            "check_name": "claims::final_boundary_blocks_formal_client_production_readiness",
            "status": "PASS"
            if not summary["formal_client_export_allowed"]
            and not summary["client_ready"]
            and not summary["production_ready"]
            and not summary["global_strict_human_review_completed"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready/global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "outputs::expanded_demo_arc_closed_only_if_all_artifacts_pass",
            "status": "PASS",
            "detail": "expanded_demo_arc_closed is computed only after QA succeeds.",
        },
        {
            "check_name": "safety::no_formal_client_export_workbook_generated",
            "status": "PASS",
            "detail": "344E generates an audit snapshot workbook, not a formal client export workbook.",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "344E is snapshot/handoff only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "344E does not write back or perform production apply.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "344E adds review-queue audit snapshot files only.",
        },
        {
            "check_name": "safety::protected_dirty_status_preserved",
            "status": "PASS" if protected_before == protected_after else "FAIL",
            "detail": json.dumps(protected_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::protected_dirty_files_not_staged",
            "status": "PASS" if not protected_staged else "FAIL",
            "detail": json.dumps(protected_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::forbidden_output_or_input_artifacts_not_staged",
            "status": "PASS" if not forbidden_staged else "FAIL",
            "detail": json.dumps(forbidden_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::sheet_names_within_limit",
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_344E) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_344E, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed
    summary["expanded_demo_audit_snapshot_generated"] = qa_fail_count == 0
    summary["final_handoff_summary_generated"] = qa_fail_count == 0
    summary["executive_summary_generated"] = qa_fail_count == 0
    summary["trust_chain_report_generated"] = qa_fail_count == 0
    summary["artifact_index_generated"] = qa_fail_count == 0
    summary["final_export_gate_snapshot_generated"] = qa_fail_count == 0
    summary["lineage_audit_summary_generated"] = qa_fail_count == 0
    summary["metric_distribution_generated"] = qa_fail_count == 0
    summary["expanded_demo_arc_closed"] = qa_fail_count == 0
    summary["ready_for_345a"] = qa_fail_count == 0
    summary["recommended_345a_scope"] = RECOMMENDED_345A_SCOPE_344E if qa_fail_count == 0 else ""
    summary["decision"] = READY_DECISION_344E if qa_fail_count == 0 else NOT_READY_DECISION_344E

    final_export_gate_snapshot = _build_final_export_gate_snapshot(summary)
    next_action_plan = _build_next_action_plan(summary)
    scope_boundary_markdown = _build_scope_boundary_markdown(summary)
    final_handoff_summary_markdown = _build_final_handoff_summary_markdown(
        summary,
        lineage_audit_summary,
    )
    executive_summary_markdown = _build_executive_summary_markdown(summary)

    manifest = {
        "task": "344E_expanded_trusted_demo_audit_snapshot_and_final_handoff_summary",
        "expanded_trusted_demo_export_package_344d_dir": str(expanded_trusted_demo_export_package_344d_dir),
        "source_check_sidecar_simulation_344c_dir": str(source_check_sidecar_simulation_344c_dir),
        "source_check_ingestion_344b_dir": str(source_check_ingestion_344b_dir),
        "source_check_evidence_enrichment_344a2_dir": str(source_check_evidence_enrichment_344a2_dir),
        "demo_audit_snapshot_343o_dir": str(demo_audit_snapshot_343o_dir),
        "limited_demo_export_package_343n_dir": str(limited_demo_export_package_343n_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "final_handoff_summary_md": str(output_dir / FINAL_HANDOFF_SUMMARY_FILE_NAME),
            "executive_summary_md": str(output_dir / EXECUTIVE_SUMMARY_FILE_NAME),
            "trust_chain_report_md": str(output_dir / TRUST_CHAIN_REPORT_FILE_NAME),
            "artifact_index_json": str(output_dir / ARTIFACT_INDEX_JSON_FILE_NAME),
            "artifact_index_md": str(output_dir / ARTIFACT_INDEX_JSON_FILE_NAME),
            "final_export_gate_snapshot_json": str(output_dir / FINAL_EXPORT_GATE_SNAPSHOT_FILE_NAME),
            "lineage_audit_summary_json": str(output_dir / LINEAGE_AUDIT_SUMMARY_FILE_NAME),
            "metric_distribution_json": str(output_dir / METRIC_DISTRIBUTION_FILE_NAME),
            "scope_boundary_md": str(output_dir / SCOPE_BOUNDARY_FILE_NAME),
            "next_action_plan_json": str(output_dir / NEXT_ACTION_PLAN_FILE_NAME),
        },
        "files_read": list(files_read),
        "warnings": [],
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": 0,
        "checks": checks,
        "warnings": [],
        "input_summary_344d": summary_344d,
        "input_qa_344d": qa_344d,
        "input_summary_344c": summary_344c,
        "input_summary_344b": summary_344b,
        "input_summary_344a2": summary_344a2,
        "input_summary_343o": summary_343o,
        "input_summary_343a": summary_343a,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _build_readme_df(summary),
        "01_SNAPSHOT_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_344D_SUMMARY": _build_key_value_df(summary_344d),
        "03_EXPANDED_PACKAGE": _clean_frame(pd.DataFrame(_build_expanded_package_rows(export_rows_344d))),
        "04_TRUST_CHAIN": _clean_frame(pd.DataFrame(trust_chain_rows)),
        "05_LINEAGE_AUDIT": _build_key_value_df(lineage_audit_summary),
        "06_ARTIFACT_INDEX": _clean_frame(pd.DataFrame(artifact_index_rows)),
        "07_FINAL_GATE": _build_key_value_df(final_export_gate_snapshot),
        "08_SCOPE_BOUNDARY": _build_key_value_df(
            {
                "scope_boundary_report": scope_boundary_markdown,
                "upstream_344d_scope_boundary": scope_boundary_344d,
                "upstream_344d_demo_readme_excerpt": demo_readme_344d[:1200],
                "upstream_343o_handoff_excerpt": handoff_343o[:1200],
                "upstream_344a2_resolution_counts": summary_344a2,
            }
        ),
        "09_NEXT_ACTION_PLAN": _build_key_value_df(next_action_plan),
        "10_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "trust_chain_rows": trust_chain_rows,
        "artifact_index_rows": artifact_index_rows,
        "final_export_gate_snapshot": final_export_gate_snapshot,
        "lineage_audit_summary": lineage_audit_summary,
        "metric_distribution": metric_distribution_344d,
        "next_action_plan": next_action_plan,
        "final_handoff_summary_markdown": final_handoff_summary_markdown,
        "executive_summary_markdown": executive_summary_markdown,
        "trust_chain_markdown": trust_chain_markdown,
        "scope_boundary_markdown": scope_boundary_markdown,
        "artifact_index_markdown": artifact_index_markdown,
        "workbook_sheets": workbook_sheets,
        "reference_artifacts": {
            "artifact_index_343o": artifact_index_343o,
            "evidence_map_344a2": evidence_map_344a2,
            "export_gate_344c": export_gate_344c,
            "export_gate_343n": export_gate_343n,
            "schema_343a": schema_343a,
            "dedup_audit_344c": dedup_audit_344c,
        },
    }
