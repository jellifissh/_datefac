from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "patch_diff_preview",
    "target_inventory",
    "qa_summary",
    "no_apply_proof",
    "rollback_plan",
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


def official_patch_dry_run_report_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Official Semantic Patch Dry Run 322L",
        "",
        "## Decision",
        f"- official_patch_dry_run_decision: {summary.get('official_patch_dry_run_decision', '')}",
        "",
        "## Readiness",
        f"- controlled_proposal_readiness_passed: {summary.get('controlled_proposal_readiness_passed', False)}",
        f"- controlled_proposal_source_decision: {summary.get('controlled_proposal_source_decision', '')}",
        f"- controlled_proposal_source_qa_fail_count: {summary.get('controlled_proposal_source_qa_fail_count', 0)}",
        "",
        "## Counts",
        f"- total_patch_operation_count: {summary.get('total_patch_operation_count', 0)}",
        f"- alias_patch_operation_count: {summary.get('alias_patch_operation_count', 0)}",
        f"- scope_patch_operation_count: {summary.get('scope_patch_operation_count', 0)}",
        f"- unit_patch_operation_count: {summary.get('unit_patch_operation_count', 0)}",
        f"- rejected_noise_patch_operation_count: {summary.get('rejected_noise_patch_operation_count', 0)}",
        "",
        "## Expected Impact",
        f"- expected_affected_candidate_count: {summary.get('expected_affected_candidate_count', 0)}",
        f"- expected_trusted_gain: {summary.get('expected_trusted_gain', 0)}",
        f"- expected_review_reduction: {summary.get('expected_review_reduction', 0)}",
        f"- expected_out_of_scope_or_rejected_gain: {summary.get('expected_out_of_scope_or_rejected_gain', 0)}",
        "",
        "## Safety",
        f"- no_apply_confirmed: {summary.get('no_apply_confirmed', False)}",
        f"- official_files_not_modified_confirmed: {summary.get('official_files_not_modified_confirmed', False)}",
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
            "- 322L inspects official target files or rule groups but does not write to them.",
            "- The patch diff is a dry-run preview only and remains subject to human approval.",
            "",
        ]
    )
    return "\n".join(lines)

