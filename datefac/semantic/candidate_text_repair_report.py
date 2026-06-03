from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


REPAIRED_RANKED_GROUPS_SHEET_ORDER = [
    "summary",
    "repaired_ranked_groups",
    "mojibake_groups",
    "unrepairable_holdouts",
    "qa_summary",
    "qa_checks",
    "known_limitations",
]

REPAIRED_TOP_PACKAGE_SHEET_ORDER = [
    "summary",
    "repaired_top_opportunities",
    "qa_checks",
]

REVIEW_READY_PACKAGE_SHEET_ORDER = [
    "summary",
    "review_ready_alias",
    "review_ready_scope_noise",
    "holdout_groups",
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


def candidate_text_repair_323ar_notes_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Candidate Text Repair 323A-R",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Input Readiness",
        f"- input_323a_decision: {summary.get('input_323a_decision', '')}",
        f"- input_323a_qa_fail_count: {summary.get('input_323a_qa_fail_count', 0)}",
        f"- grouped_candidate_count_323a: {summary.get('grouped_candidate_count_323a', 0)}",
        "",
        "## Mojibake Detection",
        f"- mojibake_group_count: {summary.get('mojibake_group_count', 0)}",
        f"- mojibake_top_alias_count: {summary.get('mojibake_top_alias_count', 0)}",
        f"- mojibake_top_scope_count: {summary.get('mojibake_top_scope_count', 0)}",
        f"- mojibake_sample_text_count: {summary.get('mojibake_sample_text_count', 0)}",
        "",
        "## Repair Outcome",
        f"- deterministic_repair_count: {summary.get('deterministic_repair_count', 0)}",
        f"- already_clean_count: {summary.get('already_clean_count', 0)}",
        f"- unrepairable_holdout_count: {summary.get('unrepairable_holdout_count', 0)}",
        f"- review_ready_alias_count: {summary.get('review_ready_alias_count', 0)}",
        f"- review_ready_scope_count: {summary.get('review_ready_scope_count', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    examples = summary.get("highest_priority_repaired_examples") or []
    if examples:
        lines.append("## Highest-Priority Repaired Examples")
        for item in examples:
            lines.append(
                f"- {item.get('group_type_candidate', '')} | {item.get('original_label', '')} -> {item.get('repaired_label', '')} | status={item.get('repair_status', '')} | priority={item.get('priority_score', '')}"
            )
        lines.append("")
    blocking_reasons = summary.get("blocking_reasons") or []
    if blocking_reasons:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking_reasons], ""])
    lines.extend(
        [
            "## Notes",
            "- 323A-R reads cached 323A workbooks and cached 322B2 candidate rows only.",
            "- Deterministic repair prefers already clean workbook text, then cached source text, then conservative encoding reinterpretation.",
            "- Unrepairable or unsafe groups are isolated from the review-ready package instead of being guessed.",
            "",
        ]
    )
    return "\n".join(lines)
