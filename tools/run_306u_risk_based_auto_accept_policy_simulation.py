from __future__ import annotations

import hashlib
import json
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
OUT_DIR = BASE_DIR / "output" / "eval_306u_risk_based_auto_accept_policy_simulation"

IN_GTABLE = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"
IN_GMAP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_group_to_candidate_manifest.xlsx"
IN_QPOOL = BASE_DIR / "output" / "eval_306q_post_review_candidate_package_validation" / "306q_reviewed_candidate_pool.xlsx"
IN_SPROJ = BASE_DIR / "output" / "eval_306s_reviewed_projection_unit_normalization_gate" / "306s_unit_normalized_projection.xlsx"
IN_TVALID = BASE_DIR / "output" / "eval_306t_missing_candidate_intake_validation" / "306t_valid_missing_candidate_intake.xlsx"
IN_TCOMBINED = BASE_DIR / "output" / "eval_306t_missing_candidate_intake_validation" / "306t_combined_reviewed_plus_missing_preview.xlsx"

OUT_SUMMARY = OUT_DIR / "306u_summary.json"
OUT_REPORT = OUT_DIR / "306u_report.md"
OUT_GROUP_ROUTING = OUT_DIR / "306u_group_risk_routing.xlsx"
OUT_AUTO = OUT_DIR / "306u_auto_accept_candidate_preview.xlsx"
OUT_SAMPLE = OUT_DIR / "306u_sample_review_required.xlsx"
OUT_HUMAN = OUT_DIR / "306u_human_review_required.xlsx"
OUT_BLOCKED = OUT_DIR / "306u_blocked_or_review_required.xlsx"
OUT_MANUAL = OUT_DIR / "306u_manual_reviewed_preview.xlsx"
OUT_MISSING = OUT_DIR / "306u_missing_candidate_preview.xlsx"
OUT_WORKLOAD = OUT_DIR / "306u_review_workload_estimate.xlsx"
OUT_POLICY = OUT_DIR / "306u_policy_rules.json"
OUT_NO_APPLY = OUT_DIR / "306u_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}


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
    s = _norm(v).lower()
    return s in {"true", "1", "yes"}


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


def _group_clean_gate_pass(row: pd.Series) -> Tuple[bool, List[str]]:
    fail: List[str] = []
    if _to_bool(row.get("missing_year", False)):
        fail.append("missing_year_true")
    if _to_bool(row.get("unit_unknown", False)):
        fail.append("unit_unknown_warning")
    if _to_bool(row.get("zero_candidate_rescued", False)):
        fail.append("zero_candidate_rescued_true")
    if _to_bool(row.get("alias_recovered", False)):
        fail.append("alias_recovered_true")
    if _to_bool(row.get("multi_panel_source", False)):
        fail.append("multi_panel_source_true")
    if _to_bool(row.get("contains_chinese_value", False)) or _to_bool(row.get("contains_alpha_num_value", False)) or _to_bool(row.get("contains_fragmented_value", False)) or _to_bool(row.get("contains_inconsistent_percent", False)) or _to_bool(row.get("contains_prose_value", False)):
        fail.append("suspicious_value_text_detected")
    if not _to_bool(row.get("years_continuous", True)):
        fail.append("years_not_continuous")
    return len(fail) == 0, fail


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_GTABLE, IN_GMAP, IN_QPOOL, IN_SPROJ, IN_TVALID, IN_TCOMBINED]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306U",
                "mode": "risk_based_auto_accept_policy_simulation",
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

    gtable = _load_first_sheet(IN_GTABLE, "grouped_review_table")
    gmap = _load_first_sheet(IN_GMAP, "group_to_candidate_manifest")
    qpool = _drop_note_rows(_load_first_sheet(IN_QPOOL, "reviewed_candidate_pool"))
    sproj = _drop_note_rows(_load_first_sheet(IN_SPROJ, "unit_normalized_projection"))
    tvalid = _drop_note_rows(_load_first_sheet(IN_TVALID, "valid_missing_candidate_intake"))
    tcombined = _load_first_sheet(IN_TCOMBINED, "combined_reviewed_plus_missing_preview")

    gtable["group_id"] = gtable["group_id"].map(_norm)
    gmap["group_id"] = gmap["group_id"].map(_norm)
    gmap["candidate_id"] = gmap["candidate_id"].map(_norm)
    gmap["年份"] = gmap["年份"].map(_to_int)
    gmap["数值"] = gmap["数值"].map(_norm)

    reviewed_candidate_ids = set(sproj["candidate_id"].map(_norm).tolist()) if "candidate_id" in sproj.columns else set()

    # Group-level routing
    routing_rows: List[Dict[str, Any]] = []
    route_by_group: Dict[str, str] = {}
    block_reason_by_group: Dict[str, str] = {}

    for _, r in gtable.iterrows():
        gid = _norm(r.get("group_id", ""))
        prio = _norm(r.get("review_priority", "")).upper()
        gate_pass, gate_fail = _group_clean_gate_pass(r)

        route = "blocked_or_review_required"
        reason = ""
        if prio == "HIGH":
            route = "human_review_required"
            reason = "priority_high"
        elif prio == "MEDIUM":
            route = "sample_review_required"
            reason = "priority_medium"
        elif prio == "LOW":
            if gate_pass:
                route = "auto_accept_candidate_preview"
                reason = "low_clean_gate_pass"
            else:
                route = "blocked_or_review_required"
                reason = "low_clean_gate_fail:" + ",".join(gate_fail)
        else:
            route = "blocked_or_review_required"
            reason = "unknown_priority"

        route_by_group[gid] = route
        block_reason_by_group[gid] = reason
        rec = r.to_dict()
        rec["route_bucket"] = route
        rec["route_reason"] = reason
        rec["low_clean_gate_pass"] = bool(gate_pass)
        rec["low_clean_gate_fail_reasons"] = ",".join(gate_fail)
        routing_rows.append(rec)

    routing_df = pd.DataFrame(routing_rows).fillna("")

    # Candidate-level pools based on group route (excluding manually reviewed candidates from all auto/sample/human/blocked pools)
    candidate_rows: List[Dict[str, Any]] = []
    for _, r in gmap.iterrows():
        gid = _norm(r.get("group_id", ""))
        cid = _norm(r.get("candidate_id", ""))
        if cid in reviewed_candidate_ids:
            continue
        route = route_by_group.get(gid, "blocked_or_review_required")
        candidate_rows.append(
            {
                "group_id": gid,
                "candidate_id": cid,
                "row_uid": _norm(r.get("row_uid", "")),
                "PDF文件名": _norm(r.get("PDF文件名", "")),
                "标准指标": _norm(r.get("标准指标", "")),
                "年份": _to_int(r.get("年份", 0)),
                "value_raw": _norm(r.get("数值", "")),
                "route_bucket": route,
                "route_reason": block_reason_by_group.get(gid, ""),
            }
        )
    cand_route_df = pd.DataFrame(candidate_rows).fillna("")

    auto_df = cand_route_df[cand_route_df["route_bucket"] == "auto_accept_candidate_preview"].copy()
    sample_df = cand_route_df[cand_route_df["route_bucket"] == "sample_review_required"].copy()
    human_df = cand_route_df[cand_route_df["route_bucket"] == "human_review_required"].copy()
    blocked_df = cand_route_df[cand_route_df["route_bucket"] == "blocked_or_review_required"].copy()

    # duplicate/conflict for auto-accept preview
    if not auto_df.empty:
        auto_df["key"] = auto_df["PDF文件名"].map(_norm) + "|" + auto_df["标准指标"].map(_norm) + "|" + auto_df["年份"].map(_to_int).astype(str)
        dup_auto = auto_df.groupby("key", dropna=False).size().reset_index(name="count")
        dup_auto = dup_auto[dup_auto["count"] > 1].copy()

        conflict_rows: List[Dict[str, Any]] = []
        for k, g in auto_df.groupby("key", dropna=False):
            vals = sorted({v for v in g["value_raw"].map(_norm).tolist() if v != ""})
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
        conflict_auto = pd.DataFrame(conflict_rows)

        # If duplicate/conflict exists, move those keys to blocked
        bad_keys = set(dup_auto["key"].tolist()) if not dup_auto.empty else set()
        bad_keys.update(set(conflict_auto["key"].tolist()) if not conflict_auto.empty else set())
        if bad_keys:
            move_rows = auto_df[auto_df["key"].isin(bad_keys)].copy()
            move_rows["route_bucket"] = "blocked_or_review_required"
            move_rows["route_reason"] = move_rows["route_reason"].map(_norm) + ";auto_accept_dup_or_conflict"
            blocked_df = pd.concat([blocked_df, move_rows], ignore_index=True)
            auto_df = auto_df[~auto_df["key"].isin(bad_keys)].copy()
    else:
        dup_auto = pd.DataFrame()
        conflict_auto = pd.DataFrame()

    # Recompute duplicate/conflict after move to ensure required assertions
    if not auto_df.empty:
        auto_df["key"] = auto_df["PDF文件名"].map(_norm) + "|" + auto_df["标准指标"].map(_norm) + "|" + auto_df["年份"].map(_to_int).astype(str)
        dup_auto_final = auto_df.groupby("key", dropna=False).size().reset_index(name="count")
        dup_auto_final = dup_auto_final[dup_auto_final["count"] > 1].copy()
        conflict_rows_final: List[Dict[str, Any]] = []
        for k, g in auto_df.groupby("key", dropna=False):
            vals = sorted({v for v in g["value_raw"].map(_norm).tolist() if v != ""})
            if len(vals) > 1:
                one = g.iloc[0]
                conflict_rows_final.append(
                    {
                        "key": k,
                        "PDF文件名": _norm(one.get("PDF文件名", "")),
                        "标准指标": _norm(one.get("标准指标", "")),
                        "年份": _to_int(one.get("年份", 0)),
                        "distinct_values": " | ".join(vals),
                        "row_count": int(len(g)),
                    }
                )
        conflict_auto_final = pd.DataFrame(conflict_rows_final)
    else:
        dup_auto_final = pd.DataFrame()
        conflict_auto_final = pd.DataFrame()

    # Separate pools explicitly
    manual_reviewed_preview = sproj.copy()
    missing_candidate_preview = tvalid.copy()

    # enforce missing not in auto_accept and reviewed separate
    auto_ids = set(auto_df["candidate_id"].map(_norm).tolist()) if not auto_df.empty else set()
    manual_ids = set(manual_reviewed_preview["candidate_id"].map(_norm).tolist()) if "candidate_id" in manual_reviewed_preview.columns else set()
    missing_ids = set(missing_candidate_preview["candidate_id"].map(_norm).tolist()) if "candidate_id" in missing_candidate_preview.columns else set()
    missing_ids_nonempty = {x for x in missing_ids if x != ""}

    reviewed_overlap_with_auto = sorted([x for x in auto_ids if x in manual_ids and x != ""])
    missing_overlap_with_auto = sorted([x for x in auto_ids if x in missing_ids_nonempty and x != ""])

    # workload estimation
    workload = pd.DataFrame(
        [
            {"bucket": "auto_accept_candidate_preview", "candidate_count": int(len(auto_df)), "group_count": int(auto_df["group_id"].nunique()) if not auto_df.empty else 0},
            {"bucket": "sample_review_required", "candidate_count": int(len(sample_df)), "group_count": int(sample_df["group_id"].nunique()) if not sample_df.empty else 0},
            {"bucket": "human_review_required", "candidate_count": int(len(human_df)), "group_count": int(human_df["group_id"].nunique()) if not human_df.empty else 0},
            {"bucket": "blocked_or_review_required", "candidate_count": int(len(blocked_df)), "group_count": int(blocked_df["group_id"].nunique()) if not blocked_df.empty else 0},
            {"bucket": "manual_reviewed_preview", "candidate_count": int(len(manual_reviewed_preview)), "group_count": int(manual_reviewed_preview["group_id"].nunique()) if "group_id" in manual_reviewed_preview.columns else 0},
            {"bucket": "missing_candidate_preview", "candidate_count": int(len(missing_candidate_preview)), "group_count": int(missing_candidate_preview["group_id"].nunique()) if "group_id" in missing_candidate_preview.columns else 0},
        ]
    )

    # output write helpers
    def _or_note(df: pd.DataFrame, note: str) -> pd.DataFrame:
        return df if not df.empty else pd.DataFrame([{"note": note}])

    _write_excel(
        OUT_GROUP_ROUTING,
        {
            "group_risk_routing": routing_df,
            "route_distribution": routing_df.groupby("route_bucket", dropna=False).size().reset_index(name="group_count"),
        },
    )
    _write_excel(OUT_AUTO, {"auto_accept_candidate_preview": _or_note(auto_df, "no_auto_accept_rows")})
    _write_excel(OUT_SAMPLE, {"sample_review_required": _or_note(sample_df, "no_sample_review_rows")})
    _write_excel(OUT_HUMAN, {"human_review_required": _or_note(human_df, "no_human_review_rows")})
    _write_excel(OUT_BLOCKED, {"blocked_or_review_required": _or_note(blocked_df, "no_blocked_rows")})
    _write_excel(OUT_MANUAL, {"manual_reviewed_preview": _or_note(manual_reviewed_preview, "no_manual_reviewed_rows")})
    _write_excel(OUT_MISSING, {"missing_candidate_preview": _or_note(missing_candidate_preview, "no_missing_preview_rows")})
    _write_excel(OUT_WORKLOAD, {"review_workload_estimate": workload})

    _write_json(
        OUT_POLICY,
        {
            "policy_name": "306u_risk_based_auto_accept_policy_simulation",
            "low_clean_gate": {
                "missing_year_must_be_false": True,
                "unit_unknown_must_be_false": True,
                "zero_candidate_rescued_must_be_false": True,
                "alias_recovered_must_be_false": True,
                "multi_panel_source_must_be_false": True,
                "suspicious_value_text_must_be_false": True,
                "years_continuous_must_be_true": True,
            },
            "priority_routing": {
                "HIGH": "human_review_required",
                "MEDIUM": "sample_review_required",
                "LOW_clean_pass": "auto_accept_candidate_preview",
                "LOW_clean_fail": "blocked_or_review_required",
            },
            "separation_rules": {
                "manual_reviewed_preview_separate_from_auto_accept": True,
                "missing_candidate_preview_separate_from_auto_accept": True,
            },
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

    # assertions
    forbidden_fields_generated = sorted(
        [
            c
            for c in set(auto_df.columns)
            .union(set(sample_df.columns))
            .union(set(human_df.columns))
            .union(set(blocked_df.columns))
            .union(set(manual_reviewed_preview.columns))
            .union(set(missing_candidate_preview.columns))
            if c in FORBIDDEN_FIELDS
        ]
    )
    auto_has_high_groups = False
    if not auto_df.empty:
        high_groups = set(routing_df[routing_df["review_priority"].map(_norm).str.upper() == "HIGH"]["group_id"].map(_norm).tolist())
        auto_has_high_groups = auto_df["group_id"].map(_norm).isin(high_groups).any()

    duplicate_key_count = int(len(dup_auto_final) if not dup_auto_final.empty else 0)
    value_conflict_count = int(len(conflict_auto_final) if not conflict_auto_final.empty else 0)

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-306U",
        "mode": "risk_based_auto_accept_policy_simulation",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "group_count_total": int(len(routing_df)),
        "auto_accept_candidate_count": int(len(auto_df)),
        "sample_review_candidate_count": int(len(sample_df)),
        "human_review_candidate_count": int(len(human_df)),
        "blocked_review_candidate_count": int(len(blocked_df)),
        "manual_reviewed_candidate_count": int(len(manual_reviewed_preview)),
        "missing_candidate_preview_count": int(len(missing_candidate_preview)),
        "auto_accept_contains_high_risk_group": bool(auto_has_high_groups),
        "missing_candidates_entered_auto_accept": bool(len(missing_overlap_with_auto) > 0),
        "reviewed_candidates_entered_auto_accept": bool(len(reviewed_overlap_with_auto) > 0),
        "duplicate_key_count_auto_accept": duplicate_key_count,
        "value_conflict_count_auto_accept": value_conflict_count,
        "forbidden_fields_generated": forbidden_fields_generated,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "source_tcombined_rows": int(len(tcombined)),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306U Risk-Based Auto-Accept Policy Simulation",
        "",
        "## Scope",
        "- Simulated risk-based routing on 306L risk groups and candidate mapping.",
        "- Kept manually reviewed (306S) and missing (306T) previews separate from auto-accept.",
        "- No apply and no production modifications.",
        "",
        "## Routing Counts",
        f"- auto_accept_candidate_count: {summary['auto_accept_candidate_count']}",
        f"- sample_review_candidate_count: {summary['sample_review_candidate_count']}",
        f"- human_review_candidate_count: {summary['human_review_candidate_count']}",
        f"- blocked_review_candidate_count: {summary['blocked_review_candidate_count']}",
        f"- manual_reviewed_candidate_count: {summary['manual_reviewed_candidate_count']}",
        f"- missing_candidate_preview_count: {summary['missing_candidate_preview_count']}",
        "",
        "## Assertions",
        f"- auto_accept_contains_high_risk_group: {summary['auto_accept_contains_high_risk_group']}",
        f"- missing_candidates_entered_auto_accept: {summary['missing_candidates_entered_auto_accept']}",
        f"- reviewed_candidates_entered_auto_accept: {summary['reviewed_candidates_entered_auto_accept']}",
        f"- duplicate_key_count_auto_accept: {summary['duplicate_key_count_auto_accept']}",
        f"- value_conflict_count_auto_accept: {summary['value_conflict_count_auto_accept']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        "",
        "## Delivery Guard",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306u_summary_json: {OUT_SUMMARY}")
    print(f"eval_306u_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

