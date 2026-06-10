from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.parser_ensemble_compare_342d import (  # noqa: E402
    DEFAULT_CORPUS_342B_DIR,
    DEFAULT_MINERU_342C6_DIR,
    DEFAULT_OUTPUT_DIR,
    build_parser_ensemble_compare_342d,
)
from datefac.benchmark.parser_ensemble_compare_342d_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342D parser ensemble compare benchmark.")
    parser.add_argument("--corpus-342b-dir", default=str(DEFAULT_CORPUS_342B_DIR))
    parser.add_argument("--mineru-342c6-dir", default=str(DEFAULT_MINERU_342C6_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_parser_ensemble_compare_342d(
        corpus_342b_dir=Path(args.corpus_342b_dir),
        mineru_342c6_dir=Path(args.mineru_342c6_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "parser_ensemble_compare_342d_summary.json"
    manifest_json = output_dir / "parser_ensemble_compare_342d_manifest.json"
    qa_json = output_dir / "parser_ensemble_compare_342d_qa.json"
    no_write_back_json = output_dir / "parser_ensemble_compare_342d_no_write_back_proof.json"
    report_md = output_dir / "parser_ensemble_compare_342d_report.md"
    workbook_xlsx = output_dir / "parser_ensemble_compare_342d.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"parser_ensemble_compare_342d_summary_json: {summary_json}")
    print(f"parser_ensemble_compare_342d_manifest_json: {manifest_json}")
    print(f"parser_ensemble_compare_342d_qa_json: {qa_json}")
    print(f"parser_ensemble_compare_342d_no_write_back_proof_json: {no_write_back_json}")
    print(f"parser_ensemble_compare_342d_report_md: {report_md}")
    print(f"parser_ensemble_compare_342d_xlsx: {workbook_xlsx}")
    for key in [
        "compared_pdf_count",
        "mineru_success_count",
        "mineru_artifact_complete_count",
        "mineru_markdown_usable_count",
        "mineru_content_list_usable_count",
        "baseline_available_count",
        "mineru_stronger_signal_count",
        "insufficient_baseline_count",
        "ready_for_342e",
        "recommended_342e_scope",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
