from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


BATCH_WORKBOOK_SHEET_ORDER = [
    "summary",
    "batch_items",
    "alias_items",
    "scope_items",
    "excluded_review_ready_items",
    "holdout_reference",
    "qa_summary",
    "qa_checks",
    "known_limitations",
]

SIMPLE_ITEM_SHEET_ORDER = [
    "summary",
    "items",
    "qa_checks",
]

HOLDOUT_SHEET_ORDER = [
    "summary",
    "excluded_review_ready_items",
    "holdout_reference",
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


def semantic_adjudication_batch_prep_323ab_review_instructions(summary: Dict[str, Any]) -> str:
    lines = [
        "# Semantic Adjudication Batch Prep 323A-B",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Batch Scope",
        f"- loaded_review_ready_alias_count: {summary.get('loaded_review_ready_alias_count', 0)}",
        f"- loaded_review_ready_scope_count: {summary.get('loaded_review_ready_scope_count', 0)}",
        f"- selected_alias_batch_count: {summary.get('selected_alias_batch_count', 0)}",
        f"- selected_scope_batch_count: {summary.get('selected_scope_batch_count', 0)}",
        f"- total_batch_count: {summary.get('total_batch_count', 0)}",
        "",
        "## Review Rules",
        "- Every item must start with `review_decision = PENDING_REVIEW`.",
        "- Do not pre-approve or auto-apply any semantic rule from this package.",
        "- Alias items are for deciding whether a repaired label safely maps to an existing selected core metric alias.",
        "- Scope items are for deciding whether a repaired label is safely out of scope for selected core metric extraction.",
        "",
        "## Allowed Decisions",
        "- Alias items: `ACCEPT_ALIAS`, `REJECT_ALIAS`, `NEEDS_MORE_INFO`, `OUT_OF_SCOPE`.",
        "- Scope items: `ACCEPT_OUT_OF_SCOPE`, `REJECT_OUT_OF_SCOPE`, `NEEDS_MORE_INFO`, `POSSIBLE_CORE_METRIC`.",
        "",
        "## Safety Notes",
        "- Unit-related holdouts, ambiguous holdouts, unrepairable holdouts, dates, stock codes, empty labels, and already-official 322 rules are excluded from this batch.",
        "- Long narrative/policy-text labels are excluded from the compact review batch even if they are human-readable.",
        "- Use the provenance and sample texts to confirm context before accepting any item.",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    examples = summary.get("highest_priority_batch_examples") or []
    if examples:
        lines.append("## Highest-Priority Examples")
        for item in examples:
            lines.append(
                f"- {item.get('candidate_type', '')} | {item.get('repaired_label', '')} | priority={item.get('priority_score', '')} | affected_review={item.get('affected_review_required_count', '')}"
            )
        lines.append("")
    blocking_reasons = summary.get("blocking_reasons") or []
    if blocking_reasons:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking_reasons], ""])
    return "\n".join(lines)
