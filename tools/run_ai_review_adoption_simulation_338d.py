from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.ai_review_adoption_simulation_338d import (  # noqa: E402
    DEFAULT_GROUNDED_AI_REVIEW_338C_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_STRICTNESS_337D_DIR,
    build_ai_review_adoption_simulation_338d,
)
from datefac.trust.ai_review_adoption_simulation_338d_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 338D AI review adoption simulation.")
    parser.add_argument("--grounded-ai-review-338c-dir", default=str(DEFAULT_GROUNDED_AI_REVIEW_338C_DIR))
    parser.add_argument("--reviewed-strictness-337d-dir", default=str(DEFAULT_REVIEWED_STRICTNESS_337D_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    grounded_ai_review_338c_dir = Path(args.grounded_ai_review_338c_dir)
    reviewed_strictness_337d_dir = Path(args.reviewed_strictness_337d_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_ai_review_adoption_simulation_338d(
        grounded_ai_review_338c_dir=grounded_ai_review_338c_dir,
        reviewed_strictness_337d_dir=reviewed_strictness_337d_dir,
        output_dir=output_dir,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "ai_review_adoption_simulation_338d_summary.json"
    manifest_json = output_dir / "ai_review_adoption_simulation_338d_manifest.json"
    qa_json = output_dir / "ai_review_adoption_simulation_338d_qa.json"
    report_md = output_dir / "ai_review_adoption_simulation_338d_report.md"
    plan_xlsx = output_dir / "ai_review_adoption_simulation_338d_plan.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_excel(plan_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"ai_review_adoption_simulation_338d_summary_json: {summary_json}")
    print(f"ai_review_adoption_simulation_338d_manifest_json: {manifest_json}")
    print(f"ai_review_adoption_simulation_338d_qa_json: {qa_json}")
    print(f"ai_review_adoption_simulation_338d_report_md: {report_md}")
    print(f"ai_review_adoption_simulation_338d_plan_xlsx: {plan_xlsx}")
    for key in [
        "input_338c_row_count",
        "accept_model_confirm_count",
        "accept_model_downgrade_count",
        "accept_model_reject_count",
        "hold_for_human_review_count",
        "reject_by_deterministic_rule_count",
        "invalid_model_response_count",
        "deterministic_rule_override_count",
        "suggest_set_ai_review_model_default",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
