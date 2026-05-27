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
OUT_DIR = BASE_DIR / "output" / "eval_307c_eps_review_burden_drilldown"

IN_307A_FINAL = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_final_core_metric_preview.xlsx"
IN_307A_REVIEW = BASE_DIR / "output" / "eval_307a_core_metric_final_export_preview" / "307a_review_required_core_metrics.xlsx"
IN_307B_METRIC = BASE_DIR / "output" / "eval_307b_core_metric_export_quality_diagnosis" / "307b_review_burden_by_metric.xlsx"
IN_306Z_REVIEW = BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2" / "306z_review_required_v2.xlsx"
IN_306L_GROUP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"
IN_306X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"

OUT_SUMMARY = OUT_DIR / "307c_summary.json"
OUT_REPORT = OUT_DIR / "307c_report.md"
OUT_TRUSTED = OUT_DIR / "307c_eps_trusted_rows.xlsx"
OUT_REVIEW = OUT_DIR / "307c_eps_review_required_rows.xlsx"
OUT_BURDEN_PDF = OUT_DIR / "307c_eps_review_burden_by_pdf.xlsx"
OUT_BLOCKER = OUT_DIR / "307c_eps_blocker_distribution.xlsx"
OUT_SUSP = OUT_DIR / "307c_eps_suspicious_value_audit.xlsx"
OUT_POTENTIAL = OUT_DIR / "307c_eps_potential_auto_accept_candidates.xlsx"
OUT_MUST_REVIEW = OUT_DIR / "307c_eps_must_review_candidates.xlsx"
OUT_NO_APPLY = OUT_DIR / "307c_no_apply_proof.json"

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


def _parse_float(s: str) -> float | None:
    t = _norm(s)
    if t == "":
        return None
    if "%" in t:
        return None
    t2 = t.replace(",", "")
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", t2):
        try:
            return float(t2)
        except Exception:
            return None
    return None


def _has_chinese(s: str) -> bool:
    return re.search(r"[\u4e00-\u9fff]", _norm(s)) is not None


def _is_numeric_like(s: str) -> bool:
    t = _norm(s)
    if t == "":
        return False
    if "%" in t:
        return False
    t2 = t.replace(",", "")
    return re.fullmatch(r"[-+]?\d+(\.\d+)?", t2) is not None


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

    required = [IN_307A_FINAL, IN_307A_REVIEW, IN_307B_METRIC, IN_306Z_REVIEW, IN_306L_GROUP, IN_306X_BLOCKER]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307C",
                "mode": "eps_review_burden_drilldown",
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

    final_df = _drop_note_rows(_load_first_sheet(IN_307A_FINAL, "final_core_metric_preview"))
    review_df = _drop_note_rows(_load_first_sheet(IN_307A_REVIEW, "review_required_core_metrics"))
    metric_burden_df = _drop_note_rows(_load_first_sheet(IN_307B_METRIC, "review_burden_by_metric"))
    z_review_df = _drop_note_rows(_load_first_sheet(IN_306Z_REVIEW, "review_required_v2"))
    l_group_df = _drop_note_rows(_load_first_sheet(IN_306L_GROUP, "grouped_review_table"))
    blocker_df = _drop_note_rows(_load_first_sheet(IN_306X_BLOCKER, "blocker_by_group"))

    # EPS filter
    final_df["标准指标"] = final_df["标准指标"].map(_norm).str.lower()
    review_df["标准指标"] = review_df["标准指标"].map(_norm).str.lower()
    z_review_df["标准指标"] = z_review_df["标准指标"].map(_norm).str.lower()
    l_group_df["标准指标"] = l_group_df["标准指标"].map(_norm).str.lower()
    blocker_df["标准指标"] = blocker_df["标准指标"].map(_norm).str.lower()

    eps_trusted = final_df[final_df["标准指标"] == "eps"].copy()
    eps_review = review_df[review_df["标准指标"] == "eps"].copy()
    eps_z_review = z_review_df[z_review_df["标准指标"] == "eps"].copy()
    eps_groups = set(eps_review["group_id"].map(_norm).tolist()) if "group_id" in eps_review.columns else set()

    eps_blockers = blocker_df[(blocker_df["标准指标"] == "eps") & (blocker_df["group_id"].map(_norm).isin(eps_groups))].copy()

    # burden by pdf
    burden_by_pdf = (
        eps_review.groupby("PDF文件名", dropna=False)
        .agg(
            review_required_eps_rows=("PDF文件名", "count"),
            unique_group_count=("group_id", "nunique"),
            parser_mix=("source_parser", lambda x: "|".join(sorted({ _norm(v) for v in x if _norm(v) != "" }))),
            risk_mix=("risk_level", lambda x: "|".join(sorted({ _norm(v) for v in x if _norm(v) != "" }))),
        )
        .reset_index()
        .sort_values(["review_required_eps_rows", "unique_group_count"], ascending=[False, False])
        if not eps_review.empty
        else pd.DataFrame(columns=["PDF文件名", "review_required_eps_rows", "unique_group_count", "parser_mix", "risk_mix"])
    )

    # blocker distribution
    blk_cols = [c for c in eps_blockers.columns if c.startswith("blk_")]
    blk_rows: List[Dict[str, Any]] = []
    for c in blk_cols:
        sub = eps_blockers[eps_blockers[c].map(lambda v: _norm(v).lower() in {"true", "1", "yes"})]
        blk_rows.append(
            {
                "blocker": c.replace("blk_", ""),
                "group_count": int(sub["group_id"].nunique()) if not sub.empty else 0,
                "candidate_count_est": int(sub["candidate_count_review_required"].map(_to_int).sum()) if not sub.empty and "candidate_count_review_required" in sub.columns else 0,
            }
        )
    eps_blocker_dist = pd.DataFrame(blk_rows).sort_values(["group_count", "candidate_count_est"], ascending=False).reset_index(drop=True)

    # suspicious value audit (review-required EPS rows)
    susp_rows: List[Dict[str, Any]] = []
    for _, r in eps_review.iterrows():
        v = _norm(r.get("value", ""))
        f = _parse_float(v)
        very_large_abs = (f is not None and abs(f) > 20)
        percent_like = "%" in v
        has_cn = _has_chinese(v)
        non_numeric = (f is None)
        mixed_cn_num = has_cn and bool(re.search(r"\d", v))
        if any([very_large_abs, percent_like, mixed_cn_num, non_numeric]):
            susp_rows.append(
                {
                    "PDF文件名": _norm(r.get("PDF文件名", "")),
                    "group_id": _norm(r.get("group_id", "")),
                    "candidate_id": _norm(r.get("candidate_id", "")),
                    "年份": _to_int(r.get("年份", 0)),
                    "value": v,
                    "very_large_abs_gt_20": bool(very_large_abs),
                    "percent_like": bool(percent_like),
                    "mixed_chinese_text": bool(mixed_cn_num),
                    "non_numeric_value": bool(non_numeric),
                }
            )
    susp_df = pd.DataFrame(susp_rows)

    # potential vs must-review groups based on blocker and group-level conditions
    l_group_df["group_id"] = l_group_df["group_id"].map(_norm)
    eps_group_profile = l_group_df[l_group_df["标准指标"] == "eps"].copy()
    eps_group_profile = eps_group_profile[eps_group_profile["group_id"].isin(eps_groups)].copy()
    eps_group_profile = eps_group_profile.merge(
        eps_blockers[["group_id", "blk_duplicate_or_conflict", "blk_reviewed_risky_group", "blk_suspicious_value_text"]].drop_duplicates("group_id"),
        on="group_id",
        how="left",
    )
    eps_group_profile["blk_duplicate_or_conflict"] = eps_group_profile["blk_duplicate_or_conflict"].fillna(False)
    eps_group_profile["blk_reviewed_risky_group"] = eps_group_profile["blk_reviewed_risky_group"].fillna(False)
    eps_group_profile["blk_suspicious_value_text"] = eps_group_profile["blk_suspicious_value_text"].fillna(False)

    def _to_bool(v: Any) -> bool:
        return _norm(v).lower() in {"true", "1", "yes"}

    pot_rows: List[Dict[str, Any]] = []
    must_rows: List[Dict[str, Any]] = []
    for _, r in eps_group_profile.iterrows():
        conds = {
            "page1_summary": _to_bool(r.get("page1_summary", False)),
            "numeric_like_values": _to_bool(r.get("numeric_values_clean", False)),
            "semantic_unit_yuan_per_share": _norm(r.get("单位", "")).lower() in {"", "元/股", "yuan_per_share"} or _to_bool(r.get("unit_unknown", False)),
            "no_multi_panel": not _to_bool(r.get("multi_panel_source", False)),
            "no_zero_candidate_rescued": not _to_bool(r.get("zero_candidate_rescued", False)),
            "no_missing_year": not _to_bool(r.get("missing_year", False)),
            "no_duplicate_conflict": not _to_bool(r.get("blk_duplicate_or_conflict", False)),
            "no_suspicious_text": not _to_bool(r.get("blk_suspicious_value_text", False)),
            "no_reviewed_risky_group": not _to_bool(r.get("blk_reviewed_risky_group", False)),
        }
        rec = {
            "group_id": _norm(r.get("group_id", "")),
            "PDF文件名": _norm(r.get("PDF文件名", "")),
            "标准指标": "eps",
            "source_panel_id": _norm(r.get("source_panel_id", "")),
            "risk_reasons": _norm(r.get("risk_reasons", "")),
            "blocker_list": _norm(r.get("blocker_list", "")),
            **conds,
            "all_conditions_pass": all(conds.values()),
        }
        if rec["all_conditions_pass"]:
            pot_rows.append(rec)
        else:
            must_rows.append(rec)

    potential_df = pd.DataFrame(pot_rows)
    must_df = pd.DataFrame(must_rows)

    # review burden by parser/source bucket/risk
    eps_review_breakdown = (
        eps_review.groupby(["source_parser", "source_bucket", "risk_level"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .sort_values("row_count", ascending=False)
        if not eps_review.empty
        else pd.DataFrame(columns=["source_parser", "source_bucket", "risk_level", "row_count"])
    )

    _write_excel(OUT_TRUSTED, {"eps_trusted_rows": eps_trusted})
    _write_excel(OUT_REVIEW, {"eps_review_required_rows": eps_review, "eps_review_breakdown": eps_review_breakdown})
    _write_excel(OUT_BURDEN_PDF, {"eps_review_burden_by_pdf": burden_by_pdf})
    _write_excel(OUT_BLOCKER, {"eps_blocker_distribution": eps_blocker_dist})
    _write_excel(OUT_SUSP, {"eps_suspicious_value_audit": susp_df if not susp_df.empty else pd.DataFrame([{"note": "no_suspicious_eps_values"}])})
    _write_excel(OUT_POTENTIAL, {"eps_potential_auto_accept_candidates": potential_df if not potential_df.empty else pd.DataFrame([{"note": "no_eps_potential_auto_accept_candidates"}])})
    _write_excel(OUT_MUST_REVIEW, {"eps_must_review_candidates": must_df if not must_df.empty else pd.DataFrame([{"note": "no_eps_must_review_candidates"}])})

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

    forbidden_fields_generated = sorted([c for c in set(eps_trusted.columns).union(set(eps_review.columns)).union(set(potential_df.columns)).union(set(must_df.columns)) if c in FORBIDDEN_FIELDS])

    # cross-check from 307b metric burden table
    eps_metric_row = metric_burden_df[metric_burden_df["标准指标"].map(_norm).str.lower() == "eps"]
    eps_review_count_from_307b = int(eps_metric_row.iloc[0]["review_required_row_count"]) if not eps_metric_row.empty else 0

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-307C",
        "mode": "eps_review_burden_drilldown",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eps_trusted_row_count": int(len(eps_trusted)),
        "eps_review_required_row_count": int(len(eps_review)),
        "eps_review_required_row_count_from_307b": int(eps_review_count_from_307b),
        "eps_review_required_count_consistent_with_307b": bool(int(len(eps_review)) == int(eps_review_count_from_307b)),
        "eps_suspicious_value_row_count": int(len(susp_df)),
        "eps_potential_auto_accept_group_count": int(potential_df["group_id"].nunique()) if not potential_df.empty else 0,
        "eps_must_review_group_count": int(must_df["group_id"].nunique()) if not must_df.empty else 0,
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
        "# 307C EPS Review Burden Drilldown",
        "",
        "## EPS Volume",
        f"- eps_trusted_row_count: {summary['eps_trusted_row_count']}",
        f"- eps_review_required_row_count: {summary['eps_review_required_row_count']}",
        f"- eps_review_required_row_count_from_307b: {summary['eps_review_required_row_count_from_307b']}",
        f"- eps_review_required_count_consistent_with_307b: {summary['eps_review_required_count_consistent_with_307b']}",
        "",
        "## EPS Risk Diagnostics",
        f"- eps_suspicious_value_row_count: {summary['eps_suspicious_value_row_count']}",
        f"- eps_potential_auto_accept_group_count: {summary['eps_potential_auto_accept_group_count']}",
        f"- eps_must_review_group_count: {summary['eps_must_review_group_count']}",
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

    print(f"eval_307c_summary_json: {OUT_SUMMARY}")
    print(f"eval_307c_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
