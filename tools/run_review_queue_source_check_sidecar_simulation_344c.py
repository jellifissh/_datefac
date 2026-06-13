from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_source_check_sidecar_simulation_344c import (  # noqa: E402
    CORRECTIONS_APPLIED_FILE_NAME,
    DEDUP_AUDIT_FILE_NAME,
    DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR,
    DEFAULT_LIMITED_DEMO_EXPORT_PACKAGE_343N_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR,
    DEFAULT_SOURCE_CHECK_INGESTION_344B_DIR,
    EXPANDED_TRUST_GATE_FILE_NAME,
    EXPANDED_TRUST_SUMMARY_FILE_NAME,
    EXPANDED_TRUSTED_CANDIDATES_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_ACTION_PLAN_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SOURCE_CHECK_APPLIED_SIDECAR_FILE_NAME,
    SOURCE_CHECK_APPLY_PLAN_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_344C,
    build_review_queue_source_check_sidecar_simulation_344c,
)
from datefac.benchmark.review_queue_source_check_sidecar_simulation_344c_report import (  # noqa: E402
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 344C source-check sidecar apply simulation and expanded trust gate."
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
        "--human-confirmed-sidecar-simulation-343m-dir",
        default=str(DEFAULT_HUMAN_CONFIRMED_SIDECAR_SIMULATION_343M_DIR),
    )
    parser.add_argument(
        "--pure-human-attestation-ingestion-343l-dir",
        default=str(DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR),
    )
    parser.add_argument(
        "--review-queue-schema-343a-dir",
        default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_source_check_sidecar_simulation_344c(
        source_check_ingestion_344b_dir=Path(args.source_check_ingestion_344b_dir),
        source_check_evidence_enrichment_344a2_dir=Path(
            args.source_check_evidence_enrichment_344a2_dir
        ),
        demo_audit_snapshot_343o_dir=Path(args.demo_audit_snapshot_343o_dir),
        limited_demo_export_package_343n_dir=Path(
            args.limited_demo_export_package_343n_dir
        ),
        human_confirmed_sidecar_simulation_343m_dir=Path(
            args.human_confirmed_sidecar_simulation_343m_dir
        ),
        pure_human_attestation_ingestion_343l_dir=Path(
            args.pure_human_attestation_ingestion_343l_dir
        ),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / EXPANDED_TRUST_GATE_FILE_NAME, artifacts["expanded_trust_gate"])
    write_json(output_dir / NEXT_ACTION_PLAN_FILE_NAME, artifacts["next_action_plan"])
    write_jsonl(output_dir / SOURCE_CHECK_APPLY_PLAN_FILE_NAME, artifacts["source_check_apply_plan_rows"])
    write_jsonl(output_dir / SOURCE_CHECK_APPLIED_SIDECAR_FILE_NAME, artifacts["source_check_applied_sidecar_rows"])
    write_jsonl(output_dir / EXPANDED_TRUSTED_CANDIDATES_FILE_NAME, artifacts["expanded_trusted_candidate_rows"])
    write_jsonl(output_dir / CORRECTIONS_APPLIED_FILE_NAME, artifacts["corrections_applied_rows"])
    write_jsonl(output_dir / DEDUP_AUDIT_FILE_NAME, artifacts["dedup_audit_rows"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_344C)
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / SCOPE_BOUNDARY_FILE_NAME).write_text(
        artifacts["scope_boundary_markdown"],
        encoding="utf-8",
    )
    (output_dir / EXPANDED_TRUST_SUMMARY_FILE_NAME).write_text(
        artifacts["expanded_trust_summary_markdown"],
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_source_check_sidecar_simulation_344c_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_source_check_apply_plan_jsonl: {output_dir / SOURCE_CHECK_APPLY_PLAN_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_source_check_applied_sidecar_jsonl: {output_dir / SOURCE_CHECK_APPLIED_SIDECAR_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_expanded_trusted_candidates_jsonl: {output_dir / EXPANDED_TRUSTED_CANDIDATES_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_corrections_applied_jsonl: {output_dir / CORRECTIONS_APPLIED_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_dedup_audit_jsonl: {output_dir / DEDUP_AUDIT_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_expanded_trust_gate_json: {output_dir / EXPANDED_TRUST_GATE_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_scope_boundary_md: {output_dir / SCOPE_BOUNDARY_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_expanded_trust_summary_md: {output_dir / EXPANDED_TRUST_SUMMARY_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_next_action_plan_json: {output_dir / NEXT_ACTION_PLAN_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_source_check_sidecar_simulation_344c_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "source_check_input_sidecar_row_count",
        "source_check_apply_plan_row_count",
        "source_check_apply_confirm_count",
        "source_check_apply_correct_count",
        "source_check_apply_blocked_count",
        "source_check_applied_sidecar_row_count",
        "corrections_applied_count",
        "prior_demo_trusted_row_count",
        "source_check_trusted_row_count",
        "expanded_trusted_candidate_count",
        "deduplicated_expanded_trusted_candidate_count",
        "dedup_conflict_count",
        "expanded_trusted_scope",
        "source_check_sidecar_apply_simulation_completed",
        "expanded_trust_gate_evaluated",
        "source_check_backlog_resolved",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "global_strict_human_review_completed",
        "ready_for_344d",
        "recommended_344d_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

