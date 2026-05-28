from __future__ import annotations

import hashlib
import json
import random
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
OUT_DIR = BASE_DIR / "output" / "eval_308d_panel_denoise_rescue_safety_validation"

IN_308C_RESCUE = BASE_DIR / "output" / "eval_308c_parser_panel_denoise_rule_simulation" / "308c_would_rescue_from_review.xlsx"
IN_308C_RULE_HIT = BASE_DIR / "output" / "eval_308c_parser_panel_denoise_rule_simulation" / "308c_denoise_rule_hit_audit.xlsx"
IN_308C_CONFLICT = BASE_DIR / "output" / "eval_308c_parser_panel_denoise_rule_simulation" / "308c_conflict_audit.xlsx"
IN_308C_IMPACT = BASE_DIR / "output" / "eval_308c_parser_panel_denoise_rule_simulation" / "308c_impact_estimate.xlsx"
IN_308B_PPM = BASE_DIR / "output" / "eval_308b_parser_panel_denoise_and_merge_design" / "308b_panel_issue_by_pdf_page_metric.xlsx"
IN_307G_FINAL = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_final_core_metric_preview_v2.xlsx"
IN_307G_REVIEW = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_306L_GROUP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"
IN_306X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"

OUT_SUMMARY = OUT_DIR / "308d_summary.json"
OUT_REPORT = OUT_DIR / "308d_report.md"
OUT_SCORED = OUT_DIR / "308d_rescue_safety_scored_rows.xlsx"
OUT_SAMPLE = OUT_DIR / "308d_manual_spot_check_sample.xlsx"
OUT_RISK_METRIC = OUT_DIR / "308d_risk_distribution_by_metric.xlsx"
OUT_RISK_PDF = OUT_DIR / "308d_risk_distribution_by_pdf.xlsx"
OUT_RULE_AUDIT = OUT_DIR / "308d_rule_safety_audit.xlsx"
OUT_SILENT = OUT_DIR / "308d_silent_risk_audit.xlsx"
OUT_RECO = OUT_DIR / "308d_merge_readiness_recommendation.md"
OUT_NO_APPLY = OUT_DIR / "308d_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
PERCENT_METRICS = {"roe", "gross_margin", "margin", "growth_rate"}
MONETARY_METRICS = {"revenue", "net_profit", "attributable_net_profit", "operating_cash_flow", "total_assets", "total_liabilities"}
VALUATION_METRICS = {"pe", "pb", "ev_ebitda"}
TARGET_SAMPLE_SIZE_MIN = 30
TARGET_SAMPLE_SIZE_MAX = 40

# parser outputs from prior stages to guard unchanged
PARSER_OUTPUT_GUARD_FILES = {
    "306x_blocker_by_group": IN_306X_BLOCKER,
    "306l_fix_grouped_review_table": IN_306L_GROUP,
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


def _to_float(v: Any) -> float | None:
    s = _norm(v)
    if s == "":
        return None
    t = s.replace(",", "").replace("%", "")
    try:
        return float(t)
    except Exception:
        return None


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


def _extract_page_num(v: Any) -> int:
    t = _norm(v)
    m = re.search(r"\d+", t)
    return int(m.group()) if m else 0


def _risk_metric_family_mismatch(metric: str, unit: str, value: str) -> bool:
    m = _norm(metric).lower()
    u = _norm(unit).lower()
    v = _norm(value)
    is_percent_val = "%" in v
    if m in PERCENT_METRICS and u in {"multiple", "yuan_per_share"}:
        return True
    if m in VALUATION_METRICS and is_percent_val:
        return True
    if m in MONETARY_METRICS and u == "percent":
        return True
    return False


def _risk_unit_mismatch(metric: str, unit: str) -> bool:
    m = _norm(metric).lower()
    u = _norm(unit).lower()
    if m in PERCENT_METRICS and u not in {"percent", "%"}:
        return True
    if m in VALUATION_METRICS and u not in {"multiple", "x", "倍"}:
        return True
    if m in MONETARY_METRICS and u in {"", "unknown"}:
        return True
    return False


def _risk_abnormal_value(metric: str, value: str) -> bool:
    m = _norm(metric).lower()
    fv = _to_float(value)
    if fv is None:
        return True
    av = abs(fv)
    if m == "roe" and av > 100:
        return True
    if m == "gross_margin" and av > 100:
        return True
    if m == "eps" and av > 50:
        return True
    if m in {"pe", "pb", "ev_ebitda"} and av > 200:
        return True
    if m in MONETARY_METRICS and av > 1e9:  # unitless guard, conservative
        return True
    return False


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_308C_RESCUE,
        IN_308C_RULE_HIT,
        IN_308C_CONFLICT,
        IN_308C_IMPACT,
        IN_308B_PPM,
        IN_307G_FINAL,
        IN_307G_REVIEW,
        IN_306L_GROUP,
        IN_306X_BLOCKER,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-308D",
                "mode": "panel_denoise_rescue_safety_validation",
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
    final_before_hash = _sha256(IN_307G_FINAL)

    rescue_df = _drop_note_rows(_load_first_sheet(IN_308C_RESCUE, "would_rescue_from_review"))
    rule_hit_df = _drop_note_rows(_load_first_sheet(IN_308C_RULE_HIT, "denoise_rule_hit_audit"))
    conflict_df = _drop_note_rows(_load_first_sheet(IN_308C_CONFLICT, "conflict_audit"))
    impact_df = _drop_note_rows(_load_first_sheet(IN_308C_IMPACT, "impact_estimate"))
    ppm_df = _drop_note_rows(_load_first_sheet(IN_308B_PPM, "panel_issue_by_pdf_page_metric"))
    final_df = _drop_note_rows(_load_first_sheet(IN_307G_FINAL, "final_core_metric_preview_v2"))
    review_df = _drop_note_rows(_load_first_sheet(IN_307G_REVIEW, "review_required_core_metrics_v2"))
    group_df = _drop_note_rows(_load_first_sheet(IN_306L_GROUP, "grouped_review_table"))
    blocker_df = _drop_note_rows(_load_first_sheet(IN_306X_BLOCKER, "blocker_by_group"))

    for c in ["PDF文件名", "group_id", "candidate_id", "标准指标", "指标名", "source_parser", "source_page", "risk_level", "value", "unit", "normalized_unit", "source_bucket"]:
        if c in rescue_df.columns:
            rescue_df[c] = rescue_df[c].map(_norm)

    rescue_df["年份"] = rescue_df["年份"].map(_to_int)
    rescue_df["source_page_num"] = rescue_df["source_page"].map(_extract_page_num)

    input_would_rescue_row_count = int(len(rescue_df))

    # derive denoise_rule from rule hits in row columns
    def _derive_rule(row: pd.Series) -> str:
        tags = []
        if _to_bool(row.get("r1_panel_row_deduplication_hit", False)):
            tags.append("panel_row_deduplication")
        if _to_bool(row.get("r2_panel_boundary_validation_hit", False)):
            tags.append("panel_boundary_validation")
        if _to_bool(row.get("r4_numeric_value_sanity_guard_hit", False)):
            tags.append("numeric_value_sanity_guard")
        if _to_bool(row.get("r5_year_column_continuity_guard_hit", False)):
            tags.append("year_column_continuity_guard")
        if _to_bool(row.get("r6_source_parser_priority_adjustment_hit", False)):
            tags.append("source_parser_priority_adjustment")
        if _to_bool(row.get("r3_metric_row_purity_guard_hit", False)):
            tags.append("metric_row_purity_guard")
        return "|".join(tags) if tags else "none"

    rescue_df["denoise_rule"] = rescue_df.apply(_derive_rule, axis=1)

    # silent risk detection
    rescue_df["silent_risk_metric_family_mismatch"] = rescue_df.apply(
        lambda r: _risk_metric_family_mismatch(r.get("标准指标", ""), r.get("normalized_unit", ""), r.get("value", "")), axis=1
    )
    rescue_df["silent_risk_unit_mismatch"] = rescue_df.apply(
        lambda r: _risk_unit_mismatch(r.get("标准指标", ""), r.get("normalized_unit", "")), axis=1
    )
    rescue_df["silent_risk_abnormal_value_range"] = rescue_df.apply(
        lambda r: _risk_abnormal_value(r.get("标准指标", ""), r.get("value", "")), axis=1
    )

    # year sequence gap by (pdf, metric, group)
    rescue_df["year_series_key"] = rescue_df.apply(
        lambda r: f"{_norm(r.get('PDF文件名',''))}|{_norm(r.get('标准指标','')).lower()}|{_norm(r.get('group_id',''))}",
        axis=1,
    )
    year_gap_keys: Set[str] = set()
    for key, g in rescue_df.groupby("year_series_key", dropna=False):
        years = sorted(set(_to_int(v) for v in g["年份"].tolist() if _to_int(v) > 0))
        if len(years) >= 2:
            for i in range(len(years) - 1):
                if years[i + 1] - years[i] > 1:
                    year_gap_keys.add(_norm(key))
                    break
    rescue_df["silent_risk_year_sequence_gap"] = rescue_df["year_series_key"].map(lambda k: _norm(k) in year_gap_keys)

    # source page concentration risk: >60% rows of a PDF from same page
    page_concentration_keys: Set[str] = set()
    for pdf, g in rescue_df.groupby("PDF文件名", dropna=False):
        total = len(g)
        if total == 0:
            continue
        top_page_count = g.groupby("source_page_num", dropna=False).size().max()
        if top_page_count / total >= 0.6 and total >= 5:
            page_concentration_keys.add(_norm(pdf))
    rescue_df["silent_risk_source_page_concentration"] = rescue_df["PDF文件名"].map(lambda p: _norm(p) in page_concentration_keys)

    # repeated identical series across PDFs
    rescue_df["series_signature"] = rescue_df.apply(
        lambda r: f"{_norm(r.get('标准指标','')).lower()}|{_to_int(r.get('年份',0))}|{_norm(r.get('value',''))}|{_norm(r.get('normalized_unit','')).lower()}",
        axis=1,
    )
    sig_pdf_count = rescue_df.groupby("series_signature", dropna=False)["PDF文件名"].nunique().reset_index(name="pdf_n")
    repeated_sigs = set(sig_pdf_count[sig_pdf_count["pdf_n"] >= 3]["series_signature"].tolist())
    rescue_df["silent_risk_repeated_identical_series_across_pdfs"] = rescue_df["series_signature"].map(lambda s: _norm(s) in repeated_sigs)

    silent_risk_cols = [
        "silent_risk_metric_family_mismatch",
        "silent_risk_unit_mismatch",
        "silent_risk_year_sequence_gap",
        "silent_risk_abnormal_value_range",
        "silent_risk_source_page_concentration",
        "silent_risk_repeated_identical_series_across_pdfs",
    ]
    rescue_df["silent_risk_count"] = rescue_df[silent_risk_cols].sum(axis=1)

    # risk label
    def _risk_label(row: pd.Series) -> str:
        c = _to_int(row.get("silent_risk_count", 0))
        high_guard = _to_bool(row.get("blk_unresolved_monetary_unit", False)) or _to_bool(row.get("blk_years_not_continuous", False))
        if c >= 3 or high_guard:
            return "high_risk_keep_review_required"
        if c >= 1:
            return "medium_risk_needs_spot_check"
        return "low_risk_rescue_candidate"

    rescue_df["safety_risk_label"] = rescue_df.apply(_risk_label, axis=1)

    # distributions
    risk_by_metric = (
        rescue_df.groupby(["标准指标", "safety_risk_label"], dropna=False)
        .agg(row_count=("candidate_id", "count"), pdf_count=("PDF文件名", "nunique"))
        .reset_index()
        .sort_values(["row_count", "pdf_count"], ascending=[False, False])
    )
    risk_by_pdf = (
        rescue_df.groupby(["PDF文件名", "safety_risk_label"], dropna=False)
        .agg(row_count=("candidate_id", "count"), metric_count=("标准指标", "nunique"))
        .reset_index()
        .sort_values(["row_count", "metric_count"], ascending=[False, False])
    )

    # rule safety audit (rule x risk label)
    rule_rows = []
    for rule in [
        "panel_row_deduplication",
        "panel_boundary_validation",
        "metric_row_purity_guard",
        "numeric_value_sanity_guard",
        "year_column_continuity_guard",
        "source_parser_priority_adjustment",
    ]:
        hit = rescue_df[rescue_df["denoise_rule"].map(lambda x: rule in _norm(x).split("|"))]
        row = {
            "denoise_rule": rule,
            "hit_row_count": int(len(hit)),
            "low_risk_count": int((hit["safety_risk_label"] == "low_risk_rescue_candidate").sum()),
            "medium_risk_count": int((hit["safety_risk_label"] == "medium_risk_needs_spot_check").sum()),
            "high_risk_count": int((hit["safety_risk_label"] == "high_risk_keep_review_required").sum()),
        }
        rule_rows.append(row)
    rule_safety_audit = pd.DataFrame(rule_rows).sort_values("hit_row_count", ascending=False)

    # silent risk audit summary + detail
    silent_summary_rows = []
    for c in silent_risk_cols:
        silent_summary_rows.append(
            {
                "silent_risk": c,
                "row_count": int(rescue_df[c].sum()),
                "row_ratio": float(rescue_df[c].sum() / len(rescue_df)) if len(rescue_df) else 0.0,
            }
        )
    silent_summary = pd.DataFrame(silent_summary_rows).sort_values("row_count", ascending=False)

    silent_detail = rescue_df[rescue_df["silent_risk_count"] > 0].copy()

    # manual spot check sample 30-40 prioritized
    random.seed(30804)
    top_metric = _norm(rescue_df.groupby("标准指标").size().sort_values(ascending=False).index[0]) if len(rescue_df) else ""
    top_pdf = _norm(rescue_df.groupby("PDF文件名").size().sort_values(ascending=False).index[0]) if len(rescue_df) else ""

    rescue_df["sample_priority_score"] = 0
    rescue_df.loc[rescue_df["标准指标"].map(_norm) == top_metric, "sample_priority_score"] += 5
    rescue_df.loc[rescue_df["PDF文件名"].map(_norm) == top_pdf, "sample_priority_score"] += 5
    rescue_df.loc[rescue_df["标准指标"].map(lambda m: _norm(m).lower() in {"roe", "gross_margin"}), "sample_priority_score"] += 4
    rescue_df.loc[rescue_df["标准指标"].map(lambda m: _norm(m).lower() in {"revenue", "net_profit", "attributable_net_profit"}), "sample_priority_score"] += 4
    rescue_df.loc[rescue_df["标准指标"].map(lambda m: _norm(m).lower() in VALUATION_METRICS), "sample_priority_score"] += 3
    rescue_df.loc[rescue_df.get("blk_multi_panel_source", False).map(_to_bool), "sample_priority_score"] += 4
    rescue_df.loc[rescue_df["safety_risk_label"] == "high_risk_keep_review_required", "sample_priority_score"] += 6
    rescue_df.loc[rescue_df["safety_risk_label"] == "medium_risk_needs_spot_check", "sample_priority_score"] += 3

    candidates = rescue_df.sort_values(["sample_priority_score", "silent_risk_count"], ascending=[False, False]).copy()
    sample_n = min(TARGET_SAMPLE_SIZE_MAX, max(TARGET_SAMPLE_SIZE_MIN, min(len(candidates), 35)))

    # take diversified sample by metric/pdf first then fill
    sampled_idx: List[int] = []
    seen_metric: Set[str] = set()
    seen_pdf: Set[str] = set()

    for idx, r in candidates.iterrows():
        m = _norm(r.get("标准指标", "")).lower()
        p = _norm(r.get("PDF文件名", ""))
        if (m not in seen_metric or p not in seen_pdf) and len(sampled_idx) < sample_n:
            sampled_idx.append(idx)
            seen_metric.add(m)
            seen_pdf.add(p)

    if len(sampled_idx) < sample_n:
        remaining = [i for i in candidates.index.tolist() if i not in sampled_idx]
        sampled_idx.extend(remaining[: sample_n - len(sampled_idx)])

    sample_df = candidates.loc[sampled_idx].copy().sort_values(["sample_priority_score", "silent_risk_count"], ascending=[False, False])

    # no merge action - verify final preview unchanged
    final_after_hash = _sha256(IN_307G_FINAL)
    final_preview_v2_unchanged = final_before_hash == final_after_hash

    # parser outputs unchanged
    after_parser_outputs = _snapshot_parser_outputs()
    parser_output_files_modified = any(before_parser_outputs[k] != after_parser_outputs[k] for k in before_parser_outputs.keys())
    parser_output_modified_files = [k for k in before_parser_outputs.keys() if before_parser_outputs[k] != after_parser_outputs[k]]

    # guard snapshots
    after_guard = _snapshot_guard()
    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    forbidden_fields_generated = sorted([c for c in set(rescue_df.columns) if c in FORBIDDEN_FIELDS])

    # recommendation
    low_cnt = int((rescue_df["safety_risk_label"] == "low_risk_rescue_candidate").sum())
    med_cnt = int((rescue_df["safety_risk_label"] == "medium_risk_needs_spot_check").sum())
    high_cnt = int((rescue_df["safety_risk_label"] == "high_risk_keep_review_required").sum())
    if high_cnt > low_cnt:
        readiness = "not_ready_for_merge"
        reco = "High-risk rows exceed low-risk rows. Keep would_rescue sandbox-only and run targeted spot-check + rule tightening first."
    elif med_cnt > low_cnt:
        readiness = "partial_ready_after_spot_check"
        reco = "Medium-risk dominates. Merge is not recommended now; complete prioritized manual spot-check first."
    else:
        readiness = "conditionally_ready_for_next_sandbox_gate"
        reco = "Low-risk dominates; proceed only to next sandbox gate, still no trusted merge/apply."

    reco_lines = [
        "# 308D Merge Readiness Recommendation",
        "",
        f"- readiness: `{readiness}`",
        f"- low_risk_rescue_candidate: `{low_cnt}`",
        f"- medium_risk_needs_spot_check: `{med_cnt}`",
        f"- high_risk_keep_review_required: `{high_cnt}`",
        "",
        "## Recommendation",
        f"- {reco}",
        "- Do not merge into final trusted preview in this stage.",
        "- Keep no safe_to_apply / approve_for_real_apply policy.",
    ]
    OUT_RECO.write_text("\n".join(reco_lines) + "\n", encoding="utf-8")

    _write_excel(
        OUT_SCORED,
        {
            "rescue_safety_scored_rows": rescue_df,
        },
    )
    _write_excel(
        OUT_SAMPLE,
        {
            "manual_spot_check_sample": sample_df,
        },
    )
    _write_excel(
        OUT_RISK_METRIC,
        {
            "risk_distribution_by_metric": risk_by_metric,
        },
    )
    _write_excel(
        OUT_RISK_PDF,
        {
            "risk_distribution_by_pdf": risk_by_pdf,
        },
    )
    _write_excel(
        OUT_RULE_AUDIT,
        {
            "rule_safety_audit": rule_safety_audit,
            "rule_hit_reference": rule_hit_df,
        },
    )
    _write_excel(
        OUT_SILENT,
        {
            "silent_risk_summary": silent_summary,
            "silent_risk_detail": silent_detail,
            "conflict_reference": conflict_df,
            "impact_reference": impact_df,
            "panel_issue_reference": ppm_df,
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

    summary = {
        "stage": "EVAL-308D",
        "mode": "panel_denoise_rescue_safety_validation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_would_rescue_row_count": input_would_rescue_row_count,
        "scored_row_count": int(len(rescue_df)),
        "manual_spot_check_sample_row_count": int(len(sample_df)),
        "input_would_rescue_row_count_preserved": bool(input_would_rescue_row_count == len(rescue_df)),
        "no_rows_merged_into_final_preview": True,
        "final_preview_v2_unchanged": bool(final_preview_v2_unchanged),
        "parser_output_files_unchanged": bool(not parser_output_files_modified),
        "parser_output_modified_files": parser_output_modified_files,
        "low_risk_rescue_candidate_count": low_cnt,
        "medium_risk_needs_spot_check_count": med_cnt,
        "high_risk_keep_review_required_count": high_cnt,
        "merge_readiness": readiness,
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
        "# 308D Panel Denoise Rescue Safety Validation",
        "",
        "## Safety Stratification",
        f"- input_would_rescue_row_count: {input_would_rescue_row_count}",
        f"- low_risk_rescue_candidate: {low_cnt}",
        f"- medium_risk_needs_spot_check: {med_cnt}",
        f"- high_risk_keep_review_required: {high_cnt}",
        f"- manual_spot_check_sample_row_count: {len(sample_df)}",
        "",
        "## Silent Risk Focus",
        "- metric family mismatch",
        "- unit mismatch",
        "- year sequence gap",
        "- abnormal value range by metric",
        "- source page concentration risk",
        "- repeated identical series across PDFs",
        "",
        "## Merge Readiness",
        f"- merge_readiness: {readiness}",
        f"- recommendation: {reco}",
        "",
        "## Guard Assertions",
        f"- input_would_rescue_row_count_preserved: {summary['input_would_rescue_row_count_preserved']}",
        f"- no_rows_merged_into_final_preview: {summary['no_rows_merged_into_final_preview']}",
        f"- final_preview_v2_unchanged: {summary['final_preview_v2_unchanged']}",
        f"- parser_output_files_unchanged: {summary['parser_output_files_unchanged']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_308d_summary_json: {OUT_SUMMARY}")
    print(f"eval_308d_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
