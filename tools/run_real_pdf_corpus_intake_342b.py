from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.real_pdf_corpus_intake_342b import (  # noqa: E402
    DEFAULT_BENCHMARK_PLAN_342A_DIR,
    DEFAULT_INPUT_DIR,
    DEFAULT_OUTPUT_DIR,
    build_real_pdf_corpus_intake_342b,
)
from datefac.benchmark.real_pdf_corpus_intake_342b_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342B real PDF corpus intake and metadata audit.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--benchmark-plan-342a-dir", default=str(DEFAULT_BENCHMARK_PLAN_342A_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_real_pdf_corpus_intake_342b(
        input_dir=Path(args.input_dir),
        benchmark_plan_342a_dir=Path(args.benchmark_plan_342a_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "real_pdf_corpus_intake_342b_summary.json"
    manifest_json = output_dir / "real_pdf_corpus_intake_342b_manifest.json"
    qa_json = output_dir / "real_pdf_corpus_intake_342b_qa.json"
    no_write_back_json = output_dir / "real_pdf_corpus_intake_342b_no_write_back_proof.json"
    report_md = output_dir / "real_pdf_corpus_intake_342b_report.md"
    workbook_xlsx = output_dir / "real_pdf_corpus_intake_342b.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"real_pdf_corpus_intake_342b_summary_json: {summary_json}")
    print(f"real_pdf_corpus_intake_342b_manifest_json: {manifest_json}")
    print(f"real_pdf_corpus_intake_342b_qa_json: {qa_json}")
    print(f"real_pdf_corpus_intake_342b_no_write_back_proof_json: {no_write_back_json}")
    print(f"real_pdf_corpus_intake_342b_report_md: {report_md}")
    print(f"real_pdf_corpus_intake_342b_xlsx: {workbook_xlsx}")
    for key in [
        "current_pdf_count",
        "unique_pdf_count",
        "duplicate_pdf_count",
        "assigned_tier_count",
        "unknown_tier_count",
        "pilot_set_count",
        "benchmark_set_count",
        "holdout_set_count",
        "ready_for_342c",
        "recommended_first_run_pdf_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
