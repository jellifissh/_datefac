from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_308c_parser_panel_denoise_rule_simulation"

IN_308B_CAND = BASE_DIR / "output" / "eval_308b_parser_panel_denoise_and_merge_design" / "308b_panel_issue_candidates.xlsx"
IN_308B_RULES = BASE_DIR / "output" / "eval_308b_parser_panel_denoise_and_merge_design" / "308b_proposed_denoise_rules.xlsx"
IN_308B_IMPACT = BASE_DIR / "output" / "eval_308b_parser_panel_denoise_and_merge_design" / "308b_expected_impact_estimate.xlsx"
IN_307G_REVIEW = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_307G_FINAL = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_final_core_metric_preview_v2.xlsx"
IN_306X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"
IN_306Z_REVIEW = BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2" / "306z_review_required_v2.xlsx"

OUT_SUMMARY = OUT_DIR / "308c_summary.json"
OUT_REPORT = OUT_DIR / "308c_report.md"
OUT_RESCUE = OUT_DIR / "308c_would_rescue_from_review.xlsx"
OUT_STILL = OUT_DIR / "308c_still_review_required_after_simulation.xlsx"
OUT_BLOCKED = OUT_DIR / "308c_blocked_by_denoise_rules.xlsx"
OUT_HIT_AUDIT = OUT_DIR / "308c_denoise_rule_hit_audit.xlsx"
OUT_CONFLICT = OUT_DIR / "308c_conflict_audit.xlsx"
OUT_IMPACT = OUT_DIR / "308c_impact_estimate.xlsx"
OUT_NO_APPLY = OUT_DIR / "308c_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
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

PARSER_OUTPUT_GUARD_FILES = {
    "306x_blocker_by_group": IN_306X_BLOCKER,
    "306z_review_required_v2": IN_306Z_REVIEW,
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


def _is_numeric_like(v: Any) -> bool:
    t = _norm(v)
    if t == "":
        return False
    t2 = t.replace(",", "").replace("%", "")
    if t2.startswith("+") or t2.startswith("-"):
        t2 = t2[1:]
    return bool(re.fullmatch(r"\d+(\.\d+)?", t2))


def _has_chinese_mix(v: Any) -> bool:
    t = _norm(v)
    return bool(re.search(r"[\u4e00-\u9fff]", t) and re.search(r"\d", t))


def _has_merged_value_cell(v: Any) -> bool:
    t = _norm(v)
    if t == "":
        return True
    toks = ["/", "|", "；", ";", "、", " and ", "同比", "增长", "其中", "货币资金"]
    return any(x in t for x in toks)


def _year_valid(v: Any) -> bool:
    y = _to_int(v)
    return 1990 <= y <= 2035


def _build_key(pdf: str, metric: str, year: int) -> str:
    return f"{_norm(pdf)}|{_norm(metric).lower()}|{int(year)}"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_308B_CAND,
        IN_308B_RULES,
        IN_308B_IMPACT,
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
                "stage": "EVAL-308C",
                "mode": "parser_panel_denoise_rule_simulation",
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

    cand_df = _drop_note_rows(_load_first_sheet(IN_308B_CAND, "panel_issue_candidates"))
    rules_df = _drop_note_rows(_load_first_sheet(IN_308B_RULES, "proposed_denoise_rules"))
    impact_ref_df = _drop_note_rows(_load_first_sheet(IN_308B_IMPACT, "expected_impact_estimate"))
    review_df = _drop_note_rows(_load_first_sheet(IN_307G_REVIEW, "review_required_core_metrics_v2"))
    final_df = _drop_note_rows(_load_first_sheet(IN_307G_FINAL, "final_core_metric_preview_v2"))
    blocker_df = _drop_note_rows(_load_first_sheet(IN_306X_BLOCKER, "blocker_by_group"))

    for c in ["PDF文件名", "group_id", "candidate_id", "标准指标", "指标名", "source_parser", "source_bucket", "review_status", "value", "unit", "normalized_unit"]:
        if c in review_df.columns:
            review_df[c] = review_df[c].map(_norm)
        if c in cand_df.columns:
            cand_df[c] = cand_df[c].map(_norm)

    review_df["年份"] = review_df["年份"].map(_to_int)
    final_df["年份"] = final_df["年份"].map(_to_int)

    input_review_required_row_count = int(len(review_df))

    # Join blocker flags by group_id for all review rows
    blocker_df["group_id"] = blocker_df.get("group_id", "").map(_norm)
    for src_col in [
        "blk_multi_panel_source",
        "blk_suspicious_value_text",
        "blk_duplicate_or_conflict",
        "blk_years_not_continuous",
        "blk_unresolved_monetary_unit",
    ]:
        if src_col not in blocker_df.columns:
            blocker_df[src_col] = False

    blocker_map = blocker_df[["group_id", "blk_multi_panel_source", "blk_suspicious_value_text", "blk_duplicate_or_conflict", "blk_years_not_continuous", "blk_unresolved_monetary_unit", "contains_fragmented_value", "contains_inconsistent_percent", "contains_prose_value", "contains_chinese_value", "contains_alpha_num_value", "years_continuous"]].copy()

    sim = review_df.merge(blocker_map, on="group_id", how="left")

    # Rule guard booleans
    sim["r1_panel_row_deduplication_hit"] = sim["blk_duplicate_or_conflict"].map(_to_bool)
    sim["r2_panel_boundary_validation_hit"] = sim["blk_multi_panel_source"].map(_to_bool)
    sim["r3_metric_row_purity_guard_hit"] = (
        sim["blk_suspicious_value_text"].map(_to_bool)
        | sim.get("contains_chinese_value", "").map(_to_bool)
        | sim.get("contains_prose_value", "").map(_to_bool)
        | sim.get("contains_alpha_num_value", "").map(_to_bool)
    )
    sim["r4_numeric_value_sanity_guard_hit"] = (
        sim["value"].map(_is_numeric_like)
        & (~sim.get("contains_fragmented_value", "").map(_to_bool))
        & (~sim.get("contains_inconsistent_percent", "").map(_to_bool))
    )
    sim["r5_year_column_continuity_guard_hit"] = sim.get("years_continuous", "").map(_to_bool)
    sim["r6_source_parser_priority_adjustment_hit"] = (
        sim["source_parser"].map(lambda x: _norm(x).lower() in {"marker", "pdfplumber"})
        & sim["r4_numeric_value_sanity_guard_hit"]
    )

    # Required entry guards
    sim["g_numeric_like"] = sim["value"].map(_is_numeric_like)
    sim["g_no_chinese_mixed_value"] = ~sim["value"].map(_has_chinese_mix)
    sim["g_no_merged_value_cell"] = ~sim["value"].map(_has_merged_value_cell)
    sim["g_no_missing_candidate_id"] = sim["candidate_id"].map(_norm) != ""
    sim["g_no_human_reject_or_needs_more_info"] = ~sim["review_status"].map(lambda s: _norm(s).lower() in {"reject", "needs_more_info", "reject_series", "needs_more_info_series"})
    sim["g_year_valid"] = sim["年份"].map(_year_valid)
    sim["g_metric_target_core"] = sim["标准指标"].map(lambda m: _norm(m).lower() in TARGET_CORE_METRICS)

    # Conflict/duplicate with trusted preview v2
    trusted_key_to_values: Dict[str, Set[str]] = {}
    for _, r in final_df.iterrows():
        k = _build_key(r.get("PDF文件名", ""), r.get("标准指标", ""), _to_int(r.get("年份", 0)))
        trusted_key_to_values.setdefault(k, set()).add(_norm(r.get("value", "")))

    sim["sim_key"] = sim.apply(lambda r: _build_key(r.get("PDF文件名", ""), r.get("标准指标", ""), _to_int(r.get("年份", 0))), axis=1)
    sim["conflict_with_trusted_preview"] = sim.apply(
        lambda r: (r["sim_key"] in trusted_key_to_values) and (_norm(r.get("value", "")) not in trusted_key_to_values.get(r["sim_key"], set())),
        axis=1,
    )
    sim["duplicate_with_trusted_preview"] = sim["sim_key"].map(lambda k: k in trusted_key_to_values)
    sim["g_no_duplicate_or_conflict_with_trusted"] = ~(sim["conflict_with_trusted_preview"] | sim["duplicate_with_trusted_preview"])

    # full pass condition
    guard_cols = [
        "g_numeric_like",
        "g_no_chinese_mixed_value",
        "g_no_merged_value_cell",
        "g_no_duplicate_or_conflict_with_trusted",
        "g_no_missing_candidate_id",
        "g_no_human_reject_or_needs_more_info",
        "g_year_valid",
        "g_metric_target_core",
    ]
    sim["all_entry_guards_pass"] = sim[guard_cols].all(axis=1)

    # rule bundle pass (at least one structural denoise rule + sanity rules)
    sim["rule_bundle_pass"] = (
        (sim["r1_panel_row_deduplication_hit"] | sim["r2_panel_boundary_validation_hit"] | sim["r6_source_parser_priority_adjustment_hit"])
        & sim["r4_numeric_value_sanity_guard_hit"]
        & sim["r5_year_column_continuity_guard_hit"]
        & (~sim["r3_metric_row_purity_guard_hit"])
    )

    sim["would_rescue"] = sim["all_entry_guards_pass"] & sim["rule_bundle_pass"]

    # categories
    sim["simulation_bucket"] = "still_review_required"
    sim.loc[~sim["all_entry_guards_pass"], "simulation_bucket"] = "blocked_by_denoise"
    sim.loc[sim["would_rescue"], "simulation_bucket"] = "would_rescue_from_review"

    would_rescue = sim[sim["simulation_bucket"] == "would_rescue_from_review"].copy()
    still_review = sim[sim["simulation_bucket"] == "still_review_required"].copy()
    blocked = sim[sim["simulation_bucket"] == "blocked_by_denoise"].copy()

    # apply simulation-only source bucket
    would_rescue["source_bucket"] = "simulated_panel_denoise_rescue"

    # dedupe / conflict audits on would_rescue itself
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
                    "conflict_type": "value_conflict_with_trusted",
                }
            )
    conflict_audit = pd.DataFrame(conflict_rows)
    if conflict_audit.empty:
        conflict_audit = pd.DataFrame([{"note": "no_value_conflict_with_trusted_preview"}])

    # rule hit audit
    rule_hit_audit = pd.DataFrame(
        [
            {"rule_category": "panel_row_deduplication", "hit_row_count": int(sim["r1_panel_row_deduplication_hit"].sum())},
            {"rule_category": "panel_boundary_validation", "hit_row_count": int(sim["r2_panel_boundary_validation_hit"].sum())},
            {"rule_category": "metric_row_purity_guard", "hit_row_count": int(sim["r3_metric_row_purity_guard_hit"].sum())},
            {"rule_category": "numeric_value_sanity_guard", "hit_row_count": int(sim["r4_numeric_value_sanity_guard_hit"].sum())},
            {"rule_category": "year_column_continuity_guard", "hit_row_count": int(sim["r5_year_column_continuity_guard_hit"].sum())},
            {"rule_category": "source_parser_priority_adjustment", "hit_row_count": int(sim["r6_source_parser_priority_adjustment_hit"].sum())},
            {"rule_category": "would_rescue_from_review", "hit_row_count": int(len(would_rescue))},
            {"rule_category": "still_review_required", "hit_row_count": int(len(still_review))},
            {"rule_category": "blocked_by_denoise", "hit_row_count": int(len(blocked))},
        ]
    )

    # impact estimate
    impact_df = pd.DataFrame(
        [
            {
                "scenario": "simulation_result",
                "input_review_required_row_count": input_review_required_row_count,
                "would_rescue_row_count": int(len(would_rescue)),
                "still_review_required_row_count": int(len(still_review)),
                "blocked_row_count": int(len(blocked)),
                "reduction_ratio": float(len(would_rescue) / input_review_required_row_count) if input_review_required_row_count else 0.0,
            }
        ]
    )

    if not impact_ref_df.empty:
        for c in impact_ref_df.columns:
            if c not in impact_df.columns:
                impact_df[c] = ""
        impact_combined = pd.concat([impact_df, impact_ref_df], ignore_index=True, sort=False)
    else:
        impact_combined = impact_df

    _write_excel(OUT_RESCUE, {"would_rescue_from_review": would_rescue})
    _write_excel(OUT_STILL, {"still_review_required_after_simulation": still_review})
    _write_excel(OUT_BLOCKED, {"blocked_by_denoise_rules": blocked})
    _write_excel(OUT_HIT_AUDIT, {"denoise_rule_hit_audit": rule_hit_audit, "rule_catalog": rules_df})
    _write_excel(OUT_CONFLICT, {"conflict_audit": conflict_audit})
    _write_excel(OUT_IMPACT, {"impact_estimate": impact_combined})

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

    forbidden_fields_generated = sorted([c for c in set(sim.columns) if c in FORBIDDEN_FIELDS])
    duplicate_trusted_key_count_would_rescue = int(len(dup_keys))
    value_conflict_count_with_final_preview_v2 = 0 if (len(conflict_rows) == 0) else len(conflict_rows)

    final_after_hash = _sha256(IN_307G_FINAL)
    final_trusted_preview_v2_unchanged = final_before_hash == final_after_hash

    after_parser_outputs = _snapshot_parser_outputs()
    parser_output_files_modified = any(before_parser_outputs[k] != after_parser_outputs[k] for k in before_parser_outputs.keys())
    parser_output_modified_files = [k for k in before_parser_outputs.keys() if before_parser_outputs[k] != after_parser_outputs[k]]

    after_guard = _snapshot_guard()
    production_files_modified = any(before_guard[k] != after_guard[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before_guard["official_02b"] != after_guard["official_02b"]
    formal_rules_modified = before_guard["formal_rules"] != after_guard["formal_rules"]
    standardizer_modified = before_guard["standardizer"] != after_guard["standardizer"]
    release_package_modified = before_guard["release_zip"] != after_guard["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-308C",
        "mode": "parser_panel_denoise_rule_simulation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_review_required_row_count": input_review_required_row_count,
        "would_rescue_row_count": int(len(would_rescue)),
        "still_review_required_row_count": int(len(still_review)),
        "blocked_by_denoise_row_count": int(len(blocked)),
        "input_review_required_row_count_preserved": bool(input_review_required_row_count == len(sim)),
        "final_trusted_preview_v2_unchanged": bool(final_trusted_preview_v2_unchanged),
        "parser_output_files_unchanged": bool(not parser_output_files_modified),
        "parser_output_modified_files": parser_output_modified_files,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "forbidden_fields_generated": forbidden_fields_generated,
        "duplicate_trusted_key_count_would_rescue": duplicate_trusted_key_count_would_rescue,
        "value_conflict_count_with_final_preview_v2": value_conflict_count_with_final_preview_v2,
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 308C Parser Panel Denoise Rule Simulation",
        "",
        "## Scope",
        "- simulation only on review_required rows",
        "- no parser rerun, no parser output modification",
        "- no merge to trusted preview in this stage",
        "",
        "## Simulation Result",
        f"- input_review_required_row_count: {input_review_required_row_count}",
        f"- would_rescue_from_review: {len(would_rescue)}",
        f"- still_review_required_after_simulation: {len(still_review)}",
        f"- blocked_by_denoise_rules: {len(blocked)}",
        "",
        "## Guard Assertions",
        f"- input_review_required_row_count_preserved: {summary['input_review_required_row_count_preserved']}",
        f"- final_trusted_preview_v2_unchanged: {summary['final_trusted_preview_v2_unchanged']}",
        f"- parser_output_files_unchanged: {summary['parser_output_files_unchanged']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- duplicate_trusted_key_count_would_rescue: {summary['duplicate_trusted_key_count_would_rescue']}",
        f"- value_conflict_count_with_final_preview_v2: {summary['value_conflict_count_with_final_preview_v2']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_308c_summary_json: {OUT_SUMMARY}")
    print(f"eval_308c_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
