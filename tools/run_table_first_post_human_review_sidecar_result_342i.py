from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.table_first_post_human_review_sidecar_result_342i import (  # noqa: E402
    DEFAULT_HUMAN_REVIEW_342H_DIR,
    DEFAULT_OUTPUT_DIR,
    build_table_first_post_human_review_sidecar_result_342i,
)
from datefac.benchmark.table_first_post_human_review_sidecar_result_342i_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342I table-first post-human-review sidecar result.")
    parser.add_argument("--human-review-342h-dir", default=str(DEFAULT_HUMAN_REVIEW_342H_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_table_first_post_human_review_sidecar_result_342i(
        human_review_342h_dir=Path(args.human_review_342h_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "table_first_post_human_review_sidecar_result_342i_summary.json"
    manifest_json = output_dir / "table_first_post_human_review_sidecar_result_342i_manifest.json"
    qa_json = output_dir / "table_first_post_human_review_sidecar_result_342i_qa.json"
    no_write_back_json = output_dir / "table_first_post_human_review_sidecar_result_342i_no_write_back_proof.json"
    report_md = output_dir / "table_first_post_human_review_sidecar_result_342i_report.md"
    workbook_xlsx = output_dir / "table_first_post_human_review_sidecar_result_342i.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"table_first_post_human_review_sidecar_result_342i_summary_json: {summary_json}")
    print(f"table_first_post_human_review_sidecar_result_342i_manifest_json: {manifest_json}")
    print(f"table_first_post_human_review_sidecar_result_342i_qa_json: {qa_json}")
    print(f"table_first_post_human_review_sidecar_result_342i_no_write_back_proof_json: {no_write_back_json}")
    print(f"table_first_post_human_review_sidecar_result_342i_report_md: {report_md}")
    print(f"table_first_post_human_review_sidecar_result_342i_xlsx: {workbook_xlsx}")
    for key in [
        "decision",
        "input_review_template_row_count",
        "reviewed_row_count",
        "pending_review_count",
        "final_confirmed_cell_count",
        "final_corrected_cell_count",
        "final_rejected_cell_count",
        "post_human_confirmed_count",
        "metric_covered_after_human_count",
        "metric_year_pair_after_human_count",
        "remaining_review_count",
        "unit_year_remaining_count",
        "duplicate_remaining_count",
        "growth_row_remaining_count",
        "ready_for_342j",
        "recommended_342j_scope",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
