from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.human_confirmed_patch_preview import (
    build_human_confirmed_patch_preview,
    load_human_confirmed_patch_inputs,
)
from datefac.semantic.human_confirmed_patch_report import (
    patch_preview_report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322H",
        "output_dir": str(output_dir),
        "reviewed_proposal_count": 0,
        "accepted_proposal_count": 0,
        "rejected_proposal_count": 0,
        "needs_more_info_proposal_count": 0,
        "accepted_alias_patch_count": 0,
        "accepted_out_of_scope_patch_count": 0,
        "accepted_unit_inference_patch_count": 0,
        "accepted_rejected_noise_patch_count": 0,
        "affected_candidate_count": 0,
        "trusted_total_before_322h": 0,
        "trusted_total_after_322h": 0,
        "review_required_total_before_322h": 0,
        "review_required_total_after_322h": 0,
        "rejected_total_before_322h": 0,
        "rejected_total_after_322h": 0,
        "trusted_gain_322h": 0,
        "review_reduction_322h": 0,
        "out_of_scope_or_rejected_gain_322h": 0,
        "selected_core_trusted_rate_before_322h": 0,
        "selected_core_trusted_rate_after_322h": 0,
        "remaining_unknown_metric_candidate_count": 0,
        "remaining_unit_unknown_candidate_count": 0,
        "remaining_manual_review_count": 0,
        "official_rule_candidate_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "human_confirmed_patch_preview_decision": code,
    }
    sheets = {
        "summary": pd.DataFrame([summary]),
        "reviewed_proposal_inventory": pd.DataFrame(),
        "alias_patch_preview": pd.DataFrame(),
        "out_of_scope_patch_preview": pd.DataFrame(),
        "unit_inference_patch_preview": pd.DataFrame(),
        "rejected_noise_patch_preview": pd.DataFrame(),
        "candidate_before_after_diff_322h": pd.DataFrame(),
        "trusted_after_patch_preview_322h": pd.DataFrame(),
        "review_required_after_patch_preview_322h": pd.DataFrame(),
        "rejected_after_patch_preview_322h": pd.DataFrame(),
        "patch_impact_by_proposal_322h": pd.DataFrame(),
        "remaining_review_burden_322h": pd.DataFrame(),
        "official_rule_candidate_preview": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input is missing."}]),
    }
    write_excel(output_dir / "human_confirmed_semantic_patch_preview_322h.xlsx", sheets)
    write_json(output_dir / "human_confirmed_semantic_patch_preview_322h_summary.json", summary)
    (output_dir / "human_confirmed_semantic_patch_preview_322h_report.md").write_text(
        patch_preview_report_markdown(summary),
        encoding="utf-8",
    )
    write_jsonl(output_dir / "candidate_before_after_diff_322h.jsonl", pd.DataFrame())
    write_jsonl(output_dir / "official_rule_candidate_preview_322h.jsonl", pd.DataFrame())
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322H human-confirmed semantic patch preview.")
    parser.add_argument("--reviewed-proposal-xlsx", required=True)
    parser.add_argument("--proposal-dir", required=True)
    parser.add_argument("--adjudicator-apply-dir", required=True)
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    reviewed_proposal_xlsx = Path(args.reviewed_proposal_xlsx)
    proposal_dir = Path(args.proposal_dir)
    adjudicator_apply_dir = Path(args.adjudicator_apply_dir)
    trust_split_dir = Path(args.trust_split_dir)
    output_dir = Path(args.output_dir)

    if not reviewed_proposal_xlsx.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_REVIEWED_PROPOSAL_XLSX")
        print(f"human_confirmed_patch_preview_322h_summary_json: {output_dir / 'human_confirmed_semantic_patch_preview_322h_summary.json'}")
        return 0
    if not proposal_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322G_PROPOSAL_DIR")
        print(f"human_confirmed_patch_preview_322h_summary_json: {output_dir / 'human_confirmed_semantic_patch_preview_322h_summary.json'}")
        return 0
    if not adjudicator_apply_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322F_APPLY_DIR")
        print(f"human_confirmed_patch_preview_322h_summary_json: {output_dir / 'human_confirmed_semantic_patch_preview_322h_summary.json'}")
        return 0
    if not trust_split_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR")
        print(f"human_confirmed_patch_preview_322h_summary_json: {output_dir / 'human_confirmed_semantic_patch_preview_322h_summary.json'}")
        return 0

    inputs = load_human_confirmed_patch_inputs(
        reviewed_proposal_xlsx=reviewed_proposal_xlsx,
        proposal_dir=proposal_dir,
        adjudicator_apply_dir=adjudicator_apply_dir,
        trust_split_dir=trust_split_dir,
    )
    artifacts = build_human_confirmed_patch_preview(
        reviewed_sheets=inputs["reviewed_sheets"],
        proposal_summary=inputs["proposal_summary"],
        apply_summary=inputs["apply_summary"],
        trust_summary=inputs["trust_summary"],
        selected_candidates_df=inputs["selected_candidates_df"],
        candidate_replay_diff_df=inputs["candidate_replay_diff_df"],
        replay_instructions_df=inputs["replay_instructions_df"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "excel": output_dir / "human_confirmed_semantic_patch_preview_322h.xlsx",
        "summary_json": output_dir / "human_confirmed_semantic_patch_preview_322h_summary.json",
        "report_md": output_dir / "human_confirmed_semantic_patch_preview_322h_report.md",
        "diff_jsonl": output_dir / "candidate_before_after_diff_322h.jsonl",
        "official_rule_jsonl": output_dir / "official_rule_candidate_preview_322h.jsonl",
    }

    sheets = {
        "summary": pd.DataFrame([summary]),
        "reviewed_proposal_inventory": artifacts["reviewed_proposal_inventory_df"],
        "alias_patch_preview": artifacts["alias_patch_preview_df"],
        "out_of_scope_patch_preview": artifacts["out_of_scope_patch_preview_df"],
        "unit_inference_patch_preview": artifacts["unit_inference_patch_preview_df"],
        "rejected_noise_patch_preview": artifacts["rejected_noise_patch_preview_df"],
        "candidate_before_after_diff_322h": artifacts["candidate_before_after_diff_df"],
        "trusted_after_patch_preview_322h": artifacts["trusted_after_patch_preview_df"],
        "review_required_after_patch_preview_322h": artifacts["review_required_after_patch_preview_df"],
        "rejected_after_patch_preview_322h": artifacts["rejected_after_patch_preview_df"],
        "patch_impact_by_proposal_322h": artifacts["patch_impact_by_proposal_df"],
        "remaining_review_burden_322h": artifacts["remaining_review_burden_322h_df"],
        "official_rule_candidate_preview": artifacts["official_rule_candidate_preview_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }

    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(patch_preview_report_markdown(summary), encoding="utf-8")
    write_jsonl(output_files["diff_jsonl"], artifacts["candidate_before_after_diff_df"])
    write_jsonl(output_files["official_rule_jsonl"], artifacts["official_rule_candidate_preview_df"])

    qa_df = artifacts["qa_checks_df"].copy()
    output_files_written = all(path.exists() for path in output_files.values())
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output_files_written_successfully",
                        "status": "PASS" if output_files_written else "FAIL",
                        "detail": str(output_dir),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    if summary["qa_fail_count"] > 0:
        decision = "HUMAN_CONFIRMED_PATCH_PREVIEW_322H_BLOCKED_BY_QA_FAILURE"
    elif int(summary.get("accepted_proposal_count", 0)) > 0 and int(summary.get("review_reduction_322h", 0)) > 0:
        decision = "HUMAN_CONFIRMED_PATCH_PREVIEW_322H_READY_FOR_322I_OFFICIAL_RULE_CANDIDATES"
    elif int(summary.get("accepted_proposal_count", 0)) > 0:
        decision = "HUMAN_CONFIRMED_PATCH_PREVIEW_322H_PARTIAL_NO_REDUCTION"
    else:
        decision = "HUMAN_CONFIRMED_PATCH_PREVIEW_322H_NO_ACCEPTED_PROPOSALS"
    summary["human_confirmed_patch_preview_decision"] = decision

    sheets["summary"] = pd.DataFrame([summary])
    sheets["qa_checks"] = qa_df
    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(patch_preview_report_markdown(summary), encoding="utf-8")

    print(f"human_confirmed_patch_preview_322h_excel: {output_files['excel']}")
    print(f"human_confirmed_patch_preview_322h_summary_json: {output_files['summary_json']}")
    print(f"human_confirmed_patch_preview_322h_report_md: {output_files['report_md']}")
    for key in [
        "reviewed_proposal_count",
        "accepted_proposal_count",
        "rejected_proposal_count",
        "needs_more_info_proposal_count",
        "accepted_alias_patch_count",
        "accepted_out_of_scope_patch_count",
        "accepted_unit_inference_patch_count",
        "accepted_rejected_noise_patch_count",
        "affected_candidate_count",
        "trusted_total_before_322h",
        "trusted_total_after_322h",
        "review_required_total_before_322h",
        "review_required_total_after_322h",
        "rejected_total_before_322h",
        "rejected_total_after_322h",
        "trusted_gain_322h",
        "review_reduction_322h",
        "selected_core_trusted_rate_before_322h",
        "selected_core_trusted_rate_after_322h",
        "remaining_unknown_metric_candidate_count",
        "remaining_unit_unknown_candidate_count",
        "remaining_manual_review_count",
        "official_rule_candidate_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "human_confirmed_patch_preview_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
