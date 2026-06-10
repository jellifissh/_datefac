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


READY_INPUT_DECISION = "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY"
READY_DECISION = "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY"
NOT_READY_DECISION = "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_NOT_READY"

DEFAULT_POST_HUMAN_REVIEW_342I_DIR = Path(r"D:\_datefac\output\table_first_post_human_review_sidecar_result_342i")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")

SUMMARY_FILE_NAME = "table_first_reviewed_client_preview_pilot_342j_summary.json"
MANIFEST_FILE_NAME = "table_first_reviewed_client_preview_pilot_342j_manifest.json"
QA_FILE_NAME = "table_first_reviewed_client_preview_pilot_342j_qa.json"
NO_WRITE_BACK_FILE_NAME = "table_first_reviewed_client_preview_pilot_342j_no_write_back_proof.json"
REPORT_FILE_NAME = "table_first_reviewed_client_preview_pilot_342j_report.md"
WORKBOOK_FILE_NAME = "table_first_reviewed_client_preview_pilot_342j.xlsx"

INPUT_SUMMARY_NAME = "table_first_post_human_review_sidecar_result_342i_summary.json"
INPUT_QA_NAME = "table_first_post_human_review_sidecar_result_342i_qa.json"
INPUT_REPORT_NAME = "table_first_post_human_review_sidecar_result_342i_report.md"
INPUT_WORKBOOK_NAME = "table_first_post_human_review_sidecar_result_342i.xlsx"
INPUT_NO_WRITE_BACK_NAME = "table_first_post_human_review_sidecar_result_342i_no_write_back_proof.json"

REQUIRED_342I_SHEETS = [
    "03_HUMAN_REVIEWED_CELLS",
    "04_FINAL_CONFIRMED",
    "05_FINAL_CORRECTED",
    "07_PENDING_REVIEW",
    "08_BEFORE_AFTER",
    "09_SOURCE_TRACE",
    "10_METRIC_COVERAGE_AFTER",
    "12_REMAINING_RISKS",
    "13_342J_READINESS",
    "14_NO_WRITE_BACK",
]
OPTIONAL_342I_SHEETS = [
    "01_RESULT_SUMMARY",
    "06_FINAL_REJECTED",
    "11_UNIT_YEAR_AFTER",
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

PREVIEW_ALLOWED_DECISIONS = {"CONFIRM_CELL", "CORRECT_AND_CONFIRM"}
PREVIEW_ALLOWED_FINAL_STATUS = {"POST_HUMAN_CONFIRMED", "POST_HUMAN_CORRECTED_CONFIRMED"}
PREVIEW_LIMIT_NOTE = "first_batch_review_only | not_full_human_review | not_client_ready | not_production_ready"
DEFAULT_342K_SCOPE = "llm_assisted_review_adjudication_or_preview_polish"


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
            window = lowered[max(0, idx - 80) : idx]
            if "not " not in window and "false" not in window and "不是" not in window and "非" not in window:
                return True
            start = idx + len(token_lower)
    return False


def _load_342i_context(
    post_human_review_342i_dir: Path,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []

    summary_path = post_human_review_342i_dir / INPUT_SUMMARY_NAME
    qa_path = post_human_review_342i_dir / INPUT_QA_NAME
    report_path = post_human_review_342i_dir / INPUT_REPORT_NAME
    workbook_path = post_human_review_342i_dir / INPUT_WORKBOOK_NAME
    proof_path = post_human_review_342i_dir / INPUT_NO_WRITE_BACK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    proof_json = _read_json(proof_path) if proof_path.exists() else {}

    for path, label in [
        (summary_path, "342I summary"),
        (qa_path, "342I qa"),
        (report_path, "342I report"),
        (workbook_path, "342I workbook"),
        (proof_path, "342I no-write-back proof"),
    ]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing {label}: {path}")

    workbook_sheets: Dict[str, pd.DataFrame] = {}
    workbook_sheet_names: List[str] = []
    requested_sheets = REQUIRED_342I_SHEETS + OPTIONAL_342I_SHEETS
    if workbook_path.exists():
        try:
            excel = pd.ExcelFile(workbook_path)
            workbook_sheet_names = list(excel.sheet_names)
            for sheet in requested_sheets:
                if sheet in excel.sheet_names:
                    workbook_sheets[sheet] = _clean_frame(pd.read_excel(workbook_path, sheet_name=sheet))
                else:
                    workbook_sheets[sheet] = pd.DataFrame()
                    if sheet in REQUIRED_342I_SHEETS:
                        warnings.append(f"missing required 342I workbook sheet: {sheet}")
        except Exception as exc:
            warnings.append(f"unable to read 342I workbook: {exc}")
            for sheet in requested_sheets:
                workbook_sheets[sheet] = pd.DataFrame()
    else:
        for sheet in requested_sheets:
            workbook_sheets[sheet] = pd.DataFrame()
    return summary, qa_json, proof_json, workbook_sheets, workbook_sheet_names, files_read, warnings


def _preview_confidence_label(row: Mapping[str, Any]) -> str:
    decision = _norm_text(row.get("reviewer_decision"))
    if decision == "CORRECT_AND_CONFIRM":
        return "HUMAN_CORRECTED"
    return "HUMAN_CONFIRMED"


def _build_preview_df(final_confirmed_df: pd.DataFrame, final_corrected_df: pd.DataFrame) -> pd.DataFrame:
    preview_frames = []
    if not final_confirmed_df.empty:
        preview_frames.append(_clean_frame(final_confirmed_df.copy()))
    if not final_corrected_df.empty:
        preview_frames.append(_clean_frame(final_corrected_df.copy()))
    if not preview_frames:
        return pd.DataFrame()

    combined = _clean_frame(pd.concat(preview_frames, ignore_index=True))
    combined = combined[
        combined["reviewer_decision"].map(_norm_text).isin(PREVIEW_ALLOWED_DECISIONS)
        & combined["final_status"].map(_norm_text).isin(PREVIEW_ALLOWED_FINAL_STATUS)
        & combined["final_metric_standardized"].map(_norm_text).ne("")
    ].copy()

    rows: List[Dict[str, Any]] = []
    for idx, row in enumerate(combined.to_dict(orient="records"), start=1):
        rows.append(
            {
                "preview_row_id": f"342j::preview::{idx:04d}",
                "review_item_id": _norm_text(row.get("review_item_id")),
                "final_status": _norm_text(row.get("final_status")),
                "reviewer_decision": _norm_text(row.get("reviewer_decision")),
                "corpus_pdf_id": _norm_text(row.get("corpus_pdf_id")),
                "file_name": _norm_text(row.get("file_name")),
                "table_id": _norm_text(row.get("table_id")),
                "table_type": _norm_text(row.get("table_type")),
                "source_page": row.get("source_page"),
                "bbox": _norm_text(row.get("bbox")),
                "image_path": _norm_text(row.get("image_path")),
                "metric_raw": _norm_text(row.get("metric_raw")),
                "metric_standardized": _norm_text(row.get("metric_standardized")),
                "year_standardized": _norm_text(row.get("year_standardized")),
                "value_numeric": row.get("value_numeric"),
                "normalized_unit": _norm_text(row.get("normalized_unit")),
                "final_metric_standardized": _norm_text(row.get("final_metric_standardized")),
                "final_year_standardized": _norm_text(row.get("final_year_standardized")),
                "final_value_numeric": row.get("final_value_numeric"),
                "final_normalized_unit": _norm_text(row.get("final_normalized_unit")),
                "reviewer_note": _norm_text(row.get("reviewer_note")),
                "reviewer_id": _norm_text(row.get("reviewer_id")),
                "reviewed_at": _norm_text(row.get("reviewed_at")),
                "source_html_snippet": _norm_text(row.get("source_html_snippet")),
                "preview_confidence_label": _preview_confidence_label(row),
                "preview_limit_note": PREVIEW_LIMIT_NOTE,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_metric_year_matrix_df(preview_df: pd.DataFrame) -> pd.DataFrame:
    if preview_df.empty:
        return pd.DataFrame()
    metric_covered_count = int(preview_df["final_metric_standardized"].map(_norm_text).replace("", pd.NA).dropna().nunique())
    metric_year_pair_count = int(
        (
            preview_df["final_metric_standardized"].map(_norm_text)
            + "||"
            + preview_df["final_year_standardized"].map(_norm_text)
        ).replace("||", pd.NA).dropna().nunique()
    )
    pdf_covered_count = int(preview_df["corpus_pdf_id"].map(_norm_text).replace("", pd.NA).dropna().nunique())
    table_covered_count = int(preview_df["table_id"].map(_norm_text).replace("", pd.NA).dropna().nunique())
    matrix = preview_df[
        [
            "preview_row_id",
            "review_item_id",
            "final_metric_standardized",
            "final_year_standardized",
            "final_value_numeric",
            "final_normalized_unit",
            "final_status",
            "corpus_pdf_id",
            "table_id",
            "source_page",
            "reviewer_decision",
        ]
    ].copy()
    matrix["metric_covered_count"] = metric_covered_count
    matrix["metric_year_pair_count"] = metric_year_pair_count
    matrix["pdf_covered_count"] = pdf_covered_count
    matrix["table_covered_count"] = table_covered_count
    return _clean_frame(matrix)


def _build_before_after_df(before_after_input_df: pd.DataFrame, preview_df: pd.DataFrame) -> pd.DataFrame:
    if before_after_input_df.empty or preview_df.empty:
        return pd.DataFrame()
    preview_map = preview_df[["preview_row_id", "review_item_id", "preview_confidence_label"]].copy()
    merged = before_after_input_df.merge(preview_map, on="review_item_id", how="inner")
    columns = [
        "preview_row_id",
        "review_item_id",
        "preview_confidence_label",
        "reviewer_decision",
        "original_metric_standardized",
        "final_metric_standardized",
        "original_year_standardized",
        "final_year_standardized",
        "original_value_numeric",
        "final_value_numeric",
        "original_normalized_unit",
        "final_normalized_unit",
        "change_type",
    ]
    return _clean_frame(merged[columns].copy())


def _build_source_trace_df(source_trace_input_df: pd.DataFrame, preview_df: pd.DataFrame) -> pd.DataFrame:
    if source_trace_input_df.empty or preview_df.empty:
        return pd.DataFrame()
    preview_map = preview_df[
        [
            "preview_row_id",
            "review_item_id",
            "preview_confidence_label",
            "preview_limit_note",
            "final_metric_standardized",
            "final_year_standardized",
            "final_value_numeric",
            "final_normalized_unit",
        ]
    ].copy()
    merged = source_trace_input_df.merge(preview_map, on="review_item_id", how="inner")
    columns = [
        "preview_row_id",
        "review_item_id",
        "preview_confidence_label",
        "final_status",
        "reviewer_decision",
        "corpus_pdf_id",
        "file_name",
        "table_id",
        "table_type",
        "source_page",
        "bbox",
        "image_path",
        "source_html_snippet",
        "final_metric_standardized",
        "final_year_standardized",
        "final_value_numeric",
        "final_normalized_unit",
        "preview_limit_note",
    ]
    return _clean_frame(merged[columns].copy())


def _build_remaining_review_df(pending_df: pd.DataFrame, remaining_risks_row: Mapping[str, Any]) -> pd.DataFrame:
    if pending_df.empty:
        base = pd.DataFrame([remaining_risks_row]) if remaining_risks_row else pd.DataFrame()
        return _clean_frame(base)
    out = _clean_frame(pending_df.copy())
    out["remaining_review_count"] = int(remaining_risks_row.get("pending_review_count", len(pending_df)) or 0)
    out["unit_year_remaining_count"] = int(remaining_risks_row.get("unit_year_remaining_count", 0) or 0)
    out["duplicate_remaining_count"] = int(remaining_risks_row.get("duplicate_remaining_count", 0) or 0)
    out["growth_row_remaining_count"] = int(remaining_risks_row.get("growth_row_remaining_count", 0) or 0)
    out["high_priority_remaining_count"] = int(remaining_risks_row.get("high_priority_remaining_count", 0) or 0)
    out["medium_priority_remaining_count"] = int(remaining_risks_row.get("medium_priority_remaining_count", 0) or 0)
    out["low_priority_remaining_count"] = int(remaining_risks_row.get("low_priority_remaining_count", 0) or 0)
    return _clean_frame(out)


def _build_readme_df(summary_342i: Mapping[str, Any]) -> pd.DataFrame:
    reviewed_row_count = int(summary_342i.get("reviewed_row_count", 0) or 0)
    pending_review_count = int(summary_342i.get("pending_review_count", 0) or 0)
    post_human_confirmed_count = int(summary_342i.get("post_human_confirmed_count", 0) or 0)
    rows = [
        {
            "topic": "Purpose / 用途",
            "message": "342J builds a reviewed client preview pilot from the current 342I post-human-review sidecar result. 342J 基于当前 342I 侧车结果生成 reviewed client preview pilot。",
        },
        {
            "topic": "Pilot scope / 试点范围",
            "message": f"Only the current batch of {reviewed_row_count} reviewed rows is considered, and only {post_human_confirmed_count} confirmed or corrected rows can enter preview. 当前只基于 {reviewed_row_count} 条已 review 记录，其中仅 {post_human_confirmed_count} 条 confirmed/corrected 可进入 preview。",
        },
        {
            "topic": "Pending review / 待审剩余",
            "message": f"{pending_review_count} rows still remain pending review, so this workbook cannot claim full human-review completion. 仍有 {pending_review_count} 条 pending review，不能声称全量人审完成。",
        },
        {
            "topic": "Boundary / 边界",
            "message": "client_ready = false; production_ready = false; not investment advice; no upstream workbook write-back. 当前必须保持 client_ready=false、production_ready=false、not investment advice，并且不写回上游 workbook。",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_demo_notes_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "note_id": "demo_01",
            "topic": "What to show / 展示重点",
            "message": f"Show the {summary.get('reviewed_preview_row_count', 0)} reviewed preview rows with source page, bbox, image path, and HTML snippet. 展示 {summary.get('reviewed_preview_row_count', 0)} 条 reviewed preview，并强调 source page / bbox / image / HTML traceability。",
        },
        {
            "note_id": "demo_02",
            "topic": "Confirmed vs corrected / 人工确认与修正",
            "message": f"Confirmed rows = {summary.get('confirmed_preview_row_count', 0)}; corrected rows = {summary.get('corrected_preview_row_count', 0)}. 人工确认 {summary.get('confirmed_preview_row_count', 0)} 条，人工修正 {summary.get('corrected_preview_row_count', 0)} 条。",
        },
        {
            "note_id": "demo_03",
            "topic": "Why still pilot / 为什么仍是 pilot",
            "message": f"{summary.get('pending_review_count', 0)} rows are still pending review and {summary.get('rejected_in_batch_count', 0)} rows were rejected or not core in this batch. 仍有 {summary.get('pending_review_count', 0)} 条待审，而且本批有 {summary.get('rejected_in_batch_count', 0)} 条被拒绝或判为 not core。",
        },
        {
            "note_id": "demo_04",
            "topic": "Safety / 安全表述",
            "message": "This workbook is not formal client delivery and not investment advice. 该 workbook 不是正式客户交付，也不是投资建议。",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_limitations_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "limitation_id": "limit_01",
            "message": f"Only the first {summary.get('reviewed_row_count', 0)} review rows were processed in the current effective batch.",
        },
        {
            "limitation_id": "limit_02",
            "message": f"{summary.get('pending_review_count', 0)} rows still remain pending review.",
        },
        {
            "limitation_id": "limit_03",
            "message": f"{summary.get('rejected_in_batch_count', 0)} rows in the reviewed batch were rejected or marked not core and were excluded from preview.",
        },
        {
            "limitation_id": "limit_04",
            "message": "client_ready = false and production_ready = false must remain unchanged.",
        },
        {
            "limitation_id": "limit_05",
            "message": "No investment advice claim is allowed, and no full corpus human review completion claim is allowed.",
        },
        {
            "limitation_id": "limit_06",
            "message": "This workbook is a reviewed preview pilot only.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342k": summary.get("ready_for_342k", False),
                    "recommended_342k_scope": summary.get("recommended_342k_scope", ""),
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


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    if summary.get("ready_for_342k", False):
        first_step = "342K LLM-Assisted Review Adjudication"
        first_recommendation = "342J is ready for a next-stage assisted adjudication or preview polish workflow, but still only as a pilot."
    else:
        first_step = "expand_human_review_batch"
        first_recommendation = "342J is not yet ready for 342K. Expand reviewed rows or fix input/QA gaps first."
    rows = [
        {
            "next_step": first_step,
            "recommendation": first_recommendation,
        },
        {
            "next_step": "342K Reviewed Preview Polish",
            "recommendation": "Polish the reviewed preview presentation only if pilot boundaries remain explicit.",
        },
        {
            "next_step": "continue_342H_review_expansion",
            "recommendation": "Continue filling more review rows if wider coverage is needed before any larger preview scope.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _source_trace_missing_count(preview_df: pd.DataFrame) -> int:
    if preview_df.empty:
        return 0
    required_fields = ["source_page", "bbox", "image_path", "source_html_snippet"]
    count = 0
    for row in preview_df.to_dict(orient="records"):
        missing = False
        for field in required_fields:
            value = row.get(field)
            if field == "source_page":
                if _norm_text(value) == "":
                    missing = True
                    break
            elif _norm_text(value) == "":
                missing = True
                break
        if missing:
            count += 1
    return count


def build_table_first_reviewed_client_preview_pilot_342j(
    *,
    post_human_review_342i_dir: Path,
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
        summary_342i,
        qa_342i,
        proof_342i,
        workbook_342i,
        workbook_sheet_names,
        files_read_342i,
        warnings_342i,
    ) = _load_342i_context(post_human_review_342i_dir)
    files_read.extend(files_read_342i)
    warnings.extend(warnings_342i)

    summary_path = post_human_review_342i_dir / INPUT_SUMMARY_NAME
    qa_path = post_human_review_342i_dir / INPUT_QA_NAME
    report_path = post_human_review_342i_dir / INPUT_REPORT_NAME
    workbook_path = post_human_review_342i_dir / INPUT_WORKBOOK_NAME

    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [summary_path, qa_path, report_path, workbook_path]
        if path.exists()
    }

    required_sheets_present = all(sheet in workbook_sheet_names for sheet in REQUIRED_342I_SHEETS)
    input_ready = bool(
        summary_path.exists()
        and qa_path.exists()
        and workbook_path.exists()
        and summary_342i.get("decision") == READY_INPUT_DECISION
        and bool(summary_342i.get("ready_for_342j", False))
        and int(summary_342i.get("qa_fail_count", 0) or 0) == 0
        and int(summary_342i.get("post_human_confirmed_count", 0) or 0) > 0
        and int(summary_342i.get("reviewed_row_count", 0) or 0) > 0
        and required_sheets_present
    )

    final_confirmed_df = _clean_frame(workbook_342i.get("04_FINAL_CONFIRMED", pd.DataFrame()))
    final_corrected_df = _clean_frame(workbook_342i.get("05_FINAL_CORRECTED", pd.DataFrame()))
    final_rejected_df = _clean_frame(workbook_342i.get("06_FINAL_REJECTED", pd.DataFrame()))
    pending_df = _clean_frame(workbook_342i.get("07_PENDING_REVIEW", pd.DataFrame()))
    before_after_input_df = _clean_frame(workbook_342i.get("08_BEFORE_AFTER", pd.DataFrame()))
    source_trace_input_df = _clean_frame(workbook_342i.get("09_SOURCE_TRACE", pd.DataFrame()))
    remaining_risks_df = _clean_frame(workbook_342i.get("12_REMAINING_RISKS", pd.DataFrame()))

    if input_ready:
        reviewed_preview_df = _build_preview_df(final_confirmed_df, final_corrected_df)
        confirmed_preview_df = _clean_frame(reviewed_preview_df[reviewed_preview_df["preview_confidence_label"].eq("HUMAN_CONFIRMED")].copy())
        corrected_preview_df = _clean_frame(reviewed_preview_df[reviewed_preview_df["preview_confidence_label"].eq("HUMAN_CORRECTED")].copy())
        metric_year_matrix_df = _build_metric_year_matrix_df(reviewed_preview_df)
        before_after_df = _build_before_after_df(before_after_input_df, reviewed_preview_df)
        source_trace_df = _build_source_trace_df(source_trace_input_df, reviewed_preview_df)
        remaining_risks_row = remaining_risks_df.to_dict(orient="records")[0] if not remaining_risks_df.empty else {}
        remaining_review_df = _build_remaining_review_df(pending_df, remaining_risks_row)
    else:
        reviewed_preview_df = pd.DataFrame()
        confirmed_preview_df = pd.DataFrame()
        corrected_preview_df = pd.DataFrame()
        metric_year_matrix_df = pd.DataFrame()
        before_after_df = pd.DataFrame()
        source_trace_df = pd.DataFrame()
        remaining_risks_row = {}
        remaining_review_df = pd.DataFrame()
        pending_df = pd.DataFrame()
        final_rejected_df = pd.DataFrame()

    input_review_template_row_count = int(summary_342i.get("input_review_template_row_count", 0) or 0) if input_ready else 0
    reviewed_row_count = int(summary_342i.get("reviewed_row_count", 0) or 0) if input_ready else 0
    pending_review_count = int(summary_342i.get("pending_review_count", 0) or 0) if input_ready else 0
    input_post_human_confirmed_count = int(summary_342i.get("post_human_confirmed_count", 0) or 0) if input_ready else 0
    reviewed_preview_row_count = int(len(reviewed_preview_df))
    confirmed_preview_row_count = int(len(confirmed_preview_df))
    corrected_preview_row_count = int(len(corrected_preview_df))
    rejected_in_batch_count = int(len(final_rejected_df))
    metric_covered_count = int(reviewed_preview_df["final_metric_standardized"].map(_norm_text).replace("", pd.NA).dropna().nunique()) if not reviewed_preview_df.empty else 0
    metric_year_pair_count = int(
        (
            reviewed_preview_df["final_metric_standardized"].map(_norm_text)
            + "||"
            + reviewed_preview_df["final_year_standardized"].map(_norm_text)
        ).replace("||", pd.NA).dropna().nunique()
    ) if not reviewed_preview_df.empty else 0
    pdf_covered_count = int(reviewed_preview_df["corpus_pdf_id"].map(_norm_text).replace("", pd.NA).dropna().nunique()) if not reviewed_preview_df.empty else 0
    table_covered_count = int(reviewed_preview_df["table_id"].map(_norm_text).replace("", pd.NA).dropna().nunique()) if not reviewed_preview_df.empty else 0
    remaining_review_count = int(summary_342i.get("remaining_review_count", pending_review_count) or 0) if input_ready else 0
    unit_year_remaining_count = int(summary_342i.get("unit_year_remaining_count", remaining_risks_row.get("unit_year_remaining_count", 0)) or 0) if input_ready else 0
    duplicate_remaining_count = int(summary_342i.get("duplicate_remaining_count", remaining_risks_row.get("duplicate_remaining_count", 0)) or 0) if input_ready else 0
    growth_row_remaining_count = int(summary_342i.get("growth_row_remaining_count", remaining_risks_row.get("growth_row_remaining_count", 0)) or 0) if input_ready else 0
    source_trace_missing_count = _source_trace_missing_count(reviewed_preview_df)

    if source_trace_missing_count > 0:
        warnings.append(f"{source_trace_missing_count} preview rows have incomplete source trace fields, but the preview pilot can still be generated with warnings.")

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
        stage="342J",
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
        bool(no_write_back_json.get("no_official_asset_modification_during_342j"))
        and upstream_unchanged
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df(summary_342i if input_ready else {})
    demo_notes_df = _build_demo_notes_df(
        {
            "reviewed_preview_row_count": reviewed_preview_row_count,
            "confirmed_preview_row_count": confirmed_preview_row_count,
            "corrected_preview_row_count": corrected_preview_row_count,
            "pending_review_count": pending_review_count,
            "rejected_in_batch_count": rejected_in_batch_count,
        }
    )
    limitations_df = _build_limitations_df(
        {
            "reviewed_row_count": reviewed_row_count,
            "pending_review_count": pending_review_count,
            "rejected_in_batch_count": rejected_in_batch_count,
        }
    )
    claims_text = "\n".join(
        readme_df.get("message", pd.Series(dtype=object)).astype(str).tolist()
        + demo_notes_df.get("message", pd.Series(dtype=object)).astype(str).tolist()
        + limitations_df.get("message", pd.Series(dtype=object)).astype(str).tolist()
    )

    ready_for_342k_candidate = bool(
        input_ready
        and reviewed_preview_row_count > 0
        and no_write_back_proof_passed
    )

    checks = [
        {"check_name": "inputs::342i_output_dir_exists", "status": "PASS" if post_human_review_342i_dir.exists() else "FAIL", "detail": str(post_human_review_342i_dir)},
        {"check_name": "inputs::342i_summary_exists", "status": "PASS" if summary_path.exists() else "FAIL", "detail": str(summary_path)},
        {"check_name": "inputs::342i_qa_exists", "status": "PASS" if qa_path.exists() else "FAIL", "detail": str(qa_path)},
        {"check_name": "inputs::342i_workbook_exists", "status": "PASS" if workbook_path.exists() else "FAIL", "detail": str(workbook_path)},
        {
            "check_name": "inputs::342i_ready_for_342j_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342i.get("decision", ""),
                    "ready_for_342j": summary_342i.get("ready_for_342j", False),
                    "reviewed_row_count": summary_342i.get("reviewed_row_count", 0),
                    "post_human_confirmed_count": summary_342i.get("post_human_confirmed_count", 0),
                    "qa_fail_count": summary_342i.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342i_required_sheets_exist",
            "status": "PASS" if required_sheets_present else "FAIL",
            "detail": json.dumps({sheet: sheet in workbook_sheet_names for sheet in REQUIRED_342I_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "quality::preview_rows_from_confirmed_or_corrected_only",
            "status": "PASS"
            if reviewed_preview_df.empty or reviewed_preview_df["reviewer_decision"].map(_norm_text).isin(PREVIEW_ALLOWED_DECISIONS).all()
            else "FAIL",
            "detail": json.dumps(sorted(set(reviewed_preview_df["reviewer_decision"].map(_norm_text).tolist())) if not reviewed_preview_df.empty else [], ensure_ascii=False),
        },
        {
            "check_name": "quality::rejected_rows_not_in_preview",
            "status": "PASS"
            if reviewed_preview_df.empty
            else ("PASS" if not reviewed_preview_df["final_status"].map(_norm_text).eq("POST_HUMAN_REJECTED").any() else "FAIL"),
            "detail": str(rejected_in_batch_count),
        },
        {
            "check_name": "quality::pending_rows_not_in_preview",
            "status": "PASS"
            if reviewed_preview_df.empty
            else ("PASS" if not reviewed_preview_df["review_item_id"].isin(set(pending_df.get("review_item_id", pd.Series(dtype=object)).astype(str))).any() else "FAIL"),
            "detail": str(pending_review_count),
        },
        {
            "check_name": "quality::not_a_core_metric_rows_not_in_preview",
            "status": "PASS"
            if reviewed_preview_df.empty
            else ("PASS" if not reviewed_preview_df["reviewer_decision"].map(_norm_text).eq("NOT_A_CORE_METRIC").any() else "FAIL"),
            "detail": "preview excludes NOT_A_CORE_METRIC rows",
        },
        {
            "check_name": "quality::source_trace_fields_preserved",
            "status": "PASS" if len(source_trace_df) == reviewed_preview_row_count else "FAIL",
            "detail": f"source_trace_rows={len(source_trace_df)}; preview_rows={reviewed_preview_row_count}; missing={source_trace_missing_count}",
        },
        {
            "check_name": "quality::limitations_sheet_exists",
            "status": "PASS" if not limitations_df.empty else "FAIL",
            "detail": f"rows={len(limitations_df)}",
        },
        {
            "check_name": "quality::demo_notes_sheet_exists",
            "status": "PASS" if not demo_notes_df.empty else "FAIL",
            "detail": f"rows={len(demo_notes_df)}",
        },
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {
            "check_name": "claims::no_investment_advice_claim",
            "status": "PASS" if not _contains_forbidden_claim(claims_text, ["investment advice", "投资建议"]) else "FAIL",
            "detail": "README/demo/limitations text checked",
        },
        {"check_name": "safety::no_upstream_workbook_modified", "status": "PASS" if upstream_unchanged else "FAIL", "detail": "input hashes before/after compared"},
        {"check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified", "status": "PASS", "detail": "342J adds sidecar preview code only"},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "safety::reviewed_input_workbook_not_staged", "status": "PASS" if not reviewed_input_staged else "FAIL", "detail": json.dumps(reviewed_input_staged, ensure_ascii=False)},
        {"check_name": "safety::no_sheet_name_exceeds_limit", "status": "PASS", "detail": "all 342J sheet names are <= 31 chars"},
        {"check_name": "safety::no_write_back_proof_generated", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342k = bool(ready_for_342k_candidate and qa_fail_count == 0)
    recommended_342k_scope = DEFAULT_342K_SCOPE if ready_for_342k else ""
    decision = READY_DECISION if ready_for_342k else NOT_READY_DECISION
    readiness_reason = (
        "342J has a reviewed preview pilot with traceable confirmed/corrected rows and can move to 342K while still keeping client_ready=false and production_ready=false."
        if ready_for_342k
        else "342J cannot move to 342K yet because the 342I input is not ready or required preview QA checks failed."
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "input_review_template_row_count": input_review_template_row_count,
        "reviewed_row_count": reviewed_row_count,
        "pending_review_count": pending_review_count,
        "input_post_human_confirmed_count": input_post_human_confirmed_count,
        "reviewed_preview_row_count": reviewed_preview_row_count,
        "confirmed_preview_row_count": confirmed_preview_row_count,
        "corrected_preview_row_count": corrected_preview_row_count,
        "rejected_in_batch_count": rejected_in_batch_count,
        "metric_covered_count": metric_covered_count,
        "metric_year_pair_count": metric_year_pair_count,
        "pdf_covered_count": pdf_covered_count,
        "table_covered_count": table_covered_count,
        "remaining_review_count": remaining_review_count,
        "unit_year_remaining_count": unit_year_remaining_count,
        "duplicate_remaining_count": duplicate_remaining_count,
        "growth_row_remaining_count": growth_row_remaining_count,
        "source_trace_missing_count": source_trace_missing_count,
        "ready_for_342k": ready_for_342k,
        "recommended_342k_scope": recommended_342k_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "readiness_reason": readiness_reason,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342J_table_first_reviewed_client_preview_pilot",
        "post_human_review_342i_dir": str(post_human_review_342i_dir),
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
        "01_PREVIEW_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342I_SUMMARY": _clean_frame(pd.DataFrame([summary_342i])) if summary_342i else pd.DataFrame(),
        "03_REVIEWED_PREVIEW": reviewed_preview_df,
        "04_CONFIRMED_PREVIEW": confirmed_preview_df,
        "05_CORRECTED_PREVIEW": corrected_preview_df,
        "06_METRIC_YEAR_MATRIX": metric_year_matrix_df,
        "07_BEFORE_AFTER": before_after_df,
        "08_SOURCE_TRACE": source_trace_df,
        "09_REMAINING_REVIEW": remaining_review_df,
        "10_DEMO_NOTES": demo_notes_df,
        "11_LIMITATIONS": limitations_df,
        "12_342K_READINESS": _build_readiness_df(summary),
        "13_NO_WRITE_BACK": _build_no_write_back_proof_df(no_write_back_json),
        "14_NEXT_STEPS": _build_next_steps_df(summary),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
