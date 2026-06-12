from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_spot_check_package_343f import (  # noqa: E402
    BOUNDARY_FILE_NAME,
    DEFAULT_APPLY_SIMULATION_343E_DIR,
    DEFAULT_EXCEL_INGESTION_343D_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    EXPECTED_IMPORT_CONTRACT_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    PRIORITY_PLAN_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    REVIEWER_INSTRUCTIONS_FILE_NAME,
    REVIEW_TEMPLATE_FILE_NAME,
    SOURCE_CHECK_TODO_FILE_NAME,
    SPOT_CHECK_ITEMS_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS,
    build_review_queue_spot_check_package_343f,
)
from datefac.benchmark.review_queue_spot_check_package_343f_report import (  # noqa: E402
    ai_assisted_boundary_markdown,
    report_markdown,
    reviewer_instructions_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 343F AI-assisted review spot-check package.")
    parser.add_argument("--apply-simulation-343e-dir", default=str(DEFAULT_APPLY_SIMULATION_343E_DIR))
    parser.add_argument("--excel-ingestion-343d-dir", default=str(DEFAULT_EXCEL_INGESTION_343D_DIR))
    parser.add_argument("--review-queue-schema-343a-dir", default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_spot_check_package_343f(
        apply_simulation_343e_dir=Path(args.apply_simulation_343e_dir),
        excel_ingestion_343d_dir=Path(args.excel_ingestion_343d_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / PRIORITY_PLAN_FILE_NAME, artifacts["priority_plan"])
    write_json(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME, artifacts["expected_import_contract"])
    write_jsonl(output_dir / SPOT_CHECK_ITEMS_FILE_NAME, artifacts["spot_check_items"])
    write_jsonl(output_dir / SOURCE_CHECK_TODO_FILE_NAME, artifacts["source_check_todo"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    write_excel(output_dir / REVIEW_TEMPLATE_FILE_NAME, {"04_REVIEW_TEMPLATE": artifacts["workbook_sheets"]["04_REVIEW_TEMPLATE"]}, ["04_REVIEW_TEMPLATE"])
    (output_dir / REPORT_FILE_NAME).write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")
    (output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME).write_text(reviewer_instructions_markdown(artifacts["summary"]), encoding="utf-8")
    (output_dir / BOUNDARY_FILE_NAME).write_text(ai_assisted_boundary_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"review_queue_spot_check_package_343f_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_review_template_xlsx: {output_dir / REVIEW_TEMPLATE_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_spot_check_items_jsonl: {output_dir / SPOT_CHECK_ITEMS_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_priority_plan_json: {output_dir / PRIORITY_PLAN_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_source_check_todo_jsonl: {output_dir / SOURCE_CHECK_TODO_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_reviewer_instructions_md: {output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_expected_import_contract_json: {output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_ai_assisted_boundary_md: {output_dir / BOUNDARY_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_spot_check_package_343f_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "input_apply_plan_row_count",
        "input_simulated_sidecar_row_count",
        "spot_check_item_count",
        "simulated_applied_spot_check_count",
        "source_check_required_count",
        "skipped_hold_count",
        "priority_tier_count",
        "review_template_generated",
        "source_check_todo_generated",
        "expected_import_contract_generated",
        "review_source_type",
        "not_pure_human_review",
        "strict_human_review_completed",
        "requires_human_spot_check",
        "apply_mode",
        "spot_check_package_generated",
        "waiting_for_spot_check",
        "spot_check_result_ingested",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343g",
        "recommended_343g_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
