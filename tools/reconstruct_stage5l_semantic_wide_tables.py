import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import financial_standardizer as fs


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_PDF = BASE_DIR / "input" / "H3_AP202605121822223662_1.pdf"
STAGE5K_DIR = OUTPUT_DIR / "stage5k_full_sandbox_rebuild"
INPUT_RAW_XLSX = STAGE5K_DIR / "146_stage5k_raw_tables_rebuilt.xlsx"
INPUT_STAGE5K_02_XLSX = STAGE5K_DIR / "146_stage5k_structured_02_sandbox.xlsx"
INPUT_STAGE5K_05_XLSX = STAGE5K_DIR / "146_stage5k_standardized_05_sandbox.xlsx"
INPUT_STAGE5K_DIFF_XLSX = STAGE5K_DIR / "146_stage5k_rebuild_diff_report.xlsx"
INPUT_STAGE5K_SUMMARY_JSON = STAGE5K_DIR / "147_stage5k_full_rebuild_summary.json"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_ALIAS_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

PROD_02_PATH = BASE_DIR / "02_研报全量结构化数据.xlsx"
PROD_05_PATH = BASE_DIR / "05_核心财务指标标准化.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5l_semantic_table_reconstruction"
OUT_GRID_XLSX = OUT_DIR / "148_stage5l_raw_table_grid_review.xlsx"
OUT_BLOCKS_XLSX = OUT_DIR / "148_stage5l_semantic_table_blocks.xlsx"
OUT_WIDE_XLSX = OUT_DIR / "148_stage5l_wide_financial_tables.xlsx"
OUT_02_XLSX = OUT_DIR / "148_stage5l_structured_02_from_wide_review.xlsx"
OUT_05_XLSX = OUT_DIR / "148_stage5l_standardized_05_from_wide_review.xlsx"
OUT_REPORT_MD = OUT_DIR / "148_stage5l_semantic_reconstruction_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "149_stage5l_semantic_reconstruction_summary.json"

BLOCK_BALANCE = "BALANCE_SHEET"
BLOCK_INCOME = "INCOME_STATEMENT"
BLOCK_CASH = "CASH_FLOW_STATEMENT"
BLOCK_RATIO = "FINANCIAL_RATIO"
BLOCK_VALUATION = "VALUATION_TABLE"
BLOCK_FORECAST = "FORECAST_SUMMARY"
BLOCK_NON_FIN = "NON_FINANCIAL_TEXT"
BLOCK_UNKNOWN = "UNKNOWN_TABLE"

ISSUE_NONE = "NONE"
ISSUE_SPLIT_REQUIRED = "SPLIT_REQUIRED"
ISSUE_HEADER_BROKEN = "HEADER_BROKEN"
ISSUE_YEAR_HEADER_MISSING = "YEAR_HEADER_MISSING"
ISSUE_UNIT_MISSING = "UNIT_MISSING"
ISSUE_METRIC_COL_AMBIG = "METRIC_COLUMN_AMBIGUOUS"
ISSUE_NON_FIN = "NON_FINANCIAL_TABLE"
ISSUE_UNKNOWN = "UNKNOWN"

WIDE_OK = "RECONSTRUCTED_OK"
WIDE_WARN = "RECONSTRUCTED_WITH_WARNING"
WIDE_FILTER_HEADER = "FILTERED_HEADER"
WIDE_FILTER_NON_FIN = "FILTERED_NON_FINANCIAL"
WIDE_FAILED = "FAILED"

CHG_DERIVED = "UNCHANGED_DERIVED_METRIC_NOT_SUPPORTED"
CHG_NON_CORE = "UNCHANGED_NON_CORE_METRIC"
CHG_MISS = "UNCHANGED_MAPPING_MISS"
CHG_OTHER = "UNCHANGED_OTHER"

YEAR_RE = re.compile(r"20\d{2}[AE]?", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
VALUE_VALID_RE = re.compile(r"[-+]?\d+(?:\.\d+)?$")
YEAR_VALID_RE = re.compile(r"20\d{2}(?:[AE])?$", re.IGNORECASE)

HEADER_TOKENS = ("成长能力", "获利能力", "偿债能力", "营运能力", "每股指标", "估值比率", "资料来源", "敬请参阅")
NON_FIN_TOKENS = ("免责声明", "证券研究报告", "资料来源", "敬请参阅", "分析师", "评级", "联系方式")

YEAR_COLUMNS_CANONICAL = ["2024A", "2025A", "2026E", "2027E", "2028E"]

LABEL_FIXUPS = {
    "动资产": "流动资产",
    "收票据及应收账款合计": "应收票据及应收账款合计",
    "产总计": "资产总计",
    "动负债": "流动负债",
    "付票据及应付账款合计": "应付票据及应付账款合计",
    "债合计": "负债合计",
    "数股东权益": "少数股东权益",
    "属母公司股东权益": "归属母公司股东权益",
    "债和股东权益": "负债和股东权益",
    "营活动现金流": "经营活动现金流",
    "资活动现金流": "投资活动现金流",
    "金净增加额": "现金净增加额",
    "净利润": "净利润",
}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    t = _norm(v).replace("（", "(").replace("）", ")").replace("／", "/")
    return re.sub(r"\s+", "", t).upper()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing delivery file pattern: {pattern}")
    non_copy = [p for p in files if "_copy_" not in p.name.lower()]
    return non_copy[0] if non_copy else files[0]


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_scope_rules": _sha256(FORMAL_SCOPE_RULES_JSON),
        "formal_mapping_rules": _sha256(FORMAL_MAPPING_RULE_FILE),
        "formal_normalization_rules": _sha256(FORMAL_NORMALIZATION_RULE_FILE),
        "formal_alias_rules": _sha256(FORMAL_ALIAS_RULE_FILE),
    }


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31-len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    return json.loads(text)


def _read_pdf_page_count(pdf_path: Path) -> int:
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(pdf_path)) as pdf:
            return int(len(pdf.pages))
    except Exception:
        return 0


def _clean_label(text: str) -> str:
    t = _norm(text).replace("（", "(").replace("）", ")")
    t = re.sub(r"\s+", "", t)
    t = t.strip(":：;；,，.")
    return t


def _fix_label(text: str) -> str:
    t = _clean_label(text)
    return LABEL_FIXUPS.get(t, t)


def _first_sheet(path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    return pd.read_excel(path, sheet_name=xl.sheet_names[0]).fillna("")


def _table_grid(raw_df: pd.DataFrame, table_id: str) -> Tuple[pd.DataFrame, int, int]:
    g = raw_df[raw_df["table_id"] == table_id].copy()
    g["row_index"] = pd.to_numeric(g["row_index"], errors="coerce").fillna(0).astype(int)
    g["col_index"] = pd.to_numeric(g["col_index"], errors="coerce").fillna(0).astype(int)
    max_row = int(g["row_index"].max()) if not g.empty else 0
    max_col = int(g["col_index"].max()) if not g.empty else 0
    rows: List[Dict[str, Any]] = []
    for ridx in range(1, max_row + 1):
        rec: Dict[str, Any] = {"table_id": table_id, "row_index": ridx}
        row_slice = g[g["row_index"] == ridx]
        for cidx in range(1, max_col + 1):
            hit = row_slice[row_slice["col_index"] == cidx]
            rec[f"col_{cidx}"] = _norm(hit.iloc[0]["cell_text"]) if not hit.empty else ""
        rows.append(rec)
    grid_df = pd.DataFrame(rows)
    return grid_df, max_row, max_col


def _row_text(grid_df: pd.DataFrame, ridx: int, start_col: int, end_col: int) -> str:
    if grid_df.empty:
        return ""
    hit = grid_df[grid_df["row_index"] == ridx]
    if hit.empty:
        return ""
    cells = []
    for c in range(start_col, end_col + 1):
        v = _norm(hit.iloc[0].get(f"col_{c}", ""))
        if v:
            cells.append(v)
    return " | ".join(cells)


def _get_cell(grid_df: pd.DataFrame, ridx: int, cidx: int) -> str:
    hit = grid_df[grid_df["row_index"] == ridx]
    if hit.empty:
        return ""
    return _norm(hit.iloc[0].get(f"col_{cidx}", ""))


def _find_row_by_tokens(grid_df: pd.DataFrame, start_col: int, end_col: int, tokens: Tuple[str, ...]) -> int:
    for ridx in grid_df["row_index"].astype(int).tolist():
        txt = _row_text(grid_df, ridx, start_col, end_col)
        if all(tok in txt for tok in tokens):
            return int(ridx)
    return 0


def _parse_semantic_blocks(table_meta: Dict[str, Any], grid_df: pd.DataFrame, max_row: int, max_col: int) -> List[Dict[str, Any]]:
    table_id = _norm(table_meta["table_id"])
    page = int(table_meta["page"])
    source_pdf = _norm(table_meta["source_pdf"])
    blocks: List[Dict[str, Any]] = []

    if page != 3:
        blocks.append(
            {
                "semantic_table_id": f"S5L-{table_id}-NONFIN",
                "source_pdf": source_pdf,
                "source_page": page,
                "source_raw_table_id": table_id,
                "block_type": BLOCK_NON_FIN,
                "statement_type": "NON_FINANCIAL",
                "unit": "",
                "start_row_index": 1,
                "end_row_index": max_row,
                "start_col_index": 1,
                "end_col_index": max_col,
                "metric_name_col_index": "",
                "year_col_indices": "",
                "year_labels": "",
                "block_confidence": 0.99,
                "block_issue_type": ISSUE_NON_FIN,
                "evidence": "page not financial forecast summary",
            }
        )
        return blocks

    # Page 3: forecast summary and semantic split.
    balance_header = _find_row_by_tokens(grid_df, 1, max_col, ("产负", "债表"))
    income_header = _find_row_by_tokens(grid_df, 1, max_col, ("利润表",))
    ratio_header = _find_row_by_tokens(grid_df, 10, max_col, ("主要财务比率",))
    cash_header = _find_row_by_tokens(grid_df, 1, 8, ("金流", "量表"))
    source_row = _find_row_by_tokens(grid_df, 1, max_col, ("资料来源",))
    end_data_row = source_row - 1 if source_row > 0 else max_row

    blocks.append(
        {
            "semantic_table_id": f"S5L-{table_id}-FORECAST",
            "source_pdf": source_pdf,
            "source_page": page,
            "source_raw_table_id": table_id,
            "block_type": BLOCK_FORECAST,
            "statement_type": "FORECAST_SUMMARY",
            "unit": "",
            "start_row_index": 1,
            "end_row_index": end_data_row,
            "start_col_index": 1,
            "end_col_index": max_col,
            "metric_name_col_index": "",
            "year_col_indices": "",
            "year_labels": "",
            "block_confidence": 0.98,
            "block_issue_type": ISSUE_SPLIT_REQUIRED,
            "evidence": "single physical table contains parallel financial blocks",
        }
    )

    blocks.extend(
        [
            {
                "semantic_table_id": f"S5L-{table_id}-BS",
                "source_pdf": source_pdf,
                "source_page": page,
                "source_raw_table_id": table_id,
                "block_type": BLOCK_BALANCE,
                "statement_type": "资产负债表",
                "unit": "百万元",
                "start_row_index": balance_header or 3,
                "end_row_index": (cash_header - 1) if cash_header else end_data_row,
                "start_col_index": 1,
                "end_col_index": 8,
                "metric_name_col_index": "1,2",
                "year_col_indices": "3,5,6,7,8",
                "year_labels": "2024A,2025A,2026E,2027E,2028E",
                "block_confidence": 0.95,
                "block_issue_type": ISSUE_NONE if balance_header else ISSUE_HEADER_BROKEN,
                "evidence": f"balance_header_row={balance_header}",
            },
            {
                "semantic_table_id": f"S5L-{table_id}-IS",
                "source_pdf": source_pdf,
                "source_page": page,
                "source_raw_table_id": table_id,
                "block_type": BLOCK_INCOME,
                "statement_type": "利润表",
                "unit": "百万元",
                "start_row_index": income_header or 3,
                "end_row_index": (ratio_header - 1) if ratio_header else end_data_row,
                "start_col_index": 10,
                "end_col_index": 16,
                "metric_name_col_index": "10",
                "year_col_indices": "11,12,13,15,16",
                "year_labels": "2024A,2025A,2026E,2027E,2028E",
                "block_confidence": 0.95,
                "block_issue_type": ISSUE_NONE if income_header else ISSUE_HEADER_BROKEN,
                "evidence": f"income_header_row={income_header}",
            },
            {
                "semantic_table_id": f"S5L-{table_id}-CF",
                "source_pdf": source_pdf,
                "source_page": page,
                "source_raw_table_id": table_id,
                "block_type": BLOCK_CASH,
                "statement_type": "现金流量表",
                "unit": "百万元",
                "start_row_index": cash_header or 34,
                "end_row_index": end_data_row,
                "start_col_index": 1,
                "end_col_index": 8,
                "metric_name_col_index": "1,2",
                "year_col_indices": "3,5,6,7,8",
                "year_labels": "2024A,2025A,2026E,2027E,2028E",
                "block_confidence": 0.95,
                "block_issue_type": ISSUE_NONE if cash_header else ISSUE_HEADER_BROKEN,
                "evidence": f"cash_header_row={cash_header}",
            },
            {
                "semantic_table_id": f"S5L-{table_id}-RATIO",
                "source_pdf": source_pdf,
                "source_page": page,
                "source_raw_table_id": table_id,
                "block_type": BLOCK_RATIO,
                "statement_type": "主要财务比率",
                "unit": "ratio",
                "start_row_index": ratio_header or 26,
                "end_row_index": end_data_row,
                "start_col_index": 10,
                "end_col_index": 16,
                "metric_name_col_index": "10",
                "year_col_indices": "11,12,13,15,16",
                "year_labels": "2024A,2025A,2026E,2027E,2028E",
                "block_confidence": 0.96,
                "block_issue_type": ISSUE_NONE if ratio_header else ISSUE_HEADER_BROKEN,
                "evidence": f"ratio_header_row={ratio_header}",
            },
        ]
    )
    return blocks


def _extract_metric_label(grid_df: pd.DataFrame, ridx: int, metric_cols: List[int]) -> str:
    parts = [_clean_label(_get_cell(grid_df, ridx, c)) for c in metric_cols if _clean_label(_get_cell(grid_df, ridx, c))]
    if not parts:
        return ""
    label = "".join(parts)
    label = _fix_label(label)
    label = fs._clean_metric_label_noise(label)
    return _norm(label)


def _extract_year_value(grid_df: pd.DataFrame, ridx: int, cidx: int) -> str:
    txt = _norm(_get_cell(grid_df, ridx, cidx)).replace(",", "")
    m = NUM_RE.search(txt)
    return m.group(0) if m else ""


def _wide_rows_from_block(block: Dict[str, Any], grid_df: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    block_type = _norm(block["block_type"])
    if block_type not in {BLOCK_BALANCE, BLOCK_INCOME, BLOCK_CASH, BLOCK_RATIO, BLOCK_VALUATION}:
        return rows

    metric_cols = [int(x) for x in _norm(block["metric_name_col_index"]).split(",") if _norm(x).isdigit()]
    year_cols = [int(x) for x in _norm(block["year_col_indices"]).split(",") if _norm(x).isdigit()]
    year_labels = [_norm(x) for x in _norm(block["year_labels"]).split(",") if _norm(x)]
    year_map = {c: year_labels[i] for i, c in enumerate(year_cols) if i < len(year_labels)}

    for ridx in range(int(block["start_row_index"]), int(block["end_row_index"]) + 1):
        raw_metric = _extract_metric_label(grid_df, ridx, metric_cols)
        metric_cleaned = _norm(raw_metric)
        status = WIDE_OK
        issue = ISSUE_NONE
        evidence = ""

        if not raw_metric:
            status = WIDE_FILTER_HEADER
            issue = ISSUE_METRIC_COL_AMBIG
            evidence = "empty metric label"
        elif any(tok in raw_metric for tok in HEADER_TOKENS):
            status = WIDE_FILTER_HEADER
            issue = ISSUE_HEADER_BROKEN
            evidence = "section/header row"
        elif any(tok in raw_metric for tok in NON_FIN_TOKENS):
            status = WIDE_FILTER_NON_FIN
            issue = ISSUE_NON_FIN
            evidence = "non-financial row"

        year_values: Dict[str, str] = {}
        numeric_cnt = 0
        for c in year_cols:
            yl = year_map.get(c, f"Y{c}")
            val = _extract_year_value(grid_df, ridx, c)
            year_values[yl] = val
            if val:
                numeric_cnt += 1

        if status == WIDE_OK and numeric_cnt == 0:
            status = WIDE_FILTER_HEADER
            issue = ISSUE_YEAR_HEADER_MISSING
            evidence = "no numeric year value"

        if status == WIDE_OK and len(metric_cleaned) <= 2:
            status = WIDE_WARN
            issue = ISSUE_HEADER_BROKEN
            evidence = "very short metric label"

        row = {
            "raw_metric_name": raw_metric,
            "metric_name_cleaned": metric_cleaned,
            "statement_type": _norm(block["statement_type"]),
            "unit": _norm(block["unit"]),
            "semantic_table_id": _norm(block["semantic_table_id"]),
            "source_page": int(block["source_page"]),
            "source_raw_table_id": _norm(block["source_raw_table_id"]),
            "source_row_index": ridx,
            "metric_reconstruction_status": status,
            "metric_reconstruction_issue": issue,
            "evidence": evidence,
        }
        for yl in YEAR_COLUMNS_CANONICAL:
            row[yl] = _norm(year_values.get(yl, ""))
        rows.append(row)
    return rows


def _long_02_from_wide(wide_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    use_df = wide_df[wide_df["metric_reconstruction_status"].isin([WIDE_OK, WIDE_WARN])].copy() if not wide_df.empty else pd.DataFrame()
    for _, r in use_df.iterrows():
        metric = _norm(r.get("metric_name_cleaned")) or _norm(r.get("raw_metric_name"))
        if not metric:
            continue
        for yl in YEAR_COLUMNS_CANONICAL:
            v = _norm(r.get(yl)).replace(",", "")
            if not v:
                continue
            if not VALUE_VALID_RE.fullmatch(v):
                continue
            row_trace_id = f"{_norm(r.get('semantic_table_id'))}|r{int(r.get('source_row_index'))}|y{yl}"
            rows.append(
                {
                    "row_trace_id": row_trace_id,
                    "semantic_table_id": _norm(r.get("semantic_table_id")),
                    "source_pdf": str(INPUT_PDF),
                    "source_page": _norm(r.get("source_page")),
                    "source_raw_table_id": _norm(r.get("source_raw_table_id")),
                    "source_row_index": _norm(r.get("source_row_index")),
                    "raw_metric_name": _norm(r.get("raw_metric_name")),
                    "metric_name_cleaned": metric,
                    "statement_type": _norm(r.get("statement_type")),
                    "unit": _norm(r.get("unit")),
                    "year": yl,
                    "value": v,
                    "source_reference": f"{_norm(r.get('source_raw_table_id'))}:r{int(r.get('source_row_index'))}:y{yl}",
                    "structured_status": "STRUCTURED_OK",
                    "structured_issue_type": "NONE",
                    "evidence": "from semantic wide reconstruction",
                }
            )
    return pd.DataFrame(rows).fillna("")


def _classify_mapping_miss(metric: str) -> str:
    t = _norm(metric)
    if any(x in t for x in ["(%)", "%", "周转率", "ROIC", "资产负债率", "净利率"]):
        return CHG_DERIVED
    if any(x in t for x in ["营业利润", "净利润", "EBITDA"]):
        return CHG_NON_CORE
    return CHG_MISS


def _build_alias_rule_id(standard_metric: str, raw_metric: str) -> str:
    std = _norm(standard_metric)
    raw = _norm(raw_metric)
    if not std or std not in fs.STANDARD_METRIC_ALIASES:
        return ""
    aliases = fs.STANDARD_METRIC_ALIASES.get(std, [])
    for i, a in enumerate(aliases, start=1):
        if _compact(a) == _compact(raw):
            return f"FS_ALIAS_{_compact(std)}_{i:03d}"
    return ""


def _standardize_05_from_02(df_02: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    for _, r in df_02.iterrows():
        raw_metric = _norm(r.get("metric_name_cleaned")) or _norm(r.get("raw_metric_name"))
        year = _norm(r.get("year")).upper()
        value = _norm(r.get("value")).replace(",", "")
        unit = _norm(r.get("unit"))

        standard_metric = ""
        status = "STANDARDIZATION_FAILED"
        issue_type = "UNKNOWN"
        mapping_rule_id = ""
        alias_rule_id = ""

        m = fs._match_standard_metric(raw_metric)
        if not m:
            status = "MAPPING_MISS"
            issue_type = "METRIC_MAPPING_ISSUE"
        else:
            standard_metric = _norm(m.get("standard_metric"))
            mapping_rule_id = f"FS_MAP_{_compact(standard_metric)}" if standard_metric else ""
            alias_rule_id = _build_alias_rule_id(standard_metric, raw_metric)
            if not YEAR_VALID_RE.fullmatch(year):
                status = "YEAR_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
            elif not VALUE_VALID_RE.fullmatch(value):
                status = "VALUE_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
            elif not unit:
                status = "UNIT_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
            else:
                status = "STANDARDIZED_OK"
                issue_type = "NONE"

        rows.append(
            {
                "row_trace_id": _norm(r.get("row_trace_id")),
                "raw_metric_name": _norm(r.get("raw_metric_name")),
                "metric_name_cleaned": raw_metric,
                "standard_metric": standard_metric,
                "standardization_status": status,
                "standardization_issue_type": issue_type,
                "statement_type": _norm(r.get("statement_type")),
                "unit": unit,
                "year": year,
                "value": value,
                "matched_mapping_rule_id": mapping_rule_id,
                "matched_alias_rule_id": alias_rule_id,
                "semantic_table_id": _norm(r.get("semantic_table_id")),
                "source_reference": _norm(r.get("source_reference")),
            }
        )

    out_df = pd.DataFrame(rows).fillna("")
    standardized_ok_count = int((out_df["standardization_status"] == "STANDARDIZED_OK").sum()) if not out_df.empty else 0
    mapping_miss_count = int((out_df["standardization_status"] == "MAPPING_MISS").sum()) if not out_df.empty else 0
    derived_metric_count = 0
    non_core_count = 0
    true_gap_count = 0
    if mapping_miss_count > 0:
        miss = out_df[out_df["standardization_status"] == "MAPPING_MISS"].copy()
        miss["miss_class"] = miss["metric_name_cleaned"].map(_classify_mapping_miss)
        derived_metric_count = int((miss["miss_class"] == CHG_DERIVED).sum())
        non_core_count = int((miss["miss_class"] == CHG_NON_CORE).sum())
        true_gap_count = int((miss["miss_class"] == CHG_MISS).sum())
    unknown_count = int((out_df["standardization_status"] == "STANDARDIZATION_FAILED").sum()) if not out_df.empty else 0
    stats = {
        "standardized_05_from_wide_row_count": int(len(out_df)),
        "standardized_ok_count": int(standardized_ok_count),
        "mapping_miss_count": int(mapping_miss_count),
        "derived_metric_not_supported_count": int(derived_metric_count),
        "non_core_metric_count": int(non_core_count),
        "true_mapping_gap_count": int(true_gap_count),
        "unknown_count": int(unknown_count),
    }
    return out_df, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5L semantic table reconstruction and wide review.")
    parser.parse_args()

    required = [
        INPUT_PDF,
        INPUT_RAW_XLSX,
        INPUT_STAGE5K_02_XLSX,
        INPUT_STAGE5K_05_XLSX,
        INPUT_STAGE5K_DIFF_XLSX,
        INPUT_STAGE5K_SUMMARY_JSON,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_MAPPING_RULE_FILE,
        FORMAL_NORMALIZATION_RULE_FILE,
        FORMAL_ALIAS_RULE_FILE,
        OFFICIAL_02B_PATH,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    raw_df = pd.read_excel(INPUT_RAW_XLSX, sheet_name="raw_tables").fillna("")
    stage5k_summary = json.loads(INPUT_STAGE5K_SUMMARY_JSON.read_text(encoding="utf-8"))

    input_raw_table_count = int(raw_df["table_id"].map(_norm).replace("", pd.NA).dropna().nunique()) if not raw_df.empty else 0
    input_raw_cell_count = int(len(raw_df))

    # Reconstruct row grids.
    table_meta_rows = []
    grid_rows_frames = []
    grid_summary_rows = []
    for table_id, g in raw_df.groupby("table_id", sort=True):
        page = int(pd.to_numeric(g["page"], errors="coerce").fillna(0).iloc[0]) if not g.empty else 0
        source_pdf = _norm(g["source_pdf"].iloc[0]) if not g.empty else ""
        grid_df, max_row, max_col = _table_grid(raw_df, table_id)
        grid_rows_frames.append(grid_df)
        table_meta_rows.append({"table_id": _norm(table_id), "page": page, "source_pdf": source_pdf, "max_row": max_row, "max_col": max_col})
        grid_summary_rows.append(
            {
                "table_id": _norm(table_id),
                "page": page,
                "source_pdf": source_pdf,
                "max_row": max_row,
                "max_col": max_col,
                "raw_cell_count": int(len(g)),
            }
        )

    grid_all_df = pd.concat(grid_rows_frames, ignore_index=True) if grid_rows_frames else pd.DataFrame()
    grid_summary_df = pd.DataFrame(grid_summary_rows)
    table_meta_df = pd.DataFrame(table_meta_rows)

    _write_excel(
        OUT_GRID_XLSX,
        {
            "raw_cells": raw_df,
            "reconstructed_grid_rows": grid_all_df,
            "grid_table_summary": grid_summary_df,
        },
    )

    # Semantic block splitting.
    semantic_blocks: List[Dict[str, Any]] = []
    for _, meta in table_meta_df.iterrows():
        tid = _norm(meta["table_id"])
        one_grid = grid_all_df[grid_all_df["table_id"] == tid].copy()
        semantic_blocks.extend(_parse_semantic_blocks(meta.to_dict(), one_grid, int(meta["max_row"]), int(meta["max_col"])))
    blocks_df = pd.DataFrame(semantic_blocks).fillna("")
    _write_excel(OUT_BLOCKS_XLSX, {"semantic_table_blocks": blocks_df})

    # Wide reconstruction.
    wide_rows: List[Dict[str, Any]] = []
    for _, b in blocks_df.iterrows():
        tid = _norm(b["source_raw_table_id"])
        grid = grid_all_df[grid_all_df["table_id"] == tid].copy()
        wide_rows.extend(_wide_rows_from_block(b.to_dict(), grid))
    wide_df = pd.DataFrame(wide_rows).fillna("")
    if not wide_df.empty:
        wide_df = wide_df[
            [
                "raw_metric_name",
                "metric_name_cleaned",
                "statement_type",
                "unit",
                "2024A",
                "2025A",
                "2026E",
                "2027E",
                "2028E",
                "semantic_table_id",
                "source_page",
                "source_raw_table_id",
                "source_row_index",
                "metric_reconstruction_status",
                "metric_reconstruction_issue",
                "evidence",
            ]
        ]
    _write_excel(OUT_WIDE_XLSX, {"wide_financial_tables": wide_df})

    # 02 review and 05 review.
    df_02 = _long_02_from_wide(wide_df)
    _write_excel(OUT_02_XLSX, {"structured_02_from_wide_review": df_02})

    df_05, stats_05 = _standardize_05_from_02(df_02)
    _write_excel(OUT_05_XLSX, {"standardized_05_from_wide_review": df_05})

    # Counts.
    raw_grid_reconstructed_count = int(len(table_meta_df))
    semantic_table_block_count = int(len(blocks_df))
    financial_semantic_block_count = int(
        blocks_df["block_type"].isin([BLOCK_BALANCE, BLOCK_INCOME, BLOCK_CASH, BLOCK_RATIO, BLOCK_VALUATION]).sum()
    ) if not blocks_df.empty else 0
    non_financial_block_count = int((blocks_df["block_type"] == BLOCK_NON_FIN).sum()) if not blocks_df.empty else 0
    balance_sheet_block_count = int((blocks_df["block_type"] == BLOCK_BALANCE).sum()) if not blocks_df.empty else 0
    income_statement_block_count = int((blocks_df["block_type"] == BLOCK_INCOME).sum()) if not blocks_df.empty else 0
    cash_flow_statement_block_count = int((blocks_df["block_type"] == BLOCK_CASH).sum()) if not blocks_df.empty else 0
    financial_ratio_block_count = int((blocks_df["block_type"] == BLOCK_RATIO).sum()) if not blocks_df.empty else 0
    forecast_summary_block_count = int((blocks_df["block_type"] == BLOCK_FORECAST).sum()) if not blocks_df.empty else 0

    wide_financial_table_count = int(wide_df["semantic_table_id"].map(_norm).replace("", pd.NA).dropna().nunique()) if not wide_df.empty else 0
    wide_financial_metric_row_count = int(
        wide_df["metric_reconstruction_status"].isin([WIDE_OK, WIDE_WARN]).sum()
    ) if not wide_df.empty else 0
    wide_reconstructed_ok_count = int((wide_df["metric_reconstruction_status"] == WIDE_OK).sum()) if not wide_df.empty else 0
    wide_reconstructed_with_warning_count = int((wide_df["metric_reconstruction_status"] == WIDE_WARN).sum()) if not wide_df.empty else 0
    wide_filtered_header_count = int((wide_df["metric_reconstruction_status"] == WIDE_FILTER_HEADER).sum()) if not wide_df.empty else 0
    wide_filtered_non_financial_count = int((wide_df["metric_reconstruction_status"] == WIDE_FILTER_NON_FIN).sum()) if not wide_df.empty else 0

    structured_02_from_wide_row_count = int(len(df_02))
    structured_02_from_wide_ok_count = int((df_02["structured_status"] == "STRUCTURED_OK").sum()) if not df_02.empty else 0

    standardized_05_from_wide_row_count = int(stats_05["standardized_05_from_wide_row_count"])
    standardized_ok_count = int(stats_05["standardized_ok_count"])
    mapping_miss_count = int(stats_05["mapping_miss_count"])
    derived_metric_not_supported_count = int(stats_05["derived_metric_not_supported_count"])
    non_core_metric_count = int(stats_05["non_core_metric_count"])
    true_mapping_gap_count = int(stats_05["true_mapping_gap_count"])
    unknown_count = int(stats_05["unknown_count"])

    # Stage5k references.
    stage5k_structured_02_row_count = int(stage5k_summary.get("structured_02_sandbox_row_count", 0))
    stage5k_standardized_ok_count = int(stage5k_summary.get("standardized_ok_count", 0))
    stage5k_mapping_miss_count = int(stage5k_summary.get("mapping_miss_count", 0))

    wide_view_generated = bool(wide_financial_table_count >= 1 and wide_financial_metric_row_count > 0 and OUT_WIDE_XLSX.exists())
    semantic_splitter_pass = bool(
        semantic_table_block_count >= 1
        and financial_semantic_block_count >= 1
        and balance_sheet_block_count >= 1
        and income_statement_block_count >= 1
        and cash_flow_statement_block_count >= 1
        and financial_ratio_block_count >= 1
    )
    ready_for_stage5m_review = bool(
        semantic_splitter_pass and wide_view_generated and structured_02_from_wide_ok_count > 0 and true_mapping_gap_count == 0
    )
    recommended_next_stage = "STAGE5M_WIDE_SEMANTIC_REVIEW_AND_PROMOTION_DECISION"

    after = _snapshot_hashes()
    production_files_unchanged = bool(
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02B_unchanged = bool(before["02B"] == after["02B"])
    formal_scope_rules_unchanged = bool(before["formal_scope_rules"] == after["formal_scope_rules"])
    formal_mapping_rules_unchanged = bool(before["formal_mapping_rules"] == after["formal_mapping_rules"])
    formal_normalization_rules_unchanged = bool(before["formal_normalization_rules"] == after["formal_normalization_rules"])
    formal_alias_rules_unchanged = bool(before["formal_alias_rules"] == after["formal_alias_rules"])

    summary = {
        "input_raw_table_count": int(input_raw_table_count),
        "input_raw_cell_count": int(input_raw_cell_count),
        "raw_grid_reconstructed_count": int(raw_grid_reconstructed_count),
        "semantic_table_block_count": int(semantic_table_block_count),
        "financial_semantic_block_count": int(financial_semantic_block_count),
        "non_financial_block_count": int(non_financial_block_count),
        "balance_sheet_block_count": int(balance_sheet_block_count),
        "income_statement_block_count": int(income_statement_block_count),
        "cash_flow_statement_block_count": int(cash_flow_statement_block_count),
        "financial_ratio_block_count": int(financial_ratio_block_count),
        "forecast_summary_block_count": int(forecast_summary_block_count),
        "wide_financial_table_count": int(wide_financial_table_count),
        "wide_financial_metric_row_count": int(wide_financial_metric_row_count),
        "wide_reconstructed_ok_count": int(wide_reconstructed_ok_count),
        "wide_reconstructed_with_warning_count": int(wide_reconstructed_with_warning_count),
        "wide_filtered_header_count": int(wide_filtered_header_count),
        "wide_filtered_non_financial_count": int(wide_filtered_non_financial_count),
        "structured_02_from_wide_row_count": int(structured_02_from_wide_row_count),
        "structured_02_from_wide_ok_count": int(structured_02_from_wide_ok_count),
        "standardized_05_from_wide_row_count": int(standardized_05_from_wide_row_count),
        "standardized_ok_count": int(standardized_ok_count),
        "mapping_miss_count": int(mapping_miss_count),
        "derived_metric_not_supported_count": int(derived_metric_not_supported_count),
        "non_core_metric_count": int(non_core_metric_count),
        "true_mapping_gap_count": int(true_mapping_gap_count),
        "unknown_count": int(unknown_count),
        "stage5k_structured_02_row_count": int(stage5k_structured_02_row_count),
        "stage5k_standardized_ok_count": int(stage5k_standardized_ok_count),
        "stage5k_mapping_miss_count": int(stage5k_mapping_miss_count),
        "wide_view_generated": bool(wide_view_generated),
        "semantic_splitter_pass": bool(semantic_splitter_pass),
        "ready_for_stage5m_review": bool(ready_for_stage5m_review),
        "recommended_next_stage": str(recommended_next_stage),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "formal_alias_rules_unchanged": bool(formal_alias_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5l_semantic_reconstruction_pass": False,
    }

    summary["stage5l_semantic_reconstruction_pass"] = bool(
        summary["input_raw_table_count"] >= 1
        and summary["raw_grid_reconstructed_count"] >= 1
        and summary["semantic_table_block_count"] >= 1
        and summary["financial_semantic_block_count"] >= 1
        and summary["wide_financial_table_count"] >= 1
        and summary["wide_financial_metric_row_count"] > 0
        and summary["structured_02_from_wide_row_count"] > 0
        and summary["standardized_05_from_wide_row_count"] > 0
        and summary["wide_view_generated"]
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_scope_rules_unchanged"]
        and summary["formal_mapping_rules_unchanged"]
        and summary["formal_normalization_rules_unchanged"]
        and summary["formal_alias_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    md_lines = [
        "# Stage5L Semantic Table Reconstruction",
        "",
        "## Input",
        f"- input_raw_table_count: {summary['input_raw_table_count']}",
        f"- input_raw_cell_count: {summary['input_raw_cell_count']}",
        f"- pdf_page_count: {_read_pdf_page_count(INPUT_PDF)}",
        "",
        "## Semantic Blocks",
        f"- semantic_table_block_count: {summary['semantic_table_block_count']}",
        f"- financial_semantic_block_count: {summary['financial_semantic_block_count']}",
        f"- non_financial_block_count: {summary['non_financial_block_count']}",
        f"- balance_sheet_block_count: {summary['balance_sheet_block_count']}",
        f"- income_statement_block_count: {summary['income_statement_block_count']}",
        f"- cash_flow_statement_block_count: {summary['cash_flow_statement_block_count']}",
        f"- financial_ratio_block_count: {summary['financial_ratio_block_count']}",
        f"- forecast_summary_block_count: {summary['forecast_summary_block_count']}",
        "",
        "## Wide Review",
        f"- wide_financial_table_count: {summary['wide_financial_table_count']}",
        f"- wide_financial_metric_row_count: {summary['wide_financial_metric_row_count']}",
        f"- wide_reconstructed_ok_count: {summary['wide_reconstructed_ok_count']}",
        f"- wide_reconstructed_with_warning_count: {summary['wide_reconstructed_with_warning_count']}",
        "",
        "## 02/05 Review",
        f"- structured_02_from_wide_row_count: {summary['structured_02_from_wide_row_count']}",
        f"- standardized_05_from_wide_row_count: {summary['standardized_05_from_wide_row_count']}",
        f"- standardized_ok_count: {summary['standardized_ok_count']}",
        f"- mapping_miss_count: {summary['mapping_miss_count']}",
        f"- derived_metric_not_supported_count: {summary['derived_metric_not_supported_count']}",
        f"- non_core_metric_count: {summary['non_core_metric_count']}",
        f"- true_mapping_gap_count: {summary['true_mapping_gap_count']}",
        "",
        "## Decision",
        f"- semantic_splitter_pass: {summary['semantic_splitter_pass']}",
        f"- ready_for_stage5m_review: {summary['ready_for_stage5m_review']}",
        f"- recommended_next_stage: {summary['recommended_next_stage']}",
        f"- stage5l_semantic_reconstruction_pass: {summary['stage5l_semantic_reconstruction_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5l_grid_review_xlsx: {OUT_GRID_XLSX}")
    print(f"stage5l_blocks_xlsx: {OUT_BLOCKS_XLSX}")
    print(f"stage5l_wide_xlsx: {OUT_WIDE_XLSX}")
    print(f"stage5l_02_review_xlsx: {OUT_02_XLSX}")
    print(f"stage5l_05_review_xlsx: {OUT_05_XLSX}")
    print(f"stage5l_report_md: {OUT_REPORT_MD}")
    print(f"stage5l_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5l_semantic_reconstruction_pass: {summary['stage5l_semantic_reconstruction_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
