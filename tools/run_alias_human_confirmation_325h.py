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

from datefac.semantic.alias_human_confirmation_325h import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_OUTPUT_DIR,
    DEFAULT_SCHEMA_VALIDATION_DIR,
    NOT_READY_DECISION,
    build_alias_human_confirmation_325h_prepare,
    build_alias_human_confirmation_325h_reviewed,
    load_alias_human_confirmation_325h_inputs,
    load_reviewed_confirmation_records,
)
from datefac.semantic.alias_human_confirmation_325h_report import (  # noqa: E402
    alias_human_confirmation_325h_markdown,
    write_excel,
    write_json,
)


def _blocked_result(output_dir: Path, mode: str, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "325H",
        "mode": mode,
        "output_dir": str(output_dir),
        "confirmation_record_count": 0,
        "pending_count": 0,
        "confirmed_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": NOT_READY_DECISION,
    }
    write_json(output_dir / "alias_human_confirmation_325h_summary.json", summary)
    write_json(output_dir / "alias_human_confirmation_325h_qa.json", {"qa_fail_count": 1, "blocking_reasons": [code], "checks": []})
    return summary


def _write_prepare(output_dir: Path, artifacts: Dict[str, Any]) -> None:
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    write_json(output_dir / "alias_human_confirmation_325h_summary.json", summary)
    write_json(output_dir / "alias_human_confirmation_325h_qa.json", artifacts["qa_json"])
    write_json(output_dir / "alias_human_confirmation_325h_package.json", artifacts["package"])
    write_json(output_dir / "alias_human_confirmation_325h_no_apply_proof.json", artifacts["no_apply_proof"])
    write_excel(
        output_dir / "alias_human_confirmation_325h_workbook.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "confirmation_records": artifacts["records_df"],
            "confirmed": artifacts["confirmed_df"],
            "rejected_or_needs_more_info": artifacts["rejected_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    (output_dir / "alias_human_confirmation_325h_review_notes.md").write_text(alias_human_confirmation_325h_markdown(summary), encoding="utf-8")


def _write_reviewed(output_dir: Path, artifacts: Dict[str, Any]) -> None:
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    write_json(output_dir / "alias_human_confirmation_325h_reviewed_summary.json", summary)
    write_json(output_dir / "alias_human_confirmation_325h_reviewed_qa.json", artifacts["qa_json"])
    write_json(output_dir / "alias_human_confirmation_325h_human_confirmed_plan.json", artifacts["package"])
    write_json(output_dir / "alias_human_confirmation_325h_no_apply_proof.json", artifacts["no_apply_proof"])
    write_excel(
        output_dir / "alias_human_confirmation_325h_reviewed_workbook.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "confirmation_records": artifacts["records_df"],
            "confirmed": artifacts["confirmed_df"],
            "rejected_or_needs_more_info": artifacts["rejected_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    write_excel(
        output_dir / "alias_human_confirmation_325h_rejected_or_needs_more_info.xlsx",
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "rejected_or_needs_more_info": artifacts["rejected_df"],
            "confirmation_records": pd.DataFrame(),
            "confirmed": pd.DataFrame(),
            "qa_checks": artifacts["qa_checks_df"],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 325H alias human confirmation workflow.")
    parser.add_argument("--mode", choices=["prepare", "validate-reviewed"], default="prepare")
    parser.add_argument("--schema-validation-dir", default=str(DEFAULT_SCHEMA_VALIDATION_DIR))
    parser.add_argument("--reviewed-workbook", default="")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    mode = args.mode
    schema_validation_dir = Path(args.schema_validation_dir)
    output_dir = Path(args.output_dir) if args.output_dir else (DEFAULT_REVIEWED_OUTPUT_DIR if mode == "validate-reviewed" else DEFAULT_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    required = [
        schema_validation_dir / "alias_response_schema_validation_325g_summary.json",
        schema_validation_dir / "alias_response_schema_validation_325g_qa.json",
        schema_validation_dir / "alias_response_schema_validation_325g_validated_suggestions.json",
    ]
    if mode == "validate-reviewed":
        reviewed = Path(args.reviewed_workbook)
        required.append(reviewed)
    else:
        reviewed = Path()
    if not all(path.exists() for path in required):
        summary = _blocked_result(output_dir, mode, "BLOCKED_MISSING_325G_OR_REVIEWED_ARTIFACTS")
        print(f"qa_fail_count: {summary.get('qa_fail_count')}")
        print(f"decision: {summary.get('decision')}")
        return 0

    inputs = load_alias_human_confirmation_325h_inputs(schema_validation_dir)
    if mode == "prepare":
        artifacts = build_alias_human_confirmation_325h_prepare(inputs)
        _write_prepare(output_dir, artifacts)
    else:
        artifacts = build_alias_human_confirmation_325h_reviewed(inputs, load_reviewed_confirmation_records(reviewed))
        _write_reviewed(output_dir, artifacts)

    summary = artifacts["summary"]
    print(f"output_dir: {output_dir}")
    for key in [
        "mode",
        "confirmation_record_count",
        "pending_count",
        "confirmed_count",
        "rejected_count",
        "needs_more_info_count",
        "validate_reviewed_mode_implemented",
        "official_assets_modified",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
