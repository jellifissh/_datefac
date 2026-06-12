from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_demo_audit_snapshot_343o import (  # noqa: E402
    ARTIFACT_INDEX_JSON_FILE_NAME,
    ARTIFACT_INDEX_MD_FILE_NAME,
    BACKLOG_SUMMARY_FILE_NAME,
    DEFAULT_AUDIT_SUMMARY_343H_DIR,
    DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR,
    DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    EXECUTIVE_SUMMARY_FILE_NAME,
    EXPORT_GATE_SNAPSHOT_FILE_NAME,
    HANDOFF_SUMMARY_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_ACTION_PLAN_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SUMMARY_FILE_NAME,
    TRUST_CHAIN_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_343O,
    build_review_queue_demo_audit_snapshot_343o,
)
from datefac.benchmark.review_queue_demo_audit_snapshot_343o_report import (  # noqa: E402
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 343O demo package audit snapshot and handoff summary.")
    parser.add_argument("--limited-demo-export-package-343n-dir", default=str(DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR))
    parser.add_argument("--human-confirmed-sidecar-simulation-343m-dir", default=str(DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR))
    parser.add_argument("--pure-human-attestation-ingestion-343l-dir", default=str(DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR))
    parser.add_argument("--audit-summary-343h-dir", default=str(DEFAULT_AUDIT_SUMMARY_343H_DIR))
    parser.add_argument("--review-queue-schema-343a-dir", default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_demo_audit_snapshot_343o(
        limited_demo_export_package_343n_dir=Path(args.limited_demo_export_package_343n_dir),
        human_confirmed_sidecar_simulation_343m_dir=Path(args.human_confirmed_sidecar_simulation_343m_dir),
        pure_human_attestation_ingestion_343l_dir=Path(args.pure_human_attestation_ingestion_343l_dir),
        audit_summary_343h_dir=Path(args.audit_summary_343h_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / EXPORT_GATE_SNAPSHOT_FILE_NAME, artifacts["export_gate_snapshot"])
    write_json(output_dir / ARTIFACT_INDEX_JSON_FILE_NAME, artifacts["artifact_index_rows"])
    write_json(output_dir / BACKLOG_SUMMARY_FILE_NAME, artifacts["backlog_summary"])
    write_json(output_dir / NEXT_ACTION_PLAN_FILE_NAME, artifacts["next_action_plan"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_343O)
    (output_dir / REPORT_FILE_NAME).write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")
    (output_dir / HANDOFF_SUMMARY_FILE_NAME).write_text(artifacts["handoff_summary_markdown"], encoding="utf-8")
    (output_dir / EXECUTIVE_SUMMARY_FILE_NAME).write_text(artifacts["executive_summary_markdown"], encoding="utf-8")
    (output_dir / TRUST_CHAIN_FILE_NAME).write_text(artifacts["trust_chain_markdown"], encoding="utf-8")
    (output_dir / SCOPE_BOUNDARY_FILE_NAME).write_text(artifacts["scope_boundary_markdown"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_markdown"], encoding="utf-8")

    summary = artifacts["summary"]
    print(f"review_queue_demo_audit_snapshot_343o_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_handoff_summary_md: {output_dir / HANDOFF_SUMMARY_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_executive_summary_md: {output_dir / EXECUTIVE_SUMMARY_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_trust_chain_md: {output_dir / TRUST_CHAIN_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_scope_boundary_md: {output_dir / SCOPE_BOUNDARY_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_export_gate_snapshot_json: {output_dir / EXPORT_GATE_SNAPSHOT_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_artifact_index_json: {output_dir / ARTIFACT_INDEX_JSON_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_artifact_index_md: {output_dir / ARTIFACT_INDEX_MD_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_backlog_summary_json: {output_dir / BACKLOG_SUMMARY_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_next_action_plan_json: {output_dir / NEXT_ACTION_PLAN_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_demo_audit_snapshot_343o_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "input_demo_export_row_count",
        "audit_label_row_count",
        "limited_export_scope",
        "export_usage",
        "remaining_source_check_backlog_count",
        "package_strict_human_review_completed",
        "global_strict_human_review_completed",
        "demo_only_export_package_generated",
        "demo_handoff_ready",
        "demo_audit_snapshot_generated",
        "handoff_summary_generated",
        "executive_summary_generated",
        "trust_chain_generated",
        "artifact_index_generated",
        "export_gate_snapshot_generated",
        "demo_arc_closed",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_344a",
        "recommended_344a_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
