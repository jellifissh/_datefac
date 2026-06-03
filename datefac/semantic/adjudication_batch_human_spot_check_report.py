from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


PREPARE_SHEET_ORDER = [
    "summary",
    "human_spot_check_items",
    "auto_send_reference",
    "auto_holdout_reference",
    "qa_checks",
    "review_instructions",
]

REVIEWED_SHEET_ORDER = [
    "summary",
    "routing_manifest",
    "final_send_to_adjudicator",
    "final_holdouts",
    "reclassified_scope_candidate",
    "reclassified_alias_candidate",
    "needs_more_info",
    "reviewed_human_items",
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


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame], mode: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    order = PREPARE_SHEET_ORDER if mode == "prepare" else REVIEWED_SHEET_ORDER
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in order:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def adjudication_batch_human_spot_check_report_markdown(summary: Dict[str, Any]) -> str:
    mode = _norm(summary.get("mode")) or "prepare"
    lines: List[str] = [
        "# Adjudication Batch Human Spot-Check 323C",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        f"- mode: {mode}",
        "",
    ]
    if mode == "prepare":
        lines.extend(
            [
                "## Counts",
                f"- input_batch_count: {summary.get('input_batch_count', 0)}",
                f"- auto_send_count: {summary.get('auto_send_count', 0)}",
                f"- auto_holdout_count: {summary.get('auto_holdout_count', 0)}",
                f"- human_spot_check_item_count: {summary.get('human_spot_check_item_count', 0)}",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Routing Counts",
                f"- reviewed_human_item_count: {summary.get('reviewed_human_item_count', 0)}",
                f"- send_to_adjudicator_count: {summary.get('send_to_adjudicator_count', 0)}",
                f"- holdout_count: {summary.get('holdout_count', 0)}",
                f"- reclassified_scope_candidate_count: {summary.get('reclassified_scope_candidate_count', 0)}",
                f"- reclassified_alias_candidate_count: {summary.get('reclassified_alias_candidate_count', 0)}",
                f"- needs_more_info_count: {summary.get('needs_more_info_count', 0)}",
                f"- pending_count: {summary.get('pending_count', 0)}",
                f"- invalid_decision_count: {summary.get('invalid_decision_count', 0)}",
                "",
                "## Human Decision Distribution",
                f"- human_decision_distribution: {summary.get('human_decision_distribution', {})}",
                "",
            ]
        )
    lines.extend(
        [
            "## Safety",
            f"- official_assets_not_modified_confirmed: {summary.get('official_assets_not_modified_confirmed', False)}",
            f"- llm_not_called_confirmed: {summary.get('llm_not_called_confirmed', False)}",
            "",
            "## QA",
            f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
            f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
        ]
    )
    examples = summary.get("highest_priority_reviewed_examples") or []
    if examples:
        lines.append("## Highest-Priority Reviewed Examples")
        for item in examples:
            lines.append(
                f"- {item.get('batch_item_id', '')} | {item.get('candidate_type', '')} | {item.get('repaired_label', '')} | {item.get('human_decision', '')} | priority={item.get('priority_score', '')}"
            )
        lines.append("")
    blocking_reasons = summary.get("blocking_reasons") or []
    if blocking_reasons:
        lines.append("## Blocking Reasons")
        for reason in blocking_reasons:
            lines.append(f"- {reason}")
        lines.append("")
    return "\n".join(lines)
