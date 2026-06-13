from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_strict_human_review_package_344f import (  # noqa: E402
    ARTIFACT_INDEX_FILE_NAME,
    DEFAULT_EXPANDED_DEMO_AUDIT_SNAPSHOT_344E_DIR,
    DEFAULT_OUTPUT_DIR,
    EXECUTIVE_SUMMARY_FILE_NAME,
    FINAL_GATE_SNAPSHOT_FILE_NAME,
    MANIFEST_FILE_NAME,
    REVIEW_ROWS_CSV_FILE_NAME,
    REVIEW_ROWS_JSON_FILE_NAME,
    REVIEWER_CHECKLIST_FILE_NAME,
    WORKBOOK_FILE_NAME,
    build_review_queue_strict_human_review_package_344f,
)
from datefac.benchmark.review_queue_strict_human_review_package_344f_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    report_review_rows_json,
    reviewer_checklist_markdown,
    write_csv,
    write_excel,
    write_json,
)
from datefac.review_queue.strict_human_review_package_344f import WORKBOOK_SHEETS_344F  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 344F strict human review package generation.")
    parser.add_argument(
        "--expanded-demo-audit-snapshot-344e-dir",
        default=str(DEFAULT_EXPANDED_DEMO_AUDIT_SNAPSHOT_344E_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_strict_human_review_package_344f(
        expanded_demo_audit_snapshot_344e_dir=Path(args.expanded_demo_audit_snapshot_344e_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_csv(
        output_dir / REVIEW_ROWS_CSV_FILE_NAME,
        artifacts["review_rows"],
        artifacts["review_rows_csv_fields"],
    )
    report_review_rows_json(output_dir / REVIEW_ROWS_JSON_FILE_NAME, artifacts["review_rows"])
    write_json(output_dir / FINAL_GATE_SNAPSHOT_FILE_NAME, artifacts["final_gate_snapshot"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS_344F)
    (output_dir / REVIEWER_CHECKLIST_FILE_NAME).write_text(
        reviewer_checklist_markdown(artifacts["summary"]),
        encoding="utf-8",
    )
    (output_dir / EXECUTIVE_SUMMARY_FILE_NAME).write_text(
        executive_summary_markdown(artifacts["summary"]),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_rows_csv: {output_dir / REVIEW_ROWS_CSV_FILE_NAME}")
    print(f"review_rows_json: {output_dir / REVIEW_ROWS_JSON_FILE_NAME}")
    print(f"reviewer_checklist_md: {output_dir / REVIEWER_CHECKLIST_FILE_NAME}")
    print(f"executive_summary_md: {output_dir / EXECUTIVE_SUMMARY_FILE_NAME}")
    print(f"artifact_index_md: {output_dir / ARTIFACT_INDEX_FILE_NAME}")
    print(f"final_gate_snapshot_json: {output_dir / FINAL_GATE_SNAPSHOT_FILE_NAME}")
    print(f"workbook_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "input_expanded_export_row_count",
        "strict_review_row_count",
        "prior_demo_trusted_row_count",
        "source_check_trusted_row_count",
        "source_check_confirmed_row_count",
        "corrected_row_count",
        "strict_human_review_package_generated",
        "global_strict_human_review_completed",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "export_usage",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
