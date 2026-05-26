from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
OUT_DIR = BASE_DIR / "output" / "eval_306h_fix2_alias_recovery_growth_guard"

IN_306G_FIX_SUMMARY = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_summary.json"
IN_306G_FIX_CLEAN_CORE = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_clean_core_candidates.xlsx"
IN_306G_FIX_CLEAN_STRUCT = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_clean_structured_rows.xlsx"
IN_306G_FIX_SUSP = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_suspicious_structured_rows.xlsx"

IN_306H_FIX_SUMMARY = BASE_DIR / "output" / "eval_306h_fix_core_metric_alias_recovery" / "306h_fix_summary.json"
IN_306H_FIX_RECOVERED = BASE_DIR / "output" / "eval_306h_fix_core_metric_alias_recovery" / "306h_fix_recovered_alias_candidates.xlsx"
IN_306H_FIX_UNRESOLVED = BASE_DIR / "output" / "eval_306h_fix_core_metric_alias_recovery" / "306h_fix_unresolved_missing_core_metric_audit.xlsx"

OUT_SUMMARY = OUT_DIR / "306h_fix2_summary.json"
OUT_REPORT = OUT_DIR / "306h_fix2_report.md"
OUT_CORE_V3 = OUT_DIR / "306h_fix2_clean_core_candidates_v3.xlsx"
OUT_VALID_RECOVERED = OUT_DIR / "306h_fix2_valid_recovered_alias_candidates.xlsx"
OUT_BLOCKED = OUT_DIR / "306h_fix2_blocked_alias_candidates.xlsx"
OUT_UNRESOLVED = OUT_DIR / "306h_fix2_unresolved_missing_core_metric_audit.xlsx"
OUT_RULES = OUT_DIR / "306h_fix2_alias_recovery_rules.json"
OUT_NO_APPLY = OUT_DIR / "306h_fix2_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

CORE_METRICS = {
    "revenue",
    "net_profit",
    "attributable_net_profit",
    "total_assets",
    "total_liabilities",
    "operating_cash_flow",
    "eps",
    "roe",
    "gross_margin",
    "pe",
    "pb",
    "ev_ebitda",
}
ABSOLUTE_CORE_METRICS = {
    "revenue",
    "net_profit",
    "attributable_net_profit",
    "operating_cash_flow",
    "total_assets",
    "total_liabilities",
}
GROWTH_WORDS = ["增长", "增长率", "同比", "yoy"]

ALIAS_RULES = [
    {"metric": "revenue", "aliases": ["营业总收入", "主营业务收入"]},
    {"metric": "attributable_net_profit", "aliases": ["归属母公司净利润", "归母净利润", "归属于母公司股东的净利润"]},
    {"metric": "operating_cash_flow", "aliases": ["经营活动产生的现金流量净额", "经营活动现金流净额"]},
    {"metric": "pe", "aliases": ["市盈率(pe)", "市盈率（pe）", "p/e"]},
    {"metric": "pb", "aliases": ["市净率(pb)", "市净率（pb）", "p/b"]},
    {"metric": "ev_ebitda", "aliases": ["企业价值倍数", "ev/ebitda"]},
]

PROSE_HINTS = ["报告", "观点", "评级", "证券", "风险", "联系人", "研究所", "指数", "大市", "同比", "环比"]


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


def _to_float(v: Any) -> Optional[float]:
    s = _norm(v)
    if s == "":
        return None
    s = s.replace(",", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def _canonical_value(v: Any) -> str:
    f = _to_float(v)
    if f is not None:
        return f"{f:.12g}"
    return _norm(v).replace(" ", "").replace(",", "")


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


def _detect_alias_metric(raw_metric: str, norm_metric: str) -> Optional[str]:
    txt = f"{_norm(raw_metric)}|{_norm(norm_metric)}".lower()
    for rule in ALIAS_RULES:
        for a in rule["aliases"]:
            if a.lower() in txt:
                return _norm(rule["metric"])
    return None


def _contains_growth_word(text: str) -> bool:
    s = _norm(text).lower()
    return any(w.lower() in s for w in GROWTH_WORDS)


def _is_sentence_like(text: str) -> bool:
    s = _norm(text)
    if s == "":
        return True
    if len(s) >= 20:
        return True
    if any(ch in s for ch in ["。", "，", ",", "；", ";", "：", ":", " "]):
        return True
    return False


def _is_prose_value(value_raw: str) -> bool:
    s = _norm(value_raw)
    if s == "":
        return True
    if len(s) >= 35:
        return True
    if any(k in s for k in PROSE_HINTS):
        return True
    if _to_float(s) is None:
        return True
    return False


def _has_merged_value(value_raw: str) -> bool:
    s = _norm(value_raw)
    nums = re.findall(r"-?\d+(?:\.\d+)?", s)
    if len(nums) <= 1:
        return False
    if any(sep in s for sep in [" ", "，", ",", "、", "/", "|"]):
        return True
    return len(nums) >= 3


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        IN_306G_FIX_SUMMARY,
        IN_306G_FIX_CLEAN_CORE,
        IN_306G_FIX_CLEAN_STRUCT,
        IN_306G_FIX_SUSP,
        IN_306H_FIX_SUMMARY,
        IN_306H_FIX_RECOVERED,
        IN_306H_FIX_UNRESOLVED,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306H-FIX2",
                "mode": "alias_recovery_growth_guard",
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

    s_306g = json.loads(IN_306G_FIX_SUMMARY.read_text(encoding="utf-8"))
    s_306h_fix = json.loads(IN_306H_FIX_SUMMARY.read_text(encoding="utf-8"))
    old_unresolved = pd.read_excel(IN_306H_FIX_UNRESOLVED).fillna("")
    baseline_core = pd.read_excel(IN_306G_FIX_CLEAN_CORE).fillna("")
    clean_struct = pd.read_excel(IN_306G_FIX_CLEAN_STRUCT).fillna("")
    suspicious = pd.read_excel(IN_306G_FIX_SUSP).fillna("")

    baseline_core["source_bucket"] = "baseline_clean_core"
    baseline_core["source_suspicious_reasons"] = ""
    baseline_core["alias_recovery_applied"] = False

    existing_key_to_value: Dict[Tuple[str, str, int], str] = {}
    for _, r in baseline_core.iterrows():
        k = (_norm(r["source_pdf_name"]), _norm(r["normalized_metric_name"]).lower(), _to_int(r["year"]))
        existing_key_to_value[k] = _canonical_value(r.get("value_raw", ""))

    baseline_uid = set(baseline_core["row_uid"].map(_norm).tolist()) if "row_uid" in baseline_core.columns else set()

    # candidate pool from 306G-Fix structured outputs, not from 306H-Fix v2 recovered list.
    pool = pd.concat([clean_struct, suspicious], ignore_index=True).fillna("")
    pool["source_bucket"] = ["clean_structured"] * len(clean_struct) + ["suspicious_structured"] * len(suspicious)
    pool["source_suspicious_reasons"] = pool["suspicious_reasons"].map(_norm) if "suspicious_reasons" in pool.columns else ""
    if "row_uid" in pool.columns:
        pool = pool[~pool["row_uid"].map(_norm).isin(baseline_uid)].copy()

    attempted_rows: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    blocked_rows: List[Dict[str, Any]] = []

    for _, r in pool.iterrows():
        alias_metric = _detect_alias_metric(_norm(r.get("raw_metric_name", "")), _norm(r.get("normalized_metric_name", "")))
        if alias_metric is None:
            continue

        rec = r.to_dict()
        rec["alias_metric_recovered"] = alias_metric
        rec["recovery_key"] = f"{_norm(r.get('source_pdf_name',''))}|{alias_metric}|{_to_int(r.get('year',0))}"
        reasons: List[str] = []

        raw_m = _norm(r.get("raw_metric_name", ""))
        norm_m = _norm(r.get("normalized_metric_name", ""))
        conf_flag = _norm(r.get("confidence_flags", ""))
        year = _to_int(r.get("year", 0))
        value_raw = _norm(r.get("value_raw", ""))
        source_bucket = _norm(r.get("source_bucket", ""))
        source_susp = _norm(r.get("source_suspicious_reasons", ""))
        key = (_norm(r.get("source_pdf_name", "")), alias_metric, year)
        val_norm = _canonical_value(value_raw)

        # Required hard blocks.
        if alias_metric in ABSOLUTE_CORE_METRICS and (
            _contains_growth_word(raw_m) or _contains_growth_word(norm_m)
        ):
            reasons.append("growth_guard_absolute_core_metric")
        if source_bucket == "suspicious_structured" and "core_semantic_false_positive" in source_susp:
            reasons.append("source_suspicious_core_semantic_false_positive")

        # Generic hard blocks.
        if conf_flag not in {"", "ok", "pdfplumber_selected"}:
            reasons.append("dirty_confidence_flag")
        if year < 2020 or year > 2032:
            reasons.append("suspicious_year")
        if _has_merged_value(value_raw):
            reasons.append("merged_value_cell")
        if _is_sentence_like(raw_m) or _is_sentence_like(norm_m):
            reasons.append("sentence_like_metric")
        if _is_prose_value(value_raw):
            reasons.append("prose_value")

        if key in existing_key_to_value:
            if existing_key_to_value[key] != val_norm:
                reasons.append("conflict_key_value_mismatch")
            else:
                reasons.append("conflict_key_duplicate_existing")

        rec["recovery_block_reasons"] = "|".join(sorted(set(reasons)))
        attempted_rows.append(rec.copy())
        if reasons:
            blocked_rows.append(rec.copy())
        else:
            valid_rows.append(rec.copy())

    valid_df = pd.DataFrame(valid_rows).fillna("")
    blocked_df = pd.DataFrame(blocked_rows).fillna("")

    # Deduplicate valid rows by key and enforce no conflicts.
    final_valid: List[Dict[str, Any]] = []
    blocked_more: List[Dict[str, Any]] = []
    if not valid_df.empty:
        valid_df["_score"] = 0
        valid_df.loc[valid_df["source_bucket"].map(_norm) == "clean_structured", "_score"] += 2
        valid_df.loc[valid_df["confidence_flags"].map(_norm) == "ok", "_score"] += 2
        valid_df.loc[valid_df["confidence_flags"].map(_norm) == "pdfplumber_selected", "_score"] += 1
        valid_df["_metric_len"] = valid_df["raw_metric_name"].map(lambda x: len(_norm(x)))
        valid_df = valid_df.sort_values(["recovery_key", "_score", "_metric_len"], ascending=[True, False, True])

        for key, grp in valid_df.groupby("recovery_key", dropna=False):
            val_set = set(grp["value_raw"].map(_canonical_value).tolist())
            if len(val_set) > 1:
                for _, rr in grp.iterrows():
                    bb = rr.to_dict()
                    bb["recovery_block_reasons"] = "conflict_key_between_recovered_candidates"
                    blocked_more.append(bb)
                continue
            best = grp.iloc[0].to_dict()
            final_valid.append(best)
            if len(grp) > 1:
                for i in range(1, len(grp)):
                    bb = grp.iloc[i].to_dict()
                    bb["recovery_block_reasons"] = "duplicate_recovered_candidate_same_key"
                    blocked_more.append(bb)

    if blocked_more:
        blocked_df = pd.concat([blocked_df, pd.DataFrame(blocked_more)], ignore_index=True).fillna("")
    valid_df2 = pd.DataFrame(final_valid).fillna("")

    # Build v3 from baseline + valid recovered only.
    base_cols = baseline_core.columns.tolist()
    add_rows: List[Dict[str, Any]] = []
    for _, r in valid_df2.iterrows():
        out = {c: "" for c in base_cols}
        for c in base_cols:
            if c in r:
                out[c] = r[c]
        out["normalized_metric_name"] = _norm(r.get("alias_metric_recovered", ""))
        out["alias_recovery_applied"] = True
        out["row_uid"] = (
            f"{_norm(r.get('source_pdf_name',''))}|{_to_int(r.get('page_number',0))}|"
            f"{out['normalized_metric_name']}|{_to_int(r.get('year',0))}|{_norm(r.get('source_panel_id',''))}|{_norm(r.get('value_raw',''))}"
        )
        add_rows.append(out)
    add_df = pd.DataFrame(add_rows).fillna("")

    v3 = pd.concat([baseline_core, add_df], ignore_index=True).fillna("")
    v3["metric_norm_l"] = v3["normalized_metric_name"].map(_norm).str.lower()
    v3["year_int"] = v3["year"].map(_to_int)
    v3["value_norm"] = v3["value_raw"].map(_canonical_value)
    v3["dup_key"] = (
        v3["source_pdf_name"].map(_norm) + "|" + v3["metric_norm_l"] + "|" + v3["year_int"].map(lambda x: str(_to_int(x)))
    )

    # Duplicate and conflict checks on v3.
    grp = v3.groupby("dup_key", dropna=False).agg(
        row_count=("row_uid", "count"),
        unique_value_count=("value_norm", pd.Series.nunique),
    ).reset_index()
    dup_key_count = int((grp["row_count"] > 1).sum())
    value_conflict_count = int(((grp["row_count"] > 1) & (grp["unique_value_count"] > 1)).sum())

    # Keep one row per identical key+value, block duplicates.
    if dup_key_count > 0:
        v3 = v3.sort_values(["dup_key"]).drop_duplicates(subset=["dup_key", "value_norm"], keep="first")
        v3 = v3.copy()
        v3["dup_key"] = (
            v3["source_pdf_name"].map(_norm) + "|" + v3["metric_norm_l"] + "|" + v3["year_int"].map(lambda x: str(_to_int(x)))
        )
        grp2 = v3.groupby("dup_key", dropna=False).agg(
            row_count=("row_uid", "count"),
            unique_value_count=("value_norm", pd.Series.nunique),
        ).reset_index()
        dup_key_count = int((grp2["row_count"] > 1).sum())
        value_conflict_count = int(((grp2["row_count"] > 1) & (grp2["unique_value_count"] > 1)).sum())

    # Required assertions.
    growth_mask = v3["raw_metric_name"].map(_norm).str.contains("增长率|增长", regex=True)
    growth_row_count = int(growth_mask.sum())

    core_semantic_mask = (
        (v3["source_bucket"].map(_norm) == "suspicious_structured")
        & (v3["source_suspicious_reasons"].map(_norm).str.contains("core_semantic_false_positive", regex=False))
    )
    core_semantic_row_count = int(core_semantic_mask.sum())

    assertions = {
        "growth_rows_in_v3_equals_0": growth_row_count == 0,
        "suspicious_core_semantic_false_positive_in_v3_equals_0": core_semantic_row_count == 0,
        "duplicate_pdf_metric_year_keys_equals_0": dup_key_count == 0,
        "value_conflicts_equals_0": value_conflict_count == 0,
    }

    # unresolved missing metric audit from 306h_fix unresolved baseline.
    unresolved_rows: List[Dict[str, Any]] = []
    if "note" not in old_unresolved.columns:
        for _, r in old_unresolved.iterrows():
            pdf = _norm(r.get("pdf_file_name", ""))
            metric = _norm(r.get("core_metric", ""))
            recovered_count = int(
                v3[
                    (v3["alias_recovery_applied"] == True)
                    & (v3["source_pdf_name"].map(_norm) == pdf)
                    & (v3["metric_norm_l"] == metric.lower())
                ].shape[0]
            )
            if recovered_count > 0:
                status = "RESOLVED_BY_FIX2"
                reason = ""
            else:
                status = _norm(r.get("status", "UNRESOLVED"))
                reason = _norm(r.get("unresolved_reason", ""))
            unresolved_rows.append(
                {
                    "pdf_file_name": pdf,
                    "core_metric": metric,
                    "status": status,
                    "fix2_recovered_alias_row_count": recovered_count,
                    "unresolved_reason": reason,
                }
            )
    unresolved_df = pd.DataFrame(unresolved_rows).fillna("")
    if unresolved_df.empty:
        unresolved_df = pd.DataFrame([{"note": "no_unresolved_input"}])

    # finalize output frames.
    v3_out = v3.drop(columns=["metric_norm_l", "year_int", "value_norm", "dup_key"], errors="ignore")

    _write_excel(OUT_CORE_V3, {"clean_core_candidates_v3": v3_out})
    _write_excel(OUT_VALID_RECOVERED, {"valid_recovered_alias_candidates": valid_df2 if not valid_df2.empty else pd.DataFrame([{"note": "no_valid_recovered_alias"}])})
    _write_excel(OUT_BLOCKED, {"blocked_alias_candidates": blocked_df if not blocked_df.empty else pd.DataFrame([{"note": "no_blocked_alias_candidate"}])})
    _write_excel(OUT_UNRESOLVED, {"unresolved_missing_core_metric": unresolved_df})

    _write_json(
        OUT_RULES,
        {
            "stage": "EVAL-306H-FIX2",
            "mode": "alias_recovery_growth_guard",
            "alias_rules": ALIAS_RULES,
            "absolute_core_metrics_for_growth_guard": sorted(list(ABSOLUTE_CORE_METRICS)),
            "growth_words": GROWTH_WORDS,
            "hard_block_rules": [
                "growth_guard_absolute_core_metric",
                "source_suspicious_core_semantic_false_positive",
                "dirty_confidence_flag",
                "suspicious_year",
                "merged_value_cell",
                "sentence_like_metric",
                "prose_value",
                "conflict_key_value_mismatch",
                "conflict_key_duplicate_existing",
                "conflict_key_between_recovered_candidates",
            ],
            "baseline_rebuild_source": "306g_fix_clean_core_candidates.xlsx",
            "required_assertions": assertions,
        },
    )

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "marker_rerun_executed": False,
            "pdfplumber_rerun_executed": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
        },
    )

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]
    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    resolved_count = 0
    unresolved_count = 0
    if "status" in unresolved_df.columns:
        resolved_count = int((unresolved_df["status"].map(_norm) == "RESOLVED_BY_FIX2").sum())
        unresolved_count = int((unresolved_df["status"].map(_norm).str.startswith("UNRESOLVED")).sum())

    all_assertions_pass = all(assertions.values())
    summary = {
        "stage": "EVAL-306H-FIX2",
        "mode": "alias_recovery_growth_guard",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_306g_fix_summary_loaded": True,
        "eval_306h_fix_summary_loaded": True,
        "baseline_clean_core_row_count": int(len(baseline_core)),
        "attempted_alias_candidate_count": int(len(attempted_rows)),
        "valid_recovered_alias_candidate_count": int(len(valid_df2)),
        "blocked_alias_candidate_count": int(len(blocked_df)),
        "clean_core_candidates_v3_row_count": int(len(v3_out)),
        "fix2_resolved_missing_core_metric_count": resolved_count,
        "fix2_unresolved_missing_core_metric_count": unresolved_count,
        "assert_growth_rows_in_v3_count": growth_row_count,
        "assert_core_semantic_false_positive_rows_in_v3_count": core_semantic_row_count,
        "assert_duplicate_pdf_metric_year_key_count": dup_key_count,
        "assert_value_conflict_count": value_conflict_count,
        "assertions": assertions,
        "all_assertions_pass": all_assertions_pass,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_next_regression_gate": bool(
            delivery_status == "PASS"
            and all_assertions_pass
            and not production_files_modified
            and not official_02b_modified
            and not formal_rules_modified
            and not standardizer_modified
            and not release_package_modified
        ),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306H-Fix2 Alias Recovery Growth Guard",
        "",
        f"- baseline_clean_core_row_count: {summary['baseline_clean_core_row_count']}",
        f"- attempted_alias_candidate_count: {summary['attempted_alias_candidate_count']}",
        f"- valid_recovered_alias_candidate_count: {summary['valid_recovered_alias_candidate_count']}",
        f"- blocked_alias_candidate_count: {summary['blocked_alias_candidate_count']}",
        f"- clean_core_candidates_v3_row_count: {summary['clean_core_candidates_v3_row_count']}",
        f"- growth_rows_in_v3_count: {summary['assert_growth_rows_in_v3_count']}",
        f"- suspicious_core_semantic_false_positive_rows_in_v3_count: {summary['assert_core_semantic_false_positive_rows_in_v3_count']}",
        f"- duplicate_pdf_metric_year_key_count: {summary['assert_duplicate_pdf_metric_year_key_count']}",
        f"- value_conflict_count: {summary['assert_value_conflict_count']}",
        f"- all_assertions_pass: {summary['all_assertions_pass']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306h_fix2_summary_json: {OUT_SUMMARY}")
    print(f"eval_306h_fix2_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
