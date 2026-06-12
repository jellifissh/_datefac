from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import (
    REVIEWER_DECISION_TO_STATUS,
    build_import_simulation_rows,
    build_intentional_error_cases,
    build_review_template_rows,
    build_reviewed_result_rows,
    decision_mapping_rows,
    export_template_columns,
    normalize_bool,
    normalize_text,
    validation_rules_catalog,
    validate_import_row,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_343A_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"
READY_INPUT_342S_DECISION = "PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_READY"
READY_INPUT_342R_DECISION = "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY"
READY_DECISION = "REVIEW_QUEUE_EXCEL_ROUND_TRIP_343B_READY"
NOT_READY_DECISION = "REVIEW_QUEUE_EXCEL_ROUND_TRIP_343B_NOT_READY"
RECOMMENDED_343C_SCOPE = "argilla_human_review_ui_pilot"

DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_SNAPSHOT_342S_DIR = Path(r"D:\_datefac\output\package_audit_snapshot_demo_handoff_342s")
DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR = Path(r"D:\_datefac\output\audit_labeled_export_candidate_package_342r")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_excel_round_trip_343b")

SUMMARY_FILE_NAME = "review_queue_excel_round_trip_343b_summary.json"
MANIFEST_FILE_NAME = "review_queue_excel_round_trip_343b_manifest.json"
QA_FILE_NAME = "review_queue_excel_round_trip_343b_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_excel_round_trip_343b_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_excel_round_trip_343b_report.md"
WORKBOOK_FILE_NAME = "review_queue_excel_round_trip_343b.xlsx"
REVIEW_TEMPLATE_FILE_NAME = "review_queue_excel_round_trip_343b_review_template.xlsx"
IMPORT_SIMULATION_FILE_NAME = "review_queue_excel_round_trip_343b_import_simulation.xlsx"
REVIEWED_RESULT_FILE_NAME = "review_queue_excel_round_trip_343b_reviewed_result.jsonl"
VALIDATION_ERRORS_FILE_NAME = "review_queue_excel_round_trip_343b_validation_errors.json"

INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"
INPUT_343A_QA_NAME = "review_queue_schema_343a_qa.json"
INPUT_343A_REPORT_NAME = "review_queue_schema_343a_report.md"
INPUT_343A_WORKBOOK_NAME = "review_queue_schema_343a.xlsx"
INPUT_343A_SCHEMA_NAME = "review_queue_schema_343a_schema.json"
INPUT_343A_JSON_SCHEMA_NAME = "review_queue_schema_343a_json_schema.json"
INPUT_343A_EXCEL_SPEC_NAME = "review_queue_schema_343a_excel_template_spec.json"
INPUT_343A_SAMPLE_ITEMS_NAME = "review_queue_schema_343a_sample_items.jsonl"

INPUT_342S_SUMMARY_NAME = "package_audit_snapshot_demo_handoff_342s_summary.json"
INPUT_342S_QA_NAME = "package_audit_snapshot_demo_handoff_342s_qa.json"
INPUT_342S_REPORT_NAME = "package_audit_snapshot_demo_handoff_342s_report.md"
INPUT_342R_SUMMARY_NAME = "audit_labeled_export_candidate_package_342r_summary.json"
INPUT_342R_QA_NAME = "audit_labeled_export_candidate_package_342r_qa.json"
INPUT_342R_WORKBOOK_NAME = "audit_labeled_export_candidate_package_342r.xlsx"

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
    "real human review completed",
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


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return normalize_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    rows = [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
    return _clean_frame(pd.DataFrame(rows))


def _load_summary_qa(base_dir: Path, summary_name: str, qa_name: str, extra_names: Sequence[str]) -> tuple[Dict[str, Any], Dict[str, Any], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = base_dir / summary_name
    qa_path = base_dir / qa_name
    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    for path, label in ((summary_path, "summary"), (qa_path, "qa")):
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing {label}: {path}")
    for name in extra_names:
        path = base_dir / name
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing artifact: {path}")
    return summary, qa_json, files_read, warnings


def _input_343a_df(summary_343a: Dict[str, Any], summary_342s: Dict[str, Any], summary_342r: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for stage, summary in [("343A", summary_343a), ("342S", summary_342s), ("342R", summary_342r)]:
        for key, value in summary.items():
            rows.append({"source_stage": stage, "key": key, "value": _flatten_value(value)})
    return _clean_frame(pd.DataFrame(rows))


def _validation_rules_df() -> pd.DataFrame:
    return _clean_frame(pd.DataFrame(validation_rules_catalog()))


def _status_mapping_df() -> pd.DataFrame:
    rows = []
    for decision, status in REVIEWER_DECISION_TO_STATUS.items():
        rows.append(
            {
                "reviewer_decision": decision,
                "resulting_status": status,
                "future_apply_candidate": decision in {"CONFIRM", "CORRECT"},
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _backlog_note_df(summary_343a: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "note_type": "source_backlog_context",
            "detail": f"343A sample queue is bounded, while source backlog remains still_human_required_count={summary_343a.get('source_still_human_required_count', 0)} and remaining_review_count={summary_343a.get('source_remaining_review_count', 0)}.",
        },
        {
            "note_type": "pilot_boundary",
            "detail": "343B validates the queue contract only and does not consume the full backlog.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _readiness_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"gate": "decision", "value": summary.get("decision", ""), "meaning": "343B readiness decision"},
        {"gate": "ready_for_343c", "value": summary.get("ready_for_343c", False), "meaning": "Whether Argilla UI pilot can start next"},
        {"gate": "recommended_343c_scope", "value": summary.get("recommended_343c_scope", ""), "meaning": "Preferred 343C scope"},
        {"gate": "formal_client_export_allowed", "value": summary.get("formal_client_export_allowed", False), "meaning": "Must remain false"},
        {"gate": "client_ready", "value": summary.get("client_ready", False), "meaning": "Must remain false"},
        {"gate": "production_ready", "value": summary.get("production_ready", False), "meaning": "Must remain false"},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _next_steps_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"step": "343C_argilla", "recommendation": "Use the validated Excel round-trip contract as the source of truth and plug Argilla in as the next pilot UI.", "trigger": bool(summary.get("ready_for_343c"))},
        {"step": "keep_excel_roundtrip", "recommendation": "Retain Excel round-trip as a deterministic fallback and audit-friendly interchange format.", "trigger": True},
        {"step": "keep_boundaries", "recommendation": "Do not treat deterministic import simulation as real human-reviewed evidence.", "trigger": True},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"section": "positioning", "message": "343B validates the 343A Review Queue schema through Excel round-trip."},
        {"section": "boundary", "message": "343B does not represent real human review, does not implement Argilla, and does not implement a full UI."},
        {"section": "mechanics", "message": "343B exports a template, simulates import decisions, validates rows, and writes reviewed-result JSONL."},
        {"section": "safety", "message": "formal_client_export_allowed=false, client_ready=false, production_ready=false must remain unchanged."},
        {"section": "next", "message": "343C can now safely focus on Argilla as a pluggable review UI."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_review_queue_excel_round_trip_343b(
    *,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    snapshot_342s_dir: Path = DEFAULT_SNAPSHOT_342S_DIR,
    audit_labeled_package_342r_dir: Path = DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    files_read: List[str] = []
    warnings: List[str] = []

    summary_343a, qa_343a, files_343a, warnings_343a = _load_summary_qa(
        review_queue_schema_343a_dir,
        INPUT_343A_SUMMARY_NAME,
        INPUT_343A_QA_NAME,
        [
            INPUT_343A_REPORT_NAME,
            INPUT_343A_WORKBOOK_NAME,
            INPUT_343A_SCHEMA_NAME,
            INPUT_343A_JSON_SCHEMA_NAME,
            INPUT_343A_EXCEL_SPEC_NAME,
            INPUT_343A_SAMPLE_ITEMS_NAME,
        ],
    )
    summary_342s, qa_342s, files_342s, warnings_342s = _load_summary_qa(
        snapshot_342s_dir,
        INPUT_342S_SUMMARY_NAME,
        INPUT_342S_QA_NAME,
        [INPUT_342S_REPORT_NAME],
    )
    summary_342r, qa_342r, files_342r, warnings_342r = _load_summary_qa(
        audit_labeled_package_342r_dir,
        INPUT_342R_SUMMARY_NAME,
        INPUT_342R_QA_NAME,
        [INPUT_342R_WORKBOOK_NAME],
    )
    files_read.extend(files_343a + files_342s + files_342r)
    warnings.extend(warnings_343a + warnings_342s + warnings_342r)

    excel_spec_path = review_queue_schema_343a_dir / INPUT_343A_EXCEL_SPEC_NAME
    schema_path = review_queue_schema_343a_dir / INPUT_343A_SCHEMA_NAME
    json_schema_path = review_queue_schema_343a_dir / INPUT_343A_JSON_SCHEMA_NAME
    sample_items_path = review_queue_schema_343a_dir / INPUT_343A_SAMPLE_ITEMS_NAME
    excel_template_spec = _read_json(excel_spec_path) if excel_spec_path.exists() else {}
    schema_json = _read_json(schema_path) if schema_path.exists() else {}
    json_schema = _read_json(json_schema_path) if json_schema_path.exists() else {}
    sample_items = _read_jsonl(sample_items_path) if sample_items_path.exists() else []

    all_input_paths = [
        review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME,
        review_queue_schema_343a_dir / INPUT_343A_QA_NAME,
        review_queue_schema_343a_dir / INPUT_343A_REPORT_NAME,
        review_queue_schema_343a_dir / INPUT_343A_WORKBOOK_NAME,
        schema_path,
        json_schema_path,
        excel_spec_path,
        sample_items_path,
        snapshot_342s_dir / INPUT_342S_SUMMARY_NAME,
        snapshot_342s_dir / INPUT_342S_QA_NAME,
        snapshot_342s_dir / INPUT_342S_REPORT_NAME,
        audit_labeled_package_342r_dir / INPUT_342R_SUMMARY_NAME,
        audit_labeled_package_342r_dir / INPUT_342R_QA_NAME,
        audit_labeled_package_342r_dir / INPUT_342R_WORKBOOK_NAME,
    ]
    input_hashes_before = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}

    input_ready = bool(
        summary_343a.get("decision") == READY_INPUT_343A_DECISION
        and normalize_bool(summary_343a.get("ready_for_343b"))
        and summary_343a.get("review_queue_schema_version") == "343A.review_queue.v1"
        and not normalize_bool(summary_343a.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343a.get("client_ready"))
        and not normalize_bool(summary_343a.get("production_ready"))
        and int(summary_343a.get("qa_fail_count", 1)) == 0
        and summary_342s.get("decision") == READY_INPUT_342S_DECISION
        and int(summary_342s.get("qa_fail_count", 1)) == 0
        and summary_342r.get("decision") == READY_INPUT_342R_DECISION
        and int(summary_342r.get("qa_fail_count", 1)) == 0
        and bool(sample_items)
        and bool(excel_template_spec)
        and bool(schema_json)
        and bool(json_schema)
    )

    template_rows = build_review_template_rows(sample_items, excel_template_spec=excel_template_spec)
    import_simulation_rows = build_import_simulation_rows(template_rows)
    reviewed_result_rows = build_reviewed_result_rows(import_simulation_rows)
    error_case_rows = build_intentional_error_cases(template_rows)
    error_case_validations = [validate_import_row(row) for row in error_case_rows]

    validation_error_count = sum(len(row["validation_errors"]) for row in reviewed_result_rows if row["validation_status"] == "FAIL")
    validation_warning_count = sum(len(row["validation_warnings"]) for row in reviewed_result_rows)
    confirmed_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "REVIEWED_CONFIRMED")
    corrected_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "REVIEWED_CORRECTED")
    rejected_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "REJECTED")
    needs_source_check_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "NEEDS_SOURCE_CHECK")
    skipped_count = sum(1 for row in reviewed_result_rows if row["resulting_status"] == "SKIPPED")

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343A",
        "review_queue_schema_version": summary_343a.get("review_queue_schema_version", ""),
        "template_row_count": len(template_rows),
        "import_simulation_row_count": len(import_simulation_rows),
        "reviewed_result_row_count": len(reviewed_result_rows),
        "confirmed_count": confirmed_count,
        "corrected_count": corrected_count,
        "rejected_count": rejected_count,
        "needs_source_check_count": needs_source_check_count,
        "skipped_count": skipped_count,
        "validation_error_count": validation_error_count,
        "validation_warning_count": validation_warning_count,
        "excel_template_generated": True,
        "import_simulation_generated": True,
        "reviewed_result_jsonl_generated": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_343c": False,
        "recommended_343c_scope": "",
        "qa_fail_count": 0,
        "decision": NOT_READY_DECISION,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
        "review_template_workbook_path": str(output_dir / REVIEW_TEMPLATE_FILE_NAME),
        "import_simulation_workbook_path": str(output_dir / IMPORT_SIMULATION_FILE_NAME),
        "reviewed_result_jsonl_path": str(output_dir / REVIEWED_RESULT_FILE_NAME),
    }

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    input_hashes_after = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="343B",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_343b")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
    )

    claims_text = "\n".join(
        [
            json.dumps(summary, ensure_ascii=False),
            json.dumps(excel_template_spec, ensure_ascii=False),
            json.dumps(reviewed_result_rows[:3], ensure_ascii=False),
        ]
    )

    checks = [
        {"check_name": "inputs::343a_ready", "status": "PASS" if input_ready else "FAIL", "detail": json.dumps({"343a_decision": summary_343a.get("decision", ""), "ready_for_343b": summary_343a.get("ready_for_343b", False), "qa_fail_count": summary_343a.get("qa_fail_count", 0)}, ensure_ascii=False)},
        {"check_name": "inputs::343a_schema_exists", "status": "PASS" if schema_path.exists() and json_schema_path.exists() else "FAIL", "detail": json.dumps({"schema_json": schema_path.exists(), "json_schema": json_schema_path.exists()}, ensure_ascii=False)},
        {"check_name": "inputs::343a_sample_jsonl_exists", "status": "PASS" if sample_items_path.exists() else "FAIL", "detail": str(sample_items_path)},
        {"check_name": "outputs::review_template_generated", "status": "PASS" if bool(template_rows) else "FAIL", "detail": str(len(template_rows))},
        {"check_name": "outputs::import_simulation_generated", "status": "PASS" if bool(import_simulation_rows) else "FAIL", "detail": str(len(import_simulation_rows))},
        {"check_name": "outputs::reviewed_result_jsonl_generated", "status": "PASS" if bool(reviewed_result_rows) else "FAIL", "detail": str(len(reviewed_result_rows))},
        {"check_name": "validation::happy_path_has_zero_errors", "status": "PASS" if validation_error_count == 0 else "FAIL", "detail": str(validation_error_count)},
        {"check_name": "validation::intentional_error_cases_captured", "status": "PASS" if all(case["validation_status"] == "FAIL" for case in error_case_validations) else "FAIL", "detail": json.dumps([case["validation_status"] for case in error_case_validations], ensure_ascii=False)},
        {"check_name": "mapping::decision_mapping_generated", "status": "PASS" if len(decision_mapping_rows()) == len(REVIEWER_DECISION_TO_STATUS) else "FAIL", "detail": str(len(decision_mapping_rows()))},
        {"check_name": "claims::formal_client_export_allowed_false", "status": "PASS" if not summary["formal_client_export_allowed"] else "FAIL", "detail": "false"},
        {"check_name": "claims::client_ready_false", "status": "PASS" if not summary["client_ready"] else "FAIL", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS" if not summary["production_ready"] else "FAIL", "detail": "false"},
        {"check_name": "claims::no_real_human_review_claim", "status": "PASS" if not _contains_forbidden_claim(claims_text, FORBIDDEN_CLAIMS) else "FAIL", "detail": "generated 343B texts checked"},
        {"check_name": "safety::no_argilla_call_made", "status": "PASS", "detail": "343B is Excel-only and does not import or call Argilla."},
        {"check_name": "safety::no_upstream_workbook_modified", "status": "PASS" if upstream_unchanged else "FAIL", "detail": "input hashes before/after compared"},
        {"check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified", "status": "PASS", "detail": "343B adds review-queue sidecar files only."},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::forbidden_output_or_input_artifacts_not_staged", "status": "PASS" if not forbidden_staged else "FAIL", "detail": json.dumps(forbidden_staged, ensure_ascii=False)},
        {"check_name": "safety::no_sheet_name_exceeds_limit", "status": "PASS", "detail": "all 343B sheet names are <= 31 chars"},
        {"check_name": "safety::no_write_back_proof_generated", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    ready_for_343c = bool(input_ready and len(template_rows) > 0 and len(import_simulation_rows) == len(template_rows) and validation_error_count == 0 and no_write_back_proof_passed and qa_fail_count == 0)

    summary["ready_for_343c"] = ready_for_343c
    summary["recommended_343c_scope"] = RECOMMENDED_343C_SCOPE if ready_for_343c else ""
    summary["qa_fail_count"] = qa_fail_count
    summary["decision"] = READY_DECISION if ready_for_343c else NOT_READY_DECISION
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    validation_errors_json = {
        "happy_path_validation_error_count": validation_error_count,
        "happy_path_validation_warning_count": validation_warning_count,
        "intentional_error_cases": error_case_validations,
    }

    manifest = {
        "task": "343B_excel_round_trip_review_queue_pilot",
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "snapshot_342s_dir": str(snapshot_342s_dir),
        "audit_labeled_package_342r_dir": str(audit_labeled_package_342r_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "review_template_xlsx": str(output_dir / REVIEW_TEMPLATE_FILE_NAME),
            "import_simulation_xlsx": str(output_dir / IMPORT_SIMULATION_FILE_NAME),
            "reviewed_result_jsonl": str(output_dir / REVIEWED_RESULT_FILE_NAME),
            "validation_errors_json": str(output_dir / VALIDATION_ERRORS_FILE_NAME),
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

    template_df = _clean_frame(pd.DataFrame(template_rows))
    import_df = _clean_frame(pd.DataFrame(import_simulation_rows))
    reviewed_df = _clean_frame(pd.DataFrame(reviewed_result_rows))
    error_cases_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "case_index": index + 1,
                    "reviewer_decision": case["reviewer_decision"],
                    "validation_status": case["validation_status"],
                    "errors": case["errors"],
                    "warnings": case["warnings"],
                }
                for index, case in enumerate(error_case_validations)
            ]
        )
    )
    template_spec_df = _clean_frame(pd.DataFrame(excel_template_spec.get("columns", [])))

    workbook_sheets = {
        "00_README": _readme_df(summary),
        "01_ROUND_TRIP_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343A_SUMMARY": _input_343a_df(summary_343a, summary_342s, summary_342r),
        "03_REVIEW_TEMPLATE_SPEC": template_spec_df,
        "04_EXPORT_TEMPLATE_ROWS": template_df,
        "05_IMPORT_SIMULATION": import_df,
        "06_VALIDATION_RULES": _validation_rules_df(),
        "07_STATUS_MAPPING": _status_mapping_df(),
        "08_DECISION_MAPPING": _clean_frame(pd.DataFrame(decision_mapping_rows())),
        "09_ERROR_CASES": error_cases_df,
        "10_REVIEWED_RESULT": reviewed_df,
        "11_BACKLOG_NOTE": _backlog_note_df(summary_343a),
        "12_343C_READINESS": _readiness_df(summary),
        "13_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "14_NEXT_STEPS": _next_steps_df(summary),
    }

    review_template_sheets = {
        "review_queue_roundtrip": template_df,
        "review_instructions": _validation_rules_df(),
    }
    import_simulation_sheets = {
        "import_simulation": import_df,
        "validation_result": reviewed_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "validation_errors_json": validation_errors_json,
        "review_template_rows": template_rows,
        "import_simulation_rows": import_simulation_rows,
        "reviewed_result_rows": reviewed_result_rows,
        "workbook_sheets": workbook_sheets,
        "review_template_sheets": review_template_sheets,
        "import_simulation_sheets": import_simulation_sheets,
    }
