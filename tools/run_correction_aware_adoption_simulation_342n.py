from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.correction_aware_adoption_simulation_342n import (  # noqa: E402
    DEFAULT_LLM_REVIEW_342K_DIR,
    DEFAULT_LLM_SUGGESTION_342L_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    DEFAULT_SPOT_CHECK_GATE_342M_DIR,
    build_correction_aware_adoption_simulation_342n,
)
from datefac.benchmark.correction_aware_adoption_simulation_342n_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342N correction-aware adoption simulation.")
    parser.add_argument("--spot-check-gate-342m-dir", default=str(DEFAULT_SPOT_CHECK_GATE_342M_DIR))
    parser.add_argument("--llm-suggestion-342l-dir", default=str(DEFAULT_LLM_SUGGESTION_342L_DIR))
    parser.add_argument("--llm-review-342k-dir", default=str(DEFAULT_LLM_REVIEW_342K_DIR))
    parser.add_argument("--reviewed-preview-342j-dir", default=str(DEFAULT_REVIEWED_PREVIEW_342J_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_correction_aware_adoption_simulation_342n(
        spot_check_gate_342m_dir=Path(args.spot_check_gate_342m_dir),
        llm_suggestion_342l_dir=Path(args.llm_suggestion_342l_dir),
        llm_review_342k_dir=Path(args.llm_review_342k_dir),
        reviewed_preview_342j_dir=Path(args.reviewed_preview_342j_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    summary_json = output_dir / "correction_aware_adoption_simulation_342n_summary.json"
    manifest_json = output_dir / "correction_aware_adoption_simulation_342n_manifest.json"
    qa_json = output_dir / "correction_aware_adoption_simulation_342n_qa.json"
    no_write_back_json = output_dir / "correction_aware_adoption_simulation_342n_no_write_back_proof.json"
    report_md = output_dir / "correction_aware_adoption_simulation_342n_report.md"
    workbook_xlsx = output_dir / "correction_aware_adoption_simulation_342n.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"correction_aware_adoption_simulation_342n_summary_json: {summary_json}")
    print(f"correction_aware_adoption_simulation_342n_manifest_json: {manifest_json}")
    print(f"correction_aware_adoption_simulation_342n_qa_json: {qa_json}")
    print(f"correction_aware_adoption_simulation_342n_no_write_back_proof_json: {no_write_back_json}")
    print(f"correction_aware_adoption_simulation_342n_report_md: {report_md}")
    print(f"correction_aware_adoption_simulation_342n_xlsx: {workbook_xlsx}")
    for key in [
        "decision",
        "pending_review_count",
        "input_adoption_candidate_count",
        "spot_check_sample_count",
        "spot_check_confirm_count",
        "spot_check_correct_count",
        "spot_check_correction_rate",
        "direct_adopt_sim_count",
        "correction_adopt_sim_count",
        "still_human_required_count",
        "adoption_sim_total_count",
        "risk_adjusted_reduction_count",
        "required_human_review_after_342n",
        "conservative_reduction_rate_after_342n",
        "ready_for_342o",
        "recommended_342o_scope",
        "client_ready",
        "production_ready",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
