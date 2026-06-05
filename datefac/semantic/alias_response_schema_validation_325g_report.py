from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


WORKBOOK_SHEET_ORDER = [
    "summary",
    "validated_suggestions",
    "accepted_for_human_confirmation",
    "rejected_or_needs_more_info",
    "deterministic_gate_report",
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


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame], ordered_names: List[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    order = ordered_names or WORKBOOK_SHEET_ORDER
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in order:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def alias_response_schema_validation_325g_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Alias Response Schema Validation 325G",
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
        f"- rejected_by_schema_count: {summary.get('rejected_by_schema_count', 0)}",
        f"- rejected_by_deterministic_gate_count: {summary.get('rejected_by_deterministic_gate_count', 0)}",
        f"- rejected_alias_suggestion_count: {summary.get('rejected_alias_suggestion_count', 0)}",
        f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
        "",
        "## Safety",
        f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
        f"- llm_or_adjudicator_called: {summary.get('llm_or_adjudicator_called', False)}",
        f"- official_rule_candidates_created: {summary.get('official_rule_candidates_created', False)}",
        f"- controlled_official_proposals_created: {summary.get('controlled_official_proposals_created', False)}",
        f"- sandbox_replay_package_created: {summary.get('sandbox_replay_package_created', False)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    reasons = summary.get("deterministic_gate_failure_reasons") or {}
    if reasons:
        lines.append("## Deterministic Gate Failures")
        for reason, count in reasons.items():
            lines.append(f"- {reason}: {count}")
        lines.append("")
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.append("## Blocking Reasons")
        lines.extend(f"- {reason}" for reason in blocking)
        lines.append("")
    return "\n".join(lines)
