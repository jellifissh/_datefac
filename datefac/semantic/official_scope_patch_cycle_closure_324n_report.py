from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "cycle_summary",
    "stage_timeline",
    "remaining_burden",
    "warnings",
    "next_cycle_recommendations",
    "official_asset_proof",
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


def official_scope_patch_cycle_closure_324n_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Official Scope Patch Cycle Closure 324N",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## 324 Cycle Summary",
        f"- official_rule_count_324: {summary.get('official_rule_count_324', 0)}",
        f"- scope_rule_count_324: {summary.get('scope_rule_count_324', 0)}",
        f"- alias_rule_count_324: {summary.get('alias_rule_count_324', 0)}",
        f"- trusted_gain_324: {summary.get('trusted_gain_324', 0)}",
        f"- review_reduction_324: {summary.get('review_reduction_324', 0)}",
        f"- out_of_scope_or_rejected_gain_324: {summary.get('out_of_scope_or_rejected_gain_324', 0)}",
        f"- affected_candidate_count_324: {summary.get('affected_candidate_count_324', 0)}",
        "",
        "## Cumulative Official Patch Metrics",
        f"- previous_combined_official_rule_count: {summary.get('previous_combined_official_rule_count', 0)}",
        f"- previous_combined_trusted_gain: {summary.get('previous_combined_trusted_gain', 0)}",
        f"- previous_combined_review_reduction: {summary.get('previous_combined_review_reduction', 0)}",
        f"- combined_official_rule_count: {summary.get('combined_official_rule_count', 0)}",
        f"- combined_trusted_gain: {summary.get('combined_trusted_gain', 0)}",
        f"- combined_review_reduction: {summary.get('combined_review_reduction', 0)}",
        f"- combined_out_of_scope_or_rejected_gain: {summary.get('combined_out_of_scope_or_rejected_gain', 0)}",
        "",
        "## Warning Status",
        f"- warning_status: {summary.get('warning_status', '')}",
        f"- current_duplicate_count: {summary.get('current_duplicate_count', 0)}",
        f"- new_duplicate_delta_count_324: {summary.get('new_duplicate_delta_count_324', 0)}",
        "",
        "## Remaining Burden",
        f"- remaining_burden_status: {summary.get('remaining_burden_status', '')}",
        f"- remaining_unknown_metric_candidate_count: {summary.get('remaining_unknown_metric_candidate_count', 0)}",
        f"- remaining_unit_unknown_candidate_count: {summary.get('remaining_unit_unknown_candidate_count', 0)}",
        f"- remaining_manual_review_count: {summary.get('remaining_manual_review_count', 0)}",
        "",
        "## Recommended Next Cycle",
        f"- primary: {summary.get('recommended_next_cycle_direction_primary', '')}",
        f"- secondary: {summary.get('recommended_next_cycle_direction_secondary', '')}",
        f"- reason: {summary.get('recommendation_reason', '')}",
        "",
        "## Safety",
        f"- no_official_asset_modification_during_324n: {summary.get('no_official_asset_modification_during_324n', False)}",
        f"- official_assets_written: {summary.get('official_assets_written', [])}",
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
            "- 324N is a closure/reporting stage and does not modify official assets.",
            "- 324N uses cached 324A through 324M outputs only.",
            "- Remaining burden metrics are inherited from 323P / pre-324 and are not recomputed here.",
            "",
        ]
    )
    return "\n".join(lines)
