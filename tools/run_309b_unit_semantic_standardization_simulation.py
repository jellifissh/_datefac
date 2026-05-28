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
OUT_DIR = BASE_DIR / "output" / "eval_309b_unit_semantic_standardization_simulation"

IN_309A_SAFE = BASE_DIR / "output" / "eval_309a_unit_semantic_standardization_diagnosis" / "309a_safe_semantic_unit_candidates.xlsx"
IN_309A_AMBIG = BASE_DIR / "output" / "eval_309a_unit_semantic_standardization_diagnosis" / "309a_ambiguous_monetary_unit_candidates.xlsx"
IN_309A_RULES = BASE_DIR / "output" / "eval_309a_unit_semantic_standardization_diagnosis" / "309a_proposed_unit_rules.xlsx"
IN_307G_REVIEW = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_307G_FINAL = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_final_core_metric_preview_v2.xlsx"
IN_306X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"
IN_306Z_REVIEW = BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2" / "306z_review_required_v2.xlsx"

OUT_SUMMARY = OUT_DIR / "309b_summary.json"
OUT_REPORT = OUT_DIR / "309b_report.md"
OUT_RESCUE = OUT_DIR / "309b_would_rescue_unit_standardized.xlsx"
OUT_STILL = OUT_DIR / "309b_still_review_required_after_unit_simulation.xlsx"
OUT_BLOCKED = OUT_DIR / "309b_blocked_unit_candidates.xlsx"
OUT_RULE_HIT = OUT_DIR / "309b_unit_rule_hit_audit.xlsx"
OUT_CONFLICT = OUT_DIR / "309b_conflict_audit.xlsx"
OUT_IMPACT = OUT_DIR / "309b_impact_estimate.xlsx"
OUT_NO_APPLY = OUT_DIR / "309b_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
ALLOWED_METRICS = {"roe", "gross_margin", "pe", "pb", "ev_ebitda", "eps"}
TARGET_CORE_METRICS = {
    "revenue",
    "attributable_net_profit",
    "gross_margin",
    "roe",
    "eps",
    "pe",
    "pb",
    "ev_ebitda",
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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_309A_SAFE,
        IN_309A_AMBIG,
        IN_309A_RULES,
        IN_307G_REVIEW,
        IN_307G_FINAL,
        IN_306X_BLOCKER,
        IN_306Z_REVIEW,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-309B",
                "mode": "unit_semantic_standardization_simulation",
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

    safe_df = _drop_note_rows(_load_first_sheet(IN_309A_SAFE, "safe_semantic_unit_candidates"))
    ambig_df = _drop_note_rows(_load_first_sheet(IN_309A_AMBIG, "ambiguous_monetary_unit_candidates"))
    rules_df = _drop_note_rows(_load_first_sheet(IN_309A_RULES, "proposed_unit_rules"))
    review_df = _drop_note_rows(_load_first_sheet(IN_307G_REVIEW, "review_required_core_metrics_v2"))
    final_df = _drop_note_rows(_load_first_sheet(IN_307G_FINAL, "final_core_metric_preview_v2"))
    blocker_df = _drop_note_rows(_load_first_sheet(IN_306X_BLOCKER, "blocker_by_group"))
    review_306z_df = _drop_note_rows(_load_first_sheet(IN_306Z_REVIEW, "review_required_v2"))

    for c in ["PDF文件名", "group_id", "candidate_id", "标准指标", "指标名", "unit", "normalized_unit", "value", "source_parser", "source_page", "review_status", "risk_level"]:
        if c in review_df.columns:
            review_df[c] = review_df[c].map(_norm)
        if c in safe_df.columns:
            safe_df[c] = safe_df[c].map(_norm)
        if c in ambig_df.columns:
            ambig_df[c] = ambig_df[c].map(_norm)

    review_df["年份"] = review_df["年份"].map(_to_int)

    input_review_required_v2_row_count = int(len(review_df))

    # Build blocker map for suspicious text guards
    blocker_df["group_id"] = blocker_df.get("group_id", "").map(_norm)
    for c in ["blk_suspicious_value_text", "contains_prose_value", "contains_chinese_value", "contains_alpha_num_value", "contains_fragmented_value", "contains_inconsistent_percent"]:
        if c not in blocker_df.columns:
            blocker_df[c] = False

    blocker_map = blocker_df[[
        "group_id",
        "blk_suspicious_value_text",
        "contains_prose_value",
        "contains_chinese_value",
        "contains_alpha_num_value",
        "contains_fragmented_value",
        "contains_inconsistent_percent",
    ]].copy()

    sim = review_df.merge(blocker_map, on="group_id", how="left")
    sim["metric_norm"] = sim["标准指标"].map(_norm).str.lower()

    # mark whether in 309a safe / ambiguous pools
    safe_keys = set(
        safe_df.apply(
            lambda r: (_norm(r.get("candidate_id", "")), _norm(r.get("group_id", "")), _norm(r.get("PDF文件名", "")), _norm(r.get("标准指标", "")).lower(), _to_int(r.get("年份", 0))),
            axis=1,
        ).tolist()
    )
    ambig_keys = set(
        ambig_df.apply(
            lambda r: (_norm(r.get("candidate_id", "")), _norm(r.get("group_id", "")), _norm(r.get("PDF文件名", "")), _norm(r.get("标准指标", "")).lower(), _to_int(r.get("年份", 0))),
            axis=1,
        ).tolist()
    )

    sim["row_key"] = sim.apply(
        lambda r: (_norm(r.get("candidate_id", "")), _norm(r.get("group_id", "")), _norm(r.get("PDF文件名", "")), _norm(r.get("标准指标", "")).lower(), _to_int(r.get("年份", 0))),
        axis=1,
    )
    sim["in_309a_safe_pool"] = sim["row_key"].map(lambda x: x in safe_keys)
    sim["in_309a_ambiguous_pool"] = sim["row_key"].map(lambda x: x in ambig_keys)

    # deterministic metric and inferred unit
    unit_map = {
        "roe": "percent",
        "gross_margin": "percent",
        "pe": "multiple",
        "pb": "multiple",
        "ev_ebitda": "multiple",
        "eps": "yuan_per_share",
    }
    sim["semantic_target_unit"] = sim["metric_norm"].map(lambda m: unit_map.get(_norm(m), ""))
    sim["deterministic_metric_allowed"] = sim["metric_norm"].map(lambda m: _norm(m) in ALLOWED_METRICS)

    # guards
    sim["g_candidate_id_exists"] = sim["candidate_id"].map(_norm) != ""
    sim["g_metric_target_core"] = sim["metric_norm"].map(lambda m: _norm(m) in TARGET_CORE_METRICS)
    sim["g_value_numeric_like"] = sim["value"].map(_is_numeric_like)
    sim["g_year_valid"] = sim["年份"].map(_year_valid)
    sim["g_no_human_reject_or_needs_more_info"] = ~sim["review_status"].map(lambda s: _norm(s).lower() in {"reject", "needs_more_info", "reject_series", "needs_more_info_series"})

    sim["g_no_suspicious_value_text"] = ~(
        sim["blk_suspicious_value_text"].map(_to_bool)
        | sim["contains_prose_value"].map(_to_bool)
        | sim["contains_chinese_value"].map(_to_bool)
        | sim["contains_alpha_num_value"].map(_to_bool)
        | sim["contains_fragmented_value"].map(_to_bool)
        | sim["contains_inconsistent_percent"].map(_to_bool)
    )

    # no duplicate/conflict with final preview
    trusted_key_to_values: Dict[str, Set[str]] = {}
    for _, r in final_df.iterrows():
        k = _build_key(r.get("PDF文件名", ""), r.get("标准指标", ""), _to_int(r.get("年份", 0)))
        trusted_key_to_values.setdefault(k, set()).add(_norm(r.get("value", "")))

    sim["sim_key"] = sim.apply(lambda r: _build_key(r.get("PDF文件名", ""), r.get("标准指标", ""), _to_int(r.get("年份", 0))), axis=1)
    sim["duplicate_with_trusted"] = sim["sim_key"].map(lambda k: k in trusted_key_to_values)
    sim["conflict_with_trusted"] = sim.apply(
        lambda r: (r["sim_key"] in trusted_key_to_values) and (_norm(r.get("value", "")) not in trusted_key_to_values.get(r["sim_key"], set())),
        axis=1,
    )
    sim["g_no_duplicate_or_conflict_with_trusted"] = ~(sim["duplicate_with_trusted"] | sim["conflict_with_trusted"])

    # ambiguous monetary rows must not be rescued
    sim["g_not_ambiguous_monetary"] = ~sim["in_309a_ambiguous_pool"]

    # only from deterministic safe pool
    sim["g_in_309a_deterministic_safe_pool"] = sim["in_309a_safe_pool"] & sim["deterministic_metric_allowed"]

    guard_cols = [
        "g_candidate_id_exists",
        "g_metric_target_core",
        "g_value_numeric_like",
        "g_year_valid",
        "g_no_duplicate_or_conflict_with_trusted",
        "g_no_human_reject_or_needs_more_info",
        "g_no_suspicious_value_text",
        "g_not_ambiguous_monetary",
        "g_in_309a_deterministic_safe_pool",
    ]
    sim["all_guards_pass"] = sim[guard_cols].all(axis=1)

    sim["simulation_bucket"] = "still_review_required_after_unit_simulation"
    sim.loc[~sim["all_guards_pass"], "simulation_bucket"] = "blocked_unit_candidates"
    sim.loc[sim["all_guards_pass"], "simulation_bucket"] = "would_rescue_unit_standardized"

    would_rescue = sim[sim["simulation_bucket"] == "would_rescue_unit_standardized"].copy()
    still_review = sim[sim["simulation_bucket"] == "still_review_required_after_unit_simulation"].copy()
    blocked = sim[sim["simulation_bucket"] == "blocked_unit_candidates"].copy()

    # simulation output bucket only
    would_rescue["source_bucket"] = "simulated_unit_semantic_rescue"
    would_rescue["simulated_normalized_unit"] = would_rescue["semantic_target_unit"]

    # audits
    dup_counts = would_rescue.groupby("sim_key", dropna=False).size().reset_index(name="cnt") if not would_rescue.empty else pd.DataFrame(columns=["sim_key", "cnt"])
    dup_keys = set(dup_counts[dup_counts["cnt"] > 1]["sim_key"].tolist())

    conflict_rows: List[Dict[str, Any]] = []
    for _, r in would_rescue.iterrows():
        k = _norm(r.get("sim_key", ""))
        proposed = _norm(r.get("value", ""))
        trusted_vals = sorted(list(trusted_key_to_values.get(k, set())))
        if k in trusted_key_to_values and proposed not in trusted_key_to_values[k]:
            conflict_rows.append(
                {
                    "sim_key": k,
                    "PDF文件名": _norm(r.get("PDF文件名", "")),
                    "标准指标": _norm(r.get("标准指标", "")),
                    "年份": _to_int(r.get("年份", 0)),
                    "proposed_value": proposed,
                    "trusted_values": "|".join(trusted_vals),
                    "conflict_type": "value_conflict_with_final_preview_v2",
                }
            )
    conflict_audit = pd.DataFrame(conflict_rows)
    if conflict_audit.empty:
        conflict_audit = pd.DataFrame([{"note": "no_conflict_with_final_preview_v2"}])

    rule_hit_audit = pd.DataFrame(
        [
            {"rule": "roe/gross_margin -> percent", "hit_row_count": int((would_rescue["metric_norm"].isin({"roe", "gross_margin"})).sum())},
            {"rule": "pe/pb/ev_ebitda -> multiple", "hit_row_count": int((would_rescue["metric_norm"].isin({"pe", "pb", "ev_ebitda"})).sum())},
            {"rule": "eps -> yuan_per_share", "hit_row_count": int((would_rescue["metric_norm"] == "eps").sum())},
            {"rule": "ambiguous_monetary_not_rescued", "hit_row_count": int((sim["in_309a_ambiguous_pool"] == True).sum())},
            {"rule": "would_rescue_unit_standardized", "hit_row_count": int(len(would_rescue))},
            {"rule": "still_review_required_after_unit_simulation", "hit_row_count": int(len(still_review))},
            {"rule": "blocked_unit_candidates", "hit_row_count": int(len(blocked))},
        ]
    )

    impact_estimate = pd.DataFrame(
        [
            {
                "scenario": "309b_unit_semantic_standardization_simulation",
                "input_review_required_v2_row_count": input_review_required_v2_row_count,
                "would_rescue_row_count": int(len(would_rescue)),
                "still_review_required_row_count": int(len(still_review)),
                "blocked_row_count": int(len(blocked)),
                "ambiguous_monetary_input_row_count": int((sim["in_309a_ambiguous_pool"] == True).sum()),
                "ambiguous_monetary_rescued_row_count": int((would_rescue["in_309a_ambiguous_pool"] == True).sum()) if not would_rescue.empty else 0,
                "reduction_ratio": float(len(would_rescue) / input_review_required_v2_row_count) if input_review_required_v2_row_count else 0.0,
            }
        ]
    )

    _write_excel(OUT_RESCUE, {"would_rescue_unit_standardized": would_rescue})
    _write_excel(OUT_STILL, {"still_review_required_after_unit_simulation": still_review})
    _write_excel(OUT_BLOCKED, {"blocked_unit_candidates": blocked})
    _write_excel(OUT_RULE_HIT, {"unit_rule_hit_audit": rule_hit_audit, "rule_catalog_309a": rules_df})
    _write_excel(OUT_CONFLICT, {"conflict_audit": conflict_audit})
    _write_excel(OUT_IMPACT, {"impact_estimate": impact_estimate})

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

    forbidden_fields_generated = sorted([c for c in set(sim.columns).union(set(would_rescue.columns)) if c in FORBIDDEN_FIELDS])

    final_after_hash = _sha256(IN_307G_FINAL)
    final_preview_v2_unchanged = final_before_hash == final_after_hash

    ambiguous_monetary_rows_not_rescued = int((would_rescue["in_309a_ambiguous_pool"] == True).sum()) == 0 if not would_rescue.empty else True

    duplicate_trusted_key_count_would_rescue = int(len(dup_keys))
    value_conflict_count_with_final_preview_v2 = len(conflict_rows)

    after_guard = _snapshot_guard()
    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-309B",
        "mode": "unit_semantic_standardization_simulation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_review_required_v2_row_count": input_review_required_v2_row_count,
        "would_rescue_row_count": int(len(would_rescue)),
        "still_review_required_row_count": int(len(still_review)),
        "blocked_row_count": int(len(blocked)),
        "input_review_required_v2_row_count_preserved": bool(input_review_required_v2_row_count == len(sim)),
        "final_preview_v2_unchanged": bool(final_preview_v2_unchanged),
        "ambiguous_monetary_rows_not_rescued": bool(ambiguous_monetary_rows_not_rescued),
        "no_rows_merged_into_final_preview": True,
        "duplicate_trusted_key_count_would_rescue": duplicate_trusted_key_count_would_rescue,
        "value_conflict_count_with_final_preview_v2": value_conflict_count_with_final_preview_v2,
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
        "# 309B Unit Semantic Standardization Simulation",
        "",
        "## Simulation Snapshot",
        f"- input_review_required_v2_row_count: {input_review_required_v2_row_count}",
        f"- would_rescue_unit_standardized: {len(would_rescue)}",
        f"- still_review_required_after_unit_simulation: {len(still_review)}",
        f"- blocked_unit_candidates: {len(blocked)}",
        "",
        "## Deterministic Rules Applied",
        "- roe / gross_margin -> percent",
        "- pe / pb / ev_ebitda -> multiple",
        "- eps -> yuan_per_share",
        "- ambiguous monetary rows excluded",
        "",
        "## Guard Assertions",
        f"- final_preview_v2_unchanged: {summary['final_preview_v2_unchanged']}",
        f"- ambiguous_monetary_rows_not_rescued: {summary['ambiguous_monetary_rows_not_rescued']}",
        f"- no_rows_merged_into_final_preview: {summary['no_rows_merged_into_final_preview']}",
        f"- duplicate_trusted_key_count_would_rescue: {summary['duplicate_trusted_key_count_would_rescue']}",
        f"- value_conflict_count_with_final_preview_v2: {summary['value_conflict_count_with_final_preview_v2']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_309b_summary_json: {OUT_SUMMARY}")
    print(f"eval_309b_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
