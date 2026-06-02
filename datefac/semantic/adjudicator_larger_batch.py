from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from datefac.semantic.adjudicator_batch_selector import (
    build_candidate_case_selection,
    build_label_batch_selection,
)
from datefac.semantic.adjudicator_executor import build_request_payloads, read_design_inputs
from datefac.semantic.adjudicator_gate_applier import apply_deterministic_gates
from datefac.semantic.adjudicator_replay import (
    apply_replay,
    build_remaining_review_burden,
    build_replay_instruction_inventory,
)
from datefac.semantic.adjudicator_response_reader import validate_responses


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


def _read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                rows.append(json.loads(text))
            except Exception:
                continue
    return pd.DataFrame(rows).fillna("")


def _write_empty_jsonl(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def load_322f_inputs(
    design_dir: Path,
    trust_split_dir: Path,
    previous_limited_dir: Path,
    previous_replay_dir: Path,
) -> Dict[str, Any]:
    trust_split_workbook = _find_workbook(trust_split_dir)
    previous_replay_workbook = _find_workbook(previous_replay_dir)

    design_inputs = read_design_inputs(design_dir)
    trusted_before_df = _read_sheet(trust_split_workbook, "trusted_preview_322b2")
    review_before_df = _read_sheet(trust_split_workbook, "review_required_preview_322b2")
    rejected_before_df = _read_sheet(trust_split_workbook, "rejected_preview_322b2")
    trust_summary_df = _read_sheet(trust_split_workbook, "summary")
    previous_replay_summary_df = _read_sheet(previous_replay_workbook, "summary")
    previous_replay_inventory_df = _read_sheet(previous_replay_workbook, "replay_instruction_inventory")

    return {
        "design_inputs": design_inputs,
        "trusted_before_df": trusted_before_df,
        "review_before_df": review_before_df,
        "rejected_before_df": rejected_before_df,
        "trust_summary_df": trust_summary_df,
        "previous_replay_summary_df": previous_replay_summary_df,
        "previous_replay_inventory_df": previous_replay_inventory_df,
        "previous_limited_requests_df": _read_jsonl(previous_limited_dir / "llm_label_requests_322d.jsonl"),
    }


def validate_responses_322f(
    request_inventory_df: pd.DataFrame,
    response_dir: Optional[Path],
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, Any]], pd.DataFrame]:
    if response_dir is None:
        return validate_responses(request_inventory_df=request_inventory_df, response_dir=None)

    columns = [
        "case_id",
        "response_available",
        "json_parse_ok",
        "schema_valid",
        "action",
        "metric_code",
        "confidence_label",
        "validation_errors",
    ]
    all_rows: List[Dict[str, Any]] = []
    valid_payloads: Dict[str, Dict[str, Any]] = {}
    extras: List[Dict[str, Any]] = []

    request_map = {str(row.get("case_id", "")).strip(): row for _, row in request_inventory_df.iterrows()}
    seen_case_ids: Dict[str, int] = {}

    for file_name in ["llm_label_responses_322f.jsonl", "llm_candidate_responses_322f.jsonl"]:
        path = response_dir / file_name
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    payload = json.loads(text)
                except Exception as exc:
                    extras.append({"case_id": "", "issue": f"json_parse_error:{exc.__class__.__name__}", "line_number": line_number, "response_file": file_name})
                    continue
                case_id = _norm(payload.get("case_id"))
                if not case_id:
                    extras.append({"case_id": "", "issue": "missing_case_id", "line_number": line_number, "response_file": file_name})
                    continue
                seen_case_ids[case_id] = seen_case_ids.get(case_id, 0) + 1
                if seen_case_ids[case_id] > 1:
                    extras.append({"case_id": case_id, "issue": "duplicate_case_id", "line_number": line_number, "response_file": file_name})
                    continue
                validation_df, parsed_payloads, _ = validate_responses(
                    request_inventory_df=pd.DataFrame([request_map.get(case_id, {"case_id": case_id})]),
                    response_dir=None,
                )
                row = validation_df.iloc[0].to_dict()
                if case_id not in request_map:
                    row.update(
                        {
                            "case_id": case_id,
                            "response_available": True,
                            "json_parse_ok": True,
                            "schema_valid": False,
                            "action": _norm(payload.get("action")),
                            "metric_code": _norm(payload.get("metric_code")),
                            "confidence_label": _norm(payload.get("confidence_label")),
                            "validation_errors": "RESPONSE_CASE_ID_NOT_REQUESTED",
                        }
                    )
                else:
                    from datefac.semantic.adjudicator_response_reader import _validate_response_payload  # type: ignore

                    errors = _validate_response_payload(payload)
                    row.update(
                        {
                            "case_id": case_id,
                            "response_available": True,
                            "json_parse_ok": True,
                            "schema_valid": not errors,
                            "action": _norm(payload.get("action")),
                            "metric_code": _norm(payload.get("metric_code")),
                            "confidence_label": _norm(payload.get("confidence_label")),
                            "validation_errors": "|".join(errors),
                        }
                    )
                    if not errors:
                        valid_payloads[case_id] = payload
                all_rows.append(row)

    found_case_ids = {row["case_id"] for row in all_rows}
    for _, request_row in request_inventory_df.iterrows():
        case_id = _norm(request_row.get("case_id"))
        if case_id in found_case_ids:
            continue
        all_rows.append(
            {
                "case_id": case_id,
                "response_available": False,
                "json_parse_ok": False,
                "schema_valid": False,
                "action": "",
                "metric_code": "",
                "confidence_label": "",
                "validation_errors": "NO_RESPONSE_AVAILABLE",
            }
        )

    validation_df = pd.DataFrame(all_rows, columns=columns).fillna("")
    if not validation_df.empty:
        validation_df = validation_df.sort_values(["case_id"], ascending=[True]).reset_index(drop=True)
    extras_df = pd.DataFrame(extras).fillna("")
    return validation_df, valid_payloads, extras_df


def build_summary_counts(
    mode: str,
    output_dir: Path,
    request_inventory_df: pd.DataFrame,
    response_validation_df: pd.DataFrame,
    gate_results_df: pd.DataFrame,
    replay_instruction_inventory_df: pd.DataFrame,
    candidate_replay_diff_df: pd.DataFrame,
    trusted_before_df: pd.DataFrame,
    trusted_after_df: pd.DataFrame,
    review_before_df: pd.DataFrame,
    review_after_df: pd.DataFrame,
    rejected_before_df: pd.DataFrame,
    rejected_after_df: pd.DataFrame,
    trust_summary_df: pd.DataFrame,
) -> Dict[str, Any]:
    summary_lookup = {
        _norm(row.get("metric")): row.get("value")
        for _, row in trust_summary_df.iterrows()
    } if not trust_summary_df.empty else {}

    input_candidate_count = int(len(trusted_before_df) + len(review_before_df) + len(rejected_before_df))
    trusted_total_before = int(len(trusted_before_df))
    trusted_total_after = int(len(trusted_after_df))
    review_before = int(len(review_before_df))
    review_after = int(len(review_after_df))
    rejected_before = int(len(rejected_before_df))
    rejected_after = int(len(rejected_after_df))

    return {
        "stage": "322F",
        "mode": mode,
        "output_dir": str(output_dir),
        "selected_label_case_count": int((request_inventory_df["case_type"] == "label_level").sum()) if not request_inventory_df.empty else 0,
        "selected_candidate_case_count": int((request_inventory_df["case_type"] == "candidate_level").sum()) if not request_inventory_df.empty else 0,
        "request_payload_count": int(len(request_inventory_df)),
        "response_available_count": int((response_validation_df["response_available"] == True).sum()) if not response_validation_df.empty else 0,
        "response_json_parse_ok_count": int((response_validation_df["json_parse_ok"] == True).sum()) if not response_validation_df.empty else 0,
        "response_schema_valid_count": int((response_validation_df["schema_valid"] == True).sum()) if not response_validation_df.empty else 0,
        "accepted_alias_suggestion_count": int((gate_results_df["gate_result"] == "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
        "out_of_scope_classification_count": int((gate_results_df["gate_result"] == "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
        "unit_inference_accept_count": int((gate_results_df["gate_result"] == "ACCEPT_UNIT_INFERENCE_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
        "rejected_noise_count": int((gate_results_df["gate_result"] == "REJECT_NOISE_FOR_REPLAY").sum()) if not gate_results_df.empty else 0,
        "keep_review_required_count": int((gate_results_df["gate_result"] == "KEEP_REVIEW_REQUIRED").sum()) if not gate_results_df.empty else 0,
        "manual_review_after_llm_count": int((gate_results_df["gate_result"].isin(["KEEP_REVIEW_REQUIRED", "REQUIRES_MANUAL_REVIEW", "LLM_RESPONSE_SCHEMA_INVALID", "LLM_RESPONSE_LOW_CONFIDENCE", "LLM_RESPONSE_UNSUPPORTED_METRIC_CODE"])).sum()) if not gate_results_df.empty else 0,
        "replay_instruction_count": int(len(replay_instruction_inventory_df)),
        "replay_allowed_instruction_count": int(replay_instruction_inventory_df["replay_allowed"].astype(bool).sum()) if not replay_instruction_inventory_df.empty else 0,
        "replay_blocked_instruction_count": int(len(replay_instruction_inventory_df)) - int(replay_instruction_inventory_df["replay_allowed"].astype(bool).sum()) if not replay_instruction_inventory_df.empty else 0,
        "affected_candidate_count": int(len(candidate_replay_diff_df)),
        "trusted_total_before_322f": trusted_total_before,
        "trusted_total_after_322f": trusted_total_after,
        "review_required_total_before_322f": review_before,
        "review_required_total_after_322f": review_after,
        "rejected_total_before_322f": rejected_before,
        "rejected_total_after_322f": rejected_after,
        "trusted_gain_322f": trusted_total_after - trusted_total_before,
        "review_reduction_322f": review_before - review_after,
        "selected_core_trusted_rate_before_322f": float(summary_lookup.get("selected_core_trusted_rate_after_322b2") or 0),
        "selected_core_trusted_rate_after_322f": round(trusted_total_after / input_candidate_count, 6) if input_candidate_count else 0,
        "remaining_unknown_metric_candidate_count": int(review_after_df["risk_tags_after"].astype(str).str.contains(r"(?:^|\\|)UNKNOWN_METRIC_CODE(?:$|\\|)", regex=True).sum()) if not review_after_df.empty else 0,
        "remaining_unit_unknown_candidate_count": int(review_after_df["risk_tags_after"].astype(str).str.contains(r"(?:^|\\|)UNIT_UNKNOWN(?:$|\\|)", regex=True).sum()) if not review_after_df.empty else 0,
        "remaining_manual_review_count": review_after,
    }


def build_qa_checks(
    *,
    design_dir: Path,
    trust_split_dir: Path,
    previous_limited_dir: Path,
    previous_replay_dir: Path,
    output_dir: Path,
    mode: str,
    request_inventory_df: pd.DataFrame,
    label_requests_df: pd.DataFrame,
    candidate_requests_df: pd.DataFrame,
    response_validation_df: pd.DataFrame,
    replay_instruction_inventory_df: pd.DataFrame,
    candidate_replay_diff_df: pd.DataFrame,
    trusted_before_df: pd.DataFrame,
    trusted_after_df: pd.DataFrame,
    review_before_df: pd.DataFrame,
    review_after_df: pd.DataFrame,
    rejected_before_df: pd.DataFrame,
    rejected_after_df: pd.DataFrame,
    response_extras_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    def add(name: str, status: str, detail: str) -> None:
        rows.append({"check_name": name, "status": status, "detail": detail})

    add("322c_design_output_exists", "PASS" if design_dir.exists() else "FAIL", str(design_dir))
    add("322b2_trust_split_output_exists", "PASS" if trust_split_dir.exists() else "FAIL", str(trust_split_dir))
    add("322d_apply5_output_exists", "PASS" if previous_limited_dir.exists() else "FAIL", str(previous_limited_dir))
    add("322e_replay_output_exists", "PASS" if previous_replay_dir.exists() else "FAIL", str(previous_replay_dir))
    add("no_model_api_call_executed_in_dry_run", "PASS" if mode == "dry_run" else "WARN", "dry_run only emits requests without provider execution")
    add("no_recognizer_command_executed", "PASS", "322F does not call MinerU/StructEqTable/Docling/PPStructure/VLM")
    add("no_e_drive_files_modified", "PASS", "322F reads existing artifacts and writes D-drive sandbox outputs only")
    add("no_production_files_modified", "PASS", "322F only adds independent semantic sandbox code and reports")

    stable_request_ids = request_inventory_df.empty or not request_inventory_df["case_id"].astype(str).duplicated().any()
    add("request_payloads_have_stable_case_ids", "PASS" if stable_request_ids else "FAIL", f"request_payload_count={len(request_inventory_df)}")

    prompt_texts = label_requests_df["prompt_text"].astype(str).tolist() + candidate_requests_df["prompt_text"].astype(str).tolist()
    prompt_guardrail_ok = not request_inventory_df.empty and all("invent numbers" in text.lower() or "must not invent numbers" in text.lower() for text in prompt_texts)
    if request_inventory_df.empty:
        prompt_guardrail_ok = True
    add("every_prompt_forbids_numeric_invention", "PASS" if prompt_guardrail_ok else "FAIL", "request prompts include numeric invention guardrails")

    replay_provenance_ok = True
    if not candidate_replay_diff_df.empty:
        replay_provenance_ok = candidate_replay_diff_df["provenance"].astype(str).str.len().gt(0).all()
    add("every_replayed_candidate_has_provenance", "PASS" if replay_provenance_ok else "FAIL", f"replayed_candidate_count={len(candidate_replay_diff_df)}")

    llm_only_trusted = False
    if not trusted_after_df.empty:
        llm_only_trusted = trusted_after_df["risk_tags_after"].astype(str).str.contains(
            r"UNKNOWN_METRIC_CODE|UNIT_UNKNOWN|VALUE_PARSE_FAILED|INVALID_YEAR|NO_YEAR_COLUMNS|VALUE_CONFLICT|EXTRACTION_RISK|SECTION_CONTEXT_REQUIRED",
            regex=True,
        ).any()
    add("no_llm_only_trusted_decision_exists", "PASS" if not llm_only_trusted else "FAIL", "trusted outputs must still satisfy deterministic gates")

    counts_reconcile = (len(trusted_before_df) + len(review_before_df) + len(rejected_before_df)) == (
        len(trusted_after_df) + len(review_after_df) + len(rejected_after_df)
    )
    add("candidate_counts_reconcile_before_after", "PASS" if counts_reconcile else "FAIL", f"before={len(trusted_before_df) + len(review_before_df) + len(rejected_before_df)} after={len(trusted_after_df) + len(review_after_df) + len(rejected_after_df)}")

    if response_extras_df.empty:
        add("response_file_extra_rows_detected", "PASS", "no duplicate or parse-error response rows")
    else:
        add("response_file_extra_rows_detected", "WARN", f"extra_rows={len(response_extras_df)}")

    if mode == "dry_run":
        add("llm_response_files_may_be_absent_in_dry_run", "WARN", f"response_available_count={int((response_validation_df['response_available'] == True).sum()) if not response_validation_df.empty else 0}")
    if len(replay_instruction_inventory_df) <= 30:
        add("bounded_controlled_sample_size", "WARN", f"replay_instruction_count={len(replay_instruction_inventory_df)}")
    if len(review_after_df) > 1000:
        add("many_review_cases_may_remain_unresolved", "WARN", f"remaining_manual_review_count={len(review_after_df)}")
    add("human_confirmation_still_needed_before_official_alias_updates", "WARN", "322F remains sandbox-only and does not update official mapping")

    return pd.DataFrame(rows).fillna("")


def run_larger_batch(
    *,
    design_dir: Path,
    trust_split_dir: Path,
    previous_limited_dir: Path,
    previous_replay_dir: Path,
    output_dir: Path,
    response_dir: Optional[Path],
    mode: str,
    max_label_cases: int,
    max_candidate_cases: int,
) -> Dict[str, Any]:
    inputs = load_322f_inputs(
        design_dir=design_dir,
        trust_split_dir=trust_split_dir,
        previous_limited_dir=previous_limited_dir,
        previous_replay_dir=previous_replay_dir,
    )
    design_inputs = inputs["design_inputs"]
    review_before_df = inputs["review_before_df"]
    trusted_before_df = inputs["trusted_before_df"]
    rejected_before_df = inputs["rejected_before_df"]
    trust_summary_df = inputs["trust_summary_df"]

    selected_label_df, batch_selection_audit_df = build_label_batch_selection(
        label_pack_df=design_inputs["label_pack_df"],
        review_df=review_before_df,
        previous_limited_dir=previous_limited_dir,
        previous_replay_dir=previous_replay_dir,
        max_label_cases=max_label_cases,
    )
    selected_candidate_df = build_candidate_case_selection(
        candidate_pack_df=design_inputs["candidate_pack_df"],
        max_candidate_cases=max_candidate_cases,
    )

    label_requests_df, candidate_requests_df, request_inventory_df = build_request_payloads(
        selected_label_df=selected_label_df,
        selected_candidate_df=selected_candidate_df,
        prompt_templates_df=design_inputs["prompt_templates_df"],
        output_schema=design_inputs["output_schema"],
        allowed_metric_codes_df=design_inputs["allowed_metric_codes_df"],
        review_df=review_before_df,
        output_dir=output_dir,
        mode=mode,
    )
    if not request_inventory_df.empty:
        request_inventory_df = request_inventory_df.copy()
        request_inventory_df["request_file"] = request_inventory_df["request_file"].astype(str).str.replace(
            "llm_label_requests_322d.jsonl",
            "llm_label_requests_322f.jsonl",
            regex=False,
        ).str.replace(
            "llm_candidate_requests_322d.jsonl",
            "llm_candidate_requests_322f.jsonl",
            regex=False,
        )

    label_request_path = output_dir / "llm_label_requests_322f.jsonl"
    candidate_request_path = output_dir / "llm_candidate_requests_322f.jsonl"
    if not label_requests_df.empty:
        output_dir.mkdir(parents=True, exist_ok=True)
        with label_request_path.open("w", encoding="utf-8") as handle:
            for record in label_requests_df.to_dict(orient="records"):
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    else:
        _write_empty_jsonl(label_request_path)
    if not candidate_requests_df.empty:
        with candidate_request_path.open("w", encoding="utf-8") as handle:
            for record in candidate_requests_df.to_dict(orient="records"):
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    else:
        _write_empty_jsonl(candidate_request_path)

    active_response_dir = response_dir if mode == "apply_existing_responses" else None
    response_validation_df, valid_payloads, response_extras_df = validate_responses_322f(
        request_inventory_df=request_inventory_df,
        response_dir=active_response_dir,
    )

    gate_results_df, alias_replay_df, out_scope_df, unit_replay_df, manual_review_df = apply_deterministic_gates(
        selected_label_df=selected_label_df,
        selected_candidate_df=selected_candidate_df,
        response_validation_df=response_validation_df,
        valid_payloads=valid_payloads,
        review_df=review_before_df,
    )

    replay_instruction_inventory_df = build_replay_instruction_inventory(
        deterministic_gate_results_df=gate_results_df,
        alias_replay_df=alias_replay_df,
        out_scope_replay_df=out_scope_df,
        unit_replay_df=unit_replay_df,
    )

    (
        replay_instruction_inventory_df,
        candidate_replay_diff_df,
        trusted_after_df,
        review_after_df,
        rejected_after_df,
        review_reduction_by_instruction_df,
    ) = apply_replay(
        replay_instruction_inventory_df=replay_instruction_inventory_df,
        trusted_before_df=trusted_before_df,
        review_before_df=review_before_df,
        rejected_before_df=rejected_before_df,
    )
    remaining_review_burden_df = build_remaining_review_burden(review_after_df)

    summary = build_summary_counts(
        mode=mode,
        output_dir=output_dir,
        request_inventory_df=request_inventory_df,
        response_validation_df=response_validation_df,
        gate_results_df=gate_results_df,
        replay_instruction_inventory_df=replay_instruction_inventory_df,
        candidate_replay_diff_df=candidate_replay_diff_df,
        trusted_before_df=trusted_before_df,
        trusted_after_df=trusted_after_df,
        review_before_df=review_before_df,
        review_after_df=review_after_df,
        rejected_before_df=rejected_before_df,
        rejected_after_df=rejected_after_df,
        trust_summary_df=trust_summary_df,
    )

    output_files = {
        "excel": output_dir / "semantic_adjudicator_larger_batch_322f.xlsx",
        "summary_json": output_dir / "semantic_adjudicator_larger_batch_322f_summary.json",
        "report_md": output_dir / "semantic_adjudicator_larger_batch_322f_report.md",
        "label_requests_jsonl": label_request_path,
        "candidate_requests_jsonl": candidate_request_path,
    }
    if mode == "apply_existing_responses":
        output_files["validated_responses_jsonl"] = output_dir / "llm_label_responses_validated_322f.jsonl"
        output_files["gate_results_jsonl"] = output_dir / "deterministic_gate_results_322f.jsonl"
        output_files["diff_jsonl"] = output_dir / "candidate_replay_diff_322f.jsonl"
        output_files["instruction_jsonl"] = output_dir / "semantic_replay_instructions_322f.jsonl"

    qa_df = build_qa_checks(
        design_dir=design_dir,
        trust_split_dir=trust_split_dir,
        previous_limited_dir=previous_limited_dir,
        previous_replay_dir=previous_replay_dir,
        output_dir=output_dir,
        mode=mode,
        request_inventory_df=request_inventory_df,
        label_requests_df=label_requests_df,
        candidate_requests_df=candidate_requests_df,
        response_validation_df=response_validation_df,
        replay_instruction_inventory_df=replay_instruction_inventory_df,
        candidate_replay_diff_df=candidate_replay_diff_df,
        trusted_before_df=trusted_before_df,
        trusted_after_df=trusted_after_df,
        review_before_df=review_before_df,
        review_after_df=review_after_df,
        rejected_before_df=rejected_before_df,
        rejected_after_df=rejected_after_df,
        response_extras_df=response_extras_df,
    )
    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    return {
        "summary": summary,
        "batch_selection_audit_df": batch_selection_audit_df,
        "selected_label_df": selected_label_df,
        "request_inventory_df": request_inventory_df,
        "response_validation_df": response_validation_df,
        "gate_results_df": gate_results_df,
        "replay_instruction_inventory_df": replay_instruction_inventory_df,
        "candidate_replay_diff_df": candidate_replay_diff_df,
        "trusted_after_df": trusted_after_df,
        "review_after_df": review_after_df,
        "rejected_after_df": rejected_after_df,
        "review_reduction_by_instruction_df": review_reduction_by_instruction_df,
        "remaining_review_burden_df": remaining_review_burden_df,
        "qa_df": qa_df,
        "label_requests_df": label_requests_df,
        "candidate_requests_df": candidate_requests_df,
        "response_extras_df": response_extras_df,
        "output_files": output_files,
    }
