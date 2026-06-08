from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.grounded_ai_review_338c import (  # noqa: E402
    DEFAULT_AB_338B_DIR,
    DEFAULT_LIMIT,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_STRICTNESS_337D_DIR,
    DEFAULT_TIMEOUT_SECONDS,
    build_grounded_ai_review_338c,
)
from datefac.trust.grounded_ai_review_338c_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 338C grounded AI review schema tightening.")
    parser.add_argument("--ab-338b-dir", default=str(DEFAULT_AB_338B_DIR))
    parser.add_argument("--reviewed-strictness-337d-dir", default=str(DEFAULT_REVIEWED_STRICTNESS_337D_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--dry-run-prompts-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    ab_338b_dir = Path(args.ab_338b_dir)
    reviewed_strictness_337d_dir = Path(args.reviewed_strictness_337d_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_grounded_ai_review_338c(
        ab_338b_dir=ab_338b_dir,
        reviewed_strictness_337d_dir=reviewed_strictness_337d_dir,
        output_dir=output_dir,
        limit=args.limit,
        dry_run_prompts_only=args.dry_run_prompts_only,
        timeout_seconds=args.timeout_seconds,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "grounded_ai_review_338c_summary.json"
    manifest_json = output_dir / "grounded_ai_review_338c_manifest.json"
    qa_json = output_dir / "grounded_ai_review_338c_qa.json"
    report_md = output_dir / "grounded_ai_review_338c_report.md"
    plan_xlsx = output_dir / "grounded_ai_review_338c_plan.xlsx"
    cache_jsonl = output_dir / "grounded_ai_review_338c_cache.jsonl"
    prompt_preview_jsonl = output_dir / "grounded_ai_review_338c_prompt_preview.jsonl"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_excel(plan_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    prompt_preview_jsonl.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in artifacts["prompt_preview_rows"])
        + ("\n" if artifacts["prompt_preview_rows"] else ""),
        encoding="utf-8",
    )
    cache_jsonl.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in artifacts["cache_rows"])
        + ("\n" if artifacts["cache_rows"] else ""),
        encoding="utf-8",
    )
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"grounded_ai_review_338c_summary_json: {summary_json}")
    print(f"grounded_ai_review_338c_manifest_json: {manifest_json}")
    print(f"grounded_ai_review_338c_qa_json: {qa_json}")
    print(f"grounded_ai_review_338c_report_md: {report_md}")
    print(f"grounded_ai_review_338c_plan_xlsx: {plan_xlsx}")
    print(f"grounded_ai_review_338c_cache_jsonl: {cache_jsonl}")
    print(f"grounded_ai_review_338c_prompt_preview_jsonl: {prompt_preview_jsonl}")
    for key in [
        "model_name",
        "row_count",
        "invalid_response_count_338b",
        "invalid_response_count_338c",
        "confirm_reviewed_count_338b",
        "confirm_reviewed_count_338c",
        "needs_more_context_count_338b",
        "needs_more_context_count_338c",
        "raw_quote_valid_count",
        "context_quote_valid_count",
        "confirm_with_raw_evidence_count",
        "confirm_with_both_count",
        "confirm_with_context_only_count",
        "confirm_rejected_by_grounding_count",
        "rule_model_conflict_count",
        "final_recommendation",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
