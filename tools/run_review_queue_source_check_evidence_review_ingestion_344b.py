from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_source_check_evidence_review_ingestion_344b import (  # noqa: E402
    AUDIT_GATE_FILE_NAME,
    CORRECTIONS_FILE_NAME,
    DECISION_SUMMARY_FILE_NAME,
    DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR,
    DEFAULT_FILLED_WORKBOOK,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    DEFAULT_SOURCE_CHECK_BACKLOG_PACKAGE_344A_DIR,
    DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    RESULT_FILE_NAME,
    SCOPE_BOUNDARY_FILE_NAME,
    SUMMARY_FILE_NAME,
    VALIDATED_SIDECAR_FILE_NAME,
    VALIDATION_ERRORS_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS_344B,
    build_review_queue_source_check_evidence_review_ingestion_344b,
)
from datefac.benchmark.review_queue_source_check_evidence_review_ingestion_344b_report import (  # noqa: E402
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _resolve_filled_workbook(filled_workbook: str | None, source_dir: Path) -> Path:
    if filled_workbook:
        return Path(filled_workbook)
    candidates = sorted(source_dir.glob("*.xlsx"))
    if len(candidates) == 1:
        return candidates[0]
    if DEFAULT_FILLED_WORKBOOK.exists():
        return DEFAULT_FILLED_WORKBOOK
    raise FileNotFoundError(
        f"Unable to resolve filled workbook in {source_dir}; pass --filled-workbook explicitly."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 344B source-check evidence review result ingestion."
    )
    parser.add_argument(
        "--source-check-evidence-enrichment-344a2-dir",
        default=str(DEFAULT_SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_DIR),
    )
    parser.add_argument(
        "--source-check-backlog-package-344a-dir",
        default=str(DEFAULT_SOURCE_CHECK_BACKLOG_PACKAGE_344A_DIR),
    )
    parser.add_argument(
        "--demo-audit-snapshot-343o-dir",
        default=str(DEFAULT_DEMO_AUDIT_SNAPSHOT_343O_DIR),
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

    filled_workbook = _resolve_filled_workbook(
        args.filled_workbook,
        Path(args.source_check_evidence_enrichment_344a2_dir),
    )

    artifacts = build_review_queue_source_check_evidence_review_ingestion_344b(
        source_check_evidence_enrichment_344a2_dir=Path(
            args.source_check_evidence_enrichment_344a2_dir
        ),
        source_check_backlog_package_344a_dir=Path(
            args.source_check_backlog_package_344a_dir
        ),
        demo_audit_snapshot_343o_dir=Path(args.demo_audit_snapshot_343o_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        filled_workbook=filled_workbook,
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / DECISION_SUMMARY_FILE_NAME, artifacts["decision_summary"])
    write_json(output_dir / AUDIT_GATE_FILE_NAME, artifacts["audit_gate"])
    write_jsonl(output_dir / RESULT_FILE_NAME, artifacts["result_rows"])
    write_jsonl(output_dir / VALIDATED_SIDECAR_FILE_NAME, artifacts["validated_sidecar_rows"])
    write_jsonl(output_dir / CORRECTIONS_FILE_NAME, artifacts["correction_rows"])
    write_jsonl(output_dir / VALIDATION_ERRORS_FILE_NAME, artifacts["validation_errors"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_344B)
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / SCOPE_BOUNDARY_FILE_NAME).write_text(
        artifacts["scope_boundary_markdown"],
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_source_check_evidence_review_ingestion_344b_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_result_jsonl: {output_dir / RESULT_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_validated_sidecar_jsonl: {output_dir / VALIDATED_SIDECAR_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_corrections_jsonl: {output_dir / CORRECTIONS_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_validation_errors_jsonl: {output_dir / VALIDATION_ERRORS_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_decision_summary_json: {output_dir / DECISION_SUMMARY_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_audit_gate_json: {output_dir / AUDIT_GATE_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_scope_boundary_md: {output_dir / SCOPE_BOUNDARY_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_source_check_evidence_review_ingestion_344b_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "filled_row_count",
        "valid_row_count",
        "invalid_row_count",
        "source_confirm_count",
        "source_correct_count",
        "source_reject_count",
        "source_still_insufficient_count",
        "source_defer_count",
        "validated_sidecar_row_count",
        "correction_row_count",
        "source_check_result_ingested",
        "source_check_backlog_resolved",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "global_strict_human_review_completed",
        "ready_for_344c",
        "recommended_344c_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

