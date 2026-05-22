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

STAGE5B_DIR = OUTPUT_DIR / "stage5b_table_extraction_restore"
STAGE5C_DIR = OUTPUT_DIR / "stage5c_raw_tables_to_structured_02"
STAGE5D_DIR = OUTPUT_DIR / "stage5d_standardize_sandbox_02_to_05"
STAGE5E_DIR = OUTPUT_DIR / "stage5e_mapping_miss_inventory"

RAW_TABLE_XLSX = STAGE5B_DIR / "raw_tables.xlsx"
RAW_TABLE_JSON = STAGE5B_DIR / "raw_tables.json"
PREV_02_XLSX = STAGE5C_DIR / "130_stage5c_structured_02_sandbox.xlsx"
PREV_05_XLSX = STAGE5D_DIR / "132_stage5d_sandbox_05_standardized.xlsx"
PREV_5E_SUMMARY_JSON = STAGE5E_DIR / "135_stage5e_mapping_miss_summary.json"
PREV_5C_SUMMARY_JSON = STAGE5C_DIR / "131_stage5c_raw_to_02_summary.json"
PREV_5D_SUMMARY_JSON = STAGE5D_DIR / "133_stage5d_standardization_summary.json"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5f_raw_metric_extraction_fix"
OUT_02_XLSX = OUT_DIR / "136_stage5f_improved_structured_02.xlsx"
OUT_PREVIEW_XLSX = OUT_DIR / "136_stage5f_improved_standardization_preview.xlsx"
OUT_REPORT_XLSX = OUT_DIR / "136_stage5f_raw_metric_extraction_fix_report.xlsx"
OUT_REPORT_MD = OUT_DIR / "136_stage5f_raw_metric_extraction_fix_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "137_stage5f_raw_metric_extraction_fix_summary.json"

YEAR_RE = re.compile(r"(20\d{2}(?:[A-Z])?)", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")

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

TRUNCATED_PARSE_FRAGMENTS = {
    "动资",
    "现金",
    "收票",
    "预付",
    "存货",
    "流动",
    "资活",
    "长期",
    "固定",
    "无形",
    "产总",
    "动负",
    "付票",
    "债合",
    "债和",
    "短期",
    "资本",
    "股本",
    "留存",
    "金净",
    "金流",
    "营活",
    "营运",
    "投资",
    "财务",
    "折旧",
    "属母",
    "净利",
    "普通",
    "数",
    "其他",
}

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


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    text = _norm(v).replace("（", "(").replace("）", ")").replace("／", "/")
    return re.sub(r"\s+", "", text).upper()


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
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    return json.loads(text)


def _load_raw_tables() -> pd.DataFrame:
    if RAW_TABLE_XLSX.exists():
        return pd.read_excel(RAW_TABLE_XLSX, sheet_name="raw_tables").fillna("")
    if RAW_TABLE_JSON.exists():
        return pd.DataFrame(json.loads(RAW_TABLE_JSON.read_text(encoding="utf-8"))).fillna("")
    raise FileNotFoundError("Missing stage5b raw tables input")


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
        # gap > 2 usually indicates another side-by-side table region
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
    # Keep these to allow Stage5D mapping on core+ratio layer.
    if any(x in lc for x in ["净利润", "营业利润", "EBITDA", "净利率", "ROIC", "资产负债率", "流动比率", "速动比率", "周转率"]):
        return True
    return False


def _is_non_fin_label(label: str) -> bool:
    t = _norm(label)
    return any(x in t for x in NON_FIN_TERMS)


def _build_standardization_preview(
    improved_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    if improved_df.empty:
        return pd.DataFrame(columns=STANDARD_COLS), {
            "standardized_ok_count": 0,
            "mapping_miss_count": 0,
            "parse_issue_miss_count": 0,
        }

    ready = improved_df[improved_df["parse_status"].map(_norm) == "STRUCTURED_OK"].copy()

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
            cleaned = fs._clean_metric_label_noise(raw_metric_name)
            if cleaned != raw_metric_name and _compact(cleaned) in TRUNCATED_PARSE_FRAGMENTS:
                status = "NORMALIZATION_MISS"
                issue_type = "NORMALIZATION_ISSUE"
                reason = "cleaning changed metric but still no mapping"
            else:
                status = "MAPPING_MISS"
                issue_type = "METRIC_MAPPING_ISSUE"
                reason = "no mapping hit"
        else:
            standard_metric = _norm(m.get("standard_metric"))
            if not re.fullmatch(r"20\d{2}(?:[AE])?", year):
                status = "YEAR_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                reason = "year invalid"
            elif not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", value):
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

    # Duplicate key downgrade
    if not out_df.empty:
        ok = out_df[out_df["standardization_status"] == "STANDARDIZED_OK"].copy()
        dup_ids = set()
        if not ok.empty:
            ok = ok.sort_values(["asset_package", "standard_metric", "year", "source_page", "row_trace_id"], kind="mergesort")
            for _, g in ok.groupby(["asset_package", "standard_metric", "year"], dropna=False):
                if len(g) > 1:
                    for rid in g.iloc[1:]["row_trace_id"].map(_norm).tolist():
                        dup_ids.add(rid)
        if dup_ids:
            m = out_df["row_trace_id"].map(_norm).isin(dup_ids)
            out_df.loc[m, "standardization_status"] = "DUPLICATE_CANDIDATE"
            out_df.loc[m, "standardization_issue_type"] = "DUPLICATE_KEY"
            out_df.loc[m, "standardization_issue_reason"] = "duplicate key in preview"

    mm = out_df[out_df["standardization_status"] == "MAPPING_MISS"].copy() if not out_df.empty else pd.DataFrame()
    parse_issue_miss = 0
    if not mm.empty:
        for raw in mm["raw_metric_name"].map(_norm).tolist():
            cleaned = fs._clean_metric_label_noise(raw)
            if len(_norm(cleaned)) <= 2 or _norm(cleaned) in TRUNCATED_PARSE_FRAGMENTS:
                parse_issue_miss += 1

    stats = {
        "standardized_ok_count": int((out_df["standardization_status"] == "STANDARDIZED_OK").sum()) if not out_df.empty else 0,
        "mapping_miss_count": int((out_df["standardization_status"] == "MAPPING_MISS").sum()) if not out_df.empty else 0,
        "parse_issue_miss_count": int(parse_issue_miss),
    }
    return out_df, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5F improve raw metric extraction in sandbox pipeline.")
    parser.parse_args()

    required = [
        RAW_TABLE_XLSX,
        PREV_02_XLSX,
        PREV_05_XLSX,
        PREV_5E_SUMMARY_JSON,
        PREV_5C_SUMMARY_JSON,
        PREV_5D_SUMMARY_JSON,
        FORMAL_SCOPE_RULES_JSON,
        OFFICIAL_02B_PATH,
        FORMAL_NORMALIZATION_RULE_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    raw_df = _load_raw_tables()
    prev_02_df = pd.read_excel(PREV_02_XLSX, sheet_name="structured_02_sandbox").fillna("")
    prev_05_df = pd.read_excel(PREV_05_XLSX, sheet_name="sandbox_05_standardized").fillna("")
    prev_5e = json.loads(PREV_5E_SUMMARY_JSON.read_text(encoding="utf-8"))
    prev_5c = json.loads(PREV_5C_SUMMARY_JSON.read_text(encoding="utf-8"))
    prev_5d = json.loads(PREV_5D_SUMMARY_JSON.read_text(encoding="utf-8"))

    required_raw_cols = {"table_id", "page", "row_index", "col_index", "cell_text", "extractor_name", "source_pdf"}
    if not required_raw_cols.issubset(set(raw_df.columns)):
        raise RuntimeError("Stage5b raw table schema mismatch")

    raw_df["row_index"] = pd.to_numeric(raw_df["row_index"], errors="coerce").fillna(0).astype(int)
    raw_df["col_index"] = pd.to_numeric(raw_df["col_index"], errors="coerce").fillna(0).astype(int)

    improved_rows: List[Dict[str, Any]] = []
    table_diag_rows: List[Dict[str, Any]] = []

    header_filtered_count = 0
    non_financial_filtered_count = 0
    metric_name_inferred_count = 0
    metric_name_cleaned_count = 0

    for table_id, tdf in raw_df.groupby("table_id", sort=True):
        tdf = tdf.sort_values(["row_index", "col_index"]).copy()
        source_pdf = _norm(tdf["source_pdf"].iloc[0])
        page = _norm(tdf["page"].iloc[0])
        extractor_name = _norm(tdf["extractor_name"].iloc[0])
        asset_package = (Path(source_pdf).stem if source_pdf else "unknown_pdf") + "_stage5f"

        # detect header rows and year columns
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
            # fallback: scan whole table for year-like columns
            for _, rr in tdf.iterrows():
                y = _parse_year(rr.get("cell_text"))
                c = int(rr.get("col_index"))
                if y:
                    col_year_map[c] = y
                    year_cols_set.add(c)
            year_groups = _split_year_groups(sorted(year_cols_set))

        # per group metadata
        group_meta: List[Dict[str, Any]] = []
        for gi, gcols in enumerate(year_groups):
            start_col = min(gcols)
            label_cols = _candidate_label_cols(start_col, year_cols_set)

            # gather header text around this group
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
        table_inferred = 0
        table_cleaned = 0
        table_structured_ok = 0

        for ridx, g in tdf.groupby("row_index", sort=True):
            row_df = g.sort_values("col_index")
            row_text = " | ".join([_norm(x) for x in row_df["cell_text"].tolist() if _norm(x)])
            if not row_text:
                continue

            if int(ridx) in header_rows:
                table_header_filtered += 1
                header_filtered_count += 1
                continue
            if _is_meta_row(row_text):
                table_header_filtered += 1
                header_filtered_count += 1
                continue

            for gm in group_meta:
                ycols = gm["year_cols"]
                if not ycols:
                    continue
                # numeric cells in this group
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

                # metric label from label cols
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
                inferred = False
                if not raw_label and _norm(gm["last_label"]):
                    raw_label = _norm(gm["last_label"])
                    inferred = True
                    table_inferred += 1
                    metric_name_inferred_count += 1
                if raw_label:
                    gm["last_label"] = raw_label

                cleaned_label = fs._clean_metric_label_noise(raw_label) if raw_label else ""
                if cleaned_label and cleaned_label != raw_label:
                    table_cleaned += 1
                    metric_name_cleaned_count += 1

                if not cleaned_label:
                    # skip non-actionable row
                    table_non_fin_filtered += 1
                    non_financial_filtered_count += 1
                    continue
                if _is_non_fin_label(cleaned_label):
                    table_non_fin_filtered += 1
                    non_financial_filtered_count += 1
                    continue

                # keep only metric-like rows for stage5d preview to avoid feeding obvious non-core garbage
                if not _looks_core_or_metric_like(cleaned_label):
                    table_non_fin_filtered += 1
                    non_financial_filtered_count += 1
                    continue

                for yc, val, raw_val_cell in numeric_cells:
                    year = _norm(col_year_map.get(yc, ""))
                    unit = _unit_from_text(cleaned_label, row_text, gm["header_text"], raw_val_cell)
                    parse_status = "STRUCTURED_OK"
                    issue_type = "NONE"
                    issue_reason = "improved group-aware metric extraction"

                    if not cleaned_label:
                        parse_status = "MISSING_METRIC_NAME"
                        issue_type = "METRIC_NAME_EMPTY"
                        issue_reason = "metric label empty after cleaning"
                    elif not year:
                        parse_status = "MISSING_YEAR"
                        issue_type = "YEAR_DETECTION_FAILED"
                        issue_reason = "year not mapped from header group"
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
                        "parse_issue_reason": issue_reason + (";label_inferred" if inferred else ""),
                    }
                    improved_rows.append(rec)
                    if parse_status == "STRUCTURED_OK":
                        table_structured_ok += 1

        table_diag_rows.append(
            {
                "source_table_id": _norm(table_id),
                "source_page": page,
                "year_group_count": len(year_groups),
                "header_row_count": len(header_rows),
                "structured_ok_count": table_structured_ok,
                "header_filtered_count": table_header_filtered,
                "non_financial_filtered_count": table_non_fin_filtered,
                "metric_name_inferred_count": table_inferred,
                "metric_name_cleaned_count": table_cleaned,
            }
        )

    improved_df = pd.DataFrame(improved_rows, columns=STRUCTURED_COLS).fillna("")

    # improved standardization preview (dry-run only)
    preview_df, preview_stats = _build_standardization_preview(improved_df)

    prev_raw_metric_name_parse_issue_count = int(prev_5e.get("raw_metric_name_parse_issue_count", 0))
    improved_raw_metric_name_parse_issue_count = int(preview_stats.get("parse_issue_miss_count", 0))

    previous_structured_02_row_count = int(len(prev_02_df))
    improved_structured_02_row_count = int(len(improved_df))
    previous_ready_for_standardization_count = int(prev_5c.get("ready_for_stage5d_standardization_count", 0))
    improved_ready_for_standardization_count = int((improved_df["parse_status"].map(_norm) == "STRUCTURED_OK").sum()) if not improved_df.empty else 0

    previous_standardized_ok_count = int(prev_5d.get("standardized_ok_count", 0))
    improved_standardized_ok_count = int(preview_stats.get("standardized_ok_count", 0))
    previous_mapping_miss_count = int(prev_5d.get("mapping_miss_count", 0))
    improved_mapping_miss_count = int(preview_stats.get("mapping_miss_count", 0))

    parse_issue_reduced_count = int(prev_raw_metric_name_parse_issue_count - improved_raw_metric_name_parse_issue_count)

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

    summary = {
        "input_raw_table_count": int(raw_df["table_id"].map(_norm).replace("", pd.NA).dropna().nunique()),
        "previous_structured_02_row_count": int(previous_structured_02_row_count),
        "improved_structured_02_row_count": int(improved_structured_02_row_count),
        "previous_raw_metric_name_parse_issue_count": int(prev_raw_metric_name_parse_issue_count),
        "improved_raw_metric_name_parse_issue_count": int(improved_raw_metric_name_parse_issue_count),
        "parse_issue_reduced_count": int(parse_issue_reduced_count),
        "previous_ready_for_standardization_count": int(previous_ready_for_standardization_count),
        "improved_ready_for_standardization_count": int(improved_ready_for_standardization_count),
        "previous_standardized_ok_count": int(previous_standardized_ok_count),
        "improved_standardized_ok_count": int(improved_standardized_ok_count),
        "previous_mapping_miss_count": int(previous_mapping_miss_count),
        "improved_mapping_miss_count": int(improved_mapping_miss_count),
        "header_filtered_count": int(header_filtered_count),
        "non_financial_filtered_count": int(non_financial_filtered_count),
        "metric_name_inferred_count": int(metric_name_inferred_count),
        "metric_name_cleaned_count": int(metric_name_cleaned_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5f_raw_metric_extraction_fix_pass": False,
    }

    summary["stage5f_raw_metric_extraction_fix_pass"] = bool(
        summary["improved_structured_02_row_count"] > 0
        and summary["improved_raw_metric_name_parse_issue_count"] < summary["previous_raw_metric_name_parse_issue_count"]
        and summary["improved_standardized_ok_count"] >= summary["previous_standardized_ok_count"]
        and summary["improved_mapping_miss_count"] <= summary["previous_mapping_miss_count"]
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_scope_rules_unchanged"]
        and summary["formal_mapping_rules_unchanged"]
        and summary["formal_normalization_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    status_dist_df = (
        improved_df.groupby(["parse_status", "parse_issue_type"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "parse_status"], ascending=[False, True], kind="mergesort")
        if not improved_df.empty
        else pd.DataFrame(columns=["parse_status", "parse_issue_type", "count"])
    )
    preview_dist_df = (
        preview_df.groupby(["standardization_status", "standardization_issue_type"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "standardization_status"], ascending=[False, True], kind="mergesort")
        if not preview_df.empty
        else pd.DataFrame(columns=["standardization_status", "standardization_issue_type", "count"])
    )
    table_diag_df = pd.DataFrame(table_diag_rows)

    _write_excel(OUT_02_XLSX, {"improved_structured_02": improved_df})
    _write_excel(
        OUT_PREVIEW_XLSX,
        {
            "improved_standardization_preview": preview_df,
            "preview_status_distribution": preview_dist_df,
        },
    )
    _write_excel(
        OUT_REPORT_XLSX,
        {
            "summary": pd.DataFrame([summary]),
            "structured_status_distribution": status_dist_df,
            "preview_status_distribution": preview_dist_df,
            "table_diagnostics": table_diag_df,
            "improved_structured_sample": improved_df.head(400),
            "preview_sample": preview_df.head(400),
            "baseline_refs": pd.DataFrame(
                [
                    {"metric": "prev_ready_for_standardization_count", "value": previous_ready_for_standardization_count},
                    {"metric": "prev_standardized_ok_count", "value": previous_standardized_ok_count},
                    {"metric": "prev_mapping_miss_count", "value": previous_mapping_miss_count},
                    {"metric": "prev_parse_issue_count", "value": prev_raw_metric_name_parse_issue_count},
                ]
            ),
        },
    )

    md_lines = [
        "# Stage5F Raw Metric Extraction Fix (Sandbox)",
        "",
        f"- input_raw_table_count: {summary['input_raw_table_count']}",
        f"- previous_structured_02_row_count: {summary['previous_structured_02_row_count']}",
        f"- improved_structured_02_row_count: {summary['improved_structured_02_row_count']}",
        f"- previous_raw_metric_name_parse_issue_count: {summary['previous_raw_metric_name_parse_issue_count']}",
        f"- improved_raw_metric_name_parse_issue_count: {summary['improved_raw_metric_name_parse_issue_count']}",
        f"- parse_issue_reduced_count: {summary['parse_issue_reduced_count']}",
        f"- previous_ready_for_standardization_count: {summary['previous_ready_for_standardization_count']}",
        f"- improved_ready_for_standardization_count: {summary['improved_ready_for_standardization_count']}",
        f"- previous_standardized_ok_count: {summary['previous_standardized_ok_count']}",
        f"- improved_standardized_ok_count: {summary['improved_standardized_ok_count']}",
        f"- previous_mapping_miss_count: {summary['previous_mapping_miss_count']}",
        f"- improved_mapping_miss_count: {summary['improved_mapping_miss_count']}",
        f"- header_filtered_count: {summary['header_filtered_count']}",
        f"- non_financial_filtered_count: {summary['non_financial_filtered_count']}",
        f"- metric_name_inferred_count: {summary['metric_name_inferred_count']}",
        f"- metric_name_cleaned_count: {summary['metric_name_cleaned_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- stage5f_raw_metric_extraction_fix_pass: {summary['stage5f_raw_metric_extraction_fix_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"improved_structured_02_xlsx: {OUT_02_XLSX}")
    print(f"improved_standardization_preview_xlsx: {OUT_PREVIEW_XLSX}")
    print(f"fix_report_xlsx: {OUT_REPORT_XLSX}")
    print(f"fix_report_md: {OUT_REPORT_MD}")
    print(f"fix_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5f_raw_metric_extraction_fix_pass: {summary['stage5f_raw_metric_extraction_fix_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
