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

from datefac.semantic.human_confirmed_sandbox_replay import (  # noqa: E402
    NOT_READY_DECISION,
    build_human_confirmed_sandbox_replay,
    load_human_confirmed_sandbox_replay_inputs,
)
from datefac.semantic.human_confirmed_sandbox_replay_report import (  # noqa: E402
    human_confirmed_sandbox_replay_report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323H",
        "output_dir": str(output_dir),
        "total_confirmed_suggestion_count": 0,
        "alias_confirmed_suggestion_count": 0,
        "scope_confirmed_suggestion_count": 0,
        "sandbox_rule_count": 0,
        "sandbox_alias_rule_count": 0,
        "sandbox_scope_rule_count": 0,
        "effective_unique_rule_count": 0,
        "duplicate_rule_count": 0,
        "conflict_count": 0,
        "metric_target_unresolved_count": 0,
        "trusted_total_before_323h": 0,
        "trusted_total_after_323h": 0,
        "review_required_total_before_323h": 0,
        "review_required_total_after_323h": 0,
        "rejected_total_before_323h": 0,
        "rejected_total_after_323h": 0,
        "affected_candidate_count": 0,
        "trusted_gain_323h": 0,
        "review_reduction_323h": 0,
        "out_of_scope_or_rejected_gain_323h": 0,
        "alias_trusted_gain_323h": 0,
        "alias_review_reduction_323h": 0,
        "scope_trusted_gain_323h": 0,
        "scope_review_reduction_323h": 0,
        "scope_out_of_scope_or_rejected_gain_323h": 0,
        "selected_core_trusted_rate_before_323h": 0,
        "selected_core_trusted_rate_after_323h": 0,
        "baseline_unknown_metric_candidate_count": 0,
        "baseline_unit_unknown_candidate_count": 0,
        "baseline_manual_review_count": 0,
        "remaining_unknown_metric_candidate_count": 0,
        "remaining_unit_unknown_candidate_count": 0,
        "remaining_manual_review_count": 0,
        "reference_322o_trusted_gain": 0,
        "reference_322o_review_reduction": 0,
        "reference_322o_out_of_scope_or_rejected_gain": 0,
        "reference_322o_affected_candidate_count": 0,
        "core_false_exclusion_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    empty = pd.DataFrame()
    write_json(output_dir / "human_confirmed_sandbox_replay_323h_summary.json", summary)
    write_json(output_dir / "human_confirmed_sandbox_replay_323h_qa.json", qa_json)
    write_json(
        output_dir / "human_confirmed_sandbox_replay_323h_sandbox_rule_set.json",
        {
            "stage": "323H",
            "mode": "sandbox_replay_only",
            "source_rule_count": 0,
            "alias_rule_count": 0,
            "scope_rule_count": 0,
            "duplicate_conflict_summary": [],
            "alias_rules": [],
            "scope_rules": [],
        },
    )
    write_excel(
        output_dir / "human_confirmed_sandbox_replay_323h_before_after_comparison.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "before_after_overview": empty,
            "rule_application_overview": empty,
            "alias_scope_contribution": empty,
            "remaining_review_burden": empty,
            "qa_checks": pd.DataFrame(qa_json["checks"]),
        },
    )
    write_excel(
        output_dir / "human_confirmed_sandbox_replay_323h_affected_candidates.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "source_rule_inventory": empty,
            "candidate_before_after_diff": empty,
            "patch_impact_by_rule": empty,
            "qa_checks": pd.DataFrame(qa_json["checks"]),
        },
    )
    write_excel(
        output_dir / "human_confirmed_sandbox_replay_323h_alias_replay.xlsx",
        {"alias_rules": empty, "alias_diff": empty},
    )
    write_excel(
        output_dir / "human_confirmed_sandbox_replay_323h_scope_replay.xlsx",
        {"scope_rules": empty, "scope_diff": empty},
    )
    write_excel(
        output_dir / "human_confirmed_sandbox_replay_323h_conflict_report.xlsx",
        {"duplicate_conflict": empty},
    )
    write_excel(
        output_dir / "human_confirmed_sandbox_replay_323h_core_false_exclusion_check.xlsx",
        {"core_false_exclusion": empty},
    )
    write_jsonl(output_dir / "human_confirmed_sandbox_replay_323h_rule_application_log.jsonl", empty)
    (output_dir / "human_confirmed_sandbox_replay_323h_notes.md").write_text(
        human_confirmed_sandbox_replay_report_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 323H human-confirmed sandbox replay."
    )
    parser.add_argument("--reviewed-confirmation-dir", required=True)
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--post-patch-regression-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    reviewed_confirmation_dir = Path(args.reviewed_confirmation_dir)
    trust_split_dir = Path(args.trust_split_dir)
    post_patch_regression_dir = Path(args.post_patch_regression_dir)
    output_dir = Path(args.output_dir)

    if not reviewed_confirmation_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_323G_REVIEWED_DIR")
        print(
            "human_confirmed_sandbox_replay_323h_summary_json: "
            f"{output_dir / 'human_confirmed_sandbox_replay_323h_summary.json'}"
        )
        return 0
    if not trust_split_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR")
        print(
            "human_confirmed_sandbox_replay_323h_summary_json: "
            f"{output_dir / 'human_confirmed_sandbox_replay_323h_summary.json'}"
        )
        return 0
    if not post_patch_regression_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322O_POST_PATCH_REGRESSION_DIR")
        print(
            "human_confirmed_sandbox_replay_323h_summary_json: "
            f"{output_dir / 'human_confirmed_sandbox_replay_323h_summary.json'}"
        )
        return 0

    inputs = load_human_confirmed_sandbox_replay_inputs(
        reviewed_confirmation_dir=reviewed_confirmation_dir,
        trust_split_dir=trust_split_dir,
        post_patch_regression_dir=post_patch_regression_dir,
    )
    artifacts = build_human_confirmed_sandbox_replay(
        reviewed_summary=inputs["reviewed_summary"],
        reviewed_qa=inputs["reviewed_qa"],
        reviewed_plan=inputs["reviewed_plan"],
        trust_summary=inputs["trust_summary"],
        selected_candidates_df=inputs["selected_candidates_df"],
        post_patch_summary=inputs["post_patch_summary"],
        official_alias_df=inputs["official_alias_df"],
        official_scope_df=inputs["official_scope_df"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_json_path = output_dir / "human_confirmed_sandbox_replay_323h_summary.json"
    qa_json_path = output_dir / "human_confirmed_sandbox_replay_323h_qa.json"
    rule_set_json_path = output_dir / "human_confirmed_sandbox_replay_323h_sandbox_rule_set.json"
    before_after_xlsx_path = (
        output_dir / "human_confirmed_sandbox_replay_323h_before_after_comparison.xlsx"
    )
    affected_xlsx_path = (
        output_dir / "human_confirmed_sandbox_replay_323h_affected_candidates.xlsx"
    )
    alias_xlsx_path = output_dir / "human_confirmed_sandbox_replay_323h_alias_replay.xlsx"
    scope_xlsx_path = output_dir / "human_confirmed_sandbox_replay_323h_scope_replay.xlsx"
    conflict_xlsx_path = (
        output_dir / "human_confirmed_sandbox_replay_323h_conflict_report.xlsx"
    )
    core_false_exclusion_xlsx_path = (
        output_dir / "human_confirmed_sandbox_replay_323h_core_false_exclusion_check.xlsx"
    )
    rule_log_jsonl_path = (
        output_dir / "human_confirmed_sandbox_replay_323h_rule_application_log.jsonl"
    )
    notes_md_path = output_dir / "human_confirmed_sandbox_replay_323h_notes.md"

    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(rule_set_json_path, artifacts["sandbox_rule_set_json"])
    write_excel(
        before_after_xlsx_path,
        {
            "summary": pd.DataFrame([summary]),
            "before_after_overview": artifacts["before_after_overview_df"],
            "rule_application_overview": artifacts["rule_application_overview_df"],
            "alias_scope_contribution": artifacts["alias_scope_contribution_df"],
            "remaining_review_burden": artifacts["remaining_review_burden_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    write_excel(
        affected_xlsx_path,
        {
            "summary": pd.DataFrame([summary]),
            "source_rule_inventory": artifacts["source_rule_inventory_df"],
            "candidate_before_after_diff": artifacts["candidate_before_after_diff_df"],
            "patch_impact_by_rule": artifacts["patch_impact_by_rule_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    write_excel(
        alias_xlsx_path,
        {
            "alias_rules": artifacts["alias_rule_inventory_df"],
            "alias_diff": artifacts["alias_diff_df"],
        },
    )
    write_excel(
        scope_xlsx_path,
        {
            "scope_rules": artifacts["scope_rule_inventory_df"],
            "scope_diff": artifacts["scope_diff_df"],
        },
    )
    write_excel(
        conflict_xlsx_path,
        {"duplicate_conflict": artifacts["duplicate_conflict_df"]},
    )
    write_excel(
        core_false_exclusion_xlsx_path,
        {"core_false_exclusion": artifacts["core_false_exclusion_df"]},
    )
    write_jsonl(rule_log_jsonl_path, artifacts["rule_application_overview_df"])
    notes_md_path.write_text(artifacts["notes_markdown"], encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            summary_json_path,
            qa_json_path,
            rule_set_json_path,
            before_after_xlsx_path,
            affected_xlsx_path,
            alias_xlsx_path,
            scope_xlsx_path,
            conflict_xlsx_path,
            core_false_exclusion_xlsx_path,
            rule_log_jsonl_path,
            notes_md_path,
        ]
    )

    qa_df = artifacts["qa_checks_df"].copy()
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
    summary["blocking_reasons"] = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )
    if summary["qa_fail_count"] > 0:
        summary["decision"] = NOT_READY_DECISION
    elif summary["qa_warn_count"] > 0:
        summary["decision"] = "HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_REVIEW_WITH_WARNINGS"
    else:
        summary["decision"] = (
            "HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY_FOR_323I_OFFICIAL_RULE_CANDIDATES"
        )

    artifacts["qa_json"]["qa_pass_count"] = summary["qa_pass_count"]
    artifacts["qa_json"]["qa_warn_count"] = summary["qa_warn_count"]
    artifacts["qa_json"]["qa_fail_count"] = summary["qa_fail_count"]
    artifacts["qa_json"]["blocking_reasons"] = summary["blocking_reasons"]
    artifacts["qa_json"]["checks"] = qa_df.to_dict(orient="records")

    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_excel(
        before_after_xlsx_path,
        {
            "summary": pd.DataFrame([summary]),
            "before_after_overview": artifacts["before_after_overview_df"],
            "rule_application_overview": artifacts["rule_application_overview_df"],
            "alias_scope_contribution": artifacts["alias_scope_contribution_df"],
            "remaining_review_burden": artifacts["remaining_review_burden_df"],
            "qa_checks": qa_df,
        },
    )
    write_excel(
        affected_xlsx_path,
        {
            "summary": pd.DataFrame([summary]),
            "source_rule_inventory": artifacts["source_rule_inventory_df"],
            "candidate_before_after_diff": artifacts["candidate_before_after_diff_df"],
            "patch_impact_by_rule": artifacts["patch_impact_by_rule_df"],
            "qa_checks": qa_df,
        },
    )
    notes_md_path.write_text(artifacts["notes_markdown"], encoding="utf-8")

    print(f"human_confirmed_sandbox_replay_323h_summary_json: {summary_json_path}")
    print(f"human_confirmed_sandbox_replay_323h_qa_json: {qa_json_path}")
    print(f"human_confirmed_sandbox_replay_323h_sandbox_rule_set_json: {rule_set_json_path}")
    print(f"human_confirmed_sandbox_replay_323h_before_after_comparison_xlsx: {before_after_xlsx_path}")
    print(f"human_confirmed_sandbox_replay_323h_affected_candidates_xlsx: {affected_xlsx_path}")
    print(f"human_confirmed_sandbox_replay_323h_alias_replay_xlsx: {alias_xlsx_path}")
    print(f"human_confirmed_sandbox_replay_323h_scope_replay_xlsx: {scope_xlsx_path}")
    print(f"human_confirmed_sandbox_replay_323h_conflict_report_xlsx: {conflict_xlsx_path}")
    print(
        "human_confirmed_sandbox_replay_323h_core_false_exclusion_check_xlsx: "
        f"{core_false_exclusion_xlsx_path}"
    )
    print(f"human_confirmed_sandbox_replay_323h_notes_md: {notes_md_path}")
    print(f"human_confirmed_sandbox_replay_323h_rule_application_log_jsonl: {rule_log_jsonl_path}")
    for key in [
        "total_confirmed_suggestion_count",
        "alias_confirmed_suggestion_count",
        "scope_confirmed_suggestion_count",
        "sandbox_rule_count",
        "sandbox_alias_rule_count",
        "sandbox_scope_rule_count",
        "effective_unique_rule_count",
        "duplicate_rule_count",
        "conflict_count",
        "affected_candidate_count",
        "trusted_gain_323h",
        "review_reduction_323h",
        "out_of_scope_or_rejected_gain_323h",
        "alias_trusted_gain_323h",
        "scope_review_reduction_323h",
        "scope_out_of_scope_or_rejected_gain_323h",
        "selected_core_trusted_rate_before_323h",
        "selected_core_trusted_rate_after_323h",
        "core_false_exclusion_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
