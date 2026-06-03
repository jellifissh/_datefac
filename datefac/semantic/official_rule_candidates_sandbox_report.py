from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


BEFORE_AFTER_SHEET_ORDER = [
    "summary",
    "before_after_overview",
    "rule_application_overview",
    "official_alias_rule_candidates",
    "official_scope_rule_candidates",
    "trusted_after_preview_322j",
    "review_required_after_preview_322j",
    "rejected_after_preview_322j",
    "remaining_review_burden_322j",
    "qa_checks",
    "known_limitations",
]

AFFECTED_CANDIDATE_SHEET_ORDER = [
    "summary",
    "candidate_before_after_diff_322j",
    "rule_application_log_322j",
    "affected_candidate_deltas_by_rule",
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


def write_jsonl(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in df.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def official_rule_candidates_322j_report_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Official Semantic Rule Candidates Sandbox Application 322J",
        "",
        "## Decision",
        f"- official_rule_candidates_322j_decision: {summary.get('official_rule_candidates_322j_decision', '')}",
        "",
        "## Package Validation",
        f"- input_official_rule_candidate_count: {summary.get('input_official_rule_candidate_count', 0)}",
        f"- alias_rule_candidate_count: {summary.get('alias_rule_candidate_count', 0)}",
        f"- scope_rule_candidate_count: {summary.get('scope_rule_candidate_count', 0)}",
        f"- unit_rule_candidate_count: {summary.get('unit_rule_candidate_count', 0)}",
        f"- rejected_noise_rule_candidate_count: {summary.get('rejected_noise_rule_candidate_count', 0)}",
        f"- duplicate_rule_candidate_count: {summary.get('duplicate_rule_candidate_count', 0)}",
        f"- conflict_rule_candidate_count: {summary.get('conflict_rule_candidate_count', 0)}",
        f"- ready_for_sandbox_application_count: {summary.get('ready_for_sandbox_application_count', 0)}",
        f"- needs_additional_review_count: {summary.get('needs_additional_review_count', 0)}",
        "",
        "## Before / After",
        f"- trusted_total_before_322j: {summary.get('trusted_total_before_322j', 0)}",
        f"- trusted_total_after_322j: {summary.get('trusted_total_after_322j', 0)}",
        f"- review_required_total_before_322j: {summary.get('review_required_total_before_322j', 0)}",
        f"- review_required_total_after_322j: {summary.get('review_required_total_after_322j', 0)}",
        f"- rejected_total_before_322j: {summary.get('rejected_total_before_322j', 0)}",
        f"- rejected_total_after_322j: {summary.get('rejected_total_after_322j', 0)}",
        f"- trusted_gain_322j: {summary.get('trusted_gain_322j', 0)}",
        f"- review_reduction_322j: {summary.get('review_reduction_322j', 0)}",
        f"- out_of_scope_or_rejected_gain_322j: {summary.get('out_of_scope_or_rejected_gain_322j', 0)}",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        "",
        "## Alignment To 322I",
        f"- trusted_gain_delta_vs_322i_expected: {summary.get('trusted_gain_delta_vs_322i_expected', 0)}",
        f"- review_reduction_delta_vs_322i_expected: {summary.get('review_reduction_delta_vs_322i_expected', 0)}",
        f"- out_of_scope_or_rejected_gain_delta_vs_322i_expected: {summary.get('out_of_scope_or_rejected_gain_delta_vs_322i_expected', 0)}",
        f"- affected_candidate_count_delta_vs_322i_expected: {summary.get('affected_candidate_count_delta_vs_322i_expected', 0)}",
        "",
        "## Remaining Review Burden",
        f"- selected_core_trusted_rate_before_322j: {summary.get('selected_core_trusted_rate_before_322j', 0)}",
        f"- selected_core_trusted_rate_after_322j: {summary.get('selected_core_trusted_rate_after_322j', 0)}",
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
            "- 322J is sandbox-only and does not modify production mapping, overrides, or delivery pipeline.",
            "- 322J replays 322I official rule candidates against the 322B2 selected candidate pool only.",
            "",
        ]
    )
    return "\n".join(lines)
