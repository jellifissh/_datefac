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

from datefac.semantic.scope_noise_human_confirmed_sandbox_replay_324g import (  # noqa: E402
    NOT_READY_DECISION,
    build_scope_noise_human_confirmed_sandbox_replay_324g,
    load_scope_noise_human_confirmed_sandbox_replay_324g_inputs,
)
from datefac.semantic.scope_noise_human_confirmed_sandbox_replay_324g_report import (  # noqa: E402
    scope_noise_human_confirmed_sandbox_replay_324g_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324G",
        "output_dir": str(output_dir),
        "confirmed_scope_noise_count": 0,
        "sandbox_rule_count": 0,
        "sandbox_scope_rule_count": 0,
        "sandbox_alias_rule_count": 0,
        "effective_unique_rule_count": 0,
        "duplicate_count": 0,
        "conflict_count": 0,
        "full_pool_label_match_count": 0,
        "review_required_label_match_count": 0,
        "trusted_label_match_count": 0,
        "rejected_label_match_count": 0,
        "trusted_total_before_324g": 0,
        "trusted_total_after_324g": 0,
        "review_required_total_before_324g": 0,
        "review_required_total_after_324g": 0,
        "rejected_total_before_324g": 0,
        "rejected_total_after_324g": 0,
        "affected_candidate_count": 0,
        "trusted_gain_324g": 0,
        "review_reduction_324g": 0,
        "out_of_scope_or_rejected_gain_324g": 0,
        "alias_trusted_gain_324g": 0,
        "alias_review_reduction_324g": 0,
        "scope_trusted_gain_324g": 0,
        "scope_review_reduction_324g": 0,
        "scope_out_of_scope_or_rejected_gain_324g": 0,
        "selected_core_trusted_rate_before_324g": 0,
        "selected_core_trusted_rate_after_324g": 0,
        "baseline_unknown_metric_candidate_count": 0,
        "baseline_unit_unknown_candidate_count": 0,
        "baseline_manual_review_count": 0,
        "remaining_unknown_metric_candidate_count": 0,
        "remaining_unit_unknown_candidate_count": 0,
        "remaining_manual_review_count": 0,
        "reference_323n_affected_candidate_count": 0,
        "reference_323n_trusted_gain": 0,
        "reference_323n_review_reduction": 0,
        "reference_323n_out_of_scope_or_rejected_gain": 0,
        "core_false_exclusion_count": 0,
        "official_assets_not_modified": True,
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
    write_json(
        output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_summary.json", summary
    )
    write_json(
        output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_qa.json", qa_json
    )
    write_json(
        output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_sandbox_rule_set.json",
        {
            "stage": "324G",
            "mode": "sandbox_replay_only",
            "source_rule_count": 0,
            "confirmed_scope_noise_count": 0,
            "alias_rule_count": 0,
            "scope_rule_count": 0,
            "duplicate_conflict_summary": [],
            "scope_rules": [],
        },
    )
    write_excel(
        output_dir
        / "scope_noise_human_confirmed_sandbox_replay_324g_before_after_comparison.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "before_after_overview": empty,
            "rule_application_overview": empty,
            "alias_scope_contribution": empty,
            "full_pool_match_breakdown": empty,
            "remaining_review_burden": empty,
            "qa_checks": pd.DataFrame(qa_json["checks"]),
        },
    )
    write_excel(
        output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_affected_candidates.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "source_rule_inventory": empty,
            "candidate_before_after_diff": empty,
            "patch_impact_by_rule": empty,
            "qa_checks": pd.DataFrame(qa_json["checks"]),
        },
    )
    write_excel(
        output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_scope_replay.xlsx",
        {"scope_rules": empty, "scope_diff": empty},
    )
    write_excel(
        output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_conflict_report.xlsx",
        {"duplicate_conflict": empty},
    )
    write_excel(
        output_dir
        / "scope_noise_human_confirmed_sandbox_replay_324g_core_false_exclusion_check.xlsx",
        {"core_false_exclusion": empty},
    )
    write_jsonl(
        output_dir
        / "scope_noise_human_confirmed_sandbox_replay_324g_rule_application_log.jsonl",
        empty,
    )
    (output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_notes.md").write_text(
        scope_noise_human_confirmed_sandbox_replay_324g_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 324G scope-noise human-confirmed sandbox replay."
    )
    parser.add_argument("--reviewed-confirmation-dir", required=True)
    parser.add_argument("--scope-noise-response-schema-validation-dir", required=True)
    parser.add_argument("--safe-adjudicator-request-dir", required=True)
    parser.add_argument("--scope-refinement-dir", required=True)
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--post-patch-regression-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    reviewed_confirmation_dir = Path(args.reviewed_confirmation_dir)
    scope_noise_response_schema_validation_dir = Path(
        args.scope_noise_response_schema_validation_dir
    )
    safe_adjudicator_request_dir = Path(args.safe_adjudicator_request_dir)
    scope_refinement_dir = Path(args.scope_refinement_dir)
    trust_split_dir = Path(args.trust_split_dir)
    post_patch_regression_dir = Path(args.post_patch_regression_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (reviewed_confirmation_dir, "BLOCKED_MISSING_324F_REVIEWED_DIR"),
        (
            scope_noise_response_schema_validation_dir,
            "BLOCKED_MISSING_324E_SCHEMA_VALIDATION_DIR",
        ),
        (safe_adjudicator_request_dir, "BLOCKED_MISSING_324C_SAFE_REQUEST_DIR"),
        (scope_refinement_dir, "BLOCKED_MISSING_324A_SCOPE_REFINEMENT_DIR"),
        (trust_split_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR"),
        (post_patch_regression_dir, "BLOCKED_MISSING_323N_POST_PATCH_REGRESSION_DIR"),
    ]
    for directory, code in required_dirs:
        if not directory.exists():
            _blocked_result(output_dir, code)
            print(
                "scope_noise_human_confirmed_sandbox_replay_324g_summary_json: "
                f"{output_dir / 'scope_noise_human_confirmed_sandbox_replay_324g_summary.json'}"
            )
            return 0

    inputs = load_scope_noise_human_confirmed_sandbox_replay_324g_inputs(
        reviewed_confirmation_dir=reviewed_confirmation_dir,
        scope_noise_response_schema_validation_dir=scope_noise_response_schema_validation_dir,
        safe_adjudicator_request_dir=safe_adjudicator_request_dir,
        scope_refinement_dir=scope_refinement_dir,
        trust_split_dir=trust_split_dir,
        post_patch_regression_dir=post_patch_regression_dir,
    )
    artifacts = build_scope_noise_human_confirmed_sandbox_replay_324g(
        reviewed_summary=inputs["reviewed_summary"],
        reviewed_qa=inputs["reviewed_qa"],
        reviewed_outcome=inputs["reviewed_outcome"],
        schema_validation_summary=inputs["schema_validation_summary"],
        safe_request_package=inputs["safe_request_package"],
        scope_refinement_summary=inputs["scope_refinement_summary"],
        scope_refinement_batch=inputs["scope_refinement_batch"],
        trust_summary=inputs["trust_summary"],
        selected_candidates_df=inputs["selected_candidates_df"],
        post_patch_summary=inputs["post_patch_summary"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_json_path = output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_summary.json"
    qa_json_path = output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_qa.json"
    rule_set_json_path = (
        output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_sandbox_rule_set.json"
    )
    before_after_xlsx_path = (
        output_dir
        / "scope_noise_human_confirmed_sandbox_replay_324g_before_after_comparison.xlsx"
    )
    affected_xlsx_path = (
        output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_affected_candidates.xlsx"
    )
    scope_xlsx_path = output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_scope_replay.xlsx"
    conflict_xlsx_path = (
        output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_conflict_report.xlsx"
    )
    core_false_exclusion_xlsx_path = (
        output_dir
        / "scope_noise_human_confirmed_sandbox_replay_324g_core_false_exclusion_check.xlsx"
    )
    rule_log_jsonl_path = (
        output_dir
        / "scope_noise_human_confirmed_sandbox_replay_324g_rule_application_log.jsonl"
    )
    notes_md_path = output_dir / "scope_noise_human_confirmed_sandbox_replay_324g_notes.md"

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
            "full_pool_match_breakdown": artifacts["full_pool_match_breakdown_df"],
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
                        "check_name": "output::artifacts_written_successfully",
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
        summary["decision"] = "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_WITH_WARNINGS"
    else:
        summary["decision"] = (
            "SCOPE_NOISE_HUMAN_CONFIRMED_SANDBOX_REPLAY_324G_READY_FOR_324H_OFFICIAL_RULE_CANDIDATE"
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
            "full_pool_match_breakdown": artifacts["full_pool_match_breakdown_df"],
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

    print(f"scope_noise_human_confirmed_sandbox_replay_324g_summary_json: {summary_json_path}")
    print(f"scope_noise_human_confirmed_sandbox_replay_324g_qa_json: {qa_json_path}")
    print(f"scope_noise_human_confirmed_sandbox_replay_324g_sandbox_rule_set_json: {rule_set_json_path}")
    print(
        "scope_noise_human_confirmed_sandbox_replay_324g_before_after_comparison_xlsx: "
        f"{before_after_xlsx_path}"
    )
    print(
        "scope_noise_human_confirmed_sandbox_replay_324g_affected_candidates_xlsx: "
        f"{affected_xlsx_path}"
    )
    print(f"scope_noise_human_confirmed_sandbox_replay_324g_scope_replay_xlsx: {scope_xlsx_path}")
    print(
        "scope_noise_human_confirmed_sandbox_replay_324g_conflict_report_xlsx: "
        f"{conflict_xlsx_path}"
    )
    print(
        "scope_noise_human_confirmed_sandbox_replay_324g_core_false_exclusion_check_xlsx: "
        f"{core_false_exclusion_xlsx_path}"
    )
    print(f"scope_noise_human_confirmed_sandbox_replay_324g_rule_application_log_jsonl: {rule_log_jsonl_path}")
    print(f"scope_noise_human_confirmed_sandbox_replay_324g_notes_md: {notes_md_path}")
    for key in [
        "confirmed_scope_noise_count",
        "sandbox_rule_count",
        "duplicate_count",
        "conflict_count",
        "affected_candidate_count",
        "trusted_gain_324g",
        "review_reduction_324g",
        "out_of_scope_or_rejected_gain_324g",
        "core_false_exclusion_count",
        "official_assets_not_modified",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
