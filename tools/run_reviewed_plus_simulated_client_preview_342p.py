from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.reviewed_plus_simulated_client_preview_342p import (  # noqa: E402
    DEFAULT_ADOPTION_SIMULATION_342N_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR,
    DEFAULT_POST_HUMAN_SIDECAR_342I_DIR,
    DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    build_reviewed_plus_simulated_client_preview_342p,
)
from datefac.benchmark.reviewed_plus_simulated_client_preview_342p_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342P reviewed plus simulated client preview pilot.")
    parser.add_argument("--post-adoption-sidecar-342o-dir", default=str(DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR))
    parser.add_argument("--reviewed-preview-342j-dir", default=str(DEFAULT_REVIEWED_PREVIEW_342J_DIR))
    parser.add_argument("--post-human-sidecar-342i-dir", default=str(DEFAULT_POST_HUMAN_SIDECAR_342I_DIR))
    parser.add_argument("--adoption-simulation-342n-dir", default=str(DEFAULT_ADOPTION_SIMULATION_342N_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_reviewed_plus_simulated_client_preview_342p(
        post_adoption_sidecar_342o_dir=Path(args.post_adoption_sidecar_342o_dir),
        reviewed_preview_342j_dir=Path(args.reviewed_preview_342j_dir),
        post_human_sidecar_342i_dir=Path(args.post_human_sidecar_342i_dir),
        adoption_simulation_342n_dir=Path(args.adoption_simulation_342n_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    summary_json = output_dir / "reviewed_plus_simulated_client_preview_342p_summary.json"
    manifest_json = output_dir / "reviewed_plus_simulated_client_preview_342p_manifest.json"
    qa_json = output_dir / "reviewed_plus_simulated_client_preview_342p_qa.json"
    no_write_back_json = output_dir / "reviewed_plus_simulated_client_preview_342p_no_write_back_proof.json"
    report_md = output_dir / "reviewed_plus_simulated_client_preview_342p_report.md"
    workbook_xlsx = output_dir / "reviewed_plus_simulated_client_preview_342p.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"reviewed_plus_simulated_client_preview_342p_summary_json: {summary_json}")
    print(f"reviewed_plus_simulated_client_preview_342p_manifest_json: {manifest_json}")
    print(f"reviewed_plus_simulated_client_preview_342p_qa_json: {qa_json}")
    print(f"reviewed_plus_simulated_client_preview_342p_no_write_back_proof_json: {no_write_back_json}")
    print(f"reviewed_plus_simulated_client_preview_342p_report_md: {report_md}")
    print(f"reviewed_plus_simulated_client_preview_342p_xlsx: {workbook_xlsx}")
    for key in [
        "decision",
        "human_reviewed_preview_count",
        "simulated_preview_count",
        "simulated_direct_preview_count",
        "simulated_corrected_preview_count",
        "combined_preview_row_count",
        "still_human_required_count",
        "remaining_review_count",
        "metric_covered_count",
        "metric_year_pair_count",
        "duplicate_review_item_id_count",
        "duplicate_metric_year_source_count",
        "human_over_simulation_override_count",
        "simulated_duplicate_dropped_count",
        "ready_for_342q",
        "recommended_342q_scope",
        "client_ready",
        "production_ready",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
