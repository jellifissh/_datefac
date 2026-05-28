from __future__ import annotations

import hashlib
import json
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
OUT_DIR = BASE_DIR / "output" / "eval_309a_unit_semantic_standardization_diagnosis"

IN_308A_FIX = BASE_DIR / "output" / "eval_308a_review_burden_reduction_strategy" / "308a_high_impact_fix_candidates.xlsx"
IN_308A_BLOCKER = BASE_DIR / "output" / "eval_308a_review_burden_reduction_strategy" / "308a_blocker_impact_ranking.xlsx"
IN_307G_REVIEW = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_307G_FINAL = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_final_core_metric_preview_v2.xlsx"
IN_306X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"
IN_306Z_REVIEW = BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2" / "306z_review_required_v2.xlsx"
IN_306L_GROUP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"

OUT_SUMMARY = OUT_DIR / "309a_summary.json"
OUT_REPORT = OUT_DIR / "309a_report.md"
OUT_CAND = OUT_DIR / "309a_unit_issue_candidates.xlsx"
OUT_METRIC_PDF = OUT_DIR / "309a_unit_issue_by_metric_pdf.xlsx"
OUT_SAFE = OUT_DIR / "309a_safe_semantic_unit_candidates.xlsx"
OUT_AMBIG = OUT_DIR / "309a_ambiguous_monetary_unit_candidates.xlsx"
OUT_RULES = OUT_DIR / "309a_proposed_unit_rules.xlsx"
OUT_IMPACT = OUT_DIR / "309a_expected_impact_estimate.xlsx"
OUT_NEXT = OUT_DIR / "309a_next_action_recommendation.md"
OUT_NO_APPLY = OUT_DIR / "309a_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
SAFE_PERCENT_METRICS = {"roe", "gross_margin"}
SAFE_MULTIPLE_METRICS = {"pe", "pb", "ev_ebitda"}
SAFE_EPS_METRICS = {"eps"}
MONETARY_METRICS = {"revenue", "attributable_net_profit"}


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


def _infer_semantic_unit(metric: str) -> str:
    m = _norm(metric).lower()
    if m in SAFE_PERCENT_METRICS:
        return "percent"
    if m in SAFE_MULTIPLE_METRICS:
        return "multiple"
    if m in SAFE_EPS_METRICS:
        return "yuan_per_share"
    return ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_308A_FIX,
        IN_308A_BLOCKER,
        IN_307G_REVIEW,
        IN_307G_FINAL,
        IN_306X_BLOCKER,
        IN_306Z_REVIEW,
        IN_306L_GROUP,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-309A",
                "mode": "unit_semantic_standardization_diagnosis",
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

    fix_df = _drop_note_rows(_load_first_sheet(IN_308A_FIX, "high_impact_fix_candidates"))
    blocker_rank_df = _drop_note_rows(_load_first_sheet(IN_308A_BLOCKER, "blocker_impact_ranking"))
    review_df = _drop_note_rows(_load_first_sheet(IN_307G_REVIEW, "review_required_core_metrics_v2"))
    final_df = _drop_note_rows(_load_first_sheet(IN_307G_FINAL, "final_core_metric_preview_v2"))
    blocker_df = _drop_note_rows(_load_first_sheet(IN_306X_BLOCKER, "blocker_by_group"))
    review_306z_df = _drop_note_rows(_load_first_sheet(IN_306Z_REVIEW, "review_required_v2"))
    grouped_df = _drop_note_rows(_load_first_sheet(IN_306L_GROUP, "grouped_review_table"))

    for c in ["PDF文件名", "group_id", "candidate_id", "标准指标", "指标名", "source_parser", "source_page", "unit", "normalized_unit", "value", "risk_level"]:
        if c in review_df.columns:
            review_df[c] = review_df[c].map(_norm)
    review_df["年份"] = review_df["年份"].map(_to_int)

    input_review_required_v2_row_count = int(len(review_df))

    # map group blocker flags to row level
    blocker_df["group_id"] = blocker_df.get("group_id", "").map(_norm)
    if "blk_unit_unknown_or_warning" not in blocker_df.columns:
        blocker_df["blk_unit_unknown_or_warning"] = blocker_df.get("unit_unknown", "").map(_to_bool)
    if "blk_unresolved_monetary_unit" not in blocker_df.columns:
        blocker_df["blk_unresolved_monetary_unit"] = False

    map_cols = [
        "group_id",
        "blk_unit_unknown_or_warning",
        "blk_unresolved_monetary_unit",
        "unit_unknown",
        "risk_reasons",
        "review_priority",
    ]
    for c in map_cols:
        if c not in blocker_df.columns:
            blocker_df[c] = ""

    row_df = review_df.merge(blocker_df[map_cols], on="group_id", how="left")
    row_df["unit_unknown_or_warning"] = row_df["blk_unit_unknown_or_warning"].map(_to_bool)
    row_df["unresolved_monetary_unit"] = row_df["blk_unresolved_monetary_unit"].map(_to_bool)

    unit_issue_candidates = row_df[
        (row_df["unit_unknown_or_warning"] == True) | (row_df["unresolved_monetary_unit"] == True)
    ].copy()

    # semantic inference
    unit_issue_candidates["metric_norm"] = unit_issue_candidates["标准指标"].map(_norm).str.lower()
    unit_issue_candidates["semantic_inferred_unit"] = unit_issue_candidates["metric_norm"].map(_infer_semantic_unit)

    # safe semantic cases
    safe_semantic = unit_issue_candidates[
        unit_issue_candidates["semantic_inferred_unit"].map(_norm) != ""
    ].copy()
    safe_semantic["inference_confidence"] = "high_semantic_deterministic"

    # monetary context checks (conservative)
    monetary_candidates = unit_issue_candidates[
        unit_issue_candidates["metric_norm"].isin(MONETARY_METRICS)
    ].copy()

    monetary_candidates["source_context_supports_monetary"] = (
        monetary_candidates["unit"].map(_norm).ne("")
        | monetary_candidates["normalized_unit"].map(_norm).ne("")
        | monetary_candidates["risk_reasons"].map(_norm).str.contains("monetary|currency|亿元|万元|元", case=False, regex=True)
    )

    safe_monetary = monetary_candidates[
        (monetary_candidates["source_context_supports_monetary"] == True)
        & (monetary_candidates["unresolved_monetary_unit"] == False)
    ].copy()
    safe_monetary["semantic_inferred_unit"] = "monetary_contextual"
    safe_monetary["inference_confidence"] = "medium_context_supported"

    ambiguous_monetary = monetary_candidates[
        (monetary_candidates["source_context_supports_monetary"] == False)
        | (monetary_candidates["unresolved_monetary_unit"] == True)
    ].copy()
    ambiguous_monetary["inference_confidence"] = "ambiguous_require_review"

    safe_candidates = pd.concat([safe_semantic, safe_monetary], ignore_index=True).drop_duplicates(
        subset=["candidate_id", "group_id", "PDF文件名", "标准指标", "年份", "value"], keep="first"
    )

    # metric/pdf breakdown
    by_metric_pdf = (
        unit_issue_candidates.groupby(["标准指标", "PDF文件名"], dropna=False)
        .agg(
            row_count=("candidate_id", "count"),
            pdf_count=("PDF文件名", "nunique"),
            parser_mix=("source_parser", lambda x: "|".join(sorted(set(_norm(v) for v in x if _norm(v) != "")))),
            page_mix=("source_page", lambda x: "|".join(sorted(set(_norm(v) for v in x if _norm(v) != ""))[:6])),
            unit_mix=("unit", lambda x: "|".join(sorted(set(_norm(v) for v in x if _norm(v) != ""))[:6])),
            normalized_unit_mix=("normalized_unit", lambda x: "|".join(sorted(set(_norm(v) for v in x if _norm(v) != ""))[:6])),
        )
        .reset_index()
        .sort_values(["row_count"], ascending=False)
    )

    # proposed rules
    proposed_rules = pd.DataFrame(
        [
            {
                "rule_id": "U1_percent_semantic_default",
                "scope_metric": "roe|gross_margin",
                "condition": "unit_unknown_or_warning=true and metric semantic deterministic",
                "proposed_unit": "percent",
                "safety_guard": "exclude if value looks like multiple or has prose",
                "estimated_risk": "low",
            },
            {
                "rule_id": "U2_multiple_semantic_default",
                "scope_metric": "pe|pb|ev_ebitda",
                "condition": "unit_unknown_or_warning=true and valuation metric",
                "proposed_unit": "multiple",
                "safety_guard": "exclude if value contains percent sign",
                "estimated_risk": "low",
            },
            {
                "rule_id": "U3_eps_semantic_default",
                "scope_metric": "eps",
                "condition": "unit_unknown_or_warning=true and eps numeric-like",
                "proposed_unit": "yuan_per_share",
                "safety_guard": "exclude abnormal abs(value)>50",
                "estimated_risk": "low_medium",
            },
            {
                "rule_id": "U4_monetary_contextual_inference",
                "scope_metric": "revenue|attributable_net_profit",
                "condition": "source context explicitly supports monetary unit",
                "proposed_unit": "monetary_contextual",
                "safety_guard": "do not infer when unresolved_monetary_unit=true and context empty",
                "estimated_risk": "medium",
            },
            {
                "rule_id": "U5_keep_ambiguous_monetary_review",
                "scope_metric": "revenue|attributable_net_profit",
                "condition": "context missing or unresolved_monetary_unit=true",
                "proposed_unit": "no_change_keep_review",
                "safety_guard": "must remain review_required",
                "estimated_risk": "high_if_auto",
            },
        ]
    )

    # impact estimates
    total_issues = int(len(unit_issue_candidates))
    safe_rows = int(len(safe_candidates))
    ambiguous_rows = int(len(ambiguous_monetary))

    # reference from 308a for unit_semantic_standardization
    ref = fix_df[fix_df["fix_id"].map(_norm) == "unit_semantic_standardization"]
    ref_cons = _to_int(ref["estimated_reduction_rows_conservative"].iloc[0]) if not ref.empty else 0
    ref_mod = _to_int(ref["estimated_reduction_rows_moderate"].iloc[0]) if not ref.empty else 0

    est_cons = min(safe_rows, max(ref_cons, int(round(safe_rows * 0.65))))
    est_mod = min(safe_rows, max(ref_mod, int(round(safe_rows * 0.85))))

    impact_estimate = pd.DataFrame(
        [
            {
                "scenario": "309a_unit_semantic_standardization_safe_only",
                "unit_issue_row_count": total_issues,
                "safe_semantic_or_contextual_row_count": safe_rows,
                "ambiguous_monetary_row_count": ambiguous_rows,
                "estimated_reduction_rows_conservative": est_cons,
                "estimated_reduction_rows_moderate": est_mod,
                "estimated_reduction_ratio_conservative": float(est_cons / input_review_required_v2_row_count) if input_review_required_v2_row_count else 0.0,
                "estimated_reduction_ratio_moderate": float(est_mod / input_review_required_v2_row_count) if input_review_required_v2_row_count else 0.0,
                "note": "safe rows only; ambiguous monetary kept review_required",
            },
            {
                "scenario": "reference_308a_unit_standardization",
                "unit_issue_row_count": total_issues,
                "safe_semantic_or_contextual_row_count": safe_rows,
                "ambiguous_monetary_row_count": ambiguous_rows,
                "estimated_reduction_rows_conservative": ref_cons,
                "estimated_reduction_rows_moderate": ref_mod,
                "estimated_reduction_ratio_conservative": float(ref_cons / input_review_required_v2_row_count) if input_review_required_v2_row_count else 0.0,
                "estimated_reduction_ratio_moderate": float(ref_mod / input_review_required_v2_row_count) if input_review_required_v2_row_count else 0.0,
                "note": "baseline from 308A",
            },
        ]
    )

    # recommendations
    next_lines = [
        "# 309A Next Action Recommendation",
        "",
        "## Priority",
        "1. Implement sandbox-only semantic unit default for deterministic metrics (roe/gross_margin/pe/pb/ev_ebitda/eps).",
        "2. Keep monetary ambiguous rows in review_required and add context extraction diagnostics.",
        "3. Run a sandbox validation gate before any merge simulation.",
        "",
        "## Guard",
        "- Do not merge rescue rows into final preview in this stage.",
        "- Do not emit safe_to_apply / approve_for_real_apply.",
    ]
    OUT_NEXT.write_text("\n".join(next_lines) + "\n", encoding="utf-8")

    _write_excel(
        OUT_CAND,
        {
            "unit_issue_candidates": unit_issue_candidates,
        },
    )
    _write_excel(
        OUT_METRIC_PDF,
        {
            "unit_issue_by_metric_pdf": by_metric_pdf,
            "308a_blocker_impact_reference": blocker_rank_df,
        },
    )
    _write_excel(
        OUT_SAFE,
        {
            "safe_semantic_unit_candidates": safe_candidates,
        },
    )
    _write_excel(
        OUT_AMBIG,
        {
            "ambiguous_monetary_unit_candidates": ambiguous_monetary,
        },
    )
    _write_excel(
        OUT_RULES,
        {
            "proposed_unit_rules": proposed_rules,
        },
    )
    _write_excel(
        OUT_IMPACT,
        {
            "expected_impact_estimate": impact_estimate,
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

    forbidden_fields_generated = sorted([c for c in set(unit_issue_candidates.columns).union(set(safe_candidates.columns)).union(set(ambiguous_monetary.columns)) if c in FORBIDDEN_FIELDS])

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
        "stage": "EVAL-309A",
        "mode": "unit_semantic_standardization_diagnosis",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_review_required_v2_row_count": input_review_required_v2_row_count,
        "unit_issue_row_count": total_issues,
        "safe_semantic_or_contextual_row_count": safe_rows,
        "ambiguous_monetary_row_count": ambiguous_rows,
        "input_review_required_v2_row_count_preserved": True,
        "final_preview_v2_unchanged": bool(final_preview_v2_unchanged),
        "no_rows_merged_into_final_preview": True,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "forbidden_fields_generated": forbidden_fields_generated,
        "estimated_reduction_rows_conservative": est_cons,
        "estimated_reduction_rows_moderate": est_mod,
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 309A Unit Semantic Standardization Diagnosis",
        "",
        "## Scope",
        "- diagnosis/design only",
        "- no merge to final preview",
        "",
        "## Unit Burden Snapshot",
        f"- input_review_required_v2_row_count: {input_review_required_v2_row_count}",
        f"- unit_issue_row_count: {total_issues}",
        f"- safe_semantic_or_contextual_row_count: {safe_rows}",
        f"- ambiguous_monetary_row_count: {ambiguous_rows}",
        "",
        "## Proposed Safe Inference",
        "- roe/gross_margin -> percent",
        "- pe/pb/ev_ebitda -> multiple",
        "- eps -> yuan_per_share",
        "- revenue/attributable_net_profit -> monetary only with context support",
        "",
        "## Estimated Impact",
        f"- conservative: {est_cons}",
        f"- moderate: {est_mod}",
        "",
        "## Guard Assertions",
        f"- final_preview_v2_unchanged: {summary['final_preview_v2_unchanged']}",
        f"- no_rows_merged_into_final_preview: {summary['no_rows_merged_into_final_preview']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_309a_summary_json: {OUT_SUMMARY}")
    print(f"eval_309a_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
