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
OUT_DIR = BASE_DIR / "output" / "eval_306y_potential_safe_relaxation_review_package"

IN_X_RELAX = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_potential_safe_relaxation_candidates.xlsx"
IN_X_SINGLE = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_single_blocker_groups.xlsx"
IN_X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"
IN_L_MAP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_group_to_candidate_manifest.xlsx"
IN_W_REVIEW = BASE_DIR / "output" / "eval_306w_relaxed_auto_accept_policy_simulation" / "306w_relaxed_review_required.xlsx"

OUT_SUMMARY = OUT_DIR / "306y_summary.json"
OUT_REPORT = OUT_DIR / "306y_report.md"
OUT_REVIEW = OUT_DIR / "306y_relaxation_candidate_review.xlsx"
OUT_SAMPLED = OUT_DIR / "306y_sampled_relaxation_review.xlsx"
OUT_TYPE_DIST = OUT_DIR / "306y_relaxation_type_distribution.xlsx"
OUT_ORDER = OUT_DIR / "306y_recommended_review_order.xlsx"
OUT_NO_APPLY = OUT_DIR / "306y_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
YEAR_COLS = [str(y) for y in range(2020, 2031)]
RELAX_TYPE_COLS = [
    "unit_unknown_semantic_resolvable",
    "clean_multi_panel_candidate",
    "clean_missing_year_partial_series",
    "page1_summary_clean_candidate",
    "marker_clean_non_page1_candidate",
]


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


def _relax_types(row: pd.Series) -> List[str]:
    out: List[str] = []
    for c in RELAX_TYPE_COLS:
        if _to_bool(row.get(c, False)):
            out.append(c)
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_X_RELAX, IN_X_SINGLE, IN_X_BLOCKER, IN_L_MAP, IN_W_REVIEW]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306Y",
                "mode": "potential_safe_relaxation_review_package",
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

    x_relax = _drop_note_rows(_load_first_sheet(IN_X_RELAX, "potential_safe_relaxation_candidates"))
    x_single = _drop_note_rows(_load_first_sheet(IN_X_SINGLE, "single_blocker_groups"))
    x_blocker = _drop_note_rows(_load_first_sheet(IN_X_BLOCKER, "blocker_by_group"))
    l_map = _drop_note_rows(_load_first_sheet(IN_L_MAP, "group_to_candidate_manifest"))
    w_review = _drop_note_rows(_load_first_sheet(IN_W_REVIEW, "relaxed_review_required"))

    # Ensure group_id normalization
    for df in [x_relax, x_single, x_blocker, l_map, w_review]:
        if "group_id" in df.columns:
            df["group_id"] = df["group_id"].map(_norm)

    # Candidate mapping and page info
    l_map["candidate_id"] = l_map["candidate_id"].map(_norm)
    l_map["年份"] = l_map["年份"].map(_to_int)
    l_map["source_page"] = l_map["row_uid"].map(_norm).str.extract(r"\|(\d+)\|", expand=False).fillna("").map(_norm)
    map_group = (
        l_map.groupby("group_id", dropna=False)
        .agg(
            mapped_candidate_count=("candidate_id", "nunique"),
            mapped_candidate_ids=("candidate_id", lambda x: "|".join(sorted({_norm(v) for v in x if _norm(v) != ""}))),
            mapped_page_set=("source_page", lambda x: "|".join(sorted({_norm(v) for v in x if _norm(v) != ""}))),
        )
        .reset_index()
    )

    # review-required candidate counts
    rev_group = (
        w_review.groupby("group_id", dropna=False)
        .agg(
            review_required_candidate_count=("candidate_id", "nunique"),
            review_required_candidate_ids=("candidate_id", lambda x: "|".join(sorted({_norm(v) for v in x if _norm(v) != ""}))),
        )
        .reset_index()
    )

    # Build main review table from potential relaxation set
    xr = x_relax.copy()
    xr["relaxation_type_list"] = xr.apply(lambda r: "|".join(_relax_types(r)), axis=1)
    xr["relaxation_type_count"] = xr["relaxation_type_list"].map(lambda s: len([x for x in _norm(s).split("|") if x]))
    xr["is_single_blocker_group"] = xr["group_id"].isin(set(x_single["group_id"].map(_norm).tolist()))
    xr["blocker_reasons"] = xr.get("blocker_list", "").map(_norm)
    xr["risk_flags"] = xr.apply(
        lambda r: "|".join(
            [
                f
                for f, c in [
                    ("missing_year", "missing_year"),
                    ("unit_unknown", "unit_unknown"),
                    ("alias_recovered", "alias_recovered"),
                    ("zero_candidate_rescued", "zero_candidate_rescued"),
                    ("multi_panel_source", "multi_panel_source"),
                    ("suspicious_value_text", "blk_suspicious_value_text"),
                    ("years_not_continuous", "blk_years_not_continuous"),
                    ("reviewed_risky_group", "blk_reviewed_risky_group"),
                ]
                if _to_bool(r.get(c, False))
            ]
        ),
        axis=1,
    )

    review_df = xr.merge(map_group, on="group_id", how="left").merge(rev_group, on="group_id", how="left")
    review_df["mapped_candidate_count"] = review_df["mapped_candidate_count"].fillna(0).map(_to_int)
    review_df["review_required_candidate_count"] = review_df["review_required_candidate_count"].fillna(0).map(_to_int)

    # Reorder columns for human readability
    base_cols = [
        "group_id",
        "PDF文件名",
        "标准指标",
        "指标名",
        "单位",
        "来源解析器",
        "source_panel_id",
        "mapped_page_set",
        "review_priority",
        "blocker_count",
        "blocker_reasons",
        "relaxation_type_list",
        "relaxation_type_count",
        "is_single_blocker_group",
        "risk_flags",
        "mapped_candidate_count",
        "review_required_candidate_count",
        "mapped_candidate_ids",
        "review_required_candidate_ids",
    ]
    year_cols = [c for c in YEAR_COLS if c in review_df.columns]
    rest = [c for c in review_df.columns if c not in set(base_cols + year_cols)]
    review_df = review_df[base_cols + year_cols + rest]

    # Sample 20-30 groups, prioritize single-blocker groups first.
    # Fixed sample size = 24 groups.
    sample_target = 24
    unique_groups = review_df.drop_duplicates(subset=["group_id"]).copy()
    unique_groups["single_rank"] = unique_groups["is_single_blocker_group"].map(lambda x: 0 if bool(x) else 1)
    unique_groups["blocker_rank"] = unique_groups["blocker_count"].map(_to_int)
    unique_groups["candidate_rank"] = unique_groups["mapped_candidate_count"].map(_to_int)
    unique_groups = unique_groups.sort_values(
        by=["single_rank", "blocker_rank", "candidate_rank", "group_id"],
        ascending=[True, True, False, True],
    )
    sampled_group_ids = unique_groups.head(sample_target)["group_id"].tolist()
    sampled_df = review_df[review_df["group_id"].isin(sampled_group_ids)].copy()
    sampled_df["sample_priority_note"] = sampled_df["is_single_blocker_group"].map(lambda x: "single_blocker_first" if bool(x) else "multi_blocker_secondary")

    # Type distribution
    dist_rows: List[Dict[str, Any]] = []
    for t in RELAX_TYPE_COLS:
        sub = review_df[review_df[t].map(_to_bool) == True] if t in review_df.columns else pd.DataFrame()
        dist_rows.append(
            {
                "relaxation_type": t,
                "group_count": int(sub["group_id"].nunique()) if not sub.empty else 0,
                "candidate_count_estimated": int(sub["mapped_candidate_count"].sum()) if not sub.empty else 0,
                "single_blocker_group_count": int(sub[sub["is_single_blocker_group"] == True]["group_id"].nunique()) if not sub.empty else 0,
            }
        )
    dist_df = pd.DataFrame(dist_rows).sort_values(["group_count", "candidate_count_estimated"], ascending=False).reset_index(drop=True)

    # Recommended review order
    order_df = unique_groups.copy()
    order_df["recommended_order"] = list(range(1, len(order_df) + 1))
    order_df["recommended_review_reason"] = order_df.apply(
        lambda r: "single_blocker_first" if bool(r.get("is_single_blocker_group", False)) else "multi_blocker_after_single",
        axis=1,
    )

    _write_excel(OUT_REVIEW, {"relaxation_candidate_review": review_df})
    _write_excel(OUT_SAMPLED, {"sampled_relaxation_review": sampled_df})
    _write_excel(OUT_TYPE_DIST, {"relaxation_type_distribution": dist_df})
    _write_excel(OUT_ORDER, {"recommended_review_order": order_df})
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

    forbidden_fields_generated = sorted([c for c in review_df.columns if c in FORBIDDEN_FIELDS])

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-306Y",
        "mode": "potential_safe_relaxation_review_package",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "relaxation_candidate_group_count": int(review_df["group_id"].nunique()) if not review_df.empty else 0,
        "relaxation_candidate_row_count": int(len(review_df)),
        "sampled_group_count": int(sampled_df["group_id"].nunique()) if not sampled_df.empty else 0,
        "sampled_row_count": int(len(sampled_df)),
        "single_blocker_group_count_in_candidates": int(review_df[review_df["is_single_blocker_group"] == True]["group_id"].nunique()) if not review_df.empty else 0,
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
        "# 306Y Potential Safe Relaxation Review Package",
        "",
        "## Package Overview",
        f"- relaxation_candidate_group_count: {summary['relaxation_candidate_group_count']}",
        f"- relaxation_candidate_row_count: {summary['relaxation_candidate_row_count']}",
        f"- sampled_group_count: {summary['sampled_group_count']}",
        f"- sampled_row_count: {summary['sampled_row_count']}",
        f"- single_blocker_group_count_in_candidates: {summary['single_blocker_group_count_in_candidates']}",
        "",
        "## Sampling Policy",
        "- sampled 24 groups (within required 20-30 range)",
        "- prioritize single-blocker groups first, then multi-blocker groups",
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

    print(f"eval_306y_summary_json: {OUT_SUMMARY}")
    print(f"eval_306y_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
