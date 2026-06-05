from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "proposal_overview",
    "alias_proposals",
    "scope_proposals",
    "target_asset_plan",
    "proposal_source_bridge",
    "provenance_samples",
    "qa_summary",
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


def controlled_official_proposal_from_324h_report_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Controlled Official Proposal From 324H 324I",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Proposal Counts",
        f"- loaded_ready_candidate_count: {summary.get('loaded_ready_candidate_count', 0)}",
        f"- proposal_count: {summary.get('proposal_count', 0)}",
        f"- alias_proposal_count: {summary.get('alias_proposal_count', 0)}",
        f"- scope_proposal_count: {summary.get('scope_proposal_count', 0)}",
        f"- ready_for_dry_run_proposal_count: {summary.get('ready_for_dry_run_proposal_count', 0)}",
        f"- needs_review_proposal_count: {summary.get('needs_review_proposal_count', 0)}",
        f"- rejected_proposal_count: {summary.get('rejected_proposal_count', 0)}",
        "",
        "## Target Asset Plan",
        f"- target_asset_plan_count: {summary.get('target_asset_plan_count', 0)}",
        f"- target_asset_file_count: {summary.get('target_asset_file_count', 0)}",
        f"- duplicate_proposal_id_count: {summary.get('duplicate_proposal_id_count', 0)}",
        f"- already_official_overlap_count: {summary.get('already_official_overlap_count', 0)}",
        f"- alias_conflict_count: {summary.get('alias_conflict_count', 0)}",
        f"- target_conflict_count: {summary.get('target_conflict_count', 0)}",
        f"- missing_target_asset_or_group_count: {summary.get('missing_target_asset_or_group_count', 0)}",
        f"- missing_provenance_count: {summary.get('missing_provenance_count', 0)}",
        "",
        "## Impact",
        f"- expected_affected_candidate_count: {summary.get('expected_affected_candidate_count', 0)}",
        f"- expected_trusted_gain: {summary.get('expected_trusted_gain', 0)}",
        f"- expected_review_reduction: {summary.get('expected_review_reduction', 0)}",
        f"- expected_out_of_scope_or_rejected_gain: {summary.get('expected_out_of_scope_or_rejected_gain', 0)}",
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
            "- 324I creates a controlled proposal package only.",
            "- No official mapping or override asset is modified in this stage.",
            "- The single scope proposal preserves 324A through 324H provenance for later dry run review.",
            "",
        ]
    )
    return "\n".join(lines)
