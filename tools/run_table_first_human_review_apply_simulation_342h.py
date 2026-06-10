from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.table_first_human_review_apply_simulation_342h import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_PACKAGE_342G_DIR,
    DEFAULT_REVIEWED_INPUT_DIR,
    build_table_first_human_review_apply_simulation_342h,
)
from datefac.benchmark.table_first_human_review_apply_simulation_342h_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342H table-first human review apply simulation.")
    parser.add_argument("--review-package-342g-dir", default=str(DEFAULT_REVIEW_PACKAGE_342G_DIR))
    parser.add_argument("--reviewed-input-dir", default=str(DEFAULT_REVIEWED_INPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_table_first_human_review_apply_simulation_342h(
        review_package_342g_dir=Path(args.review_package_342g_dir),
        reviewed_input_dir=Path(args.reviewed_input_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "table_first_human_review_apply_simulation_342h_summary.json"
    manifest_json = output_dir / "table_first_human_review_apply_simulation_342h_manifest.json"
    qa_json = output_dir / "table_first_human_review_apply_simulation_342h_qa.json"
    no_write_back_json = output_dir / "table_first_human_review_apply_simulation_342h_no_write_back_proof.json"
    report_md = output_dir / "table_first_human_review_apply_simulation_342h_report.md"
    workbook_xlsx = output_dir / "table_first_human_review_apply_simulation_342h.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"table_first_human_review_apply_simulation_342h_summary_json: {summary_json}")
    print(f"table_first_human_review_apply_simulation_342h_manifest_json: {manifest_json}")
    print(f"table_first_human_review_apply_simulation_342h_qa_json: {qa_json}")
    print(f"table_first_human_review_apply_simulation_342h_no_write_back_proof_json: {no_write_back_json}")
    print(f"table_first_human_review_apply_simulation_342h_report_md: {report_md}")
    print(f"table_first_human_review_apply_simulation_342h_xlsx: {workbook_xlsx}")
    for key in [
        "reviewed_workbook_exists",
        "decision",
        "input_review_template_row_count",
        "reviewed_row_count",
        "pending_review_count",
        "confirmed_cell_count",
        "corrected_cell_count",
        "rejected_cell_count",
        "still_review_required_count",
        "needs_source_check_count",
        "validation_error_count",
        "net_confirmed_after_human_count",
        "net_review_reduction_count",
        "ready_for_342i",
        "recommended_342i_scope",
        "recommended_next_action",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
