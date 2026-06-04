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
    records = rows.to_dict(orient="records") if isinstance(rows, pd.DataFrame) else list(rows)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def scope_noise_human_confirmed_sandbox_replay_324g_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Scope Noise Human Confirmed Sandbox Replay 324G",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- confirmed_scope_noise_count: {summary.get('confirmed_scope_noise_count', 0)}",
        f"- sandbox_rule_count: {summary.get('sandbox_rule_count', 0)}",
        f"- duplicate_count: {summary.get('duplicate_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        "",
        "## Replay Impact",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_324g: {summary.get('trusted_gain_324g', 0)}",
        f"- review_reduction_324g: {summary.get('review_reduction_324g', 0)}",
        f"- out_of_scope_or_rejected_gain_324g: {summary.get('out_of_scope_or_rejected_gain_324g', 0)}",
        "",
        "## Safety",
        f"- core_false_exclusion_count: {summary.get('core_false_exclusion_count', 0)}",
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
            "- 324G is sandbox evidence only and does not modify any official semantic asset.",
            "- 324G replays only the single 324F human-confirmed scope-noise suggestion.",
            "",
        ]
    )
    return "\n".join(lines)
