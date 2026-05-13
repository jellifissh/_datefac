from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


def find_latest_matching(directory: Path, pattern: str) -> Optional[Path]:
    candidates = [p for p in directory.glob(pattern) if p.is_file()]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def df_to_simple_markdown(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_empty_"
    cols = [str(c) for c in df.columns.tolist()]
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        vals = [str(v).replace("\n", " ").strip() for v in row.tolist()]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def summarize_quality_flags(table_blocks_df: pd.DataFrame, limit: int = 8) -> str:
    if "quality_flags" not in table_blocks_df.columns:
        return "(missing quality_flags column)"
    flags = (
        table_blocks_df["quality_flags"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    values = sorted({x for x in flags.tolist() if x})
    if not values:
        return "(none)"
    return ", ".join(values[:limit])


def detect_obvious_anomaly(summary_df: pd.DataFrame, table_blocks_df: pd.DataFrame) -> bool:
    if summary_df.empty:
        return True
    has_warning = False
    if "warning_count" in summary_df.columns:
        has_warning = bool((summary_df["warning_count"].fillna(0) > 0).any())
    low_quality = False
    if "avg_quality_score" in summary_df.columns:
        low_quality = bool((summary_df["avg_quality_score"].fillna(1.0) < 0.45).any())
    no_tables = False
    if "table_count" in summary_df.columns:
        no_tables = bool((summary_df["table_count"].fillna(0).sum() <= 0))
    mostly_bad = False
    if "quality_level" in table_blocks_df.columns and not table_blocks_df.empty:
        levels = table_blocks_df["quality_level"].fillna("").astype(str)
        bad_count = int((levels == "BAD").sum())
        mostly_bad = bad_count >= max(1, int(len(levels) * 0.5))
    return has_warning or low_quality or no_tables or mostly_bad


def export_10_report(asset_dir: Path, debug_asset_dir: Path) -> Optional[Path]:
    report_path = find_latest_matching(asset_dir, "10_extractor_compare_report*.xlsx")
    if report_path is None:
        return None

    summary_df = pd.read_excel(report_path, sheet_name="summary")
    table_blocks_df = pd.read_excel(report_path, sheet_name="table_blocks")

    write_csv(summary_df, debug_asset_dir / "10_summary.csv")
    write_csv(table_blocks_df.head(50), debug_asset_dir / "10_table_blocks_head.csv")

    total_tables = int(summary_df["table_count"].sum()) if "table_count" in summary_df.columns else 0
    total_warnings = int(summary_df["warning_count"].sum()) if "warning_count" in summary_df.columns else 0
    flags_sample = summarize_quality_flags(table_blocks_df)
    anomaly = detect_obvious_anomaly(summary_df, table_blocks_df)

    lines: List[str] = []
    lines.append(f"# {asset_dir.name} - 10_extractor_compare_report 摘要")
    lines.append("")
    lines.append(f"- 源文件: `{report_path.name}`")
    lines.append(f"- backend 数量: `{len(summary_df)}`")
    lines.append(f"- 总 table_count: `{total_tables}`")
    lines.append(f"- 总 warning_count: `{total_warnings}`")
    lines.append(f"- quality_flags 样例: `{flags_sample}`")
    lines.append(f"- 是否发现明显异常: `{'是' if anomaly else '否'}`")
    lines.append("")
    lines.append("## backend 对比")
    lines.append("")
    if summary_df.empty:
        lines.append("_summary 为空_")
    else:
        cols = [c for c in ["backend", "table_count", "avg_quality_score", "good_table_count", "warning_count"] if c in summary_df.columns]
        lines.append(df_to_simple_markdown(summary_df[cols]))
    md_path = debug_asset_dir / "10_extractor_summary.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def export_07_report(asset_dir: Path, debug_asset_dir: Path) -> bool:
    report_path = find_latest_matching(asset_dir, "07_table_segment_map*.xlsx")
    if report_path is None:
        return False

    xls = pd.ExcelFile(report_path)
    exported = False
    if "segment_validation" in xls.sheet_names:
        df = pd.read_excel(report_path, sheet_name="segment_validation")
        write_csv(df, debug_asset_dir / "07_segment_validation.csv")
        exported = True
    if "segment_map" in xls.sheet_names:
        df = pd.read_excel(report_path, sheet_name="segment_map")
        write_csv(df.head(100), debug_asset_dir / "07_segment_map_head.csv")
        exported = True
    return exported


def export_09_report(output_dir: Path, debug_root: Path) -> Optional[Path]:
    status_path = find_latest_matching(output_dir, "09_batch_run_status*.xlsx")
    if status_path is None:
        return None

    df = pd.read_excel(status_path)
    write_csv(df, debug_root / "09_batch_run_status.csv")

    total = len(df)
    failed = int((df.get("status", pd.Series(dtype=str)).astype(str) == "FAILED").sum()) if total > 0 else 0
    success = int((df.get("status", pd.Series(dtype=str)).astype(str) == "SUCCESS").sum()) if total > 0 else 0
    lines = [
        "# 09_batch_run_status 摘要",
        "",
        f"- 源文件: `{status_path.name}`",
        f"- 文档总数: `{total}`",
        f"- SUCCESS 数: `{success}`",
        f"- FAILED 数: `{failed}`",
        "",
    ]
    cols = [c for c in ["doc_name", "status", "table_count", "vision_success", "markdown_available", "error_message"] if c in df.columns]
    if cols:
        lines.append("## 关键字段预览")
        lines.append("")
        lines.append(df_to_simple_markdown(df[cols].head(30)))
    md_path = debug_root / "09_batch_run_status.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def run(output_dir: Path, debug_root: Path) -> Dict[str, int]:
    debug_root.mkdir(parents=True, exist_ok=True)
    counters = {"asset_scanned": 0, "asset_exported_10": 0, "asset_exported_07": 0}

    asset_dirs = sorted([p for p in output_dir.glob("*_资产包") if p.is_dir()])
    for asset_dir in asset_dirs:
        counters["asset_scanned"] += 1
        debug_asset_dir = debug_root / asset_dir.name

        if export_10_report(asset_dir, debug_asset_dir):
            counters["asset_exported_10"] += 1
        if export_07_report(asset_dir, debug_asset_dir):
            counters["asset_exported_07"] += 1

    export_09_report(output_dir, debug_root)
    return counters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export lightweight debug summaries from output Excel artifacts.")
    parser.add_argument("--output-dir", default=r"D:\_datefac\output", help="Output directory containing *_资产包")
    parser.add_argument("--debug-dir", default=r"D:\_datefac\debug_reports", help="Target directory for CSV/MD summaries")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    debug_dir = Path(args.debug_dir).expanduser().resolve()

    if not output_dir.exists():
        print(f"[export_debug_summary] output dir not found: {output_dir}")
        return 1

    stats = run(output_dir, debug_dir)
    print(f"[export_debug_summary] debug dir: {debug_dir}")
    print(f"[export_debug_summary] assets scanned: {stats['asset_scanned']}")
    print(f"[export_debug_summary] assets exported (10): {stats['asset_exported_10']}")
    print(f"[export_debug_summary] assets exported (07): {stats['asset_exported_07']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
