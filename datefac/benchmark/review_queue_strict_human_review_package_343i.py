from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.strict_human_review_package_343i import (
    EDITABLE_STRICT_REVIEW_COLUMNS,
    NOT_READY_DECISION_343I,
    READY_DECISION_343I,
    RECOMMENDED_343J_SCOPE,
    WORKBOOK_SHEETS_343I,
    build_boundary_rows,
    build_evidence_context_rows,
    build_expected_import_contract,
    build_next_steps_rows,
    build_readiness_rows,
    build_strict_review_items,
    client_export_gate_is_safe,
    strict_review_decision_rules,
    strict_review_decisions_blank,
    strict_review_validation_rules,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_343H_DECISION = "AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_READY"

DEFAULT_AUDIT_SUMMARY_343H_DIR = Path(r"D:\_datefac\output\review_queue_audit_summary_343h")
DEFAULT_SPOT_CHECK_INGESTION_343G_DIR = Path(r"D:\_datefac\output\review_queue_spot_check_ingestion_343g")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_strict_human_review_package_343i")

SUMMARY_FILE_NAME = "review_queue_strict_human_review_package_343i_summary.json"
MANIFEST_FILE_NAME = "review_queue_strict_human_review_package_343i_manifest.json"
QA_FILE_NAME = "review_queue_strict_human_review_package_343i_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_strict_human_review_package_343i_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_strict_human_review_package_343i_report.md"
WORKBOOK_FILE_NAME = "review_queue_strict_human_review_package_343i.xlsx"
REVIEW_TEMPLATE_FILE_NAME = "review_queue_strict_human_review_package_343i_review_template.xlsx"
REVIEW_ITEMS_FILE_NAME = "review_queue_strict_human_review_package_343i_review_items.jsonl"
REVIEWER_INSTRUCTIONS_FILE_NAME = "review_queue_strict_human_review_package_343i_reviewer_instructions.md"
FILL_GUIDE_FILE_NAME = "review_queue_strict_human_review_package_343i_fill_guide.md"
EXPECTED_IMPORT_CONTRACT_FILE_NAME = "review_queue_strict_human_review_package_343i_expected_import_contract.json"
CLIENT_EXPORT_BOUNDARY_FILE_NAME = "review_queue_strict_human_review_package_343i_client_export_boundary.md"

INPUT_343H_SUMMARY_NAME = "review_queue_audit_summary_343h_summary.json"
INPUT_343H_QA_NAME = "review_queue_audit_summary_343h_qa.json"
INPUT_343H_REPORT_NAME = "review_queue_audit_summary_343h_report.md"
INPUT_343H_STRICT_GAP_NAME = "review_queue_audit_summary_343h_strict_human_gap_report.md"
INPUT_343H_CONFIRMED_ITEMS_NAME = "review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl"
INPUT_343H_GAP_ITEMS_NAME = "review_queue_audit_summary_343h_gap_items.jsonl"
INPUT_343H_CLIENT_EXPORT_GATE_NAME = "review_queue_audit_summary_343h_client_export_gate.json"
INPUT_343H_NEXT_ACTION_NAME = "review_queue_audit_summary_343h_next_action_plan.json"
INPUT_343H_NO_WRITE_BACK_NAME = "review_queue_audit_summary_343h_no_write_back_proof.json"

INPUT_343G_RESULT_NAME = "review_queue_spot_check_ingestion_343g_result.jsonl"
INPUT_343G_DISCLOSURE_NAME = "review_queue_spot_check_ingestion_343g_ai_assisted_spot_check_disclosure.md"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"
INPUT_343A_SCHEMA_NAME = "review_queue_schema_343a_schema.json"
INPUT_343A_JSON_SCHEMA_NAME = "review_queue_schema_343a_json_schema.json"

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
    "input/review_queue_strict_human_review_343i_filled",
    "input/review_queue_spot_check_package_343f_filled",
    "input/review_queue_real_excel_review_343c_filled",
    "input/llm_review_responses_342m",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
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


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return normalize_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
        )
    )


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "343I creates a strict human review package for AI-assisted confirmed rows only.",
                },
                {
                    "section": "boundary",
                    "message": "343I does not ingest strict human review results and does not enable formal client export.",
                },
                {
                    "section": "backlog",
                    "message": "19 source-check-required rows remain separate backlog outside the fillable strict review template.",
                },
                {
                    "section": "next",
                    "message": "User must fill the strict human review workbook before 343J ingestion can begin.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def build_review_queue_strict_human_review_package_343i(
    *,
    audit_summary_343h_dir: Path = DEFAULT_AUDIT_SUMMARY_343H_DIR,
    spot_check_ingestion_343g_dir: Path = DEFAULT_SPOT_CHECK_INGESTION_343G_DIR,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_343h_path = audit_summary_343h_dir / INPUT_343H_SUMMARY_NAME
    qa_343h_path = audit_summary_343h_dir / INPUT_343H_QA_NAME
    report_343h_path = audit_summary_343h_dir / INPUT_343H_REPORT_NAME
    strict_gap_343h_path = audit_summary_343h_dir / INPUT_343H_STRICT_GAP_NAME
    confirmed_items_343h_path = audit_summary_343h_dir / INPUT_343H_CONFIRMED_ITEMS_NAME
    gap_items_343h_path = audit_summary_343h_dir / INPUT_343H_GAP_ITEMS_NAME
    gate_343h_path = audit_summary_343h_dir / INPUT_343H_CLIENT_EXPORT_GATE_NAME
    next_action_343h_path = audit_summary_343h_dir / INPUT_343H_NEXT_ACTION_NAME
    no_write_back_343h_path = audit_summary_343h_dir / INPUT_343H_NO_WRITE_BACK_NAME
    result_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_RESULT_NAME
    disclosure_343g_path = spot_check_ingestion_343g_dir / INPUT_343G_DISCLOSURE_NAME
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME
    schema_343a_path = review_queue_schema_343a_dir / INPUT_343A_SCHEMA_NAME
    json_schema_343a_path = review_queue_schema_343a_dir / INPUT_343A_JSON_SCHEMA_NAME

    input_paths = [
        summary_343h_path,
        qa_343h_path,
        report_343h_path,
        strict_gap_343h_path,
        confirmed_items_343h_path,
        gap_items_343h_path,
        gate_343h_path,
        next_action_343h_path,
        no_write_back_343h_path,
        result_343g_path,
        disclosure_343g_path,
        summary_343a_path,
        schema_343a_path,
        json_schema_343a_path,
    ]
    files_read: List[str] = []
    warnings: List[str] = []
    for path in input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input: {path}")

    summary_343h = _read_json(summary_343h_path) if summary_343h_path.exists() else {}
    qa_343h = _read_json(qa_343h_path) if qa_343h_path.exists() else {}
    confirmed_items = _read_jsonl(confirmed_items_343h_path) if confirmed_items_343h_path.exists() else []
    gap_items = _read_jsonl(gap_items_343h_path) if gap_items_343h_path.exists() else []
    client_export_gate = _read_json(gate_343h_path) if gate_343h_path.exists() else {}
    next_action_plan = _read_json(next_action_343h_path) if next_action_343h_path.exists() else {}
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths if path.exists()}

    input_ready = bool(
        summary_343h.get("decision") == READY_INPUT_343H_DECISION
        and normalize_bool(summary_343h.get("ready_for_343i"))
        and int(summary_343h.get("qa_fail_count", 1)) == 0
        and summary_343h.get("review_queue_schema_version") == "343A.review_queue.v1"
        and int(summary_343h.get("ai_assisted_confirmed_count", -1)) == len(confirmed_items)
        and client_export_gate_is_safe(client_export_gate)
        and next_action_plan.get("recommended_343i_scope")
        == "strict_human_review_package_for_ai_assisted_confirmed_rows"
    )

    strict_review_items = build_strict_review_items(confirmed_items)
    evidence_context_rows = build_evidence_context_rows(confirmed_items)
    expected_import_contract = build_expected_import_contract(
        review_queue_schema_version=summary_343h.get("review_queue_schema_version", ""),
        output_dir_hint=str(output_dir),
    )

    strict_review_columns_exist = bool(
        strict_review_items
        and all(column in strict_review_items[0] for column in EDITABLE_STRICT_REVIEW_COLUMNS)
    )
    strict_review_columns_blank = strict_review_decisions_blank(strict_review_items)
    unsafe_item_rows = [
        row
        for row in confirmed_items
        if normalize_bool(row.get("strict_human_review_completed"))
        or normalize_bool(row.get("formal_client_export_allowed"))
        or normalize_bool(row.get("client_ready"))
        or normalize_bool(row.get("production_ready"))
    ]

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343H",
        "decision": NOT_READY_DECISION_343I,
        "review_queue_schema_version": summary_343h.get("review_queue_schema_version", ""),
        "input_ai_assisted_confirmed_count": len(confirmed_items),
        "strict_review_item_count": len(strict_review_items),
        "source_check_backlog_context_count": int(
            summary_343h.get("source_check_backlog_count", 0)
        ),
        "strict_human_gap_item_count": len(gap_items),
        "strict_human_review_package_generated": False,
        "review_template_generated": bool(strict_review_items),
        "reviewer_instructions_generated": True,
        "fill_guide_generated": True,
        "expected_import_contract_generated": True,
        "waiting_for_strict_human_review": True,
        "strict_human_review_result_ingested": False,
        "strict_human_review_completed": False,
        "requires_strict_human_review": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343j": False,
        "recommended_343j_scope": "",
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
        stage="343I",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["strict_human_review_result_ingested"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343i")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("strict_human_review_result_ingested", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::343h_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_343h.get("decision", ""),
                    "ready_for_343i": summary_343h.get("ready_for_343i", False),
                    "qa_fail_count": summary_343h.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::confirmed_ai_assisted_items_jsonl_exists_and_readable",
            "status": "PASS" if confirmed_items_343h_path.exists() and len(confirmed_items) > 0 else "FAIL",
            "detail": str(confirmed_items_343h_path),
        },
        {
            "check_name": "inputs::client_export_gate_exists_and_remains_false",
            "status": "PASS" if client_export_gate_is_safe(client_export_gate) else "FAIL",
            "detail": json.dumps(client_export_gate, ensure_ascii=False),
        },
        {
            "check_name": "counts::strict_review_item_count_matches_input_confirmed_count",
            "status": "PASS"
            if len(strict_review_items) == int(summary_343h.get("ai_assisted_confirmed_count", -1))
            else "FAIL",
            "detail": json.dumps(
                {
                    "strict_review_item_count": len(strict_review_items),
                    "expected": summary_343h.get("ai_assisted_confirmed_count", -1),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::review_template_generated",
            "status": "PASS" if summary["review_template_generated"] else "FAIL",
            "detail": REVIEW_TEMPLATE_FILE_NAME,
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
            "check_name": "schema::editable_strict_review_columns_exist",
            "status": "PASS" if strict_review_columns_exist else "FAIL",
            "detail": json.dumps(EDITABLE_STRICT_REVIEW_COLUMNS, ensure_ascii=False),
        },
        {
            "check_name": "schema::allowed_decision_list_present",
            "status": "PASS"
            if len(expected_import_contract.get("allowed_strict_review_decisions", [])) == 5
            else "FAIL",
            "detail": json.dumps(
                expected_import_contract.get("allowed_strict_review_decisions", []),
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "state::strict_review_decisions_not_prefilled_completed",
            "status": "PASS" if strict_review_columns_blank else "FAIL",
            "detail": "strict_review_* columns must stay blank in generated package",
        },
        {
            "check_name": "state::waiting_for_strict_human_review_true",
            "status": "PASS" if summary["waiting_for_strict_human_review"] else "FAIL",
            "detail": str(summary["waiting_for_strict_human_review"]),
        },
        {
            "check_name": "state::strict_human_review_result_ingested_false",
            "status": "PASS" if not summary["strict_human_review_result_ingested"] else "FAIL",
            "detail": str(summary["strict_human_review_result_ingested"]),
        },
        {
            "check_name": "claims::strict_human_review_not_claimed_complete",
            "status": "PASS"
            if not summary["strict_human_review_completed"] and not unsafe_item_rows
            else "FAIL",
            "detail": json.dumps({"unsafe_item_row_count": len(unsafe_item_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "claims::formal_client_or_production_flags_remain_false",
            "status": "PASS"
            if not summary["formal_client_export_allowed"]
            and not summary["client_ready"]
            and not summary["production_ready"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "343I is workbook package generation only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "343I does not perform real apply or workbook write-back.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "343I adds review-queue sidecar files only.",
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
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_343I) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_343I, ensure_ascii=False),
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
    ready_state = bool(
        input_ready
        and len(strict_review_items) > 0
        and strict_review_columns_exist
        and strict_review_columns_blank
        and no_write_back_proof_passed
        and qa_fail_count == 0
    )

    summary["strict_human_review_package_generated"] = ready_state
    summary["recommended_343j_scope"] = RECOMMENDED_343J_SCOPE if ready_state else ""
    summary["decision"] = READY_DECISION_343I if ready_state else NOT_READY_DECISION_343I
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    manifest = {
        "task": "343I_strict_human_review_package_for_ai_assisted_confirmed_rows",
        "audit_summary_343h_dir": str(audit_summary_343h_dir),
        "spot_check_ingestion_343g_dir": str(spot_check_ingestion_343g_dir),
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
            "review_items_jsonl": str(output_dir / REVIEW_ITEMS_FILE_NAME),
            "reviewer_instructions_md": str(output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME),
            "fill_guide_md": str(output_dir / FILL_GUIDE_FILE_NAME),
            "expected_import_contract_json": str(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME),
            "client_export_boundary_md": str(output_dir / CLIENT_EXPORT_BOUNDARY_FILE_NAME),
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

    strict_review_df = _clean_frame(pd.DataFrame(strict_review_items))
    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_PACKAGE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343H_SUMMARY": _build_key_value_df(summary_343h),
        "03_STRICT_REVIEW_ITEMS": strict_review_df,
        "04_REVIEW_TEMPLATE": strict_review_df,
        "05_EVIDENCE_CONTEXT": _clean_frame(pd.DataFrame(evidence_context_rows)),
        "06_DECISION_RULES": _clean_frame(pd.DataFrame(strict_review_decision_rules())),
        "07_VALIDATION_RULES": _clean_frame(pd.DataFrame(strict_review_validation_rules())),
        "08_CLIENT_EXPORT_BOUNDARY": _clean_frame(pd.DataFrame(build_boundary_rows())),
        "09_IMPORT_CONTRACT": _build_key_value_df(expected_import_contract),
        "10_343J_READINESS": _clean_frame(pd.DataFrame(build_readiness_rows(summary))),
        "11_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "12_NEXT_STEPS": _clean_frame(pd.DataFrame(build_next_steps_rows())),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "strict_review_items": strict_review_items,
        "expected_import_contract": expected_import_contract,
        "workbook_sheets": workbook_sheets,
        "review_template_sheets": {"04_REVIEW_TEMPLATE": strict_review_df},
    }
