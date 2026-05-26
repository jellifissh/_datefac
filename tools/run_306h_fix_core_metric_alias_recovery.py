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
OUT_DIR = BASE_DIR / "output" / "eval_306h_fix_core_metric_alias_recovery"

IN_306G_FIX_SUMMARY = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_summary.json"
IN_306G_FIX_CLEAN_CORE = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_clean_core_candidates.xlsx"
IN_306G_FIX_CLEAN_STRUCT = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_clean_structured_rows.xlsx"
IN_306G_FIX_SUSP = BASE_DIR / "output" / "eval_306g_fix_core_semantic_quality_gate" / "306g_fix_suspicious_structured_rows.xlsx"

IN_306H_SUMMARY = BASE_DIR / "output" / "eval_306h_clean_candidate_regression" / "306h_summary.json"
IN_306H_MISSING = BASE_DIR / "output" / "eval_306h_clean_candidate_regression" / "306h_missing_core_metric_audit.xlsx"

OUT_SUMMARY = OUT_DIR / "306h_fix_summary.json"
OUT_REPORT = OUT_DIR / "306h_fix_report.md"
OUT_CLEAN_CORE_V2 = OUT_DIR / "306h_fix_clean_core_candidates_v2.xlsx"
OUT_RECOVERED = OUT_DIR / "306h_fix_recovered_alias_candidates.xlsx"
OUT_UNRESOLVED = OUT_DIR / "306h_fix_unresolved_missing_core_metric_audit.xlsx"
OUT_RULES = OUT_DIR / "306h_fix_alias_recovery_rules.json"
OUT_NO_APPLY = OUT_DIR / "306h_fix_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

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
        IN_306H_SUMMARY,
        IN_306H_MISSING,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306H-FIX",
                "mode": "core_metric_alias_recovery",
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
    s_306h = json.loads(IN_306H_SUMMARY.read_text(encoding="utf-8"))
    clean_core = pd.read_excel(IN_306G_FIX_CLEAN_CORE).fillna("")
    clean_struct = pd.read_excel(IN_306G_FIX_CLEAN_STRUCT).fillna("")
    suspicious = pd.read_excel(IN_306G_FIX_SUSP).fillna("")
    missing_audit = pd.read_excel(IN_306H_MISSING).fillna("")

    existing_keys: Dict[Tuple[str, str, int], str] = {}
    for _, r in clean_core.iterrows():
        k = (_norm(r["source_pdf_name"]), _norm(r["normalized_metric_name"]).lower(), _to_int(r["year"]))
        existing_keys[k] = _canonical_value(r.get("value_raw", ""))

    clean_core_uid = set(clean_core["row_uid"].map(_norm).tolist()) if "row_uid" in clean_core.columns else set()
    candidates = pd.concat([clean_struct, suspicious], ignore_index=True).fillna("")
    candidates["source_bucket"] = ["clean_structured"] * len(clean_struct) + ["suspicious_structured"] * len(suspicious)
    if "row_uid" in candidates.columns:
        candidates = candidates[~candidates["row_uid"].map(_norm).isin(clean_core_uid)].copy()

    attempted_rows: List[Dict[str, Any]] = []
    pass_rows: List[Dict[str, Any]] = []
    blocked_rows: List[Dict[str, Any]] = []

    for _, r in candidates.iterrows():
        alias_metric = _detect_alias_metric(_norm(r.get("raw_metric_name", "")), _norm(r.get("normalized_metric_name", "")))
        if alias_metric is None:
            continue

        pdf = _norm(r.get("source_pdf_name", ""))
        year = _to_int(r.get("year", 0))
        key = (pdf, alias_metric, year)
        value_norm = _canonical_value(r.get("value_raw", ""))
        reasons: List[str] = []

        conf_flag = _norm(r.get("confidence_flags", ""))
        if conf_flag not in {"", "ok", "pdfplumber_selected"}:
            reasons.append("dirty_confidence_flag")
        if year < 2020 or year > 2032:
            reasons.append("suspicious_year")
        if _has_merged_value(_norm(r.get("value_raw", ""))):
            reasons.append("merged_value_cell")
        if _is_sentence_like(_norm(r.get("raw_metric_name", ""))):
            reasons.append("long_sentence_metric")
        if _is_prose_value(_norm(r.get("value_raw", ""))):
            reasons.append("prose_value")
        if "suspicious_reasons" in r and "value_raw_multi_numbers" in _norm(r.get("suspicious_reasons", "")):
            reasons.append("merged_value_cell")
        if "suspicious_reasons" in r and "metric_sentence_like_or_too_long" in _norm(r.get("suspicious_reasons", "")):
            reasons.append("long_sentence_metric")

        if key in existing_keys:
            if existing_keys[key] != value_norm:
                reasons.append("conflict_key_value_mismatch")
            else:
                reasons.append("conflict_key_duplicate_existing")

        rec = r.to_dict()
        rec["alias_metric_recovered"] = alias_metric
        rec["recovery_key"] = f"{pdf}|{alias_metric}|{year}"
        rec["recovery_block_reasons"] = "|".join(sorted(set(reasons)))
        attempted_rows.append(rec.copy())

        if reasons:
            blocked_rows.append(rec.copy())
            continue
        pass_rows.append(rec.copy())

    # Deduplicate pass rows by key and resolve in-source conflicts.
    pass_df = pd.DataFrame(pass_rows).fillna("")
    recovered_rows: List[Dict[str, Any]] = []
    blocked_more: List[Dict[str, Any]] = []
    if not pass_df.empty:
        pass_df["_score"] = 0
        pass_df.loc[pass_df["source_bucket"].map(_norm) == "clean_structured", "_score"] += 2
        pass_df.loc[pass_df["confidence_flags"].map(_norm) == "ok", "_score"] += 2
        pass_df.loc[pass_df["confidence_flags"].map(_norm) == "pdfplumber_selected", "_score"] += 1
        pass_df["_metric_len"] = pass_df["raw_metric_name"].map(lambda x: len(_norm(x)))
        pass_df = pass_df.sort_values(["recovery_key", "_score", "_metric_len"], ascending=[True, False, True])

        for key, grp in pass_df.groupby("recovery_key", dropna=False):
            grp = grp.copy()
            val_set = set(grp["value_raw"].map(_canonical_value).tolist())
            if len(val_set) > 1:
                for _, rr in grp.iterrows():
                    bb = rr.to_dict()
                    bb["recovery_block_reasons"] = "conflict_key_between_recovered_candidates"
                    blocked_more.append(bb)
                continue
            best = grp.iloc[0].to_dict()
            recovered_rows.append(best)
            if len(grp) > 1:
                for i in range(1, len(grp)):
                    bb = grp.iloc[i].to_dict()
                    bb["recovery_block_reasons"] = "duplicate_recovered_candidate_same_key"
                    blocked_more.append(bb)

    blocked_df = pd.concat([pd.DataFrame(blocked_rows), pd.DataFrame(blocked_more)], ignore_index=True).fillna("")
    recovered_df = pd.DataFrame(recovered_rows).fillna("")

    # Build clean core v2 by appending recovered rows using clean_core schema.
    clean_cols = clean_core.columns.tolist()
    add_rows: List[Dict[str, Any]] = []
    for _, r in recovered_df.iterrows():
        out = {c: "" for c in clean_cols}
        for c in clean_cols:
            if c in r:
                out[c] = r[c]
        out["normalized_metric_name"] = _norm(r.get("alias_metric_recovered", ""))
        out["row_uid"] = f"{_norm(r.get('source_pdf_name',''))}|{_to_int(r.get('page_number',0))}|{out['normalized_metric_name']}|{_to_int(r.get('year',0))}|{_norm(r.get('source_panel_id',''))}|{_norm(r.get('value_raw',''))}"
        add_rows.append(out)

    add_df = pd.DataFrame(add_rows).fillna("")
    clean_core_v2 = pd.concat([clean_core, add_df], ignore_index=True).fillna("")

    # safety dedupe by key with same value; conflicts should already be blocked.
    if not clean_core_v2.empty:
        clean_core_v2["_key"] = (
            clean_core_v2["source_pdf_name"].map(_norm)
            + "|"
            + clean_core_v2["normalized_metric_name"].map(_norm).str.lower()
            + "|"
            + clean_core_v2["year"].map(lambda x: str(_to_int(x)))
        )
        clean_core_v2["_val"] = clean_core_v2["value_raw"].map(_canonical_value)
        clean_core_v2 = clean_core_v2.sort_values(["_key"]).drop_duplicates(subset=["_key", "_val"], keep="first")
        clean_core_v2 = clean_core_v2.drop(columns=["_key", "_val"], errors="ignore")

    # unresolved missing metric audit.
    unresolved_rows: List[Dict[str, Any]] = []
    if "note" not in missing_audit.columns:
        attempted_df = pd.DataFrame(attempted_rows).fillna("")
        for _, mr in missing_audit.iterrows():
            pdf = _norm(mr.get("pdf_file_name", ""))
            metric = _norm(mr.get("missing_core_metric", "")).lower()
            recovered_count = 0
            if not recovered_df.empty:
                recovered_count = int(
                    recovered_df[
                        (recovered_df["source_pdf_name"].map(_norm) == pdf)
                        & (recovered_df["alias_metric_recovered"].map(_norm).str.lower() == metric)
                    ].shape[0]
                )
            attempted_sub = attempted_df[
                (attempted_df["source_pdf_name"].map(_norm) == pdf)
                & (attempted_df["alias_metric_recovered"].map(_norm).str.lower() == metric)
            ] if not attempted_df.empty else pd.DataFrame()
            if recovered_count > 0:
                status = "RESOLVED_BY_ALIAS_RECOVERY"
                reason = ""
            elif attempted_sub.empty:
                status = "UNRESOLVED"
                reason = "no_alias_candidate_detected"
            else:
                status = "UNRESOLVED"
                reasons = sorted(set("|".join(attempted_sub["recovery_block_reasons"].map(_norm).tolist()).split("|")))
                reasons = [x for x in reasons if x]
                reason = "|".join(reasons) if reasons else "blocked_by_safety_gate"
            unresolved_rows.append(
                {
                    "pdf_file_name": pdf,
                    "core_metric": metric,
                    "recovered_alias_row_count": recovered_count,
                    "attempted_alias_row_count": int(len(attempted_sub)),
                    "status": status,
                    "unresolved_reason": reason,
                }
            )
    unresolved_df = pd.DataFrame(unresolved_rows).fillna("")
    if unresolved_df.empty:
        unresolved_df = pd.DataFrame([{"note": "no_missing_core_metric_input"}])

    _write_excel(OUT_CLEAN_CORE_V2, {"clean_core_candidates_v2": clean_core_v2 if not clean_core_v2.empty else pd.DataFrame([{"note": "no_clean_core_v2"}])})
    _write_excel(
        OUT_RECOVERED,
        {
            "recovered_alias_candidates": recovered_df if not recovered_df.empty else pd.DataFrame([{"note": "no_recovered_alias_candidate"}]),
            "blocked_alias_candidates": blocked_df if not blocked_df.empty else pd.DataFrame([{"note": "no_blocked_alias_candidate"}]),
        },
    )
    _write_excel(OUT_UNRESOLVED, {"unresolved_missing_core_metric": unresolved_df})

    _write_json(
        OUT_RULES,
        {
            "stage": "EVAL-306H-FIX",
            "mode": "core_metric_alias_recovery",
            "alias_rules": ALIAS_RULES,
            "safety_blocks": [
                "dirty_confidence_flag",
                "suspicious_year",
                "merged_value_cell",
                "long_sentence_metric",
                "prose_value",
                "conflict_key_value_mismatch",
                "conflict_key_duplicate_existing",
                "conflict_key_between_recovered_candidates",
            ],
            "year_guard_min": 2020,
            "year_guard_max": 2032,
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

    unresolved_count = 0
    resolved_count = 0
    if "status" in unresolved_df.columns:
        unresolved_count = int((unresolved_df["status"].map(_norm) == "UNRESOLVED").sum())
        resolved_count = int((unresolved_df["status"].map(_norm) == "RESOLVED_BY_ALIAS_RECOVERY").sum())

    summary = {
        "stage": "EVAL-306H-FIX",
        "mode": "core_metric_alias_recovery",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_306g_fix_summary_loaded": True,
        "eval_306h_summary_loaded": True,
        "source_clean_core_row_count": int(len(clean_core)),
        "alias_candidate_attempt_count": int(len(attempted_rows)),
        "recovered_alias_candidate_count": int(len(recovered_df)),
        "blocked_alias_candidate_count": int(len(blocked_df)),
        "clean_core_v2_row_count": int(len(clean_core_v2)),
        "missing_core_metric_resolved_count": resolved_count,
        "missing_core_metric_unresolved_count": unresolved_count,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_next_regression_gate": bool(
            delivery_status == "PASS"
            and not production_files_modified
            and not official_02b_modified
            and not formal_rules_modified
            and not standardizer_modified
            and not release_package_modified
        ),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306H-Fix Core Metric Alias Recovery",
        "",
        f"- source_clean_core_row_count: {summary['source_clean_core_row_count']}",
        f"- alias_candidate_attempt_count: {summary['alias_candidate_attempt_count']}",
        f"- recovered_alias_candidate_count: {summary['recovered_alias_candidate_count']}",
        f"- blocked_alias_candidate_count: {summary['blocked_alias_candidate_count']}",
        f"- clean_core_v2_row_count: {summary['clean_core_v2_row_count']}",
        f"- missing_core_metric_resolved_count: {summary['missing_core_metric_resolved_count']}",
        f"- missing_core_metric_unresolved_count: {summary['missing_core_metric_unresolved_count']}",
        f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"eval_306h_fix_summary_json: {OUT_SUMMARY}")
    print(f"eval_306h_fix_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
