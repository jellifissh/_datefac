from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import pandas as pd


REVIEW_WORKBOOK_SHEET_ORDER = [
    "summary",
    "review_package",
    "schema_invalid",
    "gate_failures",
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


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def scope_noise_response_schema_validation_324e_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Scope Noise Response Schema Validation 324E",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- request_count: {summary.get('request_count', 0)}",
        f"- response_count: {summary.get('response_count', 0)}",
        f"- schema_valid_count: {summary.get('schema_valid_count', 0)}",
        f"- schema_invalid_count: {summary.get('schema_invalid_count', 0)}",
        f"- accepted_for_human_confirmation_count: {summary.get('accepted_for_human_confirmation_count', 0)}",
        f"- rejected_out_of_scope_suggestion_count: {summary.get('rejected_out_of_scope_suggestion_count', 0)}",
        f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
        f"- rejected_by_deterministic_gate_count: {summary.get('rejected_by_deterministic_gate_count', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    blocking_reasons = summary.get("blocking_reasons") or []
    if blocking_reasons:
        lines.append("## Blocking Reasons")
        for reason in blocking_reasons:
            lines.append(f"- {reason}")
        lines.append("")
    return "\n".join(lines)
