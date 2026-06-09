from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.post_human_review_sidecar_result_340e import (  # noqa: E402
    DEFAULT_FULL_HUMAN_REVIEW_APPLY_340D_DIR,
    DEFAULT_OUTPUT_DIR,
    build_post_human_review_sidecar_result_340e,
)
from datefac.trust.post_human_review_sidecar_result_340e_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 340E post human review sidecar result.")
    parser.add_argument("--full-human-review-apply-340d-dir", default=str(DEFAULT_FULL_HUMAN_REVIEW_APPLY_340D_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_post_human_review_sidecar_result_340e(
        full_human_review_apply_340d_dir=Path(args.full_human_review_apply_340d_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "post_human_review_sidecar_result_340e_summary.json"
    manifest_json = output_dir / "post_human_review_sidecar_result_340e_manifest.json"
    qa_json = output_dir / "post_human_review_sidecar_result_340e_qa.json"
    no_write_back_proof_json = output_dir / "post_human_review_sidecar_result_340e_no_write_back_proof.json"
    report_md = output_dir / "post_human_review_sidecar_result_340e_report.md"
    workbook_xlsx = output_dir / "post_human_review_sidecar_result_340e.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_proof_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"post_human_review_sidecar_result_340e_summary_json: {summary_json}")
    print(f"post_human_review_sidecar_result_340e_manifest_json: {manifest_json}")
    print(f"post_human_review_sidecar_result_340e_qa_json: {qa_json}")
    print(f"post_human_review_sidecar_result_340e_no_write_back_proof_json: {no_write_back_proof_json}")
    print(f"post_human_review_sidecar_result_340e_report_md: {report_md}")
    print(f"post_human_review_sidecar_result_340e_xlsx: {workbook_xlsx}")
    for key in [
        "total_input_rows",
        "reviewed_after_human_count",
        "reviewed_after_human_corrected_count",
        "reviewed_after_human_total_count",
        "rejected_after_human_count",
        "needs_review_after_human_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
