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
OUT_DIR = BASE_DIR / "output" / "eval_306w_relaxed_auto_accept_policy_simulation"

IN_306V_SUMMARY = BASE_DIR / "output" / "eval_306v_risk_policy_calibration" / "306v_summary.json"
IN_306U_GROUP_ROUTING = BASE_DIR / "output" / "eval_306u_risk_based_auto_accept_policy_simulation" / "306u_group_risk_routing.xlsx"
IN_306L_GROUP_TABLE = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"
IN_306L_GROUP_MAP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_group_to_candidate_manifest.xlsx"
IN_306S_PROJECTION = BASE_DIR / "output" / "eval_306s_reviewed_projection_unit_normalization_gate" / "306s_unit_normalized_projection.xlsx"
IN_306T_VALID_MISSING = BASE_DIR / "output" / "eval_306t_missing_candidate_intake_validation" / "306t_valid_missing_candidate_intake.xlsx"

IN_306O_REVIEW_RESULTS = BASE_DIR / "output" / "eval_306o_expand_grouped_review_to_candidate_results" / "306o_candidate_review_results.xlsx"
IN_306P_CORRECTED = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_corrected_reviewed_candidates.xlsx"
IN_306P_REJECTED = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_rejected_candidates.xlsx"
IN_306P_NEEDS = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_needs_more_info_candidates.xlsx"

OUT_SUMMARY = OUT_DIR / "306w_summary.json"
OUT_REPORT = OUT_DIR / "306w_report.md"
OUT_GROUP_ROUTING = OUT_DIR / "306w_relaxed_group_routing.xlsx"
OUT_AUTO_ACCEPT = OUT_DIR / "306w_relaxed_auto_accept_candidate_preview.xlsx"
OUT_REVIEW_REQUIRED = OUT_DIR / "306w_relaxed_review_required.xlsx"
OUT_COMPARE = OUT_DIR / "306w_strict_vs_relaxed_comparison.xlsx"
OUT_SAFETY = OUT_DIR / "306w_relaxed_policy_safety_audit.xlsx"
OUT_POLICY = OUT_DIR / "306w_policy_rules.json"
OUT_NO_APPLY = OUT_DIR / "306w_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
YEAR_COLS = [str(y) for y in range(2020, 2031)]
SEMANTIC_UNIT_METRICS = {"eps", "pe", "pb", "ev_ebitda", "roe", "gross_margin"}


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


def _extract_human_risky_groups(df: pd.DataFrame) -> Set[str]:
    out: Set[str] = set()
    if df.empty:
        return out
    if "group_id" not in df.columns:
        return out
    label_col = "decision_candidate" if "decision_candidate" in df.columns else ""
    if label_col == "":
        return out
    for gid, g in df.groupby(df["group_id"].map(_norm)):
        labels = {_norm(x).lower() for x in g[label_col].tolist() if _norm(x) != ""}
        if "correct_value" in labels or "reject" in labels or "needs_more_info" in labels:
            out.add(gid)
    return out


def _semantic_unit_name(metric: str) -> str:
    m = _norm(metric).lower()
    if m == "eps":
        return "yuan_per_share"
    if m in {"pe", "pb", "ev_ebitda"}:
        return "multiple"
    if m in {"roe", "gross_margin"}:
        return "percent"
    return ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_306V_SUMMARY,
        IN_306U_GROUP_ROUTING,
        IN_306L_GROUP_TABLE,
        IN_306L_GROUP_MAP,
        IN_306S_PROJECTION,
        IN_306T_VALID_MISSING,
        IN_306O_REVIEW_RESULTS,
        IN_306P_CORRECTED,
        IN_306P_REJECTED,
        IN_306P_NEEDS,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306W",
                "mode": "relaxed_auto_accept_policy_simulation",
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

    summary_306v = json.loads(IN_306V_SUMMARY.read_text(encoding="utf-8"))
    strict_auto_accept_group_count = int(summary_306v.get("auto_accept_group_count", 0))
    strict_auto_accept_candidate_count = int(summary_306v.get("auto_accept_candidate_count", 0))
    strict_review_reduction_rate = float(summary_306v.get("review_reduction_rate", 0.0))

    gtable = _load_first_sheet(IN_306L_GROUP_TABLE, "grouped_review_table")
    gmap = _load_first_sheet(IN_306L_GROUP_MAP, "group_to_candidate_manifest")
    ugroup = _load_first_sheet(IN_306U_GROUP_ROUTING, "group_risk_routing")
    sproj = _drop_note_rows(_load_first_sheet(IN_306S_PROJECTION, "unit_normalized_projection"))
    tvalid = _drop_note_rows(_load_first_sheet(IN_306T_VALID_MISSING, "valid_missing_candidate_intake"))
    oreview = _drop_note_rows(_load_first_sheet(IN_306O_REVIEW_RESULTS, "candidate_review_results"))
    pcorr = _drop_note_rows(_load_first_sheet(IN_306P_CORRECTED, "corrected_reviewed_candidates"))
    prej = _drop_note_rows(_load_first_sheet(IN_306P_REJECTED, "rejected_candidates"))
    pneed = _drop_note_rows(_load_first_sheet(IN_306P_NEEDS, "needs_more_info_candidates"))

    for df, cols in [
        (gtable, ["group_id", "标准指标", "来源解析器"]),
        (gmap, ["group_id", "candidate_id", "PDF文件名", "标准指标", "年份", "数值"]),
    ]:
        for c in cols:
            if c not in df.columns:
                raise RuntimeError(f"missing column {c}")

    gtable["group_id"] = gtable["group_id"].map(_norm)
    gmap["group_id"] = gmap["group_id"].map(_norm)
    gmap["candidate_id"] = gmap["candidate_id"].map(_norm)
    gmap["年份"] = gmap["年份"].map(_to_int)

    strict_route_by_group = {
        _norm(r["group_id"]): _norm(r["route_bucket"]) for _, r in ugroup.iterrows() if _norm(r.get("group_id", "")) != ""
    }

    reviewed_candidate_ids = set(sproj["candidate_id"].map(_norm).tolist()) if "candidate_id" in sproj.columns else set()
    missing_candidate_ids = set(tvalid["candidate_id"].map(_norm).tolist()) if "candidate_id" in tvalid.columns else set()
    missing_candidate_ids_nonempty = {x for x in missing_candidate_ids if x != ""}

    risky_groups = _extract_human_risky_groups(oreview)
    risky_groups |= { _norm(x) for x in pcorr.get("group_id", pd.Series(dtype=object)).tolist() if _norm(x) != "" }
    risky_groups |= { _norm(x) for x in pneed.get("group_id", pd.Series(dtype=object)).tolist() if _norm(x) != "" }
    if "group_id" in prej.columns:
        risky_groups |= { _norm(x) for x in prej.get("group_id", pd.Series(dtype=object)).tolist() if _norm(x) != "" }

    routing_rows: List[Dict[str, Any]] = []
    route_by_group: Dict[str, str] = {}

    for _, r in gtable.iterrows():
        gid = _norm(r.get("group_id", ""))
        metric = _norm(r.get("标准指标", "")).lower()
        parser = _norm(r.get("来源解析器", ""))

        missing_year = _to_bool(r.get("missing_year", False))
        unit_unknown = _to_bool(r.get("unit_unknown", False))
        alias_recovered = _to_bool(r.get("alias_recovered", False))
        zero_candidate_rescued = _to_bool(r.get("zero_candidate_rescued", False))
        multi_panel_source = _to_bool(r.get("multi_panel_source", False))
        years_continuous = _to_bool(r.get("years_continuous", True))
        contains_suspicious = any(
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

        is_marker_only = _to_bool(r.get("marker_only", False)) or _norm(parser).lower() == "marker"
        is_page1_summary = _to_bool(r.get("page1_summary", False))
        semantic_unit = _semantic_unit_name(metric)

        has_values = False
        all_numeric = True
        for y in YEAR_COLS:
            v = _norm(r.get(y, ""))
            if v != "":
                has_values = True
            if not _is_numeric_like(v):
                all_numeric = False

        route = "relaxed_review_required"
        reasons: List[str] = []
        relaxed_gate = False

        if gid in risky_groups:
            reasons.append("human_risky_group_block")
        if zero_candidate_rescued:
            reasons.append("zero_candidate_rescued_block")
        if alias_recovered:
            reasons.append("alias_recovered_block")
        if multi_panel_source:
            reasons.append("multi_panel_source_block")
        if missing_year:
            reasons.append("missing_year_block")
        if not years_continuous:
            reasons.append("years_not_continuous_block")
        if contains_suspicious:
            reasons.append("suspicious_value_text_block")
        if gid in strict_route_by_group and _norm(strict_route_by_group.get(gid)) == "blocked_or_review_required":
            reasons.append("strict_blocked_group")

        if len(reasons) == 0:
            unit_rule_pass = (not unit_unknown) or (unit_unknown and semantic_unit != "")
            if not unit_rule_pass:
                reasons.append("unresolved_monetary_unit_block")

        if len(reasons) == 0:
            marker_gate = is_marker_only and years_continuous and all_numeric and has_values
            page1_gate = is_page1_summary and years_continuous and all_numeric and has_values
            fallback_low_gate = (_norm(r.get("review_priority", "")).upper() == "LOW") and years_continuous and all_numeric and has_values
            relaxed_gate = marker_gate or page1_gate or fallback_low_gate
            if relaxed_gate:
                route = "relaxed_auto_accept_candidate_preview"
                if marker_gate:
                    reasons.append("marker_only_clean_pass")
                elif page1_gate:
                    reasons.append("page1_summary_clean_pass")
                else:
                    reasons.append("low_clean_numeric_pass")
            else:
                reasons.append("relaxed_gate_not_matched")

        if route != "relaxed_auto_accept_candidate_preview":
            route = "relaxed_review_required"

        route_by_group[gid] = route
        rec = r.to_dict()
        rec["strict_route_bucket"] = _norm(strict_route_by_group.get(gid, "unknown"))
        rec["relaxed_route_bucket"] = route
        rec["relaxed_route_reason"] = ",".join(reasons)
        rec["semantic_unit_for_metric"] = semantic_unit
        rec["unit_unknown_resolved_by_semantics"] = bool(unit_unknown and semantic_unit != "")
        rec["all_year_values_numeric_like"] = all_numeric
        rec["relaxed_gate_pass"] = bool(relaxed_gate)
        routing_rows.append(rec)

    routing_df = pd.DataFrame(routing_rows).fillna("")

    candidate_rows: List[Dict[str, Any]] = []
    for _, r in gmap.iterrows():
        gid = _norm(r.get("group_id", ""))
        cid = _norm(r.get("candidate_id", ""))
        route = route_by_group.get(gid, "relaxed_review_required")
        rec = {
            "group_id": gid,
            "candidate_id": cid,
            "PDF文件名": _norm(r.get("PDF文件名", "")),
            "标准指标": _norm(r.get("标准指标", "")),
            "年份": _to_int(r.get("年份", 0)),
            "value_raw": _norm(r.get("数值", "")),
            "strict_route_bucket": _norm(strict_route_by_group.get(gid, "unknown")),
            "relaxed_route_bucket": route,
            "key": f"{_norm(r.get('PDF文件名',''))}|{_norm(r.get('标准指标',''))}|{_to_int(r.get('年份',0))}",
        }
        candidate_rows.append(rec)
    cdf = pd.DataFrame(candidate_rows).fillna("")

    auto_df = cdf[cdf["relaxed_route_bucket"] == "relaxed_auto_accept_candidate_preview"].copy()
    review_df = cdf[cdf["relaxed_route_bucket"] != "relaxed_auto_accept_candidate_preview"].copy()

    # Safety exclusion: keep reviewed/corrected and missing intake outside relaxed auto-accept pool.
    auto_df = auto_df[~auto_df["candidate_id"].map(_norm).isin(reviewed_candidate_ids)].copy()
    auto_df = auto_df[~auto_df["candidate_id"].map(_norm).isin(missing_candidate_ids_nonempty)].copy()

    # Recompute review pool after exclusion.
    auto_ids = set(auto_df["candidate_id"].map(_norm).tolist())
    review_df = cdf[~cdf["candidate_id"].map(_norm).isin(auto_ids)].copy()

    # Duplicate and conflict audits in relaxed auto-accept
    dup_df = (
        auto_df.groupby("key", dropna=False).size().reset_index(name="count")
        if not auto_df.empty
        else pd.DataFrame(columns=["key", "count"])
    )
    dup_df = dup_df[dup_df["count"] > 1].copy()

    conflict_rows: List[Dict[str, Any]] = []
    if not auto_df.empty:
        for k, g in auto_df.groupby("key", dropna=False):
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
    conflict_df = pd.DataFrame(conflict_rows)

    # Group-level risky to auto count
    relaxed_auto_groups = set(auto_df["group_id"].map(_norm).tolist()) if not auto_df.empty else set()
    risky_groups_to_auto = sorted([g for g in relaxed_auto_groups if g in risky_groups])

    # reviewed/corrected candidates routed to auto accept count
    reviewed_to_auto_ids = sorted([x for x in auto_ids if x in reviewed_candidate_ids and x != ""])
    missing_to_auto_ids = sorted([x for x in auto_ids if x in missing_candidate_ids_nonempty and x != ""])

    strict_total_candidates = int(len(cdf))
    relaxed_auto_accept_group_count = int(len(relaxed_auto_groups))
    relaxed_auto_accept_candidate_count = int(len(auto_df))
    relaxed_review_required_candidate_count = int(len(review_df))
    relaxed_review_reduction_rate = float(relaxed_auto_accept_candidate_count / strict_total_candidates) if strict_total_candidates > 0 else 0.0
    review_reduction_improvement = relaxed_review_reduction_rate - strict_review_reduction_rate

    strict_vs_relaxed = pd.DataFrame(
        [
            {
                "strict_auto_accept_group_count": strict_auto_accept_group_count,
                "relaxed_auto_accept_group_count": relaxed_auto_accept_group_count,
                "strict_auto_accept_candidate_count": strict_auto_accept_candidate_count,
                "relaxed_auto_accept_candidate_count": relaxed_auto_accept_candidate_count,
                "strict_review_reduction_rate": strict_review_reduction_rate,
                "relaxed_review_reduction_rate": relaxed_review_reduction_rate,
                "review_reduction_rate_improvement": review_reduction_improvement,
                "total_policy_candidates": strict_total_candidates,
                "relaxed_review_required_candidate_count": relaxed_review_required_candidate_count,
            }
        ]
    )

    safety_audit = pd.DataFrame(
        [
            {
                "corrected_rejected_needs_groups_routed_to_relaxed_auto_accept_count": int(len(risky_groups_to_auto)),
                "missing_candidates_routed_to_relaxed_auto_accept_count": int(len(missing_to_auto_ids)),
                "reviewed_or_corrected_candidates_routed_to_relaxed_auto_accept_count": int(len(reviewed_to_auto_ids)),
                "relaxed_auto_accept_duplicate_key_count": int(len(dup_df)),
                "relaxed_auto_accept_value_conflict_count": int(len(conflict_df)),
            }
        ]
    )

    policy_rules = {
        "stage": "EVAL-306W",
        "mode": "relaxed_auto_accept_policy_simulation",
        "allow_auto_accept_if": [
            "unit_unknown resolved by deterministic metric semantics (eps/pe/pb/ev_ebitda/roe/gross_margin)",
            "marker-only clean group: no missing_year, no suspicious text, years continuous, numeric values",
            "page1 summary clean group: no risk flags, years continuous, numeric values",
        ],
        "always_block_or_review_if": [
            "human corrected/rejected/needs_more_info group",
            "zero_candidate_rescued",
            "alias_recovered",
            "multi_panel_source",
            "missing_year",
            "years_not_continuous",
            "suspicious value text",
            "duplicate key or value conflict",
            "unresolved monetary unit",
            "missing candidate intake",
        ],
        "no_safe_to_apply": True,
        "no_approve_for_real_apply": True,
    }

    _write_excel(
        OUT_GROUP_ROUTING,
        {
            "relaxed_group_routing": routing_df,
            "relaxed_route_distribution": routing_df.groupby("relaxed_route_bucket", dropna=False).size().reset_index(name="group_count"),
        },
    )
    _write_excel(OUT_AUTO_ACCEPT, {"relaxed_auto_accept_candidate_preview": auto_df})
    _write_excel(OUT_REVIEW_REQUIRED, {"relaxed_review_required": review_df})
    _write_excel(OUT_COMPARE, {"strict_vs_relaxed_comparison": strict_vs_relaxed})
    _write_excel(
        OUT_SAFETY,
        {
            "relaxed_policy_safety_audit": safety_audit,
            "risky_groups_routed_to_auto": pd.DataFrame({"group_id": risky_groups_to_auto}) if risky_groups_to_auto else pd.DataFrame([{"note": "none"}]),
            "reviewed_overlap_with_auto": pd.DataFrame({"candidate_id": reviewed_to_auto_ids}) if reviewed_to_auto_ids else pd.DataFrame([{"note": "none"}]),
            "missing_overlap_with_auto": pd.DataFrame({"candidate_id": missing_to_auto_ids}) if missing_to_auto_ids else pd.DataFrame([{"note": "none"}]),
            "duplicate_key_audit": dup_df if not dup_df.empty else pd.DataFrame([{"note": "duplicate_key_count_0"}]),
            "value_conflict_audit": conflict_df if not conflict_df.empty else pd.DataFrame([{"note": "value_conflict_count_0"}]),
        },
    )
    _write_json(OUT_POLICY, policy_rules)
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

    forbidden_fields_generated = sorted(
        [
            c
            for c in set(routing_df.columns).union(set(cdf.columns)).union(set(auto_df.columns)).union(set(review_df.columns))
            if c in FORBIDDEN_FIELDS
        ]
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
        "stage": "EVAL-306W",
        "mode": "relaxed_auto_accept_policy_simulation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "strict_auto_accept_group_count": strict_auto_accept_group_count,
        "strict_auto_accept_candidate_count": strict_auto_accept_candidate_count,
        "strict_review_reduction_rate": strict_review_reduction_rate,
        "relaxed_auto_accept_group_count": relaxed_auto_accept_group_count,
        "relaxed_auto_accept_candidate_count": relaxed_auto_accept_candidate_count,
        "relaxed_review_reduction_rate": relaxed_review_reduction_rate,
        "review_reduction_rate_improvement": review_reduction_improvement,
        "corrected_rejected_needs_more_info_reviewed_groups_routed_to_relaxed_auto_accept_count": int(len(risky_groups_to_auto)),
        "missing_candidates_routed_to_relaxed_auto_accept_count": int(len(missing_to_auto_ids)),
        "reviewed_corrected_candidates_routed_to_relaxed_auto_accept_count": int(len(reviewed_to_auto_ids)),
        "relaxed_auto_accept_duplicate_key_count": int(len(dup_df)),
        "relaxed_auto_accept_value_conflict_count": int(len(conflict_df)),
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
        "# 306W Relaxed Auto-Accept Policy Simulation",
        "",
        "## Strict vs Relaxed",
        f"- strict_auto_accept_group_count: {strict_auto_accept_group_count}",
        f"- relaxed_auto_accept_group_count: {relaxed_auto_accept_group_count}",
        f"- strict_auto_accept_candidate_count: {strict_auto_accept_candidate_count}",
        f"- relaxed_auto_accept_candidate_count: {relaxed_auto_accept_candidate_count}",
        f"- strict_review_reduction_rate: {strict_review_reduction_rate:.6f}",
        f"- relaxed_review_reduction_rate: {relaxed_review_reduction_rate:.6f}",
        f"- review_reduction_rate_improvement: {review_reduction_improvement:.6f}",
        "",
        "## Safety Assertions",
        f"- corrected/rejected/needs_more_info reviewed groups routed to relaxed auto_accept: {summary['corrected_rejected_needs_more_info_reviewed_groups_routed_to_relaxed_auto_accept_count']}",
        f"- missing candidates routed to relaxed auto_accept: {summary['missing_candidates_routed_to_relaxed_auto_accept_count']}",
        f"- reviewed/corrected candidates routed to relaxed auto_accept: {summary['reviewed_corrected_candidates_routed_to_relaxed_auto_accept_count']}",
        f"- relaxed auto_accept duplicate_key_count: {summary['relaxed_auto_accept_duplicate_key_count']}",
        f"- relaxed auto_accept value_conflict_count: {summary['relaxed_auto_accept_value_conflict_count']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        "",
        "## Guard",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306w_summary_json: {OUT_SUMMARY}")
    print(f"eval_306w_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
