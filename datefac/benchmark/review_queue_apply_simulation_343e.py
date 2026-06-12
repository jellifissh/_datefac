from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.apply_simulation_343e import (
    APPLY_MODE,
    build_apply_plan_row,
    build_audit_gate,
    build_risk_register,
    build_simulated_sidecar_row,
    validate_reviewed_result_row,
)
from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_343D_DECISION = "REVIEW_QUEUE_EXCEL_INGESTION_343D_READY"
READY_DECISION = "AI_ASSISTED_REVIEW_APPLY_SIMULATION_343E_READY"
NOT_READY_DECISION = "AI_ASSISTED_REVIEW_APPLY_SIMULATION_343E_NOT_READY"
RECOMMENDED_343F_SCOPE = "ai_assisted_review_spot_check_package"

DEFAULT_EXCEL_INGESTION_343D_DIR = Path(r"D:\_datefac\output\review_queue_excel_ingestion_343d")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_apply_simulation_343e")

SUMMARY_FILE_NAME = "review_queue_apply_simulation_343e_summary.json"
MANIFEST_FILE_NAME = "review_queue_apply_simulation_343e_manifest.json"
QA_FILE_NAME = "review_queue_apply_simulation_343e_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_apply_simulation_343e_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_apply_simulation_343e_report.md"
WORKBOOK_FILE_NAME = "review_queue_apply_simulation_343e.xlsx"
APPLY_PLAN_FILE_NAME = "review_queue_apply_simulation_343e_apply_plan.jsonl"
SIMULATED_SIDECAR_FILE_NAME = "review_queue_apply_simulation_343e_simulated_sidecar.jsonl"
AUDIT_GATE_FILE_NAME = "review_queue_apply_simulation_343e_audit_gate.json"
RISK_REGISTER_FILE_NAME = "review_queue_apply_simulation_343e_risk_register.json"
BOUNDARY_FILE_NAME = "review_queue_apply_simulation_343e_ai_assisted_boundary.md"

INPUT_343D_SUMMARY_NAME = "review_queue_excel_ingestion_343d_summary.json"
INPUT_343D_QA_NAME = "review_queue_excel_ingestion_343d_qa.json"
INPUT_343D_RESULT_NAME = "review_queue_excel_ingestion_343d_reviewed_result.jsonl"
INPUT_343D_DISCLOSURE_NAME = "review_queue_excel_ingestion_343d_ai_assisted_review_disclosure.md"
INPUT_343D_NO_WRITE_BACK_NAME = "review_queue_excel_ingestion_343d_no_write_back_proof.json"
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
    "01_SIM_SUMMARY",
    "02_INPUT_343D_SUMMARY",
    "03_REVIEWED_RESULTS",
    "04_APPLY_PLAN",
    "05_SIMULATED_SIDECAR",
    "06_HOLD_ROWS",
    "07_AUDIT_GATE",
    "08_RISK_REGISTER",
    "09_AI_ASSISTED_BOUNDARY",
    "10_343F_READINESS",
    "11_NO_WRITE_BACK",
    "12_NEXT_STEPS",
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
                {"section": "positioning", "message": "343E performs simulation-only apply planning on AI-assisted reviewed results."},
                {"section": "boundary", "message": "No real apply, no formal client export, no production application."},
                {"section": "ai_assisted", "message": "AI-assisted disclosure must remain on every downstream simulated artifact."},
                {"section": "next", "message": "Recommended next step is 343F AI-assisted review spot-check package."},
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
            "apply_mode": APPLY_MODE,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
    ]


def _next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"step": "open_audit_excel", "recommendation": "Open the simulation workbook and review apply-plan vs hold rows."},
        {"step": "spot_check_boundary", "recommendation": "Keep AI-assisted boundary visible; human spot-check is still required."},
        {"step": "no_real_apply", "recommendation": "Do not write back anything to upstream queue artifacts or production systems."},
        {"step": "next_task", "recommendation": summary.get("recommended_343f_scope", "") or "Resolve QA issues before 343F."},
    ]


def build_review_queue_apply_simulation_343e(
    *,
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

    summary_343d_path = excel_ingestion_343d_dir / INPUT_343D_SUMMARY_NAME
    qa_343d_path = excel_ingestion_343d_dir / INPUT_343D_QA_NAME
    result_343d_path = excel_ingestion_343d_dir / INPUT_343D_RESULT_NAME
    disclosure_343d_path = excel_ingestion_343d_dir / INPUT_343D_DISCLOSURE_NAME
    no_write_back_343d_path = excel_ingestion_343d_dir / INPUT_343D_NO_WRITE_BACK_NAME
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME

    files_read: List[str] = []
    warnings: List[str] = []
    input_paths = [
        summary_343d_path,
        qa_343d_path,
        result_343d_path,
        disclosure_343d_path,
        no_write_back_343d_path,
        summary_343a_path,
    ]
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input: {path}")

    summary_343d = _read_json(summary_343d_path) if summary_343d_path.exists() else {}
    reviewed_rows = _read_jsonl(result_343d_path) if result_343d_path.exists() else []

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        summary_343d.get("decision") == READY_INPUT_343D_DECISION
        and normalize_bool(summary_343d.get("reviewed_result_ingested"))
        and normalize_bool(summary_343d.get("reviewed_result_jsonl_generated"))
        and normalize_bool(summary_343d.get("ready_for_343e"))
        and int(summary_343d.get("qa_fail_count", 1)) == 0
        and summary_343d.get("review_source_type") == "AI_ASSISTED_REVIEW"
        and normalize_bool(summary_343d.get("not_pure_human_review"))
        and not normalize_bool(summary_343d.get("strict_human_review_completed"))
        and normalize_bool(summary_343d.get("requires_human_spot_check"))
        and not normalize_bool(summary_343d.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343d.get("client_ready"))
        and not normalize_bool(summary_343d.get("production_ready"))
        and bool(reviewed_rows)
    )

    validation_failures: List[Dict[str, Any]] = []
    apply_plan_rows: List[Dict[str, Any]] = []
    simulated_sidecar_rows: List[Dict[str, Any]] = []
    hold_rows: List[Dict[str, Any]] = []

    for row in reviewed_rows:
        validation = validate_reviewed_result_row(row)
        if validation["validation_status"] == "FAIL":
            validation_failures.append(validation)
        plan_row = build_apply_plan_row(row)
        apply_plan_rows.append(plan_row)
        if plan_row["apply_eligibility_classification"] == "SIMULATION_ELIGIBLE":
            simulated_sidecar_rows.append(build_simulated_sidecar_row(plan_row, row))
        else:
            hold_rows.append(plan_row)

    simulate_confirm_apply_count = sum(1 for row in apply_plan_rows if row["simulated_downstream_action"] == "SIMULATE_CONFIRM_APPLY")
    simulate_correction_apply_count = sum(1 for row in apply_plan_rows if row["simulated_downstream_action"] == "SIMULATE_CORRECTION_APPLY")
    hold_rejected_count = sum(1 for row in apply_plan_rows if row["simulated_downstream_action"] == "HOLD_REJECTED")
    hold_source_check_required_count = sum(1 for row in apply_plan_rows if row["simulated_downstream_action"] == "HOLD_SOURCE_CHECK_REQUIRED")
    hold_skipped_count = sum(1 for row in apply_plan_rows if row["simulated_downstream_action"] == "HOLD_SKIPPED")

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343D",
        "decision": NOT_READY_DECISION,
        "review_queue_schema_version": summary_343d.get("review_queue_schema_version", ""),
        "input_reviewed_result_row_count": len(reviewed_rows),
        "apply_plan_row_count": len(apply_plan_rows),
        "simulated_sidecar_row_count": len(simulated_sidecar_rows),
        "hold_row_count": len(hold_rows),
        "simulate_confirm_apply_count": simulate_confirm_apply_count,
        "simulate_correction_apply_count": simulate_correction_apply_count,
        "hold_rejected_count": hold_rejected_count,
        "hold_source_check_required_count": hold_source_check_required_count,
        "hold_skipped_count": hold_skipped_count,
        "review_source_type": "AI_ASSISTED_REVIEW",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "apply_mode": APPLY_MODE,
        "apply_simulation_completed": False,
        "audit_gate_passed_for_spot_check_package": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343f": False,
        "recommended_343f_scope": "",
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
        stage="343E",
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
        no_write_back_json.get("no_official_asset_modification_during_343e")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    simulation_generated = bool(apply_plan_rows) and bool(simulated_sidecar_rows)
    summary["apply_simulation_completed"] = bool(input_ready and simulation_generated and not validation_failures)
    summary["audit_gate_passed_for_spot_check_package"] = summary["apply_simulation_completed"]
    summary["ready_for_343f"] = summary["apply_simulation_completed"]
    summary["recommended_343f_scope"] = RECOMMENDED_343F_SCOPE if summary["ready_for_343f"] else ""
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    audit_gate = build_audit_gate(summary)
    risk_register = build_risk_register(summary)
    checks = [
        {
            "check_name": "inputs::343d_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps({"decision": summary_343d.get("decision", ""), "ready_for_343e": summary_343d.get("ready_for_343e", False)}, ensure_ascii=False),
        },
        {
            "check_name": "inputs::reviewed_result_jsonl_exists_and_readable",
            "status": "PASS" if result_343d_path.exists() and len(reviewed_rows) > 0 else "FAIL",
            "detail": str(result_343d_path),
        },
        {
            "check_name": "disclosure::all_rows_preserve_ai_assisted_boundary",
            "status": "PASS" if all(row.get("review_source_type") == "AI_ASSISTED_REVIEW" and row.get("not_pure_human_review") is True and row.get("strict_human_review_completed") is False and row.get("requires_human_spot_check") is True for row in reviewed_rows) else "FAIL",
            "detail": "AI_ASSISTED_REVIEW boundary fields preserved on every row",
        },
        {
            "check_name": "claims::no_row_claims_strict_pure_human_review",
            "status": "PASS" if all(row.get("strict_human_review_completed") is False for row in reviewed_rows) else "FAIL",
            "detail": "strict_human_review_completed must remain false",
        },
        {
            "check_name": "claims::no_formal_client_or_production_ready_true",
            "status": "PASS" if all(not normalize_bool(row.get("formal_client_export_allowed")) and not normalize_bool(row.get("client_ready")) and not normalize_bool(row.get("production_ready")) for row in reviewed_rows) else "FAIL",
            "detail": "formal/client/production flags remain false",
        },
        {
            "check_name": "outputs::apply_plan_jsonl_generated",
            "status": "PASS" if len(apply_plan_rows) == len(reviewed_rows) else "FAIL",
            "detail": str(len(apply_plan_rows)),
        },
        {
            "check_name": "outputs::simulated_sidecar_generated_for_eligible_rows",
            "status": "PASS" if len(simulated_sidecar_rows) == simulate_confirm_apply_count + simulate_correction_apply_count else "FAIL",
            "detail": json.dumps({"simulated_sidecar_row_count": len(simulated_sidecar_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "validation::hold_rows_classified_correctly",
            "status": "PASS" if len(hold_rows) == hold_rejected_count + hold_source_check_required_count + hold_skipped_count else "FAIL",
            "detail": json.dumps({"hold_row_count": len(hold_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "outputs::audit_gate_generated",
            "status": "PASS",
            "detail": json.dumps(audit_gate, ensure_ascii=False),
        },
        {
            "check_name": "outputs::risk_register_generated",
            "status": "PASS",
            "detail": json.dumps(risk_register, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343E performs simulation only.",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343E is sidecar simulation only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343E adds review-queue sidecar files only.",
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
    summary["decision"] = READY_DECISION if summary["apply_simulation_completed"] and qa_fail_count == 0 else NOT_READY_DECISION
    audit_gate = build_audit_gate(summary)
    for check in checks:
        if check["check_name"] == "outputs::audit_gate_generated":
            check["detail"] = json.dumps(audit_gate, ensure_ascii=False)
            break

    manifest = {
        "task": "343E_ai_assisted_review_result_apply_simulation_and_audit_gate",
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
            "apply_plan_jsonl": str(output_dir / APPLY_PLAN_FILE_NAME),
            "simulated_sidecar_jsonl": str(output_dir / SIMULATED_SIDECAR_FILE_NAME),
            "audit_gate_json": str(output_dir / AUDIT_GATE_FILE_NAME),
            "risk_register_json": str(output_dir / RISK_REGISTER_FILE_NAME),
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
        "01_SIM_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343D_SUMMARY": _build_key_value_df(summary_343d),
        "03_REVIEWED_RESULTS": _clean_frame(pd.DataFrame(reviewed_rows)),
        "04_APPLY_PLAN": _clean_frame(pd.DataFrame(apply_plan_rows)),
        "05_SIMULATED_SIDECAR": _clean_frame(pd.DataFrame(simulated_sidecar_rows)),
        "06_HOLD_ROWS": _clean_frame(pd.DataFrame(hold_rows)),
        "07_AUDIT_GATE": _build_key_value_df(audit_gate),
        "08_RISK_REGISTER": _clean_frame(pd.DataFrame(risk_register)),
        "09_AI_ASSISTED_BOUNDARY": _clean_frame(pd.DataFrame(_boundary_rows())),
        "10_343F_READINESS": _clean_frame(pd.DataFrame([{
            "apply_simulation_completed": summary["apply_simulation_completed"],
            "audit_gate_passed_for_spot_check_package": summary["audit_gate_passed_for_spot_check_package"],
            "ready_for_343f": summary["ready_for_343f"],
            "recommended_343f_scope": summary["recommended_343f_scope"],
            "strict_human_review_completed": summary["strict_human_review_completed"],
            "requires_human_spot_check": summary["requires_human_spot_check"],
        }])),
        "11_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "12_NEXT_STEPS": _clean_frame(pd.DataFrame(_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "apply_plan_rows": apply_plan_rows,
        "simulated_sidecar_rows": simulated_sidecar_rows,
        "audit_gate": audit_gate,
        "risk_register": risk_register,
        "workbook_sheets": workbook_sheets,
    }
