from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


BEFORE_AFTER_SHEET_ORDER = [
    "summary",
    "metric_comparison",
    "rule_application_alignment",
    "official_rule_visibility",
    "source_linkage",
    "duplicate_conflict",
    "rollback_artifacts",
    "trusted_after_preview_323n",
    "review_after_preview_323n",
    "rejected_after_preview_323n",
    "qa_summary",
    "qa_checks",
    "known_limitations",
]

AFFECTED_CANDIDATES_SHEET_ORDER = [
    "summary",
    "candidate_before_after_diff_323n",
    "impact_by_rule_323n",
    "core_false_exclusion_check",
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


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def post_patch_regression_validation_323n_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Post-Patch Regression Validation 323N",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Official Rule Visibility",
        f"- official_rule_visibility_total: {summary.get('official_rule_visibility_total', 0)}",
        f"- alias_rules_visible: {summary.get('alias_rules_visible', 0)}",
        f"- scope_rules_visible: {summary.get('scope_rules_visible', 0)}",
        "",
        "## Impact Validation",
        f"- trusted_total_before_323n: {summary.get('trusted_total_before_323n', 0)}",
        f"- trusted_total_after_323n: {summary.get('trusted_total_after_323n', 0)}",
        f"- review_required_total_before_323n: {summary.get('review_required_total_before_323n', 0)}",
        f"- review_required_total_after_323n: {summary.get('review_required_total_after_323n', 0)}",
        f"- rejected_total_before_323n: {summary.get('rejected_total_before_323n', 0)}",
        f"- rejected_total_after_323n: {summary.get('rejected_total_after_323n', 0)}",
        f"- trusted_gain_323n: {summary.get('trusted_gain_323n', 0)}",
        f"- review_reduction_323n: {summary.get('review_reduction_323n', 0)}",
        f"- out_of_scope_or_rejected_gain_323n: {summary.get('out_of_scope_or_rejected_gain_323n', 0)}",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        "",
        "## Safety",
        f"- selected_core_trusted_rate_before_323n: {summary.get('selected_core_trusted_rate_before_323n', 0)}",
        f"- selected_core_trusted_rate_after_323n: {summary.get('selected_core_trusted_rate_after_323n', 0)}",
        f"- core_false_exclusion_count: {summary.get('core_false_exclusion_count', 0)}",
        f"- historical_duplicate_count: {summary.get('historical_duplicate_count', 0)}",
        f"- current_duplicate_count: {summary.get('current_duplicate_count', 0)}",
        f"- new_duplicate_delta_count: {summary.get('new_duplicate_delta_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        f"- rollback_artifact_check_passed: {summary.get('rollback_artifact_check_passed', False)}",
        f"- source_linkage_all_present: {summary.get('source_linkage_all_present', False)}",
        f"- no_official_asset_modification_during_323n: {summary.get('no_official_asset_modification_during_323n', False)}",
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
            "- 323N is validation-only and reads current official semantic assets without modifying them.",
            "- 323N replays cached 322B2 candidate outputs using the 323M official rules that are already visible in assets.",
            "- Historical duplicates can remain as warnings only when 323M introduced no new duplicate entries.",
            "",
        ]
    )
    return "\n".join(lines)


def post_patch_regression_validation_323n_decision_markdown(decision_json: Dict[str, Any]) -> str:
    lines = [
        "# 323N Decision",
        "",
        f"- decision: {decision_json.get('decision', '')}",
        f"- qa_fail_count: {decision_json.get('qa_fail_count', 0)}",
        f"- qa_warn_count: {decision_json.get('qa_warn_count', 0)}",
        f"- rollback_recommendation: {decision_json.get('rollback_recommendation', '')}",
    ]
    blocking_reasons = decision_json.get("blocking_reasons") or []
    warning_reasons = decision_json.get("warning_reasons") or []
    if blocking_reasons:
        lines.extend(["", "## Blocking Reasons", *[f"- {item}" for item in blocking_reasons]])
    if warning_reasons:
        lines.extend(["", "## Warning Reasons", *[f"- {item}" for item in warning_reasons]])
    lines.append("")
    return "\n".join(lines)
