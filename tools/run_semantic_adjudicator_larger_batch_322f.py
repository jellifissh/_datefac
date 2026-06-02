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

from datefac.semantic.adjudicator_larger_batch import run_larger_batch
from datefac.semantic.adjudicator_larger_batch_report import (
    build_known_limitations_df,
    build_report_markdown,
    larger_batch_decision,
    write_excel,
    write_json,
    write_jsonl,
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _write_empty_jsonl(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _blocked_result(output_dir: Path, code: str, mode: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322F",
        "mode": mode,
        "output_dir": str(output_dir),
        "selected_label_case_count": 0,
        "selected_candidate_case_count": 0,
        "request_payload_count": 0,
        "response_available_count": 0,
        "response_json_parse_ok_count": 0,
        "response_schema_valid_count": 0,
        "accepted_alias_suggestion_count": 0,
        "out_of_scope_classification_count": 0,
        "unit_inference_accept_count": 0,
        "rejected_noise_count": 0,
        "keep_review_required_count": 0,
        "manual_review_after_llm_count": 0,
        "replay_instruction_count": 0,
        "replay_allowed_instruction_count": 0,
        "replay_blocked_instruction_count": 0,
        "affected_candidate_count": 0,
        "trusted_total_before_322f": 0,
        "trusted_total_after_322f": 0,
        "review_required_total_before_322f": 0,
        "review_required_total_after_322f": 0,
        "rejected_total_before_322f": 0,
        "rejected_total_after_322f": 0,
        "trusted_gain_322f": 0,
        "review_reduction_322f": 0,
        "selected_core_trusted_rate_before_322f": 0,
        "selected_core_trusted_rate_after_322f": 0,
        "remaining_unknown_metric_candidate_count": 0,
        "remaining_unit_unknown_candidate_count": 0,
        "remaining_manual_review_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
    }
    summary["semantic_adjudicator_larger_batch_decision"] = code

    qa_df = pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}])
    sheets = {
        "summary": pd.DataFrame([summary]),
        "batch_selection_audit": pd.DataFrame(),
        "selected_label_cases_322f": pd.DataFrame(),
        "llm_request_inventory_322f": pd.DataFrame(),
        "llm_response_validation_322f": pd.DataFrame(),
        "deterministic_gate_results_322f": pd.DataFrame(),
        "replay_instruction_inventory_322f": pd.DataFrame(),
        "candidate_replay_diff_322f": pd.DataFrame(),
        "trusted_preview_322f": pd.DataFrame(),
        "review_required_preview_322f": pd.DataFrame(),
        "rejected_preview_322f": pd.DataFrame(),
        "review_reduction_by_instruction_322f": pd.DataFrame(),
        "remaining_review_burden_322f": pd.DataFrame(),
        "qa_checks": qa_df,
        "known_limitations": build_known_limitations_df(),
    }

    excel_path = output_dir / "semantic_adjudicator_larger_batch_322f.xlsx"
    summary_json_path = output_dir / "semantic_adjudicator_larger_batch_322f_summary.json"
    report_path = output_dir / "semantic_adjudicator_larger_batch_322f_report.md"
    write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    report_path.write_text(build_report_markdown(summary), encoding="utf-8")
    _write_empty_jsonl(output_dir / "llm_label_requests_322f.jsonl")
    _write_empty_jsonl(output_dir / "llm_candidate_requests_322f.jsonl")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322F larger semantic adjudicator batch.")
    parser.add_argument("--design-dir", required=True)
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--previous-limited-dir", required=True)
    parser.add_argument("--previous-replay-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--response-dir", default="")
    parser.add_argument("--mode", choices=["dry_run", "apply_existing_responses"], default="dry_run")
    parser.add_argument("--max-label-cases", type=int, default=30)
    parser.add_argument("--max-candidate-cases", type=int, default=0)
    args = parser.parse_args()

    design_dir = Path(args.design_dir)
    trust_split_dir = Path(args.trust_split_dir)
    previous_limited_dir = Path(args.previous_limited_dir)
    previous_replay_dir = Path(args.previous_replay_dir)
    output_dir = Path(args.output_dir)
    response_dir = Path(args.response_dir) if _norm(args.response_dir) else None

    if not design_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322C_DESIGN_DIR", args.mode)
        print(f"semantic_adjudicator_larger_batch_322f_summary_json: {output_dir / 'semantic_adjudicator_larger_batch_322f_summary.json'}")
        return 0
    if not trust_split_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR", args.mode)
        print(f"semantic_adjudicator_larger_batch_322f_summary_json: {output_dir / 'semantic_adjudicator_larger_batch_322f_summary.json'}")
        return 0

    result = run_larger_batch(
        design_dir=design_dir,
        trust_split_dir=trust_split_dir,
        previous_limited_dir=previous_limited_dir,
        previous_replay_dir=previous_replay_dir,
        output_dir=output_dir,
        response_dir=response_dir,
        mode=args.mode,
        max_label_cases=args.max_label_cases,
        max_candidate_cases=args.max_candidate_cases,
    )

    summary = result["summary"]
    summary["semantic_adjudicator_larger_batch_decision"] = larger_batch_decision(summary)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = result["output_files"]

    if args.mode == "apply_existing_responses":
        validated_df = result["response_validation_df"]
        if not validated_df.empty:
            write_jsonl(output_files["validated_responses_jsonl"], validated_df)
        else:
            _write_empty_jsonl(output_files["validated_responses_jsonl"])
        gate_results_df = result["gate_results_df"]
        if not gate_results_df.empty:
            write_jsonl(output_files["gate_results_jsonl"], gate_results_df)
        else:
            _write_empty_jsonl(output_files["gate_results_jsonl"])
        replay_diff_df = result["candidate_replay_diff_df"]
        if not replay_diff_df.empty:
            write_jsonl(output_files["diff_jsonl"], replay_diff_df)
        else:
            _write_empty_jsonl(output_files["diff_jsonl"])
        replay_instruction_df = result["replay_instruction_inventory_df"]
        if not replay_instruction_df.empty:
            write_jsonl(output_files["instruction_jsonl"], replay_instruction_df)
        else:
            _write_empty_jsonl(output_files["instruction_jsonl"])

    sheets = {
        "summary": pd.DataFrame([summary]),
        "batch_selection_audit": result["batch_selection_audit_df"],
        "selected_label_cases_322f": result["selected_label_df"][
            [
                "label_case_id",
                "normalized_label",
                "candidate_count",
                "unique_table_count",
                "candidate_category",
                "priority",
                "selection_score",
                "selection_reason",
            ]
        ].rename(columns={"label_case_id": "label_case_id"}).copy() if not result["selected_label_df"].empty else pd.DataFrame(
            columns=[
                "label_case_id",
                "normalized_label",
                "candidate_count",
                "unique_table_count",
                "candidate_category",
                "priority",
                "selection_score",
                "selection_reason",
            ]
        ),
        "llm_request_inventory_322f": result["request_inventory_df"],
        "llm_response_validation_322f": result["response_validation_df"],
        "deterministic_gate_results_322f": result["gate_results_df"],
        "replay_instruction_inventory_322f": result["replay_instruction_inventory_df"],
        "candidate_replay_diff_322f": result["candidate_replay_diff_df"],
        "trusted_preview_322f": result["trusted_after_df"],
        "review_required_preview_322f": result["review_after_df"],
        "rejected_preview_322f": result["rejected_after_df"],
        "review_reduction_by_instruction_322f": result["review_reduction_by_instruction_df"],
        "remaining_review_burden_322f": result["remaining_review_burden_df"],
        "qa_checks": result["qa_df"],
        "known_limitations": build_known_limitations_df(),
    }

    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(build_report_markdown(summary), encoding="utf-8")

    output_files_written = all(path.exists() for path in output_files.values())
    if not output_files_written:
        qa_df = pd.concat(
            [
                result["qa_df"],
                pd.DataFrame([{"check_name": "output_files_written_successfully", "status": "FAIL", "detail": str(output_dir)}]),
            ],
            ignore_index=True,
        )
        summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum())
        summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum())
        summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum())
        summary["semantic_adjudicator_larger_batch_decision"] = larger_batch_decision(summary)
        sheets["summary"] = pd.DataFrame([summary])
        sheets["qa_checks"] = qa_df
        write_excel(output_files["excel"], sheets)
        write_json(output_files["summary_json"], summary)
        output_files["report_md"].write_text(build_report_markdown(summary), encoding="utf-8")

    print(f"semantic_adjudicator_larger_batch_322f_excel: {output_files['excel']}")
    print(f"semantic_adjudicator_larger_batch_322f_summary_json: {output_files['summary_json']}")
    print(f"semantic_adjudicator_larger_batch_322f_report_md: {output_files['report_md']}")
    for key in [
        "mode",
        "selected_label_case_count",
        "selected_candidate_case_count",
        "request_payload_count",
        "response_available_count",
        "response_schema_valid_count",
        "accepted_alias_suggestion_count",
        "out_of_scope_classification_count",
        "unit_inference_accept_count",
        "replay_allowed_instruction_count",
        "affected_candidate_count",
        "trusted_gain_322f",
        "review_reduction_322f",
        "selected_core_trusted_rate_before_322f",
        "selected_core_trusted_rate_after_322f",
        "remaining_unknown_metric_candidate_count",
        "remaining_unit_unknown_candidate_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "semantic_adjudicator_larger_batch_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
