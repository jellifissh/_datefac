from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.real_test_full_flow_336a import (  # noqa: E402
    DEFAULT_INPUT_PDF_DIR,
    DEFAULT_OUTPUT_DIR,
    WORKBOOK_SHEETS,
    build_real_test_full_flow_336a,
)
from datefac.trust.real_test_full_flow_336a_report import (  # noqa: E402
    real_test_full_flow_336a_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 336A real test full flow from a PDF folder.")
    parser.add_argument("--input-pdf-dir", default=str(DEFAULT_INPUT_PDF_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    input_pdf_dir = Path(args.input_pdf_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_real_test_full_flow_336a(
        input_pdf_dir=input_pdf_dir,
        output_dir=output_dir,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "real_test_full_flow_336a_summary.json"
    manifest_json = output_dir / "real_test_full_flow_336a_manifest.json"
    qa_json = output_dir / "real_test_full_flow_336a_qa.json"
    report_md = output_dir / "real_test_full_flow_336a_report.md"
    preview_xlsx = output_dir / "real_test_client_export_336a.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_excel(
        preview_xlsx,
        {
            WORKBOOK_SHEETS["readme"]: artifacts["readme_df"],
            WORKBOOK_SHEETS["reviewed"]: artifacts["reviewed_df"],
            WORKBOOK_SHEETS["needs_review"]: artifacts["needs_review_df"],
            WORKBOOK_SHEETS["rejected"]: artifacts["rejected_df"],
            WORKBOOK_SHEETS["trace"]: artifacts["source_trace_df"],
            WORKBOOK_SHEETS["summary"]: artifacts["run_summary_df"],
        },
    )
    report_md.write_text(
        real_test_full_flow_336a_markdown(artifacts["summary"], artifacts["qa_json"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"real_test_full_flow_336a_summary_json: {summary_json}")
    print(f"real_test_full_flow_336a_manifest_json: {manifest_json}")
    print(f"real_test_full_flow_336a_qa_json: {qa_json}")
    print(f"real_test_full_flow_336a_report_md: {report_md}")
    print(f"real_test_client_export_336a_xlsx: {preview_xlsx}")
    for key in [
        "pdf_found_count",
        "pdf_processed_count",
        "reviewed_count",
        "needs_review_count",
        "rejected_or_excluded_count",
        "page_failure_count",
        "pdf_failure_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
