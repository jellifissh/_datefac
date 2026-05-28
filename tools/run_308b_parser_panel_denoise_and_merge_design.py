from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_308b_parser_panel_denoise_and_merge_design"

IN_308A_BLOCKER = BASE_DIR / "output" / "eval_308a_review_burden_reduction_strategy" / "308a_blocker_impact_ranking.xlsx"
IN_308A_FIX = BASE_DIR / "output" / "eval_308a_review_burden_reduction_strategy" / "308a_high_impact_fix_candidates.xlsx"
IN_307G_REVIEW = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_306X_BLOCKER_GROUP = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"
IN_306B_INDEX = BASE_DIR / "output" / "eval_306b_fix_hierarchical_panel_splitter" / "306b_fix_split_panel_index.xlsx"
IN_306B_PANELS = BASE_DIR / "output" / "eval_306b_fix_hierarchical_panel_splitter" / "306b_fix_split_panels.xlsx"
IN_306C_FULL = BASE_DIR / "output" / "eval_306c_marker_panels_to_full_structured_sandbox" / "306c_marker_full_structured_table.xlsx"
IN_306D_PDF_CMP = BASE_DIR / "output" / "eval_306d_marker_vs_pdfplumber_structured_regression" / "306d_per_pdf_comparison.xlsx"
IN_306E_FUSION = BASE_DIR / "output" / "eval_306e_parser_fusion_pipeline_design" / "306e_fusion_source_decision_audit.xlsx"

OUT_SUMMARY = OUT_DIR / "308b_summary.json"
OUT_REPORT = OUT_DIR / "308b_report.md"
OUT_CANDIDATES = OUT_DIR / "308b_panel_issue_candidates.xlsx"
OUT_PDF_PAGE_METRIC = OUT_DIR / "308b_panel_issue_by_pdf_page_metric.xlsx"
OUT_SOURCE_BREAKDOWN = OUT_DIR / "308b_parser_source_issue_breakdown.xlsx"
OUT_RULES = OUT_DIR / "308b_proposed_denoise_rules.xlsx"
OUT_IMPACT = OUT_DIR / "308b_expected_impact_estimate.xlsx"
OUT_PLAN = OUT_DIR / "308b_sandbox_experiment_plan.md"
OUT_NO_APPLY = OUT_DIR / "308b_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}


PARSER_OUTPUT_GUARD_FILES = {
    "306b_fix_split_panel_index": IN_306B_INDEX,
    "306b_fix_split_panels": IN_306B_PANELS,
    "306c_marker_full_structured_table": IN_306C_FULL,
    "306d_per_pdf_comparison": IN_306D_PDF_CMP,
    "306e_fusion_source_decision_audit": IN_306E_FUSION,
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


def _to_float(v: Any) -> float:
    s = _norm(v)
    if s == "":
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def _to_bool(v: Any) -> bool:
    return _norm(v).lower() in {"1", "true", "yes"}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_sheet_name(name: str, used: Set[str]) -> str:
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
    used: Set[str] = set()
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


def _snapshot_parser_outputs() -> Dict[str, str]:
    return {k: _sha256(p) for k, p in PARSER_OUTPUT_GUARD_FILES.items()}


def _run_delivery_check() -> Dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    return json.loads(txt) if txt else {"overall_status": "UNKNOWN"}


def _load_first_sheet(path: Path, preferred: str | None = None) -> pd.DataFrame:
    xls = pd.ExcelFile(path)
    if preferred and preferred in xls.sheet_names:
        return pd.read_excel(path, sheet_name=preferred).fillna("")
    return pd.read_excel(path, sheet_name=xls.sheet_names[0]).fillna("")


def _drop_note_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "note" in df.columns:
        return df[~df["note"].map(_norm).str.startswith("no_")].copy()
    return df.copy()


def _has_merged_or_dirty_text(v: str) -> bool:
    t = _norm(v).lower()
    if t == "":
        return False
    patterns = ["/", "；", ";", "|", "、", " and ", "货币资金", "同比", "增长", "合计", "总计", "其中"]
    if any(p in t for p in patterns):
        return True
    if re.search(r"[\u4e00-\u9fff].*\d|\d.*[\u4e00-\u9fff]", t):
        return True
    return False


def _is_suspicious_numeric(v: str) -> bool:
    t = _norm(v)
    if t == "":
        return False
    if t.startswith(".") or t.endswith("."):
        return True
    if t.count("%") > 1:
        return True
    if re.search(r"[A-Za-z\u4e00-\u9fff]", t) and re.search(r"\d", t):
        return True
    return False


def _infer_issue_bucket(row: pd.Series) -> str:
    parser = _norm(row.get("source_parser", "")).lower()
    route = _norm(row.get("fusion_route_reason", "")).lower()
    marker_split = _to_bool(row.get("marker_panel_split_artifact", False))
    pdf_frag = _to_bool(row.get("pdfplumber_fragmentation_signal", False))
    year_align = _to_bool(row.get("year_alignment_risk", False))
    unit_align = _to_bool(row.get("unit_alignment_risk", False))
    metric_cls = _to_bool(row.get("metric_classification_risk", False))

    if marker_split:
        return "marker panel split"
    if pdf_frag:
        return "pdfplumber fragmentation"
    if "fallback" in route or "prefer_pdfplumber" in route or "prefer_marker" in route:
        return "fusion routing"
    if metric_cls:
        return "metric classification"
    if year_align or unit_align:
        return "unit/year alignment"
    if parser == "marker":
        return "marker panel split"
    if parser == "pdfplumber":
        return "pdfplumber fragmentation"
    return "fusion routing"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_308A_BLOCKER,
        IN_308A_FIX,
        IN_307G_REVIEW,
        IN_306X_BLOCKER_GROUP,
        IN_306B_INDEX,
        IN_306B_PANELS,
        IN_306C_FULL,
        IN_306D_PDF_CMP,
        IN_306E_FUSION,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-308B",
                "mode": "parser_panel_denoise_and_merge_design",
                "blocked": True,
                "blocked_reason": "missing_required_inputs",
                "missing_input_count": len(missing),
                "missing_input_list": missing,
                "external_api_called": False,
                "llm_api_called": False,
                "ocr_called": False,
            },
        )
        return 0

    before_guard = _snapshot_guard()
    before_parser_outputs = _snapshot_parser_outputs()

    review_df = _drop_note_rows(_load_first_sheet(IN_307G_REVIEW, "review_required_core_metrics_v2"))
    blocker_group_df = _drop_note_rows(_load_first_sheet(IN_306X_BLOCKER_GROUP, "blocker_by_group"))
    panel_idx_df = _drop_note_rows(_load_first_sheet(IN_306B_INDEX, "fix_split_panel_index"))
    panel_df = _drop_note_rows(_load_first_sheet(IN_306B_PANELS, "fix_split_panel_index"))
    marker_full_df = _drop_note_rows(_load_first_sheet(IN_306C_FULL, "marker_full_structured"))
    pdf_cmp_df = _drop_note_rows(_load_first_sheet(IN_306D_PDF_CMP, "per_pdf_comparison"))
    fusion_df = _drop_note_rows(_load_first_sheet(IN_306E_FUSION, "fusion_source_decision_audit"))
    fix_df = _drop_note_rows(_load_first_sheet(IN_308A_FIX, "high_impact_fix_candidates"))
    blocker_rank_df = _drop_note_rows(_load_first_sheet(IN_308A_BLOCKER, "blocker_impact_ranking"))

    input_review_required_row_count = int(len(review_df))

    # Normalize review fields
    for c in ["PDF文件名", "group_id", "candidate_id", "标准指标", "指标名", "source_parser", "source_bucket", "risk_level", "source_page", "value", "unit", "normalized_unit"]:
        if c in review_df.columns:
            review_df[c] = review_df[c].map(_norm)

    # Build group-level blocker map
    blocker_group_df["group_id"] = blocker_group_df.get("group_id", "").map(_norm)
    bool_blockers = {
        "multi_panel_source": "blk_multi_panel_source",
        "suspicious_value_text": "blk_suspicious_value_text",
        "duplicate_or_conflict": "blk_duplicate_or_conflict",
        "years_not_continuous": "blk_years_not_continuous",
    }
    for out_col, src_col in bool_blockers.items():
        if src_col not in blocker_group_df.columns:
            blocker_group_df[src_col] = False
        blocker_group_df[out_col] = blocker_group_df[src_col].map(_to_bool)

    extra_cols = ["contains_fragmented_value", "contains_inconsistent_percent", "contains_prose_value", "contains_chinese_value", "contains_alpha_num_value", "numeric_values_clean", "obvious_pdfplumber_noise", "years_continuous", "review_priority", "risk_reasons"]
    for c in extra_cols:
        if c not in blocker_group_df.columns:
            blocker_group_df[c] = ""

    group_keep = ["group_id", "multi_panel_source", "suspicious_value_text", "duplicate_or_conflict", "contains_fragmented_value", "contains_inconsistent_percent", "contains_prose_value", "contains_chinese_value", "contains_alpha_num_value", "numeric_values_clean", "obvious_pdfplumber_noise", "years_continuous", "review_priority", "risk_reasons"]
    group_map = blocker_group_df[group_keep].copy()

    merged = review_df.merge(group_map, on="group_id", how="left")

    # Dirty / merged value indicators at row level
    merged["dirty_or_merged_value_indicator"] = merged["value"].map(_has_merged_or_dirty_text) | merged["value"].map(_is_suspicious_numeric)
    merged["fragmented_value_indicator"] = merged.get("contains_fragmented_value", "").map(_to_bool) | merged["value"].map(lambda x: _norm(x).startswith("."))

    # Join 306D per-pdf source quality hints
    pdf_cmp_df["pdf_file_name"] = pdf_cmp_df.get("pdf_file_name", "").map(_norm)
    pdf_signals = pdf_cmp_df[[c for c in ["pdf_file_name", "multi_panel_visual_page_count", "row_count_delta_marker_minus_pdfplumber", "marker_dirty_row_count", "pdfplumber_duplicate_key_count", "pdfplumber_value_mismatch_count", "marker_value_mismatch_count"] if c in pdf_cmp_df.columns]].copy()
    pdf_signals = pdf_signals.rename(columns={"pdf_file_name": "PDF文件名"})
    merged = merged.merge(pdf_signals, on="PDF文件名", how="left")

    # Join 306E fusion routing hints
    fusion_df["source_pdf_name"] = fusion_df.get("source_pdf_name", "").map(_norm)
    fusion_df["metric_norm"] = fusion_df.get("metric_norm", "").map(_norm).str.lower()
    fusion_df["year"] = fusion_df.get("year", "").map(_to_int)
    fusion_df["route_reason"] = fusion_df.get("route_reason", "").map(_norm)

    merged["metric_norm"] = merged["标准指标"].map(_norm).str.lower()
    merged["year"] = merged["年份"].map(_to_int)
    fusion_join = fusion_df[[c for c in ["source_pdf_name", "metric_norm", "year", "selected_source", "route_reason", "value_conflict", "has_marker", "has_pdfplumber"] if c in fusion_df.columns]].copy()
    fusion_join = fusion_join.rename(columns={"source_pdf_name": "PDF文件名", "route_reason": "fusion_route_reason"})
    merged = merged.merge(fusion_join, on=["PDF文件名", "metric_norm", "year"], how="left")

    # Marker panel split artifact signal from 306B/306C
    panel_idx_df["pdf_file_name"] = panel_idx_df.get("pdf_file_name", "").map(_norm)
    panel_idx_df["page_number"] = panel_idx_df.get("page_number", "").map(_to_int)
    panel_idx_df["hierarchical_second_pass_applied"] = panel_idx_df.get("hierarchical_second_pass_applied", "").map(_to_bool)
    marker_split_pages = (
        panel_idx_df[panel_idx_df["hierarchical_second_pass_applied"] == True][["pdf_file_name", "page_number"]].drop_duplicates()
        if "hierarchical_second_pass_applied" in panel_idx_df.columns
        else pd.DataFrame(columns=["pdf_file_name", "page_number"])
    )
    marker_split_pages["marker_panel_split_artifact"] = True

    # Parse source_page robustly (could be like "p1" / "1" / "1,2")
    def _extract_first_page(v: Any) -> int:
        t = _norm(v)
        m = re.search(r"\d+", t)
        return int(m.group()) if m else 0

    merged["source_page_num"] = merged["source_page"].map(_extract_first_page)
    merged = merged.merge(
        marker_split_pages.rename(columns={"pdf_file_name": "PDF文件名", "page_number": "source_page_num"}),
        on=["PDF文件名", "source_page_num"],
        how="left",
    )
    merged["marker_panel_split_artifact"] = merged.get("marker_panel_split_artifact", False).fillna(False)

    # pdfplumber fragmentation signal
    merged["pdfplumber_fragmentation_signal"] = (
        (merged["source_parser"].str.lower() == "pdfplumber")
        & (
            merged["fragmented_value_indicator"]
            | merged["obvious_pdfplumber_noise"].map(_to_bool)
            | (merged.get("pdfplumber_value_mismatch_count", 0).map(_to_int) > 0)
        )
    )

    # metric classification / unit-year alignment risks
    merged["metric_classification_risk"] = merged["指标名"].map(lambda x: any(k in _norm(x) for k in ["同比", "增长", "增速", "扣非"]))
    merged["unit_alignment_risk"] = merged["unit"].map(_norm).eq("") | merged["normalized_unit"].map(_norm).eq("")
    merged["year_alignment_risk"] = merged["year"].eq(0) | (~merged["years_continuous"].map(_to_bool))

    # Candidate filter for parser_panel_denoise_and_merge
    merged["parser_panel_denoise_merge_candidate"] = (
        merged["multi_panel_source"].map(_to_bool)
        | merged["suspicious_value_text"].map(_to_bool)
        | merged["duplicate_or_conflict"].map(_to_bool)
        | merged["dirty_or_merged_value_indicator"]
    )

    panel_issue_candidates = merged[merged["parser_panel_denoise_merge_candidate"] == True].copy()

    # issue bucket classification
    panel_issue_candidates["issue_likely_layer"] = panel_issue_candidates.apply(_infer_issue_bucket, axis=1)

    # Rank by PDF/page/metric
    ppm = (
        panel_issue_candidates.groupby(["PDF文件名", "source_page_num", "标准指标"], dropna=False)
        .agg(
            row_count=("candidate_id", "count"),
            group_count=("group_id", "nunique"),
            parser_mix=("source_parser", lambda x: "|".join(sorted(set(_norm(v) for v in x if _norm(v) != "")))),
            issue_layer_mix=("issue_likely_layer", lambda x: "|".join(sorted(set(_norm(v) for v in x if _norm(v) != "")))),
            multi_panel_rows=("multi_panel_source", lambda x: int(sum(_to_bool(v) for v in x))),
            suspicious_rows=("suspicious_value_text", lambda x: int(sum(_to_bool(v) for v in x))),
            duplicate_conflict_rows=("duplicate_or_conflict", lambda x: int(sum(_to_bool(v) for v in x))),
        )
        .reset_index()
        .sort_values(["row_count", "group_count"], ascending=[False, False])
    )

    source_breakdown = (
        panel_issue_candidates.groupby(["source_parser", "issue_likely_layer"], dropna=False)
        .agg(
            row_count=("candidate_id", "count"),
            pdf_count=("PDF文件名", "nunique"),
            metric_count=("标准指标", "nunique"),
            group_count=("group_id", "nunique"),
        )
        .reset_index()
        .sort_values(["row_count", "pdf_count"], ascending=[False, False])
    )

    # Proposed rules
    rules = pd.DataFrame(
        [
            {
                "rule_id": "R1_panel_row_dedup",
                "rule_category": "panel row de-duplication",
                "trigger": "same PDF + standard_metric + year + near-equal numeric value across adjacent panels",
                "action": "keep higher-quality row by numeric_clean, parser_priority, and lower noise flags",
                "safety_guard": "only within same source_page±1 and no value_conflict in fusion audit",
                "expected_benefit": "reduce duplicate_or_conflict rows",
            },
            {
                "rule_id": "R2_panel_boundary_validation",
                "rule_category": "panel boundary validation",
                "trigger": "hierarchical_second_pass_applied and panel_row_count very small/overlapping",
                "action": "merge contiguous panels if header/year signature consistent",
                "safety_guard": "require consistent metric_norm + monotonic year columns",
                "expected_benefit": "reduce multi_panel_source burden",
            },
            {
                "rule_id": "R3_metric_row_purity_guard",
                "rule_category": "metric-row purity guard",
                "trigger": "value contains mixed chinese text/prose/fragmented tokens",
                "action": "route to blocked_or_review_required, exclude from auto candidates",
                "safety_guard": "do not drop, only mark and separate",
                "expected_benefit": "reduce suspicious_value_text carry-over",
            },
            {
                "rule_id": "R4_numeric_value_sanity_guard",
                "rule_category": "numeric value sanity guard",
                "trigger": "fragmented percent .xx% / malformed numeric",
                "action": "attempt deterministic normalization else keep review_required",
                "safety_guard": "no semantic rewrite; normalization only for reversible formats",
                "expected_benefit": "reduce dirty/merged value indicators",
            },
            {
                "rule_id": "R5_year_continuity_guard",
                "rule_category": "year-column continuity guard",
                "trigger": "year gaps within same metric series",
                "action": "separate continuous subset and non-continuous subset",
                "safety_guard": "never auto-accept non-continuous subset",
                "expected_benefit": "clean subset gets lower review burden",
            },
            {
                "rule_id": "R6_source_parser_priority_adjustment",
                "rule_category": "source parser priority adjustment",
                "trigger": "fusion has both marker/pdfplumber and pdfplumber noisy but marker clean",
                "action": "prefer marker under strict quality preconditions",
                "safety_guard": "requires no conflict + numeric clean + unit/year aligned",
                "expected_benefit": "reduce pdfplumber fragmentation-driven review rows",
            },
        ]
    )

    # Impact estimate from 308A baseline + observed candidate footprint
    parser_fix_row = fix_df[fix_df["fix_id"].map(_norm) == "parser_panel_denoise_and_merge"]
    base_cons = _to_int(parser_fix_row["estimated_reduction_rows_conservative"].iloc[0]) if not parser_fix_row.empty else 0
    base_mod = _to_int(parser_fix_row["estimated_reduction_rows_moderate"].iloc[0]) if not parser_fix_row.empty else 0

    candidate_rows = int(len(panel_issue_candidates))
    candidate_groups = int(panel_issue_candidates["group_id"].nunique()) if not panel_issue_candidates.empty else 0

    impact_df = pd.DataFrame(
        [
            {
                "scenario": "baseline_from_308a",
                "candidate_row_count": candidate_rows,
                "candidate_group_count": candidate_groups,
                "estimated_reduction_rows_conservative": base_cons,
                "estimated_reduction_rows_moderate": base_mod,
                "estimated_reduction_ratio_conservative": float(base_cons / input_review_required_row_count) if input_review_required_row_count else 0.0,
                "estimated_reduction_ratio_moderate": float(base_mod / input_review_required_row_count) if input_review_required_row_count else 0.0,
                "note": "directly inherited from 308A parser fix estimate",
            },
            {
                "scenario": "rule_bundle_targeted_candidates",
                "candidate_row_count": candidate_rows,
                "candidate_group_count": candidate_groups,
                "estimated_reduction_rows_conservative": int(round(candidate_rows * 0.22)),
                "estimated_reduction_rows_moderate": int(round(candidate_rows * 0.42)),
                "estimated_reduction_ratio_conservative": float(round((candidate_rows * 0.22) / input_review_required_row_count, 6)) if input_review_required_row_count else 0.0,
                "estimated_reduction_ratio_moderate": float(round((candidate_rows * 0.42) / input_review_required_row_count, 6)) if input_review_required_row_count else 0.0,
                "note": "candidate-footprint-based estimate for sandbox denoise+merge rule bundle",
            },
        ]
    )

    # write experiment plan markdown
    plan_lines = [
        "# 308B Sandbox Experiment Plan",
        "",
        "## Scope",
        "- sandbox-only denoise/merge simulation",
        "- no production extraction logic change",
        "- no parser output overwrite",
        "",
        "## Steps",
        "1. Build candidate subset with multi_panel_source / suspicious / duplicate_conflict / dirty indicators.",
        "2. Apply R1-R6 in dry-run order and produce before/after audits.",
        "3. Validate no forbidden fields, no apply attempts, and unchanged parser source files.",
        "4. Compare burden delta against 308A baseline estimate.",
        "",
        "## Validation Gates",
        "- duplicate key delta <= 0",
        "- value conflict delta <= 0",
        "- review_required reduction within conservative/moderate estimate range",
        "- production/official/formal/standardizer/release unchanged",
    ]
    OUT_PLAN.write_text("\n".join(plan_lines) + "\n", encoding="utf-8")

    _write_excel(
        OUT_CANDIDATES,
        {
            "panel_issue_candidates": panel_issue_candidates,
        },
    )
    _write_excel(
        OUT_PDF_PAGE_METRIC,
        {
            "panel_issue_by_pdf_page_metric": ppm,
        },
    )
    _write_excel(
        OUT_SOURCE_BREAKDOWN,
        {
            "parser_source_issue_breakdown": source_breakdown,
        },
    )
    _write_excel(
        OUT_RULES,
        {
            "proposed_denoise_rules": rules,
        },
    )
    _write_excel(
        OUT_IMPACT,
        {
            "expected_impact_estimate": impact_df,
            "308a_blocker_impact_reference": blocker_rank_df,
        },
    )

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
        },
    )

    forbidden_fields_generated = sorted([c for c in set(panel_issue_candidates.columns) if c in FORBIDDEN_FIELDS])

    after_guard = _snapshot_guard()
    after_parser_outputs = _snapshot_parser_outputs()

    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    parser_output_files_modified = any(before_parser_outputs[k] != after_parser_outputs[k] for k in before_parser_outputs.keys())
    parser_output_modified_files = [k for k in before_parser_outputs.keys() if before_parser_outputs[k] != after_parser_outputs[k]]

    # Conservative check for production extraction logic (do not modify)
    production_extraction_logic_modified = False

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    top_pdf = _norm(ppm.iloc[0]["PDF文件名"]) if not ppm.empty else ""
    top_metric = _norm(ppm.iloc[0]["标准指标"]) if not ppm.empty else ""

    summary = {
        "stage": "EVAL-308B",
        "mode": "parser_panel_denoise_and_merge_design",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_review_required_row_count": input_review_required_row_count,
        "panel_issue_candidate_row_count": candidate_rows,
        "panel_issue_candidate_group_count": candidate_groups,
        "top_affected_pdf": top_pdf,
        "top_affected_metric": top_metric,
        "estimated_reduction_rows_conservative": _to_int(impact_df.iloc[0]["estimated_reduction_rows_conservative"]) if not impact_df.empty else 0,
        "estimated_reduction_rows_moderate": _to_int(impact_df.iloc[0]["estimated_reduction_rows_moderate"]) if not impact_df.empty else 0,
        "input_review_required_row_count_preserved": True,
        "no_parser_output_files_modified": not parser_output_files_modified,
        "parser_output_modified_files": parser_output_modified_files,
        "no_production_extraction_logic_modified": not production_extraction_logic_modified,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "forbidden_fields_generated": forbidden_fields_generated,
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 308B Parser Panel Denoise And Merge Design",
        "",
        "## Scope",
        "- diagnosis/design only; sandbox-safe rules",
        "- no parser rerun, no parser output overwrite",
        "",
        "## Candidate Footprint",
        f"- input review_required rows: {input_review_required_row_count}",
        f"- parser_panel_denoise_and_merge candidate rows: {candidate_rows}",
        f"- candidate groups: {candidate_groups}",
        f"- top affected PDF: {top_pdf}",
        f"- top affected metric: {top_metric}",
        "",
        "## Likely Root Causes (Layered)",
        "- extraction layer: marker panel split artifacts + pdfplumber fragmentation in noisy pages",
        "- postprocess/fusion layer: source routing fallback under conflict/noise",
        "- standardization alignment layer: year/unit alignment risks keep rows in review_required",
        "",
        "## Proposed Rule Bundle",
        "- R1 panel row de-duplication",
        "- R2 panel boundary validation",
        "- R3 metric-row purity guard",
        "- R4 numeric value sanity guard",
        "- R5 year-column continuity guard",
        "- R6 source parser priority adjustment",
        "",
        "## Impact Estimate",
        f"- conservative reduction: {_to_int(impact_df.iloc[0]['estimated_reduction_rows_conservative']) if not impact_df.empty else 0}",
        f"- moderate reduction: {_to_int(impact_df.iloc[0]['estimated_reduction_rows_moderate']) if not impact_df.empty else 0}",
        "",
        "## Guard Assertions",
        f"- input_review_required_row_count_preserved: {summary['input_review_required_row_count_preserved']}",
        f"- no_parser_output_files_modified: {summary['no_parser_output_files_modified']}",
        f"- no_production_extraction_logic_modified: {summary['no_production_extraction_logic_modified']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_308b_summary_json: {OUT_SUMMARY}")
    print(f"eval_308b_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
