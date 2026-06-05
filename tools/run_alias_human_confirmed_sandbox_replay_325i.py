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

from datefac.semantic.alias_human_confirmed_sandbox_replay_325i import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_PATCH_REGRESSION_DIR,
    DEFAULT_REQUEST_DIR,
    DEFAULT_REVIEWED_CONFIRMATION_DIR,
    DEFAULT_SCHEMA_VALIDATION_DIR,
    DEFAULT_TRUST_SPLIT_DIR,
    NOT_READY_DECISION,
    build_alias_human_confirmed_sandbox_replay_325i,
    load_alias_human_confirmed_sandbox_replay_325i_inputs,
)
from datefac.semantic.alias_human_confirmed_sandbox_replay_325i_report import (  # noqa: E402
    alias_human_confirmed_sandbox_replay_325i_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, reason: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325I",
        "output_dir": str(output_dir),
        "confirmed_alias_count": 0,
        "sandbox_alias_rule_count": 0,
        "affected_candidate_count": 0,
        "trusted_gain_325i": 0,
        "review_reduction_325i": 0,
        "out_of_scope_or_rejected_gain_325i": 0,
        "duplicate_count": 0,
        "conflict_count": 0,
        "target_conflict_count": 0,
        "official_overlap_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
        "core_false_mapping_count": 0,
        "official_assets_modified": False,
        "qa_fail_count": 1,
        "blocking_reasons": [reason],
        "decision": NOT_READY_DECISION,
    }
    write_json(output_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json", summary)
    write_json(
        output_dir / "alias_human_confirmed_sandbox_replay_325i_qa.json",
        {"qa_fail_count": 1, "blocking_reasons": [reason], "checks": []},
    )
    return summary


def _write_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    write_json(output_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json", summary)
    write_json(output_dir / "alias_human_confirmed_sandbox_replay_325i_qa.json", artifacts["qa_json"])
    write_json(output_dir / "alias_human_confirmed_sandbox_replay_325i_sandbox_rules.json", artifacts["sandbox_rules_json"])
    write_json(output_dir / "alias_human_confirmed_sandbox_replay_325i_no_apply_proof.json", artifacts["no_apply_proof"])
    write_jsonl(
        output_dir / "alias_human_confirmed_sandbox_replay_325i_affected_candidates.jsonl",
        artifacts["affected_candidates_df"],
    )
    write_excel(
        output_dir / "alias_human_confirmed_sandbox_replay_325i_affected_candidates.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "affected_candidates": artifacts["affected_candidates_df"],
            "patch_impact_by_rule": artifacts["patch_impact_by_rule_df"],
            "sandbox_alias_rules": artifacts["sandbox_alias_rules_df"],
            "duplicate_conflict": artifacts["duplicate_conflict_df"],
            "special_checks": artifacts["special_checks_df"],
            "core_false_mapping": artifacts["core_false_mapping_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    write_excel(
        output_dir / "alias_human_confirmed_sandbox_replay_325i_before_after.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "before_after_overview": artifacts["before_after_overview_df"],
            "trusted_after": artifacts["trusted_after_df"],
            "review_after": artifacts["review_after_df"],
            "rejected_after": artifacts["rejected_after_df"],
            "remaining_review_burden": artifacts["remaining_review_burden_df"],
        },
    )
    (output_dir / "alias_human_confirmed_sandbox_replay_325i_report.md").write_text(
        alias_human_confirmed_sandbox_replay_325i_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325I alias human-confirmed sandbox replay.")
    parser.add_argument("--reviewed-confirmation-dir", default=str(DEFAULT_REVIEWED_CONFIRMATION_DIR))
    parser.add_argument("--schema-validation-dir", default=str(DEFAULT_SCHEMA_VALIDATION_DIR))
    parser.add_argument("--request-dir", default=str(DEFAULT_REQUEST_DIR))
    parser.add_argument("--trust-split-dir", default=str(DEFAULT_TRUST_SPLIT_DIR))
    parser.add_argument("--post-patch-regression-dir", default=str(DEFAULT_POST_PATCH_REGRESSION_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    reviewed_confirmation_dir = Path(args.reviewed_confirmation_dir)
    schema_validation_dir = Path(args.schema_validation_dir)
    request_dir = Path(args.request_dir)
    trust_split_dir = Path(args.trust_split_dir)
    post_patch_regression_dir = Path(args.post_patch_regression_dir)
    output_dir = Path(args.output_dir)

    required = [
        reviewed_confirmation_dir / "alias_human_confirmation_325h_reviewed_summary.json",
        reviewed_confirmation_dir / "alias_human_confirmation_325h_reviewed_qa.json",
        reviewed_confirmation_dir / "alias_human_confirmation_325h_human_confirmed_plan.json",
        schema_validation_dir / "alias_response_schema_validation_325g_summary.json",
        schema_validation_dir / "alias_response_schema_validation_325g_qa.json",
        request_dir / "alias_safe_adjudicator_request_325e_request_package.json",
        trust_split_dir / "selected_candidate_reclassified_322b2.jsonl",
        trust_split_dir / "router_mineru_trust_split_322b2_summary.json",
        post_patch_regression_dir / "post_patch_regression_validation_324m_summary.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_REQUIRED_INPUTS")
        summary["missing_inputs"] = missing
        write_json(output_dir / "alias_human_confirmed_sandbox_replay_325i_summary.json", summary)
    else:
        inputs = load_alias_human_confirmed_sandbox_replay_325i_inputs(
            reviewed_confirmation_dir=reviewed_confirmation_dir,
            schema_validation_dir=schema_validation_dir,
            request_dir=request_dir,
            trust_split_dir=trust_split_dir,
            post_patch_regression_dir=post_patch_regression_dir,
        )
        summary = _write_outputs(output_dir, build_alias_human_confirmed_sandbox_replay_325i(inputs))

    print(f"output_dir: {output_dir}")
    for key in [
        "confirmed_alias_count",
        "sandbox_alias_rule_count",
        "affected_candidate_count",
        "trusted_gain_325i",
        "review_reduction_325i",
        "out_of_scope_or_rejected_gain_325i",
        "duplicate_count",
        "conflict_count",
        "target_conflict_count",
        "official_overlap_count",
        "adjusted_metric_mismatch_count",
        "diluted_eps_mismatch_count",
        "core_false_mapping_count",
        "official_assets_modified",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
