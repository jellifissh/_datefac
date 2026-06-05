from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "spot_check_records",
    "carried_forward_holdout",
    "send_to_adjudicator",
    "holdout_or_rejected",
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


def alias_human_spot_check_325d_markdown(summary: Dict[str, Any]) -> str:
    examples = summary.get("top_spot_check_examples") or []
    lines: List[str] = [
        "# Alias Human Spot-Check 325D",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- mode: {summary.get('mode', '')}",
        f"- spot_check_record_count: {summary.get('spot_check_record_count', 0)}",
        f"- pending_count: {summary.get('pending_count', 0)}",
        f"- send_to_adjudicator_count: {summary.get('send_to_adjudicator_count', 0)}",
        f"- holdout_count: {summary.get('holdout_count', 0)}",
        f"- rejected_count: {summary.get('rejected_count', 0)}",
        f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
        f"- carried_forward_325c_holdout_count: {summary.get('carried_forward_325c_holdout_count', 0)}",
        "",
        "## Safety",
        f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
        f"- official_assets_written: {summary.get('official_assets_written', [])}",
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
    if examples:
        lines.append("## Top Spot-Check Examples")
        for item in examples:
            lines.append(
                f"- {item.get('spot_check_id', '')}: {item.get('alias_label', '')} "
                f"({item.get('human_spot_check_decision', '')})"
            )
        lines.append("")
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    lines.extend(
        [
            "## Review Warning",
            "- PE/PB/P/E/P/B/EBIT/EBITDA style aliases are definition-sensitive and must not be auto-promoted.",
            "- 325D does not call an LLM/adjudicator, apply semantic rules, create official candidates, create proposals, or run sandbox replay.",
            "",
        ]
    )
    return "\n".join(lines)
