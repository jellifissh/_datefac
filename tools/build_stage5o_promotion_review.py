import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import financial_standardizer as fs


BASE_DIR = Path(r"D:\_datefac")
OUTPUT_DIR = BASE_DIR / "output"
DELIVERY_DIR = OUTPUT_DIR / "delivery_package"

INPUT_STAGE5N_DIR = OUTPUT_DIR / "stage5n_wide_review_layout_fix"
INPUT_WIDE_XLSX = INPUT_STAGE5N_DIR / "152_stage5n_clean_wide_financial_tables_by_sheet.xlsx"
INPUT_02_XLSX = INPUT_STAGE5N_DIR / "152_stage5n_structured_02_from_wide.xlsx"
INPUT_05_XLSX = INPUT_STAGE5N_DIR / "152_stage5n_standardized_05_from_wide.xlsx"
INPUT_CROSSCHECK_XLSX = INPUT_STAGE5N_DIR / "152_stage5n_valuation_summary_crosscheck.xlsx"
INPUT_STAGE5N_SUMMARY_JSON = INPUT_STAGE5N_DIR / "153_stage5n_wide_layout_summary.json"

OFFICIAL_02B_PATH = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES_JSON = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
FORMAL_MAPPING_RULE_FILE = FORMAL_SCOPE_RULES_JSON
FORMAL_NORMALIZATION_RULE_FILE = BASE_DIR / "financial_standardizer.py"
FORMAL_ALIAS_RULE_FILE = BASE_DIR / "financial_standardizer.py"

OUT_DIR = OUTPUT_DIR / "stage5o_promotion_review"
OUT_CANDIDATE_02_XLSX = OUT_DIR / "154_stage5o_candidate_02.xlsx"
OUT_CANDIDATE_05_XLSX = OUT_DIR / "154_stage5o_candidate_05.xlsx"
OUT_REVIEW_XLSX = OUT_DIR / "154_stage5o_promotion_review.xlsx"
OUT_DIFF_XLSX = OUT_DIR / "154_stage5o_diff_with_production_02_05.xlsx"
OUT_REPORT_MD = OUT_DIR / "154_stage5o_promotion_review_report.md"
OUT_SUMMARY_JSON = OUT_DIR / "155_stage5o_promotion_review_summary.json"

INPUT_PDF = BASE_DIR / "input" / "H3_AP202605121822223662_1.pdf"
YEAR_COLUMNS = ["2024A", "2025A", "2026E", "2027E", "2028E"]
YEAR_TOKEN_RE = re.compile(r"^20\d{2}(?:[AE])?$", re.IGNORECASE)
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


def _canonical_num_token(v: Any) -> str:
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


def _find_production_reference_file(kind: str) -> Path:
    # Prefer canonical names; fallback to current delivery package variants.
    if kind == "02":
        candidates: Sequence[Path] = [
            DELIVERY_DIR / "02_研报全量结构化数据.xlsx",
            DELIVERY_DIR / "02_人工复核指标队列.xlsx",
        ]
    elif kind == "05":
        candidates = [
            DELIVERY_DIR / "05_核心财务指标标准化.xlsx",
            DELIVERY_DIR / "05_表格区域截图索引.xlsx",
        ]
    else:
        raise ValueError(kind)
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"Cannot find production reference file for {kind}")


def _iter_metric_year_value_rows(df: pd.DataFrame) -> List[Dict[str, str]]:
    metric_cols = ["metric_name_cleaned", "raw_metric_name", "standard_metric", "source_row_label", "metric_name", "指标", "指标名称"]
    year_cols = ["year", "年份", "报告期"]
    value_cols = ["value", "corrected_value", "metric_value", "数值", "指标值"]
    unit_cols = ["unit", "corrected_unit", "单位"]
    statement_cols = ["statement_type", "报表类型"]
    standard_cols = ["standard_metric", "标准指标"]

    rows: List[Dict[str, str]] = []
    for _, r in df.iterrows():
        metric = ""
        for c in metric_cols:
            if c in df.columns and _norm(r.get(c)):
                metric = _norm(r.get(c))
                break
        year = ""
        for c in year_cols:
            if c in df.columns and _norm(r.get(c)):
                year = _norm(r.get(c))
                break
        if not year:
            continue
        year_compact = _compact(year)
        if year_compact in {"2024", "2025", "2026", "2027", "2028"}:
            year = f"{year_compact}A" if year_compact in {"2024", "2025"} else f"{year_compact}E"
        elif YEAR_TOKEN_RE.fullmatch(year_compact):
            year = year_compact
        else:
            continue

        value = ""
        for c in value_cols:
            if c in df.columns and _norm(r.get(c)):
                value = _canonical_num_token(r.get(c))
                break
        unit = ""
        for c in unit_cols:
            if c in df.columns and _norm(r.get(c)):
                unit = _norm(r.get(c))
                break
        statement_type = ""
        for c in statement_cols:
            if c in df.columns and _norm(r.get(c)):
                statement_type = _norm(r.get(c))
                break
        standard_metric = ""
        for c in standard_cols:
            if c in df.columns and _norm(r.get(c)):
                standard_metric = _norm(r.get(c))
                break
        rows.append(
            {
                "metric_name_cleaned": metric,
                "year": year,
                "value": value,
                "unit": unit,
                "statement_type": statement_type,
                "standard_metric": standard_metric,
            }
        )
    return rows


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


def _classify_mapping_miss(metric: str) -> str:
    t = _norm(metric)
    if any(x in t for x in ["(%)", "%", "周转率", "ROIC", "资产负债率", "净利率"]):
        return "DEFER_DERIVED_METRIC"
    if any(x in t for x in ["营业利润", "净利润", "EBITDA"]):
        return "FILTER_NON_CORE_METRIC"
    return "NEED_MAPPING_OR_ALIAS_REVIEW"


def _build_candidate_02_from_wide(
    detail_wide_df: pd.DataFrame,
    valuation_df: pd.DataFrame,
    cross_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    valuation_review_rows: List[Dict[str, Any]] = []

    # Detailed tables are the primary data source.
    for _, r in detail_wide_df.iterrows():
        metric = _norm(r.get("metric_name_cleaned")) or _norm(r.get("raw_metric_name"))
        if not metric:
            continue
        for yl in YEAR_COLUMNS:
            v = _canonical_num_token(r.get(yl))
            if not v or not VALUE_VALID_RE.fullmatch(v):
                continue
            rows.append(
                {
                    "asset_package": INPUT_PDF.stem,
                    "source_pdf": str(INPUT_PDF),
                    "source_page": _norm(r.get("source_page")),
                    "source_sheet": _norm(r.get("statement_type")),
                    "source_table_id": _norm(r.get("source_raw_table_id")),
                    "source_row_index": _norm(r.get("source_row_index")),
                    "semantic_table_id": _norm(r.get("semantic_table_id")),
                    "raw_metric_name": _norm(r.get("raw_metric_name")),
                    "metric_name_cleaned": metric,
                    "statement_type": _norm(r.get("statement_type")),
                    "unit": _norm(r.get("unit")),
                    "year": yl,
                    "value": v,
                    "source_reference": f"{_norm(r.get('source_raw_table_id'))}:r{_norm(r.get('source_row_index'))}:y{yl}",
                    "candidate_action": "PROMOTE_TO_02_CANDIDATE",
                    "promotion_reason": "detail_tables_primary_source",
                }
            )

    # Valuation summary: reference-only for duplicated/consistent metrics.
    detail_metric_set = set(detail_wide_df["metric_name_cleaned"].map(_norm).tolist())
    detail_value_sig_set = set(
        detail_wide_df[YEAR_COLUMNS].apply(lambda rr: "|".join(_canonical_num_token(rr.get(y)) for y in YEAR_COLUMNS), axis=1).tolist()
    ) if not detail_wide_df.empty else set()

    consistent_metric_keys = set()
    conflict_metric_keys = set()
    if not cross_df.empty:
        for _, r in cross_df.iterrows():
            m = _norm(r.get("valuation_summary_metric_name"))
            if not m:
                continue
            rs = _norm(r.get("crosscheck_result"))
            if rs == "CONSISTENT_WITH_DETAIL_TABLE":
                consistent_metric_keys.add(m)
            elif rs == "CONFLICT_WITH_DETAIL_TABLE":
                conflict_metric_keys.add(m)

    valuation_summary_reference_only_count = 0
    valuation_summary_review_required_count = 0
    valuation_summary_conflict_count = 0

    for _, r in valuation_df.iterrows():
        m = _norm(r.get("metric_name_cleaned"))
        sig = "|".join(_canonical_num_token(r.get(y)) for y in YEAR_COLUMNS)
        if m in conflict_metric_keys:
            valuation_summary_conflict_count += 1
            valuation_review_rows.append(
                {
                    "source_type": "valuation_summary",
                    "metric_name_cleaned": m,
                    "statement_type": _norm(r.get("statement_type")),
                    "source_row_index": _norm(r.get("source_row_index")),
                    "review_action": "BLOCKED_SUMMARY_DETAIL_CONFLICT",
                    "reason": "crosscheck_conflict_with_detail_table",
                    "value_signature": sig,
                }
            )
            continue

        if (m in detail_metric_set and m in consistent_metric_keys) or sig in detail_value_sig_set:
            valuation_summary_reference_only_count += 1
            valuation_review_rows.append(
                {
                    "source_type": "valuation_summary",
                    "metric_name_cleaned": m,
                    "statement_type": _norm(r.get("statement_type")),
                    "source_row_index": _norm(r.get("source_row_index")),
                    "review_action": "SUMMARY_CONSISTENT_REFERENCE_ONLY",
                    "reason": "duplicate_or_consistent_with_detail_table",
                    "value_signature": sig,
                }
            )
            continue

        # Rare case: not found in detail, keep for manual promotion review.
        valuation_summary_review_required_count += 1
        for yl in YEAR_COLUMNS:
            v = _canonical_num_token(r.get(yl))
            if not v or not VALUE_VALID_RE.fullmatch(v):
                continue
            rows.append(
                {
                    "asset_package": INPUT_PDF.stem,
                    "source_pdf": str(INPUT_PDF),
                    "source_page": _norm(r.get("source_page")),
                    "source_sheet": "valuation_summary",
                    "source_table_id": _norm(r.get("source_raw_table_id")),
                    "source_row_index": _norm(r.get("source_row_index")),
                    "semantic_table_id": _norm(r.get("semantic_table_id")),
                    "raw_metric_name": _norm(r.get("raw_metric_name")),
                    "metric_name_cleaned": m,
                    "statement_type": "valuation_summary",
                    "unit": _norm(r.get("unit")),
                    "year": yl,
                    "value": v,
                    "source_reference": f"{_norm(r.get('source_raw_table_id'))}:r{_norm(r.get('source_row_index'))}:y{yl}",
                    "candidate_action": "PROMOTION_REVIEW_REQUIRED",
                    "promotion_reason": "valuation_summary_metric_not_found_in_detail",
                }
            )
            valuation_review_rows.append(
                {
                    "source_type": "valuation_summary",
                    "metric_name_cleaned": m,
                    "statement_type": _norm(r.get("statement_type")),
                    "source_row_index": _norm(r.get("source_row_index")),
                    "review_action": "PROMOTION_REVIEW_REQUIRED",
                    "reason": "not_found_in_detail_table",
                    "value_signature": sig,
                }
            )

    candidate_02_df = pd.DataFrame(rows).fillna("")
    valuation_review_df = pd.DataFrame(valuation_review_rows).fillna("")

    stats = {
        "valuation_summary_reference_only_count": int(valuation_summary_reference_only_count),
        "valuation_summary_review_required_count": int(valuation_summary_review_required_count),
        "valuation_summary_conflict_count": int(valuation_summary_conflict_count),
    }
    return candidate_02_df, valuation_review_df, stats


def _standardize_candidate_05(candidate_02_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    for _, r in candidate_02_df.iterrows():
        metric = _norm(r.get("metric_name_cleaned")) or _norm(r.get("raw_metric_name"))
        year = _norm(r.get("year")).upper()
        value = _canonical_num_token(r.get("value"))
        unit = _norm(r.get("unit"))

        standard_metric = ""
        status = "STANDARDIZATION_FAILED"
        issue_type = "UNKNOWN"
        mapping_rule_id = ""
        alias_rule_id = ""
        review_action = ""
        review_reason = ""

        m = fs._match_standard_metric(metric)
        if not m:
            status = "MAPPING_MISS"
            issue_type = "METRIC_MAPPING_ISSUE"
            review_action = _classify_mapping_miss(metric)
            review_reason = "mapping_miss_after_clean_wide"
        else:
            standard_metric = _norm(m.get("standard_metric"))
            mapping_rule_id = f"FS_MAP_{_compact(standard_metric)}" if standard_metric else ""
            alias_rule_id = _build_alias_rule_id(standard_metric, metric)
            if not YEAR_TOKEN_RE.fullmatch(year):
                status = "YEAR_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                review_action = "NEED_MANUAL_REVIEW"
                review_reason = "year_invalid"
            elif not VALUE_VALID_RE.fullmatch(value):
                status = "VALUE_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                review_action = "NEED_MANUAL_REVIEW"
                review_reason = "value_invalid"
            elif not unit:
                status = "UNIT_INVALID"
                issue_type = "VALUE_UNIT_YEAR_ISSUE"
                review_action = "NEED_MANUAL_REVIEW"
                review_reason = "unit_missing"
            else:
                status = "STANDARDIZED_OK"
                issue_type = "NONE"
                review_action = "PROMOTE_TO_05_CANDIDATE"
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
                "statement_type": _norm(r.get("statement_type")),
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

    out_df = pd.DataFrame(rows).fillna("")
    standardized_ok = int((out_df["standardization_status"] == "STANDARDIZED_OK").sum()) if not out_df.empty else 0
    mapping_miss = int((out_df["standardization_status"] == "MAPPING_MISS").sum()) if not out_df.empty else 0

    true_gap_count = 0
    derived_metric_defer_count = 0
    non_core_filter_count = 0
    if mapping_miss > 0:
        mm = out_df[out_df["standardization_status"] == "MAPPING_MISS"]
        true_gap_count = int((mm["review_action"] == "NEED_MAPPING_OR_ALIAS_REVIEW").sum())
        derived_metric_defer_count = int((mm["review_action"] == "DEFER_DERIVED_METRIC").sum())
        non_core_filter_count = int((mm["review_action"] == "FILTER_NON_CORE_METRIC").sum())

    stats = {
        "candidate_05_row_count": int(len(out_df)),
        "candidate_05_standardized_ok_count": int(standardized_ok),
        "candidate_05_mapping_miss_count": int(mapping_miss),
        "candidate_05_true_mapping_gap_count": int(true_gap_count),
        "derived_metric_defer_count": int(derived_metric_defer_count),
        "non_core_filter_count": int(non_core_filter_count),
    }
    return out_df, stats


def _diff_long_tables(
    candidate_rows: List[Dict[str, str]],
    production_rows: List[Dict[str, str]],
    include_standard_metric: bool,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    candidate_df = pd.DataFrame(candidate_rows).fillna("")
    production_df = pd.DataFrame(production_rows).fillna("")

    for df in [candidate_df, production_df]:
        for c in ["metric_name_cleaned", "year", "value", "unit", "statement_type", "standard_metric"]:
            if c not in df.columns:
                df[c] = ""

    cdf = candidate_df.copy()
    pdf = production_df.copy()
    if include_standard_metric:
        cdf["base_key"] = cdf["standard_metric"].map(_compact) + "||" + cdf["year"].map(_compact)
        pdf["base_key"] = pdf["standard_metric"].map(_compact) + "||" + pdf["year"].map(_compact)
    else:
        cdf["base_key"] = cdf["metric_name_cleaned"].map(_compact) + "||" + cdf["year"].map(_compact)
        pdf["base_key"] = pdf["metric_name_cleaned"].map(_compact) + "||" + pdf["year"].map(_compact)
    cdf["exact_key"] = cdf["base_key"] + "||" + cdf["value"].map(_canonical_num_token) + "||" + cdf["unit"].map(_compact)
    pdf["exact_key"] = pdf["base_key"] + "||" + pdf["value"].map(_canonical_num_token) + "||" + pdf["unit"].map(_compact)

    prod_base_map: Dict[str, List[Dict[str, str]]] = {}
    for _, r in pdf.iterrows():
        prod_base_map.setdefault(_norm(r["base_key"]), []).append(r.to_dict())
    prod_exact_set = set(pdf["exact_key"].map(_norm).tolist())

    diff_rows: List[Dict[str, Any]] = []
    same_count = 0
    new_count = 0
    diff_count = 0

    dup_map = cdf.groupby("base_key")["value"].nunique(dropna=False)
    duplicate_keys = set(dup_map[dup_map > 1].index.tolist())

    for _, r in cdf.iterrows():
        base = _norm(r["base_key"])
        exact = _norm(r["exact_key"])
        cls = "NEW_RECORD"
        reason = "base_key_not_in_production"

        if base in duplicate_keys:
            cls = "DUPLICATE_CANDIDATE"
            reason = "multiple_candidate_values_same_metric_year"
            diff_count += 1
        elif exact in prod_exact_set:
            cls = "SAME_AS_PRODUCTION"
            reason = "exact_match_metric_year_value_unit"
            same_count += 1
        elif base in prod_base_map:
            # Compare against first row with same base.
            p0 = prod_base_map[base][0]
            pv = _canonical_num_token(p0.get("value", ""))
            pu = _compact(p0.get("unit", ""))
            cv = _canonical_num_token(r.get("value", ""))
            cu = _compact(r.get("unit", ""))
            if cv != pv and cu == pu:
                cls = "VALUE_CHANGED"
                reason = "value_changed_same_metric_year"
            elif cv == pv and cu != pu:
                cls = "UNIT_CHANGED"
                reason = "unit_changed_same_metric_year"
            else:
                cls = "VALUE_CHANGED"
                reason = "value_or_unit_changed_same_metric_year"
            diff_count += 1
        else:
            new_count += 1
            diff_count += 1

        diff_rows.append(
            {
                "metric_name_cleaned": _norm(r.get("metric_name_cleaned")),
                "standard_metric": _norm(r.get("standard_metric")),
                "year": _norm(r.get("year")),
                "candidate_value": _norm(r.get("value")),
                "candidate_unit": _norm(r.get("unit")),
                "statement_type": _norm(r.get("statement_type")),
                "diff_class": cls,
                "diff_reason": reason,
            }
        )

    c_base_set = set(cdf["base_key"].map(_norm).tolist())
    only_prod_count = 0
    for _, r in pdf.iterrows():
        base = _norm(r.get("base_key"))
        if base and base not in c_base_set:
            only_prod_count += 1
            diff_rows.append(
                {
                    "metric_name_cleaned": _norm(r.get("metric_name_cleaned")),
                    "standard_metric": _norm(r.get("standard_metric")),
                    "year": _norm(r.get("year")),
                    "candidate_value": "",
                    "candidate_unit": "",
                    "statement_type": _norm(r.get("statement_type")),
                    "diff_class": "ONLY_IN_PRODUCTION",
                    "diff_reason": "production_metric_year_absent_in_candidate",
                }
            )

    out_df = pd.DataFrame(diff_rows).fillna("")
    stats = {
        "same_as_production_count": int(same_count),
        "new_record_count": int(new_count),
        "diff_with_production_count": int(diff_count),
        "only_in_production_count": int(only_prod_count),
    }
    return out_df, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage5O build promotion candidates from Stage5N clean wide tables.")
    parser.parse_args()

    required = [
        INPUT_WIDE_XLSX,
        INPUT_02_XLSX,
        INPUT_05_XLSX,
        INPUT_CROSSCHECK_XLSX,
        INPUT_STAGE5N_SUMMARY_JSON,
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

    stage5n_summary = json.loads(INPUT_STAGE5N_SUMMARY_JSON.read_text(encoding="utf-8"))
    xl = pd.ExcelFile(INPUT_WIDE_XLSX)
    input_clean_wide_sheet_count = int(len(xl.sheet_names))

    balance_df = pd.read_excel(INPUT_WIDE_XLSX, sheet_name="balance_sheet").fillna("")
    income_df = pd.read_excel(INPUT_WIDE_XLSX, sheet_name="income_statement").fillna("")
    cash_df = pd.read_excel(INPUT_WIDE_XLSX, sheet_name="cash_flow_statement").fillna("")
    ratio_df = pd.read_excel(INPUT_WIDE_XLSX, sheet_name="financial_ratio").fillna("")
    valuation_df = pd.read_excel(INPUT_WIDE_XLSX, sheet_name="valuation_summary").fillna("")
    cross_df = pd.read_excel(INPUT_CROSSCHECK_XLSX, sheet_name=0).fillna("")

    detail_wide_df = pd.concat([balance_df, income_df, cash_df, ratio_df], ignore_index=True).fillna("")
    input_clean_wide_metric_row_count = int(len(detail_wide_df) + len(valuation_df))

    candidate_02_df, valuation_review_df, valuation_stats = _build_candidate_02_from_wide(detail_wide_df, valuation_df, cross_df)
    candidate_02_row_count = int(len(candidate_02_df))

    candidate_05_df, c05_stats = _standardize_candidate_05(candidate_02_df)

    # Production references and diffs.
    production_02_path = _find_production_reference_file("02")
    production_05_path = _find_production_reference_file("05")
    prod02_df = pd.read_excel(production_02_path, sheet_name=0).fillna("")
    prod05_df = pd.read_excel(production_05_path, sheet_name=0).fillna("")
    prod02_rows = _iter_metric_year_value_rows(prod02_df)
    prod05_rows = _iter_metric_year_value_rows(prod05_df)

    cand02_rows = candidate_02_df[
        ["metric_name_cleaned", "year", "value", "unit", "statement_type"]
    ].to_dict("records") if not candidate_02_df.empty else []
    c02_diff_df, c02_diff_stats = _diff_long_tables(cand02_rows, prod02_rows, include_standard_metric=False)

    cand05_rows = candidate_05_df[
        ["metric_name_cleaned", "standard_metric", "year", "value", "unit", "statement_type"]
    ].to_dict("records") if not candidate_05_df.empty else []
    c05_diff_df, c05_diff_stats = _diff_long_tables(cand05_rows, prod05_rows, include_standard_metric=True)

    # Review action aggregations.
    promote_to_02_candidate_count = int((candidate_02_df["candidate_action"] == "PROMOTE_TO_02_CANDIDATE").sum()) if not candidate_02_df.empty else 0
    promote_to_05_candidate_count = int((candidate_05_df["review_action"] == "PROMOTE_TO_05_CANDIDATE").sum()) if not candidate_05_df.empty else 0
    need_manual_review_count = int(
        (candidate_05_df["review_action"].isin(["NEED_MAPPING_OR_ALIAS_REVIEW", "NEED_MANUAL_REVIEW", "PROMOTION_REVIEW_REQUIRED"])).sum()
    ) + int(valuation_stats["valuation_summary_review_required_count"])
    blocked_count = int(valuation_stats["valuation_summary_conflict_count"])

    # Persist outputs.
    _write_excel(OUT_CANDIDATE_02_XLSX, {"candidate_02": candidate_02_df})
    _write_excel(OUT_CANDIDATE_05_XLSX, {"candidate_05": candidate_05_df})
    _write_excel(
        OUT_REVIEW_XLSX,
        {
            "promotion_review_actions": pd.concat(
                [
                    candidate_05_df[
                        [
                            "metric_name_cleaned",
                            "standard_metric",
                            "year",
                            "value",
                            "unit",
                            "statement_type",
                            "standardization_status",
                            "review_action",
                            "review_reason",
                            "source_reference",
                        ]
                    ] if not candidate_05_df.empty else pd.DataFrame(),
                    valuation_review_df[
                        [
                            "metric_name_cleaned",
                            "statement_type",
                            "review_action",
                            "reason",
                            "value_signature",
                        ]
                    ] if not valuation_review_df.empty else pd.DataFrame(),
                ],
                ignore_index=True,
            ).fillna(""),
            "valuation_summary_review": valuation_review_df,
            "summary_metrics": pd.DataFrame(
                [
                    {"metric": "production_02_reference_file", "value": str(production_02_path)},
                    {"metric": "production_05_reference_file", "value": str(production_05_path)},
                ]
            ),
        },
    )
    _write_excel(
        OUT_DIFF_XLSX,
        {
            "diff_with_production_02": c02_diff_df,
            "diff_with_production_05": c05_diff_df,
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

    ready_for_stage5p_apply_review = bool(
        c05_stats["candidate_05_standardized_ok_count"] > 0
        and valuation_stats["valuation_summary_conflict_count"] == 0
        and production_files_unchanged
        and official_02B_unchanged
        and formal_scope_rules_unchanged
        and formal_mapping_rules_unchanged
        and formal_normalization_rules_unchanged
        and formal_alias_rules_unchanged
    )
    recommended_next_stage = "STAGE5P_APPLY_REVIEW" if ready_for_stage5p_apply_review else "STAGE5P_BLOCKED_MANUAL_REVIEW"

    summary = {
        "input_clean_wide_sheet_count": int(input_clean_wide_sheet_count),
        "input_clean_wide_metric_row_count": int(input_clean_wide_metric_row_count),
        "candidate_02_row_count": int(candidate_02_row_count),
        "candidate_05_row_count": int(c05_stats["candidate_05_row_count"]),
        "candidate_05_standardized_ok_count": int(c05_stats["candidate_05_standardized_ok_count"]),
        "candidate_05_mapping_miss_count": int(c05_stats["candidate_05_mapping_miss_count"]),
        "candidate_05_true_mapping_gap_count": int(c05_stats["candidate_05_true_mapping_gap_count"]),
        "derived_metric_defer_count": int(c05_stats["derived_metric_defer_count"]),
        "non_core_filter_count": int(c05_stats["non_core_filter_count"]),
        "valuation_summary_reference_only_count": int(valuation_stats["valuation_summary_reference_only_count"]),
        "valuation_summary_review_required_count": int(valuation_stats["valuation_summary_review_required_count"]),
        "valuation_summary_conflict_count": int(valuation_stats["valuation_summary_conflict_count"]),
        "new_record_count_02": int(c02_diff_stats["new_record_count"]),
        "same_as_production_count_02": int(c02_diff_stats["same_as_production_count"]),
        "diff_with_production_02_count": int(c02_diff_stats["diff_with_production_count"]),
        "new_record_count_05": int(c05_diff_stats["new_record_count"]),
        "same_as_production_count_05": int(c05_diff_stats["same_as_production_count"]),
        "diff_with_production_05_count": int(c05_diff_stats["diff_with_production_count"]),
        "promote_to_02_candidate_count": int(promote_to_02_candidate_count),
        "promote_to_05_candidate_count": int(promote_to_05_candidate_count),
        "need_manual_review_count": int(need_manual_review_count),
        "blocked_count": int(blocked_count),
        "ready_for_stage5p_apply_review": bool(ready_for_stage5p_apply_review),
        "recommended_next_stage": str(recommended_next_stage),
        "production_02_reference_file": str(production_02_path),
        "production_05_reference_file": str(production_05_path),
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
        "stage5o_promotion_review_pass": False,
    }

    summary["stage5o_promotion_review_pass"] = bool(
        summary["input_clean_wide_metric_row_count"] > 0
        and summary["candidate_02_row_count"] > 0
        and summary["candidate_05_row_count"] > 0
        and summary["valuation_summary_conflict_count"] == 0
        and (
            summary["candidate_05_true_mapping_gap_count"] == 0
            or summary["need_manual_review_count"] >= summary["candidate_05_true_mapping_gap_count"]
        )
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
        "# Stage5O Promotion Review From Clean Wide Tables",
        "",
        "## Input",
        f"- input_clean_wide_sheet_count: {summary['input_clean_wide_sheet_count']}",
        f"- input_clean_wide_metric_row_count: {summary['input_clean_wide_metric_row_count']}",
        "",
        "## Candidates",
        f"- candidate_02_row_count: {summary['candidate_02_row_count']}",
        f"- candidate_05_row_count: {summary['candidate_05_row_count']}",
        f"- candidate_05_standardized_ok_count: {summary['candidate_05_standardized_ok_count']}",
        f"- candidate_05_mapping_miss_count: {summary['candidate_05_mapping_miss_count']}",
        f"- candidate_05_true_mapping_gap_count: {summary['candidate_05_true_mapping_gap_count']}",
        "",
        "## Valuation Summary Handling",
        f"- valuation_summary_reference_only_count: {summary['valuation_summary_reference_only_count']}",
        f"- valuation_summary_review_required_count: {summary['valuation_summary_review_required_count']}",
        f"- valuation_summary_conflict_count: {summary['valuation_summary_conflict_count']}",
        "",
        "## Diff",
        f"- production_02_reference_file: {summary['production_02_reference_file']}",
        f"- production_05_reference_file: {summary['production_05_reference_file']}",
        f"- same_as_production_count_02: {summary['same_as_production_count_02']}",
        f"- diff_with_production_02_count: {summary['diff_with_production_02_count']}",
        f"- same_as_production_count_05: {summary['same_as_production_count_05']}",
        f"- diff_with_production_05_count: {summary['diff_with_production_05_count']}",
        "",
        "## Decision",
        f"- promote_to_02_candidate_count: {summary['promote_to_02_candidate_count']}",
        f"- promote_to_05_candidate_count: {summary['promote_to_05_candidate_count']}",
        f"- need_manual_review_count: {summary['need_manual_review_count']}",
        f"- blocked_count: {summary['blocked_count']}",
        f"- ready_for_stage5p_apply_review: {summary['ready_for_stage5p_apply_review']}",
        f"- recommended_next_stage: {summary['recommended_next_stage']}",
        f"- stage5o_promotion_review_pass: {summary['stage5o_promotion_review_pass']}",
    ]
    OUT_REPORT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"stage5o_candidate_02_xlsx: {OUT_CANDIDATE_02_XLSX}")
    print(f"stage5o_candidate_05_xlsx: {OUT_CANDIDATE_05_XLSX}")
    print(f"stage5o_promotion_review_xlsx: {OUT_REVIEW_XLSX}")
    print(f"stage5o_diff_xlsx: {OUT_DIFF_XLSX}")
    print(f"stage5o_report_md: {OUT_REPORT_MD}")
    print(f"stage5o_summary_json: {OUT_SUMMARY_JSON}")
    print(f"stage5o_promotion_review_pass: {summary['stage5o_promotion_review_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
