import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_VALIDATION_REPORT = r"D:\_datefac\output\19_financial_value_validation_report.xlsx"
DEFAULT_REGRESSION_REPORT = r"D:\_datefac\output\08_批量回归报告.xlsx"
DEFAULT_OUTPUT_REPORT = r"D:\_datefac\output\20_financial_value_repair_probe.xlsx"

TARGET_ISSUES = {"label_value_glued", "mixed_text_values", "non_numeric_value"}
SKIP_HARD_ISSUES = {"invalid_ratio_too_large", "invalid_eps_too_large"}

AMOUNT_METRICS = {"营业收入", "归属母公司净利润"}
RATIO_METRICS = {"毛利率", "ROE"}
EPS_METRICS = {"每股收益"}

FORBID_ROW_TOKENS = ["税金", "营业成本", "资产", "负债", "现金流", "少数股东", "扣非"]
FORBID_RAW_TOKENS = ["税金及附加", "资产总计", "负债合计", "现金流", "营业成本"]

NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
ASSET_RE = re.compile(r"^H3_AP\d+_\d+_资产包$")

METRIC_ALIASES: Dict[str, List[str]] = {
    "营业收入": ["营业收入", "收入"],
    "归属母公司净利润": [
        "归属母公司净利润",
        "归属于母公司股东的净利润",
        "归母净利润",
        "归母净利",
        "母公司股东净利润",
    ],
    "毛利率": ["毛利率", "毛利"],
    "ROE": ["ROE", "净资产收益率"],
    "每股收益": ["每股收益", "EPS", "基本每股收益", "稀释每股收益", "摊薄EPS", "EPS(元)", "EPS（元）"],
    "P/E": ["P/E", "PE", "市盈率"],
    "P/B": ["P/B", "PB", "市净率"],
    "EV/EBITDA": ["EV/EBITDA", "EV EBITDA", "EVEBITDA"],
}


def _norm_text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _norm_compact(s: str) -> str:
    s = _norm_text(s).upper()
    s = s.replace("（", "(").replace("）", ")").replace("／", "/").replace("，", ",")
    s = re.sub(r"\s+", "", s)
    return s


def _split_flags(v) -> List[str]:
    text = _norm_text(v)
    if not text:
        return []
    out = []
    for f in re.split(r"[|;,]+", text):
        f = f.strip()
        if f:
            out.append(f)
    return out


def _join_flags(flags: List[str]) -> str:
    seen = set()
    out = []
    for f in flags:
        if f and f not in seen:
            seen.add(f)
            out.append(f)
    return "|".join(out)


def _to_float(v) -> Optional[float]:
    s = _norm_text(v).replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _metric_aliases(metric: str) -> List[str]:
    aliases = METRIC_ALIASES.get(metric, [metric])
    uniq = []
    seen = set()
    for a in aliases + [metric]:
        a = _norm_text(a)
        if a and a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


def _label_matches_metric(label: str, metric: str) -> bool:
    compact = _norm_compact(label)
    if not compact:
        return False
    for alias in _metric_aliases(metric):
        a = _norm_compact(alias)
        if not a:
            continue
        if compact == a or a in compact or compact in a:
            return True
    return False


def _raw_starts_with_metric_alias(raw_value: str, metric: str) -> bool:
    raw = _norm_compact(raw_value)
    if not raw:
        return False
    for alias in _metric_aliases(metric):
        a = _norm_compact(alias)
        if not a:
            continue
        if raw.startswith(a):
            return True
    return False


def _has_forbid_context_for_amount(metric: str, source_row_label: str, raw_value: str) -> bool:
    if metric not in AMOUNT_METRICS:
        return False
    label = _norm_text(source_row_label)
    raw = _norm_text(raw_value)
    for tok in FORBID_ROW_TOKENS:
        if tok in label or tok in raw:
            return True
    return False


def _contains_any_token(text: str, tokens: List[str]) -> bool:
    t = _norm_text(text)
    return any(tok in t for tok in tokens)


def _extract_last_numeric(raw_value: str) -> Optional[float]:
    nums = NUM_RE.findall(_norm_text(raw_value))
    if not nums:
        return None
    try:
        return float(nums[-1])
    except Exception:
        return None


def _extract_single_numeric(raw_value: str) -> Optional[float]:
    nums = NUM_RE.findall(_norm_text(raw_value))
    if len(nums) != 1:
        return None
    try:
        return float(nums[0])
    except Exception:
        return None


def _repair_strategy_1(metric: str, source_row_label: str, raw_value: str) -> Tuple[bool, Optional[float], str]:
    if not _label_matches_metric(source_row_label, metric):
        return False, None, "source_row_label_not_matching_metric"
    if not _raw_starts_with_metric_alias(raw_value, metric):
        return False, None, "raw_value_not_starting_with_metric_alias"
    if _contains_any_token(raw_value, FORBID_RAW_TOKENS):
        return False, None, "raw_value_contains_other_financial_row_label"
    val = _extract_last_numeric(raw_value)
    if val is None:
        return False, None, "no_numeric_tail_found"
    return True, val, "trailing_number_from_matching_label"


def _repair_strategy_2(metric: str, source_row_label: str, raw_value: str) -> Tuple[bool, Optional[float], str]:
    if not _label_matches_metric(source_row_label, metric):
        return False, None, "source_row_label_not_exact_or_synonym"
    if not _raw_starts_with_metric_alias(raw_value, metric):
        return False, None, "raw_value_not_starting_with_metric_alias"
    nums = NUM_RE.findall(_norm_text(raw_value))
    if len(nums) != 1:
        return False, None, "raw_value_has_multiple_or_zero_numbers"
    val = _extract_single_numeric(raw_value)
    if val is None:
        return False, None, "single_numeric_parse_failed"
    return True, val, "numeric_tail_if_source_label_exact"


def _reject_wrong_row_context(
    metric: str,
    source_row_label: str,
    raw_value: str,
    repaired_value: Optional[float],
) -> Tuple[bool, str, List[str]]:
    flags: List[str] = []
    if repaired_value is None:
        flags.append("repair_value_empty")
        return True, "repaired_value_empty", flags

    if metric in RATIO_METRICS and abs(repaired_value) > 300:
        flags.append("invalid_ratio_too_large")
        return True, "ratio_value_too_large", flags
    if metric in EPS_METRICS and abs(repaired_value) > 100:
        flags.append("invalid_eps_too_large")
        return True, "eps_value_too_large", flags
    if metric in AMOUNT_METRICS and "%" in _norm_text(raw_value):
        flags.append("amount_has_percent")
        return True, "amount_contains_percent", flags
    if _has_forbid_context_for_amount(metric, source_row_label, raw_value):
        flags.append("likely_wrong_row")
        return True, "forbidden_row_context_for_amount", flags
    return False, "ok", flags


def _candidate_key(row: pd.Series) -> Tuple[str, str, str, str, str, str]:
    return (
        _norm_text(row.get("asset_package")),
        _norm_text(row.get("standard_metric")),
        _norm_text(row.get("source_table_index")),
        _norm_text(row.get("source_row_index")),
        _norm_text(row.get("source_label_column")),
        _norm_text(row.get("source_row_label")),
    )


def _status_rank(status: str) -> int:
    mapping = {"valid": 0, "suspicious": 1, "invalid": 2, "missing": 3, "empty": 4}
    return mapping.get(_norm_text(status), 9)


def _candidate_status_from_rows(rows: pd.DataFrame, status_col: str) -> Tuple[str, int, int, int]:
    valid = int((rows[status_col] == "valid").sum())
    suspicious = int((rows[status_col] == "suspicious").sum())
    invalid = int((rows[status_col] == "invalid").sum())
    if valid > 0 and suspicious == 0 and invalid == 0:
        return "valid", valid, suspicious, invalid
    if valid > 0 and invalid == 0:
        return "suspicious", valid, suspicious, invalid
    if valid == 0 and suspicious > 0 and invalid == 0:
        return "suspicious", valid, suspicious, invalid
    if valid > 0 and invalid > 0:
        return "suspicious", valid, suspicious, invalid
    if invalid > 0:
        return "invalid", valid, suspicious, invalid
    return "missing", valid, suspicious, invalid


def _recommend_metric(original_status: str, repaired_status: str, repairable_year_count: int) -> str:
    if repaired_status == "valid" and original_status != "valid":
        return "可低风险引入值修复策略"
    if repairable_year_count == 0:
        return "当前策略难以安全修复，优先检查表结构与列对齐"
    if repaired_status == "suspicious":
        return "可做保守修复并保留人工复核"
    if repaired_status == "invalid":
        return "不要自动修复，优先回查错列问题"
    return "保持现状，继续扩样本观察"


def _save_excel_robust(sheet_map: Dict[str, pd.DataFrame], out_path: Path) -> str:
    final_path = out_path
    if out_path.exists():
        try:
            with open(out_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = out_path.with_name(f"{out_path.stem}_copy_{ts}{out_path.suffix}")

    used = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for name, df in sheet_map.items():
            safe = re.sub(r"[\\/*?:\[\]]", "_", name)[:31] or "Sheet1"
            base = safe
            i = 1
            while safe in used:
                suffix = f"_{i}"
                safe = f"{base[:31-len(suffix)]}{suffix}"
                i += 1
            used.add(safe)
            (df if isinstance(df, pd.DataFrame) else pd.DataFrame()).to_excel(writer, sheet_name=safe, index=False)
    return str(final_path)


def build_repair_probe_report(
    validation_report_path: Path,
    regression_report_path: Optional[Path],
    output_report_path: Path,
) -> Tuple[str, pd.DataFrame]:
    details = pd.read_excel(validation_report_path, sheet_name="metric_value_details", engine="openpyxl")
    metric_summary = pd.read_excel(validation_report_path, sheet_name="metric_candidate_summary", engine="openpyxl")
    asset_summary = pd.read_excel(validation_report_path, sheet_name="asset_value_summary", engine="openpyxl")

    details["asset_package"] = details["asset_package"].astype(str)
    metric_summary["asset_package"] = metric_summary["asset_package"].astype(str)
    asset_summary["asset_package"] = asset_summary["asset_package"].astype(str)

    assets = sorted(
        [a for a in asset_summary["asset_package"].unique().tolist() if ASSET_RE.match(str(a))]
    )

    if regression_report_path and regression_report_path.exists():
        try:
            reg = pd.read_excel(regression_report_path, sheet_name="summary", engine="openpyxl")
            if "asset_package" in reg.columns:
                reg_assets = [
                    str(a)
                    for a in reg["asset_package"].astype(str).tolist()
                    if ASSET_RE.match(str(a))
                ]
                if reg_assets:
                    assets = sorted(set(reg_assets))
        except Exception:
            pass

    details = details[details["asset_package"].isin(assets)].copy()
    metric_summary = metric_summary[metric_summary["asset_package"].isin(assets)].copy()
    asset_summary = asset_summary[asset_summary["asset_package"].isin(assets)].copy()

    repair_rows: List[Dict[str, object]] = []
    for _, row in details.iterrows():
        standard_metric = _norm_text(row.get("standard_metric"))
        source_row_label = _norm_text(row.get("source_row_label"))
        raw_value = _norm_text(row.get("raw_value"))
        year = _norm_text(row.get("year"))
        original_status = _norm_text(row.get("validation_status"))
        original_flags_list = _split_flags(row.get("issue_flags"))
        original_flags = _join_flags(original_flags_list)

        should_consider = bool(set(original_flags_list) & TARGET_ISSUES)
        hard_skip = bool(set(original_flags_list) & SKIP_HARD_ISSUES)

        repair_applied = False
        repair_strategy = ""
        repaired_value: Optional[float] = _to_float(row.get("parsed_value"))
        repair_status = original_status or "missing"
        repair_issue_flags = list(original_flags_list)
        repair_reason = "no_repair_needed"

        if should_consider and not hard_skip:
            ok1, v1, r1 = _repair_strategy_1(standard_metric, source_row_label, raw_value)
            ok2, v2, r2 = _repair_strategy_2(standard_metric, source_row_label, raw_value)

            chosen_val: Optional[float] = None
            chosen_strategy = ""
            strategy_reason = ""
            if ok1:
                chosen_val = v1
                chosen_strategy = "trailing_number_from_matching_label"
                strategy_reason = r1
            elif ok2:
                chosen_val = v2
                chosen_strategy = "numeric_tail_if_source_label_exact"
                strategy_reason = r2
            else:
                repair_reason = f"not_repairable:{r1};{r2}"

            if chosen_strategy:
                reject, reject_reason, reject_flags = _reject_wrong_row_context(
                    standard_metric, source_row_label, raw_value, chosen_val
                )
                if reject:
                    repair_applied = False
                    repair_strategy = "reject_wrong_row_context"
                    repair_status = original_status or "invalid"
                    repair_issue_flags = _split_flags(original_flags)
                    repair_issue_flags.extend(reject_flags)
                    repair_reason = f"rejected:{reject_reason}"
                else:
                    repair_applied = True
                    repair_strategy = chosen_strategy
                    repaired_value = chosen_val
                    repair_status = "valid"
                    repair_issue_flags = []
                    repair_reason = f"repaired:{strategy_reason}"
        elif hard_skip:
            repair_reason = "skip_hard_issue_flag"

        repair_rows.append(
            {
                "asset_package": _norm_text(row.get("asset_package")),
                "standard_metric": standard_metric,
                "year": year,
                "source_row_label": source_row_label,
                "raw_value": raw_value,
                "original_validation_status": original_status,
                "original_issue_flags": original_flags,
                "repair_applied": repair_applied,
                "repair_strategy": repair_strategy,
                "repaired_value": repaired_value,
                "repair_validation_status": repair_status,
                "repair_issue_flags": _join_flags(repair_issue_flags),
                "repair_reason": repair_reason,
                "source_table_index": row.get("source_table_index"),
                "source_row_index": row.get("source_row_index"),
                "confidence": row.get("confidence"),
                "candidate_key": "||".join(_candidate_key(row)),
            }
        )

    repair_details = pd.DataFrame(repair_rows)

    candidate_rows = []
    if not repair_details.empty:
        group_cols = ["asset_package", "standard_metric", "candidate_key"]
        for (asset_pkg, metric, ckey), g in repair_details.groupby(group_cols, dropna=False):
            original_status, original_valid, _, _ = _candidate_status_from_rows(g, "original_validation_status")
            repaired_status, repaired_valid, _, _ = _candidate_status_from_rows(g, "repair_validation_status")
            candidate_rows.append(
                {
                    "asset_package": asset_pkg,
                    "standard_metric": metric,
                    "candidate_key": ckey,
                    "candidate_source_row_label": _norm_text(g["source_row_label"].iloc[0]),
                    "original_candidate_status": original_status,
                    "original_valid_year_count": original_valid,
                    "repairable_year_count": int(g["repair_applied"].sum()),
                    "repaired_valid_year_count": repaired_valid,
                    "repaired_candidate_status": repaired_status,
                    "repair_issue_flags": _join_flags(
                        [f for v in g["repair_issue_flags"].tolist() for f in _split_flags(v)]
                    ),
                    "confidence": pd.to_numeric(g["confidence"], errors="coerce").fillna(0).max(),
                }
            )
    candidate_df = pd.DataFrame(candidate_rows)

    metric_rows = []
    for _, ms in metric_summary.iterrows():
        asset_pkg = _norm_text(ms.get("asset_package"))
        metric = _norm_text(ms.get("standard_metric"))
        original_metric_status = _norm_text(ms.get("metric_value_status")) or "missing"
        original_valid_year_count = int(ms.get("best_candidate_valid_year_count") or 0)
        sub = candidate_df[
            (candidate_df["asset_package"] == asset_pkg) & (candidate_df["standard_metric"] == metric)
        ].copy()

        repairable_year_count = int(sub["repairable_year_count"].sum()) if not sub.empty else 0

        if sub.empty:
            repaired_best_status = original_metric_status
            repaired_valid_year_count = original_valid_year_count
        else:
            sub["status_rank"] = sub["repaired_candidate_status"].apply(_status_rank)
            sub["issue_cnt"] = sub["repair_issue_flags"].apply(lambda x: 0 if not _norm_text(x) else len(_split_flags(x)))
            sub = sub.sort_values(
                ["status_rank", "repaired_valid_year_count", "issue_cnt", "confidence"],
                ascending=[True, False, True, False],
            )
            best = sub.iloc[0]
            repaired_best_status = _norm_text(best.get("repaired_candidate_status")) or original_metric_status
            repaired_valid_year_count = int(best.get("repaired_valid_year_count") or 0)

        metric_rows.append(
            {
                "asset_package": asset_pkg,
                "standard_metric": metric,
                "original_metric_value_status": original_metric_status,
                "original_valid_year_count": original_valid_year_count,
                "repairable_year_count": repairable_year_count,
                "repaired_valid_year_count": repaired_valid_year_count,
                "repaired_best_candidate_status": repaired_best_status,
                "recommendation": _recommend_metric(
                    original_metric_status, repaired_best_status, repairable_year_count
                ),
            }
        )

    candidate_repair_summary = pd.DataFrame(metric_rows)

    asset_rows = []
    for _, ar in asset_summary.iterrows():
        asset_pkg = _norm_text(ar.get("asset_package"))
        original_valid_metric_count = int(ar.get("value_valid_metric_count") or 0)
        sub = candidate_repair_summary[candidate_repair_summary["asset_package"] == asset_pkg]
        repaired_valid_metric_count = int((sub["repaired_best_candidate_status"] == "valid").sum())
        potential_gain = repaired_valid_metric_count - original_valid_metric_count
        repairable_metrics = "|".join(
            sorted(
                sub.loc[sub["repairable_year_count"] > 0, "standard_metric"].astype(str).unique().tolist()
            )
        )
        risky_metrics = "|".join(
            sorted(
                sub.loc[sub["repaired_best_candidate_status"] == "invalid", "standard_metric"]
                .astype(str)
                .unique()
                .tolist()
            )
        )

        if potential_gain > 0:
            rec = "值修复策略有增益，可优先做低风险落地"
        elif repairable_metrics:
            rec = "可修复空间有限，建议结合表结构对齐优化"
        else:
            rec = "当前样本修复收益低，优先回查抽取与后处理"

        asset_rows.append(
            {
                "asset_package": asset_pkg,
                "original_value_valid_metric_count": original_valid_metric_count,
                "repaired_value_valid_metric_count": repaired_valid_metric_count,
                "potential_gain": potential_gain,
                "repairable_metrics": repairable_metrics,
                "risky_metrics": risky_metrics,
                "recommendation": rec,
            }
        )

    asset_repair_summary = pd.DataFrame(asset_rows).sort_values("asset_package")

    issue_rows = []
    all_flags = set()
    for v in repair_details["original_issue_flags"].tolist():
        all_flags.update(_split_flags(v))
    all_flags = sorted(all_flags)

    for flag in all_flags:
        sf = repair_details[repair_details["original_issue_flags"].fillna("").str.contains(flag, regex=False)]
        if sf.empty:
            continue
        repairable = sf[sf["repair_applied"] == True]
        repaired_valid = sf[sf["repair_validation_status"] == "valid"]
        unsafe = sf[sf["repair_applied"] == False]
        examples = " | ".join(sf["raw_value"].dropna().astype(str).head(3).tolist())
        issue_rows.append(
            {
                "issue_flag": flag,
                "original_occurrence_count": int(len(sf)),
                "repairable_count": int(len(repairable)),
                "repaired_valid_count": int(len(repaired_valid)),
                "unsafe_count": int(len(unsafe)),
                "examples": examples,
            }
        )

    issue_repair_summary = pd.DataFrame(issue_rows).sort_values(
        ["original_occurrence_count", "repairable_count"], ascending=[False, False]
    )

    report_path = _save_excel_robust(
        {
            "repair_details": repair_details[
                [
                    "asset_package",
                    "standard_metric",
                    "year",
                    "source_row_label",
                    "raw_value",
                    "original_validation_status",
                    "original_issue_flags",
                    "repair_applied",
                    "repair_strategy",
                    "repaired_value",
                    "repair_validation_status",
                    "repair_issue_flags",
                    "repair_reason",
                ]
            ],
            "candidate_repair_summary": candidate_repair_summary,
            "asset_repair_summary": asset_repair_summary,
            "issue_repair_summary": issue_repair_summary,
        },
        output_report_path,
    )
    return report_path, asset_repair_summary


def main():
    parser = argparse.ArgumentParser(description="Probe financial metric value repair strategies.")
    parser.add_argument("--validation-report", default=DEFAULT_VALIDATION_REPORT, help="Path to 19 report.")
    parser.add_argument("--regression-report", default=DEFAULT_REGRESSION_REPORT, help="Path to 08 report.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_REPORT, help="Output report path.")
    args = parser.parse_args()

    validation_report = Path(args.validation_report)
    regression_report = Path(args.regression_report)
    output_report = Path(args.output)

    if not validation_report.exists():
        raise FileNotFoundError(f"Validation report not found: {validation_report}")

    report_path, asset_summary = build_repair_probe_report(
        validation_report,
        regression_report if regression_report.exists() else None,
        output_report,
    )

    print(f"report_path={report_path}")
    if not asset_summary.empty:
        cols = [
            "asset_package",
            "original_value_valid_metric_count",
            "repaired_value_valid_metric_count",
            "potential_gain",
            "repairable_metrics",
            "risky_metrics",
        ]
        print(asset_summary[cols].to_string(index=False))


if __name__ == "__main__":
    main()
