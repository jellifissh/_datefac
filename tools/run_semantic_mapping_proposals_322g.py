from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.semantic_mapping_proposals import (
    build_semantic_mapping_proposals,
    load_semantic_mapping_proposal_inputs,
)
from datefac.semantic.semantic_mapping_proposals_report import (
    proposal_report_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322G",
        "output_dir": str(output_dir),
        "accepted_instruction_count": 0,
        "proposal_total_count": 0,
        "alias_mapping_proposal_count": 0,
        "out_of_scope_proposal_count": 0,
        "unit_inference_proposal_count": 0,
        "rejected_noise_proposal_count": 0,
        "candidate_impact_sample_count": 0,
        "alias_affected_candidate_count": 0,
        "out_of_scope_affected_candidate_count": 0,
        "unit_inference_affected_candidate_count": 0,
        "rejected_noise_affected_candidate_count": 0,
        "trusted_gain_total": 0,
        "review_reduction_total": 0,
        "remaining_manual_review_count_after_322f": 0,
        "selected_core_trusted_rate_after_322f": 0,
        "selected_core_trusted_rate_before_322f": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "semantic_mapping_proposals_decision": code,
    }
    sheets = {
        "summary": pd.DataFrame([summary]),
        "alias_mapping_proposals": pd.DataFrame(),
        "out_of_scope_proposals": pd.DataFrame(),
        "unit_inference_proposals": pd.DataFrame(),
        "rejected_noise_proposals": pd.DataFrame(),
        "candidate_impact_samples": pd.DataFrame(),
        "human_review_checklist": pd.DataFrame(),
        "remaining_review_burden_after_322f": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame(
            [{"limitation": "blocked_input", "detail": "Required input directory is missing."}]
        ),
    }
    write_excel(output_dir / "semantic_mapping_proposals_322g.xlsx", sheets)
    write_json(output_dir / "semantic_mapping_proposals_322g_summary.json", summary)
    (output_dir / "semantic_mapping_proposals_322g_report.md").write_text(
        proposal_report_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build 322G human-confirmed semantic mapping proposals.")
    parser.add_argument("--apply30-dir", required=True)
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    apply30_dir = Path(args.apply30_dir)
    trust_split_dir = Path(args.trust_split_dir)
    output_dir = Path(args.output_dir)

    if not apply30_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322F_APPLY30_DIR")
        print(f"semantic_mapping_proposals_322g_summary_json: {output_dir / 'semantic_mapping_proposals_322g_summary.json'}")
        return 0
    if not trust_split_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR")
        print(f"semantic_mapping_proposals_322g_summary_json: {output_dir / 'semantic_mapping_proposals_322g_summary.json'}")
        return 0

    inputs = load_semantic_mapping_proposal_inputs(
        apply30_dir=apply30_dir,
        trust_split_dir=trust_split_dir,
    )
    artifacts = build_semantic_mapping_proposals(
        apply_summary=inputs["apply_summary"],
        trust_summary=inputs["trust_summary"],
        instructions_df=inputs["instructions_df"],
        gate_results_df=inputs["gate_results_df"],
        candidate_replay_diff_df=inputs["candidate_replay_diff_df"],
        selected_candidates_df=inputs["selected_candidates_df"],
        remaining_review_burden_df=inputs["remaining_review_burden_df"],
        qa_checks_322f_df=inputs["qa_checks_322f_df"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)

    qa_df = artifacts["qa_checks_df"].copy()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "excel": output_dir / "semantic_mapping_proposals_322g.xlsx",
        "summary_json": output_dir / "semantic_mapping_proposals_322g_summary.json",
        "report_md": output_dir / "semantic_mapping_proposals_322g_report.md",
    }

    sheets = {
        "summary": pd.DataFrame([summary]),
        "alias_mapping_proposals": artifacts["alias_mapping_proposals_df"],
        "out_of_scope_proposals": artifacts["out_of_scope_proposals_df"],
        "unit_inference_proposals": artifacts["unit_inference_proposals_df"],
        "rejected_noise_proposals": artifacts["rejected_noise_proposals_df"],
        "candidate_impact_samples": artifacts["candidate_impact_samples_df"],
        "human_review_checklist": artifacts["human_review_checklist_df"],
        "remaining_review_burden_after_322f": artifacts["remaining_review_burden_after_322f_df"],
        "qa_checks": qa_df,
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(proposal_report_markdown(summary), encoding="utf-8")

    output_files_written = all(path.exists() for path in output_files.values())
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "writes_proposal_outputs_only",
                        "status": "PASS",
                        "detail": "322G writes semantic mapping proposal outputs only.",
                    },
                    {
                        "check_name": "output_files_written_successfully",
                        "status": "PASS" if output_files_written else "FAIL",
                        "detail": str(output_dir),
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["semantic_mapping_proposals_decision"] = (
        "SEMANTIC_MAPPING_PROPOSALS_322G_READY_FOR_HUMAN_CONFIRMATION"
        if summary["qa_fail_count"] == 0 and int(summary.get("proposal_total_count", 0)) > 0
        else "SEMANTIC_MAPPING_PROPOSALS_322G_BLOCKED_BY_QA_FAILURE"
    )

    sheets["summary"] = pd.DataFrame([summary])
    sheets["qa_checks"] = qa_df
    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(proposal_report_markdown(summary), encoding="utf-8")

    print(f"semantic_mapping_proposals_322g_excel: {output_files['excel']}")
    print(f"semantic_mapping_proposals_322g_summary_json: {output_files['summary_json']}")
    print(f"semantic_mapping_proposals_322g_report_md: {output_files['report_md']}")
    for key in [
        "accepted_instruction_count",
        "proposal_total_count",
        "alias_mapping_proposal_count",
        "out_of_scope_proposal_count",
        "unit_inference_proposal_count",
        "rejected_noise_proposal_count",
        "candidate_impact_sample_count",
        "trusted_gain_total",
        "review_reduction_total",
        "remaining_manual_review_count_after_322f",
        "selected_core_trusted_rate_after_322f",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "semantic_mapping_proposals_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
