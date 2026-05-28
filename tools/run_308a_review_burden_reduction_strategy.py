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
OUT_DIR = BASE_DIR / "output" / "eval_308a_review_burden_reduction_strategy"

IN_307X_SUMMARY = BASE_DIR / "output" / "eval_307x_core_metric_pipeline_stage_summary" / "307x_summary.json"
IN_307H_BREAKDOWN = BASE_DIR / "output" / "eval_307h_final_preview_v2_quality_diagnosis" / "307h_review_required_breakdown_v2.xlsx"
IN_307H_METRIC = BASE_DIR / "output" / "eval_307h_final_preview_v2_quality_diagnosis" / "307h_review_burden_by_metric_v2.xlsx"
IN_307H_PDF = BASE_DIR / "output" / "eval_307h_final_preview_v2_quality_diagnosis" / "307h_review_burden_by_pdf_v2.xlsx"
IN_307G_REVIEW = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_306X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"
IN_306Z_REVIEW = BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2" / "306z_review_required_v2.xlsx"
IN_306L_GROUP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"

OUT_SUMMARY = OUT_DIR / "308a_summary.json"
OUT_REPORT = OUT_DIR / "308a_report.md"
OUT_GLOBAL = OUT_DIR / "308a_review_required_global_breakdown.xlsx"
OUT_BLOCKER = OUT_DIR / "308a_blocker_impact_ranking.xlsx"
OUT_SINGLE_MULTI = OUT_DIR / "308a_single_vs_multi_blocker_analysis.xlsx"
OUT_FIX = OUT_DIR / "308a_high_impact_fix_candidates.xlsx"
OUT_MATRIX = OUT_DIR / "308a_metric_pdf_bottleneck_matrix.xlsx"
OUT_NEXT = OUT_DIR / "308a_next_action_recommendation.md"
OUT_NO_APPLY = OUT_DIR / "308a_no_apply_proof.json"

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


def _prepare_global_breakdown(review_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    metric = (
        review_df.groupby("标准指标", dropna=False)
        .agg(row_count=("candidate_id", "count"), pdf_count=("PDF文件名", "nunique"), group_count=("group_id", "nunique"))
        .reset_index()
        .sort_values(["row_count", "pdf_count"], ascending=[False, False])
    )
    pdf = (
        review_df.groupby("PDF文件名", dropna=False)
        .agg(row_count=("candidate_id", "count"), metric_count=("标准指标", "nunique"), group_count=("group_id", "nunique"))
        .reset_index()
        .sort_values(["row_count", "metric_count"], ascending=[False, False])
    )
    source_parser = (
        review_df.groupby("source_parser", dropna=False)
        .agg(row_count=("candidate_id", "count"), pdf_count=("PDF文件名", "nunique"), metric_count=("标准指标", "nunique"))
        .reset_index()
        .sort_values("row_count", ascending=False)
    )
    source_bucket = (
        review_df.groupby("source_bucket", dropna=False)
        .agg(row_count=("candidate_id", "count"), pdf_count=("PDF文件名", "nunique"), metric_count=("标准指标", "nunique"))
        .reset_index()
        .sort_values("row_count", ascending=False)
    )
    risk_level = (
        review_df.groupby("risk_level", dropna=False)
        .agg(row_count=("candidate_id", "count"), pdf_count=("PDF文件名", "nunique"), metric_count=("标准指标", "nunique"))
        .reset_index()
        .sort_values("row_count", ascending=False)
    )

    return {
        "by_metric": metric,
        "by_pdf": pdf,
        "by_source_parser": source_parser,
        "by_source_bucket": source_bucket,
        "by_risk_level": risk_level,
    }


def _estimate_fix_impact(blocker_rows: pd.DataFrame) -> pd.DataFrame:
    # Group-level blockers mapped to row-level burden; estimate with conservative + moderate scenarios.
    fix_defs: List[Tuple[str, str, List[str], str]] = [
        (
            "parser_panel_denoise_and_merge",
            "parser fix",
            ["multi_panel_source", "suspicious_value_text", "duplicate_or_conflict"],
            "Parser-side panel stitching + noise filter to reduce mixed-panel and noisy-value review rows.",
        ),
        (
            "unit_semantic_standardization",
            "metric standardization fix",
            ["unit_unknown_or_warning", "unresolved_monetary_unit"],
            "Metric semantic unit resolver + monetary unit inference guardrails for unresolved unit warnings.",
        ),
        (
            "series_continuity_and_year_gap_repair",
            "auto_accept policy refinement",
            ["missing_year", "years_not_continuous"],
            "Year-gap detection repair + continuity-aware routing to separate recoverable vs must-review series.",
        ),
    ]

    rows: List[Dict[str, Any]] = []
    for fix_id, fix_type, blockers, note in fix_defs:
        cols = [f"blk_{b}" for b in blockers if f"blk_{b}" in blocker_rows.columns]
        if not cols:
            impacted = blocker_rows.iloc[0:0].copy()
        else:
            impacted = blocker_rows[blocker_rows[cols].any(axis=1)].copy()

        if impacted.empty:
            rows.append(
                {
                    "fix_id": fix_id,
                    "fix_type": fix_type,
                    "target_blockers": "|".join(blockers),
                    "impacted_group_count": 0,
                    "impacted_row_count": 0,
                    "single_blocker_row_count": 0,
                    "multi_blocker_row_count": 0,
                    "estimated_reduction_rows_conservative": 0,
                    "estimated_reduction_rows_moderate": 0,
                    "estimated_reduction_ratio_overall_conservative": 0.0,
                    "estimated_reduction_ratio_overall_moderate": 0.0,
                    "fix_note": note,
                }
            )
            continue

        single = impacted[impacted["blocker_count"] == 1]
        multi = impacted[impacted["blocker_count"] > 1]
        single_rows = int(len(single))
        multi_rows = int(len(multi))
        total_rows = int(len(impacted))

        # Conservative: single-blocker only + 20% of multi-blocker rows
        est_cons = int(round(single_rows + 0.20 * multi_rows))
        # Moderate: single-blocker + 45% of multi-blocker rows
        est_mod = int(round(single_rows + 0.45 * multi_rows))

        overall = int(len(blocker_rows)) if len(blocker_rows) else 1
        rows.append(
            {
                "fix_id": fix_id,
                "fix_type": fix_type,
                "target_blockers": "|".join(blockers),
                "impacted_group_count": int(impacted["group_id"].nunique()),
                "impacted_row_count": total_rows,
                "single_blocker_row_count": single_rows,
                "multi_blocker_row_count": multi_rows,
                "estimated_reduction_rows_conservative": est_cons,
                "estimated_reduction_rows_moderate": est_mod,
                "estimated_reduction_ratio_overall_conservative": float(est_cons / overall),
                "estimated_reduction_ratio_overall_moderate": float(est_mod / overall),
                "fix_note": note,
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["estimated_reduction_rows_moderate", "estimated_reduction_rows_conservative"],
        ascending=False,
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_307X_SUMMARY,
        IN_307H_BREAKDOWN,
        IN_307H_METRIC,
        IN_307H_PDF,
        IN_307G_REVIEW,
        IN_306X_BLOCKER,
        IN_306Z_REVIEW,
        IN_306L_GROUP,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-308A",
                "mode": "review_burden_reduction_strategy",
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

    s307x = json.loads(IN_307X_SUMMARY.read_text(encoding="utf-8"))

    review_df = _drop_note_rows(_load_first_sheet(IN_307G_REVIEW, "review_required_core_metrics_v2"))
    blocker_group_df = _drop_note_rows(_load_first_sheet(IN_306X_BLOCKER, "blocker_by_group"))
    review_306z_df = _drop_note_rows(_load_first_sheet(IN_306Z_REVIEW, "review_required_v2"))

    # Normalize core columns
    for c in ["group_id", "candidate_id", "PDF文件名", "标准指标", "source_parser", "source_bucket", "risk_level"]:
        if c in review_df.columns:
            review_df[c] = review_df[c].map(_norm)

    input_row_count = int(len(review_df))

    # Map group-level blockers to each review-required row
    blocker_cols = [
        "missing_year",
        "unit_unknown_or_warning",
        "zero_candidate_rescued",
        "alias_recovered",
        "multi_panel_source",
        "suspicious_value_text",
        "years_not_continuous",
        "unresolved_monetary_unit",
        "duplicate_or_conflict",
    ]
    blk_prefixed = [f"blk_{b}" for b in blocker_cols]

    blocker_group_df["group_id"] = blocker_group_df.get("group_id", "").map(_norm)
    for b in blocker_cols:
        key = f"blk_{b}"
        if key not in blocker_group_df.columns:
            blocker_group_df[key] = False

    keep_cols = ["group_id", "blocker_count", "blocker_list"] + blk_prefixed
    blocker_map = blocker_group_df[[c for c in keep_cols if c in blocker_group_df.columns]].copy()
    for b in blocker_cols:
        key = f"blk_{b}"
        blocker_map[key] = blocker_map[key].map(lambda x: str(x).strip().lower() in {"true", "1", "yes"})

    merged = review_df.merge(blocker_map, on="group_id", how="left")
    merged["blocker_count"] = merged.get("blocker_count", 0).map(_to_int)
    merged["blocker_list"] = merged.get("blocker_list", "").map(_norm)
    for b in blocker_cols:
        key = f"blk_{b}"
        merged[key] = merged.get(key, False).fillna(False)

    merged["single_blocker"] = merged["blocker_count"] == 1
    merged["multi_blocker"] = merged["blocker_count"] > 1

    global_breakdown = _prepare_global_breakdown(review_df)

    blocker_ranking_rows: List[Dict[str, Any]] = []
    for b in blocker_cols:
        key = f"blk_{b}"
        sub = merged[merged[key] == True]
        blocker_ranking_rows.append(
            {
                "blocker": b,
                "group_count": int(sub["group_id"].nunique()),
                "row_count": int(len(sub)),
                "pdf_count": int(sub["PDF文件名"].nunique()),
                "metric_count": int(sub["标准指标"].nunique()),
                "single_blocker_row_count": int(len(sub[sub["single_blocker"] == True])),
                "multi_blocker_row_count": int(len(sub[sub["multi_blocker"] == True])),
                "row_ratio": float(len(sub) / input_row_count) if input_row_count > 0 else 0.0,
            }
        )
    blocker_ranking_df = pd.DataFrame(blocker_ranking_rows).sort_values(["row_count", "group_count"], ascending=False)

    single_multi = pd.DataFrame(
        [
            {
                "segment": "single_blocker",
                "group_count": int(merged[merged["single_blocker"] == True]["group_id"].nunique()),
                "row_count": int(len(merged[merged["single_blocker"] == True])),
                "row_ratio": float(len(merged[merged["single_blocker"] == True]) / input_row_count) if input_row_count else 0.0,
            },
            {
                "segment": "multi_blocker",
                "group_count": int(merged[merged["multi_blocker"] == True]["group_id"].nunique()),
                "row_count": int(len(merged[merged["multi_blocker"] == True])),
                "row_ratio": float(len(merged[merged["multi_blocker"] == True]) / input_row_count) if input_row_count else 0.0,
            },
            {
                "segment": "no_blocker_flag_found",
                "group_count": int(merged[merged["blocker_count"] == 0]["group_id"].nunique()),
                "row_count": int(len(merged[merged["blocker_count"] == 0])),
                "row_ratio": float(len(merged[merged["blocker_count"] == 0]) / input_row_count) if input_row_count else 0.0,
            },
        ]
    )

    fix_df = _estimate_fix_impact(merged)
    top3 = fix_df.head(3).copy()

    metric_pdf_matrix = (
        review_df.pivot_table(
            index="标准指标",
            columns="PDF文件名",
            values="candidate_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )

    # Recommendation
    top_metric = _norm(global_breakdown["by_metric"].iloc[0]["标准指标"]) if not global_breakdown["by_metric"].empty else ""
    top_pdf = _norm(global_breakdown["by_pdf"].iloc[0]["PDF文件名"]) if not global_breakdown["by_pdf"].empty else ""

    # Strategy order by impact profile
    next_order = [
        "B. review burden reduction",
        "C. parser/metric standardization improvement",
        "A. human review UI/export productization",
        "D. targeted human review batch",
    ]

    next_md = [
        "# 308A Next Action Recommendation",
        "",
        "## Priority Order",
        "1. B. review burden reduction",
        "2. C. parser/metric standardization improvement",
        "3. A. human review UI/export productization",
        "4. D. targeted human review batch",
        "",
        "## Why",
        f"- current review_required rows: `{input_row_count}`",
        f"- top bottleneck metric: `{top_metric}`",
        f"- top bottleneck PDF: `{top_pdf}`",
        "- single-blocker rows should be reduced first because they offer highest safe ROI.",
        "- multi-blocker rows should follow after parser + standardization hardening.",
        "",
        "## Layered Diagnosis",
        "- extraction layer: multi-panel/noisy rows still propagate to review queue.",
        "- postprocess layer: year continuity and grouping amplify review burden for partial series.",
        "- standardization layer: unresolved unit semantics still block safe routing.",
    ]
    OUT_NEXT.write_text("\n".join(next_md) + "\n", encoding="utf-8")

    _write_excel(
        OUT_GLOBAL,
        {
            "by_metric": global_breakdown["by_metric"],
            "by_pdf": global_breakdown["by_pdf"],
            "by_source_parser": global_breakdown["by_source_parser"],
            "by_source_bucket": global_breakdown["by_source_bucket"],
            "by_risk_level": global_breakdown["by_risk_level"],
        },
    )
    _write_excel(OUT_BLOCKER, {"blocker_impact_ranking": blocker_ranking_df})
    _write_excel(
        OUT_SINGLE_MULTI,
        {
            "single_vs_multi_summary": single_multi,
            "single_blocker_rows": merged[merged["single_blocker"] == True],
            "multi_blocker_rows": merged[merged["multi_blocker"] == True],
        },
    )
    _write_excel(OUT_FIX, {"high_impact_fix_candidates": fix_df, "top3_fix_candidates": top3})
    _write_excel(OUT_MATRIX, {"metric_pdf_bottleneck_matrix": metric_pdf_matrix})

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

    forbidden_fields_generated = sorted([c for c in set(merged.columns) if c in FORBIDDEN_FIELDS])

    review_required_v2_row_count_from_307x = _to_int(s307x.get("review_required_rows_current", 0))
    review_required_307z_row_count = int(len(review_306z_df))
    input_row_count_preserved = input_row_count == review_required_v2_row_count_from_307x

    # Optional cross-check for continuity from 306Z to 307G v2
    review_required_delta_vs_306z = input_row_count - review_required_307z_row_count

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-308A",
        "mode": "review_burden_reduction_strategy",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "input_review_required_v2_row_count": input_row_count,
        "review_required_v2_row_count_from_307x": review_required_v2_row_count_from_307x,
        "input_row_count_preserved": bool(input_row_count_preserved),
        "review_required_307z_row_count": review_required_307z_row_count,
        "review_required_delta_vs_306z": review_required_delta_vs_306z,
        "top_bottleneck_metric_current": top_metric,
        "top_bottleneck_pdf_current": top_pdf,
        "top_3_high_impact_fixes": top3[["fix_id", "fix_type", "estimated_reduction_rows_conservative", "estimated_reduction_rows_moderate"]].to_dict(orient="records"),
        "recommended_next_stage_priority": "B > C > A > D",
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
        "# 308A Review Burden Reduction Strategy",
        "",
        "## Snapshot",
        f"- review_required rows (input): {input_row_count}",
        f"- top bottleneck metric: {top_metric}",
        f"- top bottleneck PDF: {top_pdf}",
        "",
        "## Global Burden",
        f"- source_parser categories: {int(global_breakdown['by_source_parser']['source_parser'].nunique()) if not global_breakdown['by_source_parser'].empty else 0}",
        f"- source_bucket categories: {int(global_breakdown['by_source_bucket']['source_bucket'].nunique()) if not global_breakdown['by_source_bucket'].empty else 0}",
        f"- risk_level categories: {int(global_breakdown['by_risk_level']['risk_level'].nunique()) if not global_breakdown['by_risk_level'].empty else 0}",
        "",
        "## Blocker Structure",
        f"- single_blocker rows: {_to_int(single_multi[single_multi['segment']=='single_blocker']['row_count'].iloc[0])}",
        f"- multi_blocker rows: {_to_int(single_multi[single_multi['segment']=='multi_blocker']['row_count'].iloc[0])}",
        "",
        "## Top 3 High-Impact Generic Fixes",
    ]
    for _, r in top3.iterrows():
        report_lines.append(
            f"- {r['fix_id']} ({r['fix_type']}): est_reduction_conservative={_to_int(r['estimated_reduction_rows_conservative'])}, est_reduction_moderate={_to_int(r['estimated_reduction_rows_moderate'])}"
        )
    report_lines += [
        "",
        "## Layered Conclusion",
        "- extraction layer: panel mixing/noise still drives large review burden segments.",
        "- postprocess layer: year-gap continuity and grouped-series coverage produce medium-high carry-over.",
        "- standardization layer: unit semantic ambiguity (especially monetary) remains a key blocker.",
        "",
        "## Guard",
        f"- input_row_count_preserved: {summary['input_row_count_preserved']}",
        f"- no_safe_to_apply_or_approve_for_real_apply_fields_generated: {summary['no_safe_to_apply_or_approve_for_real_apply_fields_generated']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
        f"- production_files_modified: {summary['production_files_modified']}",
        f"- official_02b_modified: {summary['official_02b_modified']}",
        f"- formal_rules_modified: {summary['formal_rules_modified']}",
        f"- standardizer_modified: {summary['standardizer_modified']}",
        f"- release_package_modified: {summary['release_package_modified']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_308a_summary_json: {OUT_SUMMARY}")
    print(f"eval_308a_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
