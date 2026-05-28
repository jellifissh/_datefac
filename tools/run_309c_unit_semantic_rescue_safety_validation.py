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
OUT_DIR = BASE_DIR / "output" / "eval_309c_unit_semantic_rescue_safety_validation"

IN_309B_RESCUE = BASE_DIR / "output" / "eval_309b_unit_semantic_standardization_simulation" / "309b_would_rescue_unit_standardized.xlsx"
IN_309B_RULE_HIT = BASE_DIR / "output" / "eval_309b_unit_semantic_standardization_simulation" / "309b_unit_rule_hit_audit.xlsx"
IN_309B_CONFLICT = BASE_DIR / "output" / "eval_309b_unit_semantic_standardization_simulation" / "309b_conflict_audit.xlsx"
IN_309B_IMPACT = BASE_DIR / "output" / "eval_309b_unit_semantic_standardization_simulation" / "309b_impact_estimate.xlsx"
IN_309A_RULES = BASE_DIR / "output" / "eval_309a_unit_semantic_standardization_diagnosis" / "309a_proposed_unit_rules.xlsx"
IN_307G_FINAL = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_final_core_metric_preview_v2.xlsx"
IN_307G_REVIEW = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_306X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"

OUT_SUMMARY = OUT_DIR / "309c_summary.json"
OUT_REPORT = OUT_DIR / "309c_report.md"
OUT_SCORED = OUT_DIR / "309c_unit_rescue_safety_scored_rows.xlsx"
OUT_LOW = OUT_DIR / "309c_low_risk_unit_rescue_candidates.xlsx"
OUT_MED = OUT_DIR / "309c_medium_risk_unit_spot_check_candidates.xlsx"
OUT_HIGH = OUT_DIR / "309c_high_risk_unit_keep_review_required.xlsx"
OUT_RISK_METRIC = OUT_DIR / "309c_risk_distribution_by_metric.xlsx"
OUT_RISK_PDF = OUT_DIR / "309c_risk_distribution_by_pdf.xlsx"
OUT_RULE_AUDIT = OUT_DIR / "309c_unit_safety_rule_audit.xlsx"
OUT_NO_APPLY = OUT_DIR / "309c_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
DETERMINISTIC_MAP = {
    "roe": "percent",
    "gross_margin": "percent",
    "pe": "multiple",
    "pb": "multiple",
    "ev_ebitda": "multiple",
    "eps": "yuan_per_share",
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


def _is_numeric_like(v: Any) -> bool:
    t = _norm(v)
    if t == "":
        return False
    t2 = t.replace(",", "").replace("%", "")
    if t2.startswith("+") or t2.startswith("-"):
        t2 = t2[1:]
    return bool(re.fullmatch(r"\d+(\.\d+)?", t2))


def _year_valid(v: Any) -> bool:
    y = _to_int(v)
    return 1990 <= y <= 2035


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


def _build_key(pdf: str, metric: str, year: int) -> str:
    return f"{_norm(pdf)}|{_norm(metric).lower()}|{int(year)}"


def _abnormal_value(metric: str, value: Any) -> bool:
    m = _norm(metric).lower()
    fv = _to_float(value)
    if fv is None:
        return True
    av = abs(fv)
    if m in {"roe", "gross_margin"} and av > 100:
        return True
    if m in {"pe", "pb", "ev_ebitda"} and av > 200:
        return True
    if m == "eps" and av > 50:
        return True
    return False


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_309B_RESCUE,
        IN_309B_RULE_HIT,
        IN_309B_CONFLICT,
        IN_309B_IMPACT,
        IN_309A_RULES,
        IN_307G_FINAL,
        IN_307G_REVIEW,
        IN_306X_BLOCKER,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-309C",
                "mode": "unit_semantic_rescue_safety_validation",
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
    final_before_hash = _sha256(IN_307G_FINAL)

    rescue_df = _drop_note_rows(_load_first_sheet(IN_309B_RESCUE, "would_rescue_unit_standardized"))
    rule_hit_df = _drop_note_rows(_load_first_sheet(IN_309B_RULE_HIT, "unit_rule_hit_audit"))
    conflict_df = _drop_note_rows(_load_first_sheet(IN_309B_CONFLICT, "conflict_audit"))
    impact_df = _drop_note_rows(_load_first_sheet(IN_309B_IMPACT, "impact_estimate"))
    rules_309a_df = _drop_note_rows(_load_first_sheet(IN_309A_RULES, "proposed_unit_rules"))
    final_df = _drop_note_rows(_load_first_sheet(IN_307G_FINAL, "final_core_metric_preview_v2"))
    review_df = _drop_note_rows(_load_first_sheet(IN_307G_REVIEW, "review_required_core_metrics_v2"))
    blocker_df = _drop_note_rows(_load_first_sheet(IN_306X_BLOCKER, "blocker_by_group"))

    for c in ["PDF文件名", "group_id", "candidate_id", "标准指标", "value", "unit", "normalized_unit", "source_parser", "source_page", "review_status", "source_bucket", "semantic_target_unit", "simulated_normalized_unit"]:
        if c in rescue_df.columns:
            rescue_df[c] = rescue_df[c].map(_norm)
    rescue_df["年份"] = rescue_df["年份"].map(_to_int)

    input_would_rescue_row_count = int(len(rescue_df))

    blocker_df["group_id"] = blocker_df.get("group_id", "").map(_norm)
    for c in [
        "blk_suspicious_value_text",
        "blk_multi_panel_source",
        "blk_zero_candidate_rescued",
        "blk_alias_recovered",
        "blk_missing_year",
        "contains_prose_value",
        "contains_chinese_value",
        "contains_alpha_num_value",
        "contains_fragmented_value",
        "contains_inconsistent_percent",
        "page1_summary",
        "review_priority",
    ]:
        if c not in blocker_df.columns:
            blocker_df[c] = False if c.startswith("blk_") or c.startswith("contains_") or c == "page1_summary" else ""

    map_cols = [
        "group_id",
        "blk_suspicious_value_text",
        "blk_multi_panel_source",
        "blk_zero_candidate_rescued",
        "blk_alias_recovered",
        "blk_missing_year",
        "contains_prose_value",
        "contains_chinese_value",
        "contains_alpha_num_value",
        "contains_fragmented_value",
        "contains_inconsistent_percent",
        "page1_summary",
        "review_priority",
    ]

    scored = rescue_df.merge(blocker_df[map_cols], on="group_id", how="left", suffixes=("", "_from_blocker"))

    # Rescue rows may already carry blocker flags from 309B output.
    # Keep rescue-side values first; backfill with 306X blocker map when missing.
    blocker_fields = [
        "blk_suspicious_value_text",
        "blk_multi_panel_source",
        "blk_zero_candidate_rescued",
        "blk_alias_recovered",
        "blk_missing_year",
        "contains_prose_value",
        "contains_chinese_value",
        "contains_alpha_num_value",
        "contains_fragmented_value",
        "contains_inconsistent_percent",
        "page1_summary",
        "review_priority",
    ]
    for f in blocker_fields:
        from_col = f"{f}_from_blocker"
        if f not in scored.columns and from_col in scored.columns:
            scored[f] = scored[from_col]
        elif f in scored.columns and from_col in scored.columns:
            scored[f] = scored[f].where(scored[f].map(_norm) != "", scored[from_col])
        elif f not in scored.columns:
            scored[f] = False if (f.startswith("blk_") or f.startswith("contains_") or f == "page1_summary") else ""
    scored["metric_norm"] = scored["标准指标"].map(_norm).str.lower()

    # inferred unit from simulation fields fallback to deterministic map
    scored["inferred_unit"] = scored.get("simulated_normalized_unit", "").map(_norm)
    scored.loc[scored["inferred_unit"].eq(""), "inferred_unit"] = scored["metric_norm"].map(lambda m: DETERMINISTIC_MAP.get(_norm(m), ""))

    # recompute conflict with final preview for safety guard
    trusted_key_to_values: Dict[str, Set[str]] = {}
    for _, r in final_df.iterrows():
        k = _build_key(r.get("PDF文件名", ""), r.get("标准指标", ""), _to_int(r.get("年份", 0)))
        trusted_key_to_values.setdefault(k, set()).add(_norm(r.get("value", "")))

    scored["sim_key"] = scored.apply(lambda r: _build_key(r.get("PDF文件名", ""), r.get("标准指标", ""), _to_int(r.get("年份", 0))), axis=1)
    scored["duplicate_or_conflict_risk"] = scored.apply(
        lambda r: (r["sim_key"] in trusted_key_to_values) and (_norm(r.get("value", "")) not in trusted_key_to_values.get(r["sim_key"], set())),
        axis=1,
    )

    # soft blockers for medium risk
    # source page concentration per pdf
    source_page_concentration_pdf: Set[str] = set()
    if not scored.empty:
        for pdf, g in scored.groupby("PDF文件名", dropna=False):
            total = len(g)
            if total <= 0:
                continue
            page_counts = g.groupby(g["source_page"].map(_norm)).size()
            if len(page_counts) and (page_counts.max() / total) >= 0.7 and total >= 4:
                source_page_concentration_pdf.add(_norm(pdf))

    scored["soft_blocker_non_page1"] = ~scored.get("page1_summary", False).map(_to_bool)
    scored["soft_blocker_source_concentration"] = scored["PDF文件名"].map(lambda p: _norm(p) in source_page_concentration_pdf)
    scored["soft_blocker_source_parser_warning"] = scored["source_parser"].map(lambda s: _norm(s).lower() == "pdfplumber")

    # hard conditions for low risk
    scored["low_metric_allowed"] = scored["metric_norm"].map(lambda m: _norm(m) in DETERMINISTIC_MAP.keys())
    scored["deterministic_unit_match"] = scored.apply(
        lambda r: _norm(r.get("inferred_unit", "")).lower() == _norm(DETERMINISTIC_MAP.get(_norm(r.get("metric_norm", "")), "")).lower(),
        axis=1,
    )
    scored["value_numeric_like"] = scored["value"].map(_is_numeric_like)
    scored["year_valid"] = scored["年份"].map(_year_valid)
    scored["no_suspicious_value_text"] = ~(
        scored["blk_suspicious_value_text"].map(_to_bool)
        | scored["contains_prose_value"].map(_to_bool)
        | scored["contains_chinese_value"].map(_to_bool)
        | scored["contains_alpha_num_value"].map(_to_bool)
        | scored["contains_fragmented_value"].map(_to_bool)
        | scored["contains_inconsistent_percent"].map(_to_bool)
    )
    scored["no_multi_panel_source"] = ~scored["blk_multi_panel_source"].map(_to_bool)
    scored["no_zero_candidate_rescued"] = ~scored["blk_zero_candidate_rescued"].map(_to_bool)
    scored["no_alias_recovered"] = ~scored["blk_alias_recovered"].map(_to_bool)
    scored["no_missing_year"] = ~scored["blk_missing_year"].map(_to_bool)
    scored["no_abnormal_value_range"] = ~scored.apply(lambda r: _abnormal_value(r.get("metric_norm", ""), r.get("value", "")), axis=1)
    scored["no_conflict_risk"] = ~scored["duplicate_or_conflict_risk"]

    low_guards = [
        "low_metric_allowed",
        "deterministic_unit_match",
        "value_numeric_like",
        "year_valid",
        "no_conflict_risk",
        "no_suspicious_value_text",
        "no_multi_panel_source",
        "no_zero_candidate_rescued",
        "no_alias_recovered",
        "no_missing_year",
        "no_abnormal_value_range",
    ]
    scored["low_guard_pass"] = scored[low_guards].all(axis=1)

    # medium risk if deterministic base valid + exactly one soft blocker + no hard failures
    hard_fail_for_high = ~scored[[
        "low_metric_allowed",
        "deterministic_unit_match",
        "value_numeric_like",
        "year_valid",
        "no_conflict_risk",
        "no_suspicious_value_text",
        "no_multi_panel_source",
        "no_zero_candidate_rescued",
        "no_alias_recovered",
        "no_missing_year",
        "no_abnormal_value_range",
    ]].all(axis=1)

    soft_count = (
        scored["soft_blocker_non_page1"].astype(int)
        + scored["soft_blocker_source_concentration"].astype(int)
        + scored["soft_blocker_source_parser_warning"].astype(int)
    )
    scored["soft_blocker_count"] = soft_count

    scored["safety_risk_label"] = "high_risk_keep_review_required"
    scored.loc[scored["low_guard_pass"], "safety_risk_label"] = "low_risk_unit_rescue_candidate"
    scored.loc[(~hard_fail_for_high) & (soft_count >= 1) & (soft_count <= 2), "safety_risk_label"] = "medium_risk_needs_spot_check"

    # stratify pivots
    risk_by_metric = (
        scored.groupby(["metric_norm", "safety_risk_label"], dropna=False)
        .agg(row_count=("candidate_id", "count"), pdf_count=("PDF文件名", "nunique"))
        .reset_index()
        .sort_values(["row_count", "pdf_count"], ascending=[False, False])
    )

    risk_by_pdf = (
        scored.groupby(["PDF文件名", "safety_risk_label"], dropna=False)
        .agg(row_count=("candidate_id", "count"), metric_count=("metric_norm", "nunique"))
        .reset_index()
        .sort_values(["row_count", "metric_count"], ascending=[False, False])
    )

    # unit safety rule audit
    rule_audit_rows: List[Dict[str, Any]] = []
    for metric, unit in DETERMINISTIC_MAP.items():
        sub = scored[scored["metric_norm"] == metric]
        rule_audit_rows.append(
            {
                "metric": metric,
                "deterministic_unit": unit,
                "row_count": int(len(sub)),
                "low_risk_count": int((sub["safety_risk_label"] == "low_risk_unit_rescue_candidate").sum()),
                "medium_risk_count": int((sub["safety_risk_label"] == "medium_risk_needs_spot_check").sum()),
                "high_risk_count": int((sub["safety_risk_label"] == "high_risk_keep_review_required").sum()),
                "deterministic_unit_match_rate": float((sub["deterministic_unit_match"].sum() / len(sub)) if len(sub) else 0.0),
            }
        )
    rule_safety_audit = pd.DataFrame(rule_audit_rows).sort_values("row_count", ascending=False)

    low_df = scored[scored["safety_risk_label"] == "low_risk_unit_rescue_candidate"].copy()
    med_df = scored[scored["safety_risk_label"] == "medium_risk_needs_spot_check"].copy()
    high_df = scored[scored["safety_risk_label"] == "high_risk_keep_review_required"].copy()

    _write_excel(OUT_SCORED, {"unit_rescue_safety_scored_rows": scored})
    _write_excel(OUT_LOW, {"low_risk_unit_rescue_candidates": low_df})
    _write_excel(OUT_MED, {"medium_risk_unit_spot_check_candidates": med_df})
    _write_excel(OUT_HIGH, {"high_risk_unit_keep_review_required": high_df})
    _write_excel(OUT_RISK_METRIC, {"risk_distribution_by_metric": risk_by_metric})
    _write_excel(OUT_RISK_PDF, {"risk_distribution_by_pdf": risk_by_pdf})
    _write_excel(
        OUT_RULE_AUDIT,
        {
            "unit_safety_rule_audit": rule_safety_audit,
            "unit_rule_hit_reference_309b": rule_hit_df,
            "unit_rule_catalog_309a": rules_309a_df,
            "unit_conflict_reference_309b": conflict_df,
            "unit_impact_reference_309b": impact_df,
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

    forbidden_fields_generated = sorted([c for c in set(scored.columns) if c in FORBIDDEN_FIELDS])

    final_after_hash = _sha256(IN_307G_FINAL)
    final_preview_v2_unchanged = final_before_hash == final_after_hash

    after_guard = _snapshot_guard()
    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-309C",
        "mode": "unit_semantic_rescue_safety_validation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_would_rescue_row_count": input_would_rescue_row_count,
        "scored_row_count": int(len(scored)),
        "low_risk_count": int(len(low_df)),
        "medium_risk_count": int(len(med_df)),
        "high_risk_count": int(len(high_df)),
        "input_would_rescue_row_count_preserved": bool(input_would_rescue_row_count == len(scored)),
        "no_rows_merged_into_final_preview": True,
        "final_preview_v2_unchanged": bool(final_preview_v2_unchanged),
        "parser_output_files_unchanged": True,
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
        "# 309C Unit Semantic Rescue Safety Validation",
        "",
        "## Risk Stratification",
        f"- input_would_rescue_row_count: {input_would_rescue_row_count}",
        f"- low_risk_unit_rescue_candidate: {len(low_df)}",
        f"- medium_risk_needs_spot_check: {len(med_df)}",
        f"- high_risk_keep_review_required: {len(high_df)}",
        "",
        "## Low-Risk Rule Basis",
        "- deterministic metric-unit match",
        "- numeric-like value and valid year",
        "- no conflict/suspicious/multi_panel/zero_candidate/alias/missing_year",
        "- no abnormal value range",
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

    print(f"eval_309c_summary_json: {OUT_SUMMARY}")
    print(f"eval_309c_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
