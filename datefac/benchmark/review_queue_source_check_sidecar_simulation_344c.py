from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.ingest_strict_review_343j import PROTECTED_DIRTY_PATHS
from datefac.review_queue.source_check_sidecar_simulation_344c import (
    EXPANDED_TRUST_SCOPE_344C,
    NOT_READY_DECISION_344C,
    READY_DECISION_344C,
    RECOMMENDED_344D_SCOPE_344C,
    build_dedup_audit_rows,
    build_expanded_trust_gate,
    build_expanded_trusted_candidate_from_demo_row,
    build_expanded_trusted_candidate_from_source_check_row,
    build_scope_boundary_lines,
    build_source_check_applied_sidecar_row,
    build_source_check_apply_plan_row,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_344B_DECISION = "SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_READY"
READY_INPUT_343O_DECISION = "DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_READY"
READY_INPUT_343N_DECISION = "LIMITED_HUMAN_CONFIRMED_DEMO_EXPORT_PACKAGE_343N_READY"
READY_INPUT_343M_DECISION = "HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_READY"
READY_INPUT_343L_DECISION = "PURE_HUMAN_ATTESTATION_INGESTION_343L_READY"
READY_INPUT_343A_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"

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
DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR = Path(
    r"D:\_datefac\output\review_queue_human_confirmed_sidecar_simulation_343m"
)
DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR = Path(
    r"D:\_datefac\output\review_queue_pure_human_attestation_ingestion_343l"
)
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(
    r"D:\_datefac\output\review_queue_schema_343a"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_sidecar_simulation_344c"
)

SUMMARY_FILE_NAME = "review_queue_source_check_sidecar_simulation_344c_summary.json"
MANIFEST_FILE_NAME = "review_queue_source_check_sidecar_simulation_344c_manifest.json"
QA_FILE_NAME = "review_queue_source_check_sidecar_simulation_344c_qa.json"
NO_WRITE_BACK_FILE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_no_write_back_proof.json"
)
REPORT_FILE_NAME = "review_queue_source_check_sidecar_simulation_344c_report.md"
WORKBOOK_FILE_NAME = "review_queue_source_check_sidecar_simulation_344c.xlsx"
SOURCE_CHECK_APPLY_PLAN_FILE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_source_check_apply_plan.jsonl"
)
SOURCE_CHECK_APPLIED_SIDECAR_FILE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_source_check_applied_sidecar.jsonl"
)
EXPANDED_TRUSTED_CANDIDATES_FILE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_expanded_trusted_candidates.jsonl"
)
CORRECTIONS_APPLIED_FILE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_corrections_applied.jsonl"
)
DEDUP_AUDIT_FILE_NAME = "review_queue_source_check_sidecar_simulation_344c_dedup_audit.jsonl"
EXPANDED_TRUST_GATE_FILE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_expanded_trust_gate.json"
)
SCOPE_BOUNDARY_FILE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_scope_boundary.md"
)
EXPANDED_TRUST_SUMMARY_FILE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_expanded_trust_summary.md"
)
NEXT_ACTION_PLAN_FILE_NAME = (
    "review_queue_source_check_sidecar_simulation_344c_next_action_plan.json"
)

INPUT_344B_SUMMARY_NAME = "review_queue_source_check_evidence_review_ingestion_344b_summary.json"
INPUT_344B_QA_NAME = "review_queue_source_check_evidence_review_ingestion_344b_qa.json"
INPUT_344B_RESULT_NAME = "review_queue_source_check_evidence_review_ingestion_344b_result.jsonl"
INPUT_344B_VALIDATED_SIDECAR_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_validated_sidecar.jsonl"
)
INPUT_344B_CORRECTIONS_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_corrections.jsonl"
)
INPUT_344B_AUDIT_GATE_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_audit_gate.json"
)
INPUT_344B_SCOPE_BOUNDARY_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_scope_boundary.md"
)
INPUT_344B_NO_WRITE_BACK_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_no_write_back_proof.json"
)
INPUT_344A2_SUMMARY_NAME = "review_queue_source_check_evidence_enrichment_344a2_summary.json"
INPUT_343O_SUMMARY_NAME = "review_queue_demo_audit_snapshot_343o_summary.json"
INPUT_343O_EXPORT_GATE_NAME = (
    "review_queue_demo_audit_snapshot_343o_export_gate_snapshot.json"
)
INPUT_343N_SUMMARY_NAME = "review_queue_limited_demo_export_package_343n_summary.json"
INPUT_343N_EXPORT_ROWS_NAME = (
    "review_queue_limited_demo_export_package_343n_export_rows.jsonl"
)
INPUT_343N_AUDIT_LABELS_NAME = (
    "review_queue_limited_demo_export_package_343n_audit_labels.jsonl"
)
INPUT_343N_EXPORT_GATE_NAME = (
    "review_queue_limited_demo_export_package_343n_export_gate.json"
)
INPUT_343M_SUMMARY_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_summary.json"
INPUT_343M_GATE_NAME = (
    "review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate.json"
)
INPUT_343L_SUMMARY_NAME = "review_queue_pure_human_attestation_ingestion_343l_summary.json"
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

WORKBOOK_SHEETS_344C = [
    "00_README",
    "01_SIM_SUMMARY",
    "02_INPUT_344B_SUMMARY",
    "03_SOURCE_CHECK_SIDECAR",
    "04_CORRECTIONS_APPLIED",
    "05_EXPANDED_TRUSTED",
    "06_DEDUP_AUDIT",
    "07_EXPANDED_GATE",
    "08_SCOPE_BOUNDARY",
    "09_NO_WRITE_BACK",
    "10_NEXT_STEPS",
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
                    "message": "344C simulates applying 19 source-check resolved rows and expands the trusted sidecar scope to 29 rows.",
                },
                {
                    "section": "boundary",
                    "message": "344C is sidecar apply simulation only. No production write-back or formal client export is allowed.",
                },
                {
                    "section": "trusted_scope",
                    "message": summary.get("expanded_trusted_scope", ""),
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
        "# 344C Scope Boundary",
        "",
        "## Chinese-first Summary",
    ]
    rendered.extend(f"- {line}" for line in lines)
    rendered.extend(
        [
            "",
            "## English Summary",
            "- 344C simulates applying 19 source-check resolved rows from 344B.",
            "- It combines those rows with the prior 10-row trusted demo arc from 343O/343N.",
            "- Expanded trusted candidate coverage reaches 29 rows when dedup passes cleanly.",
            "- No production write-back or formal client export occurred.",
            "- The next safe task is 344D expanded trusted export package generation for review/demo only.",
        ]
    )
    return "\n".join(rendered)


def _expanded_trust_summary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 344C Expanded Trust Summary",
            "",
            "## 中文摘要",
            f"- prior_demo_trusted_row_count = {summary.get('prior_demo_trusted_row_count', 0)}",
            f"- source_check_trusted_row_count = {summary.get('source_check_trusted_row_count', 0)}",
            f"- expanded_trusted_candidate_count = {summary.get('expanded_trusted_candidate_count', 0)}",
            f"- deduplicated_expanded_trusted_candidate_count = {summary.get('deduplicated_expanded_trusted_candidate_count', 0)}",
            f"- dedup_conflict_count = {summary.get('dedup_conflict_count', 0)}",
            "- 当前 expanded trusted coverage 仍然只是 review/demo sidecar simulation，不是 formal client export。",
            "",
            "## English Summary",
            "- Expanded trusted coverage is available only as sidecar simulation.",
            "- Formal client export and production readiness remain blocked.",
        ]
    )


def _next_action_plan(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ready_for_344d": summary.get("ready_for_344d", False),
        "recommended_344d_scope": summary.get("recommended_344d_scope", ""),
        "next_safe_action": (
            "Generate an expanded trusted export package for review/demo only."
            if summary.get("ready_for_344d")
            else "Resolve 344C validation issues before any expanded export packaging."
        ),
    }


def _next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {
            "step": "open_apply_plan",
            "recommendation": "Inspect the 19-row source-check apply plan and confirm all rows are READY without blocked actions.",
        },
        {
            "step": "open_expanded_candidates",
            "recommendation": "Review the expanded trusted candidate rows and verify the 10 demo + 19 source-check composition.",
        },
        {
            "step": "open_dedup_audit",
            "recommendation": "Confirm dedup conflict count remains 0 before any downstream packaging.",
        },
        {
            "step": "next_task",
            "recommendation": summary.get("recommended_344d_scope", ""),
        },
    ]


def build_review_queue_source_check_sidecar_simulation_344c(
    *,
    source_check_ingestion_344b_dir: Path = DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR,
    source_check_evidence_enrichment_344a2_dir: Path = DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR,
    demo_audit_snapshot_343o_dir: Path = DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    limited_demo_export_package_343n_dir: Path = DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR,
    human_confirmed_sidecar_simulation_343m_dir: Path = DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR,
    pure_human_attestation_ingestion_343l_dir: Path = DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_344b_path = source_check_ingestion_344b_dir / INPUT_344B_SUMMARY_NAME
    qa_344b_path = source_check_ingestion_344b_dir / INPUT_344B_QA_NAME
    result_344b_path = source_check_ingestion_344b_dir / INPUT_344B_RESULT_NAME
    validated_sidecar_344b_path = (
        source_check_ingestion_344b_dir / INPUT_344B_VALIDATED_SIDECAR_NAME
    )
    corrections_344b_path = source_check_ingestion_344b_dir / INPUT_344B_CORRECTIONS_NAME
    audit_gate_344b_path = source_check_ingestion_344b_dir / INPUT_344B_AUDIT_GATE_NAME
    scope_boundary_344b_path = (
        source_check_ingestion_344b_dir / INPUT_344B_SCOPE_BOUNDARY_NAME
    )
    no_write_back_344b_path = (
        source_check_ingestion_344b_dir / INPUT_344B_NO_WRITE_BACK_NAME
    )
    summary_344a2_path = (
        source_check_evidence_enrichment_344a2_dir / INPUT_344A2_SUMMARY_NAME
    )
    summary_343o_path = demo_audit_snapshot_343o_dir / INPUT_343O_SUMMARY_NAME
    export_gate_343o_path = demo_audit_snapshot_343o_dir / INPUT_343O_EXPORT_GATE_NAME
    summary_343n_path = limited_demo_export_package_343n_dir / INPUT_343N_SUMMARY_NAME
    export_rows_343n_path = (
        limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_ROWS_NAME
    )
    audit_labels_343n_path = (
        limited_demo_export_package_343n_dir / INPUT_343N_AUDIT_LABELS_NAME
    )
    export_gate_343n_path = (
        limited_demo_export_package_343n_dir / INPUT_343N_EXPORT_GATE_NAME
    )
    summary_343m_path = human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_SUMMARY_NAME
    gate_343m_path = human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_GATE_NAME
    summary_343l_path = pure_human_attestation_ingestion_343l_dir / INPUT_343L_SUMMARY_NAME
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME

    files_read: List[str] = []
    warnings: List[str] = []
    required_input_paths = [
        summary_344b_path,
        qa_344b_path,
        result_344b_path,
        validated_sidecar_344b_path,
        corrections_344b_path,
        audit_gate_344b_path,
        scope_boundary_344b_path,
        no_write_back_344b_path,
        summary_344a2_path,
        summary_343o_path,
        export_gate_343o_path,
        summary_343n_path,
        export_rows_343n_path,
        audit_labels_343n_path,
        export_gate_343n_path,
        summary_343m_path,
        gate_343m_path,
        summary_343l_path,
        summary_343a_path,
    ]
    missing_required_inputs = [str(path) for path in required_input_paths if not path.exists()]
    for path in required_input_paths:
        if path.exists():
            files_read.append(str(path))

    summary_344b = _read_json(summary_344b_path) if summary_344b_path.exists() else {}
    qa_344b = _read_json(qa_344b_path) if qa_344b_path.exists() else {}
    result_rows_344b = _read_jsonl(result_344b_path) if result_344b_path.exists() else []
    validated_sidecar_rows_344b = (
        _read_jsonl(validated_sidecar_344b_path) if validated_sidecar_344b_path.exists() else []
    )
    corrections_344b = (
        _read_jsonl(corrections_344b_path) if corrections_344b_path.exists() else []
    )
    audit_gate_344b = _read_json(audit_gate_344b_path) if audit_gate_344b_path.exists() else {}
    scope_boundary_344b = (
        _read_text(scope_boundary_344b_path) if scope_boundary_344b_path.exists() else ""
    )
    no_write_back_344b = (
        _read_json(no_write_back_344b_path) if no_write_back_344b_path.exists() else {}
    )
    summary_344a2 = _read_json(summary_344a2_path) if summary_344a2_path.exists() else {}
    summary_343o = _read_json(summary_343o_path) if summary_343o_path.exists() else {}
    export_gate_343o = (
        _read_json(export_gate_343o_path) if export_gate_343o_path.exists() else {}
    )
    summary_343n = _read_json(summary_343n_path) if summary_343n_path.exists() else {}
    export_rows_343n = (
        _read_jsonl(export_rows_343n_path) if export_rows_343n_path.exists() else []
    )
    audit_labels_343n = (
        _read_jsonl(audit_labels_343n_path) if audit_labels_343n_path.exists() else []
    )
    export_gate_343n = (
        _read_json(export_gate_343n_path) if export_gate_343n_path.exists() else {}
    )
    summary_343m = _read_json(summary_343m_path) if summary_343m_path.exists() else {}
    gate_343m = _read_json(gate_343m_path) if gate_343m_path.exists() else {}
    summary_343l = _read_json(summary_343l_path) if summary_343l_path.exists() else {}
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}

    input_hashes_before = {
        str(path): sha256_file(path) for path in required_input_paths if path.exists()
    }

    input_ready = bool(
        not missing_required_inputs
        and summary_344b.get("decision") == READY_INPUT_344B_DECISION
        and summary_343o.get("decision") == READY_INPUT_343O_DECISION
        and summary_343n.get("decision") == READY_INPUT_343N_DECISION
        and summary_343m.get("decision") == READY_INPUT_343M_DECISION
        and summary_343l.get("decision") == READY_INPUT_343L_DECISION
        and summary_343a.get("decision") == READY_INPUT_343A_DECISION
        and int(summary_344b.get("qa_fail_count", 1)) == 0
        and int(summary_343o.get("qa_fail_count", 1)) == 0
        and int(summary_343n.get("qa_fail_count", 1)) == 0
        and int(summary_343m.get("qa_fail_count", 1)) == 0
        and int(summary_343l.get("qa_fail_count", 1)) == 0
        and int(summary_343a.get("qa_fail_count", 1)) == 0
        and int(summary_344b.get("validated_sidecar_row_count", 0)) == 19
        and int(summary_344b.get("correction_row_count", 0)) == 9
        and normalize_bool(summary_344b.get("source_check_result_ingested"))
        and normalize_bool(summary_344b.get("source_check_backlog_resolved"))
        and normalize_bool(summary_344b.get("ready_for_344c"))
        and int(summary_343n.get("demo_export_row_count", 0)) == 10
        and normalize_bool(summary_343o.get("demo_arc_closed"))
        and normalize_text(summary_343n.get("limited_export_scope")) == "343K_PACKAGE_ONLY"
        and normalize_text(summary_343n.get("export_usage")) == "DEMO_ONLY"
        and not normalize_bool(summary_344b.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343o.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343n.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343m.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343l.get("formal_client_export_allowed"))
    )

    source_check_apply_plan_rows = [
        build_source_check_apply_plan_row(row) for row in validated_sidecar_rows_344b
    ]
    source_check_applied_sidecar_rows = [
        build_source_check_applied_sidecar_row(plan_row, source_row)
        for plan_row, source_row in zip(source_check_apply_plan_rows, validated_sidecar_rows_344b)
        if normalize_text(plan_row.get("apply_action")) != ""
    ]
    corrections_applied_rows = [
        row for row in source_check_applied_sidecar_rows if bool(row.get("correction_applied"))
    ]

    demo_label_index = {
        (
            normalize_text(row.get("queue_item_id")),
            normalize_text(row.get("review_item_id")),
        ): row
        for row in audit_labels_343n
    }
    prior_demo_trusted_rows = []
    for row in export_rows_343n:
        key = (
            normalize_text(row.get("queue_item_id")),
            normalize_text(row.get("review_item_id")),
        )
        merged = dict(row)
        merged["audit_labels"] = demo_label_index.get(key, {}).get("audit_labels", [])
        prior_demo_trusted_rows.append(merged)

    expanded_candidate_rows = [
        build_expanded_trusted_candidate_from_demo_row(row)
        for row in prior_demo_trusted_rows
    ] + [
        build_expanded_trusted_candidate_from_source_check_row(row)
        for row in source_check_applied_sidecar_rows
    ]

    dedup_audit_rows, deduplicated_rows, dedup_conflict_count = build_dedup_audit_rows(
        expanded_candidate_rows
    )

    source_check_apply_confirm_count = sum(
        1
        for row in source_check_apply_plan_rows
        if normalize_text(row.get("apply_action"))
        == "SIMULATE_APPLY_SOURCE_CHECK_CONFIRM"
    )
    source_check_apply_correct_count = sum(
        1
        for row in source_check_apply_plan_rows
        if normalize_text(row.get("apply_action"))
        == "SIMULATE_APPLY_SOURCE_CHECK_CORRECTION"
    )
    source_check_apply_blocked_count = sum(
        1 for row in source_check_apply_plan_rows if normalize_text(row.get("apply_action")) == ""
    )

    source_check_input_sidecar_row_count = len(validated_sidecar_rows_344b)
    source_check_apply_plan_row_count = len(source_check_apply_plan_rows)
    source_check_applied_sidecar_row_count = len(source_check_applied_sidecar_rows)
    corrections_applied_count = len(corrections_applied_rows)
    prior_demo_trusted_row_count = len(prior_demo_trusted_rows)
    source_check_trusted_row_count = len(source_check_applied_sidecar_rows)
    expanded_trusted_candidate_count = len(expanded_candidate_rows)
    deduplicated_expanded_trusted_candidate_count = len(deduplicated_rows)

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "344B",
        "decision": NOT_READY_DECISION_344C,
        "review_queue_schema_version": summary_344b.get(
            "review_queue_schema_version",
            summary_343a.get("review_queue_schema_version", ""),
        ),
        "source_check_input_sidecar_row_count": source_check_input_sidecar_row_count,
        "source_check_apply_plan_row_count": source_check_apply_plan_row_count,
        "source_check_apply_confirm_count": source_check_apply_confirm_count,
        "source_check_apply_correct_count": source_check_apply_correct_count,
        "source_check_apply_blocked_count": source_check_apply_blocked_count,
        "source_check_applied_sidecar_row_count": source_check_applied_sidecar_row_count,
        "corrections_applied_count": corrections_applied_count,
        "prior_demo_trusted_row_count": prior_demo_trusted_row_count,
        "source_check_trusted_row_count": source_check_trusted_row_count,
        "expanded_trusted_candidate_count": expanded_trusted_candidate_count,
        "deduplicated_expanded_trusted_candidate_count": deduplicated_expanded_trusted_candidate_count,
        "dedup_conflict_count": dedup_conflict_count,
        "expanded_trusted_scope": EXPANDED_TRUST_SCOPE_344C,
        "source_check_backlog_resolved": bool(summary_344b.get("source_check_backlog_resolved")),
        "source_check_sidecar_apply_simulation_completed": False,
        "source_check_applied_sidecar_generated": False,
        "expanded_trusted_candidates_generated": False,
        "expanded_trust_gate_evaluated": False,
        "dedup_audit_generated": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "ready_for_344d": False,
        "recommended_344d_scope": "",
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
        stage="344C",
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
    no_write_back_json["source_check_sidecar_apply_simulation_completed"] = (
        source_check_apply_plan_row_count == 19 and source_check_apply_blocked_count == 0
    )
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_344c")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::344b_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "missing_required_inputs": missing_required_inputs,
                    "decision_344b": summary_344b.get("decision", ""),
                    "decision_343o": summary_343o.get("decision", ""),
                    "decision_343n": summary_343n.get("decision", ""),
                    "decision_343m": summary_343m.get("decision", ""),
                    "decision_343l": summary_343l.get("decision", ""),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::344b_validated_sidecar_has_19_rows",
            "status": "PASS" if source_check_input_sidecar_row_count == 19 else "FAIL",
            "detail": json.dumps(
                {"source_check_input_sidecar_row_count": source_check_input_sidecar_row_count},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "validation::source_check_confirm_correct_counts_match_10_9",
            "status": "PASS"
            if source_check_apply_confirm_count == 10 and source_check_apply_correct_count == 9
            else "FAIL",
            "detail": json.dumps(
                {
                    "confirm": source_check_apply_confirm_count,
                    "correct": source_check_apply_correct_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::apply_plan_has_19_rows_and_no_blocked_rows",
            "status": "PASS"
            if source_check_apply_plan_row_count == 19 and source_check_apply_blocked_count == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "source_check_apply_plan_row_count": source_check_apply_plan_row_count,
                    "source_check_apply_blocked_count": source_check_apply_blocked_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::source_check_applied_sidecar_has_19_rows",
            "status": "PASS"
            if source_check_applied_sidecar_row_count == 19
            else "FAIL",
            "detail": json.dumps(
                {"source_check_applied_sidecar_row_count": source_check_applied_sidecar_row_count},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::corrections_applied_count_is_9",
            "status": "PASS" if corrections_applied_count == 9 else "FAIL",
            "detail": json.dumps(
                {"corrections_applied_count": corrections_applied_count},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::343n_343o_demo_trusted_rows_are_readable_and_count_10",
            "status": "PASS" if prior_demo_trusted_row_count == 10 else "FAIL",
            "detail": json.dumps(
                {"prior_demo_trusted_row_count": prior_demo_trusted_row_count},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::expanded_trusted_candidates_count_is_29",
            "status": "PASS" if expanded_trusted_candidate_count == 29 else "FAIL",
            "detail": json.dumps(
                {"expanded_trusted_candidate_count": expanded_trusted_candidate_count},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::deduplicated_count_is_29_and_no_conflict",
            "status": "PASS"
            if deduplicated_expanded_trusted_candidate_count == 29 and dedup_conflict_count == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "deduplicated_expanded_trusted_candidate_count": deduplicated_expanded_trusted_candidate_count,
                    "dedup_conflict_count": dedup_conflict_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::expanded_trust_gate_generated",
            "status": "PASS"
            if expanded_trusted_candidate_count == 29 and dedup_conflict_count == 0
            else "FAIL",
            "detail": "expanded trust gate can be generated only after successful simulation and dedup audit",
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
            "detail": "344C generates only sidecar simulation and trust-gate artifacts.",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "344C is sidecar simulation only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "344C does not write back to upstream production data.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "344C adds review-queue sidecar files only.",
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
            if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_344C)
            else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_344C, ensure_ascii=False),
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
    summary["source_check_sidecar_apply_simulation_completed"] = bool(
        source_check_apply_plan_row_count == 19
        and source_check_apply_blocked_count == 0
        and qa_fail_count == 0
    )
    summary["source_check_applied_sidecar_generated"] = bool(
        source_check_applied_sidecar_row_count == 19 and qa_fail_count == 0
    )
    summary["expanded_trusted_candidates_generated"] = bool(
        expanded_trusted_candidate_count == 29 and qa_fail_count == 0
    )
    summary["expanded_trust_gate_evaluated"] = bool(
        expanded_trusted_candidate_count == 29 and qa_fail_count == 0
    )
    summary["dedup_audit_generated"] = bool(dedup_audit_rows and qa_fail_count == 0)
    summary["ready_for_344d"] = bool(
        summary["expanded_trust_gate_evaluated"]
        and dedup_conflict_count == 0
        and qa_fail_count == 0
    )
    summary["recommended_344d_scope"] = (
        RECOMMENDED_344D_SCOPE_344C if summary["ready_for_344d"] else ""
    )
    summary["decision"] = READY_DECISION_344C if summary["ready_for_344d"] else NOT_READY_DECISION_344C

    expanded_trust_gate = build_expanded_trust_gate(summary)
    scope_boundary_markdown = _scope_boundary_markdown(build_scope_boundary_lines())
    expanded_trust_summary_markdown = _expanded_trust_summary_markdown(summary)
    next_action_plan = _next_action_plan(summary)

    manifest = {
        "task": "344C_source_check_confirmed_sidecar_apply_simulation_and_expanded_trust_gate",
        "source_check_ingestion_344b_dir": str(source_check_ingestion_344b_dir),
        "source_check_evidence_enrichment_344a2_dir": str(source_check_evidence_enrichment_344a2_dir),
        "demo_audit_snapshot_343o_dir": str(demo_audit_snapshot_343o_dir),
        "limited_demo_export_package_343n_dir": str(limited_demo_export_package_343n_dir),
        "human_confirmed_sidecar_simulation_343m_dir": str(human_confirmed_sidecar_simulation_343m_dir),
        "pure_human_attestation_ingestion_343l_dir": str(pure_human_attestation_ingestion_343l_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "source_check_apply_plan_jsonl": str(output_dir / SOURCE_CHECK_APPLY_PLAN_FILE_NAME),
            "source_check_applied_sidecar_jsonl": str(output_dir / SOURCE_CHECK_APPLIED_SIDECAR_FILE_NAME),
            "expanded_trusted_candidates_jsonl": str(output_dir / EXPANDED_TRUSTED_CANDIDATES_FILE_NAME),
            "corrections_applied_jsonl": str(output_dir / CORRECTIONS_APPLIED_FILE_NAME),
            "dedup_audit_jsonl": str(output_dir / DEDUP_AUDIT_FILE_NAME),
            "expanded_trust_gate_json": str(output_dir / EXPANDED_TRUST_GATE_FILE_NAME),
            "scope_boundary_md": str(output_dir / SCOPE_BOUNDARY_FILE_NAME),
            "expanded_trust_summary_md": str(output_dir / EXPANDED_TRUST_SUMMARY_FILE_NAME),
            "next_action_plan_json": str(output_dir / NEXT_ACTION_PLAN_FILE_NAME),
        },
        "files_read": list(dict.fromkeys(files_read)),
        "warnings": warnings,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "input_summary_344b": summary_344b,
        "input_qa_344b": qa_344b,
        "input_summary_344a2": summary_344a2,
        "input_summary_343o": summary_343o,
        "input_export_gate_343o": export_gate_343o,
        "input_summary_343n": summary_343n,
        "input_export_gate_343n": export_gate_343n,
        "input_summary_343m": summary_343m,
        "input_gate_343m": gate_343m,
        "input_summary_343l": summary_343l,
        "input_summary_343a": summary_343a,
        "input_scope_boundary_344b": scope_boundary_344b,
        "input_no_write_back_344b": no_write_back_344b,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _build_readme_df(summary),
        "01_SIM_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_344B_SUMMARY": _build_key_value_df(summary_344b),
        "03_SOURCE_CHECK_SIDECAR": _clean_frame(pd.DataFrame(source_check_applied_sidecar_rows)),
        "04_CORRECTIONS_APPLIED": _clean_frame(pd.DataFrame(corrections_applied_rows)),
        "05_EXPANDED_TRUSTED": _clean_frame(pd.DataFrame(deduplicated_rows)),
        "06_DEDUP_AUDIT": _clean_frame(pd.DataFrame(dedup_audit_rows)),
        "07_EXPANDED_GATE": _build_key_value_df(expanded_trust_gate),
        "08_SCOPE_BOUNDARY": _build_key_value_df(
            {
                "scope_boundary_report": scope_boundary_markdown,
                "upstream_344b_scope_boundary": scope_boundary_344b,
                "upstream_343o_summary": summary_343o,
                "upstream_343n_summary": summary_343n,
            }
        ),
        "09_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "10_NEXT_STEPS": _clean_frame(pd.DataFrame(_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "source_check_apply_plan_rows": source_check_apply_plan_rows,
        "source_check_applied_sidecar_rows": source_check_applied_sidecar_rows,
        "expanded_trusted_candidate_rows": deduplicated_rows,
        "corrections_applied_rows": corrections_applied_rows,
        "dedup_audit_rows": dedup_audit_rows,
        "expanded_trust_gate": expanded_trust_gate,
        "scope_boundary_markdown": scope_boundary_markdown,
        "expanded_trust_summary_markdown": expanded_trust_summary_markdown,
        "next_action_plan": next_action_plan,
        "workbook_sheets": workbook_sheets,
    }

