import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = r"D:\_datefac\output"
DEFAULT_REPORT_PATH = r"D:\_datefac\output\19_financial_value_validation_report.xlsx"
ASSET_SUFFIX = "_资产包"

CORE_METRICS = [
    "营业收入",
    "归属母公司净利润",
    "毛利率",
    "ROE",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
]

AMOUNT_METRICS = {"营业收入", "归属母公司净利润"}
RATIO_METRICS = {"毛利率", "ROE"}
EPS_METRICS = {"每股收益"}
MULTIPLE_METRICS = {"P/E", "P/B", "EV/EBITDA"}

LABEL_TOKENS = [
    "营业收入",
    "净利润",
    "归母",
    "归属母公司",
    "毛利率",
    "ROE",
    "EPS",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
]

ROW_WRONG_HINT_TOKENS = [
    "资产负债",
    "现金流",
    "现金流量",
    "负债",
    "资产",
]

AMOUNT_FORBID_TOKENS = [
    "营业收入",
    "净利润",
    "税金",
    "资产",
    "负债",
    "现金流",
]

YEAR_RE = re.compile(r"(20\d{2}(?:[AE])?)", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def _normalize_text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _find_asset_packages(output_dir: Path) -> List[Path]:
    if not output_dir.exists():
        return []
    return sorted(
        [p for p in output_dir.iterdir() if p.is_dir() and p.name.endswith(ASSET_SUFFIX)],
        key=lambda x: x.name,
    )


def _find_latest_05(asset_pkg: Path) -> Optional[Path]:
    files = [
        p
        for p in asset_pkg.iterdir()
        if p.is_file() and p.suffix.lower() == ".xlsx" and p.name.startswith("05_")
    ]
    if not files:
        return None
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0]


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _normalize_text(name) or "Sheet")[:31] or "Sheet"
    base = s
    idx = 1
    while s in used:
        suffix = f"_{idx}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used.add(s)
    return s


def _save_excel_robust(sheet_map: Dict[str, pd.DataFrame], report_path: Path) -> str:
    final = report_path
    if report_path.exists():
        try:
            with open(report_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final = report_path.with_name(f"{report_path.stem}_copy_{ts}{report_path.suffix}")

    used = set()
    with pd.ExcelWriter(final, engine="openpyxl") as writer:
        for sheet, df in sheet_map.items():
            safe = _safe_sheet_name(sheet, used)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return str(final)


def _detect_detail_sheet(file_05: Path) -> Tuple[pd.DataFrame, str]:
    xls = pd.ExcelFile(file_05, engine="openpyxl")
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_05, sheet_name=sheet_name, engine="openpyxl")
        cols = [str(c) for c in df.columns]
        if "source_row_label" in cols and ("标准指标" in cols or "指标" in cols):
            metric_col = "标准指标" if "标准指标" in cols else "指标"
            return df, metric_col
    return pd.DataFrame(), "标准指标"


def _year_columns(df: pd.DataFrame) -> List[str]:
    years = []
    for c in df.columns:
        s = _normalize_text(c)
        if YEAR_RE.search(s):
            years.append(str(c))
    return years


def _normalize_year(col_name: str) -> str:
    m = YEAR_RE.search(_normalize_text(col_name))
    return m.group(1).upper() if m else _normalize_text(col_name)


def _contains_chinese(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def _parse_value(raw: str) -> Tuple[Optional[float], str]:
    text = _normalize_text(raw)
    if not text:
        return None, "empty"
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", text.replace(",", "")):
        return float(text.replace(",", "")), "numeric"

    compact = text.replace(",", "").replace(" ", "")
    compact = compact.replace("（", "(").replace("）", ")").replace("％", "%")
    is_percent = compact.endswith("%")
    if is_percent:
        compact = compact[:-1]

    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", compact):
        return float(compact), "percent" if is_percent else "numeric"

    nums = NUM_RE.findall(compact)
    if nums:
        try:
            return float(nums[0]), "mixed_text_numeric"
        except Exception:
            return None, "text"
    return None, "text"


def _issue_join(flags: List[str]) -> str:
    uniq = []
    seen = set()
    for f in flags:
        if not f:
            continue
        if f not in seen:
            uniq.append(f)
            seen.add(f)
    return "|".join(uniq)


def _validate_cell(
    metric: str,
    raw_value: str,
    parsed_value: Optional[float],
    value_type: str,
    source_row_label: str,
) -> Tuple[str, str, str]:
    issues: List[str] = []
    reasons: List[str] = []
    raw = _normalize_text(raw_value)
    raw_upper = raw.upper()
    label_upper = _normalize_text(source_row_label).upper()

    if any(tok.upper() in raw_upper for tok in LABEL_TOKENS):
        issues.append("label_value_glued")
        reasons.append("value contains metric/label token")

    if parsed_value is None:
        issues.append("non_numeric_value")
        reasons.append("value cannot be parsed as numeric")
        return "invalid", _issue_join(issues), "; ".join(reasons)

    if value_type == "mixed_text_numeric":
        issues.append("mixed_text_values")
        reasons.append("numeric extracted from mixed text")

    if metric in AMOUNT_METRICS:
        if "%" in raw or "％" in raw:
            issues.append("percentage_not_allowed_for_amount")
            reasons.append("amount metric should not be percent")
        if any(tok in raw for tok in AMOUNT_FORBID_TOKENS if tok not in metric):
            issues.append("likely_wrong_row")
            reasons.append("contains other financial row labels")
        if abs(parsed_value) > 1e12:
            issues.append("suspicious_amount_extreme")
            reasons.append("extreme amount value")

    if metric in RATIO_METRICS:
        if abs(parsed_value) > 300:
            issues.append("invalid_ratio_too_large")
            reasons.append("ratio absolute value too large")
        if any(tok in label_upper for tok in ROW_WRONG_HINT_TOKENS):
            issues.append("likely_wrong_row")
            reasons.append("ratio from likely non-ratio row")

    if metric in EPS_METRICS:
        if abs(parsed_value) > 100:
            issues.append("invalid_eps_too_large")
            reasons.append("eps absolute value too large")
        if any(tok in label_upper for tok in ROW_WRONG_HINT_TOKENS):
            issues.append("likely_wrong_row")
            reasons.append("eps from likely wrong row")

    if metric in MULTIPLE_METRICS:
        if abs(parsed_value) > 1000:
            issues.append("suspicious_multiple_extreme")
            reasons.append("multiple absolute value too large")
        if metric == "P/B" and abs(parsed_value) > 100:
            issues.append("suspicious_pb_too_large")
            reasons.append("pb absolute value unusually large")

    invalid_flags = {
        "non_numeric_value",
        "invalid_ratio_too_large",
        "invalid_eps_too_large",
        "percentage_not_allowed_for_amount",
    }
    suspicious_flags = {
        "label_value_glued",
        "mixed_text_values",
        "likely_wrong_row",
        "suspicious_multiple_extreme",
        "suspicious_pb_too_large",
        "suspicious_amount_extreme",
    }

    issue_set = set(issues)
    if issue_set & invalid_flags:
        status = "invalid"
    elif issue_set & suspicious_flags:
        status = "suspicious"
    else:
        status = "valid"
    return status, _issue_join(issues), "; ".join(reasons)


def _candidate_status_from_years(year_rows: List[Dict[str, object]]) -> Tuple[str, int, int, int, str]:
    if not year_rows:
        return "invalid", 0, 0, 0, "no_year_values"
    v = sum(1 for r in year_rows if r.get("validation_status") == "valid")
    s = sum(1 for r in year_rows if r.get("validation_status") == "suspicious")
    i = sum(1 for r in year_rows if r.get("validation_status") == "invalid")
    all_flags: List[str] = []
    for r in year_rows:
        all_flags.extend(_normalize_text(r.get("issue_flags")).split("|"))
    merged = _issue_join(all_flags)
    if i == 0 and s == 0 and v > 0:
        return "valid", v, s, i, merged
    if i == 0 and (s > 0 or v > 0):
        return "suspicious", v, s, i, merged
    if i > 0 and v > 0:
        return "suspicious", v, s, i, merged
    return "invalid", v, s, i, merged


def _metric_recommendation(metric_status: str) -> str:
    if metric_status == "valid":
        return "保留当前最佳候选"
    if metric_status == "suspicious":
        return "建议人工复核并优先保留有效年份更多的候选"
    if metric_status == "invalid":
        return "建议回查 02 行标签和值列，避免标签值粘连"
    return "缺少可用候选，建议回查上游抽取与后处理"


def _asset_recommendation(valid_ratio: float, primary_issue: str) -> str:
    if valid_ratio >= 0.75:
        return "值层质量可接受，优先扩样本验证"
    if primary_issue == "label_value_glued":
        return "优先修值列清洗与标签-值分离"
    if primary_issue in {"invalid_ratio_too_large", "invalid_eps_too_large"}:
        return "优先修行标签定位与候选筛选"
    if primary_issue == "non_numeric_value":
        return "优先修年份列和值列定位"
    if primary_issue == "missing_metrics":
        return "优先回查抽取覆盖和02结构化质量"
    return "建议定向审计低命中样本并补充约束规则"


def build_validation_report(output_dir: Path) -> Tuple[str, pd.DataFrame]:
    asset_dirs = _find_asset_packages(output_dir)
    detail_rows: List[Dict[str, object]] = []
    candidate_summary_rows: List[Dict[str, object]] = []
    asset_summary_rows: List[Dict[str, object]] = []

    for asset_dir in asset_dirs:
        asset_name = asset_dir.name
        file_05 = _find_latest_05(asset_dir)

        metric_to_candidates: Dict[str, List[Dict[str, object]]] = {m: [] for m in CORE_METRICS}

        if file_05 and file_05.exists():
            detail_df, metric_col = _detect_detail_sheet(file_05)
            if not detail_df.empty:
                detail_df = detail_df.fillna("")
                year_cols = _year_columns(detail_df)
                for ridx, row in detail_df.iterrows():
                    metric = _normalize_text(row.get(metric_col, ""))
                    if metric not in CORE_METRICS:
                        continue
                    source_row_label = _normalize_text(row.get("source_row_label", ""))
                    source_table_index = row.get("source_table_index", "")
                    source_row_index = row.get("source_row_index", "")
                    source_label_column = _normalize_text(row.get("source_label_column", ""))
                    source_column = _normalize_text(row.get("source_column", ""))
                    matched_alias = _normalize_text(row.get("matched_alias", ""))
                    match_method = _normalize_text(row.get("match_method", ""))
                    confidence = row.get("confidence", "")
                    header_repaired = row.get("header_repaired", "")

                    candidate_year_rows: List[Dict[str, object]] = []
                    for ycol in year_cols:
                        raw = _normalize_text(row.get(ycol, ""))
                        if not raw:
                            continue
                        parsed, value_type = _parse_value(raw)
                        v_status, issue_flags, reason = _validate_cell(
                            metric=metric,
                            raw_value=raw,
                            parsed_value=parsed,
                            value_type=value_type,
                            source_row_label=source_row_label,
                        )
                        row_item = {
                            "asset_package": asset_name,
                            "standard_metric": metric,
                            "source_row_label": source_row_label,
                            "source_table_index": source_table_index,
                            "source_row_index": source_row_index,
                            "source_label_column": source_label_column,
                            "source_column": source_column,
                            "matched_alias": matched_alias,
                            "match_method": match_method,
                            "confidence": confidence,
                            "header_repaired": header_repaired,
                            "year": _normalize_year(ycol),
                            "raw_value": raw,
                            "parsed_value": parsed,
                            "value_type": value_type,
                            "validation_status": v_status,
                            "issue_flags": issue_flags,
                            "reason": reason,
                            "_candidate_id": int(ridx),
                        }
                        detail_rows.append(row_item)
                        candidate_year_rows.append(row_item)

                    candidate_status, v_cnt, s_cnt, i_cnt, merged_flags = _candidate_status_from_years(candidate_year_rows)
                    metric_to_candidates[metric].append(
                        {
                            "candidate_id": int(ridx),
                            "source_row_label": source_row_label,
                            "source_table_index": source_table_index,
                            "source_row_index": source_row_index,
                            "source_label_column": source_label_column,
                            "source_column": source_column,
                            "matched_alias": matched_alias,
                            "match_method": match_method,
                            "confidence": float(confidence) if str(confidence).strip() not in {"", "nan"} else 0.0,
                            "year_rows": candidate_year_rows,
                            "status": candidate_status,
                            "valid_year_count": v_cnt,
                            "suspicious_year_count": s_cnt,
                            "invalid_year_count": i_cnt,
                            "issue_flags": merged_flags,
                        }
                    )

        metric_status_map: Dict[str, str] = {}
        metric_issue_for_asset: List[str] = []
        for metric in CORE_METRICS:
            cands = metric_to_candidates.get(metric, [])
            if not cands:
                metric_status = "missing"
                candidate_summary_rows.append(
                    {
                        "asset_package": asset_name,
                        "standard_metric": metric,
                        "candidate_count": 0,
                        "valid_candidate_count": 0,
                        "invalid_candidate_count": 0,
                        "best_candidate_source_row_label": "",
                        "best_candidate_year_count": 0,
                        "best_candidate_valid_year_count": 0,
                        "best_candidate_issue_flags": "",
                        "metric_value_status": metric_status,
                        "recommendation": _metric_recommendation(metric_status),
                    }
                )
                metric_status_map[metric] = metric_status
                metric_issue_for_asset.append("missing_metrics")
                continue

            for cand in cands:
                cand["issue_count"] = len([x for x in _normalize_text(cand.get("issue_flags")).split("|") if x])
            cands_sorted = sorted(
                cands,
                key=lambda x: (
                    -int(x.get("valid_year_count", 0)),
                    int(x.get("issue_count", 0)),
                    -float(x.get("confidence", 0.0)),
                ),
            )
            best = cands_sorted[0]
            valid_candidate_count = sum(1 for c in cands if c.get("status") == "valid")
            invalid_candidate_count = sum(1 for c in cands if c.get("status") == "invalid")
            suspicious_candidate_count = sum(1 for c in cands if c.get("status") == "suspicious")

            if valid_candidate_count > 0:
                metric_status = "valid"
            elif suspicious_candidate_count > 0:
                metric_status = "suspicious"
            else:
                metric_status = "invalid"
            metric_status_map[metric] = metric_status

            if best.get("issue_flags"):
                metric_issue_for_asset.extend([x for x in str(best["issue_flags"]).split("|") if x])

            candidate_summary_rows.append(
                {
                    "asset_package": asset_name,
                    "standard_metric": metric,
                    "candidate_count": len(cands),
                    "valid_candidate_count": valid_candidate_count,
                    "invalid_candidate_count": invalid_candidate_count,
                    "best_candidate_source_row_label": best.get("source_row_label", ""),
                    "best_candidate_year_count": len(best.get("year_rows", [])),
                    "best_candidate_valid_year_count": int(best.get("valid_year_count", 0)),
                    "best_candidate_issue_flags": best.get("issue_flags", ""),
                    "metric_value_status": metric_status,
                    "recommendation": _metric_recommendation(metric_status),
                }
            )

        total_metrics = len(CORE_METRICS)
        label_hit_metric_count = sum(
            1 for m in CORE_METRICS if len(metric_to_candidates.get(m, [])) > 0
        )
        value_valid_metric_count = sum(1 for m in CORE_METRICS if metric_status_map.get(m) == "valid")
        value_suspicious_metric_count = sum(1 for m in CORE_METRICS if metric_status_map.get(m) == "suspicious")
        value_invalid_metric_count = sum(1 for m in CORE_METRICS if metric_status_map.get(m) == "invalid")
        missing_metric_count = sum(1 for m in CORE_METRICS if metric_status_map.get(m) == "missing")
        value_valid_ratio = round(value_valid_metric_count / total_metrics, 4) if total_metrics else 0.0

        primary_value_issue = ""
        if metric_issue_for_asset:
            vc = pd.Series(metric_issue_for_asset).value_counts()
            primary_value_issue = str(vc.index[0])
        elif missing_metric_count > 0:
            primary_value_issue = "missing_metrics"
        else:
            primary_value_issue = "none_or_minor"

        asset_summary_rows.append(
            {
                "asset_package": asset_name,
                "total_metrics": total_metrics,
                "label_hit_metric_count": label_hit_metric_count,
                "value_valid_metric_count": value_valid_metric_count,
                "value_suspicious_metric_count": value_suspicious_metric_count,
                "value_invalid_metric_count": value_invalid_metric_count,
                "missing_metric_count": missing_metric_count,
                "value_valid_ratio": value_valid_ratio,
                "primary_value_issue": primary_value_issue,
                "recommendation": _asset_recommendation(value_valid_ratio, primary_value_issue),
            }
        )

    detail_df = pd.DataFrame(detail_rows)
    if not detail_df.empty and "_candidate_id" in detail_df.columns:
        detail_df = detail_df.drop(columns=["_candidate_id"])
    candidate_df = pd.DataFrame(candidate_summary_rows)
    asset_df = pd.DataFrame(asset_summary_rows)

    report_path = Path(DEFAULT_REPORT_PATH)
    final_path = _save_excel_robust(
        {
            "metric_value_details": detail_df,
            "metric_candidate_summary": candidate_df,
            "asset_value_summary": asset_df,
        },
        report_path,
    )
    return final_path, asset_df


def main():
    parser = argparse.ArgumentParser(description="Validate 05 financial metric values and output value-confidence report.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory containing asset packages")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    final_path, asset_df = build_validation_report(out_dir)
    print(f"report_path={final_path}")

    if asset_df.empty:
        print("asset_summary: empty")
        return

    cols = [
        "asset_package",
        "label_hit_metric_count",
        "value_valid_metric_count",
        "value_invalid_metric_count",
        "value_valid_ratio",
        "primary_value_issue",
        "recommendation",
    ]
    for _, row in asset_df.sort_values("asset_package").iterrows():
        parts = [f"{c}={_normalize_text(row.get(c, ''))}" for c in cols]
        print(" | ".join(parts))


if __name__ == "__main__":
    main()

