from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "alias_review_records",
    "review_instructions",
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


def alias_review_batch_325b_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Alias Review Batch 325B",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- loaded_safe_alias_candidate_count: {summary.get('loaded_safe_alias_candidate_count', 0)}",
        f"- review_record_count: {summary.get('review_record_count', 0)}",
        f"- pending_count: {summary.get('pending_count', 0)}",
        f"- accepted_count: {summary.get('accepted_count', 0)}",
        f"- rejected_count: {summary.get('rejected_count', 0)}",
        f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
        f"- holdout_count: {summary.get('holdout_count', 0)}",
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
    examples = summary.get("top_review_examples") or []
    if examples:
        lines.extend(["## Top Review Examples"])
        for item in examples:
            lines.append(
                f"- {item.get('alias_review_id', '')}: {item.get('normalized_label', '')} "
                f"(affected_review_required_count={item.get('affected_review_required_count', 0)})"
            )
        lines.append("")
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    lines.extend(
        [
            "## Notes",
            "- 325B prepares review records only and does not call an LLM/adjudicator.",
            "- PE/PB/EBIT-style labels carry ambiguity warnings for downstream reviewers.",
            "",
        ]
    )
    return "\n".join(lines)
