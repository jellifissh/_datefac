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

STAGE5D_DIR = OUTPUT_DIR / "stage5d_standardize_sandbox_02_to_05"
STAGE5C_DIR = OUTPUT_DIR / "stage5c_raw_tables_to_structured_02"

INPUT_05_XLSX = STAGE5D_DIR / "132_stage5d_sandbox_05_standardized.xlsx"
INPUT_05_REPORT_XLSX = STAGE5D_DIR / "132_stage5d_standardization_report.xlsx"
INPUT_05_SUMMARY_JSON = STAGE5D_DIR / "133_stage5d_standardization_summary.json"
INPUT_02_SANDBOX_XLSX = STAGE5C_DIR / "130_stage5c_structured_02_sandbox.xlsx"

FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"

OUT_DIR = OUTPUT_DIR / "stage5e_mapping_miss_inventory"
OUT_XLSX = OUT_DIR / "134_stage5e_mapping_miss_inventory.xlsx"
OUT_MD = OUT_DIR / "134_stage5e_mapping_miss_inventory.md"
OUT_JSON = OUT_DIR / "135_stage5e_mapping_miss_summary.json"

MISS_CATEGORIES = {
    "TRUE_MAPPING_GAP",
    "RAW_METRIC_NAME_PARSE_ISSUE",
    "HEADER_OR_METADATA_ROW",
    "NON_FINANCIAL_ROW",
    "DERIVED_METRIC_NOT_SUPPORTED",
    "PACKAGE_SPECIFIC_METRIC",
    "ALIAS_MISSING",
    "SCOPE_CONDITION_MISMATCH",
    "NORMALIZATION_DEPENDENT",
    "LOW_VALUE_NO_ACTION",
    "UNKNOWN",
}

RECOMMENDED_ACTIONS = {
    "DRAFT_MAPPING_RULE",
    "DRAFT_ALIAS_RULE",
    "FIX_RAW_METRIC_EXTRACTION",
    "FILTER_HEADER_ROW",
    "FILTER_NON_FINANCIAL_ROW",
    "DEFER_DERIVED_METRIC_RULE",
    "DEFER_PACKAGE_SPECIFIC_RULE",
    "NEED_MANUAL_REVIEW",
    "NO_ACTION",
}

HEADER_OR_META_TERMS = [
    "证券研究报告",
    "请务必阅读",
    "分析师",
    "评级",
    "风险提示",
    "资料来源",
    "日期",
    "2026年05月",
]

NON_FINANCIAL_TERMS = [
    "其他",
    "合计",
    "总计",
    "小计",
]

DERIVED_TERMS = [
    "同比",
    "增速",
    "增长率",
    "CAGR",
    "环比",
    "YoY",
    "QoQ",
]

# Frequent truncated fragments observed in Stage5D mapping misses.
TRUNCATED_PARSE_FRAGMENTS = {
    "动资",
    "现金",
    "收票",
    "预付",
    "存货",
    "其他",
    "流动",
    "资活",
    "长期",
    "固定",
    "无形",
    "产总",
    "动负",
    "付票",
    "债合",
    "债和",
    "短期",
    "资本",
    "股本",
    "留存",
    "金净",
    "金流",
    "营活",
    "营运",
    "投资",
    "财务",
    "折旧",
    "属母",
    "净利",
    "普通",
    "数",
}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    text = _norm(v)
    text = text.replace("（", "(").replace("）", ")").replace("／", "/")
    text = re.sub(r"\s+", "", text)
    return text.upper()


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
    pool: List[Tuple[str, str]] = []
    for standard_metric, aliases in fs.STANDARD_METRIC_ALIASES.items():
        pool.append((_norm(standard_metric), _norm(standard_metric)))
        for alias in aliases:
            pool.append((_norm(alias), _norm(standard_metric)))
    uniq = []
    seen = set()
    for alias, std in pool:
        k = (_compact(alias), _compact(std))
        if k in seen:
            continue
        seen.add(k)
        uniq.append((alias, std))
    return uniq


def _nearest_metric(raw_cleaned: str, pool: List[Tuple[str, str]]) -> Tuple[str, str, float]:
    rc = _compact(raw_cleaned)
    if not rc:
        return "", "", 0.0
    best_alias = ""
    best_std = ""
    best_score = 0.0
    for alias, std in pool:
        ac = _compact(alias)
        if not ac:
            continue
        score = SequenceMatcher(None, rc, ac).ratio()
        if ac.startswith(rc) or rc.startswith(ac):
            score = max(score, 0.72 if len(rc) >= 2 else score)
        if score > best_score:
            best_score = score
            best_alias = alias
            best_std = std
    return best_std, best_alias, float(round(best_score, 4))


def _clean_raw_metric(raw: str) -> str:
    text = fs._clean_metric_label_noise(_norm(raw))
    text = text.replace("（", "(").replace("）", ")").replace("／", "/")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[\|,;:]+$", "", text)
    return text


def _contains_any(text: str, terms: List[str]) -> bool:
    t = _norm(text)
    return any(x in t for x in terms)


def _classify_miss(
    *,
    raw_metric_name: str,
    raw_metric_name_cleaned: str,
    year: str,
    value: str,
    unit: str,
    statement_type: str,
    nearest_existing_standard_metric: str,
    nearest_alias: str,
    similarity_score: float,
) -> Tuple[str, str, str, str, str]:
    raw = _norm(raw_metric_name)
    cleaned = _norm(raw_metric_name_cleaned)
    st = _norm(statement_type)

    # category, root_cause, recommended_action, confidence, evidence
    if not cleaned:
        return (
            "RAW_METRIC_NAME_PARSE_ISSUE",
            "raw_metric_name empty after cleaning",
            "FIX_RAW_METRIC_EXTRACTION",
            "HIGH",
            "cleaned metric is empty",
        )
    if re.search(r"20\d{2}年\d{2}月", cleaned) or _contains_any(cleaned, HEADER_OR_META_TERMS):
        return (
            "HEADER_OR_METADATA_ROW",
            "header/metadata text entered metric column",
            "FILTER_HEADER_ROW",
            "HIGH",
            "date/report metadata tokens detected",
        )
    if cleaned in {"数", "普通"}:
        return (
            "RAW_METRIC_NAME_PARSE_ISSUE",
            "single-token fragment likely from row split/glue issue",
            "FIX_RAW_METRIC_EXTRACTION",
            "HIGH",
            "very short fragment token",
        )
    if _contains_any(cleaned, DERIVED_TERMS):
        return (
            "DERIVED_METRIC_NOT_SUPPORTED",
            "derived growth/rate metric not in current core direct-mapping scope",
            "DEFER_DERIVED_METRIC_RULE",
            "MEDIUM",
            "derived-metric token detected",
        )
    if cleaned in {"其他"}:
        return (
            "LOW_VALUE_NO_ACTION",
            "generic 'other' bucket is low-value and noisy for core metric mapping",
            "NO_ACTION",
            "MEDIUM",
            "generic bucket term",
        )
    if len(cleaned) <= 2 and cleaned in TRUNCATED_PARSE_FRAGMENTS:
        return (
            "RAW_METRIC_NAME_PARSE_ISSUE",
            "two-char fragment suggests truncation from original row label",
            "FIX_RAW_METRIC_EXTRACTION",
            "HIGH",
            "fragment belongs to known truncation pattern set",
        )
    if len(cleaned) <= 4 and similarity_score >= 0.76 and nearest_existing_standard_metric:
        return (
            "ALIAS_MISSING",
            "close to existing metric alias but exact alias not covered",
            "DRAFT_ALIAS_RULE",
            "MEDIUM",
            f"nearest={nearest_existing_standard_metric} alias={nearest_alias} score={similarity_score}",
        )
    if st and st != "利润表" and len(cleaned) <= 4 and cleaned in TRUNCATED_PARSE_FRAGMENTS:
        return (
            "SCOPE_CONDITION_MISMATCH",
            "statement_type/scope might be mismatched for parsed metric fragment",
            "NEED_MANUAL_REVIEW",
            "LOW",
            "statement_type not aligned with metric fragment",
        )
    if len(cleaned) <= 6 and similarity_score >= 0.65 and nearest_existing_standard_metric:
        return (
            "NORMALIZATION_DEPENDENT",
            "normalization/alias expansion likely needed before mapping",
            "DRAFT_ALIAS_RULE",
            "MEDIUM",
            f"nearest={nearest_existing_standard_metric} alias={nearest_alias} score={similarity_score}",
        )
    if _contains_any(cleaned, NON_FINANCIAL_TERMS):
        return (
            "NON_FINANCIAL_ROW",
            "non-core or subtotal-style textual row entered mapping flow",
            "FILTER_NON_FINANCIAL_ROW",
            "MEDIUM",
            "non-financial marker term detected",
        )
    if len(cleaned) >= 3 and similarity_score >= 0.55 and nearest_existing_standard_metric:
        return (
            "TRUE_MAPPING_GAP",
            "appears to be metric-like token with no direct mapping rule",
            "DRAFT_MAPPING_RULE",
            "LOW",
            f"nearest={nearest_existing_standard_metric} alias={nearest_alias} score={similarity_score}",
        )
    if len(cleaned) <= 4 and any(x in cleaned for x in ["券", "资产包", "分部", "业务", "品类"]):
        return (
            "PACKAGE_SPECIFIC_METRIC",
            "package/business-specific metric likely needs scoped rule",
            "DEFER_PACKAGE_SPECIFIC_RULE",
            "LOW",
            "package-specific pattern detected",
        )
    return (
        "UNKNOWN",
        "insufficient signal to classify confidently",
        "NEED_MANUAL_REVIEW",
        "LOW",
        "fallback unknown classification",
    )


def _mapping_rule_id_from_metric(metric: str) -> str:
    m = _norm(metric)
    if not m:
        return ""
    return f"FS_MAP_{_compact(m)}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5E analyze sandbox mapping misses.")
    parser.parse_args()

    required_paths = [
        INPUT_05_XLSX,
        INPUT_05_REPORT_XLSX,
        INPUT_05_SUMMARY_JSON,
        INPUT_02_SANDBOX_XLSX,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_NORMALIZATION_RULE_FILE,
        OFFICIAL_02B_PATH,
    ]
    for p in required_paths:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    df_05 = pd.read_excel(INPUT_05_XLSX, sheet_name="sandbox_05_standardized").fillna("")
    df_02 = pd.read_excel(INPUT_02_SANDBOX_XLSX, sheet_name="structured_02_sandbox").fillna("")
    _ = pd.read_excel(_find_delivery_file("05_*.xlsx")).fillna("")

    summary_5d = json.loads(INPUT_05_SUMMARY_JSON.read_text(encoding="utf-8"))
    input_sandbox_05_row_count = int(len(df_05))
    input_mapping_miss_count = int((df_05["standardization_status"].map(_norm) == "MAPPING_MISS").sum()) if not df_05.empty else 0

    miss_df = df_05[df_05["standardization_status"].map(_norm) == "MAPPING_MISS"].copy()
    metric_pool = _metric_pool()

    rows: List[Dict[str, Any]] = []
    for _, r in miss_df.iterrows():
        raw_metric_name = _norm(r.get("raw_metric_name"))
        raw_metric_name_cleaned = _clean_raw_metric(raw_metric_name)
        nearest_std, nearest_alias, similarity_score = _nearest_metric(raw_metric_name_cleaned, metric_pool)

        miss_category, root_cause, recommended_action, confidence_level, evidence = _classify_miss(
            raw_metric_name=raw_metric_name,
            raw_metric_name_cleaned=raw_metric_name_cleaned,
            year=_norm(r.get("year")),
            value=_norm(r.get("value")),
            unit=_norm(r.get("unit")),
            statement_type=_norm(r.get("statement_type")),
            nearest_existing_standard_metric=nearest_std,
            nearest_alias=nearest_alias,
            similarity_score=similarity_score,
        )

        if miss_category not in MISS_CATEGORIES:
            miss_category = "UNKNOWN"
        if recommended_action not in RECOMMENDED_ACTIONS:
            recommended_action = "NEED_MANUAL_REVIEW"

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
                "nearest_existing_mapping_rule_id": _mapping_rule_id_from_metric(nearest_std),
                "similarity_score": similarity_score,
                "miss_category": miss_category,
                "root_cause": root_cause,
                "recommended_action": recommended_action,
                "confidence_level": confidence_level,
                "evidence": evidence,
            }
        )

    inventory_df = pd.DataFrame(rows)
    analyzed_mapping_miss_count = int(len(inventory_df))

    # Groupings and diagnostics
    by_raw_df = (
        inventory_df.groupby(["raw_metric_name_cleaned"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "raw_metric_name_cleaned"], ascending=[False, True], kind="mergesort")
    ) if not inventory_df.empty else pd.DataFrame(columns=["raw_metric_name_cleaned", "count"])

    by_table_df = (
        inventory_df.groupby(["source_table_id"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "source_table_id"], ascending=[False, True], kind="mergesort")
    ) if not inventory_df.empty else pd.DataFrame(columns=["source_table_id", "count"])

    by_statement_df = (
        inventory_df.groupby(["statement_type"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "statement_type"], ascending=[False, True], kind="mergesort")
    ) if not inventory_df.empty else pd.DataFrame(columns=["statement_type", "count"])

    by_category_df = (
        inventory_df.groupby(["miss_category"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "miss_category"], ascending=[False, True], kind="mergesort")
    ) if not inventory_df.empty else pd.DataFrame(columns=["miss_category", "count"])

    top50_raw_df = by_raw_df.head(50).copy()
    suspected_header_df = inventory_df[inventory_df["miss_category"] == "HEADER_OR_METADATA_ROW"].copy() if not inventory_df.empty else pd.DataFrame(columns=inventory_df.columns)
    suspected_true_fin_df = inventory_df[inventory_df["miss_category"].isin(["TRUE_MAPPING_GAP", "ALIAS_MISSING", "NORMALIZATION_DEPENDENT"])].copy() if not inventory_df.empty else pd.DataFrame(columns=inventory_df.columns)
    stage5f_candidates_df = inventory_df[inventory_df["recommended_action"].isin(["DRAFT_MAPPING_RULE", "DRAFT_ALIAS_RULE"])].copy() if not inventory_df.empty else pd.DataFrame(columns=inventory_df.columns)

    # Counts for summary
    def _cat_count(name: str) -> int:
        if inventory_df.empty:
            return 0
        return int((inventory_df["miss_category"] == name).sum())

    def _action_count(name: str) -> int:
        if inventory_df.empty:
            return 0
        return int((inventory_df["recommended_action"] == name).sum())

    true_mapping_gap_count = _cat_count("TRUE_MAPPING_GAP")
    raw_metric_name_parse_issue_count = _cat_count("RAW_METRIC_NAME_PARSE_ISSUE")
    header_or_metadata_row_count = _cat_count("HEADER_OR_METADATA_ROW")
    non_financial_row_count = _cat_count("NON_FINANCIAL_ROW")
    derived_metric_not_supported_count = _cat_count("DERIVED_METRIC_NOT_SUPPORTED")
    package_specific_metric_count = _cat_count("PACKAGE_SPECIFIC_METRIC")
    alias_missing_count = _cat_count("ALIAS_MISSING")
    scope_condition_mismatch_count = _cat_count("SCOPE_CONDITION_MISMATCH")
    normalization_dependent_count = _cat_count("NORMALIZATION_DEPENDENT")
    low_value_no_action_count = _cat_count("LOW_VALUE_NO_ACTION")
    unknown_count = _cat_count("UNKNOWN")

    draft_mapping_rule_candidate_count = _action_count("DRAFT_MAPPING_RULE")
    draft_alias_rule_candidate_count = _action_count("DRAFT_ALIAS_RULE")
    fix_raw_metric_extraction_count = _action_count("FIX_RAW_METRIC_EXTRACTION")
    filter_header_row_count = _action_count("FILTER_HEADER_ROW")
    filter_non_financial_row_count = _action_count("FILTER_NON_FINANCIAL_ROW")
    need_manual_review_count = _action_count("NEED_MANUAL_REVIEW")

    top_raw_metric_name_count = int(len(top50_raw_df))
    unique_raw_metric_name_count = int(inventory_df["raw_metric_name_cleaned"].map(_norm).replace("", pd.NA).dropna().nunique()) if not inventory_df.empty else 0

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

    coverage_guard_sum = (
        true_mapping_gap_count
        + raw_metric_name_parse_issue_count
        + header_or_metadata_row_count
        + non_financial_row_count
        + alias_missing_count
        + scope_condition_mismatch_count
        + normalization_dependent_count
        + unknown_count
    )

    summary = {
        "input_sandbox_05_row_count": int(input_sandbox_05_row_count),
        "input_mapping_miss_count": int(input_mapping_miss_count),
        "analyzed_mapping_miss_count": int(analyzed_mapping_miss_count),
        "true_mapping_gap_count": int(true_mapping_gap_count),
        "raw_metric_name_parse_issue_count": int(raw_metric_name_parse_issue_count),
        "header_or_metadata_row_count": int(header_or_metadata_row_count),
        "non_financial_row_count": int(non_financial_row_count),
        "derived_metric_not_supported_count": int(derived_metric_not_supported_count),
        "package_specific_metric_count": int(package_specific_metric_count),
        "alias_missing_count": int(alias_missing_count),
        "scope_condition_mismatch_count": int(scope_condition_mismatch_count),
        "normalization_dependent_count": int(normalization_dependent_count),
        "low_value_no_action_count": int(low_value_no_action_count),
        "unknown_count": int(unknown_count),
        "draft_mapping_rule_candidate_count": int(draft_mapping_rule_candidate_count),
        "draft_alias_rule_candidate_count": int(draft_alias_rule_candidate_count),
        "fix_raw_metric_extraction_count": int(fix_raw_metric_extraction_count),
        "filter_header_row_count": int(filter_header_row_count),
        "filter_non_financial_row_count": int(filter_non_financial_row_count),
        "need_manual_review_count": int(need_manual_review_count),
        "top_raw_metric_name_count": int(top_raw_metric_name_count),
        "unique_raw_metric_name_count": int(unique_raw_metric_name_count),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5e_mapping_miss_inventory_pass": False,
    }

    summary["stage5e_mapping_miss_inventory_pass"] = bool(
        summary["input_mapping_miss_count"] == 432
        and summary["analyzed_mapping_miss_count"] == 432
        and coverage_guard_sum > 0
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

    summary_df = pd.DataFrame([summary])

    _write_excel(
        OUT_XLSX,
        {
            "mapping_miss_inventory": inventory_df,
            "by_raw_metric_name": by_raw_df,
            "by_source_table_id": by_table_df,
            "by_statement_type": by_statement_df,
            "by_miss_category": by_category_df,
            "top50_raw_metric_name": top50_raw_df,
            "suspected_header_meta_rows": suspected_header_df,
            "suspected_true_fin_rows": suspected_true_fin_df,
            "stage5f_draft_candidates": stage5f_candidates_df,
            "summary": summary_df,
            "stage5d_summary_ref": pd.DataFrame([summary_5d]),
        },
    )

    md_lines = [
        "# Stage5E Mapping Miss Inventory (Sandbox)",
        "",
        f"- input_sandbox_05_row_count: {summary['input_sandbox_05_row_count']}",
        f"- input_mapping_miss_count: {summary['input_mapping_miss_count']}",
        f"- analyzed_mapping_miss_count: {summary['analyzed_mapping_miss_count']}",
        f"- true_mapping_gap_count: {summary['true_mapping_gap_count']}",
        f"- raw_metric_name_parse_issue_count: {summary['raw_metric_name_parse_issue_count']}",
        f"- header_or_metadata_row_count: {summary['header_or_metadata_row_count']}",
        f"- non_financial_row_count: {summary['non_financial_row_count']}",
        f"- derived_metric_not_supported_count: {summary['derived_metric_not_supported_count']}",
        f"- package_specific_metric_count: {summary['package_specific_metric_count']}",
        f"- alias_missing_count: {summary['alias_missing_count']}",
        f"- scope_condition_mismatch_count: {summary['scope_condition_mismatch_count']}",
        f"- normalization_dependent_count: {summary['normalization_dependent_count']}",
        f"- low_value_no_action_count: {summary['low_value_no_action_count']}",
        f"- unknown_count: {summary['unknown_count']}",
        f"- draft_mapping_rule_candidate_count: {summary['draft_mapping_rule_candidate_count']}",
        f"- draft_alias_rule_candidate_count: {summary['draft_alias_rule_candidate_count']}",
        f"- fix_raw_metric_extraction_count: {summary['fix_raw_metric_extraction_count']}",
        f"- filter_header_row_count: {summary['filter_header_row_count']}",
        f"- filter_non_financial_row_count: {summary['filter_non_financial_row_count']}",
        f"- need_manual_review_count: {summary['need_manual_review_count']}",
        f"- top_raw_metric_name_count: {summary['top_raw_metric_name_count']}",
        f"- unique_raw_metric_name_count: {summary['unique_raw_metric_name_count']}",
        f"- production_files_unchanged: {summary['production_files_unchanged']}",
        f"- official_02B_unchanged: {summary['official_02B_unchanged']}",
        f"- formal_scope_rules_unchanged: {summary['formal_scope_rules_unchanged']}",
        f"- formal_mapping_rules_unchanged: {summary['formal_mapping_rules_unchanged']}",
        f"- formal_normalization_rules_unchanged: {summary['formal_normalization_rules_unchanged']}",
        f"- stage5e_mapping_miss_inventory_pass: {summary['stage5e_mapping_miss_inventory_pass']}",
    ]
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5e_inventory_xlsx: {OUT_XLSX}")
    print(f"stage5e_inventory_md: {OUT_MD}")
    print(f"stage5e_inventory_summary_json: {OUT_JSON}")
    print(f"input_mapping_miss_count: {summary['input_mapping_miss_count']}")
    print(f"analyzed_mapping_miss_count: {summary['analyzed_mapping_miss_count']}")
    print(f"stage5e_mapping_miss_inventory_pass: {summary['stage5e_mapping_miss_inventory_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
