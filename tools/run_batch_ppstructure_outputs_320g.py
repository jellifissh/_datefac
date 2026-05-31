from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.batch_row_text_delivery_benchmark import run_batch_row_text_delivery_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 320G batch PPStructure outputs to multi-report delivery benchmark.")
    parser.add_argument("--ppstructure-batch-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_batch_row_text_delivery_benchmark(
        ppstructure_batch_dir=Path(args.ppstructure_batch_dir),
        output_dir=Path(args.output_dir),
    )
    s = result["summary"]
    print(f"batch_row_text_delivery_excel: {result['excel_path']}")
    print(f"batch_row_text_delivery_summary_json: {result['summary_json_path']}")
    print(f"batch_row_text_delivery_report_md: {result['report_md_path']}")
    print(f"batch_table_count: {s.get('batch_table_count', 0)}")
    print(f"batch_ok_count: {s.get('batch_ok_count', 0)}")
    print(f"parsed_table_count: {s.get('parsed_table_count', 0)}")
    print(f"table_with_row_text_count: {s.get('table_with_row_text_count', 0)}")
    print(f"table_with_candidates_count: {s.get('table_with_candidates_count', 0)}")
    print(f"table_with_trusted_count: {s.get('table_with_trusted_count', 0)}")
    print(f"report_count: {s.get('report_count', 0)}")
    print(f"trusted_total_count: {s.get('trusted_total_count', 0)}")
    print(f"review_required_total_count: {s.get('review_required_total_count', 0)}")
    print(f"rejected_total_count: {s.get('rejected_total_count', 0)}")
    print(f"trusted_rate: {s.get('trusted_rate', 0.0)}")
    print(f"provenance_complete_rate: {s.get('provenance_complete_rate', 0.0)}")
    print(f"qa_pass_count: {s.get('qa_pass_count', 0)}")
    print(f"qa_warn_count: {s.get('qa_warn_count', 0)}")
    print(f"qa_fail_count: {s.get('qa_fail_count', 0)}")
    print(f"batch_delivery_decision: {s.get('batch_delivery_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
