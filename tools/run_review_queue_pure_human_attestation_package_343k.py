from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_pure_human_attestation_package_343k import (  # noqa: E402
    ATTESTATION_ITEMS_FILE_NAME,
    ATTESTATION_TEMPLATE_FILE_NAME,
    CLIENT_EXPORT_BOUNDARY_FILE_NAME,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR,
    DEFAULT_STRICT_REVIEW_INGESTION_343J_DIR,
    EXPECTED_IMPORT_CONTRACT_FILE_NAME,
    FILL_GUIDE_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    REVIEWER_INSTRUCTIONS_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_343K,
    build_review_queue_pure_human_attestation_package_343k,
)
from datefac.benchmark.review_queue_pure_human_attestation_package_343k_report import (  # noqa: E402
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 343K pure human confirmation attestation package generation."
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
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_pure_human_attestation_package_343k(
        strict_review_ingestion_343j_dir=Path(args.strict_review_ingestion_343j_dir),
        source_evidence_enrichment_343i2_dir=Path(
            args.source_evidence_enrichment_343i2_dir
        ),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(
        output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME,
        artifacts["expected_import_contract"],
    )
    write_jsonl(output_dir / ATTESTATION_ITEMS_FILE_NAME, artifacts["attestation_items"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_343K)
    write_excel(
        output_dir / ATTESTATION_TEMPLATE_FILE_NAME,
        artifacts["attestation_template_sheets"],
        ["04_ATTESTATION_TEMPLATE"],
    )
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME).write_text(
        artifacts["reviewer_instructions_markdown"],
        encoding="utf-8",
    )
    (output_dir / FILL_GUIDE_FILE_NAME).write_text(
        artifacts["fill_guide_markdown"],
        encoding="utf-8",
    )
    (output_dir / CLIENT_EXPORT_BOUNDARY_FILE_NAME).write_text(
        artifacts["client_export_boundary_markdown"],
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_pure_human_attestation_package_343k_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_workbook_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_attestation_template_xlsx: {output_dir / ATTESTATION_TEMPLATE_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_attestation_items_jsonl: {output_dir / ATTESTATION_ITEMS_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_reviewer_instructions_md: {output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_fill_guide_md: {output_dir / FILL_GUIDE_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_expected_import_contract_json: {output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME}")
    print(f"review_queue_pure_human_attestation_package_343k_client_export_boundary_md: {output_dir / CLIENT_EXPORT_BOUNDARY_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "input_ai_assisted_strict_review_confirm_count",
        "attestation_item_count",
        "evidence_resolved_count",
        "source_pdf_name_available_count",
        "source_text_snippet_available_count",
        "pure_human_attestation_package_generated",
        "attestation_template_generated",
        "reviewer_instructions_generated",
        "fill_guide_generated",
        "expected_import_contract_generated",
        "waiting_for_pure_human_attestation",
        "pure_human_attestation_result_ingested",
        "pure_strict_human_confirm_count",
        "ai_assisted_strict_review_confirm_count",
        "pure_strict_human_review_completed",
        "strict_human_review_completed",
        "requires_pure_human_confirmation",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343l",
        "recommended_343l_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
