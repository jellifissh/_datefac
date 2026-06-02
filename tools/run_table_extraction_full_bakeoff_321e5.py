from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.table_bakeoff.full_table_extraction_bakeoff import FullBakeoffConfig, run_full_table_extraction_bakeoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321E5 full table extraction bakeoff from existing outputs only.")
    parser.add_argument("--structtable-mapping-dir", required=True)
    parser.add_argument("--structtable-audit-dir", required=True)
    parser.add_argument("--docling-mapping-dir", required=True)
    parser.add_argument("--docling-audit-dir", required=True)
    parser.add_argument("--mineru-body-dir", required=True)
    parser.add_argument("--pure-vlm-calibration-dir", required=True)
    parser.add_argument("--ppstructure-benchmark-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_full_table_extraction_bakeoff(
        FullBakeoffConfig(
            structtable_mapping_dir=Path(args.structtable_mapping_dir),
            structtable_audit_dir=Path(args.structtable_audit_dir),
            docling_mapping_dir=Path(args.docling_mapping_dir),
            docling_audit_dir=Path(args.docling_audit_dir),
            mineru_body_dir=Path(args.mineru_body_dir),
            pure_vlm_calibration_dir=Path(args.pure_vlm_calibration_dir),
            ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir),
            output_dir=Path(args.output_dir),
        )
    )
    summary = result.get("summary", {})
    print(f"table_extraction_full_bakeoff_excel: {result.get('excel_path', '')}")
    print(f"table_extraction_full_bakeoff_summary_json: {result.get('summary_json_path', '')}")
    print(f"table_extraction_full_bakeoff_report_md: {result.get('report_md_path', '')}")
    print(f"table_extraction_router_plan_json: {result.get('router_json_path', '')}")
    for key in [
        "route_count",
        "top_overall_route",
        "pdf_table_body_default_route",
        "image_table_default_route",
        "qa_pass_count",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
