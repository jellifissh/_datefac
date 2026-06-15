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
    semantic_distribution: Dict[str, int],
    unit_action_distribution: Dict[str, int],
) -> str:
    semantic_lines = [f"- {key}: {value}" for key, value in sorted(semantic_distribution.items())] or ["- none"]
    unit_lines = [f"- {key}: {value}" for key, value in sorted(unit_action_distribution.items())] or ["- none"]
    return "\n".join(
        [
            "# 346B5 Executive Summary",
            "",
            "- 346B5 follows 346B4Q because the 500-row controlled replay batch was independently QA-cleared for a larger but still bounded expansion.",
            f"- full_quality_limited_row_count: {manifest.get('full_quality_limited_row_count', 0)}",
            f"- larger_expansion_input_limit: {manifest.get('larger_expansion_input_limit', 0)}",
            f"- larger_expansion_input_row_count: {manifest.get('larger_expansion_input_row_count', 0)}",
            f"- already_346b_pilot_row_count: {manifest.get('already_346b_pilot_row_count', 0)}",
            f"- already_346b4_controlled_batch_row_count: {manifest.get('already_346b4_controlled_batch_row_count', 0)}",
            f"- new_quality_limited_row_count: {manifest.get('new_quality_limited_row_count', 0)}",
            "",
            "## Recovery Outcome",
            f"- recovered_candidate_count: {manifest.get('recovered_candidate_count', 0)}",
            f"- safe_recovered_candidate_count: {manifest.get('safe_recovered_candidate_count', 0)}",
            f"- risky_candidate_count: {manifest.get('risky_candidate_count', 0)}",
            f"- false_positive_guardrail_hit_count: {manifest.get('false_positive_guardrail_hit_count', 0)}",
            f"- still_quality_limited_count: {manifest.get('still_quality_limited_count', 0)}",
            f"- needs_human_review_count: {manifest.get('needs_human_review_count', 0)}",
            f"- needs_rule_refinement_count: {manifest.get('needs_rule_refinement_count', 0)}",
            f"- needs_vlm_count: {manifest.get('needs_vlm_count', 0)}",
            "",
            "## Sanitizer And Semantics",
            f"- value_sanitizer_attempt_count: {manifest.get('value_sanitizer_attempt_count', 0)}",
            f"- sanitized_value_success_count: {manifest.get('sanitized_value_success_count', 0)}",
            f"- sanitized_value_failure_count: {manifest.get('sanitized_value_failure_count', 0)}",
            f"- semantic_class_known_count: {manifest.get('semantic_class_known_count', 0)}",
            f"- semantic_class_unknown_count: {manifest.get('semantic_class_unknown_count', 0)}",
            f"- unit_repair_attempt_count: {manifest.get('unit_repair_attempt_count', 0)}",
            f"- unit_repair_success_count: {manifest.get('unit_repair_success_count', 0)}",
            f"- unit_semantic_mismatch_count: {manifest.get('unit_semantic_mismatch_count', 0)}",
            "",
            "## Semantic Class Distribution",
            *semantic_lines,
            "",
            "## Unit Action Distribution",
            *unit_lines,
            "",
            "## Audit Posture",
            f"- lineage_audit_passed: {manifest.get('lineage_audit_passed', False)}",
            f"- evidence_weakness_count: {manifest.get('evidence_weakness_count', 0)}",
            f"- safe_to_qa_larger_expansion: {manifest.get('safe_to_qa_larger_expansion', False)}",
            f"- safe_to_qa_larger_expansion_reason: {manifest.get('safe_to_qa_larger_expansion_reason', '')}",
            f"- recommended_next_step: {manifest.get('recommended_next_step', '')}",
            "- No live VLM/LLM calls, OCR runs, or MinerU reruns were performed.",
            "- Outputs remain sidecar/demo-only and do not mutate upstream datasets or official assets.",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 346B5 Artifact Index",
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
            "# 346B5 Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            "- 346B6 Full Quality-Limited Recovery Expansion still requires 346B5Q independent QA before any broader rollout.",
            "- 346C0 Live VLM Pilot Request Execution still requires explicit approval before any spend.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
