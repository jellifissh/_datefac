from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.larger_real_pdf_benchmark_plan_342a import (  # noqa: E402
    DEFAULT_CLIENT_PREVIEW_340F_DIR,
    DEFAULT_CLIENT_PREVIEW_AUDIT_340G_DIR,
    DEFAULT_INPUT_DIR,
    DEFAULT_MILESTONE_341A_DIR,
    DEFAULT_OUTPUT_DIR,
    build_larger_real_pdf_benchmark_plan_342a,
)
from datefac.benchmark.larger_real_pdf_benchmark_plan_342a_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342A larger real-PDF benchmark plan.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--milestone-341a-dir", default=str(DEFAULT_MILESTONE_341A_DIR))
    parser.add_argument("--client-preview-audit-340g-dir", default=str(DEFAULT_CLIENT_PREVIEW_AUDIT_340G_DIR))
    parser.add_argument("--client-preview-340f-dir", default=str(DEFAULT_CLIENT_PREVIEW_340F_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_larger_real_pdf_benchmark_plan_342a(
        input_dir=Path(args.input_dir),
        milestone_341a_dir=Path(args.milestone_341a_dir),
        client_preview_audit_340g_dir=Path(args.client_preview_audit_340g_dir),
        client_preview_340f_dir=Path(args.client_preview_340f_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "larger_real_pdf_benchmark_plan_342a_summary.json"
    manifest_json = output_dir / "larger_real_pdf_benchmark_plan_342a_manifest.json"
    qa_json = output_dir / "larger_real_pdf_benchmark_plan_342a_qa.json"
    report_md = output_dir / "larger_real_pdf_benchmark_plan_342a_report.md"
    workbook_xlsx = output_dir / "larger_real_pdf_benchmark_plan_342a.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"larger_real_pdf_benchmark_plan_342a_summary_json: {summary_json}")
    print(f"larger_real_pdf_benchmark_plan_342a_manifest_json: {manifest_json}")
    print(f"larger_real_pdf_benchmark_plan_342a_qa_json: {qa_json}")
    print(f"larger_real_pdf_benchmark_plan_342a_report_md: {report_md}")
    print(f"larger_real_pdf_benchmark_plan_342a_xlsx: {workbook_xlsx}")
    for key in [
        "current_pdf_count",
        "benchmark_status",
        "target_pdf_count_min",
        "target_pdf_count_recommended",
        "target_pdf_count_stretch",
        "detected_341a_decision",
        "detected_340g_audit_passed",
        "detected_340f_client_preview_core_metric_count",
        "warning_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
