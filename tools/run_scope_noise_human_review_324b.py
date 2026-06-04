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

from datefac.semantic.scope_noise_human_review_324b import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_OUTPUT_DIR,
    DEFAULT_SCOPE_REFINEMENT_324A_DIR,
    EXPECTED_324B_PREPARE_DECISION,
    EXPECTED_324B_PREPARE_NOT_READY,
    EXPECTED_324B_REVIEWED_NOT_READY,
    build_scope_noise_human_review_324b_prepare,
    build_scope_noise_human_review_324b_validate_reviewed,
    load_scope_noise_human_review_324b_inputs,
)
from datefac.semantic.scope_noise_human_review_324b_report import (  # noqa: E402
    scope_noise_human_review_324b_markdown,
    write_excel,
    write_json,
)


def _blocked_prepare_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324B",
        "mode": "prepare",
        "output_dir": str(output_dir),
        "review_record_count": 0,
        "pending_count": 0,
        "confirmed_scope_noise_count": 0,
        "rejected_scope_noise_count": 0,
        "needs_more_info_count": 0,
        "escalate_to_adjudicator_count": 0,
        "risk_flags_carried_forward": "",
        "official_assets_not_modified_confirmed": True,
        "human_review_only_no_apply_confirmed": True,
        "validate_reviewed_mode_implemented": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_324B_PREPARE_NOT_READY,
    }
    workbook_path = output_dir / "scope_noise_human_review_324b_workbook.xlsx"
    summary_json_path = output_dir / "scope_noise_human_review_324b_summary.json"
    qa_json_path = output_dir / "scope_noise_human_review_324b_qa.json"
    package_json_path = output_dir / "scope_noise_human_review_324b_review_package.json"
    empty = pd.DataFrame()
    write_excel(
        workbook_path,
        {
            "summary": pd.DataFrame([summary]),
            "scope_review_records": empty,
            "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
            "review_instructions": pd.DataFrame(
                [{"section": "blocked_input", "instruction": "Required input is missing."}]
            ),
        },
        mode="prepare",
    )
    write_json(summary_json_path, summary)
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
    write_json(
        package_json_path,
        {"stage": "324B", "mode": "prepare", "decision": EXPECTED_324B_PREPARE_NOT_READY, "scope_review_records": []},
    )
    (output_dir / "scope_noise_human_review_324b_review_instructions.md").write_text(
        scope_noise_human_review_324b_markdown(summary),
        encoding="utf-8",
    )
    return summary


def _blocked_reviewed_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324B",
        "mode": "validate-reviewed",
        "output_dir": str(output_dir),
        "review_record_count": 0,
        "pending_count": 0,
        "confirmed_scope_noise_count": 0,
        "rejected_scope_noise_count": 0,
        "needs_more_info_count": 0,
        "escalate_to_adjudicator_count": 0,
        "risk_flags_carried_forward": "",
        "official_assets_not_modified_confirmed": True,
        "human_review_only_no_apply_confirmed": True,
        "validate_reviewed_mode_implemented": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_324B_REVIEWED_NOT_READY,
    }
    workbook_path = output_dir / "scope_noise_human_review_324b_reviewed_workbook.xlsx"
    summary_json_path = output_dir / "scope_noise_human_review_324b_reviewed_summary.json"
    qa_json_path = output_dir / "scope_noise_human_review_324b_reviewed_qa.json"
    routing_json_path = output_dir / "scope_noise_human_review_324b_final_routing_plan.json"
    empty = pd.DataFrame()
    write_excel(
        workbook_path,
        {
            "reviewed_summary": pd.DataFrame([summary]),
            "confirmed_scope_noise": empty,
            "escalated_to_adjudicator": empty,
            "rejected_scope_noise": empty,
            "needs_more_info": empty,
            "all_reviewed_records": empty,
            "reviewed_qa": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        },
        mode="validate-reviewed",
    )
    write_json(summary_json_path, summary)
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
    write_json(
        routing_json_path,
        {"stage": "324B", "mode": "validate-reviewed", "decision": EXPECTED_324B_REVIEWED_NOT_READY},
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 324B scope noise human review workflow.")
    parser.add_argument("--mode", choices=["prepare", "validate-reviewed"], default="prepare")
    parser.add_argument("--scope-refinement-dir", default=str(DEFAULT_SCOPE_REFINEMENT_324A_DIR))
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--reviewed-workbook", default="")
    args = parser.parse_args()

    scope_refinement_dir = Path(args.scope_refinement_dir)
    output_dir = Path(
        args.output_dir
        or (str(DEFAULT_OUTPUT_DIR) if args.mode == "prepare" else str(DEFAULT_REVIEWED_OUTPUT_DIR))
    )

    if args.mode == "prepare":
        required = [
            scope_refinement_dir / "scope_noise_refinement_324a_summary.json",
            scope_refinement_dir / "scope_noise_refinement_324a_qa.json",
            scope_refinement_dir / "scope_noise_refinement_324a_refined_batch.json",
        ]
        if not all(path.exists() for path in required):
            _blocked_prepare_result(output_dir, "BLOCKED_MISSING_324A_SCOPE_REFINEMENT_ARTIFACTS")
            print(f"scope_noise_human_review_324b_summary_json: {output_dir / 'scope_noise_human_review_324b_summary.json'}")
            return 0

        inputs = load_scope_noise_human_review_324b_inputs(scope_refinement_dir=scope_refinement_dir)
        artifacts = build_scope_noise_human_review_324b_prepare(inputs)
        summary = artifacts["summary"]
        summary["output_dir"] = str(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        workbook_path = output_dir / "scope_noise_human_review_324b_workbook.xlsx"
        summary_json_path = output_dir / "scope_noise_human_review_324b_summary.json"
        qa_json_path = output_dir / "scope_noise_human_review_324b_qa.json"
        package_json_path = output_dir / "scope_noise_human_review_324b_review_package.json"
        instructions_path = output_dir / "scope_noise_human_review_324b_review_instructions.md"

        write_excel(
            workbook_path,
            {
                "summary": pd.DataFrame([summary]),
                "scope_review_records": artifacts["scope_review_records_df"],
                "qa_checks": artifacts["qa_checks_df"],
                "review_instructions": artifacts["review_instructions_df"],
            },
            mode="prepare",
        )
        write_json(summary_json_path, summary)
        write_json(qa_json_path, artifacts["qa_json"])
        write_json(package_json_path, artifacts["review_package_json"])
        instructions_path.write_text(scope_noise_human_review_324b_markdown(summary), encoding="utf-8")

        output_files_written = all(
            path.exists()
            for path in [workbook_path, summary_json_path, qa_json_path, package_json_path, instructions_path]
        )
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
        summary["decision"] = (
            EXPECTED_324B_PREPARE_DECISION
            if summary["qa_fail_count"] == 0
            else EXPECTED_324B_PREPARE_NOT_READY
        )
        artifacts["review_package_json"]["decision"] = summary["decision"]

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
        write_json(package_json_path, artifacts["review_package_json"])
        write_excel(
            workbook_path,
            {
                "summary": pd.DataFrame([summary]),
                "scope_review_records": artifacts["scope_review_records_df"],
                "qa_checks": qa_df,
                "review_instructions": artifacts["review_instructions_df"],
            },
            mode="prepare",
        )
        instructions_path.write_text(scope_noise_human_review_324b_markdown(summary), encoding="utf-8")

        print(f"scope_noise_human_review_324b_workbook: {workbook_path}")
        print(f"scope_noise_human_review_324b_summary_json: {summary_json_path}")
        print(f"scope_noise_human_review_324b_qa_json: {qa_json_path}")
        print(f"scope_noise_human_review_324b_review_package_json: {package_json_path}")
        print(f"scope_noise_human_review_324b_review_instructions_md: {instructions_path}")
        for key in [
            "review_record_count",
            "pending_count",
            "confirmed_scope_noise_count",
            "rejected_scope_noise_count",
            "needs_more_info_count",
            "escalate_to_adjudicator_count",
            "risk_flags_carried_forward",
            "qa_pass_count",
            "qa_warn_count",
            "qa_fail_count",
            "decision",
        ]:
            print(f"{key}: {summary.get(key, '')}")
        return 0

    reviewed_workbook = Path(args.reviewed_workbook) if args.reviewed_workbook else (
        scope_refinement_dir.parent / "scope_noise_human_review_324b" / "scope_noise_human_review_324b_workbook.xlsx"
    )
    summary_path = scope_refinement_dir / "scope_noise_refinement_324a_summary.json"
    if not summary_path.exists():
        _blocked_reviewed_result(output_dir, "BLOCKED_MISSING_324A_SUMMARY")
        print(f"scope_noise_human_review_324b_reviewed_summary_json: {output_dir / 'scope_noise_human_review_324b_reviewed_summary.json'}")
        return 0
    if not reviewed_workbook.exists():
        _blocked_reviewed_result(output_dir, "BLOCKED_MISSING_REVIEWED_WORKBOOK")
        print(f"scope_noise_human_review_324b_reviewed_summary_json: {output_dir / 'scope_noise_human_review_324b_reviewed_summary.json'}")
        return 0

    summary_324a = _read_summary(summary_path)
    artifacts = build_scope_noise_human_review_324b_validate_reviewed(
        reviewed_workbook=reviewed_workbook,
        summary_324a=summary_324a,
    )
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = output_dir / "scope_noise_human_review_324b_reviewed_workbook.xlsx"
    summary_json_path = output_dir / "scope_noise_human_review_324b_reviewed_summary.json"
    qa_json_path = output_dir / "scope_noise_human_review_324b_reviewed_qa.json"
    routing_json_path = output_dir / "scope_noise_human_review_324b_final_routing_plan.json"

    write_excel(
        workbook_path,
        {
            "reviewed_summary": pd.DataFrame([summary]),
            "confirmed_scope_noise": artifacts["confirmed_df"],
            "escalated_to_adjudicator": artifacts["escalated_df"],
            "rejected_scope_noise": artifacts["rejected_df"],
            "needs_more_info": artifacts["needs_more_info_df"],
            "all_reviewed_records": artifacts["all_reviewed_df"],
            "reviewed_qa": artifacts["qa_checks_df"],
        },
        mode="validate-reviewed",
    )
    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(routing_json_path, artifacts["routing_plan_json"])

    output_files_written = all(
        path.exists() for path in [workbook_path, summary_json_path, qa_json_path, routing_json_path]
    )
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
    artifacts["routing_plan_json"]["decision"] = summary["decision"]

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
    write_json(routing_json_path, artifacts["routing_plan_json"])
    write_excel(
        workbook_path,
        {
            "reviewed_summary": pd.DataFrame([summary]),
            "confirmed_scope_noise": artifacts["confirmed_df"],
            "escalated_to_adjudicator": artifacts["escalated_df"],
            "rejected_scope_noise": artifacts["rejected_df"],
            "needs_more_info": artifacts["needs_more_info_df"],
            "all_reviewed_records": artifacts["all_reviewed_df"],
            "reviewed_qa": qa_df,
        },
        mode="validate-reviewed",
    )

    print(f"scope_noise_human_review_324b_reviewed_workbook: {workbook_path}")
    print(f"scope_noise_human_review_324b_reviewed_summary_json: {summary_json_path}")
    print(f"scope_noise_human_review_324b_reviewed_qa_json: {qa_json_path}")
    print(f"scope_noise_human_review_324b_final_routing_plan_json: {routing_json_path}")
    for key in [
        "review_record_count",
        "pending_count",
        "confirmed_scope_noise_count",
        "rejected_scope_noise_count",
        "needs_more_info_count",
        "escalate_to_adjudicator_count",
        "risk_flags_carried_forward",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


def _read_summary(path: Path) -> Dict[str, Any]:
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


if __name__ == "__main__":
    raise SystemExit(main())
