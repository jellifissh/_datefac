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

from datefac.semantic.official_patch_dry_run import (
    EXPECTED_322L_DECISION,
    build_official_patch_dry_run,
    load_official_patch_dry_run_inputs,
)
from datefac.semantic.official_patch_dry_run_report import (
    official_patch_dry_run_report_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322L",
        "output_dir": str(output_dir),
        "controlled_proposal_readiness_passed": False,
        "controlled_proposal_source_decision": "",
        "controlled_proposal_source_qa_fail_count": 1,
        "total_patch_operation_count": 0,
        "alias_patch_operation_count": 0,
        "scope_patch_operation_count": 0,
        "unit_patch_operation_count": 0,
        "rejected_noise_patch_operation_count": 0,
        "expected_affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "no_apply_confirmed": True,
        "official_files_not_modified_confirmed": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "official_patch_dry_run_decision": "OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_NOT_READY",
    }
    sheets = {
        "summary": pd.DataFrame([summary]),
        "patch_diff_preview": pd.DataFrame(),
        "target_inventory": pd.DataFrame(),
        "qa_summary": pd.DataFrame([{"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": code, "decision": summary["official_patch_dry_run_decision"]}]),
        "no_apply_proof": pd.DataFrame([{"files_read_count": 0, "files_written_count": 0, "target_official_files_inspected_count": 0, "target_official_files_not_modified_count": 0, "output_only_write_confirmation": True, "decision": "dry_run_only_no_apply"}]),
        "rollback_plan": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input is missing."}]),
    }
    write_excel(output_dir / "official_semantic_patch_dry_run_322l_patch_diff_preview.xlsx", sheets)
    write_json(output_dir / "official_semantic_patch_dry_run_322l_summary.json", summary)
    write_json(output_dir / "official_semantic_patch_dry_run_322l_patch_diff_preview.json", {"patch_operations": []})
    write_json(output_dir / "official_semantic_patch_dry_run_322l_target_files.json", {"target_official_files_inspected": [], "target_rule_groups": []})
    write_json(output_dir / "official_semantic_patch_dry_run_322l_qa.json", {"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": [code], "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}]})
    write_json(output_dir / "official_semantic_patch_dry_run_322l_no_apply_proof.json", {"files_read": [], "files_written": [], "target_official_files_inspected": [], "target_official_files_not_modified": [], "output_only_write_confirmation": True, "decision": "dry_run_only_no_apply"})
    (output_dir / "official_semantic_patch_dry_run_322l_patch_diff_preview.md").write_text(official_patch_dry_run_report_markdown(summary), encoding="utf-8")
    (output_dir / "official_semantic_patch_dry_run_322l_rollback_plan.md").write_text("# Official Semantic Patch Dry Run 322L Rollback Plan\n\nBlocked input.\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322L official semantic patch dry run.")
    parser.add_argument("--controlled-proposal-dir", default=r"D:\_datefac\output\controlled_official_semantic_patch_proposal_322k")
    parser.add_argument("--sandbox-application-dir", default=r"D:\_datefac\output\official_semantic_rule_candidates_322j")
    parser.add_argument("--official-rule-candidate-dir", default=r"D:\_datefac\output\official_semantic_rule_candidates_322i")
    parser.add_argument("--output-dir", default=r"D:\_datefac\output\official_semantic_patch_dry_run_322l")
    args = parser.parse_args()

    controlled_proposal_dir = Path(args.controlled_proposal_dir)
    sandbox_application_dir = Path(args.sandbox_application_dir)
    official_rule_candidate_dir = Path(args.official_rule_candidate_dir)
    output_dir = Path(args.output_dir)

    if not controlled_proposal_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322K_CONTROLLED_PROPOSAL_DIR")
        print(f"official_patch_dry_run_322l_summary_json: {output_dir / 'official_semantic_patch_dry_run_322l_summary.json'}")
        return 0
    if not sandbox_application_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322J_SANDBOX_APPLICATION_DIR")
        print(f"official_patch_dry_run_322l_summary_json: {output_dir / 'official_semantic_patch_dry_run_322l_summary.json'}")
        return 0
    if not official_rule_candidate_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322I_OFFICIAL_RULE_CANDIDATE_DIR")
        print(f"official_patch_dry_run_322l_summary_json: {output_dir / 'official_semantic_patch_dry_run_322l_summary.json'}")
        return 0

    inputs = load_official_patch_dry_run_inputs(
        controlled_proposal_dir=controlled_proposal_dir,
        sandbox_application_dir=sandbox_application_dir,
        official_rule_candidate_dir=official_rule_candidate_dir,
    )
    artifacts = build_official_patch_dry_run(
        controlled_summary=inputs["controlled_summary"],
        controlled_qa=inputs["controlled_qa"],
        alias_proposals=inputs["alias_proposals"],
        scope_proposals=inputs["scope_proposals"],
        sandbox_summary=inputs["sandbox_summary"],
        official_candidate_summary=inputs["official_candidate_summary"],
        formal_scope_rules=inputs["formal_scope_rules"],
        official_override_sheets=inputs["official_override_sheets"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_json_path = output_dir / "official_semantic_patch_dry_run_322l_summary.json"
    diff_json_path = output_dir / "official_semantic_patch_dry_run_322l_patch_diff_preview.json"
    diff_md_path = output_dir / "official_semantic_patch_dry_run_322l_patch_diff_preview.md"
    diff_xlsx_path = output_dir / "official_semantic_patch_dry_run_322l_patch_diff_preview.xlsx"
    target_files_json_path = output_dir / "official_semantic_patch_dry_run_322l_target_files.json"
    qa_json_path = output_dir / "official_semantic_patch_dry_run_322l_qa.json"
    no_apply_json_path = output_dir / "official_semantic_patch_dry_run_322l_no_apply_proof.json"
    rollback_md_path = output_dir / "official_semantic_patch_dry_run_322l_rollback_plan.md"

    sheets = {
        "summary": pd.DataFrame([summary]),
        "patch_diff_preview": artifacts["patch_diff_preview_df"],
        "target_inventory": artifacts["target_inventory_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "no_apply_proof": artifacts["no_apply_proof_df"],
        "rollback_plan": artifacts["rollback_plan_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_excel(diff_xlsx_path, sheets)
    write_json(summary_json_path, summary)
    write_json(diff_json_path, artifacts["patch_diff_preview_json"])
    write_json(target_files_json_path, artifacts["target_files_json"])
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(no_apply_json_path, artifacts["no_apply_proof_json"])
    diff_md_path.write_text(official_patch_dry_run_report_markdown(summary), encoding="utf-8")
    rollback_md_path.write_text(artifacts["rollback_plan_markdown"], encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            summary_json_path,
            diff_json_path,
            diff_md_path,
            diff_xlsx_path,
            target_files_json_path,
            qa_json_path,
            no_apply_json_path,
            rollback_md_path,
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
    summary["official_patch_dry_run_decision"] = EXPECTED_322L_DECISION if summary["qa_fail_count"] == 0 else "OFFICIAL_SEMANTIC_PATCH_DRY_RUN_322L_NOT_READY"

    sheets["summary"] = pd.DataFrame([summary])
    sheets["qa_summary"] = pd.DataFrame(
        [
            {
                "qa_pass_count": summary["qa_pass_count"],
                "qa_warn_count": summary["qa_warn_count"],
                "qa_fail_count": summary["qa_fail_count"],
                "blocking_reasons": " | ".join(summary["blocking_reasons"]),
                "decision": summary["official_patch_dry_run_decision"],
            }
        ]
    )
    sheets["qa_checks"] = qa_df
    write_excel(diff_xlsx_path, sheets)
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
    diff_md_path.write_text(official_patch_dry_run_report_markdown(summary), encoding="utf-8")

    print(f"official_patch_dry_run_322l_summary_json: {summary_json_path}")
    print(f"official_patch_dry_run_322l_patch_diff_preview_json: {diff_json_path}")
    print(f"official_patch_dry_run_322l_patch_diff_preview_md: {diff_md_path}")
    print(f"official_patch_dry_run_322l_patch_diff_preview_xlsx: {diff_xlsx_path}")
    print(f"official_patch_dry_run_322l_target_files_json: {target_files_json_path}")
    print(f"official_patch_dry_run_322l_qa_json: {qa_json_path}")
    print(f"official_patch_dry_run_322l_no_apply_proof_json: {no_apply_json_path}")
    print(f"official_patch_dry_run_322l_rollback_plan_md: {rollback_md_path}")
    for key in [
        "total_patch_operation_count",
        "alias_patch_operation_count",
        "scope_patch_operation_count",
        "unit_patch_operation_count",
        "rejected_noise_patch_operation_count",
        "expected_affected_candidate_count",
        "expected_trusted_gain",
        "expected_review_reduction",
        "expected_out_of_scope_or_rejected_gain",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "official_patch_dry_run_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
