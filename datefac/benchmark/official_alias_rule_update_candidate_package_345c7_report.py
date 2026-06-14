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


def executive_summary_markdown(summary: Dict[str, Any], top_impact_rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# 345C7 Official Alias Rule Update Candidate Package",
        "",
        "## Input Context",
        f"- input_345c5_decision: {summary.get('input_345c5_decision', '')}",
        f"- input_345c6_decision: {summary.get('input_345c6_decision', '')}",
        f"- validated_approved_alias_count: {summary.get('validated_approved_alias_count', 0)}",
        "",
        "## Candidate Packaging",
        f"- candidate_row_count: {summary.get('candidate_row_count', 0)}",
        f"- controlled_rule_update_candidate_count: {summary.get('controlled_rule_update_candidate_count', 0)}",
        f"- demo_only_sidecar_candidate_count: {summary.get('demo_only_sidecar_candidate_count', 0)}",
        f"- needs_additional_review_candidate_count: {summary.get('needs_additional_review_candidate_count', 0)}",
        f"- do_not_update_rule_candidate_count: {summary.get('do_not_update_rule_candidate_count', 0)}",
        "",
        "## Risk Distribution",
        f"- low_risk_candidate_count: {summary.get('low_risk_candidate_count', 0)}",
        f"- medium_risk_candidate_count: {summary.get('medium_risk_candidate_count', 0)}",
        f"- high_risk_candidate_count: {summary.get('high_risk_candidate_count', 0)}",
        "",
        "## Preserved 345C6 Impact",
        f"- simulated_alias_applied_row_count: {summary.get('simulated_alias_applied_row_count', 0)}",
        f"- simulated_newly_normalized_row_count: {summary.get('simulated_newly_normalized_row_count', 0)}",
        f"- normalization_coverage_ratio_before: {summary.get('normalization_coverage_ratio_before', None)}",
        f"- normalization_coverage_ratio_after_simulation: {summary.get('normalization_coverage_ratio_after_simulation', None)}",
        f"- normalization_coverage_ratio_delta: {summary.get('normalization_coverage_ratio_delta', None)}",
        f"- ready_candidate_count_delta: {summary.get('ready_candidate_count_delta', None)}",
        "",
        "## Remaining Blind Spots",
        f"- remaining_unnormalized_raw_metric_name_count: {summary.get('remaining_unnormalized_raw_metric_name_count', 0)}",
        f"- remaining_unnormalized_metric_row_count: {summary.get('remaining_unnormalized_metric_row_count', 0)}",
        "",
        "## Top Impact Aliases",
    ]
    for row in top_impact_rows:
        lines.append(
            f"- {row.get('raw_metric_name', '')} -> {row.get('proposed_standard_metric', '')}: "
            f"rows={row.get('simulation_newly_normalized_row_count', 0)}, "
            f"coverage_delta_contribution={row.get('coverage_delta_contribution', None)}, "
            f"recommendation={row.get('rule_update_recommendation', '')}, "
            f"risk={row.get('rule_update_risk_level', '')}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "- 345C7 only prepares a candidate package for later explicit review.",
            "- Official normalization rules were not modified.",
            "- Official alias assets were not modified.",
            f"- formal_client_export_allowed = {summary.get('formal_client_export_allowed', False)}",
            f"- client_ready = {summary.get('client_ready', False)}",
            f"- production_ready = {summary.get('production_ready', False)}",
            "",
            "## Recommendation",
            f"- recommended_next_scope: {summary.get('recommended_next_scope', '')}",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
    return "\n".join(lines)


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345C7 Artifact Index",
        "",
        "| Artifact | Path | Use |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def rule_update_checklist_markdown() -> str:
    return "\n".join(
        [
            "# 345C7 Rule Update Checklist",
            "",
            "1. This package does not modify official rules.",
            "2. Only candidates marked `READY_FOR_CONTROLLED_RULE_UPDATE` may be considered for a later explicit rule update.",
            "3. Official alias assets should be changed only in a separate reviewed task.",
            "4. Any future official rule update must include before/after tests and a rollback plan.",
            "5. Demo export may use this candidate package only as a documented sidecar unless a rule update is explicitly applied.",
        ]
    )


def next_plan_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 345C7 Next Plan",
            "",
            f"- Recommended next scope: {summary.get('recommended_next_scope', '')}",
            "",
            "Boundary reminder:",
            "- 345C7 does not modify normalization rules.",
            "- 345C7 does not modify official alias assets.",
            "- 345C7 does not write back into 345C5/345C6 inputs.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
