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
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]] | pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = rows.to_dict(orient="records") if isinstance(rows, pd.DataFrame) else list(rows)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(_to_jsonable(record), ensure_ascii=False) + "\n")


def alias_human_confirmed_sandbox_replay_325i_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Alias Human-Confirmed Sandbox Replay 325I",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Rule Counts",
        f"- confirmed_alias_count: {summary.get('confirmed_alias_count', 0)}",
        f"- sandbox_alias_rule_count: {summary.get('sandbox_alias_rule_count', 0)}",
        f"- sandbox_scope_rule_count: {summary.get('sandbox_scope_rule_count', 0)}",
        "",
        "## Replay Impact",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_325i: {summary.get('trusted_gain_325i', 0)}",
        f"- review_reduction_325i: {summary.get('review_reduction_325i', 0)}",
        f"- out_of_scope_or_rejected_gain_325i: {summary.get('out_of_scope_or_rejected_gain_325i', 0)}",
        "",
        "## Conflict Checks",
        f"- duplicate_count: {summary.get('duplicate_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        f"- target_conflict_count: {summary.get('target_conflict_count', 0)}",
        f"- official_overlap_count: {summary.get('official_overlap_count', 0)}",
        f"- adjusted_metric_mismatch_count: {summary.get('adjusted_metric_mismatch_count', 0)}",
        f"- diluted_eps_mismatch_count: {summary.get('diluted_eps_mismatch_count', 0)}",
        f"- core_false_mapping_count: {summary.get('core_false_mapping_count', 0)}",
        "",
        "## Safety",
        f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
        f"- official_assets_written: {summary.get('official_assets_written', [])}",
        f"- llm_or_adjudicator_called: {summary.get('llm_or_adjudicator_called', False)}",
        f"- official_rule_candidates_created: {summary.get('official_rule_candidates_created', False)}",
        f"- controlled_proposals_created: {summary.get('controlled_proposals_created', False)}",
        f"- official_patches_applied: {summary.get('official_patches_applied', False)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
        "## Notes",
        "- 325I is sandbox replay only. It does not write official mapping or override assets.",
        "- Confirmed alias suggestions still require 325J official rule candidate packaging before any controlled proposal flow.",
        "",
    ]
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    return "\n".join(lines)
