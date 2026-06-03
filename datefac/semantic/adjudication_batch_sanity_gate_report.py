from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


GATED_BATCH_SHEET_ORDER = [
    "summary",
    "gated_batch",
    "send_to_adjudicator",
    "human_spot_check",
    "holdouts",
    "qa_summary",
    "qa_checks",
    "known_limitations",
]

SIMPLE_ITEM_SHEET_ORDER = [
    "summary",
    "items",
    "qa_checks",
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


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame], ordered_names: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in ordered_names:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def adjudication_batch_sanity_gate_323c_notes_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Adjudication Batch Sanity Gate 323C",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Input",
        f"- input_batch_count: {summary.get('input_batch_count', 0)}",
        f"- input_alias_batch_count: {summary.get('input_alias_batch_count', 0)}",
        f"- input_scope_batch_count: {summary.get('input_scope_batch_count', 0)}",
        "",
        "## Routing",
        f"- suspicious_alias_count: {summary.get('suspicious_alias_count', 0)}",
        f"- send_to_adjudicator_count: {summary.get('send_to_adjudicator_count', 0)}",
        f"- human_spot_check_count: {summary.get('human_spot_check_count', 0)}",
        f"- holdout_category_mismatch_count: {summary.get('holdout_category_mismatch_count', 0)}",
        f"- holdout_ambiguous_count: {summary.get('holdout_ambiguous_count', 0)}",
        f"- holdout_already_official_count: {summary.get('holdout_already_official_count', 0)}",
        f"- holdout_invalid_text_count: {summary.get('holdout_invalid_text_count', 0)}",
        "",
        "## Human Spot-Check Rules",
        "- Default `human_decision` must stay `PENDING_HUMAN_SPOT_CHECK` until a reviewer edits the workbook.",
        "- Allowed human decisions: `SEND_TO_ADJUDICATOR`, `HOLDOUT`, `RECLASSIFY_AS_SCOPE_CANDIDATE`, `RECLASSIFY_AS_ALIAS_CANDIDATE`, `NEEDS_MORE_INFO`.",
        "- Human spot-check is only a routing confirmation step. It does not approve or apply semantic rules.",
        "",
        "## Safety Notes",
        "- 323C is deterministic only and does not call LLM / semantic adjudicator.",
        "- Already-official 322 labels must not be re-sent downstream.",
        "- Suspicious alias items must not be auto-sent to adjudicator.",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    examples = summary.get("highest_priority_gated_examples") or []
    if examples:
        lines.append("## Highest-Priority Gated Examples")
        for item in examples:
            reasons = " | ".join(item.get("sanity_reasons", []) or [])
            lines.append(
                f"- {item.get('batch_item_id', '')} | {item.get('candidate_type', '')} | {item.get('repaired_label', '')} | {item.get('sanity_bucket', '')} | priority={item.get('priority_score', '')} | reasons={reasons}"
            )
        lines.append("")
    blocking_reasons = summary.get("blocking_reasons") or []
    if blocking_reasons:
        lines.append("## Blocking Reasons")
        for reason in blocking_reasons:
            lines.append(f"- {reason}")
        lines.append("")
    return "\n".join(lines)
