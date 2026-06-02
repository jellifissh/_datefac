from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.table_bakeoff.structtable_output_audit import StructTableAuditConfig, run_structtable_output_audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321E3 StructEqTable output audit.")
    parser.add_argument("--input-image-dir", required=True)
    parser.add_argument("--structtable-output-dir", required=True)
    parser.add_argument("--docling-audit-dir", required=False, default="")
    parser.add_argument("--docling-mapping-dir", required=False, default="")
    parser.add_argument("--mineru-body-dir", required=False, default="")
    parser.add_argument("--pure-vlm-calibration-dir", required=False, default="")
    parser.add_argument("--ppstructure-benchmark-dir", required=False, default="")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_structtable_output_audit(
        StructTableAuditConfig(
            input_image_dir=Path(args.input_image_dir),
            structtable_output_dir=Path(args.structtable_output_dir),
            docling_audit_dir=Path(args.docling_audit_dir) if args.docling_audit_dir else None,
            docling_mapping_dir=Path(args.docling_mapping_dir) if args.docling_mapping_dir else None,
            mineru_body_dir=Path(args.mineru_body_dir) if args.mineru_body_dir else None,
            pure_vlm_calibration_dir=Path(args.pure_vlm_calibration_dir) if args.pure_vlm_calibration_dir else None,
            ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir) if args.ppstructure_benchmark_dir else None,
            output_dir=Path(args.output_dir),
        )
    )
    summary = result.get("summary", {})
    print(f"structtable_output_audit_excel: {result.get('excel_path', '')}")
    print(f"structtable_output_audit_summary_json: {result.get('summary_json_path', '')}")
    print(f"structtable_output_audit_report_md: {result.get('report_md_path', '')}")
    for key in [
        "input_image_count",
        "discovered_structtable_folder_count",
        "matched_image_count",
        "raw_response_exists_count",
        "markdown_exists_count",
        "xlsx_exists_count",
        "csv_exists_count",
        "parse_success_count",
        "parse_failed_count",
        "table_count",
        "image_with_real_table_grid_count",
        "numeric_parse_success_rate",
        "valid_year_header_count",
        "invalid_year_header_count",
        "chinese_label_row_count",
        "label_corruption_count",
        "suspicious_short_label_count",
        "possible_missing_value_count",
        "timeout_warning_count",
        "good_candidate_count",
        "partial_review_needed_count",
        "poor_or_text_only_count",
        "output_missing_or_invalid_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "structtable_audit_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
