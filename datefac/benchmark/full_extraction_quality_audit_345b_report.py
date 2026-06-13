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
    stage_quality_rows: List[Dict[str, Any]],
    pdf_quality_rows: List[Dict[str, Any]],
    missing_hotspots: List[Dict[str, Any]],
    evidence_trace_quality: Dict[str, Any],
    priority_fix_queue: List[Dict[str, Any]],
) -> str:
    lines = [
        "# 345B Full Extraction Quality Audit",
        "",
        "## Input Context",
        f"- input_stage: {manifest.get('input_stage', '')}",
        f"- input_inventory_row_count: {manifest.get('input_inventory_row_count', '')}",
        f"- audited_row_count: {manifest.get('audited_row_count', '')}",
        "",
        "## Severity Totals",
        f"- high_severity_issue_count: {manifest.get('high_severity_issue_count', '')}",
        f"- medium_severity_issue_count: {manifest.get('medium_severity_issue_count', '')}",
        f"- low_severity_issue_count: {manifest.get('low_severity_issue_count', '')}",
        f"- no_issue_row_count: {manifest.get('no_issue_row_count', '')}",
        "",
        "## Major Issue Counts",
        f"- missing_unit_issue_count: {manifest.get('missing_unit_issue_count', '')}",
        f"- missing_period_issue_count: {manifest.get('missing_period_issue_count', '')}",
        f"- missing_source_trace_issue_count: {manifest.get('missing_source_trace_issue_count', '')}",
        f"- rejected_or_excluded_issue_count: {manifest.get('rejected_or_excluded_issue_count', '')}",
        f"- review_required_issue_count: {manifest.get('review_required_issue_count', '')}",
        f"- unnormalized_metric_issue_count: {manifest.get('unnormalized_metric_issue_count', '')}",
        f"- human_review_pending_issue_count: {manifest.get('human_review_pending_issue_count', '')}",
        f"- strict_human_review_pending_issue_count: {manifest.get('strict_human_review_pending_issue_count', '')}",
        "",
        "## Stage-Level Quality Distribution",
    ]
    for row in stage_quality_rows:
        lines.append(
            f"- {row.get('source_stage', '')}: high={row.get('high_severity_issue_count', 0)}, medium={row.get('medium_severity_issue_count', 0)}, low={row.get('low_severity_issue_count', 0)}, no_issue={row.get('no_issue_row_count', 0)}, top_issues={row.get('top_quality_issues', '')}"
        )
    lines.extend(["", "## PDF / Source Hotspots"])
    for row in pdf_quality_rows[:10]:
        lines.append(
            f"- {row.get('pdf_name', '')}: row_count={row.get('row_count', 0)}, high={row.get('high_severity_issue_count', 0)}, medium={row.get('medium_severity_issue_count', 0)}, top_issues={row.get('top_quality_issues', '')}"
        )
    lines.extend(["", "## Missing-Field Hotspots"])
    for row in missing_hotspots:
        lines.append(
            f"- {row.get('source_stage', '')}: missing_unit={row.get('missing_unit_count', 0)}, missing_period={row.get('missing_period_count', 0)}, missing_source_page={row.get('missing_source_page_count', 0)}"
        )
    lines.extend(
        [
            "",
            "## Evidence / Source Trace Quality",
            f"- total_rows_with_source_trace: {evidence_trace_quality.get('total_rows_with_source_trace', 0)}",
            f"- total_rows_missing_source_trace: {evidence_trace_quality.get('total_rows_missing_source_trace', 0)}",
            f"- downstream_candidate_missing_source_trace_count: {evidence_trace_quality.get('downstream_candidate_missing_source_trace_count', 0)}",
            f"- low_traceability_row_count: {evidence_trace_quality.get('low_traceability_row_count', 0)}",
            "",
            "## Priority Fix Queue",
            f"- priority_fix_queue_count: {manifest.get('priority_fix_queue_count', '')}",
            "- The priority queue highlights rows that should be fixed first before any broader structured demo export work continues.",
            f"- first_priority_examples: {', '.join(str(row.get('quality_row_id', '')) for row in priority_fix_queue[:5])}",
            "",
            "## Gate Boundary",
            f"- formal_client_export_allowed = {manifest.get('formal_client_export_allowed', False)}",
            f"- client_ready = {manifest.get('client_ready', False)}",
            f"- production_ready = {manifest.get('production_ready', False)}",
            f"- global_strict_human_review_completed = {manifest.get('global_strict_human_review_completed', False)}",
            "",
            "## Next",
            "- 345C should quantify metric candidate normalization coverage and blind spots.",
            "- 345D should only package a broader structured demo export after this audit evidence is understood.",
            "- 345E should keep QA gate decisions explicit and leave all formal/client/production gates false unless a later gate changes them.",
            "- 344G still waits for a truly human-filled 344F workbook.",
        ]
    )
    return "\n".join(lines)


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345B Artifact Index",
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
            "# 345B Next Plan",
            "",
            "- 345C Metric Candidate Normalization Coverage",
            "- 345D Full Structured Demo Export Package",
            "- 345E Full Structured QA Gate",
            "",
            "Boundary reminder:",
            "- 344G still waits for a truly human-filled 344F workbook.",
            "- 345B is audit-only and does not enable formal client export.",
        ]
    )

