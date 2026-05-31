from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.delivery.sandbox_bundle_builder import build_sandbox_delivery_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build 320E sandbox delivery bundle from 320D2 mapping outputs.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = build_sandbox_delivery_bundle(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
    )
    s = result["summary"]
    print(f"row_text_delivery_excel: {result['excel_path']}")
    print(f"row_text_delivery_summary_json: {result.get('summary_json_path', '')}")
    print(f"row_text_delivery_report_md: {result['report_md_path']}")
    print(f"source_candidate_count: {s.get('source_candidate_count', 0)}")
    print(f"trusted_delivery_count: {s.get('trusted_delivery_count', 0)}")
    print(f"review_required_delivery_count: {s.get('review_required_delivery_count', 0)}")
    print(f"rejected_source_count: {s.get('rejected_source_count', 0)}")
    print(f"unique_metric_count: {s.get('unique_metric_count', 0)}")
    print(f"unique_year_count: {s.get('unique_year_count', 0)}")
    print(f"provenance_row_count: {s.get('provenance_row_count', 0)}")
    print(f"qa_pass_count: {s.get('qa_pass_count', 0)}")
    print(f"qa_warn_count: {s.get('qa_warn_count', 0)}")
    print(f"qa_fail_count: {s.get('qa_fail_count', 0)}")
    print(f"delivery_decision: {s.get('delivery_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
