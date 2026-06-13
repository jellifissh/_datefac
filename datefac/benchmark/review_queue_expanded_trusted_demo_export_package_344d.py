from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.expanded_trusted_demo_export_package_344d import (
    EXPANDED_EXPORT_SCOPE_344D,
    EXPORT_USAGE_344D,
    NOT_READY_DECISION_344D,
    READY_DECISION_344D,
    RECOMMENDED_344E_SCOPE_344D,
    build_audit_label_row,
    build_expanded_export_row,
    build_export_gate,
    build_lineage_summary,
    build_scope_boundary_lines,
)
from datefac.review_queue.ingest_strict_review_343j import PROTECTED_DIRTY_PATHS
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_344C_DECISION = "SOURCE_CHECK_SIDECAR_SIMULATION_344C_READY"
READY_INPUT_344B_DECISION = "SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_READY"
READY_INPUT_343O_DECISION = "DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_READY"
READY_INPUT_343A_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"

DEFAULT_SOURCE_CHECK_SIDECAR_SIMULATION_344C_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_sidecar_simulation_344c"
)
DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_evidence_review_ingestion_344b"
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
    r"D:\_datefac\output\review_queue_expanded_trusted_demo_export_package_344d"
)

SUMMARY_FILE_NAME = "review_queue_expanded_trusted_demo_export_package_344d_summary.json"
MANIFEST_FILE_NAME = "review_queue_expanded_trusted_demo_export_package_344d_manifest.json"
QA_FILE_NAME = "review_queue_expanded_trusted_demo_export_package_344d_qa.json"
NO_WRITE_BACK_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_no_write_back_proof.json"
)
REPORT_FILE_NAME = "review_queue_expanded_trusted_demo_export_package_344d_report.md"
WORKBOOK_FILE_NAME = "review_queue_expanded_trusted_demo_export_package_344d.xlsx"
DEMO_README_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_demo_readme.md"
)
EXPORT_ROWS_JSONL_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_export_rows.jsonl"
)
EXPORT_ROWS_CSV_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_export_rows.csv"
)
AUDIT_LABELS_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_audit_labels.jsonl"
)
EXPORT_GATE_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_export_gate.json"
)
LINEAGE_SUMMARY_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_lineage_summary.json"
)
SCOPE_BOUNDARY_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_scope_boundary.md"
)
HANDOFF_SUMMARY_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_handoff_summary.md"
)
METRIC_DISTRIBUTION_FILE_NAME = (
    "review_queue_expanded_trusted_demo_export_package_344d_metric_distribution.json"
)

INPUT_344C_SUMMARY_NAME = "review_queue_source_check_sidecar_simulation_344c_summary.json"
INPUT_344C_QA_NAME = "review_queue_source_check_sidecar_simulation_344c_qa.json"
INPUT_344C_CANDIDATES_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_expanded_trusted_candidates.jsonl"
)
INPUT_344C_APPLIED_SIDECAR_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_source_check_applied_sidecar.jsonl"
)
INPUT_344C_CORRECTIONS_APPLIED_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_corrections_applied.jsonl"
)
INPUT_344C_DEDUP_AUDIT_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_dedup_audit.jsonl"
)
INPUT_344C_GATE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_expanded_trust_gate.json"
)
INPUT_344C_SCOPE_BOUNDARY_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_scope_boundary.md"
)
INPUT_344C_NO_WRITE_BACK_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_no_write_back_proof.json"
)
INPUT_344B_SUMMARY_NAME = "review_queue_source_check_evidence_review_ingestion_344b_summary.json"
INPUT_344B_AUDIT_GATE_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_audit_gate.json"
)
INPUT_343O_SUMMARY_NAME = "review_queue_demo_audit_snapshot_343o_summary.json"
INPUT_343O_ARTIFACT_INDEX_NAME = "review_queue_demo_audit_snapshot_343o_artifact_index.json"
INPUT_343N_EXPORT_GATE_NAME = "review_queue_limited_demo_export_package_343n_export_gate.json"
INPUT_343A_SCHEMA_NAME = "review_queue_schema_343a_schema.json"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input/review_queue_source_check_evidence_344a2_filled",
    "input/review_queue_pure_human_attestation_343k_filled",
    "input/review_queue_strict_human_review_343i2_filled",
    "input/review_queue_spot_check_package_343f_filled",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

WORKBOOK_SHEETS_344D = [
    "00_README",
    "01_PACKAGE_SUMMARY",
    "02_INPUT_344C_SUMMARY",
    "03_EXPANDED_EXPORT_ROWS",
    "04_AUDIT_LABELS",
    "05_LINEAGE_SUMMARY",
    "06_EXPORT_GATE",
    "07_SCOPE_BOUNDARY",
    "08_NO_WRITE_BACK",
    "09_NEXT_STEPS",
]


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
                    "message": "344D packages 29 expanded trusted candidate rows for review/demo-only handoff.",
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


def _scope_boundary_markdown(lines: Iterable[str]) -> str:
    rendered = [
        "# 344D Scope Boundary",
        "",
        "## Chinese-first Summary",
    ]
    rendered.extend(f"- {line}" for line in lines)
    rendered.extend(
        [
            "",
            "## English Summary",
            "- 344D generates a 29-row expanded trusted export package for review/demo only.",
            "- It combines the 10-row demo arc and 19 source-check resolved rows.",
            "- It is not formal client export and not production ready.",
            "- No production write-back occurred.",
            "- The next safe task is 344E expanded trusted demo audit snapshot and final handoff summary.",
        ]
    )
    return "\n".join(rendered)


def _demo_readme_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 344D Expanded Trusted Review/Demo Package",
            "",
            "## 中文摘要",
            f"- 当前包包含 {summary.get('expanded_export_row_count', 0)} 条 reviewed trusted candidate rows。",
            "- 该包合并了 10 条 closed demo-arc rows 和 19 条 source-check resolved rows。",
            "- 该包仅用于 review/demo，不是 formal client export，也不是 production-ready。",
            "- 没有发生 production write-back。",
            "",
            "## English Summary",
            "- This package contains 29 reviewed trusted candidate rows.",
            "- It combines the 10-row demo arc and 19 source-check resolved rows.",
            "- It is review/demo only, not formal client export, and not production-ready.",
            "- No production write-back occurred.",
        ]
    )


def _handoff_summary_markdown(summary: Dict[str, Any], lineage_summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 344D Expanded Trusted Handoff Summary",
            "",
            "## Snapshot",
            f"- expanded_export_row_count: {summary.get('expanded_export_row_count', 0)}",
            f"- prior_demo_trusted_row_count: {lineage_summary.get('prior_demo_trusted_row_count', 0)}",
            f"- source_check_trusted_row_count: {lineage_summary.get('source_check_trusted_row_count', 0)}",
            f"- source_check_confirmed_row_count: {lineage_summary.get('source_check_confirmed_row_count', 0)}",
            f"- source_check_corrected_row_count: {lineage_summary.get('source_check_corrected_row_count', 0)}",
            f"- dedup_conflict_count: {summary.get('dedup_conflict_count', 0)}",
            "",
            "## Boundary",
            "- REVIEW_DEMO_ONLY",
            "- NOT_FORMAL_CLIENT_EXPORT",
            "- NOT_PRODUCTION_READY",
            "- NO_PRODUCTION_WRITE_BACK",
        ]
    )


def _metric_distribution(export_rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(export_rows)
    metric_counts: Dict[str, int] = {}
    lineage_counts: Dict[str, int] = {}
    for row in rows:
        metric = normalize_text(row.get("metric_standardized"))
        lineage = normalize_text(row.get("source_lineage_stage"))
        metric_counts[metric] = metric_counts.get(metric, 0) + 1
        lineage_counts[lineage] = lineage_counts.get(lineage, 0) + 1
    return {
        "metric_counts": metric_counts,
        "lineage_counts": lineage_counts,
    }


def _next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {
            "step": "open_package_workbook",
            "recommendation": "Review the 29-row expanded package workbook first for handoff/demo use.",
        },
        {
            "step": "check_export_rows",
            "recommendation": "Inspect export rows and audit labels together to verify review/demo-only boundary markers on every row.",
        },
        {
            "step": "check_lineage_gate",
            "recommendation": "Open lineage summary and export gate to confirm 10 + 19 composition and closed formal export gate.",
        },
        {
            "step": "next_task",
            "recommendation": summary.get("recommended_344e_scope", ""),
        },
    ]


def build_review_queue_expanded_trusted_demo_export_package_344d(
    *,
    source_check_sidecar_simulation_344c_dir: Path = DEFAULT_SOURCE_CHECK_SIDECAR_SIMULATION_344C_DIR,
    source_check_ingestion_344b_dir: Path = DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR,
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

    summary_344c_path = source_check_sidecar_simulation_344c_dir / INPUT_344C_SUMMARY_NAME
    qa_344c_path = source_check_sidecar_simulation_344c_dir / INPUT_344C_QA_NAME
    candidates_344c_path = source_check_sidecar_simulation_344c_dir / INPUT_344C_CANDIDATES_NAME
    applied_sidecar_344c_path = (
        source_check_sidecar_simulation_344c_dir / INPUT_344C_APPLIED_SIDECAR_NAME
    )
    corrections_applied_344c_path = (
        source_check_sidecar_simulation_344c_dir / INPUT_344C_CORRECTIONS_APPLIED_NAME
    )
    dedup_audit_344c_path = source_check_sidecar_simulation_344c_dir / INPUT_344C_DEDUP_AUDIT_NAME
    gate_344c_path = source_check_sidecar_simulation_344c_dir / INPUT_344C_GATE_NAME
    scope_boundary_344c_path = (
        source_check_sidecar_simulation_344c_dir / INPUT_344C_SCOPE_BOUNDARY_NAME
    )
    no_write_back_344c_path = (
        source_check_sidecar_simulation_344c_dir / INPUT_344C_NO_WRITE_BACK_NAME
    )
    summary_344b_path = source_check_ingestion_344b_dir / INPUT_344B_SUMMARY_NAME
    audit_gate_344b_path = source_check_ingestion_344b_dir / INPUT_344B_AUDIT_GATE_NAME
    summary_343o_path = demo_audit_snapshot_343o_dir / INPUT_343O_SUMMARY_NAME
    artifact_index_343o_path = demo_audit_snapshot_343o_dir / INPUT_343O_ARTIFACT_INDEX_NAME
    export_gate_343n_path = limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_GATE_NAME
    schema_343a_path = review_queue_schema_343a_dir / INPUT_343A_SCHEMA_NAME
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME

    files_read: List[str] = []
    warnings: List[str] = []
    required_input_paths = [
        summary_344c_path,
        qa_344c_path,
        candidates_344c_path,
        applied_sidecar_344c_path,
        corrections_applied_344c_path,
        dedup_audit_344c_path,
        gate_344c_path,
        scope_boundary_344c_path,
        no_write_back_344c_path,
        summary_344b_path,
        audit_gate_344b_path,
        summary_343o_path,
        artifact_index_343o_path,
        export_gate_343n_path,
        schema_343a_path,
        summary_343a_path,
    ]
    missing_required_inputs = [str(path) for path in required_input_paths if not path.exists()]
    for path in required_input_paths:
        if path.exists():
            files_read.append(str(path))

    summary_344c = _read_json(summary_344c_path) if summary_344c_path.exists() else {}
    qa_344c = _read_json(qa_344c_path) if qa_344c_path.exists() else {}
    candidates_344c = _read_jsonl(candidates_344c_path) if candidates_344c_path.exists() else []
    applied_sidecar_344c = (
        _read_jsonl(applied_sidecar_344c_path) if applied_sidecar_344c_path.exists() else []
    )
    corrections_applied_344c = (
        _read_jsonl(corrections_applied_344c_path)
        if corrections_applied_344c_path.exists()
        else []
    )
    dedup_audit_344c = (
        _read_jsonl(dedup_audit_344c_path) if dedup_audit_344c_path.exists() else []
    )
    gate_344c = _read_json(gate_344c_path) if gate_344c_path.exists() else {}
    scope_boundary_344c = (
        _read_text(scope_boundary_344c_path) if scope_boundary_344c_path.exists() else ""
    )
    no_write_back_344c = (
        _read_json(no_write_back_344c_path) if no_write_back_344c_path.exists() else {}
    )
    summary_344b = _read_json(summary_344b_path) if summary_344b_path.exists() else {}
    audit_gate_344b = (
        _read_json(audit_gate_344b_path) if audit_gate_344b_path.exists() else {}
    )
    summary_343o = _read_json(summary_343o_path) if summary_343o_path.exists() else {}
    artifact_index_343o = (
        _read_json(artifact_index_343o_path) if artifact_index_343o_path.exists() else []
    )
    export_gate_343n = (
        _read_json(export_gate_343n_path) if export_gate_343n_path.exists() else {}
    )
    schema_343a = _read_json(schema_343a_path) if schema_343a_path.exists() else {}
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}

    input_hashes_before = {
        str(path): sha256_file(path) for path in required_input_paths if path.exists()
    }

    dedup_conflicts_detected = [
        row
        for row in dedup_audit_344c
        if normalize_text(row.get("dedup_status")) not in {"", "UNIQUE"}
    ]
    input_ready = bool(
        not missing_required_inputs
        and summary_344c.get("decision") == READY_INPUT_344C_DECISION
        and summary_344b.get("decision") == READY_INPUT_344B_DECISION
        and summary_343o.get("decision") == READY_INPUT_343O_DECISION
        and summary_343a.get("decision") == READY_INPUT_343A_DECISION
        and int(summary_344c.get("qa_fail_count", 1)) == 0
        and int(summary_344b.get("qa_fail_count", 1)) == 0
        and int(summary_343o.get("qa_fail_count", 1)) == 0
        and int(summary_343a.get("qa_fail_count", 1)) == 0
        and int(summary_344c.get("expanded_trusted_candidate_count", 0)) == 29
        and int(summary_344c.get("deduplicated_expanded_trusted_candidate_count", 0)) == 29
        and int(summary_344c.get("dedup_conflict_count", -1)) == 0
        and len(candidates_344c) == 29
        and not dedup_conflicts_detected
        and normalize_bool(summary_344c.get("source_check_sidecar_apply_simulation_completed"))
        and normalize_bool(summary_344c.get("expanded_trust_gate_evaluated"))
        and normalize_bool(summary_344c.get("source_check_backlog_resolved"))
        and normalize_bool(summary_344c.get("ready_for_344d"))
        and normalize_text(summary_344c.get("expanded_trusted_scope")) == EXPANDED_EXPORT_SCOPE_344D
        and not normalize_bool(summary_344c.get("formal_client_export_allowed"))
        and not normalize_bool(summary_344c.get("client_ready"))
        and not normalize_bool(summary_344c.get("production_ready"))
        and not normalize_bool(summary_344c.get("global_strict_human_review_completed"))
        and not normalize_bool(export_gate_343n.get("formal_client_export_allowed"))
    )

    export_rows = [build_expanded_export_row(row) for row in candidates_344c]
    audit_label_rows = [build_audit_label_row(row) for row in export_rows]
    lineage_summary = build_lineage_summary(export_rows)
    metric_distribution = _metric_distribution(export_rows)

    input_expanded_trusted_candidate_count = len(candidates_344c)
    expanded_export_row_count = len(export_rows)
    audit_label_row_count = len(audit_label_rows)
    prior_demo_trusted_row_count = int(lineage_summary.get("prior_demo_trusted_row_count", 0))
    source_check_trusted_row_count = int(
        lineage_summary.get("source_check_trusted_row_count", 0)
    )
    source_check_confirmed_row_count = int(
        lineage_summary.get("source_check_confirmed_row_count", 0)
    )
    source_check_corrected_row_count = int(
        lineage_summary.get("source_check_corrected_row_count", 0)
    )
    correction_row_count = int(lineage_summary.get("correction_row_count", 0))
    dedup_conflict_count = int(summary_344c.get("dedup_conflict_count", 0))

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "344C",
        "decision": NOT_READY_DECISION_344D,
        "review_queue_schema_version": summary_344c.get(
            "review_queue_schema_version",
            summary_343a.get("review_queue_schema_version", ""),
        ),
        "input_expanded_trusted_candidate_count": input_expanded_trusted_candidate_count,
        "expanded_export_row_count": expanded_export_row_count,
        "audit_label_row_count": audit_label_row_count,
        "prior_demo_trusted_row_count": prior_demo_trusted_row_count,
        "source_check_trusted_row_count": source_check_trusted_row_count,
        "source_check_confirmed_row_count": source_check_confirmed_row_count,
        "source_check_corrected_row_count": source_check_corrected_row_count,
        "correction_row_count": correction_row_count,
        "dedup_conflict_count": dedup_conflict_count,
        "expanded_export_scope": EXPANDED_EXPORT_SCOPE_344D,
        "export_usage": EXPORT_USAGE_344D,
        "source_check_backlog_resolved": bool(summary_344c.get("source_check_backlog_resolved")),
        "expanded_review_demo_package_generated": False,
        "expanded_demo_handoff_ready": False,
        "expanded_export_gate_generated": False,
        "lineage_summary_generated": False,
        "audit_labels_generated": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "ready_for_344e": False,
        "recommended_344e_scope": "",
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {
        str(path): sha256_file(path) for path in required_input_paths if path.exists()
    }
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="344D",
        files_read=list(dict.fromkeys(files_read)),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["expanded_review_demo_package_generated"] = (
        expanded_export_row_count == 29 and audit_label_row_count == 29
    )
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_344d")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    labels_have_review_demo_flags = all(
        set(row.get("audit_labels", []))
        >= {
            "EXPANDED_TRUSTED_CANDIDATE",
            "REVIEW_DEMO_ONLY",
            "NOT_FORMAL_CLIENT_EXPORT",
            "NOT_PRODUCTION_READY",
            "NO_PRODUCTION_WRITE_BACK",
        }
        for row in audit_label_rows
    )
    corrected_semantics_ok = all(
        normalize_text(row.get("metric_standardized")) == "YOY"
        and normalize_text(row.get("normalized_unit")) == "%"
        for row in export_rows
        if normalize_text(row.get("source_check_status")) == "CORRECTED"
    )
    corrected_row_count_matches_input = correction_row_count == len(corrections_applied_344c) == 9
    applied_sidecar_count_matches = len(applied_sidecar_344c) == 19

    checks = [
        {
            "check_name": "inputs::344c_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "missing_required_inputs": missing_required_inputs,
                    "decision_344c": summary_344c.get("decision", ""),
                    "decision_344b": summary_344b.get("decision", ""),
                    "decision_343o": summary_343o.get("decision", ""),
                    "decision_343a": summary_343a.get("decision", ""),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::expanded_trusted_candidates_file_has_29_rows",
            "status": "PASS" if input_expanded_trusted_candidate_count == 29 else "FAIL",
            "detail": json.dumps(
                {"input_expanded_trusted_candidate_count": input_expanded_trusted_candidate_count},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "validation::no_dedup_conflicts_exist",
            "status": "PASS" if dedup_conflict_count == 0 and not dedup_conflicts_detected else "FAIL",
            "detail": json.dumps(
                {
                    "dedup_conflict_count": dedup_conflict_count,
                    "dedup_conflicts_detected": len(dedup_conflicts_detected),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::expanded_export_rows_count_is_29",
            "status": "PASS" if expanded_export_row_count == 29 else "FAIL",
            "detail": json.dumps({"expanded_export_row_count": expanded_export_row_count}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::audit_labels_count_is_29",
            "status": "PASS" if audit_label_row_count == 29 else "FAIL",
            "detail": json.dumps({"audit_label_row_count": audit_label_row_count}, ensure_ascii=False),
        },
        {
            "check_name": "validation::every_export_row_has_review_demo_only_labels",
            "status": "PASS" if labels_have_review_demo_flags else "FAIL",
            "detail": "Every row must visibly carry review/demo-only and not-formal-export labels.",
        },
        {
            "check_name": "outputs::lineage_summary_matches_10_plus_19",
            "status": "PASS"
            if prior_demo_trusted_row_count == 10
            and source_check_trusted_row_count == 19
            and expanded_export_row_count == 29
            else "FAIL",
            "detail": json.dumps(lineage_summary, ensure_ascii=False),
        },
        {
            "check_name": "validation::corrected_rows_preserve_yoy_percent_semantics",
            "status": "PASS"
            if corrected_semantics_ok and corrected_row_count_matches_input
            else "FAIL",
            "detail": json.dumps(
                {
                    "source_check_corrected_row_count": source_check_corrected_row_count,
                    "correction_row_count": correction_row_count,
                    "corrections_applied_input_count": len(corrections_applied_344c),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "validation::applied_sidecar_count_matches_19",
            "status": "PASS" if applied_sidecar_count_matches else "FAIL",
            "detail": json.dumps(
                {"applied_sidecar_row_count": len(applied_sidecar_344c)},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::export_gate_generated",
            "status": "PASS"
            if expanded_export_row_count == 29 and audit_label_row_count == 29
            else "FAIL",
            "detail": "Export gate can be generated only after successful expanded package assembly.",
        },
        {
            "check_name": "claims::formal_client_export_gate_remains_false",
            "status": "PASS"
            if not summary["formal_client_export_allowed"]
            and not summary["client_ready"]
            and not summary["production_ready"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "claims::global_strict_human_review_completed_false",
            "status": "PASS"
            if not summary["global_strict_human_review_completed"]
            else "FAIL",
            "detail": "global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "safety::no_formal_client_export_workbook_generated",
            "status": "PASS",
            "detail": "344D generates only review/demo-only expanded package artifacts.",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "344D is package generation only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "344D does not write back to upstream production data.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "344D adds review-queue package files only.",
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
            "status": "PASS"
            if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_344D)
            else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_344D, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {"no_write_back_proof_passed": no_write_back_proof_passed},
                ensure_ascii=False,
            ),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed
    summary["expanded_review_demo_package_generated"] = bool(
        expanded_export_row_count == 29 and qa_fail_count == 0
    )
    summary["expanded_demo_handoff_ready"] = bool(
        expanded_export_row_count == 29 and qa_fail_count == 0
    )
    summary["expanded_export_gate_generated"] = bool(
        expanded_export_row_count == 29 and qa_fail_count == 0
    )
    summary["lineage_summary_generated"] = bool(lineage_summary and qa_fail_count == 0)
    summary["audit_labels_generated"] = bool(audit_label_row_count == 29 and qa_fail_count == 0)
    summary["ready_for_344e"] = bool(summary["expanded_review_demo_package_generated"] and qa_fail_count == 0)
    summary["recommended_344e_scope"] = (
        RECOMMENDED_344E_SCOPE_344D if summary["ready_for_344e"] else ""
    )
    summary["decision"] = READY_DECISION_344D if summary["ready_for_344e"] else NOT_READY_DECISION_344D

    export_gate = build_export_gate(summary)
    scope_boundary_markdown = _scope_boundary_markdown(build_scope_boundary_lines())
    demo_readme_markdown = _demo_readme_markdown(summary)
    handoff_summary_markdown = _handoff_summary_markdown(summary, lineage_summary)

    manifest = {
        "task": "344D_expanded_trusted_export_package_generation_for_review_demo_only",
        "source_check_sidecar_simulation_344c_dir": str(source_check_sidecar_simulation_344c_dir),
        "source_check_ingestion_344b_dir": str(source_check_ingestion_344b_dir),
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
            "demo_readme_md": str(output_dir / DEMO_README_FILE_NAME),
            "export_rows_jsonl": str(output_dir / EXPORT_ROWS_JSONL_FILE_NAME),
            "export_rows_csv": str(output_dir / EXPORT_ROWS_CSV_FILE_NAME),
            "audit_labels_jsonl": str(output_dir / AUDIT_LABELS_FILE_NAME),
            "export_gate_json": str(output_dir / EXPORT_GATE_FILE_NAME),
            "lineage_summary_json": str(output_dir / LINEAGE_SUMMARY_FILE_NAME),
            "scope_boundary_md": str(output_dir / SCOPE_BOUNDARY_FILE_NAME),
            "handoff_summary_md": str(output_dir / HANDOFF_SUMMARY_FILE_NAME),
            "metric_distribution_json": str(output_dir / METRIC_DISTRIBUTION_FILE_NAME),
        },
        "files_read": list(dict.fromkeys(files_read)),
        "warnings": warnings,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "input_summary_344c": summary_344c,
        "input_qa_344c": qa_344c,
        "input_gate_344c": gate_344c,
        "input_summary_344b": summary_344b,
        "input_audit_gate_344b": audit_gate_344b,
        "input_summary_343o": summary_343o,
        "input_artifact_index_343o": artifact_index_343o,
        "input_export_gate_343n": export_gate_343n,
        "input_schema_343a": schema_343a,
        "input_scope_boundary_344c": scope_boundary_344c,
        "input_no_write_back_344c": no_write_back_344c,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _build_readme_df(summary),
        "01_PACKAGE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_344C_SUMMARY": _build_key_value_df(summary_344c),
        "03_EXPANDED_EXPORT_ROWS": _clean_frame(pd.DataFrame(export_rows)),
        "04_AUDIT_LABELS": _clean_frame(pd.DataFrame(audit_label_rows)),
        "05_LINEAGE_SUMMARY": _build_key_value_df(lineage_summary),
        "06_EXPORT_GATE": _build_key_value_df(export_gate),
        "07_SCOPE_BOUNDARY": _build_key_value_df(
            {
                "scope_boundary_report": scope_boundary_markdown,
                "upstream_344c_scope_boundary": scope_boundary_344c,
                "upstream_343o_summary": summary_343o,
                "upstream_343n_export_gate": export_gate_343n,
            }
        ),
        "08_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "09_NEXT_STEPS": _clean_frame(pd.DataFrame(_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "demo_readme_markdown": demo_readme_markdown,
        "export_rows": export_rows,
        "audit_label_rows": audit_label_rows,
        "export_gate": export_gate,
        "lineage_summary": lineage_summary,
        "scope_boundary_markdown": scope_boundary_markdown,
        "handoff_summary_markdown": handoff_summary_markdown,
        "metric_distribution": metric_distribution,
        "workbook_sheets": workbook_sheets,
    }
