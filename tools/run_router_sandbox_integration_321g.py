from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.router.router_sandbox_integration import (
    RouterSandboxIntegrationConfig,
    run_router_sandbox_integration_321g,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321G router sandbox integration dry-run.")
    parser.add_argument("--router-dir", required=True)
    parser.add_argument("--bakeoff-dir", required=True)
    parser.add_argument("--router-revision-dir", required=True)
    parser.add_argument("--mineru-body-dir", required=True)
    parser.add_argument("--structtable-mapping-dir", required=True)
    parser.add_argument("--docling-mapping-dir", required=True)
    parser.add_argument("--pure-vlm-calibration-dir", required=True)
    parser.add_argument("--ppstructure-benchmark-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_router_sandbox_integration_321g(
        RouterSandboxIntegrationConfig(
            router_dir=Path(args.router_dir),
            bakeoff_dir=Path(args.bakeoff_dir),
            router_revision_dir=Path(args.router_revision_dir),
            mineru_body_dir=Path(args.mineru_body_dir),
            structtable_mapping_dir=Path(args.structtable_mapping_dir),
            docling_mapping_dir=Path(args.docling_mapping_dir),
            pure_vlm_calibration_dir=Path(args.pure_vlm_calibration_dir),
            ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir),
            output_dir=Path(args.output_dir),
        )
    )
    summary = result.get("summary", {})
    print(f"router_sandbox_integration_321g_excel: {result.get('excel_path', '')}")
    print(f"router_sandbox_integration_321g_summary_json: {result.get('summary_json_path', '')}")
    print(f"router_sandbox_integration_321g_report_md: {result.get('report_md_path', '')}")
    print(f"router_sandbox_action_plan_321g_json: {result.get('action_plan_json_path', '')}")
    for key in [
        "route_total_count",
        "selected_output_table_count",
        "no_available_output_count",
        "mineru_routed_count",
        "mineru_output_available_count",
        "structtable_routed_count",
        "structtable_output_available_count",
        "docling_backup_routed_count",
        "docling_output_available_count",
        "pure_vlm_adjudicator_count",
        "pure_vlm_output_available_count",
        "manual_review_count",
        "semantic_adjudicator_worklist_count",
        "missing_output_worklist_count",
        "selected_candidate_total_count",
        "selected_trusted_total_count",
        "selected_review_required_total_count",
        "selected_core_trusted_rate",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "router_sandbox_integration_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
