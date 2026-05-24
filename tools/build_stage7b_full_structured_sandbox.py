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
import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
INPUT_PDF_DIR = BASE_DIR / "input" / "stage7a_regression_pdfs"

STAGE7A_DIR = BASE_DIR / "output" / "stage7a_5pdf_regression_sandbox"
STAGE7A_RAW_DIR = STAGE7A_DIR / "sandbox_raw_tables"
STAGE7A_WIDE_DIR = STAGE7A_DIR / "sandbox_clean_wide"
STAGE7A_SUMMARY = STAGE7A_DIR / "180_stage7a_5pdf_regression_summary.json"
STAGE7A_INVENTORY = STAGE7A_DIR / "180_stage7a_per_pdf_inventory.xlsx"

OUT_DIR = BASE_DIR / "output" / "stage7b_full_structured_sandbox"
OUT_SUMMARY = OUT_DIR / "181_stage7b_full_structured_summary.json"
OUT_REPORT = OUT_DIR / "181_stage7b_full_structured_report.md"
OUT_INVENTORY = OUT_DIR / "181_stage7b_per_pdf_table_block_inventory.xlsx"
OUT_FULL_TABLE = OUT_DIR / "181_stage7b_full_structured_table.xlsx"
OUT_STD_TABLE = OUT_DIR / "181_stage7b_standardized_structured_table.xlsx"
OUT_CORE_PREVIEW = OUT_DIR / "181_stage7b_core_metrics_preview.xlsx"

OUT_BLOCK_DIR = OUT_DIR / "sandbox_table_blocks"
OUT_DEBUG_DIR = OUT_DIR / "sandbox_parse_debug"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

YEAR_TOKEN_RE = re.compile(r"20\d{2}(?:[AE])?", re.IGNORECASE)
NUM_TOKEN_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")

CORE_METRICS = ["营业收入", "归属母公司净利润", "毛利率", "ROE", "每股收益", "P/E", "P/B", "EV/EBITDA"]

STATEMENT_TYPE_VALUES = [
    "financial_data_and_valuation",
    "income_statement",
    "balance_sheet",
    "cash_flow_statement",
    "financial_ratios",
    "per_share_metrics",
    "valuation_metrics",
    "company_profile",
    "rating_explanation",
    "disclaimer",
    "unknown_financial_table",
    "non_financial_table",
]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    return re.sub(r"\s+", "", _norm(v)).upper()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    txt = (p.stdout or "").strip()
    if not txt:
        return {"overall_status": "UNKNOWN"}
    return json.loads(txt)


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_scope_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _build_grid(raw_df: pd.DataFrame, table_id: str) -> Tuple[pd.DataFrame, int, int]:
    one = raw_df[raw_df["table_id"].map(_norm) == _norm(table_id)].copy()
    if one.empty:
        return pd.DataFrame(), 0, 0
    one["row_index"] = pd.to_numeric(one["row_index"], errors="coerce").fillna(0).astype(int)
    one["col_index"] = pd.to_numeric(one["col_index"], errors="coerce").fillna(0).astype(int)
    max_row = int(one["row_index"].max())
    max_col = int(one["col_index"].max())
    rows: List[Dict[str, Any]] = []
    for ridx in range(1, max_row + 1):
        rec: Dict[str, Any] = {"row_index": ridx}
        rs = one[one["row_index"] == ridx]
        for cidx in range(1, max_col + 1):
            h = rs[rs["col_index"] == cidx]
            rec[f"col_{cidx}"] = _norm(h.iloc[0]["cell_text"]) if not h.empty else ""
        rows.append(rec)
    return pd.DataFrame(rows), max_row, max_col


def _row_text(grid: pd.DataFrame, ridx: int, max_col: int) -> str:
    if grid.empty:
        return ""
    one = grid[grid["row_index"] == ridx]
    if one.empty:
        return ""
    vals = []
    for c in range(1, max_col + 1):
        v = _norm(one.iloc[0].get(f"col_{c}", ""))
        if v:
            vals.append(v)
    return " | ".join(vals)


def _classify_statement_type(text: str) -> str:
    t = _compact(text)
    if not t:
        return "unknown_financial_table"
    if any(k in t for k in ["免责声明", "请务必阅读", "资料来源", "分析师", "评级说明"]):
        return "non_financial_table"
    if any(k in t for k in ["公司概况", "公司基本情况", "公司信息", "主营业务"]):
        return "company_profile"
    if "财务数据与估值" in t:
        return "financial_data_and_valuation"
    if any(k in t for k in ["利润表", "损益表", "营业收入", "净利润"]):
        return "income_statement"
    if any(k in t for k in ["资产负债表", "总资产", "总负债", "流动资产", "非流动资产"]):
        return "balance_sheet"
    if any(k in t for k in ["现金流量表", "经营活动现金流", "投资活动现金流", "筹资活动现金流"]):
        return "cash_flow_statement"
    if any(k in t for k in ["主要财务比率", "财务比率", "毛利率", "ROE", "ROA"]):
        return "financial_ratios"
    if any(k in t for k in ["每股", "EPS", "每股收益", "每股净资产"]):
        return "per_share_metrics"
    if any(k in t for k in ["PE", "P/E", "PB", "P/B", "EV/EBITDA", "估值", "目标价"]):
        return "valuation_metrics"
    if any(k in t for k in ["评级", "买入", "增持", "中性", "卖出"]):
        return "rating_explanation"
    return "unknown_financial_table"


def _detect_table_statement_type(grid: pd.DataFrame, max_row: int, max_col: int) -> str:
    buf = []
    for ridx in range(1, min(max_row, 8) + 1):
        buf.append(_row_text(grid, ridx, max_col))
    return _classify_statement_type(" || ".join(buf))


def _detect_block_type(grid: pd.DataFrame, max_row: int, max_col: int, table_text: str) -> str:
    t = _compact(table_text)
    if any(x in t for x in ["免责声明", "请务必阅读", "资料来源", "评级说明"]):
        return "non_financial_text_table"
    if max_col >= 10 and any(x in t for x in ["利润表", "资产负债表", "现金流量表", "主要财务比率"]):
        return "stacked_multi_panel_table"
    if max_col >= 8 and any(x in t for x in ["财务数据与估值", "每股指标", "估值比率"]):
        return "left_right_multi_panel_table"
    if max_col >= 5:
        return "single_wide_year_table"
    if " | " in table_text and NUM_TOKEN_RE.search(table_text):
        return "paragraph_embedded_metrics"
    return "unknown"


def _normalize_year_token(v: str) -> str:
    tok = _norm(v).upper()
    if not tok:
        return ""
    m = YEAR_TOKEN_RE.search(tok)
    if not m:
        return ""
    y = m.group(0).upper()
    if y.endswith("A") or y.endswith("E"):
        return y
    if y in {"2024", "2025"}:
        return f"{y}A"
    if y in {"2026", "2027", "2028"}:
        return f"{y}E"
    return y


def _extract_year_cols(grid: pd.DataFrame, max_row: int, max_col: int) -> Dict[int, str]:
    year_cols: Dict[int, str] = {}
    header_scan_rows = min(max_row, 5)
    for ridx in range(1, header_scan_rows + 1):
        one = grid[grid["row_index"] == ridx]
        if one.empty:
            continue
        for c in range(1, max_col + 1):
            val = _norm(one.iloc[0].get(f"col_{c}", ""))
            y = _normalize_year_token(val)
            if y and c not in year_cols:
                year_cols[c] = y
    if not year_cols:
        canonical = ["2024A", "2025A", "2026E", "2027E", "2028E"]
        start_col = max(2, max_col - 4)
        for i, c in enumerate(range(start_col, min(max_col, start_col + 4) + 1)):
            if i < len(canonical):
                year_cols[c] = canonical[i]
    return year_cols


def _infer_unit(table_text: str, metric: str, value_raw: str) -> Tuple[str, float, bool]:
    tt = _compact(table_text)
    mm = _compact(metric)
    vv = _compact(value_raw)
    if "每股收益" in mm or "EPS" in mm:
        return "元/股", 0.98, False
    if "(%)" in metric or metric.endswith("%") or "率" in metric or "%" in vv:
        return "%", 0.9, False
    if any(x in mm for x in ["P/E", "PE", "P/B", "PB", "EV/EBITDA"]) or any(x in tt for x in ["估值", "倍"]):
        return "倍", 0.82, False
    if any(x in tt for x in ["百万元", "百万"]):
        return "百万元", 0.85, False
    if any(x in tt for x in ["亿元"]):
        return "亿元", 0.85, False
    if any(x in tt for x in ["万元"]):
        return "万元", 0.82, False
    if any(x in tt for x in ["元/股"]):
        return "元/股", 0.85, False
    return "", 0.3, True


def _extract_metric_label(row_vals: List[str], year_cols: Dict[int, str]) -> str:
    year_col_set = set(year_cols.keys())
    for idx, val in enumerate(row_vals, start=1):
        if idx in year_col_set:
            continue
        v = _norm(val)
        if not v:
            continue
        if _normalize_year_token(v):
            continue
        if NUM_TOKEN_RE.fullmatch(v.replace(",", "")):
            continue
        if len(v) >= 2:
            return v
    return ""


def _build_rows_from_table(
    raw_df: pd.DataFrame,
    pdf_name: str,
    page_number: int,
    table_id: str,
    block_prefix: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    grid, max_row, max_col = _build_grid(raw_df, table_id)
    if grid.empty:
        return [], [], []
    table_text = " || ".join([_row_text(grid, r, max_col) for r in range(1, min(max_row, 10) + 1)])
    table_statement = _detect_table_statement_type(grid, max_row, max_col)
    block_type = _detect_block_type(grid, max_row, max_col, table_text)
    year_cols = _extract_year_cols(grid, max_row, max_col)

    rows: List[Dict[str, Any]] = []
    debug: List[Dict[str, Any]] = []
    blocks: List[Dict[str, Any]] = []

    block_id = f"{block_prefix}|{table_id}|b01"
    cur_statement = table_statement
    block_conf = 0.75 if cur_statement != "unknown_financial_table" else 0.52
    blocks.append(
        {
            "source_pdf_name": pdf_name,
            "page_number": page_number,
            "raw_table_id": table_id,
            "block_id": block_id,
            "block_type": block_type,
            "statement_type": cur_statement,
            "max_row": max_row,
            "max_col": max_col,
            "year_columns": ",".join([f"c{c}:{y}" for c, y in year_cols.items()]),
            "block_confidence": block_conf,
        }
    )

    for ridx in range(1, max_row + 1):
        one = grid[grid["row_index"] == ridx]
        if one.empty:
            continue
        row_vals = [_norm(one.iloc[0].get(f"col_{c}", "")) for c in range(1, max_col + 1)]
        row_text = " | ".join([v for v in row_vals if v])
        if not row_text:
            continue

        header_stmt = _classify_statement_type(row_text)
        if header_stmt in STATEMENT_TYPE_VALUES and header_stmt not in {"unknown_financial_table", "non_financial_table"}:
            cur_statement = header_stmt

        metric = _extract_metric_label(row_vals, year_cols)
        if not metric:
            debug.append(
                {
                    "source_pdf_name": pdf_name,
                    "raw_table_id": table_id,
                    "row_index": ridx,
                    "reason": "metric_not_found",
                    "row_text": row_text,
                }
            )
            continue

        normalized_metric = _norm(fs._clean_metric_label_noise(metric)) or metric
        match = fs._match_standard_metric(normalized_metric) or fs._match_standard_metric(metric)
        mapping_status = "MAPPED" if match else "MAPPING_MISS"
        standard_metric = _norm(match.get("standard_metric")) if match else ""

        for cidx, y in year_cols.items():
            val_raw = _norm(one.iloc[0].get(f"col_{cidx}", ""))
            if not val_raw:
                continue
            m = NUM_TOKEN_RE.search(val_raw.replace(",", ""))
            if not m:
                debug.append(
                    {
                        "source_pdf_name": pdf_name,
                        "raw_table_id": table_id,
                        "row_index": ridx,
                        "col_index": cidx,
                        "reason": "value_not_numeric",
                        "row_text": row_text,
                        "value_raw": val_raw,
                    }
                )
                continue
            value = m.group(0).replace(",", "")
            if not YEAR_TOKEN_RE.fullmatch(y):
                debug.append(
                    {
                        "source_pdf_name": pdf_name,
                        "raw_table_id": table_id,
                        "row_index": ridx,
                        "col_index": cidx,
                        "reason": "bad_year_token",
                        "row_text": row_text,
                        "year": y,
                    }
                )
                continue
            inferred_unit, unit_confidence, needs_unit_review = _infer_unit(table_text, normalized_metric, val_raw)
            raw_unit = inferred_unit

            needs_mapping_review = not bool(match)
            needs_manual_review = bool(needs_mapping_review or needs_unit_review or _norm(cur_statement) in {"unknown_financial_table", "non_financial_table"})
            if "EPS" in _compact(normalized_metric) or "每股收益" in normalized_metric:
                if inferred_unit in {"", "ratio", "%"}:
                    inferred_unit = "元/股"
                    needs_unit_review = True
                    needs_manual_review = True

            rows.append(
                {
                    "source_pdf": str(INPUT_PDF_DIR / pdf_name),
                    "source_pdf_name": pdf_name,
                    "page_number": int(page_number),
                    "raw_table_id": table_id,
                    "block_id": block_id,
                    "block_type": block_type,
                    "statement_type": cur_statement if cur_statement in STATEMENT_TYPE_VALUES else "unknown_financial_table",
                    "raw_metric_name": metric,
                    "normalized_metric_name": normalized_metric,
                    "raw_unit": raw_unit,
                    "inferred_unit": inferred_unit,
                    "year": y,
                    "value": value,
                    "value_raw": val_raw,
                    "row_order": int(ridx),
                    "column_order": int(cidx),
                    "parse_method": "row_label_plus_year_column",
                    "extraction_confidence": 0.86 if value else 0.35,
                    "block_confidence": block_conf,
                    "unit_confidence": float(unit_confidence),
                    "mapping_status": mapping_status,
                    "standard_metric": standard_metric,
                    "needs_mapping_review": bool(needs_mapping_review),
                    "needs_unit_review": bool(needs_unit_review),
                    "needs_manual_review": bool(needs_manual_review),
                    "source_text_excerpt": row_text[:400],
                }
            )

    return rows, blocks, debug


def _first_sheet(path: Path) -> pd.DataFrame:
    xls = pd.ExcelFile(path)
    return pd.read_excel(path, sheet_name=xls.sheet_names[0]).fillna("")


def _load_stage7a_clean_counts() -> Dict[str, int]:
    if not STAGE7A_INVENTORY.exists():
        return {}
    df = pd.read_excel(STAGE7A_INVENTORY, sheet_name="per_pdf").fillna("")
    out: Dict[str, int] = {}
    for _, r in df.iterrows():
        out[_norm(r.get("pdf"))] = int(pd.to_numeric(r.get("clean_wide_row_count"), errors="coerce") or 0)
    return out


def main() -> int:
    for p in [STAGE7A_SUMMARY, STAGE7A_INVENTORY, STAGE7A_RAW_DIR, STAGE7A_WIDE_DIR, INPUT_PDF_DIR]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    before = _snapshot_guard()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BLOCK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    stage7a_summary = json.loads(STAGE7A_SUMMARY.read_text(encoding="utf-8"))
    clean_counts = _load_stage7a_clean_counts()

    raw_files = sorted(STAGE7A_RAW_DIR.glob("*_raw_tables.xlsx"))
    if len(raw_files) != 5:
        raise RuntimeError(f"Expected 5 stage7a raw table files, got {len(raw_files)}")

    full_rows: List[Dict[str, Any]] = []
    block_rows: List[Dict[str, Any]] = []
    debug_rows: List[Dict[str, Any]] = []
    pdf_results: List[Dict[str, Any]] = []

    for raw_path in raw_files:
        pdf_stem = raw_path.name.replace("_raw_tables.xlsx", "")
        source_pdf = f"{pdf_stem}.pdf"
        parse_ok = True
        parse_error = ""

        raw_df = pd.read_excel(raw_path, sheet_name="raw_tables").fillna("")

        per_rows: List[Dict[str, Any]] = []
        per_blocks: List[Dict[str, Any]] = []
        per_debug: List[Dict[str, Any]] = []
        detected_stmt = set()

        try:
            table_ids = raw_df["table_id"].map(_norm).dropna().unique().tolist()
            for table_id in table_ids:
                m = re.search(r"\|p(\d+)\|t(\d+)\|", table_id)
                page_num = int(m.group(1)) if m else 0
                rows, blocks, dbg = _build_rows_from_table(
                    raw_df=raw_df,
                    pdf_name=source_pdf,
                    page_number=page_num,
                    table_id=table_id,
                    block_prefix=pdf_stem,
                )
                per_rows.extend(rows)
                per_blocks.extend(blocks)
                per_debug.extend(dbg)
                for b in blocks:
                    st = _norm(b.get("statement_type"))
                    if st:
                        detected_stmt.add(st)
        except Exception as exc:
            parse_ok = False
            parse_error = f"{type(exc).__name__}: {exc}"

        per_full_df = pd.DataFrame(per_rows).fillna("")
        per_block_df = pd.DataFrame(per_blocks).fillna("")
        per_debug_df = pd.DataFrame(per_debug).fillna("")

        full_rows.extend(per_rows)
        block_rows.extend(per_blocks)
        debug_rows.extend(per_debug)

        _write_excel(
            OUT_BLOCK_DIR / f"{pdf_stem}_table_blocks.xlsx",
            {
                "table_blocks": per_block_df,
                "full_structured_rows": per_full_df,
            },
        )
        _write_excel(
            OUT_DEBUG_DIR / f"{pdf_stem}_parse_debug.xlsx",
            {
                "parse_debug": per_debug_df,
            },
        )

        stage7a_clean = int(clean_counts.get(source_pdf, 0))
        stage7b_full = int(len(per_full_df))
        mapping_review_count = int(per_full_df["needs_mapping_review"].astype(bool).sum()) if not per_full_df.empty else 0
        unit_review_count = int(per_full_df["needs_unit_review"].astype(bool).sum()) if not per_full_df.empty else 0
        manual_review_count = int(per_full_df["needs_manual_review"].astype(bool).sum()) if not per_full_df.empty else 0

        detected_sorted = sorted(list(detected_stmt))
        pdf_results.append(
            {
                "source_pdf": source_pdf,
                "parse_ok": bool(parse_ok),
                "raw_table_count": int(raw_df["table_id"].map(_norm).nunique()) if not raw_df.empty else 0,
                "stage7a_clean_wide_row_count": int(stage7a_clean),
                "stage7b_full_structured_row_count": int(stage7b_full),
                "full_structured_gain": int(stage7b_full - stage7a_clean),
                "detected_block_count": int(len(per_block_df)),
                "detected_statement_types": detected_sorted,
                "income_statement_detected": "income_statement" in detected_sorted,
                "balance_sheet_detected": "balance_sheet" in detected_sorted,
                "cash_flow_statement_detected": "cash_flow_statement" in detected_sorted,
                "financial_ratios_detected": "financial_ratios" in detected_sorted,
                "per_share_metrics_detected": "per_share_metrics" in detected_sorted,
                "valuation_metrics_detected": "valuation_metrics" in detected_sorted,
                "mapping_review_count": int(mapping_review_count),
                "unit_review_count": int(unit_review_count),
                "manual_review_count": int(manual_review_count),
                "status": "OK" if parse_ok else f"FAILED:{parse_error}",
            }
        )

    full_df = pd.DataFrame(full_rows).fillna("")
    blocks_df = pd.DataFrame(block_rows).fillna("")
    parse_debug_df = pd.DataFrame(debug_rows).fillna("")
    pdf_result_df = pd.DataFrame(pdf_results).fillna("")

    if full_df.empty:
        raise RuntimeError("Stage7B generated empty full_structured_table.")

    std_df = full_df.copy()
    std_df["standardized_status"] = std_df["mapping_status"].map(lambda x: "STANDARDIZED_CANDIDATE" if _norm(x) == "MAPPED" else "UNMAPPED_RETAINED")
    std_df["year_valid"] = std_df["year"].map(lambda y: bool(YEAR_TOKEN_RE.fullmatch(_norm(y))))
    std_df["value_valid"] = std_df["value"].map(lambda v: bool(NUM_TOKEN_RE.fullmatch(_norm(v))))

    core_df = std_df[
        std_df["standard_metric"].map(_norm).isin(CORE_METRICS)
        & std_df["year_valid"].astype(bool)
        & std_df["value_valid"].astype(bool)
    ].copy()
    core_df["core_preview_status"] = core_df["needs_manual_review"].map(lambda x: "REVIEW_REQUIRED" if bool(x) else "SAFE_PREVIEW")

    eps_df = full_df[
        full_df["normalized_metric_name"].map(lambda x: "EPS" in _compact(x) or "每股收益" in _norm(x))
    ].copy()
    eps_detected_count = int(len(eps_df))
    bad_eps_ratio_count = int(eps_df["inferred_unit"].map(_norm).isin({"ratio", "%"}).sum()) if not eps_df.empty else 0
    eps_unit_good = bool(bad_eps_ratio_count == 0)

    total_stage7a_clean_wide_rows = int(pdf_result_df["stage7a_clean_wide_row_count"].sum()) if not pdf_result_df.empty else 0
    total_stage7b_full_rows = int(pdf_result_df["stage7b_full_structured_row_count"].sum()) if not pdf_result_df.empty else 0
    full_structured_gain = int(total_stage7b_full_rows - total_stage7a_clean_wide_rows)

    after = _snapshot_guard()
    production_files_modified = not (
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_scope_rules"] != after["formal_scope_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery_check = _run_delivery_check()
    overall_status = _norm(delivery_check.get("overall_status"))

    # Acceptance checks
    pdf_gain_ge_3 = int((pdf_result_df["stage7b_full_structured_row_count"] > pdf_result_df["stage7a_clean_wide_row_count"]).sum()) >= 3
    has_statement_detection = bool(
        pdf_result_df["income_statement_detected"].astype(bool).any()
        or pdf_result_df["balance_sheet_detected"].astype(bool).any()
        or pdf_result_df["cash_flow_statement_detected"].astype(bool).any()
    )
    has_fin_ratio = bool(pdf_result_df["financial_ratios_detected"].astype(bool).any())

    ready_for_stage7c = bool(
        pdf_gain_ge_3
        and has_statement_detection
        and has_fin_ratio
        and eps_unit_good
        and not production_files_modified
        and not official_02b_modified
        and not formal_rules_modified
        and not standardizer_modified
        and not release_package_modified
        and overall_status == "PASS"
    )

    summary = {
        "stage": "stage7b_full_structured_table_block_segmentation",
        "mode": "sandbox_only",
        "based_on_stage6c_commit": "9fa3bafbd2ff869b119a03f14be1471710813f8d",
        "input_pdf_count": 5,
        "stage7a_summary_file": str(STAGE7A_SUMMARY),
        "stage7a_inventory_file": str(STAGE7A_INVENTORY),
        "full_structured_table_generated": bool(not full_df.empty),
        "standardized_structured_table_generated": bool(not std_df.empty),
        "core_metrics_preview_generated": bool(core_df is not None),
        "production_files_modified": bool(production_files_modified),
        "official_02b_modified": bool(official_02b_modified),
        "formal_rules_modified": bool(formal_rules_modified),
        "standardizer_modified": bool(standardizer_modified),
        "release_package_modified": bool(release_package_modified),
        "check_delivery_state_overall_status": overall_status,
        "total_stage7a_clean_wide_rows": int(total_stage7a_clean_wide_rows),
        "total_stage7b_full_structured_rows": int(total_stage7b_full_rows),
        "full_structured_gain": int(full_structured_gain),
        "pdf_results": pdf_results,
        "eps_check": {
            "eps_detected_count": int(eps_detected_count),
            "eps_unit_all_normalized_or_recommended": bool(eps_unit_good),
            "bad_eps_ratio_count": int(bad_eps_ratio_count),
        },
        "blocker_count": int(0 if ready_for_stage7c else 1),
        "ready_for_stage7c_pipeline_refactor": bool(ready_for_stage7c),
    }

    # Save outputs
    _write_excel(
        OUT_INVENTORY,
        {
            "per_pdf_inventory": pdf_result_df,
            "table_blocks": blocks_df,
        },
    )
    _write_excel(
        OUT_FULL_TABLE,
        {
            "full_structured_table": full_df,
            "table_blocks": blocks_df,
            "parse_debug": parse_debug_df,
        },
    )
    _write_excel(
        OUT_STD_TABLE,
        {
            "standardized_structured_table": std_df,
            "unmapped_retained": std_df[std_df["mapping_status"].map(_norm) != "MAPPED"].copy(),
        },
    )
    _write_excel(
        OUT_CORE_PREVIEW,
        {
            "core_metrics_preview": core_df,
            "eps_rows": eps_df,
        },
    )

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    stmt_set = sorted({s for one in pdf_results for s in one.get("detected_statement_types", [])})
    md_lines = [
        "# Stage 7B Full Structured Table Block Segmentation (Sandbox)",
        "",
        "## 1) 背景",
        "- Stage 7A 证明 parse/raw 可跑通，但 clean wide 对复杂多面板研报表格保留不足。",
        "- 现阶段问题核心是缺少 full_structured_table 分层，而不是继续向 06 收敛。",
        "",
        "## 2) 本轮目标",
        "- 在 sandbox 中新增 full_structured_table 架构层，保留更多财务表行。",
        "- 保留 mapping miss 行，不因未标准化而丢弃。",
        "- core_metrics_06 仅做 preview，不写生产 06。",
        "",
        "## 3) 每份 PDF 对比（Stage7A vs Stage7B）",
    ]
    for _, r in pdf_result_df.iterrows():
        md_lines.append(
            f"- {r['source_pdf']}: clean_wide={int(r['stage7a_clean_wide_row_count'])}, full_structured={int(r['stage7b_full_structured_row_count'])}, gain={int(r['full_structured_gain'])}, blocks={int(r['detected_block_count'])}, status={r['status']}"
        )
    md_lines.extend(
        [
            "",
            "## 4) 检测到的表块类型/语义",
            f"- detected_statement_types: {', '.join(stmt_set) if stmt_set else 'N/A'}",
            "",
            "## 5) 仍未完全解析的情况",
            "- 复杂跨栏/跨行合并表仍会出现 metric 缺失或单元格语义歧义，已落入 parse_debug。",
            "- 对非年份列或段落嵌入型指标采用保守提取策略，避免误写年份值。",
            "",
            "## 6) 为什么 clean wide 不能代表全量结构化表",
            "- clean wide 偏向核心指标和审阅友好格式，会提前过滤大量未映射/单位不确定行。",
            "- full_structured_table 需要优先保留原始财务证据行，再分层进入标准化与核心层。",
            "",
            "## 7) 分层建议",
            "- raw_tables -> table_blocks -> full_structured_table -> standardized_structured_table -> core_metrics_preview/06。",
            "- full_structured_table 与 core_metrics_06 必须解耦，避免早删导致不可追溯。",
            "",
            "## 8) Stage 7C 建议",
            "- 建议将上述分层固化到统一 pipeline，先做保留率，再做标准化命中率优化。",
            "",
            "## 9) 安全检查",
            f"- production_files_modified: {production_files_modified}",
            f"- official_02b_modified: {official_02b_modified}",
            f"- formal_rules_modified: {formal_rules_modified}",
            f"- standardizer_modified: {standardizer_modified}",
            f"- release_package_modified: {release_package_modified}",
            f"- check_delivery_state_overall_status: {overall_status}",
            f"- ready_for_stage7c_pipeline_refactor: {ready_for_stage7c}",
        ]
    )
    OUT_REPORT.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"stage7b_summary_json: {OUT_SUMMARY}")
    print(f"stage7b_report_md: {OUT_REPORT}")
    print(f"stage7b_ready_for_stage7c_pipeline_refactor: {ready_for_stage7c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
