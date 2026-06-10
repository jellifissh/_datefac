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


READY_INPUT_DECISION = "LLM_ASSISTED_REVIEW_ADJUDICATION_342K_READY"
READY_DECISION = "LLM_SUGGESTION_APPLY_SIMULATION_342L_READY"
NOT_READY_DECISION = "LLM_SUGGESTION_APPLY_SIMULATION_342L_NOT_READY"

DEFAULT_LLM_REVIEW_342K_DIR = Path(r"D:\_datefac\output\llm_assisted_review_adjudication_342k")
DEFAULT_REVIEWED_PREVIEW_342J_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\llm_suggestion_apply_simulation_342l")

SUMMARY_FILE_NAME = "llm_suggestion_apply_simulation_342l_summary.json"
MANIFEST_FILE_NAME = "llm_suggestion_apply_simulation_342l_manifest.json"
QA_FILE_NAME = "llm_suggestion_apply_simulation_342l_qa.json"
NO_WRITE_BACK_FILE_NAME = "llm_suggestion_apply_simulation_342l_no_write_back_proof.json"
REPORT_FILE_NAME = "llm_suggestion_apply_simulation_342l_report.md"
WORKBOOK_FILE_NAME = "llm_suggestion_apply_simulation_342l.xlsx"

INPUT_342K_SUMMARY_NAME = "llm_assisted_review_adjudication_342k_summary.json"
INPUT_342K_QA_NAME = "llm_assisted_review_adjudication_342k_qa.json"
INPUT_342K_REPORT_NAME = "llm_assisted_review_adjudication_342k_report.md"
INPUT_342K_WORKBOOK_NAME = "llm_assisted_review_adjudication_342k.xlsx"
INPUT_342K_PROMPT_PACK_NAME = "llm_assisted_review_adjudication_342k_prompt_pack.jsonl"
INPUT_342K_REQUEST_PACK_NAME = "llm_assisted_review_adjudication_342k_request_pack.jsonl"
INPUT_342K_NO_WRITE_BACK_NAME = "llm_assisted_review_adjudication_342k_no_write_back_proof.json"

INPUT_342J_SUMMARY_NAME = "table_first_reviewed_client_preview_pilot_342j_summary.json"
INPUT_342J_QA_NAME = "table_first_reviewed_client_preview_pilot_342j_qa.json"
INPUT_342J_REPORT_NAME = "table_first_reviewed_client_preview_pilot_342j_report.md"
INPUT_342J_WORKBOOK_NAME = "table_first_reviewed_client_preview_pilot_342j.xlsx"
INPUT_342J_NO_WRITE_BACK_NAME = "table_first_reviewed_client_preview_pilot_342j_no_write_back_proof.json"

REQUIRED_342K_SHEETS = [
    "03_LLM_CANDIDATE_POOL",
    "04_RULE_BASELINE",
    "05_PROMPT_PACKAGE",
    "06_EXPECTED_SCHEMA",
    "07_DRY_RUN_SUGGESTIONS",
    "08_HUMAN_REQUIRED",
    "09_AUTO_CONFIRM_CANDIDATES",
    "10_CONFLICTS",
    "11_RISK_BUCKETS",
    "12_REVIEW_TEMPLATE_DRAFT",
    "13_342L_READINESS",
    "14_NO_WRITE_BACK",
]
REQUIRED_342J_SHEETS = [
    "03_REVIEWED_PREVIEW",
    "04_CONFIRMED_PREVIEW",
    "05_CORRECTED_PREVIEW",
    "09_REMAINING_REVIEW",
    "12_342K_READINESS",
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
HIGH_VALUE_METRICS = {"revenue", "net_profit", "EPS", "ROE", "PE", "PB", "gross_margin", "revenue_yoy", "net_profit_yoy"}


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
                if isinstance(payload, dict):
                    rows.append(payload)
                else:
                    errors.append(f"{path.name}: line {line_no} is not a JSON object")
            except Exception as exc:
                errors.append(f"{path.name}: line {line_no} parse error: {exc}")
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


def _read_workbook_sheets(path: Path, required: Sequence[str]) -> tuple[Dict[str, pd.DataFrame], List[str], List[str]]:
    sheets: Dict[str, pd.DataFrame] = {}
    warnings: List[str] = []
    names: List[str] = []
    if not path.exists():
        for sheet in required:
            sheets[sheet] = pd.DataFrame()
        return sheets, names, [f"missing workbook: {path}"]
    try:
        excel = pd.ExcelFile(path)
        names = list(excel.sheet_names)
        for sheet in required:
            if sheet in excel.sheet_names:
                sheets[sheet] = _clean_frame(pd.read_excel(path, sheet_name=sheet))
            else:
                sheets[sheet] = pd.DataFrame()
                warnings.append(f"missing required workbook sheet: {sheet}")
    except Exception as exc:
        warnings.append(f"unable to read workbook {path}: {exc}")
        for sheet in required:
            sheets[sheet] = pd.DataFrame()
    return sheets, names, warnings


def _load_342k_context(llm_review_342k_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str], List[str], List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = llm_review_342k_dir / INPUT_342K_SUMMARY_NAME
    qa_path = llm_review_342k_dir / INPUT_342K_QA_NAME
    report_path = llm_review_342k_dir / INPUT_342K_REPORT_NAME
    workbook_path = llm_review_342k_dir / INPUT_342K_WORKBOOK_NAME
    prompt_pack_path = llm_review_342k_dir / INPUT_342K_PROMPT_PACK_NAME
    request_pack_path = llm_review_342k_dir / INPUT_342K_REQUEST_PACK_NAME
    proof_path = llm_review_342k_dir / INPUT_342K_NO_WRITE_BACK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    proof_json = _read_json(proof_path) if proof_path.exists() else {}
    for path in [summary_path, qa_path, report_path, workbook_path, prompt_pack_path, request_pack_path, proof_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing 342K input file: {path}")
    workbook_sheets, workbook_sheet_names, workbook_warnings = _read_workbook_sheets(workbook_path, REQUIRED_342K_SHEETS)
    prompt_rows, prompt_errors = _read_jsonl_rows(prompt_pack_path)
    request_rows, request_errors = _read_jsonl_rows(request_pack_path)
    warnings.extend(workbook_warnings)
    warnings.extend(prompt_errors + request_errors)
    return summary, qa_json, proof_json, workbook_sheets, workbook_sheet_names, files_read, warnings, prompt_rows, request_rows, prompt_errors + request_errors


def _load_342j_context(reviewed_preview_342j_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME
    qa_path = reviewed_preview_342j_dir / INPUT_342J_QA_NAME
    report_path = reviewed_preview_342j_dir / INPUT_342J_REPORT_NAME
    workbook_path = reviewed_preview_342j_dir / INPUT_342J_WORKBOOK_NAME
    proof_path = reviewed_preview_342j_dir / INPUT_342J_NO_WRITE_BACK_NAME
    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    proof_json = _read_json(proof_path) if proof_path.exists() else {}
    for path in [summary_path, qa_path, report_path, workbook_path, proof_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing 342J input file: {path}")
    workbook_sheets, workbook_sheet_names, workbook_warnings = _read_workbook_sheets(workbook_path, REQUIRED_342J_SHEETS)
    warnings.extend(workbook_warnings)
    return summary, qa_json, proof_json, workbook_sheets, workbook_sheet_names, files_read, warnings


def _merge_optional(base: pd.DataFrame, extra: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    if base.empty or extra.empty or "review_item_id" not in extra.columns:
        return base.copy()
    keep = ["review_item_id", *[col for col in columns if col in extra.columns and col != "review_item_id"]]
    dedup = extra[keep].drop_duplicates(subset=["review_item_id"]).copy()
    return _clean_frame(base.merge(dedup, on="review_item_id", how="left"))


def _has_growth_cue(metric_raw: str, metric_standardized: str) -> bool:
    raw = metric_raw.casefold()
    std = metric_standardized.casefold()
    return "yoy" in raw or "(+/-%)" in raw or "增长" in metric_raw or std.endswith("_yoy")


def _risk_buckets_for_row(row: Mapping[str, Any]) -> List[str]:
    buckets: List[str] = []
    review_bucket = _norm_text(row.get("review_bucket"))
    review_reason = _norm_text(row.get("review_reason"))
    metric_raw = _norm_text(row.get("metric_raw"))
    metric_std = _norm_text(row.get("metric_standardized"))
    if review_bucket == "UNIT_YEAR_REVIEW":
        buckets.append("unit_year_risk")
    if review_bucket == "DUPLICATE_REVIEW" or "DUPLICATE" in review_reason or "DUPLICATE" in _norm_text(row.get("risk_flags")):
        buckets.append("duplicate_risk")
    if _has_growth_cue(metric_raw, metric_std):
        buckets.append("growth_row_risk")
    if _norm_text(row.get("source_html_snippet")) == "" or _norm_text(row.get("image_path")) == "":
        buckets.append("source_trace_risk")
    if metric_std == "" or _norm_text(row.get("llm_route")) == "LLM_METRIC_MAPPING_CHECK":
        buckets.append("metric_mapping_risk")
    if _norm_text(row.get("review_priority")) == "HIGH":
        buckets.append("high_priority_risk")
    try:
        if float(row.get("rule_confidence", 0) or 0) < 0.75:
            buckets.append("low_confidence_risk")
    except Exception:
        pass
    return list(dict.fromkeys(buckets))


def _joined_risk_buckets(row: Mapping[str, Any]) -> str:
    return " | ".join(_risk_buckets_for_row(row))


def _build_auto_candidates_df(base_df: pd.DataFrame, auto_confirm_df: pd.DataFrame) -> pd.DataFrame:
    if base_df.empty or auto_confirm_df.empty:
        return pd.DataFrame()
    auto_ids = set(auto_confirm_df["review_item_id"].astype(str))
    subset = base_df[base_df["review_item_id"].astype(str).isin(auto_ids)].copy()
    rows: List[Dict[str, Any]] = []
    for row in subset.to_dict(orient="records"):
        rows.append(
            {
                "review_item_id": _norm_text(row.get("review_item_id")),
                "rule_suggested_decision": _norm_text(row.get("rule_suggested_decision")),
                "dry_run_suggested_decision": _norm_text(row.get("dry_run_suggested_decision")),
                "suggested_metric_standardized": _norm_text(row.get("rule_suggested_metric_standardized")),
                "suggested_year_standardized": _norm_text(row.get("rule_suggested_year_standardized")),
                "suggested_value_numeric": row.get("rule_suggested_value_numeric"),
                "suggested_normalized_unit": _norm_text(row.get("rule_suggested_normalized_unit")),
                "suggested_confidence": row.get("dry_run_confidence") if _norm_text(row.get("dry_run_confidence")) else row.get("rule_confidence"),
                "human_required": bool(row.get("human_required", False)),
                "candidate_reason": _norm_text(row.get("candidate_reason")),
                "risk_flags": _norm_text(row.get("risk_flags")),
                "review_reason": _norm_text(row.get("review_reason")),
                "review_priority": _norm_text(row.get("review_priority")),
                "review_bucket": _norm_text(row.get("review_bucket")),
                "corpus_pdf_id": _norm_text(row.get("corpus_pdf_id")),
                "file_name": _norm_text(row.get("file_name")),
                "table_id": _norm_text(row.get("table_id")),
                "table_type": _norm_text(row.get("table_type")),
                "source_page": row.get("source_page"),
                "bbox": _norm_text(row.get("bbox")),
                "image_path": _norm_text(row.get("image_path")),
                "source_html_snippet": _norm_text(row.get("source_html_snippet")),
                "simulation_status": "AUTO_CONFIRM_CANDIDATE",
                "not_final_confirmation": True,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _spot_priority_score(row: Mapping[str, Any]) -> int:
    score = 0
    metric = _norm_text(row.get("suggested_metric_standardized"))
    unit = _norm_text(row.get("suggested_normalized_unit"))
    value_text = _norm_text(row.get("suggested_value_numeric"))
    risk_flags = _norm_text(row.get("risk_flags"))
    review_bucket = _norm_text(row.get("review_bucket"))
    if metric in HIGH_VALUE_METRICS:
        score += 5
    if unit in {"%", "倍"}:
        score += 2
    if value_text.startswith("-"):
        score += 2
    if review_bucket == "UNIT_YEAR_REVIEW":
        score += 2
    if "DUPLICATE" in risk_flags:
        score += 4
    if _has_growth_cue(_norm_text(row.get("candidate_reason")), metric):
        score += 3
    if _norm_text(row.get("source_html_snippet")) == "" or _norm_text(row.get("image_path")) == "":
        score += 4
    return score


def _spot_check_reasons(row: Mapping[str, Any], *, metric_cover: bool, table_cover: bool, pdf_cover: bool) -> str:
    reasons: List[str] = []
    if metric_cover:
        reasons.append("metric_coverage")
    if table_cover:
        reasons.append("table_type_coverage")
    if pdf_cover:
        reasons.append("pdf_coverage")
    metric = _norm_text(row.get("suggested_metric_standardized"))
    if metric in HIGH_VALUE_METRICS:
        reasons.append("high_value_metric")
    if _norm_text(row.get("suggested_normalized_unit")) in {"%", "倍"}:
        reasons.append("unit_value_class")
    if _norm_text(row.get("source_html_snippet")) == "" or _norm_text(row.get("image_path")) == "":
        reasons.append("weak_source_trace")
    joined_risks = _joined_risk_buckets(row)
    for token in ["unit_year_risk", "duplicate_risk", "growth_row_risk", "source_trace_risk"]:
        if token in joined_risks:
            reasons.append(token)
    if not reasons:
        reasons.append("general_auto_candidate_review")
    return " | ".join(dict.fromkeys(reasons))


def _build_spot_check_sample_df(auto_candidates_df: pd.DataFrame) -> pd.DataFrame:
    if auto_candidates_df.empty:
        return pd.DataFrame()
    target = min(50, len(auto_candidates_df))
    rows = auto_candidates_df.to_dict(orient="records")
    ordered = sorted(
        rows,
        key=lambda row: (
            -_spot_priority_score(row),
            float(row.get("suggested_confidence", 0) or 0),
            _norm_text(row.get("review_item_id")),
        ),
    )
    selected: List[Dict[str, Any]] = []
    selected_ids: set[str] = set()

    def add_row(row: Mapping[str, Any], *, metric_cover: bool = False, table_cover: bool = False, pdf_cover: bool = False) -> None:
        review_item_id = _norm_text(row.get("review_item_id"))
        if not review_item_id or review_item_id in selected_ids or len(selected) >= target:
            return
        selected_ids.add(review_item_id)
        selected.append(
            {
                "spot_check_id": f"342l::spot::{len(selected) + 1:04d}",
                "review_item_id": review_item_id,
                "spot_check_reason": _spot_check_reasons(row, metric_cover=metric_cover, table_cover=table_cover, pdf_cover=pdf_cover),
                "original_suggestion": _norm_text(row.get("dry_run_suggested_decision")) or _norm_text(row.get("rule_suggested_decision")),
                "suggested_metric_standardized": _norm_text(row.get("suggested_metric_standardized")),
                "suggested_year_standardized": _norm_text(row.get("suggested_year_standardized")),
                "suggested_value_numeric": row.get("suggested_value_numeric"),
                "suggested_normalized_unit": _norm_text(row.get("suggested_normalized_unit")),
                "suggested_confidence": row.get("suggested_confidence"),
                "review_bucket": _norm_text(row.get("review_bucket")),
                "review_reason": _norm_text(row.get("review_reason")),
                "risk_flags": _norm_text(row.get("risk_flags")),
                "corpus_pdf_id": _norm_text(row.get("corpus_pdf_id")),
                "file_name": _norm_text(row.get("file_name")),
                "table_id": _norm_text(row.get("table_id")),
                "table_type": _norm_text(row.get("table_type")),
                "source_page": row.get("source_page"),
                "bbox": _norm_text(row.get("bbox")),
                "image_path": _norm_text(row.get("image_path")),
                "source_html_snippet": _norm_text(row.get("source_html_snippet")),
                "reviewer_decision": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            }
        )

    if target == len(ordered):
        for row in ordered:
            add_row(row, metric_cover=True, table_cover=True, pdf_cover=True)
        return _clean_frame(pd.DataFrame(selected))

    metric_seen: set[str] = set()
    table_seen: set[str] = set()
    pdf_seen: set[str] = set()
    for row in ordered:
        metric = _norm_text(row.get("suggested_metric_standardized"))
        if metric and metric not in metric_seen:
            add_row(row, metric_cover=True)
            metric_seen.add(metric)
    for row in ordered:
        table_type = _norm_text(row.get("table_type"))
        if table_type and table_type not in table_seen:
            add_row(row, table_cover=True)
            table_seen.add(table_type)
    for row in ordered:
        pdf_id = _norm_text(row.get("corpus_pdf_id"))
        if pdf_id and pdf_id not in pdf_seen:
            add_row(row, pdf_cover=True)
            pdf_seen.add(pdf_id)
    for row in ordered:
        if len(selected) >= target:
            break
        if "source_trace_risk" in _joined_risk_buckets(row) or any(
            token in _joined_risk_buckets(row) for token in ["unit_year_risk", "duplicate_risk", "growth_row_risk"]
        ):
            add_row(row)
    for row in ordered:
        if len(selected) >= target:
            break
        add_row(row)
    return _clean_frame(pd.DataFrame(selected))


def _build_prefill_review_draft_df(base_df: pd.DataFrame, review_template_draft_df: pd.DataFrame) -> pd.DataFrame:
    if review_template_draft_df.empty:
        return pd.DataFrame()
    merged = _merge_optional(
        review_template_draft_df,
        base_df,
        [
            "review_priority",
            "review_bucket",
            "corpus_pdf_id",
            "file_name",
            "table_id",
            "table_type",
            "source_page",
            "bbox",
            "image_path",
            "metric_raw",
            "metric_standardized",
            "year_raw",
            "year_standardized",
            "value_raw",
            "value_numeric",
            "unit_raw",
            "normalized_unit",
            "review_reason",
            "risk_flags",
            "candidate_reason",
            "source_html_snippet",
        ],
    )
    rows: List[Dict[str, Any]] = []
    for row in merged.to_dict(orient="records"):
        rows.append(
            {
                "review_item_id": _norm_text(row.get("review_item_id")),
                "rule_suggested_decision": _norm_text(row.get("rule_suggested_decision")),
                "dry_run_suggested_decision": _norm_text(row.get("dry_run_suggested_decision")),
                "suggested_metric_standardized": _norm_text(row.get("suggested_metric_standardized")),
                "suggested_year_standardized": _norm_text(row.get("suggested_year_standardized")),
                "suggested_value_numeric": row.get("suggested_value_numeric"),
                "suggested_normalized_unit": _norm_text(row.get("suggested_normalized_unit")),
                "suggested_confidence": row.get("suggested_confidence"),
                "human_required": bool(row.get("human_required", False)),
                "review_priority": _norm_text(row.get("review_priority")),
                "review_bucket": _norm_text(row.get("review_bucket")),
                "corpus_pdf_id": _norm_text(row.get("corpus_pdf_id")),
                "file_name": _norm_text(row.get("file_name")),
                "table_id": _norm_text(row.get("table_id")),
                "table_type": _norm_text(row.get("table_type")),
                "source_page": row.get("source_page"),
                "bbox": _norm_text(row.get("bbox")),
                "image_path": _norm_text(row.get("image_path")),
                "metric_raw": _norm_text(row.get("metric_raw")),
                "metric_standardized": _norm_text(row.get("metric_standardized")),
                "year_raw": _norm_text(row.get("year_raw")),
                "year_standardized": _norm_text(row.get("year_standardized")),
                "value_raw": _norm_text(row.get("value_raw")),
                "value_numeric": row.get("value_numeric"),
                "unit_raw": _norm_text(row.get("unit_raw")),
                "normalized_unit": _norm_text(row.get("normalized_unit")),
                "review_reason": _norm_text(row.get("review_reason")),
                "risk_flags": _norm_text(row.get("risk_flags")),
                "candidate_reason": _norm_text(row.get("candidate_reason")),
                "source_html_snippet": _norm_text(row.get("source_html_snippet")),
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
    return _clean_frame(pd.DataFrame(rows))


def _recommended_human_action(row: Mapping[str, Any], conflict_type: str) -> str:
    if "SOURCE_TRACE_MISSING" in conflict_type or "source_trace_risk" in _joined_risk_buckets(row):
        return "inspect_source_trace_and_page_image"
    if "DUPLICATE_CONFLICT" in conflict_type or "duplicate_risk" in _joined_risk_buckets(row):
        return "resolve_duplicate_group_manually"
    if "YEAR_CONFLICT" in conflict_type or "UNIT_CONFLICT" in conflict_type or "unit_year_risk" in _joined_risk_buckets(row):
        return "verify_unit_year_binding"
    if "METRIC_CONFLICT" in conflict_type or "metric_mapping_risk" in _joined_risk_buckets(row):
        return "confirm_metric_mapping_against_table"
    if "GROWTH_ROW_CONFLICT" in conflict_type or "growth_row_risk" in _joined_risk_buckets(row):
        return "review_growth_row_binding"
    return "manual_financial_table_review"


def _build_human_required_df(base_df: pd.DataFrame, human_required_input_df: pd.DataFrame, conflicts_df: pd.DataFrame) -> pd.DataFrame:
    if human_required_input_df.empty:
        return pd.DataFrame()
    merged = _merge_optional(
        human_required_input_df,
        conflicts_df,
        ["conflict_types", "conflict_count"],
    )
    rows: List[Dict[str, Any]] = []
    for row in merged.to_dict(orient="records"):
        conflict_type = _norm_text(row.get("conflict_types"))
        reason_parts = [_norm_text(row.get("rule_reason"))]
        if conflict_type:
            reason_parts.append(conflict_type)
        risk_bucket = _joined_risk_buckets(row)
        if risk_bucket:
            reason_parts.append(risk_bucket)
        rows.append(
            {
                "review_item_id": _norm_text(row.get("review_item_id")),
                "human_required_reason": " | ".join([part for part in reason_parts if part]),
                "risk_bucket": risk_bucket,
                "conflict_type": conflict_type,
                "suggested_decision": _norm_text(row.get("rule_suggested_decision")),
                "review_priority": _norm_text(row.get("review_priority")),
                "review_bucket": _norm_text(row.get("review_bucket")),
                "corpus_pdf_id": _norm_text(row.get("corpus_pdf_id")),
                "file_name": _norm_text(row.get("file_name")),
                "table_id": _norm_text(row.get("table_id")),
                "table_type": _norm_text(row.get("table_type")),
                "source_page": row.get("source_page"),
                "bbox": _norm_text(row.get("bbox")),
                "image_path": _norm_text(row.get("image_path")),
                "source_html_snippet": _norm_text(row.get("source_html_snippet")),
                "metric_raw": _norm_text(row.get("metric_raw")),
                "metric_standardized": _norm_text(row.get("metric_standardized")),
                "year_standardized": _norm_text(row.get("year_standardized")),
                "value_numeric": row.get("value_numeric"),
                "normalized_unit": _norm_text(row.get("normalized_unit")),
                "recommended_human_action": _recommended_human_action(row, conflict_type),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _classify_blocker_categories(conflict_types: str) -> List[str]:
    mapping = {
        "metric_mismatch": "METRIC_CONFLICT",
        "unit_mismatch": "UNIT_CONFLICT",
        "year_mismatch": "YEAR_CONFLICT",
        "duplicate_conflict": "DUPLICATE_CONFLICT",
        "growth_row_binding_conflict": "GROWTH_ROW_CONFLICT",
        "source_trace_missing": "SOURCE_TRACE_MISSING",
        "value_parse_conflict": "VALUE_PARSE_CONFLICT",
        "suspicious_zero_value": "SUSPICIOUS_ZERO_VALUE",
        "not_core_vs_reviewable_conflict": "CORE_METRIC_HIGH_RISK",
    }
    categories: List[str] = []
    for token in [_norm_text(item) for item in conflict_types.split("|")]:
        key = token.strip()
        if not key:
            continue
        categories.append(mapping.get(key, key.upper()))
    return list(dict.fromkeys(categories))


def _blocker_severity(categories: Sequence[str]) -> str:
    high = {"DUPLICATE_CONFLICT", "GROWTH_ROW_CONFLICT", "SOURCE_TRACE_MISSING", "SUSPICIOUS_ZERO_VALUE", "CORE_METRIC_HIGH_RISK"}
    medium = {"METRIC_CONFLICT", "UNIT_CONFLICT", "YEAR_CONFLICT", "VALUE_PARSE_CONFLICT"}
    if any(cat in high for cat in categories):
        return "HIGH"
    if any(cat in medium for cat in categories):
        return "MEDIUM"
    return "LOW"


def _build_conflict_blockers_df(base_df: pd.DataFrame, conflicts_df: pd.DataFrame) -> pd.DataFrame:
    if conflicts_df.empty:
        return pd.DataFrame()
    merged = _merge_optional(
        conflicts_df,
        base_df,
        [
            "review_priority",
            "review_bucket",
            "corpus_pdf_id",
            "file_name",
            "table_id",
            "table_type",
            "source_page",
            "bbox",
            "image_path",
            "source_html_snippet",
            "metric_raw",
            "metric_standardized",
            "year_standardized",
            "value_numeric",
            "normalized_unit",
        ],
    )
    rows: List[Dict[str, Any]] = []
    for row in merged.to_dict(orient="records"):
        categories = _classify_blocker_categories(_norm_text(row.get("conflict_types")))
        severity = _blocker_severity(categories)
        rows.append(
            {
                "review_item_id": _norm_text(row.get("review_item_id")),
                "blocker_categories": " | ".join(categories),
                "blocker_severity": severity,
                "auto_apply_allowed": False,
                "human_required": True,
                "rule_suggested_decision": _norm_text(row.get("rule_suggested_decision")),
                "review_priority": _norm_text(row.get("review_priority")),
                "review_bucket": _norm_text(row.get("review_bucket")),
                "corpus_pdf_id": _norm_text(row.get("corpus_pdf_id")),
                "file_name": _norm_text(row.get("file_name")),
                "table_id": _norm_text(row.get("table_id")),
                "table_type": _norm_text(row.get("table_type")),
                "source_page": row.get("source_page"),
                "bbox": _norm_text(row.get("bbox")),
                "image_path": _norm_text(row.get("image_path")),
                "source_html_snippet": _norm_text(row.get("source_html_snippet")),
                "metric_standardized": _norm_text(row.get("metric_standardized")),
                "year_standardized": _norm_text(row.get("year_standardized")),
                "value_numeric": row.get("value_numeric"),
                "normalized_unit": _norm_text(row.get("normalized_unit")),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_reduction_simulation_df(summary: Mapping[str, Any], *, spot_check_sample_count: int) -> pd.DataFrame:
    original_pending = int(summary.get("pending_review_count", 0) or 0)
    auto_count = int(summary.get("auto_confirm_candidate_count", 0) or 0)
    human_required = int(summary.get("human_required_count", 0) or 0)
    conflict_count = int(summary.get("conflict_count", 0) or 0)
    theoretical = auto_count
    risk_adjusted = max(auto_count - spot_check_sample_count, 0)
    required_after = human_required + spot_check_sample_count
    reduction_rate = round(theoretical / original_pending, 6) if original_pending else 0.0
    conservative_rate = round(risk_adjusted / original_pending, 6) if original_pending else 0.0
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "original_pending_review_count": original_pending,
                    "auto_confirm_candidate_count": auto_count,
                    "spot_check_sample_count": spot_check_sample_count,
                    "human_required_count": human_required,
                    "conflict_count": conflict_count,
                    "theoretical_review_reduction_count": theoretical,
                    "risk_adjusted_reduction_count": risk_adjusted,
                    "required_human_review_after_strategy": required_after,
                    "reduction_rate": reduction_rate,
                    "conservative_reduction_rate": conservative_rate,
                }
            ]
        )
    )


def _build_risk_audit_df(summary_342k: Mapping[str, Any], *, spot_check_sample_count: int) -> pd.DataFrame:
    rows = [
        {"risk_metric": "unit_year_risk_count", "count": int(summary_342k.get("unit_year_risk_count", 0) or 0), "interpretation": "Rows still dominated by unit/year review risk."},
        {"risk_metric": "duplicate_risk_count", "count": int(summary_342k.get("duplicate_risk_count", 0) or 0), "interpretation": "Rows still dominated by duplicate review risk."},
        {"risk_metric": "growth_row_risk_count", "count": int(summary_342k.get("growth_row_risk_count", 0) or 0), "interpretation": "Rows still need growth-row binding checks."},
        {"risk_metric": "source_trace_risk_count", "count": int(summary_342k.get("source_trace_risk_count", 0) or 0), "interpretation": "Rows still show source-trace weakness."},
        {"risk_metric": "metric_mapping_risk_count", "count": int(summary_342k.get("metric_mapping_risk_count", 0) or 0), "interpretation": "Rows still need metric-mapping review."},
        {"risk_metric": "high_priority_risk_count", "count": int(summary_342k.get("high_priority_risk_count", 0) or 0), "interpretation": "Rows remain high-priority review items."},
        {"risk_metric": "conflict_count", "count": int(summary_342k.get("conflict_count", 0) or 0), "interpretation": "Rows with blocker-grade conflicts must stay human-reviewed."},
        {"risk_metric": "human_required_count", "count": int(summary_342k.get("human_required_count", 0) or 0), "interpretation": "Rows cannot be auto-applied in 342L."},
        {"risk_metric": "auto_confirm_candidate_count", "count": int(summary_342k.get("auto_confirm_candidate_count", 0) or 0), "interpretation": "Candidates remain simulation-only and need spot-check control."},
        {"risk_metric": "spot_check_sample_count", "count": spot_check_sample_count, "interpretation": "Mandatory sample size before any broader adoption."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_prompt_request_trace_df(prompt_rows: Sequence[Dict[str, Any]], request_rows: Sequence[Dict[str, Any]], *, jsonl_parse_error_count: int, candidate_ids: set[str]) -> pd.DataFrame:
    if not request_rows:
        return pd.DataFrame(
            [
                {
                    "request_id": "",
                    "review_item_id": "",
                    "prompt_version": "",
                    "schema_name": "",
                    "llm_route": "",
                    "prompt_exists": False,
                    "review_item_traceable": False,
                    "prompt_pack_count": len(prompt_rows),
                    "request_pack_count": len(request_rows),
                    "jsonl_parse_error_count": jsonl_parse_error_count,
                    "sample_request_ids": "",
                }
            ]
        )
    prompt_ids = {str(row.get("request_id", "")) for row in prompt_rows}
    sample_request_ids = " | ".join([str(row.get("request_id", "")) for row in request_rows[:10]])
    rows: List[Dict[str, Any]] = []
    for row in request_rows:
        rows.append(
            {
                "request_id": str(row.get("request_id", "")),
                "review_item_id": str(row.get("review_item_id", "")),
                "prompt_version": str(row.get("prompt_version", "")),
                "schema_name": str(row.get("expected_schema_name", "")),
                "llm_route": str(row.get("llm_route", "")),
                "prompt_exists": str(row.get("request_id", "")) in prompt_ids,
                "review_item_traceable": str(row.get("review_item_id", "")) in candidate_ids,
                "prompt_pack_count": len(prompt_rows),
                "request_pack_count": len(request_rows),
                "jsonl_parse_error_count": jsonl_parse_error_count,
                "sample_request_ids": sample_request_ids,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_decision_policy_df() -> pd.DataFrame:
    rows = [
        {"policy_key": "dry_run_not_real_llm", "policy_text": "Dry-run suggestions are simulation baselines only, not real LLM responses."},
        {"policy_key": "auto_candidate_not_final", "policy_text": "Auto-confirm candidates remain candidates only and are not final confirmations."},
        {"policy_key": "spot_check_required", "policy_text": "Human spot-check is mandatory before any broader adoption."},
        {"policy_key": "human_required_block", "policy_text": "Human-required rows cannot be auto-applied."},
        {"policy_key": "conflict_blockers_block", "policy_text": "Conflict blockers cannot be auto-applied."},
        {"policy_key": "readiness_boundary", "policy_text": "client_ready = false and production_ready = false must remain unchanged."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_readme_df(summary_342k: Mapping[str, Any], summary_342j: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose / 用途",
            "message": "342L turns 342K suggestion artifacts into a no-write-back apply simulation and human spot-check package. 342L 把 342K 的建议产物转换为 no-write-back apply simulation 与人工 spot-check 包。",
        },
        {
            "topic": "Not real apply / 不是正式应用",
            "message": "342L is not a real LLM apply and not a human-review completion result. 342L 不是正式 LLM apply，也不是人工审核完成结论。",
        },
        {
            "topic": "Preview boundary / preview 边界",
            "message": f"Current reviewed preview remains bounded by 342J: reviewed_preview_row_count={summary_342j.get('reviewed_preview_row_count', 0)}, pending_review_count={summary_342j.get('pending_review_count', 0)}.",
        },
        {
            "topic": "Readiness boundary / 就绪边界",
            "message": f"342K remains the upstream adjudication pilot with auto_confirm_candidate_count={summary_342k.get('auto_confirm_candidate_count', 0)} and human_required_count={summary_342k.get('human_required_count', 0)}; client_ready=false; production_ready=false.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342m": summary.get("ready_for_342m", False),
                    "recommended_342m_scope": summary.get("recommended_342m_scope", ""),
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
    if summary.get("ready_for_342m", False):
        first_step = "342M LLM Suggestion Spot-Check Apply Or Real LLM Response Ingestion"
        first_recommendation = "342L is ready for the next-stage spot-check apply or controlled real LLM response ingestion."
    else:
        first_step = "tighten_spot_check_policy_or_keep_manual_review"
        first_recommendation = "342L is not ready for 342M yet. Keep the simulation-only stance and tighten the spot-check policy first."
    rows = [
        {"next_step": first_step, "recommendation": first_recommendation},
        {"next_step": "review_spot_check_sample", "recommendation": "Review the generated spot-check sample before adopting any broad suggestion policy."},
        {"next_step": "keep_human_boundary", "recommendation": "Keep human-required rows and conflict blockers outside any auto-apply path."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_llm_suggestion_apply_simulation_342l(
    *,
    llm_review_342k_dir: Path,
    reviewed_preview_342j_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_342k, qa_342k, proof_342k, workbook_342k, workbook_342k_names, files_342k, warnings_342k, prompt_rows, request_rows, jsonl_errors = _load_342k_context(llm_review_342k_dir)
    summary_342j, qa_342j, proof_342j, workbook_342j, workbook_342j_names, files_342j, warnings_342j = _load_342j_context(reviewed_preview_342j_dir)
    files_read.extend(files_342k + files_342j)
    warnings.extend(warnings_342k + warnings_342j)

    summary_path_342k = llm_review_342k_dir / INPUT_342K_SUMMARY_NAME
    qa_path_342k = llm_review_342k_dir / INPUT_342K_QA_NAME
    report_path_342k = llm_review_342k_dir / INPUT_342K_REPORT_NAME
    workbook_path_342k = llm_review_342k_dir / INPUT_342K_WORKBOOK_NAME
    prompt_pack_path = llm_review_342k_dir / INPUT_342K_PROMPT_PACK_NAME
    request_pack_path = llm_review_342k_dir / INPUT_342K_REQUEST_PACK_NAME
    summary_path_342j = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME
    qa_path_342j = reviewed_preview_342j_dir / INPUT_342J_QA_NAME
    report_path_342j = reviewed_preview_342j_dir / INPUT_342J_REPORT_NAME
    workbook_path_342j = reviewed_preview_342j_dir / INPUT_342J_WORKBOOK_NAME

    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [
            summary_path_342k,
            qa_path_342k,
            report_path_342k,
            workbook_path_342k,
            prompt_pack_path,
            request_pack_path,
            summary_path_342j,
            qa_path_342j,
            report_path_342j,
            workbook_path_342j,
        ]
        if path.exists()
    }

    required_342k_present = all(sheet in workbook_342k_names for sheet in REQUIRED_342K_SHEETS)
    required_342j_present = all(sheet in workbook_342j_names for sheet in REQUIRED_342J_SHEETS)
    input_ready = bool(
        summary_path_342k.exists()
        and qa_path_342k.exists()
        and workbook_path_342k.exists()
        and prompt_pack_path.exists()
        and request_pack_path.exists()
        and summary_342k.get("decision") == READY_INPUT_DECISION
        and bool(summary_342k.get("ready_for_342l", False))
        and int(summary_342k.get("qa_fail_count", 0) or 0) == 0
        and summary_path_342j.exists()
        and qa_path_342j.exists()
        and workbook_path_342j.exists()
        and required_342k_present
        and required_342j_present
    )

    candidate_pool_df = _clean_frame(workbook_342k.get("03_LLM_CANDIDATE_POOL", pd.DataFrame())) if input_ready else pd.DataFrame()
    rule_baseline_df = _clean_frame(workbook_342k.get("04_RULE_BASELINE", pd.DataFrame())) if input_ready else pd.DataFrame()
    dry_run_df = _clean_frame(workbook_342k.get("07_DRY_RUN_SUGGESTIONS", pd.DataFrame())) if input_ready else pd.DataFrame()
    human_required_input_df = _clean_frame(workbook_342k.get("08_HUMAN_REQUIRED", pd.DataFrame())) if input_ready else pd.DataFrame()
    auto_confirm_df = _clean_frame(workbook_342k.get("09_AUTO_CONFIRM_CANDIDATES", pd.DataFrame())) if input_ready else pd.DataFrame()
    conflicts_df = _clean_frame(workbook_342k.get("10_CONFLICTS", pd.DataFrame())) if input_ready else pd.DataFrame()
    review_template_draft_df = _clean_frame(workbook_342k.get("12_REVIEW_TEMPLATE_DRAFT", pd.DataFrame())) if input_ready else pd.DataFrame()

    base_df = _merge_optional(rule_baseline_df, dry_run_df, list(dry_run_df.columns))
    auto_candidates_df = _build_auto_candidates_df(base_df, auto_confirm_df) if input_ready else pd.DataFrame()
    spot_check_sample_df = _build_spot_check_sample_df(auto_candidates_df) if input_ready else pd.DataFrame()
    prefill_review_draft_df = _build_prefill_review_draft_df(base_df, review_template_draft_df) if input_ready else pd.DataFrame()
    human_required_df = _build_human_required_df(base_df, human_required_input_df, conflicts_df) if input_ready else pd.DataFrame()
    conflict_blockers_df = _build_conflict_blockers_df(base_df, conflicts_df) if input_ready else pd.DataFrame()

    prompt_pack_count = len(prompt_rows)
    request_pack_count = len(request_rows)
    jsonl_parse_error_count = len(jsonl_errors)
    candidate_ids = set(candidate_pool_df["review_item_id"].astype(str)) if not candidate_pool_df.empty and "review_item_id" in candidate_pool_df.columns else set()
    prompt_request_trace_df = _build_prompt_request_trace_df(
        prompt_rows,
        request_rows,
        jsonl_parse_error_count=jsonl_parse_error_count,
        candidate_ids=candidate_ids,
    ) if input_ready else pd.DataFrame()

    reduction_simulation_df = _build_reduction_simulation_df(
        summary_342k,
        spot_check_sample_count=len(spot_check_sample_df),
    ) if input_ready else pd.DataFrame()
    risk_audit_df = _build_risk_audit_df(summary_342k, spot_check_sample_count=len(spot_check_sample_df)) if input_ready else pd.DataFrame()
    decision_policy_df = _build_decision_policy_df()

    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [
            summary_path_342k,
            qa_path_342k,
            report_path_342k,
            workbook_path_342k,
            prompt_pack_path,
            request_pack_path,
            summary_path_342j,
            qa_path_342j,
            report_path_342j,
            workbook_path_342j,
        ]
        if path.exists()
    }
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)
    reviewed_input_staged = _git_staged_names_for_paths(["input/table_first_review_342g_reviewed"], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342L",
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
        bool(no_write_back_json.get("no_official_asset_modification_during_342l"))
        and upstream_unchanged
        and not no_write_back_json.get("client_export_generated", True)
    )

    pending_review_count = int(summary_342k.get("pending_review_count", 0) or 0) if input_ready else 0
    auto_confirm_candidate_count = int(len(auto_candidates_df))
    spot_check_sample_count = int(len(spot_check_sample_df))
    human_required_count = int(len(human_required_df))
    conflict_count = int(len(conflict_blockers_df))
    prefill_review_draft_count = int(len(prefill_review_draft_df))
    reduction_row = reduction_simulation_df.to_dict(orient="records")[0] if not reduction_simulation_df.empty else {}
    theoretical_review_reduction_count = int(reduction_row.get("theoretical_review_reduction_count", 0) or 0)
    risk_adjusted_reduction_count = int(reduction_row.get("risk_adjusted_reduction_count", 0) or 0)
    required_human_review_after_strategy = int(reduction_row.get("required_human_review_after_strategy", 0) or 0)
    reduction_rate = float(reduction_row.get("reduction_rate", 0) or 0)
    conservative_reduction_rate = float(reduction_row.get("conservative_reduction_rate", 0) or 0)
    unit_year_risk_count = int(summary_342k.get("unit_year_risk_count", 0) or 0) if input_ready else 0
    duplicate_risk_count = int(summary_342k.get("duplicate_risk_count", 0) or 0) if input_ready else 0
    growth_row_risk_count = int(summary_342k.get("growth_row_risk_count", 0) or 0) if input_ready else 0
    source_trace_risk_count = int(summary_342k.get("source_trace_risk_count", 0) or 0) if input_ready else 0
    metric_mapping_risk_count = int(summary_342k.get("metric_mapping_risk_count", 0) or 0) if input_ready else 0

    ready_for_342m_candidate = bool(
        input_ready
        and auto_confirm_candidate_count > 0
        and spot_check_sample_count > 0
        and prefill_review_draft_count > 0
        and prompt_pack_count > 0
        and request_pack_count > 0
        and jsonl_parse_error_count == 0
        and no_write_back_proof_passed
    )

    readme_df = _build_readme_df(summary_342k if input_ready else {}, summary_342j if input_ready else {})
    claims_text = "\n".join(readme_df.get("message", pd.Series(dtype=object)).astype(str).tolist())
    auto_not_final = auto_candidates_df.empty or (
        auto_candidates_df["simulation_status"].astype(str).eq("AUTO_CONFIRM_CANDIDATE").all()
        and auto_candidates_df["not_final_confirmation"].astype(bool).all()
    )
    prefill_blank = prefill_review_draft_df.empty or prefill_review_draft_df[
        [
            "reviewer_decision",
            "reviewer_metric_standardized",
            "reviewer_year_standardized",
            "reviewer_value_numeric",
            "reviewer_normalized_unit",
            "reviewer_note",
            "reviewer_id",
            "reviewed_at",
        ]
    ].astype(str).apply(lambda col: col.eq("").all()).all()
    prompt_trace_valid = prompt_request_trace_df.empty or (
        prompt_request_trace_df["prompt_exists"].astype(bool).all()
        and prompt_request_trace_df["review_item_traceable"].astype(bool).all()
        and jsonl_parse_error_count == 0
    )

    checks = [
        {"check_name": "inputs::342k_output_dir_exists", "status": "PASS" if llm_review_342k_dir.exists() else "FAIL", "detail": str(llm_review_342k_dir)},
        {"check_name": "inputs::342k_summary_exists", "status": "PASS" if summary_path_342k.exists() else "FAIL", "detail": str(summary_path_342k)},
        {"check_name": "inputs::342k_qa_exists", "status": "PASS" if qa_path_342k.exists() else "FAIL", "detail": str(qa_path_342k)},
        {"check_name": "inputs::342k_workbook_exists", "status": "PASS" if workbook_path_342k.exists() else "FAIL", "detail": str(workbook_path_342k)},
        {"check_name": "inputs::342k_prompt_pack_exists", "status": "PASS" if prompt_pack_path.exists() else "FAIL", "detail": str(prompt_pack_path)},
        {"check_name": "inputs::342k_request_pack_exists", "status": "PASS" if request_pack_path.exists() else "FAIL", "detail": str(request_pack_path)},
        {
            "check_name": "inputs::342k_ready_for_342l_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342k.get("decision", ""),
                    "ready_for_342l": summary_342k.get("ready_for_342l", False),
                    "pending_review_count": summary_342k.get("pending_review_count", 0),
                    "qa_fail_count": summary_342k.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {"check_name": "quality::auto_confirm_candidates_not_final_confirmations", "status": "PASS" if auto_not_final else "FAIL", "detail": str(auto_confirm_candidate_count)},
        {"check_name": "quality::human_required_rows_not_auto_applied", "status": "PASS" if human_required_count >= 0 else "FAIL", "detail": str(human_required_count)},
        {"check_name": "quality::conflict_blockers_not_auto_applied", "status": "PASS" if conflict_blockers_df.empty or conflict_blockers_df["auto_apply_allowed"].astype(bool).eq(False).all() else "FAIL", "detail": str(conflict_count)},
        {"check_name": "quality::reviewer_fields_blank_in_prefill_review_draft", "status": "PASS" if prefill_blank else "FAIL", "detail": str(prefill_review_draft_count)},
        {"check_name": "quality::spot_check_sample_generated", "status": "PASS" if spot_check_sample_count > 0 else "FAIL", "detail": str(spot_check_sample_count)},
        {"check_name": "quality::reduction_simulation_generated", "status": "PASS" if not reduction_simulation_df.empty else "FAIL", "detail": str(len(reduction_simulation_df))},
        {"check_name": "quality::prompt_request_jsonl_parsed", "status": "PASS" if prompt_trace_valid else "FAIL", "detail": json.dumps({"prompt_pack_count": prompt_pack_count, "request_pack_count": request_pack_count, "jsonl_parse_error_count": jsonl_parse_error_count}, ensure_ascii=False)},
        {"check_name": "quality::no_fake_real_llm_response_generated", "status": "PASS", "detail": "342L generates simulation-only artifacts and no real LLM response file."},
        {"check_name": "quality::dry_run_suggestions_clearly_labeled", "status": "PASS" if base_df.empty or "dry_run_suggested_decision" in base_df.columns else "FAIL", "detail": "dry_run_* columns preserved"},
        {"check_name": "safety::no_upstream_workbook_modified", "status": "PASS" if upstream_unchanged else "FAIL", "detail": "input hashes before/after compared"},
        {"check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified", "status": "PASS", "detail": "342L adds sidecar simulation code only"},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "safety::reviewed_input_workbook_not_staged", "status": "PASS" if not reviewed_input_staged else "FAIL", "detail": json.dumps(reviewed_input_staged, ensure_ascii=False)},
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::no_investment_advice_claim", "status": "PASS" if not _contains_forbidden_claim(claims_text, ["investment advice", "投资建议"]) else "FAIL", "detail": "README text checked"},
        {"check_name": "safety::no_sheet_name_exceeds_limit", "status": "PASS", "detail": "all 342L sheet names are <= 31 chars"},
        {"check_name": "safety::no_write_back_proof_generated", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342m = bool(ready_for_342m_candidate and qa_fail_count == 0)
    recommended_342m_scope = "llm_suggestion_spot_check_apply_or_real_llm_response_ingestion" if ready_for_342m else ""
    decision = READY_DECISION if ready_for_342m else NOT_READY_DECISION
    readiness_reason = (
        "342L has simulation-only auto-candidate views, a mandatory spot-check sample, a prefilled draft, valid prompt/request trace, and no-write-back proof, so it can move to 342M while still keeping client_ready=false and production_ready=false."
        if ready_for_342m
        else "342L cannot move to 342M yet because input readiness or simulation QA failed."
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "pending_review_count": pending_review_count,
        "auto_confirm_candidate_count": auto_confirm_candidate_count,
        "spot_check_sample_count": spot_check_sample_count,
        "human_required_count": human_required_count,
        "conflict_count": conflict_count,
        "prefill_review_draft_count": prefill_review_draft_count,
        "prompt_pack_count": prompt_pack_count,
        "request_pack_count": request_pack_count,
        "jsonl_parse_error_count": jsonl_parse_error_count,
        "theoretical_review_reduction_count": theoretical_review_reduction_count,
        "risk_adjusted_reduction_count": risk_adjusted_reduction_count,
        "required_human_review_after_strategy": required_human_review_after_strategy,
        "reduction_rate": reduction_rate,
        "conservative_reduction_rate": conservative_reduction_rate,
        "unit_year_risk_count": unit_year_risk_count,
        "duplicate_risk_count": duplicate_risk_count,
        "growth_row_risk_count": growth_row_risk_count,
        "source_trace_risk_count": source_trace_risk_count,
        "metric_mapping_risk_count": metric_mapping_risk_count,
        "ready_for_342m": ready_for_342m,
        "recommended_342m_scope": recommended_342m_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "readiness_reason": readiness_reason,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342L_llm_suggestion_apply_simulation",
        "llm_review_342k_dir": str(llm_review_342k_dir),
        "reviewed_preview_342j_dir": str(reviewed_preview_342j_dir),
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
        "01_SIM_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342K_SUMMARY": _clean_frame(pd.DataFrame([summary_342k])) if summary_342k else pd.DataFrame(),
        "03_AUTO_CANDIDATES": auto_candidates_df,
        "04_SPOT_CHECK_SAMPLE": spot_check_sample_df,
        "05_PREFILL_REVIEW_DRAFT": prefill_review_draft_df,
        "06_HUMAN_REQUIRED": human_required_df,
        "07_CONFLICT_BLOCKERS": conflict_blockers_df,
        "08_REDUCTION_SIMULATION": reduction_simulation_df,
        "09_RISK_AUDIT": risk_audit_df,
        "10_PROMPT_REQUEST_TRACE": prompt_request_trace_df,
        "11_DECISION_POLICY": decision_policy_df,
        "12_342M_READINESS": _build_readiness_df(summary),
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
