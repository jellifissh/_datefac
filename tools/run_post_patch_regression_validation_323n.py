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

from datefac.semantic.post_patch_regression_validation_323n import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PATCH_APPLICATION_DIR,
    DEFAULT_REFERENCE_322O_DIR,
    DEFAULT_SANDBOX_REPLAY_DIR,
    DEFAULT_TRUST_SPLIT_DIR,
    EXPECTED_323N_NOT_READY_DECISION,
    EXPECTED_323N_READY_DECISION,
    EXPECTED_323N_READY_WITH_WARNINGS_DECISION,
    build_post_patch_regression_validation_323n,
    load_post_patch_regression_validation_323n_inputs,
)
from datefac.semantic.post_patch_regression_validation_323n_report import (  # noqa: E402
    AFFECTED_CANDIDATES_SHEET_ORDER,
    BEFORE_AFTER_SHEET_ORDER,
    post_patch_regression_validation_323n_decision_markdown,
    post_patch_regression_validation_323n_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323N",
        "output_dir": str(output_dir),
        "official_rule_visibility_total": 0,
        "alias_rules_visible": 0,
        "scope_rules_visible": 0,
        "trusted_total_before_323n": 0,
        "trusted_total_after_323n": 0,
        "review_required_total_before_323n": 0,
        "review_required_total_after_323n": 0,
        "rejected_total_before_323n": 0,
        "rejected_total_after_323n": 0,
        "trusted_gain_323n": 0,
        "review_reduction_323n": 0,
        "out_of_scope_or_rejected_gain_323n": 0,
        "affected_candidate_count": 0,
        "selected_core_trusted_rate_before_323n": 0,
        "selected_core_trusted_rate_after_323n": 0,
        "core_false_exclusion_count": 0,
        "historical_duplicate_count": 0,
        "current_duplicate_count": 0,
        "new_duplicate_delta_count": 0,
        "conflict_count": 0,
        "rollback_artifact_check_passed": False,
        "source_linkage_all_present": False,
        "no_official_asset_modification_during_323n": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323N_NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    decision_json = {
        "decision": EXPECTED_323N_NOT_READY_DECISION,
        "qa_fail_count": 1,
        "qa_warn_count": 0,
        "blocking_reasons": [code],
        "warning_reasons": [],
        "rollback_recommendation": "Missing required inputs. Review upstream stage outputs before any rollback decision.",
    }

    before_after_sheets = {
        "summary": pd.DataFrame([summary]),
        "metric_comparison": pd.DataFrame(),
        "rule_application_alignment": pd.DataFrame(),
        "official_rule_visibility": pd.DataFrame(),
        "source_linkage": pd.DataFrame(),
        "duplicate_conflict": pd.DataFrame(),
        "rollback_artifacts": pd.DataFrame(),
        "trusted_after_preview_323n": pd.DataFrame(),
        "review_after_preview_323n": pd.DataFrame(),
        "rejected_after_preview_323n": pd.DataFrame(),
        "qa_summary": pd.DataFrame(
            [
                {
                    "qa_pass_count": 0,
                    "qa_warn_count": 0,
                    "qa_fail_count": 1,
                    "blocking_reasons": code,
                    "decision": EXPECTED_323N_NOT_READY_DECISION,
                }
            ]
        ),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
        "known_limitations": pd.DataFrame(
            [{"limitation": "blocked_input", "detail": "Required input directory is missing."}]
        ),
    }
    affected_candidate_sheets = {
        "summary": pd.DataFrame([summary]),
        "candidate_before_after_diff_323n": pd.DataFrame(),
        "impact_by_rule_323n": pd.DataFrame(),
        "core_false_exclusion_check": pd.DataFrame(),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
    }

    summary_json_path = output_dir / "post_patch_regression_validation_323n_summary.json"
    qa_json_path = output_dir / "post_patch_regression_validation_323n_qa.json"
    visibility_json_path = output_dir / "post_patch_regression_validation_323n_official_rule_visibility.json"
    duplicate_conflict_json_path = output_dir / "post_patch_regression_validation_323n_duplicate_conflict_check.json"
    rollback_check_json_path = output_dir / "post_patch_regression_validation_323n_rollback_artifact_check.json"
    before_after_xlsx_path = output_dir / "post_patch_regression_validation_323n_before_after_comparison.xlsx"
    affected_candidates_xlsx_path = output_dir / "post_patch_regression_validation_323n_affected_candidates.xlsx"
    report_md_path = output_dir / "post_patch_regression_validation_323n_regression_notes.md"
    decision_md_path = output_dir / "post_patch_regression_validation_323n_decision.md"

    write_json(summary_json_path, summary)
    write_json(qa_json_path, qa_json)
    write_json(
        visibility_json_path,
        {"official_rule_visibility_total": 0, "alias_rules_visible": 0, "scope_rules_visible": 0},
    )
    write_json(
        duplicate_conflict_json_path,
        {"historical_duplicate_count": 0, "current_duplicate_count": 0, "new_duplicate_delta_count": 0, "conflict_count": 0},
    )
    write_json(
        rollback_check_json_path,
        {"rollback_artifact_check_passed": False, "artifacts": []},
    )
    write_excel(before_after_xlsx_path, before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    write_excel(affected_candidates_xlsx_path, affected_candidate_sheets, AFFECTED_CANDIDATES_SHEET_ORDER)
    report_md_path.write_text(post_patch_regression_validation_323n_markdown(summary), encoding="utf-8")
    decision_md_path.write_text(post_patch_regression_validation_323n_decision_markdown(decision_json), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323N post-patch regression validation.")
    parser.add_argument("--patch-application-dir", default=str(DEFAULT_PATCH_APPLICATION_DIR))
    parser.add_argument("--sandbox-replay-dir", default=str(DEFAULT_SANDBOX_REPLAY_DIR))
    parser.add_argument("--trust-split-dir", default=str(DEFAULT_TRUST_SPLIT_DIR))
    parser.add_argument("--reference-322o-dir", default=str(DEFAULT_REFERENCE_322O_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    patch_application_dir = Path(args.patch_application_dir)
    sandbox_replay_dir = Path(args.sandbox_replay_dir)
    trust_split_dir = Path(args.trust_split_dir)
    reference_322o_dir = Path(args.reference_322o_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (patch_application_dir, "BLOCKED_MISSING_323M_PATCH_APPLICATION_DIR"),
        (sandbox_replay_dir, "BLOCKED_MISSING_323H_SANDBOX_REPLAY_DIR"),
        (trust_split_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR"),
        (reference_322o_dir, "BLOCKED_MISSING_322O_REFERENCE_DIR"),
    ]
    for path, code in required_dirs:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"post_patch_regression_validation_323n_summary_json: {output_dir / 'post_patch_regression_validation_323n_summary.json'}")
            return 0

    inputs = load_post_patch_regression_validation_323n_inputs(
        patch_application_dir=patch_application_dir,
        sandbox_replay_dir=sandbox_replay_dir,
        trust_split_dir=trust_split_dir,
        reference_322o_dir=reference_322o_dir,
    )
    artifacts = build_post_patch_regression_validation_323n(
        patch_summary=inputs["patch_summary"],
        patch_qa=inputs["patch_qa"],
        patch_apply_proof=inputs["patch_apply_proof"],
        patch_application_log_df=inputs["patch_application_log_df"],
        sandbox_summary=inputs["sandbox_summary"],
        trust_summary=inputs["trust_summary"],
        selected_candidates_df=inputs["selected_candidates_df"],
        reference_322o_summary=inputs["reference_322o_summary"],
        output_dir=output_dir,
    )

    summary = artifacts["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "post_patch_regression_validation_323n_summary.json",
        "qa_json": output_dir / "post_patch_regression_validation_323n_qa.json",
        "visibility_json": output_dir / "post_patch_regression_validation_323n_official_rule_visibility.json",
        "duplicate_conflict_json": output_dir / "post_patch_regression_validation_323n_duplicate_conflict_check.json",
        "rollback_check_json": output_dir / "post_patch_regression_validation_323n_rollback_artifact_check.json",
        "before_after_xlsx": output_dir / "post_patch_regression_validation_323n_before_after_comparison.xlsx",
        "affected_candidates_xlsx": output_dir / "post_patch_regression_validation_323n_affected_candidates.xlsx",
        "report_md": output_dir / "post_patch_regression_validation_323n_regression_notes.md",
        "decision_md": output_dir / "post_patch_regression_validation_323n_decision.md",
    }

    before_after_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "metric_comparison": artifacts["metric_comparison_df"],
        "rule_application_alignment": artifacts["application_alignment_df"],
        "official_rule_visibility": artifacts["visibility_df"],
        "source_linkage": artifacts["source_linkage_df"],
        "duplicate_conflict": artifacts["duplicate_conflict_df"],
        "rollback_artifacts": artifacts["rollback_artifact_df"],
        "trusted_after_preview_323n": artifacts["trusted_after_df"],
        "review_after_preview_323n": artifacts["review_after_df"],
        "rejected_after_preview_323n": artifacts["rejected_after_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    affected_candidate_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "candidate_before_after_diff_323n": artifacts["diff_df"],
        "impact_by_rule_323n": artifacts["impact_df"],
        "core_false_exclusion_check": artifacts["core_false_exclusion_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["visibility_json"], artifacts["official_rule_visibility_json"])
    write_json(output_files["duplicate_conflict_json"], artifacts["duplicate_conflict_json"])
    write_json(output_files["rollback_check_json"], artifacts["rollback_artifact_check_json"])
    write_excel(output_files["before_after_xlsx"], before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    write_excel(output_files["affected_candidates_xlsx"], affected_candidate_sheets, AFFECTED_CANDIDATES_SHEET_ORDER)
    output_files["report_md"].write_text(
        post_patch_regression_validation_323n_markdown(summary),
        encoding="utf-8",
    )
    output_files["decision_md"].write_text(
        post_patch_regression_validation_323n_decision_markdown(artifacts["decision_json"]),
        encoding="utf-8",
    )

    output_files_written = all(path.exists() for path in output_files.values())
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
    summary["blocking_reasons"] = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    warn_names = qa_df.loc[qa_df["status"] == "WARN", "check_name"].astype(str).tolist() if not qa_df.empty else []
    if summary["qa_fail_count"] > 0:
        summary["decision"] = EXPECTED_323N_NOT_READY_DECISION
    elif warn_names and set(warn_names).issubset({"duplicates::historical_duplicates_unchanged"}):
        summary["decision"] = EXPECTED_323N_READY_WITH_WARNINGS_DECISION
    else:
        summary["decision"] = EXPECTED_323N_READY_DECISION

    write_json(output_files["summary_json"], summary)
    write_json(
        output_files["qa_json"],
        {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    before_after_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    before_after_sheets["qa_summary"] = pd.DataFrame(
        [
            {
                "qa_pass_count": summary["qa_pass_count"],
                "qa_warn_count": summary["qa_warn_count"],
                "qa_fail_count": summary["qa_fail_count"],
                "blocking_reasons": " | ".join(summary["blocking_reasons"]),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")
    before_after_sheets["qa_checks"] = qa_df
    affected_candidate_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    affected_candidate_sheets["qa_checks"] = qa_df
    write_excel(output_files["before_after_xlsx"], before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    write_excel(output_files["affected_candidates_xlsx"], affected_candidate_sheets, AFFECTED_CANDIDATES_SHEET_ORDER)
    output_files["report_md"].write_text(
        post_patch_regression_validation_323n_markdown(summary),
        encoding="utf-8",
    )
    output_files["decision_md"].write_text(
        post_patch_regression_validation_323n_decision_markdown(
            {
                "decision": summary["decision"],
                "qa_fail_count": summary["qa_fail_count"],
                "qa_warn_count": summary["qa_warn_count"],
                "blocking_reasons": summary["blocking_reasons"],
                "warning_reasons": warn_names,
                "rollback_recommendation": (
                    "Use 323M rollback artifacts for review because blocking regression issues were detected."
                    if summary["qa_fail_count"] > 0
                    else "No rollback recommended. Official patch cycle can be closed."
                ),
            }
        ),
        encoding="utf-8",
    )

    print(f"post_patch_regression_validation_323n_summary_json: {output_files['summary_json']}")
    print(f"post_patch_regression_validation_323n_qa_json: {output_files['qa_json']}")
    print(f"post_patch_regression_validation_323n_official_rule_visibility_json: {output_files['visibility_json']}")
    print(f"post_patch_regression_validation_323n_duplicate_conflict_json: {output_files['duplicate_conflict_json']}")
    print(f"post_patch_regression_validation_323n_rollback_artifact_check_json: {output_files['rollback_check_json']}")
    print(f"post_patch_regression_validation_323n_before_after_comparison_xlsx: {output_files['before_after_xlsx']}")
    print(f"post_patch_regression_validation_323n_affected_candidates_xlsx: {output_files['affected_candidates_xlsx']}")
    print(f"post_patch_regression_validation_323n_regression_notes_md: {output_files['report_md']}")
    print(f"post_patch_regression_validation_323n_decision_md: {output_files['decision_md']}")
    for key in [
        "official_rule_visibility_total",
        "alias_rules_visible",
        "scope_rules_visible",
        "trusted_gain_323n",
        "review_reduction_323n",
        "out_of_scope_or_rejected_gain_323n",
        "affected_candidate_count",
        "core_false_exclusion_count",
        "current_duplicate_count",
        "new_duplicate_delta_count",
        "conflict_count",
        "rollback_artifact_check_passed",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
