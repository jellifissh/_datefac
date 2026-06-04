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

from datefac.semantic.scope_noise_safe_adjudicator_request_324c import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_324B_DIR,
    DEFAULT_SCOPE_REFINEMENT_324A_DIR,
    EXPECTED_324C_NOT_READY,
    EXPECTED_324C_READY_DECISION,
    build_scope_noise_safe_adjudicator_request_324c,
    load_scope_noise_safe_adjudicator_request_324c_inputs,
)
from datefac.semantic.scope_noise_safe_adjudicator_request_324c_report import (  # noqa: E402
    scope_noise_safe_adjudicator_request_324c_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "324C",
        "mode": "prepare",
        "output_dir": str(output_dir),
        "request_count": 0,
        "scope_noise_request_count": 0,
        "risk_flags_carried_forward": "",
        "allowed_response_labels": "",
        "llm_or_adjudicator_called": False,
        "review_record_count": 0,
        "escalate_to_adjudicator_count": 0,
        "confirmed_scope_noise_count": 0,
        "pending_count": 0,
        "invalid_decision_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": EXPECTED_324C_NOT_READY,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    empty_df = pd.DataFrame()
    write_json(output_dir / "scope_noise_safe_adjudicator_request_324c_summary.json", summary)
    write_json(output_dir / "scope_noise_safe_adjudicator_request_324c_qa.json", qa_json)
    write_json(
        output_dir / "scope_noise_safe_adjudicator_request_324c_request_package.json",
        {"stage": "324C", "mode": "prepare", "decision": EXPECTED_324C_NOT_READY, "request_items": []},
    )
    write_json(output_dir / "scope_noise_safe_adjudicator_request_324c_schema.json", {})
    write_json(
        output_dir / "scope_noise_safe_adjudicator_request_324c_no_apply_proof.json",
        {"decision": "blocked_input"},
    )
    write_jsonl(output_dir / "scope_noise_safe_adjudicator_request_324c_request_items.jsonl", [])
    write_excel(
        output_dir / "scope_noise_safe_adjudicator_request_324c_evidence_workbook.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "request_items": empty_df,
            "evidence": empty_df,
            "response_schema": empty_df,
            "qa_checks": pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}]),
        },
    )
    (output_dir / "scope_noise_safe_adjudicator_request_324c_manual_prompt.md").write_text(
        "",
        encoding="utf-8",
    )
    (output_dir / "scope_noise_safe_adjudicator_request_324c_notes.md").write_text(
        scope_noise_safe_adjudicator_request_324c_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 324C scope-noise safe adjudicator request prep.")
    parser.add_argument("--reviewed-dir", default=str(DEFAULT_REVIEWED_324B_DIR))
    parser.add_argument("--scope-refinement-dir", default=str(DEFAULT_SCOPE_REFINEMENT_324A_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    reviewed_dir = Path(args.reviewed_dir)
    scope_refinement_dir = Path(args.scope_refinement_dir)
    output_dir = Path(args.output_dir)

    required_paths = [
        reviewed_dir / "scope_noise_human_review_324b_reviewed_summary.json",
        reviewed_dir / "scope_noise_human_review_324b_reviewed_qa.json",
        reviewed_dir / "scope_noise_human_review_324b_final_routing_plan.json",
        reviewed_dir / "scope_noise_human_review_324b_reviewed_workbook.xlsx",
        scope_refinement_dir / "scope_noise_refinement_324a_summary.json",
        scope_refinement_dir / "scope_noise_refinement_324a_qa.json",
        scope_refinement_dir / "scope_noise_refinement_324a_refined_batch.json",
    ]
    if not all(path.exists() for path in required_paths):
        _blocked_result(output_dir, "BLOCKED_MISSING_324B_REVIEWED_OR_324A_REFINEMENT_ARTIFACTS")
        print(
            "scope_noise_safe_adjudicator_request_324c_summary_json: "
            f"{output_dir / 'scope_noise_safe_adjudicator_request_324c_summary.json'}"
        )
        return 0

    inputs = load_scope_noise_safe_adjudicator_request_324c_inputs(
        reviewed_dir=reviewed_dir,
        scope_refinement_dir=scope_refinement_dir,
    )
    artifacts = build_scope_noise_safe_adjudicator_request_324c(inputs)
    summary = artifacts["summary"]
    summary["output_dir"] = str(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "scope_noise_safe_adjudicator_request_324c_summary.json"
    qa_path = output_dir / "scope_noise_safe_adjudicator_request_324c_qa.json"
    request_jsonl_path = output_dir / "scope_noise_safe_adjudicator_request_324c_request_items.jsonl"
    request_package_path = output_dir / "scope_noise_safe_adjudicator_request_324c_request_package.json"
    workbook_path = output_dir / "scope_noise_safe_adjudicator_request_324c_evidence_workbook.xlsx"
    manual_prompt_path = output_dir / "scope_noise_safe_adjudicator_request_324c_manual_prompt.md"
    schema_path = output_dir / "scope_noise_safe_adjudicator_request_324c_schema.json"
    notes_path = output_dir / "scope_noise_safe_adjudicator_request_324c_notes.md"
    no_apply_proof_path = output_dir / "scope_noise_safe_adjudicator_request_324c_no_apply_proof.json"

    write_json(summary_path, summary)
    write_json(qa_path, artifacts["qa_json"])
    write_json(request_package_path, artifacts["request_package_json"])
    write_json(schema_path, artifacts["schema_json"])
    write_json(no_apply_proof_path, artifacts["no_apply_proof_json"])
    write_jsonl(request_jsonl_path, artifacts["request_items"])
    write_excel(
        workbook_path,
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "request_items": artifacts["request_items_df"],
            "evidence": artifacts["evidence_df"],
            "response_schema": artifacts["response_schema_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
    )
    manual_prompt_path.write_text(artifacts["manual_prompt_md"], encoding="utf-8")
    notes_path.write_text(artifacts["notes_md"], encoding="utf-8")

    output_files_written = all(
        path.exists()
        for path in [
            summary_path,
            qa_path,
            request_jsonl_path,
            request_package_path,
            workbook_path,
            manual_prompt_path,
            schema_path,
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
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    )
    summary["decision"] = EXPECTED_324C_READY_DECISION if summary["qa_fail_count"] == 0 else EXPECTED_324C_NOT_READY

    request_package_json = artifacts["request_package_json"]
    request_package_json["decision"] = summary["decision"]

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
    write_json(request_package_path, request_package_json)
    write_excel(
        workbook_path,
        {
            "summary": pd.DataFrame([summary]).fillna(""),
            "request_items": artifacts["request_items_df"],
            "evidence": artifacts["evidence_df"],
            "response_schema": artifacts["response_schema_df"],
            "qa_checks": qa_df,
        },
    )
    notes_path.write_text(scope_noise_safe_adjudicator_request_324c_markdown(summary), encoding="utf-8")

    print(f"scope_noise_safe_adjudicator_request_324c_summary_json: {summary_path}")
    print(f"scope_noise_safe_adjudicator_request_324c_qa_json: {qa_path}")
    print(f"scope_noise_safe_adjudicator_request_324c_request_items_jsonl: {request_jsonl_path}")
    print(f"scope_noise_safe_adjudicator_request_324c_request_package_json: {request_package_path}")
    print(f"scope_noise_safe_adjudicator_request_324c_evidence_workbook_xlsx: {workbook_path}")
    print(f"scope_noise_safe_adjudicator_request_324c_manual_prompt_md: {manual_prompt_path}")
    print(f"scope_noise_safe_adjudicator_request_324c_schema_json: {schema_path}")
    print(f"scope_noise_safe_adjudicator_request_324c_no_apply_proof_json: {no_apply_proof_path}")
    print(f"scope_noise_safe_adjudicator_request_324c_notes_md: {notes_path}")
    for key in [
        "request_count",
        "scope_noise_request_count",
        "risk_flags_carried_forward",
        "allowed_response_labels",
        "llm_or_adjudicator_called",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
