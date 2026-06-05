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

from datefac.semantic.controlled_official_proposal_from_325j_325k import (  # noqa: E402
    DEFAULT_OFFICIAL_RULE_CANDIDATE_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SANDBOX_REPLAY_DIR,
    NOT_READY_DECISION,
    build_controlled_official_proposal_from_325j,
    load_controlled_official_proposal_from_325j_inputs,
)
from datefac.semantic.controlled_official_proposal_from_325j_325k_report import (  # noqa: E402
    controlled_official_proposal_from_325j_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, reason: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325K",
        "output_dir": str(output_dir),
        "loaded_ready_candidate_count": 0,
        "proposal_count": 0,
        "alias_proposal_count": 0,
        "scope_proposal_count": 0,
        "ready_for_dry_run_proposal_count": 0,
        "needs_review_proposal_count": 0,
        "rejected_proposal_count": 0,
        "target_asset_plan_count": 0,
        "target_asset_file_count": 0,
        "duplicate_proposal_id_count": 0,
        "already_official_overlap_count": 0,
        "target_conflict_count": 0,
        "missing_target_asset_or_group_count": 0,
        "missing_provenance_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
        "expected_affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "official_assets_modified": False,
        "official_assets_written": [],
        "qa_fail_count": 1,
        "blocking_reasons": [reason],
        "decision": NOT_READY_DECISION,
    }
    write_json(output_dir / "controlled_official_proposal_from_325j_325k_summary.json", summary)
    write_json(
        output_dir / "controlled_official_proposal_from_325j_325k_qa.json",
        {"qa_fail_count": 1, "blocking_reasons": [reason], "checks": []},
    )
    return summary


def _write_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)

    write_json(output_dir / "controlled_official_proposal_from_325j_325k_summary.json", summary)
    write_json(output_dir / "controlled_official_proposal_from_325j_325k_qa.json", artifacts["qa_json"])
    write_json(
        output_dir / "controlled_official_proposal_from_325j_325k_proposals.json",
        artifacts["proposal_package"],
    )
    write_json(
        output_dir / "controlled_official_proposal_from_325j_325k_target_asset_plan.json",
        {
            "stage": "325K",
            "decision": summary["decision"],
            "target_asset_plan": artifacts["target_asset_plan_df"].to_dict(orient="records"),
        },
    )
    write_json(
        output_dir / "controlled_official_proposal_from_325j_325k_no_apply_proof.json",
        artifacts["no_apply_proof"],
    )
    write_excel(
        output_dir / "controlled_official_proposal_from_325j_325k_proposals.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "proposal_overview": artifacts["proposal_overview_df"],
            "alias_proposals": artifacts["alias_proposals_df"],
            "scope_proposals": artifacts["scope_proposals_df"],
            "target_asset_plan": artifacts["target_asset_plan_df"],
            "provenance": artifacts["provenance_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
    )
    write_excel(
        output_dir / "controlled_official_proposal_from_325j_325k_target_asset_plan.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "proposal_overview": artifacts["proposal_overview_df"],
            "alias_proposals": artifacts["alias_proposals_df"],
            "scope_proposals": artifacts["scope_proposals_df"],
            "target_asset_plan": artifacts["target_asset_plan_df"],
            "provenance": artifacts["provenance_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
    )
    (output_dir / "controlled_official_proposal_from_325j_325k_report.md").write_text(
        controlled_official_proposal_from_325j_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 325K controlled official proposal generation from 325J."
    )
    parser.add_argument(
        "--official-rule-candidate-dir", default=str(DEFAULT_OFFICIAL_RULE_CANDIDATE_DIR)
    )
    parser.add_argument("--sandbox-replay-dir", default=str(DEFAULT_SANDBOX_REPLAY_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    official_rule_candidate_dir = Path(args.official_rule_candidate_dir)
    sandbox_replay_dir = Path(args.sandbox_replay_dir)
    output_dir = Path(args.output_dir)

    required = [
        official_rule_candidate_dir / "alias_official_rule_candidates_from_325i_325j_summary.json",
        official_rule_candidate_dir / "alias_official_rule_candidates_from_325i_325j_qa.json",
        official_rule_candidate_dir
        / "alias_official_rule_candidates_from_325i_325j_candidate_package.json",
        sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json",
        sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_sandbox_rules.json",
    ]
    if not all(path.exists() for path in required):
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_REQUIRED_325J_OR_325I_INPUTS")
    else:
        inputs = load_controlled_official_proposal_from_325j_inputs(
            official_rule_candidate_dir=official_rule_candidate_dir,
            sandbox_replay_dir=sandbox_replay_dir,
        )
        summary = _write_outputs(output_dir, build_controlled_official_proposal_from_325j(inputs))

    print(f"output_dir: {output_dir}")
    for key in [
        "loaded_ready_candidate_count",
        "proposal_count",
        "alias_proposal_count",
        "scope_proposal_count",
        "ready_for_dry_run_proposal_count",
        "needs_review_proposal_count",
        "rejected_proposal_count",
        "target_asset_plan_count",
        "target_asset_file_count",
        "duplicate_proposal_id_count",
        "already_official_overlap_count",
        "target_conflict_count",
        "missing_target_asset_or_group_count",
        "missing_provenance_count",
        "adjusted_metric_mismatch_count",
        "diluted_eps_mismatch_count",
        "expected_affected_candidate_count",
        "expected_trusted_gain",
        "expected_review_reduction",
        "expected_out_of_scope_or_rejected_gain",
        "official_assets_modified",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
