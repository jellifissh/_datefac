from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.official_alias_patch_application_325n import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    EXPECTED_325N_NOT_READY,
    build_official_alias_patch_application_325n,
    load_official_alias_patch_application_325n_inputs,
)
from datefac.semantic.official_alias_patch_application_325n_report import (  # noqa: E402
    official_alias_patch_application_325n_markdown,
    rollback_instructions_markdown,
    write_excel,
    write_json,
)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325N",
        "output_dir": str(output_dir),
        "approved_patch_operation_count": 0,
        "alias_approved_patch_operation_count": 0,
        "scope_approved_patch_operation_count": 0,
        "applied_operation_count": 0,
        "idempotent_operation_count": 0,
        "applied_or_idempotent_operation_count": 0,
        "conflicting_existing_alias_count": 0,
        "target_conflict_count": 0,
        "duplicate_count_before": 0,
        "duplicate_count_after": 0,
        "duplicate_delta_count": 0,
        "semantic_alias_candidates_hash_before": "",
        "semantic_alias_candidates_hash_after": "",
        "formal_scope_rules_hash_before": "",
        "formal_scope_rules_hash_after": "",
        "semantic_alias_candidates_hash_changed": False,
        "formal_scope_rules_hash_unchanged": True,
        "target_official_assets_modified": [],
        "formal_scope_rules_unchanged_confirmed": True,
        "affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "rollback_backup_paths": {},
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_325N_NOT_READY,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    write_json(output_dir / "official_alias_patch_application_325n_summary.json", summary)
    write_json(output_dir / "official_alias_patch_application_325n_before_snapshot.json", {"assets": []})
    write_json(output_dir / "official_alias_patch_application_325n_after_snapshot.json", {"assets": []})
    write_json(
        output_dir / "official_alias_patch_application_325n_rollback_plan.json",
        {"stage": "325N", "decision": EXPECTED_325N_NOT_READY, "rollback_rows": []},
    )
    write_json(output_dir / "official_alias_patch_application_325n_qa.json", qa_json)
    write_json(
        output_dir / "official_alias_patch_application_325n_apply_proof.json",
        {"stage": "325N", "decision": EXPECTED_325N_NOT_READY, "official_assets_written": []},
    )
    (output_dir / "official_alias_patch_application_325n_applied_operations.jsonl").write_text("", encoding="utf-8")
    (output_dir / "official_alias_patch_application_325n_asset_diff_preview.md").write_text(
        official_alias_patch_application_325n_markdown(summary),
        encoding="utf-8",
    )
    (output_dir / "official_alias_patch_application_325n_rollback_instructions.md").write_text(
        rollback_instructions_markdown(summary, []),
        encoding="utf-8",
    )
    write_excel(
        output_dir / "official_alias_patch_application_325n_asset_diff_preview.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "before_snapshot": pd.DataFrame(),
            "after_snapshot": pd.DataFrame(),
            "precheck": pd.DataFrame(),
            "before_after_preview": pd.DataFrame(),
            "asset_diff_preview": pd.DataFrame(),
            "application_log": pd.DataFrame(),
            "rollback_plan": pd.DataFrame(),
            "qa_summary": pd.DataFrame(
                [
                    {
                        "qa_pass_count": 0,
                        "qa_warn_count": 0,
                        "qa_fail_count": 1,
                        "blocking_reasons": code,
                        "decision": EXPECTED_325N_NOT_READY,
                    }
                ]
            ),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "known_limitations": pd.DataFrame(
                [{"limitation": "blocked_input", "detail": "Required input is missing."}]
            ),
        },
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325N official alias patch application.")
    parser.add_argument(
        "--reviewed-approval-dir",
        default=r"D:\_datefac\output\controlled_alias_proposal_human_approval_325m_reviewed",
    )
    parser.add_argument(
        "--dry-run-dir",
        default=r"D:\_datefac\output\controlled_official_proposal_dry_run_325l",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    reviewed_dir = Path(args.reviewed_approval_dir)
    dry_run_dir = Path(args.dry_run_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (reviewed_dir, "BLOCKED_MISSING_325M_REVIEWED_DIR"),
        (dry_run_dir, "BLOCKED_MISSING_325L_DRY_RUN_DIR"),
    ]
    for path, code in required_dirs:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"official_alias_patch_application_325n_summary_json: {output_dir / 'official_alias_patch_application_325n_summary.json'}")
            return 0

    inputs = load_official_alias_patch_application_325n_inputs(
        reviewed_dir=reviewed_dir,
        dry_run_dir=dry_run_dir,
    )
    artifacts = build_official_alias_patch_application_325n(
        reviewed_summary=inputs["reviewed_summary"],
        reviewed_qa=inputs["reviewed_qa"],
        reviewed_result=inputs["reviewed_result"],
        dry_run_summary=inputs["dry_run_summary"],
        dry_run_qa=inputs["dry_run_qa"],
        patch_operations_json=inputs["patch_operations_json"],
        output_dir=output_dir,
    )

    summary = artifacts["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "official_alias_patch_application_325n_summary.json",
        "application_log_jsonl": output_dir / "official_alias_patch_application_325n_applied_operations.jsonl",
        "before_snapshot_json": output_dir / "official_alias_patch_application_325n_before_snapshot.json",
        "after_snapshot_json": output_dir / "official_alias_patch_application_325n_after_snapshot.json",
        "asset_diff_md": output_dir / "official_alias_patch_application_325n_asset_diff_preview.md",
        "asset_diff_xlsx": output_dir / "official_alias_patch_application_325n_asset_diff_preview.xlsx",
        "rollback_plan_json": output_dir / "official_alias_patch_application_325n_rollback_plan.json",
        "rollback_instructions_md": output_dir / "official_alias_patch_application_325n_rollback_instructions.md",
        "qa_json": output_dir / "official_alias_patch_application_325n_qa.json",
        "apply_proof_json": output_dir / "official_alias_patch_application_325n_apply_proof.json",
    }

    write_json(output_files["summary_json"], summary)
    write_json(output_files["before_snapshot_json"], artifacts["before_snapshot_json"])
    write_json(output_files["after_snapshot_json"], artifacts["after_snapshot_json"])
    write_json(
        output_files["rollback_plan_json"],
        {
            "stage": "325N",
            "decision": summary["decision"],
            "rollback_rows": artifacts["rollback_plan_rows"],
        },
    )
    write_json(output_files["qa_json"], artifacts["qa_json"])
    write_json(output_files["apply_proof_json"], artifacts["apply_proof_json"])
    _write_jsonl(output_files["application_log_jsonl"], artifacts["application_log_rows"])
    output_files["asset_diff_md"].write_text(
        official_alias_patch_application_325n_markdown(summary),
        encoding="utf-8",
    )
    output_files["rollback_instructions_md"].write_text(
        rollback_instructions_markdown(summary, artifacts["rollback_plan_rows"]),
        encoding="utf-8",
    )

    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "before_snapshot": artifacts["before_snapshot_df"],
        "after_snapshot": artifacts["after_snapshot_df"],
        "precheck": artifacts["precheck_df"],
        "before_after_preview": artifacts["before_after_preview_df"],
        "asset_diff_preview": artifacts["asset_diff_df"],
        "application_log": artifacts["application_log_df"],
        "rollback_plan": artifacts["rollback_plan_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_excel(output_files["asset_diff_xlsx"], sheets)

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
    summary["blocking_reasons"] = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )
    summary["decision"] = (
        "OFFICIAL_ALIAS_PATCH_APPLICATION_325N_READY_FOR_325O_POST_PATCH_REGRESSION"
        if summary["qa_fail_count"] == 0
        else EXPECTED_325N_NOT_READY
    )

    final_qa_json = {
        "qa_pass_count": summary["qa_pass_count"],
        "qa_warn_count": summary["qa_warn_count"],
        "qa_fail_count": summary["qa_fail_count"],
        "blocking_reasons": summary["blocking_reasons"],
        "checks": qa_df.to_dict(orient="records"),
    }

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

    write_json(output_files["summary_json"], summary)
    write_json(output_files["qa_json"], final_qa_json)
    write_excel(output_files["asset_diff_xlsx"], sheets)
    output_files["asset_diff_md"].write_text(
        official_alias_patch_application_325n_markdown(summary),
        encoding="utf-8",
    )

    print(f"official_alias_patch_application_325n_summary_json: {output_files['summary_json']}")
    print(f"official_alias_patch_application_325n_applied_operations_jsonl: {output_files['application_log_jsonl']}")
    print(f"official_alias_patch_application_325n_before_snapshot_json: {output_files['before_snapshot_json']}")
    print(f"official_alias_patch_application_325n_after_snapshot_json: {output_files['after_snapshot_json']}")
    print(f"official_alias_patch_application_325n_asset_diff_preview_md: {output_files['asset_diff_md']}")
    print(f"official_alias_patch_application_325n_asset_diff_preview_xlsx: {output_files['asset_diff_xlsx']}")
    print(f"official_alias_patch_application_325n_rollback_plan_json: {output_files['rollback_plan_json']}")
    print(f"official_alias_patch_application_325n_rollback_instructions_md: {output_files['rollback_instructions_md']}")
    print(f"official_alias_patch_application_325n_qa_json: {output_files['qa_json']}")
    print(f"official_alias_patch_application_325n_apply_proof_json: {output_files['apply_proof_json']}")
    for key in [
        "approved_patch_operation_count",
        "alias_approved_patch_operation_count",
        "scope_approved_patch_operation_count",
        "applied_operation_count",
        "idempotent_operation_count",
        "applied_or_idempotent_operation_count",
        "conflicting_existing_alias_count",
        "target_conflict_count",
        "duplicate_delta_count",
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
