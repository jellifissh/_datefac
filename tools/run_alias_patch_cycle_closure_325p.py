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

from datefac.semantic.alias_patch_cycle_closure_325p import (  # noqa: E402
    DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_PATCH_REGRESSION_DIR,
    DEFAULT_PREVIOUS_CYCLE_CLOSURE_DIR,
    DEFAULT_REMAINING_BURDEN_DIR,
    NOT_READY_DECISION,
    build_alias_patch_cycle_closure_325p,
    load_alias_patch_cycle_closure_325p_inputs,
)
from datefac.semantic.alias_patch_cycle_closure_325p_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    alias_patch_cycle_closure_325p_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325P",
        "output_dir": str(output_dir),
        "official_alias_rule_count_325": 0,
        "trusted_gain_325": 0,
        "review_reduction_325": 0,
        "out_of_scope_or_rejected_gain_325": 0,
        "affected_candidate_count_325": 0,
        "duplicate_delta_count": 0,
        "target_conflict_count": 0,
        "adjusted_metric_mismatch_count": 0,
        "diluted_eps_mismatch_count": 0,
        "core_false_mapping_count": 0,
        "rollback_artifact_check_passed": False,
        "cumulative_official_rule_count_after_325": 0,
        "cumulative_trusted_gain_after_325": 0,
        "cumulative_review_reduction_after_325": 0,
        "remaining_burden_status": "blocked",
        "primary_next_direction": "",
        "secondary_next_direction": "",
        "no_official_asset_modification_during_325p": True,
        "official_assets_written": [],
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
    write_json(output_dir / "alias_patch_cycle_closure_325p_summary.json", summary)
    write_json(output_dir / "alias_patch_cycle_closure_325p_qa.json", qa_json)
    write_json(
        output_dir / "alias_patch_cycle_closure_325p_closure.json",
        {"funnel_counts_325": {}, "cycle_325": {}, "previous_combined": {}, "combined_through_325": {}, "next_cycle_recommendations": []},
    )
    write_json(
        output_dir / "alias_patch_cycle_closure_325p_no_apply_proof.json",
        {"stage": "325P", "official_assets_written": [], "no_official_asset_modification_during_325p": True},
    )
    empty_sheets = {
        "summary": pd.DataFrame([summary]),
        "funnel_counts": pd.DataFrame(),
        "cycle_summary": pd.DataFrame(),
        "stage_timeline": pd.DataFrame(),
        "remaining_burden": pd.DataFrame(),
        "residual_risks": pd.DataFrame(),
        "next_cycle_recommendations": pd.DataFrame(),
        "official_asset_proof": pd.DataFrame(),
        "qa_summary": pd.DataFrame(
            [{"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": code, "decision": NOT_READY_DECISION}]
        ),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": code}]),
    }
    write_excel(output_dir / "alias_patch_cycle_closure_325p_summary.xlsx", empty_sheets, SUMMARY_SHEET_ORDER)
    write_excel(output_dir / "alias_patch_cycle_closure_325p_stage_timeline.xlsx", {"stage_timeline": pd.DataFrame()}, ["stage_timeline"])
    (output_dir / "alias_patch_cycle_closure_325p_report.md").write_text(
        alias_patch_cycle_closure_325p_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325P alias patch cycle closure.")
    parser.add_argument("--post-patch-regression-dir", default=str(DEFAULT_POST_PATCH_REGRESSION_DIR))
    parser.add_argument("--official-patch-application-dir", default=str(DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR))
    parser.add_argument("--previous-cycle-closure-dir", default=str(DEFAULT_PREVIOUS_CYCLE_CLOSURE_DIR))
    parser.add_argument("--remaining-burden-planning-dir", default=str(DEFAULT_REMAINING_BURDEN_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    post_patch_regression_dir = Path(args.post_patch_regression_dir)
    official_patch_application_dir = Path(args.official_patch_application_dir)
    previous_cycle_closure_dir = Path(args.previous_cycle_closure_dir)
    remaining_burden_planning_dir = Path(args.remaining_burden_planning_dir)
    output_dir = Path(args.output_dir)

    for path, code in [
        (post_patch_regression_dir / "post_patch_regression_validation_325o_summary.json", "BLOCKED_MISSING_325O_SUMMARY"),
        (official_patch_application_dir / "official_alias_patch_application_325n_summary.json", "BLOCKED_MISSING_325N_SUMMARY"),
        (previous_cycle_closure_dir / "official_scope_patch_cycle_closure_324n_summary.json", "BLOCKED_MISSING_324N_SUMMARY"),
        (remaining_burden_planning_dir / "remaining_burden_planning_323p_summary.json", "BLOCKED_MISSING_323P_SUMMARY"),
    ]:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"alias_patch_cycle_closure_325p_summary_json: {output_dir / 'alias_patch_cycle_closure_325p_summary.json'}")
            print(f"qa_fail_count: {summary.get('qa_fail_count', '')}")
            print(f"decision: {summary.get('decision', '')}")
            return 0

    inputs = load_alias_patch_cycle_closure_325p_inputs(
        post_patch_regression_dir=post_patch_regression_dir,
        official_patch_application_dir=official_patch_application_dir,
        previous_cycle_closure_dir=previous_cycle_closure_dir,
        remaining_burden_dir=remaining_burden_planning_dir,
    )
    artifacts = build_alias_patch_cycle_closure_325p(
        summary_325o=inputs["summary_325o"],
        qa_325o=inputs["qa_325o"],
        no_apply_325o=inputs["no_apply_325o"],
        summary_325n=inputs["summary_325n"],
        summary_324n=inputs["summary_324n"],
        summary_323o=inputs["summary_323o"],
        summary_323p=inputs["summary_323p"],
        stage_summaries=inputs["stage_summaries"],
        output_dir=output_dir,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "alias_patch_cycle_closure_325p_summary.json",
        "qa_json": output_dir / "alias_patch_cycle_closure_325p_qa.json",
        "closure_json": output_dir / "alias_patch_cycle_closure_325p_closure.json",
        "summary_xlsx": output_dir / "alias_patch_cycle_closure_325p_summary.xlsx",
        "stage_timeline_xlsx": output_dir / "alias_patch_cycle_closure_325p_stage_timeline.xlsx",
        "report_md": output_dir / "alias_patch_cycle_closure_325p_report.md",
        "no_apply_proof_json": output_dir / "alias_patch_cycle_closure_325p_no_apply_proof.json",
    }
    summary = artifacts["summary"]
    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "funnel_counts": artifacts["funnel_df"],
        "cycle_summary": artifacts["cycle_summary_df"],
        "stage_timeline": artifacts["stage_timeline_df"],
        "remaining_burden": artifacts["remaining_burden_df"],
        "residual_risks": artifacts["residual_risks_df"],
        "next_cycle_recommendations": artifacts["recommendations_df"],
        "official_asset_proof": artifacts["official_asset_proof_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["closure_json"], artifacts["closure_json"])
    write_json(output_files["no_apply_proof_json"], artifacts["no_apply_proof_json"])
    write_excel(output_files["summary_xlsx"], sheets, SUMMARY_SHEET_ORDER)
    write_excel(output_files["stage_timeline_xlsx"], {"stage_timeline": artifacts["stage_timeline_df"]}, ["stage_timeline"])
    output_files["report_md"].write_text(
        alias_patch_cycle_closure_325p_markdown(summary),
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
    write_excel(output_files["summary_xlsx"], sheets, SUMMARY_SHEET_ORDER)
    output_files["report_md"].write_text(
        alias_patch_cycle_closure_325p_markdown(summary),
        encoding="utf-8",
    )

    print(f"alias_patch_cycle_closure_325p_summary_json: {output_files['summary_json']}")
    print(f"alias_patch_cycle_closure_325p_qa_json: {output_files['qa_json']}")
    print(f"alias_patch_cycle_closure_325p_closure_json: {output_files['closure_json']}")
    print(f"alias_patch_cycle_closure_325p_summary_xlsx: {output_files['summary_xlsx']}")
    print(f"alias_patch_cycle_closure_325p_stage_timeline_xlsx: {output_files['stage_timeline_xlsx']}")
    print(f"alias_patch_cycle_closure_325p_report_md: {output_files['report_md']}")
    print(f"alias_patch_cycle_closure_325p_no_apply_proof_json: {output_files['no_apply_proof_json']}")
    for key in [
        "official_alias_rule_count_325",
        "trusted_gain_325",
        "review_reduction_325",
        "out_of_scope_or_rejected_gain_325",
        "affected_candidate_count_325",
        "cumulative_official_rule_count_after_325",
        "cumulative_trusted_gain_after_325",
        "cumulative_review_reduction_after_325",
        "primary_next_direction",
        "secondary_next_direction",
        "no_official_asset_modification_during_325p",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
