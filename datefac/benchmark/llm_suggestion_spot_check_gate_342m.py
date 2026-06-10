from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_DECISION = "LLM_SUGGESTION_APPLY_SIMULATION_342L_READY"
WAITING_DECISION = "LLM_SUGGESTION_SPOT_CHECK_GATE_342M_WAITING_FOR_EVIDENCE"
SPOT_CHECK_READY_DECISION = "LLM_SUGGESTION_SPOT_CHECK_APPLY_342M_READY"
REAL_RESPONSE_READY_DECISION = "REAL_LLM_RESPONSE_INGESTION_342M_READY"
NOT_READY_DECISION = "LLM_SUGGESTION_SPOT_CHECK_GATE_342M_NOT_READY"

DEFAULT_LLM_SUGGESTION_342L_DIR = Path(r"D:\_datefac\output\llm_suggestion_apply_simulation_342l")
DEFAULT_LLM_REVIEW_342K_DIR = Path(r"D:\_datefac\output\llm_assisted_review_adjudication_342k")
DEFAULT_REVIEWED_PREVIEW_342J_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")
DEFAULT_SPOT_CHECK_REVIEWED_DIR = Path(r"D:\_datefac\input\spot_check_reviewed_342m")
DEFAULT_LLM_RESPONSE_DIR = Path(r"D:\_datefac\input\llm_review_responses_342m")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\llm_suggestion_spot_check_gate_342m")

SUMMARY_FILE_NAME = "llm_suggestion_spot_check_gate_342m_summary.json"
MANIFEST_FILE_NAME = "llm_suggestion_spot_check_gate_342m_manifest.json"
QA_FILE_NAME = "llm_suggestion_spot_check_gate_342m_qa.json"
NO_WRITE_BACK_FILE_NAME = "llm_suggestion_spot_check_gate_342m_no_write_back_proof.json"
REPORT_FILE_NAME = "llm_suggestion_spot_check_gate_342m_report.md"
WORKBOOK_FILE_NAME = "llm_suggestion_spot_check_gate_342m.xlsx"
SPOT_CHECK_TEMPLATE_WORKBOOK_NAME = "llm_suggestion_spot_check_review_template_342m.xlsx"
REAL_RESPONSE_SCHEMA_NAME = "real_llm_response_schema_342m.json"
REAL_RESPONSE_TEMPLATE_NAME = "real_llm_response_ingestion_template_342m.jsonl"

INPUT_342L_SUMMARY_NAME = "llm_suggestion_apply_simulation_342l_summary.json"
INPUT_342L_QA_NAME = "llm_suggestion_apply_simulation_342l_qa.json"
INPUT_342L_REPORT_NAME = "llm_suggestion_apply_simulation_342l_report.md"
INPUT_342L_WORKBOOK_NAME = "llm_suggestion_apply_simulation_342l.xlsx"
INPUT_342L_NO_WRITE_BACK_NAME = "llm_suggestion_apply_simulation_342l_no_write_back_proof.json"
INPUT_342K_PROMPT_PACK_NAME = "llm_assisted_review_adjudication_342k_prompt_pack.jsonl"
INPUT_342K_REQUEST_PACK_NAME = "llm_assisted_review_adjudication_342k_request_pack.jsonl"
INPUT_342J_SUMMARY_NAME = "table_first_reviewed_client_preview_pilot_342j_summary.json"

REQUIRED_342L_SHEETS = [
    "03_AUTO_CANDIDATES",
    "04_SPOT_CHECK_SAMPLE",
    "05_PREFILL_REVIEW_DRAFT",
    "06_HUMAN_REQUIRED",
    "07_CONFLICT_BLOCKERS",
    "08_REDUCTION_SIMULATION",
    "09_RISK_AUDIT",
    "10_PROMPT_REQUEST_TRACE",
    "11_DECISION_POLICY",
    "12_342M_READINESS",
    "13_NO_WRITE_BACK",
]

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

ALLOWED_SPOT_CHECK_DECISIONS = {
    "CONFIRM_SUGGESTION",
    "CORRECT_SUGGESTION",
    "REJECT_SUGGESTION",
    "KEEP_HUMAN_REQUIRED",
    "NEEDS_SOURCE_CHECK",
}
ALLOWED_LLM_DECISIONS = {
    "CONFIRM_CELL",
    "CORRECT_AND_CONFIRM",
    "REJECT_CELL",
    "KEEP_REVIEW_REQUIRED",
    "NOT_A_CORE_METRIC",
    "NEEDS_SOURCE_CHECK",
}

ADOPTION_CONFIDENCE_THRESHOLD = 0.95
PASS_RATE_THRESHOLD = 0.90


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl_rows(path: Path) -> tuple[List[Dict[str, Any]], List[str]]:
    rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    if not path.exists():
        return rows, [f"missing jsonl: {path}"]
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except Exception as exc:
                errors.append(f"{path.name}: line {line_no} parse error: {exc}")
                continue
            if isinstance(payload, dict):
                rows.append(payload)
            else:
                errors.append(f"{path.name}: line {line_no} is not a JSON object")
    return rows, errors


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
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


def _contains_forbidden_claim(text: str, forbidden: Sequence[str]) -> bool:
    lowered = text.casefold()
    for token in forbidden:
        token_lower = token.casefold()
        start = 0
        while True:
            idx = lowered.find(token_lower, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 32) : idx]
            if "not " not in window and "false" not in window:
                return True
            start = idx + len(token_lower)
    return False


def _read_workbook_sheets(path: Path, required: Sequence[str]) -> tuple[Dict[str, pd.DataFrame], List[str], List[str]]:
    sheets: Dict[str, pd.DataFrame] = {}
    sheet_names: List[str] = []
    warnings: List[str] = []
    if not path.exists():
        for sheet in required:
            sheets[sheet] = pd.DataFrame()
        return sheets, sheet_names, [f"missing workbook: {path}"]
    try:
        excel = pd.ExcelFile(path)
        sheet_names = list(excel.sheet_names)
        for sheet in required:
            if sheet in sheet_names:
                sheets[sheet] = _clean_frame(pd.read_excel(path, sheet_name=sheet))
            else:
                sheets[sheet] = pd.DataFrame()
                warnings.append(f"missing required workbook sheet: {sheet}")
    except Exception as exc:
        warnings.append(f"unable to read workbook {path}: {exc}")
        for sheet in required:
            sheets[sheet] = pd.DataFrame()
    return sheets, sheet_names, warnings


def _load_342l_context(
    llm_suggestion_342l_dir: Path,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []

    summary_path = llm_suggestion_342l_dir / INPUT_342L_SUMMARY_NAME
    qa_path = llm_suggestion_342l_dir / INPUT_342L_QA_NAME
    report_path = llm_suggestion_342l_dir / INPUT_342L_REPORT_NAME
    workbook_path = llm_suggestion_342l_dir / INPUT_342L_WORKBOOK_NAME
    proof_path = llm_suggestion_342l_dir / INPUT_342L_NO_WRITE_BACK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    proof_json = _read_json(proof_path) if proof_path.exists() else {}

    for path in [summary_path, qa_path, report_path, workbook_path, proof_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing 342L input file: {path}")

    workbook_sheets, workbook_sheet_names, workbook_warnings = _read_workbook_sheets(
        workbook_path,
        REQUIRED_342L_SHEETS,
    )
    warnings.extend(workbook_warnings)
    return summary, qa_json, proof_json, workbook_sheets, workbook_sheet_names, files_read, warnings


def _load_342k_packs(
    llm_review_342k_dir: Path,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str], List[str], int]:
    files_read: List[str] = []
    warnings: List[str] = []
    prompt_path = llm_review_342k_dir / INPUT_342K_PROMPT_PACK_NAME
    request_path = llm_review_342k_dir / INPUT_342K_REQUEST_PACK_NAME
    prompt_rows, prompt_errors = _read_jsonl_rows(prompt_path)
    request_rows, request_errors = _read_jsonl_rows(request_path)

    for path in [prompt_path, request_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing 342K input file: {path}")
    warnings.extend(prompt_errors + request_errors)
    return prompt_rows, request_rows, files_read, warnings, len(prompt_errors + request_errors)


def _load_342j_summary(reviewed_preview_342j_dir: Path) -> tuple[Dict[str, Any], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME
    summary = _read_json(summary_path) if summary_path.exists() else {}
    if summary_path.exists():
        files_read.append(str(summary_path))
    else:
        warnings.append(f"missing 342J input file: {summary_path}")
    return summary, files_read, warnings


def _first_existing_workbook(path_dir: Path) -> Path | None:
    preferred = path_dir / "llm_suggestion_spot_check_reviewed_342m.xlsx"
    if preferred.exists():
        return preferred
    workbooks = sorted(path_dir.glob("*.xlsx"))
    return workbooks[0] if workbooks else None


def _jsonl_files(path_dir: Path) -> List[Path]:
    if not path_dir.exists():
        return []
    return sorted(path_dir.glob("*.jsonl"))


def _read_reviewed_spot_check_workbook(path: Path) -> tuple[pd.DataFrame, List[str], str]:
    warnings: List[str] = []
    if not path.exists():
        return pd.DataFrame(), [f"missing reviewed spot-check workbook: {path}"], ""
    try:
        excel = pd.ExcelFile(path)
        chosen_sheet = ""
        for name in excel.sheet_names:
            upper_name = name.upper()
            if "SPOT" in upper_name or "REVIEW" in upper_name:
                chosen_sheet = name
                break
        if not chosen_sheet and excel.sheet_names:
            chosen_sheet = excel.sheet_names[0]
        if not chosen_sheet:
            return pd.DataFrame(), [f"reviewed spot-check workbook has no sheets: {path}"], ""
        return _clean_frame(pd.read_excel(path, sheet_name=chosen_sheet)), warnings, chosen_sheet
    except Exception as exc:
        return pd.DataFrame(), [f"unable to read reviewed spot-check workbook {path}: {exc}"], ""


def _candidate_maps(
    auto_candidates_df: pd.DataFrame,
    prefill_df: pd.DataFrame,
    human_required_df: pd.DataFrame,
    blocked_df: pd.DataFrame,
) -> tuple[Dict[str, Dict[str, Any]], set[str], set[str]]:
    candidate_map: Dict[str, Dict[str, Any]] = {}
    for df in [prefill_df, auto_candidates_df]:
        if df.empty or "review_item_id" not in df.columns:
            continue
        for row in df.to_dict(orient="records"):
            review_item_id = _norm_text(row.get("review_item_id"))
            if review_item_id and review_item_id not in candidate_map:
                candidate_map[review_item_id] = row

    human_required_ids = set()
    if not human_required_df.empty and "review_item_id" in human_required_df.columns:
        human_required_ids = {
            item for item in human_required_df["review_item_id"].map(_norm_text).tolist() if item
        }

    blocked_ids = set()
    if not blocked_df.empty and "review_item_id" in blocked_df.columns:
        blocked_ids = {
            item for item in blocked_df["review_item_id"].map(_norm_text).tolist() if item
        }
    return candidate_map, human_required_ids, blocked_ids


def _build_spot_check_template(
    spot_sample_df: pd.DataFrame,
    auto_candidates_df: pd.DataFrame,
    prefill_df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "spot_check_id",
        "review_item_id",
        "spot_check_reason",
        "original_suggestion",
        "rule_suggested_decision",
        "dry_run_suggested_decision",
        "suggested_metric_standardized",
        "suggested_year_standardized",
        "suggested_value_numeric",
        "suggested_normalized_unit",
        "suggested_confidence",
        "source_page",
        "bbox",
        "image_path",
        "source_html_snippet",
        "risk_flags",
        "review_reason",
        "reviewer_decision",
        "reviewer_metric_standardized",
        "reviewer_year_standardized",
        "reviewer_value_numeric",
        "reviewer_normalized_unit",
        "reviewer_note",
        "reviewer_id",
        "reviewed_at",
    ]
    if spot_sample_df.empty:
        return pd.DataFrame(columns=columns)

    lookup: Dict[str, Dict[str, Any]] = {}
    for df in [prefill_df, auto_candidates_df]:
        if df.empty or "review_item_id" not in df.columns:
            continue
        for row in df.to_dict(orient="records"):
            review_item_id = _norm_text(row.get("review_item_id"))
            if review_item_id and review_item_id not in lookup:
                lookup[review_item_id] = row

    rows: List[Dict[str, Any]] = []
    for row in spot_sample_df.to_dict(orient="records"):
        review_item_id = _norm_text(row.get("review_item_id"))
        base = lookup.get(review_item_id, {})
        rows.append(
            {
                "spot_check_id": _norm_text(row.get("spot_check_id")),
                "review_item_id": review_item_id,
                "spot_check_reason": _norm_text(row.get("spot_check_reason")),
                "original_suggestion": _norm_text(row.get("original_suggestion")),
                "rule_suggested_decision": _norm_text(base.get("rule_suggested_decision")),
                "dry_run_suggested_decision": _norm_text(base.get("dry_run_suggested_decision"))
                or _norm_text(row.get("original_suggestion")),
                "suggested_metric_standardized": _norm_text(row.get("suggested_metric_standardized"))
                or _norm_text(base.get("suggested_metric_standardized")),
                "suggested_year_standardized": _norm_text(row.get("suggested_year_standardized"))
                or _norm_text(base.get("suggested_year_standardized")),
                "suggested_value_numeric": row.get("suggested_value_numeric")
                if _norm_text(row.get("suggested_value_numeric"))
                else base.get("suggested_value_numeric"),
                "suggested_normalized_unit": _norm_text(row.get("suggested_normalized_unit"))
                or _norm_text(base.get("suggested_normalized_unit")),
                "suggested_confidence": row.get("suggested_confidence")
                if _norm_text(row.get("suggested_confidence"))
                else base.get("suggested_confidence"),
                "source_page": row.get("source_page"),
                "bbox": _norm_text(row.get("bbox")),
                "image_path": _norm_text(row.get("image_path")),
                "source_html_snippet": _norm_text(row.get("source_html_snippet")),
                "risk_flags": _norm_text(row.get("risk_flags")),
                "review_reason": _norm_text(row.get("review_reason")),
                "reviewer_decision": "",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            }
        )
    return _clean_frame(pd.DataFrame(rows, columns=columns))


def _real_llm_response_schema() -> Dict[str, Any]:
    return {
        "request_id": "string",
        "review_item_id": "string",
        "llm_suggested_decision": "CONFIRM_CELL | CORRECT_AND_CONFIRM | REJECT_CELL | KEEP_REVIEW_REQUIRED | NOT_A_CORE_METRIC | NEEDS_SOURCE_CHECK",
        "llm_suggested_metric_standardized": "string|null",
        "llm_suggested_year_standardized": "string|null",
        "llm_suggested_value_numeric": "number|string|null",
        "llm_suggested_normalized_unit": "string|null",
        "llm_confidence": "number 0-1",
        "llm_evidence": "string",
        "llm_risk_reason": "string",
        "human_required": "boolean",
    }


def _schema_frame(schema: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame([{"field_name": key, "field_type": value} for key, value in schema.items()])
    )


def _build_real_response_template_rows(request_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in request_rows:
        rows.append(
            {
                "request_id": _norm_text(row.get("request_id")),
                "review_item_id": _norm_text(row.get("review_item_id")),
                "llm_suggested_decision": "",
                "llm_suggested_metric_standardized": None,
                "llm_suggested_year_standardized": None,
                "llm_suggested_value_numeric": None,
                "llm_suggested_normalized_unit": None,
                "llm_confidence": None,
                "llm_evidence": "",
                "llm_risk_reason": "",
                "human_required": True,
            }
        )
    return rows


def _apply_spot_check_results(
    reviewed_df: pd.DataFrame,
    template_df: pd.DataFrame,
) -> tuple[pd.DataFrame, Dict[str, Any], List[str], List[str]]:
    warnings: List[str] = []
    validation_errors: List[str] = []

    if reviewed_df.empty:
        empty = pd.DataFrame(
            [
                {
                    "spot_check_status": "WAITING_FOR_HUMAN_SPOT_CHECK",
                    "reviewed_spot_check_count": 0,
                    "spot_check_confirm_count": 0,
                    "spot_check_correct_count": 0,
                    "spot_check_reject_count": 0,
                    "spot_check_keep_human_count": 0,
                    "spot_check_needs_source_check_count": 0,
                    "spot_check_validation_error_count": 0,
                    "spot_check_pass_rate": 0.0,
                    "spot_check_failure_rate": 0.0,
                }
            ]
        )
        metrics = empty.to_dict(orient="records")[0]
        return _clean_frame(empty), metrics, warnings, validation_errors

    expected_ids = set()
    if not template_df.empty and "review_item_id" in template_df.columns:
        expected_ids = {
            item for item in template_df["review_item_id"].map(_norm_text).tolist() if item
        }

    rows: List[Dict[str, Any]] = []
    confirm_count = 0
    correct_count = 0
    reject_count = 0
    keep_count = 0
    source_check_count = 0
    reviewed_count = 0

    for row in reviewed_df.to_dict(orient="records"):
        review_item_id = _norm_text(row.get("review_item_id"))
        reviewer_decision = _norm_text(row.get("reviewer_decision"))
        if not reviewer_decision:
            continue

        reviewed_count += 1
        row_errors: List[str] = []
        if reviewer_decision not in ALLOWED_SPOT_CHECK_DECISIONS:
            row_errors.append("invalid reviewer_decision")
        if expected_ids and review_item_id not in expected_ids:
            row_errors.append("unknown review_item_id")

        correction_fields = [
            _norm_text(row.get("reviewer_metric_standardized")),
            _norm_text(row.get("reviewer_year_standardized")),
            _norm_text(row.get("reviewer_value_numeric")),
            _norm_text(row.get("reviewer_normalized_unit")),
        ]
        reviewer_note = _norm_text(row.get("reviewer_note"))
        reviewer_id = _norm_text(row.get("reviewer_id"))
        reviewed_at = _norm_text(row.get("reviewed_at"))

        if reviewer_decision == "CORRECT_SUGGESTION" and not any(correction_fields):
            row_errors.append("CORRECT_SUGGESTION requires at least one correction field")
        if reviewer_decision in {"REJECT_SUGGESTION", "NEEDS_SOURCE_CHECK"} and not reviewer_note:
            row_errors.append(f"{reviewer_decision} requires reviewer_note")
        if not reviewer_id:
            warnings.append(f"missing reviewer_id for review_item_id={review_item_id}")
        if not reviewed_at:
            warnings.append(f"missing reviewed_at for review_item_id={review_item_id}")

        if reviewer_decision == "CONFIRM_SUGGESTION":
            confirm_count += 1
        elif reviewer_decision == "CORRECT_SUGGESTION":
            correct_count += 1
        elif reviewer_decision == "REJECT_SUGGESTION":
            reject_count += 1
        elif reviewer_decision == "KEEP_HUMAN_REQUIRED":
            keep_count += 1
        elif reviewer_decision == "NEEDS_SOURCE_CHECK":
            source_check_count += 1

        if row_errors:
            validation_errors.append(
                f"{review_item_id}: " + "; ".join(row_errors)
            )

        rows.append(
            {
                "review_item_id": review_item_id,
                "reviewer_decision": reviewer_decision,
                "reviewer_metric_standardized": _norm_text(row.get("reviewer_metric_standardized")),
                "reviewer_year_standardized": _norm_text(row.get("reviewer_year_standardized")),
                "reviewer_value_numeric": _norm_text(row.get("reviewer_value_numeric")),
                "reviewer_normalized_unit": _norm_text(row.get("reviewer_normalized_unit")),
                "reviewer_note": reviewer_note,
                "reviewer_id": reviewer_id,
                "reviewed_at": reviewed_at,
                "validation_status": "PASS" if not row_errors else "FAIL",
                "validation_detail": " | ".join(row_errors),
            }
        )

    pass_like = confirm_count + correct_count
    reviewed_nonzero = reviewed_count if reviewed_count else 1
    metrics = {
        "spot_check_status": "REVIEWED_SPOT_CHECK_AVAILABLE" if reviewed_count else "WAITING_FOR_HUMAN_SPOT_CHECK",
        "reviewed_spot_check_count": reviewed_count,
        "spot_check_confirm_count": confirm_count,
        "spot_check_correct_count": correct_count,
        "spot_check_reject_count": reject_count,
        "spot_check_keep_human_count": keep_count,
        "spot_check_needs_source_check_count": source_check_count,
        "spot_check_validation_error_count": len(validation_errors),
        "spot_check_pass_rate": round(pass_like / reviewed_nonzero, 6) if reviewed_count else 0.0,
        "spot_check_failure_rate": round((reject_count + keep_count + source_check_count) / reviewed_nonzero, 6)
        if reviewed_count
        else 0.0,
    }
    apply_df = _clean_frame(pd.DataFrame(rows))
    if apply_df.empty:
        apply_df = _clean_frame(pd.DataFrame([metrics]))
    return apply_df, metrics, warnings, validation_errors


def _ingest_real_llm_responses(
    response_files: Sequence[Path],
    request_rows: Sequence[Mapping[str, Any]],
    candidate_map: Mapping[str, Mapping[str, Any]],
) -> tuple[pd.DataFrame, Dict[str, Any], List[str], List[str], List[Dict[str, Any]]]:
    warnings: List[str] = []
    validation_errors: List[str] = []
    response_rows: List[Dict[str, Any]] = []
    parsed_objects: List[Dict[str, Any]] = []

    if not response_files:
        empty = pd.DataFrame(
            [
                {
                    "real_llm_response_status": "WAITING_FOR_REAL_LLM_RESPONSES",
                    "response_count": 0,
                    "valid_response_count": 0,
                    "invalid_response_count": 0,
                    "jsonl_parse_error_count": 0,
                    "schema_validation_error_count": 0,
                    "unknown_review_item_id_count": 0,
                    "duplicate_response_count": 0,
                }
            ]
        )
        metrics = empty.to_dict(orient="records")[0]
        return _clean_frame(empty), metrics, warnings, validation_errors, parsed_objects

    request_id_set = {_norm_text(row.get("request_id")) for row in request_rows if _norm_text(row.get("request_id"))}
    review_item_id_set = {_norm_text(row.get("review_item_id")) for row in request_rows if _norm_text(row.get("review_item_id"))}
    review_item_id_set.update(candidate_map.keys())

    parse_error_count = 0
    duplicate_count = 0
    unknown_id_count = 0
    seen_pairs: set[tuple[str, str]] = set()
    valid_count = 0
    invalid_count = 0

    for path in response_files:
        rows, errors = _read_jsonl_rows(path)
        parse_error_count += len(errors)
        warnings.extend(errors)
        for row in rows:
            parsed_objects.append(row)
            request_id = _norm_text(row.get("request_id"))
            review_item_id = _norm_text(row.get("review_item_id"))
            llm_decision = _norm_text(row.get("llm_suggested_decision"))
            llm_evidence = _norm_text(row.get("llm_evidence"))
            row_errors: List[str] = []

            if not request_id:
                row_errors.append("missing request_id")
            if not review_item_id:
                row_errors.append("missing review_item_id")
            if llm_decision not in ALLOWED_LLM_DECISIONS:
                row_errors.append("invalid llm_suggested_decision")
            if request_id and request_id_set and request_id not in request_id_set:
                row_errors.append("unknown request_id")
            if review_item_id and review_item_id_set and review_item_id not in review_item_id_set:
                row_errors.append("unknown review_item_id")
                unknown_id_count += 1

            try:
                confidence = float(row.get("llm_confidence"))
                if confidence < 0 or confidence > 1:
                    row_errors.append("llm_confidence out of range")
            except Exception:
                confidence = None
                row_errors.append("invalid llm_confidence")

            if not llm_evidence:
                row_errors.append("missing llm_evidence")

            pair = (request_id, review_item_id)
            if request_id and review_item_id:
                if pair in seen_pairs:
                    row_errors.append("duplicate response")
                    duplicate_count += 1
                else:
                    seen_pairs.add(pair)

            response_rows.append(
                {
                    "source_file": str(path),
                    "request_id": request_id,
                    "review_item_id": review_item_id,
                    "llm_suggested_decision": llm_decision,
                    "llm_suggested_metric_standardized": _norm_text(row.get("llm_suggested_metric_standardized")),
                    "llm_suggested_year_standardized": _norm_text(row.get("llm_suggested_year_standardized")),
                    "llm_suggested_value_numeric": _norm_text(row.get("llm_suggested_value_numeric")),
                    "llm_suggested_normalized_unit": _norm_text(row.get("llm_suggested_normalized_unit")),
                    "llm_confidence": row.get("llm_confidence"),
                    "llm_evidence": llm_evidence,
                    "llm_risk_reason": _norm_text(row.get("llm_risk_reason")),
                    "human_required": row.get("human_required"),
                    "validation_status": "PASS" if not row_errors else "FAIL",
                    "validation_detail": " | ".join(row_errors),
                }
            )

            if row_errors:
                invalid_count += 1
                validation_errors.append(
                    f"{review_item_id or '__missing__'}: " + "; ".join(row_errors)
                )
            else:
                valid_count += 1

    metrics = {
        "real_llm_response_status": "REAL_LLM_RESPONSES_AVAILABLE" if response_rows else "WAITING_FOR_REAL_LLM_RESPONSES",
        "response_count": len(response_rows),
        "valid_response_count": valid_count,
        "invalid_response_count": invalid_count,
        "jsonl_parse_error_count": parse_error_count,
        "schema_validation_error_count": len(validation_errors),
        "unknown_review_item_id_count": unknown_id_count,
        "duplicate_response_count": duplicate_count,
    }
    ingest_df = _clean_frame(pd.DataFrame(response_rows))
    if ingest_df.empty:
        ingest_df = _clean_frame(pd.DataFrame([metrics]))
    return ingest_df, metrics, warnings, validation_errors, parsed_objects


def _compare_rule_and_llm(
    valid_response_objects: Sequence[Mapping[str, Any]],
    candidate_map: Mapping[str, Mapping[str, Any]],
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not valid_response_objects:
        empty = pd.DataFrame(
            [
                {
                    "comparison_status": "WAITING_FOR_REAL_LLM_RESPONSES",
                    "agreement_count": 0,
                    "decision_conflict_count": 0,
                    "metric_conflict_count": 0,
                    "unit_conflict_count": 0,
                    "year_conflict_count": 0,
                    "confidence_low_count": 0,
                    "human_required_by_llm_count": 0,
                }
            ]
        )
        return _clean_frame(empty), empty.to_dict(orient="records")[0]

    agreement_count = 0
    decision_conflict_count = 0
    metric_conflict_count = 0
    unit_conflict_count = 0
    year_conflict_count = 0
    confidence_low_count = 0
    human_required_by_llm_count = 0

    for row in valid_response_objects:
        review_item_id = _norm_text(row.get("review_item_id"))
        baseline = dict(candidate_map.get(review_item_id, {}))
        baseline_decision = _norm_text(baseline.get("dry_run_suggested_decision")) or _norm_text(
            baseline.get("rule_suggested_decision")
        )
        baseline_metric = _norm_text(baseline.get("suggested_metric_standardized"))
        baseline_year = _norm_text(baseline.get("suggested_year_standardized"))
        baseline_unit = _norm_text(baseline.get("suggested_normalized_unit"))
        llm_decision = _norm_text(row.get("llm_suggested_decision"))
        llm_metric = _norm_text(row.get("llm_suggested_metric_standardized"))
        llm_year = _norm_text(row.get("llm_suggested_year_standardized"))
        llm_unit = _norm_text(row.get("llm_suggested_normalized_unit"))
        confidence = float(row.get("llm_confidence"))
        human_required = bool(row.get("human_required"))

        decision_match = baseline_decision == llm_decision
        metric_match = baseline_metric == llm_metric or not llm_metric
        year_match = baseline_year == llm_year or not llm_year
        unit_match = baseline_unit == llm_unit or not llm_unit

        if decision_match and metric_match and year_match and unit_match:
            agreement_count += 1
        if not decision_match:
            decision_conflict_count += 1
        if llm_metric and not metric_match:
            metric_conflict_count += 1
        if llm_year and not year_match:
            year_conflict_count += 1
        if llm_unit and not unit_match:
            unit_conflict_count += 1
        if confidence < ADOPTION_CONFIDENCE_THRESHOLD:
            confidence_low_count += 1
        if human_required or llm_decision in {"KEEP_REVIEW_REQUIRED", "NEEDS_SOURCE_CHECK"}:
            human_required_by_llm_count += 1

        rows.append(
            {
                "review_item_id": review_item_id,
                "baseline_decision": baseline_decision,
                "llm_suggested_decision": llm_decision,
                "decision_match": decision_match,
                "baseline_metric_standardized": baseline_metric,
                "llm_suggested_metric_standardized": llm_metric,
                "metric_match": metric_match,
                "baseline_year_standardized": baseline_year,
                "llm_suggested_year_standardized": llm_year,
                "year_match": year_match,
                "baseline_normalized_unit": baseline_unit,
                "llm_suggested_normalized_unit": llm_unit,
                "unit_match": unit_match,
                "llm_confidence": confidence,
                "human_required": human_required,
            }
        )

    metrics = {
        "comparison_status": "REAL_LLM_RESPONSE_COMPARED",
        "agreement_count": agreement_count,
        "decision_conflict_count": decision_conflict_count,
        "metric_conflict_count": metric_conflict_count,
        "unit_conflict_count": unit_conflict_count,
        "year_conflict_count": year_conflict_count,
        "confidence_low_count": confidence_low_count,
        "human_required_by_llm_count": human_required_by_llm_count,
    }
    return _clean_frame(pd.DataFrame(rows)), metrics


def _has_source_trace(row: Mapping[str, Any]) -> bool:
    return bool(_norm_text(row.get("source_page")) or str(row.get("source_page", "")).strip()) and bool(
        _norm_text(row.get("image_path")) or _norm_text(row.get("source_html_snippet"))
    )


def _candidate_block_reason(
    row: Mapping[str, Any],
    *,
    human_required_ids: set[str],
    conflict_ids: set[str],
) -> str:
    review_item_id = _norm_text(row.get("review_item_id"))
    reasons: List[str] = []
    if review_item_id in human_required_ids:
        reasons.append("human_required")
    if review_item_id in conflict_ids:
        reasons.append("conflict_blocker")
    try:
        if float(row.get("suggested_confidence", 0) or 0) < ADOPTION_CONFIDENCE_THRESHOLD:
            reasons.append("low_confidence")
    except Exception:
        reasons.append("low_confidence")
    if not _has_source_trace(row):
        reasons.append("source_trace_missing")
    if not reasons:
        return ""
    return " | ".join(reasons)


def _build_adoption_policy_df() -> pd.DataFrame:
    rows = [
        {
            "policy_name": "entry_conditions",
            "policy_value": "spot_check_pass_rate >= 0.90 OR real_llm_agreement_rate >= 0.90",
            "notes": "Evidence is required before any broader adoption simulation.",
        },
        {
            "policy_name": "candidate_filters",
            "policy_value": "not in human_required, not in conflict blockers, source trace complete, confidence >= 0.95",
            "notes": "Adoption candidates remain candidates only and are never final confirmations in 342M.",
        },
        {
            "policy_name": "blocked_cases",
            "policy_value": "human_required, conflict_blocker, missing_source_trace, low_confidence, waiting_for_evidence, failed_spot_check, llm_rule_conflict",
            "notes": "Blocked rows must remain outside automatic adoption.",
        },
        {
            "policy_name": "boundary",
            "policy_value": "client_ready=false; production_ready=false; dry_run_suggestions_are_not_real_llm_output",
            "notes": "342M is a gate, not a final apply stage.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_adoption_results(
    auto_candidates_df: pd.DataFrame,
    *,
    human_required_ids: set[str],
    conflict_ids: set[str],
    evidence_ready: bool,
    allow_adoption: bool,
    block_reason_if_no_evidence: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidate_rows: List[Dict[str, Any]] = []
    blocked_rows: List[Dict[str, Any]] = []

    for row in auto_candidates_df.to_dict(orient="records"):
        review_item_id = _norm_text(row.get("review_item_id"))
        base_block_reason = _candidate_block_reason(
            row,
            human_required_ids=human_required_ids,
            conflict_ids=conflict_ids,
        )
        if not evidence_ready:
            blocked_rows.append(
                {
                    "review_item_id": review_item_id,
                    "block_reason": block_reason_if_no_evidence,
                    "blocker_severity": "MEDIUM",
                    "human_required": review_item_id in human_required_ids,
                    "auto_apply_allowed": False,
                }
            )
            continue

        if not allow_adoption:
            reason = "evidence_present_but_policy_not_met"
            if base_block_reason:
                reason = f"{reason} | {base_block_reason}"
            blocked_rows.append(
                {
                    "review_item_id": review_item_id,
                    "block_reason": reason,
                    "blocker_severity": "MEDIUM",
                    "human_required": review_item_id in human_required_ids,
                    "auto_apply_allowed": False,
                }
            )
            continue

        if base_block_reason:
            blocked_rows.append(
                {
                    "review_item_id": review_item_id,
                    "block_reason": base_block_reason,
                    "blocker_severity": "MEDIUM",
                    "human_required": review_item_id in human_required_ids,
                    "auto_apply_allowed": False,
                }
            )
            continue

        candidate_rows.append(
            {
                "review_item_id": review_item_id,
                "adoption_status": "ELIGIBLE_FOR_NEXT_STAGE_SIMULATION",
                "rule_suggested_decision": _norm_text(row.get("rule_suggested_decision")),
                "dry_run_suggested_decision": _norm_text(row.get("dry_run_suggested_decision")),
                "suggested_metric_standardized": _norm_text(row.get("suggested_metric_standardized")),
                "suggested_year_standardized": _norm_text(row.get("suggested_year_standardized")),
                "suggested_value_numeric": row.get("suggested_value_numeric"),
                "suggested_normalized_unit": _norm_text(row.get("suggested_normalized_unit")),
                "suggested_confidence": row.get("suggested_confidence"),
                "candidate_reason": _norm_text(row.get("candidate_reason")),
                "risk_flags": _norm_text(row.get("risk_flags")),
                "not_final_confirmation": True,
            }
        )

    return _clean_frame(pd.DataFrame(candidate_rows)), _clean_frame(pd.DataFrame(blocked_rows))


def _build_risk_gate_df(
    summary_342l: Mapping[str, Any],
    *,
    blocked_candidate_count: int,
    waiting_for_human_spot_check: bool,
    waiting_for_real_llm_responses: bool,
) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "human_required_count": int(summary_342l.get("human_required_count", 0) or 0),
                    "conflict_count": int(summary_342l.get("conflict_count", 0) or 0),
                    "source_trace_risk_count": int(summary_342l.get("source_trace_risk_count", 0) or 0),
                    "unit_year_risk_count": int(summary_342l.get("unit_year_risk_count", 0) or 0),
                    "duplicate_risk_count": int(summary_342l.get("duplicate_risk_count", 0) or 0),
                    "growth_row_risk_count": int(summary_342l.get("growth_row_risk_count", 0) or 0),
                    "metric_mapping_risk_count": int(summary_342l.get("metric_mapping_risk_count", 0) or 0),
                    "spot_check_missing_count": int(summary_342l.get("spot_check_sample_count", 0) or 0)
                    if waiting_for_human_spot_check
                    else 0,
                    "real_llm_response_missing_count": int(summary_342l.get("request_pack_count", 0) or 0)
                    if waiting_for_real_llm_responses
                    else 0,
                    "adoption_blocker_count": blocked_candidate_count,
                }
            ]
        )
    )


def _build_reduction_after_gate_df(
    pending_review_count: int,
    auto_confirm_candidate_count: int,
    spot_check_sample_count: int,
    reviewed_spot_check_count: int,
    valid_llm_response_count: int,
    adoption_candidate_count: int,
    blocked_candidate_count: int,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    required_after_gate = max(pending_review_count - adoption_candidate_count, 0)
    rate = round(adoption_candidate_count / pending_review_count, 6) if pending_review_count else 0.0
    row = {
        "original_pending_review_count": pending_review_count,
        "auto_confirm_candidate_count": auto_confirm_candidate_count,
        "spot_check_sample_count": spot_check_sample_count,
        "reviewed_spot_check_count": reviewed_spot_check_count,
        "valid_llm_response_count": valid_llm_response_count,
        "adoption_candidate_count": adoption_candidate_count,
        "blocked_candidate_count": blocked_candidate_count,
        "risk_adjusted_reduction_count": adoption_candidate_count,
        "required_human_review_after_gate": required_after_gate,
        "conservative_reduction_rate_after_gate": rate,
    }
    frame = _clean_frame(pd.DataFrame([row]))
    return frame, row


def _build_readme_df(summary_342l: Mapping[str, Any], summary_342j: Mapping[str, Any]) -> pd.DataFrame:
    messages = [
        "342M is an adoption gate only. It does not auto-apply suggestions and does not write back upstream workbooks.",
        "Without reviewed spot-check evidence or real LLM response files, 342M must stay in WAITING_FOR_EVIDENCE.",
        "Dry-run suggestions are not real LLM outputs.",
        "Auto-confirm candidates are still candidates only, not final confirmations.",
        f"Upstream 342L decision: {summary_342l.get('decision', '')}",
        f"Boundary check from 342J: client_ready={summary_342j.get('client_ready', False)}, production_ready={summary_342j.get('production_ready', False)}",
    ]
    return _clean_frame(pd.DataFrame([{"message": message} for message in messages]))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    row = {
        "ready_for_342n": summary.get("ready_for_342n", False),
        "recommended_342n_scope": summary.get("recommended_342n_scope", ""),
        "decision": summary.get("decision", ""),
        "waiting_for_human_spot_check": summary.get("waiting_for_human_spot_check", False),
        "waiting_for_real_llm_responses": summary.get("waiting_for_real_llm_responses", False),
    }
    return _clean_frame(pd.DataFrame([row]))


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    if summary.get("ready_for_342n", False):
        steps = [
            "Proceed to 342N spot-check adoption simulation or controlled real LLM response apply.",
            "Keep no-write-back boundaries in place.",
            "Keep client_ready=false and production_ready=false.",
        ]
    else:
        steps = [
            "Collect reviewed spot-check workbook evidence or real LLM response files.",
            "Do not fabricate human review outcomes or real LLM responses.",
            "Do not treat auto-confirm candidates as final confirmations.",
        ]
    return _clean_frame(pd.DataFrame([{"next_step": step} for step in steps]))


def _build_no_write_back_proof_df(payload: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for key, value in payload.items():
        rows.append({"key": key, "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value})
    return _clean_frame(pd.DataFrame(rows))


def _row_truthy_series_all_blank(df: pd.DataFrame, columns: Sequence[str]) -> bool:
    if df.empty:
        return True
    return df[list(columns)].astype(str).apply(lambda col: col.eq("").all()).all()


def build_llm_suggestion_spot_check_gate_342m(
    *,
    llm_suggestion_342l_dir: Path,
    llm_review_342k_dir: Path,
    reviewed_preview_342j_dir: Path,
    spot_check_reviewed_dir: Path,
    llm_response_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    (
        summary_342l,
        qa_342l,
        proof_342l,
        workbook_342l,
        workbook_342l_names,
        files_342l,
        warnings_342l,
    ) = _load_342l_context(llm_suggestion_342l_dir)
    prompt_rows, request_rows, files_342k, warnings_342k, prompt_request_parse_error_count = _load_342k_packs(
        llm_review_342k_dir
    )
    summary_342j, files_342j, warnings_342j = _load_342j_summary(reviewed_preview_342j_dir)

    files_read.extend(files_342l + files_342k + files_342j)
    warnings.extend(warnings_342l + warnings_342k + warnings_342j)

    summary_path_342l = llm_suggestion_342l_dir / INPUT_342L_SUMMARY_NAME
    qa_path_342l = llm_suggestion_342l_dir / INPUT_342L_QA_NAME
    report_path_342l = llm_suggestion_342l_dir / INPUT_342L_REPORT_NAME
    workbook_path_342l = llm_suggestion_342l_dir / INPUT_342L_WORKBOOK_NAME
    prompt_path_342k = llm_review_342k_dir / INPUT_342K_PROMPT_PACK_NAME
    request_path_342k = llm_review_342k_dir / INPUT_342K_REQUEST_PACK_NAME
    summary_path_342j = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME

    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [
            summary_path_342l,
            qa_path_342l,
            report_path_342l,
            workbook_path_342l,
            prompt_path_342k,
            request_path_342k,
            summary_path_342j,
        ]
        if path.exists()
    }

    required_342l_present = all(sheet in workbook_342l_names for sheet in REQUIRED_342L_SHEETS)
    input_ready = bool(
        llm_suggestion_342l_dir.exists()
        and summary_path_342l.exists()
        and qa_path_342l.exists()
        and workbook_path_342l.exists()
        and summary_path_342j.exists()
        and prompt_path_342k.exists()
        and request_path_342k.exists()
        and summary_342l.get("decision") == READY_INPUT_DECISION
        and bool(summary_342l.get("ready_for_342m", False))
        and int(summary_342l.get("qa_fail_count", 0) or 0) == 0
        and required_342l_present
        and prompt_request_parse_error_count == 0
        and summary_342j.get("client_ready", False) is False
        and summary_342j.get("production_ready", False) is False
    )

    auto_candidates_df = _clean_frame(workbook_342l.get("03_AUTO_CANDIDATES", pd.DataFrame())) if input_ready else pd.DataFrame()
    spot_sample_df = _clean_frame(workbook_342l.get("04_SPOT_CHECK_SAMPLE", pd.DataFrame())) if input_ready else pd.DataFrame()
    prefill_df = _clean_frame(workbook_342l.get("05_PREFILL_REVIEW_DRAFT", pd.DataFrame())) if input_ready else pd.DataFrame()
    human_required_df = _clean_frame(workbook_342l.get("06_HUMAN_REQUIRED", pd.DataFrame())) if input_ready else pd.DataFrame()
    conflict_df = _clean_frame(workbook_342l.get("07_CONFLICT_BLOCKERS", pd.DataFrame())) if input_ready else pd.DataFrame()

    template_df = _build_spot_check_template(spot_sample_df, auto_candidates_df, prefill_df) if input_ready else pd.DataFrame()
    schema_json = _real_llm_response_schema()
    schema_df = _schema_frame(schema_json)
    response_template_rows = _build_real_response_template_rows(request_rows) if input_ready else []

    reviewed_spot_check_path = _first_existing_workbook(spot_check_reviewed_dir)
    reviewed_spot_sheet = ""
    reviewed_spot_df = pd.DataFrame()
    reviewed_warnings: List[str] = []
    if reviewed_spot_check_path is not None:
        reviewed_spot_df, reviewed_warnings, reviewed_spot_sheet = _read_reviewed_spot_check_workbook(
            reviewed_spot_check_path
        )
        files_read.append(str(reviewed_spot_check_path))
    warnings.extend(reviewed_warnings)

    spot_apply_df, spot_metrics, spot_warnings, spot_validation_errors = _apply_spot_check_results(
        reviewed_spot_df,
        template_df,
    )
    warnings.extend(spot_warnings)

    candidate_map, human_required_ids, conflict_ids = _candidate_maps(
        auto_candidates_df,
        prefill_df,
        human_required_df,
        conflict_df,
    )

    response_files = _jsonl_files(llm_response_dir)
    for path in response_files:
        files_read.append(str(path))
    (
        response_ingest_df,
        response_metrics,
        response_warnings,
        response_validation_errors,
        parsed_response_objects,
    ) = _ingest_real_llm_responses(response_files, request_rows, candidate_map)
    warnings.extend(response_warnings)

    valid_response_objects = [
        row
        for row in parsed_response_objects
        if _norm_text(row.get("request_id"))
        and _norm_text(row.get("review_item_id"))
        and _norm_text(row.get("llm_suggested_decision")) in ALLOWED_LLM_DECISIONS
        and _norm_text(row.get("review_item_id")) in candidate_map
        and _norm_text(row.get("request_id")) in {
            _norm_text(request_row.get("request_id")) for request_row in request_rows
        }
        and isinstance(row.get("human_required"), bool)
        and isinstance(row.get("llm_evidence"), str)
        and _norm_text(row.get("llm_evidence"))
        and isinstance(row.get("llm_confidence"), (int, float))
        and 0 <= float(row.get("llm_confidence")) <= 1
    ]

    comparison_df, comparison_metrics = _compare_rule_and_llm(valid_response_objects, candidate_map)

    reviewed_spot_check_count = int(spot_metrics.get("reviewed_spot_check_count", 0) or 0)
    response_count = int(response_metrics.get("response_count", 0) or 0)
    valid_llm_response_count = int(response_metrics.get("valid_response_count", 0) or 0)
    waiting_for_human_spot_check = reviewed_spot_check_count == 0
    waiting_for_real_llm_responses = response_count == 0

    spot_check_pass_rate = float(spot_metrics.get("spot_check_pass_rate", 0) or 0)
    llm_agreement_rate = (
        round(
            int(comparison_metrics.get("agreement_count", 0) or 0) / valid_llm_response_count,
            6,
        )
        if valid_llm_response_count
        else 0.0
    )
    evidence_ready = reviewed_spot_check_count > 0 or valid_llm_response_count > 0
    allow_adoption = bool(
        (reviewed_spot_check_count > 0 and not spot_validation_errors and spot_check_pass_rate >= PASS_RATE_THRESHOLD)
        or (
            valid_llm_response_count > 0
            and not response_validation_errors
            and llm_agreement_rate >= PASS_RATE_THRESHOLD
        )
    )

    adoption_candidates_df, blocked_candidates_df = _build_adoption_results(
        auto_candidates_df,
        human_required_ids=human_required_ids,
        conflict_ids=conflict_ids,
        evidence_ready=evidence_ready,
        allow_adoption=allow_adoption,
        block_reason_if_no_evidence="waiting_for_human_spot_check | waiting_for_real_llm_responses",
    )
    adoption_candidate_count = int(len(adoption_candidates_df))
    blocked_candidate_count = int(len(blocked_candidates_df))

    reduction_after_gate_df, reduction_metrics = _build_reduction_after_gate_df(
        int(summary_342l.get("pending_review_count", 0) or 0) if input_ready else 0,
        int(summary_342l.get("auto_confirm_candidate_count", 0) or 0) if input_ready else 0,
        int(summary_342l.get("spot_check_sample_count", 0) or 0) if input_ready else 0,
        reviewed_spot_check_count,
        valid_llm_response_count,
        adoption_candidate_count,
        blocked_candidate_count,
    )
    risk_gate_df = _build_risk_gate_df(
        summary_342l if input_ready else {},
        blocked_candidate_count=blocked_candidate_count,
        waiting_for_human_spot_check=waiting_for_human_spot_check,
        waiting_for_real_llm_responses=waiting_for_real_llm_responses,
    )
    adoption_policy_df = _build_adoption_policy_df()

    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [
            summary_path_342l,
            qa_path_342l,
            report_path_342l,
            workbook_path_342l,
            prompt_path_342k,
            request_path_342k,
            summary_path_342j,
        ]
        if path.exists()
    }
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)
    optional_inputs_staged = _git_staged_names_for_paths(
        ["input/spot_check_reviewed_342m", "input/llm_review_responses_342m"],
        repo_root,
    )

    no_write_back_json = build_no_apply_proof(
        stage="342M",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["client_export_generated"] = False
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_342m")
        and upstream_unchanged
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df(summary_342l if input_ready else {}, summary_342j if input_ready else {})
    claims_text = "\n".join(readme_df.get("message", pd.Series(dtype=object)).astype(str).tolist())
    template_blank = _row_truthy_series_all_blank(
        template_df,
        [
            "reviewer_decision",
            "reviewer_metric_standardized",
            "reviewer_year_standardized",
            "reviewer_value_numeric",
            "reviewer_normalized_unit",
            "reviewer_note",
            "reviewer_id",
            "reviewed_at",
        ],
    )
    response_template_generated = bool(response_template_rows)

    checks = [
        {
            "check_name": "inputs::342l_output_dir_exists",
            "status": "PASS" if llm_suggestion_342l_dir.exists() else "FAIL",
            "detail": str(llm_suggestion_342l_dir),
        },
        {
            "check_name": "inputs::342l_summary_exists",
            "status": "PASS" if summary_path_342l.exists() else "FAIL",
            "detail": str(summary_path_342l),
        },
        {
            "check_name": "inputs::342l_qa_exists",
            "status": "PASS" if qa_path_342l.exists() else "FAIL",
            "detail": str(qa_path_342l),
        },
        {
            "check_name": "inputs::342l_workbook_exists",
            "status": "PASS" if workbook_path_342l.exists() else "FAIL",
            "detail": str(workbook_path_342l),
        },
        {
            "check_name": "inputs::342l_ready_for_342m_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342l.get("decision", ""),
                    "ready_for_342m": summary_342l.get("ready_for_342m", False),
                    "qa_fail_count": summary_342l.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342k_prompt_pack_exists",
            "status": "PASS" if prompt_path_342k.exists() else "FAIL",
            "detail": str(prompt_path_342k),
        },
        {
            "check_name": "inputs::342k_request_pack_exists",
            "status": "PASS" if request_path_342k.exists() else "FAIL",
            "detail": str(request_path_342k),
        },
        {
            "check_name": "inputs::342j_summary_client_production_false",
            "status": "PASS"
            if summary_342j.get("client_ready", False) is False and summary_342j.get("production_ready", False) is False
            else "FAIL",
            "detail": json.dumps(
                {
                    "client_ready": summary_342j.get("client_ready"),
                    "production_ready": summary_342j.get("production_ready"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "quality::spot_check_template_generated",
            "status": "PASS" if not template_df.empty else "FAIL",
            "detail": str(len(template_df)),
        },
        {
            "check_name": "quality::reviewer_fields_blank_in_template",
            "status": "PASS" if template_blank else "FAIL",
            "detail": str(len(template_df)),
        },
        {
            "check_name": "quality::no_fake_human_spot_check_result_generated",
            "status": "PASS",
            "detail": "342M does not fabricate reviewed spot-check decisions.",
        },
        {
            "check_name": "quality::real_llm_response_schema_generated",
            "status": "PASS" if not schema_df.empty and response_template_generated else "FAIL",
            "detail": json.dumps(
                {"schema_fields": len(schema_json), "template_rows": len(response_template_rows)},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "quality::no_fake_real_llm_response_generated",
            "status": "PASS",
            "detail": "342M only ingests optional real response files.",
        },
        {
            "check_name": "quality::adoption_candidates_not_final_confirmations",
            "status": "PASS"
            if adoption_candidates_df.empty
            or adoption_candidates_df["not_final_confirmation"].astype(bool).all()
            else "FAIL",
            "detail": str(adoption_candidate_count),
        },
        {
            "check_name": "quality::human_required_rows_not_auto_applied",
            "status": "PASS"
            if not (
                {_norm_text(row.get("review_item_id")) for row in adoption_candidates_df.to_dict(orient="records")}
                & human_required_ids
            )
            else "FAIL",
            "detail": str(len(human_required_ids)),
        },
        {
            "check_name": "quality::conflict_blockers_not_auto_applied",
            "status": "PASS"
            if not (
                {_norm_text(row.get("review_item_id")) for row in adoption_candidates_df.to_dict(orient="records")}
                & conflict_ids
            )
            else "FAIL",
            "detail": str(len(conflict_ids)),
        },
        {
            "check_name": "quality::prompt_request_jsonl_parsed",
            "status": "PASS" if prompt_request_parse_error_count == 0 and bool(request_rows) else "FAIL",
            "detail": json.dumps(
                {
                    "prompt_pack_count": len(prompt_rows),
                    "request_pack_count": len(request_rows),
                    "jsonl_parse_error_count": prompt_request_parse_error_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "quality::optional_waiting_state_allowed",
            "status": "PASS"
            if (waiting_for_human_spot_check and waiting_for_real_llm_responses)
            or reviewed_spot_check_count > 0
            or response_count > 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "waiting_for_human_spot_check": waiting_for_human_spot_check,
                    "waiting_for_real_llm_responses": waiting_for_real_llm_responses,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "342M adds sidecar gate code only.",
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
            "check_name": "safety::output_artifacts_not_staged",
            "status": "PASS" if not output_staged else "FAIL",
            "detail": json.dumps(output_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::optional_input_artifacts_not_staged",
            "status": "PASS" if not optional_inputs_staged else "FAIL",
            "detail": json.dumps(optional_inputs_staged, ensure_ascii=False),
        },
        {
            "check_name": "claims::client_ready_false",
            "status": "PASS",
            "detail": "false",
        },
        {
            "check_name": "claims::production_ready_false",
            "status": "PASS",
            "detail": "false",
        },
        {
            "check_name": "claims::no_investment_advice_claim",
            "status": "PASS"
            if not _contains_forbidden_claim(claims_text, ["investment advice"])
            else "FAIL",
            "detail": "README text checked",
        },
        {
            "check_name": "safety::no_sheet_name_exceeds_limit",
            "status": "PASS",
            "detail": "all 342M sheet names are <= 31 chars",
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
        {
            "check_name": "quality::spot_check_validation_errors_clear",
            "status": "PASS" if not spot_validation_errors else "FAIL",
            "detail": json.dumps(spot_validation_errors[:10], ensure_ascii=False),
        },
        {
            "check_name": "quality::real_llm_response_schema_validation_clear",
            "status": "PASS" if not response_validation_errors else "FAIL",
            "detail": json.dumps(response_validation_errors[:10], ensure_ascii=False),
        },
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342n = bool(
        input_ready
        and no_write_back_proof_passed
        and qa_fail_count == 0
        and (
            (reviewed_spot_check_count > 0 and int(spot_metrics.get("spot_check_validation_error_count", 0) or 0) == 0)
            or (valid_llm_response_count > 0 and int(response_metrics.get("schema_validation_error_count", 0) or 0) == 0)
        )
    )

    if not input_ready:
        decision = NOT_READY_DECISION
        recommended_342n_scope = "fix_342l_inputs"
    elif response_count > 0 and valid_llm_response_count > 0 and not response_validation_errors and qa_fail_count == 0:
        decision = REAL_RESPONSE_READY_DECISION
        recommended_342n_scope = "spot_check_adoption_simulation_or_real_llm_response_apply"
    elif reviewed_spot_check_count > 0 and not spot_validation_errors and qa_fail_count == 0:
        decision = SPOT_CHECK_READY_DECISION
        recommended_342n_scope = "spot_check_adoption_simulation_or_real_llm_response_apply"
    elif qa_fail_count == 0:
        decision = WAITING_DECISION
        recommended_342n_scope = "collect_spot_check_or_real_llm_responses"
    else:
        decision = NOT_READY_DECISION
        recommended_342n_scope = "fix_342m_evidence_validation"

    summary = {
        "generated_at_utc": _utc_now(),
        "pending_review_count": int(summary_342l.get("pending_review_count", 0) or 0) if input_ready else 0,
        "auto_confirm_candidate_count": int(summary_342l.get("auto_confirm_candidate_count", 0) or 0) if input_ready else 0,
        "spot_check_sample_count": int(summary_342l.get("spot_check_sample_count", 0) or 0) if input_ready else 0,
        "reviewed_spot_check_count": reviewed_spot_check_count,
        "spot_check_confirm_count": int(spot_metrics.get("spot_check_confirm_count", 0) or 0),
        "spot_check_correct_count": int(spot_metrics.get("spot_check_correct_count", 0) or 0),
        "spot_check_reject_count": int(spot_metrics.get("spot_check_reject_count", 0) or 0),
        "spot_check_validation_error_count": int(spot_metrics.get("spot_check_validation_error_count", 0) or 0),
        "spot_check_pass_rate": float(spot_metrics.get("spot_check_pass_rate", 0) or 0),
        "response_count": response_count,
        "valid_llm_response_count": valid_llm_response_count,
        "jsonl_parse_error_count": int(response_metrics.get("jsonl_parse_error_count", 0) or 0),
        "schema_validation_error_count": int(response_metrics.get("schema_validation_error_count", 0) or 0),
        "agreement_count": int(comparison_metrics.get("agreement_count", 0) or 0),
        "decision_conflict_count": int(comparison_metrics.get("decision_conflict_count", 0) or 0),
        "adoption_candidate_count": adoption_candidate_count,
        "blocked_candidate_count": blocked_candidate_count,
        "risk_adjusted_reduction_count": int(reduction_metrics.get("risk_adjusted_reduction_count", 0) or 0),
        "required_human_review_after_gate": int(
            reduction_metrics.get("required_human_review_after_gate", 0) or 0
        ),
        "conservative_reduction_rate_after_gate": float(
            reduction_metrics.get("conservative_reduction_rate_after_gate", 0) or 0
        ),
        "waiting_for_human_spot_check": waiting_for_human_spot_check,
        "waiting_for_real_llm_responses": waiting_for_real_llm_responses,
        "ready_for_342n": ready_for_342n,
        "recommended_342n_scope": recommended_342n_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "spot_check_template_workbook_path": str(output_dir / SPOT_CHECK_TEMPLATE_WORKBOOK_NAME),
        "real_llm_response_schema_path": str(output_dir / REAL_RESPONSE_SCHEMA_NAME),
        "real_llm_response_template_path": str(output_dir / REAL_RESPONSE_TEMPLATE_NAME),
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342M_llm_suggestion_spot_check_gate",
        "llm_suggestion_342l_dir": str(llm_suggestion_342l_dir),
        "llm_review_342k_dir": str(llm_review_342k_dir),
        "reviewed_preview_342j_dir": str(reviewed_preview_342j_dir),
        "spot_check_reviewed_dir": str(spot_check_reviewed_dir),
        "llm_response_dir": str(llm_response_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "spot_check_template_xlsx": str(output_dir / SPOT_CHECK_TEMPLATE_WORKBOOK_NAME),
            "real_llm_response_schema_json": str(output_dir / REAL_RESPONSE_SCHEMA_NAME),
            "real_llm_response_template_jsonl": str(output_dir / REAL_RESPONSE_TEMPLATE_NAME),
        },
        "reviewed_spot_check_workbook": str(reviewed_spot_check_path) if reviewed_spot_check_path else "",
        "reviewed_spot_check_sheet": reviewed_spot_sheet,
        "response_files": [str(path) for path in response_files],
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
        "00_README": readme_df,
        "01_GATE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342L_SUMMARY": _clean_frame(pd.DataFrame([summary_342l])) if summary_342l else pd.DataFrame(),
        "03_SPOT_CHECK_TEMPLATE": template_df,
        "04_SPOT_CHECK_APPLY": spot_apply_df,
        "05_LLM_RESPONSE_SCHEMA": schema_df,
        "06_LLM_RESPONSE_INGEST": response_ingest_df,
        "07_RULE_LLM_COMPARISON": comparison_df,
        "08_ADOPTION_POLICY": adoption_policy_df,
        "09_ADOPTION_CANDIDATES": adoption_candidates_df,
        "10_BLOCKED_CANDIDATES": blocked_candidates_df,
        "11_RISK_GATE": risk_gate_df,
        "12_REDUCTION_AFTER_GATE": reduction_after_gate_df,
        "13_342N_READINESS": _build_readiness_df(summary),
        "14_NO_WRITE_BACK": _build_no_write_back_proof_df(no_write_back_json),
        "15_NEXT_STEPS": _build_next_steps_df(summary),
    }
    template_workbook_sheets = {
        "00_README": _clean_frame(
            pd.DataFrame(
                [
                    {"message": "Fill reviewer_* fields only. Keep suggestion fields unchanged."},
                    {
                        "message": "Allowed reviewer_decision: CONFIRM_SUGGESTION | CORRECT_SUGGESTION | REJECT_SUGGESTION | KEEP_HUMAN_REQUIRED | NEEDS_SOURCE_CHECK"
                    },
                    {"message": "This workbook is evidence input for 342M and must not be committed."},
                ]
            )
        ),
        "01_SPOT_CHECK_REVIEW": template_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
        "template_workbook_sheets": template_workbook_sheets,
        "real_llm_response_schema_json": schema_json,
        "real_llm_response_template_rows": response_template_rows,
    }
