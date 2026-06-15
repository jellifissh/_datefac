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
    replay_decision_distribution: Dict[str, int],
    delta_rows: Iterable[Dict[str, Any]],
) -> str:
    decision_lines = [f"- {key}: {value}" for key, value in sorted(replay_decision_distribution.items())] or ["- none"]
    delta_lines = [
        f"- {row.get('metric_name', '')}: previous={row.get('previous_value', '')}, replay={row.get('replay_value', '')}, delta={row.get('delta_value', '')}"
        for row in delta_rows
    ] or ["- none"]
    return "\n".join(
        [
            "# 346B4R Executive Summary",
            "",
            "- 346B4R follows 346B3R because 346B4 was blocked only by 22 `semantic_class_unknown / needs_rule_refinement` rows.",
            "- This replay uses the exact same 500-row controlled batch from 346B4 and applies 346B3R patch proposals as sidecar rules only.",
            "- No live VLM/LLM calls, OCR runs, MinerU reruns, upstream write-back, or official rule changes occurred.",
            "",
            "## Same-Row-Set Proof",
            f"- previous_controlled_expansion_input_row_count: {manifest.get('previous_controlled_expansion_input_row_count', 0)}",
            f"- replay_input_row_count: {manifest.get('replay_input_row_count', 0)}",
            f"- same_row_set_replay: {manifest.get('same_row_set_replay', False)}",
            f"- new_row_selected_count: {manifest.get('new_row_selected_count', 0)}",
            "",
            "## Replay Outcome",
            f"- previous_safe_recovered_candidate_count: {manifest.get('previous_safe_recovered_candidate_count', 0)}",
            f"- replay_safe_recovered_candidate_count: {manifest.get('replay_safe_recovered_candidate_count', 0)}",
            f"- safe_recovered_delta: {manifest.get('safe_recovered_delta', 0)}",
            f"- previous_semantic_class_unknown_count: {manifest.get('previous_semantic_class_unknown_count', 0)}",
            f"- replay_semantic_class_unknown_count: {manifest.get('replay_semantic_class_unknown_count', 0)}",
            f"- unknown_resolved_count: {manifest.get('unknown_resolved_count', 0)}",
            f"- needs_rule_refinement_previous_count: {manifest.get('needs_rule_refinement_previous_count', 0)}",
            f"- needs_rule_refinement_replay_count: {manifest.get('needs_rule_refinement_replay_count', 0)}",
            "",
            "## Replay Decision Distribution",
            *decision_lines,
            "",
            "## Delta Highlights",
            *delta_lines,
            "",
            "## Safety And Gates",
            f"- patch_applied_row_count: {manifest.get('patch_applied_row_count', 0)}",
            f"- patch_regression_count: {manifest.get('patch_regression_count', 0)}",
            f"- false_positive_guardrail_hit_count: {manifest.get('false_positive_guardrail_hit_count', 0)}",
            f"- unit_semantic_mismatch_count: {manifest.get('unit_semantic_mismatch_count', 0)}",
            f"- evidence_weakness_count: {manifest.get('evidence_weakness_count', 0)}",
            f"- lineage_audit_passed: {manifest.get('lineage_audit_passed', False)}",
            f"- safe_to_continue_expansion: {manifest.get('safe_to_continue_expansion', False)}",
            f"- safe_to_continue_expansion_reason: {manifest.get('safe_to_continue_expansion_reason', '')}",
            "- Outputs remain demo-only sidecars with all formal/client/production gates closed.",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 346B4R Artifact Index",
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
            "# 346B4R Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            "- 346B5 Larger Quality-Limited Recovery Expansion still requires a dedicated QA checkpoint before any broader rollout.",
            "- 346C0 Live VLM Pilot Request Execution still requires explicit approval before any spend.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
