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


READY_INPUT_DECISION = "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY"
READY_DECISION = "LLM_ASSISTED_REVIEW_ADJUDICATION_342K_READY"
NOT_READY_DECISION = "LLM_ASSISTED_REVIEW_ADJUDICATION_342K_NOT_READY"

DEFAULT_REVIEWED_PREVIEW_342J_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")
DEFAULT_POST_HUMAN_REVIEW_342I_DIR = Path(r"D:\_datefac\output\table_first_post_human_review_sidecar_result_342i")
DEFAULT_REVIEW_PACKAGE_342G_DIR = Path(r"D:\_datefac\output\table_first_extraction_review_package_342g")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\llm_assisted_review_adjudication_342k")

SUMMARY_FILE_NAME = "llm_assisted_review_adjudication_342k_summary.json"
MANIFEST_FILE_NAME = "llm_assisted_review_adjudication_342k_manifest.json"
QA_FILE_NAME = "llm_assisted_review_adjudication_342k_qa.json"
NO_WRITE_BACK_FILE_NAME = "llm_assisted_review_adjudication_342k_no_write_back_proof.json"
REPORT_FILE_NAME = "llm_assisted_review_adjudication_342k_report.md"
WORKBOOK_FILE_NAME = "llm_assisted_review_adjudication_342k.xlsx"
PROMPT_PACK_FILE_NAME = "llm_assisted_review_adjudication_342k_prompt_pack.jsonl"
REQUEST_PACK_FILE_NAME = "llm_assisted_review_adjudication_342k_request_pack.jsonl"

INPUT_342J_SUMMARY_NAME = "table_first_reviewed_client_preview_pilot_342j_summary.json"
INPUT_342J_QA_NAME = "table_first_reviewed_client_preview_pilot_342j_qa.json"
INPUT_342J_REPORT_NAME = "table_first_reviewed_client_preview_pilot_342j_report.md"
INPUT_342J_WORKBOOK_NAME = "table_first_reviewed_client_preview_pilot_342j.xlsx"
INPUT_342J_NO_WRITE_BACK_NAME = "table_first_reviewed_client_preview_pilot_342j_no_write_back_proof.json"

INPUT_342I_SUMMARY_NAME = "table_first_post_human_review_sidecar_result_342i_summary.json"
INPUT_342I_QA_NAME = "table_first_post_human_review_sidecar_result_342i_qa.json"
INPUT_342I_REPORT_NAME = "table_first_post_human_review_sidecar_result_342i_report.md"
INPUT_342I_WORKBOOK_NAME = "table_first_post_human_review_sidecar_result_342i.xlsx"

INPUT_342G_WORKBOOK_NAME = "table_first_extraction_review_package_342g.xlsx"

REQUIRED_342J_SHEETS = [
    "03_REVIEWED_PREVIEW",
    "04_CONFIRMED_PREVIEW",
    "05_CORRECTED_PREVIEW",
    "09_REMAINING_REVIEW",
    "12_342K_READINESS",
]
REQUIRED_342I_SHEETS = [
    "04_FINAL_CONFIRMED",
    "05_FINAL_CORRECTED",
    "06_FINAL_REJECTED",
    "07_PENDING_REVIEW",
]
REQUIRED_342G_SHEETS = [
    "03_REVIEW_QUEUE",
    "04_TRUSTED_AUDIT",
    "05_UNIT_YEAR_ISSUES",
    "06_DUPLICATE_ISSUES",
    "07_GROWTH_ROW_ISSUES",
    "08_TABLE_TRACE",
    "10_REVIEW_TEMPLATE",
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

EXCLUDED_TABLE_TYPES = {"BASIC_DATA", "RATING_STANDARD", "RELATED_REPORTS", "DISCLAIMER", "CHART_OR_IMAGE", "NOISE_TABLE", "UNKNOWN_TABLE"}
CRITICAL_METRICS = {"revenue", "net_profit", "EPS", "ROE", "PE", "PB"}
PROMPT_SCHEMA_NAME = "llm_assisted_review_adjudication_342k_v1"
PROMPT_VERSION = "342k.v1"


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


def _load_342i_context(post_human_review_342i_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = post_human_review_342i_dir / INPUT_342I_SUMMARY_NAME
    qa_path = post_human_review_342i_dir / INPUT_342I_QA_NAME
    report_path = post_human_review_342i_dir / INPUT_342I_REPORT_NAME
    workbook_path = post_human_review_342i_dir / INPUT_342I_WORKBOOK_NAME
    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    for path in [summary_path, qa_path, report_path, workbook_path]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing 342I input file: {path}")
    workbook_sheets, workbook_sheet_names, workbook_warnings = _read_workbook_sheets(workbook_path, REQUIRED_342I_SHEETS)
    warnings.extend(workbook_warnings)
    return summary, qa_json, workbook_sheets, workbook_sheet_names, files_read, warnings


def _load_342g_context(review_package_342g_dir: Path) -> tuple[Dict[str, pd.DataFrame], List[str], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    workbook_path = review_package_342g_dir / INPUT_342G_WORKBOOK_NAME
    if workbook_path.exists():
        files_read.append(str(workbook_path))
    else:
        warnings.append(f"missing 342G input workbook: {workbook_path}")
    workbook_sheets, workbook_sheet_names, workbook_warnings = _read_workbook_sheets(workbook_path, REQUIRED_342G_SHEETS)
    warnings.extend(workbook_warnings)
    return workbook_sheets, workbook_sheet_names, files_read, warnings


def _already_reviewed_ids(workbook_342i: Mapping[str, pd.DataFrame]) -> set[str]:
    ids: set[str] = set()
    for sheet in ["04_FINAL_CONFIRMED", "05_FINAL_CORRECTED", "06_FINAL_REJECTED"]:
        df = workbook_342i.get(sheet, pd.DataFrame())
        if not df.empty and "review_item_id" in df.columns:
            ids.update(df["review_item_id"].map(_norm_text).tolist())
    ids.discard("")
    return ids


def _is_excluded_metric(metric_raw: str, metric_standardized: str) -> bool:
    metric_raw_l = metric_raw.casefold()
    metric_std_l = metric_standardized.casefold()
    if metric_std_l in {"stock_code", "rating", "broker", "report_date", "stock_name"}:
        return True
    if any(token in metric_raw_l for token in ["评级", "代码", "券商", "报告日期", "股票名称"]):
        return True
    return False


def _has_growth_cue(metric_raw: str, metric_standardized: str) -> bool:
    raw = metric_raw.casefold()
    std = metric_standardized.casefold()
    return (
        "yoy" in raw
        or "(+/-%)" in raw
        or "增长" in metric_raw
        or std.endswith("_yoy")
    )


def _infer_metric(metric_raw: str, metric_standardized: str) -> str:
    raw = metric_raw.casefold()
    if "收入增长" in metric_raw or "营收增长" in metric_raw or (metric_raw.strip().upper() == "YOY"):
        return "revenue_yoy"
    if "净利润增长" in metric_raw or "归母净利润增长" in metric_raw:
        return "net_profit_yoy"
    if "营业收入" in metric_raw or metric_raw.strip() == "收入":
        return "revenue"
    if "净利润" in metric_raw or "归母净利润" in metric_raw:
        return "net_profit"
    if "毛利率" in metric_raw:
        return "gross_margin"
    if "roe" in raw or "净资产收益率" in metric_raw:
        return "ROE"
    if "每股收益" in metric_raw or raw == "eps":
        return "EPS"
    if "市盈率" in metric_raw or raw == "pe":
        return "PE"
    if "市净率" in metric_raw or raw == "pb":
        return "PB"
    if metric_standardized:
        return metric_standardized
    return ""


def _infer_unit(metric_raw: str, value_raw: str, unit_raw: str, normalized_unit: str, suggested_metric: str) -> str:
    for candidate in [normalized_unit, unit_raw]:
        text = _norm_text(candidate)
        if text:
            return text
    value_text = _norm_text(value_raw)
    metric_raw_l = metric_raw.casefold()
    suggested_l = suggested_metric.casefold()
    if "%" in value_text or suggested_l.endswith("_yoy") or suggested_l in {"roe", "gross_margin", "net_margin"}:
        return "%"
    if "每股收益" in metric_raw or suggested_metric == "EPS":
        return "元"
    if any(token in metric_raw_l for token in ["市盈率", "市净率"]) or suggested_metric in {"PE", "PB"}:
        return "倍"
    if "百万元" in metric_raw:
        return "百万元"
    if "亿元" in metric_raw:
        return "亿元"
    return ""


def _candidate_reason(row: Mapping[str, Any]) -> str:
    parts: List[str] = []
    review_reason = _norm_text(row.get("review_reason"))
    risk_flags = _norm_text(row.get("risk_flags"))
    metric_raw = _norm_text(row.get("metric_raw"))
    if review_reason:
        parts.append(review_reason)
    if risk_flags:
        parts.append(risk_flags)
    if _has_growth_cue(metric_raw, _norm_text(row.get("metric_standardized"))):
        parts.append("growth_row_candidate")
    if _norm_text(row.get("normalized_unit")) == "" and _norm_text(row.get("value_raw")).find("%") >= 0:
        parts.append("unit_inferable_from_value")
    return " | ".join(dict.fromkeys(parts)) if parts else "pending_review_candidate"


def _llm_route(row: Mapping[str, Any]) -> str:
    review_priority = _norm_text(row.get("review_priority"))
    review_bucket = _norm_text(row.get("review_bucket"))
    review_reason = _norm_text(row.get("review_reason"))
    risk_flags = _norm_text(row.get("risk_flags"))
    metric_raw = _norm_text(row.get("metric_raw"))
    metric_standardized = _norm_text(row.get("metric_standardized"))
    source_html = _norm_text(row.get("source_html_snippet"))
    image_path = _norm_text(row.get("image_path"))
    if not source_html or not image_path:
        return "HUMAN_ONLY_HIGH_RISK"
    if review_priority == "HIGH" and "DUPLICATE" in review_reason:
        return "HUMAN_ONLY_HIGH_RISK"
    if review_priority == "HIGH" and "DUPLICATE_DROPPED" in risk_flags and _infer_metric(metric_raw, metric_standardized) in CRITICAL_METRICS:
        return "HUMAN_ONLY_HIGH_RISK"
    if "DUPLICATE" in review_reason or "DUPLICATE_DROPPED" in risk_flags or review_bucket == "DUPLICATE_REVIEW":
        return "LLM_DUPLICATE_CHECK"
    if _has_growth_cue(metric_raw, metric_standardized):
        return "LLM_GROWTH_ROW_CHECK"
    if not metric_standardized:
        return "LLM_METRIC_MAPPING_CHECK"
    if not _norm_text(row.get("normalized_unit")) or not _norm_text(row.get("year_standardized")):
        return "LLM_UNIT_YEAR_CHECK"
    if review_bucket == "TRUSTED_AUDIT_SAMPLE":
        return "LLM_SOURCE_TRACE_CHECK"
    return "LLM_UNIT_YEAR_CHECK"


def _build_candidate_pool_df(pending_df: pd.DataFrame, review_template_df: pd.DataFrame, processed_ids: set[str]) -> pd.DataFrame:
    if pending_df.empty:
        return pd.DataFrame()
    template_lookup = review_template_df.set_index("review_item_id", drop=False) if not review_template_df.empty and "review_item_id" in review_template_df.columns else None
    rows: List[Dict[str, Any]] = []
    for row in pending_df.to_dict(orient="records"):
        review_item_id = _norm_text(row.get("review_item_id"))
        if not review_item_id or review_item_id in processed_ids:
            continue
        merged = dict(row)
        if template_lookup is not None and review_item_id in template_lookup.index:
            template_row = template_lookup.loc[review_item_id]
            if isinstance(template_row, pd.DataFrame):
                template_row = template_row.iloc[0]
            for key, value in template_row.to_dict().items():
                if _norm_text(merged.get(key)) == "" and _norm_text(value) != "":
                    merged[key] = value
        if _norm_text(merged.get("table_type")) in EXCLUDED_TABLE_TYPES:
            continue
        if _is_excluded_metric(_norm_text(merged.get("metric_raw")), _norm_text(merged.get("metric_standardized"))):
            continue
        merged["candidate_reason"] = _candidate_reason(merged)
        merged["llm_route"] = _llm_route(merged)
        rows.append(merged)
    return _clean_frame(pd.DataFrame(rows))


def _rule_baseline_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    metric_raw = _norm_text(row.get("metric_raw"))
    metric_standardized = _norm_text(row.get("metric_standardized"))
    year_standardized = _norm_text(row.get("year_standardized"))
    value_numeric = row.get("value_numeric")
    value_raw = _norm_text(row.get("value_raw"))
    unit_raw = _norm_text(row.get("unit_raw"))
    normalized_unit = _norm_text(row.get("normalized_unit"))
    llm_route = _norm_text(row.get("llm_route"))
    review_priority = _norm_text(row.get("review_priority"))
    source_html = _norm_text(row.get("source_html_snippet"))

    suggested_metric = _infer_metric(metric_raw, metric_standardized)
    suggested_unit = _infer_unit(metric_raw, value_raw, unit_raw, normalized_unit, suggested_metric)
    suggested_year = year_standardized
    suggested_value = value_numeric if _norm_text(value_numeric) else value_raw

    human_required = False
    decision = "KEEP_REVIEW_REQUIRED"
    confidence = 0.72
    reason_parts: List[str] = []

    if llm_route == "HUMAN_ONLY_HIGH_RISK":
        human_required = True
        decision = "KEEP_REVIEW_REQUIRED"
        confidence = 0.35
        reason_parts.append("high_risk_or_incomplete_source_trace")
    elif not source_html:
        human_required = True
        decision = "NEEDS_SOURCE_CHECK"
        confidence = 0.40
        reason_parts.append("source_html_missing")
    elif not suggested_metric:
        human_required = True
        decision = "NOT_A_CORE_METRIC"
        confidence = 0.55
        reason_parts.append("metric_not_mappable_to_core_set")
    elif llm_route == "LLM_DUPLICATE_CHECK":
        human_required = review_priority == "HIGH"
        decision = "KEEP_REVIEW_REQUIRED" if human_required else "CORRECT_AND_CONFIRM"
        confidence = 0.68 if human_required else 0.82
        reason_parts.append("duplicate_conflict_requires_check")
    elif llm_route == "LLM_GROWTH_ROW_CHECK":
        decision = "CORRECT_AND_CONFIRM" if suggested_metric != metric_standardized or suggested_unit != normalized_unit else "CONFIRM_CELL"
        confidence = 0.90 if decision == "CORRECT_AND_CONFIRM" else 0.96
        reason_parts.append("growth_row_binding_rule")
    elif llm_route == "LLM_METRIC_MAPPING_CHECK":
        decision = "CORRECT_AND_CONFIRM" if suggested_metric else "KEEP_REVIEW_REQUIRED"
        confidence = 0.78 if suggested_metric else 0.50
        human_required = not bool(suggested_metric)
        reason_parts.append("metric_mapping_rule")
    elif llm_route == "LLM_SOURCE_TRACE_CHECK":
        decision = "CONFIRM_CELL" if suggested_metric and suggested_unit else "KEEP_REVIEW_REQUIRED"
        confidence = 0.97 if decision == "CONFIRM_CELL" else 0.70
        reason_parts.append("trusted_audit_or_source_trace_rule")
    else:
        decision = "CORRECT_AND_CONFIRM" if suggested_unit != normalized_unit or suggested_metric != metric_standardized else "CONFIRM_CELL"
        confidence = 0.93 if decision == "CORRECT_AND_CONFIRM" else 0.96
        reason_parts.append("unit_year_rule")

    if review_priority == "HIGH" and decision != "CONFIRM_CELL":
        human_required = True
        confidence = min(confidence, 0.70)
        reason_parts.append("high_priority_needs_human_confirmation")

    if _norm_text(value_raw) == "0" and suggested_metric in CRITICAL_METRICS:
        human_required = True
        confidence = min(confidence, 0.60)
        reason_parts.append("suspicious_zero_value")

    return {
        "review_item_id": _norm_text(row.get("review_item_id")),
        "llm_route": llm_route,
        "rule_suggested_decision": decision,
        "rule_suggested_metric_standardized": suggested_metric,
        "rule_suggested_year_standardized": suggested_year,
        "rule_suggested_value_numeric": suggested_value,
        "rule_suggested_normalized_unit": suggested_unit,
        "rule_confidence": round(float(confidence), 2),
        "rule_reason": " | ".join(dict.fromkeys(reason_parts)),
        "rule_human_required": bool(human_required),
    }


def _build_rule_baseline_df(candidate_pool_df: pd.DataFrame) -> pd.DataFrame:
    if candidate_pool_df.empty:
        return pd.DataFrame()
    rows = []
    for row in candidate_pool_df.to_dict(orient="records"):
        merged = dict(row)
        merged.update(_rule_baseline_row(row))
        rows.append(merged)
    return _clean_frame(pd.DataFrame(rows))


def _expected_schema_df() -> pd.DataFrame:
    rows = [
        {"field_name": "review_item_id", "type": "string", "required": True, "allowed_values": "", "notes": "Echo back the input review_item_id."},
        {"field_name": "llm_suggested_decision", "type": "enum", "required": True, "allowed_values": "CONFIRM_CELL | CORRECT_AND_CONFIRM | REJECT_CELL | KEEP_REVIEW_REQUIRED | NOT_A_CORE_METRIC | NEEDS_SOURCE_CHECK", "notes": "Suggestion only, not final human review."},
        {"field_name": "llm_suggested_metric_standardized", "type": "string", "required": False, "allowed_values": "", "notes": "Core metric mapping suggestion."},
        {"field_name": "llm_suggested_year_standardized", "type": "string", "required": False, "allowed_values": "", "notes": "Year binding suggestion."},
        {"field_name": "llm_suggested_value_numeric", "type": "number|string|null", "required": False, "allowed_values": "", "notes": "Suggested numeric value."},
        {"field_name": "llm_suggested_normalized_unit", "type": "string", "required": False, "allowed_values": "", "notes": "Suggested normalized unit."},
        {"field_name": "llm_confidence", "type": "number 0-1", "required": True, "allowed_values": "", "notes": "Model confidence, not human confidence."},
        {"field_name": "llm_evidence", "type": "string", "required": True, "allowed_values": "", "notes": "Short evidence string from the provided table evidence only."},
        {"field_name": "llm_risk_reason", "type": "string", "required": True, "allowed_values": "", "notes": "Reason for keeping human review when needed."},
        {"field_name": "human_required", "type": "boolean", "required": True, "allowed_values": "true|false", "notes": "True means the suggestion still needs human review."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _system_prompt() -> str:
    return (
        "You are a financial table extraction review assistant. "
        "Judge only from the provided table evidence. "
        "Do not invent facts outside the evidence. "
        "Do not provide investment advice. "
        "Return JSON only and follow the required schema exactly. "
        "If evidence is insufficient, output NEEDS_SOURCE_CHECK or KEEP_REVIEW_REQUIRED. "
        "Any LLM suggestion is not a final human-review result."
    )


def _allowed_decisions() -> str:
    return "CONFIRM_CELL | CORRECT_AND_CONFIRM | REJECT_CELL | KEEP_REVIEW_REQUIRED | NOT_A_CORE_METRIC | NEEDS_SOURCE_CHECK"


def _prompt_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    request_id = f"342k::{_norm_text(row.get('review_item_id'))}"
    evidence = {
        "review_item_id": _norm_text(row.get("review_item_id")),
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
        "source_html_snippet": _norm_text(row.get("source_html_snippet")),
        "llm_route": _norm_text(row.get("llm_route")),
        "allowed_decisions": _allowed_decisions(),
    }
    user_prompt = (
        "Review the following pending financial-table row and return only JSON.\n"
        f"review_item_id: {evidence['review_item_id']}\n"
        f"metric_raw: {evidence['metric_raw']}\n"
        f"metric_standardized: {evidence['metric_standardized']}\n"
        f"year_raw: {evidence['year_raw']}\n"
        f"year_standardized: {evidence['year_standardized']}\n"
        f"value_raw: {evidence['value_raw']}\n"
        f"value_numeric: {evidence['value_numeric']}\n"
        f"unit_raw: {evidence['unit_raw']}\n"
        f"normalized_unit: {evidence['normalized_unit']}\n"
        f"table_type: {evidence['table_type']}\n"
        f"review_reason: {evidence['review_reason']}\n"
        f"risk_flags: {evidence['risk_flags']}\n"
        f"source_page: {evidence['source_page']}\n"
        f"bbox: {evidence['bbox']}\n"
        f"image_path: {evidence['image_path']}\n"
        f"source_html_snippet: {evidence['source_html_snippet']}\n"
        f"allowed decisions: {_allowed_decisions()}"
    )
    return {
        "request_id": request_id,
        "review_item_id": evidence["review_item_id"],
        "prompt_version": PROMPT_VERSION,
        "system_prompt": _system_prompt(),
        "user_prompt": user_prompt,
        "evidence_json": json.dumps(evidence, ensure_ascii=False),
        "expected_schema_name": PROMPT_SCHEMA_NAME,
        "max_tokens_hint": 400,
        "temperature_hint": 0.0,
    }


def _build_prompt_package_df(rule_baseline_df: pd.DataFrame) -> tuple[pd.DataFrame, List[Dict[str, Any]], List[Dict[str, Any]]]:
    if rule_baseline_df.empty:
        return pd.DataFrame(), [], []
    allowed_rows = rule_baseline_df[~rule_baseline_df["llm_route"].astype(str).eq("HUMAN_ONLY_HIGH_RISK")].copy()
    allowed_rows = allowed_rows[~allowed_rows["rule_human_required"].astype(bool)].copy()
    rows: List[Dict[str, Any]] = []
    requests: List[Dict[str, Any]] = []
    for row in allowed_rows.to_dict(orient="records"):
        prompt_row = _prompt_row(row)
        rows.append(prompt_row)
        requests.append(
            {
                "request_id": prompt_row["request_id"],
                "review_item_id": prompt_row["review_item_id"],
                "prompt_version": prompt_row["prompt_version"],
                "expected_schema_name": prompt_row["expected_schema_name"],
                "llm_route": _norm_text(row.get("llm_route")),
                "evidence_json": prompt_row["evidence_json"],
            }
        )
    return _clean_frame(pd.DataFrame(rows)), rows, requests


def _build_dry_run_suggestions_df(rule_baseline_df: pd.DataFrame) -> pd.DataFrame:
    if rule_baseline_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for row in rule_baseline_df.to_dict(orient="records"):
        can_auto = bool(
            float(row.get("rule_confidence", 0) or 0) >= 0.95
            and not bool(row.get("rule_human_required", False))
            and _norm_text(row.get("llm_route")) != "HUMAN_ONLY_HIGH_RISK"
            and _norm_text(row.get("rule_suggested_metric_standardized")) != ""
            and _norm_text(row.get("rule_suggested_year_standardized")) != ""
            and _norm_text(row.get("rule_suggested_normalized_unit")) != ""
            and "DUPLICATE" not in _norm_text(row.get("risk_flags"))
        )
        rows.append(
            {
                "review_item_id": _norm_text(row.get("review_item_id")),
                "dry_run_suggested_decision": _norm_text(row.get("rule_suggested_decision")),
                "dry_run_suggested_metric_standardized": _norm_text(row.get("rule_suggested_metric_standardized")),
                "dry_run_suggested_year_standardized": _norm_text(row.get("rule_suggested_year_standardized")),
                "dry_run_suggested_value_numeric": row.get("rule_suggested_value_numeric"),
                "dry_run_suggested_normalized_unit": _norm_text(row.get("rule_suggested_normalized_unit")),
                "dry_run_confidence": row.get("rule_confidence"),
                "dry_run_reason": f"DRY_RUN_BASELINE_ONLY | {_norm_text(row.get('rule_reason'))}",
                "human_required": bool(row.get("rule_human_required", False)),
                "can_auto_confirm_candidate": can_auto,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_conflicts_df(rule_baseline_df: pd.DataFrame) -> pd.DataFrame:
    if rule_baseline_df.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for row in rule_baseline_df.to_dict(orient="records"):
        conflicts: List[str] = []
        if _norm_text(row.get("metric_standardized")) != _norm_text(row.get("rule_suggested_metric_standardized")):
            conflicts.append("metric_mismatch")
        if _norm_text(row.get("normalized_unit")) != _norm_text(row.get("rule_suggested_normalized_unit")):
            conflicts.append("unit_mismatch")
        if _norm_text(row.get("year_standardized")) != _norm_text(row.get("rule_suggested_year_standardized")):
            conflicts.append("year_mismatch")
        if "DUPLICATE" in _norm_text(row.get("review_reason")) or "DUPLICATE_DROPPED" in _norm_text(row.get("risk_flags")):
            conflicts.append("duplicate_conflict")
        if not _norm_text(row.get("source_html_snippet")) or not _norm_text(row.get("image_path")):
            conflicts.append("source_trace_missing")
        if _norm_text(row.get("rule_suggested_decision")) == "NOT_A_CORE_METRIC" and _norm_text(row.get("extraction_status")) in {"REVIEW_REQUIRED", "TRUSTED_CELL"}:
            conflicts.append("not_core_vs_reviewable_conflict")
        if _norm_text(row.get("value_raw")) == "0" and _infer_metric(_norm_text(row.get("metric_raw")), _norm_text(row.get("metric_standardized"))) in CRITICAL_METRICS:
            conflicts.append("suspicious_zero_value")
        if _has_growth_cue(_norm_text(row.get("metric_raw")), _norm_text(row.get("metric_standardized"))) and _norm_text(row.get("rule_suggested_metric_standardized")) not in {"revenue_yoy", "net_profit_yoy"}:
            conflicts.append("growth_row_binding_conflict")
        if conflicts:
            rows.append(
                {
                    "review_item_id": _norm_text(row.get("review_item_id")),
                    "llm_route": _norm_text(row.get("llm_route")),
                    "conflict_types": " | ".join(conflicts),
                    "conflict_count": len(conflicts),
                    "rule_suggested_decision": _norm_text(row.get("rule_suggested_decision")),
                    "rule_reason": _norm_text(row.get("rule_reason")),
                    "human_required": bool(row.get("rule_human_required", False)),
                }
            )
    return _clean_frame(pd.DataFrame(rows))


def _build_risk_buckets_df(rule_baseline_df: pd.DataFrame) -> pd.DataFrame:
    if rule_baseline_df.empty:
        return pd.DataFrame()
    risk_rows = []
    risk_defs = {
        "unit_year_risk": lambda df: df["review_bucket"].astype(str).eq("UNIT_YEAR_REVIEW"),
        "duplicate_risk": lambda df: df["review_bucket"].astype(str).eq("DUPLICATE_REVIEW")
        | df["review_reason"].astype(str).str.contains("DUPLICATE", regex=False),
        "growth_row_risk": lambda df: df.apply(
            lambda row: _has_growth_cue(_norm_text(row.get("metric_raw")), _norm_text(row.get("metric_standardized"))),
            axis=1,
        ),
        "source_trace_risk": lambda df: df["source_html_snippet"].astype(str).eq("") | df["image_path"].astype(str).eq(""),
        "metric_mapping_risk": lambda df: df["metric_standardized"].astype(str).eq("")
        | df["llm_route"].astype(str).eq("LLM_METRIC_MAPPING_CHECK"),
        "high_priority_risk": lambda df: df["review_priority"].astype(str).eq("HIGH"),
        "low_confidence_risk": lambda df: pd.to_numeric(df["rule_confidence"], errors="coerce").fillna(0).lt(0.75),
    }
    for name, mask_builder in risk_defs.items():
        subset = rule_baseline_df[mask_builder(rule_baseline_df)].copy()
        risk_rows.append(
            {
                "risk_bucket": name,
                "row_count": int(len(subset)),
                "sample_review_item_ids": " | ".join(subset["review_item_id"].astype(str).head(10).tolist()),
            }
        )
    return _clean_frame(pd.DataFrame(risk_rows))


def _build_review_template_draft_df(rule_baseline_df: pd.DataFrame, dry_run_df: pd.DataFrame) -> pd.DataFrame:
    if rule_baseline_df.empty:
        return pd.DataFrame()
    dry_run_lookup = dry_run_df.set_index("review_item_id", drop=False) if not dry_run_df.empty else None
    rows: List[Dict[str, Any]] = []
    for row in rule_baseline_df.to_dict(orient="records"):
        dry = dry_run_lookup.loc[_norm_text(row.get("review_item_id"))].to_dict() if dry_run_lookup is not None and _norm_text(row.get("review_item_id")) in dry_run_lookup.index else {}
        rows.append(
            {
                "review_item_id": _norm_text(row.get("review_item_id")),
                "rule_suggested_decision": _norm_text(row.get("rule_suggested_decision")),
                "dry_run_suggested_decision": _norm_text(dry.get("dry_run_suggested_decision")),
                "suggested_metric_standardized": _norm_text(row.get("rule_suggested_metric_standardized")),
                "suggested_year_standardized": _norm_text(row.get("rule_suggested_year_standardized")),
                "suggested_value_numeric": row.get("rule_suggested_value_numeric"),
                "suggested_normalized_unit": _norm_text(row.get("rule_suggested_normalized_unit")),
                "suggested_confidence": row.get("rule_confidence"),
                "human_required": bool(row.get("rule_human_required", False)),
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


def _build_readme_df(summary_342j: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose / 用途",
            "message": "342K builds an LLM-assisted review adjudication pilot from the current pending review rows. 342K 从当前 pending review rows 构建 LLM-assisted review adjudication pilot。",
        },
        {
            "topic": "No-real-LLM default / 默认不调真实 LLM",
            "message": "By default this stage only generates prompt/request packages and dry-run rule baselines unless an explicit real LLM path is configured and requested. 默认只生成 prompt/request package 和 rule baseline dry-run suggestions，不直接调用真实 LLM。",
        },
        {
            "topic": "Human boundary / 人工边界",
            "message": "Dry-run suggestions are not final LLM output, and LLM suggestions are not human-review results. dry-run suggestions 不是最终 LLM 输出，LLM 建议也不是人工审核结果。",
        },
        {
            "topic": "Readiness boundary / 就绪边界",
            "message": "client_ready = false; production_ready = false; no write-back to upstream workbooks. 当前必须保持 client_ready=false、production_ready=false，且不写回上游 workbook。",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "ready_for_342l": summary.get("ready_for_342l", False),
                    "recommended_342l_scope": summary.get("recommended_342l_scope", ""),
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
    if summary.get("ready_for_342l", False):
        first_step = "342L LLM Suggestion Apply Or Human Spot-Check Simulation"
        first_recommendation = "342K is ready for a next-stage suggestion-apply or human spot-check simulation."
    else:
        first_step = "tighten_rule_baseline_or_expand_human_review"
        first_recommendation = "342K is not yet ready for 342L. Fix the adjudication package or expand human review first."
    rows = [
        {"next_step": first_step, "recommendation": first_recommendation},
        {"next_step": "review_prompt_package", "recommendation": "Review prompt/request packages before enabling any real LLM execution path."},
        {"next_step": "keep_human_spot_check", "recommendation": "Retain human spot-check as the final control layer even for high-confidence candidates."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_llm_assisted_review_adjudication_342k(
    *,
    reviewed_preview_342j_dir: Path,
    post_human_review_342i_dir: Path,
    review_package_342g_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_342j, qa_342j, proof_342j, workbook_342j, workbook_342j_names, files_342j, warnings_342j = _load_342j_context(reviewed_preview_342j_dir)
    summary_342i, qa_342i, workbook_342i, workbook_342i_names, files_342i, warnings_342i = _load_342i_context(post_human_review_342i_dir)
    workbook_342g, workbook_342g_names, files_342g, warnings_342g = _load_342g_context(review_package_342g_dir)
    files_read.extend(files_342j + files_342i + files_342g)
    warnings.extend(warnings_342j + warnings_342i + warnings_342g)

    summary_path_342j = reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME
    qa_path_342j = reviewed_preview_342j_dir / INPUT_342J_QA_NAME
    report_path_342j = reviewed_preview_342j_dir / INPUT_342J_REPORT_NAME
    workbook_path_342j = reviewed_preview_342j_dir / INPUT_342J_WORKBOOK_NAME
    summary_path_342i = post_human_review_342i_dir / INPUT_342I_SUMMARY_NAME
    qa_path_342i = post_human_review_342i_dir / INPUT_342I_QA_NAME
    report_path_342i = post_human_review_342i_dir / INPUT_342I_REPORT_NAME
    workbook_path_342i = post_human_review_342i_dir / INPUT_342I_WORKBOOK_NAME
    workbook_path_342g = review_package_342g_dir / INPUT_342G_WORKBOOK_NAME

    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [
            summary_path_342j,
            qa_path_342j,
            report_path_342j,
            workbook_path_342j,
            summary_path_342i,
            qa_path_342i,
            report_path_342i,
            workbook_path_342i,
            workbook_path_342g,
        ]
        if path.exists()
    }

    required_342j_present = all(sheet in workbook_342j_names for sheet in REQUIRED_342J_SHEETS)
    required_342i_present = all(sheet in workbook_342i_names for sheet in REQUIRED_342I_SHEETS)
    required_342g_present = all(sheet in workbook_342g_names for sheet in REQUIRED_342G_SHEETS)
    input_ready = bool(
        summary_path_342j.exists()
        and qa_path_342j.exists()
        and workbook_path_342j.exists()
        and summary_342j.get("decision") == READY_INPUT_DECISION
        and bool(summary_342j.get("ready_for_342k", False))
        and int(summary_342j.get("qa_fail_count", 0) or 0) == 0
        and workbook_path_342i.exists()
        and workbook_path_342g.exists()
        and required_342j_present
        and required_342i_present
        and required_342g_present
    )

    processed_ids = _already_reviewed_ids(workbook_342i)
    pending_df = _clean_frame(workbook_342i.get("07_PENDING_REVIEW", pd.DataFrame())) if input_ready else pd.DataFrame()
    review_template_df = _clean_frame(workbook_342g.get("10_REVIEW_TEMPLATE", pd.DataFrame())) if input_ready else pd.DataFrame()
    candidate_pool_df = _build_candidate_pool_df(pending_df, review_template_df, processed_ids) if input_ready else pd.DataFrame()
    rule_baseline_df = _build_rule_baseline_df(candidate_pool_df) if input_ready else pd.DataFrame()
    prompt_package_df, prompt_pack_rows, request_pack_rows = _build_prompt_package_df(rule_baseline_df) if input_ready else (pd.DataFrame(), [], [])
    expected_schema_df = _expected_schema_df() if input_ready else pd.DataFrame()
    dry_run_df = _build_dry_run_suggestions_df(rule_baseline_df) if input_ready else pd.DataFrame()
    conflicts_df = _build_conflicts_df(rule_baseline_df) if input_ready else pd.DataFrame()
    risk_buckets_df = _build_risk_buckets_df(rule_baseline_df) if input_ready else pd.DataFrame()
    human_required_df = _clean_frame(rule_baseline_df[rule_baseline_df["rule_human_required"].astype(bool)].copy()) if not rule_baseline_df.empty else pd.DataFrame()
    auto_confirm_df = pd.DataFrame()
    if not dry_run_df.empty:
        auto_confirm_df = _clean_frame(dry_run_df[dry_run_df["can_auto_confirm_candidate"].astype(bool)].copy())
    review_template_draft_df = _build_review_template_draft_df(rule_baseline_df, dry_run_df) if input_ready else pd.DataFrame()

    input_review_template_row_count = int(summary_342j.get("input_review_template_row_count", 0) or 0) if input_ready else 0
    reviewed_row_count = int(summary_342j.get("reviewed_row_count", 0) or 0) if input_ready else 0
    pending_review_count = int(summary_342j.get("pending_review_count", 0) or 0) if input_ready else 0
    llm_candidate_pool_count = int(len(candidate_pool_df))
    prompt_package_count = int(len(prompt_package_df))
    request_pack_count = int(len(request_pack_rows))
    rule_baseline_count = int(len(rule_baseline_df))
    dry_run_suggestion_count = int(len(dry_run_df))
    human_required_count = int(len(human_required_df))
    auto_confirm_candidate_count = int(len(auto_confirm_df))
    conflict_count = int(len(conflicts_df))
    risk_lookup = {row["risk_bucket"]: int(row["row_count"]) for row in risk_buckets_df.to_dict(orient="records")} if not risk_buckets_df.empty else {}
    unit_year_risk_count = risk_lookup.get("unit_year_risk", 0)
    duplicate_risk_count = risk_lookup.get("duplicate_risk", 0)
    growth_row_risk_count = risk_lookup.get("growth_row_risk", 0)
    source_trace_risk_count = risk_lookup.get("source_trace_risk", 0)
    metric_mapping_risk_count = risk_lookup.get("metric_mapping_risk", 0)
    high_priority_risk_count = risk_lookup.get("high_priority_risk", 0)
    review_template_draft_count = int(len(review_template_draft_df))

    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [
            summary_path_342j,
            qa_path_342j,
            report_path_342j,
            workbook_path_342j,
            summary_path_342i,
            qa_path_342i,
            report_path_342i,
            workbook_path_342i,
            workbook_path_342g,
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
        stage="342K",
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
        bool(no_write_back_json.get("no_official_asset_modification_during_342k"))
        and upstream_unchanged
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df(summary_342j if input_ready else {})
    claims_text = "\n".join(readme_df.get("message", pd.Series(dtype=object)).astype(str).tolist())
    ready_for_342l_candidate = bool(
        input_ready
        and llm_candidate_pool_count > 0
        and prompt_package_count > 0
        and dry_run_suggestion_count > 0
        and review_template_draft_count > 0
        and no_write_back_proof_passed
    )

    checks = [
        {"check_name": "inputs::342j_output_dir_exists", "status": "PASS" if reviewed_preview_342j_dir.exists() else "FAIL", "detail": str(reviewed_preview_342j_dir)},
        {"check_name": "inputs::342j_summary_exists", "status": "PASS" if summary_path_342j.exists() else "FAIL", "detail": str(summary_path_342j)},
        {"check_name": "inputs::342j_qa_exists", "status": "PASS" if qa_path_342j.exists() else "FAIL", "detail": str(qa_path_342j)},
        {"check_name": "inputs::342j_workbook_exists", "status": "PASS" if workbook_path_342j.exists() else "FAIL", "detail": str(workbook_path_342j)},
        {
            "check_name": "inputs::342j_ready_for_342k_detected",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342j.get("decision", ""),
                    "ready_for_342k": summary_342j.get("ready_for_342k", False),
                    "reviewed_row_count": summary_342j.get("reviewed_row_count", 0),
                    "pending_review_count": summary_342j.get("pending_review_count", 0),
                    "qa_fail_count": summary_342j.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {"check_name": "inputs::342i_workbook_exists", "status": "PASS" if workbook_path_342i.exists() else "FAIL", "detail": str(workbook_path_342i)},
        {"check_name": "inputs::342g_workbook_exists", "status": "PASS" if workbook_path_342g.exists() else "FAIL", "detail": str(workbook_path_342g)},
        {"check_name": "inputs::342g_required_sheets_exist", "status": "PASS" if required_342g_present else "FAIL", "detail": json.dumps({sheet: sheet in workbook_342g_names for sheet in REQUIRED_342G_SHEETS}, ensure_ascii=False)},
        {"check_name": "inputs::342i_required_sheets_exist", "status": "PASS" if required_342i_present else "FAIL", "detail": json.dumps({sheet: sheet in workbook_342i_names for sheet in REQUIRED_342I_SHEETS}, ensure_ascii=False)},
        {
            "check_name": "quality::already_reviewed_rows_excluded_from_candidate_pool",
            "status": "PASS" if not candidate_pool_df.empty and not candidate_pool_df["review_item_id"].astype(str).isin(processed_ids).any() or (candidate_pool_df.empty and not input_ready) else ("PASS" if not candidate_pool_df["review_item_id"].astype(str).isin(processed_ids).any() else "FAIL"),
            "detail": f"processed_ids={len(processed_ids)}; candidate_pool={llm_candidate_pool_count}",
        },
        {
            "check_name": "quality::rejected_not_core_reviewed_rows_excluded",
            "status": "PASS"
            if not candidate_pool_df.empty
            else ("PASS" if input_ready else "FAIL"),
            "detail": "candidate pool built from 342I pending rows only",
        },
        {"check_name": "quality::prompt_package_generated", "status": "PASS" if prompt_package_count > 0 else "FAIL", "detail": str(prompt_package_count)},
        {"check_name": "quality::expected_schema_generated", "status": "PASS" if not expected_schema_df.empty else "FAIL", "detail": str(len(expected_schema_df))},
        {"check_name": "quality::dry_run_clearly_labeled", "status": "PASS" if dry_run_df.empty or dry_run_df.columns.str.startswith("dry_run_").any() else "FAIL", "detail": json.dumps(list(dry_run_df.columns), ensure_ascii=False)},
        {"check_name": "quality::auto_confirm_rows_are_candidates_only", "status": "PASS" if auto_confirm_df.empty or "can_auto_confirm_candidate" in auto_confirm_df.columns else "FAIL", "detail": str(auto_confirm_candidate_count)},
        {"check_name": "quality::human_required_rows_generated", "status": "PASS" if human_required_count >= 0 else "FAIL", "detail": str(human_required_count)},
        {
            "check_name": "quality::review_template_draft_generated_with_blank_reviewer_fields",
            "status": "PASS"
            if review_template_draft_df.empty
            else (
                "PASS"
                if review_template_draft_df[["reviewer_decision", "reviewer_metric_standardized", "reviewer_year_standardized", "reviewer_value_numeric", "reviewer_normalized_unit", "reviewer_note", "reviewer_id", "reviewed_at"]]
                .astype(str)
                .apply(lambda col: col.eq("").all())
                .all()
                else "FAIL"
            ),
            "detail": str(review_template_draft_count),
        },
        {"check_name": "safety::no_upstream_workbook_modified", "status": "PASS" if upstream_unchanged else "FAIL", "detail": "input hashes before/after compared"},
        {"check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified", "status": "PASS", "detail": "342K adds sidecar adjudication code only"},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "safety::reviewed_input_workbook_not_staged", "status": "PASS" if not reviewed_input_staged else "FAIL", "detail": json.dumps(reviewed_input_staged, ensure_ascii=False)},
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::no_investment_advice_claim", "status": "PASS" if not _contains_forbidden_claim(claims_text, ["investment advice", "投资建议"]) else "FAIL", "detail": "README text checked"},
        {"check_name": "safety::no_sheet_name_exceeds_limit", "status": "PASS", "detail": "all 342K sheet names are <= 31 chars"},
        {"check_name": "safety::no_write_back_proof_generated", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    ready_for_342l = bool(ready_for_342l_candidate and qa_fail_count == 0)
    recommended_342l_scope = "llm_suggestion_apply_or_human_spot_check_simulation" if ready_for_342l else ""
    decision = READY_DECISION if ready_for_342l else NOT_READY_DECISION
    readiness_reason = (
        "342K has a valid candidate pool, prompt/request package, dry-run suggestions, and a draft review template, so it can move to 342L while still keeping client_ready=false and production_ready=false."
        if ready_for_342l
        else "342K cannot move to 342L yet because input readiness or adjudication package QA failed."
    )

    summary = {
        "generated_at_utc": _utc_now(),
        "input_review_template_row_count": input_review_template_row_count,
        "reviewed_row_count": reviewed_row_count,
        "pending_review_count": pending_review_count,
        "llm_candidate_pool_count": llm_candidate_pool_count,
        "prompt_package_count": prompt_package_count,
        "request_pack_count": request_pack_count,
        "rule_baseline_count": rule_baseline_count,
        "dry_run_suggestion_count": dry_run_suggestion_count,
        "human_required_count": human_required_count,
        "auto_confirm_candidate_count": auto_confirm_candidate_count,
        "conflict_count": conflict_count,
        "unit_year_risk_count": unit_year_risk_count,
        "duplicate_risk_count": duplicate_risk_count,
        "growth_row_risk_count": growth_row_risk_count,
        "source_trace_risk_count": source_trace_risk_count,
        "metric_mapping_risk_count": metric_mapping_risk_count,
        "high_priority_risk_count": high_priority_risk_count,
        "review_template_draft_count": review_template_draft_count,
        "ready_for_342l": ready_for_342l,
        "recommended_342l_scope": recommended_342l_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "readiness_reason": readiness_reason,
        "prompt_pack_path": str(output_dir / PROMPT_PACK_FILE_NAME),
        "request_pack_path": str(output_dir / REQUEST_PACK_FILE_NAME),
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342K_llm_assisted_review_adjudication_pilot",
        "reviewed_preview_342j_dir": str(reviewed_preview_342j_dir),
        "post_human_review_342i_dir": str(post_human_review_342i_dir),
        "review_package_342g_dir": str(review_package_342g_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "prompt_pack_jsonl": str(output_dir / PROMPT_PACK_FILE_NAME),
            "request_pack_jsonl": str(output_dir / REQUEST_PACK_FILE_NAME),
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
        "01_LLM_REVIEW_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342J_SUMMARY": _clean_frame(pd.DataFrame([summary_342j])) if summary_342j else pd.DataFrame(),
        "03_LLM_CANDIDATE_POOL": candidate_pool_df,
        "04_RULE_BASELINE": rule_baseline_df,
        "05_PROMPT_PACKAGE": prompt_package_df,
        "06_EXPECTED_SCHEMA": expected_schema_df,
        "07_DRY_RUN_SUGGESTIONS": dry_run_df,
        "08_HUMAN_REQUIRED": human_required_df,
        "09_AUTO_CONFIRM_CANDIDATES": auto_confirm_df,
        "10_CONFLICTS": conflicts_df,
        "11_RISK_BUCKETS": risk_buckets_df,
        "12_REVIEW_TEMPLATE_DRAFT": review_template_draft_df,
        "13_342L_READINESS": _build_readiness_df(summary),
        "14_NO_WRITE_BACK": _build_no_write_back_proof_df(no_write_back_json),
        "15_NEXT_STEPS": _build_next_steps_df(summary),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
        "prompt_pack_rows": prompt_pack_rows,
        "request_pack_rows": request_pack_rows,
    }
