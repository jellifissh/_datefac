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

from datefac.semantic.post_patch_regression_validation_325o import (  # noqa: E402
    DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SANDBOX_REPLAY_DIR,
    DEFAULT_TRUST_SPLIT_DIR,
    NOT_READY_DECISION,
    build_post_patch_regression_validation_325o,
    load_post_patch_regression_validation_325o_inputs,
)
from datefac.semantic.post_patch_regression_validation_325o_report import (  # noqa: E402
    post_patch_regression_validation_325o_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325O",
        "output_dir": str(output_dir),
        "official_rule_visibility_total": 0,
        "official_alias_rules_visible": 0,
        "missing_official_alias_rule_count": 0,
        "wrong_target_metric_count": 0,
        "affected_candidate_count": 0,
        "trusted_gain_325o": 0,
        "review_reduction_325o": 0,
        "out_of_scope_or_rejected_gain_325o": 0,
        "current_duplicate_count": 0,
        "duplicate_delta_count": 0,
        "target_conflict_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
        "core_false_mapping_count": 0,
        "rollback_artifact_check_passed": False,
        "formal_scope_rules_hash_matches_325n": False,
        "no_official_asset_modification_during_325o": True,
        "trust_split_summary_loaded": False,
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
    write_json(output_dir / "post_patch_regression_validation_325o_summary.json", summary)
    write_json(output_dir / "post_patch_regression_validation_325o_qa.json", qa_json)
    write_json(
        output_dir / "post_patch_regression_validation_325o_official_rule_visibility.json",
        {"official_rule_visibility_total": 0, "visibility_records": []},
    )
    write_json(
        output_dir / "post_patch_regression_validation_325o_rollback_artifact_check.json",
        {"rollback_artifact_check_passed": False, "artifacts": []},
    )
    write_json(
        output_dir / "post_patch_regression_validation_325o_no_apply_proof.json",
        {"stage": "325O", "official_assets_written": [], "no_official_asset_modification_during_325o": True},
    )
    write_excel(
        output_dir / "post_patch_regression_validation_325o_before_after_comparison.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "before_after_hashes": pd.DataFrame(),
            "official_rule_visibility": pd.DataFrame(),
            "impact_metrics": pd.DataFrame(),
            "duplicate_conflict": pd.DataFrame(),
            "rollback_artifacts": pd.DataFrame(),
            "semantic_constraints": pd.DataFrame(),
            "qa_summary": pd.DataFrame(
                [
                    {
                        "qa_pass_count": 0,
                        "qa_warn_count": 0,
                        "qa_fail_count": 1,
                        "blocking_reasons": code,
                        "decision": NOT_READY_DECISION,
                    }
                ]
            ),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": code}]),
        },
    )
    (output_dir / "post_patch_regression_validation_325o_report.md").write_text(
        post_patch_regression_validation_325o_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325O post-patch regression validation.")
    parser.add_argument("--official-patch-application-dir", default=str(DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR))
    parser.add_argument("--sandbox-replay-dir", default=str(DEFAULT_SANDBOX_REPLAY_DIR))
    parser.add_argument("--trust-split-dir", default=str(DEFAULT_TRUST_SPLIT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    official_patch_application_dir = Path(args.official_patch_application_dir)
    sandbox_replay_dir = Path(args.sandbox_replay_dir)
    trust_split_dir = Path(args.trust_split_dir)
    output_dir = Path(args.output_dir)

    for path, code in [
        (official_patch_application_dir, "BLOCKED_MISSING_325N_PATCH_APPLICATION_DIR"),
        (sandbox_replay_dir, "BLOCKED_MISSING_325I_SANDBOX_REPLAY_DIR"),
        (trust_split_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR"),
    ]:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"post_patch_regression_validation_325o_summary_json: {output_dir / 'post_patch_regression_validation_325o_summary.json'}")
            return 0

    inputs = load_post_patch_regression_validation_325o_inputs(
        official_patch_application_dir=official_patch_application_dir,
        sandbox_replay_dir=sandbox_replay_dir,
        trust_split_dir=trust_split_dir,
    )
    artifacts = build_post_patch_regression_validation_325o(
        patch_summary=inputs["patch_summary"],
        patch_qa=inputs["patch_qa"],
        patch_apply_proof=inputs["patch_apply_proof"],
        patch_rollback_plan=inputs["patch_rollback_plan"],
        patch_logs=inputs["patch_logs"],
        sandbox_summary=inputs["sandbox_summary"],
        sandbox_affected_rows=inputs["sandbox_affected_rows"],
        trust_summary=inputs["trust_summary"],
        alias_asset=inputs["alias_asset"],
        scope_asset=inputs["scope_asset"],
        official_patch_application_dir=official_patch_application_dir,
        sandbox_replay_dir=sandbox_replay_dir,
        trust_split_dir=trust_split_dir,
        output_dir=output_dir,
    )

    summary = artifacts["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "post_patch_regression_validation_325o_summary.json",
        "qa_json": output_dir / "post_patch_regression_validation_325o_qa.json",
        "before_after_xlsx": output_dir / "post_patch_regression_validation_325o_before_after_comparison.xlsx",
        "visibility_xlsx": output_dir / "post_patch_regression_validation_325o_official_rule_visibility.xlsx",
        "impact_xlsx": output_dir / "post_patch_regression_validation_325o_impact_metrics.xlsx",
        "semantic_xlsx": output_dir / "post_patch_regression_validation_325o_semantic_constraint_check.xlsx",
        "duplicate_conflict_xlsx": output_dir / "post_patch_regression_validation_325o_duplicate_conflict_check.xlsx",
        "visibility_json": output_dir / "post_patch_regression_validation_325o_official_rule_visibility.json",
        "rollback_check_json": output_dir / "post_patch_regression_validation_325o_rollback_artifact_check.json",
        "no_apply_proof_json": output_dir / "post_patch_regression_validation_325o_no_apply_proof.json",
        "report_md": output_dir / "post_patch_regression_validation_325o_report.md",
    }

    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "before_after_hashes": artifacts["before_after_df"],
        "official_rule_visibility": artifacts["visibility_df"],
        "impact_metrics": artifacts["impact_df"],
        "duplicate_conflict": artifacts["duplicate_conflict_df"],
        "rollback_artifacts": artifacts["rollback_artifact_df"],
        "semantic_constraints": artifacts["semantic_constraint_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["visibility_json"], artifacts["visibility_json"])
    write_json(output_files["rollback_check_json"], artifacts["rollback_artifact_check_json"])
    write_json(output_files["no_apply_proof_json"], artifacts["no_apply_proof_json"])
    write_excel(output_files["before_after_xlsx"], sheets)
    write_excel(
        output_files["visibility_xlsx"],
        {"official_rule_visibility": artifacts["visibility_df"], "qa_checks": artifacts["qa_checks_df"]},
    )
    write_excel(
        output_files["impact_xlsx"],
        {"impact_metrics": artifacts["impact_df"], "qa_checks": artifacts["qa_checks_df"]},
    )
    write_excel(
        output_files["semantic_xlsx"],
        {"semantic_constraints": artifacts["semantic_constraint_df"], "qa_checks": artifacts["qa_checks_df"]},
    )
    write_excel(
        output_files["duplicate_conflict_xlsx"],
        {"duplicate_conflict": artifacts["duplicate_conflict_df"], "qa_checks": artifacts["qa_checks_df"]},
    )
    output_files["report_md"].write_text(
        post_patch_regression_validation_325o_markdown(summary),
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
    if summary["qa_fail_count"] > 0:
        summary["decision"] = NOT_READY_DECISION

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
    sheets["summary"] = pd.DataFrame([summary]).fillna("")
    sheets["qa_summary"] = pd.DataFrame(
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
    sheets["qa_checks"] = qa_df
    write_excel(output_files["before_after_xlsx"], sheets)
    output_files["report_md"].write_text(
        post_patch_regression_validation_325o_markdown(summary),
        encoding="utf-8",
    )

    print(f"post_patch_regression_validation_325o_summary_json: {output_files['summary_json']}")
    print(f"post_patch_regression_validation_325o_qa_json: {output_files['qa_json']}")
    print(f"post_patch_regression_validation_325o_before_after_comparison_xlsx: {output_files['before_after_xlsx']}")
    print(f"post_patch_regression_validation_325o_official_rule_visibility_xlsx: {output_files['visibility_xlsx']}")
    print(f"post_patch_regression_validation_325o_impact_metrics_xlsx: {output_files['impact_xlsx']}")
    print(f"post_patch_regression_validation_325o_semantic_constraint_check_xlsx: {output_files['semantic_xlsx']}")
    print(f"post_patch_regression_validation_325o_duplicate_conflict_check_xlsx: {output_files['duplicate_conflict_xlsx']}")
    print(f"post_patch_regression_validation_325o_official_rule_visibility_json: {output_files['visibility_json']}")
    print(f"post_patch_regression_validation_325o_rollback_artifact_check_json: {output_files['rollback_check_json']}")
    print(f"post_patch_regression_validation_325o_no_apply_proof_json: {output_files['no_apply_proof_json']}")
    print(f"post_patch_regression_validation_325o_report_md: {output_files['report_md']}")
    for key in [
        "official_rule_visibility_total",
        "official_alias_rules_visible",
        "missing_official_alias_rule_count",
        "wrong_target_metric_count",
        "affected_candidate_count",
        "trusted_gain_325o",
        "review_reduction_325o",
        "out_of_scope_or_rejected_gain_325o",
        "target_conflict_count",
        "adjusted_metric_mismatch_count",
        "diluted_eps_mismatch_count",
        "core_false_mapping_count",
        "rollback_artifact_check_passed",
        "no_official_asset_modification_during_325o",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
