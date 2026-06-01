from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.vlm.vlm_mapping_calibration import run_vlm_mapping_calibration


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321B2 pure-VLM mapping calibration and diagnostics.")
    parser.add_argument("--vlm-output-root", required=True)
    parser.add_argument("--quality-dir", required=True)
    parser.add_argument("--previous-mapping-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--ppstructure-benchmark-dir", required=False)
    args = parser.parse_args()

    result = run_vlm_mapping_calibration(
        vlm_output_root=Path(args.vlm_output_root),
        quality_dir=Path(args.quality_dir),
        previous_mapping_dir=Path(args.previous_mapping_dir),
        ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir) if args.ppstructure_benchmark_dir else None,
        output_dir=Path(args.output_dir),
    )
    summary = result.get("summary", {})
    print(f"vlm_mapping_calibration_excel: {result.get('excel_path', '')}")
    print(f"vlm_mapping_calibration_summary_json: {result.get('summary_json_path', '')}")
    print(f"vlm_mapping_calibration_report_md: {result.get('report_md_path', '')}")
    for key in [
        "calibrated_total_candidate_count",
        "calibrated_trusted_total_count",
        "calibrated_review_required_total_count",
        "calibrated_trusted_rate",
        "table_with_trusted_count",
        "unknown_metric_code_count",
        "unreadable_label_count",
        "unit_unknown_count",
        "invalid_year_count",
        "table_not_ready_candidate_count",
        "table_level_review_count",
        "unreadable_label_row_review_count",
        "same_value_duplicate_collapsed_count",
        "true_value_conflict_count",
        "alias_added_count",
        "unit_propagated_count",
        "year_normalized_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "calibration_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
