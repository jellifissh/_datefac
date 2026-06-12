from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_audit_summary_343h import (  # noqa: E402
    AUDIT_MATRIX_FILE_NAME,
    CLIENT_EXPORT_GATE_FILE_NAME,
    CONFIRMED_ITEMS_FILE_NAME,
    DEFAULT_APPLY_SIMULATION_343E_DIR,
    DEFAULT_EXCEL_INGESTION_343D_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SPOT_CHECK_INGESTION_343G_DIR,
    DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR,
    GAP_ITEMS_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_ACTION_PLAN_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    SOURCE_CHECK_BACKLOG_FILE_NAME,
    STRICT_GAP_REPORT_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS,
    build_review_queue_audit_summary_343h,
)
from datefac.benchmark.review_queue_audit_summary_343h_report import (  # noqa: E402
    report_markdown,
    strict_human_gap_report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 343H AI-assisted spot-check audit summary.")
    parser.add_argument("--spot-check-ingestion-343g-dir", default=str(DEFAULT_SPOT_CHECK_INGESTION_343G_DIR))
    parser.add_argument("--spot-check-package-343f-dir", default=str(DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR))
    parser.add_argument("--apply-simulation-343e-dir", default=str(DEFAULT_APPLY_SIMULATION_343E_DIR))
    parser.add_argument("--excel-ingestion-343d-dir", default=str(DEFAULT_EXCEL_INGESTION_343D_DIR))
    parser.add_argument("--review-queue-schema-343a-dir", default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_audit_summary_343h(
        spot_check_ingestion_343g_dir=Path(args.spot_check_ingestion_343g_dir),
        spot_check_package_343f_dir=Path(args.spot_check_package_343f_dir),
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
    write_json(output_dir / AUDIT_MATRIX_FILE_NAME, artifacts["audit_matrix"])
    write_json(output_dir / CLIENT_EXPORT_GATE_FILE_NAME, artifacts["client_export_gate"])
    write_json(output_dir / NEXT_ACTION_PLAN_FILE_NAME, artifacts["next_action_plan"])
    write_jsonl(output_dir / GAP_ITEMS_FILE_NAME, artifacts["gap_items"])
    write_jsonl(output_dir / CONFIRMED_ITEMS_FILE_NAME, artifacts["confirmed_items"])
    write_jsonl(output_dir / SOURCE_CHECK_BACKLOG_FILE_NAME, artifacts["source_check_backlog"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    (output_dir / REPORT_FILE_NAME).write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")
    (output_dir / STRICT_GAP_REPORT_FILE_NAME).write_text(
        strict_human_gap_report_markdown(
            artifacts["summary"],
            confirmed_count=len(artifacts["confirmed_items"]),
            source_check_count=len(artifacts["source_check_backlog"]),
            keep_hold_count=artifacts["summary"].get("keep_hold_count", 0),
        ),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_audit_summary_343h_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_audit_matrix_json: {output_dir / AUDIT_MATRIX_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_gap_items_jsonl: {output_dir / GAP_ITEMS_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_confirmed_ai_assisted_items_jsonl: {output_dir / CONFIRMED_ITEMS_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_source_check_backlog_jsonl: {output_dir / SOURCE_CHECK_BACKLOG_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_client_export_gate_json: {output_dir / CLIENT_EXPORT_GATE_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_next_action_plan_json: {output_dir / NEXT_ACTION_PLAN_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_strict_human_gap_report_md: {output_dir / STRICT_GAP_REPORT_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_audit_summary_343h_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "input_spot_check_result_row_count",
        "ai_assisted_confirmed_count",
        "source_check_required_count",
        "keep_hold_count",
        "strict_human_gap_item_count",
        "source_check_backlog_count",
        "audit_stage_count",
        "audit_summary_generated",
        "strict_human_gap_report_generated",
        "client_export_gate_generated",
        "next_action_plan_generated",
        "review_source_type",
        "spot_check_source_type",
        "not_pure_human_review",
        "strict_human_review_completed",
        "requires_strict_human_review",
        "apply_mode",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343i",
        "recommended_343i_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
