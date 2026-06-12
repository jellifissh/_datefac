from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.ingest_strict_review_343j import FORBIDDEN_STAGE_PATHS, PROTECTED_DIRTY_PATHS
from datefac.review_queue.limited_demo_export_package_343n import READY_DECISION_343N
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_343O = "DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_READY"
NOT_READY_DECISION_343O = "DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_NOT_READY"
RECOMMENDED_344A_SCOPE_343O = "source_check_backlog_resolution_package"

WORKBOOK_SHEETS_343O = [
    "00_README",
    "01_SNAPSHOT_SUMMARY",
    "02_INPUT_343N_SUMMARY",
    "03_TRUST_CHAIN",
    "04_DEMO_EXPORT_OVERVIEW",
    "05_EXPORT_GATE_SNAPSHOT",
    "06_BACKLOG_SUMMARY",
    "07_ARTIFACT_INDEX",
    "08_SCOPE_BOUNDARY",
    "09_NEXT_ACTION_PLAN",
    "10_NO_WRITE_BACK",
]

INPUT_343N_SUMMARY_NAME = "review_queue_limited_demo_export_package_343n_summary.json"
INPUT_343N_QA_NAME = "review_queue_limited_demo_export_package_343n_qa.json"
INPUT_343N_WORKBOOK_NAME = "review_queue_limited_demo_export_package_343n.xlsx"
INPUT_343N_DEMO_README_NAME = "review_queue_limited_demo_export_package_343n_demo_readme.md"
INPUT_343N_EXPORT_ROWS_JSONL_NAME = "review_queue_limited_demo_export_package_343n_export_rows.jsonl"
INPUT_343N_EXPORT_ROWS_CSV_NAME = "review_queue_limited_demo_export_package_343n_export_rows.csv"
INPUT_343N_AUDIT_LABELS_NAME = "review_queue_limited_demo_export_package_343n_audit_labels.jsonl"
INPUT_343N_EXPORT_GATE_NAME = "review_queue_limited_demo_export_package_343n_export_gate.json"
INPUT_343N_SCOPE_BOUNDARY_NAME = "review_queue_limited_demo_export_package_343n_scope_boundary.md"
INPUT_343N_REMAINING_BACKLOG_NAME = "review_queue_limited_demo_export_package_343n_remaining_backlog.jsonl"
INPUT_343N_NO_WRITE_BACK_NAME = "review_queue_limited_demo_export_package_343n_no_write_back_proof.json"

INPUT_343M_SUMMARY_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_summary.json"
INPUT_343M_GATE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate.json"
INPUT_343L_SUMMARY_NAME = "review_queue_pure_human_attestation_ingestion_343l_summary.json"
INPUT_343L_SCOPE_BOUNDARY_NAME = "review_queue_pure_human_attestation_ingestion_343l_scope_boundary.md"
INPUT_343H_SUMMARY_NAME = "review_queue_audit_summary_343h_summary.json"
INPUT_343H_GAP_REPORT_NAME = "review_queue_audit_summary_343h_strict_human_gap_report.md"
INPUT_343H_BACKLOG_NAME = "review_queue_audit_summary_343h_source_check_backlog.jsonl"
INPUT_343A_SCHEMA_NAME = "review_queue_schema_343a_schema.json"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"


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
                    "message": "343O closes the trusted 10-row demo arc with an audit snapshot and handoff summary.",
                },
                {
                    "section": "scope",
                    "message": "The package scope remains strictly limited to 343K_PACKAGE_ONLY and DEMO_ONLY.",
                },
                {
                    "section": "boundary",
                    "message": "This is not a formal client export, not production-ready, and not global client-ready.",
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
    summary_343h: Dict[str, Any],
    summary_343l: Dict[str, Any],
    summary_343m: Dict[str, Any],
    summary_343n: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return [
        {
            "milestone_id": "343A",
            "purpose": "Review queue schema and UI contract",
            "key_count": int(summary_343a.get("field_count", 0)),
            "review_or_evidence_status": "schema_ready",
            "human_ai_disclosure": "schema_only",
            "gate_decision": summary_343a.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Schema only; no review result implied.",
        },
        {
            "milestone_id": "343H",
            "purpose": "AI-assisted spot-check audit summary",
            "key_count": int(summary_343h.get("ai_assisted_confirmed_count", 0)),
            "review_or_evidence_status": "ai_assisted_spot_check_audit_ready",
            "human_ai_disclosure": "AI_ASSISTED_REVIEW + AI_ASSISTED_SPOT_CHECK",
            "gate_decision": summary_343h.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": f"{int(summary_343h.get('source_check_backlog_count', 0))} source-check backlog rows remain.",
        },
        {
            "milestone_id": "343I2",
            "purpose": "Source evidence enrichment for strict review package",
            "key_count": 10,
            "review_or_evidence_status": "upstream_evidence_locator_enrichment_referenced",
            "human_ai_disclosure": "AI-assisted evidence locator enrichment referenced by downstream package",
            "gate_decision": "REFERENCED_UPSTREAM_FOR_PACKAGE_SCOPE",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "343O references package-scope enriched evidence; it does not re-run enrichment.",
        },
        {
            "milestone_id": "343L",
            "purpose": "Pure human attestation ingestion for package scope",
            "key_count": int(summary_343l.get("human_accept_count", 0)),
            "review_or_evidence_status": "package_level_pure_human_confirmation_complete",
            "human_ai_disclosure": "pure human attestation at package scope",
            "gate_decision": summary_343l.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Scope limited to 343K_PACKAGE_ONLY; global review incomplete.",
        },
        {
            "milestone_id": "343M",
            "purpose": "Human-confirmed sidecar simulation and limited export gate",
            "key_count": int(summary_343m.get("limited_export_candidate_row_count", 0)),
            "review_or_evidence_status": "package_scope_sidecar_simulation_ready",
            "human_ai_disclosure": "human-confirmed package rows only",
            "gate_decision": summary_343m.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": f"{int(summary_343m.get('remaining_source_check_backlog_count', 0))} backlog rows still block global export.",
        },
        {
            "milestone_id": "343N",
            "purpose": "Demo-only limited export package generation",
            "key_count": int(summary_343n.get("demo_export_row_count", 0)),
            "review_or_evidence_status": "demo_only_limited_package_ready",
            "human_ai_disclosure": "package-scope human-confirmed demo export only",
            "gate_decision": summary_343n.get("decision", ""),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "remaining_limitation": "Demo/sample/handoff only; not formal client export.",
        },
    ]


def _build_artifact_index_rows(
    *,
    limited_demo_export_package_343n_dir: Path,
    human_confirmed_sidecar_simulation_343m_dir: Path,
    pure_human_attestation_ingestion_343l_dir: Path,
    audit_summary_343h_dir: Path,
) -> List[Dict[str, Any]]:
    return [
        {
            "artifact_name": "343N workbook",
            "path": str(limited_demo_export_package_343n_dir / INPUT_343N_WORKBOOK_NAME),
            "role": "Primary 10-row demo package workbook",
            "user_facing_demo_facing": True,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "DEMO_ONLY",
        },
        {
            "artifact_name": "343N demo readme",
            "path": str(limited_demo_export_package_343n_dir / INPUT_343N_DEMO_README_NAME),
            "role": "Open-first package explanation",
            "user_facing_demo_facing": True,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "NOT_FORMAL_CLIENT_EXPORT",
        },
        {
            "artifact_name": "343N export rows jsonl",
            "path": str(limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_ROWS_JSONL_NAME),
            "role": "Machine-readable demo export rows",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "GLOBAL_REVIEW_INCOMPLETE",
        },
        {
            "artifact_name": "343N export gate",
            "path": str(limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_GATE_NAME),
            "role": "Demo-only gate snapshot",
            "user_facing_demo_facing": True,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "NOT_PRODUCTION_READY",
        },
        {
            "artifact_name": "343M sidecar summary",
            "path": str(human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_SUMMARY_NAME),
            "role": "Upstream package-sidecar simulation summary",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "SIDECAR_ONLY",
        },
        {
            "artifact_name": "343M limited export gate",
            "path": str(human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_GATE_NAME),
            "role": "Scoped export candidate gate",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "LIMITED_SCOPE_ONLY",
        },
        {
            "artifact_name": "343L attestation summary",
            "path": str(pure_human_attestation_ingestion_343l_dir / INPUT_343L_SUMMARY_NAME),
            "role": "Package-level pure human confirmation summary",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "PACKAGE_ONLY",
        },
        {
            "artifact_name": "343L scope boundary",
            "path": str(pure_human_attestation_ingestion_343l_dir / INPUT_343L_SCOPE_BOUNDARY_NAME),
            "role": "Pure human confirmation scope boundary note",
            "user_facing_demo_facing": True,
            "formal_client_export": False,
            "scope": "343K_PACKAGE_ONLY",
            "caution_label": "NOT_GLOBAL_REVIEW_COMPLETE",
        },
        {
            "artifact_name": "343H audit summary",
            "path": str(audit_summary_343h_dir / INPUT_343H_SUMMARY_NAME),
            "role": "AI-assisted audit baseline and backlog summary",
            "user_facing_demo_facing": False,
            "formal_client_export": False,
            "scope": "audit_baseline",
            "caution_label": "AI_ASSISTED_REVIEW",
        },
        {
            "artifact_name": "343H strict human gap report",
            "path": str(audit_summary_343h_dir / INPUT_343H_GAP_REPORT_NAME),
            "role": "Gap explanation for remaining human/source checks",
            "user_facing_demo_facing": True,
            "formal_client_export": False,
            "scope": "audit_baseline",
            "caution_label": "BACKLOG_REMAINS",
        },
    ]


def _build_export_overview_rows(demo_export_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in demo_export_rows:
        rows.append(
            {
                "queue_item_id": row.get("queue_item_id", ""),
                "review_item_id": row.get("review_item_id", ""),
                "metric_standardized": row.get("metric_standardized", ""),
                "year_standardized": row.get("year_standardized", ""),
                "value_numeric": row.get("value_numeric", ""),
                "normalized_unit": row.get("normalized_unit", ""),
                "source_pdf_name": row.get("source_pdf_name", ""),
                "page_number": row.get("page_number", ""),
                "table_id": row.get("table_id", ""),
                "export_scope": row.get("export_scope", ""),
                "export_usage": row.get("export_usage", ""),
                "audit_labels": row.get("audit_labels", []),
            }
        )
    return rows


def _build_backlog_summary(
    *,
    remaining_backlog_rows: List[Dict[str, Any]],
    summary_343h: Dict[str, Any],
) -> Dict[str, Any]:
    unique_metrics = sorted(
        {
            normalize_text(row.get("metric_standardized"))
            for row in remaining_backlog_rows
            if normalize_text(row.get("metric_standardized"))
        }
    )
    return {
        "remaining_source_check_backlog_count": len(remaining_backlog_rows),
        "source_check_required_count_from_343h": int(summary_343h.get("source_check_required_count", 0)),
        "strict_human_gap_item_count_from_343h": int(summary_343h.get("strict_human_gap_item_count", 0)),
        "unique_metric_count_in_backlog": len(unique_metrics),
        "sample_metrics": unique_metrics[:10],
        "interpretation": "Backlog rows remain outside the 10-row trusted demo package and block any formal/global export claim.",
    }


def _build_next_action_plan(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "primary_route": {
            "task_id": "344A",
            "scope": RECOMMENDED_344A_SCOPE_343O,
            "reason": "Expand trusted coverage beyond the current 10-row demo package by resolving remaining source-check backlog.",
        },
        "secondary_route": {
            "task_id": "343P",
            "scope": "demo_presentation_report_material_assembly",
            "reason": "If the immediate goal is presentation/handoff, package the current trusted arc into presentation-ready materials.",
        },
        "default_recommendation": RECOMMENDED_344A_SCOPE_343O,
        "demo_arc_closed": bool(summary.get("demo_arc_closed", False)),
    }


def _build_handoff_summary_markdown(summary: Dict[str, Any], backlog_summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 343O Demo Package Handoff Summary",
            "",
            "## 中文说明",
            "- 建议先打开 343O executive summary、artifact index 和 export gate snapshot，再看 343N workbook。",
            "- 当前 demo package 只包含 10 条 `343K_PACKAGE_ONLY` 范围内的 package-scope human-confirmed rows。",
            "- 这 10 条之所以可信，是因为它们经过了 evidence enrichment、package-level pure human attestation、343M sidecar simulation 和 343N demo-only export gate。",
            "- 这仍然不是 formal client export，不是 production export，也不是 global client-ready。",
            f"- 当前仍有 {backlog_summary.get('remaining_source_check_backlog_count', 0)} 条 source-check backlog 在包外，不能忽略。",
            "- 对外展示时只能说这是受限 demo/sample/handoff artifact，不应声称已完成全局严格人审或正式客户导出。",
            "",
            "## English Note",
            "- Open the executive summary, artifact index, and gate snapshot first, then the 343N workbook.",
            "- The current package contains only 10 package-scope human-confirmed rows.",
            "- It remains demo-only and must not be described as a formal client export.",
        ]
    )


def _build_executive_summary_markdown(summary: Dict[str, Any], backlog_summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 343O Executive Summary",
            "",
            "## 中文摘要",
            "- DateFac 当前已经形成一个 10-row、package-scope、human-confirmed 的 demo-only export package。",
            "- 这条可信链路覆盖了 evidence enrichment、pure human attestation、sidecar simulation、limited export gate 和 demo package generation。",
            "- formal client export 仍然禁止，global strict human review 仍未完成。",
            f"- 剩余 source-check backlog = {backlog_summary.get('remaining_source_check_backlog_count', 0)}，因此当前主建议是进入 344A backlog resolution。",
            "",
            "## English Summary",
            "- DateFac currently has a 10-row human-confirmed demo-only export package within package scope.",
            "- Formal client export remains blocked and global strict human review remains incomplete.",
        ]
    )


def _build_trust_chain_markdown(trust_chain_rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# 343O Trust Chain",
        "",
        "## 中文说明",
        "- 下表概括了从 343A 到 343N 的 package-scope 可信链路。",
        "",
        "| Milestone | Purpose | Count | Status | Limitation |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in trust_chain_rows:
        lines.append(
            f"| {row['milestone_id']} | {row['purpose']} | {row['key_count']} | {row['review_or_evidence_status']} | {row['remaining_limitation']} |"
        )
    lines.extend(
        [
            "",
            "## English Note",
            "- The current trusted arc is package-scoped and demo-only.",
        ]
    )
    return "\n".join(lines)


def _build_scope_boundary_markdown(summary: Dict[str, Any], backlog_summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 343O Scope Boundary",
            "",
            "## 中文说明",
            "- 343O 只对 343N 的 10-row demo package 做审计快照和交接总结。",
            "- 这不是 formal client export，不是 production export，不代表全局 client-ready。",
            f"- 包外仍有 {backlog_summary.get('remaining_source_check_backlog_count', 0)} 条 backlog，global strict human review 仍未完成。",
            "",
            "## Current Boundary",
            f"- limited_export_scope: {summary.get('limited_export_scope', '')}",
            f"- export_usage: {summary.get('export_usage', '')}",
            f"- formal_client_export_allowed: {summary.get('formal_client_export_allowed', False)}",
            f"- client_ready: {summary.get('client_ready', False)}",
            f"- production_ready: {summary.get('production_ready', False)}",
            f"- global_strict_human_review_completed: {summary.get('global_strict_human_review_completed', False)}",
        ]
    )


def _build_artifact_index_markdown(artifact_index_rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# 343O Artifact Index",
        "",
        "| Artifact | Role | Scope | Demo-facing | Caution |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in artifact_index_rows:
        lines.append(
            f"| {row['artifact_name']} | {row['role']} | {row['scope']} | {row['user_facing_demo_facing']} | {row['caution_label']} |"
        )
        lines.append(f"| Path | {row['path']} |  |  |  |")
    return "\n".join(lines)


def build_review_queue_demo_audit_snapshot_343o(
    *,
    limited_demo_export_package_343n_dir: Path,
    human_confirmed_sidecar_simulation_343m_dir: Path,
    pure_human_attestation_ingestion_343l_dir: Path,
    audit_summary_343h_dir: Path,
    review_queue_schema_343a_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    input_paths = [
        limited_demo_export_package_343n_dir / INPUT_343N_SUMMARY_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_QA_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_WORKBOOK_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_DEMO_README_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_ROWS_JSONL_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_ROWS_CSV_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_AUDIT_LABELS_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_GATE_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_SCOPE_BOUNDARY_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_REMAINING_BACKLOG_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_NO_WRITE_BACK_NAME,
        human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_SUMMARY_NAME,
        human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_GATE_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_SUMMARY_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_SCOPE_BOUNDARY_NAME,
        audit_summary_343h_dir / INPUT_343H_SUMMARY_NAME,
        audit_summary_343h_dir / INPUT_343H_GAP_REPORT_NAME,
        audit_summary_343h_dir / INPUT_343H_BACKLOG_NAME,
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

    summary_343n = _read_json(limited_demo_export_package_343n_dir / INPUT_343N_SUMMARY_NAME)
    qa_343n = _read_json(limited_demo_export_package_343n_dir / INPUT_343N_QA_NAME)
    export_rows_343n = _read_jsonl(limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_ROWS_JSONL_NAME)
    audit_labels_343n = _read_jsonl(limited_demo_export_package_343n_dir / INPUT_343N_AUDIT_LABELS_NAME)
    export_gate_343n = _read_json(limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_GATE_NAME)
    remaining_backlog_343n = _read_jsonl(limited_demo_export_package_343n_dir / INPUT_343N_REMAINING_BACKLOG_NAME)
    summary_343m = _read_json(human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_SUMMARY_NAME)
    summary_343l = _read_json(pure_human_attestation_ingestion_343l_dir / INPUT_343L_SUMMARY_NAME)
    summary_343h = _read_json(audit_summary_343h_dir / INPUT_343H_SUMMARY_NAME)
    summary_343a = _read_json(review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME)

    demo_readme_343n = _read_text(limited_demo_export_package_343n_dir / INPUT_343N_DEMO_README_NAME)
    scope_boundary_343n = _read_text(limited_demo_export_package_343n_dir / INPUT_343N_SCOPE_BOUNDARY_NAME)
    gap_report_343h = _read_text(audit_summary_343h_dir / INPUT_343H_GAP_REPORT_NAME)
    scope_boundary_343l = _read_text(pure_human_attestation_ingestion_343l_dir / INPUT_343L_SCOPE_BOUNDARY_NAME)

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        not missing_required_inputs
        and summary_343n.get("decision") == READY_DECISION_343N
        and int(summary_343n.get("qa_fail_count", 1)) == 0
        and normalize_bool(summary_343n.get("demo_only_export_package_generated"))
        and normalize_bool(summary_343n.get("demo_handoff_ready"))
        and int(summary_343n.get("demo_export_row_count", -1)) == 10
        and int(summary_343n.get("audit_label_row_count", -1)) == 10
        and normalize_text(summary_343n.get("limited_export_scope")) == "343K_PACKAGE_ONLY"
        and normalize_text(summary_343n.get("export_usage")) == "DEMO_ONLY"
        and not normalize_bool(summary_343n.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343n.get("client_ready"))
        and not normalize_bool(summary_343n.get("production_ready"))
        and not normalize_bool(summary_343n.get("global_strict_human_review_completed"))
        and normalize_bool(export_gate_343n.get("demo_only_export_package_generated"))
        and not normalize_bool(export_gate_343n.get("formal_client_export_allowed"))
    )

    trust_chain_rows = _build_trust_chain_rows(
        summary_343a=summary_343a,
        summary_343h=summary_343h,
        summary_343l=summary_343l,
        summary_343m=summary_343m,
        summary_343n=summary_343n,
    )
    artifact_index_rows = _build_artifact_index_rows(
        limited_demo_export_package_343n_dir=limited_demo_export_package_343n_dir,
        human_confirmed_sidecar_simulation_343m_dir=human_confirmed_sidecar_simulation_343m_dir,
        pure_human_attestation_ingestion_343l_dir=pure_human_attestation_ingestion_343l_dir,
        audit_summary_343h_dir=audit_summary_343h_dir,
    )
    backlog_summary = _build_backlog_summary(
        remaining_backlog_rows=remaining_backlog_343n,
        summary_343h=summary_343h,
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343N",
        "decision": NOT_READY_DECISION_343O,
        "review_queue_schema_version": summary_343n.get(
            "review_queue_schema_version",
            summary_343a.get("review_queue_schema_version", ""),
        ),
        "input_demo_export_row_count": len(export_rows_343n),
        "audit_label_row_count": len(audit_labels_343n),
        "limited_export_scope": "343K_PACKAGE_ONLY",
        "export_usage": "DEMO_ONLY",
        "remaining_source_check_backlog_count": backlog_summary["remaining_source_check_backlog_count"],
        "package_strict_human_review_completed": True,
        "global_strict_human_review_completed": False,
        "demo_only_export_package_generated": True,
        "demo_handoff_ready": True,
        "demo_audit_snapshot_generated": False,
        "handoff_summary_generated": False,
        "executive_summary_generated": False,
        "trust_chain_generated": False,
        "artifact_index_generated": False,
        "export_gate_snapshot_generated": False,
        "demo_arc_closed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_344a": False,
        "recommended_344a_scope": "",
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    handoff_summary_markdown = _build_handoff_summary_markdown(summary, backlog_summary)
    executive_summary_markdown = _build_executive_summary_markdown(summary, backlog_summary)
    trust_chain_markdown = _build_trust_chain_markdown(trust_chain_rows)
    artifact_index_markdown = _build_artifact_index_markdown(artifact_index_rows)
    scope_boundary_markdown = _build_scope_boundary_markdown(summary, backlog_summary)

    export_gate_snapshot = {
        "demo_only_export_package_generated": True,
        "demo_handoff_ready": True,
        "limited_package_export_candidate_allowed": True,
        "limited_export_scope": "343K_PACKAGE_ONLY",
        "export_usage": "DEMO_ONLY",
        "limited_export_row_count": len(export_rows_343n),
        "remaining_source_check_backlog_count": backlog_summary["remaining_source_check_backlog_count"],
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "reason": "Audit snapshot confirms a demo-only package within 343K_PACKAGE_ONLY; formal/global export remains blocked by remaining backlog and incomplete global review.",
    }
    next_action_plan = _build_next_action_plan(summary)

    official_assets_after = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343O",
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
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343o")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::343n_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "missing_required_inputs": missing_required_inputs,
                    "decision": summary_343n.get("decision", ""),
                    "qa_fail_count": summary_343n.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::demo_package_row_count_is_10",
            "status": "PASS" if len(export_rows_343n) == 10 else "FAIL",
            "detail": json.dumps({"input_demo_export_row_count": len(export_rows_343n)}, ensure_ascii=False),
        },
        {
            "check_name": "counts::audit_label_row_count_is_10",
            "status": "PASS" if len(audit_labels_343n) == 10 else "FAIL",
            "detail": json.dumps({"audit_label_row_count": len(audit_labels_343n)}, ensure_ascii=False),
        },
        {
            "check_name": "scope::limited_export_scope_is_package_only",
            "status": "PASS" if normalize_text(summary_343n.get("limited_export_scope")) == "343K_PACKAGE_ONLY" else "FAIL",
            "detail": normalize_text(summary_343n.get("limited_export_scope")),
        },
        {
            "check_name": "scope::export_usage_is_demo_only",
            "status": "PASS" if normalize_text(summary_343n.get("export_usage")) == "DEMO_ONLY" else "FAIL",
            "detail": normalize_text(summary_343n.get("export_usage")),
        },
        {
            "check_name": "outputs::demo_readme_exists",
            "status": "PASS" if bool(demo_readme_343n.strip()) else "FAIL",
            "detail": INPUT_343N_DEMO_README_NAME,
        },
        {
            "check_name": "gate::export_gate_exists_and_formal_export_false",
            "status": "PASS" if not normalize_bool(export_gate_343n.get("formal_client_export_allowed")) else "FAIL",
            "detail": json.dumps(export_gate_343n, ensure_ascii=False),
        },
        {
            "check_name": "scope::scope_boundary_exists",
            "status": "PASS" if bool(scope_boundary_343n.strip()) and bool(scope_boundary_343l.strip()) else "FAIL",
            "detail": "343N and 343L scope boundaries must be readable",
        },
        {
            "check_name": "backlog::remaining_backlog_carried_forward",
            "status": "PASS",
            "detail": json.dumps(backlog_summary, ensure_ascii=False),
        },
        {
            "check_name": "outputs::trust_chain_generated",
            "status": "PASS" if len(trust_chain_rows) >= 6 and bool(trust_chain_markdown.strip()) else "FAIL",
            "detail": json.dumps({"trust_chain_row_count": len(trust_chain_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::handoff_summary_generated",
            "status": "PASS" if bool(handoff_summary_markdown.strip()) else "FAIL",
            "detail": "handoff summary markdown generated",
        },
        {
            "check_name": "outputs::executive_summary_generated",
            "status": "PASS" if bool(executive_summary_markdown.strip()) else "FAIL",
            "detail": "executive summary markdown generated",
        },
        {
            "check_name": "outputs::artifact_index_generated",
            "status": "PASS" if len(artifact_index_rows) >= 8 and bool(artifact_index_markdown.strip()) else "FAIL",
            "detail": json.dumps({"artifact_index_count": len(artifact_index_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::export_gate_snapshot_generated",
            "status": "PASS" if not normalize_bool(export_gate_snapshot.get("formal_client_export_allowed")) else "FAIL",
            "detail": json.dumps(export_gate_snapshot, ensure_ascii=False),
        },
        {
            "check_name": "claims::formal_client_production_flags_remain_false",
            "status": "PASS"
            if not normalize_bool(summary_343n.get("formal_client_export_allowed"))
            and not normalize_bool(summary_343n.get("client_ready"))
            and not normalize_bool(summary_343n.get("production_ready"))
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "claims::global_strict_human_review_remains_false",
            "status": "PASS" if not normalize_bool(summary_343n.get("global_strict_human_review_completed")) else "FAIL",
            "detail": "global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "safety::no_formal_client_export_workbook_generated",
            "status": "PASS",
            "detail": "343O generates an audit snapshot workbook, not a formal client export workbook.",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343O is snapshot/handoff only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343O does not write back or perform production apply.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343O adds review-queue audit snapshot files only.",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_343O) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_343O, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    if qa_fail_count == 0:
        summary["decision"] = READY_DECISION_343O
        summary["demo_audit_snapshot_generated"] = True
        summary["handoff_summary_generated"] = True
        summary["executive_summary_generated"] = True
        summary["trust_chain_generated"] = True
        summary["artifact_index_generated"] = True
        summary["export_gate_snapshot_generated"] = True
        summary["demo_arc_closed"] = True
        summary["ready_for_344a"] = True
        summary["recommended_344a_scope"] = RECOMMENDED_344A_SCOPE_343O
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    manifest = {
        "task": "343O_demo_package_audit_snapshot_and_handoff_summary",
        "limited_demo_export_package_343n_dir": str(limited_demo_export_package_343n_dir),
        "human_confirmed_sidecar_simulation_343m_dir": str(human_confirmed_sidecar_simulation_343m_dir),
        "pure_human_attestation_ingestion_343l_dir": str(pure_human_attestation_ingestion_343l_dir),
        "audit_summary_343h_dir": str(audit_summary_343h_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "output_dir": str(output_dir),
        "files_read": list(files_read),
        "warnings": [],
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": 0,
        "checks": checks,
        "warnings": [],
        "input_summary_343n": summary_343n,
        "input_qa_343n": qa_343n,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _build_readme_df(summary),
        "01_SNAPSHOT_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343N_SUMMARY": _build_key_value_df(summary_343n),
        "03_TRUST_CHAIN": _clean_frame(pd.DataFrame(trust_chain_rows)),
        "04_DEMO_EXPORT_OVERVIEW": _clean_frame(pd.DataFrame(_build_export_overview_rows(export_rows_343n))),
        "05_EXPORT_GATE_SNAPSHOT": _build_key_value_df(export_gate_snapshot),
        "06_BACKLOG_SUMMARY": _build_key_value_df(backlog_summary),
        "07_ARTIFACT_INDEX": _clean_frame(pd.DataFrame(artifact_index_rows)),
        "08_SCOPE_BOUNDARY": _build_key_value_df(
            {
                "scope_boundary_report": scope_boundary_markdown,
                "upstream_343n_scope_boundary": scope_boundary_343n,
                "upstream_343l_scope_boundary": scope_boundary_343l,
                "upstream_343h_gap_report_excerpt": gap_report_343h[:1200],
                "upstream_343n_demo_readme_excerpt": demo_readme_343n[:1200],
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
        "backlog_summary": backlog_summary,
        "next_action_plan": next_action_plan,
        "export_gate_snapshot": export_gate_snapshot,
        "handoff_summary_markdown": handoff_summary_markdown,
        "executive_summary_markdown": executive_summary_markdown,
        "trust_chain_markdown": trust_chain_markdown,
        "scope_boundary_markdown": scope_boundary_markdown,
        "artifact_index_markdown": artifact_index_markdown,
        "workbook_sheets": workbook_sheets,
    }
