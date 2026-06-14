from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.reviewed_alias_apply_simulation_345c6 import (  # noqa: E402
    APPLIED_ALIAS_MAP_CSV_FILE_NAME,
    APPLIED_ALIAS_MAP_FIELDS,
    APPLIED_ALIAS_MAP_JSON_FILE_NAME,
    ARTIFACT_INDEX_MD_FILE_NAME,
    COVERAGE_BEFORE_AFTER_CSV_FILE_NAME,
    COVERAGE_BEFORE_AFTER_FIELDS,
    COVERAGE_BEFORE_AFTER_JSON_FILE_NAME,
    DEFAULT_METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_ALIAS_DECISION_INGESTION_345C5_DIR,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    NON_APPLIED_ALIASES_CSV_FILE_NAME,
    NON_APPLIED_ALIASES_JSON_FILE_NAME,
    NON_APPLIED_ALIAS_FIELDS,
    REMAINING_BLIND_SPOTS_CSV_FILE_NAME,
    REMAINING_BLIND_SPOTS_JSON_FILE_NAME,
    REMAINING_BLIND_SPOT_FIELDS,
    SIMULATED_METRIC_ROWS_CSV_FILE_NAME,
    SIMULATED_METRIC_ROWS_JSON_FILE_NAME,
    SIMULATED_METRIC_ROW_FIELDS,
    build_reviewed_alias_apply_simulation_345c6,
)
from datefac.benchmark.reviewed_alias_apply_simulation_345c6_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 345C6 reviewed alias apply simulation."
    )
    parser.add_argument(
        "--metric-candidate-normalization-coverage-345c-dir",
        default=str(DEFAULT_METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_DIR),
    )
    parser.add_argument(
        "--reviewed-alias-decision-ingestion-345c5-dir",
        default=str(DEFAULT_REVIEWED_ALIAS_DECISION_INGESTION_345C5_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_reviewed_alias_apply_simulation_345c6(
        metric_candidate_normalization_coverage_345c_dir=Path(
            args.metric_candidate_normalization_coverage_345c_dir
        ),
        reviewed_alias_decision_ingestion_345c5_dir=Path(
            args.reviewed_alias_decision_ingestion_345c5_dir
        ),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(
        output_dir / SIMULATED_METRIC_ROWS_JSON_FILE_NAME,
        artifacts["simulated_metric_rows"],
    )
    write_csv(
        output_dir / SIMULATED_METRIC_ROWS_CSV_FILE_NAME,
        artifacts["simulated_metric_rows"],
        SIMULATED_METRIC_ROW_FIELDS,
    )
    write_json(output_dir / APPLIED_ALIAS_MAP_JSON_FILE_NAME, artifacts["applied_alias_map"])
    write_csv(
        output_dir / APPLIED_ALIAS_MAP_CSV_FILE_NAME,
        artifacts["applied_alias_map"],
        APPLIED_ALIAS_MAP_FIELDS,
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
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(
        executive_summary_markdown(artifacts["manifest"]),
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
    print(f"validated_approved_alias_count: {manifest.get('validated_approved_alias_count', '')}")
    print(f"applied_alias_key_count: {manifest.get('applied_alias_key_count', '')}")
    print(f"simulated_alias_applied_row_count: {manifest.get('simulated_alias_applied_row_count', '')}")
    print(f"simulated_newly_normalized_row_count: {manifest.get('simulated_newly_normalized_row_count', '')}")
    print(
        f"normalization_coverage_ratio_before: {manifest.get('normalization_coverage_ratio_before', '')}"
    )
    print(
        f"normalization_coverage_ratio_after_simulation: {manifest.get('normalization_coverage_ratio_after_simulation', '')}"
    )
    print(f"ready_candidate_count_delta: {manifest.get('ready_candidate_count_delta', '')}")
    print(
        f"remaining_unnormalized_raw_metric_name_count: {manifest.get('remaining_unnormalized_raw_metric_name_count', '')}"
    )
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
