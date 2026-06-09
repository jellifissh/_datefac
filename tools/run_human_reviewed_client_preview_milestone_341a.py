from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.human_reviewed_client_preview_milestone_341a import (  # noqa: E402
    DEFAULT_CLIENT_PREVIEW_340F_DIR,
    DEFAULT_CLIENT_PREVIEW_AUDIT_340G_DIR,
    DEFAULT_FULL_HUMAN_REVIEW_APPLY_340D_DIR,
    DEFAULT_HUMAN_REVIEW_340B_DIR,
    DEFAULT_HUMAN_REVIEW_APPLY_340C_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_HUMAN_REVIEW_340E_DIR,
    build_human_reviewed_client_preview_milestone_341a,
)
from datefac.trust.human_reviewed_client_preview_milestone_341a_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 341A human-reviewed client preview milestone package.")
    parser.add_argument("--human-review-340b-dir", default=str(DEFAULT_HUMAN_REVIEW_340B_DIR))
    parser.add_argument("--human-review-apply-340c-dir", default=str(DEFAULT_HUMAN_REVIEW_APPLY_340C_DIR))
    parser.add_argument("--full-human-review-apply-340d-dir", default=str(DEFAULT_FULL_HUMAN_REVIEW_APPLY_340D_DIR))
    parser.add_argument("--post-human-review-340e-dir", default=str(DEFAULT_POST_HUMAN_REVIEW_340E_DIR))
    parser.add_argument("--client-preview-340f-dir", default=str(DEFAULT_CLIENT_PREVIEW_340F_DIR))
    parser.add_argument("--client-preview-audit-340g-dir", default=str(DEFAULT_CLIENT_PREVIEW_AUDIT_340G_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_human_reviewed_client_preview_milestone_341a(
        human_review_340b_dir=Path(args.human_review_340b_dir),
        human_review_apply_340c_dir=Path(args.human_review_apply_340c_dir),
        full_human_review_apply_340d_dir=Path(args.full_human_review_apply_340d_dir),
        post_human_review_340e_dir=Path(args.post_human_review_340e_dir),
        client_preview_340f_dir=Path(args.client_preview_340f_dir),
        client_preview_audit_340g_dir=Path(args.client_preview_audit_340g_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "human_reviewed_client_preview_milestone_341a_summary.json"
    manifest_json = output_dir / "human_reviewed_client_preview_milestone_341a_manifest.json"
    qa_json = output_dir / "human_reviewed_client_preview_milestone_341a_qa.json"
    report_md = output_dir / "human_reviewed_client_preview_milestone_341a_report.md"
    workbook_xlsx = output_dir / "human_reviewed_client_preview_milestone_341a.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"human_reviewed_client_preview_milestone_341a_summary_json: {summary_json}")
    print(f"human_reviewed_client_preview_milestone_341a_manifest_json: {manifest_json}")
    print(f"human_reviewed_client_preview_milestone_341a_qa_json: {qa_json}")
    print(f"human_reviewed_client_preview_milestone_341a_report_md: {report_md}")
    print(f"human_reviewed_client_preview_milestone_341a_xlsx: {workbook_xlsx}")
    for key in [
        "demo_ready",
        "client_preview_ready",
        "client_ready",
        "production_ready",
        "total_review_queue_count_340b",
        "reviewed_after_human_candidate_count_340d",
        "reviewed_after_human_total_count_340e",
        "client_preview_core_metric_count_340f",
        "audited_core_metric_count_340g",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
