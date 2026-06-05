from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "confirmation_records",
    "confirmed",
    "rejected_or_needs_more_info",
    "qa_checks",
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
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
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


def alias_human_confirmation_325h_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Alias Human Confirmation 325H",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        f"- mode: {summary.get('mode', '')}",
        "",
        "## Counts",
        f"- confirmation_record_count: {summary.get('confirmation_record_count', 0)}",
        f"- pending_count: {summary.get('pending_count', 0)}",
        f"- confirmed_count: {summary.get('confirmed_count', 0)}",
        f"- rejected_count: {summary.get('rejected_count', 0)}",
        f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
        "",
        "## Safety",
        f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
        f"- llm_or_adjudicator_called: {summary.get('llm_or_adjudicator_called', False)}",
        f"- official_rule_candidates_created: {summary.get('official_rule_candidates_created', False)}",
        f"- sandbox_replay_package_created: {summary.get('sandbox_replay_package_created', False)}",
        "",
        "## QA",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
        "## Warning",
        "- Confirmation does not apply official rules. Confirmed suggestions must go through 325I sandbox replay next.",
        "",
    ]
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {reason}" for reason in blocking], ""])
    return "\n".join(lines)
