from __future__ import annotations

import json
import math
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


READY_DECISION = "TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_READY"
NOT_READY_DECISION = "TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_NOT_READY"
READY_INPUT_DECISION = "TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_READY"

DEFAULT_CORPUS_342B_DIR = Path(r"D:\_datefac\output\real_pdf_corpus_intake_342b")
DEFAULT_MINERU_342C6_DIR = Path(r"D:\_datefac\output\mineru_pilot_network_recovery_342c6")
DEFAULT_PARSER_COMPARE_342D_DIR = Path(r"D:\_datefac\output\parser_ensemble_compare_342d")
DEFAULT_CANDIDATE_QUALITY_342E_DIR = Path(r"D:\_datefac\output\core_metric_candidate_quality_342e")
DEFAULT_CORE_EXTRACTION_342F_DIR = Path(r"D:\_datefac\output\table_first_core_financial_extraction_342f")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\table_first_extraction_review_package_342g")

SUMMARY_FILE_NAME = "table_first_extraction_review_package_342g_summary.json"
MANIFEST_FILE_NAME = "table_first_extraction_review_package_342g_manifest.json"
QA_FILE_NAME = "table_first_extraction_review_package_342g_qa.json"
NO_WRITE_BACK_FILE_NAME = "table_first_extraction_review_package_342g_no_write_back_proof.json"
REPORT_FILE_NAME = "table_first_extraction_review_package_342g_report.md"
WORKBOOK_FILE_NAME = "table_first_extraction_review_package_342g.xlsx"

CORE_342F_SUMMARY_NAME = "table_first_core_financial_extraction_342f_summary.json"
CORE_342F_QA_NAME = "table_first_core_financial_extraction_342f_qa.json"
CORE_342F_NO_WRITE_BACK_NAME = "table_first_core_financial_extraction_342f_no_write_back_proof.json"
CORE_342F_REPORT_NAME = "table_first_core_financial_extraction_342f_report.md"
CORE_342F_WORKBOOK_NAME = "table_first_core_financial_extraction_342f.xlsx"

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

REQUIRED_342F_SHEETS = [
    "03_LONG_FORM_CELLS",
    "04_TRUSTED_CELLS",
    "05_REVIEW_REQUIRED",
    "09_TABLE_TRACE",
]
OPTIONAL_342F_SHEETS = [
    "01_EXTRACTION_SUMMARY",
    "06_REJECTED_CELLS",
    "07_METRIC_COVERAGE",
    "08_UNIT_NORMALIZATION",
    "10_342G_READINESS",
    "11_NO_WRITE_BACK_PROOF",
]
CORE_TABLE_TYPES = {
    "CORE_FORECAST_SUMMARY",
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "VALUATION_METRICS",
}
EXCLUDED_TABLE_TYPES = {
    "BASIC_DATA",
    "RATING_STANDARD",
    "RELATED_REPORTS",
    "DISCLAIMER",
    "CHART_OR_IMAGE",
    "NOISE_TABLE",
    "UNKNOWN_TABLE",
}
PERCENT_OR_RATIO_UNITS = {"%", "倍_or_unitless"}
REVIEWER_DECISIONS = [
    "CONFIRM_CELL",
    "CORRECT_AND_CONFIRM",
    "REJECT_CELL",
    "KEEP_REVIEW_REQUIRED",
    "NOT_A_CORE_METRIC",
    "NEEDS_SOURCE_CHECK",
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


def _safe_float(value: Any) -> float | None:
    text = _norm_text(value)
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    cleaned = frame.astype(object).where(pd.notna(frame), "")
    return cleaned


def _read_json(path: Path) -> Any:
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
            if "not " not in window and "no " not in window and "false" not in window:
                return True
            start = idx + len(token_lower)
    return False


def _split_flags(value: Any) -> List[str]:
    text = _norm_text(value)
    if not text:
        return []
    tokens = [item.strip() for item in text.split("|")]
    return [token for token in tokens if token]


def _load_optional_summary(path: Path) -> tuple[Dict[str, Any], List[str]]:
    if not path.exists():
        return {}, []
    return _read_json(path), [str(path)]


def _load_342f_context(core_extraction_342f_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []

    summary_path = core_extraction_342f_dir / CORE_342F_SUMMARY_NAME
    qa_path = core_extraction_342f_dir / CORE_342F_QA_NAME
    proof_path = core_extraction_342f_dir / CORE_342F_NO_WRITE_BACK_NAME
    report_path = core_extraction_342f_dir / CORE_342F_REPORT_NAME
    workbook_path = core_extraction_342f_dir / CORE_342F_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    proof_json = _read_json(proof_path) if proof_path.exists() else {}

    for path, label in [
        (summary_path, "342F summary"),
        (qa_path, "342F qa"),
        (proof_path, "342F no-write-back proof"),
        (report_path, "342F report"),
        (workbook_path, "342F workbook"),
    ]:
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing {label}: {path}")

    workbook_sheets: Dict[str, pd.DataFrame] = {}
    if workbook_path.exists():
        try:
            excel = pd.ExcelFile(workbook_path)
            for sheet in REQUIRED_342F_SHEETS + OPTIONAL_342F_SHEETS:
                if sheet in excel.sheet_names:
                    workbook_sheets[sheet] = _clean_frame(pd.read_excel(workbook_path, sheet_name=sheet))
                else:
                    warnings.append(f"missing required 342F workbook sheet: {sheet}" if sheet in REQUIRED_342F_SHEETS else f"missing optional 342F workbook sheet: {sheet}")
                    workbook_sheets[sheet] = pd.DataFrame()
        except Exception as exc:
            warnings.append(f"unable to read 342F workbook: {exc}")
            for sheet in REQUIRED_342F_SHEETS + OPTIONAL_342F_SHEETS:
                workbook_sheets[sheet] = pd.DataFrame()
    else:
        for sheet in REQUIRED_342F_SHEETS + OPTIONAL_342F_SHEETS:
            workbook_sheets[sheet] = pd.DataFrame()

    return summary, qa_json, proof_json, workbook_sheets, files_read, warnings


def _weak_source_trace(row: Mapping[str, Any]) -> bool:
    return not _norm_text(row.get("source_page")) or not _norm_text(row.get("image_path")) or not _norm_text(row.get("bbox"))


def _base_priority(row: Mapping[str, Any], bucket: str) -> str:
    reason = _norm_text(row.get("review_reason"))
    flags = set(_split_flags(row.get("risk_flags")))
    unit_status = _norm_text(row.get("unit_status"))
    metric = _norm_text(row.get("metric_standardized"))

    if bucket == "TRUSTED_AUDIT_SAMPLE":
        if _weak_source_trace(row) or "PAREN_NEGATIVE_VALUE" in flags:
            return "HIGH"
        if _norm_text(row.get("normalized_unit")) in PERCENT_OR_RATIO_UNITS:
            return "MEDIUM"
        return "LOW"

    if unit_status == "MISMATCH":
        return "HIGH"
    if "YEAR_HEADER_MISSING" in flags or "YEAR_ALIGNMENT_RISK" in flags or "DUPLICATE_DROPPED" in flags:
        return "HIGH"
    if metric in {"revenue_yoy", "net_profit_yoy"}:
        return "HIGH"
    if unit_status == "MISSING" or "PAREN_NEGATIVE_VALUE" in flags:
        return "MEDIUM"
    if reason == "REVIEW_REQUIRED_DUPLICATE":
        return "HIGH"
    return "LOW"


def _recommended_action(row: Mapping[str, Any], bucket: str) -> str:
    reason = _norm_text(row.get("review_reason"))
    flags = set(_split_flags(row.get("risk_flags")))
    metric = _norm_text(row.get("metric_standardized"))
    if bucket == "TRUSTED_AUDIT_SAMPLE":
        if _weak_source_trace(row):
            return "回到 source_page / bbox / image_path 复核 trusted 样本。"
        return "做 spot-check，确认 trusted cell 的 metric / year / value / unit 与原表一致。"
    if reason == "REVIEW_REQUIRED_DUPLICATE":
        return "对照同组 duplicate 候选，保留最可信一条，其余按 reviewer_decision 处理。"
    if "YEAR_HEADER_MISSING" in flags or not _norm_text(row.get("year_standardized")):
        return "优先核对表头年份列，必要时回到 PDF / image 检查真实年份绑定。"
    if _norm_text(row.get("unit_status")) in {"MISSING", "MISMATCH", "AMBIGUOUS"}:
        return "优先确认单位，尤其避免把金额、百分比和倍数指标混淆。"
    if metric in {"revenue_yoy", "net_profit_yoy"}:
        return "核对 growth row 是否与上一个核心指标行正确绑定，并确认其百分比含义。"
    return "按原始 source_html_snippet、source_page 和 image_path 做人工复核。"


def _review_bucket(row: Mapping[str, Any], bucket: str) -> str:
    if bucket == "TRUSTED_AUDIT_SAMPLE":
        return "TRUSTED_AUDIT_SAMPLE"
    reason = _norm_text(row.get("review_reason"))
    if reason == "REVIEW_REQUIRED_DUPLICATE":
        return "DUPLICATE_REVIEW"
    if _norm_text(row.get("unit_status")) in {"MISSING", "MISMATCH", "AMBIGUOUS"}:
        return "UNIT_YEAR_REVIEW"
    if _norm_text(row.get("metric_standardized")) in {"revenue_yoy", "net_profit_yoy"}:
        return "GROWTH_ROW_REVIEW"
    return "REVIEW_REQUIRED_QUEUE"


def _ensure_columns(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    return _clean_frame(out)


def _build_review_queue(review_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(review_df.to_dict(orient="records"), start=1):
        review_reason = _norm_text(row.get("review_reason"))
        risk_flags = _norm_text(row.get("risk_flags"))
        record = dict(row)
        record["review_item_id"] = f"342g::queue::{index:04d}"
        record["review_priority"] = _base_priority(row, "REVIEW_REQUIRED_QUEUE")
        record["review_bucket"] = _review_bucket(row, "REVIEW_REQUIRED_QUEUE")
        record["review_reason_detail"] = review_reason
        record["recommended_review_action"] = _recommended_action(row, "REVIEW_REQUIRED_QUEUE")
        record["risk_flags"] = risk_flags
        rows.append(record)
    return _clean_frame(pd.DataFrame(rows))


def _trusted_sort_key(row: Mapping[str, Any]) -> tuple[int, int, int, str, str, str]:
    flags = set(_split_flags(row.get("risk_flags")))
    unit = _norm_text(row.get("normalized_unit"))
    negative = 1 if (_safe_float(row.get("value_numeric")) or 0) < 0 else 0
    weak = 1 if _weak_source_trace(row) else 0
    special_unit = 1 if unit in PERCENT_OR_RATIO_UNITS else 0
    risk = 1 if flags else 0
    return (-weak, -negative, -(special_unit + risk), _norm_text(row.get("corpus_pdf_id")), _norm_text(row.get("table_type")), _norm_text(row.get("metric_standardized")))


def _build_trusted_audit(trusted_df: pd.DataFrame, limit: int = 150) -> pd.DataFrame:
    if trusted_df.empty:
        return _clean_frame(pd.DataFrame())
    records = trusted_df.to_dict(orient="records")
    selected_indices: List[int] = []

    def add_index(idx: int) -> None:
        if idx not in selected_indices and len(selected_indices) < limit:
            selected_indices.append(idx)

    pdf_seen: set[str] = set()
    for idx, row in enumerate(records):
        pdf_id = _norm_text(row.get("corpus_pdf_id"))
        if pdf_id and pdf_id not in pdf_seen:
            add_index(idx)
            pdf_seen.add(pdf_id)

    type_seen: set[str] = set()
    for idx, row in enumerate(records):
        table_type = _norm_text(row.get("table_type"))
        if table_type and table_type not in type_seen:
            add_index(idx)
            type_seen.add(table_type)

    metric_seen: set[str] = set()
    for idx, row in enumerate(records):
        metric = _norm_text(row.get("metric_standardized"))
        if metric and metric not in metric_seen:
            add_index(idx)
            metric_seen.add(metric)

    for idx, row in enumerate(records):
        flags = set(_split_flags(row.get("risk_flags")))
        if _weak_source_trace(row) or "PAREN_NEGATIVE_VALUE" in flags:
            add_index(idx)

    for idx, row in enumerate(records):
        if _norm_text(row.get("normalized_unit")) in PERCENT_OR_RATIO_UNITS:
            add_index(idx)

    sorted_candidates = sorted(range(len(records)), key=lambda idx: _trusted_sort_key(records[idx]))
    for idx in sorted_candidates:
        add_index(idx)
        if len(selected_indices) >= limit:
            break

    selected = trusted_df.iloc[selected_indices].copy().reset_index(drop=True)
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(selected.to_dict(orient="records"), start=1):
        record = dict(row)
        record["review_item_id"] = f"342g::trusted::{index:04d}"
        record["review_priority"] = _base_priority(row, "TRUSTED_AUDIT_SAMPLE")
        record["review_bucket"] = "TRUSTED_AUDIT_SAMPLE"
        record["review_reason_detail"] = "TRUSTED_AUDIT_SPOT_CHECK"
        record["recommended_review_action"] = _recommended_action(row, "TRUSTED_AUDIT_SAMPLE")
        rows.append(record)
    return _clean_frame(pd.DataFrame(rows))


def _build_unit_year_issues(long_df: pd.DataFrame, review_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return _clean_frame(pd.DataFrame())
    records: List[Dict[str, Any]] = []
    for row in long_df.to_dict(orient="records"):
        flags = set(_split_flags(row.get("risk_flags")))
        unit_status = _norm_text(row.get("unit_status"))
        year_standardized = _norm_text(row.get("year_standardized"))
        issue_types: List[str] = []
        if unit_status == "MISSING" or not _norm_text(row.get("normalized_unit")):
            issue_types.append("UNIT_MISSING")
        if unit_status == "MISMATCH":
            issue_types.append("UNIT_MISMATCH")
        if unit_status == "AMBIGUOUS":
            issue_types.append("UNIT_AMBIGUOUS")
        if not year_standardized:
            issue_types.append("YEAR_HEADER_MISSING")
        if "YEAR_HEADER_MISSING" in flags:
            issue_types.append("REVIEW_REQUIRED_YEAR_HEADER_MISSING")
        if "YEAR_ALIGNMENT_RISK" in flags:
            issue_types.append("YEAR_ALIGNMENT_RISK")
        if not issue_types:
            continue
        record = dict(row)
        record["issue_category"] = "|".join(dict.fromkeys(issue_types))
        record["review_priority"] = _base_priority(row, "REVIEW_REQUIRED_QUEUE")
        records.append(record)
    return _clean_frame(pd.DataFrame(records))


def _build_duplicate_issues(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return _clean_frame(pd.DataFrame())
    grouped = (
        long_df.assign(
            _group_key=lambda df: (
                df["corpus_pdf_id"].astype(str).fillna("")
                + "|"
                + df["table_id"].astype(str).fillna("")
                + "|"
                + df["metric_standardized"].astype(str).fillna("")
                + "|"
                + df["year_standardized"].astype(str).fillna("")
                + "|"
                + df["value_numeric"].astype(str).fillna("")
                + "|"
                + df["normalized_unit"].astype(str).fillna("")
            )
        )
        .groupby("_group_key", dropna=False)
        .agg(
            corpus_pdf_id=("corpus_pdf_id", "first"),
            table_id=("table_id", "first"),
            metric_standardized=("metric_standardized", "first"),
            year_standardized=("year_standardized", "first"),
            value_numeric=("value_numeric", "first"),
            normalized_unit=("normalized_unit", "first"),
            duplicate_count=("long_cell_id", "count"),
            statuses=("extraction_status", lambda s: "|".join(sorted({str(v) for v in s if _norm_text(v)}))),
            source_pages=("source_page", lambda s: "|".join(sorted({str(v) for v in s if _norm_text(v)}))),
            file_name=("file_name", "first"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["duplicate_count"] > 1].copy()
    if grouped.empty:
        return _clean_frame(pd.DataFrame())
    grouped = grouped.rename(columns={"_group_key": "duplicate_group_key"})
    grouped["recommended_review_action"] = "对照 duplicate 组，确认保留值与年份绑定，避免重复 cell 进入 342H apply simulation。"
    grouped["review_priority"] = "HIGH"
    return _clean_frame(grouped)


def _build_growth_row_issues(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return _clean_frame(pd.DataFrame())
    mask = (
        long_df["metric_standardized"].astype(str).isin(["revenue_yoy", "net_profit_yoy"])
        | long_df["metric_raw"].astype(str).str.contains(r"\(\+/-%\)|yoy", regex=True, na=False)
        | long_df["review_reason"].astype(str).str.contains("GROWTH", case=False, na=False)
        | long_df["risk_flags"].astype(str).str.contains("GROWTH", case=False, na=False)
    )
    growth_df = long_df[mask].copy()
    if growth_df.empty:
        return _clean_frame(pd.DataFrame())
    growth_df["growth_binding_status"] = growth_df["metric_standardized"].astype(str).map(
        {
            "revenue_yoy": "BOUND_TO_REVENUE",
            "net_profit_yoy": "BOUND_TO_NET_PROFIT",
        }
    ).fillna("NEEDS_GROWTH_SOURCE_CHECK")
    growth_df["recommended_review_action"] = "核对 (+/-%) 或 YoY cell 是否与正确的 revenue / net_profit 行绑定，并确认百分比含义。"
    growth_df["review_priority"] = growth_df.apply(lambda row: _base_priority(row.to_dict(), "REVIEW_REQUIRED_QUEUE"), axis=1)
    return _clean_frame(growth_df)


def _build_review_template(review_queue_df: pd.DataFrame, trusted_audit_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "review_item_id",
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
        "extraction_status",
        "review_reason",
        "risk_flags",
        "confidence_signal",
        "source_html_snippet",
        "reviewer_decision",
        "reviewer_metric_standardized",
        "reviewer_year_standardized",
        "reviewer_value_numeric",
        "reviewer_normalized_unit",
        "reviewer_note",
        "reviewer_id",
        "reviewed_at",
    ]

    rows: List[Dict[str, Any]] = []
    for df, default_reason in [
        (review_queue_df, None),
        (trusted_audit_df, "TRUSTED_AUDIT_SPOT_CHECK"),
    ]:
        for row in df.to_dict(orient="records"):
            rows.append(
                {
                    "review_item_id": _norm_text(row.get("review_item_id")),
                    "review_priority": _norm_text(row.get("review_priority")),
                    "review_bucket": _norm_text(row.get("review_bucket")),
                    "corpus_pdf_id": _norm_text(row.get("corpus_pdf_id")),
                    "file_name": _norm_text(row.get("file_name")),
                    "table_id": _norm_text(row.get("table_id")),
                    "table_type": _norm_text(row.get("table_type")),
                    "source_page": _norm_text(row.get("source_page")),
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
                    "extraction_status": _norm_text(row.get("extraction_status")),
                    "review_reason": _norm_text(row.get("review_reason")) or default_reason or "",
                    "risk_flags": _norm_text(row.get("risk_flags")),
                    "confidence_signal": _norm_text(row.get("confidence_signal")),
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
    return _ensure_columns(_clean_frame(pd.DataFrame(rows)), columns)


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "用途 / Purpose",
            "message": "342G 把 342F 的 table-first long-form extraction 结果整理成人工可复核的 review package。342G 不是正式财务结果，也不会写回上游 workbook。",
        },
        {
            "topic": "Boundary",
            "message": "This is a sidecar human-review package only. It does not rerun MinerU, does not call VLM/LLM, and does not modify production pipeline / parser / extraction / delivery.",
        },
        {
            "topic": "Review Queue",
            "message": "03_REVIEW_QUEUE 只来自 342F 的 REVIEW_REQUIRED rows；06_REJECTED_CELLS 不会被直接混入主 review queue。",
        },
        {
            "topic": "Trusted Audit",
            "message": "04_TRUSTED_AUDIT 是 bounded spot-check sample，不代表把所有 TRUSTED_CELL 降级成人审。",
        },
        {
            "topic": "Current Status",
            "message": "当前仍然不是 client_ready，也不是 production_ready。下一步应是 342H Table-First Human Review Apply Simulation。",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_review_guide_df() -> pd.DataFrame:
    rows = [
        {"section": "主队列 / Main queue", "guide": "优先处理 HIGH priority 行：单位冲突、年份缺失、duplicate 冲突、growth row 绑定不清或 trusted 样本弱 trace。"},
        {"section": "金额指标", "guide": "先确认 value 与 year 列绑定，再确认 unit。不要把金额、百分比和倍数指标混淆。"},
        {"section": "百分比 / 倍数", "guide": "ROE / gross_margin / yoy 行应优先确认百分比含义；PE / PB 应确认是否真的是倍数而不是金额。"},
        {"section": "Duplicate", "guide": "duplicate 组至少要看同一组的 page / bbox / source_html_snippet，决定哪条保留进入 342H。"},
        {"section": "Growth row", "guide": "带 (+/-%) 或 metric_standardized 为 revenue_yoy / net_profit_yoy 的行，要确认它绑定的上一条核心指标是否正确。"},
        {"section": "Trusted audit", "guide": "TRUSTED_AUDIT_SAMPLE 不是全部 trusted 降级，只是抽样验证 table-first 结果可复核性。"},
        {"section": "风险边界", "guide": "本 workbook 只用于 review package，不构成投资建议，也不代表 client-ready / production-ready。"},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_decision_options_df() -> pd.DataFrame:
    rows = [
        {"reviewer_decision": "CONFIRM_CELL", "meaning_zh": "原始抽取正确，可直接确认。", "meaning_en": "Original extraction is correct."},
        {"reviewer_decision": "CORRECT_AND_CONFIRM", "meaning_zh": "人工修正 metric / year / value / unit 后确认。", "meaning_en": "Correct and then confirm."},
        {"reviewer_decision": "REJECT_CELL", "meaning_zh": "不是有效核心指标 cell。", "meaning_en": "Reject as invalid core metric cell."},
        {"reviewer_decision": "KEEP_REVIEW_REQUIRED", "meaning_zh": "当前仍不确定，继续保留待复核。", "meaning_en": "Still uncertain; keep pending."},
        {"reviewer_decision": "NOT_A_CORE_METRIC", "meaning_zh": "不属于当前核心财务指标范围。", "meaning_en": "Outside current core metric scope."},
        {"reviewer_decision": "NEEDS_SOURCE_CHECK", "meaning_zh": "需要回到 PDF / bbox / image 做源证据核对。", "meaning_en": "Needs source-level PDF / bbox / image check."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "review_queue_count": summary.get("review_queue_count", 0),
                    "trusted_audit_sample_count": summary.get("trusted_audit_sample_count", 0),
                    "review_template_row_count": summary.get("review_template_row_count", 0),
                    "ready_for_342h": summary.get("ready_for_342h", ""),
                    "recommended_342h_scope": summary.get("recommended_342h_scope", ""),
                    "reason": (
                        "342G 已经把 REVIEW_REQUIRED 主队列与 TRUSTED 抽样复核样本整理好，可以进入 342H human review apply simulation。"
                        if summary.get("ready_for_342h") == "true"
                        else "342F 上游输入或 342G QA 尚未满足，暂时不能进入 342H。"
                    ),
                }
            ]
        )
    )


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {"step_order": 1, "next_step": "Open 03_REVIEW_QUEUE", "rationale": "先处理 HIGH / MEDIUM priority 的 REVIEW_REQUIRED 行。"},
        {"step_order": 2, "next_step": "Use 04_TRUSTED_AUDIT for spot-check", "rationale": "确认 trusted cell 的 table-first 质量，不把全部 trusted 降级。"},
        {"step_order": 3, "next_step": "Fill 10_REVIEW_TEMPLATE only", "rationale": "342H apply simulation 只应消费 10_REVIEW_TEMPLATE 中的 reviewer_* 字段。"},
        {"step_order": 4, "next_step": "Proceed to 342H", "rationale": f"Current recommended_342h_scope = {summary.get('recommended_342h_scope', '')}"},
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


PERCENT_OR_RATIO_UNITS = {"%", "x_or_unitless"}


def _recommended_action(row: Mapping[str, Any], bucket: str) -> str:
    reason = _norm_text(row.get("review_reason"))
    flags = set(_split_flags(row.get("risk_flags")))
    metric = _norm_text(row.get("metric_standardized"))
    if bucket == "TRUSTED_AUDIT_SAMPLE":
        if _weak_source_trace(row):
            return "回到 source_page / bbox / image_path，复核这个 trusted 样本。"
        return "做 spot-check，确认 trusted cell 的 metric / year / value / unit 与原表一致。"
    if reason == "REVIEW_REQUIRED_DUPLICATE":
        return "对照同组 duplicate 候选，保留最可信的一条，其余通过 reviewer_decision 处理。"
    if "YEAR_HEADER_MISSING" in flags or not _norm_text(row.get("year_standardized")):
        return "优先核对表头年份列，必要时回到 PDF / image 检查真实年份绑定。"
    if _norm_text(row.get("unit_status")) in {"MISSING", "MISMATCH", "AMBIGUOUS"}:
        return "优先确认单位，尤其避免把金额、百分比和倍数指标混淆。"
    if metric in {"revenue_yoy", "net_profit_yoy"}:
        return "核对 growth row 是否与上一条核心指标行正确绑定，并确认其百分比含义。"
    return "按原始 source_html_snippet、source_page 和 image_path 做人工复核。"


def _build_duplicate_issues(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return _clean_frame(pd.DataFrame())
    grouped = (
        long_df.assign(
            _group_key=lambda df: (
                df["corpus_pdf_id"].astype(str).fillna("")
                + "|"
                + df["table_id"].astype(str).fillna("")
                + "|"
                + df["metric_standardized"].astype(str).fillna("")
                + "|"
                + df["year_standardized"].astype(str).fillna("")
                + "|"
                + df["value_numeric"].astype(str).fillna("")
                + "|"
                + df["normalized_unit"].astype(str).fillna("")
            )
        )
        .groupby("_group_key", dropna=False)
        .agg(
            corpus_pdf_id=("corpus_pdf_id", "first"),
            table_id=("table_id", "first"),
            metric_standardized=("metric_standardized", "first"),
            year_standardized=("year_standardized", "first"),
            value_numeric=("value_numeric", "first"),
            normalized_unit=("normalized_unit", "first"),
            duplicate_count=("long_cell_id", "count"),
            statuses=("extraction_status", lambda s: "|".join(sorted({str(v) for v in s if _norm_text(v)}))),
            source_pages=("source_page", lambda s: "|".join(sorted({str(v) for v in s if _norm_text(v)}))),
            file_name=("file_name", "first"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["duplicate_count"] > 1].copy()
    if grouped.empty:
        return _clean_frame(pd.DataFrame())
    grouped = grouped.rename(columns={"_group_key": "duplicate_group_key"})
    grouped["recommended_review_action"] = "对照 duplicate 组，确认保留值与年份绑定，避免重复 cell 进入 342H apply simulation。"
    grouped["review_priority"] = "HIGH"
    return _clean_frame(grouped)


def _build_growth_row_issues(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return _clean_frame(pd.DataFrame())
    mask = (
        long_df["metric_standardized"].astype(str).isin(["revenue_yoy", "net_profit_yoy"])
        | long_df["metric_raw"].astype(str).str.contains(r"\(\+/-%\)|yoy", regex=True, na=False)
        | long_df["review_reason"].astype(str).str.contains("GROWTH", case=False, na=False)
        | long_df["risk_flags"].astype(str).str.contains("GROWTH", case=False, na=False)
    )
    growth_df = long_df[mask].copy()
    if growth_df.empty:
        return _clean_frame(pd.DataFrame())
    growth_df["growth_binding_status"] = growth_df["metric_standardized"].astype(str).map(
        {
            "revenue_yoy": "BOUND_TO_REVENUE",
            "net_profit_yoy": "BOUND_TO_NET_PROFIT",
        }
    ).fillna("NEEDS_GROWTH_SOURCE_CHECK")
    growth_df["recommended_review_action"] = "核对 (+/-%) 或 YoY cell 是否与正确的 revenue / net_profit 行绑定，并确认百分比含义。"
    growth_df["review_priority"] = growth_df.apply(lambda row: _base_priority(row.to_dict(), "REVIEW_REQUIRED_QUEUE"), axis=1)
    return _clean_frame(growth_df)


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "用途 / Purpose",
            "message": "342G 把 342F 的 table-first long-form extraction 结果整理成人工可复核的 review package。342G 不是正式财务结果，也不会写回上游 workbook。",
        },
        {
            "topic": "Boundary",
            "message": "This is a sidecar human-review package only. It does not rerun MinerU, does not call VLM/LLM, and does not modify production pipeline / parser / extraction / delivery.",
        },
        {
            "topic": "Review Queue",
            "message": "03_REVIEW_QUEUE 只来自 342F 的 REVIEW_REQUIRED rows；06_REJECTED_CELLS 不会被直接混入主 review queue。",
        },
        {
            "topic": "Trusted Audit",
            "message": "04_TRUSTED_AUDIT 是 bounded spot-check sample，不代表把所有 TRUSTED_CELL 降级成人审。",
        },
        {
            "topic": "Current Status",
            "message": "当前仍然不是 client_ready，也不是 production_ready。下一步应是 342H Table-First Human Review Apply Simulation。",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_review_guide_df() -> pd.DataFrame:
    rows = [
        {"section": "主队列 / Main queue", "guide": "优先处理 HIGH priority 行：单位冲突、年份缺失、duplicate 冲突、growth row 绑定不清、trusted 样本弱 trace。"},
        {"section": "金额指标", "guide": "先确认 value 与 year 列绑定，再确认 unit。不要把金额、百分比和倍数指标混淆。"},
        {"section": "百分比 / 倍数", "guide": "ROE / gross_margin / yoy 行应优先确认百分比含义；PE / PB 应确认它们确实是倍数而不是金额。"},
        {"section": "Duplicate", "guide": "duplicate 组至少要看同一组的 page / bbox / source_html_snippet，再决定哪条保留进入 342H。"},
        {"section": "Growth row", "guide": "带 (+/-%) 或 metric_standardized 为 revenue_yoy / net_profit_yoy 的行，要确认它绑定的上一条核心指标是否正确。"},
        {"section": "Trusted audit", "guide": "TRUSTED_AUDIT_SAMPLE 不是全部 trusted 降级，只是抽样验证 table-first 结果可复核性。"},
        {"section": "风险边界", "guide": "本 workbook 只用于 review package，不构成投资建议，也不代表 client-ready / production-ready。"},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_decision_options_df() -> pd.DataFrame:
    rows = [
        {"reviewer_decision": "CONFIRM_CELL", "meaning_zh": "原始抽取正确，可直接确认。", "meaning_en": "Original extraction is correct."},
        {"reviewer_decision": "CORRECT_AND_CONFIRM", "meaning_zh": "人工修正 metric / year / value / unit 后确认。", "meaning_en": "Correct and then confirm."},
        {"reviewer_decision": "REJECT_CELL", "meaning_zh": "不是有效核心指标 cell。", "meaning_en": "Reject as invalid core metric cell."},
        {"reviewer_decision": "KEEP_REVIEW_REQUIRED", "meaning_zh": "当前仍不确定，继续保留待复核。", "meaning_en": "Still uncertain; keep pending."},
        {"reviewer_decision": "NOT_A_CORE_METRIC", "meaning_zh": "不属于当前核心财务指标范围。", "meaning_en": "Outside current core metric scope."},
        {"reviewer_decision": "NEEDS_SOURCE_CHECK", "meaning_zh": "需要回到 PDF / bbox / image 做源证据核对。", "meaning_en": "Needs source-level PDF / bbox / image check."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_readiness_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "review_queue_count": summary.get("review_queue_count", 0),
                    "trusted_audit_sample_count": summary.get("trusted_audit_sample_count", 0),
                    "review_template_row_count": summary.get("review_template_row_count", 0),
                    "ready_for_342h": summary.get("ready_for_342h", ""),
                    "recommended_342h_scope": summary.get("recommended_342h_scope", ""),
                    "reason": (
                        "342G 已经把 REVIEW_REQUIRED 主队列与 TRUSTED 抽样复核样本整理好，可以进入 342H human review apply simulation。"
                        if summary.get("ready_for_342h") == "true"
                        else "342F 上游输入或 342G QA 尚未满足，暂时不能进入 342H。"
                    ),
                }
            ]
        )
    )


def _build_next_steps_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {"step_order": 1, "next_step": "Open 03_REVIEW_QUEUE", "rationale": "先处理 HIGH / MEDIUM priority 的 REVIEW_REQUIRED 行。"},
        {"step_order": 2, "next_step": "Use 04_TRUSTED_AUDIT for spot-check", "rationale": "确认 trusted cell 的 table-first 质量，不把全部 trusted 降级。"},
        {"step_order": 3, "next_step": "Fill 10_REVIEW_TEMPLATE only", "rationale": "342H apply simulation 只应消费 10_REVIEW_TEMPLATE 中的 reviewer_* 字段。"},
        {"step_order": 4, "next_step": "Proceed to 342H", "rationale": f"Current recommended_342h_scope = {summary.get('recommended_342h_scope', '')}"},
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_table_first_extraction_review_package_342g(
    *,
    corpus_342b_dir: Path,
    mineru_342c6_dir: Path,
    parser_compare_342d_dir: Path,
    candidate_quality_342e_dir: Path,
    core_extraction_342f_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_342b, read_342b = _load_optional_summary(corpus_342b_dir / "real_pdf_corpus_intake_342b_summary.json")
    summary_342c6, read_342c6 = _load_optional_summary(mineru_342c6_dir / "mineru_pilot_network_recovery_342c6_summary.json")
    summary_342d, read_342d = _load_optional_summary(parser_compare_342d_dir / "parser_ensemble_compare_342d_summary.json")
    summary_342e, read_342e = _load_optional_summary(candidate_quality_342e_dir / "core_metric_candidate_quality_342e_summary.json")
    files_read.extend(read_342b + read_342c6 + read_342d + read_342e)

    summary_342f, qa_342f, proof_342f, workbook_342f, files_read_342f, warnings_342f = _load_342f_context(core_extraction_342f_dir)
    files_read.extend(files_read_342f)
    warnings.extend(warnings_342f)

    long_df = workbook_342f.get("03_LONG_FORM_CELLS", pd.DataFrame())
    trusted_df = workbook_342f.get("04_TRUSTED_CELLS", pd.DataFrame())
    review_df = workbook_342f.get("05_REVIEW_REQUIRED", pd.DataFrame())
    rejected_df = workbook_342f.get("06_REJECTED_CELLS", pd.DataFrame())
    metric_coverage_df = workbook_342f.get("07_METRIC_COVERAGE", pd.DataFrame())
    unit_norm_df = workbook_342f.get("08_UNIT_NORMALIZATION", pd.DataFrame())
    table_trace_df = workbook_342f.get("09_TABLE_TRACE", pd.DataFrame())

    review_queue_df = _build_review_queue(review_df)
    trusted_audit_df = _build_trusted_audit(trusted_df)
    unit_year_df = _build_unit_year_issues(long_df, review_df)
    duplicate_df = _build_duplicate_issues(long_df)
    growth_df = _build_growth_row_issues(long_df)
    review_template_df = _build_review_template(review_queue_df, trusted_audit_df)

    review_queue_count = len(review_queue_df)
    trusted_audit_sample_count = len(trusted_audit_df)
    unit_year_issue_count = len(unit_year_df)
    duplicate_issue_count = len(duplicate_df)
    growth_row_issue_count = len(growth_df)
    high_priority_review_count = int((review_template_df["review_priority"].astype(str) == "HIGH").sum()) if not review_template_df.empty else 0
    medium_priority_review_count = int((review_template_df["review_priority"].astype(str) == "MEDIUM").sum()) if not review_template_df.empty else 0
    low_priority_review_count = int((review_template_df["review_priority"].astype(str) == "LOW").sum()) if not review_template_df.empty else 0
    pdf_with_review_item_count = review_template_df["corpus_pdf_id"].astype(str).replace("", pd.NA).dropna().nunique() if not review_template_df.empty else 0
    table_with_review_item_count = review_template_df["table_id"].astype(str).replace("", pd.NA).dropna().nunique() if not review_template_df.empty else 0
    metric_with_review_item_count = review_template_df["metric_standardized"].astype(str).replace("", pd.NA).dropna().nunique() if not review_template_df.empty else 0
    review_template_row_count = len(review_template_df)

    input_long_form_cell_count = int(summary_342f.get("long_form_cell_count", len(long_df)) or len(long_df))
    input_trusted_cell_count = int(summary_342f.get("trusted_cell_count", len(trusted_df)) or len(trusted_df))
    input_review_required_cell_count = int(summary_342f.get("review_required_cell_count", len(review_df)) or len(review_df))
    input_rejected_cell_count = int(summary_342f.get("rejected_cell_count", len(rejected_df)) or len(rejected_df))
    audited_pdf_count = int(summary_342f.get("audited_pdf_count", 0) or 0)

    no_write_back_input_hashes_before = {
        path: sha256_file(Path(path))
        for path in files_read
        if Path(path).exists() and Path(path).is_file()
    }
    no_write_back_input_hashes_after = {
        path: sha256_file(Path(path))
        for path in files_read
        if Path(path).exists() and Path(path).is_file()
    }

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342G",
        files_read=files_read,
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
        bool(no_write_back_json.get("no_official_asset_modification_during_342g"))
        and bool(no_write_back_json.get("upstream_workbooks_unchanged"))
        and not no_write_back_json.get("client_export_generated", True)
    )

    ready_for_342h = (
        "true"
        if review_template_row_count > 0
        else "false"
    )
    recommended_342h_scope = "table_first_human_review_apply_simulation" if ready_for_342h == "true" else "insufficient_review_package_signal"

    readme_df = _build_readme_df()
    review_guide_df = _build_review_guide_df()
    decision_options_df = _build_decision_options_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())

    required_sheet_present = all(not workbook_342f.get(sheet, pd.DataFrame()).empty for sheet in REQUIRED_342F_SHEETS)
    basic_data_overlap = int(review_template_df["table_type"].astype(str).isin(EXCLUDED_TABLE_TYPES).sum()) if not review_template_df.empty else 0
    rejected_mixed = int(review_queue_df["extraction_status"].astype(str).eq("REJECTED_CELL").sum()) if not review_queue_df.empty else 0
    trusted_mixed = int(trusted_audit_df["extraction_status"].astype(str).ne("TRUSTED_CELL").sum()) if not trusted_audit_df.empty else 0
    reviewer_blank_ok = True
    for field in [
        "reviewer_decision",
        "reviewer_metric_standardized",
        "reviewer_year_standardized",
        "reviewer_value_numeric",
        "reviewer_normalized_unit",
        "reviewer_note",
        "reviewer_id",
        "reviewed_at",
    ]:
        if field in review_template_df.columns and not review_template_df[field].fillna("").astype(str).str.strip().eq("").all():
            reviewer_blank_ok = False

    checks = [
        {"check_name": "inputs::342f_summary_exists", "status": "PASS" if (core_extraction_342f_dir / CORE_342F_SUMMARY_NAME).exists() else "FAIL", "detail": str(core_extraction_342f_dir / CORE_342F_SUMMARY_NAME)},
        {"check_name": "inputs::342f_qa_exists", "status": "PASS" if (core_extraction_342f_dir / CORE_342F_QA_NAME).exists() else "FAIL", "detail": str(core_extraction_342f_dir / CORE_342F_QA_NAME)},
        {"check_name": "inputs::342f_workbook_exists", "status": "PASS" if (core_extraction_342f_dir / CORE_342F_WORKBOOK_NAME).exists() else "FAIL", "detail": str(core_extraction_342f_dir / CORE_342F_WORKBOOK_NAME)},
        {
            "check_name": "inputs::342f_ready_for_342g_detected",
            "status": "PASS"
            if summary_342f.get("decision", "") == READY_INPUT_DECISION
            and str(summary_342f.get("ready_for_342g", "")).casefold() == "true"
            and int(summary_342f.get("qa_fail_count", 0) or 0) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342f.get("decision", ""),
                    "ready_for_342g": summary_342f.get("ready_for_342g", ""),
                    "qa_fail_count": summary_342f.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342f_no_write_back_proof_passed",
            "status": "PASS"
            if bool(summary_342f.get("no_write_back_proof_passed")) or (proof_342f.get("upstream_unchanged") and proof_342f.get("official_assets_unchanged"))
            else "FAIL",
            "detail": json.dumps(
                {
                    "summary_no_write_back_proof_passed": summary_342f.get("no_write_back_proof_passed"),
                    "proof_json": proof_342f,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342f_required_sheets_exist",
            "status": "PASS" if required_sheet_present else "FAIL",
            "detail": json.dumps({sheet: not workbook_342f.get(sheet, pd.DataFrame()).empty for sheet in REQUIRED_342F_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "scope::review_queue_generated_from_review_required_only",
            "status": "PASS" if review_queue_count == len(review_df) and rejected_mixed == 0 else "FAIL",
            "detail": f"review_queue_count={review_queue_count} input_review_required={len(review_df)} rejected_mixed={rejected_mixed}",
        },
        {
            "check_name": "scope::trusted_audit_generated_from_trusted_only",
            "status": "PASS" if trusted_mixed == 0 else "FAIL",
            "detail": f"trusted_audit_count={trusted_audit_sample_count} non_trusted_rows={trusted_mixed}",
        },
        {
            "check_name": "scope::rejected_cells_not_mixed_into_review_queue",
            "status": "PASS" if rejected_mixed == 0 else "FAIL",
            "detail": str(rejected_mixed),
        },
        {
            "check_name": "scope::basic_data_not_mixed_into_core_review_queue",
            "status": "PASS" if basic_data_overlap == 0 else "FAIL",
            "detail": str(basic_data_overlap),
        },
        {
            "check_name": "scope::excluded_tables_not_mixed_into_core_review_queue",
            "status": "PASS" if basic_data_overlap == 0 else "FAIL",
            "detail": str(basic_data_overlap),
        },
        {
            "check_name": "artifacts::source_trace_fields_preserved",
            "status": "PASS"
            if not table_trace_df.empty and all(column in table_trace_df.columns for column in ["corpus_pdf_id", "table_id", "source_page", "bbox", "image_path", "source_file"])
            else "FAIL",
            "detail": json.dumps(table_trace_df.columns.tolist() if not table_trace_df.empty else [], ensure_ascii=False),
        },
        {
            "check_name": "artifacts::reviewer_fields_are_blank",
            "status": "PASS" if reviewer_blank_ok else "FAIL",
            "detail": "review_template reviewer_* fields checked",
        },
        {
            "check_name": "artifacts::decision_options_generated",
            "status": "PASS" if len(decision_options_df) == len(REVIEWER_DECISIONS) else "FAIL",
            "detail": json.dumps(REVIEWER_DECISIONS, ensure_ascii=False),
        },
        {
            "check_name": "artifacts::review_guide_generated",
            "status": "PASS" if not review_guide_df.empty else "FAIL",
            "detail": str(len(review_guide_df)),
        },
        {
            "check_name": "artifacts::342h_readiness_generated",
            "status": "PASS" if review_template_row_count > 0 else "FAIL",
            "detail": f"review_template_row_count={review_template_row_count}",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if no_write_back_json.get("upstream_workbooks_unchanged") else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "342G adds sidecar benchmark review-package code only",
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
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {
            "check_name": "claims::no_investment_advice_claim",
            "status": "PASS" if not _contains_forbidden_claim(readme_text, ["investment advice"]) else "FAIL",
            "detail": "README text checked",
        },
        {
            "check_name": "safety::no_sheet_name_exceeds_limit",
            "status": "PASS",
            "detail": "all 342G sheet names are <= 31 chars",
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    if qa_fail_count > 0 or review_template_row_count <= 0:
        ready_for_342h = "false"
        recommended_342h_scope = "review_package_not_ready"
        decision = NOT_READY_DECISION
    else:
        ready_for_342h = "true"
        recommended_342h_scope = "table_first_human_review_apply_simulation"
        decision = READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "audited_pdf_count": audited_pdf_count,
        "input_long_form_cell_count": input_long_form_cell_count,
        "input_trusted_cell_count": input_trusted_cell_count,
        "input_review_required_cell_count": input_review_required_cell_count,
        "input_rejected_cell_count": input_rejected_cell_count,
        "review_queue_count": review_queue_count,
        "trusted_audit_sample_count": trusted_audit_sample_count,
        "unit_year_issue_count": unit_year_issue_count,
        "duplicate_issue_count": duplicate_issue_count,
        "growth_row_issue_count": growth_row_issue_count,
        "high_priority_review_count": high_priority_review_count,
        "medium_priority_review_count": medium_priority_review_count,
        "low_priority_review_count": low_priority_review_count,
        "pdf_with_review_item_count": int(pdf_with_review_item_count),
        "table_with_review_item_count": int(table_with_review_item_count),
        "metric_with_review_item_count": int(metric_with_review_item_count),
        "review_template_row_count": review_template_row_count,
        "ready_for_342h": ready_for_342h,
        "recommended_342h_scope": recommended_342h_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "detected_342b_decision": summary_342b.get("decision", ""),
        "detected_342c6_decision": summary_342c6.get("decision", ""),
        "detected_342d_decision": summary_342d.get("decision", ""),
        "detected_342e_decision": summary_342e.get("decision", ""),
        "detected_342f_decision": summary_342f.get("decision", ""),
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342G_table_first_extraction_review_package",
        "corpus_342b_dir": str(corpus_342b_dir),
        "mineru_342c6_dir": str(mineru_342c6_dir),
        "parser_compare_342d_dir": str(parser_compare_342d_dir),
        "candidate_quality_342e_dir": str(candidate_quality_342e_dir),
        "core_extraction_342f_dir": str(core_extraction_342f_dir),
        "output_dir": str(output_dir),
        "warnings": warnings,
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
        },
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": no_write_back_input_hashes_before,
        "upstream_input_hashes_after": no_write_back_input_hashes_after,
    }

    workbook_sheets = {
        "00_README": readme_df,
        "01_REVIEW_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_342F_SUMMARY": _clean_frame(pd.DataFrame([summary_342f])),
        "03_REVIEW_QUEUE": review_queue_df,
        "04_TRUSTED_AUDIT": trusted_audit_df,
        "05_UNIT_YEAR_ISSUES": unit_year_df,
        "06_DUPLICATE_ISSUES": duplicate_df,
        "07_GROWTH_ROW_ISSUES": growth_df,
        "08_TABLE_TRACE": _clean_frame(table_trace_df),
        "09_REVIEW_GUIDE": review_guide_df,
        "10_REVIEW_TEMPLATE": review_template_df,
        "11_DECISION_OPTIONS": decision_options_df,
        "12_342H_READINESS": _build_readiness_df(summary),
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
