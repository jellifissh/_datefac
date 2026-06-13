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
    stage_status_rows: List[Dict[str, Any]],
    missing_field_rows: List[Dict[str, Any]],
    downstream_readiness_summary: Dict[str, Any],
) -> str:
    lines = [
        "# 345A Full Structured Data Inventory",
        "",
        "## Scope",
        "- 345A inventories existing structured artifacts only.",
        "- It does not rerun MinerU, does not call LLM/VLM, and does not enable any formal export gate.",
        "- 344G still waits for a genuinely human-filled 344F workbook.",
        "",
        "## Inputs",
        f"- input_stage: {manifest.get('input_stage', '')}",
        f"- total_input_artifact_count: {manifest.get('total_input_artifact_count', '')}",
        f"- readable_input_artifact_count: {manifest.get('readable_input_artifact_count', '')}",
        f"- missing_input_artifact_count: {manifest.get('missing_input_artifact_count', '')}",
        "",
        "## Inventory Totals",
        f"- total_inventory_row_count: {manifest.get('total_inventory_row_count', '')}",
        f"- long_form_cell_count: {manifest.get('long_form_cell_count', '')}",
        f"- trusted_cell_count: {manifest.get('trusted_cell_count', '')}",
        f"- review_required_count: {manifest.get('review_required_count', '')}",
        f"- rejected_or_excluded_count: {manifest.get('rejected_or_excluded_count', '')}",
        f"- human_review_applied_count: {manifest.get('human_review_applied_count', '')}",
        f"- strict_human_review_pending_row_count: {manifest.get('strict_human_review_pending_row_count', '')}",
        f"- metric_candidate_row_count: {manifest.get('metric_candidate_row_count', '')}",
        f"- normalized_metric_row_count: {manifest.get('normalized_metric_row_count', '')}",
        f"- downstream_ready_candidate_count: {manifest.get('downstream_ready_candidate_count', '')}",
        "",
        "## Stage Distribution",
    ]
    for row in stage_status_rows:
        lines.append(
            f"- {row.get('source_stage', '')}: row_count = {row.get('row_count', 0)}, downstream_ready_candidate_count = {row.get('downstream_ready_candidate_count', 0)}, top_review_statuses = {row.get('top_review_statuses', '')}"
        )
    lines.extend(
        [
            "",
            "## Missing-Field Hotspots",
        ]
    )
    for row in missing_field_rows:
        lines.append(
            f"- {row.get('source_stage', '')}: missing_metric_name_count = {row.get('missing_metric_name_count', 0)}, missing_unit_count = {row.get('missing_unit_count', 0)}, missing_period_count = {row.get('missing_period_count', 0)}, missing_source_page_count = {row.get('missing_source_page_count', 0)}"
        )
    lines.extend(
        [
            "",
            "## Downstream Readiness",
            f"- downstream_ready_candidate_count: {downstream_readiness_summary.get('downstream_ready_candidate_count', 0)}",
            f"- blocked_missing_metric_name_count: {downstream_readiness_summary.get('blocked_missing_metric_name_count', 0)}",
            f"- blocked_missing_value_count: {downstream_readiness_summary.get('blocked_missing_value_count', 0)}",
            f"- blocked_rejected_status_count: {downstream_readiness_summary.get('blocked_rejected_status_count', 0)}",
            f"- blocked_missing_source_trace_count: {downstream_readiness_summary.get('blocked_missing_source_trace_count', 0)}",
            "",
            "## Gate Boundary",
            f"- formal_client_export_allowed = {manifest.get('formal_client_export_allowed', False)}",
            f"- client_ready = {manifest.get('client_ready', False)}",
            f"- production_ready = {manifest.get('production_ready', False)}",
            f"- global_strict_human_review_completed = {manifest.get('global_strict_human_review_completed', False)}",
            "",
            "## 345B Next",
            "- 345B should audit full extraction quality across the inventoried structured rows.",
            "- 345C should measure metric-candidate normalization coverage and blind spots.",
            "- 345D should prepare a full structured demo export package only after the audit evidence is clear.",
            "- 345E should evaluate the full structured QA gate while keeping all formal export flags false unless explicitly changed later.",
        ]
    )
    return "\n".join(lines)


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345A Artifact Index",
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
            "# 345A Next Plan",
            "",
            "- 345B Full Extraction Quality Audit",
            "- 345C Metric Candidate Normalization Coverage",
            "- 345D Full Structured Demo Export Package",
            "- 345E Full Structured QA Gate",
            "",
            "Boundary reminder:",
            "- 344G waits for a truly filled 344F workbook before strict human review ingestion can proceed.",
            "- None of these next steps should claim formal client export unless a later gate explicitly turns that on.",
        ]
    )

