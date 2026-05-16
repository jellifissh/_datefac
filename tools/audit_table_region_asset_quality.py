import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
DEFAULT_REPORT_PATH = Path(r"D:\_datefac\output\26_table_region_asset_quality_report.xlsx")
ASSET_SUFFIX = "_" + "\u8d44\u4ea7\u5305"
FOCUS_STEMS = {
    "H3_AP202605091822098939_1",
    "H3_AP202605121822218343_1",
    "H3_AP202605121822223662_1",
    "H3_AP202605141822317484_1",
    "H3_AP202605141822318031_1",
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


def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _safe_sheet_name(name: str, used: set) -> str:
    invalid = "\\/*?:[]"
    s = "".join("_" if c in invalid else c for c in (_norm(name) or "Sheet"))[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


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
            (df if isinstance(df, pd.DataFrame) else pd.DataFrame()).to_excel(writer, sheet_name=safe, index=False)
    return str(final_path)


def _severity_score(row: pd.Series) -> int:
    score = 0
    bbox_status = _norm(row.get("bbox_status"))
    quality_level = _norm(row.get("quality_level")).upper()
    quality_flags = _norm(row.get("quality_flags"))
    needs_review = _to_bool(row.get("needs_manual_review"))
    linked_invalid = _to_int(row.get("linked_invalid_metric_count"), 0)
    linked_suspicious = _to_int(row.get("linked_suspicious_metric_count"), 0)

    if bbox_status != "matched":
        score += 50
    if needs_review:
        score += 40
    if quality_level == "BAD":
        score += 25
    if "possible_glued_table" in quality_flags:
        score += 20
    if "single_column" in quality_flags:
        score += 15
    score += linked_invalid * 10
    score += linked_suspicious * 3
    return score


def _find_asset_dirs(output_dir: Path) -> List[Path]:
    if not output_dir.exists():
        return []
    return sorted([p for p in output_dir.iterdir() if p.is_dir() and p.name.endswith(ASSET_SUFFIX)], key=lambda x: x.name)


def _scan_02b_indexes(output_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    all_rows: List[Dict[str, object]] = []
    asset_summary_rows: List[Dict[str, object]] = []

    for asset_dir in _find_asset_dirs(output_dir):
        idx_path = asset_dir / "02B_table_region_assets" / "table_region_index.xlsx"
        if not idx_path.exists():
            continue
        try:
            df = pd.read_excel(idx_path, engine="openpyxl").fillna("")
        except Exception:
            continue
        if df.empty:
            continue

        if "asset_package" not in df.columns:
            df["asset_package"] = asset_dir.name
        if "source_pdf" not in df.columns:
            df["source_pdf"] = ""
        if "needs_manual_review" not in df.columns:
            df["needs_manual_review"] = False
        if "review_reason" not in df.columns:
            df["review_reason"] = ""

        # computed fields
        df["severity_score"] = df.apply(_severity_score, axis=1)
        df["is_focus_asset"] = df["asset_package"].astype(str).str.replace(ASSET_SUFFIX, "", regex=False).isin(FOCUS_STEMS)

        for _, r in df.iterrows():
            all_rows.append(r.to_dict())

        total_regions = len(df)
        crop_generated_count = int(df.get("crop_png_path", pd.Series(dtype=str)).astype(str).str.len().gt(0).sum())
        matched_bbox_count = int((df.get("bbox_status", "").astype(str) == "matched").sum())
        unmatched_bbox_count = int((df.get("bbox_status", "").astype(str) != "matched").sum())
        bad_quality_count = int((df.get("quality_level", "").astype(str).str.upper() == "BAD").sum())
        glued_flag_count = int(df.get("quality_flags", pd.Series(dtype=str)).astype(str).str.contains("possible_glued_table", na=False).sum())
        single_column_count = int(df.get("quality_flags", pd.Series(dtype=str)).astype(str).str.contains("single_column", na=False).sum())
        linked_invalid_metric_count = int(pd.to_numeric(df.get("linked_invalid_metric_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
        needs_manual_review_count = int(df.get("needs_manual_review", pd.Series(dtype=bool)).apply(_to_bool).sum())

        asset_summary_rows.append(
            {
                "asset_package": asset_dir.name,
                "total_regions": total_regions,
                "crop_generated_count": crop_generated_count,
                "matched_bbox_count": matched_bbox_count,
                "unmatched_bbox_count": unmatched_bbox_count,
                "bad_quality_count": bad_quality_count,
                "glued_flag_count": glued_flag_count,
                "single_column_count": single_column_count,
                "linked_invalid_metric_count": linked_invalid_metric_count,
                "needs_manual_review_count": needs_manual_review_count,
            }
        )

    all_df = pd.DataFrame(all_rows).fillna("")
    asset_summary_df = pd.DataFrame(asset_summary_rows).fillna("")
    return all_df, asset_summary_df


def _build_review_priority_crops(all_df: pd.DataFrame) -> pd.DataFrame:
    if all_df.empty:
        return pd.DataFrame()
    priority = all_df.copy()
    priority = priority.sort_values(
        ["severity_score", "needs_manual_review", "linked_invalid_metric_count"],
        ascending=[False, False, False],
    )
    priority["rank_in_asset"] = priority.groupby("asset_package").cumcount() + 1
    # keep full queue for audit sheet; focus top rows can be filtered in reporting
    return priority


def build_quality_report(output_dir: Path, report_path: Path) -> Tuple[str, Dict[str, int], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_df, asset_summary_df = _scan_02b_indexes(output_dir)
    review_priority_df = _build_review_priority_crops(all_df)
    unmatched_df = all_df[all_df.get("bbox_status", "").astype(str) != "matched"].copy() if not all_df.empty else pd.DataFrame()

    # details fields normalization
    details_cols = [
        "asset_package",
        "source_pdf",
        "page_number",
        "table_index",
        "sheet_name",
        "bbox_status",
        "crop_png_path",
        "page_png_path",
        "quality_score",
        "quality_level",
        "quality_flags",
        "business_table_type",
        "business_relevance_score",
        "linked_metric_count",
        "linked_valid_metric_count",
        "linked_invalid_metric_count",
        "linked_suspicious_metric_count",
        "linked_metrics",
        "linked_issue_flags",
        "needs_manual_review",
        "review_reason",
        "severity_score",
    ]
    region_details_df = all_df.copy()
    for c in details_cols:
        if c not in region_details_df.columns:
            region_details_df[c] = ""
    region_details_df = region_details_df[details_cols]

    report_out = _save_excel_robust(
        {
            "asset_summary": asset_summary_df,
            "region_quality_details": region_details_df,
            "review_priority_crops": review_priority_df,
            "unmatched_bbox_cases": unmatched_df,
        },
        report_path,
    )

    stats = {
        "asset_count": int(len(asset_summary_df)),
        "total_regions": int(len(region_details_df)),
        "crop_generated_count": int(region_details_df.get("crop_png_path", pd.Series(dtype=str)).astype(str).str.len().gt(0).sum()) if not region_details_df.empty else 0,
        "matched_bbox_count": int((region_details_df.get("bbox_status", "").astype(str) == "matched").sum()) if not region_details_df.empty else 0,
        "unmatched_bbox_count": int((region_details_df.get("bbox_status", "").astype(str) != "matched").sum()) if not region_details_df.empty else 0,
        "needs_manual_review_count": int(region_details_df.get("needs_manual_review", pd.Series(dtype=bool)).apply(_to_bool).sum()) if not region_details_df.empty else 0,
    }
    return report_out, stats, asset_summary_df, region_details_df, review_priority_df, unmatched_df


def _print_focus_audit(asset_summary_df: pd.DataFrame, review_priority_df: pd.DataFrame) -> None:
    print("\n[Focus Asset Audit]")
    for stem in sorted(FOCUS_STEMS):
        asset_name = stem + ASSET_SUFFIX
        sub = asset_summary_df[asset_summary_df["asset_package"].astype(str) == asset_name]
        if sub.empty:
            print(f"{stem}: no 02B index found")
            continue
        row = sub.iloc[0]
        print(
            f"{stem}: crop={_to_int(row.get('crop_generated_count'))}, unmatched={_to_int(row.get('unmatched_bbox_count'))}, "
            f"needs_manual_review={_to_int(row.get('needs_manual_review_count'))}"
        )
        rsub = review_priority_df[review_priority_df["asset_package"].astype(str) == asset_name].head(5)
        if rsub.empty:
            print("  top5: none")
            continue
        for i, (_, r) in enumerate(rsub.iterrows(), start=1):
            print(
                f"  top{i}: { _norm(r.get('crop_png_path')) or '[no_crop_path]' } | "
                f"reason={_norm(r.get('review_reason'))}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only quality audit for 02B table region assets.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output root")
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH), help="26 report path")
    args = parser.parse_args()

    report_out, stats, asset_summary_df, region_details_df, review_priority_df, _ = build_quality_report(
        output_dir=Path(args.output_dir),
        report_path=Path(args.report_path),
    )

    print(f"report_path: {report_out}")
    print(f"asset_count: {stats['asset_count']}")
    print(f"total_regions: {stats['total_regions']}")
    print(f"crop_generated_count: {stats['crop_generated_count']}")
    print(f"matched_bbox_count: {stats['matched_bbox_count']}")
    print(f"unmatched_bbox_count: {stats['unmatched_bbox_count']}")
    print(f"needs_manual_review_count: {stats['needs_manual_review_count']}")

    _print_focus_audit(asset_summary_df, review_priority_df)


if __name__ == "__main__":
    main()

