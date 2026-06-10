from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.llm_suggestion_spot_check_gate_342m import (  # noqa: E402
    DEFAULT_LLM_RESPONSE_DIR,
    DEFAULT_LLM_REVIEW_342K_DIR,
    DEFAULT_LLM_SUGGESTION_342L_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    DEFAULT_SPOT_CHECK_REVIEWED_DIR,
    REAL_RESPONSE_SCHEMA_NAME,
    REAL_RESPONSE_TEMPLATE_NAME,
    SPOT_CHECK_TEMPLATE_WORKBOOK_NAME,
    build_llm_suggestion_spot_check_gate_342m,
)
from datefac.benchmark.llm_suggestion_spot_check_gate_342m_report import (  # noqa: E402
    TEMPLATE_WORKBOOK_SHEETS,
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342M LLM suggestion spot-check gate.")
    parser.add_argument("--llm-suggestion-342l-dir", default=str(DEFAULT_LLM_SUGGESTION_342L_DIR))
    parser.add_argument("--llm-review-342k-dir", default=str(DEFAULT_LLM_REVIEW_342K_DIR))
    parser.add_argument("--reviewed-preview-342j-dir", default=str(DEFAULT_REVIEWED_PREVIEW_342J_DIR))
    parser.add_argument("--spot-check-reviewed-dir", default=str(DEFAULT_SPOT_CHECK_REVIEWED_DIR))
    parser.add_argument("--llm-response-dir", default=str(DEFAULT_LLM_RESPONSE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_llm_suggestion_spot_check_gate_342m(
        llm_suggestion_342l_dir=Path(args.llm_suggestion_342l_dir),
        llm_review_342k_dir=Path(args.llm_review_342k_dir),
        reviewed_preview_342j_dir=Path(args.reviewed_preview_342j_dir),
        spot_check_reviewed_dir=Path(args.spot_check_reviewed_dir),
        llm_response_dir=Path(args.llm_response_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    summary_json = output_dir / "llm_suggestion_spot_check_gate_342m_summary.json"
    manifest_json = output_dir / "llm_suggestion_spot_check_gate_342m_manifest.json"
    qa_json = output_dir / "llm_suggestion_spot_check_gate_342m_qa.json"
    no_write_back_json = output_dir / "llm_suggestion_spot_check_gate_342m_no_write_back_proof.json"
    report_md = output_dir / "llm_suggestion_spot_check_gate_342m_report.md"
    workbook_xlsx = output_dir / "llm_suggestion_spot_check_gate_342m.xlsx"
    spot_template_xlsx = output_dir / SPOT_CHECK_TEMPLATE_WORKBOOK_NAME
    response_schema_json = output_dir / REAL_RESPONSE_SCHEMA_NAME
    response_template_jsonl = output_dir / REAL_RESPONSE_TEMPLATE_NAME

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    write_excel(spot_template_xlsx, artifacts["template_workbook_sheets"], TEMPLATE_WORKBOOK_SHEETS)
    write_json(response_schema_json, artifacts["real_llm_response_schema_json"])
    write_jsonl(response_template_jsonl, artifacts["real_llm_response_template_rows"])
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"llm_suggestion_spot_check_gate_342m_summary_json: {summary_json}")
    print(f"llm_suggestion_spot_check_gate_342m_manifest_json: {manifest_json}")
    print(f"llm_suggestion_spot_check_gate_342m_qa_json: {qa_json}")
    print(f"llm_suggestion_spot_check_gate_342m_no_write_back_proof_json: {no_write_back_json}")
    print(f"llm_suggestion_spot_check_gate_342m_report_md: {report_md}")
    print(f"llm_suggestion_spot_check_gate_342m_xlsx: {workbook_xlsx}")
    print(f"llm_suggestion_spot_check_review_template_342m_xlsx: {spot_template_xlsx}")
    print(f"real_llm_response_schema_342m_json: {response_schema_json}")
    print(f"real_llm_response_ingestion_template_342m_jsonl: {response_template_jsonl}")
    for key in [
        "decision",
        "pending_review_count",
        "auto_confirm_candidate_count",
        "spot_check_sample_count",
        "reviewed_spot_check_count",
        "response_count",
        "valid_llm_response_count",
        "adoption_candidate_count",
        "blocked_candidate_count",
        "risk_adjusted_reduction_count",
        "required_human_review_after_gate",
        "conservative_reduction_rate_after_gate",
        "waiting_for_human_spot_check",
        "waiting_for_real_llm_responses",
        "ready_for_342n",
        "recommended_342n_scope",
        "client_ready",
        "production_ready",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
