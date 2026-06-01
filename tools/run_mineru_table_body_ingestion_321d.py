from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.mineru_body import MineruBodyIngestionConfig, run_mineru_table_body_ingestion


def _path_or_none(value: str) -> Path | None:
    text = (value or "").strip()
    return Path(text) if text else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321D MinerU table body ingestion.")
    parser.add_argument("--router-dir", required=True)
    parser.add_argument("--mineru-output-root", required=True)
    parser.add_argument("--pure-vlm-calibration-dir", required=False, default="")
    parser.add_argument("--ppstructure-benchmark-dir", required=False, default="")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-tables", required=False, type=int, default=20)
    args = parser.parse_args()

    result = run_mineru_table_body_ingestion(
        MineruBodyIngestionConfig(
            router_dir=Path(args.router_dir),
            mineru_output_root=Path(args.mineru_output_root),
            pure_vlm_calibration_dir=_path_or_none(args.pure_vlm_calibration_dir),
            ppstructure_benchmark_dir=_path_or_none(args.ppstructure_benchmark_dir),
            output_dir=Path(args.output_dir),
            max_tables=int(args.max_tables or 20),
        )
    )
    summary = result.get("summary", {})
    print(f"mineru_table_body_ingestion_excel: {result.get('excel_path', '')}")
    print(f"mineru_table_body_ingestion_summary_json: {result.get('summary_json_path', '')}")
    print(f"mineru_table_body_ingestion_report_md: {result.get('report_md_path', '')}")
    for key in [
        "selected_table_count",
        "attempted_table_count",
        "table_body_found_count",
        "table_body_missing_count",
        "parsed_table_count",
        "unified_table_count",
        "table_with_candidates_count",
        "table_with_trusted_count",
        "total_candidate_count",
        "trusted_total_count",
        "review_required_total_count",
        "rejected_total_count",
        "trusted_rate",
        "unit_unknown_count",
        "year_invalid_count",
        "unknown_metric_code_count",
        "conflict_count",
        "provenance_complete_rate",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "pure_vlm_calibrated_trusted_rate",
        "ppstructure_trusted_rate",
        "mineru_body_ingestion_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
