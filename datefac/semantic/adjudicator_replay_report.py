from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "replay_instruction_inventory",
    "candidate_replay_diff",
    "trusted_preview_322e",
    "review_required_preview_322e",
    "rejected_preview_322e",
    "review_reduction_by_instruction",
    "remaining_review_burden_322e",
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
                "detail": "322E replay is sandbox-only and does not update production mapping, delivery, overrides, or official assets.",
            },
            {
                "limitation": "small_sample",
                "detail": "Current replay is based on a 5-case semantic adjudicator apply batch and may understate later batch behaviors.",
            },
            {
                "limitation": "human_confirmation_recommended",
                "detail": "Even accepted replay instructions should still receive human confirmation before any official mapping change.",
            },
        ]
    )


def replay_decision(summary: Dict[str, Any]) -> str:
    if int(summary.get("qa_fail_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_REPLAY_BLOCKED_BY_QA_FAILURE"
    if int(summary.get("replay_allowed_instruction_count", 0)) > 0 and int(summary.get("review_reduction_322e", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_REPLAY_READY_FOR_322F_LARGER_BATCH"
    if int(summary.get("replay_allowed_instruction_count", 0)) > 0:
        return "SEMANTIC_ADJUDICATOR_REPLAY_PARTIAL_NO_REDUCTION"
    return "SEMANTIC_ADJUDICATOR_REPLAY_NO_ACCEPTED_INSTRUCTIONS"


def build_report_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Semantic Adjudicator Replay 322E",
        "",
        "## Decision",
        f"- semantic_adjudicator_replay_decision: {summary.get('semantic_adjudicator_replay_decision', '')}",
        "",
        "## Counts",
        f"- replay_instruction_count: {summary.get('replay_instruction_count', 0)}",
        f"- replay_allowed_instruction_count: {summary.get('replay_allowed_instruction_count', 0)}",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_total_before_322e: {summary.get('trusted_total_before_322e', 0)}",
        f"- trusted_total_after_322e: {summary.get('trusted_total_after_322e', 0)}",
        f"- review_required_total_before_322e: {summary.get('review_required_total_before_322e', 0)}",
        f"- review_required_total_after_322e: {summary.get('review_required_total_after_322e', 0)}",
        f"- trusted_gain_322e: {summary.get('trusted_gain_322e', 0)}",
        f"- review_reduction_322e: {summary.get('review_reduction_322e', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    return "\n".join(lines)
