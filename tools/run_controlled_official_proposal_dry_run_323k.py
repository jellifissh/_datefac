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

from datefac.semantic.controlled_official_proposal_dry_run import (  # noqa: E402
    EXPECTED_NEXT_DECISION,
    FORMAL_SCOPE_RULES_PATH,
    NOT_READY_DECISION,
    OFFICIAL_ALIAS_ASSET_PATH,
    build_controlled_official_proposal_dry_run,
    load_controlled_official_proposal_dry_run_inputs,
)
from datefac.semantic.controlled_official_proposal_dry_run_report import (  # noqa: E402
    controlled_official_proposal_dry_run_markdown,
    controlled_official_proposal_dry_run_rollback_markdown,
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
        "stage": "323K",
        "output_dir": str(output_dir),
        "source_controlled_proposal_decision": "",
        "source_controlled_proposal_qa_fail_count": 1,
        "proposal_count": 0,
        "alias_proposal_count": 0,
        "scope_proposal_count": 0,
        "ready_for_dry_run_proposal_count": 0,
        "patch_operation_count": 0,
        "alias_patch_operation_count": 0,
        "scope_patch_operation_count": 0,
        "target_asset_file_count": 0,
        "target_group_count": 0,
        "duplicate_operation_count": 0,
        "target_conflict_count": 0,
        "already_official_overlap_count": 0,
        "missing_target_asset_or_group_count": 0,
        "missing_provenance_count": 0,
        "affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "rollback_plan_record_count": 0,
        "no_apply_confirmed": True,
        "official_assets_not_modified_confirmed": True,
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
        "patch_operations": empty,
        "before_after_preview": empty,
        "target_asset_diff_preview": empty,
        "rollback_plan": empty,
        "qa_summary": pd.DataFrame(
            [{"qa_fail_count": 1, "decision": NOT_READY_DECISION, "blocking_reasons": code}]
        ),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
        "known_limitations": pd.DataFrame(
            [{"limitation": "blocked_input", "detail": code}]
        ),
    }
    write_excel(
        output_dir / "controlled_official_proposal_dry_run_323k_target_asset_diff_preview.xlsx",
        sheets,
    )
    write_json(
        output_dir / "controlled_official_proposal_dry_run_323k_summary.json", summary
    )
    write_json(
        output_dir / "controlled_official_proposal_dry_run_323k_patch_operations.json",
        {"stage": "323K", "decision": NOT_READY_DECISION, "patch_operations": []},
    )
    write_json(
        output_dir
        / "controlled_official_proposal_dry_run_323k_target_asset_diff_preview.json",
        {
            "stage": "323K",
            "decision": NOT_READY_DECISION,
            "before_after_preview": [],
            "target_asset_diff_preview": [],
        },
    )
    write_json(
        output_dir / "controlled_official_proposal_dry_run_323k_rollback_plan.json",
        {"stage": "323K", "decision": NOT_READY_DECISION, "rollback_plan": []},
    )
    write_json(output_dir / "controlled_official_proposal_dry_run_323k_qa.json", qa_json)
    write_json(
        output_dir / "controlled_official_proposal_dry_run_323k_no_apply_proof.json",
        {
            "files_read": [],
            "files_written": [],
            "target_official_files_inspected": [],
            "target_locators_preview_only": [],
            "official_assets_not_modified": [],
            "output_only_write_confirmation": True,
            "decision": "dry_run_only_no_apply",
        },
    )
    (
        output_dir
        / "controlled_official_proposal_dry_run_323k_target_asset_diff_preview.md"
    ).write_text(controlled_official_proposal_dry_run_markdown(summary), encoding="utf-8")
    (
        output_dir / "controlled_official_proposal_dry_run_323k_rollback_plan.md"
    ).write_text(
        controlled_official_proposal_dry_run_rollback_markdown([]), encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 323K controlled official proposal dry run."
    )
    parser.add_argument(
        "--controlled-proposal-dir",
        default=r"D:\_datefac\output\controlled_official_proposal_from_323i_323j",
    )
    parser.add_argument(
        "--official-rule-candidate-dir",
        default=r"D:\_datefac\output\official_rule_candidates_from_323h_323i",
    )
    parser.add_argument(
        "--sandbox-replay-dir",
        default=r"D:\_datefac\output\human_confirmed_sandbox_replay_323h",
    )
    parser.add_argument(
        "--output-dir",
        default=r"D:\_datefac\output\controlled_official_proposal_dry_run_323k",
    )
    args = parser.parse_args()

    controlled_proposal_dir = Path(args.controlled_proposal_dir)
    official_rule_candidate_dir = Path(args.official_rule_candidate_dir)
    sandbox_replay_dir = Path(args.sandbox_replay_dir)
    output_dir = Path(args.output_dir)

    if not controlled_proposal_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_323J_CONTROLLED_PROPOSAL_DIR")
        print(
            "controlled_official_proposal_dry_run_323k_summary_json: "
            f"{output_dir / 'controlled_official_proposal_dry_run_323k_summary.json'}"
        )
        return 0
    if not official_rule_candidate_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_323I_OFFICIAL_RULE_CANDIDATE_DIR")
        print(
            "controlled_official_proposal_dry_run_323k_summary_json: "
            f"{output_dir / 'controlled_official_proposal_dry_run_323k_summary.json'}"
        )
        return 0
    if not sandbox_replay_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_323H_SANDBOX_REPLAY_DIR")
        print(
            "controlled_official_proposal_dry_run_323k_summary_json: "
            f"{output_dir / 'controlled_official_proposal_dry_run_323k_summary.json'}"
        )
        return 0

    alias_hash_before = _sha256_file(OFFICIAL_ALIAS_ASSET_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    inputs = load_controlled_official_proposal_dry_run_inputs(
        controlled_proposal_dir=controlled_proposal_dir,
        official_rule_candidate_dir=official_rule_candidate_dir,
        sandbox_replay_dir=sandbox_replay_dir,
    )
    artifacts = build_controlled_official_proposal_dry_run(
        controlled_summary=inputs["controlled_summary"],
        controlled_qa=inputs["controlled_qa"],
        controlled_proposals_df=inputs["controlled_proposals_df"],
        duplicate_provenance_bridge_df=inputs["duplicate_provenance_bridge_df"],
        official_rule_candidate_summary=inputs["official_rule_candidate_summary"],
        sandbox_summary=inputs["sandbox_summary"],
        official_alias_payload=inputs["official_alias_payload"],
        formal_scope_rules_payload=inputs["formal_scope_rules_payload"],
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_json_path = output_dir / "controlled_official_proposal_dry_run_323k_summary.json"
    patch_ops_json_path = output_dir / "controlled_official_proposal_dry_run_323k_patch_operations.json"
    diff_preview_json_path = output_dir / "controlled_official_proposal_dry_run_323k_target_asset_diff_preview.json"
    qa_json_path = output_dir / "controlled_official_proposal_dry_run_323k_qa.json"
    rollback_json_path = output_dir / "controlled_official_proposal_dry_run_323k_rollback_plan.json"
    no_apply_json_path = output_dir / "controlled_official_proposal_dry_run_323k_no_apply_proof.json"
    diff_preview_md_path = output_dir / "controlled_official_proposal_dry_run_323k_target_asset_diff_preview.md"
    rollback_md_path = output_dir / "controlled_official_proposal_dry_run_323k_rollback_plan.md"
    workbook_path = output_dir / "controlled_official_proposal_dry_run_323k_target_asset_diff_preview.xlsx"

    sheets = {
        "summary": pd.DataFrame([summary]),
        "patch_operations": artifacts["patch_operations_df"],
        "before_after_preview": artifacts["before_after_preview_df"],
        "target_asset_diff_preview": artifacts["target_asset_diff_preview_df"],
        "rollback_plan": artifacts["rollback_plan_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }

    write_excel(workbook_path, sheets)
    write_json(summary_json_path, summary)
    write_json(patch_ops_json_path, artifacts["patch_operations_json"])
    write_json(diff_preview_json_path, artifacts["target_asset_diff_preview_json"])
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(rollback_json_path, artifacts["rollback_plan_json"])
    write_json(no_apply_json_path, artifacts["no_apply_proof_json"])
    diff_preview_md_path.write_text(
        controlled_official_proposal_dry_run_markdown(summary), encoding="utf-8"
    )
    rollback_md_path.write_text(
        controlled_official_proposal_dry_run_rollback_markdown(
            artifacts["rollback_plan_df"].to_dict(orient="records")
        ),
        encoding="utf-8",
    )

    alias_hash_after = _sha256_file(OFFICIAL_ALIAS_ASSET_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    official_assets_unchanged = (
        alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    )

    qa_df = artifacts["qa_checks_df"].copy()
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "safety::official_assets_not_modified",
                        "status": "PASS" if official_assets_unchanged else "FAIL",
                        "detail": (
                            f"alias_before={alias_hash_before} alias_after={alias_hash_after} "
                            f"scope_before={scope_hash_before} scope_after={scope_hash_after}"
                        ),
                    },
                    {
                        "check_name": "output::artifacts_written_successfully",
                        "status": "PASS"
                        if all(
                            path.exists()
                            for path in [
                                summary_json_path,
                                patch_ops_json_path,
                                diff_preview_json_path,
                                qa_json_path,
                                rollback_json_path,
                                no_apply_json_path,
                                diff_preview_md_path,
                                rollback_md_path,
                                workbook_path,
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
        EXPECTED_NEXT_DECISION if summary["qa_fail_count"] == 0 else NOT_READY_DECISION
    )

    artifacts["qa_json"]["qa_pass_count"] = summary["qa_pass_count"]
    artifacts["qa_json"]["qa_warn_count"] = summary["qa_warn_count"]
    artifacts["qa_json"]["qa_fail_count"] = summary["qa_fail_count"]
    artifacts["qa_json"]["blocking_reasons"] = summary["blocking_reasons"]
    artifacts["qa_json"]["checks"] = qa_df.to_dict(orient="records")
    artifacts["patch_operations_json"]["decision"] = summary["decision"]
    artifacts["target_asset_diff_preview_json"]["decision"] = summary["decision"]
    artifacts["rollback_plan_json"]["decision"] = summary["decision"]

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

    write_excel(workbook_path, sheets)
    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(patch_ops_json_path, artifacts["patch_operations_json"])
    write_json(diff_preview_json_path, artifacts["target_asset_diff_preview_json"])
    write_json(rollback_json_path, artifacts["rollback_plan_json"])
    diff_preview_md_path.write_text(
        controlled_official_proposal_dry_run_markdown(summary), encoding="utf-8"
    )
    rollback_md_path.write_text(
        controlled_official_proposal_dry_run_rollback_markdown(
            artifacts["rollback_plan_df"].to_dict(orient="records")
        ),
        encoding="utf-8",
    )

    print(f"controlled_official_proposal_dry_run_323k_summary_json: {summary_json_path}")
    print(f"controlled_official_proposal_dry_run_323k_patch_operations_json: {patch_ops_json_path}")
    print(f"controlled_official_proposal_dry_run_323k_target_asset_diff_preview_json: {diff_preview_json_path}")
    print(f"controlled_official_proposal_dry_run_323k_target_asset_diff_preview_md: {diff_preview_md_path}")
    print(f"controlled_official_proposal_dry_run_323k_target_asset_diff_preview_xlsx: {workbook_path}")
    print(f"controlled_official_proposal_dry_run_323k_rollback_plan_json: {rollback_json_path}")
    print(f"controlled_official_proposal_dry_run_323k_rollback_plan_md: {rollback_md_path}")
    print(f"controlled_official_proposal_dry_run_323k_qa_json: {qa_json_path}")
    print(f"controlled_official_proposal_dry_run_323k_no_apply_proof_json: {no_apply_json_path}")
    for key in [
        "proposal_count",
        "alias_proposal_count",
        "scope_proposal_count",
        "patch_operation_count",
        "alias_patch_operation_count",
        "scope_patch_operation_count",
        "duplicate_operation_count",
        "target_conflict_count",
        "already_official_overlap_count",
        "affected_candidate_count",
        "expected_trusted_gain",
        "expected_review_reduction",
        "expected_out_of_scope_or_rejected_gain",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
