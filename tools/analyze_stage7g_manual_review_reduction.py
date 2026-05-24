# -*- coding: utf-8 -*-
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
IN_DIR = BASE_DIR / "output" / "stage7f_core_metrics_policy_sandbox"
STAGE7D_DIR = BASE_DIR / "output" / "stage7d_pipeline_sandbox"
OUT_DIR = BASE_DIR / "output" / "stage7g_manual_review_reduction_sandbox"

IN_SUMMARY = IN_DIR / "185_stage7f_policy_apply_summary.json"
IN_MANUAL = IN_DIR / "185_stage7f_manual_review_queue.xlsx"
IN_CLEAN = IN_DIR / "185_stage7f_clean_sandbox_06_preview.xlsx"
IN_EXCLUDED = IN_DIR / "185_stage7f_excluded_conflict_rows.xlsx"
IN_AUDIT = IN_DIR / "185_stage7f_policy_application_audit.xlsx"
IN_CLASSIFIED = STAGE7D_DIR / "183_stage7d_classified_structured_table.xlsx"

OUT_SUMMARY = OUT_DIR / "186_stage7g_manual_review_reduction_summary.json"
OUT_REPORT = OUT_DIR / "186_stage7g_manual_review_reduction_report.md"
OUT_CLASSIFIED = OUT_DIR / "186_stage7g_manual_review_classified.xlsx"
OUT_AUTO = OUT_DIR / "186_stage7g_auto_resolvable_candidates.xlsx"
OUT_REMAIN = OUT_DIR / "186_stage7g_remaining_manual_review.xlsx"
OUT_POLICY = OUT_DIR / "186_stage7g_updated_policy_suggestions.json"
OUT_REDUCED = OUT_DIR / "186_stage7g_reduced_clean_06_preview.xlsx"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

EPS_METRICS = {"EPS", "每股收益"}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_scope_rules"] = _sha256(FORMAL_SCOPE_RULES)
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
    if not txt:
        return {"overall_status": "UNKNOWN"}
    return json.loads(txt)


def _to_float(v: Any) -> float:
    s = _norm(v).replace(",", "")
    try:
        return float(s)
    except Exception:
        return float("nan")


def _extract_metric_section_values(excerpt: str, raw_metric_name: str) -> List[float]:
    tokens = [_norm(t) for t in _norm(excerpt).split("|")]
    if not tokens:
        return []

    metric_idx = -1
    rm = _norm(raw_metric_name)
    for i, t in enumerate(tokens):
        if rm and rm in t:
            metric_idx = i
            break

    if metric_idx < 0:
        return []

    vals: List[float] = []
    for t in tokens[metric_idx + 1 :]:
        c = t.replace(",", "").replace("%", "").strip()
        if not c:
            continue
        try:
            vals.append(float(c))
            continue
        except Exception:
            break
    return vals


def _value_in_section(v: Any, section_vals: List[float]) -> bool:
    fv = _to_float(v)
    if pd.isna(fv):
        return False
    for x in section_vals:
        if abs(fv - x) <= 1e-9:
            return True
    return False


def _conflict_stats(df: pd.DataFrame) -> Dict[str, int]:
    if df.empty:
        return {
            "duplicate_key_count_after_preview": 0,
            "value_mismatch_count_after_preview": 0,
            "unit_conflict_count_after_preview": 0,
            "year_conflict_count_after_preview": 0,
        }

    w = df.copy()
    w["key"] = w["asset_package"].map(_norm) + "||" + w["standard_metric"].map(_norm) + "||" + w["year"].map(_norm)

    duplicate_key_count = int(w["key"].duplicated().sum())
    value_mismatch_count = 0
    unit_conflict_count = 0
    year_conflict_count = 0

    for _, g in w.groupby("key", dropna=False):
        if g["final_value"].map(_norm).nunique() > 1:
            value_mismatch_count += 1
        if g["final_unit"].map(_norm).nunique() > 1:
            unit_conflict_count += 1

    for _, g in w.groupby(["asset_package", "standard_metric"], dropna=False):
        ys = [y for y in g["year"].map(_norm).tolist() if y]
        if len(ys) != len(set(ys)):
            year_conflict_count += 1

    return {
        "duplicate_key_count_after_preview": int(duplicate_key_count),
        "value_mismatch_count_after_preview": int(value_mismatch_count),
        "unit_conflict_count_after_preview": int(unit_conflict_count),
        "year_conflict_count_after_preview": int(year_conflict_count),
    }


def _classify_group_reason(group: pd.DataFrame, aligned_count: int) -> str:
    unit_count = group["final_unit"].map(_norm).nunique()
    st_count = group["statement_type_for_priority"].map(_norm).nunique()
    years = group["year"].map(_norm).tolist()
    low_conf = pd.to_numeric(group["extraction_confidence"], errors="coerce").fillna(0) < 0.7

    if bool(low_conf.any()):
        return "low_confidence_extraction"
    if unit_count > 1:
        return "unit_semantics_uncertain"
    if len(years) != len(set(years)):
        return "year_semantics_uncertain"
    if st_count > 1:
        return "same_metric_multiple_statement_types"
    if aligned_count == 1:
        return "source_priority_missing"

    # Multiple values remain after section alignment: business interpretation is needed.
    return "needs_human_business_judgement"


def _build_reduced_preview(clean_df: pd.DataFrame, auto_selected: pd.DataFrame) -> pd.DataFrame:
    preview_cols = [
        "source_pdf",
        "asset_package",
        "standard_metric",
        "year",
        "final_value",
        "final_unit",
        "statement_type",
        "source_pdf_name",
        "page_number",
        "raw_metric_name",
        "source_text_excerpt",
        "policy_score",
        "policy_action",
        "conflict_category",
    ]

    clean = clean_df.copy()
    for c in preview_cols:
        if c not in clean.columns:
            clean[c] = ""
    clean = clean[preview_cols]

    if auto_selected.empty:
        return clean.copy()

    auto = auto_selected.copy()
    auto["statement_type"] = auto.get("statement_type_for_priority", "").map(_norm)
    auto["policy_score"] = ""
    auto["policy_action"] = "AUTO_RESOLVED_BY_STAGE7G_SECTION_ALIGNMENT"
    auto["conflict_category"] = auto.get("conflict_category", "true_value_conflict")
    for c in preview_cols:
        if c not in auto.columns:
            auto[c] = ""
    auto = auto[preview_cols]

    merged = pd.concat([clean, auto], ignore_index=True)
    merged["_key"] = merged["asset_package"].map(_norm) + "||" + merged["standard_metric"].map(_norm) + "||" + merged["year"].map(_norm)
    merged = merged.sort_values(["_key", "policy_action", "page_number"], kind="mergesort")
    merged = merged.drop_duplicates(subset=["_key"], keep="first").drop(columns=["_key"])
    return merged


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet[:31], index=False)


def main() -> int:
    required = [IN_SUMMARY, IN_MANUAL, IN_CLEAN, IN_EXCLUDED, IN_AUDIT, IN_CLASSIFIED]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    before = _snapshot_guard()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    s7f_summary = json.loads(IN_SUMMARY.read_text(encoding="utf-8"))
    manual = pd.read_excel(IN_MANUAL, sheet_name="manual_review_queue").fillna("")
    clean = pd.read_excel(IN_CLEAN, sheet_name="clean_sandbox_06_preview").fillna("")

    classified_rows: List[Dict[str, Any]] = []
    auto_selected_rows: List[Dict[str, Any]] = []
    remaining_rows: List[Dict[str, Any]] = []

    for key, g in manual.groupby("key", dropna=False):
        g = g.copy()
        g["analysis_key"] = _norm(key)
        g["metric_section_values"] = g.apply(
            lambda r: _extract_metric_section_values(_norm(r.get("source_text_excerpt")), _norm(r.get("raw_metric_name"))),
            axis=1,
        )
        g["value_in_metric_section"] = g.apply(
            lambda r: _value_in_section(r.get("final_value"), r.get("metric_section_values")),
            axis=1,
        )

        aligned_count = int(g["value_in_metric_section"].astype(bool).sum())
        reason = _classify_group_reason(g, aligned_count)

        can_auto = aligned_count == 1
        selected_idx = None
        if can_auto:
            selected_idx = g[g["value_in_metric_section"].astype(bool)].index[0]

        for idx, row in g.iterrows():
            rec = row.to_dict()
            rec["manual_review_reason"] = reason
            rec["auto_resolvable_candidate"] = bool(can_auto and idx == selected_idx)
            rec["group_auto_resolvable"] = bool(can_auto)
            rec["deterministic_policy_rule"] = (
                "source_text_metric_section_alignment" if can_auto else "none"
            )
            rec["recommended_action"] = (
                "AUTO_SELECT_AND_APPEND_TO_SANDBOX_PREVIEW"
                if rec["auto_resolvable_candidate"]
                else "KEEP_IN_MANUAL_REVIEW_QUEUE"
            )
            classified_rows.append(rec)

            if rec["auto_resolvable_candidate"]:
                auto_selected_rows.append(rec)
            else:
                remaining_rows.append(rec)

    classified_df = pd.DataFrame(classified_rows).fillna("")
    auto_df = pd.DataFrame(auto_selected_rows).fillna("")
    remain_df = pd.DataFrame(remaining_rows).fillna("")

    reduced_preview = _build_reduced_preview(clean, auto_df)

    # EPS unit guard: keep EPS out of ratio.
    eps_mask = reduced_preview["standard_metric"].map(_norm).isin(EPS_METRICS)
    bad_eps_ratio_count = int(
        reduced_preview[eps_mask & reduced_preview["final_unit"].map(_norm).isin({"ratio", "%"})].shape[0]
    ) if not reduced_preview.empty else 0
    eps_detected_count = int(eps_mask.sum()) if not reduced_preview.empty else 0

    conflict_after = _conflict_stats(reduced_preview)

    _write_excel(OUT_CLASSIFIED, {"manual_review_classified": classified_df})
    _write_excel(OUT_AUTO, {"auto_resolvable_candidates": auto_df})
    _write_excel(OUT_REMAIN, {"remaining_manual_review": remain_df})
    _write_excel(OUT_REDUCED, {"reduced_clean_06_preview": reduced_preview})

    reason_counts = (
        classified_df["manual_review_reason"].map(_norm).value_counts().to_dict()
        if not classified_df.empty
        else {}
    )

    policy_suggestions = {
        "stage": "stage7g_manual_review_reduction",
        "mode": "sandbox_analysis_only",
        "policy_source_reference": "184_stage7e_resolution_policy_draft.json",
        "new_deterministic_suggestions": [
            {
                "id": "metric_section_alignment",
                "description": "If the key has exactly one candidate value appearing in the numeric section immediately following raw_metric_name in source_text_excerpt, auto-select it.",
                "applies_to": "manual queue true_value_conflict rows",
                "safety": "high",
            },
            {
                "id": "ambiguous_multi_match_keep_manual",
                "description": "If multiple candidates match the metric section (or none match), keep the key in manual review queue.",
                "applies_to": "high-ambiguity conflicts",
                "safety": "high",
            },
            {
                "id": "eps_unit_guard",
                "description": "Keep EPS/每股收益 unit out of ratio in preview outputs.",
                "applies_to": "EPS rows",
                "safety": "high",
            },
        ],
        "manual_review_reason_counts": reason_counts,
        "auto_resolvable_candidate_rows": int(len(auto_df)),
        "remaining_manual_review_rows": int(len(remain_df)),
        "note": "Suggestion only. No formal policy/rule file changed in Stage 7G.",
    }
    OUT_POLICY.write_text(json.dumps(policy_suggestions, ensure_ascii=False, indent=2), encoding="utf-8")

    after = _snapshot_guard()
    production_files_modified = not (
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_scope_rules"] != after["formal_scope_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    input_rows = int(len(manual))
    auto_rows = int(len(auto_df))
    remain_rows = int(len(remain_df))
    reduction_count = auto_rows
    reduction_rate = float(round((reduction_count / input_rows), 6)) if input_rows else 0.0

    summary = {
        "stage": "stage7g_manual_review_reduction",
        "mode": "sandbox_analysis_only",
        "based_on_stage7f_commit": "e11e0eb45c1f496ee293508215d5330829df3fe1",
        "input_manual_review_queue_rows": input_rows,
        "auto_resolvable_candidate_rows": auto_rows,
        "remaining_manual_review_rows": remain_rows,
        "manual_review_reduction_count": int(reduction_count),
        "manual_review_reduction_rate": reduction_rate,
        "clean_06_preview_rows_before": int(len(clean)),
        "reduced_clean_06_preview_rows": int(len(reduced_preview)),
        "duplicate_key_count_after_preview": int(conflict_after["duplicate_key_count_after_preview"]),
        "value_mismatch_count_after_preview": int(conflict_after["value_mismatch_count_after_preview"]),
        "unit_conflict_count_after_preview": int(conflict_after["unit_conflict_count_after_preview"]),
        "year_conflict_count_after_preview": int(conflict_after["year_conflict_count_after_preview"]),
        "eps_detected_count": int(eps_detected_count),
        "bad_eps_ratio_count": int(bad_eps_ratio_count),
        "production_files_modified": bool(production_files_modified),
        "official_02b_modified": bool(official_02b_modified),
        "formal_rules_modified": bool(formal_rules_modified),
        "standardizer_modified": bool(standardizer_modified),
        "release_package_modified": bool(release_package_modified),
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_stage7h_ai_assisted_review_design": False,
    }

    summary["ready_for_stage7h_ai_assisted_review_design"] = bool(
        summary["duplicate_key_count_after_preview"] == 0
        and summary["value_mismatch_count_after_preview"] == 0
        and summary["unit_conflict_count_after_preview"] == 0
        and summary["year_conflict_count_after_preview"] == 0
        and summary["bad_eps_ratio_count"] == 0
        and not summary["production_files_modified"]
        and not summary["official_02b_modified"]
        and not summary["formal_rules_modified"]
        and not summary["standardizer_modified"]
        and not summary["release_package_modified"]
        and summary["check_delivery_state_overall_status"] == "PASS"
    )

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    reason_md = "\n".join([f"- {k}: {v}" for k, v in reason_counts.items()]) if reason_counts else "- (none)"
    report_lines = [
        "# Stage 7G Manual Review Reduction Analysis",
        "",
        "## Scope",
        "- Sandbox analysis only. No real apply.",
        "- No production/official/rules/release changes.",
        "",
        "## Inputs",
        f"- based_on_stage7f_commit: {summary['based_on_stage7f_commit']}",
        f"- input_manual_review_queue_rows: {summary['input_manual_review_queue_rows']}",
        f"- clean_06_preview_rows_before: {summary['clean_06_preview_rows_before']}",
        "",
        "## Reduction Result",
        f"- auto_resolvable_candidate_rows: {summary['auto_resolvable_candidate_rows']}",
        f"- remaining_manual_review_rows: {summary['remaining_manual_review_rows']}",
        f"- manual_review_reduction_count: {summary['manual_review_reduction_count']}",
        f"- manual_review_reduction_rate: {summary['manual_review_reduction_rate']}",
        f"- reduced_clean_06_preview_rows: {summary['reduced_clean_06_preview_rows']}",
        "",
        "## Conflict After Preview",
        f"- duplicate_key_count_after_preview: {summary['duplicate_key_count_after_preview']}",
        f"- value_mismatch_count_after_preview: {summary['value_mismatch_count_after_preview']}",
        f"- unit_conflict_count_after_preview: {summary['unit_conflict_count_after_preview']}",
        f"- year_conflict_count_after_preview: {summary['year_conflict_count_after_preview']}",
        "",
        "## Manual Review Reason Distribution",
        reason_md,
        "",
        "## EPS Check",
        f"- eps_detected_count: {summary['eps_detected_count']}",
        f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
        "",
        "## Safety",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        "",
        "## Decision",
        f"- ready_for_stage7h_ai_assisted_review_design: {summary['ready_for_stage7h_ai_assisted_review_design']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"stage7g_summary_json: {OUT_SUMMARY}")
    print(f"stage7g_report_md: {OUT_REPORT}")
    print(f"stage7g_ready_for_stage7h_ai_assisted_review_design: {summary['ready_for_stage7h_ai_assisted_review_design']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
