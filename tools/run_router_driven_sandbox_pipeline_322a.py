from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.pipeline.router_driven_sandbox_pipeline import (
    RouterDrivenSandboxPipelineConfig,
    run_router_driven_sandbox_pipeline_322a,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322A router-driven sandbox pipeline.")
    parser.add_argument("--router-integration-dir", required=True)
    parser.add_argument("--router-dir", required=True)
    parser.add_argument("--mineru-output-root", required=True)
    parser.add_argument("--existing-mineru-body-dir", required=True)
    parser.add_argument("--structtable-mapping-dir", required=True)
    parser.add_argument("--docling-mapping-dir", required=True)
    parser.add_argument("--pure-vlm-calibration-dir", required=True)
    parser.add_argument("--ppstructure-benchmark-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-new-mineru-tables", type=int, default=50)
    args = parser.parse_args()

    result = run_router_driven_sandbox_pipeline_322a(
        RouterDrivenSandboxPipelineConfig(
            router_integration_dir=Path(args.router_integration_dir),
            router_dir=Path(args.router_dir),
            mineru_output_root=Path(args.mineru_output_root),
            existing_mineru_body_dir=Path(args.existing_mineru_body_dir),
            structtable_mapping_dir=Path(args.structtable_mapping_dir),
            docling_mapping_dir=Path(args.docling_mapping_dir),
            pure_vlm_calibration_dir=Path(args.pure_vlm_calibration_dir),
            ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir),
            output_dir=Path(args.output_dir),
            max_new_mineru_tables=args.max_new_mineru_tables,
        )
    )
    summary = result.get("summary", {})
    print(f"router_driven_sandbox_pipeline_322a_excel: {result.get('excel_path', '')}")
    print(f"router_driven_sandbox_pipeline_322a_summary_json: {result.get('summary_json_path', '')}")
    print(f"router_driven_sandbox_pipeline_322a_report_md: {result.get('report_md_path', '')}")
    print(f"router_selected_delivery_preview_322a_jsonl: {result.get('preview_jsonl_path', '')}")
    for key in [
        "router_route_total_count",
        "eligible_mineru_missing_count",
        "selected_new_mineru_table_count",
        "attempted_new_mineru_table_count",
        "newly_processed_mineru_table_count",
        "newly_failed_mineru_table_count",
        "selected_output_table_count_before_322a",
        "selected_output_table_count_after_322a",
        "no_available_output_count_before_322a",
        "no_available_output_count_after_322a",
        "selected_candidate_total_count",
        "selected_trusted_total_count",
        "selected_review_required_total_count",
        "selected_core_trusted_rate",
        "selected_all_trusted_rate",
        "semantic_adjudicator_worklist_count",
        "manual_review_worklist_count",
        "remaining_missing_output_worklist_count",
        "mineru_coverage_before_322a",
        "mineru_coverage_after_322a",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "router_driven_sandbox_pipeline_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
