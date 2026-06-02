from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.pipeline.router_driven_sandbox_pipeline_322b import (
    RouterDrivenSandboxPipeline322BConfig,
    run_router_driven_sandbox_pipeline_322b,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322B router-driven larger batch review-burden diagnosis.")
    parser.add_argument("--router-integration-dir", required=True)
    parser.add_argument("--router-dir", required=True)
    parser.add_argument("--mineru-output-root", required=True)
    parser.add_argument("--existing-mineru-body-dir", required=True)
    parser.add_argument("--structtable-mapping-dir", required=True)
    parser.add_argument("--docling-mapping-dir", required=True)
    parser.add_argument("--pure-vlm-calibration-dir", required=True)
    parser.add_argument("--ppstructure-benchmark-dir", required=True)
    parser.add_argument("--prior-322a-output-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-new-mineru-tables", type=int, default=45)
    args = parser.parse_args()

    result = run_router_driven_sandbox_pipeline_322b(
        RouterDrivenSandboxPipeline322BConfig(
            router_integration_dir=Path(args.router_integration_dir),
            router_dir=Path(args.router_dir),
            mineru_output_root=Path(args.mineru_output_root),
            existing_mineru_body_dir=Path(args.existing_mineru_body_dir),
            structtable_mapping_dir=Path(args.structtable_mapping_dir),
            docling_mapping_dir=Path(args.docling_mapping_dir),
            pure_vlm_calibration_dir=Path(args.pure_vlm_calibration_dir),
            ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir),
            prior_322a_output_dir=Path(args.prior_322a_output_dir),
            output_dir=Path(args.output_dir),
            max_new_mineru_tables=args.max_new_mineru_tables,
        )
    )
    summary = result.get("summary", {})
    print(f"router_driven_sandbox_pipeline_322b_excel: {result.get('excel_path', '')}")
    print(f"router_driven_sandbox_pipeline_322b_summary_json: {result.get('summary_json_path', '')}")
    print(f"router_driven_sandbox_pipeline_322b_report_md: {result.get('report_md_path', '')}")
    print(f"router_selected_delivery_preview_322b_jsonl: {result.get('preview_jsonl_path', '')}")
    for key in [
        "newly_processed_mineru_table_count",
        "selected_output_table_count_before_322b",
        "selected_output_table_count_after_322b",
        "no_available_output_count_after_322b",
        "selected_candidate_total_count",
        "selected_trusted_total_count",
        "selected_review_required_total_count",
        "selected_core_trusted_rate",
        "unknown_metric_unique_label_count",
        "alias_candidate_count",
        "semantic_adjudicator_worklist_count",
        "manual_review_worklist_count",
        "qa_fail_count",
        "router_driven_sandbox_pipeline_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
