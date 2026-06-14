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


def executive_summary_markdown(
    summary: Dict[str, Any],
    second_batch_applied_alias_map: List[Dict[str, Any]],
) -> str:
    top_alias_lines = [
        f"- {row.get('raw_metric_name', '')} -> {row.get('canonical_alias_target', '')}: {row.get('applied_row_count', 0)} rows"
        for row in sorted(
            second_batch_applied_alias_map,
            key=lambda item: (-int(item.get("applied_row_count", 0)), str(item.get("raw_metric_name", ""))),
        )[:5]
    ]
    if not top_alias_lines:
        top_alias_lines = ["- No second-batch alias produced an incremental row impact."]

    limitation_lines = [
        f"- {item}" for item in summary.get("metric_limitations", []) or []
    ] or ["- No additional limitations recorded."]

    return "\n".join(
        [
            "# 345C11 Second Batch Alias Apply Simulation",
            "",
            "## Input Context",
            f"- input_345c_decision: {summary.get('input_345c_decision', '')}",
            f"- input_345c6_decision: {summary.get('input_345c6_decision', '')}",
            f"- input_345c10_decision: {summary.get('input_345c10_decision', '')}",
            f"- first_batch_alias_count: {summary.get('first_batch_alias_count', 0)}",
            f"- second_batch_eligible_alias_count: {summary.get('second_batch_eligible_alias_count', 0)}",
            "",
            "## Impact",
            f"- first_batch_simulated_newly_normalized_row_count: {summary.get('first_batch_simulated_newly_normalized_row_count', 0)}",
            f"- second_batch_simulated_newly_normalized_row_count: {summary.get('second_batch_simulated_newly_normalized_row_count', 0)}",
            f"- cumulative_simulated_newly_normalized_row_count: {summary.get('cumulative_simulated_newly_normalized_row_count', 0)}",
            f"- coverage_ratio_before: {summary.get('coverage_ratio_before', None)}",
            f"- coverage_ratio_after_first_batch: {summary.get('coverage_ratio_after_first_batch', None)}",
            f"- coverage_ratio_after_second_batch: {summary.get('coverage_ratio_after_second_batch', None)}",
            f"- ready_candidate_count_before: {summary.get('ready_candidate_count_before', 0)}",
            f"- ready_candidate_count_after_first_batch: {summary.get('ready_candidate_count_after_first_batch', 0)}",
            f"- ready_candidate_count_after_second_batch: {summary.get('ready_candidate_count_after_second_batch', 0)}",
            "",
            "## Top Second-Batch Aliases By Row Impact",
            *top_alias_lines,
            "",
            "## Remaining Blind Spots",
            f"- remaining_unnormalized_raw_metric_name_count: {summary.get('remaining_unnormalized_raw_metric_name_count', 0)}",
            f"- remaining_unnormalized_metric_row_count: {summary.get('remaining_unnormalized_metric_row_count', 0)}",
            "",
            "## Matching Limitations",
            *limitation_lines,
            "",
            "## Boundary",
            "- 345C11 only performs a no-write-back cumulative alias simulation.",
            "- Official normalization rules were not modified.",
            "- Official alias assets were not modified.",
            f"- formal_client_export_allowed = {summary.get('formal_client_export_allowed', False)}",
            f"- client_ready = {summary.get('client_ready', False)}",
            f"- production_ready = {summary.get('production_ready', False)}",
            "",
            "## Final Recommendation",
            f"- alias_branch_final_recommendation: {summary.get('alias_branch_final_recommendation', '')}",
            f"- full_structured_demo_export_reasonable_after_345c11: {summary.get('full_structured_demo_export_reasonable_after_345c11', False)}",
            f"- next_recommended_step: {summary.get('next_recommended_step', '')}",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345C11 Artifact Index",
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
    recommendation = summary.get("alias_branch_final_recommendation", "")
    if recommendation == "STOP_ALIAS_BRANCH_AND_RETURN_TO_345D":
        plan_line = "- Recommended next scope: 345D Full Structured Demo Export Package"
        caveat_line = "- Carry remaining blind spots forward as alias-risk caveats because official rules/assets are still unchanged."
    elif recommendation == "CONTINUE_ONLY_WITH_EXPLICIT_NEW_SCOPE_APPROVAL":
        plan_line = "- Recommended next scope: separate explicitly approved alias-governance scope"
        caveat_line = "- Do not continue alias governance implicitly inside 345D."
    else:
        plan_line = "- Recommended next scope: one more tightly bounded alias review batch"
        caveat_line = "- Only continue if the user explicitly approves another alias-governance batch."

    return "\n".join(
        [
            "# 345C11 Next Plan",
            "",
            plan_line,
            caveat_line,
            "",
            "Boundary reminder:",
            "- 345C11 does not modify normalization rules.",
            "- 345C11 does not modify official alias assets.",
            "- 345C11 does not write back into 345C / 345C6 / 345C10 inputs.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
