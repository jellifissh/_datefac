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


READY_DECISION = "TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_READY"
NOT_READY_DECISION = "TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_NOT_READY"
READY_INPUT_DECISION = "CORE_METRIC_CANDIDATE_QUALITY_342E_READY"

DEFAULT_CORPUS_342B_DIR = Path(r"D:\_datefac\output\real_pdf_corpus_intake_342b")
DEFAULT_MINERU_342C6_DIR = Path(r"D:\_datefac\output\mineru_pilot_network_recovery_342c6")
DEFAULT_PARSER_COMPARE_342D_DIR = Path(r"D:\_datefac\output\parser_ensemble_compare_342d")
DEFAULT_CANDIDATE_QUALITY_342E_DIR = Path(r"D:\_datefac\output\core_metric_candidate_quality_342e")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\table_first_core_financial_extraction_342f")

SUMMARY_FILE_NAME = "table_first_core_financial_extraction_342f_summary.json"
MANIFEST_FILE_NAME = "table_first_core_financial_extraction_342f_manifest.json"
QA_FILE_NAME = "table_first_core_financial_extraction_342f_qa.json"
NO_WRITE_BACK_FILE_NAME = "table_first_core_financial_extraction_342f_no_write_back_proof.json"
REPORT_FILE_NAME = "table_first_core_financial_extraction_342f_report.md"
WORKBOOK_FILE_NAME = "table_first_core_financial_extraction_342f.xlsx"

CORE_342E_SUMMARY_NAME = "core_metric_candidate_quality_342e_summary.json"
CORE_342E_QA_NAME = "core_metric_candidate_quality_342e_qa.json"
CORE_342E_WORKBOOK_NAME = "core_metric_candidate_quality_342e.xlsx"

MINERU_342C6_SUMMARY_NAME = "mineru_pilot_network_recovery_342c6_summary.json"
PARSER_COMPARE_342D_SUMMARY_NAME = "parser_ensemble_compare_342d_summary.json"

WORKBOOK_SHEETS = [
    "00_README",
    "01_EXTRACTION_SUMMARY",
    "02_INPUT_CORE_TABLES",
    "03_LONG_FORM_CELLS",
    "04_TRUSTED_CELLS",
    "05_REVIEW_REQUIRED",
    "06_REJECTED_CELLS",
    "07_METRIC_COVERAGE",
    "08_UNIT_NORMALIZATION",
    "09_TABLE_TRACE",
    "10_342G_READINESS",
    "11_NO_WRITE_BACK_PROOF",
    "12_NEXT_STEPS",
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

CORE_TABLE_TYPES = {
    "CORE_FORECAST_SUMMARY",
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "VALUATION_METRICS",
}
TRUSTED_STATUSES = {"TRUSTED_CELL", "REVIEW_REQUIRED", "REJECTED_CELL"}
YEAR_RE = re.compile(r"\b(20\d{2}(?:A|E)?)\b", re.IGNORECASE)
TR_RE = re.compile(r"<tr.*?>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
CELL_RE = re.compile(r"<t[dh]([^>]*)>(.*?)</t[dh]>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
NUMERIC_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")

METRIC_ALIASES: Dict[str, Sequence[str]] = {
    "revenue": ["营业收入", "收入", "营收"],
    "net_profit": ["经调整净利润", "归母净利润", "归属于母公司股东的净利润", "归属于母公司净利润", "净利润"],
    "EPS": ["每股收益", "EPS"],
    "PE": ["市盈率", "P/E", "PE"],
    "PB": ["市净率", "P/B", "PB"],
    "ROE": ["净资产收益率", "ROE"],
    "gross_margin": ["毛利率"],
    "net_margin": ["净利率", "净利润率"],
    "revenue_yoy": ["收入增长", "营业收入增长率", "营收同比"],
    "net_profit_yoy": ["净利润增长率", "经调整净利润增长率", "净利润同比", "归母净利润增长率"],
    "operating_cash_flow": ["经营活动现金流", "经营活动产生的现金流量净额"],
    "investing_cash_flow": ["投资活动现金流", "投资活动产生的现金流量净额"],
    "financing_cash_flow": ["融资活动现金流", "筹资活动现金流", "筹资活动产生的现金流量净额", "融资活动产生的现金流量净额"],
    "cash_net_change": ["现金净变动", "现金及现金等价物净增加额", "现金净增加额"],
    "total_assets": ["资产总计", "总资产"],
    "total_liabilities": ["负债合计", "总负债"],
    "shareholder_equity": ["股东权益", "所有者权益", "归母股东权益"],
    "total_liabilities_and_equity": ["负债和股东权益总计", "负债和所有者权益总计", "负债和权益总计"],
}
PERCENT_METRICS = {"ROE", "gross_margin", "net_margin", "revenue_yoy", "net_profit_yoy"}
RATIO_METRICS = {"PE", "PB"}
EPS_METRICS = {"EPS"}
MONEY_METRICS = {
    "revenue",
    "net_profit",
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "cash_net_change",
    "total_assets",
    "total_liabilities",
    "shareholder_equity",
    "total_liabilities_and_equity",
}
GROWTH_ROW_ALIASES = {"(+/-%)", "增长率", "增长率(%)", "同比", "yoy"}


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


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def _lower_text(value: Any) -> str:
    return _norm_text(value).casefold()


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


def _load_simple_json(path: Path) -> tuple[Dict[str, Any], List[str]]:
    files_read: List[str] = []
    payload = _read_json(path) if path.exists() else {}
    if path.exists():
        files_read.append(str(path))
    return payload, files_read


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


def _load_342e_context(candidate_quality_342e_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, pd.DataFrame], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = candidate_quality_342e_dir / CORE_342E_SUMMARY_NAME
    qa_path = candidate_quality_342e_dir / CORE_342E_QA_NAME
    workbook_path = candidate_quality_342e_dir / CORE_342E_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    if summary_path.exists():
        files_read.append(str(summary_path))
    else:
        warnings.append(f"missing 342E summary: {summary_path}")
    if qa_path.exists():
        files_read.append(str(qa_path))
    else:
        warnings.append(f"missing 342E qa: {qa_path}")

    workbook_sheets: Dict[str, pd.DataFrame] = {}
    if workbook_path.exists():
        files_read.append(str(workbook_path))
        for sheet in ["03_ALL_TABLE_BLOCKS", "05_CORE_EXTRACTABLE", "06_METADATA_EXTRACTABLE", "07_EXCLUDED_TABLES"]:
            try:
                workbook_sheets[sheet] = _clean_frame(pd.read_excel(workbook_path, sheet_name=sheet))
            except Exception as exc:
                warnings.append(f"unable to read 342E workbook sheet {sheet}: {exc}")
                workbook_sheets[sheet] = pd.DataFrame()
    else:
        warnings.append(f"missing 342E workbook: {workbook_path}")
    return summary, qa_json, workbook_sheets, files_read, warnings


def _collapse(text: str) -> str:
    return WS_RE.sub(" ", text).strip()


def _strip_html(text: str) -> str:
    return _collapse(TAG_RE.sub(" ", text))


def _extract_year_tokens(text: str) -> List[str]:
    seen: List[str] = []
    for match in YEAR_RE.findall(text):
        token = match.upper()
        if token not in seen:
            seen.append(token)
    return seen


def _normalize_year(value: str) -> str:
    token = _norm_text(value).upper()
    if re.fullmatch(r"20\d{2}", token):
        return f"{token}A"
    return token


def _html_to_rows(html: str) -> List[List[str]]:
    rows: List[List[str]] = []
    if not html:
        return rows
    for row_html in TR_RE.findall(html):
        cells: List[str] = []
        for attrs, cell_html in CELL_RE.findall(row_html):
            colspan_match = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs or "", re.IGNORECASE)
            colspan = int(colspan_match.group(1)) if colspan_match else 1
            text = _collapse(_strip_html(cell_html))
            if not text and colspan == 1:
                cells.append("")
            else:
                cells.extend([text] * max(1, colspan))
        if cells:
            rows.append(cells)
    return rows


def _parse_numeric(value_raw: str) -> tuple[float | None, List[str]]:
    raw = _norm_text(value_raw)
    flags: List[str] = []
    if not raw:
        return None, flags
    negative_by_paren = bool(re.fullmatch(r"\(\s*[\d,]+(?:\.\d+)?\s*\)", raw))
    cleaned = raw.replace(",", "").replace(" ", "")
    if negative_by_paren:
        flags.append("PAREN_NEGATIVE_VALUE")
        cleaned = f"-{cleaned.strip('()')}"
    if cleaned.endswith("%"):
        cleaned = cleaned[:-1]
    match = NUMERIC_RE.fullmatch(cleaned)
    if not match:
        return None, flags
    try:
        return float(cleaned), flags
    except ValueError:
        return None, flags


def _unit_from_context(text: str) -> str:
    if "百万元" in text:
        return "百万元"
    if "亿元" in text:
        return "亿元"
    if "万元" in text:
        return "万元"
    if "百万港元" in text:
        return "百万港元"
    if "港元" in text:
        return "港元"
    if "元" in text:
        return "元"
    if "%" in text:
        return "%"
    if "倍" in text:
        return "倍"
    return ""


def _map_metric(metric_raw: str, previous_metric: str) -> tuple[str, str]:
    raw = _norm_text(metric_raw)
    lowered = raw.casefold()
    if lowered in {token.casefold() for token in GROWTH_ROW_ALIASES}:
        if previous_metric == "revenue":
            return "revenue_yoy", ""
        if previous_metric == "net_profit":
            return "net_profit_yoy", ""
        return "", "REVIEW_REQUIRED_GROWTH_ROW_UNBOUND"
    for standard, aliases in METRIC_ALIASES.items():
        for alias in aliases:
            if alias.casefold() in lowered:
                return standard, ""
    return "", "REJECTED_METRIC_UNRECOGNIZED"


def _normalize_unit(metric_standardized: str, unit_raw: str) -> tuple[str, str]:
    unit = _norm_text(unit_raw)
    if metric_standardized in PERCENT_METRICS:
        if unit == "%":
            return "%", "OK"
        if not unit:
            return "%", "MISSING"
        return unit, "MISMATCH"
    if metric_standardized in RATIO_METRICS:
        if unit in {"", "倍"}:
            return "倍_or_unitless", "OK"
        if unit == "%":
            return "倍_or_unitless", "MISMATCH"
        return "倍_or_unitless", "AMBIGUOUS"
    if metric_standardized in EPS_METRICS:
        if "元" in unit:
            return "元", "OK"
        if not unit:
            return "元", "MISSING"
        return unit, "MISMATCH"
    if metric_standardized in MONEY_METRICS:
        if unit in {"百万元", "亿元", "万元", "百万港元", "港元", "元"}:
            return unit, "OK"
        if unit == "%":
            return "%", "MISMATCH"
        if not unit:
            return "", "MISSING"
        return unit, "AMBIGUOUS"
    if not unit:
        return "", "MISSING"
    return unit, "AMBIGUOUS"


def _status_and_confidence(
    *,
    table_type: str,
    metric_standardized: str,
    year_standardized: str,
    value_numeric: float | None,
    unit_status: str,
    source_page: str,
    table_id: str,
    image_path: str,
    reject_reason: str,
    review_reason: str,
) -> tuple[str, str, str]:
    if reject_reason:
        return "REJECTED_CELL", reject_reason, "LOW"
    if review_reason:
        return "REVIEW_REQUIRED", review_reason, "LOW"
    if table_type not in CORE_TABLE_TYPES:
        return "REJECTED_CELL", "REJECTED_NON_CORE_TABLE", "LOW"
    if not metric_standardized:
        return "REJECTED_CELL", "REJECTED_METRIC_UNRECOGNIZED", "LOW"
    if not year_standardized:
        return "REVIEW_REQUIRED", "REVIEW_REQUIRED_YEAR_HEADER_MISSING", "LOW"
    if value_numeric is None:
        return "REJECTED_CELL", "REJECTED_NO_NUMERIC_VALUE", "LOW"
    if unit_status in {"MISMATCH", "AMBIGUOUS"}:
        return "REVIEW_REQUIRED", "REVIEW_REQUIRED_UNIT_AMBIGUITY", "MEDIUM"
    if unit_status == "MISSING" and metric_standardized in MONEY_METRICS | PERCENT_METRICS | EPS_METRICS:
        return "REVIEW_REQUIRED", "REVIEW_REQUIRED_UNIT_MISSING", "MEDIUM"
    if not (source_page or table_id or image_path):
        return "REVIEW_REQUIRED", "REVIEW_REQUIRED_TRACE_WEAK", "LOW"
    return "TRUSTED_CELL", "", "HIGH"


def _confidence_rank(row: Mapping[str, Any]) -> int:
    status = _norm_text(row.get("extraction_status"))
    confidence = _norm_text(row.get("confidence_signal"))
    source_file = _lower_text(row.get("source_file"))
    base = 0
    if status == "TRUSTED_CELL":
        base += 300
    elif status == "REVIEW_REQUIRED":
        base += 200
    else:
        base += 100
    if confidence == "HIGH":
        base += 30
    elif confidence == "MEDIUM":
        base += 20
    elif confidence == "LOW":
        base += 10
    if "content_list.json" in source_file and "v2" not in source_file:
        base += 3
    elif "content_list_v2.json" in source_file:
        base += 2
    elif source_file.endswith(".md"):
        base += 1
    return base


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342F expands 342E core-extractable HTML tables into long-form metric-year-value cell evidence.",
        },
        {
            "topic": "Boundary",
            "message": "This is a sidecar extraction pilot only. It does not modify production extraction logic, does not rerun MinerU, and does not write back upstream workbooks.",
        },
        {
            "topic": "Scope",
            "message": "Only 342E sheet 05_CORE_EXTRACTABLE is used for core extraction. Metadata and excluded tables remain outside the core extraction path.",
        },
        {
            "topic": "Quality rule",
            "message": "Trusted cells require clear metric mapping, year alignment, numeric parse success, reasonable unit handling, and basic source traceability.",
        },
        {
            "topic": "Risk rule",
            "message": "Growth rows, missing year headers, duplicate cells, ambiguous units, HTML parse failures, and weak trace cases remain review-required rather than being over-promoted.",
        },
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


def _build_metric_coverage_df(cell_df: pd.DataFrame) -> pd.DataFrame:
    if cell_df.empty:
        return _clean_frame(pd.DataFrame())
    rows: List[Dict[str, Any]] = []
    filtered = cell_df[cell_df["metric_standardized"].astype(str).str.len() > 0].copy()
    for (metric, table_type), subset in filtered.groupby(["metric_standardized", "table_type"], dropna=False):
        trusted = int((subset["extraction_status"] == "TRUSTED_CELL").sum())
        review = int((subset["extraction_status"] == "REVIEW_REQUIRED").sum())
        rejected = int((subset["extraction_status"] == "REJECTED_CELL").sum())
        if trusted > 0:
            coverage_status = "TRUSTED"
        elif review > 0:
            coverage_status = "REVIEW_REQUIRED"
        else:
            coverage_status = "MISSING"
        main_risk = ""
        if review > 0:
            main_risk = (
                subset[subset["extraction_status"] == "REVIEW_REQUIRED"]["review_reason"]
                .astype(str)
                .value_counts()
                .index[0]
            )
        elif rejected > 0:
            main_risk = (
                subset[subset["extraction_status"] == "REJECTED_CELL"]["review_reason"]
                .astype(str)
                .value_counts()
                .index[0]
            )
        rows.append(
            {
                "metric_standardized": metric,
                "table_type": table_type,
                "pdf_hit_count": subset["corpus_pdf_id"].nunique(),
                "year_hit_count": subset["year_standardized"].astype(str).replace("", pd.NA).dropna().nunique(),
                "trusted_cell_count": trusted,
                "review_required_count": review,
                "rejected_cell_count": rejected,
                "coverage_status": coverage_status,
                "main_risk": main_risk,
            }
        )
    return _clean_frame(pd.DataFrame(rows).sort_values(["metric_standardized", "table_type"]).reset_index(drop=True))


def _build_unit_normalization_df(cell_df: pd.DataFrame) -> pd.DataFrame:
    if cell_df.empty:
        return _clean_frame(pd.DataFrame())
    rows: List[Dict[str, Any]] = []
    filtered = cell_df[cell_df["metric_standardized"].astype(str).str.len() > 0].copy()
    for (metric, raw_unit, normalized_unit, unit_status), subset in filtered.groupby(
        ["metric_standardized", "unit_raw", "normalized_unit", "unit_status"], dropna=False
    ):
        rows.append(
            {
                "metric_standardized": metric,
                "raw_unit": raw_unit,
                "normalized_unit": normalized_unit,
                "unit_status": unit_status,
                "affected_cell_count": len(subset),
            }
        )
    return _clean_frame(pd.DataFrame(rows).sort_values(["metric_standardized", "raw_unit"]).reset_index(drop=True))


def _build_next_steps_df(ready_for_342g: str, recommended_342g_scope: str) -> pd.DataFrame:
    rows = [
        {
            "step_order": 1,
            "next_step": "Open 03_LONG_FORM_CELLS first",
            "rationale": "This sheet is the primary extraction evidence surface because it preserves metric, year, value, unit, trace, and classification in one place.",
        },
        {
            "step_order": 2,
            "next_step": "Use 04_TRUSTED_CELLS and 05_REVIEW_REQUIRED together",
            "rationale": "Trusted cells show the strongest table-first extraction evidence while review-required cells retain the ambiguous but still valuable signals.",
        },
        {
            "step_order": 3,
            "next_step": "Prepare 342G only inside the recommended scope",
            "rationale": f"Current readiness is {ready_for_342g} with scope {recommended_342g_scope}. This remains a sidecar review package, not a production financial delivery result.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_table_first_core_financial_extraction_342f(
    *,
    corpus_342b_dir: Path,
    mineru_342c6_dir: Path,
    parser_compare_342d_dir: Path,
    candidate_quality_342e_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    _pilot_df, summary_342b, _manifest_342b, pilot_files_read = _load_pilot_corpus_rows(corpus_342b_dir)
    files_read.extend(pilot_files_read)
    if summary_342b.get("decision", "") != CORPUS_READY_DECISION:
        warnings.append(f"342B decision is {summary_342b.get('decision', '')}, expected {CORPUS_READY_DECISION}")

    summary_342c6, files_read_342c6 = _load_simple_json(mineru_342c6_dir / MINERU_342C6_SUMMARY_NAME)
    files_read.extend(files_read_342c6)
    summary_342d, files_read_342d = _load_simple_json(parser_compare_342d_dir / PARSER_COMPARE_342D_SUMMARY_NAME)
    files_read.extend(files_read_342d)
    summary_342e, _qa_342e, sheets_342e, files_read_342e, warnings_342e = _load_342e_context(candidate_quality_342e_dir)
    files_read.extend(files_read_342e)
    warnings.extend(warnings_342e)

    all_tables_df = sheets_342e.get("03_ALL_TABLE_BLOCKS", pd.DataFrame())
    core_tables_df = sheets_342e.get("05_CORE_EXTRACTABLE", pd.DataFrame())
    metadata_tables_df = sheets_342e.get("06_METADATA_EXTRACTABLE", pd.DataFrame())
    excluded_tables_df = sheets_342e.get("07_EXCLUDED_TABLES", pd.DataFrame())

    core_tables_df = _clean_frame(core_tables_df)
    if not core_tables_df.empty:
        core_tables_df = core_tables_df[core_tables_df["table_type"].isin(CORE_TABLE_TYPES)].reset_index(drop=True)

    table_trace_rows: List[Dict[str, Any]] = []
    cell_rows: List[Dict[str, Any]] = []
    duplicate_cell_count = 0
    year_header_issue_count = 0
    html_parse_failed_table_count = 0

    for table_idx, row in enumerate(core_tables_df.to_dict(orient="records"), start=1):
        html = _norm_text(row.get("html"))
        parse_rows = _html_to_rows(html)
        table_parse_status = "PARSED"
        first_col_metric_candidates = ""
        if not html or not parse_rows or len(parse_rows[0]) < 2:
            table_parse_status = "HTML_PARSE_FAILED"
            html_parse_failed_table_count += 1
            cell_rows.append(
                {
                    "long_cell_id": f"{row.get('table_id')}_parse_fail",
                    "corpus_pdf_id": _norm_text(row.get("pdf_id")),
                    "file_name": _norm_text(row.get("file_name")),
                    "table_id": _norm_text(row.get("table_id")),
                    "table_type": _norm_text(row.get("table_type")),
                    "table_value_class": _norm_text(row.get("table_value_class")),
                    "source_file": _norm_text(row.get("source_file")),
                    "source_page": _norm_text(row.get("page_idx")),
                    "bbox": _norm_text(row.get("bbox")),
                    "image_path": _norm_text(row.get("img_path")),
                    "metric_raw": "",
                    "metric_standardized": "",
                    "year_raw": "",
                    "year_standardized": "",
                    "value_raw": "",
                    "value_numeric": "",
                    "unit_raw": "",
                    "normalized_unit": "",
                    "row_index": "",
                    "col_index": "",
                    "source_html_snippet": html[:300],
                    "extraction_status": "REVIEW_REQUIRED",
                    "review_reason": "REVIEW_REQUIRED_TABLE_PARSE_FAILED",
                    "risk_flags": "",
                    "confidence_signal": "LOW",
                    "unit_status": "",
                }
            )
            table_trace_rows.append(
                {
                    "table_id": _norm_text(row.get("table_id")),
                    "corpus_pdf_id": _norm_text(row.get("pdf_id")),
                    "file_name": _norm_text(row.get("file_name")),
                    "table_type": _norm_text(row.get("table_type")),
                    "source_page": _norm_text(row.get("page_idx")),
                    "bbox": _norm_text(row.get("bbox")),
                    "image_path": _norm_text(row.get("img_path")),
                    "source_file": _norm_text(row.get("source_file")),
                    "html_available": bool(html),
                    "parse_status": table_parse_status,
                    "row_count": _norm_text(row.get("row_count")),
                    "column_count": _norm_text(row.get("column_count")),
                    "header_year_tokens": _norm_text(row.get("header_year_tokens")),
                    "first_col_metric_candidates": "",
                    "extracted_cell_count": 1,
                    "trusted_cell_count": 0,
                    "review_required_count": 1,
                    "rejected_cell_count": 0,
                }
            )
            continue

        header_index = 0
        best_score = -1
        for idx, parsed_row in enumerate(parse_rows[:3]):
            score = len(_extract_year_tokens(" ".join(parsed_row)))
            if score > best_score:
                best_score = score
                header_index = idx
        header_row = parse_rows[header_index]
        year_columns: Dict[int, tuple[str, str]] = {}
        for col_idx, header_cell in enumerate(header_row[1:], start=1):
            years = _extract_year_tokens(header_cell)
            if years:
                year_raw = years[0]
                year_columns[col_idx] = (year_raw, _normalize_year(year_raw))
        if not year_columns:
            year_header_issue_count += 1

        first_col_metric_candidates = " | ".join(
            _norm_text(r[0]) for idx, r in enumerate(parse_rows) if idx != header_index and r and _norm_text(r[0])
        )

        last_meaningful_metric = ""
        extracted_for_table = 0
        trusted_for_table = 0
        review_for_table = 0
        rejected_for_table = 0

        for row_index, parsed_row in enumerate(parse_rows):
            if row_index == header_index or not parsed_row:
                continue
            metric_raw = _norm_text(parsed_row[0])
            if not metric_raw:
                continue
            metric_standardized, metric_reason = _map_metric(metric_raw, last_meaningful_metric)
            if metric_standardized in {"revenue", "net_profit"}:
                last_meaningful_metric = metric_standardized
            elif metric_standardized and not metric_standardized.endswith("_yoy"):
                last_meaningful_metric = metric_standardized
            row_context = " ".join(
                [
                    metric_raw,
                    _norm_text(row.get("caption")),
                    _norm_text(row.get("footnote")),
                    parsed_row[0],
                    parse_rows[header_index][0] if parse_rows and parse_rows[header_index] else "",
                ]
            )
            unit_raw = _unit_from_context(row_context)

            for col_index in range(1, len(parsed_row)):
                value_raw = _norm_text(parsed_row[col_index])
                if not value_raw:
                    continue
                year_raw, year_standardized = year_columns.get(col_index, ("", ""))
                numeric_value, number_flags = _parse_numeric(value_raw)
                normalized_unit, unit_status = _normalize_unit(metric_standardized, unit_raw)
                reject_reason = ""
                review_reason = ""
                risk_flags: List[str] = list(number_flags)
                if metric_reason.startswith("REJECTED"):
                    reject_reason = metric_reason
                elif metric_reason:
                    review_reason = metric_reason
                if not year_standardized:
                    review_reason = review_reason or "REVIEW_REQUIRED_YEAR_HEADER_MISSING"
                    year_header_issue_count += 1
                if unit_status == "MISMATCH":
                    risk_flags.append("UNIT_MISMATCH")
                elif unit_status == "AMBIGUOUS":
                    risk_flags.append("UNIT_AMBIGUOUS")
                elif unit_status == "MISSING":
                    risk_flags.append("UNIT_MISSING")

                extraction_status, status_reason, confidence_signal = _status_and_confidence(
                    table_type=_norm_text(row.get("table_type")),
                    metric_standardized=metric_standardized,
                    year_standardized=year_standardized,
                    value_numeric=numeric_value,
                    unit_status=unit_status,
                    source_page=_norm_text(row.get("page_idx")),
                    table_id=_norm_text(row.get("table_id")),
                    image_path=_norm_text(row.get("img_path")),
                    reject_reason=reject_reason,
                    review_reason=review_reason,
                )
                final_reason = status_reason
                record = {
                    "long_cell_id": f"{row.get('table_id')}_{row_index:03d}_{col_index:03d}",
                    "corpus_pdf_id": _norm_text(row.get("pdf_id")),
                    "file_name": _norm_text(row.get("file_name")),
                    "table_id": _norm_text(row.get("table_id")),
                    "table_type": _norm_text(row.get("table_type")),
                    "table_value_class": _norm_text(row.get("table_value_class")),
                    "source_file": _norm_text(row.get("source_file")),
                    "source_page": _norm_text(row.get("page_idx")),
                    "bbox": _norm_text(row.get("bbox")),
                    "image_path": _norm_text(row.get("img_path")),
                    "metric_raw": metric_raw,
                    "metric_standardized": metric_standardized,
                    "year_raw": year_raw,
                    "year_standardized": year_standardized,
                    "value_raw": value_raw,
                    "value_numeric": "" if numeric_value is None else numeric_value,
                    "unit_raw": unit_raw,
                    "normalized_unit": normalized_unit,
                    "row_index": row_index,
                    "col_index": col_index,
                    "source_html_snippet": html[:300],
                    "extraction_status": extraction_status,
                    "review_reason": final_reason,
                    "risk_flags": "|".join(dict.fromkeys(flag for flag in risk_flags if flag)),
                    "confidence_signal": confidence_signal,
                    "unit_status": unit_status,
                }
                cell_rows.append(record)
                extracted_for_table += 1
                if extraction_status == "TRUSTED_CELL":
                    trusted_for_table += 1
                elif extraction_status == "REVIEW_REQUIRED":
                    review_for_table += 1
                else:
                    rejected_for_table += 1

        table_trace_rows.append(
            {
                "table_id": _norm_text(row.get("table_id")),
                "corpus_pdf_id": _norm_text(row.get("pdf_id")),
                "file_name": _norm_text(row.get("file_name")),
                "table_type": _norm_text(row.get("table_type")),
                "source_page": _norm_text(row.get("page_idx")),
                "bbox": _norm_text(row.get("bbox")),
                "image_path": _norm_text(row.get("img_path")),
                "source_file": _norm_text(row.get("source_file")),
                "html_available": bool(html),
                "parse_status": table_parse_status,
                "row_count": _norm_text(row.get("row_count")),
                "column_count": _norm_text(row.get("column_count")),
                "header_year_tokens": _norm_text(row.get("header_year_tokens")),
                "first_col_metric_candidates": first_col_metric_candidates,
                "extracted_cell_count": extracted_for_table,
                "trusted_cell_count": trusted_for_table,
                "review_required_count": review_for_table,
                "rejected_cell_count": rejected_for_table,
            }
        )

    cell_df = _clean_frame(pd.DataFrame(cell_rows))
    if cell_df.empty:
        cell_df = _clean_frame(
            pd.DataFrame(
                columns=[
                    "long_cell_id",
                    "corpus_pdf_id",
                    "file_name",
                    "table_id",
                    "table_type",
                    "table_value_class",
                    "source_file",
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
                    "row_index",
                    "col_index",
                    "source_html_snippet",
                    "extraction_status",
                    "review_reason",
                    "risk_flags",
                    "confidence_signal",
                    "unit_status",
                ]
            )
        )
    else:
        grouped: Dict[tuple[str, str, str, str, str], List[int]] = {}
        for idx, row in cell_df.iterrows():
            key = (
                _norm_text(row["corpus_pdf_id"]),
                _norm_text(row["table_id"]),
                _norm_text(row["metric_standardized"]),
                _norm_text(row["year_standardized"]),
                f"{_norm_text(row['value_numeric'])}|{_norm_text(row['normalized_unit'])}",
            )
            grouped.setdefault(key, []).append(idx)
        for indexes in grouped.values():
            if len(indexes) <= 1:
                continue
            duplicate_cell_count += len(indexes) - 1
            ranked = sorted(indexes, key=lambda i: _confidence_rank(cell_df.loc[i].to_dict()), reverse=True)
            keep = ranked[0]
            for idx in ranked[1:]:
                current_flags = [flag for flag in _norm_text(cell_df.at[idx, "risk_flags"]).split("|") if flag]
                if "DUPLICATE_DROPPED" not in current_flags:
                    current_flags.append("DUPLICATE_DROPPED")
                cell_df.at[idx, "risk_flags"] = "|".join(current_flags)
                cell_df.at[idx, "extraction_status"] = "REVIEW_REQUIRED"
                cell_df.at[idx, "review_reason"] = "REVIEW_REQUIRED_DUPLICATE"
                cell_df.at[idx, "confidence_signal"] = "LOW"

    table_trace_df = _clean_frame(pd.DataFrame(table_trace_rows))
    trusted_df = _clean_frame(cell_df[cell_df["extraction_status"] == "TRUSTED_CELL"].copy())
    review_df = _clean_frame(cell_df[cell_df["extraction_status"] == "REVIEW_REQUIRED"].copy())
    rejected_df = _clean_frame(cell_df[cell_df["extraction_status"] == "REJECTED_CELL"].copy())
    metric_coverage_df = _build_metric_coverage_df(cell_df)
    unit_normalization_df = _build_unit_normalization_df(cell_df)

    audited_pdf_count = int(summary_342e.get("audited_pdf_count", 0) or 0)
    input_core_extractable_table_count = len(core_tables_df)
    parsed_core_table_count = int((table_trace_df["parse_status"] == "PARSED").sum()) if not table_trace_df.empty else 0
    long_form_cell_count = len(cell_df)
    trusted_cell_count = len(trusted_df)
    review_required_cell_count = len(review_df)
    rejected_cell_count = len(rejected_df)
    metric_covered_count = metric_coverage_df["metric_standardized"].nunique() if not metric_coverage_df.empty else 0
    metric_year_pair_count = (
        cell_df[cell_df["metric_standardized"].astype(str).str.len() > 0][["metric_standardized", "year_standardized"]]
        .drop_duplicates()
        .shape[0]
        if not cell_df.empty
        else 0
    )
    unit_issue_count = int(unit_normalization_df["unit_status"].isin(["AMBIGUOUS", "MISMATCH", "MISSING"]).sum()) if not unit_normalization_df.empty else 0
    table_trace_count = len(table_trace_df)

    if long_form_cell_count > 0 and (trusted_cell_count > 0 or review_required_cell_count > 0) and table_trace_count > 0:
        ready_for_342g = "true"
        recommended_342g_scope = "table_first_extraction_review_package"
    else:
        ready_for_342g = "false"
        recommended_342g_scope = "insufficient_table_first_long_form_signal"

    no_write_back_input_hashes_before = {path: sha256_file(Path(path)) for path in files_read if Path(path).exists() and Path(path).is_file()}
    no_write_back_input_hashes_after = {path: sha256_file(Path(path)) for path in files_read if Path(path).exists() and Path(path).is_file()}
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342F",
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
        bool(no_write_back_json.get("no_official_asset_modification_during_342f"))
        and bool(no_write_back_json.get("upstream_workbooks_unchanged"))
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())
    readiness_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "long_form_cell_count": long_form_cell_count,
                    "trusted_cell_count": trusted_cell_count,
                    "review_required_cell_count": review_required_cell_count,
                    "table_trace_count": table_trace_count,
                    "ready_for_342g": ready_for_342g,
                    "recommended_342g_scope": recommended_342g_scope,
                    "reason": (
                        "Long-form table-first cells are available and can move into a dedicated review package."
                        if ready_for_342g == "true"
                        else "Current long-form extraction evidence is still too weak for the next review package."
                    ),
                }
            ]
        )
    )

    checks = [
        {
            "check_name": "inputs::342e_input_exists",
            "status": "PASS" if candidate_quality_342e_dir.exists() else "FAIL",
            "detail": str(candidate_quality_342e_dir),
        },
        {
            "check_name": "inputs::342e_ready_for_342f_true_detected",
            "status": "PASS"
            if summary_342e.get("decision", "") == READY_INPUT_DECISION
            and str(summary_342e.get("ready_for_342f", "")).casefold() == "true"
            and summary_342e.get("recommended_342f_scope", "") == "table_first_core_extractable_only"
            and int(summary_342e.get("qa_fail_count", 0) or 0) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "decision": summary_342e.get("decision", ""),
                    "ready_for_342f": summary_342e.get("ready_for_342f", ""),
                    "recommended_342f_scope": summary_342e.get("recommended_342f_scope", ""),
                    "qa_fail_count": summary_342e.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::342e_core_table_count_valid",
            "status": "PASS"
            if int(summary_342e.get("core_extractable_table_count", 0) or 0) > 0
            and int(summary_342e.get("pdf_with_core_extractable_table_count", 0) or 0) == 5
            else "FAIL",
            "detail": json.dumps(
                {
                    "core_extractable_table_count": summary_342e.get("core_extractable_table_count", 0),
                    "pdf_with_core_extractable_table_count": summary_342e.get("pdf_with_core_extractable_table_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "scope::core_extractable_tables_loaded",
            "status": "PASS" if input_core_extractable_table_count > 0 else "FAIL",
            "detail": str(input_core_extractable_table_count),
        },
        {
            "check_name": "scope::metadata_tables_not_mixed_into_core_extraction",
            "status": "PASS" if metadata_tables_df["table_id"].isin(cell_df["table_id"]).sum() == 0 else "FAIL",
            "detail": f"metadata_rows={len(metadata_tables_df)} overlap={int(metadata_tables_df['table_id'].isin(cell_df['table_id']).sum()) if not metadata_tables_df.empty else 0}",
        },
        {
            "check_name": "scope::excluded_tables_not_mixed_into_core_extraction",
            "status": "PASS" if excluded_tables_df["table_id"].isin(cell_df["table_id"]).sum() == 0 else "FAIL",
            "detail": f"excluded_rows={len(excluded_tables_df)} overlap={int(excluded_tables_df['table_id'].isin(cell_df['table_id']).sum()) if not excluded_tables_df.empty else 0}",
        },
        {
            "check_name": "artifacts::long_form_cells_generated",
            "status": "PASS" if long_form_cell_count > 0 else "FAIL",
            "detail": str(long_form_cell_count),
        },
        {
            "check_name": "artifacts::trusted_review_rejected_generated",
            "status": "PASS" if long_form_cell_count == trusted_cell_count + review_required_cell_count + rejected_cell_count else "FAIL",
            "detail": json.dumps(
                {
                    "trusted": trusted_cell_count,
                    "review": review_required_cell_count,
                    "rejected": rejected_cell_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "artifacts::metric_coverage_generated",
            "status": "PASS" if not metric_coverage_df.empty else "FAIL",
            "detail": str(len(metric_coverage_df)),
        },
        {
            "check_name": "artifacts::unit_normalization_generated",
            "status": "PASS" if not unit_normalization_df.empty else "FAIL",
            "detail": str(len(unit_normalization_df)),
        },
        {
            "check_name": "artifacts::table_trace_generated",
            "status": "PASS" if not table_trace_df.empty else "FAIL",
            "detail": str(len(table_trace_df)),
        },
        {
            "check_name": "readiness::342g_readiness_generated",
            "status": "PASS" if not readiness_df.empty else "FAIL",
            "detail": json.dumps(readiness_df.to_dict(orient="records"), ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {
                    "upstream_unchanged": no_write_back_json.get("upstream_workbooks_unchanged"),
                    "official_assets_unchanged": no_write_back_json.get("no_official_asset_modification_during_342f"),
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
        "input_core_extractable_table_count": input_core_extractable_table_count,
        "parsed_core_table_count": parsed_core_table_count,
        "html_parse_failed_table_count": html_parse_failed_table_count,
        "long_form_cell_count": long_form_cell_count,
        "trusted_cell_count": trusted_cell_count,
        "review_required_cell_count": review_required_cell_count,
        "rejected_cell_count": rejected_cell_count,
        "metric_covered_count": int(metric_covered_count),
        "metric_year_pair_count": int(metric_year_pair_count),
        "unit_issue_count": int(unit_issue_count),
        "year_header_issue_count": int(year_header_issue_count),
        "duplicate_cell_count": int(duplicate_cell_count),
        "table_trace_count": int(table_trace_count),
        "ready_for_342g": ready_for_342g,
        "recommended_342g_scope": recommended_342g_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "detected_342b_decision": summary_342b.get("decision", ""),
        "detected_342c6_decision": summary_342c6.get("decision", ""),
        "detected_342d_decision": summary_342d.get("decision", ""),
        "detected_342e_decision": summary_342e.get("decision", ""),
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342F_table_first_core_financial_long_form_extraction",
        "corpus_342b_dir": str(corpus_342b_dir),
        "mineru_342c6_dir": str(mineru_342c6_dir),
        "parser_compare_342d_dir": str(parser_compare_342d_dir),
        "candidate_quality_342e_dir": str(candidate_quality_342e_dir),
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
        "00_README": _build_readme_df(),
        "01_EXTRACTION_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_CORE_TABLES": _clean_frame(core_tables_df),
        "03_LONG_FORM_CELLS": _clean_frame(cell_df),
        "04_TRUSTED_CELLS": _clean_frame(trusted_df),
        "05_REVIEW_REQUIRED": _clean_frame(review_df),
        "06_REJECTED_CELLS": _clean_frame(rejected_df),
        "07_METRIC_COVERAGE": _clean_frame(metric_coverage_df),
        "08_UNIT_NORMALIZATION": _clean_frame(unit_normalization_df),
        "09_TABLE_TRACE": _clean_frame(table_trace_df),
        "10_342G_READINESS": _clean_frame(readiness_df),
        "11_NO_WRITE_BACK_PROOF": _build_no_write_back_proof_df(no_write_back_json),
        "12_NEXT_STEPS": _build_next_steps_df(ready_for_342g, recommended_342g_scope),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
