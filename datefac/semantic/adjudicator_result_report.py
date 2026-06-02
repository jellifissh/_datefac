from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "selected_label_cases",
    "selected_candidate_cases",
    "llm_request_inventory",
    "llm_response_validation",
    "deterministic_gate_results",
    "alias_replay_instructions",
    "out_of_scope_replay_instructions",
    "unit_inference_replay_instructions",
    "manual_review_after_llm",
    "estimated_impact_322d",
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
                "detail": "322D limited execution is sandbox-only and does not modify production mapping or delivery files.",
            },
            {
                "limitation": "dry_run_no_model_call",
                "detail": "Default validation is dry_run only and does not call any model, API, or cloud service.",
            },
            {
                "limitation": "human_confirmation_required",
                "detail": "Even accepted alias or scope replay instructions still require later human confirmation before any replay application.",
            },
        ]
    )


def limited_decision(summary: Dict[str, Any]) -> str:
    if int(summary.get("qa_fail_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_LIMITED_BLOCKED_BY_QA_FAILURE"
    if _norm(summary.get("mode")) == "dry_run" and int(summary.get("request_payload_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_LIMITED_REQUESTS_READY_FOR_EXTERNAL_EXECUTION"
    accepted_total = (
        int(summary.get("accepted_alias_suggestion_count", 0))
        + int(summary.get("out_of_scope_classification_count", 0))
        + int(summary.get("unit_inference_accept_count", 0))
    )
    if int(summary.get("response_schema_valid_count", 0)) > 0 and accepted_total > 0:
        return "SEMANTIC_ADJUDICATOR_LIMITED_READY_FOR_322E_REPLAY"
    if int(summary.get("response_available_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_LIMITED_RESPONSES_NEED_REVIEW"
    return "SEMANTIC_ADJUDICATOR_LIMITED_NO_RESPONSES_YET"


def build_report_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Semantic Adjudicator Limited Execution 322D",
        "",
        "## Decision",
        f"- semantic_adjudicator_limited_decision: {summary.get('semantic_adjudicator_limited_decision', '')}",
        "",
        "## Counts",
        f"- mode: {summary.get('mode', '')}",
        f"- selected_label_case_count: {summary.get('selected_label_case_count', 0)}",
        f"- selected_candidate_case_count: {summary.get('selected_candidate_case_count', 0)}",
        f"- request_payload_count: {summary.get('request_payload_count', 0)}",
        f"- response_available_count: {summary.get('response_available_count', 0)}",
        f"- accepted_alias_suggestion_count: {summary.get('accepted_alias_suggestion_count', 0)}",
        f"- out_of_scope_classification_count: {summary.get('out_of_scope_classification_count', 0)}",
        f"- unit_inference_accept_count: {summary.get('unit_inference_accept_count', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    return "\n".join(lines)
