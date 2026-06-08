from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.ai_review_model_ab_338b import (  # noqa: E402
    DEFAULT_BASELINE_338A_DIR,
    DEFAULT_LIMIT,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_STRICTNESS_337D_DIR,
    DEFAULT_TIMEOUT_SECONDS,
    build_ai_review_model_ab_338b,
)
from datefac.trust.ai_review_model_ab_338b_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 338B AI review model adapter and A/B evaluation.")
    parser.add_argument("--baseline-338a-dir", default=str(DEFAULT_BASELINE_338A_DIR))
    parser.add_argument("--reviewed-strictness-337d-dir", default=str(DEFAULT_REVIEWED_STRICTNESS_337D_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--dry-run-prompts-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    baseline_338a_dir = Path(args.baseline_338a_dir)
    reviewed_strictness_337d_dir = Path(args.reviewed_strictness_337d_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_ai_review_model_ab_338b(
        baseline_338a_dir=baseline_338a_dir,
        reviewed_strictness_337d_dir=reviewed_strictness_337d_dir,
        output_dir=output_dir,
        limit=args.limit,
        dry_run_prompts_only=args.dry_run_prompts_only,
        timeout_seconds=args.timeout_seconds,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "ai_review_model_ab_338b_summary.json"
    manifest_json = output_dir / "ai_review_model_ab_338b_manifest.json"
    qa_json = output_dir / "ai_review_model_ab_338b_qa.json"
    report_md = output_dir / "ai_review_model_ab_338b_report.md"
    plan_xlsx = output_dir / "ai_review_model_ab_338b_plan.xlsx"
    cache_jsonl = output_dir / "ai_review_model_ab_338b_cache.jsonl"
    prompt_preview_jsonl = output_dir / "ai_review_model_ab_338b_prompt_preview.jsonl"

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
    print(f"ai_review_model_ab_338b_summary_json: {summary_json}")
    print(f"ai_review_model_ab_338b_manifest_json: {manifest_json}")
    print(f"ai_review_model_ab_338b_qa_json: {qa_json}")
    print(f"ai_review_model_ab_338b_report_md: {report_md}")
    print(f"ai_review_model_ab_338b_plan_xlsx: {plan_xlsx}")
    print(f"ai_review_model_ab_338b_cache_jsonl: {cache_jsonl}")
    print(f"ai_review_model_ab_338b_prompt_preview_jsonl: {prompt_preview_jsonl}")
    for key in [
        "env_source",
        "api_env_ready",
        "baseline_model_name",
        "new_model_name",
        "row_count",
        "api_call_count",
        "cache_hit_count",
        "low_confidence_count_baseline",
        "low_confidence_count_new",
        "needs_more_context_count_baseline",
        "needs_more_context_count_new",
        "confirm_reviewed_count_baseline",
        "confirm_reviewed_count_new",
        "downgrade_count_baseline",
        "downgrade_count_new",
        "reject_count_baseline",
        "reject_count_new",
        "invalid_response_count_baseline",
        "invalid_response_count_new",
        "evidence_quote_valid_count",
        "evidence_quote_invalid_count",
        "recommendation",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
