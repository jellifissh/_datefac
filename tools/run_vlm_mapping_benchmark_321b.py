from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.vlm.vlm_mapping_benchmark import run_vlm_mapping_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321B sandbox-only VLM mapping benchmark.")
    parser.add_argument("--vlm-output-root", required=True)
    parser.add_argument("--quality-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--ppstructure-benchmark-dir", required=False)
    args = parser.parse_args()

    result = run_vlm_mapping_benchmark(
        vlm_output_root=Path(args.vlm_output_root),
        quality_dir=Path(args.quality_dir),
        ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir) if args.ppstructure_benchmark_dir else None,
        output_dir=Path(args.output_dir),
    )
    summary = result.get("summary", {})
    print(f"vlm_mapping_benchmark_excel: {result.get('excel_path', '')}")
    print(f"vlm_mapping_benchmark_summary_json: {result.get('summary_json_path', '')}")
    print(f"vlm_mapping_benchmark_report_md: {result.get('report_md_path', '')}")
    for key in [
        "vlm_folder_count",
        "parsed_json_count",
        "table_ready_count",
        "mapped_table_count",
        "table_with_candidates_count",
        "table_with_trusted_count",
        "total_candidate_count",
        "trusted_total_count",
        "review_required_total_count",
        "rejected_total_count",
        "trusted_rate",
        "unit_unknown_count",
        "year_inferred_count",
        "conflict_count",
        "provenance_complete_rate",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "ppstructure_comparison_available",
        "vlm_benchmark_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
