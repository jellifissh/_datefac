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

from datefac.semantic.scope_noise_human_confirmation_324f import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_OUTPUT_DIR,
    DEFAULT_SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_DIR,
    EXPECTED_324F_PREPARE_DECISION,
    EXPECTED_324F_PREPARE_NOT_READY,
    EXPECTED_324F_REVIEWED_NOT_READY,
    build_scope_noise_human_confirmation_324f_prepare,
    build_scope_noise_human_confirmation_324f_validate_reviewed,
    load_scope_noise_human_confirmation_324f_inputs,
)
from datefac.semantic.scope_noise_human_confirmation_324f_report import (  # noqa: E402
    scope_noise_human_confirmation_324f_markdown,
    write_excel,
    write_json,
)


def _read_summary(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _blocked_prepare_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324F",
        "mode": "prepare",
        "output_dir": str(output_dir),
        "confirmation_record_count": 0,
        "pending_count": 0,
        "confirmed_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "decision_distribution": {},
        "validate_reviewed_mode_implemented": True,
        "official_assets_not_modified": True,
        "human_confirmation_only_no_apply_confirmed": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_324F_PREPARE_NOT_READY,
    }
    workbook_path = output_dir / "scope_noise_human_confirmation_324f_workbook.xlsx"
    summary_json_path = output_dir / "scope_noise_human_confirmation_324f_summary.json"
    qa_json_path = output_dir / "scope_noise_human_confirmation_324f_qa.json"
    package_json_path = output_dir / "scope_noise_human_confirmation_324f_confirmation_package.json"
    instructions_path = output_dir / "scope_noise_human_confirmation_324f_review_instructions.md"
    empty = pd.DataFrame()
    write_excel(
        workbook_path,
        {
            "summary": pd.DataFrame([summary]),
            "confirmation_records": empty,
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
        {
            "stage": "324F",
            "mode": "prepare",
            "decision": EXPECTED_324F_PREPARE_NOT_READY,
            "confirmation_records": [],
        },
    )
    instructions_path.write_text(scope_noise_human_confirmation_324f_markdown(summary), encoding="utf-8")
    return summary


def _blocked_reviewed_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324F",
        "mode": "validate-reviewed",
        "output_dir": str(output_dir),
        "confirmation_record_count": 0,
        "pending_count": 0,
        "confirmed_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "invalid_decision_count": 0,
        "decision_distribution": {},
        "validate_reviewed_mode_implemented": True,
        "official_assets_not_modified": True,
        "human_confirmation_only_no_apply_confirmed": True,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_324F_REVIEWED_NOT_READY,
    }
    workbook_path = output_dir / "scope_noise_human_confirmation_324f_reviewed_workbook.xlsx"
    summary_json_path = output_dir / "scope_noise_human_confirmation_324f_reviewed_summary.json"
    qa_json_path = output_dir / "scope_noise_human_confirmation_324f_reviewed_qa.json"
    outcome_json_path = output_dir / "scope_noise_human_confirmation_324f_reviewed_outcome.json"
    empty = pd.DataFrame()
    write_excel(
        workbook_path,
        {
            "reviewed_summary": pd.DataFrame([summary]),
            "confirmed_records": empty,
            "rejected_records": empty,
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
        outcome_json_path,
        {"stage": "324F", "mode": "validate-reviewed", "decision": EXPECTED_324F_REVIEWED_NOT_READY},
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 324F scope-noise human confirmation workflow.")
    parser.add_argument("--mode", choices=["prepare", "validate-reviewed"], default="prepare")
    parser.add_argument(
        "--scope-noise-response-schema-validation-dir",
        default=str(DEFAULT_SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_324E_DIR),
    )
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--reviewed-workbook", default="")
    args = parser.parse_args()

    scope_noise_response_schema_validation_dir = Path(
        args.scope_noise_response_schema_validation_dir
    )
    output_dir = Path(
        args.output_dir
        or (
            str(DEFAULT_OUTPUT_DIR)
            if args.mode == "prepare"
            else str(DEFAULT_REVIEWED_OUTPUT_DIR)
        )
    )

    if args.mode == "prepare":
        required = [
            scope_noise_response_schema_validation_dir
            / "scope_noise_response_schema_validation_324e_summary.json",
            scope_noise_response_schema_validation_dir
            / "scope_noise_response_schema_validation_324e_qa.json",
            scope_noise_response_schema_validation_dir
            / "scope_noise_response_schema_validation_324e_accepted_for_human_confirmation.json",
        ]
        if not all(path.exists() for path in required):
            _blocked_prepare_result(output_dir, "BLOCKED_MISSING_324E_SCOPE_NOISE_RESPONSE_SCHEMA_VALIDATION_ARTIFACTS")
            print(
                "scope_noise_human_confirmation_324f_summary_json: "
                f"{output_dir / 'scope_noise_human_confirmation_324f_summary.json'}"
            )
            return 0

        inputs = load_scope_noise_human_confirmation_324f_inputs(
            scope_noise_response_schema_validation_dir=scope_noise_response_schema_validation_dir
        )
        artifacts = build_scope_noise_human_confirmation_324f_prepare(inputs)
        summary = artifacts["summary"]
        summary["output_dir"] = str(output_dir)
        summary["scope_noise_response_schema_validation_dir"] = str(
            scope_noise_response_schema_validation_dir
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        workbook_path = output_dir / "scope_noise_human_confirmation_324f_workbook.xlsx"
        summary_json_path = output_dir / "scope_noise_human_confirmation_324f_summary.json"
        qa_json_path = output_dir / "scope_noise_human_confirmation_324f_qa.json"
        package_json_path = output_dir / "scope_noise_human_confirmation_324f_confirmation_package.json"
        instructions_path = output_dir / "scope_noise_human_confirmation_324f_review_instructions.md"

        write_excel(
            workbook_path,
            {
                "summary": pd.DataFrame([summary]),
                "confirmation_records": artifacts["confirmation_records_df"],
                "qa_checks": artifacts["qa_checks_df"],
                "review_instructions": artifacts["review_instructions_df"],
            },
            mode="prepare",
        )
        write_json(summary_json_path, summary)
        write_json(qa_json_path, artifacts["qa_json"])
        write_json(package_json_path, artifacts["confirmation_package_json"])
        instructions_path.write_text(scope_noise_human_confirmation_324f_markdown(summary), encoding="utf-8")

        output_files_written = all(
            path.exists()
            for path in [
                workbook_path,
                summary_json_path,
                qa_json_path,
                package_json_path,
                instructions_path,
            ]
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
        summary["blocking_reasons"] = (
            qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
            if not qa_df.empty
            else []
        )
        summary["decision"] = (
            EXPECTED_324F_PREPARE_DECISION
            if summary["qa_fail_count"] == 0
            else EXPECTED_324F_PREPARE_NOT_READY
        )
        artifacts["confirmation_package_json"]["decision"] = summary["decision"]

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
        write_json(package_json_path, artifacts["confirmation_package_json"])
        write_excel(
            workbook_path,
            {
                "summary": pd.DataFrame([summary]),
                "confirmation_records": artifacts["confirmation_records_df"],
                "qa_checks": qa_df,
                "review_instructions": artifacts["review_instructions_df"],
            },
            mode="prepare",
        )
        instructions_path.write_text(scope_noise_human_confirmation_324f_markdown(summary), encoding="utf-8")

        print(f"scope_noise_human_confirmation_324f_workbook: {workbook_path}")
        print(f"scope_noise_human_confirmation_324f_summary_json: {summary_json_path}")
        print(f"scope_noise_human_confirmation_324f_qa_json: {qa_json_path}")
        print(f"scope_noise_human_confirmation_324f_confirmation_package_json: {package_json_path}")
        print(f"scope_noise_human_confirmation_324f_review_instructions_md: {instructions_path}")
        for key in [
            "confirmation_record_count",
            "pending_count",
            "confirmed_count",
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
        scope_noise_response_schema_validation_dir.parent
        / "scope_noise_human_confirmation_324f"
        / "scope_noise_human_confirmation_324f_workbook.xlsx"
    )
    summary_path = (
        scope_noise_response_schema_validation_dir
        / "scope_noise_response_schema_validation_324e_summary.json"
    )
    if not summary_path.exists():
        _blocked_reviewed_result(output_dir, "BLOCKED_MISSING_324E_SUMMARY")
        print(
            "scope_noise_human_confirmation_324f_reviewed_summary_json: "
            f"{output_dir / 'scope_noise_human_confirmation_324f_reviewed_summary.json'}"
        )
        return 0
    if not reviewed_workbook.exists():
        _blocked_reviewed_result(output_dir, "BLOCKED_MISSING_REVIEWED_WORKBOOK")
        print(
            "scope_noise_human_confirmation_324f_reviewed_summary_json: "
            f"{output_dir / 'scope_noise_human_confirmation_324f_reviewed_summary.json'}"
        )
        return 0

    summary_324e = _read_summary(summary_path)
    artifacts = build_scope_noise_human_confirmation_324f_validate_reviewed(
        reviewed_workbook=reviewed_workbook,
        summary_324e=summary_324e,
    )
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook_path = output_dir / "scope_noise_human_confirmation_324f_reviewed_workbook.xlsx"
    summary_json_path = output_dir / "scope_noise_human_confirmation_324f_reviewed_summary.json"
    qa_json_path = output_dir / "scope_noise_human_confirmation_324f_reviewed_qa.json"
    outcome_json_path = output_dir / "scope_noise_human_confirmation_324f_reviewed_outcome.json"

    write_excel(
        workbook_path,
        {
            "reviewed_summary": pd.DataFrame([summary]),
            "confirmed_records": artifacts["confirmed_df"],
            "rejected_records": artifacts["rejected_df"],
            "needs_more_info": artifacts["needs_more_info_df"],
            "all_reviewed_records": artifacts["all_reviewed_df"],
            "reviewed_qa": artifacts["qa_checks_df"],
        },
        mode="validate-reviewed",
    )
    write_json(summary_json_path, summary)
    write_json(qa_json_path, artifacts["qa_json"])
    write_json(outcome_json_path, artifacts["reviewed_outcome_json"])

    output_files_written = all(
        path.exists()
        for path in [workbook_path, summary_json_path, qa_json_path, outcome_json_path]
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
    summary["blocking_reasons"] = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

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
    write_excel(
        workbook_path,
        {
            "reviewed_summary": pd.DataFrame([summary]),
            "confirmed_records": artifacts["confirmed_df"],
            "rejected_records": artifacts["rejected_df"],
            "needs_more_info": artifacts["needs_more_info_df"],
            "all_reviewed_records": artifacts["all_reviewed_df"],
            "reviewed_qa": qa_df,
        },
        mode="validate-reviewed",
    )
    write_json(outcome_json_path, artifacts["reviewed_outcome_json"])

    print(f"scope_noise_human_confirmation_324f_reviewed_workbook: {workbook_path}")
    print(f"scope_noise_human_confirmation_324f_reviewed_summary_json: {summary_json_path}")
    print(f"scope_noise_human_confirmation_324f_reviewed_qa_json: {qa_json_path}")
    print(f"scope_noise_human_confirmation_324f_reviewed_outcome_json: {outcome_json_path}")
    for key in [
        "confirmation_record_count",
        "pending_count",
        "confirmed_count",
        "rejected_count",
        "needs_more_info_count",
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
