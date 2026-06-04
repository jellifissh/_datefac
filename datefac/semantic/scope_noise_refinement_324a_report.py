from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "refined_scope_candidates",
    "excluded_source_groups",
    "excluded_reason_summary",
    "duplicate_provenance",
    "review_instructions",
    "qa_summary",
    "qa_checks",
    "known_limitations",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


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


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def scope_noise_refinement_324a_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Scope Noise Candidate Refinement 324A",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- input_scope_group_count: {summary.get('input_scope_group_count', 0)}",
        f"- review_ready_scope_group_count_323ar: {summary.get('review_ready_scope_group_count_323ar', 0)}",
        f"- excluded_already_official_count: {summary.get('excluded_already_official_count', 0)}",
        f"- refined_scope_candidate_count: {summary.get('refined_scope_candidate_count', 0)}",
        f"- holdout_count: {summary.get('holdout_count', 0)}",
        "",
        "## Exclusion Highlights",
        f"- excluded_323m_scope_rule_count: {summary.get('excluded_323m_scope_rule_count', 0)}",
        f"- excluded_duplicate_accounted_count: {summary.get('excluded_duplicate_accounted_count', 0)}",
        f"- excluded_unrepairable_holdout_count: {summary.get('excluded_unrepairable_holdout_count', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    examples = summary.get("top_examples") or []
    if examples:
        lines.extend(["## Top Examples"])
        for item in examples:
            lines.append(
                f"- {item.get('refined_scope_candidate_id', '')}: {item.get('repaired_label', '')} "
                f"(affected_review_required_count={item.get('affected_review_required_count', 0)}, "
                f"source_group_count={item.get('source_group_count', 0)})"
            )
        lines.append("")
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    lines.extend(
        [
            "## Notes",
            "- 324A is a scope-only refinement stage for the next cycle and does not reopen alias, unit, or ambiguous paths.",
            "- 324A uses cached 323P/323A/323A-R/323N outputs only and does not modify official assets.",
            "",
        ]
    )
    return "\n".join(lines)


def scope_noise_refinement_324a_decision_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# 324A Decision",
        "",
        f"- decision: {summary.get('decision', '')}",
        f"- refined_scope_candidate_count: {summary.get('refined_scope_candidate_count', 0)}",
        f"- holdout_count: {summary.get('holdout_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
    ]
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["", "## Blocking Reasons", *[f"- {item}" for item in blocking]])
    lines.append("")
    return "\n".join(lines)
