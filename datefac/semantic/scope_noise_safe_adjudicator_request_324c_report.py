from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd


EVIDENCE_WORKBOOK_SHEET_ORDER = [
    "summary",
    "request_items",
    "evidence",
    "response_schema",
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
        out = f"{base[: 31 - len(suffix)]}{suffix}"
        index += 1
    used.add(out)
    return out


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


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in EVIDENCE_WORKBOOK_SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_to_jsonable(row), ensure_ascii=False))
            handle.write("\n")


def scope_noise_safe_adjudicator_request_324c_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Scope Noise Safe Adjudicator Request 324C",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        f"- mode: {summary.get('mode', '')}",
        f"- llm_or_adjudicator_called: {summary.get('llm_or_adjudicator_called', False)}",
        "",
        "## Counts",
        f"- request_count: {summary.get('request_count', 0)}",
        f"- scope_noise_request_count: {summary.get('scope_noise_request_count', 0)}",
        "",
        "## Safety",
        f"- risk_flags_carried_forward: {summary.get('risk_flags_carried_forward', '')}",
        f"- allowed_response_labels: {summary.get('allowed_response_labels', '')}",
        "- This package is request-prep only. It does not apply rules or create sandbox replay candidates.",
        "- The candidate is a long narrative label and must not be auto-accepted as scope noise.",
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
    return "\n".join(lines)
