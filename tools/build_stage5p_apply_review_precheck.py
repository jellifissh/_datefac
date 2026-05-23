import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_STAGE5O_DIR = OUTPUT_DIR / "stage5o_promotion_review"
INPUT_PROMOTION_REVIEW_XLSX = INPUT_STAGE5O_DIR / "154_stage5o_promotion_review.xlsx"
INPUT_CANDIDATE_02_XLSX = INPUT_STAGE5O_DIR / "154_stage5o_candidate_02.xlsx"
INPUT_CANDIDATE_05_XLSX = INPUT_STAGE5O_DIR / "154_stage5o_candidate_05.xlsx"
INPUT_DIFF_XLSX = INPUT_STAGE5O_DIR / "154_stage5o_diff_with_production_02_05.xlsx"
INPUT_STAGE5O_SUMMARY_JSON = INPUT_STAGE5O_DIR / "155_stage5o_promotion_review_summary.json"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_ALIAS_RULE_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5p_apply_review_precheck"
OUT_METRIC_LEVEL_REVIEW_XLSX = OUT_DIR / "156_stage5p_metric_level_review.xlsx"
OUT_REPORT_MD = OUT_DIR / "156_stage5p_apply_precheck_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "157_stage5p_apply_precheck_summary.json"

ALLOWED_ACTIONS = {
    "PROMOTE_TO_05_SAFE",
    "PROMOTE_TO_02_ONLY",
    "DEFER_DERIVED_METRIC",
    "FILTER_NON_CORE",
    "NEED_ALIAS_RULE",
    "NEED_MAPPING_RULE",
    "DIFF_KEY_SCHEMA_ISSUE",
    "BLOCKED",
}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    t = _norm(v).replace("（", "(").replace("）", ")").replace("／", "/")
    t = re.sub(r"\s+", "", t)
    return t.upper()


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
        "formal_alias_rules": _sha256(FORMAL_ALIAS_RULE_FILE),
    }


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


def _looks_like_schema_reference_issue(path_str: str, expected_tokens: List[str], bad_tokens: List[str]) -> bool:
    s = _norm(path_str)
    if not s:
        return True
    if any(bt in s for bt in bad_tokens):
        return True
    return not any(et in s for et in expected_tokens)


def _classify_metric_action(
    statement_type: str,
    metric_name_cleaned: str,
    raw_metric_name: str,
    row_review_actions: List[str],
    has_schema_issue: bool,
) -> Tuple[str, str]:
    st = _norm(statement_type)
    metric = _norm(metric_name_cleaned) or _norm(raw_metric_name)
    review_set = set([_norm(x) for x in row_review_actions if _norm(x)])

    if "PROMOTE_TO_05_CANDIDATE" in review_set and review_set == {"PROMOTE_TO_05_CANDIDATE"}:
        return "PROMOTE_TO_05_SAFE", "standardization_already_ok"
    if "DEFER_DERIVED_METRIC" in review_set:
        return "DEFER_DERIVED_METRIC", "derived_metric_not_target_for_current_apply"
    if "FILTER_NON_CORE_METRIC" in review_set:
        return "FILTER_NON_CORE", "non_core_metric_outside_current_apply_scope"

    # Main compression target: NEED_MAPPING_OR_ALIAS_REVIEW rows.
    if "NEED_MAPPING_OR_ALIAS_REVIEW" in review_set:
        if st in {"资产负债表", "现金流量表"}:
            # For this project stage, these are mainly structured-layer facts; keep in 02 review first.
            return "PROMOTE_TO_02_ONLY", "structured_fact_metric_not_in_current_core_05_scope"

        if st == "利润表":
            if any(tok in metric for tok in ["营业收入", "归属母公司净利润", "每股收益", "EPS", "P/E", "P/B", "EV/EBITDA", "毛利率", "ROE"]):
                return "NEED_ALIAS_RULE", "close_to_core_metric_alias_variant"
            if metric in {"净利润"}:
                return "NEED_ALIAS_RULE", "likely_alias_to_归属母公司净利润_needs_rule_review"
            return "PROMOTE_TO_02_ONLY", "non_core_income_metric_keep_in_02_only"

        if st == "主要财务比率":
            if any(tok in metric for tok in ["每股收益", "EPS", "P/E", "P/B", "EV/EBITDA", "毛利率", "ROE"]):
                return "NEED_ALIAS_RULE", "ratio_metric_close_to_core_alias_candidate"
            if any(tok in metric for tok in ["率", "%", "周转"]):
                return "DEFER_DERIVED_METRIC", "derived_ratio_metric_defer_for_later_stage"
            return "NEED_MAPPING_RULE", "ratio_metric_requires_mapping_rule_review"

        # Unknown statement type fallback
        if has_schema_issue:
            return "DIFF_KEY_SCHEMA_ISSUE", "schema_mismatch_blocks_reliable_diff_decision"
        return "NEED_MAPPING_RULE", "mapping_rule_missing_for_metric"

    if has_schema_issue:
        return "DIFF_KEY_SCHEMA_ISSUE", "schema_mismatch_blocks_reliable_diff_decision"
    return "BLOCKED", "unable_to_classify_with_current_evidence"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5P apply review precheck at metric level.")
    parser.parse_args()

    required = [
        INPUT_PROMOTION_REVIEW_XLSX,
        INPUT_CANDIDATE_02_XLSX,
        INPUT_CANDIDATE_05_XLSX,
        INPUT_DIFF_XLSX,
        INPUT_STAGE5O_SUMMARY_JSON,
        OFFICIAL_02B_PATH,
        FORMAL_SCOPE_RULES_JSON,
        FORMAL_MAPPING_RULE_FILE,
        FORMAL_NORMALIZATION_RULE_FILE,
        FORMAL_ALIAS_RULE_FILE,
    ]
    for p in required:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    before = _snapshot_hashes()

    stage5o_summary = json.loads(INPUT_STAGE5O_SUMMARY_JSON.read_text(encoding="utf-8"))
    candidate_02_df = pd.read_excel(INPUT_CANDIDATE_02_XLSX, sheet_name=0).fillna("")
    candidate_05_df = pd.read_excel(INPUT_CANDIDATE_05_XLSX, sheet_name=0).fillna("")
    diff02_df = pd.read_excel(INPUT_DIFF_XLSX, sheet_name="diff_with_production_02").fillna("")
    diff05_df = pd.read_excel(INPUT_DIFF_XLSX, sheet_name="diff_with_production_05").fillna("")

    # Main precheck focus scope: 315 need_manual_review rows
    manual_rows = candidate_05_df[candidate_05_df["review_action"] == "NEED_MAPPING_OR_ALIAS_REVIEW"].copy()
    input_need_manual_review_row_count = int(len(manual_rows))

    # Also include derived/non-core/promote rows for full metric-level picture.
    include_actions = {
        "NEED_MAPPING_OR_ALIAS_REVIEW",
        "DEFER_DERIVED_METRIC",
        "FILTER_NON_CORE_METRIC",
        "PROMOTE_TO_05_CANDIDATE",
    }
    full_scope_rows = candidate_05_df[candidate_05_df["review_action"].isin(include_actions)].copy()

    # Build per metric-level key: raw_metric_name + statement_type + unit
    full_scope_rows["metric_level_key"] = (
        full_scope_rows["raw_metric_name"].map(_norm)
        + "||"
        + full_scope_rows["statement_type"].map(_norm)
        + "||"
        + full_scope_rows["unit"].map(_norm)
    )

    diff05_work = diff05_df.copy()
    diff05_work["metric_year_key"] = (
        diff05_work["metric_name_cleaned"].map(_norm)
        + "||"
        + diff05_work["statement_type"].map(_norm)
        + "||"
        + diff05_work["candidate_unit"].map(_norm)
        + "||"
        + diff05_work["year"].map(_norm)
    )
    diff_class_map = {}
    for _, r in diff05_work.iterrows():
        k = _norm(r.get("metric_year_key"))
        if not k:
            continue
        diff_class_map.setdefault(k, set()).add(_norm(r.get("diff_class")))

    prod02_ref = _norm(stage5o_summary.get("production_02_reference_file"))
    prod05_ref = _norm(stage5o_summary.get("production_05_reference_file"))
    schema_issue_02 = _looks_like_schema_reference_issue(
        prod02_ref,
        expected_tokens=["结构化", "02_研报全量结构化数据"],
        bad_tokens=["人工复核指标队列"],
    )
    schema_issue_05 = _looks_like_schema_reference_issue(
        prod05_ref,
        expected_tokens=["标准化", "05_核心财务指标标准化"],
        bad_tokens=["表格区域截图索引"],
    )
    same_as_zero_02 = int(stage5o_summary.get("same_as_production_count_02", 0)) == 0
    same_as_zero_05 = int(stage5o_summary.get("same_as_production_count_05", 0)) == 0
    diff_key_schema_issue_detected = bool(schema_issue_02 or schema_issue_05)
    same_as_production_zero_due_schema_issue = bool(diff_key_schema_issue_detected and same_as_zero_02 and same_as_zero_05)

    metric_rows: List[Dict[str, Any]] = []
    for mkey, grp in full_scope_rows.groupby("metric_level_key", sort=True):
        grp = grp.copy()
        raw_metric_name = _norm(grp.iloc[0]["raw_metric_name"])
        metric_name_cleaned = _norm(grp.iloc[0]["metric_name_cleaned"])
        statement_type = _norm(grp.iloc[0]["statement_type"])
        unit = _norm(grp.iloc[0]["unit"])
        years = sorted(set(grp["year"].map(_norm).tolist()))
        row_review_actions = grp["review_action"].map(_norm).tolist()

        # metric-year diff classes
        diff_classes = set()
        for _, r in grp.iterrows():
            ykey = (
                _norm(r.get("metric_name_cleaned"))
                + "||"
                + _norm(r.get("statement_type"))
                + "||"
                + _norm(r.get("unit"))
                + "||"
                + _norm(r.get("year"))
            )
            diff_classes |= diff_class_map.get(ykey, set())
        diff_classes_sorted = sorted([x for x in diff_classes if x])

        action, action_reason = _classify_metric_action(
            statement_type=statement_type,
            metric_name_cleaned=metric_name_cleaned,
            raw_metric_name=raw_metric_name,
            row_review_actions=row_review_actions,
            has_schema_issue=same_as_production_zero_due_schema_issue,
        )
        if action not in ALLOWED_ACTIONS:
            action = "BLOCKED"
            action_reason = "internal_action_validation_failed"

        diff_schema_flag = bool(
            same_as_production_zero_due_schema_issue
            and (("DUPLICATE_CANDIDATE" in diff_classes) or ("NEW_RECORD" in diff_classes) or not diff_classes)
        )
        requires_manual_review = bool(action in {"NEED_ALIAS_RULE", "NEED_MAPPING_RULE", "BLOCKED", "DIFF_KEY_SCHEMA_ISSUE"})

        metric_rows.append(
            {
                "metric_level_key": mkey,
                "raw_metric_name": raw_metric_name,
                "metric_name_cleaned": metric_name_cleaned,
                "statement_type": statement_type,
                "unit": unit,
                "year_count": int(len(years)),
                "years": ",".join(years),
                "row_count": int(len(grp)),
                "row_review_action_counts": json.dumps(grp["review_action"].value_counts().to_dict(), ensure_ascii=False),
                "diff_class_counts": json.dumps(
                    pd.Series(diff_classes_sorted).value_counts().to_dict(), ensure_ascii=False
                )
                if diff_classes_sorted
                else "{}",
                "recommended_action": action,
                "action_reason": action_reason,
                "diff_key_schema_issue_flag": bool(diff_schema_flag),
                "requires_manual_review": bool(requires_manual_review),
            }
        )

    metric_level_df = pd.DataFrame(metric_rows).fillna("")
    metric_level_count = int(len(metric_level_df))

    # Summary counts by action.
    action_counts = metric_level_df["recommended_action"].value_counts().to_dict() if not metric_level_df.empty else {}
    promote_to_05_safe_metric_count = int(action_counts.get("PROMOTE_TO_05_SAFE", 0))
    promote_to_02_only_metric_count = int(action_counts.get("PROMOTE_TO_02_ONLY", 0))
    defer_derived_metric_count = int(action_counts.get("DEFER_DERIVED_METRIC", 0))
    filter_non_core_metric_count = int(action_counts.get("FILTER_NON_CORE", 0))
    need_alias_rule_metric_count = int(action_counts.get("NEED_ALIAS_RULE", 0))
    need_mapping_rule_metric_count = int(action_counts.get("NEED_MAPPING_RULE", 0))
    diff_key_schema_issue_metric_count = int(action_counts.get("DIFF_KEY_SCHEMA_ISSUE", 0))
    blocked_metric_count = int(action_counts.get("BLOCKED", 0))

    # Manual subset compression only (requested 315 compression).
    manual_scope_keys = set(
        full_scope_rows[full_scope_rows["review_action"] == "NEED_MAPPING_OR_ALIAS_REVIEW"]["metric_level_key"].map(_norm).tolist()
    )
    compressed_manual_metric_count = int(
        metric_level_df["metric_level_key"].map(_norm).isin(manual_scope_keys).sum()
    ) if not metric_level_df.empty else 0

    # Diagnostic sheet for the "same_as_production=0" root-cause evidence.
    schema_diag_rows = [
        {"check_item": "production_02_reference_file", "value": prod02_ref},
        {"check_item": "production_05_reference_file", "value": prod05_ref},
        {"check_item": "same_as_production_count_02", "value": int(stage5o_summary.get("same_as_production_count_02", 0))},
        {"check_item": "same_as_production_count_05", "value": int(stage5o_summary.get("same_as_production_count_05", 0))},
        {"check_item": "schema_issue_02_detected", "value": bool(schema_issue_02)},
        {"check_item": "schema_issue_05_detected", "value": bool(schema_issue_05)},
        {"check_item": "same_as_production_zero_due_schema_issue", "value": bool(same_as_production_zero_due_schema_issue)},
    ]
    schema_diag_df = pd.DataFrame(schema_diag_rows)

    # write workbook
    _write_excel(
        OUT_METRIC_LEVEL_REVIEW_XLSX,
        {
            "metric_level_review": metric_level_df.sort_values(["recommended_action", "statement_type", "raw_metric_name"]),
            "schema_diff_diagnostics": schema_diag_df,
            "diff_with_production_02": diff02_df,
            "diff_with_production_05": diff05_df,
        },
    )

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
    formal_alias_rules_unchanged = bool(before["formal_alias_rules"] == after["formal_alias_rules"])

    summary = {
        "input_need_manual_review_row_count": int(input_need_manual_review_row_count),
        "compressed_manual_metric_count": int(compressed_manual_metric_count),
        "metric_level_count": int(metric_level_count),
        "promote_to_05_safe_metric_count": int(promote_to_05_safe_metric_count),
        "promote_to_02_only_metric_count": int(promote_to_02_only_metric_count),
        "defer_derived_metric_count": int(defer_derived_metric_count),
        "filter_non_core_metric_count": int(filter_non_core_metric_count),
        "need_alias_rule_metric_count": int(need_alias_rule_metric_count),
        "need_mapping_rule_metric_count": int(need_mapping_rule_metric_count),
        "diff_key_schema_issue_metric_count": int(diff_key_schema_issue_metric_count),
        "blocked_metric_count": int(blocked_metric_count),
        "same_as_production_zero_due_schema_issue": bool(same_as_production_zero_due_schema_issue),
        "production_02_reference_file": prod02_ref,
        "production_05_reference_file": prod05_ref,
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_scope_rules_unchanged": bool(formal_scope_rules_unchanged),
        "formal_mapping_rules_unchanged": bool(formal_mapping_rules_unchanged),
        "formal_normalization_rules_unchanged": bool(formal_normalization_rules_unchanged),
        "formal_alias_rules_unchanged": bool(formal_alias_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5p_apply_precheck_pass": False,
    }

    summary["stage5p_apply_precheck_pass"] = bool(
        summary["input_need_manual_review_row_count"] == 315
        and summary["compressed_manual_metric_count"] > 0
        and summary["metric_level_count"] > 0
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_scope_rules_unchanged"]
        and summary["formal_mapping_rules_unchanged"]
        and summary["formal_normalization_rules_unchanged"]
        and summary["formal_alias_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    md_lines = [
        "# Stage5P Apply Review Precheck (Metric-Level)",
        "",
        "## Compression",
        f"- input_need_manual_review_row_count: {summary['input_need_manual_review_row_count']}",
        f"- compressed_manual_metric_count: {summary['compressed_manual_metric_count']}",
        f"- metric_level_count: {summary['metric_level_count']}",
        "",
        "## Recommended Actions",
        f"- promote_to_05_safe_metric_count: {summary['promote_to_05_safe_metric_count']}",
        f"- promote_to_02_only_metric_count: {summary['promote_to_02_only_metric_count']}",
        f"- defer_derived_metric_count: {summary['defer_derived_metric_count']}",
        f"- filter_non_core_metric_count: {summary['filter_non_core_metric_count']}",
        f"- need_alias_rule_metric_count: {summary['need_alias_rule_metric_count']}",
        f"- need_mapping_rule_metric_count: {summary['need_mapping_rule_metric_count']}",
        f"- diff_key_schema_issue_metric_count: {summary['diff_key_schema_issue_metric_count']}",
        f"- blocked_metric_count: {summary['blocked_metric_count']}",
        "",
        "## Diff Diagnostics",
        f"- same_as_production_zero_due_schema_issue: {summary['same_as_production_zero_due_schema_issue']}",
        f"- production_02_reference_file: {summary['production_02_reference_file']}",
        f"- production_05_reference_file: {summary['production_05_reference_file']}",
        "",
        "## Decision",
        f"- stage5p_apply_precheck_pass: {summary['stage5p_apply_precheck_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5p_metric_level_review_xlsx: {OUT_METRIC_LEVEL_REVIEW_XLSX}")
    print(f"stage5p_report_md: {OUT_REPORT_MD}")
    print(f"stage5p_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5p_apply_precheck_pass: {summary['stage5p_apply_precheck_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
