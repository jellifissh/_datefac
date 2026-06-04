from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "closed_cycle_impact",
    "remaining_burden",
    "option_comparison",
    "recommendations",
    "cautions",
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
    path.write_text(
        json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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


def remaining_burden_planning_323p_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Remaining Burden And Next Cycle Planning 323P",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Closed-Cycle Impact",
        f"- official_rule_count_total: {summary.get('official_rule_count_total', 0)}",
        f"- trusted_gain_total: {summary.get('trusted_gain_total', 0)}",
        f"- review_reduction_total: {summary.get('review_reduction_total', 0)}",
        "",
        "## Remaining Burden",
        f"- remaining_unknown_metric_candidate_count: {summary.get('remaining_unknown_metric_candidate_count', 0)}",
        f"- remaining_unit_unknown_candidate_count: {summary.get('remaining_unit_unknown_candidate_count', 0)}",
        f"- remaining_manual_review_count: {summary.get('remaining_manual_review_count', 0)}",
        f"- historical_duplicate_warning_status: {summary.get('historical_duplicate_warning_status', '')}",
        "",
        "## Direction Comparison",
        f"- alias_candidate_group_count: {summary.get('alias_candidate_group_count', 0)}",
        f"- scope_noise_candidate_group_count: {summary.get('scope_noise_candidate_group_count', 0)}",
        f"- unit_related_holdout_group_count: {summary.get('unit_related_holdout_group_count', 0)}",
        f"- ambiguous_holdout_group_count: {summary.get('ambiguous_holdout_group_count', 0)}",
        f"- duplicate_cleanup_candidate_count: {summary.get('duplicate_cleanup_candidate_count', 0)}",
        "",
        "## Recommendation",
        f"- primary_next_cycle_direction: {summary.get('primary_next_cycle_direction', '')}",
        f"- secondary_next_cycle_direction: {summary.get('secondary_next_cycle_direction', '')}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    lines.extend(
        [
            "## Notes",
            "- 323P is a planning-only stage and does not start the next cycle.",
            "- 323P uses existing summary outputs only and does not reopen adjudication or official patch application.",
            "",
        ]
    )
    return "\n".join(lines)


def remaining_burden_planning_323p_decision_markdown(decision_json: Dict[str, Any]) -> str:
    lines = [
        "# 323P Decision",
        "",
        f"- decision: {decision_json.get('decision', '')}",
        f"- qa_fail_count: {decision_json.get('qa_fail_count', 0)}",
        f"- primary_next_cycle_direction: {decision_json.get('primary_next_cycle_direction', '')}",
        f"- secondary_next_cycle_direction: {decision_json.get('secondary_next_cycle_direction', '')}",
        f"- do_not_start_next_cycle_yet: {decision_json.get('do_not_start_next_cycle_yet', False)}",
    ]
    blocking = decision_json.get("blocking_reasons") or []
    if blocking:
        lines.extend(["", "## Blocking Reasons", *[f"- {item}" for item in blocking]])
    lines.append("")
    return "\n".join(lines)
