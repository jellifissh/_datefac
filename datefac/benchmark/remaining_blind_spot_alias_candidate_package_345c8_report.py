from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
            )


def executive_summary_markdown(summary: Dict[str, Any], top_rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# 345C8 Remaining Blind Spot Alias Candidate Package",
        "",
        "## Input Context",
        f"- input_345c6_decision: {summary.get('input_345c6_decision', '')}",
        f"- input_345c7_decision: {summary.get('input_345c7_decision', '')}",
        "- 345C8 exists because 345C7 concluded the first alias-governance batch was not enough for controlled rule update or full demo export.",
        "",
        "## Remaining Blind Spots",
        f"- remaining_unnormalized_raw_metric_name_count: {summary.get('remaining_unnormalized_raw_metric_name_count', 0)}",
        f"- remaining_unnormalized_metric_row_count: {summary.get('remaining_unnormalized_metric_row_count', 0)}",
        "",
        "## Candidate Selection",
        f"- selected_candidate_count: {summary.get('selected_candidate_count', 0)}",
        f"- max_blind_spot_candidates: {summary.get('max_blind_spot_candidates', 0)}",
        f"- min_row_impact: {summary.get('min_row_impact', 0)}",
        f"- selected_estimated_row_impact_total: {summary.get('selected_estimated_row_impact_total', 0)}",
        f"- selected_estimated_coverage_delta_total: {summary.get('selected_estimated_coverage_delta_total', None)}",
        f"- selected_estimated_ready_candidate_delta_total: {summary.get('selected_estimated_ready_candidate_delta_total', 0)}",
        "",
        "## Priority Distribution",
        f"- high_priority_candidate_count: {summary.get('high_priority_candidate_count', 0)}",
        f"- medium_priority_candidate_count: {summary.get('medium_priority_candidate_count', 0)}",
        f"- low_priority_candidate_count: {summary.get('low_priority_candidate_count', 0)}",
        "",
        "## Recommendation Distribution",
        f"- include_in_second_review_batch_count: {summary.get('include_in_second_review_batch_count', 0)}",
        f"- include_as_context_only_count: {summary.get('include_as_context_only_count', 0)}",
        f"- needs_source_context_before_review_count: {summary.get('needs_source_context_before_review_count', 0)}",
        f"- exclude_too_generic_count: {summary.get('exclude_too_generic_count', 0)}",
        "",
        "## Risk Distribution",
        f"- low_risk_candidate_count: {summary.get('low_risk_candidate_count', 0)}",
        f"- medium_risk_candidate_count: {summary.get('medium_risk_candidate_count', 0)}",
        f"- high_risk_candidate_count: {summary.get('high_risk_candidate_count', 0)}",
        "",
        "## Top Selected Candidates",
    ]
    for row in top_rows:
        lines.append(
            f"- {row.get('raw_metric_name', '')}: rows={row.get('remaining_row_count', 0)}, "
            f"priority={row.get('candidate_priority', '')}, "
            f"recommendation={row.get('review_recommendation', '')}, "
            f"risk={row.get('risk_level', '')}"
        )
    lines.extend(
        [
            "",
            "## Branch Decision",
            f"- alias_branch_stop_or_continue_decision: {summary.get('alias_branch_stop_or_continue_decision', '')}",
            f"- full_structured_demo_export_reasonable_after_345c8: {summary.get('full_structured_demo_export_reasonable_after_345c8', False)}",
            "",
            "## Boundary",
            "- 345C8 only packages remaining blind-spot candidates and a branch decision.",
            "- It does not perform human review.",
            "- It does not call LLM/VLM.",
            "- It does not modify normalization rules or official alias assets.",
            f"- formal_client_export_allowed = {summary.get('formal_client_export_allowed', False)}",
            f"- client_ready = {summary.get('client_ready', False)}",
            f"- production_ready = {summary.get('production_ready', False)}",
            "",
            "## Next",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
    return "\n".join(lines)


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345C8 Artifact Index",
        "",
        "| Artifact | Path | Use |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def next_plan_markdown(summary: Dict[str, Any], stop_or_continue_decision: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 345C8 Next Plan",
            "",
            f"- alias_branch_stop_or_continue_decision: {summary.get('alias_branch_stop_or_continue_decision', '')}",
            f"- next_plan_recommendation: {stop_or_continue_decision.get('next_plan_recommendation', '')}",
            "",
            "Boundary reminder:",
            "- 345C8 does not modify normalization rules.",
            "- 345C8 does not modify official alias assets.",
            "- 345C8 does not write back into 345C6/345C7 inputs.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
