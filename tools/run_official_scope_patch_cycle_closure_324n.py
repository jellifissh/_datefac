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

from datefac.semantic.official_scope_patch_cycle_closure_324n import (  # noqa: E402
    DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_PATCH_REGRESSION_DIR,
    DEFAULT_PREVIOUS_CYCLE_CLOSURE_DIR,
    DEFAULT_REMAINING_BURDEN_DIR,
    NOT_READY_DECISION,
    build_official_scope_patch_cycle_closure_324n,
    load_official_scope_patch_cycle_closure_324n_inputs,
)
from datefac.semantic.official_scope_patch_cycle_closure_324n_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    official_scope_patch_cycle_closure_324n_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324N",
        "output_dir": str(output_dir),
        "official_rule_count_324": 0,
        "scope_rule_count_324": 0,
        "alias_rule_count_324": 0,
        "trusted_gain_324": 0,
        "review_reduction_324": 0,
        "out_of_scope_or_rejected_gain_324": 0,
        "affected_candidate_count_324": 0,
        "core_false_exclusion_count_324": 0,
        "current_duplicate_count": 0,
        "new_duplicate_delta_count_324": 0,
        "conflict_count_324": 0,
        "combined_official_rule_count": 0,
        "combined_trusted_gain": 0,
        "combined_review_reduction": 0,
        "combined_out_of_scope_or_rejected_gain": 0,
        "remaining_burden_status": "blocked",
        "warning_status": "",
        "recommended_next_cycle_direction_primary": "",
        "recommended_next_cycle_direction_secondary": "",
        "no_official_asset_modification_during_324n": True,
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
    write_json(output_dir / "official_scope_patch_cycle_closure_324n_summary.json", summary)
    write_json(output_dir / "official_scope_patch_cycle_closure_324n_qa.json", qa_json)
    write_json(
        output_dir / "official_scope_patch_cycle_closure_324n_closure.json",
        {"cycle_324": {}, "previous_combined": {}, "combined_through_324": {}, "next_cycle_recommendations": []},
    )
    write_json(
        output_dir / "official_scope_patch_cycle_closure_324n_no_apply_proof.json",
        {"stage": "324N", "official_assets_written": [], "no_official_asset_modification_during_324n": True},
    )
    empty_sheets = {
        "summary": pd.DataFrame([summary]),
        "cycle_summary": pd.DataFrame(),
        "stage_timeline": pd.DataFrame(),
        "remaining_burden": pd.DataFrame(),
        "warnings": pd.DataFrame(),
        "next_cycle_recommendations": pd.DataFrame(),
        "official_asset_proof": pd.DataFrame(),
        "qa_summary": pd.DataFrame(
            [{"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": code, "decision": NOT_READY_DECISION}]
        ),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": code}]),
    }
    write_excel(output_dir / "official_scope_patch_cycle_closure_324n_summary.xlsx", empty_sheets, SUMMARY_SHEET_ORDER)
    write_excel(output_dir / "official_scope_patch_cycle_closure_324n_stage_timeline.xlsx", {"stage_timeline": pd.DataFrame()}, ["stage_timeline"])
    (output_dir / "official_scope_patch_cycle_closure_324n_report.md").write_text(
        official_scope_patch_cycle_closure_324n_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 324N official scope patch cycle closure.")
    parser.add_argument("--post-patch-regression-dir", default=str(DEFAULT_POST_PATCH_REGRESSION_DIR))
    parser.add_argument("--official-patch-application-dir", default=str(DEFAULT_OFFICIAL_PATCH_APPLICATION_DIR))
    parser.add_argument("--previous-cycle-closure-dir", default=str(DEFAULT_PREVIOUS_CYCLE_CLOSURE_DIR))
    parser.add_argument("--remaining-burden-dir", default=str(DEFAULT_REMAINING_BURDEN_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    post_patch_regression_dir = Path(args.post_patch_regression_dir)
    official_patch_application_dir = Path(args.official_patch_application_dir)
    previous_cycle_closure_dir = Path(args.previous_cycle_closure_dir)
    remaining_burden_dir = Path(args.remaining_burden_dir)
    output_dir = Path(args.output_dir)

    for path, code in [
        (post_patch_regression_dir / "post_patch_regression_validation_324m_summary.json", "BLOCKED_MISSING_324M_SUMMARY"),
        (official_patch_application_dir / "official_patch_application_324l_summary.json", "BLOCKED_MISSING_324L_SUMMARY"),
        (previous_cycle_closure_dir / "official_semantic_patch_cycle_closure_323o_summary.json", "BLOCKED_MISSING_323O_SUMMARY"),
        (remaining_burden_dir / "remaining_burden_planning_323p_summary.json", "BLOCKED_MISSING_323P_SUMMARY"),
    ]:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"official_scope_patch_cycle_closure_324n_summary_json: {output_dir / 'official_scope_patch_cycle_closure_324n_summary.json'}")
            print(f"qa_fail_count: {summary.get('qa_fail_count', '')}")
            print(f"decision: {summary.get('decision', '')}")
            return 0

    inputs = load_official_scope_patch_cycle_closure_324n_inputs(
        post_patch_regression_dir=post_patch_regression_dir,
        official_patch_application_dir=official_patch_application_dir,
        previous_cycle_closure_dir=previous_cycle_closure_dir,
        remaining_burden_dir=remaining_burden_dir,
    )
    artifacts = build_official_scope_patch_cycle_closure_324n(
        summary_324m=inputs["summary_324m"],
        qa_324m=inputs["qa_324m"],
        no_apply_324m=inputs["no_apply_324m"],
        summary_324l=inputs["summary_324l"],
        summary_323o=inputs["summary_323o"],
        summary_323p=inputs["summary_323p"],
        stage_summaries=inputs["stage_summaries"],
        output_dir=output_dir,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "official_scope_patch_cycle_closure_324n_summary.json",
        "qa_json": output_dir / "official_scope_patch_cycle_closure_324n_qa.json",
        "closure_json": output_dir / "official_scope_patch_cycle_closure_324n_closure.json",
        "summary_xlsx": output_dir / "official_scope_patch_cycle_closure_324n_summary.xlsx",
        "stage_timeline_xlsx": output_dir / "official_scope_patch_cycle_closure_324n_stage_timeline.xlsx",
        "report_md": output_dir / "official_scope_patch_cycle_closure_324n_report.md",
        "no_apply_proof_json": output_dir / "official_scope_patch_cycle_closure_324n_no_apply_proof.json",
    }
    summary = artifacts["summary"]
    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "cycle_summary": artifacts["cycle_summary_df"],
        "stage_timeline": artifacts["stage_timeline_df"],
        "remaining_burden": artifacts["remaining_burden_df"],
        "warnings": artifacts["warnings_df"],
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
        official_scope_patch_cycle_closure_324n_markdown(summary),
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
        official_scope_patch_cycle_closure_324n_markdown(summary),
        encoding="utf-8",
    )

    print(f"official_scope_patch_cycle_closure_324n_summary_json: {output_files['summary_json']}")
    print(f"official_scope_patch_cycle_closure_324n_qa_json: {output_files['qa_json']}")
    print(f"official_scope_patch_cycle_closure_324n_closure_json: {output_files['closure_json']}")
    print(f"official_scope_patch_cycle_closure_324n_summary_xlsx: {output_files['summary_xlsx']}")
    print(f"official_scope_patch_cycle_closure_324n_stage_timeline_xlsx: {output_files['stage_timeline_xlsx']}")
    print(f"official_scope_patch_cycle_closure_324n_report_md: {output_files['report_md']}")
    print(f"official_scope_patch_cycle_closure_324n_no_apply_proof_json: {output_files['no_apply_proof_json']}")
    for key in [
        "official_rule_count_324",
        "scope_rule_count_324",
        "alias_rule_count_324",
        "trusted_gain_324",
        "review_reduction_324",
        "out_of_scope_or_rejected_gain_324",
        "affected_candidate_count_324",
        "combined_official_rule_count",
        "combined_trusted_gain",
        "combined_review_reduction",
        "warning_status",
        "remaining_burden_status",
        "recommended_next_cycle_direction_primary",
        "recommended_next_cycle_direction_secondary",
        "no_official_asset_modification_during_324n",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
