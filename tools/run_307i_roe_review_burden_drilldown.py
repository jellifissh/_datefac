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
OUT_DIR = BASE_DIR / "output" / "eval_307i_roe_review_burden_drilldown"

IN_FINAL_V2 = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_final_core_metric_preview_v2.xlsx"
IN_REVIEW_V2 = BASE_DIR / "output" / "eval_307g_merge_eps_review_into_final_preview" / "307g_review_required_core_metrics_v2.xlsx"
IN_BURDEN_METRIC_V2 = BASE_DIR / "output" / "eval_307h_final_preview_v2_quality_diagnosis" / "307h_review_burden_by_metric_v2.xlsx"
IN_306Z_REVIEW = BASE_DIR / "output" / "eval_306z_conservative_relaxation_policy_v2" / "306z_review_required_v2.xlsx"
IN_306L_GROUP = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules" / "306l_fix_grouped_review_table.xlsx"
IN_306X_BLOCKER = BASE_DIR / "output" / "eval_306x_auto_accept_blocker_diagnosis" / "306x_blocker_by_group.xlsx"

OUT_SUMMARY = OUT_DIR / "307i_summary.json"
OUT_REPORT = OUT_DIR / "307i_report.md"
OUT_TRUSTED = OUT_DIR / "307i_roe_trusted_rows.xlsx"
OUT_REVIEW = OUT_DIR / "307i_roe_review_required_rows.xlsx"
OUT_BURDEN_PDF = OUT_DIR / "307i_roe_review_burden_by_pdf.xlsx"
OUT_BLOCKER = OUT_DIR / "307i_roe_blocker_distribution.xlsx"
OUT_SUSP = OUT_DIR / "307i_roe_suspicious_value_audit.xlsx"
OUT_FOCUS = OUT_DIR / "307i_roe_potential_focused_review_candidates.xlsx"
OUT_MUST = OUT_DIR / "307i_roe_must_review_candidates.xlsx"
OUT_NO_APPLY = OUT_DIR / "307i_no_apply_proof.json"

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
    t2 = t.replace(",", "").replace("%", "")
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

    required = [IN_FINAL_V2, IN_REVIEW_V2, IN_BURDEN_METRIC_V2, IN_306Z_REVIEW, IN_306L_GROUP, IN_306X_BLOCKER]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-307I",
                "mode": "roe_review_burden_drilldown",
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

    final_v2 = _drop_note_rows(_load_first_sheet(IN_FINAL_V2, "final_core_metric_preview_v2"))
    review_v2 = _drop_note_rows(_load_first_sheet(IN_REVIEW_V2, "review_required_core_metrics_v2"))
    burden_metric_v2 = _drop_note_rows(_load_first_sheet(IN_BURDEN_METRIC_V2, "review_burden_by_metric_v2"))
    z_review_v2 = _drop_note_rows(_load_first_sheet(IN_306Z_REVIEW, "review_required_v2"))
    l_group = _drop_note_rows(_load_first_sheet(IN_306L_GROUP, "grouped_review_table"))
    blocker = _drop_note_rows(_load_first_sheet(IN_306X_BLOCKER, "blocker_by_group"))

    for df in [final_v2, review_v2, z_review_v2, l_group, blocker, burden_metric_v2]:
        if "标准指标" in df.columns:
            df["标准指标"] = df["标准指标"].map(_norm).str.lower()

    roe_trusted = final_v2[final_v2["标准指标"] == "roe"].copy()
    roe_review = review_v2[review_v2["标准指标"] == "roe"].copy()
    roe_groups = set(roe_review["group_id"].map(_norm).tolist()) if "group_id" in roe_review.columns else set()

    roe_blockers = blocker[(blocker["标准指标"] == "roe") & (blocker["group_id"].map(_norm).isin(roe_groups))].copy()

    # burden by pdf
    burden_by_pdf = (
        roe_review.groupby("PDF文件名", dropna=False)
        .agg(
            review_required_roe_rows=("PDF文件名", "count"),
            unique_group_count=("group_id", "nunique"),
            parser_mix=("source_parser", lambda x: "|".join(sorted({_norm(v) for v in x if _norm(v) != ""}))),
            risk_mix=("risk_level", lambda x: "|".join(sorted({_norm(v) for v in x if _norm(v) != ""}))),
            source_bucket_mix=("source_bucket", lambda x: "|".join(sorted({_norm(v) for v in x if _norm(v) != ""}))),
        )
        .reset_index()
        .sort_values(["review_required_roe_rows", "unique_group_count"], ascending=[False, False])
        if not roe_review.empty
        else pd.DataFrame(columns=["PDF文件名", "review_required_roe_rows", "unique_group_count", "parser_mix", "risk_mix", "source_bucket_mix"])
    )

    # blocker distribution
    blk_cols = [c for c in roe_blockers.columns if c.startswith("blk_")]
    blk_rows: List[Dict[str, Any]] = []
    for c in blk_cols:
        sub = roe_blockers[roe_blockers[c].map(lambda v: _norm(v).lower() in {"true", "1", "yes"})]
        blk_rows.append(
            {
                "blocker": c.replace("blk_", ""),
                "group_count": int(sub["group_id"].nunique()) if not sub.empty else 0,
                "candidate_count_est": int(sub["candidate_count_review_required"].map(_to_int).sum()) if not sub.empty and "candidate_count_review_required" in sub.columns else 0,
            }
        )
    roe_blocker_dist = pd.DataFrame(blk_rows).sort_values(["group_count", "candidate_count_est"], ascending=False).reset_index(drop=True)

    # suspicious value audit
    susp_rows: List[Dict[str, Any]] = []
    for _, r in roe_review.iterrows():
        v = _norm(r.get("value", ""))
        u = _norm(r.get("normalized_unit", "")).lower()
        f = _parse_float(v)
        abs_gt_100 = (f is not None and abs(f) > 100)
        percent_missing_unit = ("%" in v and u == "")
        looks_like_multiple = (f is not None and 0 <= f <= 100 and u in {"multiple", "x", "times"})
        mixed_chinese = _has_chinese(v) and bool(re.search(r"\d", v))
        non_numeric = (f is None)
        if any([abs_gt_100, percent_missing_unit, looks_like_multiple, mixed_chinese, non_numeric]):
            susp_rows.append(
                {
                    "PDF文件名": _norm(r.get("PDF文件名", "")),
                    "group_id": _norm(r.get("group_id", "")),
                    "candidate_id": _norm(r.get("candidate_id", "")),
                    "年份": _to_int(r.get("年份", 0)),
                    "value": v,
                    "normalized_unit": _norm(r.get("normalized_unit", "")),
                    "abs_gt_100": bool(abs_gt_100),
                    "percent_like_missing_unit": bool(percent_missing_unit),
                    "looks_like_pe_pb_multiple": bool(looks_like_multiple),
                    "mixed_chinese_text": bool(mixed_chinese),
                    "non_numeric_value": bool(non_numeric),
                }
            )
    susp_df = pd.DataFrame(susp_rows)

    # focused review vs must review grouping
    l_group["group_id"] = l_group["group_id"].map(_norm)
    roe_group_profile = l_group[(l_group["标准指标"] == "roe") & (l_group["group_id"].isin(roe_groups))].copy()
    roe_group_profile = roe_group_profile.merge(
        roe_blockers[["group_id", "blocker_list", "blk_duplicate_or_conflict", "blk_suspicious_value_text"]].drop_duplicates("group_id"),
        on="group_id",
        how="left",
    )
    roe_group_profile["blocker_list"] = roe_group_profile["blocker_list"].fillna("")
    roe_group_profile["blk_duplicate_or_conflict"] = roe_group_profile["blk_duplicate_or_conflict"].fillna(False)
    roe_group_profile["blk_suspicious_value_text"] = roe_group_profile["blk_suspicious_value_text"].fillna(False)

    focused_rows: List[Dict[str, Any]] = []
    must_rows: List[Dict[str, Any]] = []
    for _, r in roe_group_profile.iterrows():
        page1 = _norm(r.get("page1_summary", "")).lower() in {"true", "1", "yes"}
        numeric_clean = _norm(r.get("numeric_values_clean", "")).lower() in {"true", "1", "yes"}
        no_multi = _norm(r.get("multi_panel_source", "")).lower() not in {"true", "1", "yes"}
        no_zero = _norm(r.get("zero_candidate_rescued", "")).lower() not in {"true", "1", "yes"}
        no_missing_year = _norm(r.get("missing_year", "")).lower() not in {"true", "1", "yes"}
        no_dup = _norm(r.get("blk_duplicate_or_conflict", "")).lower() not in {"true", "1", "yes"}
        no_susp = _norm(r.get("blk_suspicious_value_text", "")).lower() not in {"true", "1", "yes"}

        rec = {
            "group_id": _norm(r.get("group_id", "")),
            "PDF文件名": _norm(r.get("PDF文件名", "")),
            "标准指标": "roe",
            "source_panel_id": _norm(r.get("source_panel_id", "")),
            "blocker_list": _norm(r.get("blocker_list", "")),
            "page1_summary": page1,
            "numeric_values_clean": numeric_clean,
            "no_multi_panel": no_multi,
            "no_zero_candidate_rescued": no_zero,
            "no_missing_year": no_missing_year,
            "no_duplicate_conflict": no_dup,
            "no_suspicious_text": no_susp,
        }
        # focused candidate: clean enough for dedicated human review batch
        is_focused = (numeric_clean and no_multi and no_zero and no_missing_year and no_dup)
        rec["is_focused_candidate"] = is_focused
        if is_focused:
            focused_rows.append(rec)
        else:
            must_rows.append(rec)

    focused_df = pd.DataFrame(focused_rows)
    must_df = pd.DataFrame(must_rows)

    review_breakdown = (
        roe_review.groupby(["source_parser", "source_bucket", "risk_level"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .sort_values("row_count", ascending=False)
        if not roe_review.empty
        else pd.DataFrame(columns=["source_parser", "source_bucket", "risk_level", "row_count"])
    )

    _write_excel(OUT_TRUSTED, {"roe_trusted_rows": roe_trusted if not roe_trusted.empty else pd.DataFrame([{"note": "no_roe_trusted_rows"}])})
    _write_excel(OUT_REVIEW, {"roe_review_required_rows": roe_review if not roe_review.empty else pd.DataFrame([{"note": "no_roe_review_required_rows"}]), "roe_review_breakdown": review_breakdown})
    _write_excel(OUT_BURDEN_PDF, {"roe_review_burden_by_pdf": burden_by_pdf})
    _write_excel(OUT_BLOCKER, {"roe_blocker_distribution": roe_blocker_dist})
    _write_excel(OUT_SUSP, {"roe_suspicious_value_audit": susp_df if not susp_df.empty else pd.DataFrame([{"note": "no_suspicious_roe_values"}])})
    _write_excel(OUT_FOCUS, {"roe_potential_focused_review_candidates": focused_df if not focused_df.empty else pd.DataFrame([{"note": "no_focused_candidates"}])})
    _write_excel(OUT_MUST, {"roe_must_review_candidates": must_df if not must_df.empty else pd.DataFrame([{"note": "no_must_review_candidates"}])})

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

    forbidden_fields_generated = sorted([c for c in set(roe_trusted.columns).union(set(roe_review.columns)).union(set(focused_df.columns)).union(set(must_df.columns)) if c in FORBIDDEN_FIELDS])

    # cross-check from 307h metric burden table
    roe_metric_row = burden_metric_v2[burden_metric_v2["标准指标"] == "roe"]
    roe_review_count_from_307h = int(roe_metric_row.iloc[0]["review_required_row_count"]) if not roe_metric_row.empty else 0

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "EVAL-307I",
        "mode": "roe_review_burden_drilldown",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "roe_trusted_row_count": int(len(roe_trusted)),
        "roe_review_required_row_count": int(len(roe_review)),
        "roe_review_required_row_count_from_307h": int(roe_review_count_from_307h),
        "roe_review_required_count_consistent_with_307h": bool(int(len(roe_review)) == int(roe_review_count_from_307h)),
        "roe_suspicious_value_row_count": int(len(susp_df)),
        "roe_focused_candidate_group_count": int(focused_df["group_id"].nunique()) if not focused_df.empty else 0,
        "roe_must_review_group_count": int(must_df["group_id"].nunique()) if not must_df.empty else 0,
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
        "# 307I ROE Review Burden Drilldown",
        "",
        "## ROE Volume",
        f"- roe_trusted_row_count: {summary['roe_trusted_row_count']}",
        f"- roe_review_required_row_count: {summary['roe_review_required_row_count']}",
        f"- roe_review_required_row_count_from_307h: {summary['roe_review_required_row_count_from_307h']}",
        f"- roe_review_required_count_consistent_with_307h: {summary['roe_review_required_count_consistent_with_307h']}",
        "",
        "## ROE Risk Diagnostics",
        f"- roe_suspicious_value_row_count: {summary['roe_suspicious_value_row_count']}",
        f"- roe_focused_candidate_group_count: {summary['roe_focused_candidate_group_count']}",
        f"- roe_must_review_group_count: {summary['roe_must_review_group_count']}",
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

    print(f"eval_307i_summary_json: {OUT_SUMMARY}")
    print(f"eval_307i_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
