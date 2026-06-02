from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.table_bakeoff.structtable_metric_probe import StructTableMetricProbeConfig, run_structtable_metric_probe


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321E4 StructEqTable unified mapping probe.")
    parser.add_argument("--structtable-audit-dir", required=True)
    parser.add_argument("--structtable-output-dir", required=True)
    parser.add_argument("--input-image-dir", required=True)
    parser.add_argument("--docling-mapping-dir", required=False, default="")
    parser.add_argument("--docling-audit-dir", required=False, default="")
    parser.add_argument("--mineru-body-dir", required=False, default="")
    parser.add_argument("--pure-vlm-calibration-dir", required=False, default="")
    parser.add_argument("--ppstructure-benchmark-dir", required=False, default="")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_structtable_metric_probe(
        StructTableMetricProbeConfig(
            structtable_audit_dir=Path(args.structtable_audit_dir),
            structtable_output_dir=Path(args.structtable_output_dir),
            input_image_dir=Path(args.input_image_dir),
            docling_mapping_dir=Path(args.docling_mapping_dir) if args.docling_mapping_dir else None,
            docling_audit_dir=Path(args.docling_audit_dir) if args.docling_audit_dir else None,
            mineru_body_dir=Path(args.mineru_body_dir) if args.mineru_body_dir else None,
            pure_vlm_calibration_dir=Path(args.pure_vlm_calibration_dir) if args.pure_vlm_calibration_dir else None,
            ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir) if args.ppstructure_benchmark_dir else None,
            output_dir=Path(args.output_dir),
        )
    )
    summary = result.get("summary", {})
    print(f"structtable_unified_mapping_excel: {result.get('excel_path', '')}")
    print(f"structtable_unified_mapping_summary_json: {result.get('summary_json_path', '')}")
    print(f"structtable_unified_mapping_report_md: {result.get('report_md_path', '')}")
    for key in [
        "input_image_count",
        "structtable_table_count",
        "unified_table_count",
        "table_with_candidates_count",
        "table_with_trusted_count",
        "total_candidate_count",
        "trusted_total_count",
        "review_required_total_count",
        "rejected_total_count",
        "trusted_rate",
        "unit_unknown_count",
        "invalid_year_count",
        "unknown_metric_code_count",
        "value_parse_failed_count",
        "possible_missing_value_count",
        "extraction_risk_candidate_count",
        "label_issue_candidate_count",
        "conflict_count",
        "provenance_complete_rate",
        "mineru_body_trusted_rate",
        "pure_vlm_calibrated_trusted_rate",
        "docling_mapping_trusted_rate",
        "ppstructure_trusted_rate",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "structtable_mapping_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
