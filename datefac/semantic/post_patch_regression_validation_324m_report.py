from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


BEFORE_AFTER_SHEET_ORDER = [
    "summary",
    "before_after_hashes",
    "official_rule_visibility",
    "impact_metrics",
    "duplicate_conflict",
    "rollback_artifacts",
    "core_false_exclusion",
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
    path.write_text(
        json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame], ordered_names: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in ordered_names:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def post_patch_regression_validation_324m_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Post-Patch Regression Validation 324M",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Official Rule Visibility",
        f"- official_rule_visibility_total: {summary.get('official_rule_visibility_total', 0)}",
        f"- scope_rules_visible: {summary.get('scope_rules_visible', 0)}",
        f"- alias_rules_visible: {summary.get('alias_rules_visible', 0)}",
        "",
        "## Impact Metrics",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_324m: {summary.get('trusted_gain_324m', 0)}",
        f"- review_reduction_324m: {summary.get('review_reduction_324m', 0)}",
        f"- out_of_scope_or_rejected_gain_324m: {summary.get('out_of_scope_or_rejected_gain_324m', 0)}",
        "",
        "## Safety",
        f"- core_false_exclusion_count: {summary.get('core_false_exclusion_count', 0)}",
        f"- current_duplicate_count: {summary.get('current_duplicate_count', 0)}",
        f"- new_duplicate_delta_count: {summary.get('new_duplicate_delta_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        f"- rollback_artifact_check_passed: {summary.get('rollback_artifact_check_passed', False)}",
        f"- no_official_asset_modification_during_324m: {summary.get('no_official_asset_modification_during_324m', False)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    blocking_reasons = summary.get("blocking_reasons") or []
    if blocking_reasons:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking_reasons], ""])
    lines.extend(
        [
            "## Notes",
            "- 324M is validation-only and does not modify official assets.",
            "- Impact metrics are verified from cached 324G replay evidence.",
            "- Historical duplicate entries are warnings only when unchanged.",
            "",
        ]
    )
    return "\n".join(lines)
