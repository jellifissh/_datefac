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

from datefac.semantic.human_confirmed_suggestion_proposals import (
    DEFAULT_CONFIGURED_RUN_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RAW_RESPONSE_VALIDATION_DIR,
    DEFAULT_SAFE_SUBSET_DIR,
    EXPECTED_323G_PREPARE_DECISION,
    EXPECTED_323G_PREPARE_NOT_READY,
    EXPECTED_323G_REVIEWED_DECISION,
    EXPECTED_323G_REVIEWED_NOT_READY,
    build_human_confirmed_suggestion_prepare,
    build_human_confirmed_suggestion_validate_reviewed,
    load_human_confirmed_suggestion_inputs,
)
from datefac.semantic.human_confirmed_suggestion_proposals_report import (
    human_confirmed_suggestion_proposals_report_markdown,
    write_excel,
    write_json,
)


def _blocked_prepare_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323G",
        "mode": "prepare",
        "output_dir": str(output_dir),
        "accepted_suggestion_count": 0,
        "alias_accepted_suggestion_count": 0,
        "scope_accepted_suggestion_count": 0,
        "confirmation_record_count": 0,
        "decision_distribution": {},
        "official_assets_not_modified_confirmed": True,
        "proposal_package_only_no_apply_confirmed": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323G_PREPARE_NOT_READY,
    }
    workbook_path = output_dir / "human_confirmed_suggestion_proposals_323g_confirmation_workbook.xlsx"
    summary_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_summary.json"
    qa_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_qa.json"
    package_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_proposal_package.json"
    alias_xlsx_path = output_dir / "human_confirmed_suggestion_proposals_323g_alias_suggestions.xlsx"
    scope_xlsx_path = output_dir / "human_confirmed_suggestion_proposals_323g_scope_suggestions.xlsx"
    instructions_path = output_dir / "human_confirmed_suggestion_proposals_323g_review_instructions.md"
    empty = pd.DataFrame()
    sheets = {
        "summary": pd.DataFrame([summary]),
        "confirmation_records": empty,
        "alias_suggestions": empty,
        "scope_suggestions": empty,
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        "review_instructions": pd.DataFrame([{"section": "blocked_input", "instruction": "Required input is missing."}]),
    }
    write_excel(workbook_path, sheets, mode="prepare")
    write_excel(alias_xlsx_path, {"alias_suggestions": empty}, mode="prepare")
    write_excel(scope_xlsx_path, {"scope_suggestions": empty}, mode="prepare")
    write_json(summary_json_path, summary)
    write_json(package_json_path, {"stage": "323G", "mode": "prepare", "confirmation_records": []})
    write_json(
        qa_json_path,
        {
            "qa_pass_count": 0,
            "qa_warn_count": 0,
            "qa_fail_count": 1,
            "blocking_reasons": [code],
            "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
        },
    )
    instructions_path.write_text(human_confirmed_suggestion_proposals_report_markdown(summary), encoding="utf-8")
    return summary


def _blocked_reviewed_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323G",
        "mode": "validate-reviewed",
        "output_dir": str(output_dir),
        "confirmation_record_count": 0,
        "confirmed_suggestion_count": 0,
        "rejected_suggestion_count": 0,
        "needs_more_info_count": 0,
        "pending_count": 0,
        "invalid_decision_count": 0,
        "decision_distribution": {},
        "official_assets_not_modified_confirmed": True,
        "proposal_package_only_no_apply_confirmed": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323G_REVIEWED_NOT_READY,
    }
    workbook_path = output_dir / "human_confirmed_suggestion_proposals_323g_reviewed_workbook.xlsx"
    summary_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_reviewed_summary.json"
    qa_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_reviewed_qa.json"
    plan_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_human_confirmed_plan.json"
    empty = pd.DataFrame()
    write_excel(
        workbook_path,
        {
            "reviewed_summary": pd.DataFrame([summary]),
            "confirmed_suggestions": empty,
            "rejected_suggestions": empty,
            "needs_more_info": empty,
            "all_reviewed": empty,
            "reviewed_qa": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        },
        mode="validate-reviewed",
    )
    write_json(summary_json_path, summary)
    write_json(plan_json_path, {"stage": "323G", "mode": "validate-reviewed", "confirmed_suggestions": [], "decision": EXPECTED_323G_REVIEWED_NOT_READY})
    write_json(
        qa_json_path,
        {
            "qa_pass_count": 0,
            "qa_warn_count": 0,
            "qa_fail_count": 1,
            "blocking_reasons": [code],
            "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
        },
    )
    return summary


def _write_prepare_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> Dict[str, Path]:
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = output_dir / "human_confirmed_suggestion_proposals_323g_confirmation_workbook.xlsx"
    summary_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_summary.json"
    qa_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_qa.json"
    package_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_proposal_package.json"
    alias_xlsx_path = output_dir / "human_confirmed_suggestion_proposals_323g_alias_suggestions.xlsx"
    scope_xlsx_path = output_dir / "human_confirmed_suggestion_proposals_323g_scope_suggestions.xlsx"
    instructions_path = output_dir / "human_confirmed_suggestion_proposals_323g_review_instructions.md"

    write_excel(
        workbook_path,
        {
            "summary": pd.DataFrame([summary]),
            "confirmation_records": artifacts["confirmation_records_df"],
            "alias_suggestions": artifacts["alias_suggestions_df"],
            "scope_suggestions": artifacts["scope_suggestions_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "review_instructions": artifacts["review_instructions_df"],
        },
        mode="prepare",
    )
    write_excel(
        alias_xlsx_path,
        {"alias_suggestions": artifacts["alias_suggestions_df"]},
        mode="prepare",
    )
    write_excel(
        scope_xlsx_path,
        {"scope_suggestions": artifacts["scope_suggestions_df"]},
        mode="prepare",
    )
    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(package_json_path, artifacts["proposal_package_json"])
    instructions_path.write_text(artifacts["review_instructions_markdown"], encoding="utf-8")

    return {
        "workbook_path": workbook_path,
        "summary_json_path": summary_json_path,
        "qa_json_path": qa_json_path,
        "package_json_path": package_json_path,
        "alias_xlsx_path": alias_xlsx_path,
        "scope_xlsx_path": scope_xlsx_path,
        "instructions_path": instructions_path,
    }


def _write_reviewed_outputs(output_dir: Path, artifacts: Dict[str, Any]) -> Dict[str, Path]:
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = output_dir / "human_confirmed_suggestion_proposals_323g_reviewed_workbook.xlsx"
    summary_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_reviewed_summary.json"
    qa_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_reviewed_qa.json"
    plan_json_path = output_dir / "human_confirmed_suggestion_proposals_323g_human_confirmed_plan.json"

    write_excel(
        workbook_path,
        {
            "reviewed_summary": pd.DataFrame([summary]),
            "confirmed_suggestions": artifacts["confirmed_df"],
            "rejected_suggestions": artifacts["rejected_df"],
            "needs_more_info": artifacts["needs_more_info_df"],
            "all_reviewed": artifacts["all_reviewed_df"],
            "reviewed_qa": artifacts["qa_checks_df"],
        },
        mode="validate-reviewed",
    )
    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(plan_json_path, artifacts["human_confirmed_plan_json"])
    return {
        "workbook_path": workbook_path,
        "summary_json_path": summary_json_path,
        "qa_json_path": qa_json_path,
        "plan_json_path": plan_json_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323G human-confirmed suggestion proposals.")
    parser.add_argument("--mode", choices=["prepare", "validate-reviewed"], default="prepare")
    parser.add_argument("--raw-response-validation-dir", default=str(DEFAULT_RAW_RESPONSE_VALIDATION_DIR))
    parser.add_argument("--safe-subset-dir", default=str(DEFAULT_SAFE_SUBSET_DIR))
    parser.add_argument("--configured-run-dir", default=str(DEFAULT_CONFIGURED_RUN_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--reviewed-confirmation-workbook", default="")
    args = parser.parse_args()

    raw_response_validation_dir = Path(args.raw_response_validation_dir)
    safe_subset_dir = Path(args.safe_subset_dir)
    configured_run_dir = Path(args.configured_run_dir)
    output_dir = Path(args.output_dir)

    if args.mode == "prepare":
        if not raw_response_validation_dir.exists():
            _blocked_prepare_result(output_dir, "BLOCKED_MISSING_323F_DIR")
            print(f"human_confirmed_suggestion_proposals_323g_summary_json: {output_dir / 'human_confirmed_suggestion_proposals_323g_summary.json'}")
            return 0
        if not safe_subset_dir.exists():
            _blocked_prepare_result(output_dir, "BLOCKED_MISSING_323D_DIR")
            print(f"human_confirmed_suggestion_proposals_323g_summary_json: {output_dir / 'human_confirmed_suggestion_proposals_323g_summary.json'}")
            return 0

        inputs = load_human_confirmed_suggestion_inputs(
            raw_response_validation_dir=raw_response_validation_dir,
            safe_subset_dir=safe_subset_dir,
            configured_run_dir=configured_run_dir if configured_run_dir.exists() else None,
        )
        artifacts = build_human_confirmed_suggestion_prepare(
            inputs=inputs,
            raw_response_validation_dir=raw_response_validation_dir,
            safe_subset_dir=safe_subset_dir,
            configured_run_dir=configured_run_dir if configured_run_dir.exists() else None,
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
        summary["decision"] = EXPECTED_323G_PREPARE_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_323G_PREPARE_NOT_READY
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
        write_excel(
            output_paths["workbook_path"],
            {
                "summary": pd.DataFrame([summary]),
                "confirmation_records": artifacts["confirmation_records_df"],
                "alias_suggestions": artifacts["alias_suggestions_df"],
                "scope_suggestions": artifacts["scope_suggestions_df"],
                "qa_checks": qa_df,
                "review_instructions": artifacts["review_instructions_df"],
            },
            mode="prepare",
        )

        print(f"human_confirmed_suggestion_proposals_323g_workbook: {output_paths['workbook_path']}")
        print(f"human_confirmed_suggestion_proposals_323g_summary_json: {output_paths['summary_json_path']}")
        print(f"human_confirmed_suggestion_proposals_323g_qa_json: {output_paths['qa_json_path']}")
        print(f"human_confirmed_suggestion_proposals_323g_proposal_package_json: {output_paths['package_json_path']}")
        print(f"human_confirmed_suggestion_proposals_323g_alias_suggestions_xlsx: {output_paths['alias_xlsx_path']}")
        print(f"human_confirmed_suggestion_proposals_323g_scope_suggestions_xlsx: {output_paths['scope_xlsx_path']}")
        print(f"human_confirmed_suggestion_proposals_323g_review_instructions_md: {output_paths['instructions_path']}")
        for key in [
            "accepted_suggestion_count",
            "alias_accepted_suggestion_count",
            "scope_accepted_suggestion_count",
            "confirmation_record_count",
            "qa_pass_count",
            "qa_warn_count",
            "qa_fail_count",
            "decision",
        ]:
            print(f"{key}: {summary.get(key, '')}")
        print(f"decision_distribution: {summary.get('decision_distribution', {})}")
        return 0

    reviewed_workbook = Path(args.reviewed_confirmation_workbook) if args.reviewed_confirmation_workbook else Path()
    if not raw_response_validation_dir.exists():
        _blocked_reviewed_result(output_dir, "BLOCKED_MISSING_323F_DIR")
        print(f"human_confirmed_suggestion_proposals_323g_reviewed_summary_json: {output_dir / 'human_confirmed_suggestion_proposals_323g_reviewed_summary.json'}")
        return 0
    if not reviewed_workbook.exists():
        _blocked_reviewed_result(output_dir, "BLOCKED_MISSING_REVIEWED_CONFIRMATION_WORKBOOK")
        print(f"human_confirmed_suggestion_proposals_323g_reviewed_summary_json: {output_dir / 'human_confirmed_suggestion_proposals_323g_reviewed_summary.json'}")
        return 0

    inputs = load_human_confirmed_suggestion_inputs(
        raw_response_validation_dir=raw_response_validation_dir,
        safe_subset_dir=safe_subset_dir if safe_subset_dir.exists() else DEFAULT_SAFE_SUBSET_DIR,
        configured_run_dir=configured_run_dir if configured_run_dir.exists() else None,
    )
    artifacts = build_human_confirmed_suggestion_validate_reviewed(
        reviewed_workbook=reviewed_workbook,
        raw_response_validation_summary=inputs["summary_323f"],
    )
    output_paths = _write_reviewed_outputs(output_dir, artifacts)
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
    summary["decision"] = EXPECTED_323G_REVIEWED_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_323G_REVIEWED_NOT_READY
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
    write_excel(
        output_paths["workbook_path"],
        {
            "reviewed_summary": pd.DataFrame([summary]),
            "confirmed_suggestions": artifacts["confirmed_df"],
            "rejected_suggestions": artifacts["rejected_df"],
            "needs_more_info": artifacts["needs_more_info_df"],
            "all_reviewed": artifacts["all_reviewed_df"],
            "reviewed_qa": qa_df,
        },
        mode="validate-reviewed",
    )

    print(f"human_confirmed_suggestion_proposals_323g_reviewed_workbook: {output_paths['workbook_path']}")
    print(f"human_confirmed_suggestion_proposals_323g_reviewed_summary_json: {output_paths['summary_json_path']}")
    print(f"human_confirmed_suggestion_proposals_323g_reviewed_qa_json: {output_paths['qa_json_path']}")
    print(f"human_confirmed_suggestion_proposals_323g_human_confirmed_plan_json: {output_paths['plan_json_path']}")
    for key in [
        "confirmation_record_count",
        "confirmed_suggestion_count",
        "rejected_suggestion_count",
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
