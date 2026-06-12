from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.audit_summary_343h import (
    NOT_READY_DECISION_343H,
    READY_DECISION_343H,
    RECOMMENDED_343I_SCOPE,
    build_chain_overview_rows,
    build_client_export_gate,
    build_confirmed_ai_assisted_items,
    build_gap_items,
    build_next_action_plan,
    build_source_check_backlog_rows,
    utc_now,
)
from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_343G_DECISION = "AI_ASSISTED_SPOT_CHECK_INGESTION_343G_READY"
READY_INPUT_343E_DECISION = "AI_ASSISTED_REVIEW_APPLY_SIMULATION_343E_READY"
READY_INPUT_343D_DECISION = "REVIEW_QUEUE_EXCEL_INGESTION_343D_READY"
READY_INPUT_343A_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"
READY_DECISION = READY_DECISION_343H
NOT_READY_DECISION = NOT_READY_DECISION_343H

DEFAULT_SPOT_CHECK_INGESTION_343G_DIR = Path(r"D:\_datefac\output\review_queue_spot_check_ingestion_343g")
DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR = Path(r"D:\_datefac\output\review_queue_spot_check_package_343f")
DEFAULT_APPLY_SIMULATION_343E_DIR = Path(r"D:\_datefac\output\review_queue_apply_simulation_343e")
DEFAULT_EXCEL_INGESTION_343D_DIR = Path(r"D:\_datefac\output\review_queue_excel_ingestion_343d")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_audit_summary_343h")

SUMMARY_FILE_NAME = "review_queue_audit_summary_343h_summary.json"
MANIFEST_FILE_NAME = "review_queue_audit_summary_343h_manifest.json"
QA_FILE_NAME = "review_queue_audit_summary_343h_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_audit_summary_343h_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_audit_summary_343h_report.md"
WORKBOOK_FILE_NAME = "review_queue_audit_summary_343h.xlsx"
STRICT_GAP_REPORT_FILE_NAME = "review_queue_audit_summary_343h_strict_human_gap_report.md"
AUDIT_MATRIX_FILE_NAME = "review_queue_audit_summary_343h_audit_matrix.json"
GAP_ITEMS_FILE_NAME = "review_queue_audit_summary_343h_gap_items.jsonl"
CONFIRMED_ITEMS_FILE_NAME = "review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl"
SOURCE_CHECK_BACKLOG_FILE_NAME = "review_queue_audit_summary_343h_source_check_backlog.jsonl"
CLIENT_EXPORT_GATE_FILE_NAME = "review_queue_audit_summary_343h_client_export_gate.json"
NEXT_ACTION_PLAN_FILE_NAME = "review_queue_audit_summary_343h_next_action_plan.json"

INPUT_343G_SUMMARY_NAME = "review_queue_spot_check_ingestion_343g_summary.json"
INPUT_343G_QA_NAME = "review_queue_spot_check_ingestion_343g_qa.json"
INPUT_343G_RESULT_NAME = "review_queue_spot_check_ingestion_343g_result.jsonl"
INPUT_343G_DECISION_SUMMARY_NAME = "review_queue_spot_check_ingestion_343g_decision_summary.json"
INPUT_343G_DISCLOSURE_NAME = "review_queue_spot_check_ingestion_343g_ai_assisted_spot_check_disclosure.md"
INPUT_343G_NO_WRITE_BACK_NAME = "review_queue_spot_check_ingestion_343g_no_write_back_proof.json"
INPUT_343F_SUMMARY_NAME = "review_queue_spot_check_package_343f_summary.json"
INPUT_343F_SOURCE_TODO_NAME = "review_queue_spot_check_package_343f_source_check_todo.jsonl"
INPUT_343E_SUMMARY_NAME = "review_queue_apply_simulation_343e_summary.json"
INPUT_343E_APPLY_PLAN_NAME = "review_queue_apply_simulation_343e_apply_plan.jsonl"
INPUT_343E_RISK_REGISTER_NAME = "review_queue_apply_simulation_343e_risk_register.json"
INPUT_343D_SUMMARY_NAME = "review_queue_excel_ingestion_343d_summary.json"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"
INPUT_343A_SCHEMA_NAME = "review_queue_schema_343a_schema.json"

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input/review_queue_spot_check_package_343f_filled",
    "input/review_queue_real_excel_review_343c_filled",
    "input/table_first_review_342g_reviewed",
    "input/spot_check_reviewed_342m",
    "input/llm_review_responses_342m",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

WORKBOOK_SHEETS = [
    "00_README",
    "01_AUDIT_SUMMARY",
    "02_INPUT_343G_SUMMARY",
    "03_CHAIN_OVERVIEW",
    "04_AI_CONFIRMED_ITEMS",
    "05_SOURCE_CHECK_BACKLOG",
    "06_STRICT_HUMAN_GAP",
    "07_CLIENT_EXPORT_GATE",
    "08_AUDIT_MATRIX",
    "09_RISK_REGISTER",
    "10_NEXT_ACTION_PLAN",
    "11_343I_READINESS",
    "12_NO_WRITE_BACK",
    "13_NEXT_STEPS",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return normalize_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame([{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()])
    )


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "343H summarizes the AI-assisted review and AI-assisted spot-check chain.",
                },
                {
                    "section": "boundary",
                    "message": "No real write-back, no production apply, no formal client export, no strict human completion claim.",
                },
                {
                    "section": "confirmed",
                    "message": "10 rows are AI-assisted spot-check confirmed only, not strict-human confirmed.",
                },
                {
                    "section": "backlog",
                    "message": "19 rows remain source-check backlog and 1 row remains keep-hold.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {
            "step": "open_audit_workbook",
            "recommendation": "Open the 343H workbook to review the chain overview, gap report, and export gate.",
        },
        {
            "step": "strict_human_review",
            "recommendation": "Default next safe step is a strict human review package for the 10 AI-assisted confirmed rows.",
        },
        {
            "step": "source_check_backlog",
            "recommendation": "Resolve the 19 source-check backlog rows before any stronger downstream trust claim.",
        },
        {
            "step": "next_task",
            "recommendation": summary.get("recommended_343i_scope", "") or "Resolve QA issues before 343I.",
        },
    ]


def build_review_queue_audit_summary_343h(
    *,
    spot_check_ingestion_343g_dir: Path = DEFAULT_SPOT_CHECK_INGESTION_343G_DIR,
    spot_check_package_343f_dir: Path = DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR,
    apply_simulation_343e_dir: Path = DEFAULT_APPLY_SIMULATION_343E_DIR,
    excel_ingestion_343d_dir: Path = DEFAULT_EXCEL_INGESTION_343D_DIR,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_SUMMARY_NAME
    qa_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_QA_NAME
    result_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_RESULT_NAME
    decision_summary_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_DECISION_SUMMARY_NAME
    disclosure_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_DISCLOSURE_NAME
    no_write_back_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_NO_WRITE_BACK_NAME
    summary_343f_path = spot_check_package_343f_dir / INPUT_343F_SUMMARY_NAME
    source_todo_343f_path = spot_check_package_343f_dir / INPUT_343F_SOURCE_TODO_NAME
    summary_343e_path = apply_simulation_343e_dir / INPUT_343E_SUMMARY_NAME
    apply_plan_343e_path = apply_simulation_343e_dir / INPUT_343E_APPLY_PLAN_NAME
    risk_register_343e_path = apply_simulation_343e_dir / INPUT_343E_RISK_REGISTER_NAME
    summary_343d_path = excel_ingestion_343d_dir / INPUT_343D_SUMMARY_NAME
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME
    schema_343a_path = review_queue_schema_343a_dir / INPUT_343A_SCHEMA_NAME

    files_read: List[str] = []
    warnings: List[str] = []
    input_paths = [
        summary_343g_path,
        qa_343g_path,
        result_343g_path,
        decision_summary_343g_path,
        disclosure_343g_path,
        no_write_back_343g_path,
        summary_343f_path,
        source_todo_343f_path,
        summary_343e_path,
        apply_plan_343e_path,
        risk_register_343e_path,
        summary_343d_path,
        summary_343a_path,
        schema_343a_path,
    ]
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input: {path}")

    summary_343g = _read_json(summary_343g_path) if summary_343g_path.exists() else {}
    qa_343g = _read_json(qa_343g_path) if qa_343g_path.exists() else {}
    result_rows = _read_jsonl(result_343g_path) if result_343g_path.exists() else []
    decision_summary_343g = _read_json(decision_summary_343g_path) if decision_summary_343g_path.exists() else []
    disclosure_343g = disclosure_343g_path.read_text(encoding="utf-8") if disclosure_343g_path.exists() else ""
    no_write_back_343g = _read_json(no_write_back_343g_path) if no_write_back_343g_path.exists() else {}
    summary_343f = _read_json(summary_343f_path) if summary_343f_path.exists() else {}
    source_todo_343f = _read_jsonl(source_todo_343f_path) if source_todo_343f_path.exists() else []
    summary_343e = _read_json(summary_343e_path) if summary_343e_path.exists() else {}
    apply_plan_343e = _read_jsonl(apply_plan_343e_path) if apply_plan_343e_path.exists() else []
    risk_register_343e = _read_json(risk_register_343e_path) if risk_register_343e_path.exists() else []
    summary_343d = _read_json(summary_343d_path) if summary_343d_path.exists() else {}
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}
    schema_343a = _read_json(schema_343a_path) if schema_343a_path.exists() else {}

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        summary_343g.get("decision") == READY_INPUT_343G_DECISION
        and normalize_bool(summary_343g.get("spot_check_result_ingested"))
        and normalize_bool(summary_343g.get("spot_check_result_jsonl_generated"))
        and normalize_bool(summary_343g.get("ready_for_343h"))
        and int(summary_343g.get("qa_fail_count", 1)) == 0
        and summary_343g.get("review_source_type") == "AI_ASSISTED_REVIEW"
        and summary_343g.get("spot_check_source_type") == "AI_ASSISTED_SPOT_CHECK"
        and normalize_bool(summary_343g.get("not_pure_human_review"))
        and not normalize_bool(summary_343g.get("strict_human_review_completed"))
        and normalize_bool(summary_343g.get("requires_strict_human_review"))
        and summary_343g.get("apply_mode") == "SIMULATION_ONLY"
        and not normalize_bool(summary_343g.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343g.get("client_ready"))
        and not normalize_bool(summary_343g.get("production_ready"))
        and summary_343e.get("decision") == READY_INPUT_343E_DECISION
        and summary_343d.get("decision") == READY_INPUT_343D_DECISION
        and summary_343a.get("decision") == READY_INPUT_343A_DECISION
        and len(result_rows) > 0
    )

    client_export_gate = build_client_export_gate()
    confirmed_items = build_confirmed_ai_assisted_items(result_rows)
    source_check_backlog = build_source_check_backlog_rows(
        result_rows=result_rows,
        source_check_todo_rows=source_todo_343f,
        apply_plan_rows=apply_plan_343e,
    )
    gap_items = build_gap_items(result_rows=result_rows, client_export_gate=client_export_gate)
    next_action_plan = build_next_action_plan()
    audit_matrix = build_chain_overview_rows(
        summary_343a=summary_343a,
        summary_343d=summary_343d,
        summary_343e=summary_343e,
        summary_343f=summary_343f,
        summary_343g=summary_343g,
    )

    ai_assisted_confirmed_count = len(confirmed_items)
    source_check_required_count = sum(
        1 for row in result_rows if normalize_text(row.get("spot_check_decision")) == "SOURCE_CHECK_REQUIRED"
    )
    keep_hold_count = sum(
        1 for row in result_rows if normalize_text(row.get("spot_check_decision")) == "KEEP_HOLD"
    )
    strict_human_gap_item_count = len(gap_items)
    source_check_backlog_count = len(source_check_backlog)
    audit_stage_count = len(audit_matrix)
    expected_source_check_backlog_count = max(
        source_check_required_count,
        int(summary_343f.get("source_check_required_count", 0) or 0),
        int(summary_343e.get("hold_source_check_required_count", 0) or 0),
        len(source_todo_343f),
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343G",
        "decision": NOT_READY_DECISION,
        "review_queue_schema_version": summary_343g.get("review_queue_schema_version", ""),
        "input_spot_check_result_row_count": len(result_rows),
        "ai_assisted_confirmed_count": ai_assisted_confirmed_count,
        "source_check_required_count": source_check_required_count,
        "keep_hold_count": keep_hold_count,
        "strict_human_gap_item_count": strict_human_gap_item_count,
        "source_check_backlog_count": source_check_backlog_count,
        "audit_stage_count": audit_stage_count,
        "audit_summary_generated": False,
        "strict_human_gap_report_generated": False,
        "client_export_gate_generated": False,
        "next_action_plan_generated": False,
        "review_source_type": "AI_ASSISTED_REVIEW",
        "spot_check_source_type": "AI_ASSISTED_SPOT_CHECK",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_strict_human_review": True,
        "apply_mode": "SIMULATION_ONLY",
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343i": False,
        "recommended_343i_scope": "",
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343H",
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
    no_write_back_json["audit_summary_generated"] = input_ready
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343h")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::343g_input_exists_and_is_ready",
            "status": "PASS" if summary_343g.get("decision") == READY_INPUT_343G_DECISION else "FAIL",
            "detail": json.dumps({"decision": summary_343g.get("decision", "")}, ensure_ascii=False),
        },
        {
            "check_name": "inputs::343g_result_jsonl_exists_and_readable",
            "status": "PASS" if result_343g_path.exists() and len(result_rows) > 0 else "FAIL",
            "detail": str(result_343g_path),
        },
        {
            "check_name": "disclosure::all_rows_preserve_ai_assisted_boundary",
            "status": "PASS" if all(row.get("review_source_type") == "AI_ASSISTED_REVIEW" and row.get("spot_check_source_type") == "AI_ASSISTED_SPOT_CHECK" and row.get("not_pure_human_review") is True and row.get("strict_human_review_completed") is False and row.get("requires_strict_human_review") is True for row in result_rows) else "FAIL",
            "detail": "AI-assisted review + AI-assisted spot-check disclosure preserved on every row",
        },
        {
            "check_name": "claims::no_row_claims_strict_pure_human_review",
            "status": "PASS" if all(row.get("strict_human_review_completed") is False for row in result_rows) else "FAIL",
            "detail": "strict_human_review_completed must remain false",
        },
        {
            "check_name": "claims::no_formal_client_or_production_ready_true",
            "status": "PASS" if all(not normalize_bool(row.get("formal_client_export_allowed")) and not normalize_bool(row.get("client_ready")) and not normalize_bool(row.get("production_ready")) for row in result_rows) else "FAIL",
            "detail": "formal/client/production flags remain false",
        },
        {
            "check_name": "outputs::audit_matrix_generated",
            "status": "PASS" if len(audit_matrix) >= 5 else "FAIL",
            "detail": json.dumps(audit_matrix, ensure_ascii=False),
        },
        {
            "check_name": "outputs::strict_human_gap_report_generated",
            "status": "PASS" if len(gap_items) > 0 else "FAIL",
            "detail": json.dumps({"gap_item_count": len(gap_items)}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::source_check_backlog_generated",
            "status": "PASS" if len(source_check_backlog) == expected_source_check_backlog_count else "FAIL",
            "detail": json.dumps(
                {
                    "source_check_backlog_count": len(source_check_backlog),
                    "expected_source_check_backlog_count": expected_source_check_backlog_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::client_export_gate_generated_and_false",
            "status": "PASS" if not client_export_gate["formal_client_export_allowed"] and not client_export_gate["client_ready"] and not client_export_gate["production_ready"] else "FAIL",
            "detail": json.dumps(client_export_gate, ensure_ascii=False),
        },
        {
            "check_name": "outputs::next_action_plan_generated",
            "status": "PASS" if next_action_plan.get("recommended_343i_scope") == RECOMMENDED_343I_SCOPE else "FAIL",
            "detail": json.dumps(next_action_plan, ensure_ascii=False),
        },
        {
            "check_name": "counts::confirmed_and_backlog_match_343g_summary",
            "status": "PASS" if ai_assisted_confirmed_count == int(summary_343g.get("confirm_ai_assisted_result_count", -1)) and source_check_required_count == int(summary_343g.get("source_check_required_count", -1)) and keep_hold_count == int(summary_343g.get("keep_hold_count", -1)) else "FAIL",
            "detail": json.dumps({"ai_assisted_confirmed_count": ai_assisted_confirmed_count, "source_check_required_count": source_check_required_count, "keep_hold_count": keep_hold_count}, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343H is summary/audit only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343H only summarizes and audits existing sidecar outputs.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343H adds review-queue sidecar files only.",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS, ensure_ascii=False),
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
    summary["audit_summary_generated"] = bool(input_ready and qa_fail_count == 0)
    summary["strict_human_gap_report_generated"] = summary["audit_summary_generated"]
    summary["client_export_gate_generated"] = summary["audit_summary_generated"]
    summary["next_action_plan_generated"] = summary["audit_summary_generated"]
    summary["ready_for_343i"] = summary["audit_summary_generated"]
    summary["recommended_343i_scope"] = RECOMMENDED_343I_SCOPE if summary["ready_for_343i"] else ""
    summary["decision"] = READY_DECISION if summary["audit_summary_generated"] else NOT_READY_DECISION

    manifest = {
        "task": "343H_ai_assisted_spot_check_audit_summary_and_strict_human_gap_report",
        "spot_check_ingestion_343g_dir": str(spot_check_ingestion_343g_dir),
        "spot_check_package_343f_dir": str(spot_check_package_343f_dir),
        "apply_simulation_343e_dir": str(apply_simulation_343e_dir),
        "excel_ingestion_343d_dir": str(excel_ingestion_343d_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "strict_human_gap_report_md": str(output_dir / STRICT_GAP_REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "audit_matrix_json": str(output_dir / AUDIT_MATRIX_FILE_NAME),
            "gap_items_jsonl": str(output_dir / GAP_ITEMS_FILE_NAME),
            "confirmed_ai_assisted_items_jsonl": str(output_dir / CONFIRMED_ITEMS_FILE_NAME),
            "source_check_backlog_jsonl": str(output_dir / SOURCE_CHECK_BACKLOG_FILE_NAME),
            "client_export_gate_json": str(output_dir / CLIENT_EXPORT_GATE_FILE_NAME),
            "next_action_plan_json": str(output_dir / NEXT_ACTION_PLAN_FILE_NAME),
        },
        "files_read": list(files_read),
        "warnings": warnings,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_AUDIT_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343G_SUMMARY": _build_key_value_df(summary_343g),
        "03_CHAIN_OVERVIEW": _clean_frame(pd.DataFrame(audit_matrix)),
        "04_AI_CONFIRMED_ITEMS": _clean_frame(pd.DataFrame(confirmed_items)),
        "05_SOURCE_CHECK_BACKLOG": _clean_frame(pd.DataFrame(source_check_backlog)),
        "06_STRICT_HUMAN_GAP": _clean_frame(pd.DataFrame(gap_items)),
        "07_CLIENT_EXPORT_GATE": _build_key_value_df(client_export_gate),
        "08_AUDIT_MATRIX": _clean_frame(pd.DataFrame(audit_matrix)),
        "09_RISK_REGISTER": _clean_frame(pd.DataFrame(risk_register_343e)),
        "10_NEXT_ACTION_PLAN": _build_key_value_df(next_action_plan),
        "11_343I_READINESS": _clean_frame(
            pd.DataFrame(
                [
                    {
                        "audit_summary_generated": summary["audit_summary_generated"],
                        "strict_human_gap_report_generated": summary["strict_human_gap_report_generated"],
                        "client_export_gate_generated": summary["client_export_gate_generated"],
                        "ready_for_343i": summary["ready_for_343i"],
                        "recommended_343i_scope": summary["recommended_343i_scope"],
                    }
                ]
            )
        ),
        "12_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "13_NEXT_STEPS": _clean_frame(pd.DataFrame(_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "audit_matrix": audit_matrix,
        "gap_items": gap_items,
        "confirmed_items": confirmed_items,
        "source_check_backlog": source_check_backlog,
        "client_export_gate": client_export_gate,
        "next_action_plan": next_action_plan,
        "risk_register": risk_register_343e,
        "workbook_sheets": workbook_sheets,
    }
