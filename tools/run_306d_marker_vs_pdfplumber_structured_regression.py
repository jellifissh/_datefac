from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306d_marker_vs_pdfplumber_structured_regression"

IN_306C_SUMMARY = BASE_DIR / "output" / "eval_306c_marker_panels_to_full_structured_sandbox" / "306c_summary.json"
IN_306C_FULL = BASE_DIR / "output" / "eval_306c_marker_panels_to_full_structured_sandbox" / "306c_marker_full_structured_table.xlsx"
IN_306C_HIGH = BASE_DIR / "output" / "eval_306c_marker_panels_to_full_structured_sandbox" / "306c_high_confidence_structured_rows.xlsx"
IN_306C_BLOCKED = BASE_DIR / "output" / "eval_306c_marker_panels_to_full_structured_sandbox" / "306c_blocked_rows_audit.xlsx"

IN_1B_SUMMARY = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression" / "302_eval1b_profile_selection_fix_summary.json"
IN_1B_PER_PDF = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression" / "302_eval1b_per_pdf_metrics.xlsx"
IN_1B_FULL = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression" / "302_eval1b_full_structured_table.xlsx"
IN_1B_CAND = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression" / "302_eval1b_core_metrics_candidate_preview.xlsx"

IN_IMG_COVER = BASE_DIR / "output" / "eval_img1_visual_table_layout_audit" / "303_eval_img1_visual_vs_raw_page_coverage.xlsx"
IN_IMG_MULTI = BASE_DIR / "output" / "eval_img1_visual_table_layout_audit" / "303_eval_img1_multi_panel_visual_audit.xlsx"

OUT_SUMMARY = OUT_DIR / "306d_summary.json"
OUT_REPORT = OUT_DIR / "306d_report.md"
OUT_PER_PDF = OUT_DIR / "306d_per_pdf_comparison.xlsx"
OUT_CORE = OUT_DIR / "306d_core_metric_coverage_comparison.xlsx"
OUT_CONFLICT = OUT_DIR / "306d_conflict_comparison.xlsx"
OUT_MARKER_IMPROVE = OUT_DIR / "306d_marker_only_improvements.xlsx"
OUT_PDFPLUMBER_ADV = OUT_DIR / "306d_pdfplumber_only_advantages.xlsx"
OUT_FUSION_MD = OUT_DIR / "306d_fusion_next_step_recommendation.md"
OUT_NO_APPLY = OUT_DIR / "306d_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

CORE_METRICS = [
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
]

PDFP_CORE_NAME_MAP = {
    "营业收入": "revenue",
    "净利润": "net_profit",
    "归属于母公司净利润": "attributable_net_profit",
    "归母净利润": "attributable_net_profit",
    "资产总计": "total_assets",
    "负债合计": "total_liabilities",
    "经营活动现金流": "operating_cash_flow",
    "经营现金流": "operating_cash_flow",
    "每股收益": "eps",
    "roe": "roe",
    "净资产收益率": "roe",
    "毛利率": "gross_margin",
    "市盈率": "pe",
    "p/e": "pe",
    "市净率": "pb",
    "p/b": "pb",
    "ev/ebitda": "ev_ebitda",
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


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_sheet_name(name: str, used: set) -> str:
    s = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
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


def _pdfp_metric_to_core(raw: str, norm_name: str) -> str:
    t = (_norm(norm_name) + " " + _norm(raw)).lower()
    for k, v in PDFP_CORE_NAME_MAP.items():
        if k.lower() in t:
            return v
    return ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_306C_SUMMARY,
        IN_306C_FULL,
        IN_306C_HIGH,
        IN_306C_BLOCKED,
        IN_1B_SUMMARY,
        IN_1B_PER_PDF,
        IN_1B_FULL,
        IN_1B_CAND,
        IN_IMG_COVER,
        IN_IMG_MULTI,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306D",
                "mode": "marker_vs_pdfplumber_structured_regression",
                "blocked": True,
                "blocked_reason": "missing_required_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
                "marker_rerun_executed": False,
                "pdfplumber_rerun_executed": False,
            },
        )
        return 0

    before = _snapshot_guard()

    s306c = json.loads(IN_306C_SUMMARY.read_text(encoding="utf-8"))
    s1b = json.loads(IN_1B_SUMMARY.read_text(encoding="utf-8"))

    marker_full = pd.read_excel(IN_306C_FULL).fillna("")
    marker_high = pd.read_excel(IN_306C_HIGH).fillna("")
    marker_blocked = pd.read_excel(IN_306C_BLOCKED).fillna("")
    pdfp_per = pd.read_excel(IN_1B_PER_PDF).fillna("")
    pdfp_full = pd.read_excel(IN_1B_FULL).fillna("")
    pdfp_cand = pd.read_excel(IN_1B_CAND).fillna("")
    vis_cov = pd.read_excel(IN_IMG_COVER).fillna("")
    vis_multi = pd.read_excel(IN_IMG_MULTI).fillna("")

    marker_full["source_pdf_name"] = marker_full["source_pdf_name"].map(_norm)
    marker_high["source_pdf_name"] = marker_high["source_pdf_name"].map(_norm)
    marker_blocked["source_pdf_name"] = marker_blocked["source_pdf_name"].map(_norm)
    pdfp_per["pdf_file_name"] = pdfp_per["pdf_file_name"].map(_norm)
    pdfp_full["source_pdf_name"] = pdfp_full["source_pdf_name"].map(_norm)
    pdfp_cand["source_pdf_name"] = pdfp_cand["source_pdf_name"].map(_norm)
    vis_cov["pdf_file_name"] = vis_cov["pdf_file_name"].map(_norm)
    vis_multi["pdf_file_name"] = vis_multi["pdf_file_name"].map(_norm)
    vis_cov["page_number"] = vis_cov["page_number"].map(_to_int)
    vis_multi["page_number"] = vis_multi["page_number"].map(_to_int)

    pdf_list = sorted(set(pdfp_per["pdf_file_name"].tolist()))

    # Core metric coverage tables.
    marker_core_df = marker_full[
        marker_full["normalized_metric_name"].map(_norm).isin(CORE_METRICS)
    ].copy()
    marker_core_df = marker_core_df[marker_core_df["value_raw"].map(_norm) != ""]
    marker_core_cov = (
        marker_core_df.groupby(["source_pdf_name", "normalized_metric_name"]).size().reset_index(name="marker_row_count")
    )

    pdfp_cand = pdfp_cand.copy()
    pdfp_cand["core_metric"] = pdfp_cand.apply(
        lambda r: _pdfp_metric_to_core(r.get("raw_metric_name", ""), r.get("normalized_metric_name", "")),
        axis=1,
    )
    pdfp_core_df = pdfp_cand[pdfp_cand["core_metric"].map(_norm) != ""].copy()
    pdfp_core_cov = (
        pdfp_core_df.groupby(["source_pdf_name", "core_metric"]).size().reset_index(name="pdfplumber_row_count")
    )

    core_rows: List[Dict[str, Any]] = []
    for pdf in pdf_list:
        for metric in CORE_METRICS:
            m_cnt = 0
            p_cnt = 0
            m = marker_core_cov[
                (marker_core_cov["source_pdf_name"] == pdf)
                & (marker_core_cov["normalized_metric_name"] == metric)
            ]
            if not m.empty:
                m_cnt = int(m.iloc[0]["marker_row_count"])
            p = pdfp_core_cov[
                (pdfp_core_cov["source_pdf_name"] == pdf)
                & (pdfp_core_cov["core_metric"] == metric)
            ]
            if not p.empty:
                p_cnt = int(p.iloc[0]["pdfplumber_row_count"])
            core_rows.append(
                {
                    "pdf_file_name": pdf,
                    "core_metric": metric,
                    "marker_present": m_cnt > 0,
                    "pdfplumber_present": p_cnt > 0,
                    "marker_row_count": m_cnt,
                    "pdfplumber_row_count": p_cnt,
                    "marker_only": m_cnt > 0 and p_cnt == 0,
                    "pdfplumber_only": p_cnt > 0 and m_cnt == 0,
                }
            )
    core_cmp_df = pd.DataFrame(core_rows).fillna("")

    # Conflicts for Marker (inferred from structured rows).
    marker_conflict_rows: List[Dict[str, Any]] = []
    for pdf in pdf_list:
        mdf = marker_full[marker_full["source_pdf_name"] == pdf].copy()
        if mdf.empty:
            marker_conflict_rows.append(
                {
                    "pdf_file_name": pdf,
                    "marker_duplicate_key_count": 0,
                    "marker_value_mismatch_count": 0,
                    "marker_unit_conflict_count": 0,
                    "marker_year_conflict_count": 0,
                }
            )
            continue
        grp = mdf.groupby(["normalized_metric_name", "year"])
        dup_key_count = 0
        value_mismatch_count = 0
        unit_conflict_count = 0
        for _, g in grp:
            if len(g) > 1:
                dup_key_count += 1
            vals = set(x for x in g["value_raw"].map(_norm).tolist() if x != "")
            if len(vals) > 1:
                value_mismatch_count += 1
            units = set(x for x in g["inferred_unit"].map(_norm).tolist() if x != "")
            if len(units) > 1:
                unit_conflict_count += 1
        year_conflict_count = int(
            mdf["confidence_flags"]
            .map(_norm)
            .str.contains("suspicious_year", regex=False)
            .sum()
        )
        marker_conflict_rows.append(
            {
                "pdf_file_name": pdf,
                "marker_duplicate_key_count": int(dup_key_count),
                "marker_value_mismatch_count": int(value_mismatch_count),
                "marker_unit_conflict_count": int(unit_conflict_count),
                "marker_year_conflict_count": int(year_conflict_count),
            }
        )
    marker_conf_df = pd.DataFrame(marker_conflict_rows).fillna("")

    # Per-pdf comparison.
    per_rows: List[Dict[str, Any]] = []
    for pdf in pdf_list:
        m_rows = int((marker_full["source_pdf_name"] == pdf).sum())
        m_high = int((marker_high["source_pdf_name"] == pdf).sum())
        m_block = int((marker_blocked["source_pdf_name"] == pdf).sum())
        m_dirty = int(
            marker_full[
                (marker_full["source_pdf_name"] == pdf)
                & (marker_full["confidence_flags"].map(_norm) != "ok")
            ].shape[0]
        )
        m_core_cov = int(
            core_cmp_df[
                (core_cmp_df["pdf_file_name"] == pdf)
                & (core_cmp_df["marker_present"] == True)
            ]["core_metric"].nunique()
        )
        p_cov = pdfp_per[pdfp_per["pdf_file_name"] == pdf]
        if p_cov.empty:
            continue
        p_row = p_cov.iloc[0]
        p_rows = _to_int(p_row.get("full_structured_row_count", 0))
        p_core_count = _to_int(p_row.get("core_metrics_candidate_count", 0))
        p_core_cov = int(
            core_cmp_df[
                (core_cmp_df["pdf_file_name"] == pdf)
                & (core_cmp_df["pdfplumber_present"] == True)
            ]["core_metric"].nunique()
        )
        p_zero = p_core_count == 0
        m_zero = m_core_cov == 0

        # conflicts
        mc = marker_conf_df[marker_conf_df["pdf_file_name"] == pdf].iloc[0]
        p_dup = _to_int(p_row.get("duplicate_key_count", 0))
        p_val = _to_int(p_row.get("value_mismatch_count", 0))
        p_unit = _to_int(p_row.get("unit_conflict_count", 0))
        p_year = _to_int(p_row.get("year_conflict_count", 0))

        # page 1 summary coverage.
        cov1 = vis_cov[(vis_cov["pdf_file_name"] == pdf) & (vis_cov["page_number"] == 1)]
        has_page1_summary_keyword = bool((cov1["summary_keyword_hit"] == True).any()) if not cov1.empty else False
        pdfp_page1_rows = int((pdfp_full[(pdfp_full["source_pdf_name"] == pdf) & (pdfp_full["page_number"].map(_to_int) == 1)]).shape[0])
        marker_page1_rows = int((marker_full[(marker_full["source_pdf_name"] == pdf) & (marker_full["page_number"].map(_to_int) == 1)]).shape[0])
        marker_page1_summary_rows = int(
            (
                marker_full[
                    (marker_full["source_pdf_name"] == pdf)
                    & (marker_full["page_number"].map(_to_int) == 1)
                    & (
                        marker_full["panel_label"].map(_norm).isin(["financial_summary", "valuation_metrics"])
                    )
                ]
            ).shape[0]
        )

        # multi-panel coverage
        multi_pages = vis_multi[vis_multi["pdf_file_name"] == pdf]
        multi_page_cnt = int(multi_pages["page_number"].nunique())
        multi_page_set = set(multi_pages["page_number"].map(_to_int).tolist())
        pdfp_multi_rows = int(
            pdfp_full[
                (pdfp_full["source_pdf_name"] == pdf)
                & (pdfp_full["page_number"].map(_to_int).isin(multi_page_set))
            ].shape[0]
        ) if multi_page_set else 0
        marker_multi_rows = int(
            marker_full[
                (marker_full["source_pdf_name"] == pdf)
                & (marker_full["page_number"].map(_to_int).isin(multi_page_set))
            ].shape[0]
        ) if multi_page_set else 0
        marker_multi_panel_rows = int(
            marker_full[
                (marker_full["source_pdf_name"] == pdf)
                & (marker_full["statement_type"].map(_norm).isin(["balance_sheet", "income_statement", "cash_flow_statement", "valuation_metrics"]))
            ].shape[0]
        )

        per_rows.append(
            {
                "pdf_file_name": pdf,
                "marker_row_count": m_rows,
                "pdfplumber_row_count": p_rows,
                "row_count_delta_marker_minus_pdfplumber": m_rows - p_rows,
                "marker_high_confidence_row_count": m_high,
                "pdfplumber_core_candidate_count": p_core_count,
                "marker_core_metric_coverage_count": m_core_cov,
                "pdfplumber_core_metric_coverage_count": p_core_cov,
                "marker_zero_candidate_like": m_zero,
                "pdfplumber_zero_candidate": p_zero,
                "marker_dirty_row_count": m_dirty,
                "marker_blocked_row_count": m_block,
                "pdfplumber_duplicate_key_count": p_dup,
                "marker_duplicate_key_count": _to_int(mc["marker_duplicate_key_count"]),
                "pdfplumber_value_mismatch_count": p_val,
                "marker_value_mismatch_count": _to_int(mc["marker_value_mismatch_count"]),
                "pdfplumber_unit_conflict_count": p_unit,
                "marker_unit_conflict_count": _to_int(mc["marker_unit_conflict_count"]),
                "pdfplumber_year_conflict_count": p_year,
                "marker_year_conflict_count": _to_int(mc["marker_year_conflict_count"]),
                "page1_has_summary_keyword": has_page1_summary_keyword,
                "pdfplumber_page1_rows": pdfp_page1_rows,
                "marker_page1_rows": marker_page1_rows,
                "marker_page1_summary_rows": marker_page1_summary_rows,
                "multi_panel_visual_page_count": multi_page_cnt,
                "pdfplumber_rows_on_multi_panel_pages": pdfp_multi_rows,
                "marker_rows_on_multi_panel_pages": marker_multi_rows,
                "marker_multi_panel_statement_rows": marker_multi_panel_rows,
            }
        )
    per_df = pd.DataFrame(per_rows).fillna("")

    # conflict comparison
    conflict_df = per_df[
        [
            "pdf_file_name",
            "pdfplumber_duplicate_key_count",
            "marker_duplicate_key_count",
            "pdfplumber_value_mismatch_count",
            "marker_value_mismatch_count",
            "pdfplumber_unit_conflict_count",
            "marker_unit_conflict_count",
            "pdfplumber_year_conflict_count",
            "marker_year_conflict_count",
        ]
    ].copy()

    # marker-only improvements / pdfplumber advantages
    marker_improve_rows: List[Dict[str, Any]] = []
    pdfplumber_adv_rows: List[Dict[str, Any]] = []
    for _, r in per_df.iterrows():
        reasons_m: List[str] = []
        reasons_p: List[str] = []
        if _to_int(r["marker_core_metric_coverage_count"]) > _to_int(r["pdfplumber_core_metric_coverage_count"]):
            reasons_m.append("core_metric_coverage_higher")
        if _to_int(r["marker_rows_on_multi_panel_pages"]) > _to_int(r["pdfplumber_rows_on_multi_panel_pages"]):
            reasons_m.append("multi_panel_page_row_coverage_higher")
        if _to_int(r["marker_page1_summary_rows"]) > 0 and _to_int(r["pdfplumber_page1_rows"]) == 0:
            reasons_m.append("page1_summary_rows_recovered")
        if _to_int(r["marker_zero_candidate_like"]) < _to_int(r["pdfplumber_zero_candidate"]):
            reasons_m.append("zero_candidate_reduced")

        if _to_int(r["pdfplumber_core_metric_coverage_count"]) > _to_int(r["marker_core_metric_coverage_count"]):
            reasons_p.append("core_metric_coverage_higher")
        if _to_int(r["pdfplumber_rows_on_multi_panel_pages"]) > _to_int(r["marker_rows_on_multi_panel_pages"]):
            reasons_p.append("multi_panel_page_row_coverage_higher")
        if _to_int(r["pdfplumber_duplicate_key_count"]) < _to_int(r["marker_duplicate_key_count"]):
            reasons_p.append("lower_duplicate_key_conflicts")
        if _to_int(r["pdfplumber_value_mismatch_count"]) < _to_int(r["marker_value_mismatch_count"]):
            reasons_p.append("lower_value_mismatch_conflicts")

        if reasons_m:
            rr = dict(r)
            rr["marker_only_improvement_reasons"] = "|".join(reasons_m)
            marker_improve_rows.append(rr)
        if reasons_p:
            rr = dict(r)
            rr["pdfplumber_only_advantage_reasons"] = "|".join(reasons_p)
            pdfplumber_adv_rows.append(rr)

    marker_improve_df = pd.DataFrame(marker_improve_rows).fillna("")
    pdfplumber_adv_df = pd.DataFrame(pdfplumber_adv_rows).fillna("")

    _write_excel(OUT_PER_PDF, {"per_pdf_comparison": per_df})
    _write_excel(OUT_CORE, {"core_metric_coverage_comparison": core_cmp_df})
    _write_excel(OUT_CONFLICT, {"conflict_comparison": conflict_df})
    _write_excel(OUT_MARKER_IMPROVE, {"marker_only_improvements": marker_improve_df})
    _write_excel(OUT_PDFPLUMBER_ADV, {"pdfplumber_only_advantages": pdfplumber_adv_df})

    marker_win_pdf_count = int(len(marker_improve_df["pdf_file_name"].unique())) if not marker_improve_df.empty else 0
    pdfplumber_win_pdf_count = int(len(pdfplumber_adv_df["pdf_file_name"].unique())) if not pdfplumber_adv_df.empty else 0
    fusion_reco = "use_parser_fusion_incremental"
    if marker_win_pdf_count >= 6 and pdfplumber_win_pdf_count <= 2:
        fusion_reco = "marker_primary_pdfplumber_backfill"
    elif pdfplumber_win_pdf_count >= 6 and marker_win_pdf_count <= 2:
        fusion_reco = "pdfplumber_primary_marker_fallback"

    fusion_lines = [
        "# 306D Fusion Next-Step Recommendation",
        "",
        f"- recommendation: {fusion_reco}",
        f"- marker_improvement_pdf_count: {marker_win_pdf_count}",
        f"- pdfplumber_advantage_pdf_count: {pdfplumber_win_pdf_count}",
        "",
        "## Suggested Next Step",
    ]
    if fusion_reco == "use_parser_fusion_incremental":
        fusion_lines.append("- Keep parser fusion: use Marker outputs for multi-panel/summary-heavy pages and keep pdfplumber for low-conflict baseline rows.")
    elif fusion_reco == "marker_primary_pdfplumber_backfill":
        fusion_lines.append("- Shift to Marker-primary for structured extraction; retain pdfplumber as fallback for low-dirty high-stability pages.")
    else:
        fusion_lines.append("- Keep pdfplumber-primary baseline; use Marker where pdfplumber has zero candidates or weak multi-panel coverage.")
    OUT_FUSION_MD.write_text("\n".join(fusion_lines) + "\n", encoding="utf-8")

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "marker_rerun_executed": False,
            "pdfplumber_rerun_executed": False,
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
        "stage": "EVAL-306D",
        "mode": "marker_vs_pdfplumber_structured_regression",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "eval_306c_summary_loaded": bool(_norm(s306c.get("stage")) == "EVAL-306C"),
        "eval1b_summary_loaded": bool(_norm(s1b.get("stage")) == "EVAL-1B"),
        "pdf_count": int(len(pdf_list)),
        "marker_total_rows": int(len(marker_full)),
        "pdfplumber_total_rows": int(len(pdfp_full)),
        "marker_high_confidence_rows": int(len(marker_high)),
        "pdfplumber_total_core_candidate_count": int(_to_int(s1b.get("new_core_metrics_candidate_total_rows", 0))),
        "marker_zero_candidate_pdf_count": int((per_df["marker_zero_candidate_like"] == True).sum()) if not per_df.empty else 0,
        "pdfplumber_zero_candidate_pdf_count": int((per_df["pdfplumber_zero_candidate"] == True).sum()) if not per_df.empty else 0,
        "marker_dirty_row_count": int(len(marker_full[marker_full["confidence_flags"].map(_norm) != "ok"])),
        "marker_blocked_row_count": int(len(marker_blocked)),
        "marker_improvement_pdf_count": marker_win_pdf_count,
        "pdfplumber_advantage_pdf_count": pdfplumber_win_pdf_count,
        "fusion_recommendation": fusion_reco,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306D Marker vs pdfplumber Structured Regression",
        "",
        f"- pdf_count: {summary['pdf_count']}",
        f"- marker_total_rows: {summary['marker_total_rows']}",
        f"- pdfplumber_total_rows: {summary['pdfplumber_total_rows']}",
        f"- marker_high_confidence_rows: {summary['marker_high_confidence_rows']}",
        f"- pdfplumber_total_core_candidate_count: {summary['pdfplumber_total_core_candidate_count']}",
        f"- marker_zero_candidate_pdf_count: {summary['marker_zero_candidate_pdf_count']}",
        f"- pdfplumber_zero_candidate_pdf_count: {summary['pdfplumber_zero_candidate_pdf_count']}",
        f"- marker_dirty_row_count: {summary['marker_dirty_row_count']}",
        f"- marker_blocked_row_count: {summary['marker_blocked_row_count']}",
        f"- marker_improvement_pdf_count: {summary['marker_improvement_pdf_count']}",
        f"- pdfplumber_advantage_pdf_count: {summary['pdfplumber_advantage_pdf_count']}",
        f"- fusion_recommendation: {summary['fusion_recommendation']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306d_summary_json: {OUT_SUMMARY}")
    print(f"eval_306d_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
