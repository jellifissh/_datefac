from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "request_items",
    "excluded_items",
    "response_schema",
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


def alias_safe_adjudicator_request_325e_markdown(summary: Dict[str, Any], schema: Dict[str, Any]) -> str:
    examples = summary.get("top_request_examples") or []
    labels = summary.get("allowed_response_labels") or []
    schema_fields = schema.get("required", [])
    lines: List[str] = [
        "# Alias Safe Adjudicator Request 325E",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- request_count: {summary.get('request_count', 0)}",
        f"- alias_request_count: {summary.get('alias_request_count', 0)}",
        f"- excluded_holdout_count: {summary.get('excluded_holdout_count', 0)}",
        f"- excluded_rejected_count: {summary.get('excluded_rejected_count', 0)}",
        f"- excluded_needs_more_info_count: {summary.get('excluded_needs_more_info_count', 0)}",
        f"- excluded_pending_count: {summary.get('excluded_pending_count', 0)}",
        "",
        "## Allowed Responses",
        f"- labels: {', '.join(labels)}",
        f"- required_schema_fields: {', '.join(schema_fields)}",
        "",
        "## Safety",
        f"- llm_or_adjudicator_called: {summary.get('llm_or_adjudicator_called', False)}",
        f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
        f"- official_assets_written: {summary.get('official_assets_written', [])}",
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
        lines.append("## Top Request Examples")
        for item in examples:
            lines.append(
                f"- {item.get('request_id', '')}: {item.get('alias_label', '')} "
                f"(source={item.get('source_review_id', '')})"
            )
        lines.append("")
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    lines.extend(
        [
            "## Downstream Requirements",
            "- ACCEPT_ALIAS suggestions still require schema validation, deterministic gate, human confirmation, sandbox replay, controlled proposal, dry run, human approval, official patch application, and post-patch regression.",
            "- The adjudicator must not apply rules, modify official assets, or mark rows trusted.",
            "- 325E does not call an LLM/adjudicator; it only packages requests.",
            "",
        ]
    )
    return "\n".join(lines)
