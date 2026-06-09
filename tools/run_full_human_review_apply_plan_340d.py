from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.full_human_review_apply_plan_340d import (  # noqa: E402
    DEFAULT_AI_ADOPTION_338D_DIR,
    DEFAULT_HUMAN_REVIEW_340B_DIR,
    DEFAULT_HUMAN_REVIEW_APPLY_340C_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_STRICTNESS_337D_DIR,
    build_full_human_review_apply_plan_340d,
)
from datefac.trust.full_human_review_apply_plan_340d_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 340D full human review apply plan.")
    parser.add_argument("--human-review-340b-dir", default=str(DEFAULT_HUMAN_REVIEW_340B_DIR))
    parser.add_argument("--human-review-apply-340c-dir", default=str(DEFAULT_HUMAN_REVIEW_APPLY_340C_DIR))
    parser.add_argument("--reviewed-strictness-337d-dir", default=str(DEFAULT_REVIEWED_STRICTNESS_337D_DIR))
    parser.add_argument("--ai-adoption-338d-dir", default=str(DEFAULT_AI_ADOPTION_338D_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_full_human_review_apply_plan_340d(
        human_review_340b_dir=Path(args.human_review_340b_dir),
        human_review_apply_340c_dir=Path(args.human_review_apply_340c_dir),
        reviewed_strictness_337d_dir=Path(args.reviewed_strictness_337d_dir),
        ai_adoption_338d_dir=Path(args.ai_adoption_338d_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "full_human_review_apply_plan_340d_summary.json"
    manifest_json = output_dir / "full_human_review_apply_plan_340d_manifest.json"
    qa_json = output_dir / "full_human_review_apply_plan_340d_qa.json"
    no_apply_proof_json = output_dir / "full_human_review_apply_plan_340d_no_apply_proof.json"
    report_md = output_dir / "full_human_review_apply_plan_340d_report.md"
    workbook_xlsx = output_dir / "full_human_review_apply_plan_340d.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_proof_json, artifacts["no_apply_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"full_human_review_apply_plan_340d_summary_json: {summary_json}")
    print(f"full_human_review_apply_plan_340d_manifest_json: {manifest_json}")
    print(f"full_human_review_apply_plan_340d_qa_json: {qa_json}")
    print(f"full_human_review_apply_plan_340d_no_apply_proof_json: {no_apply_proof_json}")
    print(f"full_human_review_apply_plan_340d_report_md: {report_md}")
    print(f"full_human_review_apply_plan_340d_xlsx: {workbook_xlsx}")
    for key in [
        "total_review_queue_count",
        "final_confirm_count",
        "final_correct_and_confirm_count",
        "final_reject_count",
        "final_keep_needs_review_count",
        "final_reviewed_after_human_candidate_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
