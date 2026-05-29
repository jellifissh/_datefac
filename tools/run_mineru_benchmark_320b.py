from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.mineru_benchmark_runner import RunnerConfig, run_mineru_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MinerU TableAsset benchmark for multiple report output folders.")
    parser.add_argument("--mineru-output-root", required=True, help="Root directory where each subdirectory is one MinerU report output.")
    parser.add_argument("--output-dir", required=True, help="Benchmark output directory.")
    parser.add_argument("--min-report-count", type=int, default=5, help="Minimum parsed report count before warning.")
    parser.add_argument("--exclude-name", action="append", default=[], help="Report folder name to exclude. Can be repeated.")
    parser.add_argument("--include-name-regex", default="", help="Optional regex filter for included report folder names.")
    args = parser.parse_args()

    cfg = RunnerConfig(
        mineru_output_root=Path(args.mineru_output_root),
        output_dir=Path(args.output_dir),
        min_report_count=int(args.min_report_count),
        exclude_names=set(args.exclude_name or []),
        include_name_regex=args.include_name_regex or None,
    )
    res = run_mineru_benchmark(cfg)
    summary = res["summary"]

    print(f"mineru_benchmark_excel: {res['excel_path']}")
    print(f"mineru_benchmark_summary_json: {res['summary_json_path']}")
    print(f"mineru_benchmark_report_md: {res['report_md_path']}")
    print(f"report_count: {summary.get('report_count', 0)}")
    print(f"parsed_report_count: {summary.get('parsed_report_count', 0)}")
    print(f"failed_report_count: {summary.get('failed_report_count', 0)}")
    print(f"total_table_asset_count: {summary.get('total_table_asset_count', 0)}")
    print(f"image_path_coverage_rate: {summary.get('image_path_coverage_rate', 0)}")
    print(f"bbox_coverage_rate: {summary.get('bbox_coverage_rate', 0)}")
    print(f"core_table_detected_rate: {summary.get('core_table_detected_rate', 0)}")
    print(f"parser_decision: {summary.get('parser_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

