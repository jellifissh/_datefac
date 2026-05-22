import argparse
import hashlib
import json
import re
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import financial_standardizer as fs


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

STAGE5F_DIR = OUTPUT_DIR / "stage5f_raw_metric_extraction_fix"
INPUT_IMPROVED_02_XLSX = STAGE5F_DIR / "136_stage5f_improved_structured_02.xlsx"
INPUT_IMPROVED_PREVIEW_XLSX = STAGE5F_DIR / "136_stage5f_improved_standardization_preview.xlsx"
INPUT_STAGE5F_REPORT_XLSX = STAGE5F_DIR / "136_stage5f_raw_metric_extraction_fix_report.xlsx"
INPUT_STAGE5F_SUMMARY_JSON = STAGE5F_DIR / "137_stage5f_raw_metric_extraction_fix_summary.json"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5g_remaining_mapping_miss_analysis"
OUT_XLSX = OUT_DIR / "138_stage5g_remaining_mapping_miss_analysis.xlsx"
OUT_MD = OUT_DIR / "138_stage5g_remaining_mapping_miss_analysis.md"
OUT_JSON = OUT_DIR / "139_stage5g_remaining_mapping_miss_summary.json"

CATEGORIES = {
    "TRUE_MAPPING_GAP",
    "ALIAS_MISSING",
    "NORMALIZATION_DEPENDENT",
    "PACKAGE_SPECIFIC_METRIC",
    "DERIVED_METRIC_NOT_SUPPORTED",
    "NON_CORE_METRIC",
    "LOW_VALUE_NO_ACTION",
    "RAW_EXTRACTION_STILL_DIRTY",
    "HEADER_OR_METADATA_ROW",
    "UNKNOWN",
}

ACTIONS = {
    "DRAFT_MAPPING_RULE",
    "DRAFT_ALIAS_RULE",
    "DEFER_PACKAGE_SPECIFIC_RULE",
    "DEFER_DERIVED_METRIC_RULE",
    "FILTER_NON_CORE_METRIC",
    "FIX_RAW_EXTRACTION_AGAIN",
    "NEED_MANUAL_REVIEW",
    "NO_ACTION",
}

PRIORITIES = {"HIGH", "MEDIUM", "LOW"}
CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}

HEADER_TERMS = ["资料来源", "证券研究报告", "敬请参阅", "免责声明", "请务必阅读"]
DERIVED_TERMS = ["(%)", "%", "周转率", "ROIC", "资产负债率", "净利率", "增长率", "同比", "增速"]
NON_CORE_TERMS = ["营业利润", "净利润", "EBITDA", "周转率", "ROIC", "资产负债率", "净利率"]
LOW_VALUE_TERMS = ["其他", "合计", "小计", "总计"]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    t = _norm(v).replace("（", "(").replace("）", ")").replace("／", "/")
    return re.sub(r"\s+", "", t).upper()


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31-len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_delivery_file(pattern: str) -> Path:
    files = sorted(DELIVERY_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Missing delivery file pattern: {pattern}")
    non_copy = [p for p in files if "_copy_" not in p.name.lower()]
    return non_copy[0] if non_copy else files[0]


def _snapshot_hashes() -> Dict[str, str]:
    return {
        "01": _sha256(_find_delivery_file("01_*.xlsx")),
        "02": _sha256(_find_delivery_file("02_*.xlsx")),
        "02A": _sha256(_find_delivery_file("02A_*.xlsx")),
        "05": _sha256(_find_delivery_file("05_*.xlsx")),
        "06": _sha256(_find_delivery_file("06_*.xlsx")),
        "02B": _sha256(OFFICIAL_02B_PATH),
        "formal_scope_rules": _sha256(FORMAL_SCOPE_RULES_JSON),
        "formal_mapping_rules": _sha256(FORMAL_MAPPING_RULE_FILE),
        "formal_normalization_rules": _sha256(FORMAL_NORMALIZATION_RULE_FILE),
    }


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True, check=False)
    text = (p.stdout or "").strip()
    if not text:
        return {"overall_status": "UNKNOWN"}
    return json.loads(text)


def _metric_pool() -> List[Tuple[str, str]]:
    pool = []
    for std, aliases in fs.STANDARD_METRIC_ALIASES.items():
        pool.append((_norm(std), _norm(std)))
        for a in aliases:
            pool.append((_norm(a), _norm(std)))
    uniq: List[Tuple[str, str]] = []
    seen = set()
    for a, s in pool:
        k = (_compact(a), _compact(s))
        if k in seen:
            continue
        seen.add(k)
        uniq.append((a, s))
    return uniq


def _nearest_metric(raw_clean: str, pool: List[Tuple[str, str]]) -> Tuple[str, str, float]:
    rc = _compact(raw_clean)
    if not rc:
        return "", "", 0.0
    best_std = ""
    best_alias = ""
    best = 0.0
    for alias, std in pool:
        ac = _compact(alias)
        if not ac:
            continue
        score = SequenceMatcher(None, rc, ac).ratio()
        if ac.startswith(rc) or rc.startswith(ac):
            score = max(score, 0.75 if len(rc) >= 2 else score)
        if score > best:
            best = score
            best_alias = alias
            best_std = std
    return best_std, best_alias, round(float(best), 4)


def _mapping_rule_id(metric: str) -> str:
    m = _norm(metric)
    if not m:
        return ""
    return f"FS_MAP_{_compact(m)}"


def _clean_raw_metric(raw: str) -> str:
    x = fs._clean_metric_label_noise(_norm(raw))
    x = x.replace("（", "(").replace("）", ")").replace("／", "/")
    x = re.sub(r"\s+", "", x)
    return x


def _classify_record(
    raw_metric_name: str,
    raw_metric_name_cleaned: str,
    statement_type: str,
    nearest_std: str,
    nearest_alias: str,
    similarity: float,
) -> Tuple[str, str, str, str, str, str]:
    raw = _norm(raw_metric_name)
    cleaned = _norm(raw_metric_name_cleaned)
    st = _norm(statement_type)

    # category, root_cause, action, priority, confidence, evidence
    if not cleaned:
        return (
            "RAW_EXTRACTION_STILL_DIRTY",
            "raw metric empty after cleaning",
            "FIX_RAW_EXTRACTION_AGAIN",
            "HIGH",
            "HIGH",
            "cleaned metric empty",
        )
    if any(x in cleaned for x in HEADER_TERMS):
        return (
            "HEADER_OR_METADATA_ROW",
            "header/metadata row still entered standardization path",
            "FIX_RAW_EXTRACTION_AGAIN",
            "HIGH",
            "HIGH",
            "header/meta keywords detected",
        )
    if any(x in cleaned for x in LOW_VALUE_TERMS):
        return (
            "LOW_VALUE_NO_ACTION",
            "low-value generic row not useful for core standardization",
            "NO_ACTION",
            "LOW",
            "HIGH",
            "generic low-value term",
        )
    if len(cleaned) <= 2:
        return (
            "RAW_EXTRACTION_STILL_DIRTY",
            "metric name too short, likely truncated or split artifact",
            "FIX_RAW_EXTRACTION_AGAIN",
            "HIGH",
            "HIGH",
            "short token length<=2",
        )
    if "每股收益" in cleaned and "摊薄" in cleaned:
        return (
            "ALIAS_MISSING",
            "core metric variant present but alias list may not cover this expression",
            "DRAFT_ALIAS_RULE",
            "HIGH",
            "HIGH",
            f"nearest={nearest_std}/{nearest_alias} score={similarity}",
        )
    if any(x in cleaned for x in DERIVED_TERMS):
        return (
            "DERIVED_METRIC_NOT_SUPPORTED",
            "derived ratio/growth metric outside current core direct mapping scope",
            "DEFER_DERIVED_METRIC_RULE",
            "MEDIUM",
            "HIGH",
            "derived metric keyword detected",
        )
    if any(x in cleaned for x in NON_CORE_TERMS):
        return (
            "NON_CORE_METRIC",
            "non-core metric not prioritized in current standardization scope",
            "FILTER_NON_CORE_METRIC",
            "LOW",
            "MEDIUM",
            "non-core metric keyword detected",
        )
    if similarity >= 0.78 and nearest_std:
        return (
            "NORMALIZATION_DEPENDENT",
            "close to existing alias but may need normalization/alias refinement",
            "DRAFT_ALIAS_RULE",
            "MEDIUM",
            "MEDIUM",
            f"nearest={nearest_std}/{nearest_alias} score={similarity}",
        )
    if st and st not in {"利润表", "资产负债表", "现金流量表", "财务比率表"}:
        return (
            "PACKAGE_SPECIFIC_METRIC",
            "statement_type indicates scoped/package-specific metric interpretation",
            "DEFER_PACKAGE_SPECIFIC_RULE",
            "MEDIUM",
            "LOW",
            f"statement_type={st}",
        )
    if cleaned:
        return (
            "TRUE_MAPPING_GAP",
            "metric-like row still unmatched after extraction cleanup",
            "DRAFT_MAPPING_RULE",
            "MEDIUM",
            "LOW",
            f"nearest={nearest_std}/{nearest_alias} score={similarity}",
        )
    return (
        "UNKNOWN",
        "insufficient signal for robust classification",
        "NEED_MANUAL_REVIEW",
        "LOW",
        "LOW",
        "fallback",
    )


def _safe_value(value: str, enum_set: set, fallback: str) -> str:
    v = _norm(value)
    return v if v in enum_set else fallback


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5G analyze remaining mapping misses after stage5f.")
    parser.parse_args()

    required = [
        INPUT_IMPROVED_02_XLSX,
        INPUT_IMPROVED_PREVIEW_XLSX,
        INPUT_STAGE5F_REPORT_XLSX,
        INPUT_STAGE5F_SUMMARY_JSON,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_NORMALIZATION_RULE_FILE,
        OFFICIAL_02B_PATH,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    # load improved preview, robust to sheet name truncation
    xl = pd.ExcelFile(INPUT_IMPROVED_PREVIEW_XLSX)
    main_sheet = xl.sheet_names[0]
    df_preview = pd.read_excel(INPUT_IMPROVED_PREVIEW_XLSX, sheet_name=main_sheet).fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")
    stage5f_summary = json.loads(INPUT_STAGE5F_SUMMARY_JSON.read_text(encoding="utf-8"))

    input_improved_standardization_row_count = int(len(df_preview))
    miss_df = df_preview[df_preview["standardization_status"].map(_norm) == "MAPPING_MISS"].copy()
    input_remaining_mapping_miss_count = int(len(miss_df))

    pool = _metric_pool()
    rows: List[Dict[str, Any]] = []
    for _, r in miss_df.iterrows():
        raw_metric_name = _norm(r.get("raw_metric_name"))
        raw_metric_name_cleaned = _clean_raw_metric(raw_metric_name)
        nearest_std, nearest_alias, sim = _nearest_metric(raw_metric_name_cleaned, pool)

        cat, root_cause, action, priority, conf, evidence = _classify_record(
            raw_metric_name=raw_metric_name,
            raw_metric_name_cleaned=raw_metric_name_cleaned,
            statement_type=_norm(r.get("statement_type")),
            nearest_std=nearest_std,
            nearest_alias=nearest_alias,
            similarity=sim,
        )

        cat = _safe_value(cat, CATEGORIES, "UNKNOWN")
        action = _safe_value(action, ACTIONS, "NEED_MANUAL_REVIEW")
        priority = _safe_value(priority, PRIORITIES, "LOW")
        conf = _safe_value(conf, CONFIDENCE, "LOW")

        rows.append(
            {
                "row_trace_id": _norm(r.get("row_trace_id")),
                "source_pdf": _norm(r.get("source_pdf")),
                "source_page": _norm(r.get("source_page")),
                "source_table_id": _norm(r.get("source_table_id")),
                "raw_metric_name": raw_metric_name,
                "raw_metric_name_cleaned": raw_metric_name_cleaned,
                "year": _norm(r.get("year")),
                "value": _norm(r.get("value")),
                "unit": _norm(r.get("unit")),
                "statement_type": _norm(r.get("statement_type")),
                "asset_package": _norm(r.get("asset_package")),
                "source_reference": _norm(r.get("source_reference")),
                "nearest_existing_standard_metric": nearest_std,
                "nearest_existing_mapping_rule_id": _mapping_rule_id(nearest_std),
                "similarity_score": sim,
                "remaining_miss_category": cat,
                "root_cause": root_cause,
                "recommended_action": action,
                "priority_level": priority,
                "confidence_level": conf,
                "evidence": evidence,
            }
        )

    out_df = pd.DataFrame(rows)
    analyzed_remaining_mapping_miss_count = int(len(out_df))

    # Group stats
    by_raw_df = (
        out_df.groupby("raw_metric_name_cleaned", dropna=False).size().reset_index(name="count")
        .sort_values(["count", "raw_metric_name_cleaned"], ascending=[False, True], kind="mergesort")
    ) if not out_df.empty else pd.DataFrame(columns=["raw_metric_name_cleaned", "count"])
    by_table_df = (
        out_df.groupby("source_table_id", dropna=False).size().reset_index(name="count")
        .sort_values(["count", "source_table_id"], ascending=[False, True], kind="mergesort")
    ) if not out_df.empty else pd.DataFrame(columns=["source_table_id", "count"])
    by_statement_df = (
        out_df.groupby("statement_type", dropna=False).size().reset_index(name="count")
        .sort_values(["count", "statement_type"], ascending=[False, True], kind="mergesort")
    ) if not out_df.empty else pd.DataFrame(columns=["statement_type", "count"])
    by_category_df = (
        out_df.groupby("remaining_miss_category", dropna=False).size().reset_index(name="count")
        .sort_values(["count", "remaining_miss_category"], ascending=[False, True], kind="mergesort")
    ) if not out_df.empty else pd.DataFrame(columns=["remaining_miss_category", "count"])
    top_raw_df = by_raw_df.head(50).copy()

    stage5h_candidates_df = (
        out_df[out_df["recommended_action"].isin(["DRAFT_MAPPING_RULE", "DRAFT_ALIAS_RULE"])].copy()
        .sort_values(["priority_level", "similarity_score"], ascending=[True, False], kind="mergesort")
        if not out_df.empty else pd.DataFrame(columns=out_df.columns)
    )

    def _cat_count(name: str) -> int:
        if out_df.empty:
            return 0
        return int((out_df["remaining_miss_category"] == name).sum())

    def _act_count(name: str) -> int:
        if out_df.empty:
            return 0
        return int((out_df["recommended_action"] == name).sum())

    true_mapping_gap_count = _cat_count("TRUE_MAPPING_GAP")
    alias_missing_count = _cat_count("ALIAS_MISSING")
    normalization_dependent_count = _cat_count("NORMALIZATION_DEPENDENT")
    package_specific_metric_count = _cat_count("PACKAGE_SPECIFIC_METRIC")
    derived_metric_not_supported_count = _cat_count("DERIVED_METRIC_NOT_SUPPORTED")
    non_core_metric_count = _cat_count("NON_CORE_METRIC")
    low_value_no_action_count = _cat_count("LOW_VALUE_NO_ACTION")
    raw_extraction_still_dirty_count = _cat_count("RAW_EXTRACTION_STILL_DIRTY")
    header_or_metadata_row_count = _cat_count("HEADER_OR_METADATA_ROW")
    unknown_count = _cat_count("UNKNOWN")

    draft_mapping_rule_candidate_count = _act_count("DRAFT_MAPPING_RULE")
    draft_alias_rule_candidate_count = _act_count("DRAFT_ALIAS_RULE")
    filter_non_core_metric_count = _act_count("FILTER_NON_CORE_METRIC")
    fix_raw_extraction_again_count = _act_count("FIX_RAW_EXTRACTION_AGAIN")
    need_manual_review_count = _act_count("NEED_MANUAL_REVIEW")

    high_priority_count = int((out_df["priority_level"] == "HIGH").sum()) if not out_df.empty else 0
    medium_priority_count = int((out_df["priority_level"] == "MEDIUM").sum()) if not out_df.empty else 0
    low_priority_count = int((out_df["priority_level"] == "LOW").sum()) if not out_df.empty else 0

    after = _snapshot_hashes()
    production_files_unchanged = bool(
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02B_unchanged = bool(before["02B"] == after["02B"])
    formal_scope_rules_unchanged = bool(before["formal_scope_rules"] == after["formal_scope_rules"])
    formal_mapping_rules_unchanged = bool(before["formal_mapping_rules"] == after["formal_mapping_rules"])
    formal_normalization_rules_unchanged = bool(before["formal_normalization_rules"] == after["formal_normalization_rules"])

    summary = {
        "input_improved_standardization_row_count": int(input_improved_standardization_row_count),
        "input_remaining_mapping_miss_count": int(input_remaining_mapping_miss_count),
        "analyzed_remaining_mapping_miss_count": int(analyzed_remaining_mapping_miss_count),
        "true_mapping_gap_count": int(true_mapping_gap_count),
        "alias_missing_count": int(alias_missing_count),
        "normalization_dependent_count": int(normalization_dependent_count),
        "package_specific_metric_count": int(package_specific_metric_count),
        "derived_metric_not_supported_count": int(derived_metric_not_supported_count),
        "non_core_metric_count": int(non_core_metric_count),
        "low_value_no_action_count": int(low_value_no_action_count),
        "raw_extraction_still_dirty_count": int(raw_extraction_still_dirty_count),
        "header_or_metadata_row_count": int(header_or_metadata_row_count),
        "unknown_count": int(unknown_count),
        "draft_mapping_rule_candidate_count": int(draft_mapping_rule_candidate_count),
        "draft_alias_rule_candidate_count": int(draft_alias_rule_candidate_count),
        "filter_non_core_metric_count": int(filter_non_core_metric_count),
        "fix_raw_extraction_again_count": int(fix_raw_extraction_again_count),
        "need_manual_review_count": int(need_manual_review_count),
        "high_priority_count": int(high_priority_count),
        "medium_priority_count": int(medium_priority_count),
        "low_priority_count": int(low_priority_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5g_remaining_mapping_miss_analysis_pass": False,
    }

    category_sum_guard = (
        summary["true_mapping_gap_count"]
        + summary["alias_missing_count"]
        + summary["normalization_dependent_count"]
        + summary["package_specific_metric_count"]
        + summary["derived_metric_not_supported_count"]
        + summary["non_core_metric_count"]
        + summary["low_value_no_action_count"]
        + summary["raw_extraction_still_dirty_count"]
        + summary["header_or_metadata_row_count"]
        + summary["unknown_count"]
    )

    summary["stage5g_remaining_mapping_miss_analysis_pass"] = bool(
        summary["input_remaining_mapping_miss_count"] == 85
        and summary["analyzed_remaining_mapping_miss_count"] == 85
        and category_sum_guard > 0
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_scope_rules_unchanged"]
        and summary["formal_mapping_rules_unchanged"]
        and summary["formal_normalization_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    _write_excel(
        OUT_XLSX,
        {
            "remaining_mapping_miss_inventory": out_df,
            "by_raw_metric_name_cleaned": by_raw_df,
            "by_source_table_id": by_table_df,
            "by_statement_type": by_statement_df,
            "by_remaining_miss_category": by_category_df,
            "top_raw_metric_name": top_raw_df,
            "stage5h_candidates": stage5h_candidates_df,
            "summary": pd.DataFrame([summary]),
            "stage5f_summary_ref": pd.DataFrame([stage5f_summary]),
        },
    )

    md_lines = [
        "# Stage5G Remaining Mapping Miss Analysis",
        "",
        f"- input_improved_standardization_row_count: {summary['input_improved_standardization_row_count']}",
        f"- input_remaining_mapping_miss_count: {summary['input_remaining_mapping_miss_count']}",
        f"- analyzed_remaining_mapping_miss_count: {summary['analyzed_remaining_mapping_miss_count']}",
        f"- true_mapping_gap_count: {summary['true_mapping_gap_count']}",
        f"- alias_missing_count: {summary['alias_missing_count']}",
        f"- normalization_dependent_count: {summary['normalization_dependent_count']}",
        f"- package_specific_metric_count: {summary['package_specific_metric_count']}",
        f"- derived_metric_not_supported_count: {summary['derived_metric_not_supported_count']}",
        f"- non_core_metric_count: {summary['non_core_metric_count']}",
        f"- low_value_no_action_count: {summary['low_value_no_action_count']}",
        f"- raw_extraction_still_dirty_count: {summary['raw_extraction_still_dirty_count']}",
        f"- header_or_metadata_row_count: {summary['header_or_metadata_row_count']}",
        f"- unknown_count: {summary['unknown_count']}",
        f"- draft_mapping_rule_candidate_count: {summary['draft_mapping_rule_candidate_count']}",
        f"- draft_alias_rule_candidate_count: {summary['draft_alias_rule_candidate_count']}",
        f"- filter_non_core_metric_count: {summary['filter_non_core_metric_count']}",
        f"- fix_raw_extraction_again_count: {summary['fix_raw_extraction_again_count']}",
        f"- need_manual_review_count: {summary['need_manual_review_count']}",
        f"- high_priority_count: {summary['high_priority_count']}",
        f"- medium_priority_count: {summary['medium_priority_count']}",
        f"- low_priority_count: {summary['low_priority_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- stage5g_remaining_mapping_miss_analysis_pass: {summary['stage5g_remaining_mapping_miss_analysis_pass']}",
    ]
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5g_analysis_xlsx: {OUT_XLSX}")
    print(f"stage5g_analysis_md: {OUT_MD}")
    print(f"stage5g_summary_json: {OUT_JSON}")
    print(f"input_remaining_mapping_miss_count: {summary['input_remaining_mapping_miss_count']}")
    print(f"analyzed_remaining_mapping_miss_count: {summary['analyzed_remaining_mapping_miss_count']}")
    print(f"stage5g_remaining_mapping_miss_analysis_pass: {summary['stage5g_remaining_mapping_miss_analysis_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
