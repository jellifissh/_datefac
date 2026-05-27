from __future__ import annotations

import hashlib
import json
import re
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
OUT_DIR = BASE_DIR / "output" / "eval_306l_fix_grouped_review_risk_rules"

IN_306L_SUMMARY = BASE_DIR / "output" / "eval_306l_grouped_human_review_package" / "306l_summary.json"
IN_306L_GROUPED = BASE_DIR / "output" / "eval_306l_grouped_human_review_package" / "306l_grouped_review_table.xlsx"
IN_306L_MAP = BASE_DIR / "output" / "eval_306l_grouped_human_review_package" / "306l_group_to_candidate_manifest.xlsx"
IN_306J_MANIFEST = BASE_DIR / "output" / "eval_306j_clean_candidate_human_review_input_design" / "306j_candidate_id_manifest.xlsx"
IN_306I_REVIEW = BASE_DIR / "output" / "eval_306i_clean_candidate_review_package" / "306i_clean_core_candidates_review.xlsx"

OUT_SUMMARY = OUT_DIR / "306l_fix_summary.json"
OUT_REPORT = OUT_DIR / "306l_fix_report.md"
OUT_GROUPED = OUT_DIR / "306l_fix_grouped_review_table.xlsx"
OUT_HIGH = OUT_DIR / "306l_fix_high_priority_review.xlsx"
OUT_MED = OUT_DIR / "306l_fix_medium_priority_review.xlsx"
OUT_LOW = OUT_DIR / "306l_fix_low_priority_auto_accept_candidates.xlsx"
OUT_BLOCKED = OUT_DIR / "306l_fix_blocked_auto_accept_candidates.xlsx"
OUT_MAP = OUT_DIR / "306l_fix_group_to_candidate_manifest.xlsx"
OUT_RULES = OUT_DIR / "306l_fix_risk_rules.json"
OUT_NO_APPLY = OUT_DIR / "306l_fix_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

YEAR_COLS = [str(y) for y in range(2020, 2031)]
CORE_METRICS = {
    "revenue",
    "net_profit",
    "attributable_net_profit",
    "gross_margin",
    "roe",
    "eps",
    "pe",
    "pb",
    "ev_ebitda",
    "operating_cash_flow",
    "total_assets",
    "total_liabilities",
}
VALUATION_METRICS = {"pe", "pb", "ev_ebitda"}
PERCENT_METRICS = {"gross_margin", "roe"}

NUMERIC_RE = re.compile(r"^\(?-?\d[\d,]*(?:\.\d+)?\)?%?$")
FRAGMENT_RE = re.compile(r"^\.\d+%?$")
HAS_CN_RE = re.compile(r"[\u4e00-\u9fff]")
ALPHA_NUM_RE = re.compile(r"(?=.*[A-Za-z])(?=.*\d)")


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


def _split_cell_values(cell: Any) -> List[str]:
    s = _norm(cell)
    if s == "":
        return []
    return [p.strip() for p in s.split("|") if p.strip()]


def _is_clean_numeric_token(token: str) -> bool:
    if token == "":
        return False
    return bool(NUMERIC_RE.fullmatch(token))


def _row_diagnostics(row: pd.Series) -> Dict[str, Any]:
    metric = _norm(row.get("标准指标")).lower()
    unit = _norm(row.get("单位")).lower()
    parser = _norm(row.get("来源解析器")).lower()

    year_tokens: Dict[int, List[str]] = {}
    all_tokens: List[str] = []
    for yc in YEAR_COLS:
        parts = _split_cell_values(row.get(yc, ""))
        if parts:
            year_tokens[int(yc)] = parts
            all_tokens.extend(parts)

    years_present = sorted(year_tokens.keys())
    has_year_gap = False
    if years_present:
        full = set(range(min(years_present), max(years_present) + 1))
        has_year_gap = len(full.difference(set(years_present))) > 0

    contains_chinese = any(HAS_CN_RE.search(t) for t in all_tokens)
    contains_alpha_num = any(ALPHA_NUM_RE.search(t) for t in all_tokens)
    contains_fragment = any(FRAGMENT_RE.fullmatch(t) for t in all_tokens)
    numeric_all = len(all_tokens) > 0 and all(_is_clean_numeric_token(t) for t in all_tokens)
    has_percent_token = any("%" in t for t in all_tokens)
    inconsistent_percent = False
    if metric in PERCENT_METRICS or unit == "%":
        if len(all_tokens) > 0:
            with_pct = sum(1 for t in all_tokens if "%" in t)
            inconsistent_percent = 0 < with_pct < len(all_tokens)

    # prose-like: long non-numeric chunk with punctuation/space or very long token
    prose_like = any(
        (not _is_clean_numeric_token(t))
        and (len(t) >= 8 or " " in t or "，" in t or "," in t and HAS_CN_RE.search(t))
        for t in all_tokens
    )

    obvious_pdfplumber_noise = (
        parser == "pdfplumber"
        and (
            contains_chinese
            or contains_alpha_num
            or contains_fragment
            or inconsistent_percent
            or prose_like
            or (not numeric_all)
            or has_year_gap
        )
    )

    is_core_metric = metric in CORE_METRICS
    unit_unknown = _to_bool(row.get("unit_unknown", False))
    valuation_unit_unknown_allowed = metric in VALUATION_METRICS and numeric_all

    return {
        "metric": metric,
        "parser": parser,
        "years_present_list": years_present,
        "has_year_gap": has_year_gap,
        "contains_chinese": contains_chinese,
        "contains_alpha_num": contains_alpha_num,
        "contains_fragment": contains_fragment,
        "inconsistent_percent": inconsistent_percent,
        "prose_like": prose_like,
        "numeric_all": numeric_all,
        "has_percent_token": has_percent_token,
        "obvious_pdfplumber_noise": obvious_pdfplumber_noise,
        "is_core_metric": is_core_metric,
        "unit_unknown": unit_unknown,
        "valuation_unit_unknown_allowed": valuation_unit_unknown_allowed,
    }


def _decide_priority(row: pd.Series, dx: Dict[str, Any]) -> Tuple[str, bool, List[str]]:
    reasons: List[str] = []
    blocked_auto_accept = False
    prio_rank = 2  # 0 HIGH, 1 MEDIUM, 2 LOW

    def raise_to(level: str) -> None:
        nonlocal prio_rank
        target = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[level]
        prio_rank = min(prio_rank, target)

    # hard data-quality blockers
    if dx["contains_chinese"]:
        reasons.append("value_contains_chinese_text")
        raise_to("HIGH")
        blocked_auto_accept = True
    if dx["contains_alpha_num"]:
        reasons.append("value_contains_alpha_num_mix")
        raise_to("HIGH")
        blocked_auto_accept = True
    if dx["prose_like"]:
        reasons.append("value_contains_prose_fragment")
        raise_to("HIGH")
        blocked_auto_accept = True
    if dx["contains_fragment"]:
        reasons.append("fragmented_value_detected")
        raise_to("HIGH")
        blocked_auto_accept = True
    if dx["inconsistent_percent"]:
        reasons.append("inconsistent_percent_format")
        raise_to("HIGH")
        blocked_auto_accept = True

    # required raises
    if _to_bool(row.get("multi_panel_source", False)):
        reasons.append("multi_panel_source_high_risk")
        raise_to("HIGH")
    if _to_bool(row.get("zero_candidate_rescued", False)):
        reasons.append("zero_candidate_rescued_high_risk")
        raise_to("HIGH")
    if _to_bool(row.get("alias_recovered", False)):
        reasons.append("alias_recovered_high_risk")
        raise_to("HIGH")

    # missing year gap must be flagged and not LOW
    if dx["has_year_gap"]:
        reasons.append("missing_year_gap_detected")
        raise_to("MEDIUM")

    # small candidate core metric should not be LOW
    candidate_count = _to_int(row.get("candidate_count", 0))
    if dx["is_core_metric"] and candidate_count <= 2:
        reasons.append("core_metric_low_candidate_count")
        raise_to("MEDIUM")

    # unit_unknown for core metrics (except clean valuation metrics)
    if dx["is_core_metric"] and dx["unit_unknown"] and (not dx["valuation_unit_unknown_allowed"]):
        reasons.append("core_metric_unit_unknown_not_allowed_for_low")
        raise_to("MEDIUM")

    # pdfplumber low guard
    if dx["parser"] == "pdfplumber":
        if dx["obvious_pdfplumber_noise"]:
            reasons.append("pdfplumber_noise_not_allowed_for_low")
            if blocked_auto_accept:
                raise_to("HIGH")
            else:
                raise_to("MEDIUM")
        elif (not dx["numeric_all"]) or dx["has_year_gap"]:
            reasons.append("pdfplumber_not_clean_or_non_continuous")
            raise_to("MEDIUM")

    priority = {0: "HIGH", 1: "MEDIUM", 2: "LOW"}[prio_rank]
    return priority, blocked_auto_accept, reasons


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [IN_306L_SUMMARY, IN_306L_GROUPED, IN_306L_MAP, IN_306J_MANIFEST, IN_306I_REVIEW]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "EVAL-306L-FIX",
                "mode": "grouped_review_risk_rules_fix",
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

    old_summary = json.loads(IN_306L_SUMMARY.read_text(encoding="utf-8"))
    grouped = pd.read_excel(IN_306L_GROUPED).fillna("")
    gmap = pd.read_excel(IN_306L_MAP).fillna("")
    cand_manifest = pd.read_excel(IN_306J_MANIFEST).fillna("")
    clean_review = pd.read_excel(IN_306I_REVIEW).fillna("")

    # mapping integrity checks against candidate manifest / review source
    gmap["candidate_id"] = gmap["candidate_id"].map(_norm)
    cand_manifest["candidate_id"] = cand_manifest["candidate_id"].map(_norm)
    manifest_id_set = set(cand_manifest["candidate_id"].tolist())
    review_id_set = set(cand_manifest["candidate_id"].tolist())
    map_id_set = set(gmap["candidate_id"].tolist())

    map_missing_from_manifest = sorted(list(map_id_set.difference(manifest_id_set)))
    map_extra_vs_manifest = sorted(list(manifest_id_set.difference(map_id_set)))

    # risk recomputation
    out_rows: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        rec = row.to_dict()
        dx = _row_diagnostics(row)
        priority, blocked_auto, reasons = _decide_priority(row, dx)

        rec["missing_year"] = bool(dx["has_year_gap"])
        rec["review_priority"] = priority
        rec["risk_reasons"] = ";".join(reasons)
        rec["blocked_auto_accept"] = bool(blocked_auto)
        rec["contains_chinese_value"] = bool(dx["contains_chinese"])
        rec["contains_alpha_num_value"] = bool(dx["contains_alpha_num"])
        rec["contains_fragmented_value"] = bool(dx["contains_fragment"])
        rec["contains_inconsistent_percent"] = bool(dx["inconsistent_percent"])
        rec["contains_prose_value"] = bool(dx["prose_like"])
        rec["numeric_values_clean"] = bool(dx["numeric_all"])
        rec["obvious_pdfplumber_noise"] = bool(dx["obvious_pdfplumber_noise"])
        rec["years_continuous"] = not bool(dx["has_year_gap"])
        out_rows.append(rec)

    out_df = pd.DataFrame(out_rows).fillna("")
    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    out_df["_prio_rank"] = out_df["review_priority"].map(lambda x: priority_rank.get(_norm(x), 9))
    out_df = out_df.sort_values(
        ["_prio_rank", "PDF文件名", "标准指标", "指标名", "source_panel_id"],
        ascending=[True, True, True, True, True],
    ).drop(columns=["_prio_rank"])

    high_df = out_df[out_df["review_priority"] == "HIGH"].copy()
    med_df = out_df[out_df["review_priority"] == "MEDIUM"].copy()
    low_df = out_df[out_df["review_priority"] == "LOW"].copy()
    blocked_df = out_df[out_df["blocked_auto_accept"]].copy()

    if high_df.empty:
        high_df = pd.DataFrame([{"note": "no_high_priority_group"}])
    if med_df.empty:
        med_df = pd.DataFrame([{"note": "no_medium_priority_group"}])
    if low_df.empty:
        low_df = pd.DataFrame([{"note": "no_low_priority_group"}])
    if blocked_df.empty:
        blocked_df = pd.DataFrame([{"note": "no_blocked_auto_accept_group"}])

    _write_excel(
        OUT_GROUPED,
        {
            "grouped_review_table": out_df,
            "priority_distribution": out_df.groupby("review_priority", dropna=False).size().reset_index(name="group_count"),
            "risk_reason_distribution": (
                out_df.assign(risk_reason_item=out_df["risk_reasons"].map(_norm))
                .assign(risk_reason_item=lambda d: d["risk_reason_item"].str.split(";"))
                .explode("risk_reason_item")
                .assign(risk_reason_item=lambda d: d["risk_reason_item"].map(_norm))
                .query("risk_reason_item != ''")
                .groupby("risk_reason_item", dropna=False)
                .size()
                .reset_index(name="group_count")
                .sort_values("group_count", ascending=False)
            ),
        },
    )
    _write_excel(OUT_HIGH, {"high_priority_review": high_df})
    _write_excel(OUT_MED, {"medium_priority_review": med_df})
    _write_excel(OUT_LOW, {"low_priority_auto_accept_candidates": low_df})
    _write_excel(OUT_BLOCKED, {"blocked_auto_accept_candidates": blocked_df})
    _write_excel(OUT_MAP, {"group_to_candidate_manifest": gmap})

    low_cn_count = int(low_df["contains_chinese_value"].map(_to_bool).sum()) if "contains_chinese_value" in low_df.columns else 0
    low_frag_count = int(low_df["contains_fragmented_value"].map(_to_bool).sum()) if "contains_fragmented_value" in low_df.columns else 0
    low_pdf_noise_count = int(low_df["obvious_pdfplumber_noise"].map(_to_bool).sum()) if "obvious_pdfplumber_noise" in low_df.columns else 0
    gap_rows = out_df[out_df["years_continuous"].map(_to_bool) == False].copy()  # noqa: E712
    missing_year_gap_flag_ok = bool(
        len(gap_rows) == 0 or gap_rows["missing_year"].map(_to_bool).all()
    )

    _write_json(
        OUT_RULES,
        {
            "version": "306l_fix_v1",
            "policy_notes": [
                "LOW excludes chinese/mixed/prose values, fragmented values, and percent-format anomalies.",
                "LOW excludes noisy pdfplumber groups unless values are clean numeric and years are continuous.",
                "multi_panel_source / zero_candidate_rescued / alias_recovered always escalated to HIGH.",
                "core metric with candidate_count <= 2 escalated to at least MEDIUM.",
                "missing year gaps are explicitly detected and flagged.",
            ],
            "core_metrics": sorted(CORE_METRICS),
            "valuation_metrics_exception_for_unit_unknown": sorted(VALUATION_METRICS),
            "assertions": {
                "low_chinese_text_count": low_cn_count,
                "low_fragmented_value_count": low_frag_count,
                "low_obvious_pdfplumber_noise_count": low_pdf_noise_count,
                "missing_year_gap_flag_ok": missing_year_gap_flag_ok,
            },
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

    summary = {
        "stage": "EVAL-306L-FIX",
        "mode": "grouped_review_risk_rules_fix",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "pdfplumber_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "old_grouped_review_row_count": int(_to_int(old_summary.get("grouped_review_row_count", 0))),
        "source_candidate_row_count": int(len(clean_review)),
        "grouped_review_row_count": int(len(out_df)),
        "high_priority_group_count": int((out_df["review_priority"] == "HIGH").sum()),
        "medium_priority_group_count": int((out_df["review_priority"] == "MEDIUM").sum()),
        "low_priority_group_count": int((out_df["review_priority"] == "LOW").sum()),
        "blocked_auto_accept_group_count": int((out_df["blocked_auto_accept"].map(_to_bool)).sum()),
        "low_priority_chinese_text_year_value_count": low_cn_count,
        "low_priority_fragmented_value_count": low_frag_count,
        "low_priority_obvious_pdfplumber_noise_count": low_pdf_noise_count,
        "missing_year_gap_group_count": int(len(gap_rows)),
        "missing_year_gap_flag_ok": missing_year_gap_flag_ok,
        "group_to_candidate_mapping_row_count": int(len(gmap)),
        "group_to_candidate_unique_candidate_count": int(gmap["candidate_id"].map(_norm).nunique()),
        "group_to_candidate_manifest_maps_all_372_candidates": bool(len(map_id_set) == 372 and len(gmap) == 372),
        "mapping_missing_from_306j_manifest_count": int(len(map_missing_from_manifest)),
        "mapping_extra_vs_306j_manifest_count": int(len(map_extra_vs_manifest)),
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 306L-Fix Grouped Review Risk Rules",
        "",
        "## Scope",
        "- Recomputed grouped review risk flags and priorities using existing 306L grouped table only.",
        "- No rerun of Marker/pdfplumber. No API/LLM/OCR calls. No production changes.",
        "",
        "## Priority Distribution",
        f"- HIGH: {summary['high_priority_group_count']}",
        f"- MEDIUM: {summary['medium_priority_group_count']}",
        f"- LOW: {summary['low_priority_group_count']}",
        f"- blocked_auto_accept_group_count: {summary['blocked_auto_accept_group_count']}",
        "",
        "## Required Assertions",
        f"- LOW rows with Chinese text in year values: {summary['low_priority_chinese_text_year_value_count']}",
        f"- LOW rows with fragmented values: {summary['low_priority_fragmented_value_count']}",
        f"- LOW rows with obvious pdfplumber noise: {summary['low_priority_obvious_pdfplumber_noise_count']}",
        f"- missing_year=true for year-gap groups: {summary['missing_year_gap_flag_ok']}",
        f"- group_to_candidate_manifest maps all 372 candidates: {summary['group_to_candidate_manifest_maps_all_372_candidates']}",
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

    print(f"eval_306l_fix_summary_json: {OUT_SUMMARY}")
    print(f"eval_306l_fix_report_md: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

