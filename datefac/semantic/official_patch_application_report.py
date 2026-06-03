from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "before_snapshot",
    "after_snapshot",
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


def official_patch_application_report_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Official Semantic Patch Application 322N",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Operation Counts",
        f"- approved_patch_count: {summary.get('approved_patch_count', 0)}",
        f"- applied_operation_count: {summary.get('applied_operation_count', 0)}",
        f"- idempotent_operation_count: {summary.get('idempotent_operation_count', 0)}",
        f"- applied_or_idempotent_operation_count: {summary.get('applied_or_idempotent_operation_count', 0)}",
        f"- alias_operation_count: {summary.get('alias_operation_count', 0)}",
        f"- scope_operation_count: {summary.get('scope_operation_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        "",
        "## Expected Impact Alignment",
        f"- expected_affected_candidate_count: {summary.get('expected_affected_candidate_count', 0)}",
        f"- expected_trusted_gain: {summary.get('expected_trusted_gain', 0)}",
        f"- expected_review_reduction: {summary.get('expected_review_reduction', 0)}",
        f"- expected_out_of_scope_or_rejected_gain: {summary.get('expected_out_of_scope_or_rejected_gain', 0)}",
        f"- trusted_gain_delta_vs_322i_expected: {summary.get('trusted_gain_delta_vs_322i_expected', 0)}",
        f"- review_reduction_delta_vs_322i_expected: {summary.get('review_reduction_delta_vs_322i_expected', 0)}",
        f"- out_of_scope_or_rejected_gain_delta_vs_322i_expected: {summary.get('out_of_scope_or_rejected_gain_delta_vs_322i_expected', 0)}",
        f"- affected_candidate_count_delta_vs_322i_expected: {summary.get('affected_candidate_count_delta_vs_322i_expected', 0)}",
        "",
        "## Safety",
        f"- partial_application_detected: {summary.get('partial_application_detected', False)}",
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
            "- 322N is the first stage allowed to modify official semantic rule assets.",
            "- 322N applies only approved operations from the reviewed final approved patch plan.",
            "- 322N does not modify production pipeline, parser, extraction, or delivery code.",
            "",
        ]
    )
    return "\n".join(lines)


def rollback_instructions_markdown(summary: Dict[str, Any], rollback_rows: List[Dict[str, Any]]) -> str:
    lines: List[str] = [
        "# Official Semantic Patch Application 322N Rollback Instructions",
        "",
        "## Rollback Safety Rule",
        "- Restore only the target official semantic rule asset from its 322N backup file.",
        "- Do not revert unrelated files.",
        "",
        "## Backup Files",
    ]
    backup_paths = summary.get("rollback_backup_paths") or {}
    for key, value in backup_paths.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Per-Operation Rollback Plan"])
    for row in rollback_rows:
        lines.append(
            f"- {row.get('approval_id', '')}: {row.get('rollback_action', '')} on {row.get('target_path', '')}"
        )
        lines.append(f"  rule_id: {row.get('rule_id', '')}")
        lines.append(f"  backup_path: {row.get('backup_path', '')}")
        lines.append(f"  rollback_note: {row.get('rollback_note', '')}")
    lines.append("")
    return "\n".join(lines)
