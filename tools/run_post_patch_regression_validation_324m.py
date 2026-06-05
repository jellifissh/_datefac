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

from datefac.semantic.post_patch_regression_validation_324m import (  # noqa: E402
    DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SANDBOX_REPLAY_DIR,
    DEFAULT_TRUST_SPLIT_DIR,
    NOT_READY_DECISION,
    build_post_patch_regression_validation_324m,
    load_post_patch_regression_validation_324m_inputs,
)
from datefac.semantic.post_patch_regression_validation_324m_report import (  # noqa: E402
    BEFORE_AFTER_SHEET_ORDER,
    post_patch_regression_validation_324m_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324M",
        "output_dir": str(output_dir),
        "official_rule_visibility_total": 0,
        "scope_rules_visible": 0,
        "alias_rules_visible": 0,
        "affected_candidate_count": 0,
        "trusted_gain_324m": 0,
        "review_reduction_324m": 0,
        "out_of_scope_or_rejected_gain_324m": 0,
        "core_false_exclusion_count": 0,
        "historical_duplicate_count": 0,
        "current_duplicate_count": 0,
        "new_duplicate_delta_count": 0,
        "conflict_count": 0,
        "rollback_artifact_check_passed": False,
        "alias_official_asset_unchanged_confirmed": False,
        "no_official_asset_modification_during_324m": True,
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
    write_json(output_dir / "post_patch_regression_validation_324m_summary.json", summary)
    write_json(output_dir / "post_patch_regression_validation_324m_qa.json", qa_json)
    write_json(
        output_dir / "post_patch_regression_validation_324m_rollback_artifact_check.json",
        {"rollback_artifact_check_passed": False, "artifacts": []},
    )
    write_json(
        output_dir / "post_patch_regression_validation_324m_no_apply_proof.json",
        {"stage": "324M", "official_assets_written": [], "no_official_asset_modification_during_324m": True},
    )
    write_excel(
        output_dir / "post_patch_regression_validation_324m_before_after_comparison.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "before_after_hashes": pd.DataFrame(),
            "official_rule_visibility": pd.DataFrame(),
            "impact_metrics": pd.DataFrame(),
            "duplicate_conflict": pd.DataFrame(),
            "rollback_artifacts": pd.DataFrame(),
            "core_false_exclusion": pd.DataFrame(),
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
        BEFORE_AFTER_SHEET_ORDER,
    )
    (output_dir / "post_patch_regression_validation_324m_report.md").write_text(
        post_patch_regression_validation_324m_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 324M post-patch regression validation.")
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
        (official_patch_application_dir, "BLOCKED_MISSING_324L_PATCH_APPLICATION_DIR"),
        (sandbox_replay_dir, "BLOCKED_MISSING_324G_SANDBOX_REPLAY_DIR"),
        (trust_split_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR"),
    ]:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"post_patch_regression_validation_324m_summary_json: {output_dir / 'post_patch_regression_validation_324m_summary.json'}")
            return 0

    inputs = load_post_patch_regression_validation_324m_inputs(
        official_patch_application_dir=official_patch_application_dir,
        sandbox_replay_dir=sandbox_replay_dir,
        trust_split_dir=trust_split_dir,
    )
    artifacts = build_post_patch_regression_validation_324m(
        patch_summary=inputs["patch_summary"],
        patch_qa=inputs["patch_qa"],
        patch_apply_proof=inputs["patch_apply_proof"],
        patch_rollback_plan=inputs["patch_rollback_plan"],
        sandbox_summary=inputs["sandbox_summary"],
        trust_summary=inputs["trust_summary"],
        scope_asset=inputs["scope_asset"],
        alias_asset=inputs["alias_asset"],
        official_patch_application_dir=official_patch_application_dir,
        sandbox_replay_dir=sandbox_replay_dir,
        trust_split_dir=trust_split_dir,
        output_dir=output_dir,
    )

    summary = artifacts["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "post_patch_regression_validation_324m_summary.json",
        "qa_json": output_dir / "post_patch_regression_validation_324m_qa.json",
        "before_after_xlsx": output_dir / "post_patch_regression_validation_324m_before_after_comparison.xlsx",
        "affected_candidates_xlsx": output_dir / "post_patch_regression_validation_324m_affected_candidates.xlsx",
        "visibility_xlsx": output_dir / "post_patch_regression_validation_324m_official_rule_visibility.xlsx",
        "core_false_xlsx": output_dir / "post_patch_regression_validation_324m_core_false_exclusion_check.xlsx",
        "duplicate_conflict_xlsx": output_dir / "post_patch_regression_validation_324m_duplicate_conflict_check.xlsx",
        "rollback_check_json": output_dir / "post_patch_regression_validation_324m_rollback_artifact_check.json",
        "no_apply_proof_json": output_dir / "post_patch_regression_validation_324m_no_apply_proof.json",
        "report_md": output_dir / "post_patch_regression_validation_324m_report.md",
    }

    before_after_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "before_after_hashes": artifacts["before_after_df"],
        "official_rule_visibility": artifacts["visibility_df"],
        "impact_metrics": artifacts["impact_df"],
        "duplicate_conflict": artifacts["duplicate_conflict_df"],
        "rollback_artifacts": artifacts["rollback_artifact_df"],
        "core_false_exclusion": artifacts["core_false_exclusion_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["rollback_check_json"], artifacts["rollback_artifact_check_json"])
    write_json(output_files["no_apply_proof_json"], artifacts["no_apply_proof_json"])
    write_excel(output_files["before_after_xlsx"], before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    write_excel(output_files["affected_candidates_xlsx"], {"impact_metrics": artifacts["impact_df"], "qa_checks": artifacts["qa_checks_df"]}, ["impact_metrics", "qa_checks"])
    write_excel(output_files["visibility_xlsx"], {"official_rule_visibility": artifacts["visibility_df"], "qa_checks": artifacts["qa_checks_df"]}, ["official_rule_visibility", "qa_checks"])
    write_excel(output_files["core_false_xlsx"], {"core_false_exclusion": artifacts["core_false_exclusion_df"], "qa_checks": artifacts["qa_checks_df"]}, ["core_false_exclusion", "qa_checks"])
    write_excel(output_files["duplicate_conflict_xlsx"], {"duplicate_conflict": artifacts["duplicate_conflict_df"], "qa_checks": artifacts["qa_checks_df"]}, ["duplicate_conflict", "qa_checks"])
    output_files["report_md"].write_text(
        post_patch_regression_validation_324m_markdown(summary),
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
    write_excel(output_files["before_after_xlsx"], before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    output_files["report_md"].write_text(
        post_patch_regression_validation_324m_markdown(summary),
        encoding="utf-8",
    )

    print(f"post_patch_regression_validation_324m_summary_json: {output_files['summary_json']}")
    print(f"post_patch_regression_validation_324m_qa_json: {output_files['qa_json']}")
    print(f"post_patch_regression_validation_324m_before_after_comparison_xlsx: {output_files['before_after_xlsx']}")
    print(f"post_patch_regression_validation_324m_affected_candidates_xlsx: {output_files['affected_candidates_xlsx']}")
    print(f"post_patch_regression_validation_324m_official_rule_visibility_xlsx: {output_files['visibility_xlsx']}")
    print(f"post_patch_regression_validation_324m_core_false_exclusion_check_xlsx: {output_files['core_false_xlsx']}")
    print(f"post_patch_regression_validation_324m_duplicate_conflict_check_xlsx: {output_files['duplicate_conflict_xlsx']}")
    print(f"post_patch_regression_validation_324m_rollback_artifact_check_json: {output_files['rollback_check_json']}")
    print(f"post_patch_regression_validation_324m_no_apply_proof_json: {output_files['no_apply_proof_json']}")
    print(f"post_patch_regression_validation_324m_report_md: {output_files['report_md']}")
    for key in [
        "official_rule_visibility_total",
        "scope_rules_visible",
        "alias_rules_visible",
        "affected_candidate_count",
        "trusted_gain_324m",
        "review_reduction_324m",
        "out_of_scope_or_rejected_gain_324m",
        "core_false_exclusion_count",
        "current_duplicate_count",
        "new_duplicate_delta_count",
        "conflict_count",
        "rollback_artifact_check_passed",
        "no_official_asset_modification_during_324m",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
