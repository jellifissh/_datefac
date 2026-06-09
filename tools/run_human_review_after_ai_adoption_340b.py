from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.human_review_after_ai_adoption_340b import (  # noqa: E402
    DEFAULT_AI_ADOPTION_338D_DIR,
    DEFAULT_MILESTONE_AUDIT_340A_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_STRICTNESS_337D_DIR,
    build_human_review_after_ai_adoption_340b,
)
from datefac.trust.human_review_after_ai_adoption_340b_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 340B human review package after AI adoption.")
    parser.add_argument("--reviewed-strictness-337d-dir", default=str(DEFAULT_REVIEWED_STRICTNESS_337D_DIR))
    parser.add_argument("--ai-adoption-338d-dir", default=str(DEFAULT_AI_ADOPTION_338D_DIR))
    parser.add_argument("--milestone-audit-340a-dir", default=str(DEFAULT_MILESTONE_AUDIT_340A_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_human_review_after_ai_adoption_340b(
        reviewed_strictness_337d_dir=Path(args.reviewed_strictness_337d_dir),
        ai_adoption_338d_dir=Path(args.ai_adoption_338d_dir),
        milestone_audit_340a_dir=Path(args.milestone_audit_340a_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "human_review_after_ai_adoption_340b_summary.json"
    manifest_json = output_dir / "human_review_after_ai_adoption_340b_manifest.json"
    qa_json = output_dir / "human_review_after_ai_adoption_340b_qa.json"
    no_apply_proof_json = output_dir / "human_review_after_ai_adoption_340b_no_apply_proof.json"
    report_md = output_dir / "human_review_after_ai_adoption_340b_report.md"
    workbook_xlsx = output_dir / "human_review_after_ai_adoption_340b_review_template.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_proof_json, artifacts["no_apply_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"human_review_after_ai_adoption_340b_summary_json: {summary_json}")
    print(f"human_review_after_ai_adoption_340b_manifest_json: {manifest_json}")
    print(f"human_review_after_ai_adoption_340b_qa_json: {qa_json}")
    print(f"human_review_after_ai_adoption_340b_no_apply_proof_json: {no_apply_proof_json}")
    print(f"human_review_after_ai_adoption_340b_report_md: {report_md}")
    print(f"human_review_after_ai_adoption_340b_review_template_xlsx: {workbook_xlsx}")
    for key in [
        "total_review_queue_count",
        "hold_for_human_count",
        "invalid_model_response_count",
        "rejected_by_rule_check_count",
        "accepted_confirm_spot_check_count",
        "accepted_reject_spot_check_count",
        "reviewer_fields_present",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
