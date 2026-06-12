from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_real_excel_review_343c import (  # noqa: E402
    DEFAULT_EXCEL_ROUND_TRIP_343B_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SNAPSHOT_342S_DIR,
    EXPECTED_IMPORT_CONTRACT_FILE_NAME,
    FILL_GUIDE_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    REVIEW_TEMPLATE_FILE_NAME,
    REVIEWER_INSTRUCTIONS_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    build_review_queue_real_excel_review_343c,
)
from datefac.benchmark.review_queue_real_excel_review_343c_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    fill_guide_markdown,
    report_markdown,
    reviewer_instructions_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 343C real Excel review queue pilot.")
    parser.add_argument("--excel-round-trip-343b-dir", default=str(DEFAULT_EXCEL_ROUND_TRIP_343B_DIR))
    parser.add_argument("--review-queue-schema-343a-dir", default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR))
    parser.add_argument("--snapshot-342s-dir", default=str(DEFAULT_SNAPSHOT_342S_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_real_excel_review_343c(
        excel_round_trip_343b_dir=Path(args.excel_round_trip_343b_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        snapshot_342s_dir=Path(args.snapshot_342s_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME, artifacts["expected_import_contract"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    write_excel(output_dir / REVIEW_TEMPLATE_FILE_NAME, artifacts["review_template_sheets"], artifacts["review_template_sheets"].keys())
    (output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME).write_text(
        reviewer_instructions_markdown(artifacts["summary"]),
        encoding="utf-8",
    )
    (output_dir / FILL_GUIDE_FILE_NAME).write_text(
        fill_guide_markdown(artifacts["summary"]),
        encoding="utf-8",
    )
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_real_excel_review_343c_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_real_excel_review_343c_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_real_excel_review_343c_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_real_excel_review_343c_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_real_excel_review_343c_expected_import_contract_json: {output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME}")
    print(f"review_queue_real_excel_review_343c_review_template_xlsx: {output_dir / REVIEW_TEMPLATE_FILE_NAME}")
    print(f"review_queue_real_excel_review_343c_reviewer_instructions_md: {output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME}")
    print(f"review_queue_real_excel_review_343c_fill_guide_md: {output_dir / FILL_GUIDE_FILE_NAME}")
    print(f"review_queue_real_excel_review_343c_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_real_excel_review_343c_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "real_review_template_row_count",
        "fillable_review_row_count",
        "human_reviewed_audit_row_count",
        "simulated_direct_review_row_count",
        "simulated_corrected_review_row_count",
        "summary_derived_review_row_count",
        "allowed_decision_count",
        "real_review_template_generated",
        "reviewer_instructions_generated",
        "fill_guide_generated",
        "expected_import_contract_generated",
        "waiting_for_human_review",
        "reviewed_result_ingested",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343d",
        "recommended_343d_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
