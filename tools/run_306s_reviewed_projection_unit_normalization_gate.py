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
OUT_DIR = BASE_DIR / "output" / "eval_306s_reviewed_projection_unit_normalization_gate"

IN_306R_SUMMARY = BASE_DIR / "output" / "eval_306r_reviewed_candidate_sandbox_projection" / "306r_summary.json"
IN_PROJ = BASE_DIR / "output" / "eval_306r_reviewed_candidate_sandbox_projection" / "306r_reviewed_candidate_projection.xlsx"
IN_UNIT_AUDIT = BASE_DIR / "output" / "eval_306r_reviewed_candidate_sandbox_projection" / "306r_unit_sanity_audit.xlsx"
IN_MISSING_PREVIEW = BASE_DIR / "output" / "eval_306r_reviewed_candidate_sandbox_projection" / "306r_missing_candidate_projection_preview.xlsx"

OUT_SUMMARY = OUT_DIR / "306s_summary.json"
OUT_REPORT = OUT_DIR / "306s_report.md"
OUT_NORM_PROJ = OUT_DIR / "306s_unit_normalized_projection.xlsx"
OUT_NORM_AUDIT = OUT_DIR / "306s_unit_normalization_audit.xlsx"
OUT_WARN_AUDIT = OUT_DIR / "306s_unit_warning_audit.xlsx"
OUT_MISSING_PREVIEW = OUT_DIR / "306s_missing_candidate_unit_preview.xlsx"
OUT_NO_APPLY = OUT_DIR / "306s_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

FORBIDDEN_FIELDS = {"safe_to_apply", "approve_for_real_apply"}
MONETARY_METRICS = {
    "revenue",
    "net_profit",
    "attributable_net_profit",
    "operating_cash_flow",
    "total_assets",
    "total_liabilities",
}


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


def _metric_semantic_default(metric: str) -> str:
    m = metric.lower()
    if m == "eps":
        return "yuan_per_share"
    if m in {"pe", "pb", "ev_ebitda"}:
        return "multiple"
    if m == "roe" or m == "gross_margin" or ("margin" in m) or ("growth_rate" in m):
        return "percent"
    return ""


def _normalize_unit_token(unit: str) -> str:
    u = _norm(unit).lower()
    if u == "":
        return ""
    if u in {"unknown", "na", "n/a", "null", "-"}:
        return ""

    percent_alias = {"percent", "%", "pct", "percentage", "百分比"}
    multiple_alias = {"multiple", "x", "倍"}
    eps_alias = {"yuan_per_share", "元/股", "元每股", "元/每股"}
    monetary_alias = {
        "million_cny": {"million_cny", "百万元", "百万", "million", "mn_cny"},
        "billion_cny": {"billion_cny", "亿元", "billion", "bn_cny"},
        "thousand_cny": {"thousand_cny", "千元", "thousand"},
        "cny": {"cny", "元", "人民币元"},
    }

    if u in {x.lower() for x in percent_alias}:
        return "percent"
    if u in {x.lower() for x in multiple_alias}:
        return "multiple"
    if u in {x.lower() for x in eps_alias}:
        return "yuan_per_share"
    for k, aliases in monetary_alias.items():
        if u in {x.lower() for x in aliases}:
            return k
    return u


def _resolve_normalized_unit(metric: str, effective_unit: str, original_unit: str) -> Tuple[str, str, str]:
    # returns: normalized_unit, unit_resolution_source, unit_warning
    sem = _metric_semantic_default(metric)
    eff_norm = _normalize_unit_token(effective_unit)
    ori_norm = _normalize_unit_token(original_unit)

    if eff_norm != "":
        return eff_norm, "from_effective_unit", ""
    if ori_norm != "":
        return ori_norm, "from_original_unit", ""
    if sem != "":
        return sem, "semantic_default", ""

    if metric.lower() in MONETARY_METRICS:
        return "", "unresolved_unknown", "monetary_unit_unknown"
    return "", "unresolved_unknown", ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306R_SUMMARY, IN_PROJ, IN_UNIT_AUDIT, IN_MISSING_PREVIEW]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306S",
                "mode": "reviewed_projection_unit_normalization_gate",
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

    s_306r = json.loads(IN_306R_SUMMARY.read_text(encoding="utf-8"))
    proj = _drop_note_rows(_load_first_sheet(IN_PROJ, "reviewed_candidate_projection"))
    unit_audit_in = _drop_note_rows(_load_first_sheet(IN_UNIT_AUDIT, "unit_sanity_audit"))
    missing_preview = _drop_note_rows(_load_first_sheet(IN_MISSING_PREVIEW, "missing_candidate_projection_preview"))

    # Normalize reviewed projection units.
    norm_rows: List[Dict[str, Any]] = []
    for _, r in proj.iterrows():
        rec = r.to_dict()
        metric = _norm(r.get("标准指标", ""))
        effective_unit = _norm(r.get("effective_unit", ""))
        original_unit = _norm(r.get("original_unit", ""))
        normalized_unit, source, warn = _resolve_normalized_unit(metric, effective_unit, original_unit)
        rec["normalized_unit"] = normalized_unit
        rec["unit_resolution_source"] = source
        rec["unit_warning"] = warn
        norm_rows.append(rec)
    norm_proj = pd.DataFrame(norm_rows).fillna("")

    # Normalize missing candidate preview units separately.
    miss_rows: List[Dict[str, Any]] = []
    for _, r in missing_preview.iterrows():
        rec = r.to_dict()
        metric = _norm(r.get("标准指标", ""))
        effective_unit = _norm(r.get("effective_unit", ""))
        original_unit = _norm(r.get("original_unit", ""))
        # missing preview typically has no original_unit; still same normalization logic
        normalized_unit, source, warn = _resolve_normalized_unit(metric, effective_unit, original_unit)
        rec["normalized_unit"] = normalized_unit
        rec["unit_resolution_source"] = source
        rec["unit_warning"] = warn
        miss_rows.append(rec)
    norm_missing = pd.DataFrame(miss_rows).fillna("")

    # Sanity checks
    projection_input_count = int(len(proj))
    normalized_projection_count = int(len(norm_proj))

    # Duplicate keys and value conflicts on normalized projection
    key_cols = ["PDF文件名", "标准指标", "年份"]
    if all(c in norm_proj.columns for c in key_cols) and not norm_proj.empty:
        key_df = norm_proj.copy()
        key_df["key_pdf"] = key_df["PDF文件名"].map(_norm)
        key_df["key_metric"] = key_df["标准指标"].map(_norm)
        key_df["key_year"] = key_df["年份"].map(_to_int)
        key_df["key"] = key_df["key_pdf"] + "|" + key_df["key_metric"] + "|" + key_df["key_year"].astype(str)
        dup_df = key_df.groupby("key", dropna=False).size().reset_index(name="count")
        dup_df = dup_df[dup_df["count"] > 1].copy()
        dup_detail = key_df[key_df["key"].isin(set(dup_df["key"]))].copy() if not dup_df.empty else pd.DataFrame()

        conflict_rows: List[Dict[str, Any]] = []
        for k, g in key_df.groupby("key", dropna=False):
            vals = sorted({v for v in g["effective_value"].map(_norm).tolist() if v != ""})
            if len(vals) > 1:
                one = g.iloc[0]
                conflict_rows.append(
                    {
                        "key": k,
                        "PDF文件名": _norm(one.get("PDF文件名", "")),
                        "标准指标": _norm(one.get("标准指标", "")),
                        "年份": _to_int(one.get("年份", 0)),
                        "distinct_effective_values": " | ".join(vals),
                        "row_count": int(len(g)),
                    }
                )
        conflict_df = pd.DataFrame(conflict_rows)
    else:
        dup_df = pd.DataFrame()
        dup_detail = pd.DataFrame()
        conflict_df = pd.DataFrame()

    duplicate_key_count = int(len(dup_df))
    value_conflict_count = int(len(conflict_df))

    # Warnings
    warning_df = norm_proj[norm_proj.get("unit_warning", "").map(_norm) != ""].copy() if not norm_proj.empty else pd.DataFrame()
    if warning_df.empty:
        warning_df = pd.DataFrame([{"note": "no_unit_warning_rows"}])

    # Forbidden fields
    all_cols = set(norm_proj.columns).union(set(norm_missing.columns))
    forbidden_fields_generated = sorted([c for c in all_cols if c in FORBIDDEN_FIELDS])

    # Outputs
    _write_excel(
        OUT_NORM_PROJ,
        {
            "unit_normalized_projection": norm_proj if not norm_proj.empty else pd.DataFrame([{"note": "no_normalized_projection_rows"}]),
            "resolution_source_distribution": (
                norm_proj.groupby("unit_resolution_source", dropna=False).size().reset_index(name="row_count")
                if not norm_proj.empty
                else pd.DataFrame([{"unit_resolution_source": "N/A", "row_count": 0}])
            ),
        },
    )
    _write_excel(
        OUT_NORM_AUDIT,
        {
            "unit_normalization_audit": norm_proj[
                [
                    c
                    for c in [
                        "candidate_id",
                        "PDF文件名",
                        "标准指标",
                        "年份",
                        "decision_candidate",
                        "effective_unit",
                        "original_unit",
                        "normalized_unit",
                        "unit_resolution_source",
                        "unit_warning",
                    ]
                    if c in norm_proj.columns
                ]
            ]
            if not norm_proj.empty
            else pd.DataFrame([{"note": "no_unit_normalization_rows"}]),
            "unit_input_vs_306r_sanity_audit": unit_audit_in if not unit_audit_in.empty else pd.DataFrame([{"note": "no_input_unit_sanity_rows"}]),
            "duplicate_key_summary": dup_df if not dup_df.empty else pd.DataFrame([{"note": "duplicate_key_count_0"}]),
            "duplicate_key_detail": dup_detail if not dup_detail.empty else pd.DataFrame([{"note": "no_duplicate_key_rows"}]),
            "value_conflict_summary": conflict_df if not conflict_df.empty else pd.DataFrame([{"note": "value_conflict_count_0"}]),
        },
    )
    _write_excel(OUT_WARN_AUDIT, {"unit_warning_audit": warning_df})
    _write_excel(
        OUT_MISSING_PREVIEW,
        {"missing_candidate_unit_preview": norm_missing if not norm_missing.empty else pd.DataFrame([{"note": "no_missing_candidate_rows"}])},
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

    # Assert missing remain separate (no candidate_id in missing preview)
    missing_separate = bool(
        ("candidate_id" in norm_missing.columns) and norm_missing["candidate_id"].map(_norm).eq("").all()
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
        "stage": "EVAL-306S",
        "mode": "reviewed_projection_unit_normalization_gate",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "projection_input_count": projection_input_count,
        "projection_input_count_expected_306r": int(s_306r.get("reviewed_candidate_projection_count", 0)),
        "projection_input_count_matches_306r": bool(projection_input_count == int(s_306r.get("reviewed_candidate_projection_count", 0))),
        "normalized_projection_count": normalized_projection_count,
        "normalized_projection_count_matches_input": bool(normalized_projection_count == projection_input_count),
        "missing_candidate_unit_preview_count": int(len(norm_missing)),
        "missing_candidates_remain_separate": bool(missing_separate),
        "duplicate_key_count": duplicate_key_count,
        "value_conflict_count": value_conflict_count,
        "monetary_unit_unknown_warning_count": int((norm_proj.get("unit_warning", "").map(_norm).eq("monetary_unit_unknown").sum()) if not norm_proj.empty else 0),
        "forbidden_fields_generated": forbidden_fields_generated,
        "no_safe_to_apply_or_approve_for_real_apply_fields_generated": bool(len(forbidden_fields_generated) == 0),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "source_306r_stage": _norm(s_306r.get("stage", "")),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306S Reviewed Projection Unit Normalization Gate",
        "",
        "## Scope",
        "- Normalized units for 306R reviewed projection and missing-candidate preview.",
        "- Applied semantic defaults and monetary unknown warnings.",
        "- No apply operations and no production modifications.",
        "",
        "## Counts",
        f"- projection_input_count: {summary['projection_input_count']}",
        f"- normalized_projection_count: {summary['normalized_projection_count']}",
        f"- missing_candidate_unit_preview_count: {summary['missing_candidate_unit_preview_count']}",
        "",
        "## Assertions",
        f"- projection_input_count_matches_306r: {summary['projection_input_count_matches_306r']}",
        f"- normalized_projection_count_matches_input: {summary['normalized_projection_count_matches_input']}",
        f"- missing_candidates_remain_separate: {summary['missing_candidates_remain_separate']}",
        f"- duplicate_key_count: {summary['duplicate_key_count']}",
        f"- value_conflict_count: {summary['value_conflict_count']}",
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

    print(f"eval_306s_summary_json: {OUT_SUMMARY}")
    print(f"eval_306s_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

