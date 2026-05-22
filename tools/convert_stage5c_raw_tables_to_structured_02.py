import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
STAGE5B_DIR = BASE_DIR / "output" / "stage5b_table_extraction_restore"
OUT_DIR = BASE_DIR / "output" / "stage5c_raw_tables_to_structured_02"

INPUT_RAW_XLSX = STAGE5B_DIR / "raw_tables.xlsx"
INPUT_RAW_JSON = STAGE5B_DIR / "raw_tables.json"
INPUT_STAGE5B_SUMMARY = STAGE5B_DIR / "129_stage5b_table_extraction_restore_summary.json"

OUT_STRUCTURED_XLSX = OUT_DIR / "130_stage5c_structured_02_sandbox.xlsx"
OUT_REPORT_XLSX = OUT_DIR / "130_stage5c_raw_to_02_conversion_report.xlsx"
OUT_REPORT_MD = OUT_DIR / "130_stage5c_raw_to_02_conversion_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "131_stage5c_raw_to_02_summary.json"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_PATH = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"

PARSE_STATUS = {
    "STRUCTURED_OK",
    "MISSING_METRIC_NAME",
    "MISSING_YEAR",
    "MISSING_VALUE",
    "MISSING_UNIT",
    "AMBIGUOUS_ROW",
    "HEADER_ROW_SKIPPED",
    "TOTAL_ROW_SKIPPED",
    "NON_FINANCIAL_ROW_SKIPPED",
    "PARSE_FAILED",
}

PARSE_ISSUE_TYPE = {
    "NONE",
    "RAW_TABLE_SCHEMA_MISMATCH",
    "HEADER_DETECTION_FAILED",
    "YEAR_DETECTION_FAILED",
    "VALUE_PARSE_FAILED",
    "UNIT_DETECTION_FAILED",
    "METRIC_NAME_EMPTY",
    "AMBIGUOUS_FINANCIAL_ROW",
    "NON_FINANCIAL_CONTENT",
    "UNKNOWN",
}

YEAR_RE = re.compile(r"(20\d{2}(?:[A-Za-z])?)")
NUM_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")

FIN_KEYWORDS = [
    "营业收入",
    "归母净利润",
    "归属于母公司股东的净利润",
    "毛利率",
    "ROE",
    "每股收益",
    "EPS",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "净利润",
    "收入",
]

NON_FINANCIAL_PATTERNS = [
    "证券研究报告",
    "请务必阅读正文之后",
    "分析师",
    "联系人",
    "评级",
    "风险提示",
    "投资要点",
    "公司研究",
    "资料来源",
    "免责声明",
]

TOTAL_PATTERNS = ["合计", "总计", "小计", "汇总", "合并", "总额"]

STRUCTURED_COLUMNS = [
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


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


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
        "formal_scope_rules": _sha256(FORMAL_SCOPE_RULES_PATH),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    return json.loads(text)


def _parse_year(text: str) -> str:
    m = YEAR_RE.search(_norm(text))
    if not m:
        return ""
    return m.group(1).upper()


def _parse_numeric(text: str) -> str:
    t = _norm(text).replace("，", ",")
    m = NUM_RE.search(t)
    if not m:
        return ""
    return m.group(0).replace(",", "")


def _is_numeric_like(text: str) -> bool:
    t = _norm(text)
    if not t:
        return False
    return bool(NUM_RE.fullmatch(t.replace(",", "").replace("%", "")))


def _is_non_financial_text(text: str) -> bool:
    t = _norm(text)
    if not t:
        return False
    return any(k in t for k in NON_FINANCIAL_PATTERNS)


def _is_total_row(label: str) -> bool:
    t = _norm(label)
    if not t:
        return False
    return any(k in t for k in TOTAL_PATTERNS)


def _contains_financial_keyword(text: str) -> bool:
    t = _norm(text).upper()
    return any(k.upper() in t for k in FIN_KEYWORDS)


def _detect_statement_type(table_text: str) -> str:
    t = _norm(table_text)
    if "利润表" in t or "损益" in t:
        return "利润表"
    if "资产负债" in t:
        return "资产负债表"
    if "现金流" in t:
        return "现金流量表"
    if "估值" in t or "PE" in t or "PB" in t:
        return "估值指标表"
    return ""


def _detect_unit(label: str, value_cell: str, row_text: str, table_text: str) -> str:
    joined = " | ".join([_norm(label), _norm(value_cell), _norm(row_text), _norm(table_text)])
    if "%" in joined or "毛利率" in joined or "ROE" in joined.upper():
        return "%"
    if "亿元" in joined:
        return "亿元"
    if "百万元" in joined:
        return "百万元"
    if "万元" in joined:
        return "万元"
    if "千元" in joined:
        return "千元"
    if "元" in joined:
        return "元"
    if "每股" in joined or "EPS" in joined.upper():
        return "元/股"
    if "P/E" in joined.upper() or "P/B" in joined.upper() or "EV/EBITDA" in joined.upper():
        return "倍"
    return ""


def _build_row_record(
    *,
    asset_package: str,
    source_pdf: str,
    page: str,
    table_id: str,
    metric: str,
    year: str,
    value: str,
    unit: str,
    statement_type: str,
    extraction_method: str,
    row_index: int,
    col_index: int,
    parse_status: str,
    issue_type: str,
    issue_reason: str,
) -> Dict[str, Any]:
    if parse_status not in PARSE_STATUS:
        parse_status = "PARSE_FAILED"
    if issue_type not in PARSE_ISSUE_TYPE:
        issue_type = "UNKNOWN"
    row_trace_id = f"{table_id}|r{row_index}|c{col_index}"
    return {
        "asset_package": asset_package,
        "source_pdf": source_pdf,
        "source_page": page,
        "source_table_id": table_id,
        "raw_metric_name": metric,
        "year": year,
        "value": value,
        "unit": unit,
        "statement_type": statement_type,
        "source_reference": f"{table_id}:r{row_index}:c{col_index}",
        "extraction_method": extraction_method,
        "row_trace_id": row_trace_id,
        "parse_status": parse_status,
        "parse_issue_type": issue_type,
        "parse_issue_reason": issue_reason,
    }


def _load_raw_tables(path_xlsx: Path, path_json: Path) -> pd.DataFrame:
    if path_xlsx.exists():
        df = pd.read_excel(path_xlsx, sheet_name="raw_tables")
        return df
    if path_json.exists():
        data = json.loads(path_json.read_text(encoding="utf-8"))
        return pd.DataFrame(data)
    raise FileNotFoundError(f"Missing raw tables input: {path_xlsx} and {path_json}")


def _schema_mismatch_records(source_pdf: str, reason: str) -> pd.DataFrame:
    rec = _build_row_record(
        asset_package=Path(source_pdf).stem + "_stage5c",
        source_pdf=source_pdf,
        page="",
        table_id="",
        metric="",
        year="",
        value="",
        unit="",
        statement_type="",
        extraction_method="",
        row_index=0,
        col_index=0,
        parse_status="PARSE_FAILED",
        issue_type="RAW_TABLE_SCHEMA_MISMATCH",
        issue_reason=reason,
    )
    return pd.DataFrame([rec], columns=STRUCTURED_COLUMNS)


def _table_context_text(table_cells: pd.DataFrame) -> str:
    head = table_cells.sort_values(["row_index", "col_index"]).head(160)
    return " | ".join([_norm(x) for x in head["cell_text"].tolist() if _norm(x)])


def _detect_header_rows_and_year_map(table_cells: pd.DataFrame) -> Tuple[List[int], Dict[int, str]]:
    header_rows: List[int] = []
    col_year_map: Dict[int, str] = {}
    by_row = table_cells.groupby("row_index", sort=True)
    for row_idx, g in by_row:
        if row_idx > 8:
            break
        years = []
        for _, r in g.iterrows():
            y = _parse_year(r.get("cell_text"))
            if y:
                years.append((int(r.get("col_index")), y))
        unique_years = sorted({y for _, y in years})
        if len(unique_years) >= 2:
            header_rows.append(int(row_idx))
            for c, y in years:
                if c not in col_year_map:
                    col_year_map[c] = y
    return header_rows, col_year_map


def _choose_metric_label(row_cells: List[Tuple[int, str]]) -> str:
    for _, txt in row_cells:
        t = _norm(txt)
        if not t:
            continue
        if _is_numeric_like(t):
            continue
        if YEAR_RE.fullmatch(t):
            continue
        return t
    return ""


def _summarize_status_count(df: pd.DataFrame, status: str) -> int:
    if df.empty:
        return 0
    return int((df["parse_status"] == status).sum())


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5C raw tables -> sandbox structured 02 converter.")
    parser.add_argument("--raw-xlsx", default=str(INPUT_RAW_XLSX), help="Stage5B raw tables xlsx")
    parser.add_argument("--raw-json", default=str(INPUT_RAW_JSON), help="Stage5B raw tables json")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_xlsx = Path(args.raw_xlsx)
    raw_json = Path(args.raw_json)

    before = _snapshot_hashes()

    raw_df = _load_raw_tables(raw_xlsx, raw_json)
    raw_df = raw_df.fillna("")
    required_raw_cols = [
        "table_id",
        "page",
        "row_index",
        "col_index",
        "cell_text",
        "extractor_name",
        "source_pdf",
    ]
    missing_raw_cols = [c for c in required_raw_cols if c not in raw_df.columns]

    input_raw_table_count = int(raw_df["table_id"].map(_norm).replace("", pd.NA).dropna().nunique()) if "table_id" in raw_df.columns else 0
    input_raw_table_total_cell_count = int(len(raw_df))
    input_raw_table_total_row_count = 0
    if {"table_id", "row_index"}.issubset(set(raw_df.columns)):
        row_max = raw_df.groupby("table_id")["row_index"].max()
        input_raw_table_total_row_count = int(pd.to_numeric(row_max, errors="coerce").fillna(0).sum())

    stage5b_summary = {}
    if INPUT_STAGE5B_SUMMARY.exists():
        stage5b_summary = json.loads(INPUT_STAGE5B_SUMMARY.read_text(encoding="utf-8"))

    structured_records: List[Dict[str, Any]] = []
    table_diag_rows: List[Dict[str, Any]] = []

    source_pdf = _norm(raw_df["source_pdf"].iloc[0]) if (not raw_df.empty and "source_pdf" in raw_df.columns) else ""
    asset_package = (Path(source_pdf).stem if source_pdf else "unknown_pdf") + "_stage5c"

    if missing_raw_cols:
        structured_df = _schema_mismatch_records(source_pdf, f"missing columns: {','.join(missing_raw_cols)}")
        table_diag_rows.append(
            {
                "table_id": "",
                "source_page": "",
                "header_row_count": 0,
                "year_column_count": 0,
                "row_count": 0,
                "cell_count": 0,
                "financial_keyword_row_count": 0,
                "parse_note": "raw_table_schema_mismatch",
            }
        )
    else:
        raw_df["row_index"] = pd.to_numeric(raw_df["row_index"], errors="coerce").fillna(0).astype(int)
        raw_df["col_index"] = pd.to_numeric(raw_df["col_index"], errors="coerce").fillna(0).astype(int)

        grouped = raw_df.groupby("table_id", sort=True)
        for table_id, tdf in grouped:
            tdf = tdf.sort_values(["row_index", "col_index"]).copy()
            page = _norm(tdf["page"].iloc[0]) if "page" in tdf.columns else ""
            extractor_name = _norm(tdf["extractor_name"].iloc[0]) if "extractor_name" in tdf.columns else ""
            table_text = _table_context_text(tdf)
            statement_type = _detect_statement_type(table_text)
            header_rows, col_year_map = _detect_header_rows_and_year_map(tdf)
            has_year_map = len(col_year_map) > 0
            financial_keyword_row_count = 0

            rows_group = tdf.groupby("row_index", sort=True)
            for row_idx, rdf in rows_group:
                row_cells = [(int(r["col_index"]), _norm(r["cell_text"])) for _, r in rdf.iterrows()]
                row_cells = sorted(row_cells, key=lambda x: x[0])
                row_text = " | ".join([txt for _, txt in row_cells if txt])
                label = _choose_metric_label(row_cells)
                numeric_cells: List[Tuple[int, str]] = []
                for col_idx, txt in row_cells:
                    val = _parse_numeric(txt)
                    if val:
                        numeric_cells.append((col_idx, val))

                if _contains_financial_keyword(row_text):
                    financial_keyword_row_count += 1

                if int(row_idx) in header_rows:
                    structured_records.append(
                        _build_row_record(
                            asset_package=asset_package,
                            source_pdf=source_pdf,
                            page=page,
                            table_id=_norm(table_id),
                            metric=label,
                            year="",
                            value="",
                            unit="",
                            statement_type=statement_type,
                            extraction_method=extractor_name,
                            row_index=int(row_idx),
                            col_index=0,
                            parse_status="HEADER_ROW_SKIPPED",
                            issue_type="NONE",
                            issue_reason="row identified as header row with year columns",
                        )
                    )
                    continue

                if not row_text:
                    structured_records.append(
                        _build_row_record(
                            asset_package=asset_package,
                            source_pdf=source_pdf,
                            page=page,
                            table_id=_norm(table_id),
                            metric="",
                            year="",
                            value="",
                            unit="",
                            statement_type=statement_type,
                            extraction_method=extractor_name,
                            row_index=int(row_idx),
                            col_index=0,
                            parse_status="NON_FINANCIAL_ROW_SKIPPED",
                            issue_type="NON_FINANCIAL_CONTENT",
                            issue_reason="empty row",
                        )
                    )
                    continue

                if _is_total_row(label):
                    structured_records.append(
                        _build_row_record(
                            asset_package=asset_package,
                            source_pdf=source_pdf,
                            page=page,
                            table_id=_norm(table_id),
                            metric=label,
                            year="",
                            value="",
                            unit="",
                            statement_type=statement_type,
                            extraction_method=extractor_name,
                            row_index=int(row_idx),
                            col_index=0,
                            parse_status="TOTAL_ROW_SKIPPED",
                            issue_type="NON_FINANCIAL_CONTENT",
                            issue_reason="total/subtotal row skipped",
                        )
                    )
                    continue

                if not label:
                    status = "MISSING_METRIC_NAME" if numeric_cells else "NON_FINANCIAL_ROW_SKIPPED"
                    issue = "METRIC_NAME_EMPTY" if numeric_cells else "NON_FINANCIAL_CONTENT"
                    reason = "numeric cells found but metric label is empty" if numeric_cells else "row without metric and numeric value"
                    structured_records.append(
                        _build_row_record(
                            asset_package=asset_package,
                            source_pdf=source_pdf,
                            page=page,
                            table_id=_norm(table_id),
                            metric="",
                            year="",
                            value="",
                            unit="",
                            statement_type=statement_type,
                            extraction_method=extractor_name,
                            row_index=int(row_idx),
                            col_index=0,
                            parse_status=status,
                            issue_type=issue,
                            issue_reason=reason,
                        )
                    )
                    continue

                if _is_non_financial_text(label) and not numeric_cells:
                    structured_records.append(
                        _build_row_record(
                            asset_package=asset_package,
                            source_pdf=source_pdf,
                            page=page,
                            table_id=_norm(table_id),
                            metric=label,
                            year="",
                            value="",
                            unit="",
                            statement_type=statement_type,
                            extraction_method=extractor_name,
                            row_index=int(row_idx),
                            col_index=0,
                            parse_status="NON_FINANCIAL_ROW_SKIPPED",
                            issue_type="NON_FINANCIAL_CONTENT",
                            issue_reason="non-financial text row skipped",
                        )
                    )
                    continue

                if not numeric_cells:
                    structured_records.append(
                        _build_row_record(
                            asset_package=asset_package,
                            source_pdf=source_pdf,
                            page=page,
                            table_id=_norm(table_id),
                            metric=label,
                            year="",
                            value="",
                            unit="",
                            statement_type=statement_type,
                            extraction_method=extractor_name,
                            row_index=int(row_idx),
                            col_index=0,
                            parse_status="MISSING_VALUE",
                            issue_type="VALUE_PARSE_FAILED",
                            issue_reason="no numeric value detected from row",
                        )
                    )
                    continue

                row_level_years = [y for y in [_parse_year(txt) for _, txt in row_cells] if y]

                for col_idx, val in numeric_cells:
                    year = _norm(col_year_map.get(col_idx, ""))
                    if not year and len(row_level_years) == 1:
                        year = row_level_years[0]
                    unit = _detect_unit(label, val, row_text, table_text)

                    parse_status = "STRUCTURED_OK"
                    parse_issue_type = "NONE"
                    parse_issue_reason = "parsed from raw table row"

                    if not has_year_map:
                        parse_status = "AMBIGUOUS_ROW"
                        parse_issue_type = "HEADER_DETECTION_FAILED"
                        parse_issue_reason = "year header not detected for this table"
                    elif not year:
                        if len(numeric_cells) > 1:
                            parse_status = "AMBIGUOUS_ROW"
                            parse_issue_type = "AMBIGUOUS_FINANCIAL_ROW"
                            parse_issue_reason = "multiple numeric cells but no year mapped"
                        else:
                            parse_status = "MISSING_YEAR"
                            parse_issue_type = "YEAR_DETECTION_FAILED"
                            parse_issue_reason = "year mapping missing for numeric cell"
                    elif not val:
                        parse_status = "MISSING_VALUE"
                        parse_issue_type = "VALUE_PARSE_FAILED"
                        parse_issue_reason = "value parse failed"
                    elif not unit:
                        parse_status = "MISSING_UNIT"
                        parse_issue_type = "UNIT_DETECTION_FAILED"
                        parse_issue_reason = "unit not detected"

                    structured_records.append(
                        _build_row_record(
                            asset_package=asset_package,
                            source_pdf=source_pdf,
                            page=page,
                            table_id=_norm(table_id),
                            metric=label,
                            year=year,
                            value=val,
                            unit=unit,
                            statement_type=statement_type,
                            extraction_method=extractor_name,
                            row_index=int(row_idx),
                            col_index=int(col_idx),
                            parse_status=parse_status,
                            issue_type=parse_issue_type,
                            issue_reason=parse_issue_reason,
                        )
                    )

            table_diag_rows.append(
                {
                    "table_id": _norm(table_id),
                    "source_page": page,
                    "header_row_count": len(header_rows),
                    "year_column_count": len(col_year_map),
                    "row_count": int(tdf["row_index"].max()) if not tdf.empty else 0,
                    "cell_count": int(len(tdf)),
                    "financial_keyword_row_count": int(financial_keyword_row_count),
                    "parse_note": "ok",
                }
            )

        structured_df = pd.DataFrame(structured_records, columns=STRUCTURED_COLUMNS)
        if structured_df.empty:
            structured_df = pd.DataFrame(columns=STRUCTURED_COLUMNS)

    if not structured_df.empty:
        structured_df["source_page"] = structured_df["source_page"].map(_norm)
        structured_df["parse_status"] = structured_df["parse_status"].map(
            lambda x: x if _norm(x) in PARSE_STATUS else "PARSE_FAILED"
        )
        structured_df["parse_issue_type"] = structured_df["parse_issue_type"].map(
            lambda x: x if _norm(x) in PARSE_ISSUE_TYPE else "UNKNOWN"
        )

    structured_ok_count = _summarize_status_count(structured_df, "STRUCTURED_OK")
    missing_metric_name_count = _summarize_status_count(structured_df, "MISSING_METRIC_NAME")
    missing_year_count = _summarize_status_count(structured_df, "MISSING_YEAR")
    missing_value_count = _summarize_status_count(structured_df, "MISSING_VALUE")
    missing_unit_count = _summarize_status_count(structured_df, "MISSING_UNIT")
    ambiguous_row_count = _summarize_status_count(structured_df, "AMBIGUOUS_ROW")
    header_row_skipped_count = _summarize_status_count(structured_df, "HEADER_ROW_SKIPPED")
    total_row_skipped_count = _summarize_status_count(structured_df, "TOTAL_ROW_SKIPPED")
    non_financial_row_skipped_count = _summarize_status_count(structured_df, "NON_FINANCIAL_ROW_SKIPPED")
    parse_failed_count = _summarize_status_count(structured_df, "PARSE_FAILED")

    year_detected_count = int((structured_df["year"].map(_norm) != "").sum()) if not structured_df.empty else 0
    value_detected_count = int((structured_df["value"].map(_norm) != "").sum()) if not structured_df.empty else 0
    unit_detected_count = int((structured_df["unit"].map(_norm) != "").sum()) if not structured_df.empty else 0
    financial_keyword_row_count = (
        int(structured_df["raw_metric_name"].map(_contains_financial_keyword).sum()) if not structured_df.empty else 0
    )
    ready_for_stage5d_standardization_count = int(
        (
            (structured_df["parse_status"] == "STRUCTURED_OK")
            & (structured_df["raw_metric_name"].map(_norm) != "")
            & (structured_df["year"].map(_norm) != "")
            & (structured_df["value"].map(_norm) != "")
        ).sum()
    ) if not structured_df.empty else 0

    before_after = _snapshot_hashes()
    production_files_unchanged = bool(
        before["01"] == before_after["01"]
        and before["02"] == before_after["02"]
        and before["02A"] == before_after["02A"]
        and before["05"] == before_after["05"]
        and before["06"] == before_after["06"]
    )
    official_02B_unchanged = bool(before["02B"] == before_after["02B"])
    formal_scope_rules_unchanged = bool(before["formal_scope_rules"] == before_after["formal_scope_rules"])

    summary = {
        "input_raw_table_count": int(input_raw_table_count),
        "input_raw_table_total_row_count": int(input_raw_table_total_row_count),
        "input_raw_table_total_cell_count": int(input_raw_table_total_cell_count),
        "structured_02_sandbox_row_count": int(len(structured_df)),
        "structured_ok_count": int(structured_ok_count),
        "missing_metric_name_count": int(missing_metric_name_count),
        "missing_year_count": int(missing_year_count),
        "missing_value_count": int(missing_value_count),
        "missing_unit_count": int(missing_unit_count),
        "ambiguous_row_count": int(ambiguous_row_count),
        "header_row_skipped_count": int(header_row_skipped_count),
        "total_row_skipped_count": int(total_row_skipped_count),
        "non_financial_row_skipped_count": int(non_financial_row_skipped_count),
        "parse_failed_count": int(parse_failed_count),
        "year_detected_count": int(year_detected_count),
        "value_detected_count": int(value_detected_count),
        "unit_detected_count": int(unit_detected_count),
        "financial_keyword_row_count": int(financial_keyword_row_count),
        "ready_for_stage5d_standardization_count": int(ready_for_stage5d_standardization_count),
        "raw_table_to_02_conversion_pass": False,
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
    }

    summary["raw_table_to_02_conversion_pass"] = bool(
        summary["input_raw_table_count"] == 5
        and summary["input_raw_table_total_row_count"] == 203
        and summary["structured_02_sandbox_row_count"] > 0
        and summary["parse_failed_count"] != summary["structured_02_sandbox_row_count"]
        and summary["ready_for_stage5d_standardization_count"] > 0
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_scope_rules_unchanged"]
        and summary["ai_called"] is False
        and summary["internet_called"] is False
        and summary["factory_core_called"] is False
        and summary["ocr_called"] is False
    )

    issue_breakdown_df = (
        structured_df.groupby(["parse_status", "parse_issue_type"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .sort_values(["row_count", "parse_status"], ascending=[False, True])
        if not structured_df.empty
        else pd.DataFrame(columns=["parse_status", "parse_issue_type", "row_count"])
    )
    table_diag_df = pd.DataFrame(table_diag_rows)
    summary_df = pd.DataFrame([summary])
    stage5b_ref_df = pd.DataFrame([stage5b_summary]) if stage5b_summary else pd.DataFrame()

    _write_excel(
        OUT_STRUCTURED_XLSX,
        {
            "structured_02_sandbox": structured_df,
        },
    )

    _write_excel(
        OUT_REPORT_XLSX,
        {
            "summary": summary_df,
            "parse_status_breakdown": issue_breakdown_df,
            "table_diagnostics": table_diag_df,
            "structured_02_sample": structured_df.head(500),
            "stage5b_summary_ref": stage5b_ref_df,
        },
    )

    md_lines = [
        "# Stage5C Raw Tables To Structured 02 (Sandbox)",
        "",
        f"- input_raw_table_count: {summary['input_raw_table_count']}",
        f"- input_raw_table_total_row_count: {summary['input_raw_table_total_row_count']}",
        f"- input_raw_table_total_cell_count: {summary['input_raw_table_total_cell_count']}",
        f"- structured_02_sandbox_row_count: {summary['structured_02_sandbox_row_count']}",
        f"- structured_ok_count: {summary['structured_ok_count']}",
        f"- missing_metric_name_count: {summary['missing_metric_name_count']}",
        f"- missing_year_count: {summary['missing_year_count']}",
        f"- missing_value_count: {summary['missing_value_count']}",
        f"- missing_unit_count: {summary['missing_unit_count']}",
        f"- ambiguous_row_count: {summary['ambiguous_row_count']}",
        f"- header_row_skipped_count: {summary['header_row_skipped_count']}",
        f"- total_row_skipped_count: {summary['total_row_skipped_count']}",
        f"- non_financial_row_skipped_count: {summary['non_financial_row_skipped_count']}",
        f"- parse_failed_count: {summary['parse_failed_count']}",
        f"- year_detected_count: {summary['year_detected_count']}",
        f"- value_detected_count: {summary['value_detected_count']}",
        f"- unit_detected_count: {summary['unit_detected_count']}",
        f"- financial_keyword_row_count: {summary['financial_keyword_row_count']}",
        f"- ready_for_stage5d_standardization_count: {summary['ready_for_stage5d_standardization_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- raw_table_to_02_conversion_pass: {summary['raw_table_to_02_conversion_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"structured_02_sandbox_xlsx: {OUT_STRUCTURED_XLSX}")
    print(f"conversion_report_xlsx: {OUT_REPORT_XLSX}")
    print(f"conversion_report_md: {OUT_REPORT_MD}")
    print(f"summary_json: {OUT_SUMMARY_JSON}")
    print(f"structured_02_sandbox_row_count: {summary['structured_02_sandbox_row_count']}")
    print(f"ready_for_stage5d_standardization_count: {summary['ready_for_stage5d_standardization_count']}")
    print(f"raw_table_to_02_conversion_pass: {summary['raw_table_to_02_conversion_pass']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
