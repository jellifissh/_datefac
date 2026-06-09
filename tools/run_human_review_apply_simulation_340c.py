from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.human_review_apply_simulation_340c import (  # noqa: E402
    DEFAULT_AI_ADOPTION_338D_DIR,
    DEFAULT_HUMAN_REVIEW_340B_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_STRICTNESS_337D_DIR,
    build_human_review_apply_simulation_340c,
)
from datefac.trust.human_review_apply_simulation_340c_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 340C human review apply simulation after AI adoption.")
    parser.add_argument("--human-review-340b-dir", default=str(DEFAULT_HUMAN_REVIEW_340B_DIR))
    parser.add_argument("--reviewed-strictness-337d-dir", default=str(DEFAULT_REVIEWED_STRICTNESS_337D_DIR))
    parser.add_argument("--ai-adoption-338d-dir", default=str(DEFAULT_AI_ADOPTION_338D_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_human_review_apply_simulation_340c(
        human_review_340b_dir=Path(args.human_review_340b_dir),
        reviewed_strictness_337d_dir=Path(args.reviewed_strictness_337d_dir),
        ai_adoption_338d_dir=Path(args.ai_adoption_338d_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "human_review_apply_simulation_340c_summary.json"
    manifest_json = output_dir / "human_review_apply_simulation_340c_manifest.json"
    qa_json = output_dir / "human_review_apply_simulation_340c_qa.json"
    no_apply_proof_json = output_dir / "human_review_apply_simulation_340c_no_apply_proof.json"
    apply_plan_xlsx = output_dir / "human_review_apply_simulation_340c_apply_plan.xlsx"
    report_md = output_dir / "human_review_apply_simulation_340c_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_proof_json, artifacts["no_apply_proof_json"])
    write_excel(apply_plan_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"human_review_apply_simulation_340c_summary_json: {summary_json}")
    print(f"human_review_apply_simulation_340c_manifest_json: {manifest_json}")
    print(f"human_review_apply_simulation_340c_qa_json: {qa_json}")
    print(f"human_review_apply_simulation_340c_no_apply_proof_json: {no_apply_proof_json}")
    print(f"human_review_apply_simulation_340c_apply_plan_xlsx: {apply_plan_xlsx}")
    print(f"human_review_apply_simulation_340c_report_md: {report_md}")
    for key in [
        "total_review_queue_count",
        "filled_review_row_count",
        "pending_review_row_count",
        "confirm_as_reviewed_count",
        "correct_and_confirm_count",
        "validation_warning_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
