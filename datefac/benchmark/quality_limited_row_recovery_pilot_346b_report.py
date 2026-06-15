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


def render_executive_summary_markdown(
    manifest: Dict[str, Any],
    *,
    top_recovery_actions: Iterable[str],
    top_fail_reasons: Iterable[str],
) -> str:
    recovery_lines = [f"- {item}" for item in top_recovery_actions] or ["- none"]
    fail_reason_lines = [f"- {item}" for item in top_fail_reasons] or ["- none"]
    return "\n".join(
        [
            "# 346B Executive Summary",
            "",
            "- 346B follows 346A2 because the project now has a bounded pilot set with deterministic text/image evidence binding but still no live VLM execution.",
            f"- full_quality_limited_row_count: {manifest.get('full_quality_limited_row_count', 0)}",
            f"- pilot_input_row_count: {manifest.get('pilot_input_row_count', 0)}",
            f"- image_bound_input_count: {manifest.get('image_bound_input_count', 0)}",
            f"- json_md_context_bound_input_count: {manifest.get('json_md_context_bound_input_count', 0)}",
            "",
            "## Recovery Layers",
            f"- value_sanitizer_attempt_count: {manifest.get('value_sanitizer_attempt_count', 0)}",
            f"- sanitized_value_success_count: {manifest.get('sanitized_value_success_count', 0)}",
            f"- sanitized_value_failure_count: {manifest.get('sanitized_value_failure_count', 0)}",
            f"- unit_injection_attempt_count: {manifest.get('unit_injection_attempt_count', 0)}",
            f"- unit_injection_success_count: {manifest.get('unit_injection_success_count', 0)}",
            f"- unit_not_applicable_count: {manifest.get('unit_not_applicable_count', 0)}",
            f"- period_injection_attempt_count: {manifest.get('period_injection_attempt_count', 0)}",
            f"- period_injection_success_count: {manifest.get('period_injection_success_count', 0)}",
            f"- evidence_assisted_recovery_attempt_count: {manifest.get('evidence_assisted_recovery_attempt_count', 0)}",
            f"- evidence_assisted_recovery_success_count: {manifest.get('evidence_assisted_recovery_success_count', 0)}",
            "",
            "## Re-Audit Result",
            f"- recovered_demo_candidate_count: {manifest.get('recovered_demo_candidate_count', 0)}",
            f"- still_quality_limited_count: {manifest.get('still_quality_limited_count', 0)}",
            f"- needs_vlm_count: {manifest.get('needs_vlm_count', 0)}",
            f"- needs_human_review_count: {manifest.get('needs_human_review_count', 0)}",
            f"- downgraded_excluded_count: {manifest.get('downgraded_excluded_count', 0)}",
            "",
            "## Top Recovery Actions",
            *recovery_lines,
            "",
            "## Top Fail Reasons",
            *fail_reason_lines,
            "",
            "## Boundary Notes",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            "- No live VLM/LLM calls were made.",
            "- Outputs remain sidecar/demo-only suggestions and do not mutate upstream artifacts.",
            f"- formal_client_export_allowed: {manifest.get('formal_client_export_allowed', False)}",
            f"- client_ready: {manifest.get('client_ready', False)}",
            f"- production_ready: {manifest.get('production_ready', False)}",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 346B Artifact Index",
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
            "# 346B Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            "- 346C Vision-Assisted Repair Response Ingestion still requires an explicitly approved live VLM run and saved responses first.",
            "- 346C0 Live VLM Pilot Request Execution remains optional and must be explicitly approved before any spend occurs.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
