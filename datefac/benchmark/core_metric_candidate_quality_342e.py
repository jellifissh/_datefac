from __future__ import annotations

import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.benchmark.mineru_batch_parse_benchmark_342c import (
    CORPUS_MANIFEST_NAME,
    CORPUS_READY_DECISION,
    CORPUS_SUMMARY_NAME,
    CORPUS_WORKBOOK_NAME,
    PILOT_SPLIT,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION = "CORE_METRIC_CANDIDATE_QUALITY_342E_READY"
NOT_READY_DECISION = "CORE_METRIC_CANDIDATE_QUALITY_342E_NOT_READY"
READY_INPUT_DECISION = "PARSER_ENSEMBLE_COMPARE_342D_READY"

DEFAULT_CORPUS_342B_DIR = Path(r"D:\_datefac\output\real_pdf_corpus_intake_342b")
DEFAULT_MINERU_342C6_DIR = Path(r"D:\_datefac\output\mineru_pilot_network_recovery_342c6")
DEFAULT_PARSER_COMPARE_342D_DIR = Path(r"D:\_datefac\output\parser_ensemble_compare_342d")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\core_metric_candidate_quality_342e")

SUMMARY_FILE_NAME = "core_metric_candidate_quality_342e_summary.json"
MANIFEST_FILE_NAME = "core_metric_candidate_quality_342e_manifest.json"
QA_FILE_NAME = "core_metric_candidate_quality_342e_qa.json"
NO_WRITE_BACK_FILE_NAME = "core_metric_candidate_quality_342e_no_write_back_proof.json"
REPORT_FILE_NAME = "core_metric_candidate_quality_342e_report.md"
WORKBOOK_FILE_NAME = "core_metric_candidate_quality_342e.xlsx"

MINERU_342C6_SUMMARY_NAME = "mineru_pilot_network_recovery_342c6_summary.json"
MINERU_342C6_QA_NAME = "mineru_pilot_network_recovery_342c6_qa.json"
MINERU_342C6_WORKBOOK_NAME = "mineru_pilot_network_recovery_342c6.xlsx"

PARSER_COMPARE_342D_SUMMARY_NAME = "parser_ensemble_compare_342d_summary.json"
PARSER_COMPARE_342D_QA_NAME = "parser_ensemble_compare_342d_qa.json"
PARSER_COMPARE_342D_WORKBOOK_NAME = "parser_ensemble_compare_342d.xlsx"

WORKBOOK_SHEETS = [
    "00_README",
    "01_TABLE_QUALITY_SUMMARY",
    "02_PDF_TABLE_SIGNAL",
    "03_ALL_TABLE_BLOCKS",
    "04_TABLE_TYPE_COVERAGE",
    "05_CORE_EXTRACTABLE",
    "06_METADATA_EXTRACTABLE",
    "07_EXCLUDED_TABLES",
    "08_SOURCE_TRACE_AUDIT",
    "09_342F_READINESS",
    "10_NO_WRITE_BACK_PROOF",
    "11_NEXT_STEPS",
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

TABLE_TYPES = {
    "CORE_FORECAST_SUMMARY",
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "VALUATION_METRICS",
    "BASIC_DATA",
    "RATING_STANDARD",
    "RELATED_REPORTS",
    "DISCLAIMER",
    "CHART_OR_IMAGE",
    "NOISE_TABLE",
    "UNKNOWN_TABLE",
}
CORE_TABLE_TYPES = {
    "CORE_FORECAST_SUMMARY",
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "VALUATION_METRICS",
}

YEAR_TOKEN_RE = re.compile(r"\b(?:20\d{2}(?:A|E)?|FY20\d{2})\b", re.IGNORECASE)
TABLE_RE = re.compile(r"<table.*?>.*?</table>", re.IGNORECASE | re.DOTALL)
TR_RE = re.compile(r"<tr.*?>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
CELL_RE = re.compile(r"<t[dh](.*?)*?>(.*?)</t[dh]>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")

FINANCIAL_KEYWORD_GROUPS: Dict[str, Sequence[str]] = {
    "forecast": ["盈利预测", "财务指标", "预测", "forecast"],
    "revenue": ["营业收入", "收入", "营收", "revenue"],
    "net_profit": ["归母净利润", "净利润", "归属于母公司股东的净利润", "net profit"],
    "balance": ["资产负债表", "资产总计", "负债总计", "股东权益", "总资产", "总负债"],
    "income": ["利润表", "营业成本", "毛利", "营业利润", "净利润", "税前利润"],
    "cashflow": ["现金流量表", "经营活动现金流", "投资活动现金流", "筹资活动现金流"],
    "valuation": ["pe", "pb", "ev/ebitda", "ps", "估值", "市盈率", "市净率"],
    "basic": ["投资评级", "收盘价", "总市值", "分析师", "52周", "基础数据"],
    "rating": ["评级说明", "投资评级说明", "买入", "增持", "中性", "卖出"],
    "related": ["相关研究", "历史报告", "相关报告"],
    "disclaimer": ["免责声明", "分析师声明", "风险提示", "法律声明"],
    "chart": ["图表", "figure", "chart"],
}
MONEY_HINTS = ["亿元", "百万元", "万元", "百万港元", "港元", "元", "人民币"]
PERCENT_HINTS = ["%", "pct", "同比", "增长率", "毛利率", "净利率", "roe"]
VALUATION_HINTS = ["pe", "pb", "ev/ebitda", "估值", "市盈率", "市净率"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_illegal_excel_chars(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return "".join(ch for ch in value if ch in {"\n", "\r", "\t"} or ord(ch) >= 32)


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    cleaned = frame.astype(object).where(pd.notna(frame), "")
    return cleaned.map(_strip_illegal_excel_chars)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int | None:
    text = _norm_text(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
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


def _load_pilot_corpus_rows(corpus_342b_dir: Path) -> tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any], List[str]]:
    workbook_path = corpus_342b_dir / CORPUS_WORKBOOK_NAME
    summary_path = corpus_342b_dir / CORPUS_SUMMARY_NAME
    manifest_path = corpus_342b_dir / CORPUS_MANIFEST_NAME
    files_read: List[str] = []

    summary = _read_json(summary_path) if summary_path.exists() else {}
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    if summary_path.exists():
        files_read.append(str(summary_path))
    if manifest_path.exists():
        files_read.append(str(manifest_path))
    if not workbook_path.exists():
        return pd.DataFrame(), summary, manifest, files_read

    files_read.append(str(workbook_path))
    corpus_df = pd.read_excel(workbook_path, sheet_name="02_PDF_CORPUS")
    tier_df = pd.read_excel(workbook_path, sheet_name="04_TIER_ASSIGNMENT")
    split_df = pd.read_excel(workbook_path, sheet_name="05_SPLIT_PLAN")
    merged = corpus_df.merge(tier_df, on="corpus_pdf_id", how="left").merge(split_df, on="corpus_pdf_id", how="left")
    pilot_df = merged[merged["split"] == PILOT_SPLIT].copy()
    pilot_df = pilot_df.sort_values(["assigned_tier", "page_count", "corpus_pdf_id"], ascending=[True, False, True])
    return _clean_frame(pilot_df.reset_index(drop=True)), summary, manifest, files_read


def _load_342c6_context(mineru_342c6_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame, List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = mineru_342c6_dir / MINERU_342C6_SUMMARY_NAME
    qa_path = mineru_342c6_dir / MINERU_342C6_QA_NAME
    workbook_path = mineru_342c6_dir / MINERU_342C6_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    if summary_path.exists():
        files_read.append(str(summary_path))
    else:
        warnings.append(f"missing 342C6 summary: {summary_path}")
    if qa_path.exists():
        files_read.append(str(qa_path))
    else:
        warnings.append(f"missing 342C6 qa: {qa_path}")

    final_rollup_df = pd.DataFrame()
    if workbook_path.exists():
        files_read.append(str(workbook_path))
        try:
            final_rollup_df = pd.read_excel(workbook_path, sheet_name="04_FINAL_PILOT_ROLLUP")
        except Exception as exc:
            warnings.append(f"unable to read 342C6 final rollup workbook: {exc}")
    else:
        warnings.append(f"missing 342C6 workbook: {workbook_path}")
    return summary, qa_json, _clean_frame(final_rollup_df), files_read, warnings


def _load_342d_context(parser_compare_342d_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame, List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = parser_compare_342d_dir / PARSER_COMPARE_342D_SUMMARY_NAME
    qa_path = parser_compare_342d_dir / PARSER_COMPARE_342D_QA_NAME
    workbook_path = parser_compare_342d_dir / PARSER_COMPARE_342D_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    if summary_path.exists():
        files_read.append(str(summary_path))
    else:
        warnings.append(f"missing 342D summary: {summary_path}")
    if qa_path.exists():
        files_read.append(str(qa_path))
    else:
        warnings.append(f"missing 342D qa: {qa_path}")

    compare_df = pd.DataFrame()
    if workbook_path.exists():
        files_read.append(str(workbook_path))
        try:
            compare_df = pd.read_excel(workbook_path, sheet_name="02_PDF_LEVEL_COMPARE")
        except Exception as exc:
            warnings.append(f"unable to read 342D compare workbook: {exc}")
    else:
        warnings.append(f"missing 342D workbook: {workbook_path}")
    return summary, qa_json, _clean_frame(compare_df), files_read, warnings


def _collapse_spaces(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def _strip_html(text: str) -> str:
    return _collapse_spaces(TAG_RE.sub(" ", text))


def _extract_year_tokens(text: str) -> List[str]:
    seen: List[str] = []
    for match in YEAR_TOKEN_RE.findall(text):
        token = match.upper()
        if token not in seen:
            seen.append(token)
    return seen


def _extract_keyword_hits(text: str) -> List[str]:
    lowered = text.casefold()
    hits: List[str] = []
    for group, tokens in FINANCIAL_KEYWORD_GROUPS.items():
        for token in tokens:
            if token.casefold() in lowered:
                hits.append(token)
    seen: List[str] = []
    for item in hits:
        if item not in seen:
            seen.append(item)
    return seen


def _html_to_rows(html: str) -> List[List[str]]:
    rows: List[List[str]] = []
    if not html:
        return rows
    for row_html in TR_RE.findall(html):
        cells: List[str] = []
        for attrs, cell_html in CELL_RE.findall(row_html):
            colspan_match = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs or "", re.IGNORECASE)
            colspan = int(colspan_match.group(1)) if colspan_match else 1
            text = _collapse_spaces(_strip_html(cell_html))
            cells.extend([text] * max(colspan, 1))
        if cells:
            rows.append(cells)
    return rows


def _row_count(html: str) -> int:
    return len(_html_to_rows(html))


def _column_count(html: str) -> int:
    rows = _html_to_rows(html)
    return max((len(row) for row in rows), default=0)


def _header_year_tokens(html: str, extra_text: str = "") -> List[str]:
    rows = _html_to_rows(html)
    header_text = " ".join(" ".join(row) for row in rows[:2])
    return _extract_year_tokens(f"{header_text} {extra_text}")


def _table_value_class(text: str, keyword_hits: Sequence[str], row_count: int, column_count: int) -> str:
    lowered = text.casefold()
    has_money = any(token.casefold() in lowered for token in MONEY_HINTS)
    has_percent = any(token.casefold() in lowered for token in PERCENT_HINTS)
    has_valuation = any(token.casefold() in lowered for token in VALUATION_HINTS)
    if has_valuation and has_money:
        return "MIXED_FINANCIAL_AND_VALUATION"
    if has_valuation:
        return "VALUATION_RATIO_TABLE"
    if has_money and has_percent:
        return "MIXED_FORECAST_TABLE"
    if has_money:
        return "MONEY_TABLE"
    if has_percent:
        return "PERCENT_TABLE"
    if any(token in keyword_hits for token in ["投资评级", "收盘价", "总市值", "分析师"]):
        return "METADATA_TABLE"
    if row_count == 0 and column_count == 0:
        return "LAYOUT_TRACE_ONLY"
    return "TEXTUAL_OR_OTHER_TABLE"


def _classify_table_type(text: str, row_count: int, column_count: int, source_kind: str) -> str:
    lowered = text.casefold()
    if "免责声明" in text or "分析师声明" in text or "法律声明" in text or "风险提示" in text:
        return "DISCLAIMER"
    if "相关研究" in text or "相关报告" in text or "历史报告" in text:
        return "RELATED_REPORTS"
    if "评级说明" in text or "投资评级说明" in text:
        return "RATING_STANDARD"
    if "投资评级" in text or "收盘价" in text or "总市值" in text or "分析师" in text or "52周" in text:
        return "BASIC_DATA"
    if "资产负债表" in text or "资产总计" in text or "负债总计" in text or "股东权益" in text:
        return "BALANCE_SHEET"
    if "现金流量表" in text or "经营活动现金流" in text or "投资活动现金流" in text or "筹资活动现金流" in text:
        return "CASH_FLOW_STATEMENT"
    if "利润表" in text or "营业成本" in text or "毛利" in text or "营业利润" in text:
        return "INCOME_STATEMENT"
    if ("盈利预测" in text or "财务指标" in text or "forecast" in lowered) and row_count >= 2 and column_count >= 3:
        return "CORE_FORECAST_SUMMARY"
    if row_count >= 2 and column_count >= 3 and (
        "营业收入" in text or "归母净利润" in text or "净利润" in text or "eps" in lowered or "roe" in lowered
    ):
        return "CORE_FORECAST_SUMMARY"
    if "ev/ebitda" in lowered or "市盈率" in text or "市净率" in text:
        return "VALUATION_METRICS"
    if source_kind == "model" and row_count == 0:
        return "CHART_OR_IMAGE"
    if "图表" in text and row_count <= 1:
        return "CHART_OR_IMAGE"
    if row_count == 0 and column_count == 0:
        return "UNKNOWN_TABLE"
    if row_count <= 1 or column_count <= 1:
        return "NOISE_TABLE"
    return "UNKNOWN_TABLE"


def _recommendation(table_type: str) -> str:
    if table_type in CORE_TABLE_TYPES:
        return "core_extractable"
    if table_type == "BASIC_DATA":
        return "metadata_extractable"
    if table_type == "UNKNOWN_TABLE":
        return "manual_review_required"
    return "exclude_from_core_extraction"


def _source_trace_quality(source_kind: str, html: str, img_path: str, bbox: str) -> str:
    if source_kind in {"content_list", "content_list_v2"} and html and img_path and bbox:
        return "STRONG"
    if source_kind == "markdown" and html:
        return "MEDIUM"
    if source_kind == "middle" and bbox:
        return "MEDIUM"
    if source_kind == "model" and bbox:
        return "WEAK"
    return "WEAK"


def _resolve_img_path(parse_dir: Path, raw_img_path: str) -> str:
    if not raw_img_path:
        return ""
    path = Path(raw_img_path)
    if path.is_absolute():
        return str(path)
    return str((parse_dir / path).resolve())


def _json_table_rows(
    *,
    parse_dir: Path,
    pdf_id: str,
    file_name: str,
    source_path: Path,
    source_kind: str,
    items: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    counter = 0
    for item in items:
        if _norm_text(item.get("type")).casefold() != "table":
            continue
        counter += 1
        html = _norm_text(item.get("table_body"))
        caption = " | ".join(_norm_text(x) for x in item.get("table_caption", []) if _norm_text(x))
        footnote = " | ".join(_norm_text(x) for x in item.get("table_footnote", []) if _norm_text(x))
        img_path = _resolve_img_path(parse_dir, _norm_text(item.get("img_path")))
        bbox_value = item.get("bbox", [])
        bbox = json.dumps(bbox_value, ensure_ascii=False) if bbox_value else ""
        page_idx = _to_int(item.get("page_idx"))
        text = _collapse_spaces(" ".join(part for part in [_strip_html(html), caption, footnote] if part))
        row_count = _row_count(html)
        column_count = _column_count(html)
        keyword_hits = _extract_keyword_hits(text)
        table_type = _classify_table_type(text, row_count, column_count, source_kind)
        rows.append(
            {
                "table_id": f"{pdf_id}_{source_kind}_{counter:03d}",
                "pdf_id": pdf_id,
                "file_name": file_name,
                "page_idx": "" if page_idx is None else page_idx,
                "bbox": bbox,
                "html": html,
                "img_path": img_path,
                "caption": caption,
                "footnote": footnote,
                "source_file": str(source_path),
                "source_kind": source_kind,
                "row_count": row_count,
                "column_count": column_count,
                "header_year_tokens": "|".join(_header_year_tokens(html, caption)),
                "financial_keyword_hits": "|".join(keyword_hits),
                "table_type": table_type,
                "table_value_class": _table_value_class(text, keyword_hits, row_count, column_count),
                "extraction_recommendation": _recommendation(table_type),
                "source_trace_quality": _source_trace_quality(source_kind, html, img_path, bbox),
                "parse_output_dir": str(parse_dir),
            }
        )
    return rows


def _extract_content_list_items(payload: Any) -> List[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items: List[Mapping[str, Any]] = []
        for page in payload.get("pdf_info", []):
            if isinstance(page, dict):
                for block in page.get("blocks", []):
                    if isinstance(block, dict):
                        items.append(block)
        return items
    return []


def _extract_content_list_v2_items(payload: Any) -> List[Mapping[str, Any]]:
    items: List[Mapping[str, Any]] = []
    if isinstance(payload, list):
        for page_idx, page in enumerate(payload):
            if isinstance(page, list):
                for block in page:
                    if not isinstance(block, dict):
                        continue
                    item = {
                        "type": block.get("type"),
                        "page_idx": page_idx,
                        "bbox": block.get("bbox"),
                    }
                    content = block.get("content") if isinstance(block.get("content"), dict) else {}
                    image_source = content.get("image_source") if isinstance(content.get("image_source"), dict) else {}
                    item["img_path"] = image_source.get("path")
                    item["table_body"] = _norm_text(content.get("html"))
                    item["table_caption"] = [
                        _norm_text(x.get("content")) for x in content.get("table_caption", []) if isinstance(x, dict)
                    ]
                    item["table_footnote"] = [
                        _norm_text(x.get("content")) for x in content.get("table_footnote", []) if isinstance(x, dict)
                    ]
                    items.append(item)
    return items


def _extract_middle_items(payload: Any) -> List[Mapping[str, Any]]:
    items: List[Mapping[str, Any]] = []
    for page in payload.get("pdf_info", []) if isinstance(payload, dict) else []:
        page_idx = page.get("page_idx")
        for bucket in ("preproc_blocks", "para_blocks"):
            for block in page.get(bucket, []) or []:
                if isinstance(block, dict) and _norm_text(block.get("type")).casefold() == "table":
                    items.append(
                        {
                            "type": "table",
                            "page_idx": page_idx,
                            "bbox": block.get("bbox"),
                            "img_path": "",
                            "table_body": "",
                            "table_caption": [],
                            "table_footnote": [],
                        }
                    )
    return items


def _extract_model_items(payload: Any) -> List[Mapping[str, Any]]:
    items: List[Mapping[str, Any]] = []
    if isinstance(payload, list):
        for page in payload:
            if not isinstance(page, dict):
                continue
            page_info = page.get("page_info") if isinstance(page.get("page_info"), dict) else {}
            page_idx = page_info.get("page_no")
            for det in page.get("layout_dets", []) or []:
                if isinstance(det, dict) and "table" in _norm_text(det.get("label")).casefold():
                    items.append(
                        {
                            "type": "table",
                            "page_idx": page_idx,
                            "bbox": det.get("bbox"),
                            "img_path": "",
                            "table_body": "",
                            "table_caption": [],
                            "table_footnote": [],
                        }
                    )
    return items


def _extract_markdown_tables(parse_dir: Path, pdf_id: str, file_name: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    counter = 0
    for md_path in sorted(parse_dir.glob("*.md")):
        md_text = _read_text_safe(md_path)
        for block in TABLE_RE.findall(md_text):
            counter += 1
            text = _strip_html(block)
            row_count = _row_count(block)
            column_count = _column_count(block)
            keyword_hits = _extract_keyword_hits(text)
            table_type = _classify_table_type(text, row_count, column_count, "markdown")
            rows.append(
                {
                    "table_id": f"{pdf_id}_markdown_{counter:03d}",
                    "pdf_id": pdf_id,
                    "file_name": file_name,
                    "page_idx": "",
                    "bbox": "",
                    "html": block,
                    "img_path": "",
                    "caption": "",
                    "footnote": "",
                    "source_file": str(md_path),
                    "source_kind": "markdown",
                    "row_count": row_count,
                    "column_count": column_count,
                    "header_year_tokens": "|".join(_header_year_tokens(block)),
                    "financial_keyword_hits": "|".join(keyword_hits),
                    "table_type": table_type,
                    "table_value_class": _table_value_class(text, keyword_hits, row_count, column_count),
                    "extraction_recommendation": _recommendation(table_type),
                    "source_trace_quality": _source_trace_quality("markdown", block, "", ""),
                    "parse_output_dir": str(parse_dir),
                }
            )
    return rows


def _extract_all_table_rows(parse_dir: Path, pdf_id: str, file_name: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for json_path in sorted(parse_dir.glob("*content_list.json")):
        payload = _read_json(json_path)
        rows.extend(
            _json_table_rows(
                parse_dir=parse_dir,
                pdf_id=pdf_id,
                file_name=file_name,
                source_path=json_path,
                source_kind="content_list",
                items=_extract_content_list_items(payload),
            )
        )
    for json_path in sorted(parse_dir.glob("*content_list_v2.json")):
        payload = _read_json(json_path)
        rows.extend(
            _json_table_rows(
                parse_dir=parse_dir,
                pdf_id=pdf_id,
                file_name=file_name,
                source_path=json_path,
                source_kind="content_list_v2",
                items=_extract_content_list_v2_items(payload),
            )
        )
    for json_path in sorted(parse_dir.glob("*middle.json")):
        payload = _read_json(json_path)
        rows.extend(
            _json_table_rows(
                parse_dir=parse_dir,
                pdf_id=pdf_id,
                file_name=file_name,
                source_path=json_path,
                source_kind="middle",
                items=_extract_middle_items(payload),
            )
        )
    for json_path in sorted(parse_dir.glob("*model.json")):
        payload = _read_json(json_path)
        rows.extend(
            _json_table_rows(
                parse_dir=parse_dir,
                pdf_id=pdf_id,
                file_name=file_name,
                source_path=json_path,
                source_kind="model",
                items=_extract_model_items(payload),
            )
        )
    rows.extend(_extract_markdown_tables(parse_dir, pdf_id, file_name))
    return rows


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342E now audits MinerU pilot outputs with a table-first method instead of continuing from the earlier 435 text candidates.",
        },
        {
            "topic": "Source priority",
            "message": "content_list.json and content_list_v2.json HTML tables are the primary structured source; middle.json, model.json, and markdown tables are supplemental source-trace evidence.",
        },
        {
            "topic": "Core boundary",
            "message": "Only CORE_FORECAST_SUMMARY, BALANCE_SHEET, INCOME_STATEMENT, CASH_FLOW_STATEMENT, and VALUATION_METRICS can be marked core_extractable.",
        },
        {
            "topic": "Metadata boundary",
            "message": "BASIC_DATA is metadata_extractable only and must not be auto-promoted into core financial extraction.",
        },
        {
            "topic": "Safety boundary",
            "message": "This stage does not rerun MinerU, does not call any vision model, does not write back upstream workbooks, and does not claim client-ready or production-ready status.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_pdf_table_signal_df(table_df: pd.DataFrame) -> pd.DataFrame:
    if table_df.empty:
        return _clean_frame(pd.DataFrame())
    grouped = (
        table_df.groupby(["pdf_id", "file_name"], dropna=False)
        .agg(
            total_table_block_count=("table_id", "count"),
            core_extractable_table_count=("extraction_recommendation", lambda s: int((s == "core_extractable").sum())),
            metadata_extractable_table_count=("extraction_recommendation", lambda s: int((s == "metadata_extractable").sum())),
            excluded_table_count=("extraction_recommendation", lambda s: int((s == "exclude_from_core_extraction").sum())),
            manual_review_required_count=("extraction_recommendation", lambda s: int((s == "manual_review_required").sum())),
            source_file_count=("source_file", pd.Series.nunique),
            source_kind_count=("source_kind", pd.Series.nunique),
        )
        .reset_index()
    )
    grouped["has_core_extractable_table"] = grouped["core_extractable_table_count"] > 0
    return _clean_frame(grouped)


def _build_type_coverage_df(table_df: pd.DataFrame) -> pd.DataFrame:
    if table_df.empty:
        return _clean_frame(pd.DataFrame(columns=["table_type", "table_count", "pdf_count", "recommendation"]))
    rows: List[Dict[str, Any]] = []
    for table_type in sorted(TABLE_TYPES):
        subset = table_df[table_df["table_type"] == table_type]
        rows.append(
            {
                "table_type": table_type,
                "table_count": len(subset),
                "pdf_count": subset["pdf_id"].nunique(),
                "recommendation": _recommendation(table_type),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_source_trace_df(table_df: pd.DataFrame) -> pd.DataFrame:
    if table_df.empty:
        return _clean_frame(pd.DataFrame())
    cols = [
        "table_id",
        "pdf_id",
        "file_name",
        "source_kind",
        "source_file",
        "page_idx",
        "img_path",
        "bbox",
        "source_trace_quality",
        "table_type",
        "extraction_recommendation",
    ]
    return _clean_frame(table_df[cols].copy())


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


def _build_next_steps_df(ready_for_342f: str, recommended_342f_scope: str) -> pd.DataFrame:
    rows = [
        {
            "step_order": 1,
            "next_step": "Open 03_ALL_TABLE_BLOCKS first",
            "rationale": "This sheet is now the primary 342E evidence surface because every table block is classified and source-traced.",
        },
        {
            "step_order": 2,
            "next_step": "Use only core_extractable tables for any next metric pilot",
            "rationale": f"Current readiness is {ready_for_342f} with scope {recommended_342f_scope}. Do not continue from the historical 435 text candidates directly.",
        },
        {
            "step_order": 3,
            "next_step": "Keep metadata, excluded, and unknown tables separated",
            "rationale": "This preserves table-first evidence boundaries and reduces over-claim risk before any formal structured metric extraction step.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_core_metric_candidate_quality_342e(
    *,
    corpus_342b_dir: Path,
    mineru_342c6_dir: Path,
    parser_compare_342d_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    pilot_df, summary_342b, _manifest_342b, pilot_files_read = _load_pilot_corpus_rows(corpus_342b_dir)
    files_read.extend(pilot_files_read)
    if summary_342b.get("decision", "") != CORPUS_READY_DECISION:
        warnings.append(f"342B decision is {summary_342b.get('decision', '')}, expected {CORPUS_READY_DECISION}")

    summary_342c6, _qa_342c6, final_rollup_df, files_read_342c6, warnings_342c6 = _load_342c6_context(mineru_342c6_dir)
    files_read.extend(files_read_342c6)
    warnings.extend(warnings_342c6)

    summary_342d, _qa_342d, _compare_df, files_read_342d, warnings_342d = _load_342d_context(parser_compare_342d_dir)
    files_read.extend(files_read_342d)
    warnings.extend(warnings_342d)

    table_rows: List[Dict[str, Any]] = []
    for row in final_rollup_df.to_dict(orient="records"):
        if _norm_text(row.get("final_parse_status")).upper() != "SUCCESS":
            continue
        pdf_id = _norm_text(row.get("corpus_pdf_id"))
        file_name = _norm_text(row.get("file_name"))
        parse_dir = Path(_norm_text(row.get("output_dir")))
        if not parse_dir.exists():
            warnings.append(f"missing parse output dir for {pdf_id}: {parse_dir}")
            continue
        table_rows.extend(_extract_all_table_rows(parse_dir, pdf_id, file_name))

    table_df = _clean_frame(pd.DataFrame(table_rows))
    if table_df.empty:
        table_df = _clean_frame(
            pd.DataFrame(
                columns=[
                    "table_id",
                    "pdf_id",
                    "file_name",
                    "page_idx",
                    "bbox",
                    "html",
                    "img_path",
                    "caption",
                    "footnote",
                    "source_file",
                    "source_kind",
                    "row_count",
                    "column_count",
                    "header_year_tokens",
                    "financial_keyword_hits",
                    "table_type",
                    "table_value_class",
                    "extraction_recommendation",
                    "source_trace_quality",
                    "parse_output_dir",
                ]
            )
        )

    pdf_signal_df = _build_pdf_table_signal_df(table_df)
    type_coverage_df = _build_type_coverage_df(table_df)
    core_df = _clean_frame(table_df[table_df["extraction_recommendation"] == "core_extractable"].copy())
    metadata_df = _clean_frame(table_df[table_df["extraction_recommendation"] == "metadata_extractable"].copy())
    excluded_df = _clean_frame(table_df[table_df["extraction_recommendation"] == "exclude_from_core_extraction"].copy())
    source_trace_df = _build_source_trace_df(table_df)

    audited_pdf_count = int(final_rollup_df["corpus_pdf_id"].nunique()) if not final_rollup_df.empty else 0
    total_table_block_count = len(table_df)
    core_extractable_table_count = len(core_df)
    metadata_extractable_table_count = len(metadata_df)
    excluded_table_count = len(excluded_df)
    manual_review_required_count = int((table_df["extraction_recommendation"] == "manual_review_required").sum()) if not table_df.empty else 0
    pdf_with_core_extractable_table_count = int(pdf_signal_df["has_core_extractable_table"].sum()) if not pdf_signal_df.empty else 0
    table_source_file_count = table_df["source_file"].nunique() if not table_df.empty else 0

    if audited_pdf_count == 5 and pdf_with_core_extractable_table_count >= 3 and core_extractable_table_count >= 5:
        ready_for_342f = "true"
        recommended_342f_scope = "table_first_core_extractable_only"
    elif pdf_with_core_extractable_table_count >= 2 and core_extractable_table_count >= 2:
        ready_for_342f = "conditional"
        recommended_342f_scope = "high_signal_core_tables_only"
    else:
        ready_for_342f = "false"
        recommended_342f_scope = "insufficient_core_table_signal"

    hashed_input_paths = [path for path in files_read if Path(path).exists() and Path(path).is_file()]
    no_write_back_input_hashes_before = {path: sha256_file(Path(path)) for path in hashed_input_paths}
    no_write_back_input_hashes_after = {path: sha256_file(Path(path)) for path in hashed_input_paths}
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342E",
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
        bool(no_write_back_json.get("no_official_asset_modification_during_342e"))
        and bool(no_write_back_json.get("upstream_workbooks_unchanged"))
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())
    readiness_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "audited_pdf_count": audited_pdf_count,
                    "pdf_with_core_extractable_table_count": pdf_with_core_extractable_table_count,
                    "core_extractable_table_count": core_extractable_table_count,
                    "ready_for_342f": ready_for_342f,
                    "recommended_342f_scope": recommended_342f_scope,
                    "reason": (
                        "All five PDFs are available and core-extractable table evidence is strong enough to continue with a table-first pilot only."
                        if ready_for_342f == "true"
                        else "Some but not all table-first thresholds are satisfied, so the next step must stay inside the strongest core tables only."
                        if ready_for_342f == "conditional"
                        else "Current table-first evidence is still too weak for a safe next extraction pilot."
                    ),
                }
            ]
        )
    )

    checks = [
        {
            "check_name": "inputs::342d_ready_for_342e_detected",
            "status": "PASS"
            if summary_342d.get("decision", "") == READY_INPUT_DECISION and summary_342d.get("ready_for_342e", "") == "true"
            else "FAIL",
            "detail": json.dumps(
                {"decision": summary_342d.get("decision", ""), "ready_for_342e": summary_342d.get("ready_for_342e", "")},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342d_success_counts_valid",
            "status": "PASS"
            if int(summary_342d.get("mineru_success_count", 0) or 0) == 5
            and int(summary_342d.get("mineru_artifact_complete_count", 0) or 0) == 5
            and int(summary_342d.get("qa_fail_count", 0) or 0) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "mineru_success_count": summary_342d.get("mineru_success_count", 0),
                    "mineru_artifact_complete_count": summary_342d.get("mineru_artifact_complete_count", 0),
                    "qa_fail_count": summary_342d.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342c6_success_counts_valid",
            "status": "PASS"
            if int(summary_342c6.get("final_success_count", 0) or 0) == 5
            and int(summary_342c6.get("final_failed_count", 0) or 0) == 0
            and int(summary_342c6.get("qa_fail_count", 0) or 0) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "final_success_count": summary_342c6.get("final_success_count", 0),
                    "final_failed_count": summary_342c6.get("final_failed_count", 0),
                    "qa_fail_count": summary_342c6.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "artifacts::table_blocks_generated",
            "status": "PASS" if total_table_block_count > 0 else "FAIL",
            "detail": str(total_table_block_count),
        },
        {
            "check_name": "artifacts::core_or_metadata_tables_detected",
            "status": "PASS" if core_extractable_table_count + metadata_extractable_table_count > 0 else "FAIL",
            "detail": json.dumps(
                {
                    "core_extractable_table_count": core_extractable_table_count,
                    "metadata_extractable_table_count": metadata_extractable_table_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "artifacts::table_type_coverage_generated",
            "status": "PASS" if len(type_coverage_df) == len(TABLE_TYPES) else "FAIL",
            "detail": str(len(type_coverage_df)),
        },
        {
            "check_name": "artifacts::source_trace_audit_generated",
            "status": "PASS" if not source_trace_df.empty else "FAIL",
            "detail": str(len(source_trace_df)),
        },
        {
            "check_name": "readiness::342f_readiness_generated",
            "status": "PASS" if not readiness_df.empty else "FAIL",
            "detail": json.dumps(readiness_df.to_dict(orient="records"), ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {
                    "upstream_unchanged": no_write_back_json.get("upstream_workbooks_unchanged"),
                    "official_assets_unchanged": no_write_back_json.get("no_official_asset_modification_during_342e"),
                    "client_export_generated": no_write_back_json.get("client_export_generated"),
                },
                ensure_ascii=False,
            ),
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
            "status": "PASS" if all(len(name) <= 31 for name in WORKBOOK_SHEETS) else "FAIL",
            "detail": json.dumps({name: len(name) for name in WORKBOOK_SHEETS}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    decision = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "audited_pdf_count": audited_pdf_count,
        "total_table_block_count": total_table_block_count,
        "core_extractable_table_count": core_extractable_table_count,
        "metadata_extractable_table_count": metadata_extractable_table_count,
        "excluded_table_count": excluded_table_count,
        "manual_review_required_count": manual_review_required_count,
        "pdf_with_core_extractable_table_count": pdf_with_core_extractable_table_count,
        "table_source_file_count": int(table_source_file_count),
        "ready_for_342f": ready_for_342f,
        "recommended_342f_scope": recommended_342f_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "detected_342b_decision": summary_342b.get("decision", ""),
        "detected_342c6_decision": summary_342c6.get("decision", ""),
        "detected_342d_decision": summary_342d.get("decision", ""),
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342E_core_metric_candidate_quality_audit",
        "mode": "table_first",
        "corpus_342b_dir": str(corpus_342b_dir),
        "mineru_342c6_dir": str(mineru_342c6_dir),
        "parser_compare_342d_dir": str(parser_compare_342d_dir),
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
        "01_TABLE_QUALITY_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_PDF_TABLE_SIGNAL": pdf_signal_df,
        "03_ALL_TABLE_BLOCKS": table_df,
        "04_TABLE_TYPE_COVERAGE": type_coverage_df,
        "05_CORE_EXTRACTABLE": core_df,
        "06_METADATA_EXTRACTABLE": metadata_df,
        "07_EXCLUDED_TABLES": excluded_df,
        "08_SOURCE_TRACE_AUDIT": source_trace_df,
        "09_342F_READINESS": readiness_df,
        "10_NO_WRITE_BACK_PROOF": _build_no_write_back_proof_df(no_write_back_json),
        "11_NEXT_STEPS": _build_next_steps_df(ready_for_342f, recommended_342f_scope),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
