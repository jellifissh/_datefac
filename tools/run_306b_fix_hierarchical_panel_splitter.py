from __future__ import annotations

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

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
IN_306B_SUMMARY = BASE_DIR / "output" / "eval_306b_marker_multi_panel_splitter" / "306b_summary.json"
IN_306B_INDEX = BASE_DIR / "output" / "eval_306b_marker_multi_panel_splitter" / "306b_split_panel_index.xlsx"
IN_306B_FAILED = BASE_DIR / "output" / "eval_306b_marker_multi_panel_splitter" / "306b_failed_split_candidates.xlsx"
IN_305B_EXCEL_DIR = BASE_DIR / "output" / "eval_marker1b_html_table_readable_render_fix" / "readable_excel"

OUT_DIR = BASE_DIR / "output" / "eval_306b_fix_hierarchical_panel_splitter"
OUT_MD_DIR = OUT_DIR / "306b_fix_split_panels_markdown"
OUT_SUMMARY = OUT_DIR / "306b_fix_summary.json"
OUT_REPORT = OUT_DIR / "306b_fix_report.md"
OUT_INDEX = OUT_DIR / "306b_fix_split_panel_index.xlsx"
OUT_PANELS = OUT_DIR / "306b_fix_split_panels.xlsx"
OUT_FAILED = OUT_DIR / "306b_fix_failed_split_candidates.xlsx"
OUT_NO_APPLY = OUT_DIR / "306b_fix_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

PANEL_ORDER = [
    "balance_sheet",
    "income_statement",
    "cash_flow_statement",
    "valuation_metrics",
    "financial_summary",
    "business_assumption",
]

PANEL_KWS: Dict[str, List[str]] = {
    "balance_sheet": ["资产负债表", "balance sheet", "资产总计", "负债合计", "股东权益", "流动资产", "流动负债"],
    "income_statement": ["利润表", "income statement", "营业收入", "营业成本", "营业利润", "净利润", "归属于母公司净利润"],
    "cash_flow_statement": ["现金流量表", "cash flow", "经营活动现金流", "投资活动现金流", "融资活动现金流", "现金净变动"],
    "valuation_metrics": ["关键财务与估值指标", "估值", "市盈率", "市净率", "p/e", "p/b", "ev/ebitda", "roe", "每股收益"],
    "financial_summary": ["盈利预测和财务指标", "盈利预测", "财务预测", "财务指标", "核心观点", "summary"],
    "business_assumption": ["业务假设", "正面银浆业务", "空白掩模版业务", "其他主营业务", "同比增长率", "毛利率"],
}

# Strict statement-title anchors for second-pass row splitting.
SECOND_PASS_TITLE_KWS: Dict[str, List[str]] = {
    "balance_sheet": ["资产负债表"],
    "income_statement": ["利润表"],
    "cash_flow_statement": ["现金流量表"],
    "valuation_metrics": ["关键财务与估值指标"],
    "financial_summary": ["盈利预测和财务指标", "财务预测"],
    "business_assumption": ["业务假设", "正面银浆业务", "空白掩模版业务", "其他主营业务"],
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
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y"}


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
    out = df.copy()
    out.columns = [_norm(c) for c in out.columns]
    out = out.fillna("")
    for c in out.columns:
        out[c] = out[c].map(_norm)
    return out


def _is_row_empty(row: pd.Series) -> bool:
    vals = [_norm(x) for x in row.tolist()]
    return all(v == "" for v in vals)


def _drop_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    keep = [not _is_row_empty(df.iloc[i, :]) for i in range(len(df))]
    return df.loc[keep, :].reset_index(drop=True)


def _panel_hits(text: str) -> Dict[str, int]:
    t = _norm(text).lower()
    out: Dict[str, int] = {}
    for p, kws in PANEL_KWS.items():
        out[p] = sum(1 for kw in kws if kw.lower() in t)
    return out


def _best_panel(text: str) -> Tuple[str, int]:
    hits = _panel_hits(text)
    best = ""
    score = 0
    for p in PANEL_ORDER:
        s = hits.get(p, 0)
        if s > score:
            best = p
            score = s
    return best, score


def _first_pass_column_split(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], str]:
    n_cols = len(df.columns)
    if n_cols < 4:
        return [], "column_anchor_not_enough_columns"
    top_rows = min(4, len(df))
    anchors: List[Tuple[int, str, int]] = []
    for j in range(n_cols):
        parts = [_norm(df.columns[j])]
        for i in range(top_rows):
            parts.append(_norm(df.iat[i, j]))
        txt = " ".join([x for x in parts if x])
        panel, score = _best_panel(txt)
        if score > 0:
            anchors.append((j, panel, score))
    if not anchors:
        return [], "column_anchor_none"
    by_col: Dict[int, Tuple[str, int]] = {}
    for j, p, s in anchors:
        old = by_col.get(j)
        if old is None or s > old[1]:
            by_col[j] = (p, s)
    anchors2 = sorted([(j, p, s) for j, (p, s) in by_col.items()], key=lambda x: x[0])
    if len(anchors2) < 2:
        return [], "column_anchor_less_than_two"
    segments: List[Dict[str, Any]] = []
    starts = [x[0] for x in anchors2]
    for idx, (start_col, panel, score) in enumerate(anchors2):
        end_col = starts[idx + 1] if idx + 1 < len(starts) else n_cols
        if idx == 0 and start_col > 0:
            start_col = 0
        seg = _drop_empty_rows(df.iloc[:, start_col:end_col].copy())
        if seg.empty:
            continue
        segments.append(
            {
                "panel_label": panel,
                "split_method": "column_anchor",
                "col_start": int(start_col),
                "col_end": int(end_col - 1),
                "row_start": 0,
                "row_end": 0,
                "anchor_score": int(score),
                "panel_df": seg,
            }
        )
    if len(segments) < 2:
        return [], "column_anchor_split_insufficient_panels"
    return segments, "column_anchor_ok"


def _first_pass_row_split(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], str]:
    if len(df) < 4:
        return [], "row_anchor_not_enough_rows"
    max_scan_cols = min(3, len(df.columns))
    anchors: List[Tuple[int, str, int]] = []
    for i in range(len(df)):
        txt = " ".join(_norm(df.iat[i, j]) for j in range(max_scan_cols))
        panel, score = _best_panel(txt)
        if score > 0:
            anchors.append((i, panel, score))
    if len(anchors) < 2:
        return [], "row_anchor_less_than_two"
    compact: List[Tuple[int, str, int]] = []
    for a in anchors:
        if not compact:
            compact.append(a)
            continue
        prev = compact[-1]
        if a[1] == prev[1] and a[0] - prev[0] <= 1:
            if a[2] > prev[2]:
                compact[-1] = a
        else:
            compact.append(a)
    anchors = compact
    if len(anchors) < 2:
        return [], "row_anchor_compacted_less_than_two"
    segments: List[Dict[str, Any]] = []
    starts = [x[0] for x in anchors]
    for idx, (start_row, panel, score) in enumerate(anchors):
        end_row = starts[idx + 1] if idx + 1 < len(starts) else len(df)
        seg = _drop_empty_rows(df.iloc[start_row:end_row, :].copy())
        if seg.empty:
            continue
        segments.append(
            {
                "panel_label": panel,
                "split_method": "row_anchor",
                "row_start": int(start_row),
                "row_end": int(end_row - 1),
                "col_start": 0,
                "col_end": len(df.columns) - 1,
                "anchor_score": int(score),
                "panel_df": seg,
            }
        )
    if len(segments) < 2:
        return [], "row_anchor_split_insufficient_panels"
    return segments, "row_anchor_ok"


def _row_title_label(row_text: str) -> Optional[str]:
    t = _norm(row_text)
    if t == "":
        return None
    for panel in PANEL_ORDER:
        for kw in SECOND_PASS_TITLE_KWS.get(panel, []):
            if kw in t:
                return panel
    return None


def _second_pass_row_split(
    panel_df: pd.DataFrame,
    parent_panel_label: str,
) -> Tuple[List[Dict[str, Any]], str]:
    # Only split when explicit statement titles appear in row labels.
    if panel_df.empty or len(panel_df) < 3:
        return [], "second_pass_too_small"

    scan_cols = min(2, len(panel_df.columns))
    anchors: List[Tuple[int, str]] = []
    for i in range(len(panel_df)):
        row_text = " ".join(_norm(panel_df.iat[i, j]) for j in range(scan_cols))
        label = _row_title_label(row_text)
        if label is not None:
            anchors.append((i, label))

    if not anchors:
        return [], "second_pass_no_title_anchor"

    # Deduplicate adjacent same labels.
    compact: List[Tuple[int, str]] = []
    for a in anchors:
        if not compact:
            compact.append(a)
            continue
        prev = compact[-1]
        if a[1] == prev[1] and a[0] - prev[0] <= 1:
            continue
        compact.append(a)
    anchors = compact

    # Ensure first segment starts from row 0 as parent panel baseline.
    if anchors[0][0] > 0:
        anchors = [(0, parent_panel_label)] + anchors
    elif anchors[0][0] == 0 and anchors[0][1] != parent_panel_label:
        anchors = [(0, parent_panel_label)] + anchors

    # Keep only change points where label changes.
    clean: List[Tuple[int, str]] = []
    for a in anchors:
        if not clean:
            clean.append(a)
            continue
        if a[1] == clean[-1][1]:
            continue
        clean.append(a)
    anchors = clean

    if len(anchors) < 2:
        return [], "second_pass_no_label_change"

    segments: List[Dict[str, Any]] = []
    starts = [x[0] for x in anchors]
    for idx, (start_row, lbl) in enumerate(anchors):
        end_row = starts[idx + 1] if idx + 1 < len(starts) else len(panel_df)
        seg = _drop_empty_rows(panel_df.iloc[start_row:end_row, :].copy())
        if seg.empty:
            continue
        segments.append(
            {
                "panel_label": lbl,
                "split_method": "second_pass_row_title",
                "row_start": int(start_row),
                "row_end": int(end_row - 1),
                "panel_df": seg,
            }
        )

    if len(segments) < 2:
        return [], "second_pass_segments_less_than_two"
    return segments, "second_pass_ok"


def _render_markdown(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "| parse_error |\n|---|\n| failed_to_render_markdown |"


def _read_required_doc(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306B_SUMMARY, IN_306B_INDEX, IN_306B_FAILED, IN_305B_EXCEL_DIR]
    missing = [str(x) for x in required if not x.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306B-FIX",
                "mode": "hierarchical_second_pass_panel_splitter",
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

    s306b = json.loads(IN_306B_SUMMARY.read_text(encoding="utf-8"))
    idx = pd.read_excel(IN_306B_INDEX).fillna("")
    failed = pd.read_excel(IN_306B_FAILED).fillna("")

    for df in [idx, failed]:
        if "pdf_file_name" in df.columns:
            df["pdf_file_name"] = df["pdf_file_name"].map(_norm)
        if "marker_table_id" in df.columns:
            df["marker_table_id"] = df["marker_table_id"].map(_norm)
        if "page_number" in df.columns:
            df["page_number"] = df["page_number"].map(_to_int)

    # Build 16 target list from existing 306B outputs.
    success_tables = idx[["pdf_file_name", "marker_table_id", "page_number", "table_seq", "source_sheet_name"]].drop_duplicates()
    failed_tables = failed[["pdf_file_name", "marker_table_id", "page_number", "table_seq", "source_sheet_name"]].drop_duplicates()
    targets = pd.concat([success_tables, failed_tables], ignore_index=True).drop_duplicates(
        subset=["pdf_file_name", "marker_table_id", "page_number"]
    )

    target_count = int(len(targets))
    expected_target_count = _to_int(s306b.get("filtered_real_split_target_count", 0))

    split_index_rows: List[Dict[str, Any]] = []
    split_flat_rows: List[Dict[str, Any]] = []
    failed_rows: List[Dict[str, Any]] = []
    sheet_map: Dict[str, pd.DataFrame] = {}

    split_success_target_count = 0
    split_failed_target_count = 0
    hierarchical_second_pass_applied_target_count = 0
    second_pass_generated_additional_panel_count = 0
    total_generated_panel_count = 0

    for _, t in targets.iterrows():
        pdf_name = _norm(t.get("pdf_file_name"))
        marker_table_id = _norm(t.get("marker_table_id"))
        page_number = _to_int(t.get("page_number"))
        table_seq = _to_int(t.get("table_seq"))
        source_sheet_name = _norm(t.get("source_sheet_name"))

        xlsx_path = IN_305B_EXCEL_DIR / f"{Path(pdf_name).stem}_tables_v2.xlsx"
        base_ctx = {
            "pdf_file_name": pdf_name,
            "marker_table_id": marker_table_id,
            "page_number": page_number,
            "table_seq": table_seq,
            "source_sheet_name": source_sheet_name,
            "xlsx_path": str(xlsx_path),
        }

        if not xlsx_path.exists():
            split_failed_target_count += 1
            failed_rows.append({**base_ctx, "failed_reason": "missing_305b_source_excel"})
            continue

        xls = pd.ExcelFile(xlsx_path)
        if source_sheet_name == "" or source_sheet_name not in xls.sheet_names:
            split_failed_target_count += 1
            failed_rows.append({**base_ctx, "failed_reason": "missing_source_sheet_name_in_305b_excel"})
            continue

        src_df = _normalize_df(pd.read_excel(xlsx_path, sheet_name=source_sheet_name))
        src_df = _drop_empty_rows(src_df)
        if src_df.empty:
            split_failed_target_count += 1
            failed_rows.append({**base_ctx, "failed_reason": "source_sheet_empty"})
            continue

        # Preserve 306B first-pass for existing success targets where possible.
        table_idx = idx[
            (idx["pdf_file_name"] == pdf_name)
            & (idx["marker_table_id"] == marker_table_id)
            & (idx["page_number"] == page_number)
        ].copy()

        first_pass_panels: List[Dict[str, Any]] = []
        first_pass_reason = ""
        if not table_idx.empty:
            table_idx = table_idx.sort_values("panel_index")
            for _, r in table_idx.iterrows():
                method = _norm(r.get("split_method"))
                label = _norm(r.get("panel_label"))
                if method == "column_anchor":
                    cs = _to_int(r.get("col_start"))
                    ce = _to_int(r.get("col_end"))
                    seg = src_df.iloc[:, cs : ce + 1].copy() if ce >= cs else pd.DataFrame()
                    seg = _drop_empty_rows(seg)
                    if seg.empty:
                        continue
                    first_pass_panels.append(
                        {
                            "panel_label": label,
                            "split_method": "column_anchor",
                            "col_start": cs,
                            "col_end": ce,
                            "row_start": 0,
                            "row_end": 0,
                            "panel_df": seg,
                        }
                    )
                elif method == "row_anchor":
                    rs = _to_int(r.get("row_start"))
                    re = _to_int(r.get("row_end"))
                    seg = src_df.iloc[rs : re + 1, :].copy() if re >= rs else pd.DataFrame()
                    seg = _drop_empty_rows(seg)
                    if seg.empty:
                        continue
                    first_pass_panels.append(
                        {
                            "panel_label": label,
                            "split_method": "row_anchor",
                            "row_start": rs,
                            "row_end": re,
                            "col_start": 0,
                            "col_end": len(src_df.columns) - 1,
                            "panel_df": seg,
                        }
                    )
            first_pass_reason = "preserved_from_306b_index"
        else:
            # For previous failed targets, try 306B first-pass logic.
            first_pass_panels, reason = _first_pass_column_split(src_df)
            if len(first_pass_panels) < 2:
                first_pass_panels, reason = _first_pass_row_split(src_df)
            first_pass_reason = f"recomputed_first_pass:{reason}"

        if len(first_pass_panels) == 0:
            split_failed_target_count += 1
            failed_rows.append({**base_ctx, "failed_reason": f"first_pass_failed:{first_pass_reason}"})
            continue

        final_panels: List[Dict[str, Any]] = []
        second_pass_applied = False
        initial_panel_count = len(first_pass_panels)

        for fp_idx, fp in enumerate(first_pass_panels, start=1):
            fp_label = _norm(fp.get("panel_label"))
            fp_method = _norm(fp.get("split_method"))
            fp_df = fp.get("panel_df")
            if not isinstance(fp_df, pd.DataFrame) or fp_df.empty:
                continue
            fp_df = _drop_empty_rows(_normalize_df(fp_df))
            if fp_df.empty:
                continue

            # Apply hierarchical second-pass only inside column panels.
            if fp_method == "column_anchor":
                sub_panels, sp_reason = _second_pass_row_split(fp_df, fp_label)
                if len(sub_panels) >= 2:
                    second_pass_applied = True
                    for sp_idx, sp in enumerate(sub_panels, start=1):
                        final_panels.append(
                            {
                                "first_pass_panel_index": fp_idx,
                                "first_pass_panel_label": fp_label,
                                "first_pass_split_method": fp_method,
                                "split_level": 2,
                                "panel_index": sp_idx,
                                "panel_label": _norm(sp.get("panel_label")),
                                "split_method": _norm(sp.get("split_method")),
                                "col_start": _to_int(fp.get("col_start")),
                                "col_end": _to_int(fp.get("col_end")),
                                "row_start": _to_int(sp.get("row_start")),
                                "row_end": _to_int(sp.get("row_end")),
                                "panel_df": _drop_empty_rows(_normalize_df(sp.get("panel_df"))),
                                "hierarchical_reason": sp_reason,
                            }
                        )
                    continue

            # Keep first-pass segment unchanged.
            final_panels.append(
                {
                    "first_pass_panel_index": fp_idx,
                    "first_pass_panel_label": fp_label,
                    "first_pass_split_method": fp_method,
                    "split_level": 1,
                    "panel_index": 1,
                    "panel_label": fp_label,
                    "split_method": fp_method,
                    "col_start": _to_int(fp.get("col_start")),
                    "col_end": _to_int(fp.get("col_end")),
                    "row_start": _to_int(fp.get("row_start")),
                    "row_end": _to_int(fp.get("row_end")),
                    "panel_df": fp_df,
                    "hierarchical_reason": "no_second_pass_split",
                }
            )

        if len(final_panels) == 0:
            split_failed_target_count += 1
            failed_rows.append({**base_ctx, "failed_reason": "no_final_panels_after_hierarchical_split"})
            continue

        split_success_target_count += 1
        total_generated_panel_count += len(final_panels)
        if second_pass_applied:
            hierarchical_second_pass_applied_target_count += 1
            second_pass_generated_additional_panel_count += max(0, len(final_panels) - initial_panel_count)

        md_lines: List[str] = []
        md_lines.append(f"# 306B Fix Split Panels: {pdf_name}")
        md_lines.append("")
        md_lines.append(f"- marker_table_id: {marker_table_id}")
        md_lines.append(f"- page_number: {page_number}")
        md_lines.append(f"- source_sheet_name: {source_sheet_name}")
        md_lines.append(f"- first_pass_source: {first_pass_reason}")
        md_lines.append(f"- hierarchical_second_pass_applied: {second_pass_applied}")
        md_lines.append("")

        for i, p in enumerate(final_panels, start=1):
            panel_df = p["panel_df"]
            if panel_df.empty:
                continue
            panel_label = _norm(p["panel_label"])
            sheet_name = f"t{table_seq}_{i}_{panel_label}"
            sheet_map[sheet_name] = panel_df

            split_index_rows.append(
                {
                    **base_ctx,
                    "first_pass_source": first_pass_reason,
                    "first_pass_panel_index": _to_int(p["first_pass_panel_index"]),
                    "first_pass_panel_label": _norm(p["first_pass_panel_label"]),
                    "first_pass_split_method": _norm(p["first_pass_split_method"]),
                    "split_level": _to_int(p["split_level"]),
                    "panel_index": i,
                    "panel_label": panel_label,
                    "split_method": _norm(p["split_method"]),
                    "col_start": _to_int(p["col_start"]),
                    "col_end": _to_int(p["col_end"]),
                    "row_start": _to_int(p["row_start"]),
                    "row_end": _to_int(p["row_end"]),
                    "panel_row_count": int(len(panel_df)),
                    "panel_col_count": int(len(panel_df.columns)),
                    "hierarchical_reason": _norm(p["hierarchical_reason"]),
                    "hierarchical_second_pass_applied": second_pass_applied,
                    "panel_sheet_name": sheet_name,
                }
            )

            for r_i in range(len(panel_df)):
                rec = {
                    "pdf_file_name": pdf_name,
                    "marker_table_id": marker_table_id,
                    "page_number": page_number,
                    "panel_index": i,
                    "panel_label": panel_label,
                    "row_in_panel": r_i + 1,
                }
                for c in panel_df.columns:
                    rec[f"c_{_norm(c)[:40]}"] = _norm(panel_df.iloc[r_i][c])
                split_flat_rows.append(rec)

            md_lines.append(f"## Panel {i}: {panel_label}")
            md_lines.append("")
            md_lines.append(f"- split_level: {_to_int(p['split_level'])}")
            md_lines.append(f"- first_pass_panel_label: {_norm(p['first_pass_panel_label'])}")
            md_lines.append(f"- first_pass_split_method: {_norm(p['first_pass_split_method'])}")
            md_lines.append(f"- split_method: {_norm(p['split_method'])}")
            md_lines.append(f"- hierarchical_reason: {_norm(p['hierarchical_reason'])}")
            md_lines.append("")
            md_lines.append(_render_markdown(panel_df))
            md_lines.append("")

        md_path = OUT_MD_DIR / f"{Path(pdf_name).stem}_p{page_number}_{table_seq}_fix_split.md"
        md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    split_index_df = pd.DataFrame(split_index_rows).fillna("")
    split_flat_df = pd.DataFrame(split_flat_rows).fillna("")
    failed_df = pd.DataFrame(failed_rows).fillna("")

    _write_excel(OUT_INDEX, {"fix_split_panel_index": split_index_df})
    out_sheets: Dict[str, pd.DataFrame] = {
        "fix_split_panel_index": split_index_df if not split_index_df.empty else pd.DataFrame([{"note": "no_split_index"}]),
        "fix_split_panels_flat": split_flat_df if not split_flat_df.empty else pd.DataFrame([{"note": "no_split_flat"}]),
    }
    for k, v in sheet_map.items():
        out_sheets[k] = v
    _write_excel(OUT_PANELS, out_sheets)
    _write_excel(
        OUT_FAILED,
        {"fix_failed_split_candidates": failed_df if not failed_df.empty else pd.DataFrame([{"note": "no_failed_candidates"}])},
    )

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

    panel_label_counts = (
        split_index_df["panel_label"].value_counts().to_dict() if not split_index_df.empty else {}
    )

    summary = {
        "stage": "EVAL-306B-FIX",
        "mode": "hierarchical_second_pass_panel_splitter",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_306b_filtered_target_count": expected_target_count,
        "target_count_from_306b_outputs": target_count,
        "split_success_target_count": int(split_success_target_count),
        "split_failed_target_count": int(split_failed_target_count),
        "hierarchical_second_pass_applied_target_count": int(hierarchical_second_pass_applied_target_count),
        "second_pass_generated_additional_panel_count": int(second_pass_generated_additional_panel_count),
        "total_generated_panel_count": int(total_generated_panel_count),
        "panel_label_counts": {k: int(v) for k, v in panel_label_counts.items()},
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306B Fix Hierarchical Panel Splitter",
        "",
        f"- input_306b_filtered_target_count: {summary['input_306b_filtered_target_count']}",
        f"- target_count_from_306b_outputs: {summary['target_count_from_306b_outputs']}",
        f"- split_success_target_count: {summary['split_success_target_count']}",
        f"- split_failed_target_count: {summary['split_failed_target_count']}",
        f"- hierarchical_second_pass_applied_target_count: {summary['hierarchical_second_pass_applied_target_count']}",
        f"- second_pass_generated_additional_panel_count: {summary['second_pass_generated_additional_panel_count']}",
        f"- total_generated_panel_count: {summary['total_generated_panel_count']}",
        f"- panel_label_counts: {summary['panel_label_counts']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306b_fix_summary_json: {OUT_SUMMARY}")
    print(f"eval_306b_fix_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
