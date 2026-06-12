from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_source_evidence_enrichment_343i2 import (  # noqa: E402
    DEFAULT_APPLY_SIMULATION_343E_DIR,
    DEFAULT_AUDIT_SUMMARY_343H_DIR,
    DEFAULT_EXCEL_INGESTION_343D_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SPOT_CHECK_INGESTION_343G_DIR,
    DEFAULT_STRICT_HUMAN_REVIEW_PACKAGE_343I_DIR,
    ENRICHED_ITEMS_FILE_NAME,
    ENRICHED_REVIEW_TEMPLATE_FILE_NAME,
    EVIDENCE_GAP_REPORT_FILE_NAME,
    EVIDENCE_RESOLUTION_MAP_FILE_NAME,
    EXPECTED_IMPORT_CONTRACT_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    SUMMARY_FILE_NAME,
    UNRESOLVED_ITEMS_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_343I2,
    build_review_queue_source_evidence_enrichment_343i2,
)
from datefac.benchmark.review_queue_source_evidence_enrichment_343i2_report import (  # noqa: E402
    evidence_gap_report_markdown,
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 343I2 source evidence enrichment for strict human review package."
    )
    parser.add_argument(
        "--strict-human-review-package-343i-dir",
        default=str(DEFAULT_STRICT_HUMAN_REVIEW_PACKAGE_343I_DIR),
    )
    parser.add_argument("--audit-summary-343h-dir", default=str(DEFAULT_AUDIT_SUMMARY_343H_DIR))
    parser.add_argument(
        "--spot-check-ingestion-343g-dir",
        default=str(DEFAULT_SPOT_CHECK_INGESTION_343G_DIR),
    )
    parser.add_argument(
        "--apply-simulation-343e-dir",
        default=str(DEFAULT_APPLY_SIMULATION_343E_DIR),
    )
    parser.add_argument(
        "--excel-ingestion-343d-dir",
        default=str(DEFAULT_EXCEL_INGESTION_343D_DIR),
    )
    parser.add_argument(
        "--review-queue-schema-343a-dir",
        default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_source_evidence_enrichment_343i2(
        strict_human_review_package_343i_dir=Path(args.strict_human_review_package_343i_dir),
        audit_summary_343h_dir=Path(args.audit_summary_343h_dir),
        spot_check_ingestion_343g_dir=Path(args.spot_check_ingestion_343g_dir),
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
    write_json(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME, artifacts["expected_import_contract"])
    write_json(output_dir / EVIDENCE_RESOLUTION_MAP_FILE_NAME, artifacts["resolution_map_payload"])
    write_jsonl(output_dir / ENRICHED_ITEMS_FILE_NAME, artifacts["enriched_items"])
    write_jsonl(output_dir / UNRESOLVED_ITEMS_FILE_NAME, artifacts["unresolved_items"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_343I2)
    write_excel(
        output_dir / ENRICHED_REVIEW_TEMPLATE_FILE_NAME,
        artifacts["review_template_sheets"],
        ["04_REVIEW_TEMPLATE"],
    )
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / EVIDENCE_GAP_REPORT_FILE_NAME).write_text(
        evidence_gap_report_markdown(artifacts["summary"], artifacts["unresolved_items"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_source_evidence_enrichment_343i2_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_enriched_items_jsonl: {output_dir / ENRICHED_ITEMS_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_unresolved_evidence_items_jsonl: {output_dir / UNRESOLVED_ITEMS_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_evidence_resolution_map_json: {output_dir / EVIDENCE_RESOLUTION_MAP_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_expected_import_contract_json: {output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_enriched_review_template_xlsx: {output_dir / ENRICHED_REVIEW_TEMPLATE_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_evidence_gap_report_md: {output_dir / EVIDENCE_GAP_REPORT_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_source_evidence_enrichment_343i2_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "input_strict_review_item_count",
        "enriched_review_item_count",
        "evidence_resolved_count",
        "evidence_partial_count",
        "evidence_unresolved_count",
        "source_pdf_name_available_count",
        "source_pdf_path_available_count",
        "page_number_available_count",
        "source_text_snippet_available_count",
        "image_path_available_count",
        "enriched_review_template_generated",
        "evidence_gap_report_generated",
        "expected_import_contract_generated",
        "source_evidence_enrichment_completed",
        "waiting_for_strict_human_review",
        "strict_human_review_result_ingested",
        "strict_human_review_completed",
        "requires_strict_human_review",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343j",
        "recommended_343j_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
