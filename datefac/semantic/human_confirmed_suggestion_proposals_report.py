from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd


PREPARE_SHEET_ORDER = [
    "summary",
    "confirmation_records",
    "alias_suggestions",
    "scope_suggestions",
    "qa_checks",
    "review_instructions",
]

REVIEWED_SHEET_ORDER = [
    "reviewed_summary",
    "confirmed_suggestions",
    "rejected_suggestions",
    "needs_more_info",
    "all_reviewed",
    "reviewed_qa",
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


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame], mode: str = "prepare") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    sheet_order = PREPARE_SHEET_ORDER if mode == "prepare" else REVIEWED_SHEET_ORDER
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in sheet_order:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def human_confirmed_suggestion_proposals_report_markdown(summary: Dict[str, Any]) -> str:
    mode = _norm(summary.get("mode")) or "prepare"
    lines: List[str] = [
        "# Human-Confirmed Suggestion Proposals 323G",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        f"- mode: {mode}",
        "",
        "## Counts",
        f"- accepted_suggestion_count: {summary.get('accepted_suggestion_count', summary.get('confirmation_record_count', 0))}",
        f"- alias_accepted_suggestion_count: {summary.get('alias_accepted_suggestion_count', 0)}",
        f"- scope_accepted_suggestion_count: {summary.get('scope_accepted_suggestion_count', 0)}",
        f"- confirmation_record_count: {summary.get('confirmation_record_count', 0)}",
        "",
        "## Decision Distribution",
        f"- decision_distribution: {summary.get('decision_distribution', {})}",
        "",
        "## Safety",
        f"- proposal_package_only_no_apply_confirmed: {summary.get('proposal_package_only_no_apply_confirmed', False)}",
        f"- official_assets_not_modified_confirmed: {summary.get('official_assets_not_modified_confirmed', False)}",
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
            "- 323G creates human confirmation records only.",
            "- Confirmed items still require sandbox replay in a later stage.",
            "",
        ]
    )
    return "\n".join(lines)


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
