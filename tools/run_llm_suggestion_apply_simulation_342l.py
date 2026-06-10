from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.llm_suggestion_apply_simulation_342l import (  # noqa: E402
    DEFAULT_LLM_REVIEW_342K_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    build_llm_suggestion_apply_simulation_342l,
)
from datefac.benchmark.llm_suggestion_apply_simulation_342l_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342L LLM suggestion apply simulation.")
    parser.add_argument("--llm-review-342k-dir", default=str(DEFAULT_LLM_REVIEW_342K_DIR))
    parser.add_argument("--reviewed-preview-342j-dir", default=str(DEFAULT_REVIEWED_PREVIEW_342J_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    artifacts = build_llm_suggestion_apply_simulation_342l(
        llm_review_342k_dir=Path(args.llm_review_342k_dir),
        reviewed_preview_342j_dir=Path(args.reviewed_preview_342j_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "llm_suggestion_apply_simulation_342l_summary.json"
    manifest_json = output_dir / "llm_suggestion_apply_simulation_342l_manifest.json"
    qa_json = output_dir / "llm_suggestion_apply_simulation_342l_qa.json"
    no_write_back_json = output_dir / "llm_suggestion_apply_simulation_342l_no_write_back_proof.json"
    report_md = output_dir / "llm_suggestion_apply_simulation_342l_report.md"
    workbook_xlsx = output_dir / "llm_suggestion_apply_simulation_342l.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"llm_suggestion_apply_simulation_342l_summary_json: {summary_json}")
    print(f"llm_suggestion_apply_simulation_342l_manifest_json: {manifest_json}")
    print(f"llm_suggestion_apply_simulation_342l_qa_json: {qa_json}")
    print(f"llm_suggestion_apply_simulation_342l_no_write_back_proof_json: {no_write_back_json}")
    print(f"llm_suggestion_apply_simulation_342l_report_md: {report_md}")
    print(f"llm_suggestion_apply_simulation_342l_xlsx: {workbook_xlsx}")
    for key in [
        "decision",
        "pending_review_count",
        "auto_confirm_candidate_count",
        "spot_check_sample_count",
        "human_required_count",
        "conflict_count",
        "prefill_review_draft_count",
        "prompt_pack_count",
        "request_pack_count",
        "jsonl_parse_error_count",
        "theoretical_review_reduction_count",
        "risk_adjusted_reduction_count",
        "required_human_review_after_strategy",
        "reduction_rate",
        "conservative_reduction_rate",
        "ready_for_342m",
        "recommended_342m_scope",
        "client_ready",
        "production_ready",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
