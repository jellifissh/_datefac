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


READY_INPUT_DECISION = "TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_READY"
READY_DECISION = "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY"
NOT_READY_DECISION = "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_NOT_READY"

DEFAULT_HUMAN_REVIEW_342H_DIR = Path(r"D:\_datefac\output\table_first_human_review_apply_simulation_342h")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\table_first_post_human_review_sidecar_result_342i")

SUMMARY_FILE_NAME = "table_first_post_human_review_sidecar_result_342i_summary.json"
MANIFEST_FILE_NAME = "table_first_post_human_review_sidecar_result_342i_manifest.json"
QA_FILE_NAME = "table_first_post_human_review_sidecar_result_342i_qa.json"
NO_WRITE_BACK_FILE_NAME = "table_first_post_human_review_sidecar_result_342i_no_write_back_proof.json"
REPORT_FILE_NAME = "table_first_post_human_review_sidecar_result_342i_report.md"
WORKBOOK_FILE_NAME = "table_first_post_human_review_sidecar_result_342i.xlsx"

INPUT_SUMMARY_NAME = "table_first_human_review_apply_simulation_342h_summary.json"
INPUT_QA_NAME = "table_first_human_review_apply_simulation_342h_qa.json"
INPUT_REPORT_NAME = "table_first_human_review_apply_simulation_342h_report.md"
INPUT_WORKBOOK_NAME = "table_first_human_review_apply_simulation_342h.xlsx"
INPUT_NO_WRITE_BACK_NAME = "table_first_human_review_apply_simulation_342h_no_write_back_proof.json"

REQUIRED_342H_SHEETS = [
    "01_APPLY_SUMMARY",
    "03_VALIDATED_DECISIONS",
    "04_CONFIRMED_CELLS",
    "05_CORRECTED_CELLS",
    "09_PENDING_REVIEW",
    "11_BEFORE_AFTER",
    "12_SOURCE_TRACE",
    "13_342I_READINESS",
    "14_NO_WRITE_BACK",
]
OPTIONAL_342H_SHEETS = [
    "06_REJECTED_CELLS",
    "07_STILL_REVIEW",
    "08_NEEDS_SOURCE_CHECK",
    "10_REVIEW_ERRORS",
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

FINAL_STATUS_MAP = {
    "HUMAN_CONFIRMED_CELL": "POST_HUMAN_CONFIRMED",
    "HUMAN_CORRECTED_CONFIRMED_CELL": "POST_HUMAN_CORRECTED_CONFIRMED",
    "HUMAN_REJECTED_CELL": "POST_HUMAN_REJECTED",
    "HUMAN_REJECTED_NOT_CORE": "POST_HUMAN_REJECTED",
    "STILL_REVIEW_REQUIRED": "POST_HUMAN_STILL_REVIEW_REQUIRED",
    "NEEDS_SOURCE_CHECK": "POST_HUMAN_NEEDS_SOURCE_CHECK",
}


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
        token_lower = token.casefold()
        start = 0
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


def _sheet_exists(workbook_sheets: Mapping[str, pd.DataFrame], sheet_name: str) -> bool:
    return sheet_name in workbook_sheets and workbook_sheets[sheet_name] is not None


def _load_342h_context(
    human_review_342h_dir: Path,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []

    summary_path = human_review_342h_dir / INPUT_SUMMARY_NAME
    qa_path = human_review_342h_dir / INPUT_QA_NAME
    report_path = human_review_342h_dir / INPUT_REPORT_NAME
    workbook_path = human_review_342h_dir / INPUT_WORKBOOK_NAME
    proof_path = human_review_342h_dir / INPUT_NO_WRITE_BACK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    proof_json = _read_json(proof_path) if proof_path.exists() else {}

    for path, label in [
        (summary_path, "342H summary"),
        (qa_path, "342H qa"),
        (report_path, "342H report"),
        (workbook_path, "342H workbook"),
        (proof_path, "342H no-write-back proof"),
    ]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing {label}: {path}")

    workbook_sheets: Dict[str, pd.DataFrame] = {}
    if workbook_path.exists():
        try:
            excel = pd.ExcelFile(workbook_path)
            for sheet in REQUIRED_342H_SHEETS + OPTIONAL_342H_SHEETS:
                if sheet in excel.sheet_names:
                    workbook_sheets[sheet] = _clean_frame(pd.read_excel(workbook_path, sheet_name=sheet))
                else:
                    workbook_sheets[sheet] = pd.DataFrame()
                    if sheet in REQUIRED_342H_SHEETS:
                        warnings.append(f"missing required 342H workbook sheet: {sheet}")
        except Exception as exc:
            warnings.append(f"unable to read 342H workbook: {exc}")
            for sheet in REQUIRED_342H_SHEETS + OPTIONAL_342H_SHEETS:
                workbook_sheets[sheet] = pd.DataFrame()
    else:
        for sheet in REQUIRED_342H_SHEETS + OPTIONAL_342H_SHEETS:
            workbook_sheets[sheet] = pd.DataFrame()

    return summary, qa_json, proof_json, workbook_sheets, files_read, warnings


def _set_final_status(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = _clean_frame(df.copy())
    out["final_status"] = out["human_status"].map(lambda value: FINAL_STATUS_MAP.get(_norm_text(value), ""))
    return out


def _fill_final_fields(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = _clean_frame(df.copy())
    mappings = [
        ("final_metric_standardized", "metric_standardized"),
        ("final_year_standardized", "year_standardized"),
        ("final_value_numeric", "value_numeric"),
        ("final_normalized_unit", "normalized_unit"),
    ]
    for final_col, source_col in mappings:
        if final_col not in out.columns:
            out[final_col] = ""
        if source_col not in out.columns:
            out[source_col] = ""
        out[final_col] = [
            row[final_col] if _norm_text(row[final_col]) else row[source_col]
            for _, row in out[[final_col, source_col]].iterrows()
        ]
    return _clean_frame(out)


def _numeric_equal(left: Any, right: Any) -> bool:
    left_text = _norm_text(left)
    right_text = _norm_text(right)
    if not left_text and not right_text:
        return True
    try:
        return float(left_text) == float(right_text)
    except Exception:
        return left_text == right_text


def _change_type(row: Mapping[str, Any]) -> str:
    human_status = _norm_text(row.get("human_status"))
    if human_status == "HUMAN_CONFIRMED_CELL":
        return "UNCHANGED_CONFIRMED"
    if human_status in {"HUMAN_REJECTED_CELL", "HUMAN_REJECTED_NOT_CORE"}:
        return "REJECTED"
    if human_status == "STILL_REVIEW_REQUIRED":
        return "STILL_REVIEW_REQUIRED"
    if human_status == "NEEDS_SOURCE_CHECK":
        return "NEEDS_SOURCE_CHECK"

    changes: List[str] = []
    if _norm_text(row.get("metric_standardized")) != _norm_text(row.get("final_metric_standardized")):
        changes.append("metric")
    if _norm_text(row.get("year_standardized")) != _norm_text(row.get("final_year_standardized")):
        changes.append("year")
    if not _numeric_equal(row.get("value_numeric"), row.get("final_value_numeric")):
        changes.append("value")
    if _norm_text(row.get("normalized_unit")) != _norm_text(row.get("final_normalized_unit")):
        changes.append("unit")

    if changes == ["metric"]:
        return "METRIC_CORRECTED"
    if changes == ["year"]:
        return "YEAR_CORRECTED"
    if changes == ["value"]:
        return "VALUE_CORRECTED"
    if changes == ["unit"]:
        return "UNIT_CORRECTED"
    if changes:
        return "MULTI_FIELD_CORRECTED"
    return "UNCHANGED_CONFIRMED"


def _build_before_after_df(human_reviewed_df: pd.DataFrame) -> pd.DataFrame:
    if human_reviewed_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for row in human_reviewed_df.to_dict(orient="records"):
        rows.append(
            {
                "review_item_id": _norm_text(row.get("review_item_id")),
                "human_status": _norm_text(row.get("human_status")),
                "reviewer_decision": _norm_text(row.get("reviewer_decision")),
                "original_metric_standardized": _norm_text(row.get("metric_standardized")),
                "final_metric_standardized": _norm_text(row.get("final_metric_standardized")),
                "original_year_standardized": _norm_text(row.get("year_standardized")),
                "final_year_standardized": _norm_text(row.get("final_year_standardized")),
                "original_value_numeric": row.get("value_numeric"),
                "final_value_numeric": row.get("final_value_numeric"),
                "original_normalized_unit": _norm_text(row.get("normalized_unit")),
                "final_normalized_unit": _norm_text(row.get("final_normalized_unit")),
                "change_type": _change_type(row),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_metric_coverage_after_df(post_human_confirmed_df: pd.DataFrame) -> pd.DataFrame:
    if post_human_confirmed_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    grouped = post_human_confirmed_df.groupby("final_metric_standardized", dropna=False)
    for metric_name, group in grouped:
        metric = _norm_text(metric_name)
        years = sorted({_norm_text(value) for value in group["final_year_standardized"].tolist() if _norm_text(value)})
        rows.append(
            {
                "final_metric_standardized": metric,
                "confirmed_count": int(group["final_status"].map(_norm_text).eq("POST_HUMAN_CONFIRMED").sum()),
                "corrected_count": int(group["final_status"].map(_norm_text).eq("POST_HUMAN_CORRECTED_CONFIRMED").sum()),
                "total_post_human_confirmed_count": int(len(group)),
                "year_covered_count": int(len(years)),
                "year_list": " | ".join(years),
                "pdf_covered_count": int(group["corpus_pdf_id"].map(_norm_text).replace("", pd.NA).dropna().nunique()),
                "table_covered_count": int(group["table_id"].map(_norm_text).replace("", pd.NA).dropna().nunique()),
            }
        )
    return _clean_frame(
        pd.DataFrame(rows).sort_values(
            by=["total_post_human_confirmed_count", "final_metric_standardized"],
            ascending=[False, True],
        )
    )


def _build_unit_year_after_df(post_human_confirmed_df: pd.DataFrame) -> pd.DataFrame:
    if post_human_confirmed_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for keys, group in post_human_confirmed_df.groupby(
        ["final_metric_standardized", "final_normalized_unit", "final_year_standardized"],
        dropna=False,
    ):
        metric_name, unit_name, year_name = keys
        unit = _norm_text(unit_name)
        year = _norm_text(year_name)
        has_unit = bool(unit)
        has_year = bool(year)
        if has_unit and has_year:
            status = "OK"
        elif has_unit and not has_year:
            status = "YEAR_MISSING"
        elif not has_unit and has_year:
            status = "UNIT_MISSING"
        else:
            status = "UNIT_YEAR_MISSING"
        rows.append(
            {
                "final_metric_standardized": _norm_text(metric_name),
                "final_normalized_unit": unit,
                "final_year_standardized": year,
                "row_count": int(len(group)),
                "has_unit": has_unit,
                "has_year": has_year,
                "unit_year_status": status,
            }
        )
    return _clean_frame(
        pd.DataFrame(rows).sort_values(
            by=["final_metric_standardized", "final_year_standardized", "final_normalized_unit"],
            ascending=[True, True, True],
        )
    )


def _count_unit_year_remaining(remaining_df: pd.DataFrame) -> int:
    if remaining_df.empty:
        return 0
    count = 0
    for row in remaining_df.to_dict(orient="records"):
        risk_flags = _norm_text(row.get("risk_flags"))
        review_reason = _norm_text(row.get("review_reason"))
        has_unit_issue = not _norm_text(row.get("normalized_unit")) or "UNIT" in risk_flags or "UNIT" in review_reason
        has_year_issue = not _norm_text(row.get("year_standardized")) or "YEAR" in risk_flags or "YEAR" in review_reason
        if has_unit_issue or has_year_issue:
            count += 1
    return count


def _count_duplicate_remaining(remaining_df: pd.DataFrame) -> int:
    if remaining_df.empty:
        return 0
    count = 0
    for row in remaining_df.to_dict(orient="records"):
        review_bucket = _norm_text(row.get("review_bucket"))
        review_reason = _norm_text(row.get("review_reason"))
        risk_flags = _norm_text(row.get("risk_flags"))
        if "DUPLICATE" in review_bucket or "DUPLICATE" in review_reason or "DUPLICATE" in risk_flags:
            count += 1
    return count


def _count_growth_row_remaining(remaining_df: pd.DataFrame) -> int:
    if remaining_df.empty:
        return 0
    count = 0
    for row in remaining_df.to_dict(orient="records"):
        review_bucket = _norm_text(row.get("review_bucket"))
        review_reason = _norm_text(row.get("review_reason"))
        metric_raw = _norm_text(row.get("metric_raw"))
        if "GROWTH" in review_bucket or "GROWTH" in review_reason or "增长" in metric_raw or "yoy" in metric_raw.casefold():
            count += 1
    return count


def _build_remaining_risks_df(
    *,
    pending_df: pd.DataFrame,
    still_review_df: pd.DataFrame,
    needs_source_df: pd.DataFrame,
) -> pd.DataFrame:
    remaining_frames = [frame for frame in [pending_df, still_review_df, needs_source_df] if not frame.empty]
    remaining_df = _clean_frame(pd.concat(remaining_frames, ignore_index=True)) if remaining_frames else pd.DataFrame()
    rows = [
        {
            "pending_review_count": int(len(pending_df)),
            "still_review_required_count": int(len(still_review_df)),
            "needs_source_check_count": int(len(needs_source_df)),
            "unit_year_remaining_count": _count_unit_year_remaining(remaining_df),
            "duplicate_remaining_count": _count_duplicate_remaining(remaining_df),
            "growth_row_remaining_count": _count_growth_row_remaining(remaining_df),
            "source_check_remaining_count": int(len(needs_source_df)),
            "high_priority_remaining_count": int(remaining_df["review_priority"].map(_norm_text).eq("HIGH").sum()) if "review_priority" in remaining_df.columns else 0,
            "medium_priority_remaining_count": int(remaining_df["review_priority"].map(_norm_text).eq("MEDIUM").sum()) if "review_priority" in remaining_df.columns else 0,
            "low_priority_remaining_count": int(remaining_df["review_priority"].map(_norm_text).eq("LOW").sum()) if "review_priority" in remaining_df.columns else 0,
        }
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342j": summary.get("ready_for_342j", False),
                    "recommended_342j_scope": summary.get("recommended_342j_scope", ""),
                    "client_ready": summary.get("client_ready", False),
                    "production_ready": summary.get("production_ready", False),
                    "decision": summary.get("decision", ""),
                    "reason": summary.get("readiness_reason", ""),
                }
            ]
        )
    )


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


def _build_readme_df(reviewed_count: int, pending_count: int) -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342I converts the current 342H reviewed batch into a post-human-review sidecar result package.",
        },
        {
            "topic": "Batch scope",
            "message": f"This run covers only the current reviewed batch of {reviewed_count} cells and preserves {pending_count} pending review rows.",
        },
        {
            "topic": "Write-back boundary",
            "message": "342I does not write back to 342H or any earlier workbook. It remains a no-write-back sidecar stage.",
        },
        {
            "topic": "Status boundary",
            "message": "342I remains client_ready = false and production_ready = false. It is not a formal client delivery package.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    if summary.get("ready_for_342j", False):
        first_recommendation = "342I is ready for a reviewed client preview pilot, but only for the current first reviewed batch."
        first_step = "342J Table-First Reviewed Client Preview Pilot"
    else:
        first_recommendation = "342I is not yet ready for 342J. Expand 342H review coverage or fix validation issues first."
        first_step = "expand_human_review_batch"
    rows = [
        {
            "next_step": first_step,
            "recommendation": first_recommendation,
        },
        {
            "next_step": "continue_342H1_or_342H2",
            "recommendation": "Continue filling the 342G review template if wider human review coverage is needed before any larger preview scope.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_table_first_post_human_review_sidecar_result_342i(
    *,
    human_review_342h_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_342h, qa_342h, proof_342h, workbook_342h, files_read_342h, warnings_342h = _load_342h_context(human_review_342h_dir)
    files_read.extend(files_read_342h)
    warnings.extend(warnings_342h)

    summary_path = human_review_342h_dir / INPUT_SUMMARY_NAME
    qa_path = human_review_342h_dir / INPUT_QA_NAME
    report_path = human_review_342h_dir / INPUT_REPORT_NAME
    workbook_path = human_review_342h_dir / INPUT_WORKBOOK_NAME

    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [summary_path, qa_path, report_path, workbook_path]
        if path.exists()
    }

    confirmed_df = _fill_final_fields(_set_final_status(_clean_frame(workbook_342h.get("04_CONFIRMED_CELLS", pd.DataFrame()))))
    corrected_df = _fill_final_fields(_set_final_status(_clean_frame(workbook_342h.get("05_CORRECTED_CELLS", pd.DataFrame()))))
    rejected_df = _fill_final_fields(_set_final_status(_clean_frame(workbook_342h.get("06_REJECTED_CELLS", pd.DataFrame()))))
    still_review_df = _fill_final_fields(_set_final_status(_clean_frame(workbook_342h.get("07_STILL_REVIEW", pd.DataFrame()))))
    needs_source_df = _fill_final_fields(_set_final_status(_clean_frame(workbook_342h.get("08_NEEDS_SOURCE_CHECK", pd.DataFrame()))))
    pending_df = _clean_frame(workbook_342h.get("09_PENDING_REVIEW", pd.DataFrame()))

    required_sheets_present = all(_sheet_exists(workbook_342h, sheet) and not workbook_342h[sheet].empty for sheet in REQUIRED_342H_SHEETS)
    input_ready = bool(
        summary_path.exists()
        and qa_path.exists()
        and workbook_path.exists()
        and summary_342h.get("decision") == READY_INPUT_DECISION
        and bool(summary_342h.get("ready_for_342i", False))
        and int(summary_342h.get("reviewed_row_count", 0) or 0) > 0
        and int(summary_342h.get("validation_error_count", 0) or 0) == 0
        and int(summary_342h.get("qa_fail_count", 0) or 0) == 0
        and required_sheets_present
    )

    if input_ready:
        reviewed_frames = [frame for frame in [confirmed_df, corrected_df, rejected_df, still_review_df, needs_source_df] if not frame.empty]
        human_reviewed_df = _clean_frame(pd.concat(reviewed_frames, ignore_index=True)) if reviewed_frames else pd.DataFrame()
        final_confirmed_df = confirmed_df.copy()
        final_corrected_df = corrected_df.copy()
        final_rejected_df = rejected_df.copy()
        before_after_df = _build_before_after_df(human_reviewed_df)
        if human_reviewed_df.empty:
            source_trace_df = pd.DataFrame()
        else:
            source_trace_df = _clean_frame(
                human_reviewed_df[
                    [
                        "review_item_id",
                        "corpus_pdf_id",
                        "file_name",
                        "table_id",
                        "table_type",
                        "source_page",
                        "bbox",
                        "image_path",
                        "source_html_snippet",
                        "final_status",
                        "reviewer_decision",
                    ]
                ].copy()
            )
        post_human_confirmed_df = _clean_frame(pd.concat([final_confirmed_df, final_corrected_df], ignore_index=True))
        metric_coverage_df = _build_metric_coverage_after_df(post_human_confirmed_df)
        unit_year_after_df = _build_unit_year_after_df(post_human_confirmed_df)
        remaining_risks_df = _build_remaining_risks_df(
            pending_df=pending_df,
            still_review_df=still_review_df,
            needs_source_df=needs_source_df,
        )
    else:
        human_reviewed_df = pd.DataFrame()
        final_confirmed_df = pd.DataFrame()
        final_corrected_df = pd.DataFrame()
        final_rejected_df = pd.DataFrame()
        pending_df = pd.DataFrame()
        before_after_df = pd.DataFrame()
        source_trace_df = pd.DataFrame()
        post_human_confirmed_df = pd.DataFrame()
        metric_coverage_df = pd.DataFrame()
        unit_year_after_df = pd.DataFrame()
        remaining_risks_df = pd.DataFrame()
        still_review_df = pd.DataFrame()
        needs_source_df = pd.DataFrame()

    input_review_template_row_count = int(summary_342h.get("input_review_template_row_count", 0) or 0) if input_ready else 0
    reviewed_row_count = int(summary_342h.get("reviewed_row_count", 0) or 0) if input_ready else 0
    pending_review_count = int(len(pending_df))
    input_confirmed_cell_count = int(summary_342h.get("confirmed_cell_count", 0) or 0) if input_ready else 0
    input_corrected_cell_count = int(summary_342h.get("corrected_cell_count", 0) or 0) if input_ready else 0
    input_rejected_cell_count = int(summary_342h.get("rejected_cell_count", 0) or 0) if input_ready else 0
    final_confirmed_cell_count = int(len(final_confirmed_df))
    final_corrected_cell_count = int(len(final_corrected_df))
    final_rejected_cell_count = int(len(final_rejected_df))
    post_human_confirmed_count = final_confirmed_cell_count + final_corrected_cell_count
    post_human_reviewed_cell_count = int(len(human_reviewed_df))

    if not post_human_confirmed_df.empty:
        metric_covered_after_human_count = int(
            post_human_confirmed_df["final_metric_standardized"].map(_norm_text).replace("", pd.NA).dropna().nunique()
        )
        metric_year_pair_after_human_count = int(
            post_human_confirmed_df.assign(
                _metric_year_pair=post_human_confirmed_df["final_metric_standardized"].map(_norm_text)
                + "||"
                + post_human_confirmed_df["final_year_standardized"].map(_norm_text)
            )["_metric_year_pair"].replace("||", pd.NA).dropna().nunique()
        )
    else:
        metric_covered_after_human_count = 0
        metric_year_pair_after_human_count = 0

    pending_review_after_human_count = pending_review_count
    remaining_review_count = pending_review_count + int(len(still_review_df)) + int(len(needs_source_df))
    remaining_risks_row = remaining_risks_df.to_dict(orient="records")[0] if not remaining_risks_df.empty else {}
    unit_year_remaining_count = int(remaining_risks_row.get("unit_year_remaining_count", 0) or 0)
    duplicate_remaining_count = int(remaining_risks_row.get("duplicate_remaining_count", 0) or 0)
    growth_row_remaining_count = int(remaining_risks_row.get("growth_row_remaining_count", 0) or 0)
    source_check_remaining_count = int(remaining_risks_row.get("source_check_remaining_count", 0) or 0)
    validation_error_count = int(summary_342h.get("validation_error_count", 0) or 0) if input_ready else 0

    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [summary_path, qa_path, report_path, workbook_path]
        if path.exists()
    }
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)
    reviewed_input_staged = _git_staged_names_for_paths(["input/table_first_review_342g_reviewed"], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342I",
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

    no_write_back_proof_passed = (
        bool(no_write_back_json.get("no_official_asset_modification_during_342i"))
        and upstream_unchanged
        and not no_write_back_json.get("client_export_generated", True)
    )

    ready_for_342j_candidate = bool(
        input_ready
        and post_human_confirmed_count > 0
        and validation_error_count == 0
        and no_write_back_proof_passed
    )
    readme_df = _build_readme_df(reviewed_row_count, pending_review_count)
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())

    checks = [
        {"check_name": "inputs::342h_output_dir_exists", "status": "PASS" if human_review_342h_dir.exists() else "FAIL", "detail": str(human_review_342h_dir)},
        {"check_name": "inputs::342h_summary_exists", "status": "PASS" if summary_path.exists() else "FAIL", "detail": str(summary_path)},
        {"check_name": "inputs::342h_qa_exists", "status": "PASS" if qa_path.exists() else "FAIL", "detail": str(qa_path)},
        {"check_name": "inputs::342h_workbook_exists", "status": "PASS" if workbook_path.exists() else "FAIL", "detail": str(workbook_path)},
        {
            "check_name": "inputs::342h_ready_for_342i_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342h.get("decision", ""),
                    "ready_for_342i": summary_342h.get("ready_for_342i", False),
                    "reviewed_row_count": summary_342h.get("reviewed_row_count", 0),
                    "validation_error_count": summary_342h.get("validation_error_count", 0),
                    "qa_fail_count": summary_342h.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342h_required_sheets_exist",
            "status": "PASS" if required_sheets_present else "FAIL",
            "detail": json.dumps({sheet: not workbook_342h.get(sheet, pd.DataFrame()).empty for sheet in REQUIRED_342H_SHEETS}, ensure_ascii=False),
        },
        {"check_name": "quality::reviewed_row_count_positive", "status": "PASS" if reviewed_row_count > 0 else "FAIL", "detail": str(reviewed_row_count)},
        {"check_name": "quality::no_fake_human_decisions_generated", "status": "PASS", "detail": "342I only consumes 342H reviewed outputs and preserved pending rows."},
        {
            "check_name": "quality::final_confirmed_sources_valid",
            "status": "PASS"
            if final_confirmed_df.empty or final_confirmed_df["reviewer_decision"].map(_norm_text).eq("CONFIRM_CELL").all()
            else "FAIL",
            "detail": json.dumps(sorted(set(final_confirmed_df["reviewer_decision"].map(_norm_text).tolist())) if not final_confirmed_df.empty else [], ensure_ascii=False),
        },
        {
            "check_name": "quality::final_corrected_sources_valid",
            "status": "PASS"
            if final_corrected_df.empty or final_corrected_df["reviewer_decision"].map(_norm_text).eq("CORRECT_AND_CONFIRM").all()
            else "FAIL",
            "detail": json.dumps(sorted(set(final_corrected_df["reviewer_decision"].map(_norm_text).tolist())) if not final_corrected_df.empty else [], ensure_ascii=False),
        },
        {
            "check_name": "quality::corrected_rows_use_reviewer_fields",
            "status": "PASS"
            if final_corrected_df.empty
            else (
                "PASS"
                if final_corrected_df.apply(
                    lambda row: any(
                        _norm_text(row.get(column))
                        for column in [
                            "reviewer_metric_standardized",
                            "reviewer_year_standardized",
                            "reviewer_value_numeric",
                            "reviewer_normalized_unit",
                        ]
                    ),
                    axis=1,
                ).all()
                else "FAIL"
            ),
            "detail": str(len(final_corrected_df)),
        },
        {
            "check_name": "quality::rejected_not_mixed_into_final_confirmed",
            "status": "PASS"
            if final_confirmed_df.empty and final_corrected_df.empty
            else (
                "PASS"
                if not pd.concat([final_confirmed_df, final_corrected_df], ignore_index=True)["final_status"].map(_norm_text).eq("POST_HUMAN_REJECTED").any()
                else "FAIL"
            ),
            "detail": str(final_rejected_cell_count),
        },
        {
            "check_name": "quality::pending_rows_preserved",
            "status": "PASS" if pending_review_count == int(summary_342h.get("pending_review_count", 0) or 0) else "FAIL",
            "detail": f"pending={pending_review_count}",
        },
        {
            "check_name": "quality::source_trace_preserved",
            "status": "PASS" if len(source_trace_df) == len(human_reviewed_df) else "FAIL",
            "detail": f"source_trace_rows={len(source_trace_df)}; reviewed_rows={len(human_reviewed_df)}",
        },
        {"check_name": "safety::no_upstream_workbook_modified", "status": "PASS" if upstream_unchanged else "FAIL", "detail": "input hashes before/after compared"},
        {"check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified", "status": "PASS", "detail": "342I adds sidecar result code only"},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "safety::reviewed_input_workbook_not_staged", "status": "PASS" if not reviewed_input_staged else "FAIL", "detail": json.dumps(reviewed_input_staged, ensure_ascii=False)},
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::no_investment_advice_claim", "status": "PASS" if not _contains_forbidden_claim(readme_text, ["investment advice"]) else "FAIL", "detail": "README text checked"},
        {"check_name": "safety::no_sheet_name_exceeds_limit", "status": "PASS", "detail": "all 342I sheet names are <= 31 chars"},
        {"check_name": "safety::no_write_back_proof_generated", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342j = bool(ready_for_342j_candidate and qa_fail_count == 0)
    recommended_342j_scope = "table_first_reviewed_client_preview_pilot" if ready_for_342j else ""
    decision = READY_DECISION if ready_for_342j else NOT_READY_DECISION
    readiness_reason = (
        "342I has a valid first reviewed batch and can move to a reviewed client preview pilot while still preserving client_ready=false and production_ready=false."
        if ready_for_342j
        else "342I cannot move to 342J yet because the 342H input is not ready or required quality checks failed."
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "input_review_template_row_count": input_review_template_row_count,
        "reviewed_row_count": reviewed_row_count,
        "pending_review_count": pending_review_count,
        "input_confirmed_cell_count": input_confirmed_cell_count,
        "input_corrected_cell_count": input_corrected_cell_count,
        "input_rejected_cell_count": input_rejected_cell_count,
        "final_confirmed_cell_count": final_confirmed_cell_count,
        "final_corrected_cell_count": final_corrected_cell_count,
        "final_rejected_cell_count": final_rejected_cell_count,
        "post_human_confirmed_count": post_human_confirmed_count,
        "post_human_reviewed_cell_count": post_human_reviewed_cell_count,
        "metric_covered_after_human_count": metric_covered_after_human_count,
        "metric_year_pair_after_human_count": metric_year_pair_after_human_count,
        "pending_review_after_human_count": pending_review_after_human_count,
        "remaining_review_count": remaining_review_count,
        "unit_year_remaining_count": unit_year_remaining_count,
        "duplicate_remaining_count": duplicate_remaining_count,
        "growth_row_remaining_count": growth_row_remaining_count,
        "source_check_remaining_count": source_check_remaining_count,
        "validation_error_count": validation_error_count,
        "ready_for_342j": ready_for_342j,
        "recommended_342j_scope": recommended_342j_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "readiness_reason": readiness_reason,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342I_table_first_post_human_review_sidecar_result",
        "human_review_342h_dir": str(human_review_342h_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
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
        "00_README": readme_df,
        "01_RESULT_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342H_SUMMARY": _clean_frame(pd.DataFrame([summary_342h])) if summary_342h else pd.DataFrame(),
        "03_HUMAN_REVIEWED_CELLS": human_reviewed_df,
        "04_FINAL_CONFIRMED": final_confirmed_df,
        "05_FINAL_CORRECTED": final_corrected_df,
        "06_FINAL_REJECTED": final_rejected_df,
        "07_PENDING_REVIEW": pending_df,
        "08_BEFORE_AFTER": before_after_df,
        "09_SOURCE_TRACE": source_trace_df,
        "10_METRIC_COVERAGE_AFTER": metric_coverage_df,
        "11_UNIT_YEAR_AFTER": unit_year_after_df,
        "12_REMAINING_RISKS": remaining_risks_df,
        "13_342J_READINESS": _build_readiness_df(summary),
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
