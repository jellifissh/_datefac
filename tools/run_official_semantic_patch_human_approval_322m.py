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

from datefac.semantic.official_patch_human_approval import (
    DEFAULT_OUTPUT_DIR,
    EXPECTED_322M_PREPARE_DECISION,
    EXPECTED_322M_PREPARE_NOT_READY,
    EXPECTED_322M_REVIEWED_DECISION,
    EXPECTED_322M_REVIEWED_NOT_READY,
    build_official_patch_human_approval_prepare,
    build_official_patch_human_approval_validate_reviewed,
    load_official_patch_human_approval_inputs,
)
from datefac.semantic.official_patch_human_approval_report import (
    official_patch_human_approval_report_markdown,
    write_excel,
    write_json,
)


def _blocked_prepare_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322M",
        "mode": "prepare",
        "output_dir": str(output_dir),
        "dry_run_readiness_passed": False,
        "dry_run_source_decision": "",
        "dry_run_source_qa_fail_count": 1,
        "approval_record_count": 0,
        "alias_approval_count": 0,
        "scope_approval_count": 0,
        "unit_approval_count": 0,
        "rejected_noise_approval_count": 0,
        "expected_affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "decision_distribution": {},
        "all_decisions_pending_human_approval": False,
        "official_files_not_modified_confirmed": True,
        "approval_package_only_no_apply_confirmed": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "official_patch_human_approval_decision": EXPECTED_322M_PREPARE_NOT_READY,
    }
    sheets = {
        "approval_summary": pd.DataFrame([summary]),
        "alias_approvals": pd.DataFrame(),
        "scope_approvals": pd.DataFrame(),
        "all_patch_operations": pd.DataFrame(),
        "qa": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "review_instructions": pd.DataFrame([{"section": "blocked_input", "instruction": "Required input is missing."}]),
        "no_apply_proof": pd.DataFrame(
            [
                {
                    "files_read_count": 0,
                    "files_written_count": 0,
                    "official_target_files_inspected_count": 0,
                    "official_target_files_not_modified_count": 0,
                    "output_only_write_confirmation": True,
                    "decision": "approval_package_only_no_apply",
                }
            ]
        ),
    }
    workbook_path = output_dir / "official_semantic_patch_human_approval_322m_approval_workbook.xlsx"
    summary_json_path = output_dir / "official_semantic_patch_human_approval_322m_summary.json"
    template_json_path = output_dir / "official_semantic_patch_human_approval_322m_approval_template.json"
    qa_json_path = output_dir / "official_semantic_patch_human_approval_322m_qa.json"
    no_apply_path = output_dir / "official_semantic_patch_human_approval_322m_no_apply_proof.json"
    instructions_path = output_dir / "official_semantic_patch_human_approval_322m_review_instructions.md"
    write_excel(workbook_path, sheets, mode="prepare")
    write_json(summary_json_path, summary)
    write_json(template_json_path, {"stage": "322M", "mode": "prepare", "approval_records": []})
    write_json(qa_json_path, {"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": [code], "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}]})
    write_json(no_apply_path, {"files_read": [], "files_written": [], "official_target_files_inspected": [], "official_target_files_not_modified": [], "output_only_write_confirmation": True, "decision": "approval_package_only_no_apply"})
    instructions_path.write_text(official_patch_human_approval_report_markdown(summary), encoding="utf-8")
    return summary


def _blocked_reviewed_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322M",
        "mode": "validate-reviewed",
        "output_dir": str(output_dir),
        "reviewed_workbook": "",
        "approval_record_count": 0,
        "approved_patch_count": 0,
        "rejected_patch_count": 0,
        "needs_more_review_count": 0,
        "decision_distribution": {},
        "official_files_not_modified_confirmed": True,
        "approval_package_only_no_apply_confirmed": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "official_patch_human_approval_decision": EXPECTED_322M_REVIEWED_NOT_READY,
    }
    sheets = {
        "reviewed_summary": pd.DataFrame([summary]),
        "approved_patch_operations": pd.DataFrame(),
        "rejected_patch_operations": pd.DataFrame(),
        "needs_more_review_patch_operations": pd.DataFrame(),
        "all_reviewed_patch_operations": pd.DataFrame(),
        "reviewed_qa": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }
    workbook_path = output_dir / "official_semantic_patch_human_approval_322m_reviewed_workbook.xlsx"
    summary_json_path = output_dir / "official_semantic_patch_human_approval_322m_reviewed_summary.json"
    plan_json_path = output_dir / "official_semantic_patch_human_approval_322m_final_approved_patch_plan.json"
    qa_json_path = output_dir / "official_semantic_patch_human_approval_322m_reviewed_qa.json"
    write_excel(workbook_path, sheets, mode="validate-reviewed")
    write_json(summary_json_path, summary)
    write_json(plan_json_path, {"stage": "322M", "mode": "validate-reviewed", "approved_patch_operations": [], "decision": EXPECTED_322M_REVIEWED_NOT_READY})
    write_json(qa_json_path, {"qa_pass_count": 0, "qa_warn_count": 0, "qa_fail_count": 1, "blocking_reasons": [code], "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}]})
    return summary


def _write_prepare_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> Dict[str, Path]:
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = output_dir / "official_semantic_patch_human_approval_322m_approval_workbook.xlsx"
    summary_json_path = output_dir / "official_semantic_patch_human_approval_322m_summary.json"
    template_json_path = output_dir / "official_semantic_patch_human_approval_322m_approval_template.json"
    qa_json_path = output_dir / "official_semantic_patch_human_approval_322m_qa.json"
    no_apply_path = output_dir / "official_semantic_patch_human_approval_322m_no_apply_proof.json"
    instructions_path = output_dir / "official_semantic_patch_human_approval_322m_review_instructions.md"

    sheets = {
        "approval_summary": artifacts["approval_summary_df"],
        "alias_approvals": artifacts["alias_approvals_df"],
        "scope_approvals": artifacts["scope_approvals_df"],
        "all_patch_operations": artifacts["all_patch_operations_df"],
        "qa": artifacts["qa_checks_df"],
        "review_instructions": artifacts["review_instructions_df"],
        "no_apply_proof": artifacts["no_apply_proof_df"],
    }
    write_excel(workbook_path, sheets, mode="prepare")
    write_json(summary_json_path, summary)
    write_json(template_json_path, artifacts["approval_template_json"])
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(no_apply_path, artifacts["no_apply_proof_json"])
    instructions_path.write_text(artifacts["review_instructions_markdown"], encoding="utf-8")

    return {
        "workbook_path": workbook_path,
        "summary_json_path": summary_json_path,
        "template_json_path": template_json_path,
        "qa_json_path": qa_json_path,
        "no_apply_path": no_apply_path,
        "instructions_path": instructions_path,
    }


def _write_reviewed_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> Dict[str, Path]:
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = output_dir / "official_semantic_patch_human_approval_322m_reviewed_workbook.xlsx"
    summary_json_path = output_dir / "official_semantic_patch_human_approval_322m_reviewed_summary.json"
    plan_json_path = output_dir / "official_semantic_patch_human_approval_322m_final_approved_patch_plan.json"
    qa_json_path = output_dir / "official_semantic_patch_human_approval_322m_reviewed_qa.json"

    sheets = {
        "reviewed_summary": pd.DataFrame([summary]),
        "approved_patch_operations": artifacts["approved_df"],
        "rejected_patch_operations": artifacts["rejected_df"],
        "needs_more_review_patch_operations": artifacts["needs_more_review_df"],
        "all_reviewed_patch_operations": artifacts["all_reviewed_df"],
        "reviewed_qa": pd.DataFrame(artifacts["qa_json"]["checks"]).fillna(""),
    }
    write_excel(workbook_path, sheets, mode="validate-reviewed")
    write_json(summary_json_path, summary)
    write_json(plan_json_path, artifacts["final_approved_patch_plan_json"])
    write_json(qa_json_path, artifacts["qa_json"])

    return {
        "workbook_path": workbook_path,
        "summary_json_path": summary_json_path,
        "plan_json_path": plan_json_path,
        "qa_json_path": qa_json_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322M official semantic patch human approval package.")
    parser.add_argument("--mode", choices=["prepare", "validate-reviewed"], default="prepare")
    parser.add_argument("--dry-run-dir", default=r"D:\_datefac\output\official_semantic_patch_dry_run_322l")
    parser.add_argument("--controlled-proposal-dir", default=r"D:\_datefac\output\controlled_official_semantic_patch_proposal_322k")
    parser.add_argument("--sandbox-application-dir", default=r"D:\_datefac\output\official_semantic_rule_candidates_322j")
    parser.add_argument("--official-rule-candidate-dir", default=r"D:\_datefac\output\official_semantic_rule_candidates_322i")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--reviewed-approval-workbook", default="")
    args = parser.parse_args()

    dry_run_dir = Path(args.dry_run_dir)
    controlled_proposal_dir = Path(args.controlled_proposal_dir)
    sandbox_application_dir = Path(args.sandbox_application_dir)
    official_rule_candidate_dir = Path(args.official_rule_candidate_dir)
    output_dir = Path(args.output_dir)

    if args.mode == "prepare":
        if not dry_run_dir.exists():
            _blocked_prepare_result(output_dir, "BLOCKED_MISSING_322L_DRY_RUN_DIR")
            print(f"official_patch_human_approval_322m_summary_json: {output_dir / 'official_semantic_patch_human_approval_322m_summary.json'}")
            return 0

        inputs = load_official_patch_human_approval_inputs(
            dry_run_dir=dry_run_dir,
            controlled_proposal_dir=controlled_proposal_dir if controlled_proposal_dir.exists() else None,
            sandbox_application_dir=sandbox_application_dir if sandbox_application_dir.exists() else None,
            official_rule_candidate_dir=official_rule_candidate_dir if official_rule_candidate_dir.exists() else None,
        )
        artifacts = build_official_patch_human_approval_prepare(
            dry_run_summary=inputs["dry_run_summary"],
            dry_run_qa=inputs["dry_run_qa"],
            dry_run_patch_diff_preview=inputs["dry_run_patch_diff_preview"],
            dry_run_target_files=inputs["dry_run_target_files"],
            controlled_summary=inputs["controlled_summary"],
            sandbox_summary=inputs["sandbox_summary"],
            official_candidate_summary=inputs["official_candidate_summary"],
        )
        output_paths = _write_prepare_outputs(output_dir, artifacts)
        output_files_written = all(path.exists() for path in output_paths.values())
        summary = artifacts["summary"]
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
        summary["official_patch_human_approval_decision"] = EXPECTED_322M_PREPARE_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_322M_PREPARE_NOT_READY
        write_json(output_paths["summary_json_path"], summary)
        write_json(
            output_paths["qa_json_path"],
            {
                "qa_pass_count": summary["qa_pass_count"],
                "qa_warn_count": summary["qa_warn_count"],
                "qa_fail_count": summary["qa_fail_count"],
                "blocking_reasons": summary["blocking_reasons"],
                "checks": qa_df.to_dict(orient="records"),
            },
        )
        sheets = {
            "approval_summary": pd.DataFrame(
                [
                    {
                        "approval_record_count": summary["approval_record_count"],
                        "alias_approval_count": summary["alias_approval_count"],
                        "scope_approval_count": summary["scope_approval_count"],
                        "unit_approval_count": summary["unit_approval_count"],
                        "rejected_noise_approval_count": summary["rejected_noise_approval_count"],
                        "decision_distribution": str(summary["decision_distribution"]),
                        "qa_fail_count": summary["qa_fail_count"],
                        "decision": summary["official_patch_human_approval_decision"],
                    }
                ]
            ).fillna(""),
            "alias_approvals": artifacts["alias_approvals_df"],
            "scope_approvals": artifacts["scope_approvals_df"],
            "all_patch_operations": artifacts["all_patch_operations_df"],
            "qa": qa_df,
            "review_instructions": artifacts["review_instructions_df"],
            "no_apply_proof": artifacts["no_apply_proof_df"],
        }
        write_excel(output_paths["workbook_path"], sheets, mode="prepare")
        output_paths["instructions_path"].write_text(artifacts["review_instructions_markdown"], encoding="utf-8")

        print(f"official_patch_human_approval_322m_workbook: {output_paths['workbook_path']}")
        print(f"official_patch_human_approval_322m_summary_json: {output_paths['summary_json_path']}")
        print(f"official_patch_human_approval_322m_approval_template_json: {output_paths['template_json_path']}")
        print(f"official_patch_human_approval_322m_qa_json: {output_paths['qa_json_path']}")
        print(f"official_patch_human_approval_322m_no_apply_proof_json: {output_paths['no_apply_path']}")
        print(f"official_patch_human_approval_322m_review_instructions_md: {output_paths['instructions_path']}")
        for key in [
            "approval_record_count",
            "alias_approval_count",
            "scope_approval_count",
            "unit_approval_count",
            "rejected_noise_approval_count",
            "qa_pass_count",
            "qa_warn_count",
            "qa_fail_count",
            "official_patch_human_approval_decision",
        ]:
            print(f"{key}: {summary.get(key, '')}")
        print(f"decision_distribution: {summary.get('decision_distribution', {})}")
        return 0

    reviewed_workbook = Path(args.reviewed_approval_workbook) if args.reviewed_approval_workbook else Path()
    if not dry_run_dir.exists():
        _blocked_reviewed_result(output_dir, "BLOCKED_MISSING_322L_DRY_RUN_DIR")
        print(f"official_patch_human_approval_322m_reviewed_summary_json: {output_dir / 'official_semantic_patch_human_approval_322m_reviewed_summary.json'}")
        return 0
    if not reviewed_workbook or not reviewed_workbook.exists():
        _blocked_reviewed_result(output_dir, "BLOCKED_MISSING_REVIEWED_APPROVAL_WORKBOOK")
        print(f"official_patch_human_approval_322m_reviewed_summary_json: {output_dir / 'official_semantic_patch_human_approval_322m_reviewed_summary.json'}")
        return 0

    inputs = load_official_patch_human_approval_inputs(dry_run_dir=dry_run_dir)
    artifacts = build_official_patch_human_approval_validate_reviewed(
        reviewed_workbook=reviewed_workbook,
        dry_run_summary=inputs["dry_run_summary"],
    )
    output_paths = _write_reviewed_outputs(output_dir, artifacts)
    output_files_written = all(path.exists() for path in output_paths.values())
    summary = artifacts["summary"]
    qa_df = pd.DataFrame(artifacts["qa_json"]["checks"]).fillna("")
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
    summary["official_patch_human_approval_decision"] = EXPECTED_322M_REVIEWED_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_322M_REVIEWED_NOT_READY
    write_json(output_paths["summary_json_path"], summary)
    write_json(
        output_paths["qa_json_path"],
        {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    reviewed_sheets = {
        "reviewed_summary": pd.DataFrame([summary]),
        "approved_patch_operations": artifacts["approved_df"],
        "rejected_patch_operations": artifacts["rejected_df"],
        "needs_more_review_patch_operations": artifacts["needs_more_review_df"],
        "all_reviewed_patch_operations": artifacts["all_reviewed_df"],
        "reviewed_qa": qa_df,
    }
    write_excel(output_paths["workbook_path"], reviewed_sheets, mode="validate-reviewed")

    print(f"official_patch_human_approval_322m_reviewed_workbook: {output_paths['workbook_path']}")
    print(f"official_patch_human_approval_322m_reviewed_summary_json: {output_paths['summary_json_path']}")
    print(f"official_patch_human_approval_322m_final_approved_patch_plan_json: {output_paths['plan_json_path']}")
    print(f"official_patch_human_approval_322m_reviewed_qa_json: {output_paths['qa_json_path']}")
    for key in [
        "reviewed_approval_record_count",
        "approved_patch_count",
        "rejected_patch_count",
        "needs_more_review_count",
        "pending_count",
        "invalid_decision_count",
        "final_approved_patch_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "official_patch_human_approval_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    print(f"decision_distribution: {summary.get('decision_distribution', {})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
