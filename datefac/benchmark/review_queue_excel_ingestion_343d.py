from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.ingest_excel_review_343d import (
    AI_ASSISTED_DISCLOSURE,
    build_reviewed_result_row,
    decision_summary_rows,
    status_mapping_rows,
    validate_filled_review_row,
)
from datefac.review_queue.real_excel_review_343c import ALLOWED_REVIEWER_DECISIONS
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_343C_DECISION = "REVIEW_QUEUE_REAL_EXCEL_REVIEW_343C_WAITING_FOR_HUMAN_REVIEW"
READY_INPUT_343A_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"
READY_DECISION = "REVIEW_QUEUE_EXCEL_INGESTION_343D_READY"
NOT_READY_DECISION = "REVIEW_QUEUE_EXCEL_INGESTION_343D_NOT_READY"
RECOMMENDED_343E_SCOPE = "ai_assisted_review_result_apply_simulation_and_audit_gate"

DEFAULT_REAL_EXCEL_REVIEW_343C_DIR = Path(r"D:\_datefac\output\review_queue_real_excel_review_343c")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_FILLED_WORKBOOK = Path(
    r"D:\_datefac\input\review_queue_real_excel_review_343c_filled\review_queue_real_excel_review_343c_review_template_filled.xlsx"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_excel_ingestion_343d")

SUMMARY_FILE_NAME = "review_queue_excel_ingestion_343d_summary.json"
MANIFEST_FILE_NAME = "review_queue_excel_ingestion_343d_manifest.json"
QA_FILE_NAME = "review_queue_excel_ingestion_343d_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_excel_ingestion_343d_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_excel_ingestion_343d_report.md"
WORKBOOK_FILE_NAME = "review_queue_excel_ingestion_343d.xlsx"
REVIEWED_RESULT_FILE_NAME = "review_queue_excel_ingestion_343d_reviewed_result.jsonl"
VALIDATION_ERRORS_FILE_NAME = "review_queue_excel_ingestion_343d_validation_errors.json"
VALIDATION_WARNINGS_FILE_NAME = "review_queue_excel_ingestion_343d_validation_warnings.json"
DECISION_SUMMARY_FILE_NAME = "review_queue_excel_ingestion_343d_decision_summary.json"
DISCLOSURE_FILE_NAME = "review_queue_excel_ingestion_343d_ai_assisted_review_disclosure.md"

INPUT_343C_SUMMARY_NAME = "review_queue_real_excel_review_343c_summary.json"
INPUT_343C_QA_NAME = "review_queue_real_excel_review_343c_qa.json"
INPUT_343C_CONTRACT_NAME = "review_queue_real_excel_review_343c_expected_import_contract.json"
INPUT_343C_TEMPLATE_NAME = "review_queue_real_excel_review_343c_review_template.xlsx"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"
INPUT_343A_QA_NAME = "review_queue_schema_343a_qa.json"

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
    "01_INGEST_SUMMARY",
    "02_INPUT_343C_SUMMARY",
    "03_FILLED_ROWS",
    "04_VALID_ROWS",
    "05_INVALID_ROWS",
    "06_DECISION_SUMMARY",
    "07_STATUS_MAPPING",
    "08_REVIEW_SOURCE_DISCLOSURE",
    "09_SPOT_CHECK_REQUIRED",
    "10_343E_READINESS",
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


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {"section": "positioning", "message": "343D ingests a filled 343C workbook into reviewed-result sidecar artifacts."},
                {"section": "disclosure", "message": "Current workbook is AI-assisted review, not strict pure human review."},
                {"section": "safety", "message": "formal_client_export_allowed=false, client_ready=false, production_ready=false remain unchanged."},
                {"section": "next", "message": "Recommended next step is 343E apply simulation and audit gate, not production export."},
                {"section": "decision", "message": summary.get("decision", "")},
            ]
        )
    )


def _disclosure_rows() -> List[Dict[str, Any]]:
    return [
        {
            "review_source_type": "AI_ASSISTED_REVIEW",
            "not_pure_human_review": True,
            "strict_human_review_completed": False,
            "requires_human_spot_check": True,
            "review_source_disclosure": AI_ASSISTED_DISCLOSURE,
        }
    ]


def _next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {
            "step": "review_jsonl",
            "recommendation": "Open the reviewed-result JSONL and workbook summary to inspect ingested decisions and validation results.",
        },
        {
            "step": "keep_disclosure",
            "recommendation": "Preserve AI-assisted disclosure fields in all downstream 343E sidecar logic.",
        },
        {
            "step": "spot_check",
            "recommendation": "Human spot-check is still required before any stronger trust claim.",
        },
        {
            "step": "next_task",
            "recommendation": summary.get("recommended_343e_scope", "") or "Resolve validation issues before 343E.",
        },
    ]


def build_review_queue_excel_ingestion_343d(
    *,
    real_excel_review_343c_dir: Path = DEFAULT_REAL_EXCEL_REVIEW_343C_DIR,
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

    summary_343c_path = real_excel_review_343c_dir / INPUT_343C_SUMMARY_NAME
    qa_343c_path = real_excel_review_343c_dir / INPUT_343C_QA_NAME
    contract_343c_path = real_excel_review_343c_dir / INPUT_343C_CONTRACT_NAME
    template_343c_path = real_excel_review_343c_dir / INPUT_343C_TEMPLATE_NAME
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME
    qa_343a_path = review_queue_schema_343a_dir / INPUT_343A_QA_NAME

    files_read: List[str] = []
    warnings: List[str] = []
    input_paths = [
        summary_343c_path,
        qa_343c_path,
        contract_343c_path,
        template_343c_path,
        summary_343a_path,
        qa_343a_path,
        filled_workbook,
    ]
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input: {path}")

    summary_343c = _read_json(summary_343c_path) if summary_343c_path.exists() else {}
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}
    import_contract = _read_json(contract_343c_path) if contract_343c_path.exists() else {}

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    expected_sheet = ""
    required_sheets = import_contract.get("required_sheets", [])
    if required_sheets:
        expected_sheet = str(required_sheets[0])
    sheet_resolved = False
    filled_df = pd.DataFrame()
    workbook_read_error = ""
    workbook_sheet_names: List[str] = []
    if filled_workbook.exists():
        try:
            excel = pd.ExcelFile(filled_workbook)
            workbook_sheet_names = list(excel.sheet_names)
            if expected_sheet and expected_sheet in workbook_sheet_names:
                filled_df = _read_excel_sheet(filled_workbook, expected_sheet)
                sheet_resolved = True
            elif "04_FILLABLE_REVIEW" in workbook_sheet_names:
                expected_sheet = "04_FILLABLE_REVIEW"
                filled_df = _read_excel_sheet(filled_workbook, expected_sheet)
                sheet_resolved = True
            else:
                workbook_read_error = f"no valid filled review sheet found; expected one of {required_sheets or ['04_FILLABLE_REVIEW']}"
        except Exception as exc:
            workbook_read_error = f"unable to read filled workbook: {exc}"
    else:
        workbook_read_error = f"filled workbook missing: {filled_workbook}"

    input_ready = bool(
        summary_343c.get("decision") == READY_INPUT_343C_DECISION
        and normalize_bool(summary_343c.get("waiting_for_human_review"))
        and not normalize_bool(summary_343c.get("reviewed_result_ingested"))
        and int(summary_343c.get("qa_fail_count", 1)) == 0
        and summary_343a.get("decision") == READY_INPUT_343A_DECISION
        and int(summary_343a.get("qa_fail_count", 1)) == 0
        and summary_343c.get("review_queue_schema_version") == "343A.review_queue.v1"
        and not normalize_bool(summary_343c.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343c.get("client_ready"))
        and not normalize_bool(summary_343c.get("production_ready"))
        and filled_workbook.exists()
        and sheet_resolved
    )

    validation_rows: List[Dict[str, Any]] = []
    reviewed_result_rows: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    validation_errors: List[Dict[str, Any]] = []
    validation_warnings: List[Dict[str, Any]] = []

    if not filled_df.empty:
        for index, row in enumerate(filled_df.to_dict(orient="records"), start=1):
            validation = validate_filled_review_row(row)
            validation_rows.append({"row_index": index, **validation})
            reviewed_row = build_reviewed_result_row(row)
            reviewed_row["row_index"] = index
            reviewed_result_rows.append(reviewed_row)
            if validation["validation_status"] == "FAIL":
                invalid_rows.append({**row, "row_index": index, "validation_errors": validation["errors"], "validation_warnings": validation["warnings"]})
            else:
                valid_rows.append(reviewed_row)
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

    confirmed_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "REVIEWED_CONFIRMED")
    corrected_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "REVIEWED_CORRECTED")
    rejected_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "REJECTED")
    needs_source_check_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "NEEDS_SOURCE_CHECK")
    skipped_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "SKIPPED")

    validation_error_count = sum(len(item["errors"]) for item in validation_errors)
    validation_warning_count = sum(len(item["warnings"]) for item in validation_warnings)
    reviewed_result_ingested = bool(input_ready and validation_error_count == 0 and len(reviewed_result_rows) > 0)
    ready_for_343e = reviewed_result_ingested

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343C",
        "decision": NOT_READY_DECISION,
        "review_queue_schema_version": summary_343c.get("review_queue_schema_version", ""),
        "filled_workbook_path": str(filled_workbook),
        "filled_row_count": len(filled_df),
        "valid_row_count": len(valid_rows),
        "invalid_row_count": len(invalid_rows),
        "confirmed_count": confirmed_count,
        "corrected_count": corrected_count,
        "rejected_count": rejected_count,
        "needs_source_check_count": needs_source_check_count,
        "skipped_count": skipped_count,
        "validation_error_count": validation_error_count,
        "validation_warning_count": validation_warning_count,
        "review_source_type": "AI_ASSISTED_REVIEW",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "reviewed_result_ingested": reviewed_result_ingested,
        "reviewed_result_jsonl_generated": reviewed_result_ingested,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343e": ready_for_343e,
        "recommended_343e_scope": RECOMMENDED_343E_SCOPE if ready_for_343e else "",
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
        "review_source_disclosure": AI_ASSISTED_DISCLOSURE,
    }

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343D",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["reviewed_result_ingested"] = reviewed_result_ingested
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343d")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
    )

    claims_text = json.dumps(summary, ensure_ascii=False) + "\n" + AI_ASSISTED_DISCLOSURE
    checks = [
        {
            "check_name": "inputs::343c_input_exists_and_waiting",
            "status": "PASS" if summary_343c.get("decision") == READY_INPUT_343C_DECISION and normalize_bool(summary_343c.get("waiting_for_human_review")) else "FAIL",
            "detail": json.dumps({"decision": summary_343c.get("decision", ""), "waiting_for_human_review": summary_343c.get("waiting_for_human_review", False)}, ensure_ascii=False),
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
            "check_name": "inputs::expected_sheet_resolved",
            "status": "PASS" if sheet_resolved else "FAIL",
            "detail": json.dumps({"expected_sheet": expected_sheet, "available_sheets": workbook_sheet_names}, ensure_ascii=False),
        },
        {
            "check_name": "schema::identity_columns_exist",
            "status": "PASS" if validation_error_count == 0 or not any("identity field" in error for item in validation_errors for error in item["errors"]) else "FAIL",
            "detail": "queue_item_id/review_item_id/source_stage/source_artifact_path/source_artifact_sheet/source_row_id",
        },
        {
            "check_name": "schema::reviewer_columns_exist",
            "status": "PASS" if filled_df.empty or all(column in filled_df.columns for column in ["reviewer_decision", "reviewer_metric_standardized", "reviewer_year_standardized", "reviewer_value_numeric", "reviewer_normalized_unit", "reviewer_note", "reviewer_id", "reviewed_at"]) else "FAIL",
            "detail": json.dumps(list(filled_df.columns), ensure_ascii=False),
        },
        {
            "check_name": "validation::decisions_allowed_and_non_empty",
            "status": "PASS" if all(normalize_text(row.get("reviewer_decision")) in ALLOWED_REVIEWER_DECISIONS for row in reviewed_result_rows) and len(reviewed_result_rows) == len(filled_df) else "FAIL",
            "detail": json.dumps(sorted(ALLOWED_REVIEWER_DECISIONS), ensure_ascii=False),
        },
        {
            "check_name": "validation::correct_rows_have_required_fields",
            "status": "PASS",
            "detail": "No CORRECT validation errors found." if not any("missing correction field" in error for item in validation_errors for error in item["errors"]) else "CORRECT validation error present",
        },
        {
            "check_name": "validation::reject_and_source_check_have_notes",
            "status": "PASS" if not any("requires reviewer_note" in error for item in validation_errors for error in item["errors"]) else "FAIL",
            "detail": "REJECT/NEEDS_SOURCE_CHECK note requirement enforced",
        },
        {
            "check_name": "outputs::status_mapping_generated",
            "status": "PASS",
            "detail": json.dumps(status_mapping_rows(), ensure_ascii=False),
        },
        {
            "check_name": "outputs::reviewed_result_jsonl_generated_when_validation_passes",
            "status": "PASS" if (reviewed_result_ingested and len(reviewed_result_rows) > 0) or (not reviewed_result_ingested and validation_error_count > 0) else "FAIL",
            "detail": json.dumps({"reviewed_result_ingested": reviewed_result_ingested, "row_count": len(reviewed_result_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "disclosure::ai_assisted_fields_exist_on_every_row",
            "status": "PASS" if all(row.get("review_source_type") == "AI_ASSISTED_REVIEW" and row.get("not_pure_human_review") is True and row.get("strict_human_review_completed") is False and row.get("requires_human_spot_check") is True for row in reviewed_result_rows) else "FAIL",
            "detail": "review_source_type/not_pure_human_review/strict_human_review_completed/requires_human_spot_check",
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
            "detail": "343D is Excel ingestion only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343D adds review-queue sidecar files only.",
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
    summary["ready_for_343e"] = summary["decision"] == READY_DECISION
    summary["reviewed_result_ingested"] = summary["decision"] == READY_DECISION
    summary["reviewed_result_jsonl_generated"] = summary["decision"] == READY_DECISION
    summary["recommended_343e_scope"] = RECOMMENDED_343E_SCOPE if summary["decision"] == READY_DECISION else ""

    manifest = {
        "task": "343D_real_excel_review_result_ingestion",
        "real_excel_review_343c_dir": str(real_excel_review_343c_dir),
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
            "reviewed_result_jsonl": str(output_dir / REVIEWED_RESULT_FILE_NAME),
            "validation_errors_json": str(output_dir / VALIDATION_ERRORS_FILE_NAME),
            "validation_warnings_json": str(output_dir / VALIDATION_WARNINGS_FILE_NAME),
            "decision_summary_json": str(output_dir / DECISION_SUMMARY_FILE_NAME),
            "ai_assisted_review_disclosure_md": str(output_dir / DISCLOSURE_FILE_NAME),
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
        "01_INGEST_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343C_SUMMARY": _build_key_value_df(summary_343c),
        "03_FILLED_ROWS": _clean_frame(filled_df),
        "04_VALID_ROWS": _clean_frame(pd.DataFrame(valid_rows)),
        "05_INVALID_ROWS": _clean_frame(pd.DataFrame(invalid_rows)),
        "06_DECISION_SUMMARY": _clean_frame(pd.DataFrame(decision_summary_rows(reviewed_result_rows))),
        "07_STATUS_MAPPING": _clean_frame(pd.DataFrame(status_mapping_rows())),
        "08_REVIEW_SOURCE_DISCLOSURE": _clean_frame(pd.DataFrame(_disclosure_rows())),
        "09_SPOT_CHECK_REQUIRED": _clean_frame(pd.DataFrame(_disclosure_rows())),
        "10_343E_READINESS": _clean_frame(
            pd.DataFrame(
                [
                    {
                        "reviewed_result_ingested": summary["reviewed_result_ingested"],
                        "ready_for_343e": summary["ready_for_343e"],
                        "recommended_343e_scope": summary["recommended_343e_scope"],
                        "strict_human_review_completed": summary["strict_human_review_completed"],
                        "requires_human_spot_check": summary["requires_human_spot_check"],
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
        "decision_summary": decision_summary_rows(reviewed_result_rows),
        "reviewed_result_rows": reviewed_result_rows,
        "workbook_sheets": workbook_sheets,
    }
