from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.full_extraction_quality_audit_345b import (  # noqa: E402
    ARTIFACT_INDEX_FILE_NAME,
    DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR,
    DEFAULT_OUTPUT_DIR,
    EVIDENCE_TRACE_QUALITY_FILE_NAME,
    EXECUTIVE_SUMMARY_FILE_NAME,
    MANIFEST_FILE_NAME,
    MISSING_FIELD_HOTSPOTS_FILE_NAME,
    NEXT_PLAN_FILE_NAME,
    PDF_QUALITY_SUMMARY_CSV_FILE_NAME,
    PDF_QUALITY_SUMMARY_JSON_FILE_NAME,
    PRIORITY_FIX_QUEUE_CSV_FILE_NAME,
    PRIORITY_FIX_QUEUE_JSON_FILE_NAME,
    QUALITY_ROW_FIELDS,
    QUALITY_ROWS_CSV_FILE_NAME,
    QUALITY_ROWS_JSON_FILE_NAME,
    STAGE_QUALITY_SUMMARY_CSV_FILE_NAME,
    STAGE_QUALITY_SUMMARY_JSON_FILE_NAME,
    build_full_extraction_quality_audit_345b,
)
from datefac.benchmark.full_extraction_quality_audit_345b_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 345B full extraction quality audit.")
    parser.add_argument(
        "--full-structured-data-inventory-345a-dir",
        default=str(DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_full_extraction_quality_audit_345b(
        full_structured_data_inventory_345a_dir=Path(
            args.full_structured_data_inventory_345a_dir
        ),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QUALITY_ROWS_JSON_FILE_NAME, artifacts["quality_rows"])
    write_csv(
        output_dir / QUALITY_ROWS_CSV_FILE_NAME,
        artifacts["quality_rows"],
        QUALITY_ROW_FIELDS,
    )
    write_json(
        output_dir / STAGE_QUALITY_SUMMARY_JSON_FILE_NAME,
        artifacts["stage_quality_summary"],
    )
    write_csv(
        output_dir / STAGE_QUALITY_SUMMARY_CSV_FILE_NAME,
        artifacts["stage_quality_summary"],
        list(artifacts["stage_quality_summary"][0].keys()),
    )
    write_json(
        output_dir / PDF_QUALITY_SUMMARY_JSON_FILE_NAME,
        artifacts["pdf_quality_summary"],
    )
    write_csv(
        output_dir / PDF_QUALITY_SUMMARY_CSV_FILE_NAME,
        artifacts["pdf_quality_summary"],
        list(artifacts["pdf_quality_summary"][0].keys()),
    )
    write_json(
        output_dir / MISSING_FIELD_HOTSPOTS_FILE_NAME,
        artifacts["missing_field_hotspots"],
    )
    write_json(
        output_dir / EVIDENCE_TRACE_QUALITY_FILE_NAME,
        artifacts["evidence_trace_quality"],
    )
    write_json(
        output_dir / PRIORITY_FIX_QUEUE_JSON_FILE_NAME,
        artifacts["priority_fix_queue"],
    )
    if artifacts["priority_fix_queue"]:
        write_csv(
            output_dir / PRIORITY_FIX_QUEUE_CSV_FILE_NAME,
            artifacts["priority_fix_queue"],
            list(artifacts["priority_fix_queue"][0].keys()),
        )
    else:
        write_csv(output_dir / PRIORITY_FIX_QUEUE_CSV_FILE_NAME, [], ["quality_row_id"])
    (output_dir / EXECUTIVE_SUMMARY_FILE_NAME).write_text(
        executive_summary_markdown(
            artifacts["manifest"],
            artifacts["stage_quality_summary"],
            artifacts["pdf_quality_summary"],
            artifacts["missing_field_hotspots"],
            artifacts["evidence_trace_quality"],
            artifacts["priority_fix_queue"],
        ),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_FILE_NAME).write_text(
        next_plan_markdown(),
        encoding="utf-8",
    )

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"quality_rows_json: {output_dir / QUALITY_ROWS_JSON_FILE_NAME}")
    print(f"quality_rows_csv: {output_dir / QUALITY_ROWS_CSV_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"audited_row_count: {manifest.get('audited_row_count', '')}")
    print(f"high_severity_issue_count: {manifest.get('high_severity_issue_count', '')}")
    print(f"priority_fix_queue_count: {manifest.get('priority_fix_queue_count', '')}")
    print(
        f"ready_candidate_count_after_quality_audit: {manifest.get('ready_candidate_count_after_quality_audit', '')}"
    )
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
