from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.table_bakeoff import DoclingAuditConfig, run_docling_output_audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321E1 Docling output audit.")
    parser.add_argument("--input-image-dir", required=True)
    parser.add_argument("--docling-output-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_docling_output_audit(
        DoclingAuditConfig(
            input_image_dir=Path(args.input_image_dir),
            docling_output_dir=Path(args.docling_output_dir),
            output_dir=Path(args.output_dir),
        )
    )
    summary = result.get("summary", {})
    print(f"docling_output_audit_excel: {result.get('excel_path', '')}")
    print(f"docling_output_audit_summary_json: {result.get('summary_json_path', '')}")
    print(f"docling_output_audit_report_md: {result.get('report_md_path', '')}")
    for key in [
        "input_image_count",
        "discovered_docling_folder_count",
        "discovered_json_file_count",
        "matched_image_count",
        "json_parse_success_count",
        "total_table_count",
        "image_with_table_count",
        "image_with_real_cell_grid_count",
        "total_cell_count",
        "overall_empty_cell_rate",
        "numeric_parse_success_rate",
        "valid_year_header_count",
        "invalid_year_header_count",
        "comma_space_number_count",
        "possible_missing_value_count",
        "good_candidate_count",
        "partial_review_needed_count",
        "poor_or_text_only_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "docling_audit_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
