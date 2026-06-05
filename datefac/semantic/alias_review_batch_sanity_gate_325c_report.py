from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "routing_manifest",
    "send_to_adjudicator",
    "human_spot_check",
    "holdout",
    "routing_bucket_summary",
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


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(_to_jsonable(row), ensure_ascii=False, sort_keys=True))
            handle.write("\n")


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


def alias_review_batch_sanity_gate_325c_markdown(summary: Dict[str, Any]) -> str:
    bucket_counts = summary.get("routing_bucket_counts") or {}
    holdout_reasons = summary.get("holdout_reason_counts") or {}
    lines: List[str] = [
        "# Alias Review Batch Sanity Gate 325C",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- input_review_record_count: {summary.get('input_review_record_count', 0)}",
        f"- send_to_adjudicator_count: {summary.get('send_to_adjudicator_count', 0)}",
        f"- human_spot_check_count: {summary.get('human_spot_check_count', 0)}",
        f"- holdout_count: {summary.get('holdout_count', 0)}",
        "",
        "## Routing Buckets",
    ]
    for bucket, count in bucket_counts.items():
        lines.append(f"- {bucket}: {count}")
    lines.extend(["", "## Holdout Reasons"])
    if holdout_reasons:
        for reason, count in holdout_reasons.items():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- none: 0")
    lines.extend(
        [
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
    )
    examples = summary.get("top_routed_examples") or []
    if examples:
        lines.append("## Top Routed Examples")
        for item in examples:
            lines.append(
                f"- {item.get('alias_review_id', '')}: {item.get('normalized_label', '')} "
                f"-> {item.get('routing_bucket', '')}"
            )
        lines.append("")
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    lines.extend(
        [
            "## Notes",
            "- 325C routes review records only and does not call an LLM/adjudicator.",
            "- 325C does not apply semantic rules, create official candidates, create controlled proposals, or produce sandbox replay packages.",
            "- PE/PB/EBIT/EBITDA and blank-target records are routed conservatively for human spot-check unless a holdout condition blocks routing.",
            "",
        ]
    )
    return "\n".join(lines)
