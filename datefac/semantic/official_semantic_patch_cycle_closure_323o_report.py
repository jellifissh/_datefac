from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "cycle_summary",
    "stage_alignment",
    "warnings",
    "remaining_risks",
    "next_cycle_recommendations",
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


def official_semantic_patch_cycle_closure_323o_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Official Semantic Patch Cycle Closure 323O",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## 322 Cycle Summary",
        f"- rules_322: {summary.get('rules_322', 0)}",
        f"- trusted_gain_322: {summary.get('trusted_gain_322', 0)}",
        f"- review_reduction_322: {summary.get('review_reduction_322', 0)}",
        f"- out_of_scope_or_rejected_gain_322: {summary.get('out_of_scope_or_rejected_gain_322', 0)}",
        "",
        "## 323 Cycle Summary",
        f"- rules_323: {summary.get('rules_323', 0)}",
        f"- trusted_gain_323: {summary.get('trusted_gain_323', 0)}",
        f"- review_reduction_323: {summary.get('review_reduction_323', 0)}",
        f"- out_of_scope_or_rejected_gain_323: {summary.get('out_of_scope_or_rejected_gain_323', 0)}",
        f"- warning_323: {summary.get('warning_323', '')}",
        "",
        "## Combined Impact",
        f"- combined_rules: {summary.get('combined_rules', 0)}",
        f"- combined_trusted_gain: {summary.get('combined_trusted_gain', 0)}",
        f"- combined_review_reduction: {summary.get('combined_review_reduction', 0)}",
        f"- combined_out_of_scope_or_rejected_gain: {summary.get('combined_out_of_scope_or_rejected_gain', 0)}",
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
            "- 323O closes the 323 official semantic patch cycle using existing output summaries only.",
            "- 323O does not modify official assets, production pipeline code, or cached stage outputs.",
            "",
        ]
    )
    return "\n".join(lines)


def official_semantic_patch_cycle_closure_323o_decision_markdown(decision_json: Dict[str, Any]) -> str:
    lines = [
        "# 323O Decision",
        "",
        f"- decision: {decision_json.get('decision', '')}",
        f"- qa_fail_count: {decision_json.get('qa_fail_count', 0)}",
        f"- warning_323: {decision_json.get('warning_323', '')}",
        f"- next_step: {decision_json.get('next_step', '')}",
    ]
    blocking = decision_json.get("blocking_reasons") or []
    if blocking:
        lines.extend(["", "## Blocking Reasons", *[f"- {item}" for item in blocking]])
    lines.append("")
    return "\n".join(lines)
