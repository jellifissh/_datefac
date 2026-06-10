from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.table_first_core_financial_extraction_342f import (  # noqa: E402
    DEFAULT_CANDIDATE_QUALITY_342E_DIR,
    DEFAULT_CORPUS_342B_DIR,
    DEFAULT_MINERU_342C6_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PARSER_COMPARE_342D_DIR,
    build_table_first_core_financial_extraction_342f,
)
from datefac.benchmark.table_first_core_financial_extraction_342f_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342F table-first core financial long-form extraction.")
    parser.add_argument("--corpus-342b-dir", default=str(DEFAULT_CORPUS_342B_DIR))
    parser.add_argument("--mineru-342c6-dir", default=str(DEFAULT_MINERU_342C6_DIR))
    parser.add_argument("--parser-compare-342d-dir", default=str(DEFAULT_PARSER_COMPARE_342D_DIR))
    parser.add_argument("--candidate-quality-342e-dir", default=str(DEFAULT_CANDIDATE_QUALITY_342E_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_table_first_core_financial_extraction_342f(
        corpus_342b_dir=Path(args.corpus_342b_dir),
        mineru_342c6_dir=Path(args.mineru_342c6_dir),
        parser_compare_342d_dir=Path(args.parser_compare_342d_dir),
        candidate_quality_342e_dir=Path(args.candidate_quality_342e_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "table_first_core_financial_extraction_342f_summary.json"
    manifest_json = output_dir / "table_first_core_financial_extraction_342f_manifest.json"
    qa_json = output_dir / "table_first_core_financial_extraction_342f_qa.json"
    no_write_back_json = output_dir / "table_first_core_financial_extraction_342f_no_write_back_proof.json"
    report_md = output_dir / "table_first_core_financial_extraction_342f_report.md"
    workbook_xlsx = output_dir / "table_first_core_financial_extraction_342f.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"table_first_core_financial_extraction_342f_summary_json: {summary_json}")
    print(f"table_first_core_financial_extraction_342f_manifest_json: {manifest_json}")
    print(f"table_first_core_financial_extraction_342f_qa_json: {qa_json}")
    print(f"table_first_core_financial_extraction_342f_no_write_back_proof_json: {no_write_back_json}")
    print(f"table_first_core_financial_extraction_342f_report_md: {report_md}")
    print(f"table_first_core_financial_extraction_342f_xlsx: {workbook_xlsx}")
    for key in [
        "audited_pdf_count",
        "input_core_extractable_table_count",
        "parsed_core_table_count",
        "html_parse_failed_table_count",
        "long_form_cell_count",
        "trusted_cell_count",
        "review_required_cell_count",
        "rejected_cell_count",
        "metric_covered_count",
        "metric_year_pair_count",
        "unit_issue_count",
        "year_header_issue_count",
        "duplicate_cell_count",
        "ready_for_342g",
        "recommended_342g_scope",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
