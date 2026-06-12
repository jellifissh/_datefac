from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_excel_ingestion_343d import (  # noqa: E402
    DECISION_SUMMARY_FILE_NAME,
    DEFAULT_FILLED_WORKBOOK,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REAL_EXCEL_REVIEW_343C_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DISCLOSURE_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    REVIEWED_RESULT_FILE_NAME,
    SUMMARY_FILE_NAME,
    VALIDATION_ERRORS_FILE_NAME,
    VALIDATION_WARNINGS_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS,
    build_review_queue_excel_ingestion_343d,
)
from datefac.benchmark.review_queue_excel_ingestion_343d_report import (  # noqa: E402
    ai_assisted_disclosure_markdown,
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 343D real Excel review result ingestion.")
    parser.add_argument("--real-excel-review-343c-dir", default=str(DEFAULT_REAL_EXCEL_REVIEW_343C_DIR))
    parser.add_argument("--review-queue-schema-343a-dir", default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR))
    parser.add_argument("--filled-workbook", default=str(DEFAULT_FILLED_WORKBOOK))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_excel_ingestion_343d(
        real_excel_review_343c_dir=Path(args.real_excel_review_343c_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        filled_workbook=Path(args.filled_workbook),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / VALIDATION_ERRORS_FILE_NAME, artifacts["validation_errors"])
    write_json(output_dir / VALIDATION_WARNINGS_FILE_NAME, artifacts["validation_warnings"])
    write_json(output_dir / DECISION_SUMMARY_FILE_NAME, artifacts["decision_summary"])
    write_jsonl(output_dir / REVIEWED_RESULT_FILE_NAME, artifacts["reviewed_result_rows"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    (output_dir / REPORT_FILE_NAME).write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")
    (output_dir / DISCLOSURE_FILE_NAME).write_text(ai_assisted_disclosure_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"review_queue_excel_ingestion_343d_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_reviewed_result_jsonl: {output_dir / REVIEWED_RESULT_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_validation_errors_json: {output_dir / VALIDATION_ERRORS_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_validation_warnings_json: {output_dir / VALIDATION_WARNINGS_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_decision_summary_json: {output_dir / DECISION_SUMMARY_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_ai_assisted_review_disclosure_md: {output_dir / DISCLOSURE_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_excel_ingestion_343d_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "filled_workbook_path",
        "filled_row_count",
        "valid_row_count",
        "invalid_row_count",
        "confirmed_count",
        "corrected_count",
        "rejected_count",
        "needs_source_check_count",
        "skipped_count",
        "validation_error_count",
        "validation_warning_count",
        "review_source_type",
        "not_pure_human_review",
        "strict_human_review_completed",
        "requires_human_spot_check",
        "reviewed_result_ingested",
        "reviewed_result_jsonl_generated",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343e",
        "recommended_343e_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
