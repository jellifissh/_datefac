import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation
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

STAGE5L_DIR = OUTPUT_DIR / "stage5l_semantic_table_reconstruction"
INPUT_GRID_XLSX = STAGE5L_DIR / "148_stage5l_raw_table_grid_review.xlsx"

STAGE5M_DIR = OUTPUT_DIR / "stage5m_clean_semantic_wide_tables"
INPUT_STAGE5M_CLEAN_WIDE_XLSX = STAGE5M_DIR / "150_stage5m_clean_wide_financial_tables.xlsx"
INPUT_STAGE5M_QUALITY_XLSX = STAGE5M_DIR / "150_stage5m_clean_reconstruction_quality_report.xlsx"
INPUT_STAGE5M_SUMMARY_JSON = STAGE5M_DIR / "151_stage5m_clean_reconstruction_summary.json"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_ALIAS_RULE_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5n_wide_review_layout_fix"
OUT_WIDE_BY_SHEET_XLSX = OUT_DIR / "152_stage5n_clean_wide_financial_tables_by_sheet.xlsx"
OUT_02_XLSX = OUT_DIR / "152_stage5n_structured_02_from_wide.xlsx"
OUT_05_XLSX = OUT_DIR / "152_stage5n_standardized_05_from_wide.xlsx"
OUT_CROSSCHECK_XLSX = OUT_DIR / "152_stage5n_valuation_summary_crosscheck.xlsx"
OUT_REPORT_MD = OUT_DIR / "152_stage5n_wide_layout_quality_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "153_stage5n_wide_layout_summary.json"

YEAR_COLUMNS = ["2024A", "2025A", "2026E", "2027E", "2028E"]
YEAR_TOKEN_RE = re.compile(r"^20\d{2}(?:[AE])?$", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
VALUE_VALID_RE = re.compile(r"[-+]?\d+(?:\.\d+)?$")

HEADER_TOKENS = [
    "资产负债表",
    "产负债表",
    "利润表",
    "现金流量表",
    "金流量表",
    "主要财务比率",
    "成长能力",
    "获利能力",
    "偿债能力",
    "营运能力",
    "每股指标",
    "估值比率",
]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    t = _norm(v).replace("（", "(").replace("）", ")").replace("／", "/")
    t = re.sub(r"\s+", "", t)
    return t.upper()


def _canonical_num_token(v: Any) -> str:
    t = _norm(v).replace(",", "")
    if not t:
        return ""
    try:
        d = Decimal(t)
    except InvalidOperation:
        return t
    if d == d.to_integral():
        return str(int(d))
    s = format(d.normalize(), "f")
    return s.rstrip("0").rstrip(".") if "." in s else s


def _clean_metric_text(v: Any) -> str:
    t = _norm(v).replace("（", "(").replace("）", ")").replace("／", "/")
    t = re.sub(r"\s+", "", t)
    t = t.strip(":：")
    t = fs._clean_metric_label_noise(t)
    return _norm(t)


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
        "formal_alias_rules": _sha256(FORMAL_ALIAS_RULE_FILE),
    }


def _row_text(cols: List[str]) -> str:
    return " ".join([_norm(x) for x in cols if _norm(x)])


def _has_explicit_year_columns(df_table: pd.DataFrame) -> bool:
    col_names = [c for c in df_table.columns if c.startswith("col_")]
    if len(col_names) < 6:
        return False
    for _, r in df_table.iterrows():
        vals = [_compact(r.get(c, "")) for c in col_names]
        years = [v for v in vals if YEAR_TOKEN_RE.fullmatch(v) or v in {"2024", "2025", "2026", "2027", "2028"}]
        if len(years) >= 5:
            return True
    return False


def _extract_valuation_metric_row(text: str) -> Optional[Dict[str, Any]]:
    src = _norm(text)
    if not src:
        return None
    nums = list(NUM_RE.finditer(src))
    if len(nums) < 5:
        return None
    first = nums[0].start()
    metric_raw = _clean_metric_text(src[:first])
    if not metric_raw:
        return None
    values = [_canonical_num_token(m.group(0)) for m in nums[:5]]
    if any(not v for v in values):
        return None

    metric_cleaned = metric_raw
    up = _compact(metric_raw)
    if "EPS" in up:
        metric_cleaned = "EPS(元)"
    elif up.startswith("营业收入"):
        metric_cleaned = "营业收入"
    elif up.startswith("净利润"):
        metric_cleaned = "净利润"
    elif up.startswith("P/E"):
        metric_cleaned = "P/E"
    elif up.startswith("P/B"):
        metric_cleaned = "P/B"

    unit = "百万元"
    if "(%)" in metric_raw or metric_raw.endswith("%") or "增长率" in metric_raw or "ROE" in up:
        unit = "%"
    elif "EPS" in up:
        unit = "元"
    elif up in {"P/E", "P/B", "EV/EBITDA"}:
        unit = "x"

    return {
        "raw_metric_name": metric_raw,
        "metric_name_cleaned": metric_cleaned,
        "unit": unit,
        "2024A": values[0],
        "2025A": values[1],
        "2026E": values[2],
        "2027E": values[3],
        "2028E": values[4],
    }


def _expected_unit(metric: str, statement_type: str, current_unit: str) -> str:
    t = _norm(metric)
    up = _compact(t)
    c = _norm(current_unit)
    if "EPS(" in t and "元" in t:
        return "元"
    if "(%)" in t or t.endswith("%") or "增长率" in t:
        return "%"
    if up in {"P/E", "P/B", "EV/EBITDA"}:
        return "x"
    if _norm(statement_type) in {"主要财务比率", "valuation_summary"}:
        return "ratio" if "率" in t and "(%)" not in t and "%" not in t else c or "%"
    return c if c else "百万元"


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


def _classify_mapping_miss(metric: str) -> str:
    t = _norm(metric)
    if any(x in t for x in ["(%)", "%", "周转率", "ROIC", "资产负债率", "净利率"]):
        return "UNCHANGED_DERIVED_METRIC_NOT_SUPPORTED"
    if any(x in t for x in ["营业利润", "净利润", "EBITDA"]):
        return "UNCHANGED_NON_CORE_METRIC"
    return "UNCHANGED_MAPPING_MISS"


def _build_long_02(wide_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, r in wide_df.iterrows():
        metric = _norm(r.get("metric_name_cleaned")) or _norm(r.get("raw_metric_name"))
        if not metric:
            continue
        for year_col in YEAR_COLUMNS:
            value = _canonical_num_token(r.get(year_col))
            if not value:
                continue
            if not VALUE_VALID_RE.fullmatch(value):
                continue
            row_trace_id = f"{_norm(r.get('semantic_table_id'))}|r{_norm(r.get('source_row_index'))}|y{year_col}"
            rows.append(
                {
                    "row_trace_id": row_trace_id,
                    "asset_package": INPUT_PDF.stem,
                    "source_pdf": str(INPUT_PDF),
                    "source_page": _norm(r.get("source_page")),
                    "source_table_id": _norm(r.get("source_raw_table_id")),
                    "source_row_index": _norm(r.get("source_row_index")),
                    "raw_metric_name": _norm(r.get("raw_metric_name")),
                    "metric_name_cleaned": metric,
                    "statement_type": _norm(r.get("statement_type")),
                    "unit": _norm(r.get("unit")),
                    "year": year_col,
                    "value": value,
                    "source_reference": f"{_norm(r.get('source_raw_table_id'))}:r{_norm(r.get('source_row_index'))}:y{year_col}",
                    "structured_status": "STRUCTURED_OK",
                    "structured_issue_type": "NONE",
                    "structured_issue_reason": "",
                    "evidence": _norm(r.get("evidence")),
                }
            )
    return pd.DataFrame(rows).fillna("")


def _standardize_05_from_02(df_02: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    for _, r in df_02.iterrows():
        raw_metric = _norm(r.get("metric_name_cleaned")) or _norm(r.get("raw_metric_name"))
        year = _norm(r.get("year")).upper()
        value = _canonical_num_token(r.get("value"))
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
            if not YEAR_TOKEN_RE.fullmatch(year):
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
    true_gap_count = 0
    if mapping_miss_count > 0:
        miss = out_df[out_df["standardization_status"] == "MAPPING_MISS"].copy()
        miss["miss_class"] = miss["metric_name_cleaned"].map(_classify_mapping_miss)
        true_gap_count = int((miss["miss_class"] == "UNCHANGED_MAPPING_MISS").sum())
    stats = {
        "standardized_05_row_count": int(len(out_df)),
        "standardized_ok_count": int(standardized_ok_count),
        "mapping_miss_count": int(mapping_miss_count),
        "true_mapping_gap_count": int(true_gap_count),
    }
    return out_df, stats


def _canonical_values_from_row(r: pd.Series) -> Tuple[str, str, str, str, str]:
    return tuple(_canonical_num_token(r.get(y, "")) for y in YEAR_COLUMNS)


def _pick_metric_row(df: pd.DataFrame, key: str) -> Optional[pd.Series]:
    if df.empty:
        return None
    if key == "营业收入":
        cand = df[df["metric_name_cleaned"].astype(str).str.contains("营业收入", regex=False, na=False)].copy()
    elif key == "净利润":
        cand = df[df["metric_name_cleaned"].astype(str).isin(["归属母公司净利润", "净利润"])].copy()
        if not cand.empty:
            pref = cand[cand["metric_name_cleaned"] == "归属母公司净利润"]
            cand = pref if not pref.empty else cand
    elif key == "EPS":
        cand = df[df["metric_name_cleaned"].astype(str).str.contains("EPS", regex=False, na=False)].copy()
    elif key == "P/E":
        cand = df[df["metric_name_cleaned"] == "P/E"].copy()
    elif key == "P/B":
        cand = df[df["metric_name_cleaned"] == "P/B"].copy()
    else:
        cand = pd.DataFrame()
    if cand.empty:
        return None
    cand["source_page_num"] = pd.to_numeric(cand.get("source_page"), errors="coerce").fillna(9999)
    cand["source_row_num"] = pd.to_numeric(cand.get("source_row_index"), errors="coerce").fillna(9999)
    cand = cand.sort_values(["source_page_num", "source_row_num"])
    return cand.iloc[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5N split semantic wide review by sheets and add valuation summary cross-check.")
    parser.parse_args()

    required = [
        INPUT_PDF,
        INPUT_GRID_XLSX,
        INPUT_STAGE5M_CLEAN_WIDE_XLSX,
        INPUT_STAGE5M_QUALITY_XLSX,
        INPUT_STAGE5M_SUMMARY_JSON,
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

    stage5m_summary = json.loads(INPUT_STAGE5M_SUMMARY_JSON.read_text(encoding="utf-8"))
    stage5m_clean_wide = pd.read_excel(INPUT_STAGE5M_CLEAN_WIDE_XLSX, sheet_name=0).fillna("")
    cleanup_log_df = pd.read_excel(INPUT_STAGE5M_QUALITY_XLSX, sheet_name="cleanup_log").fillna("")

    grid_rows_df = pd.read_excel(INPUT_GRID_XLSX, sheet_name="reconstructed_grid_rows").fillna("")
    grid_summary_df = pd.read_excel(INPUT_GRID_XLSX, sheet_name="grid_table_summary").fillna("")

    # Build non-year table guard rows from tables without explicit year columns.
    non_year_rows: List[Dict[str, Any]] = []
    non_year_table_guard_enabled = True
    for _, meta in grid_summary_df.iterrows():
        table_id = _norm(meta.get("table_id"))
        page_num = pd.to_numeric(meta.get("page"), errors="coerce")
        page = int(page_num) if pd.notna(page_num) else 0
        table_df = grid_rows_df[grid_rows_df["table_id"] == table_id].copy()
        if table_df.empty:
            continue
        has_year_cols = _has_explicit_year_columns(table_df)
        if has_year_cols:
            continue
        col_names = [c for c in table_df.columns if c.startswith("col_")]
        for _, r in table_df.sort_values("row_index").iterrows():
            txt = _row_text([r.get(c, "") for c in col_names])
            if not txt:
                continue
            non_year_rows.append(
                {
                    "table_id": table_id,
                    "page": page,
                    "row_index": (
                        int(pd.to_numeric(r.get("row_index"), errors="coerce"))
                        if pd.notna(pd.to_numeric(r.get("row_index"), errors="coerce"))
                        else 0
                    ),
                    "row_text": txt,
                    "guard_reason": "table_has_no_explicit_year_columns",
                    "excluded_from_long_02": True,
                }
            )
    non_year_table_df = pd.DataFrame(non_year_rows).fillna("")

    # Detect valuation summary section from page 2 raw grid text.
    valuation_rows: List[Dict[str, Any]] = []
    valuation_parse_issues: List[Dict[str, Any]] = []
    valuation_summary_detected = False

    page2_tables = grid_summary_df[grid_summary_df["page"] == 2]["table_id"].astype(str).tolist()
    valuation_table_id = page2_tables[0] if page2_tables else ""
    if valuation_table_id:
        page2_df = grid_rows_df[grid_rows_df["table_id"] == valuation_table_id].copy()
        page2_df["row_index"] = pd.to_numeric(page2_df["row_index"], errors="coerce").fillna(0).astype(int)
        col_names = [c for c in page2_df.columns if c.startswith("col_")]
        row_text_map: Dict[int, str] = {}
        for _, r in page2_df.sort_values("row_index").iterrows():
            row_text_map[int(r["row_index"])] = _row_text([r.get(c, "") for c in col_names])

        valuation_header_row = 0
        for ridx, txt in row_text_map.items():
            if "财务摘要和估值指标" in txt:
                valuation_header_row = ridx
                break

        if valuation_header_row > 0:
            valuation_summary_detected = True
            start_row = valuation_header_row + 1
            end_row = max(row_text_map.keys()) if row_text_map else valuation_header_row
            for ridx in range(start_row, end_row + 1):
                txt = _norm(row_text_map.get(ridx, ""))
                if not txt:
                    continue
                if "资料来源" in txt or "免责声明" in txt or "敬请参阅最后一页" in txt:
                    break
                if "指标" in txt and "2024A" in txt and "2028E" in txt:
                    continue

                parsed = _extract_valuation_metric_row(txt)
                if not parsed:
                    valuation_parse_issues.append(
                        {
                            "source_table_id": valuation_table_id,
                            "source_page": 2,
                            "source_row_index": ridx,
                            "row_text": txt,
                            "issue_type": "NON_YEAR_TABLE_GUARD",
                            "issue_reason": "does_not_match_metric_plus_five_year_values_pattern",
                        }
                    )
                    continue

                valuation_rows.append(
                    {
                        "raw_metric_name": parsed["raw_metric_name"],
                        "metric_name_cleaned": parsed["metric_name_cleaned"],
                        "statement_type": "valuation_summary",
                        "unit": parsed["unit"],
                        "2024A": parsed["2024A"],
                        "2025A": parsed["2025A"],
                        "2026E": parsed["2026E"],
                        "2027E": parsed["2027E"],
                        "2028E": parsed["2028E"],
                        "semantic_table_id": f"S5N-{valuation_table_id}-VALUATION_SUMMARY",
                        "source_page": 2,
                        "source_raw_table_id": valuation_table_id,
                        "source_row_index": ridx,
                        "metric_reconstruction_status": "RECONSTRUCTED_OK",
                        "metric_reconstruction_issue": "NONE",
                        "cleanup_action": "NONE",
                        "evidence": "parsed from page2 valuation summary section",
                    }
                )

    valuation_df = pd.DataFrame(valuation_rows).fillna("")

    # Normalize units for valuation rows.
    if not valuation_df.empty:
        for i, r in valuation_df.iterrows():
            valuation_df.at[i, "unit"] = _expected_unit(_norm(r.get("metric_name_cleaned")), "valuation_summary", _norm(r.get("unit")))

    # Split semantic sheets from Stage5M + valuation summary.
    balance_df = stage5m_clean_wide[stage5m_clean_wide["statement_type"] == "资产负债表"].copy().fillna("")
    income_df = stage5m_clean_wide[stage5m_clean_wide["statement_type"] == "利润表"].copy().fillna("")
    cash_df = stage5m_clean_wide[stage5m_clean_wide["statement_type"] == "现金流量表"].copy().fillna("")
    ratio_df = stage5m_clean_wide[stage5m_clean_wide["statement_type"] == "主要财务比率"].copy().fillna("")

    # Build exceptions: filtered rows + valuation parse issues.
    exc_rows: List[Dict[str, Any]] = []
    if not cleanup_log_df.empty:
        for _, r in cleanup_log_df.iterrows():
            include = bool(r.get("include_in_clean_wide", False))
            if include:
                continue
            exc_rows.append(
                {
                    "source_page": _norm(r.get("source_page")),
                    "source_raw_table_id": _norm(r.get("source_raw_table_id")),
                    "source_row_index": _norm(r.get("source_row_index")),
                    "raw_metric_name": _norm(r.get("raw_metric_name_original")),
                    "metric_name_cleaned": _norm(r.get("metric_name_cleaned_original")),
                    "category": "FILTERED_BY_STAGE5M",
                    "detail": _norm(r.get("cleanup_action")),
                    "evidence": _norm(r.get("evidence")),
                }
            )
    for r in valuation_parse_issues:
        exc_rows.append(
            {
                "source_page": r["source_page"],
                "source_raw_table_id": r["source_table_id"],
                "source_row_index": r["source_row_index"],
                "raw_metric_name": "",
                "metric_name_cleaned": "",
                "category": "VALUATION_PARSE_SKIPPED_BY_GUARD",
                "detail": r["issue_reason"],
                "evidence": r["row_text"],
            }
        )
    exceptions_df = pd.DataFrame(exc_rows).fillna("")

    # Cross-check valuation summary vs detailed table.
    detail_df = pd.concat([income_df, ratio_df], ignore_index=True) if not income_df.empty or not ratio_df.empty else pd.DataFrame()
    cross_metrics = ["营业收入", "净利润", "EPS", "P/E", "P/B"]
    cross_rows: List[Dict[str, Any]] = []
    consistent_count = 0
    conflict_count = 0

    for key in cross_metrics:
        v_row = _pick_metric_row(valuation_df, key)
        d_row = _pick_metric_row(detail_df, key)
        valuation_found = v_row is not None
        detail_found = d_row is not None
        v_values = _canonical_values_from_row(v_row) if v_row is not None else ("", "", "", "", "")
        d_values = _canonical_values_from_row(d_row) if d_row is not None else ("", "", "", "", "")
        if valuation_found and detail_found and v_values == d_values:
            result = "CONSISTENT_WITH_DETAIL_TABLE"
            consistent_count += 1
        else:
            result = "CONFLICT_WITH_DETAIL_TABLE"
            conflict_count += 1
        cross_rows.append(
            {
                "metric_key": key,
                "valuation_summary_metric_name": _norm(v_row.get("metric_name_cleaned")) if v_row is not None else "",
                "detail_table_metric_name": _norm(d_row.get("metric_name_cleaned")) if d_row is not None else "",
                "valuation_summary_unit": _norm(v_row.get("unit")) if v_row is not None else "",
                "detail_table_unit": _norm(d_row.get("unit")) if d_row is not None else "",
                "valuation_2024A": v_values[0],
                "valuation_2025A": v_values[1],
                "valuation_2026E": v_values[2],
                "valuation_2027E": v_values[3],
                "valuation_2028E": v_values[4],
                "detail_2024A": d_values[0],
                "detail_2025A": d_values[1],
                "detail_2026E": d_values[2],
                "detail_2027E": d_values[3],
                "detail_2028E": d_values[4],
                "crosscheck_result": result,
                "promotion_guard": "DO_NOT_AUTO_PROMOTE_IF_CONFLICT",
            }
        )
    cross_df = pd.DataFrame(cross_rows).fillna("")

    # Unified long-form outputs still kept.
    combined_wide_df = pd.concat([balance_df, income_df, cash_df, ratio_df, valuation_df], ignore_index=True).fillna("")
    clean_02_df = _build_long_02(combined_wide_df)
    clean_05_df, std_stats = _standardize_05_from_02(clean_02_df)

    # Remaining checks.
    remaining_header_row_count = 0
    remaining_unit_issue_count = 0
    for _, r in combined_wide_df.iterrows():
        metric = _norm(r.get("metric_name_cleaned"))
        if any(tok in metric for tok in HEADER_TOKENS):
            remaining_header_row_count += 1
        unit_expected = _expected_unit(metric, _norm(r.get("statement_type")), _norm(r.get("unit")))
        if _norm(r.get("unit")) != unit_expected:
            remaining_unit_issue_count += 1

    # Workbook by sheet.
    overview_rows = [
        {"sheet_name": "balance_sheet", "row_count": int(len(balance_df)), "description": "资产负债表语义宽表"},
        {"sheet_name": "income_statement", "row_count": int(len(income_df)), "description": "利润表语义宽表"},
        {"sheet_name": "cash_flow_statement", "row_count": int(len(cash_df)), "description": "现金流量表语义宽表"},
        {"sheet_name": "financial_ratio", "row_count": int(len(ratio_df)), "description": "主要财务比率语义宽表"},
        {"sheet_name": "valuation_summary", "row_count": int(len(valuation_df)), "description": "第2页财务摘要和估值指标"},
        {"sheet_name": "exceptions", "row_count": int(len(exceptions_df)), "description": "过滤行与解析例外"},
        {"sheet_name": "non_year_table", "row_count": int(len(non_year_table_df)), "description": "non-year table guard review-only"},
    ]
    overview_df = pd.DataFrame(overview_rows)

    wide_sheets = {
        "overview_index": overview_df,
        "balance_sheet": balance_df,
        "income_statement": income_df,
        "cash_flow_statement": cash_df,
        "financial_ratio": ratio_df,
        "valuation_summary": valuation_df,
        "exceptions": exceptions_df,
        "non_year_table": non_year_table_df,
    }
    _write_excel(OUT_WIDE_BY_SHEET_XLSX, wide_sheets)
    _write_excel(OUT_02_XLSX, {"structured_02_from_wide": clean_02_df})
    _write_excel(OUT_05_XLSX, {"standardized_05_from_wide": clean_05_df})
    _write_excel(OUT_CROSSCHECK_XLSX, {"valuation_summary_crosscheck": cross_df})

    after = _snapshot_hashes()
    production_files_unchanged = bool(
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    formal_rules_unchanged = bool(
        before["formal_scope_rules"] == after["formal_scope_rules"]
        and before["formal_mapping_rules"] == after["formal_mapping_rules"]
        and before["formal_normalization_rules"] == after["formal_normalization_rules"]
        and before["formal_alias_rules"] == after["formal_alias_rules"]
    )
    official_02B_unchanged = bool(before["02B"] == after["02B"])

    summary = {
        "valuation_summary_detected": bool(valuation_summary_detected),
        "valuation_summary_metric_count": int(len(valuation_df)),
        "separated_sheet_count": int(len(wide_sheets)),
        "balance_sheet_sheet_generated": bool(len(balance_df) > 0),
        "income_statement_sheet_generated": bool(len(income_df) > 0),
        "cash_flow_statement_sheet_generated": bool(len(cash_df) > 0),
        "financial_ratio_sheet_generated": bool(len(ratio_df) > 0),
        "valuation_summary_sheet_generated": bool(len(valuation_df) > 0),
        "non_year_table_guard_enabled": bool(non_year_table_guard_enabled),
        "valuation_summary_consistent_count": int(consistent_count),
        "valuation_summary_conflict_count": int(conflict_count),
        "remaining_header_row_count": int(remaining_header_row_count),
        "remaining_unit_issue_count": int(remaining_unit_issue_count),
        "structured_02_row_count": int(len(clean_02_df)),
        "standardized_05_row_count": int(std_stats["standardized_05_row_count"]),
        "standardized_ok_count": int(std_stats["standardized_ok_count"]),
        "mapping_miss_count": int(std_stats["mapping_miss_count"]),
        "stage5m_standardized_ok_count": int(stage5m_summary.get("clean_standardized_ok_count", 0)),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_rules_unchanged": bool(formal_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5n_wide_layout_fix_pass": False,
    }

    summary["stage5n_wide_layout_fix_pass"] = bool(
        summary["valuation_summary_detected"]
        and summary["valuation_summary_metric_count"] > 0
        and summary["balance_sheet_sheet_generated"]
        and summary["income_statement_sheet_generated"]
        and summary["cash_flow_statement_sheet_generated"]
        and summary["financial_ratio_sheet_generated"]
        and summary["valuation_summary_sheet_generated"]
        and summary["non_year_table_guard_enabled"]
        and summary["remaining_header_row_count"] == 0
        and summary["remaining_unit_issue_count"] == 0
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    md_lines = [
        "# Stage5N Wide Review Layout Fix",
        "",
        "## Key Layout Results",
        f"- valuation_summary_detected: {summary['valuation_summary_detected']}",
        f"- valuation_summary_metric_count: {summary['valuation_summary_metric_count']}",
        f"- separated_sheet_count: {summary['separated_sheet_count']}",
        f"- balance_sheet_sheet_generated: {summary['balance_sheet_sheet_generated']}",
        f"- income_statement_sheet_generated: {summary['income_statement_sheet_generated']}",
        f"- cash_flow_statement_sheet_generated: {summary['cash_flow_statement_sheet_generated']}",
        f"- financial_ratio_sheet_generated: {summary['financial_ratio_sheet_generated']}",
        f"- valuation_summary_sheet_generated: {summary['valuation_summary_sheet_generated']}",
        f"- non_year_table_guard_enabled: {summary['non_year_table_guard_enabled']}",
        "",
        "## Valuation Summary Cross-check",
        f"- valuation_summary_consistent_count: {summary['valuation_summary_consistent_count']}",
        f"- valuation_summary_conflict_count: {summary['valuation_summary_conflict_count']}",
        "",
        "## Quality Gates",
        f"- remaining_header_row_count: {summary['remaining_header_row_count']}",
        f"- remaining_unit_issue_count: {summary['remaining_unit_issue_count']}",
        f"- stage5n_wide_layout_fix_pass: {summary['stage5n_wide_layout_fix_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5n_wide_by_sheet_xlsx: {OUT_WIDE_BY_SHEET_XLSX}")
    print(f"stage5n_02_xlsx: {OUT_02_XLSX}")
    print(f"stage5n_05_xlsx: {OUT_05_XLSX}")
    print(f"stage5n_crosscheck_xlsx: {OUT_CROSSCHECK_XLSX}")
    print(f"stage5n_report_md: {OUT_REPORT_MD}")
    print(f"stage5n_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5n_wide_layout_fix_pass: {summary['stage5n_wide_layout_fix_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
