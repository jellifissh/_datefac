from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "patch_operations",
    "before_after_preview",
    "target_asset_diff_preview",
    "rollback_plan",
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


def controlled_official_proposal_dry_run_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Controlled Official Proposal Dry Run 323K",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- proposal_count: {summary.get('proposal_count', 0)}",
        f"- alias_proposal_count: {summary.get('alias_proposal_count', 0)}",
        f"- scope_proposal_count: {summary.get('scope_proposal_count', 0)}",
        f"- patch_operation_count: {summary.get('patch_operation_count', 0)}",
        f"- alias_patch_operation_count: {summary.get('alias_patch_operation_count', 0)}",
        f"- scope_patch_operation_count: {summary.get('scope_patch_operation_count', 0)}",
        "",
        "## Targets",
        f"- target_asset_file_count: {summary.get('target_asset_file_count', 0)}",
        f"- target_group_count: {summary.get('target_group_count', 0)}",
        f"- duplicate_operation_count: {summary.get('duplicate_operation_count', 0)}",
        f"- target_conflict_count: {summary.get('target_conflict_count', 0)}",
        f"- already_official_overlap_count: {summary.get('already_official_overlap_count', 0)}",
        "",
        "## Impact",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- expected_trusted_gain: {summary.get('expected_trusted_gain', 0)}",
        f"- expected_review_reduction: {summary.get('expected_review_reduction', 0)}",
        f"- expected_out_of_scope_or_rejected_gain: {summary.get('expected_out_of_scope_or_rejected_gain', 0)}",
        "",
        "## Safety",
        f"- no_apply_confirmed: {summary.get('no_apply_confirmed', False)}",
        f"- official_assets_not_modified_confirmed: {summary.get('official_assets_not_modified_confirmed', False)}",
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
            "- 323K generates output-only patch-operation preview artifacts.",
            "- 323K resolves target assets and virtual after-state without writing official files.",
            "- Human approval is still required before any later dry-run/application stage.",
            "",
        ]
    )
    return "\n".join(lines)


def controlled_official_proposal_dry_run_rollback_markdown(
    rollback_plan_rows: List[Dict[str, Any]]
) -> str:
    lines = [
        "# Controlled Official Proposal Dry Run 323K Rollback Plan",
        "",
        "## Rollback Principles",
        "- 323K is output-only and does not modify official assets.",
        "- Any rollback in this stage means removing dry-run preview operations from the 323K package only.",
        "",
        "## Planned Rollback Actions",
    ]
    for row in rollback_plan_rows:
        lines.append(
            f"- {row.get('dry_run_patch_operation_id', '')}: {row.get('rollback_instruction', '')}"
        )
    lines.append("")
    return "\n".join(lines)
