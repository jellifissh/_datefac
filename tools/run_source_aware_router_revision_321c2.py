from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.router.source_aware_router_revision import (
    SourceAwareRouterRevisionConfig,
    run_source_aware_router_revision,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321C2 source-aware router revision.")
    parser.add_argument("--pure-vlm-calibration-dir", required=True)
    parser.add_argument("--pure-vlm-output-root", required=True)
    parser.add_argument("--mineru-assisted-output-root", required=False)
    parser.add_argument("--previous-router-dir", required=False)
    parser.add_argument("--ppstructure-benchmark-dir", required=False)
    parser.add_argument("--mineru-benchmark-dir", required=False)
    parser.add_argument("--mineru-output-root", required=False)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_source_aware_router_revision(
        SourceAwareRouterRevisionConfig(
            pure_vlm_calibration_dir=Path(args.pure_vlm_calibration_dir),
            pure_vlm_output_root=Path(args.pure_vlm_output_root),
            mineru_assisted_output_root=Path(args.mineru_assisted_output_root) if args.mineru_assisted_output_root else None,
            previous_router_dir=Path(args.previous_router_dir) if args.previous_router_dir else None,
            ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir) if args.ppstructure_benchmark_dir else None,
            mineru_benchmark_dir=Path(args.mineru_benchmark_dir) if args.mineru_benchmark_dir else None,
            mineru_output_root=Path(args.mineru_output_root) if args.mineru_output_root else None,
            output_dir=Path(args.output_dir),
        )
    )
    summary = result.get("summary", {})
    print(f"source_aware_router_revision_excel: {result.get('excel_path', '')}")
    print(f"source_aware_router_revision_summary_json: {result.get('summary_json_path', '')}")
    print(f"source_aware_router_revision_report_md: {result.get('report_md_path', '')}")
    print(f"source_aware_router_policy_json: {result.get('policy_json_path', '')}")
    for key in [
        "pure_vlm_calibrated_trusted_rate",
        "pure_vlm_table_with_trusted_count",
        "pure_vlm_unit_unknown_count",
        "pure_vlm_unknown_metric_count",
        "pure_vlm_calibration_decision",
        "ppstructure_trusted_rate",
        "previous_router_vlm_primary_count",
        "revised_mineru_table_body_structuring_count",
        "revised_pure_vlm_image_only_count",
        "revised_ppstructure_fallback_count",
        "revised_manual_review_required_count",
        "revised_skip_non_core_count",
        "revised_unsupported_count",
        "source_audit_folder_count",
        "pure_vlm_source_verified_count",
        "source_contamination_risk_count",
        "router_qa_pass_count",
        "router_qa_warn_count",
        "router_qa_fail_count",
        "router_revision_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
