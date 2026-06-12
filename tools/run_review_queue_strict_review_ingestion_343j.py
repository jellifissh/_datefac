from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_strict_review_ingestion_343j import (  # noqa: E402
    build_review_queue_strict_review_ingestion_343j,
)
from datefac.benchmark.review_queue_strict_review_ingestion_343j_report import (  # noqa: E402
    report_markdown,
    reviewer_source_disclosure_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR = Path(
    r"D:\_datefac\output\review_queue_source_evidence_enrichment_343i2"
)
DEFAULT_STRICT_HUMAN_REVIEW_PACKAGE_343I_DIR = Path(
    r"D:\_datefac\output\review_queue_strict_human_review_package_343i"
)
DEFAULT_AUDIT_SUMMARY_343H_DIR = Path(r"D:\_datefac\output\review_queue_audit_summary_343h")
DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR = Path(r"D:\_datefac\output\review_queue_schema_343a")
DEFAULT_FILLED_WORKBOOK = Path(
    r"D:\_datefac\input\review_queue_strict_human_review_343i2_filled\review_queue_source_evidence_enrichment_343i2_enriched_review_template_filled.xlsx"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\review_queue_strict_review_ingestion_343j")

SUMMARY_FILE_NAME = "review_queue_strict_review_ingestion_343j_summary.json"
MANIFEST_FILE_NAME = "review_queue_strict_review_ingestion_343j_manifest.json"
QA_FILE_NAME = "review_queue_strict_review_ingestion_343j_qa.json"
NO_WRITE_BACK_FILE_NAME = "review_queue_strict_review_ingestion_343j_no_write_back_proof.json"
REPORT_FILE_NAME = "review_queue_strict_review_ingestion_343j_report.md"
WORKBOOK_FILE_NAME = "review_queue_strict_review_ingestion_343j.xlsx"
RESULT_FILE_NAME = "review_queue_strict_review_ingestion_343j_result.jsonl"
VALIDATION_ERRORS_FILE_NAME = "review_queue_strict_review_ingestion_343j_validation_errors.json"
DECISION_SUMMARY_FILE_NAME = "review_queue_strict_review_ingestion_343j_decision_summary.json"
CLIENT_EXPORT_GATE_FILE_NAME = "review_queue_strict_review_ingestion_343j_client_export_gate.json"
REVIEWER_SOURCE_DISCLOSURE_FILE_NAME = (
    "review_queue_strict_review_ingestion_343j_reviewer_source_disclosure.md"
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
        description="Run 343J strict review result ingestion from enriched workbook."
    )
    parser.add_argument(
        "--source-evidence-enrichment-343i2-dir",
        default=str(DEFAULT_SOURCE_EVIDENCE_ENRICHMENT_343I2_DIR),
    )
    parser.add_argument(
        "--strict-human-review-package-343i-dir",
        default=str(DEFAULT_STRICT_HUMAN_REVIEW_PACKAGE_343I_DIR),
    )
    parser.add_argument(
        "--audit-summary-343h-dir",
        default=str(DEFAULT_AUDIT_SUMMARY_343H_DIR),
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
        args.filled_workbook, Path(args.source_evidence_enrichment_343i2_dir)
    )

    artifacts = build_review_queue_strict_review_ingestion_343j(
        source_evidence_enrichment_343i2_dir=Path(args.source_evidence_enrichment_343i2_dir),
        strict_human_review_package_343i_dir=Path(args.strict_human_review_package_343i_dir),
        audit_summary_343h_dir=Path(args.audit_summary_343h_dir),
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
    write_json(output_dir / CLIENT_EXPORT_GATE_FILE_NAME, artifacts["client_export_gate"])
    write_json(output_dir / VALIDATION_ERRORS_FILE_NAME, artifacts["validation_errors"])
    write_jsonl(output_dir / RESULT_FILE_NAME, artifacts["result_rows"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], [
        "00_README",
        "01_INGEST_SUMMARY",
        "02_INPUT_343I2_SUMMARY",
        "03_REVIEW_RESULTS",
        "04_VALIDATION_ERRORS",
        "05_DECISION_SUMMARY",
        "06_EXPORT_GATE",
        "07_SOURCE_DISCLOSURE",
        "08_NO_WRITE_BACK",
        "09_NEXT_STEPS",
    ])
    (output_dir / REPORT_FILE_NAME).write_text(
        report_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )
    (output_dir / REVIEWER_SOURCE_DISCLOSURE_FILE_NAME).write_text(
        reviewer_source_disclosure_markdown(artifacts["summary"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"review_queue_strict_review_ingestion_343j_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_result_jsonl: {output_dir / RESULT_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_validation_errors_json: {output_dir / VALIDATION_ERRORS_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_decision_summary_json: {output_dir / DECISION_SUMMARY_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_client_export_gate_json: {output_dir / CLIENT_EXPORT_GATE_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_reviewer_source_disclosure_md: {output_dir / REVIEWER_SOURCE_DISCLOSURE_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_strict_review_ingestion_343j_xlsx: {output_dir / WORKBOOK_FILE_NAME}")

    for key in [
        "decision",
        "review_queue_schema_version",
        "filled_workbook_path",
        "filled_row_count",
        "valid_row_count",
        "invalid_row_count",
        "strict_confirm_count",
        "strict_correct_count",
        "strict_reject_count",
        "strict_needs_source_check_count",
        "strict_defer_count",
        "strict_review_input_source_type",
        "not_pure_human_review",
        "pure_strict_human_confirm_count",
        "ai_assisted_strict_review_confirm_count",
        "strict_review_result_ingested",
        "pure_strict_human_review_completed",
        "strict_human_review_completed",
        "requires_strict_human_review",
        "requires_pure_human_confirmation",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343k",
        "recommended_343k_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
