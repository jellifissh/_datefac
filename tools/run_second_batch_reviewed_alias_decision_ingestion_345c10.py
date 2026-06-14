from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.second_batch_reviewed_alias_decision_ingestion_345c10 import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    DECISION_SUMMARY_JSON_FILE_NAME,
    DEFAULT_345C9_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_WORKBOOK,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    OUTPUT_ROW_FIELDS,
    REJECTED_OR_BLOCKED_CSV_FILE_NAME,
    REJECTED_OR_BLOCKED_JSON_FILE_NAME,
    REVIEWED_DECISIONS_CSV_FILE_NAME,
    REVIEWED_DECISIONS_JSON_FILE_NAME,
    VALIDATED_APPROVED_CSV_FILE_NAME,
    VALIDATED_APPROVED_JSON_FILE_NAME,
    VALIDATION_ISSUES_JSON_FILE_NAME,
    append_345c10_ledger_entry,
    build_second_batch_reviewed_alias_decision_ingestion_345c10,
)
from datefac.benchmark.second_batch_reviewed_alias_decision_ingestion_345c10_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    write_csv,
    write_json,
)


def _run_once(
    *,
    input_dir: Path,
    reviewed_workbook: Path,
    output_dir: Path,
    ledger_path: Path,
) -> dict:
    return build_second_batch_reviewed_alias_decision_ingestion_345c10(
        remaining_blind_spot_human_review_package_345c9_dir=input_dir,
        reviewed_blind_spot_workbook=reviewed_workbook,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=ledger_path,
    )


def _write_outputs(output_dir: Path, artifacts: dict) -> None:
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
        output_dir / REJECTED_OR_BLOCKED_JSON_FILE_NAME,
        artifacts["rejected_or_blocked_aliases"],
    )
    write_csv(
        output_dir / REJECTED_OR_BLOCKED_CSV_FILE_NAME,
        artifacts["rejected_or_blocked_aliases"],
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 345C10 second-batch reviewed alias decision ingestion."
    )
    parser.add_argument(
        "--remaining-blind-spot-human-review-package-345c9-dir",
        default=str(DEFAULT_345C9_DIR),
    )
    parser.add_argument(
        "--reviewed-blind-spot-workbook",
        default=str(DEFAULT_REVIEWED_WORKBOOK),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    args = parser.parse_args()

    input_dir = Path(args.remaining_blind_spot_human_review_package_345c9_dir)
    reviewed_workbook = Path(args.reviewed_blind_spot_workbook)
    output_dir = Path(args.output_dir)
    ledger_path = Path(args.ledger_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    initial_artifacts = _run_once(
        input_dir=input_dir,
        reviewed_workbook=reviewed_workbook,
        output_dir=output_dir,
        ledger_path=ledger_path,
    )
    _write_outputs(output_dir, initial_artifacts)

    append_345c10_ledger_entry(
        manifest=initial_artifacts["manifest"],
        ledger_path=ledger_path,
    )

    final_artifacts = _run_once(
        input_dir=input_dir,
        reviewed_workbook=reviewed_workbook,
        output_dir=output_dir,
        ledger_path=ledger_path,
    )
    _write_outputs(output_dir, final_artifacts)

    manifest = final_artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"reviewed_row_count: {manifest.get('reviewed_row_count', '')}")
    print(
        f"approved_existing_mapping_count: {manifest.get('approved_existing_mapping_count', '')}"
    )
    print(f"approved_new_standard_count: {manifest.get('approved_new_standard_count', '')}")
    print(f"rejected_too_generic_count: {manifest.get('rejected_too_generic_count', '')}")
    print(f"needs_source_context_count: {manifest.get('needs_source_context_count', '')}")
    print(f"deferred_count: {manifest.get('deferred_count', '')}")
    print(f"validation_issue_count: {manifest.get('validation_issue_count', '')}")
    print(
        f"apply_simulation_eligible_count: {manifest.get('apply_simulation_eligible_count', '')}"
    )
    print(
        f"needs_alias_family_expansion_count: {manifest.get('needs_alias_family_expansion_count', '')}"
    )
    print(f"alias_rule_update_allowed_count: {manifest.get('alias_rule_update_allowed_count', '')}")
    print(f"milestone_ledger_updated: {manifest.get('milestone_ledger_updated', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

