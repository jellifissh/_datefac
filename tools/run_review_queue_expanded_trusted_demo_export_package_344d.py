from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_expanded_trusted_demo_export_package_344d import (  # noqa: E402
    AUDIT_LABELS_FILE_NAME,
    DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR,
    DEFAULT_SOURCE_CHECK_SIDECAR_SIMULATION_344C_DIR,
    DEMO_README_FILE_NAME,
    EXPORT_GATE_FILE_NAME,
    EXPORT_ROWS_CSV_FILE_NAME,
    EXPORT_ROWS_JSONL_FILE_NAME,
    HANDOFF_SUMMARY_FILE_NAME,
    LINEAGE_SUMMARY_FILE_NAME,
    MANIFEST_FILE_NAME,
    METRIC_DISTRIBUTION_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_344D,
    build_review_queue_expanded_trusted_demo_export_package_344d,
)
from datefac.benchmark.review_queue_expanded_trusted_demo_export_package_344d_report import (  # noqa: E402
    report_markdown,
    write_csv,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 344D expanded trusted export package generation for review/demo only."
    )
    parser.add_argument(
        "--source-check-sidecar-simulation-344c-dir",
        default=str(DEFAULT_SOURCE_CHECK_SIDECAR_SIMULATION_344C_DIR),
    )
    parser.add_argument(
        "--source-check-ingestion-344b-dir",
        default=str(DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR),
    )
    parser.add_argument(
        "--demo-audit-snapshot-343o-dir",
        default=str(DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR),
    )
    parser.add_argument(
        "--limited-demo-export-package-343n-dir",
        default=str(DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR),
    )
    parser.add_argument(
        "--review-queue-schema-343a-dir",
        default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_expanded_trusted_demo_export_package_344d(
        source_check_sidecar_simulation_344c_dir=Path(args.source_check_sidecar_simulation_344c_dir),
        source_check_ingestion_344b_dir=Path(args.source_check_ingestion_344b_dir),
        demo_audit_snapshot_343o_dir=Path(args.demo_audit_snapshot_343o_dir),
        limited_demo_export_package_343n_dir=Path(args.limited_demo_export_package_343n_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / EXPORT_GATE_FILE_NAME, artifacts["export_gate"])
    write_json(output_dir / LINEAGE_SUMMARY_FILE_NAME, artifacts["lineage_summary"])
    write_json(output_dir / METRIC_DISTRIBUTION_FILE_NAME, artifacts["metric_distribution"])
    write_jsonl(output_dir / EXPORT_ROWS_JSONL_FILE_NAME, artifacts["export_rows"])
    write_csv(output_dir / EXPORT_ROWS_CSV_FILE_NAME, artifacts["export_rows"])
    write_jsonl(output_dir / AUDIT_LABELS_FILE_NAME, artifacts["audit_label_rows"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_344D)
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / DEMO_README_FILE_NAME).write_text(
        artifacts["demo_readme_markdown"],
        encoding="utf-8",
    )
    (output_dir / SCOPE_BOUNDARY_FILE_NAME).write_text(
        artifacts["scope_boundary_markdown"],
        encoding="utf-8",
    )
    (output_dir / HANDOFF_SUMMARY_FILE_NAME).write_text(
        artifacts["handoff_summary_markdown"],
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_expanded_trusted_demo_export_package_344d_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_demo_readme_md: {output_dir / DEMO_README_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_export_rows_jsonl: {output_dir / EXPORT_ROWS_JSONL_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_export_rows_csv: {output_dir / EXPORT_ROWS_CSV_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_audit_labels_jsonl: {output_dir / AUDIT_LABELS_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_export_gate_json: {output_dir / EXPORT_GATE_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_lineage_summary_json: {output_dir / LINEAGE_SUMMARY_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_scope_boundary_md: {output_dir / SCOPE_BOUNDARY_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_handoff_summary_md: {output_dir / HANDOFF_SUMMARY_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_metric_distribution_json: {output_dir / METRIC_DISTRIBUTION_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_expanded_trusted_demo_export_package_344d_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "input_expanded_trusted_candidate_count",
        "expanded_export_row_count",
        "audit_label_row_count",
        "prior_demo_trusted_row_count",
        "source_check_trusted_row_count",
        "source_check_confirmed_row_count",
        "source_check_corrected_row_count",
        "correction_row_count",
        "dedup_conflict_count",
        "expanded_export_scope",
        "export_usage",
        "expanded_review_demo_package_generated",
        "expanded_demo_handoff_ready",
        "expanded_export_gate_generated",
        "lineage_summary_generated",
        "audit_labels_generated",
        "source_check_backlog_resolved",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "global_strict_human_review_completed",
        "ready_for_344e",
        "recommended_344e_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
