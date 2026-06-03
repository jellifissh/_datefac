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

from datefac.semantic.safe_adjudicator_subset import (
    DEFAULT_BATCH_PREP_DIR,
    DEFAULT_CANDIDATE_TEXT_REPAIR_DIR,
    DEFAULT_HUMAN_SPOT_CHECK_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RESPONSE_DIR,
    DEFAULT_SANITY_GATE_DIR,
    EXPECTED_323D_NOT_READY,
    build_safe_adjudicator_subset_prepare,
    load_safe_adjudicator_subset_inputs,
)
from datefac.semantic.safe_adjudicator_subset_report import (
    EXCLUDED_WORKBOOK_SHEET_ORDER,
    REQUEST_WORKBOOK_SHEET_ORDER,
    safe_adjudicator_subset_report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, mode: str, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "323D",
        "mode": mode,
        "output_dir": str(output_dir),
        "prepare_only": mode != "run-offline-or-configured",
        "llm_or_adjudicator_called": False,
        "input_batch_count": 0,
        "safe_request_item_count": 0,
        "alias_request_count": 0,
        "scope_request_count": 0,
        "excluded_holdout_count": 0,
        "excluded_needs_more_info_count": 0,
        "excluded_total_count": 0,
        "pending_count": 0,
        "invalid_decision_count": 0,
        "highest_priority_request_examples": [],
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_323D_NOT_READY,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    empty_df = pd.DataFrame()
    request_sheets = {
        "summary": pd.DataFrame([summary]),
        "request_items": empty_df,
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }
    excluded_sheets = {
        "summary": pd.DataFrame([summary]),
        "excluded_items": empty_df,
        "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
    }

    write_json(output_dir / "safe_adjudicator_subset_323d_summary.json", summary)
    write_json(output_dir / "safe_adjudicator_subset_323d_qa.json", qa_json)
    write_json(output_dir / "safe_adjudicator_subset_323d_request_package.json", {"request_items": []})
    write_json(output_dir / "safe_adjudicator_subset_323d_schema.json", {})
    write_json(output_dir / "safe_adjudicator_subset_323d_no_apply_proof.json", {"decision": "blocked_input"})
    write_jsonl(output_dir / "safe_adjudicator_subset_323d_request_items.jsonl", [])
    write_excel(
        output_dir / "safe_adjudicator_subset_323d_request_workbook.xlsx",
        request_sheets,
        REQUEST_WORKBOOK_SHEET_ORDER,
    )
    write_excel(
        output_dir / "safe_adjudicator_subset_323d_excluded_items.xlsx",
        excluded_sheets,
        EXCLUDED_WORKBOOK_SHEET_ORDER,
    )
    (output_dir / "safe_adjudicator_subset_323d_prompt_template.md").write_text("", encoding="utf-8")
    (output_dir / "safe_adjudicator_subset_323d_notes.md").write_text(
        safe_adjudicator_subset_report_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 323D safe adjudicator subset preparation.")
    parser.add_argument("--mode", choices=["prepare", "run-offline-or-configured"], default="prepare")
    parser.add_argument("--human-spot-check-dir", default=str(DEFAULT_HUMAN_SPOT_CHECK_DIR))
    parser.add_argument("--sanity-gate-dir", default=str(DEFAULT_SANITY_GATE_DIR))
    parser.add_argument("--batch-prep-dir", default=str(DEFAULT_BATCH_PREP_DIR))
    parser.add_argument("--candidate-text-repair-dir", default=str(DEFAULT_CANDIDATE_TEXT_REPAIR_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--response-dir", default=str(DEFAULT_RESPONSE_DIR))
    args = parser.parse_args()

    human_spot_check_dir = Path(args.human_spot_check_dir)
    sanity_gate_dir = Path(args.sanity_gate_dir)
    batch_prep_dir = Path(args.batch_prep_dir)
    candidate_text_repair_dir = Path(args.candidate_text_repair_dir)
    output_dir = Path(args.output_dir)

    required_dirs = [
        (human_spot_check_dir, "BLOCKED_MISSING_323C_HUMAN_SPOT_CHECK_DIR"),
        (sanity_gate_dir, "BLOCKED_MISSING_323C_SANITY_GATE_DIR"),
        (batch_prep_dir, "BLOCKED_MISSING_323AB_BATCH_PREP_DIR"),
        (candidate_text_repair_dir, "BLOCKED_MISSING_323AR_DIR"),
    ]
    for path, code in required_dirs:
        if not path.exists():
            _blocked_result(output_dir, args.mode, code)
            print(f"safe_adjudicator_subset_323d_summary_json: {output_dir / 'safe_adjudicator_subset_323d_summary.json'}")
            return 0

    if args.mode == "run-offline-or-configured":
        _blocked_result(output_dir, args.mode, "BLOCKED_NO_SAFE_CONFIGURED_ADJUDICATOR_WORKFLOW")
        print(f"safe_adjudicator_subset_323d_summary_json: {output_dir / 'safe_adjudicator_subset_323d_summary.json'}")
        return 0

    inputs = load_safe_adjudicator_subset_inputs(
        human_spot_check_dir=human_spot_check_dir,
        sanity_gate_dir=sanity_gate_dir,
        batch_prep_dir=batch_prep_dir,
        candidate_text_repair_dir=candidate_text_repair_dir,
    )
    artifacts = build_safe_adjudicator_subset_prepare(inputs=inputs, mode=args.mode)

    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "safe_adjudicator_subset_323d_summary.json"
    qa_path = output_dir / "safe_adjudicator_subset_323d_qa.json"
    request_jsonl_path = output_dir / "safe_adjudicator_subset_323d_request_items.jsonl"
    request_package_path = output_dir / "safe_adjudicator_subset_323d_request_package.json"
    workbook_path = output_dir / "safe_adjudicator_subset_323d_request_workbook.xlsx"
    prompt_template_path = output_dir / "safe_adjudicator_subset_323d_prompt_template.md"
    schema_path = output_dir / "safe_adjudicator_subset_323d_schema.json"
    excluded_workbook_path = output_dir / "safe_adjudicator_subset_323d_excluded_items.xlsx"
    notes_path = output_dir / "safe_adjudicator_subset_323d_notes.md"
    no_apply_proof_path = output_dir / "safe_adjudicator_subset_323d_no_apply_proof.json"

    request_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "request_items": artifacts["request_items_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }
    excluded_sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "excluded_items": artifacts["excluded_items_df"],
        "qa_checks": artifacts["qa_checks_df"],
    }

    write_json(summary_path, summary)
    write_json(qa_path, artifacts["qa_json"])
    write_json(request_package_path, artifacts["request_package_json"])
    write_json(schema_path, artifacts["schema_json"])
    write_json(no_apply_proof_path, artifacts["no_apply_proof_json"])
    write_jsonl(request_jsonl_path, artifacts["request_items"])
    write_excel(workbook_path, request_sheets, REQUEST_WORKBOOK_SHEET_ORDER)
    write_excel(excluded_workbook_path, excluded_sheets, EXCLUDED_WORKBOOK_SHEET_ORDER)
    prompt_template_path.write_text(artifacts["prompt_template_md"], encoding="utf-8")
    notes_path.write_text(artifacts["notes_md"], encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            summary_path,
            qa_path,
            request_jsonl_path,
            request_package_path,
            workbook_path,
            prompt_template_path,
            schema_path,
            excluded_workbook_path,
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
    summary["decision"] = (
        "SAFE_ADJUDICATOR_SUBSET_323D_PREPARED_READY_FOR_CONFIGURED_ADJUDICATOR_RUN"
        if summary["qa_fail_count"] == 0
        else EXPECTED_323D_NOT_READY
    )

    request_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    request_sheets["qa_checks"] = qa_df
    excluded_sheets["summary"] = pd.DataFrame([summary]).fillna("")
    excluded_sheets["qa_checks"] = qa_df

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
    request_package_json = artifacts["request_package_json"]
    request_package_json["decision"] = summary["decision"]
    write_json(request_package_path, request_package_json)
    write_excel(workbook_path, request_sheets, REQUEST_WORKBOOK_SHEET_ORDER)
    write_excel(excluded_workbook_path, excluded_sheets, EXCLUDED_WORKBOOK_SHEET_ORDER)
    notes_path.write_text(safe_adjudicator_subset_report_markdown(summary), encoding="utf-8")

    print(f"safe_adjudicator_subset_323d_summary_json: {summary_path}")
    print(f"safe_adjudicator_subset_323d_qa_json: {qa_path}")
    print(f"safe_adjudicator_subset_323d_request_items_jsonl: {request_jsonl_path}")
    print(f"safe_adjudicator_subset_323d_request_package_json: {request_package_path}")
    print(f"safe_adjudicator_subset_323d_request_workbook_xlsx: {workbook_path}")
    print(f"safe_adjudicator_subset_323d_prompt_template_md: {prompt_template_path}")
    print(f"safe_adjudicator_subset_323d_schema_json: {schema_path}")
    print(f"safe_adjudicator_subset_323d_excluded_items_xlsx: {excluded_workbook_path}")
    print(f"safe_adjudicator_subset_323d_no_apply_proof_json: {no_apply_proof_path}")
    print(f"safe_adjudicator_subset_323d_notes_md: {notes_path}")
    for key in [
        "mode",
        "safe_request_item_count",
        "alias_request_count",
        "scope_request_count",
        "excluded_holdout_count",
        "excluded_needs_more_info_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
