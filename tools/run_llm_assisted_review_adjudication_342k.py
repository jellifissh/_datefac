from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.llm_assisted_review_adjudication_342k import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_HUMAN_REVIEW_342I_DIR,
    DEFAULT_REVIEW_PACKAGE_342G_DIR,
    DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    build_llm_assisted_review_adjudication_342k,
)
from datefac.benchmark.llm_assisted_review_adjudication_342k_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342K LLM-assisted review adjudication pilot.")
    parser.add_argument("--reviewed-preview-342j-dir", default=str(DEFAULT_REVIEWED_PREVIEW_342J_DIR))
    parser.add_argument("--post-human-review-342i-dir", default=str(DEFAULT_POST_HUMAN_REVIEW_342I_DIR))
    parser.add_argument("--review-package-342g-dir", default=str(DEFAULT_REVIEW_PACKAGE_342G_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_llm_assisted_review_adjudication_342k(
        reviewed_preview_342j_dir=Path(args.reviewed_preview_342j_dir),
        post_human_review_342i_dir=Path(args.post_human_review_342i_dir),
        review_package_342g_dir=Path(args.review_package_342g_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "llm_assisted_review_adjudication_342k_summary.json"
    manifest_json = output_dir / "llm_assisted_review_adjudication_342k_manifest.json"
    qa_json = output_dir / "llm_assisted_review_adjudication_342k_qa.json"
    no_write_back_json = output_dir / "llm_assisted_review_adjudication_342k_no_write_back_proof.json"
    report_md = output_dir / "llm_assisted_review_adjudication_342k_report.md"
    workbook_xlsx = output_dir / "llm_assisted_review_adjudication_342k.xlsx"
    prompt_pack_jsonl = output_dir / "llm_assisted_review_adjudication_342k_prompt_pack.jsonl"
    request_pack_jsonl = output_dir / "llm_assisted_review_adjudication_342k_request_pack.jsonl"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    write_jsonl(prompt_pack_jsonl, artifacts["prompt_pack_rows"])
    write_jsonl(request_pack_jsonl, artifacts["request_pack_rows"])
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"llm_assisted_review_adjudication_342k_summary_json: {summary_json}")
    print(f"llm_assisted_review_adjudication_342k_manifest_json: {manifest_json}")
    print(f"llm_assisted_review_adjudication_342k_qa_json: {qa_json}")
    print(f"llm_assisted_review_adjudication_342k_no_write_back_proof_json: {no_write_back_json}")
    print(f"llm_assisted_review_adjudication_342k_report_md: {report_md}")
    print(f"llm_assisted_review_adjudication_342k_xlsx: {workbook_xlsx}")
    print(f"llm_assisted_review_adjudication_342k_prompt_pack_jsonl: {prompt_pack_jsonl}")
    print(f"llm_assisted_review_adjudication_342k_request_pack_jsonl: {request_pack_jsonl}")
    for key in [
        "decision",
        "pending_review_count",
        "llm_candidate_pool_count",
        "prompt_package_count",
        "request_pack_count",
        "rule_baseline_count",
        "dry_run_suggestion_count",
        "human_required_count",
        "auto_confirm_candidate_count",
        "conflict_count",
        "unit_year_risk_count",
        "duplicate_risk_count",
        "growth_row_risk_count",
        "source_trace_risk_count",
        "metric_mapping_risk_count",
        "ready_for_342l",
        "recommended_342l_scope",
        "client_ready",
        "production_ready",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
