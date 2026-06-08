from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.mineru_real_pdf_intake_337a import (  # noqa: E402
    COMBINED_WORKBOOK_SHEETS,
    DEFAULT_INPUT_PDF_DIR,
    DEFAULT_MINERU_EXE,
    DEFAULT_OUTPUT_DIR,
    build_mineru_real_pdf_intake_337a,
)
from datefac.trust.mineru_real_pdf_intake_337a_report import (  # noqa: E402
    COMBINED_WORKBOOK_SHEETS as REPORT_SHEET_ORDER,
    batch_report_markdown,
    document_report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 337A MinerU-first real PDF intake.")
    parser.add_argument("--input-pdf-dir", default=str(DEFAULT_INPUT_PDF_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--mineru-exe", default=str(DEFAULT_MINERU_EXE))
    args = parser.parse_args()

    input_pdf_dir = Path(args.input_pdf_dir)
    output_dir = Path(args.output_dir)
    mineru_exe = Path(args.mineru_exe)

    artifacts = build_mineru_real_pdf_intake_337a(
        input_pdf_dir=input_pdf_dir,
        output_dir=output_dir,
        mineru_exe=mineru_exe,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    batch_summary_xlsx = output_dir / "00_batch_summary.xlsx"
    batch_summary_json = output_dir / "00_batch_summary.json"
    batch_report_md = output_dir / "00_batch_report.md"
    combined_preview_xlsx = output_dir / "real_test_mineru_client_export_337a.xlsx"
    qa_json = output_dir / "real_test_mineru_337a_qa.json"
    manifest_json = output_dir / "real_test_mineru_337a_manifest.json"
    datefac_debug_root = output_dir / "datefac_debug"

    write_json(batch_summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(manifest_json, artifacts["manifest"])
    write_excel(batch_summary_xlsx, {"batch_summary": artifacts["batch_summary_df"]}, ["batch_summary"])
    write_excel(combined_preview_xlsx, artifacts["combined_workbook_sheets"], REPORT_SHEET_ORDER)
    batch_report_md.write_text(
        batch_report_markdown(artifacts["summary"], artifacts["qa_json"], artifacts["document_rows"]),
        encoding="utf-8",
    )

    for package in artifacts["document_packages"]:
        document_summary = package["document_summary"]
        document_dir = datefac_debug_root / document_summary["pdf_stem"]
        document_dir.mkdir(parents=True, exist_ok=True)
        write_json(document_dir / "document_summary.json", document_summary)
        write_excel(document_dir / "mineru_artifact_inventory.xlsx", package["inventory_sheets"], ["summary", "source_files", "warnings", "table_assets", "extracted_tables"])
        write_excel(document_dir / "extracted_page_text.xlsx", {"extracted_page_text": package["page_text_df"], "raw_text_nodes": package["raw_text_df"]}, ["extracted_page_text", "raw_text_nodes"])
        write_excel(document_dir / "extracted_tables.xlsx", {"extracted_tables": package["extracted_tables_df"]}, ["extracted_tables"])
        write_excel(document_dir / "financial_table_candidates.xlsx", {"financial_table_candidates": package["financial_candidates_df"]}, ["financial_table_candidates"])
        write_excel(document_dir / "metric_candidates.xlsx", {"metric_candidates": package["metric_candidates_df"]}, ["metric_candidates"])
        write_excel(document_dir / "routing_preview.xlsx", {"routing_preview": package["routing_preview_df"]}, ["routing_preview"])
        write_excel(document_dir / "client_preview.xlsx", package["client_preview_sheets"], REPORT_SHEET_ORDER)
        (document_dir / "debug_report.md").write_text(document_report_markdown(document_summary), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"00_batch_summary_xlsx: {batch_summary_xlsx}")
    print(f"00_batch_summary_json: {batch_summary_json}")
    print(f"00_batch_report_md: {batch_report_md}")
    print(f"real_test_mineru_client_export_337a_xlsx: {combined_preview_xlsx}")
    print(f"real_test_mineru_337a_qa_json: {qa_json}")
    print(f"real_test_mineru_337a_manifest_json: {manifest_json}")
    for key in [
        "pdf_found_count",
        "pdf_processed_count",
        "mineru_success_count",
        "reviewed_count",
        "needs_review_count",
        "rejected_or_excluded_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
