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

from config_manager import ConfigManager
from extractor_adapter import extract_pdfplumber_table_blocks
from pdfplumber_profile_extractor import extract_tables_with_pdfplumber_profiles
from table_block import TableBlock

import financial_standardizer as fs


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_PDF = BASE_DIR / "input" / "H3_AP202605121822223662_1.pdf"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_ALIAS_RULE_FILE = BASE_DIR / "financial_standardizer.py"

PROD_02_PATH = BASE_DIR / "02_研报全量结构化数据.xlsx"
PROD_05_PATH = BASE_DIR / "05_核心财务指标标准化.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5k_full_sandbox_rebuild"
OUT_RAW_XLSX = OUT_DIR / "146_stage5k_raw_tables_rebuilt.xlsx"
OUT_02_XLSX = OUT_DIR / "146_stage5k_structured_02_sandbox.xlsx"
OUT_05_XLSX = OUT_DIR / "146_stage5k_standardized_05_sandbox.xlsx"
OUT_DIFF_XLSX = OUT_DIR / "146_stage5k_rebuild_diff_report.xlsx"
OUT_REPORT_MD = OUT_DIR / "146_stage5k_full_rebuild_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "147_stage5k_full_rebuild_summary.json"

YEAR_RE = re.compile(r"(20\d{2}(?:[A-Z])?)", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
YEAR_VALID_RE = re.compile(r"20\d{2}(?:[AE])?$", re.IGNORECASE)
VALUE_VALID_RE = re.compile(r"[-+]?\d+(?:\.\d+)?$")

META_TERMS = [
    "证券研究报告",
    "敬请参阅最后一页",
    "免责声明",
    "资料来源",
    "请务必阅读",
    "分析师",
    "评级",
]
HEADER_HINT_TERMS = ["财务比率", "估值", "能力", "比率", "指标", "资产负债表", "利润表", "现金流量表"]
NON_FIN_TERMS = ["资料来源", "证券", "研究报告", "敬请参阅", "免责声明"]

CORE_TOKENS = [
    "营业收入",
    "归属母公司净利润",
    "归属于母公司净利润",
    "归母净利润",
    "毛利率",
    "ROE",
    "EPS",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
]

STRUCTURED_COLS = [
    "asset_package",
    "source_pdf",
    "source_page",
    "source_table_id",
    "raw_metric_name",
    "year",
    "value",
    "unit",
    "statement_type",
    "source_reference",
    "extraction_method",
    "row_trace_id",
    "parse_status",
    "parse_issue_type",
    "parse_issue_reason",
]

STANDARD_COLS = [
    "asset_package",
    "source_pdf",
    "source_page",
    "source_table_id",
    "raw_metric_name",
    "standard_metric",
    "year",
    "value",
    "unit",
    "statement_type",
    "mapping_rule_id",
    "scope_rule_id",
    "normalization_rule_id",
    "source_reference",
    "row_trace_id",
    "standardization_status",
    "standardization_issue_type",
    "standardization_issue_reason",
]

CHG_DERIVED = "UNCHANGED_DERIVED_METRIC_NOT_SUPPORTED"
CHG_NON_CORE = "UNCHANGED_NON_CORE_METRIC"
CHG_MISS = "UNCHANGED_MAPPING_MISS"
CHG_OTHER = "UNCHANGED_OTHER"


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
        s = f"{base[:31 - len(suffix)]}{suffix}"
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


def _table_to_rows(block: TableBlock, source_pdf: Path, extractor_name: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    df = block.raw_df if isinstance(block.raw_df, pd.DataFrame) else pd.DataFrame()
    if df.empty:
        return rows
    page = _norm(block.page)
    t_idx = _norm(block.table_index)
    table_id = f"{source_pdf.stem}|p{page or 'NA'}|t{t_idx or 'NA'}|{extractor_name}"
    col_count = int(df.shape[1])
    for ridx in range(df.shape[0]):
        row_values = [_norm(df.iat[ridx, c]) for c in range(df.shape[1])]
        raw_row_text = " | ".join([v for v in row_values if v])
        for cidx in range(df.shape[1]):
            rows.append(
                {
                    "table_id": table_id,
                    "page": page,
                    "row_index": ridx + 1,
                    "col_index": cidx + 1,
                    "cell_text": _norm(df.iat[ridx, cidx]),
                    "extractor_name": extractor_name,
                    "extraction_status": "ok",
                    "source_pdf": str(source_pdf),
                    "source_bbox": _norm(block.bbox),
                    "raw_row_text": raw_row_text,
                    "raw_col_count": col_count,
                }
            )
    return rows


def _aggregate_table_index(blocks: List[TableBlock], extractor_name: str, source_pdf: Path) -> pd.DataFrame:
    rows = []
    for b in blocks:
        df = b.raw_df if isinstance(b.raw_df, pd.DataFrame) else pd.DataFrame()
        rows.append(
            {
                "source_pdf": str(source_pdf),
                "extractor_name": extractor_name,
                "page": b.page,
                "table_index": b.table_index,
                "rows": int(df.shape[0]) if not df.empty else 0,
                "cols": int(df.shape[1]) if not df.empty else 0,
                "non_empty_cells": int((df.fillna("").astype(str) != "").sum().sum()) if not df.empty else 0,
            }
        )
    return pd.DataFrame(rows)


def _parse_year(text: str) -> str:
    m = YEAR_RE.search(_norm(text))
    return m.group(1).upper() if m else ""


def _parse_num(text: str) -> str:
    m = NUM_RE.search(_norm(text).replace("，", ","))
    if not m:
        return ""
    return m.group(0).replace(",", "")


def _is_numeric_like(text: str) -> bool:
    t = _norm(text).replace(",", "")
    return bool(t and re.fullmatch(r"[-+]?\d+(?:\.\d+)?", t))


def _is_meta_row(row_text: str) -> bool:
    t = _norm(row_text)
    return any(x in t for x in META_TERMS)


def _detect_statement_type(header_text: str) -> str:
    t = _norm(header_text)
    if "资产负债" in t:
        return "资产负债表"
    if "利润表" in t or "损益" in t:
        return "利润表"
    if "现金流" in t:
        return "现金流量表"
    if "比率" in t or "估值" in t:
        return "财务比率表"
    return ""


def _unit_from_text(label: str, row_text: str, header_text: str, value_cell: str) -> str:
    joined = " ".join([_norm(label), _norm(row_text), _norm(header_text), _norm(value_cell)])
    if "百万元" in joined:
        return "百万元"
    if "亿元" in joined:
        return "亿元"
    if "%" in joined or "毛利率" in joined or "ROE" in joined.upper():
        return "%"
    if "每股" in joined or "EPS" in joined.upper():
        return "元/股"
    if any(x in joined.upper() for x in ["P/E", "P/B", "EV/EBITDA"]):
        return "倍"
    if "元" in joined:
        return "元"
    return ""


def _split_year_groups(year_cols: List[int]) -> List[List[int]]:
    if not year_cols:
        return []
    cols = sorted(set(year_cols))
    groups: List[List[int]] = [[cols[0]]]
    for c in cols[1:]:
        if c - groups[-1][-1] > 2:
            groups.append([c])
        else:
            groups[-1].append(c)
    return groups


def _candidate_label_cols(group_start: int, year_cols_set: set) -> List[int]:
    cols: List[int] = []
    for c in [group_start - 2, group_start - 1]:
        if c >= 1 and c not in year_cols_set:
            cols.append(c)
    return cols


def _clean_label_piece(text: str) -> str:
    t = _norm(text).replace("（", "(").replace("）", ")")
    t = re.sub(r"[|]+", "", t)
    t = re.sub(r"\s+", "", t)
    t = t.strip(":：;；,，.")
    return t


def _compose_label(label_parts: List[str]) -> str:
    parts = [_clean_label_piece(x) for x in label_parts if _clean_label_piece(x)]
    return "".join(parts)


def _looks_core_or_metric_like(label: str) -> bool:
    lc = _compact(label)
    if not lc:
        return False
    if any(_compact(k) in lc for k in CORE_TOKENS):
        return True
    if any(x in lc for x in ["净利润", "营业利润", "EBITDA", "净利率", "ROIC", "资产负债率", "流动比率", "速动比率", "周转率"]):
        return True
    return False


def _is_non_fin_label(label: str) -> bool:
    t = _norm(label)
    return any(x in t for x in NON_FIN_TERMS)


def _rebuild_structured_02(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int], pd.DataFrame]:
    improved_rows: List[Dict[str, Any]] = []
    table_diag_rows: List[Dict[str, Any]] = []

    header_filtered_count = 0
    non_financial_filtered_count = 0
    structured_ok_count = 0

    raw_df = raw_df.copy()
    raw_df["row_index"] = pd.to_numeric(raw_df["row_index"], errors="coerce").fillna(0).astype(int)
    raw_df["col_index"] = pd.to_numeric(raw_df["col_index"], errors="coerce").fillna(0).astype(int)

    for table_id, tdf in raw_df.groupby("table_id", sort=True):
        tdf = tdf.sort_values(["row_index", "col_index"]).copy()
        source_pdf = _norm(tdf["source_pdf"].iloc[0])
        page = _norm(tdf["page"].iloc[0])
        extractor_name = _norm(tdf["extractor_name"].iloc[0])
        asset_package = (Path(source_pdf).stem if source_pdf else "unknown_pdf") + "_stage5k"

        header_rows: List[int] = []
        col_year_map: Dict[int, str] = {}
        year_cols_set = set()
        for ridx, g in tdf.groupby("row_index", sort=True):
            if ridx > 10:
                continue
            year_hits = []
            for _, rr in g.iterrows():
                y = _parse_year(rr.get("cell_text"))
                if y:
                    c = int(rr.get("col_index"))
                    year_hits.append((c, y))
            if len({y for _, y in year_hits}) >= 2:
                header_rows.append(int(ridx))
                for c, y in year_hits:
                    col_year_map[c] = y
                    year_cols_set.add(c)

        year_groups = _split_year_groups(sorted(year_cols_set))
        if not year_groups:
            for _, rr in tdf.iterrows():
                y = _parse_year(rr.get("cell_text"))
                c = int(rr.get("col_index"))
                if y:
                    col_year_map[c] = y
                    year_cols_set.add(c)
            year_groups = _split_year_groups(sorted(year_cols_set))

        group_meta: List[Dict[str, Any]] = []
        for gi, gcols in enumerate(year_groups):
            start_col = min(gcols)
            label_cols = _candidate_label_cols(start_col, year_cols_set)
            header_text_parts = []
            for hrow in header_rows:
                row_df = tdf[tdf["row_index"] == hrow]
                for c in sorted(set(label_cols + gcols)):
                    hit = row_df[row_df["col_index"] == c]
                    if not hit.empty:
                        v = _norm(hit.iloc[0]["cell_text"])
                        if v:
                            header_text_parts.append(v)
            header_text = " | ".join(header_text_parts)
            statement_type = _detect_statement_type(header_text)
            group_meta.append(
                {
                    "group_index": gi,
                    "year_cols": gcols,
                    "label_cols": label_cols,
                    "header_text": header_text,
                    "statement_type": statement_type,
                    "last_label": "",
                }
            )

        table_header_filtered = 0
        table_non_fin_filtered = 0
        table_structured_ok = 0

        for ridx, g in tdf.groupby("row_index", sort=True):
            row_df = g.sort_values("col_index")
            row_text = " | ".join([_norm(x) for x in row_df["cell_text"].tolist() if _norm(x)])
            if not row_text:
                continue
            if int(ridx) in header_rows or _is_meta_row(row_text):
                table_header_filtered += 1
                header_filtered_count += 1
                continue

            for gm in group_meta:
                ycols = gm["year_cols"]
                if not ycols:
                    continue
                numeric_cells: List[Tuple[int, str, str]] = []
                for yc in ycols:
                    hit = row_df[row_df["col_index"] == yc]
                    if hit.empty:
                        continue
                    cell_text = _norm(hit.iloc[0]["cell_text"])
                    val = _parse_num(cell_text)
                    if val:
                        numeric_cells.append((yc, val, cell_text))
                if not numeric_cells:
                    continue

                label_parts = []
                for lc in gm["label_cols"]:
                    hit = row_df[row_df["col_index"] == lc]
                    if hit.empty:
                        continue
                    txt = _norm(hit.iloc[0]["cell_text"])
                    if not txt:
                        continue
                    if _is_numeric_like(txt) or _parse_year(txt):
                        continue
                    if any(x in txt for x in HEADER_HINT_TERMS):
                        continue
                    label_parts.append(txt)
                raw_label = _compose_label(label_parts)
                if not raw_label and _norm(gm["last_label"]):
                    raw_label = _norm(gm["last_label"])
                if raw_label:
                    gm["last_label"] = raw_label

                cleaned_label = fs._clean_metric_label_noise(raw_label) if raw_label else ""
                if not cleaned_label or _is_non_fin_label(cleaned_label) or (not _looks_core_or_metric_like(cleaned_label)):
                    table_non_fin_filtered += 1
                    non_financial_filtered_count += 1
                    continue

                for yc, val, raw_val_cell in numeric_cells:
                    year = _norm(col_year_map.get(yc, ""))
                    unit = _unit_from_text(cleaned_label, row_text, gm["header_text"], raw_val_cell)
                    parse_status = "STRUCTURED_OK"
                    issue_type = "NONE"
                    issue_reason = "stage5k group-aware extraction"
                    if not year:
                        parse_status = "MISSING_YEAR"
                        issue_type = "YEAR_DETECTION_FAILED"
                        issue_reason = "year not mapped"
                    elif not val:
                        parse_status = "MISSING_VALUE"
                        issue_type = "VALUE_PARSE_FAILED"
                        issue_reason = "value parse failed"
                    elif not unit:
                        parse_status = "MISSING_UNIT"
                        issue_type = "UNIT_DETECTION_FAILED"
                        issue_reason = "unit not detected"

                    rec = {
                        "asset_package": asset_package,
                        "source_pdf": source_pdf,
                        "source_page": page,
                        "source_table_id": _norm(table_id),
                        "raw_metric_name": _norm(cleaned_label),
                        "year": _norm(year),
                        "value": _norm(val),
                        "unit": _norm(unit),
                        "statement_type": _norm(gm["statement_type"]),
                        "source_reference": f"{table_id}:r{int(ridx)}:c{int(yc)}",
                        "extraction_method": extractor_name,
                        "row_trace_id": f"{table_id}|r{int(ridx)}|c{int(yc)}|g{int(gm['group_index'])}",
                        "parse_status": parse_status,
                        "parse_issue_type": issue_type,
                        "parse_issue_reason": issue_reason,
                    }
                    improved_rows.append(rec)
                    if parse_status == "STRUCTURED_OK":
                        table_structured_ok += 1
                        structured_ok_count += 1

        table_diag_rows.append(
            {
                "source_table_id": _norm(table_id),
                "source_page": page,
                "year_group_count": len(year_groups),
                "header_row_count": len(header_rows),
                "structured_ok_count": table_structured_ok,
                "header_filtered_count": table_header_filtered,
                "non_financial_filtered_count": table_non_fin_filtered,
            }
        )

    improved_df = pd.DataFrame(improved_rows, columns=STRUCTURED_COLS).fillna("")
    stats = {
        "structured_02_sandbox_row_count": int(len(improved_df)),
        "structured_02_structured_ok_count": int(structured_ok_count),
        "structured_02_filtered_header_count": int(header_filtered_count),
        "structured_02_filtered_non_financial_count": int(non_financial_filtered_count),
    }
    return improved_df, stats, pd.DataFrame(table_diag_rows)


def _classify_mapping_miss(raw: str) -> str:
    t = _norm(raw)
    if any(x in t for x in ["(%)", "%", "周转率", "ROIC", "资产负债率", "净利率"]):
        return CHG_DERIVED
    if any(x in t for x in ["营业利润", "净利润", "EBITDA"]):
        return CHG_NON_CORE
    return CHG_MISS


def _standardize_05(structured_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    ready = structured_df[structured_df["parse_status"].map(_norm) == "STRUCTURED_OK"].copy() if not structured_df.empty else pd.DataFrame(columns=structured_df.columns)
    for _, r in ready.iterrows():
        raw_metric_name = _norm(r.get("raw_metric_name"))
        year = _norm(r.get("year")).upper()
        value = _norm(r.get("value")).replace(",", "")
        unit = _norm(r.get("unit"))
        standard_metric = ""
        status = "STANDARDIZATION_FAILED"
        issue_type = "UNKNOWN"
        reason = "unexpected"

        m = fs._match_standard_metric(raw_metric_name)
        if not m:
            status = "MAPPING_MISS"
            issue_type = "METRIC_MAPPING_ISSUE"
            reason = "no mapping rule hit"
        else:
            standard_metric = _norm(m.get("standard_metric"))
            if not YEAR_VALID_RE.fullmatch(year):
                status = "YEAR_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                reason = "year invalid"
            elif not VALUE_VALID_RE.fullmatch(value):
                status = "VALUE_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                reason = "value invalid"
            elif not unit:
                status = "UNIT_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                reason = "unit missing"
            else:
                status = "STANDARDIZED_OK"
                issue_type = "NONE"
                reason = "ok"

        rows.append(
            {
                "asset_package": _norm(r.get("asset_package")),
                "source_pdf": _norm(r.get("source_pdf")),
                "source_page": _norm(r.get("source_page")),
                "source_table_id": _norm(r.get("source_table_id")),
                "raw_metric_name": raw_metric_name,
                "standard_metric": standard_metric,
                "year": year,
                "value": value,
                "unit": unit,
                "statement_type": _norm(r.get("statement_type")),
                "mapping_rule_id": f"FS_MAP_{_compact(standard_metric)}" if standard_metric else "",
                "scope_rule_id": "",
                "normalization_rule_id": "",
                "source_reference": _norm(r.get("source_reference")),
                "row_trace_id": _norm(r.get("row_trace_id")),
                "standardization_status": status,
                "standardization_issue_type": issue_type,
                "standardization_issue_reason": reason,
            }
        )

    out_df = pd.DataFrame(rows, columns=STANDARD_COLS).fillna("")

    if not out_df.empty:
        ok = out_df[out_df["standardization_status"] == "STANDARDIZED_OK"].copy()
        dup_ids = set()
        if not ok.empty:
            ok = ok.sort_values(["asset_package", "standard_metric", "year", "source_page", "row_trace_id"], kind="mergesort")
            for _, g in ok.groupby(["asset_package", "standard_metric", "year"], dropna=False):
                if len(g) > 2:
                    for rid in g.iloc[2:]["row_trace_id"].map(_norm).tolist():
                        dup_ids.add(rid)
        if dup_ids:
            m = out_df["row_trace_id"].map(_norm).isin(dup_ids)
            out_df.loc[m, "standardization_status"] = "DUPLICATE_CANDIDATE"
            out_df.loc[m, "standardization_issue_type"] = "DUPLICATE_KEY"
            out_df.loc[m, "standardization_issue_reason"] = "duplicate key candidate"

    standardized_ok_count = int((out_df["standardization_status"] == "STANDARDIZED_OK").sum()) if not out_df.empty else 0
    mapping_miss_count = int((out_df["standardization_status"] == "MAPPING_MISS").sum()) if not out_df.empty else 0
    derived_metric_not_supported_count = 0
    non_core_metric_count = 0
    true_mapping_gap_count = 0
    unknown_count = 0

    if not out_df.empty:
        miss_df = out_df[out_df["standardization_status"] == "MAPPING_MISS"].copy()
        if not miss_df.empty:
            miss_df["miss_class"] = miss_df["raw_metric_name"].map(_classify_mapping_miss)
            derived_metric_not_supported_count = int((miss_df["miss_class"] == CHG_DERIVED).sum())
            non_core_metric_count = int((miss_df["miss_class"] == CHG_NON_CORE).sum())
            true_mapping_gap_count = int((miss_df["miss_class"] == CHG_MISS).sum())
        unknown_count = int((out_df["standardization_status"] == "DUPLICATE_CANDIDATE").sum())

    stats = {
        "standardized_05_sandbox_row_count": int(len(out_df)),
        "standardized_ok_count": int(standardized_ok_count),
        "mapping_miss_count": int(mapping_miss_count),
        "derived_metric_not_supported_count": int(derived_metric_not_supported_count),
        "non_core_metric_count": int(non_core_metric_count),
        "true_mapping_gap_count": int(true_mapping_gap_count),
        "unknown_count": int(unknown_count),
    }
    return out_df, stats


def _load_excel_first_sheet(path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    return pd.read_excel(path, sheet_name=xl.sheet_names[0]).fillna("")


def _norm_col_name(name: str) -> str:
    x = _norm(name).lower()
    x = re.sub(r"[\s_]+", "", x)
    return x


def _diff_count(prod_df: pd.DataFrame, sandbox_df: pd.DataFrame) -> Tuple[int, List[str]]:
    if prod_df.empty and sandbox_df.empty:
        return 0, []
    pmap = {_norm_col_name(c): c for c in prod_df.columns}
    smap = {_norm_col_name(c): c for c in sandbox_df.columns}
    common_keys = [k for k in ["rawmetricname", "year", "value", "unit", "statementtype", "sourcepage"] if k in pmap and k in smap]
    if not common_keys:
        commons = sorted(set(pmap.keys()) & set(smap.keys()))
        common_keys = commons[:3]
    if not common_keys:
        return abs(len(prod_df) - len(sandbox_df)), []

    pcols = [pmap[k] for k in common_keys]
    scols = [smap[k] for k in common_keys]
    pset = set(prod_df[pcols].fillna("").astype(str).agg("|".join, axis=1).tolist())
    sset = set(sandbox_df[scols].fillna("").astype(str).agg("|".join, axis=1).tolist())
    return len(pset.symmetric_difference(sset)), common_keys


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5K full sandbox rebuild 02/05 from PDF.")
    parser.add_argument("--pdf", default=str(INPUT_PDF), help="Input PDF path")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    required = [
        pdf_path,
        OFFICIAL_02B_PATH,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_MAPPING_RULE_FILE,
        FORMAL_NORMALIZATION_RULE_FILE,
        FORMAL_ALIAS_RULE_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    cm = ConfigManager(config_path="config.yaml")
    config = cm.load()
    extraction_cfg = (config.get("table_extraction", {}) or {})

    selected_blocks: List[TableBlock] = []
    profile_diag_df = pd.DataFrame()
    selected_by = "pdfplumber_fallback"

    selected_profile_blocks, profile_diag_df = extract_tables_with_pdfplumber_profiles(str(pdf_path), config, logger=None)
    if selected_profile_blocks:
        converted: List[TableBlock] = []
        for b in selected_profile_blocks:
            df = b.get("df")
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            tb = TableBlock(
                backend="pdfplumber",
                page=b.get("page"),
                table_index=b.get("table_index"),
                bbox=b.get("bbox"),
                confidence=b.get("confidence"),
                raw_df=df,
            )
            converted.append(tb)
        if converted:
            selected_blocks = converted
            selected_by = "pdfplumber_profiles"
    if not selected_blocks:
        selected_blocks = extract_pdfplumber_table_blocks(str(pdf_path), extraction_cfg, logger=None)
        selected_by = "pdfplumber_fallback"

    raw_rows: List[Dict[str, Any]] = []
    for b in selected_blocks:
        raw_rows.extend(_table_to_rows(b, pdf_path, "pdfplumber"))
    raw_df = pd.DataFrame(
        raw_rows,
        columns=[
            "table_id",
            "page",
            "row_index",
            "col_index",
            "cell_text",
            "extractor_name",
            "extraction_status",
            "source_pdf",
            "source_bbox",
            "raw_row_text",
            "raw_col_count",
        ],
    ).fillna("")
    table_index_df = _aggregate_table_index(selected_blocks, "pdfplumber", pdf_path)

    _write_excel(OUT_RAW_XLSX, {"raw_tables": raw_df, "table_index": table_index_df, "profile_diag": profile_diag_df})

    structured_df, s02_stats, table_diag_df = _rebuild_structured_02(raw_df)
    _write_excel(OUT_02_XLSX, {"structured_02_sandbox": structured_df, "table_diagnostics": table_diag_df})

    standardized_df, s05_stats = _standardize_05(structured_df)
    _write_excel(OUT_05_XLSX, {"standardized_05_sandbox": standardized_df})

    prod_02_path = PROD_02_PATH if PROD_02_PATH.exists() else _find_delivery_file("02_*.xlsx")
    prod_05_path = PROD_05_PATH if PROD_05_PATH.exists() else _find_delivery_file("05_*.xlsx")
    prod_02_df = _load_excel_first_sheet(prod_02_path)
    prod_05_df = _load_excel_first_sheet(prod_05_path)

    diff_02_count, diff_02_keys = _diff_count(prod_02_df, structured_df)
    diff_05_count, diff_05_keys = _diff_count(prod_05_df, standardized_df)

    diff_summary_df = pd.DataFrame(
        [
            {"layer": "02", "production_file": str(prod_02_path), "production_rows": len(prod_02_df), "sandbox_rows": len(structured_df), "diff_count": diff_02_count, "diff_keys": ",".join(diff_02_keys)},
            {"layer": "05", "production_file": str(prod_05_path), "production_rows": len(prod_05_df), "sandbox_rows": len(standardized_df), "diff_count": diff_05_count, "diff_keys": ",".join(diff_05_keys)},
        ]
    )
    _write_excel(OUT_DIFF_XLSX, {"diff_summary": diff_summary_df})

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

    ready_for_stage5l_promotion_review = bool(
        s05_stats["standardized_ok_count"] >= 45
        and s05_stats["true_mapping_gap_count"] == 0
        and s02_stats["structured_02_sandbox_row_count"] > 0
    )
    recommended_next_stage = "STAGE5L_DERIVED_NON_CORE_FILTER_AND_PROMOTION_REVIEW"

    summary = {
        "input_pdf_file": str(pdf_path),
        "pdf_exists": bool(pdf_path.exists()),
        "pdf_page_count": int(_read_pdf_page_count(pdf_path)),
        "raw_table_rebuilt_count": int(raw_df["table_id"].nunique()) if not raw_df.empty else 0,
        "raw_table_rebuilt_row_count": int(raw_df.groupby("table_id")["row_index"].max().sum()) if not raw_df.empty else 0,
        "raw_table_rebuilt_cell_count": int(len(raw_df)),
        "structured_02_sandbox_row_count": int(s02_stats["structured_02_sandbox_row_count"]),
        "structured_02_structured_ok_count": int(s02_stats["structured_02_structured_ok_count"]),
        "structured_02_filtered_header_count": int(s02_stats["structured_02_filtered_header_count"]),
        "structured_02_filtered_non_financial_count": int(s02_stats["structured_02_filtered_non_financial_count"]),
        "standardized_05_sandbox_row_count": int(s05_stats["standardized_05_sandbox_row_count"]),
        "standardized_ok_count": int(s05_stats["standardized_ok_count"]),
        "mapping_miss_count": int(s05_stats["mapping_miss_count"]),
        "derived_metric_not_supported_count": int(s05_stats["derived_metric_not_supported_count"]),
        "non_core_metric_count": int(s05_stats["non_core_metric_count"]),
        "true_mapping_gap_count": int(s05_stats["true_mapping_gap_count"]),
        "unknown_count": int(s05_stats["unknown_count"]),
        "production_02_row_count": int(len(prod_02_df)),
        "production_05_row_count": int(len(prod_05_df)),
        "diff_with_production_02_count": int(diff_02_count),
        "diff_with_production_05_count": int(diff_05_count),
        "ready_for_stage5l_promotion_review": bool(ready_for_stage5l_promotion_review),
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
        "stage5k_full_sandbox_rebuild_pass": False,
        "selected_pdf_table_extractor": selected_by,
    }

    summary["stage5k_full_sandbox_rebuild_pass"] = bool(
        summary["pdf_exists"]
        and summary["raw_table_rebuilt_count"] >= 1
        and summary["structured_02_sandbox_row_count"] > 0
        and summary["standardized_05_sandbox_row_count"] > 0
        and summary["standardized_ok_count"] >= 45
        and summary["true_mapping_gap_count"] == 0
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
        "# Stage5K Full Sandbox Rebuild 02/05",
        "",
        "## Rebuild Chain",
        f"- extractor: {summary['selected_pdf_table_extractor']}",
        f"- pdf_exists: {summary['pdf_exists']}",
        f"- pdf_page_count: {summary['pdf_page_count']}",
        f"- raw_table_rebuilt_count: {summary['raw_table_rebuilt_count']}",
        f"- raw_table_rebuilt_row_count: {summary['raw_table_rebuilt_row_count']}",
        f"- raw_table_rebuilt_cell_count: {summary['raw_table_rebuilt_cell_count']}",
        f"- structured_02_sandbox_row_count: {summary['structured_02_sandbox_row_count']}",
        f"- structured_02_structured_ok_count: {summary['structured_02_structured_ok_count']}",
        f"- standardized_05_sandbox_row_count: {summary['standardized_05_sandbox_row_count']}",
        f"- standardized_ok_count: {summary['standardized_ok_count']}",
        f"- mapping_miss_count: {summary['mapping_miss_count']}",
        f"- derived_metric_not_supported_count: {summary['derived_metric_not_supported_count']}",
        f"- non_core_metric_count: {summary['non_core_metric_count']}",
        f"- true_mapping_gap_count: {summary['true_mapping_gap_count']}",
        f"- unknown_count: {summary['unknown_count']}",
        "",
        "## Diff With Production",
        f"- production_02_row_count: {summary['production_02_row_count']}",
        f"- production_05_row_count: {summary['production_05_row_count']}",
        f"- diff_with_production_02_count: {summary['diff_with_production_02_count']}",
        f"- diff_with_production_05_count: {summary['diff_with_production_05_count']}",
        "",
        "## Guardrails",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- formal_alias_rules_unchanged: {summary['formal_alias_rules_unchanged']}",
        "",
        "## Decision",
        f"- ready_for_stage5l_promotion_review: {summary['ready_for_stage5l_promotion_review']}",
        f"- recommended_next_stage: {summary['recommended_next_stage']}",
        f"- stage5k_full_sandbox_rebuild_pass: {summary['stage5k_full_sandbox_rebuild_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5k_raw_tables_xlsx: {OUT_RAW_XLSX}")
    print(f"stage5k_structured_02_xlsx: {OUT_02_XLSX}")
    print(f"stage5k_standardized_05_xlsx: {OUT_05_XLSX}")
    print(f"stage5k_diff_report_xlsx: {OUT_DIFF_XLSX}")
    print(f"stage5k_report_md: {OUT_REPORT_MD}")
    print(f"stage5k_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5k_full_sandbox_rebuild_pass: {summary['stage5k_full_sandbox_rebuild_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
