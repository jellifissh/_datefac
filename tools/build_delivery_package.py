import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
DEFAULT_DELIVERY_DIR = Path(r"D:\_datefac\output\delivery_package")


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_int(v, default: int = -1) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _to_bool(v) -> bool:
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _safe_read_excel(path: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if not path or not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl").fillna("")
    except Exception:
        return pd.DataFrame()


def _find_report_file(output_dir: Path, preferred_name: str, prefix: str) -> Optional[Path]:
    p = output_dir / preferred_name
    if p.exists():
        return p
    matches = sorted(output_dir.glob(f"{prefix}*.xlsx"))
    return matches[0] if matches else None


def _safe_write_excel(df: pd.DataFrame, path: Path) -> Path:
    final_path = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(final_path, index=False, engine="openpyxl")
    return final_path


def _safe_write_text(text: str, path: Path) -> Path:
    final_path = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(text, encoding="utf-8")
    return final_path


def _build_pdf_map(df24_summary: pd.DataFrame, df26_regions: pd.DataFrame, df08_raw_quality: pd.DataFrame) -> Dict[str, str]:
    m: Dict[str, str] = {}
    for df, col in [(df24_summary, "source_pdf"), (df26_regions, "source_pdf"), (df08_raw_quality, "source_pdf")]:
        if df.empty or col not in df.columns or "asset_package" not in df.columns:
            continue
        for _, r in df.iterrows():
            ap = _norm(r.get("asset_package"))
            sp = _norm(r.get(col))
            if ap and sp and ap not in m:
                m[ap] = Path(sp).name
    return m


def _build_crop_lookup(df26_regions: pd.DataFrame) -> Dict[Tuple[str, int], Dict[str, str]]:
    lookup: Dict[Tuple[str, int], Dict[str, str]] = {}
    if df26_regions.empty:
        return lookup
    for _, r in df26_regions.iterrows():
        ap = _norm(r.get("asset_package"))
        tidx = _to_int(r.get("table_index"))
        if not ap or tidx < 0:
            continue
        key = (ap, tidx)
        cur = lookup.get(key)
        cand = {
            "crop_png_path": _norm(r.get("crop_png_path")),
            "review_reason": _norm(r.get("review_reason")),
            "needs_manual_review": _norm(r.get("needs_manual_review")),
            "linked_invalid_metric_count": _norm(r.get("linked_invalid_metric_count")),
        }
        if cur is None:
            lookup[key] = cand
        else:
            # Prefer rows with existing crop path.
            if not _norm(cur.get("crop_png_path")) and _norm(cand.get("crop_png_path")):
                lookup[key] = cand
    return lookup


def _resolve_year_columns(df08_fin_metrics: pd.DataFrame) -> List[str]:
    ignore = {
        "asset_package",
        "标准指标",
        "source_row_label",
        "source_table_index",
        "source_table_type",
        "source_row_index",
        "source_label_column",
        "label_detect_method",
        "source_column",
        "matched_alias",
        "match_method",
        "confidence",
        "non_empty_year_count",
        "raw_year_values",
        "value_repair_applied",
        "value_repair_strategy",
        "value_repair_issue_flags",
        "repaired_year_count",
        "value_validation_status",
        "value_issue_flags",
        "valid_year_count",
        "invalid_year_count",
        "header_repaired",
        "header_source_row",
    }
    year_cols: List[str] = []
    for c in df08_fin_metrics.columns:
        cs = _norm(c)
        if cs in ignore:
            continue
        if any(ch.isdigit() for ch in cs):
            year_cols.append(cs)
    return year_cols


def _infer_unit(metric: str) -> str:
    if metric in {"毛利率", "ROE"}:
        return "%"
    if metric in {"P/E", "P/B", "EV/EBITDA"}:
        return "x"
    return ""


def _build_trusted_metrics(
    df08_fin_metrics: pd.DataFrame,
    df23_assets: pd.DataFrame,
    df24_summary: pd.DataFrame,
    df26_regions: pd.DataFrame,
    pdf_map: Dict[str, str],
) -> pd.DataFrame:
    if df08_fin_metrics.empty:
        return pd.DataFrame(
            columns=[
                "source_pdf",
                "asset_package",
                "report_type",
                "data_usability_tier",
                "standard_metric",
                "year",
                "value",
                "unit",
                "value_validation_status",
                "value_repair_applied",
                "source_row_label",
                "source_table_index",
                "source_row_index",
                "source_column",
                "evidence_crop_path",
                "trace_note",
            ]
        )
    year_cols = _resolve_year_columns(df08_fin_metrics)
    crop_lookup = _build_crop_lookup(df26_regions)

    tier_map = {}
    for _, r in df23_assets.iterrows():
        ap = _norm(r.get("asset_package"))
        if ap:
            tier_map[ap] = {
                "data_usability_tier": _norm(r.get("data_usability_tier")),
                "report_type": _norm(r.get("report_type")),
            }
    for _, r in df24_summary.iterrows():
        ap = _norm(r.get("asset_package"))
        if ap and ap in tier_map and not tier_map[ap].get("report_type"):
            tier_map[ap]["report_type"] = _norm(r.get("report_type"))
        elif ap and ap not in tier_map:
            tier_map[ap] = {
                "data_usability_tier": "",
                "report_type": _norm(r.get("report_type")),
            }

    out_rows: List[Dict[str, str]] = []
    for _, r in df08_fin_metrics.iterrows():
        if _norm(r.get("value_validation_status")).lower() != "valid":
            continue
        ap = _norm(r.get("asset_package"))
        metric = _norm(r.get("标准指标"))
        source_table_index = _to_int(r.get("source_table_index"))
        source_row_index = _to_int(r.get("source_row_index"))
        source_col = _norm(r.get("source_column"))
        source_label = _norm(r.get("source_row_label"))
        evidence_crop = ""
        if (ap, source_table_index) in crop_lookup:
            evidence_crop = _norm(crop_lookup[(ap, source_table_index)].get("crop_png_path"))
        for y in year_cols:
            raw_val = r.get(y)
            sval = _norm(raw_val)
            if not sval:
                continue
            out_rows.append(
                {
                    "source_pdf": pdf_map.get(ap, ""),
                    "asset_package": ap,
                    "report_type": tier_map.get(ap, {}).get("report_type", ""),
                    "data_usability_tier": tier_map.get(ap, {}).get("data_usability_tier", ""),
                    "standard_metric": metric,
                    "year": y,
                    "value": sval,
                    "unit": _infer_unit(metric),
                    "value_validation_status": _norm(r.get("value_validation_status")),
                    "value_repair_applied": _norm(r.get("value_repair_applied")),
                    "source_row_label": source_label,
                    "source_table_index": source_table_index if source_table_index >= 0 else "",
                    "source_row_index": source_row_index if source_row_index >= 0 else "",
                    "source_column": source_col,
                    "evidence_crop_path": evidence_crop,
                    "trace_note": "08.financial_metrics valid candidate",
                }
            )
    return pd.DataFrame(out_rows)


def _build_manual_review(
    df22_metric_queue: pd.DataFrame,
    df22_invalid: pd.DataFrame,
    df26_regions: pd.DataFrame,
) -> pd.DataFrame:
    crop_lookup = _build_crop_lookup(df26_regions)
    out_rows: List[Dict[str, str]] = []

    for _, r in df22_metric_queue.iterrows():
        ap = _norm(r.get("asset_package"))
        tidx = _to_int(r.get("source_table_index"))
        evidence = _norm(crop_lookup.get((ap, tidx), {}).get("crop_png_path", ""))
        out_rows.append(
            {
                "asset_package": ap,
                "standard_metric": _norm(r.get("standard_metric")),
                "metric_value_status": _norm(r.get("metric_value_status")),
                "value_issue_flags": _norm(r.get("value_issue_flags")),
                "raw_value_examples": _norm(r.get("raw_value_examples")),
                "source_row_label": _norm(r.get("source_row_label")),
                "source_table_index": tidx if tidx >= 0 else "",
                "source_row_index": _to_int(r.get("source_row_index"), default=""),
                "recommendation": _norm(r.get("recommendation")),
                "evidence_crop_path": evidence,
                "source": "metric_review_queue",
            }
        )

    for _, r in df22_invalid.iterrows():
        ap = _norm(r.get("asset_package"))
        tidx = _to_int(r.get("source_table_index"))
        evidence = _norm(crop_lookup.get((ap, tidx), {}).get("crop_png_path", ""))
        raw_val = _norm(r.get("raw_value"))
        out_rows.append(
            {
                "asset_package": ap,
                "standard_metric": _norm(r.get("standard_metric")),
                "metric_value_status": "invalid",
                "value_issue_flags": _norm(r.get("issue_flags")),
                "raw_value_examples": raw_val,
                "source_row_label": _norm(r.get("source_row_label")),
                "source_table_index": tidx if tidx >= 0 else "",
                "source_row_index": _to_int(r.get("source_row_index"), default=""),
                "recommendation": _norm(r.get("recommendation")),
                "evidence_crop_path": evidence,
                "source": "invalid_value_examples",
            }
        )
    return pd.DataFrame(out_rows)


def _build_excluded_or_failed(
    df23_assets: pd.DataFrame,
    df24_summary: pd.DataFrame,
    df08_summary: pd.DataFrame,
    pdf_map: Dict[str, str],
) -> pd.DataFrame:
    m24 = {}
    for _, r in df24_summary.iterrows():
        ap = _norm(r.get("asset_package"))
        if ap:
            m24[ap] = {
                "source_pdf": _norm(r.get("source_pdf")),
                "report_type": _norm(r.get("report_type")),
                "target_applicability": _norm(r.get("target_applicability")),
                "should_include_in_8_metric_eval": _norm(r.get("should_include_in_8_metric_eval")),
                "reason": _norm(r.get("reason")),
                "recommendation": _norm(r.get("recommendation")),
            }
    m08 = {}
    for _, r in df08_summary.iterrows():
        ap = _norm(r.get("asset_package"))
        if ap:
            m08[ap] = {
                "missing_core_artifacts": _norm(r.get("missing_core_artifacts")),
                "recommendation": _norm(r.get("recommendation")),
                "eval_scope": _norm(r.get("eval_scope")),
            }
    out_rows: List[Dict[str, str]] = []
    for _, r in df23_assets.iterrows():
        ap = _norm(r.get("asset_package"))
        tier = _norm(r.get("data_usability_tier"))
        report_type = _norm(r.get("report_type")) or _norm(m24.get(ap, {}).get("report_type"))
        target_app = _norm(r.get("target_applicability")) or _norm(m24.get(ap, {}).get("target_applicability"))
        in_eval = _norm(r.get("should_include_in_8_metric_eval")) or _norm(
            m24.get(ap, {}).get("should_include_in_8_metric_eval")
        )
        missing_core = _norm(m08.get(ap, {}).get("missing_core_artifacts"))
        is_out_scope = str(in_eval).lower() in {"false", "0", "no"} or _norm(m08.get(ap, {}).get("eval_scope")) == "out_of_scope_non_target"
        is_failed_tier = tier in {"D_insufficient", "E_hard_sample"}
        has_core_missing = bool(missing_core)
        if not (is_out_scope or is_failed_tier or has_core_missing):
            continue
        out_rows.append(
            {
                "source_pdf": _norm(m24.get(ap, {}).get("source_pdf")) or pdf_map.get(ap, ""),
                "asset_package": ap,
                "report_type": report_type,
                "target_applicability": target_app,
                "should_include_in_8_metric_eval": in_eval,
                "data_usability_tier": tier,
                "reason": _norm(m24.get(ap, {}).get("reason")) or _norm(r.get("primary_bottleneck")) or missing_core,
                "recommendation": _norm(m24.get(ap, {}).get("recommendation"))
                or _norm(m08.get(ap, {}).get("recommendation"))
                or _norm(r.get("recommended_action")),
            }
        )
    return pd.DataFrame(out_rows)


def _build_region_index(df26_regions: pd.DataFrame) -> pd.DataFrame:
    if df26_regions.empty:
        return pd.DataFrame(
            columns=[
                "asset_package",
                "page_number",
                "table_index",
                "crop_png_path",
                "quality_level",
                "quality_flags",
                "needs_manual_review",
                "review_reason",
                "linked_invalid_metric_count",
            ]
        )
    cols = {
        "asset_package": "asset_package",
        "page_number": "page_number",
        "table_index": "table_index",
        "crop_png_path": "crop_png_path",
        "quality_level": "quality_level",
        "quality_flags": "quality_flags",
        "needs_manual_review": "needs_manual_review",
        "review_reason": "review_reason",
        "linked_invalid_metric_count": "linked_invalid_metric_count",
    }
    out = pd.DataFrame()
    for c, nc in cols.items():
        out[nc] = df26_regions[c] if c in df26_regions.columns else ""
    return out


def _build_summary_markdown(
    df24_scope: pd.DataFrame,
    df23_summary: pd.DataFrame,
    df23_assets: pd.DataFrame,
    trusted_rows: int,
    manual_rows: int,
) -> str:
    total_pdf = 0
    target = partial = non_target = unknown = 0
    if not df24_scope.empty:
        row = df24_scope.iloc[0].to_dict()
        total_pdf = _to_int(row.get("total_pdfs"), 0)
        target = _to_int(row.get("target_count"), 0)
        partial = _to_int(row.get("partial_count"), 0)
        non_target = _to_int(row.get("non_target_count"), 0)
        unknown = _to_int(row.get("unknown_count"), 0)

    tier_counts = {"A_usable": 0, "B_partial_review": 0, "C_label_only_untrusted": 0, "D_insufficient": 0, "E_hard_sample": 0}
    if not df23_assets.empty and "data_usability_tier" in df23_assets.columns:
        vc = df23_assets["data_usability_tier"].value_counts(dropna=False)
        for k in tier_counts.keys():
            tier_counts[k] = int(vc.get(k, 0))

    hard_sample_count = tier_counts["E_hard_sample"]
    lines = [
        "# 处理摘要",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 本次处理 PDF 数：{total_pdf}",
        f"- 目标报告数量：{target + partial}",
        f"- 非目标报告数量：{non_target}",
        f"- 未知类型数量：{unknown}",
        "",
        "## A/B/C/D/E 分布",
        f"- A_usable：{tier_counts['A_usable']}",
        f"- B_partial_review：{tier_counts['B_partial_review']}",
        f"- C_label_only_untrusted：{tier_counts['C_label_only_untrusted']}",
        f"- D_insufficient：{tier_counts['D_insufficient']}",
        f"- E_hard_sample：{tier_counts['E_hard_sample']}",
        "",
        f"- 自动可信指标数量：{trusted_rows}",
        f"- 需人工复核指标数量：{manual_rows}",
        f"- hard sample 数量：{hard_sample_count}",
        "",
        "## 当前能力边界",
        "- 当前交付包只纳入 value_validation_status=valid 的自动可信指标。",
        "- B/D/E 与非目标报告仍需人工复核或专用流程处理。",
        "- 当前不是全自动无人工复核系统。",
    ]
    return "\n".join(lines) + "\n"


def build_delivery_package(output_dir: Path, delivery_dir: Path) -> Dict[str, object]:
    p08 = _find_report_file(output_dir, "08_批量回归报告.xlsx", "08_")
    p19 = _find_report_file(output_dir, "19_financial_value_validation_report.xlsx", "19_")
    p22 = _find_report_file(output_dir, "22_manual_review_queue.xlsx", "22_")
    p23 = _find_report_file(output_dir, "23_baseline_evaluation_report.xlsx", "23_")
    p24 = _find_report_file(output_dir, "24_report_type_diagnostics.xlsx", "24_")
    p26 = _find_report_file(output_dir, "26_table_region_asset_quality_report.xlsx", "26_")

    df08_summary = _safe_read_excel(p08, "summary")
    df08_fin_metrics = _safe_read_excel(p08, "financial_metrics")
    df08_raw_quality = _safe_read_excel(p08, "raw_table_quality")

    _ = _safe_read_excel(p19, "metric_value_details")  # optional; currently not mandatory for outputs
    df22_metric_queue = _safe_read_excel(p22, "metric_review_queue")
    df22_invalid = _safe_read_excel(p22, "invalid_value_examples")
    df22_hard = _safe_read_excel(p22, "hard_samples")

    df23_summary = _safe_read_excel(p23, "baseline_summary")
    df23_assets = _safe_read_excel(p23, "asset_quality_matrix")
    df24_summary = _safe_read_excel(p24, "report_type_summary")
    df24_scope = _safe_read_excel(p24, "eval_scope_recommendation")
    df26_regions = _safe_read_excel(p26, "region_quality_details")

    pdf_map = _build_pdf_map(df24_summary, df26_regions, df08_raw_quality)

    trusted_df = _build_trusted_metrics(df08_fin_metrics, df23_assets, df24_summary, df26_regions, pdf_map)
    manual_df = _build_manual_review(df22_metric_queue, df22_invalid, df26_regions)
    excluded_df = _build_excluded_or_failed(df23_assets, df24_summary, df08_summary, pdf_map)
    region_idx_df = _build_region_index(df26_regions)

    delivery_dir.mkdir(parents=True, exist_ok=True)
    p1 = _safe_write_excel(trusted_df, delivery_dir / "01_自动可信核心指标.xlsx")
    p2 = _safe_write_excel(manual_df, delivery_dir / "02_人工复核指标队列.xlsx")
    p3 = _safe_write_excel(excluded_df, delivery_dir / "03_非目标报告与失败说明.xlsx")
    p5 = _safe_write_excel(region_idx_df, delivery_dir / "05_表格区域截图索引.xlsx")

    summary_md = _build_summary_markdown(df24_scope, df23_summary, df23_assets, len(trusted_df), len(manual_df))
    p4 = _safe_write_text(summary_md, delivery_dir / "04_处理摘要.md")

    return {
        "delivery_dir": str(delivery_dir),
        "trusted_metric_rows": int(len(trusted_df)),
        "manual_review_rows": int(len(manual_df)),
        "excluded_or_failed_rows": int(len(excluded_df)),
        "table_region_index_rows": int(len(region_idx_df)),
        "summary_md_path": str(p4),
        "output_files": [str(p1), str(p2), str(p3), str(p4), str(p5)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build clean delivery package from existing reports/artifacts.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--delivery-dir", default=str(DEFAULT_DELIVERY_DIR))
    args = parser.parse_args()

    result = build_delivery_package(Path(args.output_dir), Path(args.delivery_dir))
    print(f"delivery_dir: {result['delivery_dir']}")
    print(f"trusted_metric_rows: {result['trusted_metric_rows']}")
    print(f"manual_review_rows: {result['manual_review_rows']}")
    print(f"excluded_or_failed_rows: {result['excluded_or_failed_rows']}")
    print(f"table_region_index_rows: {result['table_region_index_rows']}")
    print(f"summary_md_path: {result['summary_md_path']}")


if __name__ == "__main__":
    main()
