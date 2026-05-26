import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
EVAL1_DIR = BASE_DIR / "output" / "eval1_10pdf_sandbox_extraction_evaluation"

IN_SUMMARY = EVAL1_DIR / "300_eval1_10pdf_extraction_evaluation_summary.json"
IN_PER_PDF = EVAL1_DIR / "300_eval1_per_pdf_metrics.xlsx"
IN_FULL = EVAL1_DIR / "300_eval1_full_structured_table.xlsx"
IN_CLASSIFIED = EVAL1_DIR / "300_eval1_classified_structured_table.xlsx"
IN_CANDIDATE = EVAL1_DIR / "300_eval1_core_metrics_candidate_preview.xlsx"
IN_STMT_DIST = EVAL1_DIR / "300_eval1_statement_type_distribution.xlsx"
IN_CONFLICT = EVAL1_DIR / "300_eval1_conflict_diagnosis_summary.xlsx"
IN_FAILED = EVAL1_DIR / "300_eval1_failed_pdf_analysis.xlsx"
IN_MANIFEST = EVAL1_DIR / "300_eval1_pipeline_file_manifest.json"
IN_NO_APPLY = EVAL1_DIR / "300_eval1_no_apply_proof.json"
IN_RAW_DIR = EVAL1_DIR / "raw_tables_per_pdf"
IN_BLOCK_DIR = EVAL1_DIR / "table_blocks_per_pdf"
IN_DEBUG_DIR = EVAL1_DIR / "debug_per_pdf"

OUT_DIR = BASE_DIR / "output" / "eval1a_table_extraction_structure_quality_audit"
OUT_SUMMARY = OUT_DIR / "301_eval1a_table_extraction_structure_quality_summary.json"
OUT_REPORT = OUT_DIR / "301_eval1a_table_extraction_structure_quality_report.md"
OUT_PER_PDF = OUT_DIR / "301_eval1a_per_pdf_structure_quality.xlsx"
OUT_PROFILE = OUT_DIR / "301_eval1a_profile_selection_audit.xlsx"
OUT_FRAGMENT = OUT_DIR / "301_eval1a_fragmented_table_audit.xlsx"
OUT_MULTI = OUT_DIR / "301_eval1a_multi_panel_table_audit.xlsx"
OUT_MISSED = OUT_DIR / "301_eval1a_missed_summary_table_audit.xlsx"
OUT_STMT_AUDIT = OUT_DIR / "301_eval1a_table_block_statement_type_audit.xlsx"
OUT_FIX_PLAN = OUT_DIR / "301_eval1a_recommended_extraction_fix_plan.json"
OUT_NO_APPLY = OUT_DIR / "301_eval1a_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

SUMMARY_KEYWORDS = ["盈利预测和财务指标", "财务预测", "核心观点", "营业收入", "净利润", "每股收益", "市盈率", "市净率"]
FRAGMENT_KEYWORDS = ["合计", "正面银浆业务", "空白掩模版业务", "其他主营业务"]
FINANCIAL_KEYWORDS = ["营业收入", "净利润", "资产负债表", "利润表", "现金流量表", "每股收益", "P/E", "P/B", "EV/EBITDA"]
MULTI_STMT_KEYWORDS = ["资产负债表", "利润表", "现金流量表", "主要财务比率"]
YEAR_HDR_RE = re.compile(r"20\d{2}(?:A|E)?", re.IGNORECASE)


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    if isinstance(v, str) and v.strip().lower() == "nan":
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    return re.sub(r"\s+", "", _norm(v)).upper()


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    used = set()
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
    snap["release_zip"] = _sha256(RELEASE_ZIP)
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


def _load_sheet(path: Path, sheet: str) -> pd.DataFrame:
    x = pd.ExcelFile(path)
    if sheet in x.sheet_names:
        return pd.read_excel(path, sheet_name=sheet).fillna("")
    return pd.DataFrame()


def _profile_issue(profile_df: pd.DataFrame) -> Tuple[bool, str, Dict[str, Any]]:
    if profile_df.empty:
        return False, "no_profile_diag", {}

    selected = profile_df[profile_df["is_selected"].map(_as_bool)]
    if selected.empty and "selected_profile" in profile_df.columns:
        selected_name = _norm(profile_df.iloc[0].get("selected_profile"))
        selected = profile_df[profile_df["profile_name"].map(_norm) == selected_name]
    if selected.empty:
        selected = profile_df.iloc[[0]]

    sel = selected.iloc[0]
    sel_score = float(sel.get("avg_quality_score", 0) or 0)
    sel_good = float(sel.get("good_count", 0) or 0)
    sel_bad = float(sel.get("bad_count", 0) or 0)
    sel_name = _norm(sel.get("profile_name"))

    best = profile_df.sort_values("avg_quality_score", ascending=False).iloc[0]
    best_name = _norm(best.get("profile_name"))
    best_score = float(best.get("avg_quality_score", 0) or 0)
    best_good = float(best.get("good_count", 0) or 0)
    best_bad = float(best.get("bad_count", 0) or 0)

    reasons = []
    if best_name != sel_name and best_score - sel_score >= 0.2:
        reasons.append("selected_score_lower_by_0.2+")
    if best_name != sel_name and best_good > sel_good:
        reasons.append("selected_good_count_lower")
    if best_name != sel_name and best_bad < sel_bad:
        reasons.append("selected_bad_count_higher")

    issue = len(reasons) > 0
    detail = {
        "selected_profile": sel_name,
        "selected_avg_quality_score": sel_score,
        "selected_good_count": sel_good,
        "selected_bad_count": sel_bad,
        "best_profile": best_name,
        "best_avg_quality_score": best_score,
        "best_good_count": best_good,
        "best_bad_count": best_bad,
    }
    return issue, "|".join(reasons) if reasons else "ok", detail


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_SUMMARY,
        IN_PER_PDF,
        IN_FULL,
        IN_CLASSIFIED,
        IN_CANDIDATE,
        IN_STMT_DIST,
        IN_CONFLICT,
        IN_FAILED,
        IN_MANIFEST,
        IN_NO_APPLY,
        IN_RAW_DIR,
        IN_BLOCK_DIR,
        IN_DEBUG_DIR,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-1A",
                "mode": "table_extraction_structure_quality_audit_only",
                "blocked": True,
                "blocked_reason": "missing_eval1_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "real_apply_executed": False,
            },
        )
        print("eval1a_status=blocked_missing_inputs")
        return 0

    before = _snapshot_guard()
    eval1_summary = _load_json(IN_SUMMARY)
    per_pdf = pd.read_excel(IN_PER_PDF).fillna("")
    full_df = pd.read_excel(IN_FULL).fillna("")
    cls_df = pd.read_excel(IN_CLASSIFIED).fillna("")
    cand_df = pd.read_excel(IN_CANDIDATE).fillna("")
    _ = pd.read_excel(IN_STMT_DIST).fillna("")
    _ = pd.read_excel(IN_CONFLICT).fillna("")
    failed_df = pd.read_excel(IN_FAILED).fillna("")
    _ = _load_json(IN_MANIFEST)
    _ = _load_json(IN_NO_APPLY)

    eval1_summary_loaded = True
    stage_ok = (
        int(eval1_summary.get("input_pdf_count", 0)) == 10
        and int(eval1_summary.get("missing_pdf_count", -1)) == 0
        and int(eval1_summary.get("pdf_failed_count", -1)) == 0
        and int(eval1_summary.get("full_structured_total_rows", 0)) > 0
        and int(eval1_summary.get("classified_total_rows", 0)) > 0
        and _norm(eval1_summary.get("check_delivery_state_overall_status")) == "PASS"
    )

    per_pdf_rows: List[Dict[str, Any]] = []
    profile_rows: List[Dict[str, Any]] = []
    fragment_rows: List[Dict[str, Any]] = []
    multi_rows: List[Dict[str, Any]] = []
    missed_rows: List[Dict[str, Any]] = []
    stmt_audit_rows: List[Dict[str, Any]] = []

    raw_table_outputs_loaded = True
    table_block_outputs_loaded = True
    profile_diag_outputs_loaded = True

    expected_pdfs = per_pdf["pdf_file_name"].map(_norm).tolist()

    for pdf_name in expected_pdfs:
        stem = Path(pdf_name).stem
        raw_path = IN_RAW_DIR / f"{stem}_raw_tables.xlsx"
        blk_path = IN_BLOCK_DIR / f"{stem}_table_blocks.xlsx"
        dbg_path = IN_DEBUG_DIR / f"{stem}_debug.xlsx"

        if not raw_path.exists():
            raw_table_outputs_loaded = False
        if not blk_path.exists():
            table_block_outputs_loaded = False
        if not dbg_path.exists():
            profile_diag_outputs_loaded = False

        raw_df = _load_sheet(raw_path, "raw_tables") if raw_path.exists() else pd.DataFrame()
        idx_df = _load_sheet(raw_path, "table_index") if raw_path.exists() else pd.DataFrame()
        prof_df = _load_sheet(raw_path, "profile_diag") if raw_path.exists() else pd.DataFrame()
        blk_df = _load_sheet(blk_path, "table_blocks") if blk_path.exists() else pd.DataFrame()
        dbg_df = _load_sheet(dbg_path, "debug") if dbg_path.exists() else pd.DataFrame()

        full_one = full_df[full_df["source_pdf_name"].map(_norm) == pdf_name].copy()
        cls_one = cls_df[cls_df["source_pdf_name"].map(_norm) == pdf_name].copy()
        cand_one = cand_df[cand_df["source_pdf_name"].map(_norm) == pdf_name].copy()

        pages = sorted({int(x) for x in pd.to_numeric(idx_df.get("page", pd.Series([], dtype=float)), errors="coerce").dropna().tolist()})
        extracted_page_count = len(pages)
        pages_with_tables = ",".join(str(p) for p in pages)

        raw_table_count = int(raw_df["table_id"].map(_norm).nunique()) if not raw_df.empty and "table_id" in raw_df.columns else 0
        raw_table_row_count = int(len(raw_df))
        raw_table_non_empty_cell_count = int((raw_df["cell_text"].map(_norm) != "").sum()) if not raw_df.empty and "cell_text" in raw_df.columns else 0

        table_block_count = int(len(blk_df))
        single_cell_table_count = int(((pd.to_numeric(idx_df.get("rows", 0), errors="coerce").fillna(0) <= 1) & (pd.to_numeric(idx_df.get("cols", 0), errors="coerce").fillna(0) <= 1)).sum()) if not idx_df.empty else 0
        one_row_table_count = int((pd.to_numeric(idx_df.get("rows", 0), errors="coerce").fillna(0) <= 1).sum()) if not idx_df.empty else 0
        low_confidence_block_count = int((pd.to_numeric(blk_df.get("block_confidence", 0), errors="coerce").fillna(0) < 0.6).sum()) if not blk_df.empty else 0
        unknown_statement_type_block_count = int((blk_df.get("statement_type", pd.Series([], dtype=str)).map(_norm) == "unknown_financial_table").sum()) if not blk_df.empty else 0
        multi_panel_block_count = int(blk_df.get("block_type", pd.Series([], dtype=str)).map(_norm).str.contains("multi_panel", case=False, regex=False).sum()) if not blk_df.empty else 0
        stacked_multi_panel_block_count = int((blk_df.get("block_type", pd.Series([], dtype=str)).map(_norm) == "stacked_multi_panel_table").sum()) if not blk_df.empty else 0
        paragraph_embedded_metrics_block_count = int((blk_df.get("block_type", pd.Series([], dtype=str)).map(_norm) == "paragraph_embedded_metrics").sum()) if not blk_df.empty else 0

        # Profile selection audit
        issue, issue_reason, issue_detail = _profile_issue(prof_df)
        profile_rows.append({"pdf_file_name": pdf_name, "suspected_profile_selection_issue": issue, "issue_reason": issue_reason, **issue_detail})

        # Fragmentation audit
        suspicious_fragmented_table_count = 0
        if not idx_df.empty:
            one_row_pages = idx_df.assign(rows_num=pd.to_numeric(idx_df["rows"], errors="coerce").fillna(0)).groupby("page", dropna=False)["rows_num"].apply(lambda s: int((s <= 1).sum()))
            tiny_pages = idx_df.assign(rows_num=pd.to_numeric(idx_df["rows"], errors="coerce").fillna(0), cols_num=pd.to_numeric(idx_df["cols"], errors="coerce").fillna(0)).groupby("page", dropna=False).apply(lambda d: int(((d["rows_num"] <= 1) & (d["cols_num"] <= 1)).sum()))
            for page, one_cnt in one_row_pages.items():
                tiny_cnt = int(tiny_pages.get(page, 0))
                if one_cnt >= 3 or tiny_cnt >= 2:
                    suspicious_fragmented_table_count += 1
                    fragment_rows.append(
                        {
                            "pdf_file_name": pdf_name,
                            "page": int(page) if str(page).isdigit() else page,
                            "reason": "multiple_one_row_or_tiny_tables",
                            "one_row_table_count_on_page": int(one_cnt),
                            "single_cell_table_count_on_page": int(tiny_cnt),
                        }
                    )
        # keyword fragment signal from debug rows
        if not dbg_df.empty and "row_text" in dbg_df.columns:
            hit = dbg_df["row_text"].map(_norm).map(lambda t: any(k in t for k in FRAGMENT_KEYWORDS)).sum()
            if int(hit) > 0:
                suspicious_fragmented_table_count += 1
                fragment_rows.append(
                    {
                        "pdf_file_name": pdf_name,
                        "page": "",
                        "reason": "fragment_keyword_hits_in_debug_rows",
                        "one_row_table_count_on_page": "",
                        "single_cell_table_count_on_page": "",
                        "keyword_hit_count": int(hit),
                    }
                )

        # Multi-panel audit
        suggested_split_panel_for_pdf = 0
        if not blk_df.empty:
            for _, b in blk_df.iterrows():
                btype = _norm(b.get("block_type"))
                reason = ""
                if "multi_panel" in btype:
                    reason = "block_type_multi_panel"
                elif int(pd.to_numeric(b.get("max_col", 0), errors="coerce") or 0) >= 10:
                    table_id = _norm(b.get("raw_table_id"))
                    raw_one = raw_df[raw_df["table_id"].map(_norm) == table_id] if not raw_df.empty else pd.DataFrame()
                    hdr = raw_one[raw_one["row_index"].map(lambda x: int(pd.to_numeric(x, errors='coerce') or 0) <= 2)]["cell_text"].map(_norm).tolist() if not raw_one.empty else []
                    year_hits = [h for h in hdr if YEAR_HDR_RE.search(h)]
                    stmt_hits = [h for h in hdr if any(k in h for k in MULTI_STMT_KEYWORDS)]
                    if len(year_hits) >= 6 or len(stmt_hits) >= 2:
                        reason = "wide_table_with_repeated_year_or_multi_statement_titles"
                if reason:
                    suggested_split_panel_for_pdf += 1
                    multi_rows.append(
                        {
                            "pdf_file_name": pdf_name,
                            "raw_table_id": _norm(b.get("raw_table_id")),
                            "block_id": _norm(b.get("block_id")),
                            "block_type": btype,
                            "statement_type": _norm(b.get("statement_type")),
                            "max_col": pd.to_numeric(b.get("max_col", 0), errors="coerce"),
                            "reason": reason,
                            "suggest_split_panel": True,
                        }
                    )

        # Missed summary audit
        suspected_missed_summary_table = False
        missed_state = "false"
        if 1 not in pages:
            # no direct page1 text extraction -> unknown
            page1_text_available = False
            if not raw_df.empty:
                page1_rows = raw_df[raw_df["table_id"].map(_norm).str.contains(r"\|p1\|", regex=True, na=False)]
                if not page1_rows.empty:
                    page1_text_available = True
                    joined = " ".join(page1_rows["cell_text"].map(_norm).tolist())
                    if any(k in joined for k in SUMMARY_KEYWORDS):
                        suspected_missed_summary_table = True
                        missed_state = "true"
                    else:
                        missed_state = "false"
            if not page1_text_available:
                missed_state = "unknown"
        missed_rows.append(
            {
                "pdf_file_name": pdf_name,
                "page1_in_extracted_pages": 1 in pages,
                "suspected_missed_summary_table": missed_state,
                "evidence_note": "unknown_due_to_no_page1_text_extraction" if missed_state == "unknown" else "",
            }
        )

        # Statement type audit rows
        if not blk_df.empty:
            for _, b in blk_df.iterrows():
                block_id = _norm(b.get("block_id"))
                raw_table_id = _norm(b.get("raw_table_id"))
                stmt_type = _norm(b.get("statement_type"))
                conf = float(pd.to_numeric(b.get("block_confidence", 0), errors="coerce") or 0)
                raw_related = full_one[full_one["raw_table_id"].map(_norm) == raw_table_id] if not full_one.empty else pd.DataFrame()
                text_blob = " ".join(raw_related.get("source_text_excerpt", pd.Series([], dtype=str)).map(_norm).tolist())
                has_fin_kw = any(k in text_blob for k in FINANCIAL_KEYWORDS)
                multi_stmt_signal = sum(1 for k in MULTI_STMT_KEYWORDS if k in text_blob)
                stmt_audit_rows.append(
                    {
                        "pdf_file_name": pdf_name,
                        "raw_table_id": raw_table_id,
                        "block_id": block_id,
                        "block_type": _norm(b.get("block_type")),
                        "statement_type": stmt_type,
                        "block_confidence": conf,
                        "is_unknown_statement_type": stmt_type == "unknown_financial_table",
                        "is_low_confidence": conf < 0.6,
                        "has_financial_keywords": has_fin_kw,
                        "multi_statement_signal_count": multi_stmt_signal,
                        "multi_statement_single_type_suspected": multi_stmt_signal >= 2 and stmt_type not in {"unknown_financial_table", ""},
                    }
                )

        per_pdf_rows.append(
            {
                "pdf_file_name": pdf_name,
                "raw_table_count": raw_table_count,
                "extracted_page_count": extracted_page_count,
                "pages_with_tables": pages_with_tables,
                "raw_table_row_count": raw_table_row_count,
                "raw_table_non_empty_cell_count": raw_table_non_empty_cell_count,
                "full_structured_row_count": int(len(full_one)),
                "classified_row_count": int(len(cls_one)),
                "core_metrics_candidate_count": int(len(cand_one)),
                "table_block_count": table_block_count,
                "single_cell_table_count": single_cell_table_count,
                "one_row_table_count": one_row_table_count,
                "low_confidence_block_count": low_confidence_block_count,
                "unknown_statement_type_block_count": unknown_statement_type_block_count,
                "multi_panel_block_count": multi_panel_block_count,
                "stacked_multi_panel_block_count": stacked_multi_panel_block_count,
                "paragraph_embedded_metrics_block_count": paragraph_embedded_metrics_block_count,
                "suspicious_fragmented_table_count": suspicious_fragmented_table_count,
                "suspected_missed_summary_table": missed_state,
                "suspected_profile_selection_issue": issue,
                "notes": issue_reason,
            }
        )

    per_pdf_audit_df = pd.DataFrame(per_pdf_rows).fillna("")
    profile_df = pd.DataFrame(profile_rows).fillna("")
    fragment_df = pd.DataFrame(fragment_rows).fillna("")
    multi_df = pd.DataFrame(multi_rows).fillna("")
    missed_df = pd.DataFrame(missed_rows).fillna("")
    stmt_df = pd.DataFrame(stmt_audit_rows).fillna("")

    _write_excel(OUT_PER_PDF, {"per_pdf_structure_quality": per_pdf_audit_df})
    _write_excel(OUT_PROFILE, {"profile_selection_audit": profile_df})
    _write_excel(OUT_FRAGMENT, {"fragmented_table_audit": fragment_df})
    _write_excel(OUT_MULTI, {"multi_panel_table_audit": multi_df})
    _write_excel(OUT_MISSED, {"missed_summary_table_audit": missed_df})
    _write_excel(OUT_STMT_AUDIT, {"table_block_statement_type_audit": stmt_df})

    suspected_profile_selection_issue_count = int((profile_df["suspected_profile_selection_issue"] == True).sum()) if not profile_df.empty else 0
    fragmented_table_pdf_count = int(fragment_df["pdf_file_name"].map(_norm).nunique()) if not fragment_df.empty else 0
    suspicious_fragment_count = int(len(fragment_df))
    multi_panel_table_count = int(len(multi_df))
    suggested_split_panel_count = int((multi_df.get("suggest_split_panel", pd.Series([], dtype=bool)) == True).sum()) if not multi_df.empty else 0
    suspected_missed_summary_table_count = int((missed_df["suspected_missed_summary_table"].map(_norm) == "true").sum()) if not missed_df.empty else 0
    unknown_financial_table_block_count = int((stmt_df.get("is_unknown_statement_type", pd.Series([], dtype=bool)) == True).sum()) if not stmt_df.empty else 0
    low_confidence_block_count = int((stmt_df.get("is_low_confidence", pd.Series([], dtype=bool)) == True).sum()) if not stmt_df.empty else 0
    multi_statement_single_type_block_count = int((stmt_df.get("multi_statement_single_type_suspected", pd.Series([], dtype=bool)) == True).sum()) if not stmt_df.empty else 0

    fix_plan = {
        "stage": "EVAL-1A",
        "apply_now": False,
        "fix_categories": [
            {
                "category": "extraction_profile_selection_fix",
                "priority": "high" if suspected_profile_selection_issue_count > 0 else "medium",
                "evidence_count": suspected_profile_selection_issue_count,
                "notes": "Prefer profile with better quality score / good_count and lower bad_count.",
            },
            {
                "category": "page1_summary_table_capture_fix",
                "priority": "high" if suspected_missed_summary_table_count > 0 else "medium",
                "evidence_count": suspected_missed_summary_table_count,
                "notes": "Improve page-1 table capture and title/summary table detection.",
            },
            {
                "category": "fragmented_table_merge_fix",
                "priority": "high" if suspicious_fragment_count > 0 else "medium",
                "evidence_count": suspicious_fragment_count,
                "notes": "Merge tiny fragments by page/title context before block parsing.",
            },
            {
                "category": "multi_panel_table_splitter",
                "priority": "high" if suggested_split_panel_count > 0 else "medium",
                "evidence_count": suggested_split_panel_count,
                "notes": "Split stacked/combined multi-panel financial tables into sub-panels.",
            },
            {
                "category": "statement_type_multi_label_support",
                "priority": "high" if multi_statement_single_type_block_count > 0 else "medium",
                "evidence_count": multi_statement_single_type_block_count,
                "notes": "Support multi-statement labels in one wide block.",
            },
            {
                "category": "table_title_context_propagation",
                "priority": "medium",
                "evidence_count": unknown_financial_table_block_count,
                "notes": "Propagate nearby title/context to unknown blocks before final statement typing.",
            },
            {
                "category": "candidate_selector_wait_until_structure_fixed",
                "priority": "high",
                "evidence_count": int((per_pdf_audit_df["core_metrics_candidate_count"] == 0).sum()),
                "notes": "Keep candidate rule tuning deferred until extraction structure quality is improved.",
            },
        ],
    }
    _write_json(OUT_FIX_PLAN, fix_plan)

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
            "note": "EVAL-1A is audit-only; no logic/rule/apply changes executed.",
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
        "stage": "EVAL-1A",
        "mode": "table_extraction_structure_quality_audit_only",
        "external_api_called": False,
        "llm_api_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval1_summary_loaded": eval1_summary_loaded,
        "input_pdf_count": int(eval1_summary.get("input_pdf_count", 0)),
        "raw_table_outputs_loaded": raw_table_outputs_loaded,
        "table_block_outputs_loaded": table_block_outputs_loaded,
        "profile_diag_outputs_loaded": profile_diag_outputs_loaded,
        "suspected_profile_selection_issue_count": suspected_profile_selection_issue_count,
        "fragmented_table_pdf_count": fragmented_table_pdf_count,
        "suspicious_fragment_count": suspicious_fragment_count,
        "multi_panel_table_count": multi_panel_table_count,
        "suggested_split_panel_count": suggested_split_panel_count,
        "suspected_missed_summary_table_count": suspected_missed_summary_table_count,
        "unknown_financial_table_block_count": unknown_financial_table_block_count,
        "low_confidence_block_count": low_confidence_block_count,
        "multi_statement_single_type_block_count": multi_statement_single_type_block_count,
        "recommended_extraction_fix_plan_generated": True,
        "extraction_logic_modified": False,
        "candidate_rules_modified": False,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_eval1b_extraction_structure_fix": True,
        "eval1_stage_precheck_pass": stage_ok,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# EVAL-1A Table Extraction Structure Quality Audit",
        "",
        f"- eval1_stage_precheck_pass: {stage_ok}",
        f"- suspected_profile_selection_issue_count: {suspected_profile_selection_issue_count}",
        f"- fragmented_table_pdf_count: {fragmented_table_pdf_count}",
        f"- suspicious_fragment_count: {suspicious_fragment_count}",
        f"- multi_panel_table_count: {multi_panel_table_count}",
        f"- suggested_split_panel_count: {suggested_split_panel_count}",
        f"- suspected_missed_summary_table_count: {suspected_missed_summary_table_count}",
        f"- unknown_financial_table_block_count: {unknown_financial_table_block_count}",
        f"- low_confidence_block_count: {low_confidence_block_count}",
        f"- multi_statement_single_type_block_count: {multi_statement_single_type_block_count}",
        "",
        "No extraction logic or candidate rules were modified in EVAL-1A.",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"eval1a_summary_json: {OUT_SUMMARY}")
    print(f"eval1a_report_md: {OUT_REPORT}")
    print("eval1a_ready_for_eval1b_extraction_structure_fix: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
