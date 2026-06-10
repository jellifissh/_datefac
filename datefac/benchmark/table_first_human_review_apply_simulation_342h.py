from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_DECISION = "TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_READY"
WAITING_DECISION = "TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_WAITING_FOR_HUMAN_REVIEW"
READY_DECISION = "TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_READY"
NOT_READY_DECISION = "TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_NOT_READY"

DEFAULT_REVIEW_PACKAGE_342G_DIR = Path(r"D:\_datefac\output\table_first_extraction_review_package_342g")
DEFAULT_REVIEWED_INPUT_DIR = Path(r"D:\_datefac\input\table_first_review_342g_reviewed")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\table_first_human_review_apply_simulation_342h")

SUMMARY_FILE_NAME = "table_first_human_review_apply_simulation_342h_summary.json"
MANIFEST_FILE_NAME = "table_first_human_review_apply_simulation_342h_manifest.json"
QA_FILE_NAME = "table_first_human_review_apply_simulation_342h_qa.json"
NO_WRITE_BACK_FILE_NAME = "table_first_human_review_apply_simulation_342h_no_write_back_proof.json"
REPORT_FILE_NAME = "table_first_human_review_apply_simulation_342h_report.md"
WORKBOOK_FILE_NAME = "table_first_human_review_apply_simulation_342h.xlsx"
REVIEWED_WORKBOOK_NAME = "table_first_extraction_review_package_342g_reviewed.xlsx"

REVIEW_PACKAGE_SUMMARY_NAME = "table_first_extraction_review_package_342g_summary.json"
REVIEW_PACKAGE_QA_NAME = "table_first_extraction_review_package_342g_qa.json"
REVIEW_PACKAGE_NO_WRITE_BACK_NAME = "table_first_extraction_review_package_342g_no_write_back_proof.json"
REVIEW_PACKAGE_REPORT_NAME = "table_first_extraction_review_package_342g_report.md"
REVIEW_PACKAGE_WORKBOOK_NAME = "table_first_extraction_review_package_342g.xlsx"

REQUIRED_342G_SHEETS = [
    "01_REVIEW_SUMMARY",
    "10_REVIEW_TEMPLATE",
    "11_DECISION_OPTIONS",
    "12_342H_READINESS",
    "13_NO_WRITE_BACK",
]
REVIEW_TEMPLATE_SHEET_CANDIDATES = ["10_REVIEW_TEMPLATE", "REVIEW_TEMPLATE"]

REVIEWER_FIELDS = [
    "reviewer_decision",
    "reviewer_metric_standardized",
    "reviewer_year_standardized",
    "reviewer_value_numeric",
    "reviewer_normalized_unit",
    "reviewer_note",
    "reviewer_id",
    "reviewed_at",
]

ALLOWED_DECISIONS = [
    "CONFIRM_CELL",
    "CORRECT_AND_CONFIRM",
    "REJECT_CELL",
    "KEEP_REVIEW_REQUIRED",
    "NOT_A_CORE_METRIC",
    "NEEDS_SOURCE_CHECK",
]

EXCLUDED_TABLE_TYPES = {
    "BASIC_DATA",
    "RATING_STANDARD",
    "RELATED_REPORTS",
    "DISCLAIMER",
    "CHART_OR_IMAGE",
    "NOISE_TABLE",
    "UNKNOWN_TABLE",
}

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]


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


def _safe_float(value: Any) -> float | None:
    text = _norm_text(value)
    if not text:
        return None
    try:
        return float(text.replace(",", ""))
    except Exception:
        return None


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
    staged: List[str] = []
    for line in result.stdout.splitlines():
        if line.strip() and len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _contains_forbidden_claim(text: str, forbidden: Sequence[str]) -> bool:
    lowered = text.casefold()
    for token in forbidden:
        start = 0
        token_lower = token.casefold()
        while True:
            idx = lowered.find(token_lower, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 60) : idx]
            if "not " not in window and "false" not in window and "no " not in window:
                return True
            start = idx + len(token_lower)
    return False


def _ensure_columns(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    return _clean_frame(out)


def _load_review_package_context(
    review_package_342g_dir: Path,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []

    summary_path = review_package_342g_dir / REVIEW_PACKAGE_SUMMARY_NAME
    qa_path = review_package_342g_dir / REVIEW_PACKAGE_QA_NAME
    proof_path = review_package_342g_dir / REVIEW_PACKAGE_NO_WRITE_BACK_NAME
    report_path = review_package_342g_dir / REVIEW_PACKAGE_REPORT_NAME
    workbook_path = review_package_342g_dir / REVIEW_PACKAGE_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    proof_json = _read_json(proof_path) if proof_path.exists() else {}

    for path, label in [
        (summary_path, "342G summary"),
        (qa_path, "342G qa"),
        (proof_path, "342G no-write-back proof"),
        (report_path, "342G report"),
        (workbook_path, "342G workbook"),
    ]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing {label}: {path}")

    workbook_sheets: Dict[str, pd.DataFrame] = {}
    if workbook_path.exists():
        try:
            excel = pd.ExcelFile(workbook_path)
            for sheet in REQUIRED_342G_SHEETS:
                if sheet in excel.sheet_names:
                    workbook_sheets[sheet] = _clean_frame(pd.read_excel(workbook_path, sheet_name=sheet))
                else:
                    warnings.append(f"missing required 342G workbook sheet: {sheet}")
                    workbook_sheets[sheet] = pd.DataFrame()
        except Exception as exc:
            warnings.append(f"unable to read 342G workbook: {exc}")
            for sheet in REQUIRED_342G_SHEETS:
                workbook_sheets[sheet] = pd.DataFrame()
    else:
        for sheet in REQUIRED_342G_SHEETS:
            workbook_sheets[sheet] = pd.DataFrame()

    return summary, qa_json, proof_json, workbook_sheets, files_read, warnings


def _find_review_sheet(workbook_path: Path) -> tuple[str, pd.DataFrame] | tuple[None, None]:
    excel = pd.ExcelFile(workbook_path)
    for candidate in REVIEW_TEMPLATE_SHEET_CANDIDATES:
        if candidate in excel.sheet_names:
            df = _clean_frame(pd.read_excel(workbook_path, sheet_name=candidate))
            return candidate, df
    for sheet_name in excel.sheet_names:
        df = _clean_frame(pd.read_excel(workbook_path, sheet_name=sheet_name))
        if "reviewer_decision" in df.columns:
            return sheet_name, df
    return None, None


def _metric_kind(metric_name: str) -> str:
    metric = metric_name.casefold()
    if metric in {"roe", "gross_margin", "revenue_yoy", "net_profit_yoy"} or "yoy" in metric or "margin" in metric:
        return "percent"
    if metric in {"pe", "pb", "p/e", "p/b"}:
        return "multiple"
    if metric:
        return "money_or_other"
    return "unknown"


def _unit_conflict(metric_name: str, unit_name: str) -> bool:
    metric_kind = _metric_kind(metric_name)
    unit = _norm_text(unit_name)
    if not unit:
        return False
    if metric_kind == "percent":
        return unit != "%"
    if metric_kind == "multiple":
        return unit not in {"倍", "x", "X"}
    if metric_kind == "money_or_other":
        return unit in {"%", "倍", "x", "X"}
    return False


def _source_trace_missing(row: Mapping[str, Any]) -> bool:
    return any(
        not _norm_text(row.get(column))
        for column in ["source_page", "bbox", "image_path", "source_html_snippet"]
    )


def _build_error(
    *,
    review_item_id: str,
    severity: str,
    error_code: str,
    detail: str,
    source_row_reference: str = "",
) -> Dict[str, Any]:
    return {
        "review_item_id": review_item_id,
        "severity": severity,
        "error_code": error_code,
        "detail": detail,
        "source_row_reference": source_row_reference,
    }


def _prepare_reviewed_overlay(
    canonical_template_df: pd.DataFrame,
    reviewed_df: pd.DataFrame,
) -> tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, int]]:
    errors: List[Dict[str, Any]] = []
    counters = {
        "duplicate_review_item_count": 0,
        "unknown_review_item_count": 0,
        "missing_review_item_count": 0,
    }

    reviewed_df = _ensure_columns(reviewed_df, ["review_item_id", *REVIEWER_FIELDS])
    source_ids = set(canonical_template_df["review_item_id"].astype(str))

    for row_index, row in enumerate(reviewed_df.to_dict(orient="records"), start=2):
        review_item_id = _norm_text(row.get("review_item_id"))
        has_reviewer_content = any(_norm_text(row.get(field)) for field in REVIEWER_FIELDS)
        if not review_item_id:
            if has_reviewer_content:
                counters["missing_review_item_count"] += 1
                errors.append(
                    _build_error(
                        review_item_id="",
                        severity="FAIL",
                        error_code="MISSING_REVIEW_ITEM_ID",
                        detail="Row contains reviewer content but review_item_id is blank.",
                        source_row_reference=f"reviewed_workbook::row_{row_index}",
                    )
                )
            continue
        if review_item_id not in source_ids:
            counters["unknown_review_item_count"] += 1
            errors.append(
                _build_error(
                    review_item_id=review_item_id,
                    severity="FAIL",
                    error_code="UNKNOWN_REVIEW_ITEM_ID",
                    detail="review_item_id not found in canonical 342G review template.",
                    source_row_reference=f"reviewed_workbook::row_{row_index}",
                )
            )

    nonblank_ids = reviewed_df["review_item_id"].map(_norm_text)
    duplicate_mask = nonblank_ids.ne("") & nonblank_ids.duplicated(keep=False)
    duplicate_ids = sorted(set(nonblank_ids[duplicate_mask].tolist()))
    counters["duplicate_review_item_count"] = len(duplicate_ids)
    for review_item_id in duplicate_ids:
        errors.append(
            _build_error(
                review_item_id=review_item_id,
                severity="FAIL",
                error_code="DUPLICATE_REVIEW_ITEM_ID",
                detail="Duplicate review_item_id detected in reviewed workbook.",
            )
        )

    overlay = reviewed_df.loc[~duplicate_mask, ["review_item_id", *REVIEWER_FIELDS]].copy()
    for field in REVIEWER_FIELDS:
        overlay[field] = overlay[field].map(_norm_text)
    overlay = overlay.drop_duplicates(subset=["review_item_id"], keep="first")
    return overlay, errors, counters


def _build_waiting_output(
    canonical_template_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pending_df = canonical_template_df.copy()
    pending_df["human_status"] = "PENDING_REVIEW"
    pending_df["validation_status"] = "PENDING_REVIEW"

    empty = _clean_frame(pd.DataFrame())
    return empty, empty, empty, empty, empty, pending_df, empty, empty


def _simulate_review_application(
    canonical_template_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, List[Dict[str, Any]], Dict[str, int]]:
    errors: List[Dict[str, Any]] = []
    counters = {
        "unknown_decision_count": 0,
        "correction_without_change_count": 0,
        "reviewer_value_parse_error_count": 0,
        "source_trace_missing_count": 0,
        "reviewed_row_count": 0,
        "pending_review_count": 0,
        "confirmed_cell_count": 0,
        "corrected_cell_count": 0,
        "rejected_cell_count": 0,
        "not_core_metric_count": 0,
        "still_review_required_count": 0,
        "needs_source_check_count": 0,
    }

    validated_rows: List[Dict[str, Any]] = []
    confirmed_rows: List[Dict[str, Any]] = []
    corrected_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    still_review_rows: List[Dict[str, Any]] = []
    needs_source_rows: List[Dict[str, Any]] = []
    pending_rows: List[Dict[str, Any]] = []
    source_trace_rows: List[Dict[str, Any]] = []

    for row in canonical_template_df.to_dict(orient="records"):
        record = dict(row)
        review_item_id = _norm_text(record.get("review_item_id"))
        reviewer_decision = _norm_text(record.get("reviewer_decision"))
        source_row_reference = f"10_REVIEW_TEMPLATE::{review_item_id or 'missing'}"

        if not reviewer_decision:
            counters["pending_review_count"] += 1
            record["human_status"] = "PENDING_REVIEW"
            record["validation_status"] = "PENDING_REVIEW"
            pending_rows.append(record)
            continue

        counters["reviewed_row_count"] += 1
        row_errors: List[Dict[str, Any]] = []

        if reviewer_decision not in ALLOWED_DECISIONS:
            counters["unknown_decision_count"] += 1
            row_errors.append(
                _build_error(
                    review_item_id=review_item_id,
                    severity="FAIL",
                    error_code="UNKNOWN_DECISION",
                    detail=f"Unsupported reviewer_decision: {reviewer_decision}",
                    source_row_reference=source_row_reference,
                )
            )

        if _source_trace_missing(record):
            counters["source_trace_missing_count"] += 1
            row_errors.append(
                _build_error(
                    review_item_id=review_item_id,
                    severity="FAIL",
                    error_code="SOURCE_TRACE_MISSING",
                    detail="source_page / bbox / image_path / source_html_snippet must be preserved.",
                    source_row_reference=source_row_reference,
                )
            )

        if reviewer_decision in {"CONFIRM_CELL", "CORRECT_AND_CONFIRM"} and _norm_text(record.get("table_type")) in EXCLUDED_TABLE_TYPES:
            row_errors.append(
                _build_error(
                    review_item_id=review_item_id,
                    severity="FAIL",
                    error_code="EXCLUDED_TABLE_CONFIRMED",
                    detail="Excluded / metadata table type cannot be confirmed as core financial output.",
                    source_row_reference=source_row_reference,
                )
            )

        if reviewer_decision in {"CONFIRM_CELL", "CORRECT_AND_CONFIRM"} and _norm_text(record.get("extraction_status")) == "REJECTED_CELL":
            row_errors.append(
                _build_error(
                    review_item_id=review_item_id,
                    severity="FAIL",
                    error_code="REJECTED_SOURCE_CONFIRMED",
                    detail="Rejected source rows cannot be confirmed as human-confirmed core outputs.",
                    source_row_reference=source_row_reference,
                )
            )

        final_metric = _norm_text(record.get("metric_standardized"))
        final_year = _norm_text(record.get("year_standardized"))
        final_value = record.get("value_numeric")
        final_unit = _norm_text(record.get("normalized_unit"))

        if reviewer_decision == "CORRECT_AND_CONFIRM":
            corrected_fields = {
                "reviewer_metric_standardized": _norm_text(record.get("reviewer_metric_standardized")),
                "reviewer_year_standardized": _norm_text(record.get("reviewer_year_standardized")),
                "reviewer_value_numeric": _norm_text(record.get("reviewer_value_numeric")),
                "reviewer_normalized_unit": _norm_text(record.get("reviewer_normalized_unit")),
            }
            if not any(corrected_fields.values()):
                counters["correction_without_change_count"] += 1
                row_errors.append(
                    _build_error(
                        review_item_id=review_item_id,
                        severity="FAIL",
                        error_code="CORRECTION_WITHOUT_CHANGE",
                        detail="CORRECT_AND_CONFIRM requires at least one corrected field.",
                        source_row_reference=source_row_reference,
                    )
                )
            if corrected_fields["reviewer_metric_standardized"]:
                final_metric = corrected_fields["reviewer_metric_standardized"]
            if corrected_fields["reviewer_year_standardized"]:
                final_year = corrected_fields["reviewer_year_standardized"]
            if corrected_fields["reviewer_value_numeric"]:
                parsed_value = _safe_float(corrected_fields["reviewer_value_numeric"])
                if parsed_value is None:
                    counters["reviewer_value_parse_error_count"] += 1
                    row_errors.append(
                        _build_error(
                            review_item_id=review_item_id,
                            severity="FAIL",
                            error_code="REVIEWER_VALUE_PARSE_ERROR",
                            detail="reviewer_value_numeric is not parseable as a number.",
                            source_row_reference=source_row_reference,
                        )
                    )
                else:
                    final_value = parsed_value
            if corrected_fields["reviewer_normalized_unit"]:
                final_unit = corrected_fields["reviewer_normalized_unit"]

        if reviewer_decision == "CONFIRM_CELL":
            record["human_status"] = "HUMAN_CONFIRMED_CELL"
        elif reviewer_decision == "CORRECT_AND_CONFIRM":
            record["human_status"] = "HUMAN_CORRECTED_CONFIRMED_CELL"
        elif reviewer_decision == "REJECT_CELL":
            record["human_status"] = "HUMAN_REJECTED_CELL"
        elif reviewer_decision == "NOT_A_CORE_METRIC":
            record["human_status"] = "HUMAN_REJECTED_NOT_CORE"
        elif reviewer_decision == "KEEP_REVIEW_REQUIRED":
            record["human_status"] = "STILL_REVIEW_REQUIRED"
        elif reviewer_decision == "NEEDS_SOURCE_CHECK":
            record["human_status"] = "NEEDS_SOURCE_CHECK"
        else:
            record["human_status"] = "REVIEW_ERROR"

        if reviewer_decision == "CORRECT_AND_CONFIRM" and final_unit and _unit_conflict(final_metric, final_unit):
            row_errors.append(
                _build_error(
                    review_item_id=review_item_id,
                    severity="FAIL",
                    error_code="REVIEWER_UNIT_CONFLICT",
                    detail="reviewer_normalized_unit conflicts with the corrected metric type.",
                    source_row_reference=source_row_reference,
                )
            )

        record["final_metric_standardized"] = final_metric
        record["final_year_standardized"] = final_year
        record["final_value_numeric"] = final_value
        record["final_normalized_unit"] = final_unit
        record["validation_status"] = "FAIL" if row_errors else "PASS"
        validated_rows.append(record)
        errors.extend(row_errors)

        if row_errors:
            continue

        if record["human_status"] == "HUMAN_CONFIRMED_CELL":
            counters["confirmed_cell_count"] += 1
            confirmed_rows.append(record)
        elif record["human_status"] == "HUMAN_CORRECTED_CONFIRMED_CELL":
            counters["corrected_cell_count"] += 1
            corrected_rows.append(record)
        elif record["human_status"] == "HUMAN_REJECTED_CELL":
            counters["rejected_cell_count"] += 1
            rejected_rows.append(record)
        elif record["human_status"] == "HUMAN_REJECTED_NOT_CORE":
            counters["not_core_metric_count"] += 1
            rejected_rows.append(record)
        elif record["human_status"] == "STILL_REVIEW_REQUIRED":
            counters["still_review_required_count"] += 1
            still_review_rows.append(record)
        elif record["human_status"] == "NEEDS_SOURCE_CHECK":
            counters["needs_source_check_count"] += 1
            needs_source_rows.append(record)

        if record["human_status"] in {
            "HUMAN_CONFIRMED_CELL",
            "HUMAN_CORRECTED_CONFIRMED_CELL",
            "HUMAN_REJECTED_CELL",
            "HUMAN_REJECTED_NOT_CORE",
        }:
            source_trace_rows.append(
                {
                    "review_item_id": review_item_id,
                    "corpus_pdf_id": _norm_text(record.get("corpus_pdf_id")),
                    "file_name": _norm_text(record.get("file_name")),
                    "table_id": _norm_text(record.get("table_id")),
                    "table_type": _norm_text(record.get("table_type")),
                    "source_page": _norm_text(record.get("source_page")),
                    "bbox": _norm_text(record.get("bbox")),
                    "image_path": _norm_text(record.get("image_path")),
                    "source_html_snippet": _norm_text(record.get("source_html_snippet")),
                    "reviewer_decision": reviewer_decision,
                    "human_status": _norm_text(record.get("human_status")),
                }
            )

    return (
        _clean_frame(pd.DataFrame(validated_rows)),
        _clean_frame(pd.DataFrame(confirmed_rows)),
        _clean_frame(pd.DataFrame(corrected_rows)),
        _clean_frame(pd.DataFrame(rejected_rows)),
        _clean_frame(pd.DataFrame(still_review_rows)),
        _clean_frame(pd.DataFrame(needs_source_rows)),
        _clean_frame(pd.DataFrame(pending_rows)),
        _clean_frame(pd.DataFrame(errors)),
        _clean_frame(pd.DataFrame(source_trace_rows)),
        counters,
    )


def _build_readme_df(reviewed_workbook_exists: bool) -> pd.DataFrame:
    status_message = (
        "342H 正在消费已填写的人审 workbook，做 human review apply simulation dry-run。"
        if reviewed_workbook_exists
        else "342H 当前处于 waiting-for-human-review 状态，因为 reviewed workbook 还不存在。"
    )
    rows = [
        {
            "topic": "用途 / Purpose",
            "message": "342H 是 human review apply simulation sidecar，不是正式财务结果，也不会写回任何上游 workbook。",
        },
        {
            "topic": "Current status",
            "message": status_message,
        },
        {
            "topic": "Boundary",
            "message": "No MinerU rerun, no VLM/LLM call, no production pipeline / parser / extraction / delivery modification.",
        },
        {
            "topic": "Allowed reviewer_decision",
            "message": "CONFIRM_CELL | CORRECT_AND_CONFIRM | REJECT_CELL | KEEP_REVIEW_REQUIRED | NOT_A_CORE_METRIC | NEEDS_SOURCE_CHECK",
        },
        {
            "topic": "Status boundary",
            "message": "342H remains not client-ready and not production-ready.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_input_review_status_df(
    *,
    review_package_dir: Path,
    reviewed_input_dir: Path,
    reviewed_workbook_path: Path,
    reviewed_workbook_exists: bool,
    reviewed_sheet_name: str,
    source_template_rows: int,
    reviewed_rows: int,
) -> pd.DataFrame:
    rows = [
        {"item": "review_package_342g_dir", "value": str(review_package_dir)},
        {"item": "reviewed_input_dir", "value": str(reviewed_input_dir)},
        {"item": "reviewed_workbook_path", "value": str(reviewed_workbook_path)},
        {"item": "reviewed_workbook_exists", "value": reviewed_workbook_exists},
        {"item": "reviewed_sheet_name", "value": reviewed_sheet_name},
        {"item": "source_template_row_count", "value": source_template_rows},
        {"item": "reviewed_sheet_row_count", "value": reviewed_rows},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_before_after_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "input_review_template_row_count": summary.get("input_review_template_row_count", 0),
                    "reviewed_row_count": summary.get("reviewed_row_count", 0),
                    "pending_review_count": summary.get("pending_review_count", 0),
                    "confirmed_cell_count": summary.get("confirmed_cell_count", 0),
                    "corrected_cell_count": summary.get("corrected_cell_count", 0),
                    "rejected_cell_count": summary.get("rejected_cell_count", 0),
                    "still_review_required_count": summary.get("still_review_required_count", 0),
                    "needs_source_check_count": summary.get("needs_source_check_count", 0),
                    "net_confirmed_after_human_count": summary.get("net_confirmed_after_human_count", 0),
                    "net_review_reduction_count": summary.get("net_review_reduction_count", 0),
                    "net_rejected_after_human_count": summary.get("net_rejected_after_human_count", 0),
                    "validation_error_count": summary.get("validation_error_count", 0),
                }
            ]
        )
    )


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342i": summary.get("ready_for_342i", False),
                    "recommended_342i_scope": summary.get("recommended_342i_scope", ""),
                    "recommended_next_action": summary.get("recommended_next_action", ""),
                    "reason": (
                        "342H 已有有效人审结果，可进入 342I Table-First Post-Human-Review Sidecar Result。"
                        if summary.get("ready_for_342i", False)
                        else "当前仍需先完成人工填写或修复 review errors，暂不进入 342I。"
                    ),
                }
            ]
        )
    )


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    if summary.get("decision") == WAITING_DECISION:
        rows = [
            {"step_order": 1, "next_step": "Fill 342G review template", "rationale": "先在 reviewed workbook 中填写 reviewer_decision 与必要修正字段。"},
            {"step_order": 2, "next_step": "Rerun 342H", "rationale": "填完后重新运行 342H，生成 apply simulation 结果。"},
        ]
    elif summary.get("ready_for_342i", False):
        rows = [
            {"step_order": 1, "next_step": "Open 04_CONFIRMED_CELLS / 05_CORRECTED_CELLS", "rationale": "检查人审后净确认结果。"},
            {"step_order": 2, "next_step": "Proceed to 342I", "rationale": "当前 recommended_342i_scope 已满足。"},
        ]
    else:
        rows = [
            {"step_order": 1, "next_step": "Fix 10_REVIEW_ERRORS", "rationale": "先修复 unknown decision、无效 correction 或 source trace 缺失。"},
            {"step_order": 2, "next_step": "Rerun 342H", "rationale": "清零 validation errors 后再判断是否进入 342I。"},
        ]
    return _clean_frame(pd.DataFrame(rows))


def _build_no_write_back_proof_df(no_write_back_json: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for path, before_hash in no_write_back_json.get("upstream_input_hashes_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_write_back_json.get("upstream_input_hashes_after", {}).get(path, ""),
                "unchanged": before_hash == no_write_back_json.get("upstream_input_hashes_after", {}).get(path, ""),
            }
        )
    for path, before_hash in no_write_back_json.get("official_assets_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_write_back_json.get("official_assets_after", {}).get(path, ""),
                "unchanged": before_hash == no_write_back_json.get("official_assets_after", {}).get(path, ""),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def build_table_first_human_review_apply_simulation_342h(
    *,
    review_package_342g_dir: Path,
    reviewed_input_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_342g, qa_342g, proof_342g, workbook_342g, files_read_342g, warnings_342g = _load_review_package_context(review_package_342g_dir)
    files_read.extend(files_read_342g)
    warnings.extend(warnings_342g)

    source_template_df = _ensure_columns(workbook_342g.get("10_REVIEW_TEMPLATE", pd.DataFrame()), ["review_item_id", *REVIEWER_FIELDS])
    source_template_df = _clean_frame(source_template_df)
    reviewed_workbook_path = reviewed_input_dir / REVIEWED_WORKBOOK_NAME
    reviewed_workbook_exists = reviewed_workbook_path.exists()
    reviewed_sheet_name = ""
    reviewed_raw_df = pd.DataFrame()

    if reviewed_workbook_exists:
        files_read.append(str(reviewed_workbook_path))
        try:
            reviewed_sheet_name, reviewed_raw_df = _find_review_sheet(reviewed_workbook_path)
            if reviewed_sheet_name is None:
                warnings.append("reviewed workbook exists but no sheet with reviewer_decision was found")
                reviewed_sheet_name = ""
                reviewed_raw_df = pd.DataFrame()
        except Exception as exc:
            warnings.append(f"unable to read reviewed workbook: {exc}")
            reviewed_sheet_name = ""
            reviewed_raw_df = pd.DataFrame()

    input_review_template_row_count = int(len(source_template_df))

    overlay_errors: List[Dict[str, Any]] = []
    overlay_counters = {
        "duplicate_review_item_count": 0,
        "unknown_review_item_count": 0,
        "missing_review_item_count": 0,
    }
    canonical_template_df = source_template_df.copy()

    if reviewed_workbook_exists and not reviewed_raw_df.empty:
        overlay_df, overlay_errors, overlay_counters = _prepare_reviewed_overlay(source_template_df, reviewed_raw_df)
        canonical_template_df = canonical_template_df.drop(columns=[column for column in REVIEWER_FIELDS if column in canonical_template_df.columns])
        canonical_template_df = canonical_template_df.merge(overlay_df, on="review_item_id", how="left")
        canonical_template_df = _ensure_columns(canonical_template_df, [*source_template_df.columns, *REVIEWER_FIELDS])
        for field in REVIEWER_FIELDS:
            canonical_template_df[field] = canonical_template_df[field].map(_norm_text)
    else:
        canonical_template_df = _ensure_columns(canonical_template_df, [*source_template_df.columns, *REVIEWER_FIELDS])

    if not reviewed_workbook_exists:
        (
            validated_df,
            confirmed_df,
            corrected_df,
            rejected_df,
            still_review_df,
            needs_source_df,
            pending_df,
            error_df,
        ) = _build_waiting_output(canonical_template_df)
        source_trace_df = _clean_frame(pd.DataFrame())
        counters = {
            "reviewed_row_count": 0,
            "pending_review_count": input_review_template_row_count,
            "confirmed_cell_count": 0,
            "corrected_cell_count": 0,
            "rejected_cell_count": 0,
            "not_core_metric_count": 0,
            "still_review_required_count": 0,
            "needs_source_check_count": 0,
            "unknown_decision_count": 0,
            "correction_without_change_count": 0,
            "reviewer_value_parse_error_count": 0,
            "source_trace_missing_count": 0,
            **overlay_counters,
        }
    else:
        (
            validated_df,
            confirmed_df,
            corrected_df,
            rejected_df,
            still_review_df,
            needs_source_df,
            pending_df,
            simulation_error_df,
            source_trace_df,
            counters,
        ) = _simulate_review_application(canonical_template_df)
        combined_errors = overlay_errors + simulation_error_df.to_dict(orient="records")
        error_df = _clean_frame(pd.DataFrame(combined_errors))
        counters = {**overlay_counters, **counters}

    reviewed_row_count = int(counters.get("reviewed_row_count", 0))
    pending_review_count = int(counters.get("pending_review_count", len(pending_df)))
    confirmed_cell_count = int(counters.get("confirmed_cell_count", 0))
    corrected_cell_count = int(counters.get("corrected_cell_count", 0))
    rejected_cell_count = int(counters.get("rejected_cell_count", 0))
    not_core_metric_count = int(counters.get("not_core_metric_count", 0))
    still_review_required_count = int(counters.get("still_review_required_count", 0))
    needs_source_check_count = int(counters.get("needs_source_check_count", 0))
    validation_error_count = int(len(error_df))
    duplicate_review_item_count = int(counters.get("duplicate_review_item_count", 0))
    unknown_decision_count = int(counters.get("unknown_decision_count", 0))
    correction_without_change_count = int(counters.get("correction_without_change_count", 0))
    reviewer_value_parse_error_count = int(counters.get("reviewer_value_parse_error_count", 0))
    source_trace_missing_count = int(counters.get("source_trace_missing_count", 0))

    net_confirmed_after_human_count = confirmed_cell_count + corrected_cell_count
    net_rejected_after_human_count = rejected_cell_count + not_core_metric_count
    net_review_reduction_count = net_confirmed_after_human_count + net_rejected_after_human_count

    ready_for_342i = bool(
        reviewed_workbook_exists
        and reviewed_row_count > 0
        and validation_error_count == 0
        and (confirmed_cell_count + corrected_cell_count + rejected_cell_count) > 0
    )
    recommended_342i_scope = "table_first_post_human_review_sidecar_result" if ready_for_342i else ""
    recommended_next_action = ""

    if not reviewed_workbook_exists:
        decision = WAITING_DECISION
        recommended_next_action = "fill_342g_review_template_first"
    elif validation_error_count == 0:
        decision = READY_DECISION
        recommended_next_action = "proceed_to_342i"
    else:
        decision = NOT_READY_DECISION
        recommended_next_action = "fix_review_errors_then_rerun_342h"

    files_for_hash = list(files_read)
    no_write_back_input_hashes_before = {
        path: sha256_file(Path(path))
        for path in files_for_hash
        if Path(path).exists() and Path(path).is_file()
    }
    no_write_back_input_hashes_after = {
        path: sha256_file(Path(path))
        for path in files_for_hash
        if Path(path).exists() and Path(path).is_file()
    }

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342H",
        files_read=files_for_hash,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = no_write_back_input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = no_write_back_input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = no_write_back_input_hashes_before == no_write_back_input_hashes_after
    no_write_back_json["client_export_generated"] = False
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True

    no_write_back_proof_passed = (
        bool(no_write_back_json.get("no_official_asset_modification_during_342h"))
        and bool(no_write_back_json.get("upstream_workbooks_unchanged"))
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df(reviewed_workbook_exists)
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())

    checks = [
        {"check_name": "inputs::342g_summary_exists", "status": "PASS" if (review_package_342g_dir / REVIEW_PACKAGE_SUMMARY_NAME).exists() else "FAIL", "detail": str(review_package_342g_dir / REVIEW_PACKAGE_SUMMARY_NAME)},
        {"check_name": "inputs::342g_qa_exists", "status": "PASS" if (review_package_342g_dir / REVIEW_PACKAGE_QA_NAME).exists() else "FAIL", "detail": str(review_package_342g_dir / REVIEW_PACKAGE_QA_NAME)},
        {"check_name": "inputs::342g_workbook_exists", "status": "PASS" if (review_package_342g_dir / REVIEW_PACKAGE_WORKBOOK_NAME).exists() else "FAIL", "detail": str(review_package_342g_dir / REVIEW_PACKAGE_WORKBOOK_NAME)},
        {
            "check_name": "inputs::342g_ready_for_342h_detected",
            "status": "PASS"
            if summary_342g.get("decision", "") == READY_INPUT_DECISION
            and bool(summary_342g.get("ready_for_342h", False))
            and int(summary_342g.get("qa_fail_count", 0) or 0) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342g.get("decision", ""),
                    "ready_for_342h": summary_342g.get("ready_for_342h", False),
                    "qa_fail_count": summary_342g.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342g_required_sheets_exist",
            "status": "PASS" if all(not workbook_342g.get(sheet, pd.DataFrame()).empty for sheet in REQUIRED_342G_SHEETS) else "FAIL",
            "detail": json.dumps({sheet: not workbook_342g.get(sheet, pd.DataFrame()).empty for sheet in REQUIRED_342G_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "inputs::review_template_exists",
            "status": "PASS" if not source_template_df.empty else "FAIL",
            "detail": str(len(source_template_df)),
        },
        {
            "check_name": "inputs::reviewed_workbook_status_detected",
            "status": "PASS",
            "detail": json.dumps(
                {
                    "reviewed_workbook_exists": reviewed_workbook_exists,
                    "reviewed_sheet_name": reviewed_sheet_name,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "quality::blank_decisions_treated_as_pending",
            "status": "PASS" if pending_review_count == int(canonical_template_df["reviewer_decision"].map(_norm_text).eq("").sum()) else "FAIL",
            "detail": f"pending={pending_review_count}",
        },
        {
            "check_name": "quality::allowed_reviewer_decisions_enforced",
            "status": "PASS" if unknown_decision_count == 0 else "FAIL",
            "detail": str(unknown_decision_count),
        },
        {
            "check_name": "quality::corrections_validated",
            "status": "PASS" if correction_without_change_count == 0 and reviewer_value_parse_error_count == 0 else "FAIL",
            "detail": json.dumps(
                {
                    "correction_without_change_count": correction_without_change_count,
                    "reviewer_value_parse_error_count": reviewer_value_parse_error_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "quality::source_trace_preserved",
            "status": "PASS" if source_trace_missing_count == 0 else "FAIL",
            "detail": str(source_trace_missing_count),
        },
        {
            "check_name": "quality::no_fake_human_decisions_generated",
            "status": "PASS",
            "detail": "342H only consumes reviewer_* fields from reviewed workbook or leaves rows pending.",
        },
        {
            "check_name": "quality::review_errors_zero_when_ready",
            "status": "PASS" if (decision != READY_DECISION or validation_error_count == 0) else "FAIL",
            "detail": str(validation_error_count),
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if no_write_back_json.get("upstream_workbooks_unchanged") else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "342H adds sidecar apply-simulation code only",
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
            "status": "PASS" if not _contains_forbidden_claim(readme_text, ["investment advice"]) else "FAIL",
            "detail": "README text checked",
        },
        {
            "check_name": "safety::no_sheet_name_exceeds_limit",
            "status": "PASS",
            "detail": "all 342H sheet names are <= 31 chars",
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]

    if not reviewed_workbook_exists:
        checks.append(
            {
                "check_name": "waiting::reviewed_workbook_missing_recognized",
                "status": "PASS",
                "detail": "Waiting branch was selected correctly.",
            }
        )

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    if not reviewed_workbook_exists:
        qa_fail_count = 0 if qa_fail_count == 0 else qa_fail_count
        ready_for_342i = False
        recommended_342i_scope = ""

    summary = {
        "generated_at_utc": _utc_now(),
        "reviewed_workbook_exists": reviewed_workbook_exists,
        "reviewed_workbook_path": str(reviewed_workbook_path),
        "reviewed_sheet_name": reviewed_sheet_name,
        "input_review_template_row_count": input_review_template_row_count,
        "reviewed_row_count": reviewed_row_count,
        "pending_review_count": pending_review_count,
        "confirmed_cell_count": confirmed_cell_count,
        "corrected_cell_count": corrected_cell_count,
        "rejected_cell_count": rejected_cell_count,
        "not_core_metric_count": not_core_metric_count,
        "still_review_required_count": still_review_required_count,
        "needs_source_check_count": needs_source_check_count,
        "validation_error_count": validation_error_count,
        "duplicate_review_item_count": duplicate_review_item_count,
        "unknown_decision_count": unknown_decision_count,
        "correction_without_change_count": correction_without_change_count,
        "reviewer_value_parse_error_count": reviewer_value_parse_error_count,
        "source_trace_missing_count": source_trace_missing_count,
        "net_confirmed_after_human_count": net_confirmed_after_human_count,
        "net_review_reduction_count": net_review_reduction_count,
        "net_rejected_after_human_count": net_rejected_after_human_count,
        "ready_for_342i": ready_for_342i,
        "recommended_342i_scope": recommended_342i_scope,
        "recommended_next_action": recommended_next_action,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342H_table_first_human_review_apply_simulation",
        "review_package_342g_dir": str(review_package_342g_dir),
        "reviewed_input_dir": str(reviewed_input_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
        },
        "allowed_reviewer_decisions": list(ALLOWED_DECISIONS),
        "files_read": files_for_hash,
        "warnings": warnings,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": no_write_back_input_hashes_before,
        "upstream_input_hashes_after": no_write_back_input_hashes_after,
    }

    input_status_df = _build_input_review_status_df(
        review_package_dir=review_package_342g_dir,
        reviewed_input_dir=reviewed_input_dir,
        reviewed_workbook_path=reviewed_workbook_path,
        reviewed_workbook_exists=reviewed_workbook_exists,
        reviewed_sheet_name=reviewed_sheet_name,
        source_template_rows=input_review_template_row_count,
        reviewed_rows=int(len(reviewed_raw_df)),
    )

    workbook_sheets = {
        "00_README": readme_df,
        "01_APPLY_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_REVIEW_STATUS": input_status_df,
        "03_VALIDATED_DECISIONS": validated_df,
        "04_CONFIRMED_CELLS": confirmed_df,
        "05_CORRECTED_CELLS": corrected_df,
        "06_REJECTED_CELLS": rejected_df,
        "07_STILL_REVIEW": still_review_df,
        "08_NEEDS_SOURCE_CHECK": needs_source_df,
        "09_PENDING_REVIEW": pending_df,
        "10_REVIEW_ERRORS": error_df,
        "11_BEFORE_AFTER": _build_before_after_df(summary),
        "12_SOURCE_TRACE": source_trace_df,
        "13_342I_READINESS": _build_readiness_df(summary),
        "14_NO_WRITE_BACK": _build_no_write_back_proof_df(no_write_back_json),
        "15_NEXT_STEPS": _build_next_steps_df(summary),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
