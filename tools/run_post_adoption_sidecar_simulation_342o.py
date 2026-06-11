from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.post_adoption_sidecar_simulation_342o import (  # noqa: E402
    DEFAULT_ADOPTION_SIMULATION_342N_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_HUMAN_SIDECAR_342I_DIR,
    DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    DEFAULT_SPOT_CHECK_GATE_342M_DIR,
    build_post_adoption_sidecar_simulation_342o,
)
from datefac.benchmark.post_adoption_sidecar_simulation_342o_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342O post-adoption sidecar simulation.")
    parser.add_argument("--adoption-simulation-342n-dir", default=str(DEFAULT_ADOPTION_SIMULATION_342N_DIR))
    parser.add_argument("--spot-check-gate-342m-dir", default=str(DEFAULT_SPOT_CHECK_GATE_342M_DIR))
    parser.add_argument("--reviewed-preview-342j-dir", default=str(DEFAULT_REVIEWED_PREVIEW_342J_DIR))
    parser.add_argument("--post-human-sidecar-342i-dir", default=str(DEFAULT_POST_HUMAN_SIDECAR_342I_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_post_adoption_sidecar_simulation_342o(
        adoption_simulation_342n_dir=Path(args.adoption_simulation_342n_dir),
        spot_check_gate_342m_dir=Path(args.spot_check_gate_342m_dir),
        reviewed_preview_342j_dir=Path(args.reviewed_preview_342j_dir),
        post_human_sidecar_342i_dir=Path(args.post_human_sidecar_342i_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    summary_json = output_dir / "post_adoption_sidecar_simulation_342o_summary.json"
    manifest_json = output_dir / "post_adoption_sidecar_simulation_342o_manifest.json"
    qa_json = output_dir / "post_adoption_sidecar_simulation_342o_qa.json"
    no_write_back_json = output_dir / "post_adoption_sidecar_simulation_342o_no_write_back_proof.json"
    report_md = output_dir / "post_adoption_sidecar_simulation_342o_report.md"
    workbook_xlsx = output_dir / "post_adoption_sidecar_simulation_342o.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"post_adoption_sidecar_simulation_342o_summary_json: {summary_json}")
    print(f"post_adoption_sidecar_simulation_342o_manifest_json: {manifest_json}")
    print(f"post_adoption_sidecar_simulation_342o_qa_json: {qa_json}")
    print(f"post_adoption_sidecar_simulation_342o_no_write_back_proof_json: {no_write_back_json}")
    print(f"post_adoption_sidecar_simulation_342o_report_md: {report_md}")
    print(f"post_adoption_sidecar_simulation_342o_xlsx: {workbook_xlsx}")
    for key in [
        "decision",
        "pending_review_count",
        "input_adoption_candidate_count",
        "direct_adopted_count",
        "corrected_adopted_count",
        "simulated_adopted_cell_count",
        "still_human_required_count",
        "remaining_review_count",
        "reduction_rate_after_342o",
        "metric_covered_count",
        "metric_year_pair_count",
        "REVENUE_AMOUNT_NOT_YOY_count",
        "REVENUE_YOY_PERCENT_count",
        "NET_PROFIT_YOY_PERCENT_count",
        "ready_for_342p",
        "recommended_342p_scope",
        "client_ready",
        "production_ready",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
