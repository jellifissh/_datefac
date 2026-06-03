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

from datefac.semantic.raw_response_schema_validation import (
    DEFAULT_CONFIGURED_RUN_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SAFE_SUBSET_DIR,
    EXPECTED_323F_NOT_READY,
    build_raw_response_schema_validation,
    load_raw_response_schema_validation_inputs,
)
from datefac.semantic.raw_response_schema_validation_report import (
    REVIEW_WORKBOOK_SHEET_ORDER,
    raw_response_schema_validation_report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323F",
        "output_dir": str(output_dir),
        "configured_run_dir": "",
        "safe_subset_dir": "",
        "request_count": 0,
        "response_count": 0,
        "schema_valid_count": 0,
        "schema_invalid_count": 0,
        "accepted_suggestion_count": 0,
        "rejected_suggestion_count": 0,
        "needs_more_info_count": 0,
        "deterministic_gate_failure_count": 0,
        "highest_priority_accepted_examples": [],
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323F_NOT_READY,
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
        "review_package": pd.DataFrame(),
        "schema_invalid": pd.DataFrame(),
        "gate_failures": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }

    write_json(output_dir / "raw_response_schema_validation_323f_summary.json", summary)
    write_json(output_dir / "raw_response_schema_validation_323f_qa.json", qa_json)
    write_json(output_dir / "raw_response_schema_validation_323f_accepted_suggestions.json", {"accepted_suggestions": []})
    write_json(output_dir / "raw_response_schema_validation_323f_rejected_suggestions.json", {"rejected_suggestions": []})
    write_json(output_dir / "raw_response_schema_validation_323f_needs_more_info.json", {"needs_more_info": []})
    write_json(output_dir / "raw_response_schema_validation_323f_no_apply_proof.json", {"decision": "blocked_input"})
    write_jsonl(output_dir / "raw_response_schema_validation_323f_validated_responses.jsonl", [])
    write_excel(
        output_dir / "raw_response_schema_validation_323f_schema_invalid.xlsx",
        {"summary": pd.DataFrame([summary]), "items": pd.DataFrame(), "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}])},
        ["summary", "items", "qa_checks"],
    )
    write_excel(
        output_dir / "raw_response_schema_validation_323f_gate_failures.xlsx",
        {"summary": pd.DataFrame([summary]), "items": pd.DataFrame(), "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}])},
        ["summary", "items", "qa_checks"],
    )
    write_excel(
        output_dir / "raw_response_schema_validation_323f_review_package.xlsx",
        sheets,
        REVIEW_WORKBOOK_SHEET_ORDER,
    )
    (output_dir / "raw_response_schema_validation_323f_notes.md").write_text(
        raw_response_schema_validation_report_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323F raw response schema validation and deterministic gate.")
    parser.add_argument("--configured-run-dir", default=str(DEFAULT_CONFIGURED_RUN_DIR))
    parser.add_argument("--safe-subset-dir", default=str(DEFAULT_SAFE_SUBSET_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    configured_run_dir = Path(args.configured_run_dir)
    safe_subset_dir = Path(args.safe_subset_dir)
    output_dir = Path(args.output_dir)

    if not configured_run_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_323E_CONFIGURED_RUN_DIR")
        print(f"raw_response_schema_validation_323f_summary_json: {output_dir / 'raw_response_schema_validation_323f_summary.json'}")
        return 0
    if not safe_subset_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_323D_SAFE_SUBSET_DIR")
        print(f"raw_response_schema_validation_323f_summary_json: {output_dir / 'raw_response_schema_validation_323f_summary.json'}")
        return 0

    inputs = load_raw_response_schema_validation_inputs(
        configured_run_dir=configured_run_dir,
        safe_subset_dir=safe_subset_dir,
    )
    artifacts = build_raw_response_schema_validation(
        inputs=inputs,
        configured_run_dir=configured_run_dir,
        safe_subset_dir=safe_subset_dir,
    )

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "raw_response_schema_validation_323f_summary.json"
    qa_path = output_dir / "raw_response_schema_validation_323f_qa.json"
    validated_path = output_dir / "raw_response_schema_validation_323f_validated_responses.jsonl"
    accepted_path = output_dir / "raw_response_schema_validation_323f_accepted_suggestions.json"
    rejected_path = output_dir / "raw_response_schema_validation_323f_rejected_suggestions.json"
    needs_more_info_path = output_dir / "raw_response_schema_validation_323f_needs_more_info.json"
    schema_invalid_path = output_dir / "raw_response_schema_validation_323f_schema_invalid.xlsx"
    gate_failures_path = output_dir / "raw_response_schema_validation_323f_gate_failures.xlsx"
    review_package_path = output_dir / "raw_response_schema_validation_323f_review_package.xlsx"
    notes_path = output_dir / "raw_response_schema_validation_323f_notes.md"
    no_apply_proof_path = output_dir / "raw_response_schema_validation_323f_no_apply_proof.json"

    review_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "review_package": artifacts["review_package_df"],
        "schema_invalid": artifacts["schema_invalid_df"],
        "gate_failures": artifacts["gate_failures_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    simple_schema_invalid = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "items": artifacts["schema_invalid_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    simple_gate_failures = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "items": artifacts["gate_failures_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_json(summary_path, summary)
    write_json(qa_path, artifacts["qa_json"])
    write_json(accepted_path, artifacts["accepted_suggestions_json"])
    write_json(rejected_path, artifacts["rejected_suggestions_json"])
    write_json(needs_more_info_path, artifacts["needs_more_info_json"])
    write_json(no_apply_proof_path, artifacts["no_apply_proof_json"])
    write_jsonl(validated_path, artifacts["validated_responses"])
    write_excel(schema_invalid_path, simple_schema_invalid, ["summary", "items", "qa_checks"])
    write_excel(gate_failures_path, simple_gate_failures, ["summary", "items", "qa_checks"])
    write_excel(review_package_path, review_sheets, REVIEW_WORKBOOK_SHEET_ORDER)
    notes_path.write_text(artifacts["notes_md"], encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            summary_path,
            qa_path,
            validated_path,
            accepted_path,
            rejected_path,
            needs_more_info_path,
            schema_invalid_path,
            gate_failures_path,
            review_package_path,
            notes_path,
            no_apply_proof_path,
        ]
    )

    qa_df = artifacts["qa_checks_df"].copy()
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output_artifact_presence",
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
    if summary["qa_fail_count"] > 0:
        summary["decision"] = EXPECTED_323F_NOT_READY
    elif summary["accepted_suggestion_count"] > 0:
        summary["decision"] = "RAW_RESPONSE_SCHEMA_VALIDATION_323F_READY_FOR_HUMAN_CONFIRMED_SUGGESTION_PROPOSALS"
    else:
        summary["decision"] = "RAW_RESPONSE_SCHEMA_VALIDATION_323F_NO_ACCEPTED_SUGGESTIONS"

    review_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    review_sheets["qa_checks"] = qa_df
    simple_schema_invalid["summary"] = pd.DataFrame([summary]).fillna("")
    simple_schema_invalid["qa_checks"] = qa_df
    simple_gate_failures["summary"] = pd.DataFrame([summary]).fillna("")
    simple_gate_failures["qa_checks"] = qa_df

    write_json(summary_path, summary)
    write_json(
        qa_path,
        {
            "qa_pass_count": summary["qa_pass_count"],
            "qa_warn_count": summary["qa_warn_count"],
            "qa_fail_count": summary["qa_fail_count"],
            "blocking_reasons": summary["blocking_reasons"],
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    write_excel(schema_invalid_path, simple_schema_invalid, ["summary", "items", "qa_checks"])
    write_excel(gate_failures_path, simple_gate_failures, ["summary", "items", "qa_checks"])
    write_excel(review_package_path, review_sheets, REVIEW_WORKBOOK_SHEET_ORDER)
    notes_path.write_text(raw_response_schema_validation_report_markdown(summary), encoding="utf-8")

    print(f"raw_response_schema_validation_323f_summary_json: {summary_path}")
    print(f"raw_response_schema_validation_323f_qa_json: {qa_path}")
    print(f"raw_response_schema_validation_323f_validated_responses_jsonl: {validated_path}")
    print(f"raw_response_schema_validation_323f_accepted_suggestions_json: {accepted_path}")
    print(f"raw_response_schema_validation_323f_rejected_suggestions_json: {rejected_path}")
    print(f"raw_response_schema_validation_323f_needs_more_info_json: {needs_more_info_path}")
    print(f"raw_response_schema_validation_323f_schema_invalid_xlsx: {schema_invalid_path}")
    print(f"raw_response_schema_validation_323f_gate_failures_xlsx: {gate_failures_path}")
    print(f"raw_response_schema_validation_323f_review_package_xlsx: {review_package_path}")
    print(f"raw_response_schema_validation_323f_no_apply_proof_json: {no_apply_proof_path}")
    print(f"raw_response_schema_validation_323f_notes_md: {notes_path}")
    for key in [
        "request_count",
        "response_count",
        "schema_valid_count",
        "schema_invalid_count",
        "accepted_suggestion_count",
        "rejected_suggestion_count",
        "needs_more_info_count",
        "deterministic_gate_failure_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
