from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd


ACCEPTED_INSTRUCTION_TYPES = {
    "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY",
    "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY",
    "ACCEPT_UNIT_INFERENCE_FOR_REPLAY",
    "REJECT_NOISE_FOR_REPLAY",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _split_tags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _parse_json_object(value: Any) -> Dict[str, Any]:
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _dedupe_preserve(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _join_unique(items: List[str], limit: int = 5) -> str:
    return " | ".join(_dedupe_preserve(items)[:limit])


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except Exception:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return pd.DataFrame(rows).fillna("")


def _find_workbook(directory: Path) -> Optional[Path]:
    if not directory.exists():
        return None
    workbooks = sorted(directory.glob("*.xlsx"))
    return workbooks[0] if workbooks else None


def read_excel_sheet(workbook: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(workbook, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def load_semantic_mapping_proposal_inputs(
    apply30_dir: Path,
    trust_split_dir: Path,
) -> Dict[str, Any]:
    apply_workbook = _find_workbook(apply30_dir)
    instructions_df = read_jsonl(apply30_dir / "semantic_replay_instructions_322f.jsonl")
    gate_results_df = read_jsonl(apply30_dir / "deterministic_gate_results_322f.jsonl")
    candidate_replay_diff_df = read_jsonl(apply30_dir / "candidate_replay_diff_322f.jsonl")
    selected_candidates_df = read_jsonl(trust_split_dir / "selected_candidate_reclassified_322b2.jsonl")
    if not selected_candidates_df.empty:
        selected_candidates_df["normalized_label"] = selected_candidates_df["raw_metric_name"].map(_normalize_label)
    if not candidate_replay_diff_df.empty:
        candidate_replay_diff_df["normalized_label"] = candidate_replay_diff_df["row_label"].map(_normalize_label)
        candidate_replay_diff_df["provenance_dict"] = candidate_replay_diff_df["provenance"].map(_parse_json_object)
        candidate_replay_diff_df["table_title"] = candidate_replay_diff_df["provenance_dict"].map(
            lambda payload: _norm(payload.get("table_title"))
        )
    return {
        "apply_summary": _read_json(apply30_dir / "semantic_adjudicator_larger_batch_322f_summary.json"),
        "trust_summary": _read_json(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
        "instructions_df": instructions_df,
        "gate_results_df": gate_results_df,
        "candidate_replay_diff_df": candidate_replay_diff_df,
        "selected_candidates_df": selected_candidates_df,
        "remaining_review_burden_df": read_excel_sheet(apply_workbook, "remaining_review_burden_322f"),
        "qa_checks_322f_df": read_excel_sheet(apply_workbook, "qa_checks"),
    }


def _accepted_instructions(instructions_df: pd.DataFrame) -> pd.DataFrame:
    if instructions_df.empty:
        return pd.DataFrame(columns=list(instructions_df.columns))
    mask = instructions_df["instruction_type"].astype(str).isin(ACCEPTED_INSTRUCTION_TYPES)
    if "replay_allowed" in instructions_df.columns:
        mask = mask & instructions_df["replay_allowed"].astype(bool)
    return instructions_df[mask].copy().reset_index(drop=True)


def _proposal_prefix(instruction_type: str) -> str:
    mapping = {
        "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY": "alias",
        "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY": "out_of_scope",
        "ACCEPT_UNIT_INFERENCE_FOR_REPLAY": "unit",
        "REJECT_NOISE_FOR_REPLAY": "noise",
    }
    return mapping.get(_norm(instruction_type), "proposal")


def _proposal_risk_flags(instruction_type: str, sample_risk_tags: List[str]) -> str:
    base_flags = ["ACCEPTED_322F_REPLAY", "HUMAN_CONFIRMATION_REQUIRED"]
    if instruction_type == "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY":
        base_flags.append("ALIAS_MAPPING_PROPOSAL")
    elif instruction_type == "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY":
        base_flags.append("OUT_OF_SCOPE_PROPOSAL")
    elif instruction_type == "ACCEPT_UNIT_INFERENCE_FOR_REPLAY":
        base_flags.append("UNIT_INFERENCE_PROPOSAL")
    elif instruction_type == "REJECT_NOISE_FOR_REPLAY":
        base_flags.append("NOISE_REJECTION_PROPOSAL")
    return " | ".join(_dedupe_preserve(base_flags + sample_risk_tags))


def _sample_candidates_for_instruction(
    instruction_row: pd.Series,
    candidate_replay_diff_df: pd.DataFrame,
    selected_candidates_df: pd.DataFrame,
    max_rows: int = 5,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    instruction_type = _norm(instruction_row.get("instruction_type"))
    normalized_label = _normalize_label(instruction_row.get("normalized_label"))
    instruction_id = _norm(instruction_row.get("instruction_id"))

    records: List[Dict[str, Any]] = []
    if instruction_type in {
        "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY",
        "ACCEPT_UNIT_INFERENCE_FOR_REPLAY",
    } and not candidate_replay_diff_df.empty:
        matched = candidate_replay_diff_df[
            candidate_replay_diff_df["replay_instruction_id"].astype(str) == instruction_id
        ].copy()
        if not matched.empty:
            matched = matched.sort_values(
                ["source_report_name", "table_asset_id", "year", "row_label"],
                ascending=[True, True, True, True],
            ).reset_index(drop=True)
            for _, row in matched.head(max_rows).iterrows():
                records.append(
                    {
                        "proposal_id": "",
                        "source_case_id": _norm(instruction_row.get("case_id")),
                        "instruction_type": instruction_type,
                        "table_asset_id": _norm(row.get("table_asset_id")),
                        "source_report_name": _norm(row.get("source_report_name")),
                        "table_title": _norm(row.get("table_title")),
                        "row_label": _norm(row.get("row_label")),
                        "year": _norm(row.get("year")),
                        "raw_value": _norm(row.get("raw_value")),
                        "normalized_value": row.get("normalized_value"),
                        "metric_code_before": _norm(row.get("metric_code_before")),
                        "metric_code_after": _norm(row.get("metric_code_after")),
                        "decision_before": _norm(row.get("decision_before")),
                        "decision_after": _norm(row.get("decision_after")),
                        "risk_tags_before": _norm(row.get("risk_tags_before")),
                        "risk_tags_after": _norm(row.get("risk_tags_after")),
                        "impact_source": "candidate_replay_diff_322f",
                    }
                )
            return matched, records

    if selected_candidates_df.empty:
        return pd.DataFrame(), records

    matched = selected_candidates_df[
        selected_candidates_df["normalized_label"].astype(str) == normalized_label
    ].copy()
    if matched.empty:
        return matched, records
    matched = matched.sort_values(
        ["source_report_name", "table_asset_id", "year", "raw_metric_name"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)
    for _, row in matched.head(max_rows).iterrows():
        decision_after = "rejected_preview" if instruction_type in {
            "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY",
            "REJECT_NOISE_FOR_REPLAY",
        } else _norm(row.get("split_decision"))
        metric_code_after = ""
        if instruction_type == "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY":
            metric_code_after = _norm(instruction_row.get("proposed_metric_code"))
        elif instruction_type == "ACCEPT_UNIT_INFERENCE_FOR_REPLAY":
            metric_code_after = _norm(row.get("metric_code"))
        records.append(
            {
                "proposal_id": "",
                "source_case_id": _norm(instruction_row.get("case_id")),
                "instruction_type": instruction_type,
                "table_asset_id": _norm(row.get("table_asset_id")),
                "source_report_name": _norm(row.get("source_report_name")),
                "table_title": _norm(row.get("table_title")),
                "row_label": _norm(row.get("raw_metric_name")),
                "year": _norm(row.get("year")),
                "raw_value": _norm(row.get("raw_value")),
                "normalized_value": row.get("normalized_value"),
                "metric_code_before": _norm(row.get("metric_code")),
                "metric_code_after": metric_code_after,
                "decision_before": _norm(row.get("split_decision")),
                "decision_after": decision_after,
                "risk_tags_before": _norm(row.get("risk_tags_after") or row.get("risk_tags")),
                "risk_tags_after": _norm(row.get("risk_tags_after") or row.get("risk_tags")),
                "impact_source": "selected_candidate_reclassified_322b2",
            }
        )
    return matched, records


def build_semantic_mapping_proposals(
    apply_summary: Dict[str, Any],
    trust_summary: Dict[str, Any],
    instructions_df: pd.DataFrame,
    gate_results_df: pd.DataFrame,
    candidate_replay_diff_df: pd.DataFrame,
    selected_candidates_df: pd.DataFrame,
    remaining_review_burden_df: pd.DataFrame,
    qa_checks_322f_df: pd.DataFrame,
) -> Dict[str, Any]:
    accepted_df = _accepted_instructions(instructions_df)
    gate_lookup = {
        _norm(row.get("case_id")): row.to_dict()
        for _, row in gate_results_df.iterrows()
    } if not gate_results_df.empty else {}

    alias_rows: List[Dict[str, Any]] = []
    out_scope_rows: List[Dict[str, Any]] = []
    unit_rows: List[Dict[str, Any]] = []
    rejected_noise_rows: List[Dict[str, Any]] = []
    candidate_impact_rows: List[Dict[str, Any]] = []
    trace_failures = 0

    prefix_counts = {
        "alias": 0,
        "out_of_scope": 0,
        "unit": 0,
        "noise": 0,
    }

    for _, instruction_row in accepted_df.iterrows():
        instruction_type = _norm(instruction_row.get("instruction_type"))
        prefix = _proposal_prefix(instruction_type)
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
        proposal_id = f"proposal::{prefix}::{prefix_counts[prefix]:03d}"
        gate_row = gate_lookup.get(_norm(instruction_row.get("case_id")), {})
        matched_df, impact_records = _sample_candidates_for_instruction(
            instruction_row=instruction_row,
            candidate_replay_diff_df=candidate_replay_diff_df,
            selected_candidates_df=selected_candidates_df,
            max_rows=5,
        )
        for record in impact_records:
            record["proposal_id"] = proposal_id
            candidate_impact_rows.append(record)

        sample_table_titles = _join_unique([_norm(item.get("table_title")) for item in impact_records], limit=5)
        sample_row_labels = _join_unique([_norm(item.get("row_label")) for item in impact_records], limit=5)
        sample_years = _join_unique([_norm(item.get("year")) for item in impact_records], limit=8)
        sample_values = _join_unique([_norm(item.get("raw_value")) for item in impact_records], limit=8)
        sample_risk_tags = _dedupe_preserve(
            [
                tag
                for item in impact_records
                for tag in _split_tags(item.get("risk_tags_before"))
            ]
        )

        affected_candidate_count = int(instruction_row.get("affected_candidate_count") or 0)
        estimated_trusted_gain = int(gate_row.get("estimated_trusted_candidate_gain") or 0)
        estimated_review_reduction = int(gate_row.get("estimated_review_reduction") or 0)
        full_trusted_gain = 0
        if not matched_df.empty and "decision_after" in matched_df.columns:
            full_trusted_gain = int(
                matched_df["decision_after"].astype(str).eq("trusted_preview").sum()
            )
        elif not matched_df.empty and "split_decision" in matched_df.columns:
            full_trusted_gain = int(
                matched_df["split_decision"].astype(str).eq("trusted_preview").sum()
            )

        if instruction_type == "ACCEPT_ALIAS_SUGGESTION_FOR_REPLAY":
            trusted_gain = full_trusted_gain or estimated_trusted_gain or affected_candidate_count
            review_reduction = trusted_gain or estimated_review_reduction
            alias_rows.append(
                {
                    "proposal_id": proposal_id,
                    "source_case_id": _norm(instruction_row.get("case_id")),
                    "normalized_label": _norm(instruction_row.get("normalized_label")),
                    "proposed_metric_code": _norm(instruction_row.get("proposed_metric_code")),
                    "proposed_metric_family": _norm(instruction_row.get("proposed_metric_family")),
                    "confidence_label": _norm(instruction_row.get("confidence_label")),
                    "affected_candidate_count": affected_candidate_count,
                    "trusted_gain": trusted_gain,
                    "review_reduction": review_reduction,
                    "sample_table_titles": sample_table_titles,
                    "sample_row_labels": sample_row_labels,
                    "sample_years": sample_years,
                    "sample_values": sample_values,
                    "risk_flags": _proposal_risk_flags(instruction_type, sample_risk_tags),
                    "recommended_human_decision": "NEEDS_CONFIRMATION",
                    "reviewer_comment": "",
                }
            )
        elif instruction_type == "CLASSIFY_OUT_OF_SCOPE_FOR_REPLAY":
            out_scope_rows.append(
                {
                    "proposal_id": proposal_id,
                    "source_case_id": _norm(instruction_row.get("case_id")),
                    "normalized_label": _norm(instruction_row.get("normalized_label")),
                    "reason": _norm(gate_row.get("reason")) or "clear_out_of_scope_context_and_semantic_support",
                    "affected_candidate_count": affected_candidate_count,
                    "review_reduction": estimated_review_reduction or affected_candidate_count,
                    "sample_table_titles": sample_table_titles,
                    "sample_row_labels": sample_row_labels,
                    "sample_values": sample_values,
                    "risk_flags": _proposal_risk_flags(instruction_type, sample_risk_tags),
                    "recommended_human_decision": "NEEDS_CONFIRMATION",
                    "reviewer_comment": "",
                }
            )
        elif instruction_type == "ACCEPT_UNIT_INFERENCE_FOR_REPLAY":
            trusted_gain = full_trusted_gain or estimated_trusted_gain
            unit_rows.append(
                {
                    "proposal_id": proposal_id,
                    "source_case_id": _norm(instruction_row.get("case_id")),
                    "normalized_label": _norm(instruction_row.get("normalized_label")),
                    "proposed_unit": _norm(instruction_row.get("proposed_unit")),
                    "confidence_label": _norm(instruction_row.get("confidence_label")),
                    "affected_candidate_count": affected_candidate_count,
                    "trusted_gain": trusted_gain,
                    "review_reduction": estimated_review_reduction or trusted_gain,
                    "sample_table_titles": sample_table_titles,
                    "sample_row_labels": sample_row_labels,
                    "sample_years": sample_years,
                    "sample_values": sample_values,
                    "risk_flags": _proposal_risk_flags(instruction_type, sample_risk_tags),
                    "recommended_human_decision": "NEEDS_CONFIRMATION",
                    "reviewer_comment": "",
                }
            )
        elif instruction_type == "REJECT_NOISE_FOR_REPLAY":
            rejected_noise_rows.append(
                {
                    "proposal_id": proposal_id,
                    "source_case_id": _norm(instruction_row.get("case_id")),
                    "normalized_label": _norm(instruction_row.get("normalized_label")),
                    "reason": _norm(gate_row.get("reason")) or "deterministic_gate_rejected_as_noise",
                    "affected_candidate_count": affected_candidate_count,
                    "review_reduction": estimated_review_reduction or affected_candidate_count,
                    "sample_table_titles": sample_table_titles,
                    "sample_row_labels": sample_row_labels,
                    "sample_values": sample_values,
                    "risk_flags": _proposal_risk_flags(instruction_type, sample_risk_tags),
                    "recommended_human_decision": "NEEDS_CONFIRMATION",
                    "reviewer_comment": "",
                }
            )

        if matched_df.empty and affected_candidate_count > 0:
            trace_failures += 1

    alias_df = pd.DataFrame(alias_rows).fillna("")
    out_scope_df = pd.DataFrame(out_scope_rows).fillna("")
    unit_df = pd.DataFrame(unit_rows).fillna("")
    rejected_noise_df = pd.DataFrame(rejected_noise_rows).fillna("")
    candidate_impact_df = pd.DataFrame(candidate_impact_rows).fillna("")

    if remaining_review_burden_df.empty:
        remaining_review_burden_df = pd.DataFrame(
            [
                {
                    "review_reason": "UNAVAILABLE",
                    "candidate_count": int(apply_summary.get("remaining_manual_review_count") or 0),
                    "unique_table_count": "",
                    "unique_label_count": "",
                    "sample_labels": "",
                    "recommended_next_action": "manual_review",
                }
            ]
        )

    human_review_checklist_df = pd.DataFrame(
        [
            {
                "checklist_id": "check::001",
                "review_area": "alias_mapping",
                "question": "Does the proposed metric code reflect the same financial meaning across sample tables?",
                "required_evidence": "Confirm row labels, table titles, years, and values align with the proposed canonical metric.",
                "decision_options": "APPROVE_ALIAS | REJECT_ALIAS | NEEDS_MORE_CONTEXT",
            },
            {
                "checklist_id": "check::002",
                "review_area": "out_of_scope",
                "question": "Is the row clearly non-core or not intended for trusted financial metric mapping?",
                "required_evidence": "Confirm sample table context shows valuation roster, ticker, peer comparison, or non-core statement detail usage.",
                "decision_options": "APPROVE_OUT_OF_SCOPE | REJECT_OUT_OF_SCOPE | NEEDS_MORE_CONTEXT",
            },
            {
                "checklist_id": "check::003",
                "review_area": "unit_inference",
                "question": "Is the inferred unit directly supported by title, header, or row label evidence?",
                "required_evidence": "Check source unit text in the original sampled table context before approval.",
                "decision_options": "APPROVE_UNIT | REJECT_UNIT | NEEDS_MORE_CONTEXT",
            },
            {
                "checklist_id": "check::004",
                "review_area": "noise_rejection",
                "question": "Would rejecting this label remove only non-metric noise and not a legitimate review candidate?",
                "required_evidence": "Check sampled row content and confirm it is structural or noise-only.",
                "decision_options": "APPROVE_REJECTION | REJECT_REJECTION | NEEDS_MORE_CONTEXT",
            },
        ]
    )

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "sandbox_only",
                "detail": "322G proposals are derived from sandbox replay outputs and do not update official mapping, overrides, or production pipeline behavior.",
            },
            {
                "limitation": "human_confirmation_required",
                "detail": "Every proposal remains in NEEDS_CONFIRMATION state until a reviewer validates semantic correctness and business scope.",
            },
            {
                "limitation": "out_of_scope_proposals_are_context_sensitive",
                "detail": "Some balance-sheet detail labels may still require reviewer judgment even when the deterministic gate accepted out-of-scope replay.",
            },
        ]
    )

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "apply30_summary_ready",
        "PASS" if bool(apply_summary) else "FAIL",
        _norm(apply_summary.get("output_dir")) or "missing 322F summary json",
    )
    add_qa(
        "trust_split_summary_ready",
        "PASS" if bool(trust_summary) else "FAIL",
        _norm(trust_summary.get("output_dir")) or "missing 322B2 summary json",
    )
    add_qa(
        "accepted_instruction_count_reconciles_with_322f",
        "PASS" if int(len(accepted_df)) == int(apply_summary.get("replay_allowed_instruction_count") or 0) else "FAIL",
        f"accepted_df={len(accepted_df)} summary={apply_summary.get('replay_allowed_instruction_count', 0)}",
    )
    add_qa(
        "proposal_total_reconciles_with_accepted_instructions",
        "PASS" if int(len(accepted_df)) == int(len(alias_df) + len(out_scope_df) + len(unit_df) + len(rejected_noise_df)) else "FAIL",
        f"accepted_df={len(accepted_df)} proposal_total={len(alias_df) + len(out_scope_df) + len(unit_df) + len(rejected_noise_df)}",
    )
    add_qa(
        "all_proposals_traceable_to_322f_accepted_instruction",
        "PASS" if trace_failures == 0 else "FAIL",
        f"trace_failures={trace_failures}",
    )
    add_qa(
        "alias_trusted_gain_reconciles_with_322f",
        "PASS" if _safe_numeric_sum(alias_df, "trusted_gain") == int(apply_summary.get("trusted_gain_322f") or 0) else "FAIL",
        f"alias_trusted_gain={_safe_numeric_sum(alias_df, 'trusted_gain')} summary={apply_summary.get('trusted_gain_322f', 0)}",
    )
    calculated_review_reduction = (
        _safe_numeric_sum(alias_df, "review_reduction")
        + _safe_numeric_sum(out_scope_df, "review_reduction")
        + _safe_numeric_sum(unit_df, "review_reduction")
        + _safe_numeric_sum(rejected_noise_df, "review_reduction")
    )
    add_qa(
        "review_reduction_reconciles_with_322f",
        "PASS" if calculated_review_reduction == int(apply_summary.get("review_reduction_322f") or 0) else "FAIL",
        f"proposal_review_reduction={calculated_review_reduction} summary={apply_summary.get('review_reduction_322f', 0)}",
    )
    add_qa(
        "no_formal_mapping_override_write_required",
        "PASS",
        "322G produces proposal tables only and does not modify data/mapping or data/overrides.",
    )
    add_qa(
        "no_recognizer_or_llm_execution_required",
        "PASS",
        "322G reads existing 322F/322B2 outputs only.",
    )
    add_qa(
        "322f_qa_fail_count_is_zero",
        "PASS" if int(apply_summary.get("qa_fail_count") or 0) == 0 else "FAIL",
        f"322f_qa_fail_count={apply_summary.get('qa_fail_count', 0)}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    summary = {
        "stage": "322G",
        "output_dir": "",
        "accepted_instruction_count": int(len(accepted_df)),
        "proposal_total_count": int(len(alias_df) + len(out_scope_df) + len(unit_df) + len(rejected_noise_df)),
        "alias_mapping_proposal_count": int(len(alias_df)),
        "out_of_scope_proposal_count": int(len(out_scope_df)),
        "unit_inference_proposal_count": int(len(unit_df)),
        "rejected_noise_proposal_count": int(len(rejected_noise_df)),
        "candidate_impact_sample_count": int(len(candidate_impact_df)),
        "alias_affected_candidate_count": _safe_numeric_sum(alias_df, "affected_candidate_count"),
        "out_of_scope_affected_candidate_count": _safe_numeric_sum(out_scope_df, "affected_candidate_count"),
        "unit_inference_affected_candidate_count": _safe_numeric_sum(unit_df, "affected_candidate_count"),
        "rejected_noise_affected_candidate_count": _safe_numeric_sum(rejected_noise_df, "affected_candidate_count"),
        "trusted_gain_total": _safe_numeric_sum(alias_df, "trusted_gain"),
        "review_reduction_total": calculated_review_reduction,
        "remaining_manual_review_count_after_322f": int(apply_summary.get("remaining_manual_review_count") or 0),
        "selected_core_trusted_rate_after_322f": float(apply_summary.get("selected_core_trusted_rate_after_322f") or 0),
        "selected_core_trusted_rate_before_322f": float(apply_summary.get("selected_core_trusted_rate_before_322f") or 0),
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "semantic_mapping_proposals_decision": (
            "SEMANTIC_MAPPING_PROPOSALS_322G_READY_FOR_HUMAN_CONFIRMATION"
            if qa_fail_count == 0 and len(accepted_df) > 0
            else "SEMANTIC_MAPPING_PROPOSALS_322G_BLOCKED_BY_QA_FAILURE"
        ),
    }

    return {
        "summary": summary,
        "accepted_instructions_df": accepted_df,
        "alias_mapping_proposals_df": alias_df,
        "out_of_scope_proposals_df": out_scope_df,
        "unit_inference_proposals_df": unit_df,
        "rejected_noise_proposals_df": rejected_noise_df,
        "candidate_impact_samples_df": candidate_impact_df,
        "human_review_checklist_df": human_review_checklist_df,
        "remaining_review_burden_after_322f_df": remaining_review_burden_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
        "qa_checks_322f_df": qa_checks_322f_df,
    }
