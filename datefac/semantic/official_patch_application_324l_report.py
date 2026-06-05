from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "before_snapshot",
    "after_snapshot",
    "before_after_preview",
    "asset_diff_preview",
    "application_log",
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


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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


def official_patch_application_324l_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Official Patch Application 324L",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Operation Counts",
        f"- approved_patch_operation_count: {summary.get('approved_patch_operation_count', 0)}",
        f"- alias_approved_patch_operation_count: {summary.get('alias_approved_patch_operation_count', 0)}",
        f"- scope_approved_patch_operation_count: {summary.get('scope_approved_patch_operation_count', 0)}",
        f"- applied_operation_count: {summary.get('applied_operation_count', 0)}",
        f"- idempotent_operation_count: {summary.get('idempotent_operation_count', 0)}",
        f"- applied_or_idempotent_operation_count: {summary.get('applied_or_idempotent_operation_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        "",
        "## Impact",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- expected_trusted_gain: {summary.get('expected_trusted_gain', 0)}",
        f"- expected_review_reduction: {summary.get('expected_review_reduction', 0)}",
        f"- expected_out_of_scope_or_rejected_gain: {summary.get('expected_out_of_scope_or_rejected_gain', 0)}",
        "",
        "## Safety",
        f"- target_official_assets_modified: {summary.get('target_official_assets_modified', [])}",
        f"- alias_official_asset_unchanged_confirmed: {summary.get('alias_official_asset_unchanged_confirmed', False)}",
        f"- rollback_backup_paths: {summary.get('rollback_backup_paths', {})}",
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
            "- 324L writes only the official formal scope rules asset.",
            "- 324L never writes the official alias override asset.",
            "- 324L does not modify production pipeline, parser, extraction, or delivery code.",
            "",
        ]
    )
    return "\n".join(lines)


def rollback_instructions_markdown(summary: Dict[str, Any], rollback_rows: List[Dict[str, Any]]) -> str:
    lines: List[str] = [
        "# Official Patch Application 324L Rollback Instructions",
        "",
        "## Rollback Rule",
        "- Restore only the official formal scope rules asset from the 324L backup file.",
        "- Do not revert unrelated source files, outputs, or the alias override asset.",
        "",
        "## Backup Files",
    ]
    for key, value in (summary.get("rollback_backup_paths") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Per-Operation Rollback Plan"])
    for row in rollback_rows:
        lines.append(
            f"- {row.get('approval_id', '')}: {row.get('rollback_action', '')} on {row.get('target_path', '')}"
        )
        lines.append(f"  generated_rule_id: {row.get('generated_rule_id', '')}")
        lines.append(f"  backup_path: {row.get('backup_path', '')}")
        lines.append(f"  rollback_note: {row.get('rollback_note', '')}")
    lines.append("")
    return "\n".join(lines)
