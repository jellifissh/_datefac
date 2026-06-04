from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "effective_unique_candidates",
    "alias_candidates",
    "scope_candidates",
    "duplicate_source_groups",
    "source_rule_inventory",
    "source_provenance",
    "candidate_source_bridge",
    "qa_checks",
    "known_limitations",
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


def official_rule_candidates_from_323h_report_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Official Rule Candidates From 323H 323I",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Candidate Counts",
        f"- source_sandbox_rule_count: {summary.get('source_sandbox_rule_count', 0)}",
        f"- effective_unique_candidate_count: {summary.get('effective_unique_candidate_count', 0)}",
        f"- alias_candidate_count: {summary.get('alias_candidate_count', 0)}",
        f"- scope_candidate_count: {summary.get('scope_candidate_count', 0)}",
        f"- ready_for_controlled_proposal_count: {summary.get('ready_for_controlled_proposal_count', 0)}",
        f"- needs_review_candidate_count: {summary.get('needs_review_candidate_count', 0)}",
        f"- rejected_candidate_count: {summary.get('rejected_candidate_count', 0)}",
        f"- duplicate_source_group_count: {summary.get('duplicate_source_group_count', 0)}",
        f"- conflict_group_count: {summary.get('conflict_group_count', 0)}",
        "",
        "## Impact Carried Forward",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_323i: {summary.get('trusted_gain_323i', 0)}",
        f"- review_reduction_323i: {summary.get('review_reduction_323i', 0)}",
        f"- out_of_scope_or_rejected_gain_323i: {summary.get('out_of_scope_or_rejected_gain_323i', 0)}",
        "",
        "## Safety",
        f"- carried_forward_core_false_exclusion_count: {summary.get('carried_forward_core_false_exclusion_count', 0)}",
        f"- carried_forward_conflict_count: {summary.get('carried_forward_conflict_count', 0)}",
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
            "- 323I deduplicates 323H sandbox-confirmed source rules into effective unique official rule candidates only.",
            "- Duplicate source suggestions are preserved as provenance and are not promoted as separate effective candidates.",
            "- No official mapping or override asset is modified in this stage.",
            "",
        ]
    )
    return "\n".join(lines)
