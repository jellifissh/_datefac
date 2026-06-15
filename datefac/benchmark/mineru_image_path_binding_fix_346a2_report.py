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
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


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


def render_executive_summary_markdown(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 346A2 Executive Summary",
            "",
            "- 346A2 exists because 346A selected a strong pilot set but had zero deterministic image bindings.",
            f"- input_346a_dir: {manifest.get('input_346a_dir', '')}",
            f"- supplied_mineru_roots: {', '.join(manifest.get('supplied_evidence_roots', [])) or 'none'}",
            f"- evidence_catalog_count: {manifest.get('evidence_catalog_count', 0)}",
            f"- binding_candidate_count: {manifest.get('binding_candidate_count', 0)}",
            f"- selected_pilot_row_count: {manifest.get('selected_pilot_row_count', 0)}",
            "",
            "## Binding Result",
            f"- bound_row_count: {manifest.get('bound_row_count', 0)}",
            f"- image_bound_count: {manifest.get('image_bound_count', 0)}",
            f"- table_crop_bound_count: {manifest.get('table_crop_bound_count', 0)}",
            f"- page_image_bound_count: {manifest.get('page_image_bound_count', 0)}",
            f"- json_md_context_bound_count: {manifest.get('json_md_context_bound_count', 0)}",
            f"- image_missing_count: {manifest.get('image_missing_count', 0)}",
            f"- ambiguous_image_candidate_count: {manifest.get('ambiguous_image_candidate_count', 0)}",
            "",
            "## VLM Request Refresh",
            f"- vlm_request_count: {manifest.get('vlm_request_count', 0)}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- live_ready_request_package: {manifest.get('live_ready_request_package', False)}",
            "- Requests remain suggestion-only and never auto-apply.",
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
        "# 346A2 Artifact Index",
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
            "# 346A2 Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            "- 346C Vision-Assisted Repair Response Ingestion still requires an explicitly approved live VLM run first.",
            "- 345G Demo Presentation Slide Outline remains a presentation-only branch option.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
