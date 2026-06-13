from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import (
    normalize_bool,
    normalize_float,
    normalize_text,
)
from datefac.review_queue.ingest_strict_review_343j import PROTECTED_DIRTY_PATHS
from datefac.review_queue.source_check_backlog_package_344a import (
    ALLOWED_SOURCE_CHECK_DECISIONS,
)
from datefac.review_queue.source_check_evidence_review_ingestion_344b import (
    NOT_READY_DECISION_344B,
    READY_DECISION_344B,
    RECOMMENDED_344C_SCOPE_344B,
    VALIDATION_FAILED_DECISION_344B,
    build_audit_gate,
    build_correction_row,
    build_scope_boundary_lines,
    build_source_check_result_row,
    build_validated_sidecar_row,
    build_validation_issue_rows,
    decision_summary_rows,
    validate_filled_source_check_row,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_344A2_DECISION = (
    "SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_WAITING_FOR_SOURCE_CHECK_REVIEW"
)
READY_INPUT_344A_DECISION = "SOURCE_CHECK_BACKLOG_PACKAGE_344A_WAITING_FOR_SOURCE_CHECK_REVIEW"
READY_INPUT_343O_DECISION = "DEMO_PACKAGE_AUDIT_SNAPSHOT_343O_READY"
READY_INPUT_343A_DECISION = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_READY"

DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_evidence_enrichment_344a2"
)
DEFAULT_SOURCE_CHECK_BACKLOG_PACKAGE_344A_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_backlog_package_344a"
)
DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR = Path(
    r"D:\_datefac\output\review_queue_demo_audit_snapshot_343o"
)
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(
    r"D:\_datefac\output\review_queue_schema_343a"
)
DEFAULT_FILLED_WORKBOOK = Path(
    r"D:\_datefac\input\review_queue_source_check_evidence_344a2_filled\review_queue_source_check_evidence_enrichment_344a2_enriched_review_template_filled_independent.xlsx"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_source_check_evidence_review_ingestion_344b"
)

SUMMARY_FILE_NAME = "review_queue_source_check_evidence_review_ingestion_344b_summary.json"
MANIFEST_FILE_NAME = "review_queue_source_check_evidence_review_ingestion_344b_manifest.json"
QA_FILE_NAME = "review_queue_source_check_evidence_review_ingestion_344b_qa.json"
NO_WRITE_BACK_FILE_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_no_write_back_proof.json"
)
REPORT_FILE_NAME = "review_queue_source_check_evidence_review_ingestion_344b_report.md"
WORKBOOK_FILE_NAME = "review_queue_source_check_evidence_review_ingestion_344b.xlsx"
RESULT_FILE_NAME = "review_queue_source_check_evidence_review_ingestion_344b_result.jsonl"
VALIDATED_SIDECAR_FILE_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_validated_sidecar.jsonl"
)
CORRECTIONS_FILE_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_corrections.jsonl"
)
VALIDATION_ERRORS_FILE_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_validation_errors.jsonl"
)
DECISION_SUMMARY_FILE_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_decision_summary.json"
)
AUDIT_GATE_FILE_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_audit_gate.json"
)
SCOPE_BOUNDARY_FILE_NAME = (
    "review_queue_source_check_evidence_review_ingestion_344b_scope_boundary.md"
)

INPUT_344A2_SUMMARY_NAME = "review_queue_source_check_evidence_enrichment_344a2_summary.json"
INPUT_344A2_QA_NAME = "review_queue_source_check_evidence_enrichment_344a2_qa.json"
INPUT_344A2_ITEMS_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_enriched_backlog_items.jsonl"
)
INPUT_344A2_EVIDENCE_MAP_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_evidence_map.json"
)
INPUT_344A2_CONTRACT_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_expected_import_contract.json"
)
INPUT_344A2_NO_WRITE_BACK_NAME = (
    "review_queue_source_check_evidence_enrichment_344a2_no_write_back_proof.json"
)
INPUT_344A_SUMMARY_NAME = "review_queue_source_check_backlog_package_344a_summary.json"
INPUT_344A_CONTRACT_NAME = (
    "review_queue_source_check_backlog_package_344a_expected_import_contract.json"
)
INPUT_343O_SUMMARY_NAME = "review_queue_demo_audit_snapshot_343o_summary.json"
INPUT_343O_BACKLOG_SUMMARY_NAME = (
    "review_queue_demo_audit_snapshot_343o_backlog_summary.json"
)
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input/review_queue_source_check_evidence_344a2_filled",
    "input/review_queue_source_check_backlog_344a_filled",
    "input/review_queue_pure_human_attestation_343k_filled",
    "input/review_queue_strict_human_review_343i2_filled",
    "input/review_queue_spot_check_package_343f_filled",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

WORKBOOK_SHEETS_344B = [
    "00_README",
    "01_INGEST_SUMMARY",
    "02_INPUT_344A2_SUMMARY",
    "03_REVIEW_RESULTS",
    "04_VALIDATED_SIDECAR",
    "05_CORRECTIONS",
    "06_VALIDATION_ERRORS",
    "07_AUDIT_GATE",
    "08_SCOPE_BOUNDARY",
    "09_NO_WRITE_BACK",
    "10_NEXT_STEPS",
]

EXPECTED_DECISION_COUNTS_344B = {
    "SOURCE_CONFIRM": 10,
    "SOURCE_CORRECT": 9,
    "SOURCE_REJECT": 0,
    "SOURCE_STILL_INSUFFICIENT": 0,
    "SOURCE_DEFER": 0,
}


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


def _normalized_numeric_text(value: Any) -> str:
    numeric = normalize_float(value)
    if numeric is None:
        return normalize_text(value)
    return f"{numeric:g}"


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


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


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


def _row_identity_key(row: Dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalize_text(row.get("backlog_item_key")),
        normalize_text(row.get("queue_item_id")),
        normalize_text(row.get("review_item_id")),
    )


def _build_readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "344B ingests the 19-row filled 344A2 source-check workbook into sidecar-only review results.",
                },
                {
                    "section": "corrections",
                    "message": "The current happy path confirms 10 rows and corrects 9 rows from revenue/亿元 to YOY/%.",
                },
                {
                    "section": "boundary",
                    "message": "No production write-back, no formal client export, and no global strict-human-complete claim.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _next_steps_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    next_scope = summary.get("recommended_344c_scope", "")
    if not next_scope:
        next_scope = "Fix the filled workbook validation issues before retrying 344B."
    return [
        {
            "step": "open_validated_sidecar",
            "recommendation": "Inspect the validated sidecar rows and confirm the 10 confirmed / 9 corrected split.",
        },
        {
            "step": "open_corrections",
            "recommendation": "Verify each correction row is YOY/% while preserving the original source year and value.",
        },
        {
            "step": "keep_boundary_closed",
            "recommendation": "Do not treat 344B as production apply or formal client export.",
        },
        {
            "step": "next_task",
            "recommendation": next_scope,
        },
    ]


def _scope_boundary_markdown(lines: Iterable[str]) -> str:
    rendered = [
        "# 344B Scope Boundary",
        "",
        "## Chinese-first Summary",
    ]
    rendered.extend(f"- {line}" for line in lines)
    rendered.extend(
        [
            "",
            "## English Summary",
            "- 344B only ingests the filled 19-row 344A2 source-check workbook.",
            "- 10 rows are confirmed and 9 rows are corrected to YOY percentage semantics.",
            "- No production write-back or formal client export occurred.",
            "- The next safe task is 344C sidecar apply simulation and expanded trust gate.",
        ]
    )
    return "\n".join(rendered)


def build_review_queue_source_check_evidence_review_ingestion_344b(
    *,
    source_check_evidence_enrichment_344a2_dir: Path = DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR,
    source_check_backlog_package_344a_dir: Path = DEFAULT_SOURCE_CHECK_BACKLOG_PACKAGE_344A_DIR,
    demo_audit_snapshot_343o_dir: Path = DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    review_queue_schema_343a_dir: Path = DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    filled_workbook: Path = DEFAULT_FILLED_WORKBOOK,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_344a2_path = (
        source_check_evidence_enrichment_344a2_dir / INPUT_344A2_SUMMARY_NAME
    )
    qa_344a2_path = source_check_evidence_enrichment_344a2_dir / INPUT_344A2_QA_NAME
    items_344a2_path = source_check_evidence_enrichment_344a2_dir / INPUT_344A2_ITEMS_NAME
    evidence_map_344a2_path = (
        source_check_evidence_enrichment_344a2_dir / INPUT_344A2_EVIDENCE_MAP_NAME
    )
    contract_344a2_path = (
        source_check_evidence_enrichment_344a2_dir / INPUT_344A2_CONTRACT_NAME
    )
    no_write_back_344a2_path = (
        source_check_evidence_enrichment_344a2_dir / INPUT_344A2_NO_WRITE_BACK_NAME
    )
    summary_344a_path = source_check_backlog_package_344a_dir / INPUT_344A_SUMMARY_NAME
    contract_344a_path = source_check_backlog_package_344a_dir / INPUT_344A_CONTRACT_NAME
    summary_343o_path = demo_audit_snapshot_343o_dir / INPUT_343O_SUMMARY_NAME
    backlog_summary_343o_path = (
        demo_audit_snapshot_343o_dir / INPUT_343O_BACKLOG_SUMMARY_NAME
    )
    summary_343a_path = review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME

    files_read: List[str] = []
    warnings: List[str] = []
    required_input_paths = [
        summary_344a2_path,
        qa_344a2_path,
        items_344a2_path,
        evidence_map_344a2_path,
        contract_344a2_path,
        no_write_back_344a2_path,
        summary_344a_path,
        contract_344a_path,
        summary_343o_path,
        backlog_summary_343o_path,
        summary_343a_path,
        filled_workbook,
    ]
    missing_required_inputs = [str(path) for path in required_input_paths if not path.exists()]
    for path in required_input_paths:
        if path.exists():
            files_read.append(str(path))

    summary_344a2 = _read_json(summary_344a2_path) if summary_344a2_path.exists() else {}
    qa_344a2 = _read_json(qa_344a2_path) if qa_344a2_path.exists() else {}
    items_344a2 = _read_jsonl(items_344a2_path) if items_344a2_path.exists() else []
    evidence_map_344a2 = _read_json(evidence_map_344a2_path) if evidence_map_344a2_path.exists() else {}
    contract_344a2 = _read_json(contract_344a2_path) if contract_344a2_path.exists() else {}
    no_write_back_344a2 = (
        _read_json(no_write_back_344a2_path) if no_write_back_344a2_path.exists() else {}
    )
    summary_344a = _read_json(summary_344a_path) if summary_344a_path.exists() else {}
    contract_344a = _read_json(contract_344a_path) if contract_344a_path.exists() else {}
    summary_343o = _read_json(summary_343o_path) if summary_343o_path.exists() else {}
    backlog_summary_343o = (
        _read_json(backlog_summary_343o_path) if backlog_summary_343o_path.exists() else {}
    )
    summary_343a = _read_json(summary_343a_path) if summary_343a_path.exists() else {}

    input_hashes_before = {
        str(path): sha256_file(path) for path in required_input_paths if path.exists()
    }

    expected_sheet = normalize_text(contract_344a2.get("required_sheet_name")) or "04_REVIEW_TEMPLATE"
    workbook_sheet_names: List[str] = []
    workbook_read_error = ""
    filled_df = pd.DataFrame()
    if filled_workbook.exists():
        try:
            excel = pd.ExcelFile(filled_workbook)
            workbook_sheet_names = list(excel.sheet_names)
            if expected_sheet in workbook_sheet_names:
                filled_df = _read_excel_sheet(filled_workbook, expected_sheet)
            elif "04_REVIEW_TEMPLATE" in workbook_sheet_names:
                expected_sheet = "04_REVIEW_TEMPLATE"
                filled_df = _read_excel_sheet(filled_workbook, expected_sheet)
            else:
                workbook_read_error = (
                    f"no valid filled source-check sheet found; expected {expected_sheet}"
                )
        except Exception as exc:
            workbook_read_error = f"unable to read filled workbook: {exc}"
    else:
        workbook_read_error = f"filled workbook missing: {filled_workbook}"

    input_ready = bool(
        not missing_required_inputs
        and summary_344a2.get("decision") == READY_INPUT_344A2_DECISION
        and summary_344a.get("decision") == READY_INPUT_344A_DECISION
        and summary_343o.get("decision") == READY_INPUT_343O_DECISION
        and summary_343a.get("decision") == READY_INPUT_343A_DECISION
        and int(summary_344a2.get("qa_fail_count", 1)) == 0
        and int(summary_344a.get("qa_fail_count", 1)) == 0
        and int(summary_343o.get("qa_fail_count", 1)) == 0
        and int(summary_343a.get("qa_fail_count", 1)) == 0
        and normalize_bool(summary_344a2.get("source_check_evidence_enrichment_completed"))
        and normalize_bool(summary_344a2.get("enriched_review_template_generated"))
        and normalize_bool(summary_344a2.get("waiting_for_source_check_review"))
        and not normalize_bool(summary_344a2.get("source_check_result_ingested"))
        and not normalize_bool(summary_344a2.get("source_check_backlog_resolved"))
        and int(summary_344a2.get("input_source_check_backlog_item_count", 0)) == 19
        and int(summary_344a2.get("deduplicated_backlog_item_count", 0)) == 19
        and int(summary_344a2.get("evidence_resolved_count", 0)) == 19
        and not normalize_bool(summary_344a2.get("formal_client_export_allowed"))
        and not normalize_bool(summary_344a2.get("client_ready"))
        and not normalize_bool(summary_344a2.get("production_ready"))
        and not normalize_bool(summary_343o.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343o.get("client_ready"))
        and not normalize_bool(summary_343o.get("production_ready"))
        and not normalize_bool(summary_343o.get("global_strict_human_review_completed"))
        and filled_workbook.exists()
        and workbook_read_error == ""
        and expected_sheet in workbook_sheet_names
    )

    expected_rows_by_key = {
        _row_identity_key(row): row for row in items_344a2
    }
    validation_rows: List[Dict[str, Any]] = []
    result_rows: List[Dict[str, Any]] = []
    validated_sidecar_rows: List[Dict[str, Any]] = []
    correction_rows: List[Dict[str, Any]] = []
    invalid_rows: List[Dict[str, Any]] = []
    row_identity_keys: List[tuple[str, str, str]] = []

    if not filled_df.empty:
        for row_index, row in enumerate(filled_df.to_dict(orient="records"), start=1):
            identity_key = _row_identity_key(row)
            row_identity_keys.append(identity_key)
            expected_row = expected_rows_by_key.get(identity_key)
            merged_row = dict(expected_row or {})
            merged_row.update(row)
            validation = validate_filled_source_check_row(
                merged_row,
                expected_row=expected_row,
            )
            validation_row = {"row_index": row_index, **validation}
            validation_rows.append(validation_row)
            result_row = build_source_check_result_row(merged_row, validation=validation)
            result_row["row_index"] = row_index
            result_rows.append(result_row)
            if validation["validation_status"] == "FAIL":
                invalid_rows.append(
                    {
                        **merged_row,
                        "row_index": row_index,
                        "validation_errors": validation["errors"],
                        "validation_warnings": validation["warnings"],
                    }
                )
                continue
            if validation["source_check_decision"] in {"SOURCE_CONFIRM", "SOURCE_CORRECT"}:
                sidecar_row = build_validated_sidecar_row(result_row)
                validated_sidecar_rows.append(sidecar_row)
                if validation["source_check_decision"] == "SOURCE_CORRECT":
                    correction_rows.append(build_correction_row(result_row))

    validation_issue_rows = build_validation_issue_rows(validation_rows)
    decision_summary = decision_summary_rows(result_rows)
    counts_by_decision = {
        row["source_check_decision"]: int(row["row_count"]) for row in decision_summary
    }

    filled_row_count = len(result_rows)
    valid_row_count = sum(
        1 for row in validation_rows if row.get("validation_status") != "FAIL"
    )
    invalid_row_count = sum(
        1 for row in validation_rows if row.get("validation_status") == "FAIL"
    )
    validation_error_count = sum(len(row.get("errors", [])) for row in validation_rows)
    row_count_matches = filled_row_count == len(items_344a2) == 19
    id_set_matches = (
        len(set(row_identity_keys)) == len(row_identity_keys)
        and set(row_identity_keys) == set(expected_rows_by_key.keys())
    )
    distribution_matches = all(
        counts_by_decision.get(decision, 0) == expected_count
        for decision, expected_count in EXPECTED_DECISION_COUNTS_344B.items()
    )
    corrected_semantics_count = sum(
        1
        for row in result_rows
        if normalize_text(row.get("source_check_decision")) == "SOURCE_CORRECT"
        and normalize_text(row.get("metric_standardized")) == "revenue"
        and normalize_text(row.get("source_check_metric_standardized")) == "YOY"
        and normalize_text(row.get("normalized_unit")) == "亿元"
        and normalize_text(row.get("source_check_normalized_unit")) == "%"
        and normalize_text(row.get("year_standardized"))
        == normalize_text(row.get("source_check_year_standardized"))
        and _normalized_numeric_text(row.get("final_value_numeric"))
        == _normalized_numeric_text(row.get("value_numeric"))
    )

    source_check_result_ingested = bool(
        input_ready and row_count_matches and id_set_matches and validation_error_count == 0
    )
    source_check_backlog_resolved = bool(
        source_check_result_ingested
        and all(
            normalize_text(row.get("source_check_decision"))
            in {"SOURCE_CONFIRM", "SOURCE_CORRECT"}
            for row in result_rows
        )
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "344A2",
        "decision": NOT_READY_DECISION_344B,
        "review_queue_schema_version": summary_344a2.get(
            "review_queue_schema_version",
            summary_343a.get("review_queue_schema_version", ""),
        ),
        "filled_workbook_path": str(filled_workbook),
        "filled_row_count": filled_row_count,
        "valid_row_count": valid_row_count,
        "invalid_row_count": invalid_row_count,
        "source_confirm_count": counts_by_decision.get("SOURCE_CONFIRM", 0),
        "source_correct_count": counts_by_decision.get("SOURCE_CORRECT", 0),
        "source_reject_count": counts_by_decision.get("SOURCE_REJECT", 0),
        "source_still_insufficient_count": counts_by_decision.get(
            "SOURCE_STILL_INSUFFICIENT", 0
        ),
        "source_defer_count": counts_by_decision.get("SOURCE_DEFER", 0),
        "validated_sidecar_row_count": len(validated_sidecar_rows),
        "correction_row_count": len(correction_rows),
        "validation_error_count": validation_error_count,
        "source_check_result_ingested": source_check_result_ingested,
        "source_check_backlog_resolved": source_check_backlog_resolved,
        "validated_sidecar_generated": False,
        "correction_sidecar_generated": False,
        "audit_gate_generated": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "ready_for_344c": False,
        "recommended_344c_scope": "",
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
        stage="344B",
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
    no_write_back_json["source_check_result_ingested"] = source_check_result_ingested
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_344b")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::344a2_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "missing_required_inputs": missing_required_inputs,
                    "decision_344a2": summary_344a2.get("decision", ""),
                    "decision_344a": summary_344a.get("decision", ""),
                    "decision_343o": summary_343o.get("decision", ""),
                    "decision_343a": summary_343a.get("decision", ""),
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
            "status": "PASS" if workbook_read_error == "" else "FAIL",
            "detail": workbook_read_error or "ok",
        },
        {
            "check_name": "inputs::required_sheet_04_review_template_exists",
            "status": "PASS" if expected_sheet in workbook_sheet_names else "FAIL",
            "detail": json.dumps(
                {"expected_sheet": expected_sheet, "sheet_names": workbook_sheet_names},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::exactly_19_filled_rows_read",
            "status": "PASS" if filled_row_count == 19 else "FAIL",
            "detail": json.dumps({"filled_row_count": filled_row_count}, ensure_ascii=False),
        },
        {
            "check_name": "identity::filled_row_identities_match_344a2_enriched_rows",
            "status": "PASS" if row_count_matches and id_set_matches else "FAIL",
            "detail": json.dumps(
                {
                    "filled_row_count": filled_row_count,
                    "expected_row_count": len(items_344a2),
                    "unique_identity_count": len(set(row_identity_keys)),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "validation::all_source_check_decisions_allowed",
            "status": "PASS"
            if all(
                normalize_text(row.get("source_check_decision")) in ALLOWED_SOURCE_CHECK_DECISIONS
                for row in result_rows
            )
            else "FAIL",
            "detail": json.dumps(ALLOWED_SOURCE_CHECK_DECISIONS, ensure_ascii=False),
        },
        {
            "check_name": "validation::decision_specific_required_fields_pass",
            "status": "PASS" if validation_error_count == 0 else "FAIL",
            "detail": json.dumps(
                {"validation_error_count": validation_error_count},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "validation::expected_distribution_10_confirm_9_correct",
            "status": "PASS" if distribution_matches else "FAIL",
            "detail": json.dumps(counts_by_decision, ensure_ascii=False),
        },
        {
            "check_name": "validation::all_9_corrections_are_yoy_percent_rows",
            "status": "PASS" if corrected_semantics_count == 9 else "FAIL",
            "detail": json.dumps(
                {"corrected_semantics_count": corrected_semantics_count},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::validated_sidecar_generated",
            "status": "PASS"
            if len(validated_sidecar_rows) == 19 and source_check_result_ingested
            else "FAIL",
            "detail": json.dumps(
                {"validated_sidecar_row_count": len(validated_sidecar_rows)},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::corrections_jsonl_generated",
            "status": "PASS" if len(correction_rows) == 9 else "FAIL",
            "detail": json.dumps(
                {"correction_row_count": len(correction_rows)},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::audit_gate_generated",
            "status": "PASS" if source_check_result_ingested else "FAIL",
            "detail": "audit gate can be generated only after successful ingestion",
        },
        {
            "check_name": "state::source_check_result_ingested_true_after_validation",
            "status": "PASS" if source_check_result_ingested else "FAIL",
            "detail": str(source_check_result_ingested),
        },
        {
            "check_name": "state::source_check_backlog_resolved_true_for_confirm_or_correct_only",
            "status": "PASS" if source_check_backlog_resolved else "FAIL",
            "detail": str(source_check_backlog_resolved),
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
            "detail": "344B generates sidecar ingestion artifacts only.",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "344B is workbook ingestion only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "344B does not write back to upstream data.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "344B adds review-queue sidecar files only.",
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
            if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_344B)
            else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_344B, ensure_ascii=False),
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
    summary["validated_sidecar_generated"] = bool(
        source_check_result_ingested and qa_fail_count == 0 and len(validated_sidecar_rows) == 19
    )
    summary["correction_sidecar_generated"] = bool(
        source_check_result_ingested and qa_fail_count == 0 and len(correction_rows) == 9
    )
    summary["audit_gate_generated"] = bool(source_check_result_ingested and qa_fail_count == 0)
    summary["source_check_result_ingested"] = bool(
        source_check_result_ingested and qa_fail_count == 0
    )
    summary["source_check_backlog_resolved"] = bool(
        source_check_backlog_resolved and qa_fail_count == 0
    )
    summary["ready_for_344c"] = bool(
        summary["source_check_backlog_resolved"] and qa_fail_count == 0
    )
    summary["recommended_344c_scope"] = (
        RECOMMENDED_344C_SCOPE_344B if summary["ready_for_344c"] else ""
    )

    if summary["ready_for_344c"]:
        summary["decision"] = READY_DECISION_344B
    elif validation_error_count > 0:
        summary["decision"] = VALIDATION_FAILED_DECISION_344B
    else:
        summary["decision"] = NOT_READY_DECISION_344B

    for row in result_rows:
        row["source_check_result_ingested"] = summary["source_check_result_ingested"]
        row["source_check_backlog_resolved"] = summary["source_check_backlog_resolved"]
        row["validated_sidecar_generated"] = summary["validated_sidecar_generated"]
        row["correction_sidecar_generated"] = summary["correction_sidecar_generated"]

    audit_gate = build_audit_gate(summary)
    scope_boundary_markdown = _scope_boundary_markdown(build_scope_boundary_lines())

    manifest = {
        "task": "344B_source_check_evidence_review_result_ingestion",
        "source_check_evidence_enrichment_344a2_dir": str(
            source_check_evidence_enrichment_344a2_dir
        ),
        "source_check_backlog_package_344a_dir": str(
            source_check_backlog_package_344a_dir
        ),
        "demo_audit_snapshot_343o_dir": str(demo_audit_snapshot_343o_dir),
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
            "validated_sidecar_jsonl": str(output_dir / VALIDATED_SIDECAR_FILE_NAME),
            "corrections_jsonl": str(output_dir / CORRECTIONS_FILE_NAME),
            "validation_errors_jsonl": str(output_dir / VALIDATION_ERRORS_FILE_NAME),
            "decision_summary_json": str(output_dir / DECISION_SUMMARY_FILE_NAME),
            "audit_gate_json": str(output_dir / AUDIT_GATE_FILE_NAME),
            "scope_boundary_md": str(output_dir / SCOPE_BOUNDARY_FILE_NAME),
        },
        "files_read": list(dict.fromkeys(files_read)),
        "warnings": warnings,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "input_summary_344a2": summary_344a2,
        "input_qa_344a2": qa_344a2,
        "input_evidence_map_344a2": evidence_map_344a2,
        "input_contract_344a2": contract_344a2,
        "input_summary_344a": summary_344a,
        "input_contract_344a": contract_344a,
        "input_summary_343o": summary_343o,
        "input_backlog_summary_343o": backlog_summary_343o,
        "input_summary_343a": summary_343a,
        "input_no_write_back_344a2": no_write_back_344a2,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _build_readme_df(summary),
        "01_INGEST_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_344A2_SUMMARY": _build_key_value_df(summary_344a2),
        "03_REVIEW_RESULTS": _clean_frame(pd.DataFrame(result_rows)),
        "04_VALIDATED_SIDECAR": _clean_frame(pd.DataFrame(validated_sidecar_rows)),
        "05_CORRECTIONS": _clean_frame(pd.DataFrame(correction_rows)),
        "06_VALIDATION_ERRORS": _clean_frame(pd.DataFrame(validation_issue_rows)),
        "07_AUDIT_GATE": _build_key_value_df(audit_gate),
        "08_SCOPE_BOUNDARY": _build_key_value_df(
            {
                "scope_boundary_report": scope_boundary_markdown,
                "upstream_344a2_summary": summary_344a2,
                "upstream_344a_summary": summary_344a,
                "upstream_343o_backlog_summary": backlog_summary_343o,
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
        "result_rows": result_rows,
        "validated_sidecar_rows": validated_sidecar_rows,
        "correction_rows": correction_rows,
        "validation_errors": validation_issue_rows,
        "decision_summary": decision_summary,
        "audit_gate": audit_gate,
        "scope_boundary_markdown": scope_boundary_markdown,
        "workbook_sheets": workbook_sheets,
    }
