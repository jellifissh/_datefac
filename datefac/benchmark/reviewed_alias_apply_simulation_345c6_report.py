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


def executive_summary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 345C6 Reviewed Alias Apply Simulation",
            "",
            "## Input Context",
            f"- input_345c_decision: {summary.get('input_345c_decision', '')}",
            f"- input_345c5_decision: {summary.get('input_345c5_decision', '')}",
            f"- validated_approved_alias_count: {summary.get('validated_approved_alias_count', 0)}",
            f"- applied_alias_key_count: {summary.get('applied_alias_key_count', 0)}",
            "",
            "## Simulation Impact",
            f"- simulated_alias_applied_row_count: {summary.get('simulated_alias_applied_row_count', 0)}",
            f"- simulated_newly_normalized_row_count: {summary.get('simulated_newly_normalized_row_count', 0)}",
            f"- normalization_coverage_ratio_before: {summary.get('normalization_coverage_ratio_before', None)}",
            f"- normalization_coverage_ratio_after_simulation: {summary.get('normalization_coverage_ratio_after_simulation', None)}",
            f"- normalization_coverage_ratio_delta: {summary.get('normalization_coverage_ratio_delta', None)}",
            f"- ready_candidate_count_before_simulation: {summary.get('ready_candidate_count_before_simulation', 0)}",
            f"- ready_candidate_count_after_alias_simulation: {summary.get('ready_candidate_count_after_alias_simulation', 0)}",
            f"- ready_candidate_count_delta: {summary.get('ready_candidate_count_delta', 0)}",
            "",
            "## Remaining Blind Spots",
            f"- remaining_unnormalized_raw_metric_name_count: {summary.get('remaining_unnormalized_raw_metric_name_count', 0)}",
            f"- remaining_unnormalized_metric_row_count: {summary.get('remaining_unnormalized_metric_row_count', 0)}",
            f"- remaining_ready_candidate_count: {summary.get('remaining_ready_candidate_count', 0)}",
            "",
            "## Boundary",
            "- 345C6 only simulates reviewed approved aliases in memory and writes a no-write-back sidecar.",
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


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345C6 Artifact Index",
        "",
        "| Artifact | Path | Use |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def next_plan_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 345C6 Next Plan",
            "",
            f"- Recommended next scope: {summary.get('recommended_next_scope', '')}",
            "",
            "Boundary reminder:",
            "- 345C6 does not modify normalization rules.",
            "- 345C6 does not modify official alias assets.",
            "- 345C6 does not write back into 345C/345C5 inputs.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
