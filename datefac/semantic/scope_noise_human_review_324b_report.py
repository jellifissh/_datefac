from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


PREPARE_SHEET_ORDER = [
    "summary",
    "scope_review_records",
    "qa_checks",
    "review_instructions",
]

REVIEWED_SHEET_ORDER = [
    "reviewed_summary",
    "confirmed_scope_noise",
    "escalated_to_adjudicator",
    "rejected_scope_noise",
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


def scope_noise_human_review_324b_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Scope Noise Human Review 324B",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        f"- mode: {summary.get('mode', '')}",
        "",
        "## Counts",
        f"- review_record_count: {summary.get('review_record_count', 0)}",
        f"- pending_count: {summary.get('pending_count', 0)}",
        f"- confirmed_scope_noise_count: {summary.get('confirmed_scope_noise_count', 0)}",
        f"- rejected_scope_noise_count: {summary.get('rejected_scope_noise_count', 0)}",
        f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
        f"- escalate_to_adjudicator_count: {summary.get('escalate_to_adjudicator_count', 0)}",
        "",
        "## Safety",
        f"- risk_flags_carried_forward: {summary.get('risk_flags_carried_forward', '')}",
        f"- validate_reviewed_mode_implemented: {summary.get('validate_reviewed_mode_implemented', False)}",
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
            "- 324B is a human review stage only and does not call an adjudicator or apply rules.",
            "- LONG_LABEL_REVIEW_REQUIRED must be treated conservatively and never as a low-risk automatic exclusion.",
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
