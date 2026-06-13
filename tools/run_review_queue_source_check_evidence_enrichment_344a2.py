from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_source_check_evidence_enrichment_344a2 import (  # noqa: E402
    ARTIFACT_SEARCH_REPORT_FILE_NAME,
    DEFAULT_AUDIT_SUMMARY_343H_DIR,
    DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_SEARCH_ROOT,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SOURCE_CHECK_BACKLOG_PACKAGE_344A_DIR,
    DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR,
    DEFAULT_SPOT_CHECK_INGESTION_343G_DIR,
    DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR,
    ENRICHED_BACKLOG_FILE_NAME,
    ENRICHED_REVIEW_TEMPLATE_FILE_NAME,
    EVIDENCE_MAP_FILE_NAME,
    EXPECTED_IMPORT_CONTRACT_FILE_NAME,
    FILL_GUIDE_FILE_NAME,
    MANIFEST_FILE_NAME,
    MATCH_CANDIDATES_FILE_NAME,
    MATCH_CONFIDENCE_AUDIT_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    REVIEWER_INSTRUCTIONS_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SUMMARY_FILE_NAME,
    UNRESOLVED_REPORT_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_344A2,
    build_review_queue_source_check_evidence_enrichment_344a2,
)
from datefac.benchmark.review_queue_source_check_evidence_enrichment_344a2_report import (  # noqa: E402
    artifact_search_report_markdown,
    fill_guide_markdown,
    report_markdown,
    reviewer_instructions_markdown,
    scope_boundary_markdown,
    unresolved_report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)
from datefac.review_queue.source_check_evidence_enrichment_344a2 import (  # noqa: E402
    REVIEW_TEMPLATE_WORKBOOK_SHEETS_344A2,
    build_scope_boundary_lines,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 344A2 source evidence enrichment for source-check backlog."
    )
    parser.add_argument(
        "--source-check-backlog-package-344a-dir",
        default=str(DEFAULT_SOURCE_CHECK_BACKLOG_PACKAGE_344A_DIR),
    )
    parser.add_argument(
        "--demo-audit-snapshot-343o-dir",
        default=str(DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR),
    )
    parser.add_argument("--audit-summary-343h-dir", default=str(DEFAULT_AUDIT_SUMMARY_343H_DIR))
    parser.add_argument(
        "--spot-check-ingestion-343g-dir",
        default=str(DEFAULT_SPOT_CHECK_INGESTION_343G_DIR),
    )
    parser.add_argument(
        "--spot-check-package-343f-dir",
        default=str(DEFAULT_SPOT_CHECK_PACKAGE_343F_DIR),
    )
    parser.add_argument(
        "--source-evidence-enrichment-343i2-dir",
        default=str(DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR),
    )
    parser.add_argument(
        "--review-queue-schema-343a-dir",
        default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR),
    )
    parser.add_argument("--output-search-root", default=str(DEFAULT_OUTPUT_SEARCH_ROOT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_source_check_evidence_enrichment_344a2(
        source_check_backlog_package_344a_dir=Path(args.source_check_backlog_package_344a_dir),
        demo_audit_snapshot_343o_dir=Path(args.demo_audit_snapshot_343o_dir),
        audit_summary_343h_dir=Path(args.audit_summary_343h_dir),
        spot_check_ingestion_343g_dir=Path(args.spot_check_ingestion_343g_dir),
        spot_check_package_343f_dir=Path(args.spot_check_package_343f_dir),
        source_evidence_enrichment_343i2_dir=Path(args.source_evidence_enrichment_343i2_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_search_root=Path(args.output_search_root),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / EVIDENCE_MAP_FILE_NAME, artifacts["resolution_map"])
    write_json(output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME, artifacts["expected_import_contract"])
    write_jsonl(output_dir / ENRICHED_BACKLOG_FILE_NAME, artifacts["enriched_backlog_items"])
    write_jsonl(output_dir / MATCH_CANDIDATES_FILE_NAME, artifacts["match_candidates"])
    write_jsonl(output_dir / MATCH_CONFIDENCE_AUDIT_FILE_NAME, artifacts["match_confidence_rows"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_344A2)
    write_excel(
        output_dir / ENRICHED_REVIEW_TEMPLATE_FILE_NAME,
        artifacts["review_template_sheets"],
        REVIEW_TEMPLATE_WORKBOOK_SHEETS_344A2,
    )
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME).write_text(
        reviewer_instructions_markdown(artifacts["summary"]),
        encoding="utf-8",
    )
    (output_dir / FILL_GUIDE_FILE_NAME).write_text(
        fill_guide_markdown(),
        encoding="utf-8",
    )
    (output_dir / UNRESOLVED_REPORT_FILE_NAME).write_text(
        unresolved_report_markdown(artifacts["summary"], artifacts["unresolved_rows"]),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_SEARCH_REPORT_FILE_NAME).write_text(
        artifact_search_report_markdown(
            artifacts["searched_artifacts"],
            artifacts["summary"].get("match_candidate_count", 0),
        ),
        encoding="utf-8",
    )
    (output_dir / SCOPE_BOUNDARY_FILE_NAME).write_text(
        scope_boundary_markdown(build_scope_boundary_lines()),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_source_check_evidence_enrichment_344a2_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_enriched_backlog_items_jsonl: {output_dir / ENRICHED_BACKLOG_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_evidence_match_candidates_jsonl: {output_dir / MATCH_CANDIDATES_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_match_confidence_audit_jsonl: {output_dir / MATCH_CONFIDENCE_AUDIT_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_evidence_map_json: {output_dir / EVIDENCE_MAP_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_expected_import_contract_json: {output_dir / EXPECTED_IMPORT_CONTRACT_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_enriched_review_template_xlsx: {output_dir / ENRICHED_REVIEW_TEMPLATE_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_reviewer_instructions_md: {output_dir / REVIEWER_INSTRUCTIONS_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_fill_guide_md: {output_dir / FILL_GUIDE_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_unresolved_evidence_report_md: {output_dir / UNRESOLVED_REPORT_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_artifact_search_report_md: {output_dir / ARTIFACT_SEARCH_REPORT_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_scope_boundary_md: {output_dir / SCOPE_BOUNDARY_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_source_check_evidence_enrichment_344a2_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "input_source_check_backlog_item_count",
        "deduplicated_backlog_item_count",
        "evidence_resolved_count",
        "evidence_partial_count",
        "evidence_unresolved_count",
        "source_pdf_name_available_count",
        "page_number_available_count",
        "image_path_available_count",
        "source_text_snippet_available_count",
        "match_candidate_count",
        "high_confidence_match_count",
        "medium_confidence_match_count",
        "low_confidence_match_count",
        "auto_enriched_item_count",
        "unresolved_item_count",
        "source_check_evidence_enrichment_completed",
        "enriched_review_template_generated",
        "expected_import_contract_generated",
        "waiting_for_source_check_review",
        "source_check_result_ingested",
        "source_check_backlog_resolved",
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

