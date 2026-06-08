from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.deepseek_text_adjudicator_338a import (  # noqa: E402
    DEFAULT_LIMIT,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_STRICTNESS_337D_DIR,
    DEFAULT_TIMEOUT_SECONDS,
    build_deepseek_text_adjudicator_338a,
)
from datefac.trust.deepseek_text_adjudicator_338a_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 338A DeepSeek text adjudicator dry run.")
    parser.add_argument("--reviewed-strictness-337d-dir", default=str(DEFAULT_REVIEWED_STRICTNESS_337D_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--dry-run-prompts-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    reviewed_strictness_337d_dir = Path(args.reviewed_strictness_337d_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_deepseek_text_adjudicator_338a(
        reviewed_strictness_337d_dir=reviewed_strictness_337d_dir,
        output_dir=output_dir,
        limit=args.limit,
        dry_run_prompts_only=args.dry_run_prompts_only,
        timeout_seconds=args.timeout_seconds,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "deepseek_text_adjudicator_338a_summary.json"
    manifest_json = output_dir / "deepseek_text_adjudicator_338a_manifest.json"
    qa_json = output_dir / "deepseek_text_adjudicator_338a_qa.json"
    report_md = output_dir / "deepseek_text_adjudicator_338a_report.md"
    plan_xlsx = output_dir / "deepseek_text_adjudication_plan_338a.xlsx"
    cache_jsonl = output_dir / "deepseek_text_adjudication_cache_338a.jsonl"
    prompt_preview_jsonl = output_dir / "deepseek_text_adjudication_prompts_preview_338a.jsonl"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_excel(plan_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    prompt_preview_jsonl.write_text(
        "\n".join(__import__("json").dumps(row, ensure_ascii=False) for row in artifacts["prompt_preview_rows"]) + ("\n" if artifacts["prompt_preview_rows"] else ""),
        encoding="utf-8",
    )
    cache_jsonl.write_text(
        "\n".join(__import__("json").dumps(row, ensure_ascii=False) for row in artifacts["cache_rows"]) + ("\n" if artifacts["cache_rows"] else ""),
        encoding="utf-8",
    )
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"deepseek_text_adjudicator_338a_summary_json: {summary_json}")
    print(f"deepseek_text_adjudicator_338a_manifest_json: {manifest_json}")
    print(f"deepseek_text_adjudicator_338a_qa_json: {qa_json}")
    print(f"deepseek_text_adjudicator_338a_report_md: {report_md}")
    print(f"deepseek_text_adjudication_plan_338a_xlsx: {plan_xlsx}")
    print(f"deepseek_text_adjudication_cache_338a_jsonl: {cache_jsonl}")
    print(f"deepseek_text_adjudication_prompts_preview_338a_jsonl: {prompt_preview_jsonl}")
    for key in [
        "api_env_ready",
        "model_name",
        "adjudication_row_count",
        "api_call_count",
        "cache_hit_count",
        "confirm_reviewed_count",
        "downgrade_to_needs_review_count",
        "reject_count",
        "needs_more_context_count",
        "invalid_response_count",
        "low_confidence_count",
        "rule_model_conflict_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
