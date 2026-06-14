from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.official_alias_rule_update_candidate_package_345c7 import (  # noqa: E402
    ALIAS_RULE_CANDIDATES_CSV_FILE_NAME,
    ALIAS_RULE_CANDIDATE_FIELDS,
    ALIAS_RULE_CANDIDATES_JSON_FILE_NAME,
    ARTIFACT_INDEX_MD_FILE_NAME,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_ALIAS_APPLY_SIMULATION_345C6_DIR,
    DEFAULT_REVIEWED_ALIAS_DECISION_INGESTION_345C5_DIR,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    IMPACT_SUMMARY_CSV_FILE_NAME,
    IMPACT_SUMMARY_FIELDS,
    IMPACT_SUMMARY_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    REMAINING_BLIND_SPOT_SUMMARY_CSV_FILE_NAME,
    REMAINING_BLIND_SPOT_SUMMARY_FIELDS,
    REMAINING_BLIND_SPOT_SUMMARY_JSON_FILE_NAME,
    RISK_REVIEW_CSV_FILE_NAME,
    RISK_REVIEW_FIELDS,
    RISK_REVIEW_JSON_FILE_NAME,
    RULE_UPDATE_CHECKLIST_MD_FILE_NAME,
    build_official_alias_rule_update_candidate_package_345c7,
)
from datefac.benchmark.official_alias_rule_update_candidate_package_345c7_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    rule_update_checklist_markdown,
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 345C7 official alias rule update candidate package."
    )
    parser.add_argument(
        "--reviewed-alias-decision-ingestion-345c5-dir",
        default=str(DEFAULT_REVIEWED_ALIAS_DECISION_INGESTION_345C5_DIR),
    )
    parser.add_argument(
        "--reviewed-alias-apply-simulation-345c6-dir",
        default=str(DEFAULT_REVIEWED_ALIAS_APPLY_SIMULATION_345C6_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_official_alias_rule_update_candidate_package_345c7(
        reviewed_alias_decision_ingestion_345c5_dir=Path(
            args.reviewed_alias_decision_ingestion_345c5_dir
        ),
        reviewed_alias_apply_simulation_345c6_dir=Path(
            args.reviewed_alias_apply_simulation_345c6_dir
        ),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(
        output_dir / ALIAS_RULE_CANDIDATES_JSON_FILE_NAME,
        artifacts["alias_rule_candidates"],
    )
    write_csv(
        output_dir / ALIAS_RULE_CANDIDATES_CSV_FILE_NAME,
        artifacts["alias_rule_candidates"],
        ALIAS_RULE_CANDIDATE_FIELDS,
    )
    write_json(output_dir / IMPACT_SUMMARY_JSON_FILE_NAME, artifacts["impact_summary"])
    write_csv(
        output_dir / IMPACT_SUMMARY_CSV_FILE_NAME,
        artifacts["impact_summary_rows"],
        IMPACT_SUMMARY_FIELDS,
    )
    write_json(output_dir / RISK_REVIEW_JSON_FILE_NAME, artifacts["risk_review"])
    write_csv(
        output_dir / RISK_REVIEW_CSV_FILE_NAME,
        artifacts["risk_review"],
        RISK_REVIEW_FIELDS,
    )
    write_json(
        output_dir / REMAINING_BLIND_SPOT_SUMMARY_JSON_FILE_NAME,
        artifacts["remaining_blind_spot_summary"],
    )
    write_csv(
        output_dir / REMAINING_BLIND_SPOT_SUMMARY_CSV_FILE_NAME,
        artifacts["remaining_blind_spot_summary"],
        REMAINING_BLIND_SPOT_SUMMARY_FIELDS,
    )
    (output_dir / RULE_UPDATE_CHECKLIST_MD_FILE_NAME).write_text(
        rule_update_checklist_markdown(),
        encoding="utf-8",
    )
    top_impact_rows = sorted(
        artifacts["alias_rule_candidates"],
        key=lambda row: (
            -int(row.get("simulation_newly_normalized_row_count", 0)),
            str(row.get("raw_metric_name", "")),
        ),
    )[:10]
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(
        executive_summary_markdown(artifacts["manifest"], top_impact_rows),
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
    print(f"candidate_row_count: {manifest.get('candidate_row_count', '')}")
    print(
        f"controlled_rule_update_candidate_count: {manifest.get('controlled_rule_update_candidate_count', '')}"
    )
    print(
        f"demo_only_sidecar_candidate_count: {manifest.get('demo_only_sidecar_candidate_count', '')}"
    )
    print(
        f"needs_additional_review_candidate_count: {manifest.get('needs_additional_review_candidate_count', '')}"
    )
    print(f"low_risk_candidate_count: {manifest.get('low_risk_candidate_count', '')}")
    print(f"medium_risk_candidate_count: {manifest.get('medium_risk_candidate_count', '')}")
    print(f"high_risk_candidate_count: {manifest.get('high_risk_candidate_count', '')}")
    print(
        f"normalization_coverage_ratio_delta: {manifest.get('normalization_coverage_ratio_delta', '')}"
    )
    print(f"ready_candidate_count_delta: {manifest.get('ready_candidate_count_delta', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
