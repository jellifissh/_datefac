from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.client_preview_export_after_human_review_340f import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_HUMAN_REVIEW_340E_DIR,
    build_client_preview_export_after_human_review_340f,
)
from datefac.trust.client_preview_export_after_human_review_340f_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 340F client preview export after human review.")
    parser.add_argument("--post-human-review-340e-dir", default=str(DEFAULT_POST_HUMAN_REVIEW_340E_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_client_preview_export_after_human_review_340f(
        post_human_review_340e_dir=Path(args.post_human_review_340e_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "client_preview_after_human_review_340f_summary.json"
    manifest_json = output_dir / "client_preview_after_human_review_340f_manifest.json"
    qa_json = output_dir / "client_preview_after_human_review_340f_qa.json"
    no_write_back_proof_json = output_dir / "client_preview_after_human_review_340f_no_write_back_proof.json"
    report_md = output_dir / "client_preview_after_human_review_340f_report.md"
    workbook_xlsx = output_dir / "client_preview_after_human_review_340f.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_proof_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"client_preview_after_human_review_340f_summary_json: {summary_json}")
    print(f"client_preview_after_human_review_340f_manifest_json: {manifest_json}")
    print(f"client_preview_after_human_review_340f_qa_json: {qa_json}")
    print(f"client_preview_after_human_review_340f_no_write_back_proof_json: {no_write_back_proof_json}")
    print(f"client_preview_after_human_review_340f_report_md: {report_md}")
    print(f"client_preview_after_human_review_340f_xlsx: {workbook_xlsx}")
    for key in [
        "total_340e_input_rows",
        "client_preview_core_metric_count",
        "client_preview_confirmed_count",
        "client_preview_corrected_count",
        "needs_review_after_human_count",
        "rejected_after_human_count",
        "source_trace_count",
        "qa_fail_count",
        "client_preview_ready",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
