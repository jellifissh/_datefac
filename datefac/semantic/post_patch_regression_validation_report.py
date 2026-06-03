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
    "trusted_after_preview_322o",
    "review_after_preview_322o",
    "rejected_after_preview_322o",
    "rollback_artifacts",
    "qa_summary",
    "qa_checks",
    "known_limitations",
]

CORE_FALSE_EXCLUSION_SHEET_ORDER = [
    "summary",
    "core_false_exclusion_check",
    "candidate_before_after_diff_322o",
    "impact_by_rule_322o",
    "qa_checks",
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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def post_patch_regression_validation_report_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Post-Patch Regression Validation 322O",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Official Rule Visibility",
        f"- official_rule_visibility_total: {summary.get('official_rule_visibility_total', 0)}",
        f"- alias_rules_visible: {summary.get('alias_rules_visible', 0)}",
        f"- scope_rules_visible: {summary.get('scope_rules_visible', 0)}",
        "",
        "## Regression Comparison",
        f"- trusted_total_before_322o: {summary.get('trusted_total_before_322o', 0)}",
        f"- trusted_total_after_322o: {summary.get('trusted_total_after_322o', 0)}",
        f"- review_required_total_before_322o: {summary.get('review_required_total_before_322o', 0)}",
        f"- review_required_total_after_322o: {summary.get('review_required_total_after_322o', 0)}",
        f"- rejected_total_before_322o: {summary.get('rejected_total_before_322o', 0)}",
        f"- rejected_total_after_322o: {summary.get('rejected_total_after_322o', 0)}",
        f"- trusted_gain_322o: {summary.get('trusted_gain_322o', 0)}",
        f"- review_reduction_322o: {summary.get('review_reduction_322o', 0)}",
        f"- out_of_scope_or_rejected_gain_322o: {summary.get('out_of_scope_or_rejected_gain_322o', 0)}",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        "",
        "## Safety",
        f"- selected_core_trusted_rate_before_322o: {summary.get('selected_core_trusted_rate_before_322o', 0)}",
        f"- selected_core_trusted_rate_after_322o: {summary.get('selected_core_trusted_rate_after_322o', 0)}",
        f"- core_false_exclusion_count: {summary.get('core_false_exclusion_count', 0)}",
        f"- duplicate_count: {summary.get('duplicate_count', 0)}",
        f"- conflict_count: {summary.get('conflict_count', 0)}",
        f"- rollback_artifact_all_present: {summary.get('rollback_artifact_all_present', False)}",
        f"- no_official_asset_modification_during_322o: {summary.get('no_official_asset_modification_during_322o', False)}",
        f"- no_parser_run_confirmation: {summary.get('no_parser_run_confirmation', False)}",
        "",
        "## Remaining Review Burden",
        f"- remaining_unknown_metric_candidate_count: {summary.get('remaining_unknown_metric_candidate_count', 0)}",
        f"- remaining_unit_unknown_candidate_count: {summary.get('remaining_unit_unknown_candidate_count', 0)}",
        f"- remaining_manual_review_count: {summary.get('remaining_manual_review_count', 0)}",
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
            "- 322O validates only cached-input post-patch behavior and does not rerun MinerU, StructEqTable, Docling, PPStructure, or VLM.",
            "- 322O does not modify official semantic assets and proves that with before/after asset hashes.",
            "",
        ]
    )
    return "\n".join(lines)


def post_patch_regression_validation_decision_markdown(decision_json: Dict[str, Any]) -> str:
    lines = [
        "# 322O Decision",
        "",
        f"- decision: {decision_json.get('decision', '')}",
        f"- qa_fail_count: {decision_json.get('qa_fail_count', 0)}",
        f"- rollback_recommendation: {decision_json.get('rollback_recommendation', '')}",
    ]
    blocking_reasons = decision_json.get("blocking_reasons") or []
    if blocking_reasons:
        lines.extend(["", "## Blocking Reasons", *[f"- {item}" for item in blocking_reasons]])
    lines.append("")
    return "\n".join(lines)
