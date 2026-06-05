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


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
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


def controlled_official_proposal_dry_run_325l_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Controlled Official Proposal Dry Run 325L",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- proposal_count: {summary.get('proposal_count', 0)}",
        f"- patch_operation_count: {summary.get('patch_operation_count', 0)}",
        f"- alias_patch_operation_count: {summary.get('alias_patch_operation_count', 0)}",
        f"- scope_patch_operation_count: {summary.get('scope_patch_operation_count', 0)}",
        f"- target_asset_file_count: {summary.get('target_asset_file_count', 0)}",
        f"- target_asset_plan_count: {summary.get('target_asset_plan_count', 0)}",
        "",
        "## Integrity",
        f"- duplicate_operation_count: {summary.get('duplicate_operation_count', 0)}",
        f"- duplicate_alias_target_pair_count: {summary.get('duplicate_alias_target_pair_count', 0)}",
        f"- target_conflict_count: {summary.get('target_conflict_count', 0)}",
        f"- already_official_overlap_count: {summary.get('already_official_overlap_count', 0)}",
        f"- missing_target_asset_or_group_count: {summary.get('missing_target_asset_or_group_count', 0)}",
        f"- missing_provenance_count: {summary.get('missing_provenance_count', 0)}",
        "",
        "## Semantic Checks",
        f"- adjusted_metric_mismatch_count: {summary.get('adjusted_metric_mismatch_count', 0)}",
        f"- diluted_eps_mismatch_count: {summary.get('diluted_eps_mismatch_count', 0)}",
        "",
        "## Impact",
        f"- expected_affected_candidate_count: {summary.get('expected_affected_candidate_count', 0)}",
        f"- expected_trusted_gain: {summary.get('expected_trusted_gain', 0)}",
        f"- expected_review_reduction: {summary.get('expected_review_reduction', 0)}",
        f"- expected_out_of_scope_or_rejected_gain: {summary.get('expected_out_of_scope_or_rejected_gain', 0)}",
        "",
        "## Safety",
        f"- official_asset_hash_unchanged: {summary.get('official_asset_hash_unchanged', False)}",
        f"- files_written_to_official_assets: {summary.get('files_written_to_official_assets', [])}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
        "## Notes",
        "- 325L generates output-only alias patch-operation previews.",
        "- 325L resolves a virtual after-state without writing the official alias asset.",
        "- Human approval is still required before any later official patch application stage.",
        "",
    ]
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    return "\n".join(lines)


def controlled_official_proposal_dry_run_325l_rollback_markdown(
    rollback_plan_rows: List[Dict[str, Any]]
) -> str:
    lines = [
        "# Controlled Official Proposal Dry Run 325L Rollback Plan",
        "",
        "## Rollback Principles",
        "- 325L is output-only and does not modify official assets.",
        "- Any rollback in this stage means removing dry-run preview operations from the 325L package only.",
        "",
        "## Planned Rollback Actions",
    ]
    for row in rollback_plan_rows:
        lines.append(
            f"- {row.get('dry_run_patch_operation_id', '')}: {row.get('rollback_instruction', '')}"
        )
    lines.append("")
    return "\n".join(lines)
