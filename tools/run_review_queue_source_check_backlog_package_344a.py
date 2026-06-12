from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_source_check_backlog_package_344a import (  # noqa: E402
    BACKLOG_ITEMS_FILE_NAME,
    DEFAULT_AUDIT_SUMMARY_343H_DIR,
    DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR,
    DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SPOT_CHECK_INGESTION_343G_DIR,
    DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR,
    EVIDENCE_MAP_FILE_NAME,
    EXPECTED_IMPORT_CONTRACT_FILE_NAME,
    FILL_GUIDE_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    PRIORITY_PLAN_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    REVIEWER_INSTRUCTIONS_FILE_NAME,
    REVIEW_TEMPLATE_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SUMMARY_FILE_NAME,
    TEMPLATE_WORKBOOK_SHEETS_344A,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_344A,
    build_review_queue_source_check_backlog_package_344a,
)
from datefac.benchmark.review_queue_source_check_backlog_package_344a_report import (  # noqa: E402
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 344A source-check backlog resolution package.")
    parser.add_argument("--demo-audit-snapshot-343o-dir", default=str(DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR))
    parser.add_argument("--limited-demo-export-package-343n-dir", default=str(DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR))
    parser.add_argument("--human-confirmed-sidecar-simulation-343m-dir", default=str(DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR))
    parser.add_argument("--audit-summary-343h-dir", default=str(DEFAULT_AUDIT_SUMMARY_343H_DIR))
    parser.add_argument("--spot-check-ingestion-343g-dir", default=str(DEFAULT_SPOT_CHECK_INGESTION_343G_DIR))
    parser.add_argument("--spot-check-package-343f-dir", default=str(DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR))
    parser.add_argument("--review-queue-schema-343a-dir", default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_source_check_backlog_package_344a(
        demo_audit_snapshot_343o_dir=Path(args.demo_audit_snapshot_343o_dir),
        limited_demo_export_package_343n_dir=Path(args.limited_demo_export_package_343n_dir),
        human_confirmed_sidecar_simulation_343m_dir=Path(args.human_confirmed_sidecar_simulation_343m_dir),
        audit_summary_343h_dir=Path(args.audit_summary_343h_dir),
        spot_check_ingestion_343g_dir=Path(args.spot_check_ingestion_343g_dir),
        spot_check_package_343f_dir=Path(args.spot_check_package_343f_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / EVIDENCE_MAP_FILE_NAME, artifacts["evidence_map"])
    write_json(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME, artifacts["expected_import_contract"])
    write_json(output_dir / PRIORITY_PLAN_FILE_NAME, artifacts["manifest"].get("source_counts", {}))
    write_jsonl(output_dir / BACKLOG_ITEMS_FILE_NAME, artifacts["backlog_items"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_344A)
    write_excel(output_dir / REVIEW_TEMPLATE_FILE_NAME, artifacts["template_workbook_sheets"], TEMPLATE_WORKBOOK_SHEETS_344A)
    (output_dir / REPORT_FILE_NAME).write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")
    (output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME).write_text(artifacts["reviewer_instructions_markdown"], encoding="utf-8")
    (output_dir / FILL_GUIDE_FILE_NAME).write_text(artifacts["fill_guide_markdown"], encoding="utf-8")
    (output_dir / SCOPE_BOUNDARY_FILE_NAME).write_text(artifacts["scope_boundary_markdown"], encoding="utf-8")

    summary = artifacts["summary"]
    print(f"review_queue_source_check_backlog_package_344a_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_review_template_xlsx: {output_dir / REVIEW_TEMPLATE_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_backlog_items_jsonl: {output_dir / BACKLOG_ITEMS_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_evidence_map_json: {output_dir / EVIDENCE_MAP_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_reviewer_instructions_md: {output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_fill_guide_md: {output_dir / FILL_GUIDE_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_expected_import_contract_json: {output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_scope_boundary_md: {output_dir / SCOPE_BOUNDARY_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_source_check_backlog_package_344a_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "input_remaining_source_check_backlog_count",
        "source_check_backlog_item_count",
        "deduplicated_backlog_item_count",
        "evidence_resolved_count",
        "evidence_partial_count",
        "evidence_unresolved_count",
        "source_pdf_name_available_count",
        "source_text_snippet_available_count",
        "source_check_backlog_package_generated",
        "review_template_generated",
        "reviewer_instructions_generated",
        "fill_guide_generated",
        "expected_import_contract_generated",
        "waiting_for_source_check_review",
        "source_check_result_ingested",
        "source_check_backlog_resolved",
        "demo_arc_closed",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_344b",
        "recommended_344b_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
