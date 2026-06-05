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

from datefac.semantic.controlled_official_proposal_dry_run_325l import (  # noqa: E402
    DEFAULT_CONTROLLED_PROPOSAL_DIR,
    DEFAULT_OFFICIAL_RULE_CANDIDATE_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SANDBOX_REPLAY_DIR,
    NOT_READY_DECISION,
    build_controlled_official_proposal_dry_run_325l,
    load_controlled_official_proposal_dry_run_325l_inputs,
)
from datefac.semantic.controlled_official_proposal_dry_run_325l_report import (  # noqa: E402
    controlled_official_proposal_dry_run_325l_markdown,
    controlled_official_proposal_dry_run_325l_rollback_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, reason: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325L",
        "output_dir": str(output_dir),
        "proposal_count": 0,
        "patch_operation_count": 0,
        "alias_patch_operation_count": 0,
        "scope_patch_operation_count": 0,
        "target_asset_file_count": 0,
        "target_asset_plan_count": 0,
        "duplicate_operation_count": 0,
        "duplicate_alias_target_pair_count": 0,
        "target_conflict_count": 0,
        "already_official_overlap_count": 0,
        "missing_target_asset_or_group_count": 0,
        "missing_provenance_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
        "official_asset_hash_unchanged": True,
        "files_written_to_official_assets": [],
        "expected_affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [reason],
        "decision": NOT_READY_DECISION,
    }
    write_json(output_dir / "controlled_official_proposal_dry_run_325l_summary.json", summary)
    write_json(
        output_dir / "controlled_official_proposal_dry_run_325l_qa.json",
        {"qa_fail_count": 1, "blocking_reasons": [reason], "checks": []},
    )
    return summary


def _write_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)

    write_json(output_dir / "controlled_official_proposal_dry_run_325l_summary.json", summary)
    write_json(output_dir / "controlled_official_proposal_dry_run_325l_qa.json", artifacts["qa_json"])
    write_json(
        output_dir / "controlled_official_proposal_dry_run_325l_patch_operations.json",
        artifacts["patch_operations_json"],
    )
    write_json(
        output_dir / "controlled_official_proposal_dry_run_325l_target_asset_diff_preview.json",
        artifacts["target_asset_diff_preview_json"],
    )
    write_json(
        output_dir / "controlled_official_proposal_dry_run_325l_rollback_plan.json",
        artifacts["rollback_plan_json"],
    )
    write_json(
        output_dir / "controlled_official_proposal_dry_run_325l_no_apply_proof.json",
        artifacts["no_apply_proof_json"],
    )
    write_excel(
        output_dir / "controlled_official_proposal_dry_run_325l.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "patch_operations": artifacts["patch_operations_df"],
            "before_after_preview": artifacts["before_after_preview_df"],
            "target_asset_diff_preview": artifacts["target_asset_diff_preview_df"],
            "rollback_plan": artifacts["rollback_plan_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
    )
    (output_dir / "controlled_official_proposal_dry_run_325l_report.md").write_text(
        controlled_official_proposal_dry_run_325l_markdown(summary),
        encoding="utf-8",
    )
    (output_dir / "controlled_official_proposal_dry_run_325l_rollback_instructions.md").write_text(
        controlled_official_proposal_dry_run_325l_rollback_markdown(
            artifacts["rollback_plan_df"].to_dict(orient="records")
        ),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325L controlled alias proposal dry run.")
    parser.add_argument("--controlled-proposal-dir", default=str(DEFAULT_CONTROLLED_PROPOSAL_DIR))
    parser.add_argument(
        "--official-rule-candidate-dir",
        default=str(DEFAULT_OFFICIAL_RULE_CANDIDATE_DIR),
    )
    parser.add_argument("--sandbox-replay-dir", default=str(DEFAULT_SANDBOX_REPLAY_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    controlled_proposal_dir = Path(args.controlled_proposal_dir)
    official_rule_candidate_dir = Path(args.official_rule_candidate_dir)
    sandbox_replay_dir = Path(args.sandbox_replay_dir)
    output_dir = Path(args.output_dir)

    required = [
        controlled_proposal_dir / "controlled_official_proposal_from_325j_325k_summary.json",
        controlled_proposal_dir / "controlled_official_proposal_from_325j_325k_qa.json",
        controlled_proposal_dir / "controlled_official_proposal_from_325j_325k_proposals.json",
        controlled_proposal_dir
        / "controlled_official_proposal_from_325j_325k_target_asset_plan.json",
        official_rule_candidate_dir
        / "alias_official_rule_candidates_from_325i_325j_summary.json",
        sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json",
    ]

    if not all(path.exists() for path in required):
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_REQUIRED_325K_325J_OR_325I_INPUTS")
    else:
        inputs = load_controlled_official_proposal_dry_run_325l_inputs(
            controlled_proposal_dir=controlled_proposal_dir,
            official_rule_candidate_dir=official_rule_candidate_dir,
            sandbox_replay_dir=sandbox_replay_dir,
        )
        summary = _write_outputs(output_dir, build_controlled_official_proposal_dry_run_325l(inputs))

    print(f"output_dir: {output_dir}")
    for key in [
        "proposal_count",
        "patch_operation_count",
        "alias_patch_operation_count",
        "scope_patch_operation_count",
        "target_asset_file_count",
        "target_asset_plan_count",
        "duplicate_operation_count",
        "duplicate_alias_target_pair_count",
        "target_conflict_count",
        "already_official_overlap_count",
        "missing_target_asset_or_group_count",
        "missing_provenance_count",
        "adjusted_metric_mismatch_count",
        "diluted_eps_mismatch_count",
        "official_asset_hash_unchanged",
        "expected_affected_candidate_count",
        "expected_trusted_gain",
        "expected_review_reduction",
        "expected_out_of_scope_or_rejected_gain",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
