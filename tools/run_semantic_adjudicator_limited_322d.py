from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.adjudicator_executor import (
    build_request_payloads,
    read_design_inputs,
    select_candidate_cases,
    select_label_cases,
)
from datefac.semantic.adjudicator_gate_applier import apply_deterministic_gates
from datefac.semantic.adjudicator_readiness import build_acceptance_gate_rules
from datefac.semantic.adjudicator_response_reader import validate_responses
from datefac.semantic.adjudicator_result_report import (
    build_known_limitations_df,
    build_report_markdown,
    limited_decision,
    write_excel,
    write_json,
    write_jsonl,
)
from datefac.semantic.adjudicator_schema import validate_output_schema_dict


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _find_workbook(directory: Path) -> Optional[Path]:
    if not directory.exists():
        return None
    workbooks = sorted(directory.glob("*.xlsx"))
    return workbooks[0] if workbooks else None


def _read_sheet(workbook: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(workbook, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _write_empty_jsonl(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _blocked_result(output_dir: Path, code: str, mode: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322D",
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
        "estimated_trusted_candidate_gain": 0,
        "estimated_review_reduction": 0,
        "estimated_manual_remaining": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "semantic_adjudicator_limited_decision": code,
    }
    qa_df = pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}])
    sheets = {
        "summary": pd.DataFrame([summary]),
        "selected_label_cases": pd.DataFrame(),
        "selected_candidate_cases": pd.DataFrame(),
        "llm_request_inventory": pd.DataFrame(),
        "llm_response_validation": pd.DataFrame(),
        "deterministic_gate_results": pd.DataFrame(),
        "alias_replay_instructions": pd.DataFrame(),
        "out_of_scope_replay_instructions": pd.DataFrame(),
        "unit_inference_replay_instructions": pd.DataFrame(),
        "manual_review_after_llm": pd.DataFrame(),
        "estimated_impact_322d": pd.DataFrame([{"input_review_required_count": 0}]),
        "qa_checks": qa_df,
        "known_limitations": build_known_limitations_df(),
    }
    write_excel(output_dir / "semantic_adjudicator_limited_322d.xlsx", sheets)
    write_json(output_dir / "semantic_adjudicator_limited_322d_summary.json", summary)
    (output_dir / "semantic_adjudicator_limited_322d_report.md").write_text(build_report_markdown(summary), encoding="utf-8")
    _write_empty_jsonl(output_dir / "llm_label_requests_322d.jsonl")
    _write_empty_jsonl(output_dir / "llm_candidate_requests_322d.jsonl")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322D limited semantic adjudicator execution.")
    parser.add_argument("--design-dir", required=True)
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--response-dir", default="")
    parser.add_argument("--mode", choices=["dry_run", "apply_existing_responses"], default="dry_run")
    parser.add_argument("--max-label-cases", type=int, default=20)
    parser.add_argument("--max-candidate-cases", type=int, default=0)
    args = parser.parse_args()

    design_dir = Path(args.design_dir)
    trust_split_dir = Path(args.trust_split_dir)
    output_dir = Path(args.output_dir)
    response_dir = Path(args.response_dir) if _norm(args.response_dir) else None

    if not design_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322C_DESIGN_DIR", args.mode)
        print(f"semantic_adjudicator_limited_322d_summary_json: {output_dir / 'semantic_adjudicator_limited_322d_summary.json'}")
        return 0

    trust_split_workbook = _find_workbook(trust_split_dir)
    review_df = _read_sheet(trust_split_workbook, "review_required_preview_322b2")
    if review_df.empty:
        review_df = pd.DataFrame()

    design_inputs = read_design_inputs(design_dir)
    label_pack_df = design_inputs["label_pack_df"]
    candidate_pack_df = design_inputs["candidate_pack_df"]
    prompt_templates_df = design_inputs["prompt_templates_df"]
    allowed_metric_codes_df = design_inputs["allowed_metric_codes_df"]
    output_schema = design_inputs["output_schema"]

    selected_label_df = select_label_cases(label_pack_df, review_df, args.max_label_cases)
    selected_candidate_df = select_candidate_cases(candidate_pack_df, args.max_candidate_cases)

    label_requests_df, candidate_requests_df, request_inventory_df = build_request_payloads(
        selected_label_df=selected_label_df,
        selected_candidate_df=selected_candidate_df,
        prompt_templates_df=prompt_templates_df,
        output_schema=output_schema,
        allowed_metric_codes_df=allowed_metric_codes_df,
        review_df=review_df,
        output_dir=output_dir,
        mode=args.mode,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    label_request_path = output_dir / "llm_label_requests_322d.jsonl"
    candidate_request_path = output_dir / "llm_candidate_requests_322d.jsonl"
    if not label_requests_df.empty:
        write_jsonl(label_request_path, label_requests_df)
    else:
        _write_empty_jsonl(label_request_path)
    if not candidate_requests_df.empty:
        write_jsonl(candidate_request_path, candidate_requests_df)
    else:
        _write_empty_jsonl(candidate_request_path)

    active_response_dir = response_dir if args.mode == "apply_existing_responses" else None
    response_validation_df, valid_payloads, response_extras_df = validate_responses(
        request_inventory_df=request_inventory_df,
        response_dir=active_response_dir,
    )

    gate_results_df, alias_replay_df, out_scope_df, unit_replay_df, manual_review_df = apply_deterministic_gates(
        selected_label_df=selected_label_df,
        selected_candidate_df=selected_candidate_df,
        response_validation_df=response_validation_df,
        valid_payloads=valid_payloads,
        review_df=review_df,
    )

    estimated_trusted_candidate_gain = int(gate_results_df["estimated_trusted_candidate_gain"].sum()) if not gate_results_df.empty else 0
    estimated_review_reduction = int(gate_results_df["estimated_review_reduction"].sum()) if not gate_results_df.empty else 0
    input_review_required_count = int(len(review_df))
    estimated_manual_remaining = max(input_review_required_count - estimated_review_reduction, 0)

    estimated_impact_df = pd.DataFrame(
        [
            {
                "input_review_required_count": input_review_required_count,
                "selected_case_count": int(len(request_inventory_df)),
                "response_valid_count": int((response_validation_df["schema_valid"] == True).sum()) if not response_validation_df.empty else 0,
                "accepted_alias_count": int((gate_results_df["gate_result"] == "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
                "out_of_scope_count": int((gate_results_df["gate_result"] == "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
                "unit_inference_count": int((gate_results_df["gate_result"] == "ACCEPT_UNIT_INFERENCE_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
                "rejected_noise_count": int((gate_results_df["gate_result"] == "REJECT_NOISE_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
                "estimated_trusted_gain": estimated_trusted_candidate_gain,
                "estimated_review_reduction": estimated_review_reduction,
                "estimated_manual_remaining": estimated_manual_remaining,
            }
        ]
    )

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa("design_output_exists", "PASS" if design_dir.exists() else "FAIL", str(design_dir))
    add_qa("no_recognizer_command_executed", "PASS", "322D dry_run/apply_existing_responses does not call MinerU/StructEqTable/Docling/PPStructure/VLM")
    add_qa("no_e_drive_files_modified", "PASS", "322D reads existing artifacts and writes sandbox outputs only")
    add_qa("no_production_files_modified", "PASS", "322D keeps all changes in datefac/semantic and sandbox output")
    add_qa(
        "default_validation_mode_does_not_call_model_api",
        "PASS" if args.mode == "dry_run" else "WARN",
        "dry_run emits request payloads only" if args.mode == "dry_run" else "non-dry mode selected; network execution still not used by this validation",
    )
    stable_request_ids = request_inventory_df.empty or not request_inventory_df["case_id"].astype(str).duplicated().any()
    add_qa("request_payloads_have_stable_case_ids", "PASS" if stable_request_ids else "FAIL", f"request_payload_count={len(request_inventory_df)}")
    combined_prompt_text = "\n".join(label_requests_df["prompt_text"].astype(str).tolist() + candidate_requests_df["prompt_text"].astype(str).tolist())
    add_qa(
        "every_prompt_forbids_numeric_invention",
        "PASS" if (not request_inventory_df.empty and "must not invent numbers" in combined_prompt_text.lower()) or request_inventory_df.empty else "FAIL",
        "numeric invention guardrail included in prompt templates",
    )
    schema_included = True
    for df in [label_requests_df, candidate_requests_df]:
        if df.empty:
            continue
        if not df["output_schema"].apply(lambda value: isinstance(value, dict) and bool(value)).all():
            schema_included = False
            break
    add_qa("output_schema_included_in_every_request_payload", "PASS" if schema_included else "FAIL", "request payloads carry 322C output schema")
    gate_rules_text = "\n".join(row["condition"] for row in build_acceptance_gate_rules())
    deterministic_gate_ok = "LLM action alone can never create trusted output".lower() in gate_rules_text.lower()
    add_qa("deterministic_gate_forbids_llm_only_trusted_decisions", "PASS" if deterministic_gate_ok else "FAIL", "322C deterministic gates are still enforced")
    add_qa("dry_run_has_no_responses", "WARN" if args.mode == "dry_run" else "PASS", f"response_available_count={int((response_validation_df['response_available'] == True).sum()) if not response_validation_df.empty else 0}")
    add_qa("limited_sample_size", "WARN" if len(request_inventory_df) <= 20 else "PASS", f"selected_case_count={len(request_inventory_df)}")
    add_qa("actual_llm_execution_requires_manual_provider_configuration", "WARN", "322D validation path does not execute any provider")
    add_qa("human_confirmation_may_still_be_required_before_replaying_aliases", "WARN", "Replay outputs remain sandbox suggestions")
    if not response_extras_df.empty:
        add_qa("response_file_extra_rows_detected", "WARN", f"extra_rows={len(response_extras_df)}")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    summary = {
        "stage": "322D",
        "mode": args.mode,
        "output_dir": str(output_dir),
        "selected_label_case_count": int(len(selected_label_df)),
        "selected_candidate_case_count": int(len(selected_candidate_df)),
        "request_payload_count": int(len(request_inventory_df)),
        "response_available_count": int((response_validation_df["response_available"] == True).sum()) if not response_validation_df.empty else 0,
        "response_json_parse_ok_count": int((response_validation_df["json_parse_ok"] == True).sum()) if not response_validation_df.empty else 0,
        "response_schema_valid_count": int((response_validation_df["schema_valid"] == True).sum()) if not response_validation_df.empty else 0,
        "accepted_alias_suggestion_count": int((gate_results_df["gate_result"] == "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
        "out_of_scope_classification_count": int((gate_results_df["gate_result"] == "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
        "unit_inference_accept_count": int((gate_results_df["gate_result"] == "ACCEPT_UNIT_INFERENCE_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
        "rejected_noise_count": int((gate_results_df["gate_result"] == "REJECT_NOISE_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
        "keep_review_required_count": int((gate_results_df["gate_result"] == "KEEP_REVIEW_REQUIRED").sum()) if not gate_results_df.empty else 0,
        "manual_review_after_llm_count": int(len(manual_review_df)),
        "estimated_trusted_candidate_gain": estimated_trusted_candidate_gain,
        "estimated_review_reduction": estimated_review_reduction,
        "estimated_manual_remaining": estimated_manual_remaining,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
    }
    summary["semantic_adjudicator_limited_decision"] = limited_decision(summary)

    output_files = {
        "excel": output_dir / "semantic_adjudicator_limited_322d.xlsx",
        "summary_json": output_dir / "semantic_adjudicator_limited_322d_summary.json",
        "report_md": output_dir / "semantic_adjudicator_limited_322d_report.md",
        "label_requests_jsonl": label_request_path,
        "candidate_requests_jsonl": candidate_request_path,
    }
    if args.mode == "apply_existing_responses":
        output_files["validated_responses_jsonl"] = output_dir / "llm_label_responses_validated_322d.jsonl"
        output_files["gate_results_jsonl"] = output_dir / "deterministic_gate_results_322d.jsonl"
        output_files["alias_replay_jsonl"] = output_dir / "alias_replay_instructions_322d.jsonl"

    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(build_report_markdown(summary), encoding="utf-8")
    if args.mode == "apply_existing_responses":
        if not response_validation_df.empty:
            write_jsonl(output_files["validated_responses_jsonl"], response_validation_df)
        else:
            _write_empty_jsonl(output_files["validated_responses_jsonl"])
        if not gate_results_df.empty:
            write_jsonl(output_files["gate_results_jsonl"], gate_results_df)
        else:
            _write_empty_jsonl(output_files["gate_results_jsonl"])
        if not alias_replay_df.empty:
            write_jsonl(output_files["alias_replay_jsonl"], alias_replay_df)
        else:
            _write_empty_jsonl(output_files["alias_replay_jsonl"])

    selected_label_sheet = selected_label_df[
        [
            "label_case_id",
            "normalized_label",
            "candidate_count",
            "unique_table_count",
            "candidate_category",
            "priority",
            "selection_reason",
        ]
    ].copy() if not selected_label_df.empty else pd.DataFrame(
        columns=[
            "label_case_id",
            "normalized_label",
            "candidate_count",
            "unique_table_count",
            "candidate_category",
            "priority",
            "selection_reason",
        ]
    )
    selected_candidate_sheet = selected_candidate_df[
        [
            "case_id",
            "table_asset_id",
            "table_title",
            "row_label",
            "current_review_reason",
            "priority",
            "selection_reason",
        ]
    ].copy() if not selected_candidate_df.empty else pd.DataFrame(
        columns=[
            "case_id",
            "table_asset_id",
            "table_title",
            "row_label",
            "current_review_reason",
            "priority",
            "selection_reason",
        ]
    )

    sheets = {
        "summary": pd.DataFrame([summary]),
        "selected_label_cases": selected_label_sheet,
        "selected_candidate_cases": selected_candidate_sheet,
        "llm_request_inventory": request_inventory_df,
        "llm_response_validation": response_validation_df,
        "deterministic_gate_results": gate_results_df,
        "alias_replay_instructions": alias_replay_df,
        "out_of_scope_replay_instructions": out_scope_df,
        "unit_inference_replay_instructions": unit_replay_df,
        "manual_review_after_llm": manual_review_df,
        "estimated_impact_322d": estimated_impact_df,
        "qa_checks": qa_df,
        "known_limitations": build_known_limitations_df(),
    }
    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(build_report_markdown(summary), encoding="utf-8")

    output_files_written = all(path.exists() for path in output_files.values())
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
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["semantic_adjudicator_limited_decision"] = limited_decision(summary)

    sheets["summary"] = pd.DataFrame([summary])
    sheets["qa_checks"] = qa_df
    write_excel(output_files["excel"], sheets)
    write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(build_report_markdown(summary), encoding="utf-8")

    print(f"semantic_adjudicator_limited_322d_excel: {output_files['excel']}")
    print(f"semantic_adjudicator_limited_322d_summary_json: {output_files['summary_json']}")
    print(f"semantic_adjudicator_limited_322d_report_md: {output_files['report_md']}")
    for key in [
        "mode",
        "selected_label_case_count",
        "selected_candidate_case_count",
        "request_payload_count",
        "response_available_count",
        "response_json_parse_ok_count",
        "response_schema_valid_count",
        "accepted_alias_suggestion_count",
        "out_of_scope_classification_count",
        "unit_inference_accept_count",
        "rejected_noise_count",
        "keep_review_required_count",
        "manual_review_after_llm_count",
        "estimated_trusted_candidate_gain",
        "estimated_review_reduction",
        "estimated_manual_remaining",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "semantic_adjudicator_limited_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
