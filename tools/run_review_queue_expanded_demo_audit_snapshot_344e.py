from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_expanded_demo_audit_snapshot_344e import (  # noqa: E402
    ARTIFACT_INDEX_JSON_FILE_NAME,
    DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    DEFAULT_EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_DIR,
    DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR,
    DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR,
    DEFAULT_SOURCE_CHECK_SIDECAR_SIMULATION_344C_DIR,
    EXECUTIVE_SUMMARY_FILE_NAME,
    FINAL_EXPORT_GATE_SNAPSHOT_FILE_NAME,
    FINAL_HANDOFF_SUMMARY_FILE_NAME,
    LINEAGE_AUDIT_SUMMARY_FILE_NAME,
    MANIFEST_FILE_NAME,
    METRIC_DISTRIBUTION_FILE_NAME,
    NEXT_ACTION_PLAN_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SUMMARY_FILE_NAME,
    TRUST_CHAIN_REPORT_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_344E,
    build_review_queue_expanded_demo_audit_snapshot_344e,
)
from datefac.benchmark.review_queue_expanded_demo_audit_snapshot_344e_report import (  # noqa: E402
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 344E expanded trusted demo audit snapshot and final handoff summary."
    )
    parser.add_argument(
        "--expanded-trusted-demo-export-package-344d-dir",
        default=str(DEFAULT_EXPANDED_TRUSTED_DEMO_EXPORT_PACKAGE_344D_DIR),
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
        "--source-check-evidence-enrichment-344a2-dir",
        default=str(DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR),
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

    artifacts = build_review_queue_expanded_demo_audit_snapshot_344e(
        expanded_trusted_demo_export_package_344d_dir=Path(args.expanded_trusted_demo_export_package_344d_dir),
        source_check_sidecar_simulation_344c_dir=Path(args.source_check_sidecar_simulation_344c_dir),
        source_check_ingestion_344b_dir=Path(args.source_check_ingestion_344b_dir),
        source_check_evidence_enrichment_344a2_dir=Path(args.source_check_evidence_enrichment_344a2_dir),
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
    write_json(output_dir / FINAL_EXPORT_GATE_SNAPSHOT_FILE_NAME, artifacts["final_export_gate_snapshot"])
    write_json(output_dir / ARTIFACT_INDEX_JSON_FILE_NAME, artifacts["artifact_index_rows"])
    write_json(output_dir / LINEAGE_AUDIT_SUMMARY_FILE_NAME, artifacts["lineage_audit_summary"])
    write_json(output_dir / METRIC_DISTRIBUTION_FILE_NAME, artifacts["metric_distribution"])
    write_json(output_dir / NEXT_ACTION_PLAN_FILE_NAME, artifacts["next_action_plan"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_344E)
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / FINAL_HANDOFF_SUMMARY_FILE_NAME).write_text(
        artifacts["final_handoff_summary_markdown"],
        encoding="utf-8",
    )
    (output_dir / EXECUTIVE_SUMMARY_FILE_NAME).write_text(
        artifacts["executive_summary_markdown"],
        encoding="utf-8",
    )
    (output_dir / TRUST_CHAIN_REPORT_FILE_NAME).write_text(
        artifacts["trust_chain_markdown"],
        encoding="utf-8",
    )
    (output_dir / SCOPE_BOUNDARY_FILE_NAME).write_text(
        artifacts["scope_boundary_markdown"],
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_JSON_FILE_NAME.replace(".json", ".md")).write_text(
        artifacts["artifact_index_markdown"],
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_expanded_demo_audit_snapshot_344e_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_final_handoff_summary_md: {output_dir / FINAL_HANDOFF_SUMMARY_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_executive_summary_md: {output_dir / EXECUTIVE_SUMMARY_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_trust_chain_report_md: {output_dir / TRUST_CHAIN_REPORT_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_scope_boundary_md: {output_dir / SCOPE_BOUNDARY_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_artifact_index_json: {output_dir / ARTIFACT_INDEX_JSON_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_artifact_index_md: {output_dir / ARTIFACT_INDEX_JSON_FILE_NAME.replace('.json', '.md')}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_final_export_gate_snapshot_json: {output_dir / FINAL_EXPORT_GATE_SNAPSHOT_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_lineage_audit_summary_json: {output_dir / LINEAGE_AUDIT_SUMMARY_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_metric_distribution_json: {output_dir / METRIC_DISTRIBUTION_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_next_action_plan_json: {output_dir / NEXT_ACTION_PLAN_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_expanded_demo_audit_snapshot_344e_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "input_expanded_export_row_count",
        "audit_label_row_count",
        "prior_demo_trusted_row_count",
        "source_check_trusted_row_count",
        "source_check_confirmed_row_count",
        "source_check_corrected_row_count",
        "correction_row_count",
        "expanded_export_scope",
        "export_usage",
        "expanded_demo_audit_snapshot_generated",
        "final_handoff_summary_generated",
        "executive_summary_generated",
        "trust_chain_report_generated",
        "artifact_index_generated",
        "final_export_gate_snapshot_generated",
        "lineage_audit_summary_generated",
        "metric_distribution_generated",
        "expanded_demo_arc_closed",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "global_strict_human_review_completed",
        "ready_for_345a",
        "recommended_345a_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
