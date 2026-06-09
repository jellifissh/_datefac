from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.milestone_acceptance_audit_340a import (  # noqa: E402
    DEFAULT_DOCS_ROOT,
    DEFAULT_INPUT_PDF_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_REPO_ROOT,
    build_milestone_acceptance_audit_340a,
)
from datefac.trust.milestone_acceptance_audit_340a_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 340A milestone acceptance audit.")
    parser.add_argument("--input-pdf-dir", default=str(DEFAULT_INPUT_PDF_DIR))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--docs-root", default=str(DEFAULT_DOCS_ROOT))
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_milestone_acceptance_audit_340a(
        input_pdf_dir=Path(args.input_pdf_dir),
        output_root=Path(args.output_root),
        docs_root=Path(args.docs_root),
        repo_root=Path(args.repo_root),
        output_dir=Path(args.output_dir),
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "milestone_acceptance_audit_340a_summary.json"
    manifest_json = output_dir / "milestone_acceptance_audit_340a_manifest.json"
    qa_json = output_dir / "milestone_acceptance_audit_340a_qa.json"
    report_md = output_dir / "milestone_acceptance_audit_340a_report.md"
    workbook_xlsx = output_dir / "milestone_acceptance_audit_340a.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"milestone_acceptance_audit_340a_summary_json: {summary_json}")
    print(f"milestone_acceptance_audit_340a_manifest_json: {manifest_json}")
    print(f"milestone_acceptance_audit_340a_qa_json: {qa_json}")
    print(f"milestone_acceptance_audit_340a_report_md: {report_md}")
    print(f"milestone_acceptance_audit_340a_xlsx: {workbook_xlsx}")
    for key in [
        "input_pdf_count",
        "expected_pdf_present_count",
        "parsed_pdf_count_337a",
        "reviewed_after_count_337d",
        "input_row_count_338d",
        "documentation_consistency_passed",
        "unsafe_claim_audit_passed",
        "milestone_judgment",
        "next_step_recommendation",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
