from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_pure_human_attestation_ingestion_343l import (  # noqa: E402
    CLIENT_EXPORT_GATE_FILE_NAME,
    DECISION_SUMMARY_FILE_NAME,
    DEFAULT_FILLED_WORKBOOK,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PURE_HUMAN_ATTESTATION_PACKAGE_343K_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR,
    DEFAULT_STRICT_REVIEW_INGESTION_343J_DIR,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    RESULT_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SUMMARY_FILE_NAME,
    VALIDATION_ERRORS_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_343L,
    build_review_queue_pure_human_attestation_ingestion_343l,
)
from datefac.benchmark.review_queue_pure_human_attestation_ingestion_343l_report import (  # noqa: E402
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 343L pure human attestation result ingestion."
    )
    parser.add_argument(
        "--pure-human-attestation-package-343k-dir",
        default=str(DEFAULT_PURE_HUMAN_ATTESTATION_PACKAGE_343K_DIR),
    )
    parser.add_argument(
        "--strict-review-ingestion-343j-dir",
        default=str(DEFAULT_STRICT_REVIEW_INGESTION_343J_DIR),
    )
    parser.add_argument(
        "--source-evidence-enrichment-343i2-dir",
        default=str(DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR),
    )
    parser.add_argument(
        "--review-queue-schema-343a-dir",
        default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR),
    )
    parser.add_argument("--filled-workbook", default=str(DEFAULT_FILLED_WORKBOOK))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_pure_human_attestation_ingestion_343l(
        pure_human_attestation_package_343k_dir=Path(
            args.pure_human_attestation_package_343k_dir
        ),
        strict_review_ingestion_343j_dir=Path(args.strict_review_ingestion_343j_dir),
        source_evidence_enrichment_343i2_dir=Path(
            args.source_evidence_enrichment_343i2_dir
        ),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        filled_workbook=Path(args.filled_workbook),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / DECISION_SUMMARY_FILE_NAME, artifacts["decision_summary"])
    write_json(output_dir / CLIENT_EXPORT_GATE_FILE_NAME, artifacts["client_export_gate"])
    write_json(output_dir / VALIDATION_ERRORS_FILE_NAME, artifacts["validation_errors"])
    write_jsonl(output_dir / RESULT_FILE_NAME, artifacts["result_rows"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_343L)
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / SCOPE_BOUNDARY_FILE_NAME).write_text(
        artifacts["scope_boundary_markdown"],
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_pure_human_attestation_ingestion_343l_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_result_jsonl: {output_dir / RESULT_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_validation_errors_json: {output_dir / VALIDATION_ERRORS_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_decision_summary_json: {output_dir / DECISION_SUMMARY_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_client_export_gate_json: {output_dir / CLIENT_EXPORT_GATE_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_scope_boundary_md: {output_dir / SCOPE_BOUNDARY_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_ingestion_343l_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "filled_workbook_path",
        "filled_row_count",
        "valid_row_count",
        "invalid_row_count",
        "human_accept_count",
        "human_correct_count",
        "human_reject_count",
        "human_needs_source_check_count",
        "human_defer_count",
        "human_source_evidence_checked_true_count",
        "human_independent_check_attested_true_count",
        "pure_human_attestation_result_ingested",
        "pure_strict_human_confirm_count",
        "pure_strict_human_correct_count",
        "pure_strict_human_review_completed_for_package",
        "strict_human_review_completed_scope",
        "global_strict_human_review_completed",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343m",
        "recommended_343m_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
