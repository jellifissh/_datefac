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
OUT_DIR = BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2"

IN_Y_REVIEW = BASE_DIR / "output" / "eval_306y_potential_safe_relaxation_review_package" / "306y_relaxation_candidate_review.xlsx"
IN_W_GROUP = BASE_DIR / "output" / "eval_306w_relaxed_auto_accept_policy_simulation" / "306w_relaxed_group_routing.xlsx"
IN_W_AUTO = BASE_DIR / "output" / "eval_306w_relaxed_auto_accept_policy_simulation" / "306w_relaxed_auto_accept_candidate_preview.xlsx"
IN_W_REVIEW = BASE_DIR / "output" / "eval_306w_relaxed_auto_accept_policy_simulation" / "306w_relaxed_review_required.xlsx"
IN_X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"
IN_L_MAP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_group_to_candidate_manifest.xlsx"
IN_T_VALID = BASE_DIR / "output" / "eval_306t_missing_candidate_intake_validation" / "306t_valid_missing_candidate_intake.xlsx"

OUT_SUMMARY = OUT_DIR / "306z_summary.json"
OUT_REPORT = OUT_DIR / "306z_report.md"
OUT_GROUP_ROUTING = OUT_DIR / "306z_group_routing_v2.xlsx"
OUT_AUTO = OUT_DIR / "306z_auto_accept_candidate_preview_v2.xlsx"
OUT_REVIEW = OUT_DIR / "306z_review_required_v2.xlsx"
OUT_COMPARE = OUT_DIR / "306z_v1_vs_v2_comparison.xlsx"
OUT_SAFETY = OUT_DIR / "306z_policy_safety_audit.xlsx"
OUT_RULES = OUT_DIR / "306z_policy_rules.json"
OUT_NO_APPLY = OUT_DIR / "306z_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
SEMANTIC_METRICS = {"eps", "pe", "pb", "ev_ebitda", "roe", "gross_margin"}


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

    required = [IN_Y_REVIEW, IN_W_GROUP, IN_W_AUTO, IN_W_REVIEW, IN_X_BLOCKER, IN_L_MAP, IN_T_VALID]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306Z",
                "mode": "conservative_relaxation_policy_v2",
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

    y_review = _drop_note_rows(_load_first_sheet(IN_Y_REVIEW, "relaxation_candidate_review"))
    w_group = _load_first_sheet(IN_W_GROUP, "relaxed_group_routing")
    w_auto = _drop_note_rows(_load_first_sheet(IN_W_AUTO, "relaxed_auto_accept_candidate_preview"))
    w_review = _drop_note_rows(_load_first_sheet(IN_W_REVIEW, "relaxed_review_required"))
    x_blocker = _drop_note_rows(_load_first_sheet(IN_X_BLOCKER, "blocker_by_group"))
    l_map = _drop_note_rows(_load_first_sheet(IN_L_MAP, "group_to_candidate_manifest"))
    t_valid = _drop_note_rows(_load_first_sheet(IN_T_VALID, "valid_missing_candidate_intake"))

    for df in [y_review, w_group, x_blocker, l_map, w_review, w_auto]:
        if "group_id" in df.columns:
            df["group_id"] = df["group_id"].map(_norm)
    if "candidate_id" in l_map.columns:
        l_map["candidate_id"] = l_map["candidate_id"].map(_norm)
    if "candidate_id" in w_review.columns:
        w_review["candidate_id"] = w_review["candidate_id"].map(_norm)
    if "candidate_id" in w_auto.columns:
        w_auto["candidate_id"] = w_auto["candidate_id"].map(_norm)

    # Use 306X blocker rows as base group universe (non-auto groups)
    base = x_blocker.copy()
    base["metric_norm"] = base["标准指标"].map(_norm).str.lower()

    missing_candidate_ids = set(t_valid["candidate_id"].map(_norm).tolist()) if "candidate_id" in t_valid.columns else set()
    missing_candidate_ids_nonempty = {x for x in missing_candidate_ids if x != ""}

    # group -> candidate ids from manifest
    map_group_ids = (
        l_map.groupby("group_id", dropna=False)["candidate_id"]
        .apply(lambda s: sorted({_norm(v) for v in s.tolist() if _norm(v) != ""}))
        .to_dict()
    )

    route_rows: List[Dict[str, Any]] = []
    for _, r in base.iterrows():
        gid = _norm(r.get("group_id", ""))
        metric = _norm(r.get("metric_norm", ""))

        # required allow conditions
        cond_page1 = _to_bool(r.get("page1_summary_clean_candidate", False))
        cond_unit_sem = _to_bool(r.get("unit_unknown_semantic_resolvable", False))
        cond_metric = metric in SEMANTIC_METRICS
        cond_numeric = _to_bool(r.get("all_year_values_numeric_like", False))
        cond_cont_year = _to_bool(r.get("years_continuous", False))
        cond_not_missing_year = not _to_bool(r.get("missing_year", False))
        cond_no_susp = not _to_bool(r.get("blk_suspicious_value_text", False))
        cond_no_dup_conf = not _to_bool(r.get("blk_duplicate_or_conflict", False))
        cond_no_alias = not _to_bool(r.get("alias_recovered", False))
        cond_no_zero = not _to_bool(r.get("zero_candidate_rescued", False))
        cond_no_multi = not _to_bool(r.get("multi_panel_source", False))
        cond_no_reviewed_risky = not _to_bool(r.get("blk_reviewed_risky_group", False))
        cond_no_missing_intake = True
        for cid in map_group_ids.get(gid, []):
            if cid in missing_candidate_ids_nonempty:
                cond_no_missing_intake = False
                break

        # explicit blocks for v2
        explicit_block = any(
            [
                _to_bool(r.get("clean_multi_panel_candidate", False)),
                _to_bool(r.get("clean_missing_year_partial_series", False)),
                _to_bool(r.get("marker_clean_non_page1_candidate", False)),
                _to_bool(r.get("zero_candidate_rescued", False)),
                _to_bool(r.get("alias_recovered", False)),
                _to_bool(r.get("multi_panel_source", False)),
                _to_bool(r.get("missing_year", False)),
                _to_bool(r.get("blk_reviewed_risky_group", False)),
            ]
        )
        if not cond_no_missing_intake:
            explicit_block = True

        allow = all(
            [
                cond_page1,
                cond_unit_sem,
                cond_metric,
                cond_numeric,
                cond_cont_year,
                cond_not_missing_year,
                cond_no_susp,
                cond_no_dup_conf,
                cond_no_alias,
                cond_no_zero,
                cond_no_multi,
                cond_no_reviewed_risky,
                cond_no_missing_intake,
                not explicit_block,
            ]
        )

        reasons: List[str] = []
        if allow:
            reasons.append("page1_summary_plus_semantic_unit_safe_pass")
            route = "auto_accept_candidate_preview_v2"
        else:
            route = "review_required_v2"
            checks = {
                "not_page1_summary_clean": not cond_page1,
                "not_unit_unknown_semantic_resolvable": not cond_unit_sem,
                "metric_not_in_semantic_allowlist": not cond_metric,
                "non_numeric_values": not cond_numeric,
                "years_not_continuous": not cond_cont_year,
                "missing_year_present": not cond_not_missing_year,
                "suspicious_value_text": not cond_no_susp,
                "duplicate_or_conflict": not cond_no_dup_conf,
                "alias_recovered": not cond_no_alias,
                "zero_candidate_rescued": not cond_no_zero,
                "multi_panel_source": not cond_no_multi,
                "reviewed_risky_group": not cond_no_reviewed_risky,
                "missing_candidate_intake_overlap": not cond_no_missing_intake,
                "explicit_v2_block_rule_hit": explicit_block,
            }
            reasons = [k for k, v in checks.items() if v]

        rec = r.to_dict()
        rec["route_bucket_v2"] = route
        rec["route_reason_v2"] = ",".join(reasons)
        route_rows.append(rec)

    route_df = pd.DataFrame(route_rows).fillna("")

    auto_groups = set(route_df[route_df["route_bucket_v2"] == "auto_accept_candidate_preview_v2"]["group_id"].map(_norm).tolist())
    all_candidates = _drop_note_rows(l_map[["group_id", "candidate_id", "PDF文件名", "标准指标", "年份", "数值"]].copy())
    all_candidates["group_id"] = all_candidates["group_id"].map(_norm)
    all_candidates["candidate_id"] = all_candidates["candidate_id"].map(_norm)
    all_candidates["年份"] = all_candidates["年份"].map(_to_int)
    all_candidates["value_raw"] = all_candidates["数值"].map(_norm)
    all_candidates["key"] = all_candidates["PDF文件名"].map(_norm) + "|" + all_candidates["标准指标"].map(_norm) + "|" + all_candidates["年份"].astype(str)

    # v2 routes apply to non-auto group base; keep original 306W auto groups unchanged for comparison context only.
    # Here we generate v2 preview only from auto_groups in v2 base.
    auto_v2 = all_candidates[all_candidates["group_id"].isin(auto_groups)].copy()
    review_v2 = all_candidates[~all_candidates["group_id"].isin(auto_groups)].copy()

    # Exclude missing candidate intake from auto_v2 by hard guard
    if not auto_v2.empty:
        auto_v2 = auto_v2[~auto_v2["candidate_id"].isin(missing_candidate_ids_nonempty)].copy()
    auto_ids = set(auto_v2["candidate_id"].map(_norm).tolist())
    review_v2 = all_candidates[~all_candidates["candidate_id"].map(_norm).isin(auto_ids)].copy()

    # audits
    dup_v2 = auto_v2.groupby("key", dropna=False).size().reset_index(name="count") if not auto_v2.empty else pd.DataFrame(columns=["key", "count"])
    dup_v2 = dup_v2[dup_v2["count"] > 1].copy()
    conflict_rows: List[Dict[str, Any]] = []
    if not auto_v2.empty:
        for k, g in auto_v2.groupby("key", dropna=False):
            vals = sorted({_norm(v) for v in g["value_raw"].tolist() if _norm(v) != ""})
            if len(vals) > 1:
                one = g.iloc[0]
                conflict_rows.append(
                    {
                        "key": k,
                        "PDF文件名": _norm(one.get("PDF文件名", "")),
                        "标准指标": _norm(one.get("标准指标", "")),
                        "年份": _to_int(one.get("年份", 0)),
                        "distinct_values": " | ".join(vals),
                        "row_count": int(len(g)),
                    }
                )
    conflict_v2 = pd.DataFrame(conflict_rows)

    # required safety assertions
    grp_auto = route_df[route_df["route_bucket_v2"] == "auto_accept_candidate_preview_v2"].copy()
    corrected_rejected_needs_to_auto = int(grp_auto["blk_reviewed_risky_group"].map(_to_bool).sum()) if not grp_auto.empty else 0
    missing_to_auto = 0
    if not auto_v2.empty:
        missing_to_auto = int(auto_v2["candidate_id"].isin(missing_candidate_ids_nonempty).sum())
    multi_panel_to_auto = int(grp_auto["multi_panel_source"].map(_to_bool).sum()) if not grp_auto.empty else 0
    zero_candidate_to_auto = int(grp_auto["zero_candidate_rescued"].map(_to_bool).sum()) if not grp_auto.empty else 0
    marker_non_page1_only_to_auto = int(grp_auto["marker_clean_non_page1_candidate"].map(_to_bool).sum()) if not grp_auto.empty else 0
    missing_year_to_auto = int(grp_auto["missing_year"].map(_to_bool).sum()) if not grp_auto.empty else 0

    v1_group_count = int(w_group[w_group["relaxed_route_bucket"].map(_norm) == "relaxed_auto_accept_candidate_preview"]["group_id"].nunique())
    v1_candidate_count = int(len(w_auto))
    v2_group_count = int(len(auto_groups))
    v2_candidate_count = int(len(auto_v2))

    comp_df = pd.DataFrame(
        [
            {
                "v1_auto_accept_group_count": v1_group_count,
                "v2_auto_accept_group_count": v2_group_count,
                "v1_auto_accept_candidate_count": v1_candidate_count,
                "v2_auto_accept_candidate_count": v2_candidate_count,
                "v2_group_delta_vs_v1": v2_group_count - v1_group_count,
                "v2_candidate_delta_vs_v1": v2_candidate_count - v1_candidate_count,
            }
        ]
    )

    safety_df = pd.DataFrame(
        [
            {
                "corrected_rejected_needs_more_info_groups_routed_to_auto_accept_v2_count": corrected_rejected_needs_to_auto,
                "missing_candidates_routed_to_auto_accept_v2_count": missing_to_auto,
                "multi_panel_groups_routed_to_auto_accept_v2_count": multi_panel_to_auto,
                "zero_candidate_rescued_groups_routed_to_auto_accept_v2_count": zero_candidate_to_auto,
                "marker_clean_non_page1_candidate_only_groups_routed_to_auto_accept_v2_count": marker_non_page1_only_to_auto,
                "missing_year_groups_routed_to_auto_accept_v2_count": missing_year_to_auto,
                "duplicate_key_count_auto_accept_v2": int(len(dup_v2)),
                "value_conflict_count_auto_accept_v2": int(len(conflict_v2)),
            }
        ]
    )

    rules_json = {
        "stage": "EVAL-306Z",
        "mode": "conservative_relaxation_policy_v2",
        "allow_only": {
            "page1_summary_clean_candidate": True,
            "unit_unknown_semantic_resolvable": True,
            "metric_allowlist": sorted(list(SEMANTIC_METRICS)),
            "values_numeric_like": True,
            "years_continuous": True,
            "missing_year": False,
            "suspicious_value_text": False,
            "duplicate_or_conflict": False,
            "alias_recovered": False,
            "zero_candidate_rescued": False,
            "multi_panel_source": False,
            "reviewed_risky_group": False,
            "missing_candidate_intake_overlap": False,
        },
        "always_review": [
            "clean_multi_panel_candidate",
            "clean_missing_year_partial_series",
            "marker_clean_non_page1_candidate",
            "zero_candidate_rescued",
            "alias_recovered",
            "multi_panel_source",
            "missing_year",
            "reviewed_risky_group",
            "missing_candidate_intake_overlap",
        ],
        "no_safe_to_apply": True,
        "no_approve_for_real_apply": True,
    }

    _write_excel(
        OUT_GROUP_ROUTING,
        {
            "group_routing_v2": route_df,
            "route_distribution_v2": route_df.groupby("route_bucket_v2", dropna=False).size().reset_index(name="group_count"),
        },
    )
    _write_excel(OUT_AUTO, {"auto_accept_candidate_preview_v2": auto_v2})
    _write_excel(OUT_REVIEW, {"review_required_v2": review_v2})
    _write_excel(OUT_COMPARE, {"v1_vs_v2_comparison": comp_df})
    _write_excel(
        OUT_SAFETY,
        {
            "policy_safety_audit": safety_df,
            "duplicate_key_audit_v2": dup_v2 if not dup_v2.empty else pd.DataFrame([{"note": "duplicate_key_count_0"}]),
            "value_conflict_audit_v2": conflict_v2 if not conflict_v2.empty else pd.DataFrame([{"note": "value_conflict_count_0"}]),
        },
    )
    _write_json(OUT_RULES, rules_json)
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

    forbidden_fields_generated = sorted([c for c in set(route_df.columns).union(set(auto_v2.columns)).union(set(review_v2.columns)) if c in FORBIDDEN_FIELDS])

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-306Z",
        "mode": "conservative_relaxation_policy_v2",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "v1_auto_accept_group_count": v1_group_count,
        "v2_auto_accept_group_count": v2_group_count,
        "v1_auto_accept_candidate_count": v1_candidate_count,
        "v2_auto_accept_candidate_count": v2_candidate_count,
        "corrected_rejected_needs_more_info_groups_routed_to_auto_accept_v2_count": corrected_rejected_needs_to_auto,
        "missing_candidates_routed_to_auto_accept_v2_count": missing_to_auto,
        "multi_panel_groups_routed_to_auto_accept_v2_count": multi_panel_to_auto,
        "zero_candidate_rescued_groups_routed_to_auto_accept_v2_count": zero_candidate_to_auto,
        "marker_clean_non_page1_candidate_only_groups_routed_to_auto_accept_v2_count": marker_non_page1_only_to_auto,
        "missing_year_groups_routed_to_auto_accept_v2_count": missing_year_to_auto,
        "duplicate_key_count_auto_accept_v2": int(len(dup_v2)),
        "value_conflict_count_auto_accept_v2": int(len(conflict_v2)),
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
        "# 306Z Conservative Relaxation Policy v2",
        "",
        "## V1 vs V2",
        f"- v1_auto_accept_group_count: {v1_group_count}",
        f"- v2_auto_accept_group_count: {v2_group_count}",
        f"- v1_auto_accept_candidate_count: {v1_candidate_count}",
        f"- v2_auto_accept_candidate_count: {v2_candidate_count}",
        "",
        "## Safety Assertions",
        f"- corrected/rejected/needs_more_info to auto_accept_v2: {corrected_rejected_needs_to_auto}",
        f"- missing candidates to auto_accept_v2: {missing_to_auto}",
        f"- multi_panel groups to auto_accept_v2: {multi_panel_to_auto}",
        f"- zero_candidate_rescued groups to auto_accept_v2: {zero_candidate_to_auto}",
        f"- marker_clean_non_page1_candidate-only groups to auto_accept_v2: {marker_non_page1_only_to_auto}",
        f"- missing_year groups to auto_accept_v2: {missing_year_to_auto}",
        f"- duplicate_key_count_auto_accept_v2: {len(dup_v2)}",
        f"- value_conflict_count_auto_accept_v2: {len(conflict_v2)}",
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

    print(f"eval_306z_summary_json: {OUT_SUMMARY}")
    print(f"eval_306z_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
