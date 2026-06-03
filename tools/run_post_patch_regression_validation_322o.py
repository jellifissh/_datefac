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

from datefac.semantic.post_patch_regression_validation import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PATCH_APPLICATION_DIR,
    DEFAULT_REFERENCE_322J_DIR,
    DEFAULT_TRUST_SPLIT_DIR,
    EXPECTED_322O_NOT_READY_DECISION,
    build_post_patch_regression_validation,
    load_post_patch_regression_validation_inputs,
)
from datefac.semantic.post_patch_regression_validation_report import (
    BEFORE_AFTER_SHEET_ORDER,
    CORE_FALSE_EXCLUSION_SHEET_ORDER,
    post_patch_regression_validation_decision_markdown,
    post_patch_regression_validation_report_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322O",
        "output_dir": str(output_dir),
        "official_rule_visibility_total": 0,
        "alias_rules_visible": 0,
        "scope_rules_visible": 0,
        "trusted_total_before_322o": 0,
        "trusted_total_after_322o": 0,
        "review_required_total_before_322o": 0,
        "review_required_total_after_322o": 0,
        "rejected_total_before_322o": 0,
        "rejected_total_after_322o": 0,
        "trusted_gain_322o": 0,
        "review_reduction_322o": 0,
        "out_of_scope_or_rejected_gain_322o": 0,
        "affected_candidate_count": 0,
        "selected_core_trusted_rate_before_322o": 0,
        "selected_core_trusted_rate_after_322o": 0,
        "remaining_unknown_metric_candidate_count": 0,
        "remaining_unit_unknown_candidate_count": 0,
        "remaining_manual_review_count": 0,
        "duplicate_count": 0,
        "conflict_count": 0,
        "core_false_exclusion_count": 0,
        "rollback_artifact_all_present": False,
        "no_official_asset_modification_during_322o": True,
        "no_parser_run_confirmation": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_322O_NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    decision_json = {
        "decision": summary["decision"],
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "rollback_recommendation": "Missing required inputs. Review upstream stage outputs before any rollback decision.",
    }

    before_after_sheets = {
        "summary": pd.DataFrame([summary]),
        "metric_comparison": pd.DataFrame(),
        "rule_application_alignment": pd.DataFrame(),
        "official_rule_visibility": pd.DataFrame(),
        "trusted_after_preview_322o": pd.DataFrame(),
        "review_after_preview_322o": pd.DataFrame(),
        "rejected_after_preview_322o": pd.DataFrame(),
        "rollback_artifacts": pd.DataFrame(),
        "qa_summary": pd.DataFrame([{"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": code, "decision": summary["decision"]}]),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input directory is missing."}]),
    }
    core_sheets = {
        "summary": pd.DataFrame([summary]),
        "core_false_exclusion_check": pd.DataFrame(),
        "candidate_before_after_diff_322o": pd.DataFrame(),
        "impact_by_rule_322o": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }

    summary_json_path = output_dir / "post_patch_regression_validation_322o_summary.json"
    qa_json_path = output_dir / "post_patch_regression_validation_322o_qa.json"
    visibility_json_path = output_dir / "post_patch_regression_validation_322o_official_rule_visibility.json"
    before_after_xlsx_path = output_dir / "post_patch_regression_validation_322o_before_after_comparison.xlsx"
    core_xlsx_path = output_dir / "post_patch_regression_validation_322o_core_false_exclusion_check.xlsx"
    report_md_path = output_dir / "post_patch_regression_validation_322o_regression_notes.md"
    decision_md_path = output_dir / "post_patch_regression_validation_322o_decision.md"

    write_json(summary_json_path, summary)
    write_json(qa_json_path, qa_json)
    write_json(visibility_json_path, {"official_rule_visibility_total": 0, "alias_rules_visible": 0, "scope_rules_visible": 0})
    write_excel(before_after_xlsx_path, before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    write_excel(core_xlsx_path, core_sheets, CORE_FALSE_EXCLUSION_SHEET_ORDER)
    report_md_path.write_text(post_patch_regression_validation_report_markdown(summary), encoding="utf-8")
    decision_md_path.write_text(post_patch_regression_validation_decision_markdown(decision_json), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322O post-patch regression validation.")
    parser.add_argument("--patch-application-dir", default=str(DEFAULT_PATCH_APPLICATION_DIR))
    parser.add_argument("--trust-split-dir", default=str(DEFAULT_TRUST_SPLIT_DIR))
    parser.add_argument("--reference-322j-dir", default=str(DEFAULT_REFERENCE_322J_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    patch_application_dir = Path(args.patch_application_dir)
    trust_split_dir = Path(args.trust_split_dir)
    reference_322j_dir = Path(args.reference_322j_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (patch_application_dir, "BLOCKED_MISSING_322N_PATCH_APPLICATION_DIR"),
        (trust_split_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR"),
        (reference_322j_dir, "BLOCKED_MISSING_322J_REFERENCE_DIR"),
    ]
    for path, code in required_dirs:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"post_patch_regression_validation_322o_summary_json: {output_dir / 'post_patch_regression_validation_322o_summary.json'}")
            return 0

    inputs = load_post_patch_regression_validation_inputs(
        patch_application_dir=patch_application_dir,
        trust_split_dir=trust_split_dir,
        reference_322j_dir=reference_322j_dir,
    )
    artifacts = build_post_patch_regression_validation(
        patch_summary=inputs["patch_summary"],
        patch_qa=inputs["patch_qa"],
        patch_application_log_df=inputs["patch_application_log_df"],
        reference_322j_summary=inputs["reference_322j_summary"],
        reference_322j_qa=inputs["reference_322j_qa"],
        trust_summary=inputs["trust_summary"],
        selected_candidates_df=inputs["selected_candidates_df"],
        output_dir=output_dir,
    )

    summary = artifacts["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json_path = output_dir / "post_patch_regression_validation_322o_summary.json"
    qa_json_path = output_dir / "post_patch_regression_validation_322o_qa.json"
    visibility_json_path = output_dir / "post_patch_regression_validation_322o_official_rule_visibility.json"
    before_after_xlsx_path = output_dir / "post_patch_regression_validation_322o_before_after_comparison.xlsx"
    core_xlsx_path = output_dir / "post_patch_regression_validation_322o_core_false_exclusion_check.xlsx"
    report_md_path = output_dir / "post_patch_regression_validation_322o_regression_notes.md"
    decision_md_path = output_dir / "post_patch_regression_validation_322o_decision.md"

    before_after_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "metric_comparison": artifacts["metric_comparison_df"],
        "rule_application_alignment": artifacts["application_alignment_df"],
        "official_rule_visibility": artifacts["visibility_df"],
        "trusted_after_preview_322o": artifacts["trusted_after_df"],
        "review_after_preview_322o": artifacts["review_after_df"],
        "rejected_after_preview_322o": artifacts["rejected_after_df"],
        "rollback_artifacts": artifacts["rollback_artifact_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    core_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "core_false_exclusion_check": artifacts["core_false_exclusion_df"],
        "candidate_before_after_diff_322o": artifacts["diff_df"],
        "impact_by_rule_322o": artifacts["impact_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(visibility_json_path, artifacts["official_rule_visibility_json"])
    write_excel(before_after_xlsx_path, before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    write_excel(core_xlsx_path, core_sheets, CORE_FALSE_EXCLUSION_SHEET_ORDER)
    report_md_path.write_text(post_patch_regression_validation_report_markdown(summary), encoding="utf-8")
    decision_md_path.write_text(post_patch_regression_validation_decision_markdown(artifacts["decision_json"]), encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            summary_json_path,
            qa_json_path,
            visibility_json_path,
            before_after_xlsx_path,
            core_xlsx_path,
            report_md_path,
            decision_md_path,
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
    summary["blocking_reasons"] = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    summary["decision"] = (
        "POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE"
        if summary["qa_fail_count"] == 0
        else EXPECTED_322O_NOT_READY_DECISION
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
    core_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    core_sheets["qa_checks"] = qa_df

    write_json(summary_json_path, summary)
    write_json(
        qa_json_path,
        {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    write_excel(before_after_xlsx_path, before_after_sheets, BEFORE_AFTER_SHEET_ORDER)
    write_excel(core_xlsx_path, core_sheets, CORE_FALSE_EXCLUSION_SHEET_ORDER)
    report_md_path.write_text(post_patch_regression_validation_report_markdown(summary), encoding="utf-8")
    decision_md_path.write_text(
        post_patch_regression_validation_decision_markdown(
            {
                "decision": summary["decision"],
                "qa_fail_count": summary["qa_fail_count"],
                "blocking_reasons": summary["blocking_reasons"],
                "rollback_recommendation": (
                    "Use 322N rollback artifacts for review because blocking regression issues were detected."
                    if summary["qa_fail_count"] > 0
                    else "No rollback recommended. Official patch cycle can be closed."
                ),
            }
        ),
        encoding="utf-8",
    )

    print(f"post_patch_regression_validation_322o_summary_json: {summary_json_path}")
    print(f"post_patch_regression_validation_322o_qa_json: {qa_json_path}")
    print(f"post_patch_regression_validation_322o_official_rule_visibility_json: {visibility_json_path}")
    print(f"post_patch_regression_validation_322o_before_after_comparison_xlsx: {before_after_xlsx_path}")
    print(f"post_patch_regression_validation_322o_core_false_exclusion_check_xlsx: {core_xlsx_path}")
    print(f"post_patch_regression_validation_322o_regression_notes_md: {report_md_path}")
    print(f"post_patch_regression_validation_322o_decision_md: {decision_md_path}")
    for key in [
        "official_rule_visibility_total",
        "alias_rules_visible",
        "scope_rules_visible",
        "trusted_gain_322o",
        "review_reduction_322o",
        "out_of_scope_or_rejected_gain_322o",
        "affected_candidate_count",
        "selected_core_trusted_rate_after_322o",
        "duplicate_count",
        "conflict_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
