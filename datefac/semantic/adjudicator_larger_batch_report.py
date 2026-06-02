from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "batch_selection_audit",
    "selected_label_cases_322f",
    "llm_request_inventory_322f",
    "llm_response_validation_322f",
    "deterministic_gate_results_322f",
    "replay_instruction_inventory_322f",
    "candidate_replay_diff_322f",
    "trusted_preview_322f",
    "review_required_preview_322f",
    "rejected_preview_322f",
    "review_reduction_by_instruction_322f",
    "remaining_review_burden_322f",
    "qa_checks",
    "known_limitations",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    base = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    out = base
    index = 1
    while out in used:
        suffix = f"_{index}"
        out = f"{base[:31 - len(suffix)]}{suffix}"
        index += 1
    used.add(out)
    return out


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in df.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_known_limitations_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "sandbox_only",
                "detail": "322F larger batch remains sandbox-only and does not update production mapping, delivery, overrides, or official assets.",
            },
            {
                "limitation": "dry_run_default",
                "detail": "Default validation uses dry_run only and does not call any LLM, API, cloud, or recognizer stack.",
            },
            {
                "limitation": "human_confirmation_required",
                "detail": "Even accepted replay instructions remain candidate proposals and still need human confirmation before any official mapping update.",
            },
            {
                "limitation": "selection_is_priority_weighted",
                "detail": "322F selection emphasizes likely review-burden reduction and may still leave many long-tail review labels unresolved.",
            },
        ]
    )


def larger_batch_decision(summary: Dict[str, Any]) -> str:
    if int(summary.get("qa_fail_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_322F_BLOCKED_BY_QA_FAILURE"
    if _norm(summary.get("mode")) == "dry_run" and int(summary.get("request_payload_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_322F_REQUESTS_READY_FOR_EXTERNAL_EXECUTION"
    if int(summary.get("replay_allowed_instruction_count", 0)) > 0 and int(summary.get("review_reduction_322f", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_322F_READY_FOR_HUMAN_CONFIRMED_MAPPING_PROPOSALS"
    if int(summary.get("response_available_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_322F_RESPONSES_NEED_REVIEW"
    return "SEMANTIC_ADJUDICATOR_322F_NO_RESPONSES_YET"


def build_report_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Semantic Adjudicator Larger Batch 322F",
        "",
        "## Decision",
        f"- semantic_adjudicator_larger_batch_decision: {summary.get('semantic_adjudicator_larger_batch_decision', '')}",
        "",
        "## Counts",
        f"- mode: {summary.get('mode', '')}",
        f"- selected_label_case_count: {summary.get('selected_label_case_count', 0)}",
        f"- selected_candidate_case_count: {summary.get('selected_candidate_case_count', 0)}",
        f"- request_payload_count: {summary.get('request_payload_count', 0)}",
        f"- response_available_count: {summary.get('response_available_count', 0)}",
        f"- response_schema_valid_count: {summary.get('response_schema_valid_count', 0)}",
        f"- accepted_alias_suggestion_count: {summary.get('accepted_alias_suggestion_count', 0)}",
        f"- out_of_scope_classification_count: {summary.get('out_of_scope_classification_count', 0)}",
        f"- unit_inference_accept_count: {summary.get('unit_inference_accept_count', 0)}",
        f"- replay_allowed_instruction_count: {summary.get('replay_allowed_instruction_count', 0)}",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_322f: {summary.get('trusted_gain_322f', 0)}",
        f"- review_reduction_322f: {summary.get('review_reduction_322f', 0)}",
        "",
        "## Review Burden",
        f"- remaining_unknown_metric_candidate_count: {summary.get('remaining_unknown_metric_candidate_count', 0)}",
        f"- remaining_unit_unknown_candidate_count: {summary.get('remaining_unit_unknown_candidate_count', 0)}",
        f"- remaining_manual_review_count: {summary.get('remaining_manual_review_count', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    return "\n".join(lines)
