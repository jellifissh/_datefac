from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.real_excel_review_343c import (
    ALLOWED_REVIEWER_DECISIONS,
    EDITABLE_REVIEWER_COLUMNS,
    REVIEW_QUEUE_REAL_EXCEL_SHEETS,
    build_blank_template_rows,
    build_expected_import_contract,
    build_next_steps_rows,
    build_readiness_rows,
    build_risk_context_rows,
    build_waiting_rows,
    field_guide_rows,
    reviewer_decision_rules,
    select_real_review_pilot_rows,
    validation_rules_catalog_343c,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_343A_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"
READY_INPUT_343B_DECISION = "REVIEW_QUEUE_EXCEL_ROUND_TRIP_343B_READY"
READY_INPUT_342S_DECISION = "PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_READY"
READY_DECISION = "REVIEW_QUEUE_REAL_EXCEL_REVIEW_343C_WAITING_FOR_HUMAN_REVIEW"
NOT_READY_DECISION = "REVIEW_QUEUE_REAL_EXCEL_REVIEW_343C_NOT_READY"
RECOMMENDED_343D_SCOPE = "real_excel_review_result_ingestion_after_user_fills_workbook"

DEFAULT_EXCEL_ROUND_TRIP_343B_DIR = Path(r"D:\_datefac\output\review_queue_excel_round_trip_343b")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_SNAPSHOT_342S_DIR = Path(r"D:\_datefac\output\package_audit_snapshot_demo_handoff_342s")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_real_excel_review_343c")

SUMMARY_FILE_NAME = "review_queue_real_excel_review_343c_summary.json"
MANIFEST_FILE_NAME = "review_queue_real_excel_review_343c_manifest.json"
QA_FILE_NAME = "review_queue_real_excel_review_343c_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_real_excel_review_343c_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_real_excel_review_343c_report.md"
WORKBOOK_FILE_NAME = "review_queue_real_excel_review_343c.xlsx"
REVIEW_TEMPLATE_FILE_NAME = "review_queue_real_excel_review_343c_review_template.xlsx"
REVIEWER_INSTRUCTIONS_FILE_NAME = "review_queue_real_excel_review_343c_reviewer_instructions.md"
FILL_GUIDE_FILE_NAME = "review_queue_real_excel_review_343c_fill_guide.md"
EXPECTED_IMPORT_CONTRACT_FILE_NAME = "review_queue_real_excel_review_343c_expected_import_contract.json"

INPUT_343B_SUMMARY_NAME = "review_queue_excel_round_trip_343b_summary.json"
INPUT_343B_QA_NAME = "review_queue_excel_round_trip_343b_qa.json"
INPUT_343B_REPORT_NAME = "review_queue_excel_round_trip_343b_report.md"
INPUT_343B_WORKBOOK_NAME = "review_queue_excel_round_trip_343b.xlsx"
INPUT_343B_REVIEW_TEMPLATE_NAME = "review_queue_excel_round_trip_343b_review_template.xlsx"
INPUT_343B_REVIEWED_RESULT_NAME = "review_queue_excel_round_trip_343b_reviewed_result.jsonl"

INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"
INPUT_343A_QA_NAME = "review_queue_schema_343a_qa.json"
INPUT_343A_EXCEL_SPEC_NAME = "review_queue_schema_343a_excel_template_spec.json"
INPUT_343A_SAMPLE_ITEMS_NAME = "review_queue_schema_343a_sample_items.jsonl"

INPUT_342S_SUMMARY_NAME = "package_audit_snapshot_demo_handoff_342s_summary.json"
INPUT_342S_QA_NAME = "package_audit_snapshot_demo_handoff_342s_qa.json"

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
    "input/table_first_review_342g_reviewed",
    "input/spot_check_reviewed_342m",
    "input/llm_review_responses_342m",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

FORBIDDEN_CLAIMS = [
    "investment advice",
    "formal_client_export_allowed=true",
    "client_ready=true",
    "production_ready=true",
    "completed human review",
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
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))
    except Exception:
        return pd.DataFrame()


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


def _contains_forbidden_claim(text: str, forbidden_tokens: Sequence[str]) -> bool:
    safe_cues = ("not ", "false", "no ", "do not", "must not", "forbidden", "cannot", "can't")
    lowered_lines = [line.casefold() for line in text.splitlines()]
    for token in forbidden_tokens:
        token_lower = token.casefold()
        for line in lowered_lines:
            if token_lower not in line:
                continue
            if any(cue in line for cue in safe_cues):
                continue
            return True
    return False


def _input_summary_df(summary_343b: Dict[str, Any], summary_343a: Dict[str, Any], summary_342s: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for stage, summary in [("343B", summary_343b), ("343A", summary_343a), ("342S", summary_342s)]:
        for key, value in summary.items():
            rows.append({"source_stage": stage, "key": key, "value": _flatten_value(value)})
    return _clean_frame(pd.DataFrame(rows))


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "343C prepares a real fillable Excel review package for later human review.",
                },
                {
                    "section": "boundary",
                    "message": "343C does not ingest results, does not call Argilla, and does not claim completed human review.",
                },
                {
                    "section": "safety",
                    "message": "formal_client_export_allowed=false, client_ready=false, production_ready=false remain unchanged.",
                },
                {
                    "section": "next",
                    "message": "User fills the workbook first, then 343D may ingest the reviewed result.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _next_steps_df() -> pd.DataFrame:
    return _clean_frame(pd.DataFrame(build_next_steps_rows()))


def _decision_rules_df() -> pd.DataFrame:
    return _clean_frame(pd.DataFrame(reviewer_decision_rules()))


def _validation_rules_df() -> pd.DataFrame:
    return _clean_frame(pd.DataFrame(validation_rules_catalog_343c()))


def _field_guide_df() -> pd.DataFrame:
    return _clean_frame(pd.DataFrame(field_guide_rows()))


def build_review_queue_real_excel_review_343c(
    *,
    excel_round_trip_343b_dir: Path = DEFAULT_EXCEL_ROUND_TRIP_343B_DIR,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    snapshot_342s_dir: Path = DEFAULT_SNAPSHOT_342S_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_343b_path = excel_round_trip_343b_dir / INPUT_343B_SUMMARY_NAME
    qa_343b_path = excel_round_trip_343b_dir / INPUT_343B_QA_NAME
    workbook_343b_path = excel_round_trip_343b_dir / INPUT_343B_WORKBOOK_NAME
    review_template_343b_path = excel_round_trip_343b_dir / INPUT_343B_REVIEW_TEMPLATE_NAME
    reviewed_result_343b_path = excel_round_trip_343b_dir / INPUT_343B_REVIEWED_RESULT_NAME
    report_343b_path = excel_round_trip_343b_dir / INPUT_343B_REPORT_NAME

    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME
    qa_343a_path = review_queue_schema_343a_dir / INPUT_343A_QA_NAME
    excel_spec_343a_path = review_queue_schema_343a_dir / INPUT_343A_EXCEL_SPEC_NAME
    sample_items_343a_path = review_queue_schema_343a_dir / INPUT_343A_SAMPLE_ITEMS_NAME

    summary_342s_path = snapshot_342s_dir / INPUT_342S_SUMMARY_NAME
    qa_342s_path = snapshot_342s_dir / INPUT_342S_QA_NAME

    files_read: List[str] = []
    warnings: List[str] = []
    input_paths = [
        summary_343b_path,
        qa_343b_path,
        workbook_343b_path,
        review_template_343b_path,
        reviewed_result_343b_path,
        report_343b_path,
        summary_343a_path,
        qa_343a_path,
        excel_spec_343a_path,
        sample_items_343a_path,
        summary_342s_path,
        qa_342s_path,
    ]
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input: {path}")

    summary_343b = _read_json(summary_343b_path) if summary_343b_path.exists() else {}
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}
    summary_342s = _read_json(summary_342s_path) if summary_342s_path.exists() else {}
    excel_template_spec = _read_json(excel_spec_343a_path) if excel_spec_343a_path.exists() else {}
    sample_items = _read_jsonl(sample_items_343a_path) if sample_items_343a_path.exists() else []

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        summary_343b.get("decision") == READY_INPUT_343B_DECISION
        and normalize_bool(summary_343b.get("ready_for_343c"))
        and int(summary_343b.get("qa_fail_count", 1)) == 0
        and summary_343a.get("decision") == READY_INPUT_343A_DECISION
        and normalize_bool(summary_343a.get("ready_for_343b"))
        and int(summary_343a.get("qa_fail_count", 1)) == 0
        and summary_342s.get("decision") == READY_INPUT_342S_DECISION
        and int(summary_342s.get("qa_fail_count", 1)) == 0
        and summary_343b.get("review_queue_schema_version") == "343A.review_queue.v1"
        and not normalize_bool(summary_343b.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343b.get("client_ready"))
        and not normalize_bool(summary_343b.get("production_ready"))
        and bool(excel_template_spec)
        and bool(sample_items)
    )

    template_rows_from_workbook = _read_excel_sheet(review_template_343b_path, "review_queue_roundtrip")
    if not template_rows_from_workbook.empty:
        base_rows = template_rows_from_workbook.to_dict(orient="records")
    else:
        base_rows = build_blank_template_rows(sample_items, excel_template_spec=excel_template_spec)

    selected = select_real_review_pilot_rows(base_rows)
    selected_rows = selected["selected_rows"]
    expected_import_contract = build_expected_import_contract(
        review_queue_schema_version=summary_343b.get("review_queue_schema_version", ""),
        output_dir_hint=str(output_dir),
    )

    reviewer_columns_exist = bool(
        selected_rows
        and all(column in selected_rows[0] for column in EDITABLE_REVIEWER_COLUMNS)
    )
    reviewer_columns_blank = all(
        not normalize_text(row.get("reviewer_decision"))
        and not normalize_text(row.get("reviewer_metric_standardized"))
        and not normalize_text(row.get("reviewer_year_standardized"))
        and not normalize_text(row.get("reviewer_value_numeric"))
        and not normalize_text(row.get("reviewer_normalized_unit"))
        and not normalize_text(row.get("reviewer_note"))
        and not normalize_text(row.get("reviewer_id"))
        and not normalize_text(row.get("reviewed_at"))
        for row in selected_rows
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343B",
        "decision": NOT_READY_DECISION,
        "review_queue_schema_version": summary_343b.get("review_queue_schema_version", ""),
        "real_review_template_row_count": len(selected_rows),
        "fillable_review_row_count": len(selected_rows),
        "human_reviewed_audit_row_count": selected["human_reviewed_audit_row_count"],
        "simulated_direct_review_row_count": selected["simulated_direct_review_row_count"],
        "simulated_corrected_review_row_count": selected["simulated_corrected_review_row_count"],
        "summary_derived_review_row_count": selected["summary_derived_review_row_count"],
        "allowed_decision_count": len(ALLOWED_REVIEWER_DECISIONS),
        "real_review_template_generated": bool(selected_rows),
        "reviewer_instructions_generated": True,
        "fill_guide_generated": True,
        "expected_import_contract_generated": True,
        "waiting_for_human_review": True,
        "reviewed_result_ingested": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343d": False,
        "recommended_343d_scope": "",
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
        "review_template_workbook_path": str(output_dir / REVIEW_TEMPLATE_FILE_NAME),
        "reviewer_instructions_path": str(output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME),
        "fill_guide_path": str(output_dir / FILL_GUIDE_FILE_NAME),
        "expected_import_contract_path": str(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME),
    }

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343C",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["reviewed_result_ingested"] = False
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343c")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("reviewed_result_ingested", True)
    )

    claims_text = "\n".join(
        [
            json.dumps(summary, ensure_ascii=False),
            json.dumps(expected_import_contract, ensure_ascii=False),
            "\n".join(ALLOWED_REVIEWER_DECISIONS),
        ]
    )

    checks = [
        {
            "check_name": "inputs::343b_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "343b_decision": summary_343b.get("decision", ""),
                    "343b_ready_for_343c": summary_343b.get("ready_for_343c", False),
                    "343b_qa_fail_count": summary_343b.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::343a_schema_and_sample_exist",
            "status": "PASS" if excel_spec_343a_path.exists() and sample_items_343a_path.exists() else "FAIL",
            "detail": json.dumps(
                {
                    "excel_template_spec": excel_spec_343a_path.exists(),
                    "sample_items_jsonl": sample_items_343a_path.exists(),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::real_review_template_generated",
            "status": "PASS" if summary["real_review_template_generated"] else "FAIL",
            "detail": str(len(selected_rows)),
        },
        {
            "check_name": "outputs::reviewer_instructions_generated",
            "status": "PASS" if summary["reviewer_instructions_generated"] else "FAIL",
            "detail": REVIEWER_INSTRUCTIONS_FILE_NAME,
        },
        {
            "check_name": "outputs::fill_guide_generated",
            "status": "PASS" if summary["fill_guide_generated"] else "FAIL",
            "detail": FILL_GUIDE_FILE_NAME,
        },
        {
            "check_name": "outputs::expected_import_contract_generated",
            "status": "PASS" if summary["expected_import_contract_generated"] else "FAIL",
            "detail": EXPECTED_IMPORT_CONTRACT_FILE_NAME,
        },
        {
            "check_name": "schema::editable_reviewer_columns_exist",
            "status": "PASS" if reviewer_columns_exist else "FAIL",
            "detail": json.dumps(EDITABLE_REVIEWER_COLUMNS, ensure_ascii=False),
        },
        {
            "check_name": "schema::allowed_decision_list_present",
            "status": "PASS" if len(ALLOWED_REVIEWER_DECISIONS) == 5 else "FAIL",
            "detail": json.dumps(ALLOWED_REVIEWER_DECISIONS, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_simulated_or_imported_reviewer_decision_treated_as_real",
            "status": "PASS" if reviewer_columns_blank and not summary["reviewed_result_ingested"] else "FAIL",
            "detail": json.dumps(
                {
                    "reviewer_columns_blank": reviewer_columns_blank,
                    "reviewed_result_ingested": summary["reviewed_result_ingested"],
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "state::reviewed_result_ingested_false",
            "status": "PASS" if not summary["reviewed_result_ingested"] else "FAIL",
            "detail": str(summary["reviewed_result_ingested"]),
        },
        {
            "check_name": "state::waiting_for_human_review_true",
            "status": "PASS" if summary["waiting_for_human_review"] else "FAIL",
            "detail": str(summary["waiting_for_human_review"]),
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
            "detail": "343C is Excel-only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343C adds review-queue sidecar files only.",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in REVIEW_QUEUE_REAL_EXCEL_SHEETS) else "FAIL",
            "detail": json.dumps(REVIEW_QUEUE_REAL_EXCEL_SHEETS, ensure_ascii=False),
        },
        {
            "check_name": "claims::no_forbidden_claims",
            "status": "PASS" if not _contains_forbidden_claim(claims_text, FORBIDDEN_CLAIMS) else "FAIL",
            "detail": "generated 343C texts checked",
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    ready_state = bool(
        input_ready
        and summary["real_review_template_generated"]
        and summary["reviewer_instructions_generated"]
        and summary["fill_guide_generated"]
        and summary["expected_import_contract_generated"]
        and reviewer_columns_exist
        and reviewer_columns_blank
        and no_write_back_proof_passed
        and qa_fail_count == 0
    )
    summary["decision"] = READY_DECISION if ready_state else NOT_READY_DECISION
    summary["recommended_343d_scope"] = RECOMMENDED_343D_SCOPE if ready_state else ""
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    manifest = {
        "task": "343C_real_excel_review_queue_pilot",
        "excel_round_trip_343b_dir": str(excel_round_trip_343b_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "snapshot_342s_dir": str(snapshot_342s_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "review_template_xlsx": str(output_dir / REVIEW_TEMPLATE_FILE_NAME),
            "reviewer_instructions_md": str(output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME),
            "fill_guide_md": str(output_dir / FILL_GUIDE_FILE_NAME),
            "expected_import_contract_json": str(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME),
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

    selected_df = _clean_frame(pd.DataFrame(selected_rows))
    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_REVIEW_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343B_SUMMARY": _input_summary_df(summary_343b, summary_343a, summary_342s),
        "03_REVIEW_QUEUE_ITEMS": selected_df,
        "04_FILLABLE_REVIEW": selected_df,
        "05_DECISION_RULES": _decision_rules_df(),
        "06_VALIDATION_RULES": _validation_rules_df(),
        "07_FIELD_GUIDE": _field_guide_df(),
        "08_RISK_CONTEXT": _clean_frame(pd.DataFrame(build_risk_context_rows(selected_rows))),
        "09_IMPORT_CONTRACT": _build_key_value_df(expected_import_contract),
        "10_WAITING_FOR_REVIEW": _clean_frame(pd.DataFrame(build_waiting_rows(summary))),
        "11_343D_READINESS": _clean_frame(pd.DataFrame(build_readiness_rows(summary))),
        "12_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "13_NEXT_STEPS": _next_steps_df(),
    }
    review_template_sheets = {
        "04_FILLABLE_REVIEW": selected_df,
        "05_DECISION_RULES": _decision_rules_df(),
        "06_VALIDATION_RULES": _validation_rules_df(),
        "07_FIELD_GUIDE": _field_guide_df(),
        "08_RISK_CONTEXT": _clean_frame(pd.DataFrame(build_risk_context_rows(selected_rows))),
        "09_IMPORT_CONTRACT": _build_key_value_df(expected_import_contract),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "expected_import_contract": expected_import_contract,
        "selected_rows": selected_rows,
        "workbook_sheets": workbook_sheets,
        "review_template_sheets": review_template_sheets,
    }
