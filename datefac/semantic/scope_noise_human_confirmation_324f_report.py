from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


PREPARE_SHEET_ORDER = [
    "summary",
    "confirmation_records",
    "qa_checks",
    "review_instructions",
]

REVIEWED_SHEET_ORDER = [
    "reviewed_summary",
    "confirmed_records",
    "rejected_records",
    "needs_more_info",
    "all_reviewed_records",
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


def scope_noise_human_confirmation_324f_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Scope Noise Human Confirmation 324F",
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
        f"- validate_reviewed_mode_implemented: {summary.get('validate_reviewed_mode_implemented', False)}",
        f"- official_assets_not_modified: {summary.get('official_assets_not_modified', False)}",
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
            "- 324F is a human confirmation stage only and does not call an adjudicator or apply rules.",
            "- This long narrative label must not be auto-promoted even if it was accepted by 324E.",
            "- Any confirmed record still requires sandbox replay in 324G.",
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
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value
