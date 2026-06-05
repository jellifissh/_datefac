from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "effective_unique_candidates",
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
    records = rows.to_dict(orient="records") if isinstance(rows, pd.DataFrame) else list(rows)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def official_rule_candidate_from_324g_324h_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Official Rule Candidate From 324G 324H",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Candidate Counts",
        f"- source_sandbox_rule_count: {summary.get('source_sandbox_rule_count', 0)}",
        f"- candidate_count: {summary.get('candidate_count', 0)}",
        f"- scope_candidate_count: {summary.get('scope_candidate_count', 0)}",
        f"- ready_for_controlled_proposal_count: {summary.get('ready_for_controlled_proposal_count', 0)}",
        f"- needs_review_candidate_count: {summary.get('needs_review_candidate_count', 0)}",
        f"- rejected_candidate_count: {summary.get('rejected_candidate_count', 0)}",
        "",
        "## Impact Carried Forward",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- expected_trusted_gain: {summary.get('expected_trusted_gain', 0)}",
        f"- expected_review_reduction: {summary.get('expected_review_reduction', 0)}",
        f"- expected_out_of_scope_or_rejected_gain: {summary.get('expected_out_of_scope_or_rejected_gain', 0)}",
        "",
        "## Safety",
        f"- duplicate_candidate_id_count: {summary.get('duplicate_candidate_id_count', 0)}",
        f"- already_official_overlap_count: {summary.get('already_official_overlap_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        f"- missing_provenance_count: {summary.get('missing_provenance_count', 0)}",
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
            "- 324H creates one official scope rule candidate only.",
            "- No official asset is modified in this stage.",
            "- Historical duplicate warning may carry only when new duplicate delta stays at zero.",
            "",
        ]
    )
    return "\n".join(lines)
