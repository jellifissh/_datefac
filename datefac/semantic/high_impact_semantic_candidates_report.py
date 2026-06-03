from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


RANKED_GROUPS_SHEET_ORDER = [
    "summary",
    "ranked_groups",
    "closed_rules_reference",
    "qa_summary",
    "qa_checks",
    "known_limitations",
]

TOP_OPPORTUNITY_SHEET_ORDER = [
    "summary",
    "top_opportunities",
    "qa_checks",
]

RISK_BUCKET_SHEET_ORDER = [
    "summary",
    "risk_buckets",
    "unit_holdouts",
    "ambiguous_holdouts",
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


def high_impact_semantic_candidates_notes_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# High-Impact Semantic Candidates Mining 323A",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Loaded Counts",
        f"- loaded_candidate_count: {summary.get('loaded_candidate_count', 0)}",
        f"- loaded_unresolved_review_required_candidate_count: {summary.get('loaded_unresolved_review_required_candidate_count', 0)}",
        f"- closed_rule_count: {summary.get('closed_rule_count', 0)}",
        "",
        "## Grouped Counts",
        f"- grouped_candidate_count: {summary.get('grouped_candidate_count', 0)}",
        f"- alias_opportunity_group_count: {summary.get('alias_opportunity_group_count', 0)}",
        f"- scope_noise_group_count: {summary.get('scope_noise_group_count', 0)}",
        f"- unit_related_group_count: {summary.get('unit_related_group_count', 0)}",
        f"- ambiguous_group_count: {summary.get('ambiguous_group_count', 0)}",
        "",
        "## Top Package Counts",
        f"- top_alias_opportunity_count: {summary.get('top_alias_opportunity_count', 0)}",
        f"- top_scope_noise_opportunity_count: {summary.get('top_scope_noise_opportunity_count', 0)}",
        f"- unit_holdout_count: {summary.get('unit_holdout_count', 0)}",
        f"- ambiguous_holdout_count: {summary.get('ambiguous_holdout_count', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    examples = summary.get("highest_priority_examples") or []
    if examples:
        lines.append("## Highest-Priority Examples")
        for item in examples:
            lines.append(
                f"- {item.get('group_type_candidate', '')} | {item.get('normalized_label_display', '')} | priority={item.get('priority_score', '')} | review={item.get('affected_review_required_count', '')}"
            )
        lines.append("")
    blocking_reasons = summary.get("blocking_reasons") or []
    if blocking_reasons:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking_reasons], ""])
    lines.extend(
        [
            "## Notes",
            "- 323A is a cached-input mining stage only; it does not modify official semantic assets or production pipeline code.",
            "- Unit-related and ambiguous holdouts are intentionally separated to avoid unsafe semantic promotion.",
            "",
        ]
    )
    return "\n".join(lines)
