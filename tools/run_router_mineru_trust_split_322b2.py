from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.pipeline.router_mineru_trust_split import (
    RouterMineruTrustSplit322B2Config,
    run_router_mineru_trust_split_322b2,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322B2 router MinerU trust split calibration.")
    parser.add_argument("--pipeline-322b-dir", required=True)
    parser.add_argument("--pipeline-322a-dir", required=True)
    parser.add_argument("--router-integration-dir", required=True)
    parser.add_argument("--router-dir", required=True)
    parser.add_argument("--mineru-body-reference-dir", required=True)
    parser.add_argument("--structtable-mapping-dir", required=True)
    parser.add_argument("--docling-mapping-dir", required=True)
    parser.add_argument("--pure-vlm-calibration-dir", required=True)
    parser.add_argument("--ppstructure-benchmark-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_router_mineru_trust_split_322b2(
        RouterMineruTrustSplit322B2Config(
            pipeline_322b_dir=Path(args.pipeline_322b_dir),
            pipeline_322a_dir=Path(args.pipeline_322a_dir),
            router_integration_dir=Path(args.router_integration_dir),
            router_dir=Path(args.router_dir),
            mineru_body_reference_dir=Path(args.mineru_body_reference_dir),
            structtable_mapping_dir=Path(args.structtable_mapping_dir),
            docling_mapping_dir=Path(args.docling_mapping_dir),
            pure_vlm_calibration_dir=Path(args.pure_vlm_calibration_dir),
            ppstructure_benchmark_dir=Path(args.ppstructure_benchmark_dir),
            output_dir=Path(args.output_dir),
        )
    )
    summary = result.get("summary", {})
    print(f"router_mineru_trust_split_322b2_excel: {result.get('excel_path', '')}")
    print(f"router_mineru_trust_split_322b2_summary_json: {result.get('summary_json_path', '')}")
    print(f"router_mineru_trust_split_322b2_report_md: {result.get('report_md_path', '')}")
    for key in [
        "input_candidate_count",
        "pending_split_before_count",
        "pending_split_after_count",
        "reclassified_candidate_count",
        "trusted_total_before_322b2",
        "trusted_total_after_322b2",
        "review_required_total_before_322b2",
        "review_required_total_after_322b2",
        "rejected_total_after_322b2",
        "selected_core_trusted_rate_before_322b2",
        "selected_core_trusted_rate_after_322b2",
        "selected_all_trusted_rate_after_322b2",
        "unknown_metric_candidate_count",
        "unit_unknown_candidate_count",
        "value_conflict_candidate_count",
        "section_context_required_candidate_count",
        "alias_candidate_count",
        "semantic_adjudicator_worklist_count",
        "manual_review_worklist_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "router_mineru_trust_split_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
