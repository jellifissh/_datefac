import argparse
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = r"D:\_datefac\output"
DEFAULT_REPORT_PATH = r"D:\_datefac\output\08_批量回归报告.xlsx"

CORE_SHEETS = ["主要财务指标", "资产负债表", "利润表", "现金流量表", "财务比率表"]


def _safe_preview_from_df(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 5, max_len: int = 300) -> str:
    if df is None or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        lines.append(" | ".join([str(x).strip() for x in row.tolist() if str(x).strip()]))
    text = " || ".join(lines).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _save_excel_robustly(sheet_map: Dict[str, pd.DataFrame], report_path: str) -> str:
    final_path = report_path
    if os.path.exists(report_path):
        try:
            with open(report_path, "a"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%H%M%S")
            final_path = report_path.replace(".xlsx", f"_副本_{ts}.xlsx")
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        used = set()
        for sheet_name, df in sheet_map.items():
            clean = re.sub(r"[\\/*?:\[\]]", "_", str(sheet_name))[:31] or "Sheet"
            base = clean
            idx = 1
            while clean in used:
                suffix = f"_{idx}"
                clean = f"{base[:31-len(suffix)]}{suffix}"
                idx += 1
            used.add(clean)
            out = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out.to_excel(writer, sheet_name=clean, index=False)
    return final_path


def _find_asset_packages(output_dir: str) -> List[str]:
    if not os.path.isdir(output_dir):
        return []
    pkgs = []
    for name in os.listdir(output_dir):
        path = os.path.join(output_dir, name)
        if os.path.isdir(path) and name.endswith("_资产包"):
            pkgs.append(path)
    return sorted(pkgs)


def _select_latest_file_by_rule(files: List[str], rule: str) -> Optional[str]:
    candidates = []
    for fn in files:
        base = os.path.basename(fn)
        lower = base.lower()
        if rule == "01" and base.startswith("01_") and lower.endswith(".md"):
            candidates.append(fn)
        elif rule == "02" and base.startswith("02_") and lower.endswith(".xlsx"):
            candidates.append(fn)
        elif rule == "03" and base.startswith("03_") and lower.endswith(".xlsx"):
            candidates.append(fn)
        elif rule == "04" and base.startswith("04_") and lower.endswith(".xlsx"):
            candidates.append(fn)
        elif rule == "05" and base.startswith("05_") and lower.endswith(".xlsx"):
            candidates.append(fn)
        elif rule == "07" and lower.endswith(".xlsx") and ("segment_map" in lower or base.startswith("07_")):
            candidates.append(fn)
    if not candidates:
        return None
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]


def _find_selected_files(asset_pkg: str) -> Dict[str, Optional[str]]:
    all_files = [os.path.join(asset_pkg, x) for x in os.listdir(asset_pkg) if os.path.isfile(os.path.join(asset_pkg, x))]
    return {
        "01": _select_latest_file_by_rule(all_files, "01"),
        "02": _select_latest_file_by_rule(all_files, "02"),
        "03": _select_latest_file_by_rule(all_files, "03"),
        "04": _select_latest_file_by_rule(all_files, "04"),
        "05": _select_latest_file_by_rule(all_files, "05"),
        "07": _select_latest_file_by_rule(all_files, "07"),
    }


def _normalize_sheet_name(s: str) -> str:
    return re.sub(r"\s+", "", str(s or "").strip())


def _hits_core_sheet(sheet_names: List[str], core_name: str) -> bool:
    ncore = _normalize_sheet_name(core_name)
    for s in sheet_names:
        ns = _normalize_sheet_name(s)
        if ns == ncore or ns.startswith(ncore + "_"):
            return True
    return False


def _extract_02_details(asset_name: str, file_02: str) -> Tuple[Dict, List[Dict], Optional[List[str]], Optional[str]]:
    summary_updates: Dict = {}
    detail_rows: List[Dict] = []
    error = ""
    sheet_names: Optional[List[str]] = None
    try:
        xls = pd.ExcelFile(file_02, engine="openpyxl")
        sheet_names = list(xls.sheet_names)
        summary_updates["sheet_count_02"] = len(sheet_names)
        summary_updates["sheet_names_02"] = "|".join(sheet_names)
        summary_updates["has_index_sheet"] = any(_normalize_sheet_name(x) == _normalize_sheet_name("00_目录") for x in sheet_names)

        summary_updates["has_key_metrics_sheet"] = _hits_core_sheet(sheet_names, "主要财务指标")
        summary_updates["has_balance_sheet"] = _hits_core_sheet(sheet_names, "资产负债表")
        summary_updates["has_income_statement"] = _hits_core_sheet(sheet_names, "利润表")
        summary_updates["has_cashflow_sheet"] = _hits_core_sheet(sheet_names, "现金流量表")
        summary_updates["has_ratio_sheet"] = _hits_core_sheet(sheet_names, "财务比率表")
        summary_updates["expected_5_core_sheets_hit_count"] = sum(
            1 for core in CORE_SHEETS if _hits_core_sheet(sheet_names, core)
        )

        for s in sheet_names:
            try:
                df = pd.read_excel(file_02, sheet_name=s, engine="openpyxl")
                detail_rows.append(
                    {
                        "asset_package": asset_name,
                        "sheet_name": s,
                        "rows": int(df.shape[0]),
                        "cols": int(df.shape[1]),
                        "preview": _safe_preview_from_df(df),
                    }
                )
            except Exception as exc:
                detail_rows.append(
                    {
                        "asset_package": asset_name,
                        "sheet_name": s,
                        "rows": "",
                        "cols": "",
                        "preview": f"read_sheet_error: {exc}",
                    }
                )
    except Exception as exc:
        error = f"read_02_error: {exc}"
    return summary_updates, detail_rows, sheet_names, error


def _extract_05_details(asset_name: str, file_05: str) -> Tuple[Dict, List[Dict], Optional[str]]:
    summary_updates: Dict = {
        "core_financial_metric_count_05": 0,
        "core_financial_metrics_05": "",
    }
    detail_rows: List[Dict] = []
    error = ""
    try:
        xls = pd.ExcelFile(file_05, engine="openpyxl")
        target_sheet = None
        for s in xls.sheet_names:
            ns = _normalize_sheet_name(s)
            if ns == _normalize_sheet_name("核心指标宽表") or "核心指标宽表" in s:
                target_sheet = s
                break
        if target_sheet is None:
            error = "missing_sheet_核心指标宽表"
            return summary_updates, detail_rows, error

        df = pd.read_excel(file_05, sheet_name=target_sheet, engine="openpyxl")
        if df.empty:
            return summary_updates, detail_rows, error

        metric_col = None
        for col in df.columns:
            if str(col).strip() in ("指标", "核心指标", "metric", "Metric"):
                metric_col = col
                break
        if metric_col is None:
            metric_col = df.columns[0]

        year_cols = [c for c in df.columns if re.search(r"20\d{2}", str(c))]
        source_table_col = next((c for c in df.columns if "来源表" in str(c)), None)
        source_type_col = next((c for c in df.columns if "来源类型" in str(c)), None)
        confidence_col = next((c for c in df.columns if "置信" in str(c) or "confidence" in str(c).lower()), None)

        metrics = []
        for _, row in df.iterrows():
            metric = str(row.get(metric_col, "")).strip()
            if not metric:
                continue
            metrics.append(metric)
            year_values = []
            for yc in year_cols:
                v = row.get(yc, "")
                if pd.isna(v) or str(v).strip() == "":
                    continue
                year_values.append(f"{yc}={v}")
            detail_rows.append(
                {
                    "asset_package": asset_name,
                    "指标": metric,
                    "年份列和值": "; ".join(year_values),
                    "来源表": row.get(source_table_col, "") if source_table_col else "",
                    "来源类型": row.get(source_type_col, "") if source_type_col else "",
                    "置信度": row.get(confidence_col, "") if confidence_col else "",
                }
            )
        summary_updates["core_financial_metric_count_05"] = len(set(metrics))
        summary_updates["core_financial_metrics_05"] = "|".join(sorted(set(metrics)))
    except Exception as exc:
        error = f"read_05_error: {exc}"
    return summary_updates, detail_rows, error


def _extract_07_segment_map(asset_name: str, file_07: str) -> Tuple[List[Dict], Optional[str]]:
    rows: List[Dict] = []
    error = ""
    try:
        xls = pd.ExcelFile(file_07, engine="openpyxl")
        target_sheet = None
        for s in xls.sheet_names:
            if _normalize_sheet_name(s) == _normalize_sheet_name("segment_map"):
                target_sheet = s
                break
        if target_sheet is None:
            return rows, "missing_sheet_segment_map"
        df = pd.read_excel(file_07, sheet_name=target_sheet, engine="openpyxl")
        if df.empty:
            return rows, ""
        for _, row in df.iterrows():
            rec = {"asset_package": asset_name}
            for c in df.columns:
                rec[str(c)] = row.get(c, "")
            rows.append(rec)
    except Exception as exc:
        error = f"read_07_error: {exc}"
    return rows, error


def build_regression_report(output_dir: str, report_path: str) -> Tuple[str, Dict[str, int]]:
    packages = _find_asset_packages(output_dir)
    summary_rows: List[Dict] = []
    details_02_rows: List[Dict] = []
    details_05_rows: List[Dict] = []
    segment_map_rows: List[Dict] = []

    for pkg in packages:
        asset_name = os.path.basename(pkg)
        selected = _find_selected_files(pkg)
        row = {
            "asset_package": asset_name,
            "report_name": asset_name.replace("_资产包", ""),
            "has_01": bool(selected["01"]),
            "has_02": bool(selected["02"]),
            "has_03": bool(selected["03"]),
            "has_04": bool(selected["04"]),
            "has_05": bool(selected["05"]),
            "has_07": bool(selected["07"]),
            "selected_02_file": selected["02"] or "",
            "selected_05_file": selected["05"] or "",
            "sheet_count_02": 0,
            "sheet_names_02": "",
            "has_index_sheet": False,
            "has_key_metrics_sheet": False,
            "has_balance_sheet": False,
            "has_income_statement": False,
            "has_cashflow_sheet": False,
            "has_ratio_sheet": False,
            "expected_5_core_sheets_hit_count": 0,
            "core_financial_metric_count_05": 0,
            "core_financial_metrics_05": "",
            "error": "",
        }

        errors = []
        if selected["02"]:
            upd, drows, _sheet_names, err = _extract_02_details(asset_name, selected["02"])
            row.update(upd)
            details_02_rows.extend(drows)
            if err:
                errors.append(err)
        else:
            errors.append("missing_02")

        if selected["05"]:
            upd5, drows5, err5 = _extract_05_details(asset_name, selected["05"])
            row.update(upd5)
            details_05_rows.extend(drows5)
            if err5:
                errors.append(err5)

        if selected["07"]:
            drows7, err7 = _extract_07_segment_map(asset_name, selected["07"])
            segment_map_rows.extend(drows7)
            if err7:
                errors.append(err7)

        row["error"] = " | ".join([e for e in errors if e])
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    details_02_df = pd.DataFrame(details_02_rows, columns=["asset_package", "sheet_name", "rows", "cols", "preview"])
    details_05_df = pd.DataFrame(
        details_05_rows,
        columns=["asset_package", "指标", "年份列和值", "来源表", "来源类型", "置信度"],
    )
    segment_map_df = pd.DataFrame(segment_map_rows)

    final_report_path = _save_excel_robustly(
        {
            "summary": summary_df,
            "details_02": details_02_df,
            "details_05": details_05_df,
            "segment_map": segment_map_df,
        },
        report_path,
    )
    counters = {
        "asset_packages": len(packages),
        "summary_rows": len(summary_df),
        "details_02_rows": len(details_02_df),
        "details_05_rows": len(details_05_df),
        "segment_map_rows": len(segment_map_df),
    }
    return final_report_path, counters


def main():
    parser = argparse.ArgumentParser(description="Build batch regression report from existing asset packages.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output root containing *_资产包 directories.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH, help="Target regression report xlsx path.")
    args = parser.parse_args()

    final_path, counters = build_regression_report(args.output_dir, args.report_path)
    print(f"资产包数量: {counters['asset_packages']}")
    print(f"回归报告路径: {final_path}")
    print(
        "行数统计: summary={summary_rows}, details_02={details_02_rows}, details_05={details_05_rows}, segment_map={segment_map_rows}".format(
            **counters
        )
    )


if __name__ == "__main__":
    main()
