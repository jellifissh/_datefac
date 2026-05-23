import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import financial_standardizer as fs


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_STAGE5O_DIR = OUTPUT_DIR / "stage5o_promotion_review"
INPUT_CANDIDATE_02_XLSX = INPUT_STAGE5O_DIR / "154_stage5o_candidate_02.xlsx"
INPUT_CANDIDATE_05_XLSX = INPUT_STAGE5O_DIR / "154_stage5o_candidate_05.xlsx"
INPUT_STAGE5O_SUMMARY_JSON = INPUT_STAGE5O_DIR / "155_stage5o_promotion_review_summary.json"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_ALIAS_RULE_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5q_apply_precheck_fix"
OUT_FIXED_METRIC_REVIEW_XLSX = OUT_DIR / "158_stage5q_fixed_metric_level_review.xlsx"
OUT_FIXED_DIFF_XLSX = OUT_DIR / "158_stage5q_fixed_diff_with_production_02_05.xlsx"
OUT_PROBLEM_FIX_XLSX = OUT_DIR / "158_stage5q_problem_metric_fix_report.xlsx"
OUT_REPORT_MD = OUT_DIR / "158_stage5q_apply_precheck_fix_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "159_stage5q_apply_precheck_fix_summary.json"

INPUT_PDF_STEM = "H3_AP202605121822223662_1"
YEAR_COLUMNS = ["2024A", "2025A", "2026E", "2027E", "2028E"]
YEAR_TOKEN_RE = re.compile(r"^20\d{2}(?:[AE])?$", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
VALUE_VALID_RE = re.compile(r"[-+]?\d+(?:\.\d+)?$")


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


def _canonical_num(v: Any) -> str:
    t = _norm(v).replace(",", "")
    if not t:
        return ""
    try:
        d = Decimal(t)
    except InvalidOperation:
        return t
    if d == d.to_integral():
        return str(int(d))
    s = format(d.normalize(), "f")
    return s.rstrip("0").rstrip(".") if "." in s else s


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
        "formal_alias_rules": _sha256(FORMAL_ALIAS_RULE_FILE),
    }


def _find_true_production_ref_files() -> Tuple[bool, bool, Optional[Path], Optional[Path]]:
    out = BASE_DIR / "output"
    cand02: List[Path] = []
    cand05: List[Path] = []
    for p in out.rglob("*.xlsx"):
        sp = str(p)
        if INPUT_PDF_STEM not in sp:
            continue
        if "stage5a_pdf_conversion_audit" in sp or "stage5k_full_sandbox_rebuild" in sp or "_stage1_safe_runner_trial" in sp:
            continue
        if p.name.startswith("02_") and "结构化" in p.name:
            cand02.append(p)
        if p.name.startswith("05_") and "标准化" in p.name:
            cand05.append(p)
    cand02 = sorted(cand02, key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)
    cand05 = sorted(cand05, key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)
    p02 = cand02[0] if cand02 else None
    p05 = cand05[0] if cand05 else None
    return bool(p02), bool(p05), p02, p05


def _wrong_reference_file_detected(stage5o_summary: Dict[str, Any]) -> bool:
    p02 = _norm(stage5o_summary.get("production_02_reference_file"))
    p05 = _norm(stage5o_summary.get("production_05_reference_file"))
    return ("人工复核指标队列" in p02) or ("表格区域截图索引" in p05)


def _fix_problem_raw_metric_name(candidate_02_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = candidate_02_df.copy().fillna("")
    fix_rows: List[Dict[str, Any]] = []
    for idx, r in df.iterrows():
        raw_name = _norm(r.get("raw_metric_name"))
        clean_name = _norm(r.get("metric_name_cleaned"))
        fixed_name = raw_name
        reason = ""
        if clean_name == "非流动资产" and raw_name == "流动资产":
            fixed_name = "非流动资产"
            reason = "fix_merged_current_noncurrent_asset"
        elif clean_name == "非流动负债" and raw_name == "流动负债":
            fixed_name = "非流动负债"
            reason = "fix_merged_current_noncurrent_liability"
        elif clean_name == "筹资活动现金流" and raw_name == "投资活动现金流":
            fixed_name = "筹资活动现金流"
            reason = "fix_merged_investing_financing_cashflow"
        if fixed_name != raw_name:
            df.at[idx, "raw_metric_name"] = fixed_name
            fix_rows.append(
                {
                    "row_index": int(idx),
                    "raw_metric_name_before": raw_name,
                    "metric_name_cleaned": clean_name,
                    "raw_metric_name_after": fixed_name,
                    "fix_reason": reason,
                    "statement_type": _norm(r.get("statement_type")),
                    "year": _norm(r.get("year")),
                    "value": _norm(r.get("value")),
                }
            )
    return df, pd.DataFrame(fix_rows).fillna("")


def _build_alias_rule_id(standard_metric: str, raw_metric: str) -> str:
    std = _norm(standard_metric)
    raw = _norm(raw_metric)
    if not std or std not in fs.STANDARD_METRIC_ALIASES:
        return ""
    aliases = fs.STANDARD_METRIC_ALIASES.get(std, [])
    for i, a in enumerate(aliases, start=1):
        if _compact(a) == _compact(raw):
            return f"FS_ALIAS_{_compact(std)}_{i:03d}"
    return ""


def _classify_row_review_action(statement_type: str, metric_name: str) -> Tuple[str, str]:
    metric = _norm(metric_name)
    st = _norm(statement_type)

    if any(x in metric for x in ["(%)", "%", "周转率", "ROIC", "资产负债率", "净利率"]):
        return "DEFER_DERIVED_METRIC", "derived_metric"

    # Stage5Q rule: these cannot be directly filtered as non-core.
    if metric in {"净利润", "营业利润", "EBITDA"}:
        return "NEED_SCOPE_REVIEW", "must_not_filter_non_core_without_scope_explanation"

    if st in {"资产负债表", "现金流量表"}:
        return "PROMOTE_TO_02_ONLY", "structured_fact_metric_not_in_current_05_core_scope"

    if st == "主要财务比率" and ("每股" in metric or "EPS" in metric):
        return "NEED_MAPPING_RULE", "per_share_ratio_metric_needs_mapping_rule"

    if st == "利润表":
        return "PROMOTE_TO_02_ONLY", "income_statement_non_core_metric_keep_for_02"

    return "NEED_MAPPING_RULE", "mapping_rule_missing"


def _rebuild_candidate_05(fixed_candidate_02_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, r in fixed_candidate_02_df.iterrows():
        metric = _norm(r.get("metric_name_cleaned")) or _norm(r.get("raw_metric_name"))
        year = _norm(r.get("year")).upper()
        value = _canonical_num(r.get("value"))
        unit = _norm(r.get("unit"))
        statement_type = _norm(r.get("statement_type"))

        standard_metric = ""
        status = "STANDARDIZATION_FAILED"
        issue_type = "UNKNOWN"
        review_action = "BLOCKED"
        review_reason = "unknown"
        mapping_rule_id = ""
        alias_rule_id = ""

        m = fs._match_standard_metric(metric)
        if not m:
            status = "MAPPING_MISS"
            issue_type = "METRIC_MAPPING_ISSUE"
            review_action, review_reason = _classify_row_review_action(statement_type, metric)
        else:
            standard_metric = _norm(m.get("standard_metric"))
            mapping_rule_id = f"FS_MAP_{_compact(standard_metric)}" if standard_metric else ""
            alias_rule_id = _build_alias_rule_id(standard_metric, metric)
            if not YEAR_TOKEN_RE.fullmatch(year):
                status = "YEAR_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                review_action = "BLOCKED"
                review_reason = "year_invalid"
            elif not VALUE_VALID_RE.fullmatch(value):
                status = "VALUE_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                review_action = "BLOCKED"
                review_reason = "value_invalid"
            elif not unit:
                status = "UNIT_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                review_action = "BLOCKED"
                review_reason = "unit_missing"
            else:
                status = "STANDARDIZED_OK"
                issue_type = "NONE"
                review_action = "PROMOTE_TO_05_SAFE"
                review_reason = "standardized_ok"

        rows.append(
            {
                "asset_package": _norm(r.get("asset_package")),
                "source_pdf": _norm(r.get("source_pdf")),
                "source_page": _norm(r.get("source_page")),
                "source_sheet": _norm(r.get("source_sheet")),
                "source_table_id": _norm(r.get("source_table_id")),
                "source_row_index": _norm(r.get("source_row_index")),
                "semantic_table_id": _norm(r.get("semantic_table_id")),
                "source_reference": _norm(r.get("source_reference")),
                "raw_metric_name": _norm(r.get("raw_metric_name")),
                "metric_name_cleaned": metric,
                "standard_metric": standard_metric,
                "statement_type": statement_type,
                "unit": unit,
                "year": year,
                "value": value,
                "mapping_rule_id": mapping_rule_id,
                "alias_rule_id": alias_rule_id,
                "standardization_status": status,
                "standardization_issue_type": issue_type,
                "review_action": review_action,
                "review_reason": review_reason,
            }
        )
    return pd.DataFrame(rows).fillna("")


def _parse_production_05_to_long(prod05_path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(prod05_path)
    target_sheet = "核心指标宽表" if "核心指标宽表" in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(prod05_path, sheet_name=target_sheet).fillna("")
    if df.empty:
        return pd.DataFrame(columns=["metric_name_cleaned", "standard_metric", "year", "value", "unit", "statement_type"])

    metric_col = "指标" if "指标" in df.columns else df.columns[0]
    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        metric = _norm(r.get(metric_col))
        if not metric:
            continue
        for yl in YEAR_COLUMNS:
            if yl not in df.columns:
                continue
            value = _canonical_num(r.get(yl))
            if not value:
                continue
            rows.append(
                {
                    "metric_name_cleaned": metric,
                    "standard_metric": metric,
                    "year": yl,
                    "value": value,
                    "unit": "",
                    "statement_type": _norm(r.get("来源类型")),
                }
            )
    return pd.DataFrame(rows).fillna("")


def _extract_metric_label_from_row(c1: str, c2: str) -> str:
    a = _norm(c1)
    b = _norm(c2)
    if not a and not b:
        return ""
    t = (a + b).replace(" ", "")
    t = t.replace("（", "(").replace("）", ")")
    if t == "产负债表(百万元)":
        return ""
    if t == "金流量表(百万元)":
        return ""
    # keep known corrected labels
    if a == "流动" and b == "资产":
        return "流动资产"
    if a == "流动" and b == "负债":
        return "流动负债"
    if a == "资活" and b == "动现金流":
        return "投资活动现金流"
    return t


def _parse_production_02_to_long(prod02_path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(prod02_path)
    if "p3_t1" not in xl.sheet_names:
        return pd.DataFrame(columns=["metric_name_cleaned", "year", "value", "unit", "statement_type"])
    df = pd.read_excel(prod02_path, sheet_name="p3_t1").fillna("")
    col_map = {c: _norm(c) for c in df.columns}
    # We expect these columns in p3_t1
    c_left_m1 = "0"
    c_left_m2 = "1"
    c_left_years = ["2", "4", "5", "6", "7"]
    c_right_m = "9"
    c_right_years = ["10", "11", "12", "14", "15"]
    if not all(c in col_map for c in [c_left_m1, c_left_m2, c_right_m]):
        return pd.DataFrame(columns=["metric_name_cleaned", "year", "value", "unit", "statement_type"])

    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        # Left block (balance + cashflow)
        left_metric = _extract_metric_label_from_row(r.get(c_left_m1, ""), r.get(c_left_m2, ""))
        if left_metric and all(_norm(r.get(y, "")) not in YEAR_COLUMNS for y in c_left_years):
            for yl, c in zip(YEAR_COLUMNS, c_left_years):
                v = _canonical_num(r.get(c, ""))
                if not v or not VALUE_VALID_RE.fullmatch(v):
                    continue
                stype = "资产负债表"
                if "现金流" in left_metric or left_metric in {
                    "经营活动现金流",
                    "投资活动现金流",
                    "筹资活动现金流",
                    "资本支出",
                    "现金净增加额",
                    "营运资金变动",
                    "其他经营现金流",
                    "其他投资现金流",
                    "其他筹资现金流",
                    "折旧摊销",
                    "投资损失",
                    "普通股增加",
                }:
                    stype = "现金流量表"
                rows.append(
                    {
                        "metric_name_cleaned": left_metric,
                        "year": yl,
                        "value": v,
                        "unit": "百万元",
                        "statement_type": stype,
                    }
                )

        # Right block (income + ratio)
        right_metric = _norm(r.get(c_right_m, "")).replace("（", "(").replace("）", ")").replace(" ", "")
        if right_metric and right_metric not in {"利润表(百万元)", "主要财务比率", "成长能力", "获利能力", "偿债能力", "营运能力", "每股指标(元)", "估值比率"}:
            for yl, c in zip(YEAR_COLUMNS, c_right_years):
                v = _canonical_num(r.get(c, ""))
                if not v or not VALUE_VALID_RE.fullmatch(v):
                    continue
                stype = "利润表"
                if any(x in right_metric for x in ["(%)", "比率", "P/E", "P/B", "EV/EBITDA", "每股"]):
                    stype = "主要财务比率"
                rows.append(
                    {
                        "metric_name_cleaned": right_metric,
                        "year": yl,
                        "value": v,
                        "unit": "ratio" if stype == "主要财务比率" else "百万元",
                        "statement_type": stype,
                    }
                )
    out = pd.DataFrame(rows).fillna("")
    return out


def _diff_candidate_vs_production(
    cand_df: pd.DataFrame,
    prod_df: pd.DataFrame,
    include_standard_metric: bool,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    c = cand_df.copy().fillna("")
    p = prod_df.copy().fillna("")
    for col in ["metric_name_cleaned", "year", "value", "unit", "statement_type", "standard_metric"]:
        if col not in c.columns:
            c[col] = ""
        if col not in p.columns:
            p[col] = ""

    if include_standard_metric:
        c["base_key"] = c["standard_metric"].map(_compact) + "||" + c["year"].map(_compact)
        p["base_key"] = p["standard_metric"].map(_compact) + "||" + p["year"].map(_compact)
    else:
        c["base_key"] = c["metric_name_cleaned"].map(_compact) + "||" + c["year"].map(_compact)
        p["base_key"] = p["metric_name_cleaned"].map(_compact) + "||" + p["year"].map(_compact)

    c["exact_key"] = c["base_key"] + "||" + c["value"].map(_canonical_num) + "||" + c["unit"].map(_compact)
    p["exact_key"] = p["base_key"] + "||" + p["value"].map(_canonical_num) + "||" + p["unit"].map(_compact)

    prod_base_map: Dict[str, List[Dict[str, str]]] = {}
    for _, r in p.iterrows():
        prod_base_map.setdefault(_norm(r["base_key"]), []).append(r.to_dict())
    prod_exact_set: Set[str] = set(p["exact_key"].map(_norm).tolist())

    dup_keys = set(c.groupby("base_key")["value"].nunique(dropna=False).loc[lambda s: s > 1].index.tolist())

    rows: List[Dict[str, Any]] = []
    same_count = 0
    new_count = 0
    diff_count = 0
    duplicate_count = 0
    for _, r in c.iterrows():
        base = _norm(r.get("base_key"))
        exact = _norm(r.get("exact_key"))
        diff_class = "NEW_RECORD"
        diff_reason = "base_key_not_in_production"
        if base in dup_keys:
            diff_class = "DUPLICATE_CANDIDATE"
            diff_reason = "multiple_candidate_values_same_metric_year"
            duplicate_count += 1
            diff_count += 1
        elif exact in prod_exact_set:
            diff_class = "SAME_AS_PRODUCTION"
            diff_reason = "exact_match_metric_year_value_unit"
            same_count += 1
        elif base in prod_base_map:
            p0 = prod_base_map[base][0]
            pv = _canonical_num(p0.get("value", ""))
            pu = _compact(p0.get("unit", ""))
            cv = _canonical_num(r.get("value", ""))
            cu = _compact(r.get("unit", ""))
            if cv != pv and cu == pu:
                diff_class = "VALUE_CHANGED"
                diff_reason = "value_changed_same_metric_year"
            elif cv == pv and cu != pu:
                diff_class = "UNIT_CHANGED"
                diff_reason = "unit_changed_same_metric_year"
            else:
                diff_class = "VALUE_CHANGED"
                diff_reason = "value_or_unit_changed_same_metric_year"
            diff_count += 1
        else:
            new_count += 1
            diff_count += 1
        rows.append(
            {
                "metric_name_cleaned": _norm(r.get("metric_name_cleaned")),
                "standard_metric": _norm(r.get("standard_metric")),
                "year": _norm(r.get("year")),
                "candidate_value": _norm(r.get("value")),
                "candidate_unit": _norm(r.get("unit")),
                "statement_type": _norm(r.get("statement_type")),
                "diff_class": diff_class,
                "diff_reason": diff_reason,
            }
        )
    out_df = pd.DataFrame(rows).fillna("")
    stats = {
        "same_as_production_count": int(same_count),
        "new_record_count": int(new_count),
        "diff_count": int(diff_count),
        "duplicate_candidate_count": int(duplicate_count),
    }
    return out_df, stats


def _metric_level_review(candidate05_df: pd.DataFrame) -> pd.DataFrame:
    df = candidate05_df.copy().fillna("")
    df["metric_level_key"] = (
        df["raw_metric_name"].map(_norm) + "||" + df["statement_type"].map(_norm) + "||" + df["unit"].map(_norm)
    )
    rows: List[Dict[str, Any]] = []
    for key, grp in df.groupby("metric_level_key", sort=True):
        actions = list(set(grp["review_action"].map(_norm).tolist()))
        action = "BLOCKED"
        reason = "mixed_or_unknown_actions"
        if actions == ["PROMOTE_TO_05_SAFE"] or set(actions) == {"PROMOTE_TO_05_SAFE"}:
            action = "PROMOTE_TO_05_SAFE"
            reason = "all_rows_standardized_ok"
        elif "NEED_SCOPE_REVIEW" in actions:
            action = "NEED_SCOPE_REVIEW"
            reason = "scope_or_business_definition_review_needed"
        elif "NEED_MAPPING_RULE" in actions:
            action = "NEED_MAPPING_RULE"
            reason = "mapping_rule_missing"
        elif "DEFER_DERIVED_METRIC" in actions:
            action = "DEFER_DERIVED_METRIC"
            reason = "derived_metric_deferred"
        elif "PROMOTE_TO_02_ONLY" in actions:
            action = "PROMOTE_TO_02_ONLY"
            reason = "structured_metric_keep_in_02_only"
        elif "BLOCKED" in actions:
            action = "BLOCKED"
            reason = "value_or_schema_issue"

        years = sorted(set(grp["year"].map(_norm).tolist()))
        rows.append(
            {
                "metric_level_key": key,
                "raw_metric_name": _norm(grp.iloc[0]["raw_metric_name"]),
                "metric_name_cleaned": _norm(grp.iloc[0]["metric_name_cleaned"]),
                "statement_type": _norm(grp.iloc[0]["statement_type"]),
                "unit": _norm(grp.iloc[0]["unit"]),
                "row_count": int(len(grp)),
                "year_count": int(len(years)),
                "years": ",".join(years),
                "row_review_action_counts": json.dumps(grp["review_action"].value_counts().to_dict(), ensure_ascii=False),
                "recommended_action": action,
                "action_reason": reason,
            }
        )
    return pd.DataFrame(rows).fillna("")


def _metric_row_count(metric_df: pd.DataFrame, metric_name: str, stype: str, unit: str) -> int:
    hit = metric_df[
        (metric_df["raw_metric_name"].map(_norm) == metric_name)
        & (metric_df["statement_type"].map(_norm) == stype)
        & (metric_df["unit"].map(_norm) == unit)
    ]
    if hit.empty:
        return 0
    return int(hit.iloc[0]["row_count"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5Q fix apply precheck metric merge and production diff references.")
    parser.parse_args()

    required = [
        INPUT_CANDIDATE_02_XLSX,
        INPUT_CANDIDATE_05_XLSX,
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
    wrong_ref_detected = _wrong_reference_file_detected(stage5o_summary)

    cand02 = pd.read_excel(INPUT_CANDIDATE_02_XLSX, sheet_name=0).fillna("")
    cand05_old = pd.read_excel(INPUT_CANDIDATE_05_XLSX, sheet_name=0).fillna("")

    # Before counts (for problem metrics).
    before_metric_df = _metric_level_review(cand05_old)
    before_asset_rows = _metric_row_count(before_metric_df, "流动资产", "资产负债表", "百万元")
    before_liability_rows = _metric_row_count(before_metric_df, "流动负债", "资产负债表", "百万元")
    before_cf_rows = _metric_row_count(before_metric_df, "投资活动现金流", "现金流量表", "百万元")

    fixed_cand02, fix_log_df = _fix_problem_raw_metric_name(cand02)
    fixed_cand05 = _rebuild_candidate_05(fixed_cand02)
    fixed_metric_df = _metric_level_review(fixed_cand05)

    # After counts (should become 5).
    after_asset_rows = _metric_row_count(fixed_metric_df, "流动资产", "资产负债表", "百万元")
    after_noncurrent_asset_rows = _metric_row_count(fixed_metric_df, "非流动资产", "资产负债表", "百万元")
    after_liability_rows = _metric_row_count(fixed_metric_df, "流动负债", "资产负债表", "百万元")
    after_noncurrent_liability_rows = _metric_row_count(fixed_metric_df, "非流动负债", "资产负债表", "百万元")
    after_investing_rows = _metric_row_count(fixed_metric_df, "投资活动现金流", "现金流量表", "百万元")
    after_financing_rows = _metric_row_count(fixed_metric_df, "筹资活动现金流", "现金流量表", "百万元")

    merged_current_noncurrent_asset_fixed = bool(
        before_asset_rows >= 10 and after_asset_rows == 5 and after_noncurrent_asset_rows == 5
    )
    merged_current_noncurrent_liability_fixed = bool(
        before_liability_rows >= 10 and after_liability_rows == 5 and after_noncurrent_liability_rows == 5
    )
    merged_investing_financing_cashflow_fixed = bool(
        before_cf_rows >= 10 and after_investing_rows == 5 and after_financing_rows == 5
    )

    # true production refs
    p02_found, p05_found, prod02_path, prod05_path = _find_true_production_ref_files()
    prod02_long = _parse_production_02_to_long(prod02_path) if prod02_path else pd.DataFrame()
    prod05_long = _parse_production_05_to_long(prod05_path) if prod05_path else pd.DataFrame()

    # build fixed diff
    cand02_cmp = fixed_cand02[["metric_name_cleaned", "year", "value", "unit", "statement_type"]].copy()
    cand05_cmp = fixed_cand05[
        ["metric_name_cleaned", "standard_metric", "year", "value", "unit", "statement_type"]
    ].copy()
    diff02_df, diff02_stats = _diff_candidate_vs_production(cand02_cmp, prod02_long, include_standard_metric=False)
    diff05_df, diff05_stats = _diff_candidate_vs_production(cand05_cmp, prod05_long, include_standard_metric=True)

    same_as_production_zero_due_schema_issue_after = bool(
        (diff02_stats["same_as_production_count"] == 0 or len(prod02_long) == 0)
        and (diff05_stats["same_as_production_count"] == 0 or len(prod05_long) == 0)
        and ((len(prod02_long) == 0) or (len(prod05_long) == 0))
    )

    remaining_metric_row_count_not_5 = int((fixed_metric_df["row_count"] != 5).sum()) if not fixed_metric_df.empty else 0

    # reclassified statuses
    def _metric_status(metric: str) -> str:
        hit = fixed_metric_df[fixed_metric_df["metric_name_cleaned"].map(_norm) == metric]
        if hit.empty:
            return "NOT_FOUND"
        return _norm(hit.iloc[0]["recommended_action"])

    reclassified_net_profit_status = _metric_status("净利润")
    reclassified_operating_profit_status = _metric_status("营业利润")
    reclassified_ebitda_status = _metric_status("EBITDA")

    action_counts = fixed_metric_df["recommended_action"].value_counts().to_dict() if not fixed_metric_df.empty else {}
    promote_to_05_safe_metric_count = int(action_counts.get("PROMOTE_TO_05_SAFE", 0))
    promote_to_02_only_metric_count = int(action_counts.get("PROMOTE_TO_02_ONLY", 0))
    need_mapping_rule_metric_count = int(action_counts.get("NEED_MAPPING_RULE", 0))
    need_scope_review_metric_count = int(action_counts.get("NEED_SCOPE_REVIEW", 0))
    blocked_metric_count = int(action_counts.get("BLOCKED", 0))

    ready_for_stage5r_apply_review = bool(
        p02_found
        and p05_found
        and merged_current_noncurrent_asset_fixed
        and merged_current_noncurrent_liability_fixed
        and merged_investing_financing_cashflow_fixed
        and blocked_metric_count == 0
    )

    # reports
    problem_metric_report_df = pd.DataFrame(
        [
            {
                "problem_metric": "流动资产/非流动资产",
                "before_row_count_flow": before_asset_rows,
                "after_row_count_flow": after_asset_rows,
                "after_row_count_noncurrent": after_noncurrent_asset_rows,
                "fixed": merged_current_noncurrent_asset_fixed,
            },
            {
                "problem_metric": "流动负债/非流动负债",
                "before_row_count_flow": before_liability_rows,
                "after_row_count_flow": after_liability_rows,
                "after_row_count_noncurrent": after_noncurrent_liability_rows,
                "fixed": merged_current_noncurrent_liability_fixed,
            },
            {
                "problem_metric": "投资活动现金流/筹资活动现金流",
                "before_row_count_flow": before_cf_rows,
                "after_row_count_flow": after_investing_rows,
                "after_row_count_noncurrent": after_financing_rows,
                "fixed": merged_investing_financing_cashflow_fixed,
            },
            {
                "problem_metric": "净利润",
                "before_row_count_flow": "",
                "after_row_count_flow": "",
                "after_row_count_noncurrent": "",
                "fixed": reclassified_net_profit_status,
            },
            {
                "problem_metric": "营业利润",
                "before_row_count_flow": "",
                "after_row_count_flow": "",
                "after_row_count_noncurrent": "",
                "fixed": reclassified_operating_profit_status,
            },
            {
                "problem_metric": "EBITDA",
                "before_row_count_flow": "",
                "after_row_count_flow": "",
                "after_row_count_noncurrent": "",
                "fixed": reclassified_ebitda_status,
            },
        ]
    )

    _write_excel(
        OUT_FIXED_METRIC_REVIEW_XLSX,
        {
            "fixed_metric_level_review": fixed_metric_df.sort_values(
                ["recommended_action", "statement_type", "raw_metric_name"]
            ),
            "fixed_candidate_02": fixed_cand02,
            "fixed_candidate_05": fixed_cand05,
        },
    )
    _write_excel(
        OUT_FIXED_DIFF_XLSX,
        {
            "fixed_diff_with_production_02": diff02_df,
            "fixed_diff_with_production_05": diff05_df,
            "production_02_long_reference": prod02_long,
            "production_05_long_reference": prod05_long,
        },
    )
    _write_excel(
        OUT_PROBLEM_FIX_XLSX,
        {
            "problem_metric_fix": problem_metric_report_df,
            "raw_metric_fix_log": fix_log_df,
            "before_metric_level_review": before_metric_df,
            "after_metric_level_review": fixed_metric_df,
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
    formal_rules_unchanged = bool(
        before["formal_scope_rules"] == after["formal_scope_rules"]
        and before["formal_mapping_rules"] == after["formal_mapping_rules"]
        and before["formal_normalization_rules"] == after["formal_normalization_rules"]
        and before["formal_alias_rules"] == after["formal_alias_rules"]
    )
    official_02B_unchanged = bool(before["02B"] == after["02B"])

    summary = {
        "production_02_reference_found": bool(p02_found),
        "production_05_reference_found": bool(p05_found),
        "production_02_reference_file": str(prod02_path) if prod02_path else "",
        "production_05_reference_file": str(prod05_path) if prod05_path else "",
        "wrong_reference_file_detected": bool(wrong_ref_detected),
        "same_as_production_zero_due_schema_issue_after": bool(same_as_production_zero_due_schema_issue_after),
        "merged_current_noncurrent_asset_fixed": bool(merged_current_noncurrent_asset_fixed),
        "merged_current_noncurrent_liability_fixed": bool(merged_current_noncurrent_liability_fixed),
        "merged_investing_financing_cashflow_fixed": bool(merged_investing_financing_cashflow_fixed),
        "remaining_metric_row_count_not_5": int(remaining_metric_row_count_not_5),
        "reclassified_net_profit_status": str(reclassified_net_profit_status),
        "reclassified_operating_profit_status": str(reclassified_operating_profit_status),
        "reclassified_ebitda_status": str(reclassified_ebitda_status),
        "promote_to_05_safe_metric_count": int(promote_to_05_safe_metric_count),
        "promote_to_02_only_metric_count": int(promote_to_02_only_metric_count),
        "need_mapping_rule_metric_count": int(need_mapping_rule_metric_count),
        "need_scope_review_metric_count": int(need_scope_review_metric_count),
        "blocked_metric_count": int(blocked_metric_count),
        "ready_for_stage5r_apply_review": bool(ready_for_stage5r_apply_review),
        "production_files_unchanged": bool(production_files_unchanged),
        "official_02B_unchanged": bool(official_02B_unchanged),
        "formal_rules_unchanged": bool(formal_rules_unchanged),
        "ai_called": False,
        "internet_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "stage5q_apply_precheck_fix_pass": False,
    }

    summary["stage5q_apply_precheck_fix_pass"] = bool(
        summary["production_02_reference_found"]
        and summary["production_05_reference_found"]
        and summary["merged_current_noncurrent_asset_fixed"]
        and summary["merged_current_noncurrent_liability_fixed"]
        and summary["merged_investing_financing_cashflow_fixed"]
        and summary["remaining_metric_row_count_not_5"] == 0
        and summary["production_files_unchanged"]
        and summary["official_02B_unchanged"]
        and summary["formal_rules_unchanged"]
        and (summary["ai_called"] is False)
        and (summary["internet_called"] is False)
        and (summary["factory_core_called"] is False)
        and (summary["ocr_called"] is False)
    )

    md_lines = [
        "# Stage5Q Apply Precheck Fix",
        "",
        "## Production Reference",
        f"- production_02_reference_found: {summary['production_02_reference_found']}",
        f"- production_05_reference_found: {summary['production_05_reference_found']}",
        f"- production_02_reference_file: {summary['production_02_reference_file']}",
        f"- production_05_reference_file: {summary['production_05_reference_file']}",
        f"- wrong_reference_file_detected: {summary['wrong_reference_file_detected']}",
        f"- same_as_production_zero_due_schema_issue_after: {summary['same_as_production_zero_due_schema_issue_after']}",
        "",
        "## Problem Metric Fix",
        f"- merged_current_noncurrent_asset_fixed: {summary['merged_current_noncurrent_asset_fixed']}",
        f"- merged_current_noncurrent_liability_fixed: {summary['merged_current_noncurrent_liability_fixed']}",
        f"- merged_investing_financing_cashflow_fixed: {summary['merged_investing_financing_cashflow_fixed']}",
        f"- remaining_metric_row_count_not_5: {summary['remaining_metric_row_count_not_5']}",
        "",
        "## Reclassification",
        f"- reclassified_net_profit_status: {summary['reclassified_net_profit_status']}",
        f"- reclassified_operating_profit_status: {summary['reclassified_operating_profit_status']}",
        f"- reclassified_ebitda_status: {summary['reclassified_ebitda_status']}",
        "",
        "## Metric-Level Decision",
        f"- promote_to_05_safe_metric_count: {summary['promote_to_05_safe_metric_count']}",
        f"- promote_to_02_only_metric_count: {summary['promote_to_02_only_metric_count']}",
        f"- need_mapping_rule_metric_count: {summary['need_mapping_rule_metric_count']}",
        f"- need_scope_review_metric_count: {summary['need_scope_review_metric_count']}",
        f"- blocked_metric_count: {summary['blocked_metric_count']}",
        "",
        "## Decision",
        f"- ready_for_stage5r_apply_review: {summary['ready_for_stage5r_apply_review']}",
        f"- stage5q_apply_precheck_fix_pass: {summary['stage5q_apply_precheck_fix_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5q_fixed_metric_level_review_xlsx: {OUT_FIXED_METRIC_REVIEW_XLSX}")
    print(f"stage5q_fixed_diff_xlsx: {OUT_FIXED_DIFF_XLSX}")
    print(f"stage5q_problem_fix_xlsx: {OUT_PROBLEM_FIX_XLSX}")
    print(f"stage5q_report_md: {OUT_REPORT_MD}")
    print(f"stage5q_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5q_apply_precheck_fix_pass: {summary['stage5q_apply_precheck_fix_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
