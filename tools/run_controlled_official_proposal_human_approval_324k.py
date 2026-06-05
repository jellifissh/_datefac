from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.controlled_official_proposal_human_approval_324k import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_OUTPUT_DIR,
    FORMAL_SCOPE_RULES_PATH,
    NOT_READY_DECISION,
    PREPARE_READY_DECISION,
    REVIEWED_APPROVED_DECISION,
    REVIEWED_NEEDS_INFO_DECISION,
    REVIEWED_REJECTED_DECISION,
    build_controlled_official_proposal_human_approval_324k_prepare,
    build_controlled_official_proposal_human_approval_324k_validate_reviewed,
    load_controlled_official_proposal_human_approval_324k_inputs,
    load_controlled_official_proposal_human_approval_324k_reviewed_inputs,
)
from datefac.semantic.controlled_official_proposal_human_approval_324k_report import (  # noqa: E402
    controlled_official_proposal_human_approval_324k_markdown,
    write_excel,
    write_json,
)


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324K",
        "mode": "prepare",
        "output_dir": str(output_dir),
        "source_dry_run_decision": "",
        "source_dry_run_qa_fail_count": 1,
        "approval_record_count": 0,
        "alias_approval_count": 0,
        "scope_approval_count": 0,
        "pending_count": 0,
        "approved_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "decision_distribution": {},
        "carried_warnings": [],
        "expected_affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "official_assets_not_modified_confirmed": True,
        "approval_package_only_no_apply_confirmed": True,
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
    sheets = {
        "summary": pd.DataFrame([summary]),
        "alias_approvals": empty,
        "scope_approvals": empty,
        "all_approval_records": empty,
        "before_after_preview": empty,
        "rollback_plan": empty,
        "qa_summary": pd.DataFrame(
            [{"qa_fail_count": 1, "decision": NOT_READY_DECISION, "blocking_reasons": code}]
        ),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
        "review_instructions": pd.DataFrame(
            [{"section": "blocked_input", "instruction": "Required input is missing."}]
        ),
        "no_apply_proof": pd.DataFrame(
            [
                {
                    "files_read_count": 0,
                    "files_written_count": 0,
                    "official_target_files_inspected_count": 0,
                    "official_target_files_not_modified_count": 0,
                    "files_written_to_official_assets_count": 0,
                    "output_only_write_confirmation": True,
                    "decision": "approval_package_only_no_apply",
                }
            ]
        ),
        "known_limitations": pd.DataFrame(
            [{"limitation": "blocked_input", "detail": code}]
        ),
    }
    workbook_path = output_dir / "controlled_official_proposal_human_approval_324k_workbook.xlsx"
    summary_json_path = output_dir / "controlled_official_proposal_human_approval_324k_summary.json"
    package_json_path = output_dir / "controlled_official_proposal_human_approval_324k_package.json"
    qa_json_path = output_dir / "controlled_official_proposal_human_approval_324k_qa.json"
    no_apply_path = output_dir / "controlled_official_proposal_human_approval_324k_no_apply_proof.json"
    notes_path = output_dir / "controlled_official_proposal_human_approval_324k_review_notes.md"
    write_excel(workbook_path, sheets, mode="prepare")
    write_json(summary_json_path, summary)
    write_json(
        package_json_path,
        {
            "stage": "324K",
            "mode": "prepare",
            "decision": NOT_READY_DECISION,
            "approval_records": [],
            "alias_approval_records": [],
            "scope_approval_records": [],
        },
    )
    write_json(qa_json_path, qa_json)
    write_json(
        no_apply_path,
        {
            "files_read": [],
            "files_written": [],
            "files_written_to_official_assets": [],
            "target_official_files_inspected": [],
            "official_assets_not_modified": [],
            "output_only_write_confirmation": True,
            "decision": "approval_package_only_no_apply",
        },
    )
    notes_path.write_text(
        controlled_official_proposal_human_approval_324k_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 324K controlled official proposal human approval package."
    )
    parser.add_argument(
        "--mode",
        choices=["prepare", "validate-reviewed"],
        default="prepare",
    )
    parser.add_argument(
        "--dry-run-dir",
        default=r"D:\_datefac\output\controlled_official_proposal_dry_run_324j",
    )
    parser.add_argument(
        "--approval-package-dir",
        default=r"D:\_datefac\output\controlled_official_proposal_human_approval_324k",
    )
    parser.add_argument("--reviewed-workbook", default="")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    dry_run_dir = Path(args.dry_run_dir)
    approval_package_dir = Path(args.approval_package_dir)
    output_dir = Path(
        args.output_dir
        or (str(DEFAULT_OUTPUT_DIR) if args.mode == "prepare" else str(DEFAULT_REVIEWED_OUTPUT_DIR))
    )

    if args.mode == "prepare":
        if not dry_run_dir.exists():
            _blocked_result(output_dir, "BLOCKED_MISSING_324J_DRY_RUN_DIR")
            print(
                "controlled_official_proposal_human_approval_324k_summary_json: "
                f"{output_dir / 'controlled_official_proposal_human_approval_324k_summary.json'}"
            )
            return 0

        scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

        inputs = load_controlled_official_proposal_human_approval_324k_inputs(
            dry_run_dir=dry_run_dir
        )
        artifacts = build_controlled_official_proposal_human_approval_324k_prepare(
            dry_run_summary=inputs["dry_run_summary"],
            dry_run_qa=inputs["dry_run_qa"],
            patch_operations_df=inputs["patch_operations_df"],
            before_after_preview_df=inputs["before_after_preview_df"],
            target_asset_diff_preview_df=inputs["target_asset_diff_preview_df"],
            rollback_plan_df=inputs["rollback_plan_df"],
            no_apply_proof_json=inputs["no_apply_proof_json"],
        )

        summary = artifacts["summary"]
        summary["output_dir"] = str(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        workbook_path = output_dir / "controlled_official_proposal_human_approval_324k_workbook.xlsx"
        summary_json_path = output_dir / "controlled_official_proposal_human_approval_324k_summary.json"
        package_json_path = output_dir / "controlled_official_proposal_human_approval_324k_package.json"
        qa_json_path = output_dir / "controlled_official_proposal_human_approval_324k_qa.json"
        no_apply_path = output_dir / "controlled_official_proposal_human_approval_324k_no_apply_proof.json"
        notes_path = output_dir / "controlled_official_proposal_human_approval_324k_review_notes.md"

        sheets = {
            "summary": pd.DataFrame([summary]),
            "alias_approvals": artifacts["alias_approvals_df"],
            "scope_approvals": artifacts["scope_approvals_df"],
            "all_approval_records": artifacts["approval_records_df"],
            "before_after_preview": artifacts["before_after_preview_df"],
            "rollback_plan": artifacts["rollback_plan_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "review_instructions": artifacts["review_instructions_df"],
            "no_apply_proof": artifacts["no_apply_proof_df"],
            "known_limitations": artifacts["known_limitations_df"],
        }

        write_excel(workbook_path, sheets, mode="prepare")
        write_json(summary_json_path, summary)
        write_json(package_json_path, artifacts["approval_package_json"])
        write_json(qa_json_path, artifacts["qa_json"])
        write_json(no_apply_path, artifacts["no_apply_proof_json"])
        notes_path.write_text(artifacts["notes_markdown"], encoding="utf-8")

        scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
        official_assets_unchanged = scope_hash_before == scope_hash_after

        qa_df = artifacts["qa_checks_df"].copy()
        qa_df = pd.concat(
            [
                qa_df,
                pd.DataFrame(
                    [
                        {
                            "check_name": "safety::official_assets_not_modified",
                            "status": "PASS" if official_assets_unchanged else "FAIL",
                            "detail": f"scope_before={scope_hash_before} scope_after={scope_hash_after}",
                        },
                        {
                            "check_name": "output::artifacts_written_successfully",
                            "status": "PASS"
                            if all(
                                path.exists()
                                for path in [
                                    workbook_path,
                                    summary_json_path,
                                    package_json_path,
                                    qa_json_path,
                                    no_apply_path,
                                    notes_path,
                                ]
                            )
                            else "FAIL",
                            "detail": str(output_dir),
                        },
                    ]
                ),
            ],
            ignore_index=True,
        )

        summary["official_assets_not_modified_confirmed"] = official_assets_unchanged
        summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
        summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
        summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
        summary["blocking_reasons"] = (
            qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
            if not qa_df.empty
            else []
        )
        summary["decision"] = (
            PREPARE_READY_DECISION if summary["qa_fail_count"] == 0 else NOT_READY_DECISION
        )

        artifacts["qa_json"]["qa_pass_count"] = summary["qa_pass_count"]
        artifacts["qa_json"]["qa_warn_count"] = summary["qa_warn_count"]
        artifacts["qa_json"]["qa_fail_count"] = summary["qa_fail_count"]
        artifacts["qa_json"]["blocking_reasons"] = summary["blocking_reasons"]
        artifacts["qa_json"]["checks"] = qa_df.to_dict(orient="records")
        artifacts["approval_package_json"]["decision"] = summary["decision"]

        sheets["summary"] = pd.DataFrame([summary])
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

        write_excel(workbook_path, sheets, mode="prepare")
        write_json(summary_json_path, summary)
        write_json(package_json_path, artifacts["approval_package_json"])
        write_json(qa_json_path, artifacts["qa_json"])
        notes_path.write_text(
            controlled_official_proposal_human_approval_324k_markdown(summary),
            encoding="utf-8",
        )

        print(f"controlled_official_proposal_human_approval_324k_workbook: {workbook_path}")
        print(f"controlled_official_proposal_human_approval_324k_summary_json: {summary_json_path}")
        print(f"controlled_official_proposal_human_approval_324k_package_json: {package_json_path}")
        print(f"controlled_official_proposal_human_approval_324k_qa_json: {qa_json_path}")
        print(f"controlled_official_proposal_human_approval_324k_no_apply_proof_json: {no_apply_path}")
        print(f"controlled_official_proposal_human_approval_324k_review_notes_md: {notes_path}")
        for key in [
            "approval_record_count",
            "alias_approval_count",
            "scope_approval_count",
            "pending_count",
            "approved_count",
            "rejected_count",
            "needs_more_info_count",
            "qa_pass_count",
            "qa_warn_count",
            "qa_fail_count",
            "decision",
        ]:
            print(f"{key}: {summary.get(key, '')}")
        print(f"decision_distribution: {summary.get('decision_distribution', {})}")
        return 0

    reviewed_workbook = Path(args.reviewed_workbook) if args.reviewed_workbook else (
        approval_package_dir / "controlled_official_proposal_human_approval_324k_workbook.xlsx"
    )
    if not approval_package_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_324K_APPROVAL_PACKAGE_DIR")
        print(
            "controlled_official_proposal_human_approval_324k_reviewed_summary_json: "
            f"{output_dir / 'controlled_official_proposal_human_approval_324k_reviewed_summary.json'}"
        )
        return 0
    if not reviewed_workbook.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_324K_REVIEWED_WORKBOOK")
        print(
            "controlled_official_proposal_human_approval_324k_reviewed_summary_json: "
            f"{output_dir / 'controlled_official_proposal_human_approval_324k_reviewed_summary.json'}"
        )
        return 0

    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    reviewed_inputs = load_controlled_official_proposal_human_approval_324k_reviewed_inputs(
        approval_package_dir=approval_package_dir,
        reviewed_workbook=reviewed_workbook,
    )
    artifacts = build_controlled_official_proposal_human_approval_324k_validate_reviewed(
        approval_summary=reviewed_inputs["approval_summary"],
        approval_qa=reviewed_inputs["approval_qa"],
        approval_package_json=reviewed_inputs["approval_package_json"],
        reviewed_all_records_df=reviewed_inputs["reviewed_all_records_df"],
        reviewed_scope_df=reviewed_inputs["reviewed_scope_df"],
        reviewed_alias_df=reviewed_inputs["reviewed_alias_df"],
        reviewed_workbook=reviewed_workbook,
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = output_dir / "controlled_official_proposal_human_approval_324k_reviewed_workbook.xlsx"
    summary_json_path = output_dir / "controlled_official_proposal_human_approval_324k_reviewed_summary.json"
    final_result_path = output_dir / "controlled_official_proposal_human_approval_324k_reviewed_result.json"
    qa_json_path = output_dir / "controlled_official_proposal_human_approval_324k_reviewed_qa.json"
    notes_path = output_dir / "controlled_official_proposal_human_approval_324k_reviewed_notes.md"

    reviewed_sheets = {
        "reviewed_summary": pd.DataFrame([summary]),
        "approved_records": artifacts["approved_df"],
        "rejected_records": artifacts["rejected_df"],
        "needs_more_info_records": artifacts["needs_more_info_df"],
        "all_reviewed_approval_records": artifacts["all_reviewed_df"],
        "reviewed_qa_summary": artifacts["qa_summary_df"],
        "reviewed_qa_checks": artifacts["qa_checks_df"],
    }
    write_excel(workbook_path, reviewed_sheets, mode="reviewed")
    write_json(summary_json_path, summary)
    write_json(final_result_path, artifacts["final_review_result_json"])
    write_json(qa_json_path, artifacts["qa_json"])
    notes_path.write_text(artifacts["notes_markdown"], encoding="utf-8")

    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    official_assets_unchanged = scope_hash_before == scope_hash_after

    qa_df = artifacts["qa_checks_df"].copy()
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "safety::official_assets_not_modified",
                        "status": "PASS" if official_assets_unchanged else "FAIL",
                        "detail": f"scope_before={scope_hash_before} scope_after={scope_hash_after}",
                    },
                    {
                        "check_name": "output::artifacts_written_successfully",
                        "status": "PASS"
                        if all(
                            path.exists()
                            for path in [
                                workbook_path,
                                summary_json_path,
                                final_result_path,
                                qa_json_path,
                                notes_path,
                            ]
                        )
                        else "FAIL",
                        "detail": str(output_dir),
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    summary["official_assets_not_modified_confirmed"] = official_assets_unchanged
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

    artifacts["qa_json"]["qa_pass_count"] = summary["qa_pass_count"]
    artifacts["qa_json"]["qa_warn_count"] = summary["qa_warn_count"]
    artifacts["qa_json"]["qa_fail_count"] = summary["qa_fail_count"]
    artifacts["qa_json"]["blocking_reasons"] = summary["blocking_reasons"]
    artifacts["qa_json"]["checks"] = qa_df.to_dict(orient="records")
    artifacts["final_review_result_json"]["decision"] = summary["decision"]

    reviewed_sheets["reviewed_summary"] = pd.DataFrame([summary])
    reviewed_sheets["reviewed_qa_summary"] = pd.DataFrame(
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
    reviewed_sheets["reviewed_qa_checks"] = qa_df

    write_excel(workbook_path, reviewed_sheets, mode="reviewed")
    write_json(summary_json_path, summary)
    write_json(final_result_path, artifacts["final_review_result_json"])
    write_json(qa_json_path, artifacts["qa_json"])
    notes_path.write_text(artifacts["notes_markdown"], encoding="utf-8")

    print(f"controlled_official_proposal_human_approval_324k_reviewed_workbook: {workbook_path}")
    print(f"controlled_official_proposal_human_approval_324k_reviewed_summary_json: {summary_json_path}")
    print(f"controlled_official_proposal_human_approval_324k_reviewed_result_json: {final_result_path}")
    print(f"controlled_official_proposal_human_approval_324k_reviewed_qa_json: {qa_json_path}")
    print(f"controlled_official_proposal_human_approval_324k_reviewed_notes_md: {notes_path}")
    for key in [
        "approval_record_count",
        "approved_count",
        "rejected_count",
        "needs_more_info_count",
        "pending_count",
        "invalid_decision_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    print(f"decision_distribution: {summary.get('decision_distribution', {})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
