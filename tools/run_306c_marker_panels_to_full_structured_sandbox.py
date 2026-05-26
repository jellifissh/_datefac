from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
IN_306A_GATE = BASE_DIR / "output" / "eval_306a_marker_table_quality_gate_and_parser_fusion_design" / "306a_marker_table_quality_gate.xlsx"
IN_306B_FIX_INDEX = BASE_DIR / "output" / "eval_306b_fix_hierarchical_panel_splitter" / "306b_fix_split_panel_index.xlsx"
IN_306B_FIX_PANELS = BASE_DIR / "output" / "eval_306b_fix_hierarchical_panel_splitter" / "306b_fix_split_panels.xlsx"
IN_306B_FIX_FAILED = BASE_DIR / "output" / "eval_306b_fix_hierarchical_panel_splitter" / "306b_fix_failed_split_candidates.xlsx"
IN_305B_INDEX = BASE_DIR / "output" / "eval_marker1b_html_table_readable_render_fix" / "305b_table_render_index.xlsx"

OUT_DIR = BASE_DIR / "output" / "eval_306c_marker_panels_to_full_structured_sandbox"
OUT_SUMMARY = OUT_DIR / "306c_summary.json"
OUT_REPORT = OUT_DIR / "306c_report.md"
OUT_FULL = OUT_DIR / "306c_marker_full_structured_table.xlsx"
OUT_HIGH = OUT_DIR / "306c_high_confidence_structured_rows.xlsx"
OUT_DIRTY = OUT_DIR / "306c_dirty_cell_audit.xlsx"
OUT_SUSPICIOUS_YEAR = OUT_DIR / "306c_suspicious_year_audit.xlsx"
OUT_MERGED_VALUE = OUT_DIR / "306c_merged_value_audit.xlsx"
OUT_BLOCKED = OUT_DIR / "306c_blocked_rows_audit.xlsx"
OUT_NO_APPLY = OUT_DIR / "306c_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

YEAR_RE = re.compile(r"(19|20)\d{2}(?:A|E)?")
NUM_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?")

STATEMENT_FROM_PANEL = {
    "balance_sheet": "balance_sheet",
    "income_statement": "income_statement",
    "cash_flow_statement": "cash_flow_statement",
    "valuation_metrics": "valuation_metrics",
    "financial_summary": "financial_summary",
    "business_assumption": "business_assumption",
}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _to_int(v: Any) -> int:
    s = _norm(v)
    if s == "":
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    used: set = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    return json.loads(txt) if txt else {"overall_status": "UNKNOWN"}


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().fillna("")
    out.columns = [_norm(c) for c in out.columns]
    for c in out.columns:
        out[c] = out[c].map(_norm)
    return out


def _infer_panel_label_from_306a_row(r: pd.Series) -> str:
    if _to_bool(r.get("financial_summary_table", False)) or _to_bool(r.get("high_value_financial_forecast_table", False)):
        return "financial_summary"
    if _to_bool(r.get("business_assumption_table", False)):
        return "business_assumption"
    bs = _to_bool(r.get("balance_sheet_panel", False))
    inc = _to_bool(r.get("income_statement_panel", False))
    cf = _to_bool(r.get("cash_flow_panel", False))
    val = _to_bool(r.get("valuation_panel", False))
    if bs and not (inc or cf or val):
        return "balance_sheet"
    if inc and not (bs or cf or val):
        return "income_statement"
    if cf and not (bs or inc or val):
        return "cash_flow_statement"
    if val and not (bs or inc or cf):
        return "valuation_metrics"
    if bs:
        return "balance_sheet"
    if inc:
        return "income_statement"
    if cf:
        return "cash_flow_statement"
    if val:
        return "valuation_metrics"
    return "financial_summary"


def _normalize_metric_name(raw_metric_name: str) -> str:
    t = _norm(raw_metric_name).lower()
    if t == "":
        return "unknown_metric"
    if ("营业收入" in t) or ("revenue" in t):
        return "revenue"
    if ("归母净利润" in t) or ("归属于母公司净利润" in t) or ("归属于母公司股东的净利润" in t):
        return "attributable_net_profit"
    if ("净利润" in t):
        return "net_profit"
    if ("资产总计" in t):
        return "total_assets"
    if ("负债合计" in t):
        return "total_liabilities"
    if ("经营活动现金流" in t) or ("经营现金流" in t):
        return "operating_cash_flow"
    if ("每股收益" in t) or ("eps" in t):
        return "eps"
    if ("roe" in t) or ("净资产收益率" in t):
        return "roe"
    if ("毛利率" in t) or ("gross margin" in t):
        return "gross_margin"
    if ("市盈率" in t) or ("p/e" in t) or (re.search(r"\bpe\b", t) is not None):
        return "pe"
    if ("市净率" in t) or ("p/b" in t) or (re.search(r"\bpb\b", t) is not None):
        return "pb"
    if ("ev/ebitda" in t):
        return "ev_ebitda"
    if ("财务费用" in t):
        return "financial_expense"
    return "other_metric"


def _infer_unit(raw_metric_name: str, value_raw: str) -> str:
    m = _norm(raw_metric_name)
    v = _norm(value_raw)
    if "%" in m or "%" in v:
        return "percent"
    if "百万元" in m:
        return "million_cny"
    if "亿元" in m:
        return "hundred_million_cny"
    if "元" in m:
        return "cny"
    return "unknown"


def _extract_numeric(value_raw: str) -> Optional[float]:
    s = _norm(value_raw).replace(",", "")
    if s == "":
        return None
    # Parentheses as negative.
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    m = NUM_RE.search(s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def _is_merged_value_cell(value_raw: str) -> bool:
    s = _norm(value_raw)
    if s == "":
        return False
    nums = NUM_RE.findall(s)
    if len(nums) >= 2 and " " in s:
        return True
    return False


def _is_polluted_metric(metric: str) -> bool:
    return re.match(r"^\d+\s+\S+", _norm(metric)) is not None


def _derive_year_map(df: pd.DataFrame) -> Dict[int, int]:
    year_map: Dict[int, int] = {}
    # First: from column headers.
    for j, c in enumerate(df.columns):
        c_txt = _norm(c)
        m = YEAR_RE.search(c_txt)
        if m:
            year_map[j] = int(m.group(0)[:4])
    # Second: from top rows.
    if len(year_map) < 2:
        scan_rows = min(3, len(df))
        for j in range(len(df.columns)):
            if j in year_map:
                continue
            y = None
            for i in range(scan_rows):
                txt = _norm(df.iat[i, j])
                m = YEAR_RE.search(txt)
                if m:
                    y = int(m.group(0)[:4])
                    break
            if y is not None:
                year_map[j] = y
    return year_map


def _row_is_headerish(metric: str) -> bool:
    t = _norm(metric)
    if t == "":
        return False
    for kw in ["资产负债表", "利润表", "现金流量表", "关键财务与估值指标", "盈利预测和财务指标", "财务预测", "合计"]:
        if kw == t:
            return True
    return False


def _convert_table_to_rows(
    df: pd.DataFrame,
    source_pdf_name: str,
    page_number: int,
    panel_label: str,
    source_panel_id: str,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if df.empty or len(df.columns) < 2:
        return out

    df = _normalize_df(df)
    year_map = _derive_year_map(df)
    if not year_map:
        return out

    statement_type = STATEMENT_FROM_PANEL.get(panel_label, panel_label)

    for i in range(len(df)):
        raw_metric_name = _norm(df.iat[i, 0])
        if _row_is_headerish(raw_metric_name):
            continue

        # Evaluate if row has any values in mapped year columns.
        has_any_value = False
        for col_idx in sorted(year_map.keys()):
            if col_idx <= 0 or col_idx >= len(df.columns):
                continue
            if _norm(df.iat[i, col_idx]) != "":
                has_any_value = True
                break
        if not has_any_value and raw_metric_name == "":
            continue

        normalized_metric_name = _normalize_metric_name(raw_metric_name)

        for col_idx, year in sorted(year_map.items()):
            if col_idx <= 0 or col_idx >= len(df.columns):
                continue
            value_raw = _norm(df.iat[i, col_idx])
            value_num = _extract_numeric(value_raw)
            inferred_unit = _infer_unit(raw_metric_name, value_raw)

            flags: List[str] = []
            if _is_polluted_metric(raw_metric_name):
                flags.append("polluted_metric_name")
            if _is_merged_value_cell(value_raw):
                flags.append("merged_value_cell")
            if raw_metric_name == "" and value_raw != "":
                flags.append("empty_metric_name_with_value")
            if normalized_metric_name in {
                "revenue",
                "net_profit",
                "attributable_net_profit",
                "total_assets",
                "total_liabilities",
                "operating_cash_flow",
                "eps",
                "roe",
                "gross_margin",
                "pe",
                "pb",
                "ev_ebitda",
            } and value_raw == "":
                flags.append("missing_value_for_core_metric")

            out.append(
                {
                    "source_pdf_name": source_pdf_name,
                    "page_number": int(page_number),
                    "panel_label": panel_label,
                    "statement_type": statement_type,
                    "raw_metric_name": raw_metric_name,
                    "normalized_metric_name": normalized_metric_name,
                    "year": int(year),
                    "value_raw": value_raw,
                    "value": value_num,
                    "inferred_unit": inferred_unit,
                    "confidence_flags": "|".join(flags) if flags else "ok",
                    "source_panel_id": source_panel_id,
                }
            )
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306A_GATE, IN_306B_FIX_INDEX, IN_306B_FIX_PANELS, IN_306B_FIX_FAILED, IN_305B_INDEX]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306C",
                "mode": "marker_panels_to_full_structured_sandbox",
                "blocked": True,
                "blocked_reason": "missing_required_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
                "marker_rerun_executed": False,
            },
        )
        return 0

    before = _snapshot_guard()

    gate_df = pd.read_excel(IN_306A_GATE, sheet_name="quality_gate").fillna("")
    fix_idx_df = pd.read_excel(IN_306B_FIX_INDEX).fillna("")
    fix_failed_df = pd.read_excel(IN_306B_FIX_FAILED).fillna("")
    index305b_df = pd.read_excel(IN_305B_INDEX).fillna("")

    for df in [gate_df, fix_idx_df, fix_failed_df, index305b_df]:
        if "pdf_file_name" in df.columns:
            df["pdf_file_name"] = df["pdf_file_name"].map(_norm)
        if "marker_table_id" in df.columns:
            df["marker_table_id"] = df["marker_table_id"].map(_norm)
        if "page_number" in df.columns:
            df["page_number"] = df["page_number"].map(_to_int)

    # 305b sequence key for direct_structurable mapping.
    index305b_df = index305b_df.copy()
    index305b_df["table_seq"] = index305b_df.groupby("pdf_file_name").cumcount() + 1

    # Include only valid direct_structurable rows.
    direct_df = gate_df[
        (gate_df["table_classification"].map(_norm) == "direct_structurable")
        & (gate_df["render_status"].map(_norm) == "SUCCESS")
        & (gate_df["row_count"].map(_to_int) > 0)
        & (gate_df["col_count"].map(_to_int) > 0)
    ][["pdf_file_name", "marker_table_id", "page_number", "table_classification", "render_status"]].drop_duplicates()

    # Include only successful split panels from 306B-Fix.
    failed_keys = set(
        (
            _norm(r["pdf_file_name"]),
            _norm(r["marker_table_id"]),
            _to_int(r["page_number"]),
        )
        for _, r in fix_failed_df.iterrows()
    )
    panel_df = fix_idx_df[
        (~fix_idx_df["panel_sheet_name"].map(_norm).eq(""))
    ].copy()
    panel_df = panel_df[
        ~panel_df.apply(
            lambda r: (_norm(r["pdf_file_name"]), _norm(r["marker_table_id"]), _to_int(r["page_number"])) in failed_keys,
            axis=1,
        )
    ].copy()

    # Exclusion counts from 306A for summary.
    exclusion_low_value = int((gate_df["table_classification"].map(_norm) == "low_value_or_junk").sum())
    exclusion_failed_parse = int((gate_df["render_status"].map(_norm) == "FAILED_PARSE").sum())
    exclusion_context_required = int((gate_df["table_classification"].map(_norm) == "context_required").sum())
    exclusion_split_failed = int(len(fix_failed_df))

    all_rows: List[Dict[str, Any]] = []
    blocked_rows: List[Dict[str, Any]] = []

    # Process direct_structurable tables from 305B readable Excel.
    direct_processed_count = 0
    direct_missing_sheet_count = 0

    for _, d in direct_df.iterrows():
        pdf_name = _norm(d["pdf_file_name"])
        marker_table_id = _norm(d["marker_table_id"])
        page_number = _to_int(d["page_number"])

        match = index305b_df[
            (index305b_df["pdf_file_name"] == pdf_name)
            & (index305b_df["marker_table_id"] == marker_table_id)
            & (index305b_df["page_number"] == page_number)
            & (index305b_df["render_status"].map(_norm) == "SUCCESS")
            & (index305b_df["parsed_table_count"].map(_to_int) > 0)
        ]
        if match.empty:
            direct_missing_sheet_count += 1
            continue

        m = match.iloc[0]
        xlsx_path = Path(_norm(m.get("xlsx_path")))
        table_seq = _to_int(m.get("table_seq"))
        parsed_count = _to_int(m.get("parsed_table_count"))
        if not xlsx_path.exists():
            direct_missing_sheet_count += 1
            continue

        xls = pd.ExcelFile(xlsx_path)
        source_sheet = None
        for k in range(1, max(parsed_count, 1) + 1):
            nm = f"t{table_seq}_p{page_number}_{k}"
            if nm in xls.sheet_names:
                source_sheet = nm
                break
        if source_sheet is None:
            pref = [s for s in xls.sheet_names if s.startswith(f"t{table_seq}_p{page_number}_")]
            if pref:
                source_sheet = sorted(pref)[0]
        if source_sheet is None:
            direct_missing_sheet_count += 1
            continue

        df_src = _normalize_df(pd.read_excel(xlsx_path, sheet_name=source_sheet))
        panel_label = _infer_panel_label_from_306a_row(
            gate_df[
                (gate_df["pdf_file_name"] == pdf_name)
                & (gate_df["marker_table_id"] == marker_table_id)
                & (gate_df["page_number"] == page_number)
            ].iloc[0]
        )
        source_panel_id = f"direct|{pdf_name}|{marker_table_id}|p{page_number}|{source_sheet}|{panel_label}"
        rows = _convert_table_to_rows(df_src, pdf_name, page_number, panel_label, source_panel_id)
        if rows:
            all_rows.extend(rows)
            direct_processed_count += 1

    # Process successful split panels from 306B-Fix panel workbook.
    panel_processed_count = 0
    panel_missing_sheet_count = 0
    fix_panel_book = pd.ExcelFile(IN_306B_FIX_PANELS)
    for _, p in panel_df.iterrows():
        pdf_name = _norm(p["pdf_file_name"])
        marker_table_id = _norm(p["marker_table_id"])
        page_number = _to_int(p["page_number"])
        panel_label = _norm(p["panel_label"])
        panel_sheet_name = _norm(p["panel_sheet_name"])
        if panel_sheet_name == "" or panel_sheet_name not in fix_panel_book.sheet_names:
            panel_missing_sheet_count += 1
            continue
        df_src = _normalize_df(pd.read_excel(IN_306B_FIX_PANELS, sheet_name=panel_sheet_name))
        source_panel_id = f"split|{pdf_name}|{marker_table_id}|p{page_number}|{panel_sheet_name}|{panel_label}"
        rows = _convert_table_to_rows(df_src, pdf_name, page_number, panel_label, source_panel_id)
        if rows:
            all_rows.extend(rows)
            panel_processed_count += 1

    full_df = pd.DataFrame(all_rows).fillna("")
    if full_df.empty:
        full_df = pd.DataFrame(
            columns=[
                "source_pdf_name",
                "page_number",
                "panel_label",
                "statement_type",
                "raw_metric_name",
                "normalized_metric_name",
                "year",
                "value_raw",
                "value",
                "inferred_unit",
                "confidence_flags",
                "source_panel_id",
            ]
        )

    # suspicious_year guard with per-panel baseline.
    suspicious_year_rows: List[int] = []
    if not full_df.empty:
        full_df["year"] = full_df["year"].map(_to_int)
        grouped = full_df.groupby("source_panel_id")
        for sid, g in grouped:
            years = [int(y) for y in g["year"].tolist() if int(y) > 0]
            if not years:
                continue
            med = int(median(years))
            for idx, row in g.iterrows():
                y = _to_int(row["year"])
                if y == 0:
                    continue
                suspicious = False
                if y < 2022 or y > 2032:
                    suspicious = True
                if med >= 2024 and y <= 2021:
                    suspicious = True
                if suspicious:
                    suspicious_year_rows.append(idx)

    if suspicious_year_rows:
        for idx in suspicious_year_rows:
            cur = _norm(full_df.at[idx, "confidence_flags"])
            flags = [] if cur in {"", "ok"} else cur.split("|")
            if "suspicious_year" not in flags:
                flags.append("suspicious_year")
            full_df.at[idx, "confidence_flags"] = "|".join(flags) if flags else "ok"

    # Audit subsets.
    if full_df.empty:
        high_df = full_df.copy()
        dirty_df = full_df.copy()
        suspicious_df = full_df.copy()
        merged_df = full_df.copy()
        blocked_df = full_df.copy()
    else:
        high_df = full_df[
            (full_df["confidence_flags"].map(_norm) == "ok")
            & (full_df["value"].map(_norm) != "")
            & (full_df["normalized_metric_name"].map(_norm) != "other_metric")
        ].copy()
        dirty_df = full_df[full_df["confidence_flags"].map(_norm) != "ok"].copy()
        suspicious_df = full_df[full_df["confidence_flags"].map(_norm).str.contains("suspicious_year", regex=False)].copy()
        merged_df = full_df[full_df["confidence_flags"].map(_norm).str.contains("merged_value_cell", regex=False)].copy()
        blocked_df = full_df[
            full_df["confidence_flags"].map(_norm).str.contains(
                "polluted_metric_name|suspicious_year|merged_value_cell|empty_metric_name_with_value|missing_value_for_core_metric",
                regex=True,
            )
        ].copy()

    _write_excel(OUT_FULL, {"marker_full_structured": full_df})
    _write_excel(OUT_HIGH, {"high_confidence_structured_rows": high_df})
    _write_excel(OUT_DIRTY, {"dirty_cell_audit": dirty_df})
    _write_excel(OUT_SUSPICIOUS_YEAR, {"suspicious_year_audit": suspicious_df})
    _write_excel(OUT_MERGED_VALUE, {"merged_value_audit": merged_df})
    _write_excel(OUT_BLOCKED, {"blocked_rows_audit": blocked_df})

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "marker_rerun_executed": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
        },
    )

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-306C",
        "mode": "marker_panels_to_full_structured_sandbox",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "direct_structurable_target_count": int(len(direct_df)),
        "direct_structurable_processed_count": int(direct_processed_count),
        "direct_structurable_missing_sheet_count": int(direct_missing_sheet_count),
        "split_panel_target_count": int(len(panel_df)),
        "split_panel_processed_count": int(panel_processed_count),
        "split_panel_missing_sheet_count": int(panel_missing_sheet_count),
        "full_structured_row_count": int(len(full_df)),
        "high_confidence_row_count": int(len(high_df)),
        "dirty_row_count": int(len(dirty_df)),
        "suspicious_year_row_count": int(len(suspicious_df)),
        "merged_value_row_count": int(len(merged_df)),
        "blocked_row_count": int(len(blocked_df)),
        "excluded_low_value_or_junk_count": exclusion_low_value,
        "excluded_failed_parse_count": exclusion_failed_parse,
        "excluded_context_required_count": exclusion_context_required,
        "excluded_split_failed_count": exclusion_split_failed,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306C Marker Panels to Full Structured Sandbox",
        "",
        f"- direct_structurable_target_count: {summary['direct_structurable_target_count']}",
        f"- direct_structurable_processed_count: {summary['direct_structurable_processed_count']}",
        f"- split_panel_target_count: {summary['split_panel_target_count']}",
        f"- split_panel_processed_count: {summary['split_panel_processed_count']}",
        f"- full_structured_row_count: {summary['full_structured_row_count']}",
        f"- high_confidence_row_count: {summary['high_confidence_row_count']}",
        f"- dirty_row_count: {summary['dirty_row_count']}",
        f"- suspicious_year_row_count: {summary['suspicious_year_row_count']}",
        f"- merged_value_row_count: {summary['merged_value_row_count']}",
        f"- blocked_row_count: {summary['blocked_row_count']}",
        f"- excluded_low_value_or_junk_count: {summary['excluded_low_value_or_junk_count']}",
        f"- excluded_failed_parse_count: {summary['excluded_failed_parse_count']}",
        f"- excluded_context_required_count: {summary['excluded_context_required_count']}",
        f"- excluded_split_failed_count: {summary['excluded_split_failed_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306c_summary_json: {OUT_SUMMARY}")
    print(f"eval_306c_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
