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
    manifest: Dict[str, Any],
    stage_rows: List[Dict[str, Any]],
    pdf_rows: List[Dict[str, Any]],
    alias_rows: List[Dict[str, Any]],
    blind_spots: Dict[str, Any],
) -> str:
    lines = [
        "# 345C Metric Candidate Normalization Coverage",
        "",
        "## Input Context",
        f"- input_inventory_row_count: {manifest.get('input_inventory_row_count', '')}",
        f"- input_audited_row_count: {manifest.get('input_audited_row_count', '')}",
        f"- metric_candidate_row_count: {manifest.get('metric_candidate_row_count', '')}",
        "",
        "## Coverage Totals",
        f"- normalized_metric_row_count: {manifest.get('normalized_metric_row_count', '')}",
        f"- unnormalized_metric_row_count: {manifest.get('unnormalized_metric_row_count', '')}",
        f"- normalization_coverage_ratio: {manifest.get('normalization_coverage_ratio', '')}",
        f"- unique_raw_metric_name_count: {manifest.get('unique_raw_metric_name_count', '')}",
        f"- unique_normalized_metric_name_count: {manifest.get('unique_normalized_metric_name_count', '')}",
        f"- unique_unnormalized_raw_metric_name_count: {manifest.get('unique_unnormalized_raw_metric_name_count', '')}",
        "",
        "## Stage Hotspots",
    ]
    for row in stage_rows:
        lines.append(
            f"- {row.get('source_stage', '')}: coverage_ratio={row.get('normalization_coverage_ratio', '')}, normalized={row.get('normalized_metric_row_count', 0)}, unnormalized={row.get('unnormalized_metric_row_count', 0)}, top_blind_spots={row.get('top_unnormalized_raw_metric_names', '')}"
        )
    lines.extend(["", "## PDF Hotspots"])
    for row in pdf_rows[:10]:
        lines.append(
            f"- {row.get('pdf_name', '')}: coverage_ratio={row.get('normalization_coverage_ratio', '')}, unnormalized={row.get('unnormalized_metric_row_count', 0)}, top_blind_spots={row.get('top_unnormalized_raw_metric_names', '')}"
        )
    lines.extend(
        [
            "",
            "## Alias Candidate Queue",
            f"- alias_candidate_count: {manifest.get('alias_candidate_count', '')}",
            f"- high_priority_alias_candidate_count: {manifest.get('high_priority_alias_candidate_count', '')}",
            f"- first_high_priority_examples: {', '.join(str(row.get('raw_metric_name', '')) for row in alias_rows[:10])}",
            "",
            "## Blind Spots",
            f"- top_unmapped_raw_metric_names: {blind_spots.get('top_unmapped_raw_metric_names', '')}",
            f"- stage_with_lowest_coverage: {manifest.get('stage_with_lowest_coverage', '')}",
            f"- pdf_with_lowest_coverage: {manifest.get('pdf_with_lowest_coverage', '')}",
            "",
            "## Ready Candidates",
            f"- ready_candidate_count_before_normalization_filter: {manifest.get('ready_candidate_count_before_normalization_filter', '')}",
            f"- ready_candidate_count_after_normalization_filter: {manifest.get('ready_candidate_count_after_normalization_filter', '')}",
            "",
            "## Gate Boundary",
            f"- formal_client_export_allowed = {manifest.get('formal_client_export_allowed', False)}",
            f"- client_ready = {manifest.get('client_ready', False)}",
            f"- production_ready = {manifest.get('production_ready', False)}",
            f"- global_strict_human_review_completed = {manifest.get('global_strict_human_review_completed', False)}",
            "",
            "## Next",
            "- 345D should package only explicitly analyzed structured demo rows without changing normalization rules here.",
            "- 345E should keep the QA gate explicit and leave all formal/client/production flags false unless a later gate changes them.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
    return "\n".join(lines)


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345C Artifact Index",
        "",
        "| Artifact | Path | Use |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def next_plan_markdown() -> str:
    return "\n".join(
        [
            "# 345C Next Plan",
            "",
            "- 345D Full Structured Demo Export Package",
            "- 345E Full Structured QA Gate",
            "",
            "Boundary reminder:",
            "- 345C does not modify normalization rules.",
            "- 344G still waits for a truly human-filled 344F workbook.",
        ]
    )

