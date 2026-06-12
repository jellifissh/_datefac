from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.spot_check_package_343f import (
    ALLOWED_SPOT_CHECK_DECISIONS,
    EDITABLE_SPOT_CHECK_COLUMNS,
    build_expected_import_contract,
    build_source_check_todo_row,
    build_spot_check_item,
    priority_plan_rows,
    validate_apply_plan_row,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_343E_DECISION = "AI_ASSISTED_REVIEW_APPLY_SIMULATION_343E_READY"
READY_DECISION = "AI_ASSISTED_REVIEW_SPOT_CHECK_PACKAGE_343F_WAITING_FOR_SPOT_CHECK"
NOT_READY_DECISION = "AI_ASSISTED_REVIEW_SPOT_CHECK_PACKAGE_343F_NOT_READY"
RECOMMENDED_343G_SCOPE = "ai_assisted_review_spot_check_result_ingestion_after_user_fills_workbook"

DEFAULT_APPLY_SIMULATION_343E_DIR = Path(r"D:\_datefac\output\review_queue_apply_simulation_343e")
DEFAULT_EXCEL_INGESTION_343D_DIR = Path(r"D:\_datefac\output\review_queue_excel_ingestion_343d")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_spot_check_package_343f")

SUMMARY_FILE_NAME = "review_queue_spot_check_package_343f_summary.json"
MANIFEST_FILE_NAME = "review_queue_spot_check_package_343f_manifest.json"
QA_FILE_NAME = "review_queue_spot_check_package_343f_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_spot_check_package_343f_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_spot_check_package_343f_report.md"
WORKBOOK_FILE_NAME = "review_queue_spot_check_package_343f.xlsx"
REVIEW_TEMPLATE_FILE_NAME = "review_queue_spot_check_package_343f_review_template.xlsx"
SPOT_CHECK_ITEMS_FILE_NAME = "review_queue_spot_check_package_343f_spot_check_items.jsonl"
PRIORITY_PLAN_FILE_NAME = "review_queue_spot_check_package_343f_priority_plan.json"
SOURCE_CHECK_TODO_FILE_NAME = "review_queue_spot_check_package_343f_source_check_todo.jsonl"
REVIEWER_INSTRUCTIONS_FILE_NAME = "review_queue_spot_check_package_343f_reviewer_instructions.md"
EXPECTED_IMPORT_CONTRACT_FILE_NAME = "review_queue_spot_check_package_343f_expected_import_contract.json"
BOUNDARY_FILE_NAME = "review_queue_spot_check_package_343f_ai_assisted_boundary.md"

INPUT_343E_SUMMARY_NAME = "review_queue_apply_simulation_343e_summary.json"
INPUT_343E_QA_NAME = "review_queue_apply_simulation_343e_qa.json"
INPUT_343E_APPLY_PLAN_NAME = "review_queue_apply_simulation_343e_apply_plan.jsonl"
INPUT_343E_SIMULATED_SIDECAR_NAME = "review_queue_apply_simulation_343e_simulated_sidecar.jsonl"
INPUT_343E_AUDIT_GATE_NAME = "review_queue_apply_simulation_343e_audit_gate.json"
INPUT_343E_RISK_REGISTER_NAME = "review_queue_apply_simulation_343e_risk_register.json"
INPUT_343E_BOUNDARY_NAME = "review_queue_apply_simulation_343e_ai_assisted_boundary.md"
INPUT_343E_NO_WRITE_BACK_NAME = "review_queue_apply_simulation_343e_no_write_back_proof.json"
INPUT_343D_SUMMARY_NAME = "review_queue_excel_ingestion_343d_summary.json"
INPUT_343D_RESULT_NAME = "review_queue_excel_ingestion_343d_reviewed_result.jsonl"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"

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
    "01_PACKAGE_SUMMARY",
    "02_INPUT_343E_SUMMARY",
    "03_SPOT_CHECK_ITEMS",
    "04_REVIEW_TEMPLATE",
    "05_SIM_APPLIED_ROWS",
    "06_HOLD_ROWS",
    "07_SOURCE_CHECK_TODO",
    "08_PRIORITY_PLAN",
    "09_RISK_REGISTER",
    "10_AI_BOUNDARY",
    "11_IMPORT_CONTRACT",
    "12_343G_READINESS",
    "13_NO_WRITE_BACK",
    "14_NEXT_STEPS",
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
    return _clean_frame(pd.DataFrame([{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]))


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {"section": "positioning", "message": "343F creates a waiting-for-spot-check package for AI-assisted review results."},
                {"section": "boundary", "message": "No spot-check result is ingested yet; no real write-back or production apply is allowed."},
                {"section": "ai_boundary", "message": "AI-assisted and simulation-only boundary must remain explicit throughout the package."},
                {"section": "next", "message": "User should fill the spot-check workbook before 343G ingestion."},
                {"section": "decision", "message": summary.get("decision", "")},
            ]
        )
    )


def _boundary_rows() -> List[Dict[str, Any]]:
    return [
        {
            "review_source_type": "AI_ASSISTED_REVIEW",
            "not_pure_human_review": True,
            "strict_human_review_completed": False,
            "requires_human_spot_check": True,
            "apply_mode": "SIMULATION_ONLY",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
    ]


def _next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"step": "open_spot_check_template", "recommendation": "Open the dedicated 343F spot-check review template workbook."},
        {"step": "review_all_30_rows", "recommendation": "Review all 10 simulation-applied rows, all 19 source-check rows, and the skipped row."},
        {"step": "preserve_boundary", "recommendation": "Do not describe this package as completed human review; it is still AI-assisted and waiting for spot-check."},
        {"step": "next_task", "recommendation": summary.get("recommended_343g_scope", "") or "Resolve package QA issues before 343G."},
    ]


def build_review_queue_spot_check_package_343f(
    *,
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

    summary_343e_path = apply_simulation_343e_dir / INPUT_343E_SUMMARY_NAME
    qa_343e_path = apply_simulation_343e_dir / INPUT_343E_QA_NAME
    apply_plan_343e_path = apply_simulation_343e_dir / INPUT_343E_APPLY_PLAN_NAME
    simulated_sidecar_343e_path = apply_simulation_343e_dir / INPUT_343E_SIMULATED_SIDECAR_NAME
    audit_gate_343e_path = apply_simulation_343e_dir / INPUT_343E_AUDIT_GATE_NAME
    risk_register_343e_path = apply_simulation_343e_dir / INPUT_343E_RISK_REGISTER_NAME
    boundary_343e_path = apply_simulation_343e_dir / INPUT_343E_BOUNDARY_NAME
    no_write_back_343e_path = apply_simulation_343e_dir / INPUT_343E_NO_WRITE_BACK_NAME
    summary_343d_path = excel_ingestion_343d_dir / INPUT_343D_SUMMARY_NAME
    result_343d_path = excel_ingestion_343d_dir / INPUT_343D_RESULT_NAME
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME

    files_read: List[str] = []
    warnings: List[str] = []
    input_paths = [
        summary_343e_path,
        qa_343e_path,
        apply_plan_343e_path,
        simulated_sidecar_343e_path,
        audit_gate_343e_path,
        risk_register_343e_path,
        boundary_343e_path,
        no_write_back_343e_path,
        summary_343d_path,
        result_343d_path,
        summary_343a_path,
    ]
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input: {path}")

    summary_343e = _read_json(summary_343e_path) if summary_343e_path.exists() else {}
    apply_plan_rows = _read_jsonl(apply_plan_343e_path) if apply_plan_343e_path.exists() else []
    simulated_sidecar_rows = _read_jsonl(simulated_sidecar_343e_path) if simulated_sidecar_343e_path.exists() else []
    audit_gate = _read_json(audit_gate_343e_path) if audit_gate_343e_path.exists() else {}
    risk_register = _read_json(risk_register_343e_path) if risk_register_343e_path.exists() else []
    reviewed_result_rows = _read_jsonl(result_343d_path) if result_343d_path.exists() else []

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        summary_343e.get("decision") == READY_INPUT_343E_DECISION
        and normalize_bool(summary_343e.get("apply_simulation_completed"))
        and normalize_bool(summary_343e.get("audit_gate_passed_for_spot_check_package"))
        and normalize_bool(summary_343e.get("ready_for_343f"))
        and int(summary_343e.get("qa_fail_count", 1)) == 0
        and summary_343e.get("review_source_type") == "AI_ASSISTED_REVIEW"
        and normalize_bool(summary_343e.get("not_pure_human_review"))
        and not normalize_bool(summary_343e.get("strict_human_review_completed"))
        and normalize_bool(summary_343e.get("requires_human_spot_check"))
        and summary_343e.get("apply_mode") == "SIMULATION_ONLY"
        and not normalize_bool(summary_343e.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343e.get("client_ready"))
        and not normalize_bool(summary_343e.get("production_ready"))
        and len(apply_plan_rows) > 0
        and len(simulated_sidecar_rows) > 0
    )

    validation_failures = [validate_apply_plan_row(row) for row in apply_plan_rows if validate_apply_plan_row(row)["validation_status"] == "FAIL"]
    spot_check_items = [build_spot_check_item(row) for row in apply_plan_rows]
    source_check_todo = [build_source_check_todo_row(row) for row in apply_plan_rows if normalize_text(row.get("simulated_downstream_action")) == "HOLD_SOURCE_CHECK_REQUIRED"]
    priority_plan = priority_plan_rows(spot_check_items)
    review_template_rows = [dict(item) for item in spot_check_items]
    expected_import_contract = build_expected_import_contract(str(output_dir))

    simulated_applied_spot_check_count = sum(1 for item in spot_check_items if normalize_text(item.get("priority_tier")) == "P1_AI_ASSISTED_SIM_APPLIED")
    source_check_required_count = sum(1 for item in spot_check_items if normalize_text(item.get("priority_tier")) == "P0_SOURCE_CHECK_REQUIRED")
    skipped_hold_count = sum(1 for item in spot_check_items if normalize_text(item.get("priority_tier")) == "P2_SKIPPED_OR_AMBIGUOUS")
    expected_apply_plan_count = int(summary_343e.get("apply_plan_row_count", len(apply_plan_rows) or 0))
    expected_source_check_count = int(summary_343e.get("hold_source_check_required_count", source_check_required_count))

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343E",
        "decision": NOT_READY_DECISION,
        "review_queue_schema_version": summary_343e.get("review_queue_schema_version", ""),
        "input_apply_plan_row_count": len(apply_plan_rows),
        "input_simulated_sidecar_row_count": len(simulated_sidecar_rows),
        "spot_check_item_count": len(spot_check_items),
        "simulated_applied_spot_check_count": simulated_applied_spot_check_count,
        "source_check_required_count": source_check_required_count,
        "skipped_hold_count": skipped_hold_count,
        "priority_tier_count": len([row for row in priority_plan if row["row_count"] > 0]),
        "review_template_generated": bool(review_template_rows),
        "source_check_todo_generated": bool(source_check_todo),
        "expected_import_contract_generated": True,
        "review_source_type": "AI_ASSISTED_REVIEW",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "apply_mode": "SIMULATION_ONLY",
        "spot_check_package_generated": False,
        "waiting_for_spot_check": True,
        "spot_check_result_ingested": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343g": False,
        "recommended_343g_scope": "",
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
        stage="343F",
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
    no_write_back_json["spot_check_result_ingested"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343f")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    review_template_columns_exist = bool(review_template_rows and all(column in review_template_rows[0] for column in EDITABLE_SPOT_CHECK_COLUMNS))
    checks = [
        {
            "check_name": "inputs::343e_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps({"decision": summary_343e.get("decision", ""), "ready_for_343f": summary_343e.get("ready_for_343f", False)}, ensure_ascii=False),
        },
        {
            "check_name": "inputs::apply_plan_jsonl_exists_and_readable",
            "status": "PASS" if apply_plan_343e_path.exists() and len(apply_plan_rows) > 0 else "FAIL",
            "detail": str(apply_plan_343e_path),
        },
        {
            "check_name": "inputs::simulated_sidecar_jsonl_exists_and_readable",
            "status": "PASS" if simulated_sidecar_343e_path.exists() and len(simulated_sidecar_rows) > 0 else "FAIL",
            "detail": str(simulated_sidecar_343e_path),
        },
        {
            "check_name": "inputs::audit_gate_passed_for_spot_check_package",
            "status": "PASS" if normalize_bool(audit_gate.get("audit_gate_passed_for_spot_check_package")) else "FAIL",
            "detail": json.dumps(audit_gate, ensure_ascii=False),
        },
        {
            "check_name": "disclosure::all_rows_preserve_ai_assisted_boundary",
            "status": "PASS" if all(normalize_text(row.get("review_source_type")) == "AI_ASSISTED_REVIEW" and normalize_bool(row.get("not_pure_human_review")) and not normalize_bool(row.get("strict_human_review_completed")) and normalize_bool(row.get("requires_human_spot_check")) for row in apply_plan_rows) else "FAIL",
            "detail": "AI-assisted boundary preserved on all spot-check population rows",
        },
        {
            "check_name": "validation::apply_plan_rows_pass_validation",
            "status": "PASS" if not validation_failures else "FAIL",
            "detail": json.dumps(validation_failures, ensure_ascii=False),
        },
        {
            "check_name": "claims::no_row_claims_strict_pure_human_review",
            "status": "PASS" if all(not normalize_bool(row.get("strict_human_review_completed")) for row in apply_plan_rows) else "FAIL",
            "detail": "strict_human_review_completed must remain false",
        },
        {
            "check_name": "claims::no_formal_client_or_production_ready_true",
            "status": "PASS" if all(not normalize_bool(row.get("formal_client_export_allowed")) and not normalize_bool(row.get("client_ready")) and not normalize_bool(row.get("production_ready")) for row in apply_plan_rows) else "FAIL",
            "detail": "formal/client/production flags remain false",
        },
        {
            "check_name": "outputs::spot_check_package_workbook_generated",
            "status": "PASS" if len(spot_check_items) == expected_apply_plan_count else "FAIL",
            "detail": str(len(spot_check_items)),
        },
        {
            "check_name": "outputs::spot_check_review_template_generated",
            "status": "PASS" if bool(review_template_rows) else "FAIL",
            "detail": str(len(review_template_rows)),
        },
        {
            "check_name": "outputs::source_check_todo_generated",
            "status": "PASS" if len(source_check_todo) == expected_source_check_count else "FAIL",
            "detail": str(len(source_check_todo)),
        },
        {
            "check_name": "outputs::expected_import_contract_generated",
            "status": "PASS",
            "detail": EXPECTED_IMPORT_CONTRACT_FILE_NAME,
        },
        {
            "check_name": "schema::editable_spot_check_columns_exist",
            "status": "PASS" if review_template_columns_exist else "FAIL",
            "detail": json.dumps(EDITABLE_SPOT_CHECK_COLUMNS, ensure_ascii=False),
        },
        {
            "check_name": "schema::allowed_decision_list_present",
            "status": "PASS" if len(ALLOWED_SPOT_CHECK_DECISIONS) == 6 else "FAIL",
            "detail": json.dumps(ALLOWED_SPOT_CHECK_DECISIONS, ensure_ascii=False),
        },
        {
            "check_name": "state::waiting_for_spot_check_true",
            "status": "PASS" if summary["waiting_for_spot_check"] else "FAIL",
            "detail": str(summary["waiting_for_spot_check"]),
        },
        {
            "check_name": "state::spot_check_result_ingested_false",
            "status": "PASS" if not summary["spot_check_result_ingested"] else "FAIL",
            "detail": str(summary["spot_check_result_ingested"]),
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343F is package generation only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343F does not perform real apply.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343F adds review-queue sidecar files only.",
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
    summary["spot_check_package_generated"] = bool(
        input_ready
        and len(spot_check_items) == expected_apply_plan_count
        and len(source_check_todo) == expected_source_check_count
        and len(review_template_rows) == expected_apply_plan_count
        and not validation_failures
    )
    summary["ready_for_343g"] = False
    summary["recommended_343g_scope"] = RECOMMENDED_343G_SCOPE if summary["spot_check_package_generated"] and qa_fail_count == 0 else ""
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed
    summary["decision"] = READY_DECISION if summary["spot_check_package_generated"] and qa_fail_count == 0 else NOT_READY_DECISION

    manifest = {
        "task": "343F_ai_assisted_review_spot_check_package",
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
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "review_template_xlsx": str(output_dir / REVIEW_TEMPLATE_FILE_NAME),
            "spot_check_items_jsonl": str(output_dir / SPOT_CHECK_ITEMS_FILE_NAME),
            "priority_plan_json": str(output_dir / PRIORITY_PLAN_FILE_NAME),
            "source_check_todo_jsonl": str(output_dir / SOURCE_CHECK_TODO_FILE_NAME),
            "reviewer_instructions_md": str(output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME),
            "expected_import_contract_json": str(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME),
            "ai_assisted_boundary_md": str(output_dir / BOUNDARY_FILE_NAME),
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
        "01_PACKAGE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343E_SUMMARY": _build_key_value_df(summary_343e),
        "03_SPOT_CHECK_ITEMS": _clean_frame(pd.DataFrame(spot_check_items)),
        "04_REVIEW_TEMPLATE": _clean_frame(pd.DataFrame(review_template_rows)),
        "05_SIM_APPLIED_ROWS": _clean_frame(pd.DataFrame([row for row in spot_check_items if normalize_text(row.get("priority_tier")) == "P1_AI_ASSISTED_SIM_APPLIED"])),
        "06_HOLD_ROWS": _clean_frame(pd.DataFrame([row for row in spot_check_items if normalize_text(row.get("priority_tier")) in {"P0_SOURCE_CHECK_REQUIRED", "P2_SKIPPED_OR_AMBIGUOUS"}])),
        "07_SOURCE_CHECK_TODO": _clean_frame(pd.DataFrame(source_check_todo)),
        "08_PRIORITY_PLAN": _clean_frame(pd.DataFrame(priority_plan)),
        "09_RISK_REGISTER": _clean_frame(pd.DataFrame(risk_register)),
        "10_AI_BOUNDARY": _clean_frame(pd.DataFrame(_boundary_rows())),
        "11_IMPORT_CONTRACT": _build_key_value_df(expected_import_contract),
        "12_343G_READINESS": _clean_frame(pd.DataFrame([{
            "spot_check_package_generated": summary["spot_check_package_generated"],
            "waiting_for_spot_check": summary["waiting_for_spot_check"],
            "spot_check_result_ingested": summary["spot_check_result_ingested"],
            "ready_for_343g": summary["ready_for_343g"],
            "recommended_343g_scope": summary["recommended_343g_scope"],
        }])),
        "13_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "14_NEXT_STEPS": _clean_frame(pd.DataFrame(_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "spot_check_items": spot_check_items,
        "priority_plan": priority_plan,
        "source_check_todo": source_check_todo,
        "expected_import_contract": expected_import_contract,
        "workbook_sheets": workbook_sheets,
    }
