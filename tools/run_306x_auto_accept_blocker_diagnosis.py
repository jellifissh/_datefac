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
OUT_DIR = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis"

IN_W_GROUP = BASE_DIR / "output" / "eval_306w_relaxed_auto_accept_policy_simulation" / "306w_relaxed_group_routing.xlsx"
IN_W_AUTO = BASE_DIR / "output" / "eval_306w_relaxed_auto_accept_policy_simulation" / "306w_relaxed_auto_accept_candidate_preview.xlsx"
IN_W_REVIEW = BASE_DIR / "output" / "eval_306w_relaxed_auto_accept_policy_simulation" / "306w_relaxed_review_required.xlsx"
IN_W_COMPARE = BASE_DIR / "output" / "eval_306w_relaxed_auto_accept_policy_simulation" / "306w_strict_vs_relaxed_comparison.xlsx"
IN_L_GROUP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"
IN_U_GROUP = BASE_DIR / "output" / "eval_306u_risk_based_auto_accept_policy_simulation" / "306u_group_risk_routing.xlsx"
IN_V_CALIB = BASE_DIR / "output" / "eval_306v_risk_policy_calibration" / "306v_policy_calibration_by_review_result.xlsx"

OUT_SUMMARY = OUT_DIR / "306x_summary.json"
OUT_REPORT = OUT_DIR / "306x_report.md"
OUT_BLOCKER_BY_GROUP = OUT_DIR / "306x_blocker_by_group.xlsx"
OUT_BLOCKER_DIST = OUT_DIR / "306x_blocker_distribution.xlsx"
OUT_CAND_IMPACT = OUT_DIR / "306x_candidate_impact_by_blocker.xlsx"
OUT_SINGLE = OUT_DIR / "306x_single_blocker_groups.xlsx"
OUT_MULTI = OUT_DIR / "306x_multi_blocker_groups.xlsx"
OUT_RELAX = OUT_DIR / "306x_potential_safe_relaxation_candidates.xlsx"
OUT_NO_APPLY = OUT_DIR / "306x_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
YEAR_COLS = [str(y) for y in range(2020, 2031)]


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
    s = _norm(v).lower()
    return s in {"true", "1", "yes"}


def _to_int(v: Any) -> int:
    s = _norm(v)
    if s == "":
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def _is_numeric_like(s: str) -> bool:
    t = _norm(s)
    if t == "":
        return True
    t = t.replace(",", "").replace("%", "").replace("x", "").replace("X", "")
    try:
        float(t)
        return True
    except Exception:
        return False


def _semantic_unit_for_metric(metric: str) -> str:
    m = _norm(metric).lower()
    if m == "eps":
        return "yuan_per_share"
    if m in {"pe", "pb", "ev_ebitda"}:
        return "multiple"
    if m in {"roe", "gross_margin"}:
        return "percent"
    return ""


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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_W_GROUP, IN_W_AUTO, IN_W_REVIEW, IN_W_COMPARE, IN_L_GROUP, IN_U_GROUP, IN_V_CALIB]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306X",
                "mode": "auto_accept_blocker_diagnosis",
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

    before = _snapshot_guard()

    w_group = _load_first_sheet(IN_W_GROUP, "relaxed_group_routing")
    w_auto = _drop_note_rows(_load_first_sheet(IN_W_AUTO, "relaxed_auto_accept_candidate_preview"))
    w_review = _drop_note_rows(_load_first_sheet(IN_W_REVIEW, "relaxed_review_required"))
    w_compare = _load_first_sheet(IN_W_COMPARE, "strict_vs_relaxed_comparison")
    l_group = _load_first_sheet(IN_L_GROUP, "grouped_review_table")
    u_group = _load_first_sheet(IN_U_GROUP, "group_risk_routing")
    v_calib = _drop_note_rows(_load_first_sheet(IN_V_CALIB, "policy_calibration_by_review_result"))

    w_group["group_id"] = w_group["group_id"].map(_norm)
    l_group["group_id"] = l_group["group_id"].map(_norm)
    u_group["group_id"] = u_group["group_id"].map(_norm)

    # Real reviewed risky group map from 306V calibration
    reviewed_risky_groups: Set[str] = set()
    if not v_calib.empty and "group_id" in v_calib.columns and "real_review_label" in v_calib.columns:
        for _, r in v_calib.iterrows():
            gid = _norm(r.get("group_id", ""))
            label = _norm(r.get("real_review_label", "")).lower()
            if label in {"corrected", "rejected", "needs_more_info"} and gid != "":
                reviewed_risky_groups.add(gid)

    # Prepare per-group candidate count from relaxed review pool
    cand_count_map = (
        w_review.groupby(w_review["group_id"].map(_norm), dropna=False)
        .size()
        .reset_index(name="candidate_count_review_required")
        if not w_review.empty and "group_id" in w_review.columns
        else pd.DataFrame(columns=["group_id", "candidate_count_review_required"])
    )
    cand_count_lookup = { _norm(r["group_id"]): int(r["candidate_count_review_required"]) for _, r in cand_count_map.iterrows() }

    # Duplicate/conflict check within review pool (diagnostic, as blocker category requested)
    duplicate_groups: Set[str] = set()
    conflict_groups: Set[str] = set()
    if not w_review.empty:
        tmp = w_review.copy()
        tmp["key"] = tmp.get("key", tmp["PDF文件名"].map(_norm) + "|" + tmp["标准指标"].map(_norm) + "|" + tmp["年份"].map(_to_int).astype(str))
        dup_key_df = tmp.groupby("key", dropna=False).size().reset_index(name="cnt")
        dup_keys = set(dup_key_df[dup_key_df["cnt"] > 1]["key"].tolist())
        if dup_keys:
            duplicate_groups = set(tmp[tmp["key"].isin(dup_keys)]["group_id"].map(_norm).tolist())
        for _, g in tmp.groupby("key", dropna=False):
            vals = sorted({_norm(v) for v in g["value_raw"].tolist() if _norm(v) != ""})
            if len(vals) > 1:
                conflict_groups.update(g["group_id"].map(_norm).tolist())

    # Non-auto groups
    non_auto = w_group[w_group["relaxed_route_bucket"].map(_norm) != "relaxed_auto_accept_candidate_preview"].copy()

    blocker_rows: List[Dict[str, Any]] = []
    for _, r in non_auto.iterrows():
        gid = _norm(r.get("group_id", ""))
        metric = _norm(r.get("标准指标", ""))
        parser = _norm(r.get("来源解析器", ""))

        missing_year = _to_bool(r.get("missing_year", False))
        unit_unknown = _to_bool(r.get("unit_unknown", False))
        zero_candidate_rescued = _to_bool(r.get("zero_candidate_rescued", False))
        alias_recovered = _to_bool(r.get("alias_recovered", False))
        multi_panel_source = _to_bool(r.get("multi_panel_source", False))
        suspicious_value_text = any(
            _to_bool(r.get(c, False))
            for c in [
                "contains_chinese_value",
                "contains_alpha_num_value",
                "contains_fragmented_value",
                "contains_inconsistent_percent",
                "contains_prose_value",
                "obvious_pdfplumber_noise",
            ]
        )
        years_not_continuous = not _to_bool(r.get("years_continuous", True))
        review_priority = _norm(r.get("review_priority", "")).upper()
        unknown_priority = review_priority not in {"LOW", "MEDIUM", "HIGH"}
        semantic_unit = _semantic_unit_for_metric(metric)
        unresolved_monetary_unit = bool(unit_unknown and semantic_unit == "")
        reviewed_risky_group = gid in reviewed_risky_groups
        duplicate_or_conflict = (gid in duplicate_groups) or (gid in conflict_groups)
        unit_unknown_or_warning = unit_unknown

        blockers = {
            "missing_year": missing_year,
            "unit_unknown_or_warning": unit_unknown_or_warning,
            "zero_candidate_rescued": zero_candidate_rescued,
            "alias_recovered": alias_recovered,
            "multi_panel_source": multi_panel_source,
            "suspicious_value_text": suspicious_value_text,
            "years_not_continuous": years_not_continuous,
            "unresolved_monetary_unit": unresolved_monetary_unit,
            "reviewed_risky_group": reviewed_risky_group,
            "duplicate_or_conflict": duplicate_or_conflict,
            "unknown_priority": unknown_priority,
        }

        blocker_list = [k for k, v in blockers.items() if v]
        blocker_count = len(blocker_list)

        # Potential safe relaxation candidates (diagnosis only)
        values = [_norm(r.get(y, "")) for y in YEAR_COLS]
        has_values = any(v != "" for v in values)
        all_numeric = all(_is_numeric_like(v) for v in values)
        page1_summary = _to_bool(r.get("page1_summary", False))
        marker_only = _to_bool(r.get("marker_only", False)) or _norm(parser).lower() == "marker"

        unit_unknown_semantic_resolvable = bool(unit_unknown and semantic_unit != "" and not unresolved_monetary_unit)
        clean_multi_panel_candidate = bool(
            multi_panel_source
            and not suspicious_value_text
            and not years_not_continuous
            and not missing_year
            and not reviewed_risky_group
            and all_numeric
            and has_values
        )
        clean_missing_year_partial_series = bool(
            missing_year
            and not suspicious_value_text
            and not years_not_continuous
            and not unresolved_monetary_unit
            and all_numeric
            and has_values
        )
        page1_summary_clean_candidate = bool(
            page1_summary
            and not missing_year
            and not suspicious_value_text
            and not years_not_continuous
            and not unresolved_monetary_unit
            and not reviewed_risky_group
            and all_numeric
            and has_values
        )
        marker_clean_non_page1_candidate = bool(
            marker_only
            and (not page1_summary)
            and not missing_year
            and not suspicious_value_text
            and not years_not_continuous
            and not unresolved_monetary_unit
            and not reviewed_risky_group
            and all_numeric
            and has_values
        )

        rec = r.to_dict()
        rec["candidate_count_review_required"] = int(cand_count_lookup.get(gid, 0))
        rec["blocker_count"] = blocker_count
        rec["blocker_list"] = "|".join(blocker_list)
        for k, v in blockers.items():
            rec[f"blk_{k}"] = bool(v)
        rec["unit_unknown_semantic_resolvable"] = unit_unknown_semantic_resolvable
        rec["clean_multi_panel_candidate"] = clean_multi_panel_candidate
        rec["clean_missing_year_partial_series"] = clean_missing_year_partial_series
        rec["page1_summary_clean_candidate"] = page1_summary_clean_candidate
        rec["marker_clean_non_page1_candidate"] = marker_clean_non_page1_candidate
        blocker_rows.append(rec)

    blocker_df = pd.DataFrame(blocker_rows).fillna("")
    if blocker_df.empty:
        blocker_df = pd.DataFrame([{"note": "no_non_auto_groups"}])

    # Distribution by blocker
    blocker_cols = [c for c in blocker_df.columns if c.startswith("blk_")]
    dist_rows: List[Dict[str, Any]] = []
    for c in blocker_cols:
        gcount = int(blocker_df[blocker_df[c] == True]["group_id"].nunique()) if "group_id" in blocker_df.columns else 0
        ccount = int(blocker_df[blocker_df[c] == True]["candidate_count_review_required"].sum()) if "candidate_count_review_required" in blocker_df.columns else 0
        dist_rows.append(
            {
                "blocker": c.replace("blk_", ""),
                "group_count": gcount,
                "candidate_count": ccount,
            }
        )
    blocker_dist_df = pd.DataFrame(dist_rows).sort_values(["group_count", "candidate_count"], ascending=False).reset_index(drop=True)

    cand_impact_df = blocker_dist_df.copy().rename(columns={"candidate_count": "candidate_count_impacted"})

    single_df = blocker_df[blocker_df["blocker_count"] == 1].copy() if "blocker_count" in blocker_df.columns else pd.DataFrame()
    multi_df = blocker_df[blocker_df["blocker_count"] > 1].copy() if "blocker_count" in blocker_df.columns else pd.DataFrame()

    relax_cols = [
        "unit_unknown_semantic_resolvable",
        "clean_multi_panel_candidate",
        "clean_missing_year_partial_series",
        "page1_summary_clean_candidate",
        "marker_clean_non_page1_candidate",
    ]
    relax_df = blocker_df[
        blocker_df[relax_cols].any(axis=1)
    ].copy() if not blocker_df.empty and all(c in blocker_df.columns for c in relax_cols) else pd.DataFrame()

    strict_groups = int(_to_int(w_compare.iloc[0].get("strict_auto_accept_group_count", 0))) if not w_compare.empty else 0
    relaxed_groups = int(_to_int(w_compare.iloc[0].get("relaxed_auto_accept_group_count", 0))) if not w_compare.empty else 0
    strict_candidates = int(_to_int(w_compare.iloc[0].get("strict_auto_accept_candidate_count", 0))) if not w_compare.empty else 0
    relaxed_candidates = int(_to_int(w_compare.iloc[0].get("relaxed_auto_accept_candidate_count", 0))) if not w_compare.empty else 0
    non_auto_group_count = int(non_auto["group_id"].nunique()) if not non_auto.empty else 0

    _write_excel(
        OUT_BLOCKER_BY_GROUP,
        {
            "blocker_by_group": blocker_df,
        },
    )
    _write_excel(
        OUT_BLOCKER_DIST,
        {
            "blocker_distribution": blocker_dist_df,
        },
    )
    _write_excel(
        OUT_CAND_IMPACT,
        {
            "candidate_impact_by_blocker": cand_impact_df,
        },
    )
    _write_excel(
        OUT_SINGLE,
        {
            "single_blocker_groups": single_df if not single_df.empty else pd.DataFrame([{"note": "no_single_blocker_groups"}]),
        },
    )
    _write_excel(
        OUT_MULTI,
        {
            "multi_blocker_groups": multi_df if not multi_df.empty else pd.DataFrame([{"note": "no_multi_blocker_groups"}]),
        },
    )
    _write_excel(
        OUT_RELAX,
        {
            "potential_safe_relaxation_candidates": relax_df if not relax_df.empty else pd.DataFrame([{"note": "no_relaxation_candidates"}]),
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

    forbidden_fields_generated = sorted([c for c in blocker_df.columns if c in FORBIDDEN_FIELDS])

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-306X",
        "mode": "auto_accept_blocker_diagnosis",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "strict_auto_accept_group_count": strict_groups,
        "relaxed_auto_accept_group_count": relaxed_groups,
        "strict_auto_accept_candidate_count": strict_candidates,
        "relaxed_auto_accept_candidate_count": relaxed_candidates,
        "non_auto_group_count": non_auto_group_count,
        "single_blocker_group_count": int(single_df["group_id"].nunique()) if not single_df.empty and "group_id" in single_df.columns else 0,
        "multi_blocker_group_count": int(multi_df["group_id"].nunique()) if not multi_df.empty and "group_id" in multi_df.columns else 0,
        "potential_safe_relaxation_group_count": int(relax_df["group_id"].nunique()) if not relax_df.empty and "group_id" in relax_df.columns else 0,
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

    top_blockers = blocker_dist_df.head(5).to_dict(orient="records") if not blocker_dist_df.empty else []
    report_lines = [
        "# 306X Auto-Accept Blocker Diagnosis",
        "",
        "## Baseline",
        f"- strict_auto_accept_group_count: {strict_groups}",
        f"- relaxed_auto_accept_group_count: {relaxed_groups}",
        f"- strict_auto_accept_candidate_count: {strict_candidates}",
        f"- relaxed_auto_accept_candidate_count: {relaxed_candidates}",
        f"- non_auto_group_count: {non_auto_group_count}",
        "",
        "## Blocker Segmentation",
        f"- single_blocker_group_count: {summary['single_blocker_group_count']}",
        f"- multi_blocker_group_count: {summary['multi_blocker_group_count']}",
        f"- potential_safe_relaxation_group_count: {summary['potential_safe_relaxation_group_count']}",
        "",
        "## Top Blockers (by group_count)",
    ]
    for x in top_blockers:
        report_lines.append(f"- {x.get('blocker')}: groups={x.get('group_count')}, candidates={x.get('candidate_count')}")
    report_lines += [
        "",
        "## Guard",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306x_summary_json: {OUT_SUMMARY}")
    print(f"eval_306x_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
