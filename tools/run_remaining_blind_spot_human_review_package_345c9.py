from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.remaining_blind_spot_human_review_package_345c9 import (  # noqa: E402
    ARTIFACT_INDEX_FILE_NAME,
    BLOCKED_ROWS_CSV_FILE_NAME,
    BLOCKED_ROWS_JSON_FILE_NAME,
    CONTEXT_ONLY_ROWS_CSV_FILE_NAME,
    CONTEXT_ONLY_ROWS_JSON_FILE_NAME,
    DECISION_OPTIONS_FILE_NAME,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_DIR,
    EXECUTIVE_SUMMARY_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_FILE_NAME,
    PACKAGE_SUMMARY_JSON_FILE_NAME,
    REVIEW_REQUIRED_FIELDS,
    REVIEW_ROWS_CSV_FILE_NAME,
    REVIEW_ROWS_JSON_FILE_NAME,
    REVIEWER_CHECKLIST_FILE_NAME,
    WORKBOOK_FILE_NAME,
    append_345c9_ledger_entry,
    build_remaining_blind_spot_human_review_package_345c9,
)
from datefac.benchmark.remaining_blind_spot_human_review_package_345c9_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    artifact_index_markdown,
    decision_options_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    reviewer_checklist_markdown,
    write_csv,
    write_excel,
    write_json,
)


def _run_once(
    *,
    input_dir: Path,
    output_dir: Path,
    include_context_only: bool,
    ledger_path: Path,
) -> dict:
    return build_remaining_blind_spot_human_review_package_345c9(
        remaining_blind_spot_alias_candidate_package_345c8_dir=input_dir,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        include_context_only=include_context_only,
        ledger_path=ledger_path,
    )


def _write_outputs(output_dir: Path, artifacts: dict) -> None:
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / REVIEW_ROWS_JSON_FILE_NAME, artifacts["review_rows"])
    write_csv(
        output_dir / REVIEW_ROWS_CSV_FILE_NAME,
        artifacts["review_rows"],
        REVIEW_REQUIRED_FIELDS,
    )
    write_json(output_dir / CONTEXT_ONLY_ROWS_JSON_FILE_NAME, artifacts["context_only_rows"])
    write_csv(
        output_dir / CONTEXT_ONLY_ROWS_CSV_FILE_NAME,
        artifacts["context_only_rows"],
        list(artifacts["context_only_rows"][0].keys()) if artifacts["context_only_rows"] else [],
    )
    write_json(output_dir / BLOCKED_ROWS_JSON_FILE_NAME, artifacts["blocked_rows"])
    write_csv(
        output_dir / BLOCKED_ROWS_CSV_FILE_NAME,
        artifacts["blocked_rows"],
        list(artifacts["blocked_rows"][0].keys()) if artifacts["blocked_rows"] else [],
    )
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    write_json(output_dir / PACKAGE_SUMMARY_JSON_FILE_NAME, artifacts["package_summary"])
    (output_dir / REVIEWER_CHECKLIST_FILE_NAME).write_text(
        reviewer_checklist_markdown(
            artifacts["manifest"],
            str(output_dir / WORKBOOK_FILE_NAME),
        ),
        encoding="utf-8",
    )
    (output_dir / DECISION_OPTIONS_FILE_NAME).write_text(
        decision_options_markdown(),
        encoding="utf-8",
    )
    top_rows = sorted(
        artifacts["review_rows"],
        key=lambda row: (-int(row.get("remaining_row_count", 0)), str(row.get("raw_metric_name", ""))),
    )[:10]
    (output_dir / EXECUTIVE_SUMMARY_FILE_NAME).write_text(
        executive_summary_markdown(artifacts["manifest"], top_rows),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_FILE_NAME).write_text(
        next_plan_markdown(artifacts["manifest"]),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 345C9 remaining blind spot human review package."
    )
    parser.add_argument(
        "--remaining-blind-spot-alias-candidate-package-345c8-dir",
        default=str(DEFAULT_REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--include-context-only", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.remaining_blind_spot_alias_candidate_package_345c8_dir)
    output_dir = Path(args.output_dir)
    ledger_path = Path(args.ledger_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    initial_artifacts = _run_once(
        input_dir=input_dir,
        output_dir=output_dir,
        include_context_only=args.include_context_only,
        ledger_path=ledger_path,
    )
    _write_outputs(output_dir, initial_artifacts)

    append_345c9_ledger_entry(manifest=initial_artifacts["manifest"], ledger_path=ledger_path)

    final_artifacts = _run_once(
        input_dir=input_dir,
        output_dir=output_dir,
        include_context_only=args.include_context_only,
        ledger_path=ledger_path,
    )
    _write_outputs(output_dir, final_artifacts)

    manifest = final_artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"workbook: {output_dir / WORKBOOK_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"review_required_row_count: {manifest.get('review_required_row_count', '')}")
    print(f"context_only_row_count: {manifest.get('context_only_row_count', '')}")
    print(
        f"blocked_or_too_generic_row_count: {manifest.get('blocked_or_too_generic_row_count', '')}"
    )
    print(
        f"generated_review_pending_count: {manifest.get('generated_review_pending_count', '')}"
    )
    print(f"generated_approved_count: {manifest.get('generated_approved_count', '')}")
    print(
        f"alias_rule_update_allowed_count: {manifest.get('alias_rule_update_allowed_count', '')}"
    )
    print(f"milestone_ledger_updated: {manifest.get('milestone_ledger_updated', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

