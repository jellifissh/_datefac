import argparse
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
DEFAULT_REPORT_08 = Path(r"D:\_datefac\output\08_批量回归报告.xlsx")
DEFAULT_REPORT_19 = Path(r"D:\_datefac\output\19_financial_value_validation_report.xlsx")
DEFAULT_OUTPUT_22 = Path(r"D:\_datefac\output\22_manual_review_queue.xlsx")

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

KEY_INVALID_FLAGS = {
    "invalid_ratio_too_large",
    "invalid_eps_too_large",
    "label_value_glued",
    "non_numeric_value",
    "mixed_text_values",
    "likely_wrong_row",
}


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_int(v, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _split_flags(s: str) -> List[str]:
    text = _norm(s)
    if not text:
        return []
    out = []
    for part in re.split(r"[|;,]", text):
        part = part.strip()
        if part:
            out.append(part)
    return out


def _join_flags(flags: List[str]) -> str:
    seen = set()
    out = []
    for f in flags:
        if f and f not in seen:
            seen.add(f)
            out.append(f)
    return "|".join(out)


def _safe_sheet_name(name: str, used: set) -> str:
    clean = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = clean
    i = 1
    while clean in used:
        suffix = f"_{i}"
        clean = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(clean)
    return clean


def _save_excel_robust(sheet_map: Dict[str, pd.DataFrame], output_path: Path) -> str:
    final_path = output_path
    if output_path.exists():
        try:
            with open(output_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = output_path.with_name(f"{output_path.stem}_copy_{ts}{output_path.suffix}")

    used = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for sheet, df in sheet_map.items():
            safe = _safe_sheet_name(sheet, used)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return str(final_path)


def _find_report_by_prefix(root: Path, prefix: str) -> Optional[Path]:
    cands = [p for p in root.glob(f"{prefix}_*.xlsx") if p.is_file()]
    if not cands:
        return None
    return sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True)[0]


def _load_report_08(path_08: Optional[Path], root: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    p = path_08 if path_08 and path_08.exists() else _find_report_by_prefix(root, "08")
    if not p or not p.exists():
        return pd.DataFrame(), pd.DataFrame()
    try:
        summary = pd.read_excel(p, sheet_name="summary", engine="openpyxl")
    except Exception:
        summary = pd.DataFrame()
    try:
        fm = pd.read_excel(p, sheet_name="financial_metrics", engine="openpyxl")
    except Exception:
        fm = pd.DataFrame()
    return summary.fillna(""), fm.fillna("")


def _load_report_19(path_19: Optional[Path], root: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    p = path_19 if path_19 and path_19.exists() else _find_report_by_prefix(root, "19")
    if not p or not p.exists():
        return pd.DataFrame(), pd.DataFrame()
    try:
        cand = pd.read_excel(p, sheet_name="metric_candidate_summary", engine="openpyxl")
    except Exception:
        cand = pd.DataFrame()
    try:
        det = pd.read_excel(p, sheet_name="metric_value_details", engine="openpyxl")
    except Exception:
        det = pd.DataFrame()
    return cand.fillna(""), det.fillna("")


def _tier_priority(tier: str, label_hit: int, value_valid: int) -> Tuple[str, str]:
    t = _norm(tier)
    if t == "E_hard_sample" or (label_hit >= 6 and value_valid == 0):
        return "P0", "高命中但值全失效或 hard sample"
    if t == "B_partial_review" or (3 <= value_valid <= 5):
        return "P1", "部分可用，需人工补齐/剔除可疑值"
    if t == "D_insufficient" or label_hit < 3:
        return "P2", "覆盖不足，先检查抽取与结构化"
    if t == "A_usable":
        return "P3", "总体可用，仅抽检"
    return "P2", "默认中优先级复核"


def _tier_action(tier: str) -> str:
    mapping = {
        "A_usable": "可进入下游分析，保留来源追溯并抽查",
        "B_partial_review": "人工复核缺失/可疑指标值",
        "C_label_only_untrusted": "标签命中但值不可信，优先查列绑定",
        "D_insufficient": "检查02A/02覆盖，必要时回查抽取层",
        "E_hard_sample": "标记hard sample，考虑新后端或人工录入",
    }
    return mapping.get(_norm(tier), "人工复核指标值")


def _load_best_probe_21(asset_dir: Path) -> Tuple[bool, int]:
    cands = [p for p in asset_dir.glob("21_*.xlsx") if p.is_file()]
    if not cands:
        return False, -1
    p = sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    try:
        df = pd.read_excel(p, sheet_name="group_summary", engine="openpyxl")
        if "value_valid_metric_count" not in df.columns or df.empty:
            return True, -1
        best = _to_int(pd.to_numeric(df["value_valid_metric_count"], errors="coerce").fillna(0).max(), -1)
        return True, best
    except Exception:
        return True, -1


def _get_asset_dir(root: Path, asset_package: str) -> Optional[Path]:
    p = root / asset_package
    return p if p.exists() and p.is_dir() else None


def _load_02_sheet_map(asset_dir: Path) -> Dict[int, Tuple[str, pd.DataFrame]]:
    out: Dict[int, Tuple[str, pd.DataFrame]] = {}
    try:
        files = [
            p
            for p in asset_dir.iterdir()
            if p.is_file() and p.suffix.lower() == ".xlsx" and p.name.startswith("02_") and not p.name.startswith("02A_")
        ]
        if not files:
            return out
        file_02 = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        xls = pd.ExcelFile(file_02, engine="openpyxl")
        data_sheets = [
            s
            for s in xls.sheet_names
            if not (s.startswith("00_") and ("目录" in s or "index" in s.lower()))
        ]
        for i, s in enumerate(data_sheets, start=1):
            try:
                out[i] = (s, pd.read_excel(file_02, sheet_name=s, engine="openpyxl").fillna(""))
            except Exception:
                out[i] = (s, pd.DataFrame())
    except Exception:
        return {}
    return out


def _nearby_preview(df: pd.DataFrame, row_index: int, window: int = 2, max_cols: int = 6) -> str:
    if df is None or df.empty:
        return ""
    n = len(df)
    if n == 0:
        return ""
    ridx = max(0, min(row_index, n - 1))
    lo = max(0, ridx - window)
    hi = min(n, ridx + window + 1)
    lines = []
    sample = df.iloc[lo:hi, :max_cols].fillna("").astype(str)
    for i, row in sample.iterrows():
        vals = [x.strip() for x in row.tolist()]
        vals = [v for v in vals if v]
        if vals:
            lines.append(f"{i}: " + " | ".join(vals))
    text = " || ".join(lines)
    return text[:500] + ("..." if len(text) > 500 else "")


def build_manual_review_queue(
    output_dir: Path,
    report_08: Optional[Path],
    report_19: Optional[Path],
    output_22: Path,
) -> Tuple[str, Dict[str, int]]:
    summary08, fm08 = _load_report_08(report_08, output_dir)
    cand19, det19 = _load_report_19(report_19, output_dir)
    if summary08.empty:
        raise FileNotFoundError("08 report summary not found or unreadable.")

    summary08 = summary08.fillna("")
    fm08 = fm08.fillna("")
    cand19 = cand19.fillna("")
    det19 = det19.fillna("")

    review_summary_rows: List[Dict[str, object]] = []
    metric_review_rows: List[Dict[str, object]] = []
    invalid_rows: List[Dict[str, object]] = []
    pointer_rows: List[Dict[str, object]] = []
    hard_rows: List[Dict[str, object]] = []

    # Build quick lookup on 08 financial_metrics for repair flags/source.
    fm_lookup: Dict[Tuple[str, str, str], Dict[str, object]] = {}
    if not fm08.empty and "asset_package" in fm08.columns:
        metric_col = "标准指标" if "标准指标" in fm08.columns else ("standard_metric" if "standard_metric" in fm08.columns else "")
        if metric_col:
            for _, r in fm08.iterrows():
                key = (_norm(r.get("asset_package")), _norm(r.get(metric_col)), _norm(r.get("source_row_label")))
                fm_lookup.setdefault(key, r.to_dict())

    # Prepare 19 grouped data.
    detail_group: Dict[Tuple[str, str, str], pd.DataFrame] = {}
    if not det19.empty:
        for (a, m, l), g in det19.groupby(["asset_package", "standard_metric", "source_row_label"], dropna=False):
            detail_group[(_norm(a), _norm(m), _norm(l))] = g.copy()

    cand_map: Dict[Tuple[str, str], Dict[str, object]] = {}
    if not cand19.empty:
        for _, r in cand19.iterrows():
            cand_map[(_norm(r.get("asset_package")), _norm(r.get("standard_metric")))] = r.to_dict()

    for _, row in summary08.iterrows():
        asset = _norm(row.get("asset_package"))
        if not asset:
            continue
        tier = _norm(row.get("data_usability_tier"))
        label_hit = _to_int(row.get("label_hit_metric_count"), 0)
        value_valid = _to_int(row.get("value_valid_metric_count"), 0)
        value_ratio = row.get("value_valid_ratio", "")
        priority, reason = _tier_priority(tier, label_hit, value_valid)
        action = _tier_action(tier)

        review_summary_rows.append(
            {
                "asset_package": asset,
                "data_usability_tier": tier,
                "label_hit_metric_count": label_hit,
                "value_valid_metric_count": value_valid,
                "value_valid_ratio": value_ratio,
                "primary_bottleneck": _norm(row.get("primary_bottleneck")),
                "value_top_issue_flags": _norm(row.get("value_top_issue_flags")),
                "review_priority": priority,
                "review_reason": reason,
                "recommended_action": action,
            }
        )

        asset_dir = _get_asset_dir(output_dir, asset)
        has_probe_21, best_probe = (False, -1)
        if asset_dir is not None:
            has_probe_21, best_probe = _load_best_probe_21(asset_dir)
        if tier == "E_hard_sample":
            hard_rows.append(
                {
                    "asset_package": asset,
                    "reason": f"tier={tier}; label_hit={label_hit}; value_valid={value_valid}",
                    "has_column_group_probe": has_probe_21,
                    "best_value_valid_metric_count": best_probe if best_probe >= 0 else "",
                    "next_action": "当前规则不适配，建议新后端或人工复核",
                }
            )

        # Build metric queue
        for metric in CORE_METRICS:
            c = cand_map.get((asset, metric), {})
            metric_status = _norm(c.get("metric_value_status", "missing")) if c else "missing"
            label_hit_bool = _to_int(c.get("candidate_count", 0), 0) > 0 if c else False
            value_valid_bool = metric_status == "valid"
            best_label = _norm(c.get("best_candidate_source_row_label")) if c else ""
            best_issue = _norm(c.get("best_candidate_issue_flags")) if c else ""
            g = detail_group.get((asset, metric, best_label), pd.DataFrame())

            source_table_index = ""
            source_row_index = ""
            source_column = ""
            value_validation_status = metric_status
            raw_examples = ""
            parsed_examples = ""
            repair_applied = ""

            if not g.empty:
                source_table_index = _norm(g.iloc[0].get("source_table_index"))
                source_row_index = _norm(g.iloc[0].get("source_row_index"))
                source_column = _norm(g.iloc[0].get("source_column"))
                raw_examples = "|".join([_norm(x) for x in g["raw_value"].head(3).tolist() if _norm(x)])
                parsed_examples = "|".join([_norm(x) for x in g["parsed_value"].head(3).tolist() if _norm(x)])
                statuses = [_norm(x) for x in g["validation_status"].tolist() if _norm(x)]
                if "invalid" in statuses:
                    value_validation_status = "invalid"
                elif "suspicious" in statuses:
                    value_validation_status = "suspicious"
                elif "valid" in statuses:
                    value_validation_status = "valid"

            fm_row = fm_lookup.get((asset, metric, best_label), {})
            if fm_row:
                repair_applied = _norm(fm_row.get("value_repair_applied"))
                if not source_column:
                    source_column = _norm(fm_row.get("source_column"))

            include = (
                (metric_status in {"missing", "invalid", "suspicious"})
                or (label_hit_bool and (not value_valid_bool))
                or (tier != "A_usable")
            )
            if not include:
                continue

            metric_review_rows.append(
                {
                    "asset_package": asset,
                    "standard_metric": metric,
                    "metric_value_status": metric_status,
                    "label_hit": label_hit_bool,
                    "value_valid": value_valid_bool,
                    "value_validation_status": value_validation_status,
                    "value_issue_flags": best_issue,
                    "source_row_label": best_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "source_column": source_column,
                    "raw_value_examples": raw_examples,
                    "parsed_value_examples": parsed_examples,
                    "repair_applied": repair_applied,
                    "recommendation": (
                        "复核原表定位与列绑定" if metric_status in {"invalid", "suspicious"} else "补录或人工确认缺失值"
                    ),
                }
            )

    # invalid value examples from 19 details
    if not det19.empty:
        for _, r in det19.iterrows():
            flags = set(_split_flags(r.get("issue_flags", "")))
            status = _norm(r.get("validation_status"))
            if not flags.intersection(KEY_INVALID_FLAGS) and status != "invalid":
                continue
            rec = "人工复核该值来源行与列绑定"
            if "invalid_ratio_too_large" in flags:
                rec = "比率极值异常，优先检查错列"
            elif "invalid_eps_too_large" in flags:
                rec = "EPS极值异常，优先检查错列"
            elif "label_value_glued" in flags:
                rec = "疑似标签值粘连，检查同列文本污染"

            invalid_rows.append(
                {
                    "asset_package": _norm(r.get("asset_package")),
                    "standard_metric": _norm(r.get("standard_metric")),
                    "year": _norm(r.get("year")),
                    "raw_value": _norm(r.get("raw_value")),
                    "parsed_value": _norm(r.get("parsed_value")),
                    "issue_flags": _norm(r.get("issue_flags")),
                    "source_row_label": _norm(r.get("source_row_label")),
                    "source_table_index": _norm(r.get("source_table_index")),
                    "source_row_index": _norm(r.get("source_row_index")),
                    "recommendation": rec,
                }
            )

    # pointers with 02 nearby preview
    metric_df = pd.DataFrame(metric_review_rows).fillna("")
    for _, r in metric_df.iterrows():
        asset = _norm(r.get("asset_package"))
        st_idx = _to_int(r.get("source_table_index"), -1)
        sr_idx = _to_int(r.get("source_row_index"), -1)
        asset_dir = _get_asset_dir(output_dir, asset)
        sheet_name = ""
        nearby = ""
        file_path = ""
        if asset_dir is not None:
            file_path = str(asset_dir)
            try:
                sheet_map = _load_02_sheet_map(asset_dir)
                if st_idx in sheet_map:
                    sheet_name, df = sheet_map[st_idx]
                    if sr_idx >= 0:
                        nearby = _nearby_preview(df, sr_idx)
                elif st_idx > 0:
                    sheet_name = f"table_index_{st_idx}_not_found"
            except Exception as exc:
                nearby = f"load_02_error: {exc}"

        pointer_rows.append(
            {
                "asset_package": asset,
                "standard_metric": _norm(r.get("standard_metric")),
                "source_table_index": _norm(r.get("source_table_index")),
                "suggested_sheet_name": sheet_name,
                "source_row_index": _norm(r.get("source_row_index")),
                "source_row_label": _norm(r.get("source_row_label")),
                "nearby_preview": nearby,
                "file_path": file_path,
            }
        )

    review_summary_df = pd.DataFrame(review_summary_rows)
    metric_review_df = pd.DataFrame(metric_review_rows)
    invalid_df = pd.DataFrame(invalid_rows)
    pointers_df = pd.DataFrame(pointer_rows)
    hard_df = pd.DataFrame(hard_rows)

    report_path = _save_excel_robust(
        {
            "review_summary": review_summary_df,
            "metric_review_queue": metric_review_df,
            "invalid_value_examples": invalid_df,
            "source_table_pointers": pointers_df,
            "hard_samples": hard_df,
        },
        output_22,
    )

    pri_counter = Counter(review_summary_df.get("review_priority", pd.Series(dtype=str)).astype(str).tolist())
    stats = {
        "review_summary_rows": len(review_summary_df),
        "P0_count": int(pri_counter.get("P0", 0)),
        "P1_count": int(pri_counter.get("P1", 0)),
        "P2_count": int(pri_counter.get("P2", 0)),
        "P3_count": int(pri_counter.get("P3", 0)),
        "metric_review_queue_rows": len(metric_review_df),
        "invalid_value_examples_rows": len(invalid_df),
        "hard_samples_rows": len(hard_df),
    }
    return report_path, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Build manual review queue from 08/19 reports.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output root path.")
    parser.add_argument("--report-08", default=str(DEFAULT_REPORT_08), help="08 regression report path.")
    parser.add_argument("--report-19", default=str(DEFAULT_REPORT_19), help="19 value validation report path.")
    parser.add_argument("--output-report", default=str(DEFAULT_OUTPUT_22), help="22 manual queue output path.")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    report_08 = Path(args.report_08)
    report_19 = Path(args.report_19)
    output_22 = Path(args.output_report)

    report_path, stats = build_manual_review_queue(
        output_dir=out_dir,
        report_08=report_08 if report_08.exists() else None,
        report_19=report_19 if report_19.exists() else None,
        output_22=output_22,
    )

    print(f"报告路径: {report_path}")
    print(f"review_summary 行数: {stats['review_summary_rows']}")
    print(f"优先级数量: P0={stats['P0_count']}, P1={stats['P1_count']}, P2={stats['P2_count']}, P3={stats['P3_count']}")
    print(f"metric_review_queue 行数: {stats['metric_review_queue_rows']}")
    print(f"invalid_value_examples 行数: {stats['invalid_value_examples_rows']}")
    print(f"hard_samples 数量: {stats['hard_samples_rows']}")

    # Required spot checks
    try:
        df = pd.read_excel(report_path, sheet_name="review_summary", engine="openpyxl").fillna("")
        r317 = df[df["asset_package"].astype(str).str.contains("H3_AP202605141822317484_1", na=False)]
        if not r317.empty:
            row = r317.iloc[0]
            print(
                "317484_check: "
                f"priority={_norm(row.get('review_priority'))}, tier={_norm(row.get('data_usability_tier'))}"
            )
        r218 = df[df["asset_package"].astype(str).str.contains("H3_AP202605121822218343_1", na=False)]
        if not r218.empty:
            row = r218.iloc[0]
            print(
                "218_check: "
                f"priority={_norm(row.get('review_priority'))}, tier={_norm(row.get('data_usability_tier'))}"
            )
    except Exception:
        pass


if __name__ == "__main__":
    main()
