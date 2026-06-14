from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.second_batch_alias_apply_simulation_345c11 import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    COMBINED_ALIAS_MAP_CSV_FILE_NAME,
    COMBINED_ALIAS_MAP_FIELDS,
    COMBINED_ALIAS_MAP_JSON_FILE_NAME,
    COVERAGE_BEFORE_AFTER_CSV_FILE_NAME,
    COVERAGE_BEFORE_AFTER_FIELDS,
    COVERAGE_BEFORE_AFTER_JSON_FILE_NAME,
    DEFAULT_LEDGER_PATH,
    DEFAULT_METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_ALIAS_APPLY_SIMULATION_345C6_DIR,
    DEFAULT_SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_DIR,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    INCREMENTAL_IMPACT_SUMMARY_CSV_FILE_NAME,
    INCREMENTAL_IMPACT_SUMMARY_FIELDS,
    INCREMENTAL_IMPACT_SUMMARY_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    NON_APPLIED_ALIASES_CSV_FILE_NAME,
    NON_APPLIED_ALIASES_JSON_FILE_NAME,
    NON_APPLIED_ALIAS_FIELDS,
    REMAINING_BLIND_SPOTS_CSV_FILE_NAME,
    REMAINING_BLIND_SPOT_FIELDS,
    REMAINING_BLIND_SPOTS_JSON_FILE_NAME,
    SECOND_BATCH_APPLIED_ALIAS_MAP_CSV_FILE_NAME,
    SECOND_BATCH_APPLIED_ALIAS_MAP_FIELDS,
    SECOND_BATCH_APPLIED_ALIAS_MAP_JSON_FILE_NAME,
    SIMULATED_METRIC_ROWS_CSV_FILE_NAME,
    SIMULATED_METRIC_ROWS_JSON_FILE_NAME,
    SIMULATED_METRIC_ROW_FIELDS,
    STOP_OR_RETURN_TO_345D_DECISION_JSON_FILE_NAME,
    build_second_batch_alias_apply_simulation_345c11,
)
from datefac.benchmark.second_batch_alias_apply_simulation_345c11_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 345C11 second-batch alias apply simulation."
    )
    parser.add_argument(
        "--metric-candidate-normalization-coverage-345c-dir",
        default=str(DEFAULT_METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_DIR),
    )
    parser.add_argument(
        "--reviewed-alias-apply-simulation-345c6-dir",
        default=str(DEFAULT_REVIEWED_ALIAS_APPLY_SIMULATION_345C6_DIR),
    )
    parser.add_argument(
        "--second-batch-reviewed-alias-decision-ingestion-345c10-dir",
        default=str(DEFAULT_SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_second_batch_alias_apply_simulation_345c11(
        metric_candidate_normalization_coverage_345c_dir=Path(
            args.metric_candidate_normalization_coverage_345c_dir
        ),
        reviewed_alias_apply_simulation_345c6_dir=Path(
            args.reviewed_alias_apply_simulation_345c6_dir
        ),
        second_batch_reviewed_alias_decision_ingestion_345c10_dir=Path(
            args.second_batch_reviewed_alias_decision_ingestion_345c10_dir
        ),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(
        output_dir / COMBINED_ALIAS_MAP_JSON_FILE_NAME,
        artifacts["combined_alias_map"],
    )
    write_csv(
        output_dir / COMBINED_ALIAS_MAP_CSV_FILE_NAME,
        artifacts["combined_alias_map"],
        COMBINED_ALIAS_MAP_FIELDS,
    )
    write_json(
        output_dir / SECOND_BATCH_APPLIED_ALIAS_MAP_JSON_FILE_NAME,
        artifacts["second_batch_applied_alias_map"],
    )
    write_csv(
        output_dir / SECOND_BATCH_APPLIED_ALIAS_MAP_CSV_FILE_NAME,
        artifacts["second_batch_applied_alias_map"],
        SECOND_BATCH_APPLIED_ALIAS_MAP_FIELDS,
    )
    write_json(
        output_dir / SIMULATED_METRIC_ROWS_JSON_FILE_NAME,
        artifacts["simulated_metric_rows"],
    )
    write_csv(
        output_dir / SIMULATED_METRIC_ROWS_CSV_FILE_NAME,
        artifacts["simulated_metric_rows"],
        SIMULATED_METRIC_ROW_FIELDS,
    )
    write_json(
        output_dir / COVERAGE_BEFORE_AFTER_JSON_FILE_NAME,
        artifacts["coverage_before_after"],
    )
    write_csv(
        output_dir / COVERAGE_BEFORE_AFTER_CSV_FILE_NAME,
        [artifacts["coverage_before_after"]],
        COVERAGE_BEFORE_AFTER_FIELDS,
    )
    write_json(
        output_dir / INCREMENTAL_IMPACT_SUMMARY_JSON_FILE_NAME,
        artifacts["incremental_impact_summary"],
    )
    write_csv(
        output_dir / INCREMENTAL_IMPACT_SUMMARY_CSV_FILE_NAME,
        [artifacts["incremental_impact_summary"]],
        INCREMENTAL_IMPACT_SUMMARY_FIELDS,
    )
    write_json(
        output_dir / REMAINING_BLIND_SPOTS_JSON_FILE_NAME,
        artifacts["remaining_blind_spots"],
    )
    write_csv(
        output_dir / REMAINING_BLIND_SPOTS_CSV_FILE_NAME,
        artifacts["remaining_blind_spots"],
        REMAINING_BLIND_SPOT_FIELDS,
    )
    write_json(
        output_dir / NON_APPLIED_ALIASES_JSON_FILE_NAME,
        artifacts["non_applied_aliases"],
    )
    write_csv(
        output_dir / NON_APPLIED_ALIASES_CSV_FILE_NAME,
        artifacts["non_applied_aliases"],
        NON_APPLIED_ALIAS_FIELDS,
    )
    write_json(
        output_dir / STOP_OR_RETURN_TO_345D_DECISION_JSON_FILE_NAME,
        artifacts["stop_or_return_to_345d_decision"],
    )
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(
        executive_summary_markdown(
            artifacts["manifest"],
            artifacts["second_batch_applied_alias_map"],
        ),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(
        next_plan_markdown(artifacts["manifest"]),
        encoding="utf-8",
    )

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"first_batch_alias_count: {manifest.get('first_batch_alias_count', '')}")
    print(f"second_batch_eligible_alias_count: {manifest.get('second_batch_eligible_alias_count', '')}")
    print(f"second_batch_applied_alias_key_count: {manifest.get('second_batch_applied_alias_key_count', '')}")
    print(
        f"second_batch_simulated_newly_normalized_row_count: {manifest.get('second_batch_simulated_newly_normalized_row_count', '')}"
    )
    print(
        f"cumulative_simulated_newly_normalized_row_count: {manifest.get('cumulative_simulated_newly_normalized_row_count', '')}"
    )
    print(f"coverage_ratio_before: {manifest.get('coverage_ratio_before', '')}")
    print(
        f"coverage_ratio_after_first_batch: {manifest.get('coverage_ratio_after_first_batch', '')}"
    )
    print(
        f"coverage_ratio_after_second_batch: {manifest.get('coverage_ratio_after_second_batch', '')}"
    )
    print(f"ready_candidate_count_before: {manifest.get('ready_candidate_count_before', '')}")
    print(
        f"ready_candidate_count_after_first_batch: {manifest.get('ready_candidate_count_after_first_batch', '')}"
    )
    print(
        f"ready_candidate_count_after_second_batch: {manifest.get('ready_candidate_count_after_second_batch', '')}"
    )
    print(
        f"remaining_unnormalized_metric_row_count: {manifest.get('remaining_unnormalized_metric_row_count', '')}"
    )
    print(
        f"alias_branch_final_recommendation: {manifest.get('alias_branch_final_recommendation', '')}"
    )
    print(
        f"full_structured_demo_export_reasonable_after_345c11: {manifest.get('full_structured_demo_export_reasonable_after_345c11', '')}"
    )
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
