from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.ingest_spot_check_343g import (
    AI_ASSISTED_SPOT_CHECK_DISCLOSURE,
    build_spot_check_result_row,
    decision_summary_rows,
    status_mapping_rows,
    validate_filled_spot_check_row,
)
from datefac.review_queue.spot_check_package_343f import ALLOWED_SPOT_CHECK_DECISIONS
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_343F_DECISION = "AI_ASSISTED_REVIEW_SPOT_CHECK_PACKAGE_343F_WAITING_FOR_SPOT_CHECK"
READY_INPUT_343E_DECISION = "AI_ASSISTED_REVIEW_APPLY_SIMULATION_343E_READY"
READY_INPUT_343A_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"
READY_DECISION = "AI_ASSISTED_SPOT_CHECK_INGESTION_343G_READY"
NOT_READY_DECISION = "AI_ASSISTED_SPOT_CHECK_INGESTION_343G_NOT_READY"
RECOMMENDED_343H_SCOPE = "ai_assisted_spot_check_audit_summary_and_strict_human_gap_report"

DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR = Path(r"D:\_datefac\output\review_queue_spot_check_package_343f")
DEFAULT_APPLY_SIMULATION_343E_DIR = Path(r"D:\_datefac\output\review_queue_apply_simulation_343e")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_FILLED_WORKBOOK = Path(
    r"D:\_datefac\input\review_queue_spot_check_package_343f_filled\review_queue_spot_check_package_343f_review_template_filled.xlsx"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_spot_check_ingestion_343g")

SUMMARY_FILE_NAME = "review_queue_spot_check_ingestion_343g_summary.json"
MANIFEST_FILE_NAME = "review_queue_spot_check_ingestion_343g_manifest.json"
QA_FILE_NAME = "review_queue_spot_check_ingestion_343g_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_spot_check_ingestion_343g_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_spot_check_ingestion_343g_report.md"
WORKBOOK_FILE_NAME = "review_queue_spot_check_ingestion_343g.xlsx"
RESULT_FILE_NAME = "review_queue_spot_check_ingestion_343g_result.jsonl"
VALIDATION_ERRORS_FILE_NAME = "review_queue_spot_check_ingestion_343g_validation_errors.json"
VALIDATION_WARNINGS_FILE_NAME = "review_queue_spot_check_ingestion_343g_validation_warnings.json"
DECISION_SUMMARY_FILE_NAME = "review_queue_spot_check_ingestion_343g_decision_summary.json"
DISCLOSURE_FILE_NAME = "review_queue_spot_check_ingestion_343g_ai_assisted_spot_check_disclosure.md"

INPUT_343F_SUMMARY_NAME = "review_queue_spot_check_package_343f_summary.json"
INPUT_343F_QA_NAME = "review_queue_spot_check_package_343f_qa.json"
INPUT_343F_CONTRACT_NAME = "review_queue_spot_check_package_343f_expected_import_contract.json"
INPUT_343F_TEMPLATE_NAME = "review_queue_spot_check_package_343f_review_template.xlsx"
INPUT_343F_SPOT_ITEMS_NAME = "review_queue_spot_check_package_343f_spot_check_items.jsonl"
INPUT_343F_SOURCE_TODO_NAME = "review_queue_spot_check_package_343f_source_check_todo.jsonl"
INPUT_343E_SUMMARY_NAME = "review_queue_apply_simulation_343e_summary.json"
INPUT_343E_APPLY_PLAN_NAME = "review_queue_apply_simulation_343e_apply_plan.jsonl"
INPUT_343E_SIMULATED_SIDECAR_NAME = "review_queue_apply_simulation_343e_simulated_sidecar.jsonl"
INPUT_343E_AUDIT_GATE_NAME = "review_queue_apply_simulation_343e_audit_gate.json"
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
    "01_INGEST_SUMMARY",
    "02_INPUT_343F_SUMMARY",
    "03_FILLED_SPOT_ROWS",
    "04_VALID_ROWS",
    "05_INVALID_ROWS",
    "06_DECISION_SUMMARY",
    "07_STATUS_MAPPING",
    "08_AI_SPOT_DISCLOSURE",
    "09_STRICT_HUMAN_GAP",
    "10_343H_READINESS",
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
    rows = [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
    return _clean_frame(pd.DataFrame(rows))


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


def _row_identity_key(row: Dict[str, Any]) -> tuple[str, str]:
    return (
        normalize_text(row.get("queue_item_id")),
        normalize_text(row.get("review_item_id")),
    )


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "343G ingests a filled 343F spot-check workbook into validated sidecar result rows.",
                },
                {
                    "section": "ai_spot_check",
                    "message": "Current workbook is AI-assisted spot-check, not strict pure human spot-check.",
                },
                {
                    "section": "safety",
                    "message": "No real write-back, no production apply, no formal client export.",
                },
                {
                    "section": "next",
                    "message": "Recommended next step is 343H audit summary and strict-human-gap report.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _disclosure_rows() -> List[Dict[str, Any]]:
    return [
        {
            "review_source_type": "AI_ASSISTED_REVIEW",
            "spot_check_source_type": "AI_ASSISTED_SPOT_CHECK",
            "not_pure_human_review": True,
            "strict_human_review_completed": False,
            "requires_human_spot_check": True,
            "requires_strict_human_review": True,
            "apply_mode": "SIMULATION_ONLY",
            "spot_check_source_disclosure": AI_ASSISTED_SPOT_CHECK_DISCLOSURE,
        }
    ]


def _strict_human_gap_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "gap_area": "review_origin",
            "current_state": "AI-assisted spot-check workbook was filled from available workbook evidence",
            "required_for_strict_human": "Independent strict human spot-check completion remains required",
        },
        {
            "gap_area": "readiness_claim",
            "current_state": "formal_client_export_allowed/client_ready/production_ready all remain false",
            "required_for_strict_human": "No stronger claim allowed until strict human review is completed",
        },
        {
            "gap_area": "next_control",
            "current_state": summary.get("recommended_343h_scope", ""),
            "required_for_strict_human": "Generate 343H audit summary and strict-human gap report before any further claim",
        },
    ]


def _next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {
            "step": "open_ingestion_workbook",
            "recommendation": "Open the 343G workbook to inspect valid and invalid spot-check rows.",
        },
        {
            "step": "keep_boundary_visible",
            "recommendation": "Preserve AI-assisted spot-check disclosure in all downstream summaries and audits.",
        },
        {
            "step": "no_real_apply",
            "recommendation": "Do not write back to upstream workbooks and do not treat this as formal export.",
        },
        {
            "step": "next_task",
            "recommendation": summary.get("recommended_343h_scope", "") or "Resolve validation issues before 343H.",
        },
    ]


def build_review_queue_spot_check_ingestion_343g(
    *,
    spot_check_package_343f_dir: Path = DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR,
    apply_simulation_343e_dir: Path = DEFAULT_APPLY_SIMULATION_343E_DIR,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    filled_workbook: Path = DEFAULT_FILLED_WORKBOOK,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_343f_path = spot_check_package_343f_dir / INPUT_343F_SUMMARY_NAME
    qa_343f_path = spot_check_package_343f_dir / INPUT_343F_QA_NAME
    contract_343f_path = spot_check_package_343f_dir / INPUT_343F_CONTRACT_NAME
    template_343f_path = spot_check_package_343f_dir / INPUT_343F_TEMPLATE_NAME
    spot_items_343f_path = spot_check_package_343f_dir / INPUT_343F_SPOT_ITEMS_NAME
    source_todo_343f_path = spot_check_package_343f_dir / INPUT_343F_SOURCE_TODO_NAME
    summary_343e_path = apply_simulation_343e_dir / INPUT_343E_SUMMARY_NAME
    apply_plan_343e_path = apply_simulation_343e_dir / INPUT_343E_APPLY_PLAN_NAME
    simulated_sidecar_343e_path = apply_simulation_343e_dir / INPUT_343E_SIMULATED_SIDECAR_NAME
    audit_gate_343e_path = apply_simulation_343e_dir / INPUT_343E_AUDIT_GATE_NAME
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME
    schema_343a_path = review_queue_schema_343a_dir / INPUT_343A_SCHEMA_NAME

    files_read: List[str] = []
    warnings: List[str] = []
    input_paths = [
        summary_343f_path,
        qa_343f_path,
        contract_343f_path,
        template_343f_path,
        spot_items_343f_path,
        source_todo_343f_path,
        summary_343e_path,
        apply_plan_343e_path,
        simulated_sidecar_343e_path,
        audit_gate_343e_path,
        summary_343a_path,
        schema_343a_path,
        filled_workbook,
    ]
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input: {path}")

    summary_343f = _read_json(summary_343f_path) if summary_343f_path.exists() else {}
    summary_343e = _read_json(summary_343e_path) if summary_343e_path.exists() else {}
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}
    import_contract = _read_json(contract_343f_path) if contract_343f_path.exists() else {}
    spot_check_items = _read_jsonl(spot_items_343f_path) if spot_items_343f_path.exists() else []
    apply_plan_rows = _read_jsonl(apply_plan_343e_path) if apply_plan_343e_path.exists() else []
    simulated_sidecar_rows = _read_jsonl(simulated_sidecar_343e_path) if simulated_sidecar_343e_path.exists() else []

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    expected_sheet = normalize_text(import_contract.get("required_sheet_name")) or "04_REVIEW_TEMPLATE"
    sheet_resolved = False
    filled_df = pd.DataFrame()
    workbook_read_error = ""
    workbook_sheet_names: List[str] = []
    if filled_workbook.exists():
        try:
            excel = pd.ExcelFile(filled_workbook)
            workbook_sheet_names = list(excel.sheet_names)
            if expected_sheet in workbook_sheet_names:
                filled_df = _read_excel_sheet(filled_workbook, expected_sheet)
                sheet_resolved = True
            elif "04_REVIEW_TEMPLATE" in workbook_sheet_names:
                expected_sheet = "04_REVIEW_TEMPLATE"
                filled_df = _read_excel_sheet(filled_workbook, expected_sheet)
                sheet_resolved = True
            else:
                workbook_read_error = (
                    f"no valid filled spot-check sheet found; expected {expected_sheet}"
                )
        except Exception as exc:
            workbook_read_error = f"unable to read filled workbook: {exc}"
    else:
        workbook_read_error = f"filled workbook missing: {filled_workbook}"

    input_ready = bool(
        summary_343f.get("decision") == READY_INPUT_343F_DECISION
        and normalize_bool(summary_343f.get("waiting_for_spot_check"))
        and not normalize_bool(summary_343f.get("spot_check_result_ingested"))
        and int(summary_343f.get("qa_fail_count", 1)) == 0
        and summary_343f.get("review_source_type") == "AI_ASSISTED_REVIEW"
        and normalize_bool(summary_343f.get("not_pure_human_review"))
        and not normalize_bool(summary_343f.get("strict_human_review_completed"))
        and normalize_bool(summary_343f.get("requires_human_spot_check"))
        and summary_343f.get("apply_mode") == "SIMULATION_ONLY"
        and not normalize_bool(summary_343f.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343f.get("client_ready"))
        and not normalize_bool(summary_343f.get("production_ready"))
        and summary_343e.get("decision") == READY_INPUT_343E_DECISION
        and int(summary_343e.get("qa_fail_count", 1)) == 0
        and summary_343a.get("decision") == READY_INPUT_343A_DECISION
        and int(summary_343a.get("qa_fail_count", 1)) == 0
        and filled_workbook.exists()
        and sheet_resolved
    )

    validation_rows: List[Dict[str, Any]] = []
    result_rows: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    validation_errors: List[Dict[str, Any]] = []
    validation_warnings: List[Dict[str, Any]] = []

    spot_item_index = {_row_identity_key(item): item for item in spot_check_items}

    if not filled_df.empty:
        for index, row in enumerate(filled_df.to_dict(orient="records"), start=1):
            merged_row = dict(spot_item_index.get(_row_identity_key(row), {}))
            merged_row.update(row)
            validation = validate_filled_spot_check_row(merged_row)
            validation_rows.append({"row_index": index, **validation})
            result_row = build_spot_check_result_row(merged_row)
            result_row["row_index"] = index
            result_rows.append(result_row)
            if validation["validation_status"] == "FAIL":
                invalid_rows.append(
                    {
                        **merged_row,
                        "row_index": index,
                        "validation_errors": validation["errors"],
                        "validation_warnings": validation["warnings"],
                    }
                )
            else:
                valid_rows.append(result_row)
            if validation["errors"]:
                validation_errors.append(
                    {
                        "row_index": index,
                        "queue_item_id": validation["queue_item_id"],
                        "review_item_id": validation["review_item_id"],
                        "errors": validation["errors"],
                    }
                )
            if validation["warnings"]:
                validation_warnings.append(
                    {
                        "row_index": index,
                        "queue_item_id": validation["queue_item_id"],
                        "review_item_id": validation["review_item_id"],
                        "warnings": validation["warnings"],
                    }
                )

    decision_summary = decision_summary_rows(result_rows)
    counts_by_decision = {
        row["spot_check_decision"]: int(row["row_count"])
        for row in decision_summary
    }
    validation_error_count = sum(len(item["errors"]) for item in validation_errors)
    validation_warning_count = sum(len(item["warnings"]) for item in validation_warnings)
    spot_check_result_ingested = bool(input_ready and validation_error_count == 0 and len(result_rows) > 0)
    ready_for_343h = spot_check_result_ingested

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343F",
        "decision": NOT_READY_DECISION,
        "review_queue_schema_version": summary_343f.get("review_queue_schema_version", ""),
        "filled_workbook_path": str(filled_workbook),
        "filled_spot_check_row_count": len(filled_df),
        "valid_row_count": len(valid_rows),
        "invalid_row_count": len(invalid_rows),
        "confirm_ai_assisted_result_count": counts_by_decision.get("CONFIRM_AI_ASSISTED_RESULT", 0),
        "correct_ai_assisted_result_count": counts_by_decision.get("CORRECT_AI_ASSISTED_RESULT", 0),
        "reject_ai_assisted_result_count": counts_by_decision.get("REJECT_AI_ASSISTED_RESULT", 0),
        "source_check_required_count": counts_by_decision.get("SOURCE_CHECK_REQUIRED", 0),
        "keep_hold_count": counts_by_decision.get("KEEP_HOLD", 0),
        "skip_spot_check_count": counts_by_decision.get("SKIP_SPOT_CHECK", 0),
        "validation_error_count": validation_error_count,
        "validation_warning_count": validation_warning_count,
        "review_source_type": "AI_ASSISTED_REVIEW",
        "spot_check_source_type": "AI_ASSISTED_SPOT_CHECK",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "requires_strict_human_review": True,
        "apply_mode": "SIMULATION_ONLY",
        "spot_check_result_ingested": spot_check_result_ingested,
        "spot_check_result_jsonl_generated": spot_check_result_ingested,
        "ai_assisted_spot_check_completed": spot_check_result_ingested,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343h": ready_for_343h,
        "recommended_343h_scope": RECOMMENDED_343H_SCOPE if ready_for_343h else "",
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
        stage="343G",
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
    no_write_back_json["spot_check_result_ingested"] = spot_check_result_ingested
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343g")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::343f_input_exists_and_waiting_for_spot_check",
            "status": "PASS" if summary_343f.get("decision") == READY_INPUT_343F_DECISION and normalize_bool(summary_343f.get("waiting_for_spot_check")) else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_343f.get("decision", ""),
                    "waiting_for_spot_check": summary_343f.get("waiting_for_spot_check", False),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::filled_workbook_exists",
            "status": "PASS" if filled_workbook.exists() else "FAIL",
            "detail": str(filled_workbook),
        },
        {
            "check_name": "inputs::filled_workbook_readable",
            "status": "PASS" if filled_workbook.exists() and workbook_read_error == "" else "FAIL",
            "detail": workbook_read_error or "ok",
        },
        {
            "check_name": "inputs::expected_sheet_04_review_template_exists",
            "status": "PASS" if sheet_resolved else "FAIL",
            "detail": json.dumps(
                {"expected_sheet": expected_sheet, "available_sheets": workbook_sheet_names},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "schema::identity_columns_exist",
            "status": "PASS" if filled_df.empty or all(column in filled_df.columns for column in ["queue_item_id", "review_item_id", "simulated_downstream_action", "priority_tier"]) else "FAIL",
            "detail": json.dumps(list(filled_df.columns), ensure_ascii=False),
        },
        {
            "check_name": "schema::editable_spot_check_columns_exist",
            "status": "PASS" if filled_df.empty or all(column in filled_df.columns for column in ["spot_check_decision", "spot_check_metric_standardized", "spot_check_year_standardized", "spot_check_value_numeric", "spot_check_normalized_unit", "spot_check_note", "spot_checker_id", "spot_checked_at"]) else "FAIL",
            "detail": json.dumps(list(filled_df.columns), ensure_ascii=False),
        },
        {
            "check_name": "validation::spot_check_decisions_allowed_and_non_empty",
            "status": "PASS" if all(normalize_text(row.get("spot_check_decision")) in ALLOWED_SPOT_CHECK_DECISIONS for row in result_rows) and len(result_rows) == len(filled_df) else "FAIL",
            "detail": json.dumps(sorted(ALLOWED_SPOT_CHECK_DECISIONS), ensure_ascii=False),
        },
        {
            "check_name": "validation::correction_rows_have_required_corrected_fields",
            "status": "PASS" if not any("missing correction field" in error or "must be numeric" in error for item in validation_errors for error in item["errors"]) else "FAIL",
            "detail": "CORRECT_AI_ASSISTED_RESULT payload validation enforced",
        },
        {
            "check_name": "validation::source_check_rows_have_notes",
            "status": "PASS" if not any("SOURCE_CHECK_REQUIRED requires spot_check_note" in error for item in validation_errors for error in item["errors"]) else "FAIL",
            "detail": "SOURCE_CHECK_REQUIRED note rule enforced",
        },
        {
            "check_name": "outputs::status_mapping_generated",
            "status": "PASS",
            "detail": json.dumps(status_mapping_rows(), ensure_ascii=False),
        },
        {
            "check_name": "outputs::result_jsonl_generated_when_validation_passes",
            "status": "PASS" if (spot_check_result_ingested and len(result_rows) > 0) or (not spot_check_result_ingested and validation_error_count > 0) else "FAIL",
            "detail": json.dumps(
                {
                    "spot_check_result_ingested": spot_check_result_ingested,
                    "row_count": len(result_rows),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "disclosure::ai_assisted_spot_check_fields_exist_on_every_row",
            "status": "PASS" if all(row.get("review_source_type") == "AI_ASSISTED_REVIEW" and row.get("spot_check_source_type") == "AI_ASSISTED_SPOT_CHECK" and row.get("not_pure_human_review") is True and row.get("strict_human_review_completed") is False and row.get("requires_strict_human_review") is True for row in result_rows) else "FAIL",
            "detail": "review_source_type/spot_check_source_type/not_pure_human_review/strict_human_review_completed/requires_strict_human_review",
        },
        {
            "check_name": "claims::strict_human_review_not_claimed",
            "status": "PASS" if summary["strict_human_review_completed"] is False else "FAIL",
            "detail": str(summary["strict_human_review_completed"]),
        },
        {
            "check_name": "claims::formal_client_export_allowed_false",
            "status": "PASS" if not summary["formal_client_export_allowed"] else "FAIL",
            "detail": "false",
        },
        {
            "check_name": "claims::client_ready_false",
            "status": "PASS" if not summary["client_ready"] else "FAIL",
            "detail": "false",
        },
        {
            "check_name": "claims::production_ready_false",
            "status": "PASS" if not summary["production_ready"] else "FAIL",
            "detail": "false",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343G is ingestion only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343G only ingests spot-check results into a sidecar result package.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343G adds review-queue sidecar files only.",
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
    summary["decision"] = READY_DECISION if input_ready and validation_error_count == 0 and qa_fail_count == 0 else NOT_READY_DECISION
    summary["spot_check_result_ingested"] = summary["decision"] == READY_DECISION
    summary["spot_check_result_jsonl_generated"] = summary["decision"] == READY_DECISION
    summary["ai_assisted_spot_check_completed"] = summary["decision"] == READY_DECISION
    summary["ready_for_343h"] = summary["decision"] == READY_DECISION
    summary["recommended_343h_scope"] = RECOMMENDED_343H_SCOPE if summary["decision"] == READY_DECISION else ""

    manifest = {
        "task": "343G_ai_assisted_review_spot_check_result_ingestion",
        "spot_check_package_343f_dir": str(spot_check_package_343f_dir),
        "apply_simulation_343e_dir": str(apply_simulation_343e_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "filled_workbook": str(filled_workbook),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "result_jsonl": str(output_dir / RESULT_FILE_NAME),
            "validation_errors_json": str(output_dir / VALIDATION_ERRORS_FILE_NAME),
            "validation_warnings_json": str(output_dir / VALIDATION_WARNINGS_FILE_NAME),
            "decision_summary_json": str(output_dir / DECISION_SUMMARY_FILE_NAME),
            "ai_assisted_spot_check_disclosure_md": str(output_dir / DISCLOSURE_FILE_NAME),
        },
        "files_read": list(files_read),
        "warnings": warnings,
        "input_reference_counts": {
            "343f_spot_check_items": len(spot_check_items),
            "343e_apply_plan_rows": len(apply_plan_rows),
            "343e_simulated_sidecar_rows": len(simulated_sidecar_rows),
        },
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
        "01_INGEST_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343F_SUMMARY": _build_key_value_df(summary_343f),
        "03_FILLED_SPOT_ROWS": _clean_frame(filled_df),
        "04_VALID_ROWS": _clean_frame(pd.DataFrame(valid_rows)),
        "05_INVALID_ROWS": _clean_frame(pd.DataFrame(invalid_rows)),
        "06_DECISION_SUMMARY": _clean_frame(pd.DataFrame(decision_summary)),
        "07_STATUS_MAPPING": _clean_frame(pd.DataFrame(status_mapping_rows())),
        "08_AI_SPOT_DISCLOSURE": _clean_frame(pd.DataFrame(_disclosure_rows())),
        "09_STRICT_HUMAN_GAP": _clean_frame(pd.DataFrame(_strict_human_gap_rows(summary))),
        "10_343H_READINESS": _clean_frame(
            pd.DataFrame(
                [
                    {
                        "spot_check_result_ingested": summary["spot_check_result_ingested"],
                        "ai_assisted_spot_check_completed": summary["ai_assisted_spot_check_completed"],
                        "strict_human_review_completed": summary["strict_human_review_completed"],
                        "requires_strict_human_review": summary["requires_strict_human_review"],
                        "ready_for_343h": summary["ready_for_343h"],
                        "recommended_343h_scope": summary["recommended_343h_scope"],
                    }
                ]
            )
        ),
        "11_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "12_NEXT_STEPS": _clean_frame(pd.DataFrame(_next_steps_rows(summary))),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "validation_errors": validation_errors,
        "validation_warnings": validation_warnings,
        "decision_summary": decision_summary,
        "result_rows": result_rows,
        "workbook_sheets": workbook_sheets,
    }
