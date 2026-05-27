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
OUT_DIR = BASE_DIR / "output" / "eval_306v_risk_policy_calibration"

IN_UGROUP = BASE_DIR / "output" / "eval_306u_risk_based_auto_accept_policy_simulation" / "306u_group_risk_routing.xlsx"
IN_UAUTO = BASE_DIR / "output" / "eval_306u_risk_based_auto_accept_policy_simulation" / "306u_auto_accept_candidate_preview.xlsx"
IN_USAMPLE = BASE_DIR / "output" / "eval_306u_risk_based_auto_accept_policy_simulation" / "306u_sample_review_required.xlsx"
IN_UHUMAN = BASE_DIR / "output" / "eval_306u_risk_based_auto_accept_policy_simulation" / "306u_human_review_required.xlsx"
IN_UBLOCK = BASE_DIR / "output" / "eval_306u_risk_based_auto_accept_policy_simulation" / "306u_blocked_or_review_required.xlsx"
IN_UWORK = BASE_DIR / "output" / "eval_306u_risk_based_auto_accept_policy_simulation" / "306u_review_workload_estimate.xlsx"
IN_OCAND = BASE_DIR / "output" / "eval_306o_expand_grouped_review_to_candidate_results" / "306o_candidate_review_results.xlsx"
IN_PCORR = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_corrected_reviewed_candidates.xlsx"
IN_PREJ = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_rejected_candidates.xlsx"
IN_PNEED = BASE_DIR / "output" / "eval_306p_post_review_candidate_decision_gate" / "306p_needs_more_info_candidates.xlsx"
IN_QPOOL = BASE_DIR / "output" / "eval_306q_post_review_candidate_package_validation" / "306q_reviewed_candidate_pool.xlsx"
IN_SPROJ = BASE_DIR / "output" / "eval_306s_reviewed_projection_unit_normalization_gate" / "306s_unit_normalized_projection.xlsx"
IN_TVALID = BASE_DIR / "output" / "eval_306t_missing_candidate_intake_validation" / "306t_valid_missing_candidate_intake.xlsx"

OUT_SUMMARY = OUT_DIR / "306v_summary.json"
OUT_REPORT = OUT_DIR / "306v_report.md"
OUT_CALIB = OUT_DIR / "306v_policy_calibration_by_review_result.xlsx"
OUT_SAFETY = OUT_DIR / "306v_auto_accept_safety_audit.xlsx"
OUT_REDUCTION = OUT_DIR / "306v_review_reduction_estimate.xlsx"
OUT_STRICTNESS = OUT_DIR / "306v_policy_too_strict_or_too_loose_audit.xlsx"
OUT_RECOMMEND = OUT_DIR / "306v_recommended_policy_adjustments.md"
OUT_NO_APPLY = OUT_DIR / "306v_no_apply_proof.json"

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

    required = [
        IN_UGROUP,
        IN_UAUTO,
        IN_USAMPLE,
        IN_UHUMAN,
        IN_UBLOCK,
        IN_UWORK,
        IN_OCAND,
        IN_PCORR,
        IN_PREJ,
        IN_PNEED,
        IN_QPOOL,
        IN_SPROJ,
        IN_TVALID,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306V",
                "mode": "risk_policy_calibration",
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

    ugroup = _load_first_sheet(IN_UGROUP, "group_risk_routing")
    uauto = _drop_note_rows(_load_first_sheet(IN_UAUTO, "auto_accept_candidate_preview"))
    usample = _drop_note_rows(_load_first_sheet(IN_USAMPLE, "sample_review_required"))
    uhuman = _drop_note_rows(_load_first_sheet(IN_UHUMAN, "human_review_required"))
    ublock = _drop_note_rows(_load_first_sheet(IN_UBLOCK, "blocked_or_review_required"))
    uwork = _load_first_sheet(IN_UWORK, "review_workload_estimate")
    ocand = _drop_note_rows(_load_first_sheet(IN_OCAND, "candidate_review_results"))
    pcorr = _drop_note_rows(_load_first_sheet(IN_PCORR, "corrected_reviewed_candidates"))
    prej = _drop_note_rows(_load_first_sheet(IN_PREJ, "rejected_candidates"))
    pneed = _drop_note_rows(_load_first_sheet(IN_PNEED, "needs_more_info_candidates"))
    qpool = _drop_note_rows(_load_first_sheet(IN_QPOOL, "reviewed_candidate_pool"))
    sproj = _drop_note_rows(_load_first_sheet(IN_SPROJ, "unit_normalized_projection"))
    tvalid = _drop_note_rows(_load_first_sheet(IN_TVALID, "valid_missing_candidate_intake"))

    # Build group->route mapping from 306U
    route_map = {
        _norm(r["group_id"]): _norm(r["route_bucket"])
        for _, r in ugroup.iterrows()
        if _norm(r.get("group_id", "")) != ""
    }
    prio_map = {
        _norm(r["group_id"]): _norm(r["review_priority"]).upper()
        for _, r in ugroup.iterrows()
        if _norm(r.get("group_id", "")) != ""
    }

    # Real reviewed group labels (from 306O candidate review decisions)
    group_label_map: Dict[str, str] = {}
    for gid, g in ocand.groupby(ocand["group_id"].map(_norm)):
        labels = sorted({ _norm(x).lower() for x in g["decision_candidate"].tolist() if _norm(x) != ""})
        # precedence: corrected > rejected > needs_more_info > approve
        label = "unknown"
        if "correct_value" in labels:
            label = "corrected"
        elif "reject" in labels:
            label = "rejected"
        elif "needs_more_info" in labels:
            label = "needs_more_info"
        elif "approve" in labels:
            label = "approved"
        group_label_map[gid] = label

    calib_rows: List[Dict[str, Any]] = []
    for gid, label in sorted(group_label_map.items()):
        calib_rows.append(
            {
                "group_id": gid,
                "real_review_label": label,
                "simulated_route_bucket": route_map.get(gid, "missing_route"),
                "simulated_review_priority": prio_map.get(gid, "UNKNOWN"),
            }
        )
    calib_df = pd.DataFrame(calib_rows)

    # Safety checks
    risky_labels = {"corrected", "rejected", "needs_more_info"}
    risky_to_auto = calib_df[
        calib_df["real_review_label"].isin(risky_labels)
        & calib_df["simulated_route_bucket"].eq("auto_accept_candidate_preview")
    ].copy()

    approved_groups = calib_df[calib_df["real_review_label"].eq("approved")].copy()
    approved_route_dist = (
        approved_groups.groupby("simulated_route_bucket", dropna=False).size().reset_index(name="group_count")
        if not approved_groups.empty
        else pd.DataFrame([{"simulated_route_bucket": "N/A", "group_count": 0}])
    )

    auto_ids = set(uauto["candidate_id"].map(_norm).tolist()) if "candidate_id" in uauto.columns else set()
    manual_ids = set(sproj["candidate_id"].map(_norm).tolist()) if "candidate_id" in sproj.columns else set()
    missing_ids = set(tvalid["candidate_id"].map(_norm).tolist()) if "candidate_id" in tvalid.columns else set()
    missing_ids_nonempty = {x for x in missing_ids if x != ""}

    reviewed_to_auto = sorted([x for x in auto_ids if x in manual_ids and x != ""])
    missing_to_auto = sorted([x for x in auto_ids if x in missing_ids_nonempty and x != ""])

    # Duplicate/conflict in auto-accept
    if not uauto.empty:
        auto_df = uauto.copy()
        auto_df["key"] = auto_df.get("key", auto_df["PDF文件名"].map(_norm) + "|" + auto_df["标准指标"].map(_norm) + "|" + auto_df["年份"].map(_to_int).astype(str))
        dup_auto = auto_df.groupby("key", dropna=False).size().reset_index(name="count")
        dup_auto = dup_auto[dup_auto["count"] > 1].copy()
        conflict_rows: List[Dict[str, Any]] = []
        for k, g in auto_df.groupby("key", dropna=False):
            vals = sorted({ _norm(v) for v in g["value_raw"].tolist() if _norm(v) != ""})
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
    else:
        dup_auto = pd.DataFrame()
        conflict_auto = pd.DataFrame()

    duplicate_key_count = int(len(dup_auto))
    value_conflict_count = int(len(conflict_auto))

    # Review reduction estimate
    total_candidates_for_policy = int(len(uauto) + len(usample) + len(uhuman) + len(ublock))
    auto_accept_count = int(len(uauto))
    review_required_count = int(len(usample) + len(uhuman) + len(ublock))
    reduction_rate = float(auto_accept_count / total_candidates_for_policy) if total_candidates_for_policy > 0 else 0.0

    # Strictness / looseness heuristic
    too_loose = len(risky_to_auto) > 0 or len(missing_to_auto) > 0 or len(reviewed_to_auto) > 0
    too_strict = (not too_loose) and reduction_rate < 0.05
    strictness_label = "balanced"
    if too_loose:
        strictness_label = "too_loose"
    elif too_strict:
        strictness_label = "too_strict"

    strictness_df = pd.DataFrame(
        [
            {
                "policy_label": strictness_label,
                "auto_accept_rate": reduction_rate,
                "risky_group_routed_to_auto_accept_count": int(len(risky_to_auto)),
                "missing_routed_to_auto_accept_count": int(len(missing_to_auto)),
                "reviewed_routed_to_auto_accept_count": int(len(reviewed_to_auto)),
                "notes": (
                    "Risk leakage detected" if too_loose else ("Very conservative but safe" if too_strict else "No leakage and moderate reduction")
                ),
            }
        ]
    )

    # Suggested adjustments
    adjustments = []
    if too_strict:
        adjustments.extend(
            [
                "Allow LOW groups with unit_unknown only for valuation metrics (PE/PB/EV_EBITDA) when values are clean numeric.",
                "Allow LOW groups with minor year sparsity under explicit manual spot-check sampling.",
                "Keep high/multi-panel/alias/zero-candidate-rescued groups out of auto-accept.",
            ]
        )
    elif too_loose:
        adjustments.extend(
            [
                "Tighten auto-accept by blocking any group with corrected/rejected/needs_more_info historical evidence.",
                "Require unit normalization without warnings before auto-accept.",
                "Add key-level duplicate/conflict pre-check before auto-accept routing.",
            ]
        )
    else:
        adjustments.extend(
            [
                "Maintain current hard safety constraints for HIGH and blocked groups.",
                "Gradually increase LOW-group sampling for offline quality drift monitoring.",
                "Keep manual-reviewed and missing-candidate pools fully separated from auto-accept.",
            ]
        )

    # Write outputs
    def _or_note(df: pd.DataFrame, note: str) -> pd.DataFrame:
        return df if not df.empty else pd.DataFrame([{"note": note}])

    _write_excel(
        OUT_CALIB,
        {
            "policy_calibration_by_review_result": _or_note(calib_df, "no_calibration_rows"),
            "approved_route_distribution": approved_route_dist,
        },
    )
    _write_excel(
        OUT_SAFETY,
        {
            "risky_groups_routed_to_auto": _or_note(risky_to_auto, "no_risky_groups_routed_to_auto"),
            "reviewed_overlap_with_auto": _or_note(pd.DataFrame({"candidate_id": reviewed_to_auto}), "no_reviewed_overlap_with_auto"),
            "missing_overlap_with_auto": _or_note(pd.DataFrame({"candidate_id": missing_to_auto}), "no_missing_overlap_with_auto"),
            "auto_accept_duplicate_key": _or_note(dup_auto, "auto_accept_duplicate_key_count_0"),
            "auto_accept_value_conflict": _or_note(conflict_auto, "auto_accept_value_conflict_count_0"),
        },
    )
    _write_excel(
        OUT_REDUCTION,
        {
            "review_reduction_estimate": pd.DataFrame(
                [
                    {
                        "total_policy_candidates": total_candidates_for_policy,
                        "auto_accept_candidate_count": auto_accept_count,
                        "review_required_candidate_count": review_required_count,
                        "auto_accept_rate": reduction_rate,
                    }
                ]
            ),
            "workload_reference_306u": uwork,
        },
    )
    _write_excel(OUT_STRICTNESS, {"policy_too_strict_or_too_loose_audit": strictness_df})

    recommend_lines = [
        "# 306V Recommended Policy Adjustments",
        "",
        f"- policy_label: `{strictness_label}`",
        f"- auto_accept_rate: `{reduction_rate:.4f}`",
        "",
        "## Suggested Adjustments",
    ] + [f"- {x}" for x in adjustments]
    OUT_RECOMMEND.write_text("\n".join(recommend_lines) + "\n", encoding="utf-8")

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
            for c in set(calib_df.columns)
            .union(set(risky_to_auto.columns))
            .union(set(uauto.columns))
            .union(set(tvalid.columns))
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
        "stage": "EVAL-306V",
        "mode": "risk_policy_calibration",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "corrected_rejected_needs_groups_routed_to_auto_accept_count": int(len(risky_to_auto)),
        "missing_candidates_routed_to_auto_accept_count": int(len(missing_to_auto)),
        "reviewed_candidates_routed_to_auto_accept_count": int(len(reviewed_to_auto)),
        "auto_accept_duplicate_key_count": duplicate_key_count,
        "auto_accept_value_conflict_count": value_conflict_count,
        "auto_accept_group_count": int(uauto["group_id"].map(_norm).nunique()) if "group_id" in uauto.columns else 0,
        "auto_accept_candidate_count": auto_accept_count,
        "review_reduction_rate": reduction_rate,
        "policy_strictness_label": strictness_label,
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
        "# 306V Risk Policy Calibration",
        "",
        "## Calibration Result",
        f"- corrected/rejected/needs_more_info groups routed to auto_accept: {summary['corrected_rejected_needs_groups_routed_to_auto_accept_count']}",
        f"- missing candidates routed to auto_accept: {summary['missing_candidates_routed_to_auto_accept_count']}",
        f"- reviewed candidates routed to auto_accept: {summary['reviewed_candidates_routed_to_auto_accept_count']}",
        f"- auto_accept_duplicate_key_count: {summary['auto_accept_duplicate_key_count']}",
        f"- auto_accept_value_conflict_count: {summary['auto_accept_value_conflict_count']}",
        "",
        "## Workload Impact",
        f"- auto_accept_group_count: {summary['auto_accept_group_count']}",
        f"- auto_accept_candidate_count: {summary['auto_accept_candidate_count']}",
        f"- review_reduction_rate: {summary['review_reduction_rate']:.4f}",
        f"- policy_strictness_label: {summary['policy_strictness_label']}",
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

    print(f"eval_306v_summary_json: {OUT_SUMMARY}")
    print(f"eval_306v_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

