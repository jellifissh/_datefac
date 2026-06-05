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

from datefac.semantic.alias_official_rule_candidates_from_325i import (  # noqa: E402
    DEFAULT_HUMAN_CONFIRMATION_REVIEWED_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SANDBOX_REPLAY_DIR,
    DEFAULT_SCHEMA_VALIDATION_DIR,
    NOT_READY_DECISION,
    build_alias_official_rule_candidates_from_325i,
    load_alias_official_rule_candidates_from_325i_inputs,
)
from datefac.semantic.alias_official_rule_candidates_from_325i_report import (  # noqa: E402
    alias_official_rule_candidates_from_325i_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, reason: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325J",
        "output_dir": str(output_dir),
        "source_sandbox_rule_count": 0,
        "candidate_count": 0,
        "alias_candidate_count": 0,
        "ready_for_controlled_proposal_count": 0,
        "needs_review_candidate_count": 0,
        "rejected_candidate_count": 0,
        "duplicate_candidate_id_count": 0,
        "duplicate_alias_target_pair_count": 0,
        "official_overlap_count": 0,
        "target_conflict_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
        "affected_candidate_count": 0,
        "trusted_gain_325j": 0,
        "review_reduction_325j": 0,
        "out_of_scope_or_rejected_gain_325j": 0,
        "official_assets_modified": False,
        "official_assets_written": [],
        "qa_fail_count": 1,
        "blocking_reasons": [reason],
        "decision": NOT_READY_DECISION,
    }
    write_json(output_dir / "alias_official_rule_candidates_from_325i_325j_summary.json", summary)
    write_json(
        output_dir / "alias_official_rule_candidates_from_325i_325j_qa.json",
        {"qa_fail_count": 1, "blocking_reasons": [reason], "checks": []},
    )
    return summary


def _write_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)

    write_json(output_dir / "alias_official_rule_candidates_from_325i_325j_summary.json", summary)
    write_json(output_dir / "alias_official_rule_candidates_from_325i_325j_qa.json", artifacts["qa_json"])
    write_json(
        output_dir / "alias_official_rule_candidates_from_325i_325j_candidate_package.json",
        artifacts["candidate_package"],
    )
    write_json(
        output_dir / "alias_official_rule_candidates_from_325i_325j_candidates.json",
        {"stage": "325J", "candidates": artifacts["candidates_df"].to_dict(orient="records")},
    )
    write_json(
        output_dir / "alias_official_rule_candidates_from_325i_325j_no_apply_proof.json",
        artifacts["no_apply_proof"],
    )
    write_jsonl(
        output_dir / "alias_official_rule_candidates_from_325i_325j_candidates.jsonl",
        artifacts["candidates_df"],
    )
    write_excel(
        output_dir / "alias_official_rule_candidates_from_325i_325j_candidates.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "alias_candidates": artifacts["candidates_df"],
            "safety_checks": artifacts["safety_checks_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
    )
    write_excel(
        output_dir / "alias_official_rule_candidates_from_325i_325j_duplicate_conflict_report.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "alias_candidates": artifacts["candidates_df"],
            "safety_checks": artifacts["safety_checks_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
    )
    (output_dir / "alias_official_rule_candidates_from_325i_325j_report.md").write_text(
        alias_official_rule_candidates_from_325i_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325J alias official rule candidates from 325I.")
    parser.add_argument("--sandbox-replay-dir", default=str(DEFAULT_SANDBOX_REPLAY_DIR))
    parser.add_argument("--human-confirmation-reviewed-dir", default=str(DEFAULT_HUMAN_CONFIRMATION_REVIEWED_DIR))
    parser.add_argument("--schema-validation-dir", default=str(DEFAULT_SCHEMA_VALIDATION_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    sandbox_replay_dir = Path(args.sandbox_replay_dir)
    human_confirmation_reviewed_dir = Path(args.human_confirmation_reviewed_dir)
    schema_validation_dir = Path(args.schema_validation_dir)
    output_dir = Path(args.output_dir)

    required = [
        sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json",
        sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_qa.json",
        sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_sandbox_rules.json",
        sandbox_replay_dir / "alias_human_confirmed_sandbox_replay_325i_affected_candidates.xlsx",
        human_confirmation_reviewed_dir / "alias_human_confirmation_325h_reviewed_summary.json",
        human_confirmation_reviewed_dir / "alias_human_confirmation_325h_human_confirmed_plan.json",
        schema_validation_dir / "alias_response_schema_validation_325g_summary.json",
    ]
    if not all(path.exists() for path in required):
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_REQUIRED_325I_325H_OR_325G_INPUTS")
    else:
        inputs = load_alias_official_rule_candidates_from_325i_inputs(
            sandbox_replay_dir=sandbox_replay_dir,
            human_confirmation_reviewed_dir=human_confirmation_reviewed_dir,
            schema_validation_dir=schema_validation_dir,
        )
        summary = _write_outputs(output_dir, build_alias_official_rule_candidates_from_325i(inputs))

    print(f"output_dir: {output_dir}")
    for key in [
        "source_sandbox_rule_count",
        "candidate_count",
        "alias_candidate_count",
        "ready_for_controlled_proposal_count",
        "needs_review_candidate_count",
        "rejected_candidate_count",
        "duplicate_candidate_id_count",
        "duplicate_alias_target_pair_count",
        "official_overlap_count",
        "target_conflict_count",
        "adjusted_metric_mismatch_count",
        "diluted_eps_mismatch_count",
        "affected_candidate_count",
        "trusted_gain_325j",
        "review_reduction_325j",
        "out_of_scope_or_rejected_gain_325j",
        "official_assets_modified",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
