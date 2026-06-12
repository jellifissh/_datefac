from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_excel_round_trip_343b import (  # noqa: E402
    DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SNAPSHOT_342S_DIR,
    IMPORT_SIMULATION_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    REVIEWED_RESULT_FILE_NAME,
    REVIEW_TEMPLATE_FILE_NAME,
    SUMMARY_FILE_NAME,
    VALIDATION_ERRORS_FILE_NAME,
    WORKBOOK_FILE_NAME,
    build_review_queue_excel_round_trip_343b,
)
from datefac.benchmark.review_queue_excel_round_trip_343b_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 343B Excel round-trip review queue pilot.")
    parser.add_argument("--review-queue-schema-343a-dir", default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR))
    parser.add_argument("--snapshot-342s-dir", default=str(DEFAULT_SNAPSHOT_342S_DIR))
    parser.add_argument("--audit-labeled-package-342r-dir", default=str(DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_excel_round_trip_343b(
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        snapshot_342s_dir=Path(args.snapshot_342s_dir),
        audit_labeled_package_342r_dir=Path(args.audit_labeled_package_342r_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / VALIDATION_ERRORS_FILE_NAME, artifacts["validation_errors_json"])
    write_jsonl(output_dir / REVIEWED_RESULT_FILE_NAME, artifacts["reviewed_result_rows"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    write_excel(output_dir / REVIEW_TEMPLATE_FILE_NAME, artifacts["review_template_sheets"], artifacts["review_template_sheets"].keys())
    write_excel(output_dir / IMPORT_SIMULATION_FILE_NAME, artifacts["import_simulation_sheets"], artifacts["import_simulation_sheets"].keys())
    (output_dir / REPORT_FILE_NAME).write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"review_queue_excel_round_trip_343b_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_excel_round_trip_343b_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_excel_round_trip_343b_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_excel_round_trip_343b_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_excel_round_trip_343b_validation_errors_json: {output_dir / VALIDATION_ERRORS_FILE_NAME}")
    print(f"review_queue_excel_round_trip_343b_review_template_xlsx: {output_dir / REVIEW_TEMPLATE_FILE_NAME}")
    print(f"review_queue_excel_round_trip_343b_import_simulation_xlsx: {output_dir / IMPORT_SIMULATION_FILE_NAME}")
    print(f"review_queue_excel_round_trip_343b_reviewed_result_jsonl: {output_dir / REVIEWED_RESULT_FILE_NAME}")
    print(f"review_queue_excel_round_trip_343b_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_excel_round_trip_343b_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "template_row_count",
        "import_simulation_row_count",
        "reviewed_result_row_count",
        "confirmed_count",
        "corrected_count",
        "rejected_count",
        "needs_source_check_count",
        "skipped_count",
        "validation_error_count",
        "validation_warning_count",
        "excel_template_generated",
        "import_simulation_generated",
        "reviewed_result_jsonl_generated",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343c",
        "recommended_343c_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
