from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.mineru_batch_parse_benchmark_342c import (  # noqa: E402
    DEFAULT_CORPUS_342B_DIR,
    DEFAULT_OUTPUT_DIR,
    build_mineru_batch_parse_benchmark_342c,
)
from datefac.benchmark.mineru_batch_parse_benchmark_342c_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342C MinerU batch parse benchmark pilot.")
    parser.add_argument("--corpus-342b-dir", default=str(DEFAULT_CORPUS_342B_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--mineru-command", default="")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    artifacts = build_mineru_batch_parse_benchmark_342c(
        corpus_342b_dir=Path(args.corpus_342b_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
        mineru_command=args.mineru_command or None,
        limit=args.limit if args.limit and args.limit > 0 else None,
        dry_run=bool(args.dry_run),
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "mineru_batch_parse_benchmark_342c_summary.json"
    manifest_json = output_dir / "mineru_batch_parse_benchmark_342c_manifest.json"
    qa_json = output_dir / "mineru_batch_parse_benchmark_342c_qa.json"
    no_write_back_json = output_dir / "mineru_batch_parse_benchmark_342c_no_write_back_proof.json"
    report_md = output_dir / "mineru_batch_parse_benchmark_342c_report.md"
    workbook_xlsx = output_dir / "mineru_batch_parse_benchmark_342c.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"mineru_batch_parse_benchmark_342c_summary_json: {summary_json}")
    print(f"mineru_batch_parse_benchmark_342c_manifest_json: {manifest_json}")
    print(f"mineru_batch_parse_benchmark_342c_qa_json: {qa_json}")
    print(f"mineru_batch_parse_benchmark_342c_no_write_back_proof_json: {no_write_back_json}")
    print(f"mineru_batch_parse_benchmark_342c_report_md: {report_md}")
    print(f"mineru_batch_parse_benchmark_342c_xlsx: {workbook_xlsx}")
    for key in [
        "pilot_total_count",
        "mineru_success_count",
        "mineru_failed_count",
        "empty_output_count",
        "total_runtime_seconds",
        "avg_runtime_seconds",
        "ready_for_342d",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
