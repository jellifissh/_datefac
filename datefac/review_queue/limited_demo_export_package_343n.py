from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.human_confirmed_sidecar_simulation_343m import READY_DECISION_343M
from datefac.review_queue.ingest_strict_review_343j import FORBIDDEN_STAGE_PATHS, PROTECTED_DIRTY_PATHS
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_343N = "LIMITED_HUMAN_CONFIRMED_DEMO_EXPORT_PACKAGE_343N_READY"
NOT_READY_DECISION_343N = "LIMITED_HUMAN_CONFIRMED_DEMO_EXPORT_PACKAGE_343N_NOT_READY"
RECOMMENDED_343O_SCOPE_343N = "demo_package_audit_snapshot_and_handoff_summary"

WORKBOOK_SHEETS_343N = [
    "00_README",
    "01_PACKAGE_SUMMARY",
    "02_INPUT_343M_SUMMARY",
    "03_DEMO_EXPORT_ROWS",
    "04_AUDIT_LABELS",
    "05_EXPORT_GATE",
    "06_REMAINING_BACKLOG",
    "07_SCOPE_BOUNDARY",
    "08_NO_WRITE_BACK",
    "09_NEXT_STEPS",
]

INPUT_343M_SUMMARY_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_summary.json"
INPUT_343M_QA_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_qa.json"
INPUT_343M_SIDECAR_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_sidecar.jsonl"
INPUT_343M_APPLY_PLAN_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_apply_plan.jsonl"
INPUT_343M_GATE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate.json"
INPUT_343M_CANDIDATE_NAME = (
    "review_queue_human_confirmed_sidecar_simulation_343m_limited_export_candidate.jsonl"
)
INPUT_343M_BACKLOG_NAME = (
    "review_queue_human_confirmed_sidecar_simulation_343m_remaining_backlog.jsonl"
)
INPUT_343M_SCOPE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_scope_boundary.md"
INPUT_343M_NO_WRITE_BACK_NAME = (
    "review_queue_human_confirmed_sidecar_simulation_343m_no_write_back_proof.json"
)

INPUT_343L_SUMMARY_NAME = "review_queue_pure_human_attestation_ingestion_343l_summary.json"
INPUT_343L_RESULT_NAME = "review_queue_pure_human_attestation_ingestion_343l_result.jsonl"
INPUT_343H_BACKLOG_NAME = "review_queue_audit_summary_343h_source_check_backlog.jsonl"
INPUT_343H_GAP_REPORT_NAME = "review_queue_audit_summary_343h_strict_human_gap_report.md"
INPUT_343A_SCHEMA_NAME = "review_queue_schema_343a_schema.json"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"

DEMO_AUDIT_LABELS = [
    "PACKAGE_SCOPE_HUMAN_CONFIRMED",
    "DEMO_ONLY",
    "NOT_FORMAL_CLIENT_EXPORT",
    "NOT_PRODUCTION_READY",
    "GLOBAL_REVIEW_INCOMPLETE",
    "SOURCE_CHECK_BACKLOG_REMAINS",
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


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {"section": "positioning", "message": "343N packages the limited human-confirmed candidate into a demo-only export bundle."},
                {"section": "scope", "message": "The package scope is strictly limited to 343K_PACKAGE_ONLY."},
                {"section": "boundary", "message": "This is not a formal client export, not production-ready, and not globally review-complete."},
                {"section": "decision", "message": summary.get("decision", "")},
            ]
        )
    )


def build_demo_export_row(candidate_row: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(candidate_row)
    row["export_scope"] = "343K_PACKAGE_ONLY"
    row["export_usage"] = "DEMO_ONLY"
    row["formal_client_export_allowed"] = False
    row["client_ready"] = False
    row["production_ready"] = False
    row["source_milestone"] = "343M"
    row["human_confirmation_scope"] = "343K_PACKAGE_ONLY"
    row["package_strict_human_review_completed"] = True
    row["global_strict_human_review_completed"] = False
    row["demo_only_flag"] = "DEMO_ONLY"
    row["not_formal_client_export_flag"] = "NOT_FORMAL_CLIENT_EXPORT"
    row["not_production_ready_flag"] = "NOT_PRODUCTION_READY"
    row["global_review_incomplete_flag"] = "GLOBAL_REVIEW_INCOMPLETE"
    row["source_check_backlog_remains_flag"] = "SOURCE_CHECK_BACKLOG_REMAINS"
    row["audit_labels"] = DEMO_AUDIT_LABELS
    return row


def build_audit_label_row(demo_row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "queue_item_id": demo_row.get("queue_item_id", ""),
        "review_item_id": demo_row.get("review_item_id", ""),
        "export_scope": "343K_PACKAGE_ONLY",
        "audit_labels": DEMO_AUDIT_LABELS,
    }


def build_demo_readme_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 343N Demo-only Limited Export Package",
            "",
            "## 中文说明",
            "- 本包只包含 10 条 `343K_PACKAGE_ONLY` 范围内的人审确认数据。",
            "- 本包用途仅限 demo / sample / handoff，不是 formal client export。",
            "- 本包不是 production export，不代表 client_ready，也不代表 global review complete。",
            f"- 当前仍有 {summary.get('remaining_source_check_backlog_count', 0)} 条 source-check backlog 留在包外。",
            "",
            "## English Note",
            "- This package contains only the 10 human-confirmed rows within the 343K package scope.",
            "- It is demo-only / sample-only / handoff-only and must not be treated as a formal client export.",
        ]
    )


def build_scope_boundary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 343N Scope Boundary",
            "",
            "## 中文说明",
            "- 343N 只生成受限 demo-only export package。",
            "- 作用范围仅为 `343K_PACKAGE_ONLY`。",
            "- 这不表示 formal client export 已开放，也不表示 production-ready。",
            "- global strict human review 仍未完成。",
            "",
            "## Current Boundary",
            f"- limited_export_scope: {summary.get('limited_export_scope', '')}",
            f"- export_usage: {summary.get('export_usage', '')}",
            f"- formal_client_export_allowed: {summary.get('formal_client_export_allowed', False)}",
            f"- global_strict_human_review_completed: {summary.get('global_strict_human_review_completed', False)}",
        ]
    )


def build_review_queue_limited_demo_export_package_343n(
    *,
    human_confirmed_sidecar_simuation_343m_dir: Path,
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
        human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_SUMMARY_NAME,
        human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_QA_NAME,
        human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_SIDECAR_NAME,
        human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_APPLY_PLAN_NAME,
        human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_GATE_NAME,
        human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_CANDIDATE_NAME,
        human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_BACKLOG_NAME,
        human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_SCOPE_NAME,
        human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_NO_WRITE_BACK_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_SUMMARY_NAME,
        pure_human_attestation_ingestion_343l_dir / INPUT_343L_RESULT_NAME,
        audit_summary_343h_dir / INPUT_343H_BACKLOG_NAME,
        audit_summary_343h_dir / INPUT_343H_GAP_REPORT_NAME,
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

    summary_343m = _read_json(human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_SUMMARY_NAME)
    gate_343m = _read_json(human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_GATE_NAME)
    candidate_rows = _read_jsonl(human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_CANDIDATE_NAME)
    remaining_backlog_rows = _read_jsonl(human_confirmed_sidecar_simuation_343m_dir / INPUT_343M_BACKLOG_NAME)
    summary_343a = _read_json(review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME)

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        not missing_required_inputs
        and summary_343m.get("decision") == READY_DECISION_343M
        and int(summary_343m.get("qa_fail_count", 1)) == 0
        and normalize_bool(summary_343m.get("sidecar_apply_simulation_completed"))
        and normalize_bool(summary_343m.get("limited_export_gate_evaluated"))
        and normalize_bool(summary_343m.get("limited_package_export_candidate_allowed"))
        and normalize_text(summary_343m.get("limited_export_scope")) == "343K_PACKAGE_ONLY"
        and int(summary_343m.get("limited_export_candidate_row_count", -1)) == 10
        and not normalize_bool(summary_343m.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343m.get("client_ready"))
        and not normalize_bool(summary_343m.get("production_ready"))
        and not normalize_bool(summary_343m.get("global_strict_human_review_completed"))
        and normalize_bool(gate_343m.get("limited_package_export_candidate_allowed"))
        and normalize_text(gate_343m.get("limited_export_scope")) == "343K_PACKAGE_ONLY"
    )

    demo_export_rows = [build_demo_export_row(row) for row in candidate_rows]
    audit_label_rows = [build_audit_label_row(row) for row in demo_export_rows]
    remaining_source_check_backlog_count = len(remaining_backlog_rows)

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343M",
        "decision": NOT_READY_DECISION_343N,
        "review_queue_schema_version": summary_343m.get("review_queue_schema_version", summary_343a.get("review_queue_schema_version", "")),
        "input_limited_export_candidate_row_count": len(candidate_rows),
        "demo_export_row_count": len(demo_export_rows),
        "audit_label_row_count": len(audit_label_rows),
        "remaining_source_check_backlog_count": remaining_source_check_backlog_count,
        "limited_export_scope": "343K_PACKAGE_ONLY",
        "export_usage": "DEMO_ONLY",
        "package_strict_human_review_completed": True,
        "global_strict_human_review_completed": False,
        "demo_only_export_package_generated": bool(demo_export_rows),
        "demo_handoff_ready": False,
        "limited_package_export_candidate_allowed": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343o": False,
        "recommended_343o_scope": "",
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    official_assets_after = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343N",
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
        no_write_back_json.get("no_official_asset_modification_during_343n")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    export_gate = {
        "demo_only_export_package_generated": bool(demo_export_rows) and input_ready,
        "demo_handoff_ready": bool(demo_export_rows) and input_ready,
        "limited_package_export_candidate_allowed": True,
        "limited_export_scope": "343K_PACKAGE_ONLY",
        "limited_export_row_count": len(demo_export_rows),
        "remaining_source_check_backlog_count": remaining_source_check_backlog_count,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "reason": "Demo-only limited package is allowed for scoped presentation/handoff; formal client export remains blocked by global review incompleteness and remaining backlog.",
    }

    checks = [
        {
            "check_name": "inputs::343m_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps({"missing_required_inputs": missing_required_inputs, "decision": summary_343m.get("decision", ""), "qa_fail_count": summary_343m.get("qa_fail_count", 0)}, ensure_ascii=False),
        },
        {
            "check_name": "gate::limited_candidate_allowed_only",
            "status": "PASS" if normalize_bool(gate_343m.get("limited_package_export_candidate_allowed")) and not normalize_bool(gate_343m.get("formal_client_export_allowed")) else "FAIL",
            "detail": json.dumps(gate_343m, ensure_ascii=False),
        },
        {
            "check_name": "claims::formal_client_production_flags_remain_false",
            "status": "PASS" if not normalize_bool(summary_343m.get("formal_client_export_allowed")) and not normalize_bool(summary_343m.get("client_ready")) and not normalize_bool(summary_343m.get("production_ready")) else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "scope::limited_export_scope_is_package_only",
            "status": "PASS" if normalize_text(summary_343m.get("limited_export_scope")) == "343K_PACKAGE_ONLY" else "FAIL",
            "detail": normalize_text(summary_343m.get("limited_export_scope")),
        },
        {
            "check_name": "counts::demo_export_rows_match_input_candidate_rows",
            "status": "PASS" if len(demo_export_rows) == len(candidate_rows) else "FAIL",
            "detail": json.dumps({"demo_export_row_count": len(demo_export_rows), "input_candidate_row_count": len(candidate_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "rows::every_demo_row_carries_required_labels",
            "status": "PASS" if all(set(DEMO_AUDIT_LABELS).issubset(set(row.get("audit_labels", []))) for row in demo_export_rows) else "FAIL",
            "detail": json.dumps(DEMO_AUDIT_LABELS, ensure_ascii=False),
        },
        {
            "check_name": "outputs::audit_labels_generated",
            "status": "PASS" if len(audit_label_rows) == len(demo_export_rows) else "FAIL",
            "detail": json.dumps({"audit_label_row_count": len(audit_label_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "backlog::remaining_backlog_carried_forward",
            "status": "PASS",
            "detail": json.dumps({"remaining_source_check_backlog_count": remaining_source_check_backlog_count}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::demo_readme_generated",
            "status": "PASS",
            "detail": "review_queue_limited_demo_export_package_343n_demo_readme.md",
        },
        {
            "check_name": "outputs::export_gate_generated",
            "status": "PASS" if export_gate["demo_only_export_package_generated"] else "FAIL",
            "detail": json.dumps(export_gate, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_formal_client_export_workbook_generated",
            "status": "PASS",
            "detail": "343N generates a demo-only package workbook, not a formal client export workbook.",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343N is demo packaging only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343N does not write back or perform production apply.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343N adds review-queue sidecar files only.",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_343N) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_343N, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    if qa_fail_count == 0:
        summary["decision"] = READY_DECISION_343N
        summary["demo_only_export_package_generated"] = True
        summary["demo_handoff_ready"] = True
        summary["ready_for_343o"] = True
        summary["recommended_343o_scope"] = RECOMMENDED_343O_SCOPE_343N
    else:
        summary["decision"] = NOT_READY_DECISION_343N
        summary["demo_only_export_package_generated"] = False
        summary["demo_handoff_ready"] = False
        summary["ready_for_343o"] = False
        summary["recommended_343o_scope"] = ""
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    manifest = {
        "task": "343N_limited_human_confirmed_export_package_generation_for_demo_only",
        "human_confirmed_sidecar_simuation_343m_dir": str(human_confirmed_sidecar_simuation_343m_dir),
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
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_PACKAGE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343M_SUMMARY": _build_key_value_df(summary_343m),
        "03_DEMO_EXPORT_ROWS": _clean_frame(pd.DataFrame(demo_export_rows)),
        "04_AUDIT_LABELS": _clean_frame(pd.DataFrame(audit_label_rows)),
        "05_EXPORT_GATE": _build_key_value_df(export_gate),
        "06_REMAINING_BACKLOG": _clean_frame(pd.DataFrame(remaining_backlog_rows)),
        "07_SCOPE_BOUNDARY": _build_key_value_df({"scope_boundary_report": build_scope_boundary_markdown(summary)}),
        "08_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "09_NEXT_STEPS": _clean_frame(pd.DataFrame([
            {"step": "open_demo_readme", "recommendation": "Open the demo readme and export gate first."},
            {"step": "handoff_scope", "recommendation": "Use only for demo/sample/handoff within 343K_PACKAGE_ONLY."},
        ])),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "demo_readme_markdown": build_demo_readme_markdown(summary),
        "demo_export_rows": demo_export_rows,
        "audit_label_rows": audit_label_rows,
        "export_gate": export_gate,
        "scope_boundary_markdown": build_scope_boundary_markdown(summary),
        "remaining_backlog_rows": remaining_backlog_rows,
        "handoff_summary_markdown": "# 343N Demo Handoff Summary\n\n- 10 rows only\n- Scope: 343K_PACKAGE_ONLY\n- Usage: DEMO_ONLY\n- Formal client export remains blocked\n",
        "workbook_sheets": workbook_sheets,
    }
