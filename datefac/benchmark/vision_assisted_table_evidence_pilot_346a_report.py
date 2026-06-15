from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


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


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_fieldnames = list(fieldnames or [])
    if not ordered_fieldnames:
        seen: set[str] = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    ordered_fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered_fieldnames, extrasaction="ignore")
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


def render_vlm_prompt_templates_markdown() -> str:
    return "\n".join(
        [
            "# 346A VLM Prompt Templates",
            "",
            "## System Template",
            "- You are checking bounded table evidence only.",
            "- Do not invent values.",
            "- Return only schema-valid suggestion output.",
            "- Do not overwrite source data.",
            "",
            "## User Template",
            "- Inspect the supplied table or page image path.",
            "- Use MinerU text context only as supporting evidence.",
            "- Answer only the listed field questions.",
            "- If evidence is weak, return `INSUFFICIENT_VISUAL_EVIDENCE`.",
            "",
            "## Question Families",
            "- Unit confirmation or repair.",
            "- Period or header alignment confirmation.",
            "- Value cell alignment confirmation.",
            "- Source trace sanity check.",
            "- Row type or header structure classification.",
        ]
    )


def render_conflict_handling_policy_markdown() -> str:
    return "\n".join(
        [
            "# 346A Conflict Handling Policy",
            "",
            "- VLM output is suggestion-only and must never auto-apply.",
            "- If image evidence conflicts with structured row text, flag `FLAG_CONFLICT`.",
            "- If confidence is medium or low, require human review.",
            "- If the row appears to be a header, subtotal, or footnote, return `NOT_A_DATA_ROW`.",
            "- If no deterministic image binding exists, do not generate a live-ready request.",
            "- Upstream 345D/345E data, MinerU outputs, official rules, and alias assets remain unchanged.",
        ]
    )


def render_executive_summary_markdown(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 346A Executive Summary",
            "",
            "- 346A treats MinerU images as bounded visual evidence instead of broad visual extraction.",
            "- This task prepares a request package only and makes zero live VLM calls.",
            f"- candidate_pool_row_count: {manifest.get('candidate_pool_row_count', 0)}",
            f"- selected_pilot_row_count: {manifest.get('selected_pilot_row_count', 0)}",
            f"- image_bound_count: {manifest.get('image_bound_count', 0)}",
            f"- image_missing_count: {manifest.get('image_missing_count', 0)}",
            f"- ambiguous_image_candidate_count: {manifest.get('ambiguous_image_candidate_count', 0)}",
            f"- vlm_request_count: {manifest.get('vlm_request_count', 0)}",
            "",
            "## Why No Live VLM Call",
            "- The pilot is capped at evidence packaging and cost estimation.",
            "- No vendor-priced inference is triggered.",
            "- No upstream structured data is mutated.",
            "",
            "## Repair Targets",
            f"- unit: {manifest.get('unit_repair_target_count', 0)}",
            f"- period: {manifest.get('period_repair_target_count', 0)}",
            f"- value alignment: {manifest.get('value_alignment_check_target_count', 0)}",
            f"- source trace: {manifest.get('source_trace_check_target_count', 0)}",
            f"- header structure: {manifest.get('header_structure_check_target_count', 0)}",
            "",
            "## Gate Status",
            f"- formal_client_export_allowed: {manifest.get('formal_client_export_allowed', False)}",
            f"- client_ready: {manifest.get('client_ready', False)}",
            f"- production_ready: {manifest.get('production_ready', False)}",
            "",
            "## Recommended Next Step",
            f"- {manifest.get('recommended_next_step', '')}",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 346A Artifact Index",
        "",
        "| Artifact | Path | Purpose |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def render_next_plan_markdown(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 346A Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            "- 346C Vision-Assisted Repair Response Ingestion requires an explicitly approved live VLM run first.",
            "- 346D Vision-Assisted Quality-Limited Row Recovery Simulation requires ingested VLM responses first.",
            "- 345G Demo Presentation Slide Outline remains a presentation-only branch option.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
