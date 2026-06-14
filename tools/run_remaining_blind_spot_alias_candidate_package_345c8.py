from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.remaining_blind_spot_alias_candidate_package_345c8 import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    CANDIDATE_IMPACT_SUMMARY_CSV_FILE_NAME,
    CANDIDATE_IMPACT_SUMMARY_FIELDS,
    CANDIDATE_IMPACT_SUMMARY_JSON_FILE_NAME,
    DEFAULT_MAX_BLIND_SPOT_CANDIDATES,
    DEFAULT_MIN_ROW_IMPACT,
    DEFAULT_OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_ALIAS_APPLY_SIMULATION_345C6_DIR,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    REVIEW_BATCH_RECOMMENDATION_JSON_FILE_NAME,
    SELECTED_CANDIDATES_CSV_FILE_NAME,
    SELECTED_CANDIDATE_FIELDS,
    SELECTED_CANDIDATES_JSON_FILE_NAME,
    STOP_OR_CONTINUE_DECISION_JSON_FILE_NAME,
    UNSELECTED_BLIND_SPOTS_CSV_FILE_NAME,
    UNSELECTED_BLIND_SPOTS_JSON_FILE_NAME,
    UNSELECTED_FIELDS,
    build_remaining_blind_spot_alias_candidate_package_345c8,
)
from datefac.benchmark.remaining_blind_spot_alias_candidate_package_345c8_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 345C8 remaining blind spot alias candidate package."
    )
    parser.add_argument(
        "--reviewed-alias-apply-simulation-345c6-dir",
        default=str(DEFAULT_REVIEWED_ALIAS_APPLY_SIMULATION_345C6_DIR),
    )
    parser.add_argument(
        "--official-alias-rule-update-candidate-package-345c7-dir",
        default=str(DEFAULT_OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--max-blind-spot-candidates",
        type=int,
        default=DEFAULT_MAX_BLIND_SPOT_CANDIDATES,
    )
    parser.add_argument("--min-row-impact", type=int, default=DEFAULT_MIN_ROW_IMPACT)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_remaining_blind_spot_alias_candidate_package_345c8(
        reviewed_alias_apply_simulation_345c6_dir=Path(
            args.reviewed_alias_apply_simulation_345c6_dir
        ),
        official_alias_rule_update_candidate_package_345c7_dir=Path(
            args.official_alias_rule_update_candidate_package_345c7_dir
        ),
        output_dir=output_dir,
        max_blind_spot_candidates=args.max_blind_spot_candidates,
        min_row_impact=args.min_row_impact,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / SELECTED_CANDIDATES_JSON_FILE_NAME, artifacts["selected_candidates"])
    write_csv(
        output_dir / SELECTED_CANDIDATES_CSV_FILE_NAME,
        artifacts["selected_candidates"],
        SELECTED_CANDIDATE_FIELDS,
    )
    write_json(
        output_dir / UNSELECTED_BLIND_SPOTS_JSON_FILE_NAME,
        artifacts["unselected_blind_spots"],
    )
    write_csv(
        output_dir / UNSELECTED_BLIND_SPOTS_CSV_FILE_NAME,
        artifacts["unselected_blind_spots"],
        UNSELECTED_FIELDS,
    )
    write_json(
        output_dir / CANDIDATE_IMPACT_SUMMARY_JSON_FILE_NAME,
        artifacts["candidate_impact_summary_rows"],
    )
    write_csv(
        output_dir / CANDIDATE_IMPACT_SUMMARY_CSV_FILE_NAME,
        artifacts["candidate_impact_summary_rows"],
        CANDIDATE_IMPACT_SUMMARY_FIELDS,
    )
    write_json(
        output_dir / REVIEW_BATCH_RECOMMENDATION_JSON_FILE_NAME,
        artifacts["review_batch_recommendation"],
    )
    write_json(
        output_dir / STOP_OR_CONTINUE_DECISION_JSON_FILE_NAME,
        artifacts["stop_or_continue_decision"],
    )
    top_rows = sorted(
        artifacts["selected_candidates"],
        key=lambda row: (
            -int(row.get("remaining_row_count", 0)),
            str(row.get("raw_metric_name", "")),
        ),
    )[:10]
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(
        executive_summary_markdown(artifacts["manifest"], top_rows),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(
        next_plan_markdown(
            artifacts["manifest"], artifacts["stop_or_continue_decision"]
        ),
        encoding="utf-8",
    )

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"selected_candidate_count: {manifest.get('selected_candidate_count', '')}")
    print(
        f"selected_estimated_row_impact_total: {manifest.get('selected_estimated_row_impact_total', '')}"
    )
    print(
        f"selected_estimated_coverage_delta_total: {manifest.get('selected_estimated_coverage_delta_total', '')}"
    )
    print(
        f"selected_estimated_ready_candidate_delta_total: {manifest.get('selected_estimated_ready_candidate_delta_total', '')}"
    )
    print(
        f"alias_branch_stop_or_continue_decision: {manifest.get('alias_branch_stop_or_continue_decision', '')}"
    )
    print(
        f"full_structured_demo_export_reasonable_after_345c8: {manifest.get('full_structured_demo_export_reasonable_after_345c8', '')}"
    )
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
