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

from datefac.semantic.alias_response_schema_validation_325g import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REQUEST_DIR,
    DEFAULT_RESPONSE_COLLECTION_DIR,
    NOT_READY_DECISION,
    build_alias_response_schema_validation_325g,
    load_alias_response_schema_validation_325g_inputs,
)
from datefac.semantic.alias_response_schema_validation_325g_report import (  # noqa: E402
    WORKBOOK_SHEET_ORDER,
    alias_response_schema_validation_325g_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325G",
        "output_dir": str(output_dir),
        "request_count": 0,
        "response_count": 0,
        "schema_valid_count": 0,
        "schema_invalid_count": 0,
        "accepted_for_human_confirmation_count": 0,
        "rejected_by_schema_count": 0,
        "rejected_by_deterministic_gate_count": 0,
        "rejected_alias_suggestion_count": 0,
        "needs_more_info_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": NOT_READY_DECISION,
    }
    write_json(output_dir / "alias_response_schema_validation_325g_summary.json", summary)
    write_json(output_dir / "alias_response_schema_validation_325g_qa.json", {"qa_fail_count": 1, "blocking_reasons": [code], "checks": []})
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325G alias response schema validation gate.")
    parser.add_argument("--response-collection-dir", default=str(DEFAULT_RESPONSE_COLLECTION_DIR))
    parser.add_argument("--request-dir", default=str(DEFAULT_REQUEST_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    response_collection_dir = Path(args.response_collection_dir)
    request_dir = Path(args.request_dir)
    output_dir = Path(args.output_dir)
    required = [
        response_collection_dir / "alias_adjudicator_response_collection_325f_summary.json",
        response_collection_dir / "alias_adjudicator_response_collection_325f_qa.json",
        response_collection_dir / "alias_adjudicator_response_collection_325f_raw_responses.jsonl",
        request_dir / "alias_safe_adjudicator_request_325e_request_package.json",
    ]
    if not all(path.exists() for path in required):
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_325F_OR_325E_ARTIFACTS")
        print(f"qa_fail_count: {summary.get('qa_fail_count')}")
        print(f"decision: {summary.get('decision')}")
        return 0

    inputs = load_alias_response_schema_validation_325g_inputs(response_collection_dir, request_dir)
    artifacts = build_alias_response_schema_validation_325g(inputs, response_collection_dir, request_dir)
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "alias_response_schema_validation_325g_summary.json", summary)
    write_json(output_dir / "alias_response_schema_validation_325g_qa.json", artifacts["qa_json"])
    write_json(output_dir / "alias_response_schema_validation_325g_validated_suggestions.json", artifacts["validated_suggestions"])
    write_json(output_dir / "alias_response_schema_validation_325g_no_apply_proof.json", artifacts["no_apply_proof"])
    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "validated_suggestions": artifacts["validated_df"],
        "accepted_for_human_confirmation": artifacts["accepted_df"],
        "rejected_or_needs_more_info": artifacts["rejected_or_needs_more_info_df"],
        "deterministic_gate_report": artifacts["gate_failures_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    write_excel(output_dir / "alias_response_schema_validation_325g_validated_suggestions.xlsx", sheets, WORKBOOK_SHEET_ORDER)
    write_excel(
        output_dir / "alias_response_schema_validation_325g_accepted_for_human_confirmation.xlsx",
        {"summary": sheets["summary"], "accepted_for_human_confirmation": artifacts["accepted_df"], "qa_checks": artifacts["qa_checks_df"]},
        ["summary", "accepted_for_human_confirmation", "qa_checks"],
    )
    write_excel(
        output_dir / "alias_response_schema_validation_325g_rejected_or_needs_more_info.xlsx",
        {"summary": sheets["summary"], "rejected_or_needs_more_info": artifacts["rejected_or_needs_more_info_df"], "qa_checks": artifacts["qa_checks_df"]},
        ["summary", "rejected_or_needs_more_info", "qa_checks"],
    )
    write_excel(
        output_dir / "alias_response_schema_validation_325g_deterministic_gate_report.xlsx",
        {"summary": sheets["summary"], "deterministic_gate_report": artifacts["gate_failures_df"], "schema_invalid": artifacts["schema_invalid_df"], "qa_checks": artifacts["qa_checks_df"]},
        ["summary", "deterministic_gate_report", "schema_invalid", "qa_checks"],
    )
    (output_dir / "alias_response_schema_validation_325g_report.md").write_text(
        alias_response_schema_validation_325g_markdown(summary),
        encoding="utf-8",
    )

    print(f"output_dir: {output_dir}")
    for key in [
        "request_count",
        "response_count",
        "schema_valid_count",
        "schema_invalid_count",
        "accepted_for_human_confirmation_count",
        "rejected_by_schema_count",
        "rejected_by_deterministic_gate_count",
        "rejected_alias_suggestion_count",
        "needs_more_info_count",
        "deterministic_gate_failure_count",
        "official_overlap_count",
        "target_conflict_count",
        "adjusted_metric_mismatch_count",
        "diluted_eps_mismatch_count",
        "official_assets_modified",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
