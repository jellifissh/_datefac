from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "alias_approvals",
    "scope_approvals",
    "all_approval_records",
    "before_after_preview",
    "rollback_plan",
    "qa_summary",
    "qa_checks",
    "review_instructions",
    "no_apply_proof",
    "known_limitations",
]

REVIEWED_SHEET_ORDER = [
    "reviewed_summary",
    "approved_records",
    "rejected_records",
    "needs_more_info_records",
    "all_reviewed_approval_records",
    "reviewed_qa_summary",
    "reviewed_qa_checks",
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
    sheet_order = SHEET_ORDER if mode == "prepare" else REVIEWED_SHEET_ORDER
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in sheet_order:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def controlled_official_proposal_human_approval_324k_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Controlled Official Proposal Human Approval 324K",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- approval_record_count: {summary.get('approval_record_count', 0)}",
        f"- alias_approval_count: {summary.get('alias_approval_count', 0)}",
        f"- scope_approval_count: {summary.get('scope_approval_count', 0)}",
        f"- pending_count: {summary.get('pending_count', 0)}",
        f"- approved_count: {summary.get('approved_count', 0)}",
        f"- rejected_count: {summary.get('rejected_count', 0)}",
        f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
        "",
        "## Decision Distribution",
        f"- decision_distribution: {summary.get('decision_distribution', {})}",
        "",
        "## Safety",
        f"- approval_package_only_no_apply_confirmed: {summary.get('approval_package_only_no_apply_confirmed', False)}",
        f"- official_assets_not_modified_confirmed: {summary.get('official_assets_not_modified_confirmed', False)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    warnings = summary.get("carried_warnings") or []
    if warnings:
        lines.extend(["## Carried Warnings", *[f"- {item}" for item in warnings], ""])
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    lines.extend(
        [
            "## Notes",
            "- 324K prepares a human approval package only.",
            "- 324K does not apply semantic rules and does not modify official assets.",
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
