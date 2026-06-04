from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Set

import pandas as pd


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


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]] | pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(rows, pd.DataFrame):
        records = rows.to_dict(orient="records")
    else:
        records = list(rows)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def human_confirmed_sandbox_replay_report_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Human Confirmed Sandbox Replay 323H",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Confirmed Suggestions",
        f"- total_confirmed_suggestion_count: {summary.get('total_confirmed_suggestion_count', 0)}",
        f"- alias_confirmed_suggestion_count: {summary.get('alias_confirmed_suggestion_count', 0)}",
        f"- scope_confirmed_suggestion_count: {summary.get('scope_confirmed_suggestion_count', 0)}",
        "",
        "## Sandbox Rule Counts",
        f"- sandbox_rule_count: {summary.get('sandbox_rule_count', 0)}",
        f"- sandbox_alias_rule_count: {summary.get('sandbox_alias_rule_count', 0)}",
        f"- sandbox_scope_rule_count: {summary.get('sandbox_scope_rule_count', 0)}",
        f"- effective_unique_rule_count: {summary.get('effective_unique_rule_count', 0)}",
        f"- duplicate_rule_count: {summary.get('duplicate_rule_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        "",
        "## Replay Impact",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_323h: {summary.get('trusted_gain_323h', 0)}",
        f"- review_reduction_323h: {summary.get('review_reduction_323h', 0)}",
        f"- out_of_scope_or_rejected_gain_323h: {summary.get('out_of_scope_or_rejected_gain_323h', 0)}",
        f"- alias_trusted_gain_323h: {summary.get('alias_trusted_gain_323h', 0)}",
        f"- scope_review_reduction_323h: {summary.get('scope_review_reduction_323h', 0)}",
        f"- scope_out_of_scope_or_rejected_gain_323h: {summary.get('scope_out_of_scope_or_rejected_gain_323h', 0)}",
        "",
        "## Safety",
        f"- selected_core_trusted_rate_before_323h: {summary.get('selected_core_trusted_rate_before_323h', 0)}",
        f"- selected_core_trusted_rate_after_323h: {summary.get('selected_core_trusted_rate_after_323h', 0)}",
        f"- remaining_unknown_metric_candidate_count: {summary.get('remaining_unknown_metric_candidate_count', 0)}",
        f"- remaining_unit_unknown_candidate_count: {summary.get('remaining_unit_unknown_candidate_count', 0)}",
        f"- remaining_manual_review_count: {summary.get('remaining_manual_review_count', 0)}",
        f"- core_false_exclusion_count: {summary.get('core_false_exclusion_count', 0)}",
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
            "- 323H is sandbox evidence only and does not modify official rule assets.",
            "- 323H replays only the 11 confirmed suggestions from 323G reviewed validation.",
            "",
        ]
    )
    return "\n".join(lines)
