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
IN_306A_MULTI = BASE_DIR / "output" / "eval_306a_marker_table_quality_gate_and_parser_fusion_design" / "306a_multi_panel_candidates.xlsx"
IN_305B_INDEX = BASE_DIR / "output" / "eval_marker1b_html_table_readable_render_fix" / "305b_table_render_index.xlsx"
IN_305B_EXCEL_DIR = BASE_DIR / "output" / "eval_marker1b_html_table_readable_render_fix" / "readable_excel"

OUT_DIR = BASE_DIR / "output" / "eval_306b_marker_multi_panel_splitter"
OUT_MD_DIR = OUT_DIR / "306b_split_panels_markdown"
OUT_SUMMARY = OUT_DIR / "306b_summary.json"
OUT_REPORT = OUT_DIR / "306b_report.md"
OUT_INDEX = OUT_DIR / "306b_split_panel_index.xlsx"
OUT_PANELS = OUT_DIR / "306b_split_panels.xlsx"
OUT_FAILED = OUT_DIR / "306b_failed_split_candidates.xlsx"
OUT_NO_APPLY = OUT_DIR / "306b_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

YEAR_TOKEN_RE = re.compile(r"(?:19|20)\d{2}(?:A|E)?")

PANEL_KWS: Dict[str, List[str]] = {
    "balance_sheet": ["资产负债表", "balance sheet", "资产总计", "负债合计", "股东权益", "流动资产", "流动负债"],
    "income_statement": ["利润表", "income statement", "营业收入", "营业成本", "营业利润", "净利润", "归属于母公司净利润"],
    "cash_flow_statement": ["现金流量表", "cash flow", "经营活动现金流", "投资活动现金流", "融资活动现金流", "现金净变动"],
    "valuation_metrics": ["关键财务与估值指标", "估值", "市盈率", "市净率", "p/e", "p/b", "ev/ebitda", "roe", "每股收益"],
    "financial_summary": ["盈利预测和财务指标", "盈利预测", "财务预测", "财务指标", "核心观点", "summary"],
    "business_assumption": ["业务假设", "正面银浆业务", "空白掩模版业务", "其他主营业务", "同比增长率", "毛利率"],
}

PANEL_ORDER = [
    "balance_sheet",
    "income_statement",
    "cash_flow_statement",
    "valuation_metrics",
    "financial_summary",
    "business_assumption",
]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y"}


def _to_int(v: Any) -> int:
    s = _norm(v)
    if s == "":
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


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


def _count_panel_hits(text: str) -> Dict[str, int]:
    t = _norm(text).lower()
    out: Dict[str, int] = {}
    for panel, kws in PANEL_KWS.items():
        out[panel] = sum(1 for kw in kws if kw.lower() in t)
    return out


def _best_panel(text: str) -> Tuple[str, int]:
    hits = _count_panel_hits(text)
    best = ""
    best_score = 0
    for p in PANEL_ORDER:
        sc = hits.get(p, 0)
        if sc > best_score:
            best = p
            best_score = sc
    return best, best_score


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
    keep_mask = [not _is_row_empty(df.iloc[i, :]) for i in range(len(df))]
    out = df.loc[keep_mask, :].reset_index(drop=True)
    return out


def _detect_repeated_year_headers(df: pd.DataFrame) -> bool:
    top_rows = min(2, len(df))
    header_text = " ".join([_norm(c) for c in df.columns])
    for i in range(top_rows):
        header_text += " " + " ".join(_norm(x) for x in df.iloc[i, :].tolist())
    tokens = YEAR_TOKEN_RE.findall(header_text)
    if not tokens:
        return False
    uniq = set(tokens)
    return len(tokens) - len(uniq) >= 2


def _detect_statement_title_count(df: pd.DataFrame) -> int:
    txt = " ".join([_norm(c) for c in df.columns])
    top_rows = min(3, len(df))
    for i in range(top_rows):
        txt += " " + " ".join(_norm(x) for x in df.iloc[i, :].tolist())
    titles = ["资产负债表", "利润表", "现金流量表", "关键财务与估值指标", "盈利预测和财务指标", "业务假设"]
    return sum(1 for t in titles if t in txt)


def _split_by_column_anchors(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], str]:
    n_cols = len(df.columns)
    if n_cols < 4:
        return [], "column_anchor_not_enough_columns"

    anchors: List[Tuple[int, str, int]] = []
    top_rows = min(4, len(df))
    for j in range(n_cols):
        col_parts = [_norm(df.columns[j])]
        for i in range(top_rows):
            col_parts.append(_norm(df.iat[i, j]))
        col_text = " ".join([x for x in col_parts if x])
        panel, score = _best_panel(col_text)
        if score > 0:
            anchors.append((j, panel, score))

    if not anchors:
        return [], "column_anchor_none"

    # Keep strongest anchor at each column.
    by_col: Dict[int, Tuple[str, int]] = {}
    for j, panel, score in anchors:
        old = by_col.get(j)
        if old is None or score > old[1]:
            by_col[j] = (panel, score)

    anchors2 = sorted([(j, p, s) for j, (p, s) in by_col.items()], key=lambda x: x[0])
    # Require at least two distinct anchor positions for split.
    if len(anchors2) < 2:
        return [], "column_anchor_less_than_two"

    segments: List[Dict[str, Any]] = []
    starts = [x[0] for x in anchors2]
    for idx, (start_col, panel, score) in enumerate(anchors2):
        end_col = starts[idx + 1] if idx + 1 < len(starts) else n_cols
        if idx == 0 and start_col > 0:
            start_col = 0
        seg = df.iloc[:, start_col:end_col].copy()
        seg = _drop_empty_rows(seg)
        if seg.empty or len(seg.columns) == 0:
            continue
        segments.append(
            {
                "panel_label": panel,
                "start_col": int(start_col),
                "end_col": int(end_col - 1),
                "anchor_score": int(score),
                "split_method": "column_anchor",
                "panel_df": seg,
            }
        )

    # Keep only expected panel labels.
    segments = [s for s in segments if s["panel_label"] in PANEL_ORDER]
    if len(segments) < 2:
        return [], "column_anchor_split_insufficient_panels"
    return segments, "column_anchor_ok"


def _split_by_row_anchors(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], str]:
    if len(df) < 4:
        return [], "row_anchor_not_enough_rows"

    anchors: List[Tuple[int, str, int]] = []
    max_scan_cols = min(3, len(df.columns))
    for i in range(len(df)):
        row_text = " ".join(_norm(df.iat[i, j]) for j in range(max_scan_cols))
        panel, score = _best_panel(row_text)
        if score > 0:
            anchors.append((i, panel, score))

    if len(anchors) < 2:
        return [], "row_anchor_less_than_two"

    # Deduplicate neighboring anchors with same panel.
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
        seg = df.iloc[start_row:end_row, :].copy()
        seg = _drop_empty_rows(seg)
        if seg.empty:
            continue
        segments.append(
            {
                "panel_label": panel,
                "start_row": int(start_row),
                "end_row": int(end_row - 1),
                "anchor_score": int(score),
                "split_method": "row_anchor",
                "panel_df": seg,
            }
        )
    segments = [s for s in segments if s["panel_label"] in PANEL_ORDER]
    if len(segments) < 2:
        return [], "row_anchor_split_insufficient_panels"
    return segments, "row_anchor_ok"


def _find_source_sheet(
    xlsx_path: Path,
    xls: pd.ExcelFile,
    table_seq: int,
    page_number: int,
    parsed_table_count: int,
) -> Optional[str]:
    names = xls.sheet_names
    preferred = [f"t{table_seq}_p{page_number}_{k}" for k in range(1, max(parsed_table_count, 1) + 1)]
    for p in preferred:
        if p in names:
            return p
    prefix = f"t{table_seq}_p{page_number}_"
    pref2 = [n for n in names if n.startswith(prefix)]
    if pref2:
        return sorted(pref2)[0]
    pref3 = [n for n in names if n.startswith(f"t{table_seq}_")]
    if pref3:
        return sorted(pref3)[0]
    return None


def _render_table_markdown(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return "| parse_error |\n|---|\n| failed_to_render_markdown |"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306A_MULTI, IN_305B_INDEX, IN_305B_EXCEL_DIR]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306B",
                "mode": "marker_multi_panel_splitter_sandbox_only",
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

    cands = pd.read_excel(IN_306A_MULTI).fillna("")
    rdx = pd.read_excel(IN_305B_INDEX).fillna("")

    cands["pdf_file_name"] = cands["pdf_file_name"].map(_norm)
    cands["marker_table_id"] = cands["marker_table_id"].map(_norm)
    cands["page_number"] = cands["page_number"].map(_to_int)
    rdx["pdf_file_name"] = rdx["pdf_file_name"].map(_norm)
    rdx["marker_table_id"] = rdx["marker_table_id"].map(_norm)
    rdx["page_number"] = rdx["page_number"].map(_to_int)
    rdx["parsed_table_count"] = rdx["parsed_table_count"].map(_to_int)

    # Build deterministic table sequence by source order within each PDF.
    rdx["table_seq"] = rdx.groupby("pdf_file_name").cumcount() + 1

    total_multi_candidates = int(len(cands))

    # Mandatory filter from manual correction.
    targets = cands[
        (cands["render_status"].map(_norm) == "SUCCESS")
        & (cands["table_classification"].map(_norm) == "multi_panel_split_required")
        & (cands["parsed_table_count"].map(_to_int) > 0)
        & (cands["row_count"].map(_to_int) > 0)
        & (cands["col_count"].map(_to_int) > 0)
        & (~cands["empty_shell_table"].map(_to_bool))
        & (cands["table_text_preview"].map(_norm) != "")
    ].copy()

    target_count = int(len(targets))

    # Join with 305B index to get xlsx path and sequence.
    m = targets.merge(
        rdx[
            [
                "pdf_file_name",
                "page_number",
                "marker_table_id",
                "table_seq",
                "xlsx_path",
                "parsed_table_count",
                "render_status",
            ]
        ],
        on=["pdf_file_name", "page_number", "marker_table_id"],
        how="left",
        suffixes=("_306a", "_305b"),
    )

    split_index_rows: List[Dict[str, Any]] = []
    split_panels_flat_rows: List[Dict[str, Any]] = []
    failed_rows: List[Dict[str, Any]] = []
    split_panel_sheets: Dict[str, pd.DataFrame] = {}

    split_success_target_count = 0
    split_failed_target_count = 0
    total_panel_count = 0
    repeated_year_header_target_count = 0

    # Cache excel handles.
    excel_cache: Dict[str, pd.ExcelFile] = {}

    for _, row in m.iterrows():
        pdf_name = _norm(row.get("pdf_file_name"))
        marker_table_id = _norm(row.get("marker_table_id"))
        page_number = _to_int(row.get("page_number"))
        table_seq = _to_int(row.get("table_seq"))
        parsed_table_count = _to_int(row.get("parsed_table_count_306a")) or _to_int(row.get("parsed_table_count_305b")) or 1
        xlsx_path_txt = _norm(row.get("xlsx_path"))

        fail_prefix = {
            "pdf_file_name": pdf_name,
            "marker_table_id": marker_table_id,
            "page_number": page_number,
            "table_seq": table_seq,
            "xlsx_path": xlsx_path_txt,
        }

        if table_seq <= 0 or xlsx_path_txt == "":
            split_failed_target_count += 1
            failed_rows.append(
                {
                    **fail_prefix,
                    "failed_reason": "missing_table_seq_or_xlsx_path",
                }
            )
            continue

        xlsx_path = Path(xlsx_path_txt)
        if not xlsx_path.exists():
            split_failed_target_count += 1
            failed_rows.append(
                {
                    **fail_prefix,
                    "failed_reason": "missing_source_excel",
                }
            )
            continue

        cache_key = str(xlsx_path)
        if cache_key not in excel_cache:
            excel_cache[cache_key] = pd.ExcelFile(xlsx_path)
        xls = excel_cache[cache_key]

        sheet_name = _find_source_sheet(xlsx_path, xls, table_seq, page_number, parsed_table_count)
        if not sheet_name:
            split_failed_target_count += 1
            failed_rows.append(
                {
                    **fail_prefix,
                    "failed_reason": "source_sheet_not_found",
                }
            )
            continue

        src_df = pd.read_excel(xlsx_path, sheet_name=sheet_name).fillna("")
        src_df = _normalize_df(src_df)
        src_df = _drop_empty_rows(src_df)
        if src_df.empty:
            split_failed_target_count += 1
            failed_rows.append(
                {
                    **fail_prefix,
                    "failed_reason": "source_sheet_empty_after_normalize",
                    "source_sheet_name": sheet_name,
                }
            )
            continue

        repeated_year_headers = _detect_repeated_year_headers(src_df)
        if repeated_year_headers:
            repeated_year_header_target_count += 1
        statement_title_count = _detect_statement_title_count(src_df)

        panels, split_reason = _split_by_column_anchors(src_df)
        if len(panels) < 2:
            panels, split_reason = _split_by_row_anchors(src_df)

        if len(panels) < 2:
            split_failed_target_count += 1
            failed_rows.append(
                {
                    **fail_prefix,
                    "failed_reason": f"split_failed:{split_reason}",
                    "source_sheet_name": sheet_name,
                    "repeated_year_headers_detected": repeated_year_headers,
                    "statement_title_count": statement_title_count,
                    "row_count": len(src_df),
                    "col_count": len(src_df.columns),
                }
            )
            continue

        split_success_target_count += 1
        total_panel_count += len(panels)

        md_lines: List[str] = []
        md_lines.append(f"# 306B Split Panels: {pdf_name}")
        md_lines.append("")
        md_lines.append(f"- marker_table_id: {marker_table_id}")
        md_lines.append(f"- page_number: {page_number}")
        md_lines.append(f"- source_sheet_name: {sheet_name}")
        md_lines.append(f"- split_method: {panels[0].get('split_method','')}")
        md_lines.append(f"- repeated_year_headers_detected: {repeated_year_headers}")
        md_lines.append(f"- statement_title_count: {statement_title_count}")
        md_lines.append("")

        for idx, p in enumerate(panels, start=1):
            panel_label = _norm(p.get("panel_label"))
            panel_df = p.get("panel_df")
            if panel_df is None or not isinstance(panel_df, pd.DataFrame) or panel_df.empty:
                continue
            panel_df = _drop_empty_rows(_normalize_df(panel_df))
            if panel_df.empty:
                continue

            panel_sheet_name = f"p{idx}_{panel_label}_{table_seq}"
            split_panel_sheets[panel_sheet_name] = panel_df

            md_lines.append(f"## Panel {idx}: {panel_label}")
            md_lines.append("")
            md_lines.append(f"- split_method: {_norm(p.get('split_method'))}")
            if p.get("split_method") == "column_anchor":
                md_lines.append(f"- col_range: {p.get('start_col')}..{p.get('end_col')}")
            else:
                md_lines.append(f"- row_range: {p.get('start_row')}..{p.get('end_row')}")
            md_lines.append("")
            md_lines.append(_render_table_markdown(panel_df))
            md_lines.append("")

            split_index_rows.append(
                {
                    "pdf_file_name": pdf_name,
                    "marker_table_id": marker_table_id,
                    "page_number": page_number,
                    "source_sheet_name": sheet_name,
                    "table_seq": table_seq,
                    "panel_index": idx,
                    "panel_label": panel_label,
                    "split_method": _norm(p.get("split_method")),
                    "col_start": _to_int(p.get("start_col")),
                    "col_end": _to_int(p.get("end_col")),
                    "row_start": _to_int(p.get("start_row")),
                    "row_end": _to_int(p.get("end_row")),
                    "anchor_score": _to_int(p.get("anchor_score")),
                    "panel_row_count": int(len(panel_df)),
                    "panel_col_count": int(len(panel_df.columns)),
                    "repeated_year_headers_detected": repeated_year_headers,
                    "statement_title_count": statement_title_count,
                    "panel_sheet_name": panel_sheet_name,
                }
            )

            for r_i in range(len(panel_df)):
                rec = {
                    "pdf_file_name": pdf_name,
                    "marker_table_id": marker_table_id,
                    "page_number": page_number,
                    "panel_index": idx,
                    "panel_label": panel_label,
                    "source_sheet_name": sheet_name,
                    "row_in_panel": r_i + 1,
                }
                for c in panel_df.columns:
                    rec[f"c_{_norm(c)[:40]}"] = _norm(panel_df.iloc[r_i][c])
                split_panels_flat_rows.append(rec)

        md_path = OUT_MD_DIR / f"{Path(pdf_name).stem}_p{page_number}_{table_seq}_split.md"
        md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    split_index_df = pd.DataFrame(split_index_rows).fillna("")
    split_panels_flat_df = pd.DataFrame(split_panels_flat_rows).fillna("")
    failed_df = pd.DataFrame(failed_rows).fillna("")

    _write_excel(OUT_INDEX, {"split_panel_index": split_index_df})

    sheets_out: Dict[str, pd.DataFrame] = {
        "split_panel_index": split_index_df if not split_index_df.empty else pd.DataFrame([{"note": "no_split_panels"}]),
        "split_panels_flat": split_panels_flat_df if not split_panels_flat_df.empty else pd.DataFrame([{"note": "no_flat_rows"}]),
    }
    # Add each panel as separate sheet where possible.
    for k, v in split_panel_sheets.items():
        sheets_out[k] = v
    _write_excel(OUT_PANELS, sheets_out)

    _write_excel(
        OUT_FAILED,
        {"failed_split_candidates": failed_df if not failed_df.empty else pd.DataFrame([{"note": "no_failed_candidates"}])},
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

    split_method_counts = (
        split_index_df["split_method"].value_counts().to_dict() if not split_index_df.empty else {}
    )
    panel_label_counts = (
        split_index_df["panel_label"].value_counts().to_dict() if not split_index_df.empty else {}
    )

    summary = {
        "stage": "EVAL-306B",
        "mode": "marker_multi_panel_splitter_sandbox_only",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_multi_panel_candidate_count": total_multi_candidates,
        "filtered_real_split_target_count": target_count,
        "ignored_noise_candidate_count": int(total_multi_candidates - target_count),
        "split_success_target_count": int(split_success_target_count),
        "split_failed_target_count": int(split_failed_target_count),
        "total_generated_panel_count": int(total_panel_count),
        "repeated_year_header_target_count": int(repeated_year_header_target_count),
        "split_method_counts": {k: int(v) for k, v in split_method_counts.items()},
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
        "# 306B Marker Multi-Panel Splitter",
        "",
        f"- input_multi_panel_candidate_count: {summary['input_multi_panel_candidate_count']}",
        f"- filtered_real_split_target_count: {summary['filtered_real_split_target_count']}",
        f"- ignored_noise_candidate_count: {summary['ignored_noise_candidate_count']}",
        f"- split_success_target_count: {summary['split_success_target_count']}",
        f"- split_failed_target_count: {summary['split_failed_target_count']}",
        f"- total_generated_panel_count: {summary['total_generated_panel_count']}",
        f"- repeated_year_header_target_count: {summary['repeated_year_header_target_count']}",
        f"- split_method_counts: {summary['split_method_counts']}",
        f"- panel_label_counts: {summary['panel_label_counts']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306b_summary_json: {OUT_SUMMARY}")
    print(f"eval_306b_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
