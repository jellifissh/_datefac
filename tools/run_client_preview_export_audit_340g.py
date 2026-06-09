from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.client_preview_export_audit_340g import (  # noqa: E402
    DEFAULT_CLIENT_PREVIEW_340F_DIR,
    DEFAULT_OUTPUT_DIR,
    build_client_preview_export_audit_340g,
)
from datefac.trust.client_preview_export_audit_340g_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 340G client preview export audit.")
    parser.add_argument("--client-preview-340f-dir", default=str(DEFAULT_CLIENT_PREVIEW_340F_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_client_preview_export_audit_340g(
        client_preview_340f_dir=Path(args.client_preview_340f_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "client_preview_export_audit_340g_summary.json"
    manifest_json = output_dir / "client_preview_export_audit_340g_manifest.json"
    qa_json = output_dir / "client_preview_export_audit_340g_qa.json"
    report_md = output_dir / "client_preview_export_audit_340g_report.md"
    no_write_back_proof_json = output_dir / "client_preview_export_audit_340g_no_write_back_proof.json"
    workbook_xlsx = output_dir / "client_preview_export_audit_340g.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_proof_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"client_preview_export_audit_340g_summary_json: {summary_json}")
    print(f"client_preview_export_audit_340g_manifest_json: {manifest_json}")
    print(f"client_preview_export_audit_340g_qa_json: {qa_json}")
    print(f"client_preview_export_audit_340g_report_md: {report_md}")
    print(f"client_preview_export_audit_340g_no_write_back_proof_json: {no_write_back_proof_json}")
    print(f"client_preview_export_audit_340g_xlsx: {workbook_xlsx}")
    for key in [
        "audited_core_metric_count",
        "confirmed_count",
        "corrected_count",
        "needs_review_count",
        "rejected_count",
        "duplicate_issue_count",
        "unit_issue_count",
        "missing_source_trace_count",
        "unsafe_claim_count",
        "qa_fail_count",
        "client_preview_audit_passed",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
