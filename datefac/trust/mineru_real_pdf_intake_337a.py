from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

from datefac.parser.mineru_output_reader import MineruReadResult, read_mineru_output
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    capture_official_asset_hashes,
)


READY_DECISION = "MINERU_FIRST_REAL_PDF_INTAKE_337A_READY"
PARTIAL_DECISION = "MINERU_FIRST_REAL_PDF_INTAKE_337A_PARTIAL"
BLOCKED_DECISION = "MINERU_FIRST_REAL_PDF_INTAKE_337A_BLOCKED"

DEFAULT_INPUT_PDF_DIR = Path(r"D:\_datefac\input\real_test")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\mineru_real_test_337a")
DEFAULT_MINERU_EXE = Path(r"D:\anaconda\envs\mineru_new\Scripts\mineru.exe")
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

COMBINED_WORKBOOK_SHEETS = {
    "readme": "00_README",
    "reviewed": "01_REVIEWED_CORE_METRICS",
    "needs_review": "02_NEEDS_REVIEW",
    "rejected": "03_REJECTED_OR_EXCLUDED",
    "trace": "04_SOURCE_TRACE",
    "document_summary": "05_DOCUMENT_SUMMARY",
    "financial_tables": "06_FINANCIAL_TABLE_CANDIDATES",
}

FINANCIAL_TABLE_KEYWORDS = [
    "财务数据",
    "估值",
    "财务摘要",
    "盈利预测",
    "营业收入",
    "归母净利润",
    "净利润",
    "EPS",
    "每股收益",
    "PE",
    "P/E",
    "PB",
    "P/B",
    "ROE",
    "毛利率",
    "净利率",
    "同比",
    "2024A",
    "2025A",
    "2026E",
    "2027E",
    "2028E",
]

REJECT_KEYWORDS = [
    "免责声明",
    "投资评级说明",
    "评级体系",
    "分析师承诺",
    "风险评级",
    "禁止",
    "转载",
    "版权",
    "免责",
]

METRIC_RULES: List[Dict[str, Any]] = [
    {"metric": "revenue", "metric_display_zh": "营业收入", "patterns": ["营业收入", "主营收入", "revenue", "sales"], "value_type": "numeric"},
    {"metric": "net_profit", "metric_display_zh": "归母净利润", "patterns": ["归母净利润", "归母净利", "净利润", "parent net profit", "net profit"], "value_type": "numeric"},
    {"metric": "EPS", "metric_display_zh": "每股收益", "patterns": ["eps", "每股收益", "每股盈利", "diluted eps"], "value_type": "numeric"},
    {"metric": "PE", "metric_display_zh": "市盈率", "patterns": ["pe", "p/e", "市盈率"], "value_type": "numeric"},
    {"metric": "PB", "metric_display_zh": "市净率", "patterns": ["pb", "p/b", "市净率"], "value_type": "numeric"},
    {"metric": "ROE", "metric_display_zh": "净资产收益率", "patterns": ["roe", "净资产收益率"], "value_type": "numeric"},
    {"metric": "gross_margin", "metric_display_zh": "毛利率", "patterns": ["毛利率", "gross margin"], "value_type": "numeric"},
    {"metric": "net_margin", "metric_display_zh": "净利率", "patterns": ["净利率", "net margin"], "value_type": "numeric"},
    {"metric": "YoY", "metric_display_zh": "同比", "patterns": ["同比", "同比增长", "yoy", "year on year", "year-over-year"], "value_type": "numeric"},
    {"metric": "rating", "metric_display_zh": "投资评级", "patterns": ["投资评级", "评级", "buy", "hold", "sell", "买入", "增持", "中性"], "value_type": "text"},
    {"metric": "report_date", "metric_display_zh": "报告日期", "patterns": ["报告日期", "发布日期", "report date"], "value_type": "text"},
    {"metric": "broker", "metric_display_zh": "机构", "patterns": ["证券", "研究所", "broker", "institution"], "value_type": "text"},
    {"metric": "stock_code", "metric_display_zh": "股票代码", "patterns": ["股票代码", "证券代码", "stock code", "ticker"], "value_type": "text"},
    {"metric": "stock_name", "metric_display_zh": "股票名称", "patterns": ["股票名称", "公司名称", "stock name", "company name"], "value_type": "text"},
]

YEAR_RE = re.compile(r"(20\d{2}|19\d{2})(?:[AE])?")
DATE_RE = re.compile(r"(20\d{2}[/-]\d{1,2}[/-]\d{1,2}|20\d{2}年\d{1,2}月\d{1,2}日)")
NUMBER_RE = re.compile(r"(?<![\w/])[-+]?\d[\d,]*(?:\.\d+)?%?(?:x|X)?")
BROKER_RE = re.compile(r"([\u4e00-\u9fffA-Za-z]{2,30}(?:证券|研究所))")
STOCK_CODE_RE = re.compile(r"\b(\d{6})(?:\.(?:SH|SZ|BJ))?\b")
STOCK_NAME_WITH_CODE_RE = re.compile(r"([\u4e00-\u9fffA-Za-z]{2,20})\s*\(?\s*(\d{6}\.(?:SH|SZ|BJ))\s*\)?")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _truncate(value: Any, limit: int = 240) -> str:
    text = _norm_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


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


def _contains_any(text: str, patterns: Sequence[str]) -> bool:
    lowered = _norm_text(text).casefold()
    return any(pattern.casefold() in lowered for pattern in patterns)


def _extract_year(text: str) -> str:
    match = YEAR_RE.search(_norm_text(text))
    return match.group(0) if match else ""


def _extract_numeric_tokens(text: str) -> List[str]:
    values: List[str] = []
    for match in NUMBER_RE.finditer(_norm_text(text)):
        token = match.group(0).strip()
        if not token or token in {"-", "--"}:
            continue
        values.append(token)
    return values


def _extract_unit(*texts: str) -> str:
    haystack = " ".join(_norm_text(text) for text in texts if _norm_text(text))
    lowered = haystack.casefold()
    if "%" in haystack or "pct" in lowered or "percent" in lowered:
        return "%"
    if "百万元" in haystack:
        return "百万元"
    if "千万元" in haystack:
        return "千万元"
    if "亿元" in haystack:
        return "亿元"
    if "万元" in haystack:
        return "万元"
    if "元/股" in haystack:
        return "元/股"
    if "元" in haystack:
        return "元"
    if "x" in haystack or "倍" in haystack:
        return "x"
    if "rmb" in lowered or "cny" in lowered:
        return "RMB"
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


def _candidate_id(*, document: str, page_no: int, table_index: int, row_index: int, metric: str, year: str, value: str) -> str:
    digest = hashlib.sha1(
        json.dumps(
            {
                "document": document,
                "page_no": page_no,
                "table_index": table_index,
                "row_index": row_index,
                "metric": metric,
                "year": year,
                "value": value,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return f"337a::{digest[:20]}"


def _customer_readme_df() -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {"topic": "Workbook purpose", "message": "This workbook is a local preview built from raw PDFs through MinerU-first parsing and conservative DateFac-side routing."},
                {"topic": "Reviewed rows", "message": "Reviewed rows are clearer preview rows only. They are not client-ready and still require human judgment."},
                {"topic": "Needs review rows", "message": "Needs review rows were kept because unit, year, value, or source context was not strong enough."},
                {"topic": "Rejected rows", "message": "Rejected or excluded rows are shown for traceability and should not be treated as trusted output."},
                {"topic": "Boundaries", "message": "This output is local-only, sidecar-only, not production-ready, not client-ready, and not investment advice."},
            ]
        )
    )


def _manual_mineru_command(pdf_path: Path, mineru_outputs_root: Path, mineru_exe: Path) -> str:
    return f"{mineru_exe} -p {pdf_path} -o {mineru_outputs_root} -b pipeline -m auto -l ch"


def _discover_parse_dir(mineru_outputs_root: Path, pdf_stem: str) -> Optional[Path]:
    direct = mineru_outputs_root / pdf_stem / "auto"
    if direct.exists():
        return direct
    parent = mineru_outputs_root / pdf_stem
    if parent.exists():
        auto_children = [path for path in parent.iterdir() if path.is_dir()]
        if len(auto_children) == 1:
            return auto_children[0]
    return None


def _parse_dir_ready(parse_dir: Path) -> bool:
    if not parse_dir.exists():
        return False
    return any(parse_dir.glob("*_content_list.json")) or any(parse_dir.glob("*_content_list_v2.json")) or any(parse_dir.glob("*.md"))


def _default_mineru_runner(pdf_path: Path, mineru_outputs_root: Path, mineru_exe: Path) -> Dict[str, Any]:
    parse_dir = _discover_parse_dir(mineru_outputs_root, pdf_path.stem)
    manual_command = _manual_mineru_command(pdf_path, mineru_outputs_root, mineru_exe)
    if parse_dir and _parse_dir_ready(parse_dir):
        return {
            "success": True,
            "parse_dir": parse_dir,
            "status": "reused_existing_output",
            "stdout": "",
            "stderr": "",
            "manual_command": manual_command,
            "returncode": 0,
        }
    if not mineru_exe.exists():
        return {
            "success": False,
            "parse_dir": parse_dir,
            "status": "mineru_executable_missing",
            "stdout": "",
            "stderr": f"MinerU executable not found: {mineru_exe}",
            "manual_command": manual_command,
            "returncode": None,
        }
    result = subprocess.run(
        [
            str(mineru_exe),
            "-p",
            str(pdf_path),
            "-o",
            str(mineru_outputs_root),
            "-b",
            "pipeline",
            "-m",
            "auto",
            "-l",
            "ch",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    parse_dir = _discover_parse_dir(mineru_outputs_root, pdf_path.stem)
    success = result.returncode == 0 and bool(parse_dir and _parse_dir_ready(parse_dir))
    return {
        "success": success,
        "parse_dir": parse_dir,
        "status": "ran_mineru" if success else "mineru_run_failed",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "manual_command": manual_command,
        "returncode": result.returncode,
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def _flatten_text_node(node: Any) -> str:
    if isinstance(node, str):
        return _norm_text(node)
    if isinstance(node, dict):
        if "text" in node and isinstance(node["text"], str):
            return _norm_text(node["text"])
        if "content" in node and isinstance(node["content"], str):
            return _norm_text(node["content"])
        if "paragraph_content" in node and isinstance(node["paragraph_content"], list):
            return " ".join(filter(None, (_flatten_text_node(item) for item in node["paragraph_content"]))).strip()
        if "content" in node and isinstance(node["content"], dict):
            nested = node["content"]
            if "paragraph_content" in nested and isinstance(nested["paragraph_content"], list):
                return " ".join(filter(None, (_flatten_text_node(item) for item in nested["paragraph_content"]))).strip()
            return _flatten_text_node(nested)
        return " ".join(filter(None, (_flatten_text_node(value) for value in node.values()))).strip()
    if isinstance(node, list):
        return " ".join(filter(None, (_flatten_text_node(item) for item in node))).strip()
    return ""


def _collect_page_text_from_content_list(parse_dir: Path) -> Tuple[Dict[int, str], List[Dict[str, Any]]]:
    page_lines: Dict[int, List[str]] = {}
    raw_rows: List[Dict[str, Any]] = []
    json_files = sorted(parse_dir.glob("*_content_list.json"))
    if not json_files:
        return {}, []
    payload = _load_json(json_files[0])

    def walk(node: Any, inherited_page: Optional[int] = None) -> None:
        if isinstance(node, dict):
            page_no = inherited_page
            if "page_idx" in node:
                page_no = _safe_int(node.get("page_idx"), 0) + 1
            text = ""
            node_type = _norm_text(node.get("type"))
            if node_type in {"text", "paragraph"}:
                text = _flatten_text_node(node)
            elif "text" in node or "paragraph_content" in node or "content" in node:
                text = _flatten_text_node(node)
            if page_no and text:
                page_lines.setdefault(page_no, []).append(text)
                raw_rows.append(
                    {
                        "page_no": page_no,
                        "node_type": node_type or "unknown",
                        "text_excerpt": _truncate(text, 200),
                    }
                )
            for value in node.values():
                walk(value, page_no)
            return
        if isinstance(node, list):
            for item in node:
                walk(item, inherited_page)

    walk(payload, None)
    page_texts = {page_no: " ".join(lines).strip() for page_no, lines in page_lines.items()}
    return page_texts, raw_rows


def _extract_markdown_fallback(parse_dir: Path) -> str:
    markdown_files = sorted(parse_dir.glob("*.md"))
    if not markdown_files:
        return ""
    return _norm_text(markdown_files[0].read_text(encoding="utf-8", errors="ignore"))


def _parse_html_table(html: str) -> List[pd.DataFrame]:
    text = _norm_text(html)
    if not text or "<table" not in text.lower():
        return []
    try:
        frames = pd.read_html(StringIO(text))
    except Exception:
        return []
    return [_clean_frame(frame) for frame in frames if isinstance(frame, pd.DataFrame) and not frame.empty]


def _table_preview(df: pd.DataFrame, limit_rows: int = 5) -> str:
    if df.empty:
        return ""
    preview_rows = []
    for _, row in df.head(limit_rows).iterrows():
        row_values = [_norm_text(value) for value in row.tolist() if _norm_text(value)]
        if row_values:
            preview_rows.append(" | ".join(row_values))
    return "\n".join(preview_rows)


def _build_financial_table_rows(document: str, result: MineruReadResult) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[int, int]]:
    all_rows: List[Dict[str, Any]] = []
    candidate_rows: List[Dict[str, Any]] = []
    likely_page_scores: Dict[int, int] = {}
    for table_index, asset in enumerate(result.table_assets, start=1):
        raw_block = asset.extra.get("raw_block", {}) if isinstance(asset.extra, dict) else {}
        table_html = ""
        if isinstance(raw_block, dict):
            table_html = _norm_text(raw_block.get("table_body") or raw_block.get("html") or raw_block.get("table_html"))
        if not table_html:
            table_html = _norm_text(asset.extra.get("table_html_preview")) if isinstance(asset.extra, dict) else ""
        frames = _parse_html_table(table_html)
        row_count = sum(len(frame.index) for frame in frames)
        col_count = max((len(frame.columns) for frame in frames), default=0)
        context_text = " ".join(
            filter(
                None,
                [
                    asset.caption,
                    asset.footnote,
                    asset.nearby_text,
                    table_html[:2000],
                ],
            )
        )
        matched_keywords = [keyword for keyword in FINANCIAL_TABLE_KEYWORDS if keyword.casefold() in context_text.casefold()]
        candidate_score = len(matched_keywords)
        if asset.table_role_guess and "financial" in asset.table_role_guess.casefold():
            candidate_score += 3
        if frames and any(frame.shape[1] >= 3 for frame in frames):
            candidate_score += 1
        if frames and any("2026E" in _table_preview(frame, 2) or "2027E" in _table_preview(frame, 2) for frame in frames):
            candidate_score += 2
        page_no = (_safe_int(asset.page_idx, -1) + 1) if asset.page_idx is not None else ""
        preview = _table_preview(frames[0], 6) if frames else _truncate(table_html, 400)
        row = {
            "document": document,
            "page_no": page_no,
            "table_index": table_index,
            "source_kind": asset.source_kind,
            "table_role_guess": asset.table_role_guess,
            "table_role_reason": asset.table_role_reason,
            "caption": asset.caption,
            "footnote": asset.footnote,
            "nearby_text": asset.nearby_text,
            "image_path": asset.image_path,
            "matched_keywords": ", ".join(matched_keywords),
            "candidate_score": candidate_score,
            "html_present": bool(table_html),
            "parsed_frame_count": len(frames),
            "row_count": row_count,
            "col_count": col_count,
            "table_preview": preview,
        }
        all_rows.append(row)
        if candidate_score > 0:
            candidate_rows.append(row)
            if isinstance(page_no, int) and page_no > 0:
                likely_page_scores[page_no] = likely_page_scores.get(page_no, 0) + candidate_score
    candidate_rows.sort(key=lambda item: (-_safe_int(item["candidate_score"]), _safe_int(item["page_no"], 9999), _safe_int(item["table_index"], 9999)))
    return all_rows, candidate_rows, likely_page_scores


def _build_extracted_tables_rows(document: str, result: MineruReadResult) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table_index, asset in enumerate(result.table_assets, start=1):
        raw_block = asset.extra.get("raw_block", {}) if isinstance(asset.extra, dict) else {}
        table_html = ""
        if isinstance(raw_block, dict):
            table_html = _norm_text(raw_block.get("table_body") or raw_block.get("html") or raw_block.get("table_html"))
        frames = _parse_html_table(table_html)
        rows.append(
            {
                "document": document,
                "page_no": (_safe_int(asset.page_idx, -1) + 1) if asset.page_idx is not None else "",
                "table_index": table_index,
                "source_kind": asset.source_kind,
                "table_role_guess": asset.table_role_guess,
                "caption": asset.caption,
                "footnote": asset.footnote,
                "nearby_text": asset.nearby_text,
                "image_path": asset.image_path,
                "parsed_frame_count": len(frames),
                "row_count": sum(len(frame.index) for frame in frames),
                "col_count": max((len(frame.columns) for frame in frames), default=0),
                "table_preview": _table_preview(frames[0], 8) if frames else _truncate(table_html, 500),
            }
        )
    return rows


def _extract_text_value(metric: str, row_values: Sequence[str], row_text: str) -> str:
    if metric == "report_date":
        match = DATE_RE.search(row_text)
        return match.group(1) if match else ""
    if metric == "stock_code":
        match = STOCK_CODE_RE.search(row_text)
        return match.group(1) if match else ""
    if metric == "broker":
        match = BROKER_RE.search(row_text)
        return match.group(1) if match else ""
    if metric == "rating":
        for candidate in ["买入", "增持", "中性", "减持", "卖出", "buy", "hold", "sell"]:
            if candidate.casefold() in row_text.casefold():
                return candidate
    for cell in row_values[1:]:
        if _norm_text(cell):
            return _norm_text(cell)
    return ""


def _route_candidate(
    *,
    metric: str,
    value_type: str,
    value: str,
    year: str,
    unit: str,
    source_page: Any,
    row_text: str,
    table_score: int,
    metric_hit_count: int,
) -> Tuple[str, str]:
    normalized_text = _norm_text(row_text)
    if _contains_any(normalized_text, REJECT_KEYWORDS):
        return "rejected_or_excluded", "disclaimer_or_rating_system_noise"
    if metric_hit_count > 1:
        return "needs_review", "multiple_metric_hits"
    if not source_page:
        return "needs_review", "missing_source_page"
    if value_type == "numeric":
        if not value:
            return "needs_review", "missing_numeric_value"
        if re.fullmatch(r"(19|20)\d{2}", value):
            return "needs_review", "numeric_value_looks_like_year"
        if metric in {"gross_margin", "net_margin", "ROE", "YoY"} and not unit and "%" not in value:
            return "needs_review", "percent_metric_missing_unit"
        if metric in {"revenue", "net_profit", "EPS", "PE", "PB"} and not year:
            return "needs_review", "missing_year_for_core_metric"
        if table_score <= 0:
            return "needs_review", "weak_table_context"
        return "reviewed_preview", "clear_metric_value_year_context"
    if not value:
        return "needs_review", "missing_text_value"
    if table_score <= 0 and metric in {"rating", "broker", "stock_code", "stock_name"}:
        return "needs_review", "metadata_found_but_context_weak"
    return "reviewed_preview", "clear_text_value"


def _parse_table_metric_candidates(document: str, result: MineruReadResult) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for table_index, asset in enumerate(result.table_assets, start=1):
        raw_block = asset.extra.get("raw_block", {}) if isinstance(asset.extra, dict) else {}
        table_html = ""
        if isinstance(raw_block, dict):
            table_html = _norm_text(raw_block.get("table_body") or raw_block.get("html") or raw_block.get("table_html"))
        frames = _parse_html_table(table_html)
        context_text = " ".join(filter(None, [asset.caption, asset.footnote, asset.nearby_text, table_html[:2000]]))
        table_keywords = [keyword for keyword in FINANCIAL_TABLE_KEYWORDS if keyword.casefold() in context_text.casefold()]
        table_score = len(table_keywords)
        if asset.table_role_guess and "financial" in asset.table_role_guess.casefold():
            table_score += 3
        for frame in frames:
            if frame.empty:
                continue
            clean_frame = _clean_frame(frame)
            header_row = [_norm_text(value) for value in clean_frame.iloc[0].tolist()] if len(clean_frame.index) > 0 else []
            second_row = [_norm_text(value) for value in clean_frame.iloc[1].tolist()] if len(clean_frame.index) > 1 else []
            header_years = []
            for index in range(len(clean_frame.columns)):
                header_context = ""
                if index < len(header_row):
                    header_context += header_row[index]
                if index < len(second_row):
                    header_context += f" {second_row[index]}"
                header_years.append(_extract_year(header_context))
            start_row_index = 1 if any(header_years) else 0
            for row_index in range(start_row_index, len(clean_frame.index)):
                row_values = [_norm_text(value) for value in clean_frame.iloc[row_index].tolist()]
                if not any(row_values):
                    continue
                row_text = " | ".join(value for value in row_values if value)
                metric_rules = _match_metric(row_text)
                if not metric_rules:
                    first_cells = " | ".join(value for value in row_values[:2] if value)
                    metric_rules = _match_metric(first_cells)
                if not metric_rules:
                    continue
                unique_rules: Dict[str, Dict[str, Any]] = {rule["metric"]: rule for rule in metric_rules}
                for rule in unique_rules.values():
                    if rule["value_type"] == "numeric":
                        numeric_entries: List[Dict[str, Any]] = []
                        for col_index, cell_text in enumerate(row_values):
                            numeric_tokens = _extract_numeric_tokens(cell_text)
                            if not numeric_tokens:
                                continue
                            header_context = ""
                            if col_index < len(header_row):
                                header_context += header_row[col_index]
                            if col_index < len(second_row):
                                header_context += f" {second_row[col_index]}"
                            numeric_entries.append(
                                {
                                    "col_index": col_index,
                                    "value": numeric_tokens[0],
                                    "year": header_years[col_index] if col_index < len(header_years) else _extract_year(f"{header_context} {row_text}"),
                                    "unit": _extract_unit(cell_text, header_context, row_text),
                                    "header_context": header_context.strip(),
                                }
                            )
                        if not numeric_entries:
                            numeric_entries = [{"col_index": -1, "value": "", "year": _extract_year(row_text), "unit": _extract_unit(row_text), "header_context": ""}]
                        for numeric_entry in numeric_entries:
                            source_page = (_safe_int(asset.page_idx, -1) + 1) if asset.page_idx is not None else ""
                            status, route_reason = _route_candidate(
                                metric=rule["metric"],
                                value_type="numeric",
                                value=numeric_entry["value"],
                                year=numeric_entry["year"],
                                unit=numeric_entry["unit"],
                                source_page=source_page,
                                row_text=row_text,
                                table_score=table_score,
                                metric_hit_count=len(unique_rules),
                            )
                            value = numeric_entry["value"]
                            year = numeric_entry["year"]
                            candidate = {
                                "candidate_id": _candidate_id(
                                    document=document,
                                    page_no=_safe_int(source_page),
                                    table_index=table_index,
                                    row_index=row_index + 1,
                                    metric=rule["metric"],
                                    year=year,
                                    value=value,
                                ),
                                "document": document,
                                "metric": rule["metric"],
                                "metric_display_zh": rule["metric_display_zh"],
                                "year": year,
                                "value": value,
                                "unit": numeric_entry["unit"],
                                "source_page": source_page,
                                "status": status,
                                "route_reason": route_reason,
                                "source_evidence_excerpt": _truncate(row_text, 260),
                                "notes": route_reason.replace("_", " "),
                                "table_index": table_index,
                                "row_index": row_index + 1,
                                "source_kind": asset.source_kind,
                                "table_score": table_score,
                                "table_matched_keywords": ", ".join(table_keywords),
                                "header_context": numeric_entry["header_context"],
                            }
                            candidates.append(candidate)
                    else:
                        source_page = (_safe_int(asset.page_idx, -1) + 1) if asset.page_idx is not None else ""
                        value = _extract_text_value(rule["metric"], row_values, row_text)
                        status, route_reason = _route_candidate(
                            metric=rule["metric"],
                            value_type="text",
                            value=value,
                            year=_extract_year(row_text),
                            unit="",
                            source_page=source_page,
                            row_text=row_text,
                            table_score=table_score,
                            metric_hit_count=len(unique_rules),
                        )
                        candidates.append(
                            {
                                "candidate_id": _candidate_id(
                                    document=document,
                                    page_no=_safe_int(source_page),
                                    table_index=table_index,
                                    row_index=row_index + 1,
                                    metric=rule["metric"],
                                    year=_extract_year(row_text),
                                    value=value,
                                ),
                                "document": document,
                                "metric": rule["metric"],
                                "metric_display_zh": rule["metric_display_zh"],
                                "year": _extract_year(row_text),
                                "value": value,
                                "unit": "",
                                "source_page": source_page,
                                "status": status,
                                "route_reason": route_reason,
                                "source_evidence_excerpt": _truncate(row_text, 260),
                                "notes": route_reason.replace("_", " "),
                                "table_index": table_index,
                                "row_index": row_index + 1,
                                "source_kind": asset.source_kind,
                                "table_score": table_score,
                                "table_matched_keywords": ", ".join(table_keywords),
                                "header_context": "",
                            }
                        )
    return candidates


def _extract_document_text_candidates(document: str, page_texts: Mapping[int, str]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    combined_text = " ".join(page_texts.get(page_no, "") for page_no in sorted(page_texts)[:5])
    stock_name_code_match = STOCK_NAME_WITH_CODE_RE.search(combined_text)
    metadata_specs = [
        ("report_date", "报告日期", lambda text: DATE_RE.search(text).group(1) if DATE_RE.search(text) else ""),
        ("broker", "机构", lambda text: BROKER_RE.search(text).group(1) if BROKER_RE.search(text) else ""),
        ("stock_code", "股票代码", lambda text: stock_name_code_match.group(2) if stock_name_code_match else (STOCK_CODE_RE.search(text).group(1) if STOCK_CODE_RE.search(text) else "")),
        ("stock_name", "股票名称", lambda text: stock_name_code_match.group(1) if stock_name_code_match else ""),
        ("rating", "投资评级", lambda text: next((token for token in ["买入", "增持", "中性", "减持", "卖出"] if token in text), "")),
    ]
    for metric, metric_display_zh, extractor in metadata_specs:
        value = extractor(combined_text)
        if not value:
            continue
        first_page = min(page_texts.keys()) if page_texts else 0
        candidates.append(
            {
                "candidate_id": _candidate_id(document=document, page_no=first_page, table_index=0, row_index=0, metric=metric, year="", value=value),
                "document": document,
                "metric": metric,
                "metric_display_zh": metric_display_zh,
                "year": "",
                "value": value,
                "unit": "",
                "source_page": first_page,
                "status": "reviewed_preview",
                "route_reason": "document_level_metadata",
                "source_evidence_excerpt": _truncate(combined_text, 260),
                "notes": "document level metadata",
                "table_index": 0,
                "row_index": 0,
                "source_kind": "document_text",
                "table_score": 1,
                "table_matched_keywords": "",
                "header_context": "",
            }
        )
    return candidates


def _build_page_text_rows(document: str, page_texts: Mapping[int, str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for page_no in sorted(page_texts):
        text = _norm_text(page_texts.get(page_no, ""))
        rows.append(
            {
                "document": document,
                "page_no": page_no,
                "text_excerpt": _truncate(text, 240),
                "full_text_or_long_excerpt": _truncate(text, 4000),
                "contains_financial_keywords": _contains_any(text, FINANCIAL_TABLE_KEYWORDS),
                "contains_forecast_years": bool(re.search(r"202[4-8][AE]?", text)),
            }
        )
    return rows


def _build_candidate_frames(candidates: Sequence[Mapping[str, Any]]) -> Dict[str, pd.DataFrame]:
    reviewed_rows: List[Dict[str, Any]] = []
    needs_review_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    source_trace_rows: List[Dict[str, Any]] = []
    reviewed_no = 1
    review_no = 1
    rejected_no = 1
    for candidate in candidates:
        customer_row = {
            "row_no": 0,
            "document": _norm_text(candidate.get("document")),
            "metric": _norm_text(candidate.get("metric")),
            "metric_display_zh": _norm_text(candidate.get("metric_display_zh")),
            "year": _norm_text(candidate.get("year")),
            "value": _norm_text(candidate.get("value")),
            "unit": _norm_text(candidate.get("unit")),
            "source_page": candidate.get("source_page", ""),
            "status": _norm_text(candidate.get("status")),
            "source_evidence_excerpt": _norm_text(candidate.get("source_evidence_excerpt")),
            "notes": _norm_text(candidate.get("notes")),
        }
        status = customer_row["status"]
        if status == "reviewed_preview":
            customer_row["row_no"] = reviewed_no
            reviewed_no += 1
            reviewed_rows.append(customer_row)
        elif status == "needs_review":
            customer_row["row_no"] = review_no
            review_no += 1
            needs_review_rows.append(customer_row)
        else:
            customer_row["row_no"] = rejected_no
            rejected_no += 1
            rejected_rows.append(customer_row)
        source_trace_rows.append(
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
                "route_reason": _norm_text(candidate.get("route_reason")),
                "table_index": candidate.get("table_index", ""),
                "row_index": candidate.get("row_index", ""),
                "source_kind": _norm_text(candidate.get("source_kind")),
                "table_score": candidate.get("table_score", 0),
                "table_matched_keywords": _norm_text(candidate.get("table_matched_keywords")),
                "source_evidence_excerpt": _norm_text(candidate.get("source_evidence_excerpt")),
                "notes": _norm_text(candidate.get("notes")),
            }
        )
    return {
        "reviewed": _clean_frame(pd.DataFrame(reviewed_rows)),
        "needs_review": _clean_frame(pd.DataFrame(needs_review_rows)),
        "rejected": _clean_frame(pd.DataFrame(rejected_rows)),
        "trace": _clean_frame(pd.DataFrame(source_trace_rows)),
    }


def _build_inventory_sheets(result: MineruReadResult, table_rows: Sequence[Mapping[str, Any]]) -> Dict[str, pd.DataFrame]:
    summary = result.summary()
    summary_df = _clean_frame(pd.DataFrame([summary]))
    source_files_df = _clean_frame(pd.DataFrame([item.to_dict() for item in result.source_files]))
    warnings_df = _clean_frame(pd.DataFrame([item.to_dict() for item in result.warnings]))
    assets_df = _clean_frame(pd.DataFrame([item.to_dict() for item in result.table_assets]))
    tables_df = _clean_frame(pd.DataFrame(list(table_rows)))
    return {
        "summary": summary_df,
        "source_files": source_files_df,
        "warnings": warnings_df,
        "table_assets": assets_df,
        "extracted_tables": tables_df,
    }


def _build_document_package(
    *,
    pdf_path: Path,
    parse_dir: Path,
    run_info: Mapping[str, Any],
    parse_reader: Callable[[Path], MineruReadResult],
) -> Dict[str, Any]:
    result = parse_reader(parse_dir)
    page_texts, raw_text_rows = _collect_page_text_from_content_list(parse_dir)
    if not page_texts:
        markdown_text = _extract_markdown_fallback(parse_dir)
        if markdown_text:
            page_texts = {1: markdown_text}
            raw_text_rows = [{"page_no": 1, "node_type": "markdown_fallback", "text_excerpt": _truncate(markdown_text, 200)}]
    page_text_rows = _build_page_text_rows(pdf_path.name, page_texts)
    extracted_tables_rows = _build_extracted_tables_rows(pdf_path.name, result)
    all_financial_table_rows, financial_table_candidate_rows, likely_page_scores = _build_financial_table_rows(pdf_path.name, result)
    metric_candidates = _parse_table_metric_candidates(pdf_path.name, result)
    metric_candidates.extend(_extract_document_text_candidates(pdf_path.name, page_texts))
    # de-duplicate exact candidate ids after table + document metadata merge
    deduped_candidates: List[Dict[str, Any]] = []
    seen_ids = set()
    for candidate in metric_candidates:
        cid = candidate["candidate_id"]
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        deduped_candidates.append(candidate)
    candidate_frames = _build_candidate_frames(deduped_candidates)
    likely_pages = sorted({page_no for page_no in likely_page_scores if page_no > 0})
    if not likely_pages:
        likely_pages = [row["page_no"] for row in page_text_rows if row.get("contains_financial_keywords") or row.get("contains_forecast_years")]
    parse_status = "processed"
    failure_reason = ""
    if not result.table_assets and not page_texts:
        parse_status = "blocked"
        failure_reason = "mineru_output_missing_readable_tables_and_text"
    elif not result.table_assets:
        parse_status = "partial"
        failure_reason = "mineru_output_has_text_but_no_table_assets"
    page_count = max(list(page_texts.keys()) + [(_safe_int(asset.page_idx, -1) + 1) for asset in result.table_assets if asset.page_idx is not None], default=0)
    document_summary = {
        "document": pdf_path.name,
        "pdf_stem": pdf_path.stem,
        "parse_status": parse_status,
        "page_count": page_count,
        "mineru_table_count": len(result.table_assets),
        "financial_table_candidate_count": len(financial_table_candidate_rows),
        "metric_candidate_count": len(deduped_candidates),
        "reviewed_count": len(candidate_frames["reviewed"]),
        "needs_review_count": len(candidate_frames["needs_review"]),
        "rejected_count": len(candidate_frames["rejected"]),
        "likely_financial_pages": likely_pages,
        "mineru_parse_dir": str(parse_dir),
        "mineru_status": run_info.get("status", ""),
        "manual_mineru_command": run_info.get("manual_command", ""),
        "failure_reason": failure_reason,
    }
    routing_preview_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "candidate_id": _norm_text(candidate.get("candidate_id")),
                    "route": _norm_text(candidate.get("status")),
                    "route_reason": _norm_text(candidate.get("route_reason")),
                    "metric": _norm_text(candidate.get("metric")),
                    "year": _norm_text(candidate.get("year")),
                    "value": _norm_text(candidate.get("value")),
                    "unit": _norm_text(candidate.get("unit")),
                    "source_page": candidate.get("source_page", ""),
                    "table_index": candidate.get("table_index", ""),
                    "table_score": candidate.get("table_score", 0),
                    "matched_keywords": _norm_text(candidate.get("table_matched_keywords")),
                    "evidence": _norm_text(candidate.get("source_evidence_excerpt")),
                }
                for candidate in deduped_candidates
            ]
        )
    )
    metric_candidates_df = _clean_frame(pd.DataFrame(deduped_candidates))
    financial_candidates_df = _clean_frame(pd.DataFrame(financial_table_candidate_rows))
    page_text_df = _clean_frame(pd.DataFrame(page_text_rows))
    raw_text_df = _clean_frame(pd.DataFrame(raw_text_rows))
    extracted_tables_df = _clean_frame(pd.DataFrame(extracted_tables_rows))
    inventory_sheets = _build_inventory_sheets(result, all_financial_table_rows)
    client_preview_sheets = {
        COMBINED_WORKBOOK_SHEETS["readme"]: _customer_readme_df(),
        COMBINED_WORKBOOK_SHEETS["reviewed"]: candidate_frames["reviewed"],
        COMBINED_WORKBOOK_SHEETS["needs_review"]: candidate_frames["needs_review"],
        COMBINED_WORKBOOK_SHEETS["rejected"]: candidate_frames["rejected"],
        COMBINED_WORKBOOK_SHEETS["trace"]: candidate_frames["trace"],
        COMBINED_WORKBOOK_SHEETS["document_summary"]: _clean_frame(pd.DataFrame([document_summary])),
        COMBINED_WORKBOOK_SHEETS["financial_tables"]: financial_candidates_df,
    }
    return {
        "document_summary": document_summary,
        "page_text_df": page_text_df,
        "raw_text_df": raw_text_df,
        "extracted_tables_df": extracted_tables_df,
        "financial_candidates_df": financial_candidates_df,
        "metric_candidates_df": metric_candidates_df,
        "routing_preview_df": routing_preview_df,
        "client_preview_sheets": client_preview_sheets,
        "inventory_sheets": inventory_sheets,
        "candidate_frames": candidate_frames,
    }


def build_mineru_real_pdf_intake_337a(
    *,
    input_pdf_dir: Path,
    output_dir: Path,
    mineru_exe: Path = DEFAULT_MINERU_EXE,
    mineru_runner: Callable[[Path, Path, Path], Dict[str, Any]] | None = None,
    parse_reader: Callable[[Path], MineruReadResult] = read_mineru_output,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    runner = mineru_runner or _default_mineru_runner
    mineru_outputs_root = output_dir / "mineru_outputs"
    datefac_debug_root = output_dir / "datefac_debug"

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    pdf_paths = _find_pdf_files(input_pdf_dir)

    document_packages: List[Dict[str, Any]] = []
    document_rows: List[Dict[str, Any]] = []
    blocked_reasons: List[str] = []
    manual_commands: List[str] = []
    mineru_success_count = 0
    mineru_failure_rows: List[Dict[str, Any]] = []

    if not pdf_paths:
        blocked_reasons.append("No PDF files were found in the input folder.")

    for pdf_path in pdf_paths:
        run_info = runner(pdf_path, mineru_outputs_root, mineru_exe)
        manual_commands.append(run_info.get("manual_command", ""))
        parse_dir = run_info.get("parse_dir")
        if run_info.get("success") and isinstance(parse_dir, Path) and parse_dir.exists():
            mineru_success_count += 1
            package = _build_document_package(
                pdf_path=pdf_path,
                parse_dir=parse_dir,
                run_info=run_info,
                parse_reader=parse_reader,
            )
        else:
            parse_status = "blocked"
            if isinstance(parse_dir, Path) and parse_dir.exists():
                parse_status = "partial"
            failure_reason = _norm_text(run_info.get("stderr") or run_info.get("status") or "mineru_run_failed")
            if failure_reason:
                mineru_failure_rows.append({"document": pdf_path.name, "failure_reason": failure_reason})
            package = {
                "document_summary": {
                    "document": pdf_path.name,
                    "pdf_stem": pdf_path.stem,
                    "parse_status": parse_status,
                    "page_count": 0,
                    "mineru_table_count": 0,
                    "financial_table_candidate_count": 0,
                    "metric_candidate_count": 0,
                    "reviewed_count": 0,
                    "needs_review_count": 0,
                    "rejected_count": 0,
                    "likely_financial_pages": [],
                    "mineru_parse_dir": str(parse_dir) if parse_dir else "",
                    "mineru_status": run_info.get("status", ""),
                    "manual_mineru_command": run_info.get("manual_command", ""),
                    "failure_reason": failure_reason,
                },
                "page_text_df": _clean_frame(pd.DataFrame()),
                "raw_text_df": _clean_frame(pd.DataFrame()),
                "extracted_tables_df": _clean_frame(pd.DataFrame()),
                "financial_candidates_df": _clean_frame(pd.DataFrame()),
                "metric_candidates_df": _clean_frame(pd.DataFrame()),
                "routing_preview_df": _clean_frame(pd.DataFrame()),
                "client_preview_sheets": {
                    COMBINED_WORKBOOK_SHEETS["readme"]: _customer_readme_df(),
                    COMBINED_WORKBOOK_SHEETS["reviewed"]: _clean_frame(pd.DataFrame()),
                    COMBINED_WORKBOOK_SHEETS["needs_review"]: _clean_frame(pd.DataFrame()),
                    COMBINED_WORKBOOK_SHEETS["rejected"]: _clean_frame(pd.DataFrame()),
                    COMBINED_WORKBOOK_SHEETS["trace"]: _clean_frame(pd.DataFrame()),
                    COMBINED_WORKBOOK_SHEETS["document_summary"]: _clean_frame(pd.DataFrame([{
                        "document": pdf_path.name,
                        "parse_status": parse_status,
                        "failure_reason": failure_reason,
                    }])),
                    COMBINED_WORKBOOK_SHEETS["financial_tables"]: _clean_frame(pd.DataFrame()),
                },
                "inventory_sheets": {
                    "summary": _clean_frame(pd.DataFrame([{"source_root": str(parse_dir) if parse_dir else "", "table_asset_count": 0, "warning_count": 0}])),
                    "source_files": _clean_frame(pd.DataFrame()),
                    "warnings": _clean_frame(pd.DataFrame([{"warning_code": "mineru_blocked", "warning_message": failure_reason}])),
                    "table_assets": _clean_frame(pd.DataFrame()),
                    "extracted_tables": _clean_frame(pd.DataFrame()),
                },
                "candidate_frames": {"reviewed": pd.DataFrame(), "needs_review": pd.DataFrame(), "rejected": pd.DataFrame(), "trace": pd.DataFrame()},
            }
        document_packages.append(package)
        document_rows.append(package["document_summary"])

    combined_reviewed = pd.concat([package["candidate_frames"]["reviewed"] for package in document_packages], ignore_index=True) if document_packages else pd.DataFrame()
    combined_needs_review = pd.concat([package["candidate_frames"]["needs_review"] for package in document_packages], ignore_index=True) if document_packages else pd.DataFrame()
    combined_rejected = pd.concat([package["candidate_frames"]["rejected"] for package in document_packages], ignore_index=True) if document_packages else pd.DataFrame()
    combined_trace = pd.concat([package["candidate_frames"]["trace"] for package in document_packages], ignore_index=True) if document_packages else pd.DataFrame()
    combined_document_summary = _clean_frame(pd.DataFrame(document_rows))
    combined_financial_candidates = pd.concat([package["financial_candidates_df"] for package in document_packages], ignore_index=True) if document_packages else pd.DataFrame()

    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])

    qa_checks = [
        {"check_name": "input_dir_exists", "status": "PASS" if input_pdf_dir.exists() else "FAIL", "detail": str(input_pdf_dir)},
        {"check_name": "pdf_found_count_gt_zero", "status": "PASS" if len(pdf_paths) > 0 else "FAIL", "detail": str(len(pdf_paths))},
        {"check_name": "mineru_executable_exists", "status": "PASS" if mineru_exe.exists() else "FAIL", "detail": str(mineru_exe)},
        {"check_name": "official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_status_preserved", "status": "PASS" if protected_status_before == protected_status_after else "FAIL", "detail": json.dumps(protected_status_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_paths_not_staged", "status": "PASS" if not protected_cached_after else "FAIL", "detail": json.dumps(protected_cached_after, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")
    pdf_processed_count = sum(1 for row in document_rows if row.get("parse_status") in {"processed", "partial"})
    if mineru_success_count == 0 and pdf_paths:
        blocked_reasons.append("MinerU could not be run successfully for any PDF. Use the manual commands in the summary.")
    if blocked_reasons:
        decision = BLOCKED_DECISION
    elif qa_fail_count == 0 and pdf_processed_count == len(pdf_paths):
        decision = READY_DECISION
    else:
        decision = PARTIAL_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "project_status": "LOCAL_PREVIEW_ONLY_MINERU_FIRST",
        "client_ready": False,
        "production_ready": False,
        "input_pdf_dir": str(input_pdf_dir),
        "output_dir": str(output_dir),
        "mineru_executable": str(mineru_exe),
        "pdf_found_count": len(pdf_paths),
        "pdf_processed_count": pdf_processed_count,
        "mineru_success_count": mineru_success_count,
        "reviewed_count": len(combined_reviewed),
        "needs_review_count": len(combined_needs_review),
        "rejected_or_excluded_count": len(combined_rejected),
        "manual_mineru_commands": [command for command in manual_commands if command],
        "no_official_asset_modification_during_337a": official_assets_before == official_assets_after,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "337A_mineru_first_real_pdf_intake",
        "input_pdf_dir": str(input_pdf_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "batch_summary_xlsx": str(output_dir / "00_batch_summary.xlsx"),
            "batch_summary_json": str(output_dir / "00_batch_summary.json"),
            "batch_report_md": str(output_dir / "00_batch_report.md"),
            "combined_preview_xlsx": str(output_dir / "real_test_mineru_client_export_337a.xlsx"),
            "qa_json": str(output_dir / "real_test_mineru_337a_qa.json"),
            "manifest_json": str(output_dir / "real_test_mineru_337a_manifest.json"),
            "mineru_outputs_dir": str(mineru_outputs_root),
            "datefac_debug_dir": str(datefac_debug_root),
        },
        "documents": document_rows,
    }

    qa_json = {
        "decision": decision,
        "qa_fail_count": qa_fail_count,
        "checks": qa_checks,
        "blocked_reasons": blocked_reasons,
        "mineru_failure_rows": mineru_failure_rows,
        "protected_dirty_status_before": protected_status_before,
        "protected_dirty_status_after": protected_status_after,
        "protected_dirty_cached_after": protected_cached_after,
        "official_assets_before": official_assets_before,
        "official_assets_after": official_assets_after,
    }

    combined_workbook_sheets = {
        COMBINED_WORKBOOK_SHEETS["readme"]: _customer_readme_df(),
        COMBINED_WORKBOOK_SHEETS["reviewed"]: _clean_frame(combined_reviewed),
        COMBINED_WORKBOOK_SHEETS["needs_review"]: _clean_frame(combined_needs_review),
        COMBINED_WORKBOOK_SHEETS["rejected"]: _clean_frame(combined_rejected),
        COMBINED_WORKBOOK_SHEETS["trace"]: _clean_frame(combined_trace),
        COMBINED_WORKBOOK_SHEETS["document_summary"]: combined_document_summary,
        COMBINED_WORKBOOK_SHEETS["financial_tables"]: _clean_frame(combined_financial_candidates),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "document_packages": document_packages,
        "document_rows": document_rows,
        "combined_workbook_sheets": combined_workbook_sheets,
        "batch_summary_df": combined_document_summary,
    }
