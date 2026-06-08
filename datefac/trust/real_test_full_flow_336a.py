from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
)
from pdfplumber_table_extractor import extract_tables_from_pdf


READY_DECISION = "REAL_TEST_FULL_FLOW_336A_LOCAL_PREVIEW_READY"
PARTIAL_DECISION = "REAL_TEST_FULL_FLOW_336A_LOCAL_PREVIEW_PARTIAL"
BLOCKED_DECISION = "REAL_TEST_FULL_FLOW_336A_BLOCKED"

DEFAULT_INPUT_PDF_DIR = Path(r"D:\_datefac\input\real_test")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\real_test_full_flow_336a")
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

WORKBOOK_SHEETS = {
    "readme": "00_README",
    "reviewed": "01_REVIEWED_CORE_METRICS",
    "needs_review": "02_NEEDS_REVIEW",
    "rejected": "03_REJECTED_OR_EXCLUDED",
    "trace": "04_SOURCE_TRACE",
    "summary": "05_RUN_SUMMARY",
}

NUMERIC_METRICS = {
    "revenue",
    "net_profit",
    "EPS",
    "PE",
    "PB",
    "ROE",
    "gross_margin",
    "net_margin",
    "YoY",
}

METRIC_RULES: List[Dict[str, Any]] = [
    {
        "metric": "revenue",
        "metric_display_zh": "营业收入",
        "patterns": ["营业收入", "主营收入", "revenue", "revenues", "sales"],
        "value_type": "numeric",
    },
    {
        "metric": "net_profit",
        "metric_display_zh": "归母净利润",
        "patterns": ["归母净利润", "归母净利", "母公司净利润", "net profit", "attributable net profit", "parent net profit"],
        "value_type": "numeric",
    },
    {
        "metric": "EPS",
        "metric_display_zh": "每股收益",
        "patterns": ["eps", "每股收益", "每股盈利", "摊薄eps", "diluted eps"],
        "value_type": "numeric",
    },
    {
        "metric": "PE",
        "metric_display_zh": "市盈率",
        "patterns": ["pe", "p/e", "市盈率"],
        "value_type": "numeric",
    },
    {
        "metric": "PB",
        "metric_display_zh": "市净率",
        "patterns": ["pb", "p/b", "市净率"],
        "value_type": "numeric",
    },
    {
        "metric": "ROE",
        "metric_display_zh": "净资产收益率",
        "patterns": ["roe", "净资产收益率"],
        "value_type": "numeric",
    },
    {
        "metric": "gross_margin",
        "metric_display_zh": "毛利率",
        "patterns": ["毛利率", "gross margin", "gross profit margin"],
        "value_type": "numeric",
    },
    {
        "metric": "net_margin",
        "metric_display_zh": "净利率",
        "patterns": ["净利率", "net margin", "profit margin"],
        "value_type": "numeric",
    },
    {
        "metric": "YoY",
        "metric_display_zh": "同比",
        "patterns": ["同比", "同比增长", "同比增速", "yoy", "year on year", "year-over-year"],
        "value_type": "numeric",
    },
    {
        "metric": "rating",
        "metric_display_zh": "投资评级",
        "patterns": ["投资评级", "评级", "rating", "buy", "hold", "sell", "增持", "买入"],
        "value_type": "text",
    },
    {
        "metric": "report_date",
        "metric_display_zh": "报告日期",
        "patterns": ["报告日期", "发布日期", "report date", "date"],
        "value_type": "text",
    },
    {
        "metric": "broker",
        "metric_display_zh": "机构",
        "patterns": ["证券", "研究所", "broker", "institution", "机构"],
        "value_type": "text",
    },
    {
        "metric": "stock_code",
        "metric_display_zh": "股票代码",
        "patterns": ["股票代码", "证券代码", "stock code", "ticker"],
        "value_type": "text",
    },
    {
        "metric": "stock_name",
        "metric_display_zh": "股票名称",
        "patterns": ["股票名称", "公司名称", "stock name", "company name"],
        "value_type": "text",
    },
]

YEAR_RE = re.compile(r"(20\d{2}|19\d{2})")
NUMBER_RE = re.compile(r"(?<![\w/])[-+]?\d[\d,]*(?:\.\d+)?%?(?:x|X|倍|亿|万|万元|亿元|元|百万元|千万元|百万)?")
DATE_RE = re.compile(r"(20\d{2}[/-]\d{1,2}[/-]\d{1,2}|20\d{2}年\d{1,2}月\d{1,2}日)")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    text = str(value or "").strip()
    return re.sub(r"\s+", " ", text)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _truncate(text: Any, limit: int = 180) -> str:
    normalized = _norm_text(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_status_porcelain_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_cached_names_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _find_pdf_files(input_pdf_dir: Path) -> List[Path]:
    if not input_pdf_dir.exists():
        return []
    return sorted(path for path in input_pdf_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")


def _extract_page_texts(pdf_path: Path) -> tuple[Dict[int, str], List[Dict[str, Any]], int | None]:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        return {}, [{"document": pdf_path.name, "page": None, "stage": "pdfplumber_import", "error": "pdfplumber not installed"}], None

    page_texts: Dict[int, str] = {}
    page_failures: List[Dict[str, Any]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for index, page in enumerate(pdf.pages, start=1):
                try:
                    page_texts[index] = _norm_text(page.extract_text() or "")
                except Exception as exc:
                    page_failures.append(
                        {
                            "document": pdf_path.name,
                            "page": index,
                            "stage": "page_text_extraction",
                            "error": str(exc),
                        }
                    )
                    page_texts[index] = ""
            return page_texts, page_failures, total_pages
    except Exception as exc:
        return {}, [{"document": pdf_path.name, "page": None, "stage": "pdf_open", "error": str(exc)}], None


def _extract_year(text: str) -> str:
    match = YEAR_RE.search(_norm_text(text))
    return match.group(1) if match else ""


def _extract_unit(*texts: str) -> str:
    haystack = " ".join(_norm_text(text) for text in texts if _norm_text(text))
    lowered = haystack.casefold()
    if "%" in haystack or "percent" in lowered or "pct" in lowered:
        return "%"
    if "亿元" in haystack:
        return "亿元"
    if "万元" in haystack:
        return "万元"
    if "百万元" in haystack:
        return "百万元"
    if "千万元" in haystack:
        return "千万元"
    if "亿" in haystack:
        return "亿"
    if "万" in haystack:
        return "万"
    if "元" in haystack:
        return "元"
    if "rmb" in lowered or "cny" in lowered:
        return "RMB"
    if "usd" in lowered:
        return "USD"
    if "x" in haystack or "倍" in haystack:
        return "x"
    return ""


def _extract_numeric_tokens(text: str) -> List[str]:
    tokens: List[str] = []
    for match in NUMBER_RE.finditer(_norm_text(text)):
        token = match.group(0).strip().strip("|")
        if not token:
            continue
        if token in {"-", "--"}:
            continue
        tokens.append(token)
    return tokens


def _extract_text_value(metric: str, row_values: Sequence[str], row_text: str) -> str:
    if metric == "report_date":
        match = DATE_RE.search(row_text)
        return match.group(1) if match else ""
    if metric == "stock_code":
        code_match = re.search(r"\b\d{6}\b", row_text)
        return code_match.group(0) if code_match else ""
    if metric == "rating":
        for candidate in ["买入", "增持", "中性", "减持", "卖出", "buy", "hold", "sell"]:
            if candidate.casefold() in row_text.casefold():
                return candidate
    for cell in row_values[1:]:
        cleaned = _norm_text(cell)
        if cleaned:
            return cleaned
    return ""


def _match_metric(text: str) -> List[Dict[str, Any]]:
    lowered = _norm_text(text).casefold()
    matches: List[Dict[str, Any]] = []
    for rule in METRIC_RULES:
        for pattern in rule["patterns"]:
            if pattern.casefold() in lowered:
                matches.append(rule)
                break
    return matches


def _row_document_candidate_id(document: str, page: int, table_index: int, row_index: int, metric: str, value: str, year: str) -> str:
    digest = hashlib.sha1(
        json.dumps(
            {
                "document": document,
                "page": page,
                "table_index": table_index,
                "row_index": row_index,
                "metric": metric,
                "value": value,
                "year": year,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return f"336a::{digest[:20]}"


def _route_candidate(
    *,
    metric: str,
    value_type: str,
    metric_hits: int,
    value: str,
    year: str,
    unit: str,
    source_page: Any,
    candidate_count_from_row: int,
) -> tuple[str, str]:
    if metric_hits > 1:
        return "rejected_or_excluded", "multiple_metric_hits"
    if not source_page:
        return "needs_review", "missing_source_page"
    if value_type == "numeric":
        if not value:
            return "needs_review", "missing_numeric_value"
        if candidate_count_from_row > 1 and not year:
            return "needs_review", "multiple_values_without_year"
        if metric in {"gross_margin", "net_margin", "ROE", "YoY"} and not unit and "%" not in value:
            return "needs_review", "percent_like_metric_without_unit"
        return "reviewed", "clear_metric_and_value"
    if not value:
        return "needs_review", "missing_text_value"
    return "reviewed", "clear_text_value"


def _build_customer_row(
    *,
    row_no: int,
    document: str,
    metric: str,
    metric_display_zh: str,
    year: str,
    value: str,
    unit: str,
    source_page: Any,
    status: str,
    source_evidence_excerpt: str,
    notes: str,
) -> Dict[str, Any]:
    return {
        "row_no": row_no,
        "document": document,
        "metric": metric,
        "metric_display_zh": metric_display_zh,
        "year": year,
        "value": value,
        "unit": unit,
        "source_page": source_page,
        "status": status,
        "source_evidence_excerpt": source_evidence_excerpt,
        "notes": notes,
    }


def _customer_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Workbook purpose",
            "message": "This workbook is a local test preview generated directly from raw financial research PDFs.",
        },
        {
            "topic": "Reviewed rows",
            "message": "Reviewed rows are the clearest preview rows in this local test run, but they still need human judgment before external use.",
        },
        {
            "topic": "Needs review rows",
            "message": "Needs review rows were kept because the metric, year, unit, or value was not clear enough for a safer preview decision.",
        },
        {
            "topic": "Rejected or excluded rows",
            "message": "Rejected or excluded rows are shown for transparency and should not be treated as trusted output.",
        },
        {
            "topic": "Boundaries",
            "message": "This is local test output only. It is not client-ready, not production-ready, and not investment advice.",
        },
        {
            "topic": "Traceability",
            "message": "Each row keeps document, page, and short evidence text so the source PDF can be checked manually.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _parse_table_block(
    *,
    document: str,
    table_block: Mapping[str, Any],
    page_text: str,
) -> List[Dict[str, Any]]:
    df = table_block.get("df")
    if not isinstance(df, pd.DataFrame) or df.empty:
        return []

    cleaned_df = _clean_frame(df)
    column_headers = [
        _norm_text(cleaned_df.iloc[0, idx]) if cleaned_df.shape[0] >= 1 else ""
        for idx in range(cleaned_df.shape[1])
    ]
    second_row_headers = [
        _norm_text(cleaned_df.iloc[1, idx]) if cleaned_df.shape[0] >= 2 else ""
        for idx in range(cleaned_df.shape[1])
    ]
    header_years = [
        _extract_year(f"{column_headers[idx]} {second_row_headers[idx]}")
        for idx in range(cleaned_df.shape[1])
    ]
    start_row = 1 if any(header_years) else 0

    candidates: List[Dict[str, Any]] = []
    for row_index in range(start_row, cleaned_df.shape[0]):
        row_values = [_norm_text(value) for value in cleaned_df.iloc[row_index].tolist()]
        if not any(row_values):
            continue
        first_cells_text = " | ".join(value for value in row_values[:2] if value)
        row_text = " | ".join(value for value in row_values if value)
        match_source_text = first_cells_text or row_text
        metric_matches = _match_metric(match_source_text)
        if not metric_matches:
            continue

        unique_metrics = {rule["metric"]: rule for rule in metric_matches}
        if len(unique_metrics) > 1:
            primary_rule = list(unique_metrics.values())[0]
            candidate_id = _row_document_candidate_id(
                document,
                _safe_int(table_block.get("page")),
                _safe_int(table_block.get("table_index")),
                row_index,
                primary_rule["metric"],
                "",
                "",
            )
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "document": document,
                    "metric": primary_rule["metric"],
                    "metric_display_zh": primary_rule["metric_display_zh"],
                    "year": "",
                    "value": "",
                    "unit": "",
                    "source_page": table_block.get("page", ""),
                    "status": "rejected_or_excluded",
                    "source_evidence_excerpt": _truncate(row_text),
                    "notes": "Multiple metric labels were detected in the same row.",
                    "table_index": table_block.get("table_index", ""),
                    "row_index": row_index,
                    "routing_reason": "multiple_metric_hits",
                    "metric_match_count": len(unique_metrics),
                    "page_text_excerpt": _truncate(page_text),
                }
            )
            continue

        rule = list(unique_metrics.values())[0]
        if rule["value_type"] == "numeric":
            numeric_candidates: List[Dict[str, Any]] = []
            for col_index, cell_text in enumerate(row_values):
                if not cell_text:
                    continue
                numeric_tokens = _extract_numeric_tokens(cell_text)
                if not numeric_tokens:
                    continue
                header_text = ""
                if col_index < len(column_headers):
                    header_text = f"{column_headers[col_index]} {second_row_headers[col_index]}".strip()
                year = ""
                if col_index < len(header_years):
                    year = header_years[col_index]
                if not year:
                    year = _extract_year(f"{header_text} {row_text}")
                value = numeric_tokens[0]
                unit = _extract_unit(cell_text, header_text, row_text)
                numeric_candidates.append(
                    {
                        "col_index": col_index,
                        "value": value,
                        "year": year,
                        "unit": unit,
                        "header_text": header_text,
                    }
                )

            if not numeric_candidates:
                candidate_id = _row_document_candidate_id(
                    document,
                    _safe_int(table_block.get("page")),
                    _safe_int(table_block.get("table_index")),
                    row_index,
                    rule["metric"],
                    "",
                    _extract_year(row_text),
                )
                candidates.append(
                    {
                        "candidate_id": candidate_id,
                        "document": document,
                        "metric": rule["metric"],
                        "metric_display_zh": rule["metric_display_zh"],
                        "year": _extract_year(row_text),
                        "value": "",
                        "unit": _extract_unit(row_text),
                        "source_page": table_block.get("page", ""),
                        "status": "needs_review",
                        "source_evidence_excerpt": _truncate(row_text),
                        "notes": "Metric label found but numeric value was not clear enough.",
                        "table_index": table_block.get("table_index", ""),
                        "row_index": row_index,
                        "routing_reason": "missing_numeric_value",
                        "metric_match_count": 1,
                        "page_text_excerpt": _truncate(page_text),
                    }
                )
                continue

            for candidate in numeric_candidates:
                status, routing_reason = _route_candidate(
                    metric=rule["metric"],
                    value_type="numeric",
                    metric_hits=1,
                    value=candidate["value"],
                    year=candidate["year"],
                    unit=candidate["unit"],
                    source_page=table_block.get("page", ""),
                    candidate_count_from_row=len(numeric_candidates),
                )
                candidate_id = _row_document_candidate_id(
                    document,
                    _safe_int(table_block.get("page")),
                    _safe_int(table_block.get("table_index")),
                    row_index,
                    rule["metric"],
                    candidate["value"],
                    candidate["year"],
                )
                note_map = {
                    "clear_metric_and_value": "Clear metric row and plausible value found.",
                    "multiple_values_without_year": "Multiple values were found but the year was not clear.",
                    "percent_like_metric_without_unit": "Percent-like metric found but unit was not clear.",
                }
                candidates.append(
                    {
                        "candidate_id": candidate_id,
                        "document": document,
                        "metric": rule["metric"],
                        "metric_display_zh": rule["metric_display_zh"],
                        "year": candidate["year"],
                        "value": candidate["value"],
                        "unit": candidate["unit"],
                        "source_page": table_block.get("page", ""),
                        "status": status,
                        "source_evidence_excerpt": _truncate(row_text),
                        "notes": note_map.get(routing_reason, routing_reason.replace("_", " ")),
                        "table_index": table_block.get("table_index", ""),
                        "row_index": row_index,
                        "routing_reason": routing_reason,
                        "metric_match_count": 1,
                        "page_text_excerpt": _truncate(page_text),
                    }
                )
            continue

        value = _extract_text_value(rule["metric"], row_values, row_text)
        status, routing_reason = _route_candidate(
            metric=rule["metric"],
            value_type="text",
            metric_hits=1,
            value=value,
            year=_extract_year(row_text),
            unit="",
            source_page=table_block.get("page", ""),
            candidate_count_from_row=1,
        )
        candidate_id = _row_document_candidate_id(
            document,
            _safe_int(table_block.get("page")),
            _safe_int(table_block.get("table_index")),
            row_index,
            rule["metric"],
            value,
            _extract_year(row_text),
        )
        candidates.append(
            {
                "candidate_id": candidate_id,
                "document": document,
                "metric": rule["metric"],
                "metric_display_zh": rule["metric_display_zh"],
                "year": _extract_year(row_text),
                "value": value,
                "unit": "",
                "source_page": table_block.get("page", ""),
                "status": status,
                "source_evidence_excerpt": _truncate(row_text),
                "notes": "Text-style metric candidate from table row.",
                "table_index": table_block.get("table_index", ""),
                "row_index": row_index,
                "routing_reason": routing_reason,
                "metric_match_count": 1,
                "page_text_excerpt": _truncate(page_text),
            }
        )
    return candidates


def _build_candidate_frames(candidates: Sequence[Mapping[str, Any]]) -> Dict[str, pd.DataFrame]:
    reviewed_rows: List[Dict[str, Any]] = []
    needs_review_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    trace_rows: List[Dict[str, Any]] = []

    reviewed_no = 1
    review_no = 1
    rejected_no = 1
    for candidate in candidates:
        base_row = _build_customer_row(
            row_no=0,
            document=_norm_text(candidate.get("document")),
            metric=_norm_text(candidate.get("metric")),
            metric_display_zh=_norm_text(candidate.get("metric_display_zh")),
            year=_norm_text(candidate.get("year")),
            value=_norm_text(candidate.get("value")),
            unit=_norm_text(candidate.get("unit")),
            source_page=candidate.get("source_page", ""),
            status=_norm_text(candidate.get("status")),
            source_evidence_excerpt=_norm_text(candidate.get("source_evidence_excerpt")),
            notes=_norm_text(candidate.get("notes")),
        )
        status = _norm_text(candidate.get("status"))
        if status == "reviewed":
            base_row["row_no"] = reviewed_no
            reviewed_no += 1
            reviewed_rows.append(base_row)
        elif status == "needs_review":
            base_row["row_no"] = review_no
            review_no += 1
            needs_review_rows.append(base_row)
        else:
            base_row["row_no"] = rejected_no
            rejected_no += 1
            rejected_rows.append(base_row)

        trace_rows.append(
            {
                "candidate_id": _norm_text(candidate.get("candidate_id")),
                "document": _norm_text(candidate.get("document")),
                "metric": _norm_text(candidate.get("metric")),
                "metric_display_zh": _norm_text(candidate.get("metric_display_zh")),
                "year": _norm_text(candidate.get("year")),
                "value": _norm_text(candidate.get("value")),
                "unit": _norm_text(candidate.get("unit")),
                "source_page": candidate.get("source_page", ""),
                "status": status,
                "routing_reason": _norm_text(candidate.get("routing_reason")),
                "table_index": candidate.get("table_index", ""),
                "row_index": candidate.get("row_index", ""),
                "source_evidence_excerpt": _norm_text(candidate.get("source_evidence_excerpt")),
                "page_text_excerpt": _norm_text(candidate.get("page_text_excerpt")),
                "notes": _norm_text(candidate.get("notes")),
            }
        )

    return {
        "reviewed": _clean_frame(pd.DataFrame(reviewed_rows)),
        "needs_review": _clean_frame(pd.DataFrame(needs_review_rows)),
        "rejected": _clean_frame(pd.DataFrame(rejected_rows)),
        "trace": _clean_frame(pd.DataFrame(trace_rows)),
    }


def _build_run_summary_df(pdf_rows: Sequence[Mapping[str, Any]], summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "section": "run_summary",
            "document": "",
            "metric": "pdf_found_count",
            "value": summary.get("pdf_found_count", 0),
            "notes": "Total PDFs discovered in the input folder.",
        },
        {
            "section": "run_summary",
            "document": "",
            "metric": "pdf_processed_count",
            "value": summary.get("pdf_processed_count", 0),
            "notes": "PDFs processed without a document-level extractor crash.",
        },
        {
            "section": "run_summary",
            "document": "",
            "metric": "reviewed_count",
            "value": summary.get("reviewed_count", 0),
            "notes": "Rows routed into reviewed core metrics.",
        },
        {
            "section": "run_summary",
            "document": "",
            "metric": "needs_review_count",
            "value": summary.get("needs_review_count", 0),
            "notes": "Rows routed into needs review.",
        },
        {
            "section": "run_summary",
            "document": "",
            "metric": "rejected_or_excluded_count",
            "value": summary.get("rejected_or_excluded_count", 0),
            "notes": "Rows routed into rejected or excluded.",
        },
    ]
    for pdf_row in pdf_rows:
        rows.append(
            {
                "section": "per_pdf",
                "document": pdf_row.get("document", ""),
                "metric": "extracted_metric_row_count",
                "value": pdf_row.get("extracted_metric_row_count", 0),
                "notes": f"reviewed={pdf_row.get('reviewed_count', 0)}; needs_review={pdf_row.get('needs_review_count', 0)}; rejected={pdf_row.get('rejected_or_excluded_count', 0)}",
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _qa_record(name: str, passed: bool, detail: str) -> Dict[str, Any]:
    return {"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def build_real_test_full_flow_336a(
    *,
    input_pdf_dir: Path,
    output_dir: Path,
    extraction_fn: Callable[..., List[Dict[str, Any]]] | None = None,
    page_text_fn: Callable[[Path], tuple[Dict[int, str], List[Dict[str, Any]], int | None]] | None = None,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    extraction_callable = extraction_fn or extract_tables_from_pdf
    page_text_callable = page_text_fn or _extract_page_texts

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)

    pdf_paths = _find_pdf_files(input_pdf_dir)
    extractor_available = True
    extractor_error = ""
    all_candidates: List[Dict[str, Any]] = []
    pdf_rows: List[Dict[str, Any]] = []
    pdf_failures: List[Dict[str, Any]] = []
    page_failures: List[Dict[str, Any]] = []
    blocked_reasons: List[str] = []

    if not pdf_paths:
        blocked_reasons.append("No PDF files were found in the input folder.")

    for pdf_path in pdf_paths:
        page_texts, page_text_failures, total_pages = page_text_callable(pdf_path)
        page_failures.extend(page_text_failures)
        try:
            table_blocks = extraction_callable(str(pdf_path), pages="all", logger=None, config=None) or []
        except Exception as exc:
            extractor_available = False
            extractor_error = str(exc)
            pdf_failures.append(
                {
                    "document": pdf_path.name,
                    "stage": "table_extraction",
                    "error": str(exc),
                }
            )
            table_blocks = []

        document_candidates: List[Dict[str, Any]] = []
        if table_blocks:
            for table_block in table_blocks:
                page_no = _safe_int(table_block.get("page"), 0)
                page_text = page_texts.get(page_no, "")
                document_candidates.extend(
                    _parse_table_block(
                        document=pdf_path.name,
                        table_block=table_block,
                        page_text=page_text,
                    )
                )
        elif not page_text_failures:
            pdf_failures.append(
                {
                    "document": pdf_path.name,
                    "stage": "table_extraction",
                    "error": "No normalized table blocks were extracted.",
                }
            )

        all_candidates.extend(document_candidates)
        reviewed_count = sum(1 for row in document_candidates if row.get("status") == "reviewed")
        needs_review_count = sum(1 for row in document_candidates if row.get("status") == "needs_review")
        rejected_count = sum(1 for row in document_candidates if row.get("status") == "rejected_or_excluded")
        extracted_metric_row_count = len(document_candidates)
        pdf_rows.append(
            {
                "document": pdf_path.name,
                "file_size_bytes": pdf_path.stat().st_size,
                "page_count": total_pages if total_pages is not None else "",
                "table_block_count": len(table_blocks),
                "extracted_metric_row_count": extracted_metric_row_count,
                "reviewed_count": reviewed_count,
                "needs_review_count": needs_review_count,
                "rejected_or_excluded_count": rejected_count,
                "document_status": "processed" if table_blocks or page_texts else "failed",
            }
        )

    if not extractor_available and not pdf_paths:
        blocked_reasons.append("The lightweight raw-PDF path did not run and no PDFs were available.")
    elif not extractor_available and extractor_error:
        blocked_reasons.append(f"Raw-PDF extraction failed: {extractor_error}")

    frames = _build_candidate_frames(all_candidates)
    reviewed_count = len(frames["reviewed"])
    needs_review_count = len(frames["needs_review"])
    rejected_count = len(frames["rejected"])

    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])

    qa_checks: List[Dict[str, Any]] = []
    qa_checks.append(_qa_record("input_dir_exists", input_pdf_dir.exists(), str(input_pdf_dir)))
    qa_checks.append(_qa_record("pdf_found_count_gt_zero", len(pdf_paths) > 0, str(len(pdf_paths))))
    qa_checks.append(_qa_record("extractor_callable_available", extraction_callable is not None, extraction_callable.__name__ if extraction_callable else "missing"))
    qa_checks.append(_qa_record("official_assets_unchanged", official_assets_before == official_assets_after, json.dumps(official_assets_after, ensure_ascii=False)))
    qa_checks.append(_qa_record("protected_dirty_status_preserved", protected_status_before == protected_status_after, json.dumps(protected_status_after, ensure_ascii=False)))
    qa_checks.append(_qa_record("protected_dirty_paths_not_staged", not protected_cached_after, json.dumps(protected_cached_after, ensure_ascii=False)))
    qa_checks.append(_qa_record("workbook_target_name_defined", True, "real_test_client_export_336a.xlsx"))

    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")

    if blocked_reasons:
        decision = BLOCKED_DECISION
    elif qa_fail_count == 0 and len(pdf_paths) == sum(1 for row in pdf_rows if row["document_status"] == "processed"):
        decision = READY_DECISION
    else:
        decision = PARTIAL_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "project_status": "LOCAL_REAL_TEST_PREVIEW_ONLY",
        "client_ready": False,
        "production_ready": False,
        "input_pdf_dir": str(input_pdf_dir),
        "output_dir": str(output_dir),
        "pdf_found_count": len(pdf_paths),
        "pdf_processed_count": sum(1 for row in pdf_rows if row["document_status"] == "processed"),
        "reviewed_count": reviewed_count,
        "needs_review_count": needs_review_count,
        "rejected_or_excluded_count": rejected_count,
        "page_failure_count": len(page_failures),
        "pdf_failure_count": len(pdf_failures),
        "no_official_asset_modification_during_336a": official_assets_before == official_assets_after,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "336A_real_test_full_flow_from_pdf_folder",
        "input_pdf_dir": str(input_pdf_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "real_test_full_flow_336a_summary.json"),
            "manifest_json": str(output_dir / "real_test_full_flow_336a_manifest.json"),
            "qa_json": str(output_dir / "real_test_full_flow_336a_qa.json"),
            "report_md": str(output_dir / "real_test_full_flow_336a_report.md"),
            "preview_xlsx": str(output_dir / "real_test_client_export_336a.xlsx"),
        },
        "pdf_inventory": pdf_rows,
    }

    qa_json = {
        "decision": decision,
        "qa_fail_count": qa_fail_count,
        "checks": qa_checks,
        "blocked_reasons": blocked_reasons,
        "pdf_failures": pdf_failures,
        "page_failures": page_failures,
        "protected_dirty_status_before": protected_status_before,
        "protected_dirty_status_after": protected_status_after,
        "protected_dirty_cached_after": protected_cached_after,
    }

    no_apply_proof_json = build_no_apply_proof(
        stage="336A",
        files_read=[
            str(path) for path in pdf_paths
        ] + [
            str(alias_asset_path),
            str(scope_asset_path),
        ],
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    run_summary_df = _build_run_summary_df(pdf_rows, summary)
    pdf_inventory_df = _clean_frame(pd.DataFrame(pdf_rows))
    if not pdf_inventory_df.empty:
        pdf_inventory_df.insert(0, "section", "pdf_inventory")
        run_summary_df = _clean_frame(pd.concat([run_summary_df, pdf_inventory_df], ignore_index=True))

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "readme_df": _customer_readme_df(),
        "reviewed_df": frames["reviewed"],
        "needs_review_df": frames["needs_review"],
        "rejected_df": frames["rejected"],
        "source_trace_df": frames["trace"],
        "run_summary_df": run_summary_df,
        "pdf_rows": pdf_rows,
        "pdf_failures": pdf_failures,
        "page_failures": page_failures,
    }
