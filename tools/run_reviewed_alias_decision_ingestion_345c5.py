from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.reviewed_alias_decision_ingestion_345c5 import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    DECISION_SUMMARY_JSON_FILE_NAME,
    DEFAULT_345C4_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_WORKBOOK,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    OUTPUT_ROW_FIELDS,
    REJECTED_OR_DEFERRED_CSV_FILE_NAME,
    REJECTED_OR_DEFERRED_JSON_FILE_NAME,
    REVIEWED_DECISIONS_CSV_FILE_NAME,
    REVIEWED_DECISIONS_JSON_FILE_NAME,
    VALIDATED_APPROVED_CSV_FILE_NAME,
    VALIDATED_APPROVED_JSON_FILE_NAME,
    VALIDATION_ISSUES_JSON_FILE_NAME,
    build_reviewed_alias_decision_ingestion_345c5,
)
from datefac.benchmark.reviewed_alias_decision_ingestion_345c5_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 345C5 reviewed alias decision ingestion."
    )
    parser.add_argument(
        "--alias-suggestion-human-review-package-345c4-dir",
        default=str(DEFAULT_345C4_DIR),
    )
    parser.add_argument(
        "--reviewed-alias-workbook",
        default=str(DEFAULT_REVIEWED_WORKBOOK),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_reviewed_alias_decision_ingestion_345c5(
        alias_suggestion_human_review_package_345c4_dir=Path(
            args.alias_suggestion_human_review_package_345c4_dir
        ),
        reviewed_alias_workbook=Path(args.reviewed_alias_workbook),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / REVIEWED_DECISIONS_JSON_FILE_NAME, artifacts["reviewed_decisions"])
    write_csv(
        output_dir / REVIEWED_DECISIONS_CSV_FILE_NAME,
        artifacts["reviewed_decisions"],
        OUTPUT_ROW_FIELDS,
    )
    write_json(
        output_dir / VALIDATED_APPROVED_JSON_FILE_NAME,
        artifacts["validated_approved_aliases"],
    )
    write_csv(
        output_dir / VALIDATED_APPROVED_CSV_FILE_NAME,
        artifacts["validated_approved_aliases"],
        OUTPUT_ROW_FIELDS,
    )
    write_json(
        output_dir / REJECTED_OR_DEFERRED_JSON_FILE_NAME,
        artifacts["rejected_or_deferred_aliases"],
    )
    write_csv(
        output_dir / REJECTED_OR_DEFERRED_CSV_FILE_NAME,
        artifacts["rejected_or_deferred_aliases"],
        OUTPUT_ROW_FIELDS,
    )
    write_json(output_dir / VALIDATION_ISSUES_JSON_FILE_NAME, artifacts["validation_issues"])
    write_json(output_dir / DECISION_SUMMARY_JSON_FILE_NAME, artifacts["decision_summary"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(
        executive_summary_markdown(artifacts["manifest"]),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(
        next_plan_markdown(),
        encoding="utf-8",
    )

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"reviewed_row_count: {manifest.get('reviewed_row_count', '')}")
    print(f"approved_new_standard_count: {manifest.get('approved_new_standard_count', '')}")
    print(f"rejected_alias_count: {manifest.get('rejected_alias_count', '')}")
    print(f"needs_more_context_count: {manifest.get('needs_more_context_count', '')}")
    print(f"apply_simulation_eligible_count: {manifest.get('apply_simulation_eligible_count', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
