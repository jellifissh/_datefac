from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_strict_human_review_package_343i import (  # noqa: E402
    CLIENT_EXPORT_BOUNDARY_FILE_NAME,
    DEFAULT_AUDIT_SUMMARY_343H_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SPOT_CHECK_INGESTION_343G_DIR,
    EXPECTED_IMPORT_CONTRACT_FILE_NAME,
    FILL_GUIDE_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    REVIEWER_INSTRUCTIONS_FILE_NAME,
    REVIEW_ITEMS_FILE_NAME,
    REVIEW_TEMPLATE_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_343I,
    build_review_queue_strict_human_review_package_343i,
)
from datefac.benchmark.review_queue_strict_human_review_package_343i_report import (  # noqa: E402
    client_export_boundary_markdown,
    fill_guide_markdown,
    report_markdown,
    reviewer_instructions_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 343I strict human review package generation."
    )
    parser.add_argument("--audit-summary-343h-dir", default=str(DEFAULT_AUDIT_SUMMARY_343H_DIR))
    parser.add_argument(
        "--spot-check-ingestion-343g-dir",
        default=str(DEFAULT_SPOT_CHECK_INGESTION_343G_DIR),
    )
    parser.add_argument(
        "--review-queue-schema-343a-dir",
        default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_strict_human_review_package_343i(
        audit_summary_343h_dir=Path(args.audit_summary_343h_dir),
        spot_check_ingestion_343g_dir=Path(args.spot_check_ingestion_343g_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME, artifacts["expected_import_contract"])
    write_jsonl(output_dir / REVIEW_ITEMS_FILE_NAME, artifacts["strict_review_items"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_343I)
    write_excel(
        output_dir / REVIEW_TEMPLATE_FILE_NAME,
        artifacts["review_template_sheets"],
        ["04_REVIEW_TEMPLATE"],
    )
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME).write_text(
        reviewer_instructions_markdown(artifacts["summary"]),
        encoding="utf-8",
    )
    (output_dir / FILL_GUIDE_FILE_NAME).write_text(
        fill_guide_markdown(),
        encoding="utf-8",
    )
    (output_dir / CLIENT_EXPORT_BOUNDARY_FILE_NAME).write_text(
        client_export_boundary_markdown(artifacts["summary"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_strict_human_review_package_343i_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_review_items_jsonl: {output_dir / REVIEW_ITEMS_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_expected_import_contract_json: {output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_review_template_xlsx: {output_dir / REVIEW_TEMPLATE_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_reviewer_instructions_md: {output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_fill_guide_md: {output_dir / FILL_GUIDE_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_client_export_boundary_md: {output_dir / CLIENT_EXPORT_BOUNDARY_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_strict_human_review_package_343i_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "input_ai_assisted_confirmed_count",
        "strict_review_item_count",
        "source_check_backlog_context_count",
        "strict_human_gap_item_count",
        "strict_human_review_package_generated",
        "review_template_generated",
        "reviewer_instructions_generated",
        "fill_guide_generated",
        "expected_import_contract_generated",
        "waiting_for_strict_human_review",
        "strict_human_review_result_ingested",
        "strict_human_review_completed",
        "requires_strict_human_review",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343j",
        "recommended_343j_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
