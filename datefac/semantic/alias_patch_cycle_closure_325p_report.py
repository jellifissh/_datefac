from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "funnel_counts",
    "cycle_summary",
    "stage_timeline",
    "remaining_burden",
    "residual_risks",
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


def alias_patch_cycle_closure_325p_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Alias Patch Cycle Closure 325P",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## 325 Funnel",
        f"- 325A input_alias_inventory_count: {summary.get('input_alias_inventory_count_325a', 0)}",
        f"- 325A safe_alias_review_batch_count: {summary.get('safe_alias_review_batch_count_325a', 0)}",
        f"- 325D send_to_adjudicator_count: {summary.get('send_to_adjudicator_count_325d', 0)}",
        f"- 325E request_count: {summary.get('request_count_325e', 0)}",
        f"- 325G accepted_for_human_confirmation_count: {summary.get('accepted_for_human_confirmation_count_325g', 0)}",
        f"- 325H confirmed_count: {summary.get('confirmed_count_325h', 0)}",
        f"- 325I sandbox_alias_rule_count: {summary.get('sandbox_alias_rule_count_325i', 0)}",
        f"- 325J ready_candidate_count: {summary.get('ready_candidate_count_325j', 0)}",
        f"- 325K ready_proposal_count: {summary.get('ready_proposal_count_325k', 0)}",
        f"- 325L patch_operation_count: {summary.get('patch_operation_count_325l', 0)}",
        f"- 325M approved_patch_operation_count: {summary.get('approved_patch_operation_count_325m', 0)}",
        f"- 325N applied_or_idempotent_operation_count: {summary.get('applied_or_idempotent_operation_count_325n', 0)}",
        f"- 325O visible_official_alias_rule_count: {summary.get('visible_official_alias_rule_count_325o', 0)}",
        "",
        "## 325 Official Rule Impact",
        f"- official_alias_rule_count_325: {summary.get('official_alias_rule_count_325', 0)}",
        f"- trusted_gain_325: {summary.get('trusted_gain_325', 0)}",
        f"- review_reduction_325: {summary.get('review_reduction_325', 0)}",
        f"- out_of_scope_or_rejected_gain_325: {summary.get('out_of_scope_or_rejected_gain_325', 0)}",
        f"- affected_candidate_count_325: {summary.get('affected_candidate_count_325', 0)}",
        "",
        "## Cumulative Progress",
        f"- previous_combined_official_rule_count: {summary.get('previous_combined_official_rule_count', 0)}",
        f"- previous_combined_trusted_gain: {summary.get('previous_combined_trusted_gain', 0)}",
        f"- previous_combined_review_reduction: {summary.get('previous_combined_review_reduction', 0)}",
        f"- cumulative_official_rule_count_after_325: {summary.get('cumulative_official_rule_count_after_325', 0)}",
        f"- cumulative_trusted_gain_after_325: {summary.get('cumulative_trusted_gain_after_325', 0)}",
        f"- cumulative_review_reduction_after_325: {summary.get('cumulative_review_reduction_after_325', 0)}",
        "",
        "## Closure Safety",
        f"- duplicate_delta_count: {summary.get('duplicate_delta_count', 0)}",
        f"- target_conflict_count: {summary.get('target_conflict_count', 0)}",
        f"- adjusted_metric_mismatch_count: {summary.get('adjusted_metric_mismatch_count', 0)}",
        f"- diluted_eps_mismatch_count: {summary.get('diluted_eps_mismatch_count', 0)}",
        f"- core_false_mapping_count: {summary.get('core_false_mapping_count', 0)}",
        f"- rollback_artifact_check_passed: {summary.get('rollback_artifact_check_passed', False)}",
        f"- no_official_asset_modification_during_325p: {summary.get('no_official_asset_modification_during_325p', False)}",
        "",
        "## Next Direction",
        f"- primary_next_direction: {summary.get('primary_next_direction', '')}",
        f"- secondary_next_direction: {summary.get('secondary_next_direction', '')}",
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
            "- 325P is a closure/reporting stage and does not modify official assets.",
            "- 325P uses cached 322 through 325 outputs only.",
            "- Remaining burden is inherited from 323P unless a newer reliable planning artifact exists.",
            "",
        ]
    )
    return "\n".join(lines)
