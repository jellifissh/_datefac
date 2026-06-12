from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_human_confirmed_sidecar_simulation_343m import (  # noqa: E402
    APPLY_PLAN_FILE_NAME,
    DEFAULT_AUDIT_SUMMARY_343H_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR,
    DEFAULT_PURE_HUMAN_ATTESTATION_PACKAGE_343K_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR,
    LIMITED_EXPORT_CANDIDATE_FILE_NAME,
    LIMITED_EXPORT_GATE_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    REMAINING_BACKLOG_FILE_NAME,
    SIDECAR_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_343M,
    build_review_queue_human_confirmed_sidecar_simulation_343m,
)
from datefac.benchmark.review_queue_human_confirmed_sidecar_simulation_343m_report import (  # noqa: E402
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 343M human-confirmed sidecar apply simulation and limited export gate.")
    parser.add_argument("--pure-human-attestation-ingestion-343l-dir", default=str(DEFAULT_PURE_HUMAN_ATTESTATION_INGESTION_343L_DIR))
    parser.add_argument("--pure-human-attestation-package-343k-dir", default=str(DEFAULT_PURE_HUMAN_ATTESTATION_PACKAGE_343K_DIR))
    parser.add_argument("--source-evidence-enrichment-343i2-dir", default=str(DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR))
    parser.add_argument("--audit-summary-343h-dir", default=str(DEFAULT_AUDIT_SUMMARY_343H_DIR))
    parser.add_argument("--review-queue-schema-343a-dir", default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_human_confirmed_sidecar_simulation_343m(
        pure_human_attestation_ingestion_343l_dir=Path(args.pure_human_attestation_ingestion_343l_dir),
        pure_human_attestation_package_343k_dir=Path(args.pure_human_attestation_package_343k_dir),
        source_evidence_enrichment_343i2_dir=Path(args.source_evidence_enrichment_343i2_dir),
        audit_summary_343h_dir=Path(args.audit_summary_343h_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / LIMITED_EXPORT_GATE_FILE_NAME, artifacts["limited_export_gate"])
    write_jsonl(output_dir / SIDECAR_FILE_NAME, artifacts["sidecar_rows"])
    write_jsonl(output_dir / APPLY_PLAN_FILE_NAME, artifacts["apply_plan_rows"])
    write_jsonl(output_dir / LIMITED_EXPORT_CANDIDATE_FILE_NAME, artifacts["limited_export_candidate_rows"])
    write_jsonl(output_dir / REMAINING_BACKLOG_FILE_NAME, artifacts["remaining_backlog_rows"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_343M)
    (output_dir / REPORT_FILE_NAME).write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")
    (output_dir / SCOPE_BOUNDARY_FILE_NAME).write_text(artifacts["scope_boundary_markdown"], encoding="utf-8")

    summary = artifacts["summary"]
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_sidecar_jsonl: {output_dir / SIDECAR_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_apply_plan_jsonl: {output_dir / APPLY_PLAN_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate_json: {output_dir / LIMITED_EXPORT_GATE_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_limited_export_candidate_jsonl: {output_dir / LIMITED_EXPORT_CANDIDATE_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_remaining_backlog_jsonl: {output_dir / REMAINING_BACKLOG_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_scope_boundary_md: {output_dir / SCOPE_BOUNDARY_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_human_confirmed_sidecar_simulation_343m_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "input_human_attested_row_count",
        "valid_human_attested_row_count",
        "sidecar_row_count",
        "sidecar_human_accept_count",
        "sidecar_human_correct_count",
        "sidecar_blocked_count",
        "limited_export_candidate_row_count",
        "remaining_source_check_backlog_count",
        "package_strict_human_review_completed",
        "strict_human_review_completed_scope",
        "global_strict_human_review_completed",
        "sidecar_apply_simulation_completed",
        "limited_export_gate_evaluated",
        "limited_package_export_candidate_allowed",
        "limited_export_scope",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343n",
        "recommended_343n_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
