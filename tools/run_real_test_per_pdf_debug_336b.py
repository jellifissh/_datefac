from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.real_test_full_flow_336a_report import write_excel as write_client_preview_excel  # noqa: E402
from datefac.trust.real_test_per_pdf_debug_336b import (  # noqa: E402
    DEFAULT_INPUT_PDF_DIR,
    DEFAULT_OUTPUT_DIR,
    build_real_test_per_pdf_debug_336b,
)
from datefac.trust.real_test_per_pdf_debug_336b_report import (  # noqa: E402
    batch_report_markdown,
    document_report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 336B real-test per-PDF debug package.")
    parser.add_argument("--input-pdf-dir", default=str(DEFAULT_INPUT_PDF_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    input_pdf_dir = Path(args.input_pdf_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_real_test_per_pdf_debug_336b(
        input_pdf_dir=input_pdf_dir,
        output_dir=output_dir,
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    batch_summary_json = output_dir / "00_batch_summary.json"
    batch_summary_xlsx = output_dir / "00_batch_summary.xlsx"
    batch_report_md = output_dir / "00_batch_report.md"

    write_json(batch_summary_json, artifacts["batch_summary"])
    write_excel(batch_summary_xlsx, {"batch_summary": artifacts["batch_summary_df"]}, sheet_order=["batch_summary"])
    batch_report_md.write_text(batch_report_markdown(artifacts["batch_summary"]), encoding="utf-8")

    for package in artifacts["document_packages"]:
        document_summary = package["document_summary"]
        document_dir = output_dir / document_summary["pdf_stem"]
        document_dir.mkdir(parents=True, exist_ok=True)
        write_json(document_dir / "document_summary.json", document_summary)
        write_excel(
            document_dir / "extracted_page_text.xlsx",
            {"extracted_page_text": package["page_text_df"]},
            sheet_order=["extracted_page_text"],
        )
        write_excel(
            document_dir / "extracted_tables.xlsx",
            {"extracted_tables": package["extracted_tables_df"]},
            sheet_order=["extracted_tables"],
        )
        write_excel(
            document_dir / "metric_candidates.xlsx",
            {"metric_candidates": package["metric_candidates_df"]},
            sheet_order=["metric_candidates"],
        )
        write_excel(
            document_dir / "routing_preview.xlsx",
            {"routing_preview": package["routing_preview_df"]},
            sheet_order=["routing_preview"],
        )
        write_client_preview_excel(document_dir / "client_preview.xlsx", package["client_preview_sheets"])
        (document_dir / "debug_report.md").write_text(
            document_report_markdown(document_summary),
            encoding="utf-8",
        )

    print(f"batch_summary_json: {batch_summary_json}")
    print(f"batch_summary_xlsx: {batch_summary_xlsx}")
    print(f"batch_report_md: {batch_report_md}")
    print(f"pdf_found_count: {artifacts['batch_summary'].get('pdf_found_count', 0)}")
    print(f"total_candidate_count: {artifacts['batch_summary'].get('total_candidate_count', 0)}")
    print(f"decision: {artifacts['batch_summary'].get('decision', '')}")
    for row in artifacts["batch_summary"].get("documents", []):
        print(
            "document={document}; pages={page_count}; tables={table_count}; candidates={candidate_count}; reviewed={reviewed_count}; needs_review={needs_review_count}; rejected={rejected_count}; folder={output_folder}".format(
                **row
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
