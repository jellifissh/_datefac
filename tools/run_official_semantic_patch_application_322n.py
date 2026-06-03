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

from datefac.semantic.official_patch_application import (
    DEFAULT_OUTPUT_DIR,
    EXPECTED_322N_NOT_READY,
    build_official_patch_application,
    load_official_patch_application_inputs,
)
from datefac.semantic.official_patch_application_report import (
    official_patch_application_report_markdown,
    rollback_instructions_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322N",
        "output_dir": str(output_dir),
        "approved_patch_count": 0,
        "applied_operation_count": 0,
        "idempotent_operation_count": 0,
        "applied_or_idempotent_operation_count": 0,
        "alias_operation_count": 0,
        "scope_operation_count": 0,
        "unit_operation_count": 0,
        "rejected_noise_operation_count": 0,
        "conflict_count": 0,
        "expected_affected_candidate_count": 0,
        "expected_trusted_gain": 0,
        "expected_review_reduction": 0,
        "expected_out_of_scope_or_rejected_gain": 0,
        "partial_application_detected": False,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_322N_NOT_READY,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    sheets = {
        "summary": pd.DataFrame([summary]),
        "before_snapshot": pd.DataFrame(),
        "after_snapshot": pd.DataFrame(),
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
                    "decision": summary["decision"],
                }
            ]
        ),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": "Required input is missing."}]),
    }
    output_files = {
        "summary_json": output_dir / "official_semantic_patch_application_322n_summary.json",
        "application_log_jsonl": output_dir / "official_semantic_patch_application_322n_application_log.jsonl",
        "before_snapshot_json": output_dir / "official_semantic_patch_application_322n_before_snapshot.json",
        "after_snapshot_json": output_dir / "official_semantic_patch_application_322n_after_snapshot.json",
        "asset_diff_md": output_dir / "official_semantic_patch_application_322n_asset_diff_preview.md",
        "asset_diff_xlsx": output_dir / "official_semantic_patch_application_322n_asset_diff_preview.xlsx",
        "rollback_plan_json": output_dir / "official_semantic_patch_application_322n_rollback_plan.json",
        "rollback_instructions_md": output_dir / "official_semantic_patch_application_322n_rollback_instructions.md",
        "qa_json": output_dir / "official_semantic_patch_application_322n_qa.json",
    }
    write_json(output_files["summary_json"], summary)
    write_json(output_files["before_snapshot_json"], {"assets": []})
    write_json(output_files["after_snapshot_json"], {"assets": []})
    write_json(output_files["rollback_plan_json"], {"rollback_rows": []})
    write_json(output_files["qa_json"], qa_json)
    output_files["application_log_jsonl"].write_text("", encoding="utf-8")
    output_files["asset_diff_md"].write_text(official_patch_application_report_markdown(summary), encoding="utf-8")
    output_files["rollback_instructions_md"].write_text(
        rollback_instructions_markdown(summary, []), encoding="utf-8"
    )
    write_excel(output_files["asset_diff_xlsx"], sheets)
    return summary


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            import json

            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322N official semantic patch application.")
    parser.add_argument(
        "--reviewed-approval-dir",
        default=r"D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed",
    )
    parser.add_argument(
        "--dry-run-dir",
        default=r"D:\_datefac\output\official_semantic_patch_dry_run_322l",
    )
    parser.add_argument(
        "--controlled-proposal-dir",
        default=r"D:\_datefac\output\controlled_official_semantic_patch_proposal_322k",
    )
    parser.add_argument(
        "--sandbox-application-dir",
        default=r"D:\_datefac\output\official_semantic_rule_candidates_322j",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    reviewed_approval_dir = Path(args.reviewed_approval_dir)
    dry_run_dir = Path(args.dry_run_dir)
    controlled_proposal_dir = Path(args.controlled_proposal_dir)
    sandbox_application_dir = Path(args.sandbox_application_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (reviewed_approval_dir, "BLOCKED_MISSING_322M_REVIEWED_DIR"),
        (dry_run_dir, "BLOCKED_MISSING_322L_DRY_RUN_DIR"),
        (controlled_proposal_dir, "BLOCKED_MISSING_322K_CONTROLLED_PROPOSAL_DIR"),
    ]
    for path, code in required_dirs:
        if not path.exists():
            _blocked_result(output_dir, code)
            print(f"official_patch_application_322n_summary_json: {output_dir / 'official_semantic_patch_application_322n_summary.json'}")
            return 0

    inputs = load_official_patch_application_inputs(
        reviewed_approval_dir=reviewed_approval_dir,
        dry_run_dir=dry_run_dir,
        controlled_proposal_dir=controlled_proposal_dir,
        sandbox_application_dir=sandbox_application_dir if sandbox_application_dir.exists() else None,
    )
    artifacts = build_official_patch_application(
        reviewed_summary=inputs["reviewed_summary"],
        reviewed_qa=inputs["reviewed_qa"],
        final_approved_patch_plan=inputs["final_approved_patch_plan"],
        dry_run_summary=inputs["dry_run_summary"],
        dry_run_qa=inputs["dry_run_qa"],
        controlled_summary=inputs["controlled_summary"],
        sandbox_summary=inputs["sandbox_summary"],
        output_dir=output_dir,
    )

    summary = artifacts["summary"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "summary_json": output_dir / "official_semantic_patch_application_322n_summary.json",
        "application_log_jsonl": output_dir / "official_semantic_patch_application_322n_application_log.jsonl",
        "before_snapshot_json": output_dir / "official_semantic_patch_application_322n_before_snapshot.json",
        "after_snapshot_json": output_dir / "official_semantic_patch_application_322n_after_snapshot.json",
        "asset_diff_md": output_dir / "official_semantic_patch_application_322n_asset_diff_preview.md",
        "asset_diff_xlsx": output_dir / "official_semantic_patch_application_322n_asset_diff_preview.xlsx",
        "rollback_plan_json": output_dir / "official_semantic_patch_application_322n_rollback_plan.json",
        "rollback_instructions_md": output_dir / "official_semantic_patch_application_322n_rollback_instructions.md",
        "qa_json": output_dir / "official_semantic_patch_application_322n_qa.json",
    }

    write_json(output_files["summary_json"], summary)
    write_json(output_files["before_snapshot_json"], artifacts["before_snapshot_json"])
    write_json(output_files["after_snapshot_json"], artifacts["after_snapshot_json"])
    write_json(
        output_files["rollback_plan_json"],
        {
            "stage": "322N",
            "rollback_rows": artifacts["rollback_plan_rows"],
            "decision": summary["decision"],
        },
    )
    write_json(output_files["qa_json"], artifacts["qa_json"])
    _write_jsonl(output_files["application_log_jsonl"], artifacts["application_log_rows"])
    output_files["asset_diff_md"].write_text(
        official_patch_application_report_markdown(summary), encoding="utf-8"
    )
    output_files["rollback_instructions_md"].write_text(
        rollback_instructions_markdown(summary, artifacts["rollback_plan_rows"]),
        encoding="utf-8",
    )

    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "before_snapshot": artifacts["before_snapshot_df"],
        "after_snapshot": artifacts["after_snapshot_df"],
        "asset_diff_preview": artifacts["before_after_assets_df"],
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
    summary["blocking_reasons"] = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    )
    summary["decision"] = (
        "OFFICIAL_SEMANTIC_PATCH_APPLICATION_322N_READY_FOR_322O_POST_PATCH_REGRESSION"
        if summary["qa_fail_count"] == 0
        else EXPECTED_322N_NOT_READY
    )

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
    write_excel(output_files["asset_diff_xlsx"], sheets)
    output_files["asset_diff_md"].write_text(
        official_patch_application_report_markdown(summary), encoding="utf-8"
    )

    print(f"official_patch_application_322n_summary_json: {output_files['summary_json']}")
    print(f"official_patch_application_322n_application_log_jsonl: {output_files['application_log_jsonl']}")
    print(f"official_patch_application_322n_before_snapshot_json: {output_files['before_snapshot_json']}")
    print(f"official_patch_application_322n_after_snapshot_json: {output_files['after_snapshot_json']}")
    print(f"official_patch_application_322n_asset_diff_preview_md: {output_files['asset_diff_md']}")
    print(f"official_patch_application_322n_asset_diff_preview_xlsx: {output_files['asset_diff_xlsx']}")
    print(f"official_patch_application_322n_rollback_plan_json: {output_files['rollback_plan_json']}")
    print(f"official_patch_application_322n_rollback_instructions_md: {output_files['rollback_instructions_md']}")
    print(f"official_patch_application_322n_qa_json: {output_files['qa_json']}")
    for key in [
        "approved_patch_count",
        "applied_or_idempotent_operation_count",
        "alias_operation_count",
        "scope_operation_count",
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
