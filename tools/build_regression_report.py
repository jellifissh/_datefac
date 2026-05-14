import argparse
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = r"D:\_datefac\output"
DEFAULT_REPORT_PATH = r"D:\_datefac\output\08_批量回归报告.xlsx"
ASSET_SUFFIX = "\u8d44\u4ea7\u5305"  # 资产包
CORE_METRICS = [
    "\u8425\u4e1a\u6536\u5165",  # 营业收入
    "\u5f52\u5c5e\u6bcd\u516c\u53f8\u51c0\u5229\u6da6",  # 归属母公司净利润
    "\u6bdb\u5229\u7387",  # 毛利率
    "ROE",
    "\u6bcf\u80a1\u6536\u76ca",  # 每股收益
    "P/E",
    "P/B",
    "EV/EBITDA",
]


def _safe_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 5, max_chars: int = 300) -> str:
    if df is None or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        vals = [str(x).strip() for x in row.tolist()]
        vals = [v for v in vals if v]
        if vals:
            lines.append(" | ".join(vals))
    text = " || ".join(lines)
    return text[:max_chars] + ("..." if len(text) > max_chars else "")


def _safe_sheet_name(name: str, used: set) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", str(name or "Sheet"))[:31] or "Sheet"
    base = cleaned
    i = 1
    while cleaned in used:
        suffix = f"_{i}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(cleaned)
    return cleaned


def _save_excel_robust(sheet_map: Dict[str, pd.DataFrame], report_path: str) -> str:
    final_path = report_path
    if os.path.exists(report_path):
        try:
            with open(report_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%H%M%S")
            final_path = report_path.replace(".xlsx", f"_copy_{ts}.xlsx")

    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        used = set()
        for sheet_name, df in sheet_map.items():
            safe = _safe_sheet_name(sheet_name, used)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return final_path


def _find_asset_packages(output_dir: str) -> List[Path]:
    root = Path(output_dir)
    if not root.is_dir():
        return []
    return sorted(
        [x for x in root.iterdir() if x.is_dir() and x.name.endswith(f"_{ASSET_SUFFIX}")],
        key=lambda x: x.name,
    )


def _latest_file(pkg: Path, prefix: str) -> Optional[Path]:
    cands = [x for x in pkg.iterdir() if x.is_file() and x.name.startswith(prefix) and x.suffix.lower() == ".xlsx"]
    if not cands:
        return None
    return sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True)[0]


def _latest_02(pkg: Path) -> Optional[Path]:
    cands = [
        x
        for x in pkg.iterdir()
        if x.is_file() and x.suffix.lower() == ".xlsx" and x.name.startswith("02_") and not x.name.startswith("02A_")
    ]
    if not cands:
        return None
    return sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True)[0]


def _load_consistency_map(output_dir: str) -> Dict[str, Dict[str, object]]:
    report_path = Path(output_dir) / "12_asset_consistency_report.xlsx"
    if not report_path.exists():
        return {}
    try:
        df = pd.read_excel(str(report_path), sheet_name="summary")
    except Exception:
        return {}

    mapping: Dict[str, Dict[str, object]] = {}
    for _, row in df.iterrows():
        name = str(row.get("asset_package", "")).strip()
        if not name:
            continue
        mapping[name] = {
            "consistency_status": str(row.get("consistency_status", "")).strip(),
            "issue_flags": str(row.get("issue_flags", "")).strip(),
            "recommendation": str(row.get("recommendation", "")).strip(),
            "can_join_financial_regression": bool(row.get("can_join_financial_regression", False)),
            "missing_core_artifacts": str(row.get("missing_core_artifacts", "")).strip(),
            "missing_optional_artifacts": str(row.get("missing_optional_artifacts", "")).strip(),
        }
    return mapping


def _load_raw_vs_structured_map(output_dir: str) -> Dict[str, Dict[str, object]]:
    report_path = Path(output_dir) / "11_raw_vs_structured_report.xlsx"
    if not report_path.exists():
        return {}
    try:
        df = pd.read_excel(str(report_path), sheet_name="summary")
    except Exception:
        return {}
    mapping: Dict[str, Dict[str, object]] = {}
    for _, row in df.iterrows():
        name = str(row.get("asset_package", "")).strip()
        if not name:
            continue
        mapping[name] = row.to_dict()
    return mapping


def _raw_quality(file_02a: Optional[Path]) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    summary = {
        "has_02A": bool(file_02a and file_02a.exists()),
        "raw_table_count": 0,
        "raw_good_count": 0,
        "raw_ok_count": 0,
        "raw_bad_count": 0,
        "raw_good_ok_ratio": 0.0,
        "raw_backend_distribution": "",
    }
    rows: List[Dict[str, object]] = []
    if not summary["has_02A"]:
        return summary, rows
    try:
        xls = pd.ExcelFile(str(file_02a))
        idx_sheet = next(
            (s for s in xls.sheet_names if s.startswith("00_") and ("\u7d22\u5f15" in s or "index" in s.lower())),
            xls.sheet_names[0],
        )
        idx_df = pd.read_excel(str(file_02a), sheet_name=idx_sheet)
        if idx_df.empty:
            return summary, rows

        summary["raw_table_count"] = int(len(idx_df))
        qcol = "quality_level" if "quality_level" in idx_df.columns else None
        bcol = "backend" if "backend" in idx_df.columns else None
        if qcol:
            qvc = idx_df[qcol].fillna("NA").astype(str).value_counts()
            summary["raw_good_count"] = int(qvc.get("GOOD", 0))
            summary["raw_ok_count"] = int(qvc.get("OK", 0))
            summary["raw_bad_count"] = int(qvc.get("BAD", 0))
        if bcol:
            bvc = idx_df[bcol].fillna("NA").astype(str).value_counts()
            summary["raw_backend_distribution"] = "|".join([f"{k}:{int(v)}" for k, v in bvc.items()])
        table_cnt = int(summary["raw_table_count"])
        good_ok = int(summary["raw_good_count"]) + int(summary["raw_ok_count"])
        summary["raw_good_ok_ratio"] = round((good_ok / table_cnt), 4) if table_cnt > 0 else 0.0
        rows = idx_df.to_dict(orient="records")
    except Exception:
        pass
    return summary, rows


def _structured_quality(file_02: Optional[Path]) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    summary = {"has_02": bool(file_02 and file_02.exists()), "structured_sheet_count": 0}
    rows: List[Dict[str, object]] = []
    if not summary["has_02"]:
        return summary, rows
    try:
        xls = pd.ExcelFile(str(file_02))
        data_sheets = [s for s in xls.sheet_names if not (s.startswith("00_") and ("\u76ee\u5f55" in s or "index" in s.lower()))]
        summary["structured_sheet_count"] = len(data_sheets)
        for s in data_sheets:
            try:
                df = pd.read_excel(str(file_02), sheet_name=s)
                total = int(df.shape[0] * df.shape[1]) if not df.empty else 0
                non_empty = (
                    int(df.fillna("").astype(str).replace(r"^\s*$", "", regex=True).ne("").sum().sum()) if total else 0
                )
                empty_ratio = round((total - non_empty) / total, 4) if total else 0.0
                rows.append(
                    {
                        "sheet_name": s,
                        "row_count": int(df.shape[0]),
                        "col_count": int(df.shape[1]),
                        "empty_cell_ratio": empty_ratio,
                        "preview": _safe_preview(df),
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "sheet_name": s,
                        "row_count": "",
                        "col_count": "",
                        "empty_cell_ratio": "",
                        "preview": f"read_error: {exc}",
                    }
                )
    except Exception:
        pass
    return summary, rows


def _financial_quality(file_05: Optional[Path]) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    summary = {
        "has_05": bool(file_05 and file_05.exists()),
        "financial_detail_count": 0,
        "financial_metric_hit_count": 0,
        "financial_metric_hit_ratio": 0.0,
        "financial_hit_metrics": "",
        "financial_missing_metrics": "|".join(CORE_METRICS),
        "header_repaired_count": 0,
        "suspicious_misextract_count": 0,
    }
    rows: List[Dict[str, object]] = []
    if not summary["has_05"]:
        return summary, rows
    try:
        xls = pd.ExcelFile(str(file_05))
        detail_df = None
        metric_col = None
        for sn in xls.sheet_names:
            df = pd.read_excel(str(file_05), sheet_name=sn)
            if "source_row_label" in df.columns:
                detail_df = df
                metric_col = "\u6807\u51c6\u6307\u6807" if "\u6807\u51c6\u6307\u6807" in df.columns else df.columns[0]
                break
        if detail_df is None or detail_df.empty:
            return summary, rows
        detail_df = detail_df.fillna("")
        hits = sorted(set(detail_df[metric_col].astype(str).str.strip().tolist()))
        hits = [h for h in hits if h]
        missing = [m for m in CORE_METRICS if m not in hits]
        summary["financial_detail_count"] = int(len(detail_df))
        summary["financial_metric_hit_count"] = int(len(hits))
        summary["financial_metric_hit_ratio"] = round(len(hits) / len(CORE_METRICS), 4)
        summary["financial_hit_metrics"] = "|".join(hits)
        summary["financial_missing_metrics"] = "|".join(missing)

        if "header_repaired" in detail_df.columns:
            summary["header_repaired_count"] = int(
                detail_df["header_repaired"].astype(str).str.lower().isin(["true", "1"]).sum()
            )

        suspicious = 0
        if "source_row_label" in detail_df.columns:
            labels = detail_df["source_row_label"].fillna("").astype(str)
            suspicious = int(
                labels.str.contains(
                    "\u540c\u6bd4|\u589e\u901f|\u589e\u957f\u7387|\u6263\u975e|\u5c11\u6570\u80a1\u4e1c\u635f\u76ca",
                    regex=True,
                ).sum()
            )
        summary["suspicious_misextract_count"] = suspicious
        rows = detail_df.to_dict(orient="records")
    except Exception:
        pass
    return summary, rows


def _diagnose(summary: Dict[str, object]) -> Dict[str, str]:
    extraction_status = "partial"
    postprocess_status = "partial"
    financial_status = "partial"
    bottleneck = "unknown"
    recommendation = "建议人工复核"

    raw_table_count = int(summary.get("raw_table_count", 0) or 0)
    raw_good_ok_ratio = float(summary.get("raw_good_ok_ratio", 0.0) or 0.0)
    raw_bad = int(summary.get("raw_bad_count", 0) or 0)
    structured_sheet_count = int(summary.get("structured_sheet_count", 0) or 0)
    hit_count = int(summary.get("financial_metric_hit_count", 0) or 0)

    if raw_table_count == 0:
        extraction_status = "bad"
    elif raw_bad == raw_table_count and raw_table_count > 0:
        extraction_status = "bad"
    elif raw_good_ok_ratio >= 0.6:
        extraction_status = "good"
    elif raw_good_ok_ratio >= 0.3:
        extraction_status = "partial"
    else:
        extraction_status = "bad"

    if raw_table_count > 0 and structured_sheet_count < raw_table_count * 0.5:
        postprocess_status = "partial"
    elif structured_sheet_count > 0:
        postprocess_status = "good"
    else:
        postprocess_status = "bad"

    if hit_count >= 6:
        financial_status = "good"
    elif 3 <= hit_count <= 5:
        financial_status = "partial"
    else:
        financial_status = "bad"

    if extraction_status == "bad" and financial_status in ("bad", "partial"):
        bottleneck = "extraction_layer"
        recommendation = "优先改抽取后端/后端仲裁，不要继续修 05"
    elif raw_table_count < 3 and hit_count < 3:
        bottleneck = "extraction_coverage"
        recommendation = "原始表格覆盖不足，优先检查抽取后端/缓存/漏表"
    elif extraction_status == "good" and financial_status == "bad":
        bottleneck = "financial_standardizer"
        recommendation = "优先修 05 规则"
    elif financial_status == "good":
        bottleneck = "none_or_minor"
        recommendation = "保持当前策略，优先扩样本验证"
    elif postprocess_status == "partial":
        bottleneck = "postprocess_layer"
        recommendation = "复核 02 相对 02A 的丢表/过滤"
    else:
        bottleneck = "financial_standardizer"
        recommendation = "定向审计 05 未命中指标"

    return {
        "extraction_layer_status": extraction_status,
        "postprocess_layer_status": postprocess_status,
        "financial_standardization_status": financial_status,
        "primary_bottleneck": bottleneck,
        "recommendation": recommendation,
    }


def build_regression_report(output_dir: str, report_path: str) -> Tuple[str, Dict[str, int]]:
    packages = _find_asset_packages(output_dir)
    consistency_map = _load_consistency_map(output_dir)
    raw_vs_map = _load_raw_vs_structured_map(output_dir)

    summary_rows: List[Dict[str, object]] = []
    asset_details_rows: List[Dict[str, object]] = []
    financial_metric_rows: List[Dict[str, object]] = []
    raw_table_quality_rows: List[Dict[str, object]] = []
    rec_rows: List[Dict[str, object]] = []

    consistency_ok_count = 0
    warning_but_eligible_count = 0
    core_missing_count = 0
    eligible_count = 0

    for pkg in packages:
        asset = pkg.name
        cinfo = consistency_map.get(asset, {})
        consistency_status = str(cinfo.get("consistency_status", "")).strip()
        issue_flags = str(cinfo.get("issue_flags", "")).strip()
        missing_core = str(cinfo.get("missing_core_artifacts", "")).strip()
        missing_optional = str(cinfo.get("missing_optional_artifacts", "")).strip()

        file_02a = _latest_file(pkg, "02A_")
        file_02 = _latest_02(pkg)
        file_05 = _latest_file(pkg, "05_")

        # Fallback if consistency report does not yet provide can_join field.
        can_join = bool(cinfo.get("can_join_financial_regression", False))
        if "can_join_financial_regression" not in cinfo:
            can_join = bool(file_02a and file_02 and file_05)

        is_eligible = bool(consistency_status == "OK" or can_join)

        if consistency_status == "OK":
            consistency_ok_count += 1
        if consistency_status == "WARNING" and can_join:
            warning_but_eligible_count += 1
        if not can_join:
            core_missing_count += 1
        if is_eligible:
            eligible_count += 1

        raw_summary, raw_rows = _raw_quality(file_02a)
        structured_summary, structured_rows = _structured_quality(file_02)
        financial_summary, financial_rows = _financial_quality(file_05) if is_eligible else (
            {
                "has_05": bool(file_05 and file_05.exists()),
                "financial_detail_count": 0,
                "financial_metric_hit_count": 0,
                "financial_metric_hit_ratio": 0.0,
                "financial_hit_metrics": "",
                "financial_missing_metrics": "|".join(CORE_METRICS),
                "header_repaired_count": 0,
                "suspicious_misextract_count": 0,
            },
            [],
        )

        summary_row: Dict[str, object] = {
            "asset_package": asset,
            "consistency_status": consistency_status,
            "issue_flags": issue_flags,
            "can_join_financial_regression": can_join,
            "regression_eligible": is_eligible,
            "missing_core_artifacts": missing_core,
            "missing_optional_artifacts": missing_optional,
            **raw_summary,
            **structured_summary,
            **financial_summary,
        }

        if asset in raw_vs_map:
            summary_row["raw_vs_structured_diagnosis"] = str(raw_vs_map[asset].get("diagnosis", ""))
            summary_row["raw_vs_structured_error"] = str(raw_vs_map[asset].get("error_message", ""))
        else:
            summary_row["raw_vs_structured_diagnosis"] = ""
            summary_row["raw_vs_structured_error"] = ""

        diag = _diagnose(summary_row)
        summary_row.update(diag)

        if not is_eligible:
            summary_row["primary_bottleneck"] = "core_artifacts_missing"
            summary_row["recommendation"] = "缺少 02A/02/05，先补核心产物后再纳入 05 回归"
            summary_row["financial_standardization_status"] = "bad"

        summary_rows.append(summary_row)

        for r in structured_rows:
            rec = {"asset_package": asset}
            rec.update(r)
            if not is_eligible:
                rec["note"] = "not_eligible_for_financial_regression"
            asset_details_rows.append(rec)

        if is_eligible:
            for r in financial_rows:
                rec = {"asset_package": asset}
                rec.update(r)
                financial_metric_rows.append(rec)

        for r in raw_rows:
            rec = {"asset_package": asset}
            rec.update(r)
            raw_table_quality_rows.append(rec)

        rec_rows.append(
            {
                "asset_package": asset,
                "regression_eligible": is_eligible,
                "can_join_financial_regression": can_join,
                "consistency_status": consistency_status,
                "primary_bottleneck": summary_row["primary_bottleneck"],
                "recommendation": summary_row["recommendation"],
                "extraction_layer_status": summary_row["extraction_layer_status"],
                "postprocess_layer_status": summary_row["postprocess_layer_status"],
                "financial_standardization_status": summary_row["financial_standardization_status"],
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    asset_details_df = pd.DataFrame(asset_details_rows)
    financial_metrics_df = pd.DataFrame(financial_metric_rows)
    raw_table_quality_df = pd.DataFrame(raw_table_quality_rows)
    recommendations_df = pd.DataFrame(rec_rows)

    final = _save_excel_robust(
        {
            "summary": summary_df,
            "asset_details": asset_details_df,
            "financial_metrics": financial_metrics_df,
            "raw_table_quality": raw_table_quality_df,
            "recommendations": recommendations_df,
        },
        report_path,
    )

    counters = {
        "total_asset_packages": len(packages),
        "summary_rows": len(summary_df),
        "asset_details_rows": len(asset_details_df),
        "financial_metrics_rows": len(financial_metrics_df),
        "raw_table_quality_rows": len(raw_table_quality_df),
        "recommendations_rows": len(recommendations_df),
        "regression_eligible_asset_count": eligible_count,
        "consistency_ok_count": consistency_ok_count,
        "consistency_warning_but_eligible_count": warning_but_eligible_count,
        "core_artifacts_missing_count": core_missing_count,
    }
    return final, counters


def main() -> None:
    parser = argparse.ArgumentParser(description="Build batch regression report with layer diagnostics.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output root containing *_资产包 directories.")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH, help="Target report xlsx path.")
    args = parser.parse_args()

    final, counters = build_regression_report(args.output_dir, args.report_path)
    print(f"报告路径: {final}")
    print(f"summary行数: {counters['summary_rows']}")
    print(
        "行数统计: asset_details={asset_details_rows}, financial_metrics={financial_metrics_rows}, "
        "raw_table_quality={raw_table_quality_rows}, recommendations={recommendations_rows}".format(**counters)
    )
    print(
        "口径统计: total_asset_packages={total_asset_packages}, regression_eligible_asset_count={regression_eligible_asset_count}, "
        "consistency_ok_count={consistency_ok_count}, consistency_warning_but_eligible_count={consistency_warning_but_eligible_count}, "
        "core_artifacts_missing_count={core_artifacts_missing_count}".format(**counters)
    )


if __name__ == "__main__":
    main()
