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
    qa_decision_distribution: Dict[str, int],
    patch_decision_distribution: Dict[str, int],
) -> str:
    qa_lines = [f"- {key}: {value}" for key, value in sorted(qa_decision_distribution.items())] or ["- none"]
    patch_lines = [f"- {key}: {value}" for key, value in sorted(patch_decision_distribution.items())] or ["- none"]
    return "\n".join(
        [
            "# 346B4Q Executive Summary",
            "",
            "- 346B4Q follows 346B4R because replay-safe rows still require an independent QA gate before any larger controlled expansion.",
            "- This stage audits the same 346B4R replay-safe candidate set only; it does not select new rows or recover new rows.",
            "- No live VLM/LLM calls, OCR runs, MinerU reruns, upstream write-back, or official rule changes occurred.",
            "",
            "## Replay Proof",
            f"- same_row_set_replay_verified: {manifest.get('same_row_set_replay_verified', False)}",
            f"- replay_input_row_count: {manifest.get('replay_input_row_count', 0)}",
            f"- replay_safe_recovered_candidate_count: {manifest.get('replay_safe_recovered_candidate_count', 0)}",
            f"- new_row_selected_count: {manifest.get('new_row_selected_count', 0)}",
            "",
            "## QA Closure",
            f"- qa_audited_candidate_count: {manifest.get('qa_audited_candidate_count', 0)}",
            f"- qa_safe_candidate_count: {manifest.get('qa_safe_candidate_count', 0)}",
            f"- qa_risky_candidate_count: {manifest.get('qa_risky_candidate_count', 0)}",
            f"- qa_false_positive_suspect_count: {manifest.get('qa_false_positive_suspect_count', 0)}",
            f"- qa_needs_human_review_count: {manifest.get('qa_needs_human_review_count', 0)}",
            f"- qa_needs_rule_refinement_count: {manifest.get('qa_needs_rule_refinement_count', 0)}",
            "",
            "## QA Decision Distribution",
            *qa_lines,
            "",
            "## Patch-Applied Row QA",
            f"- patch_applied_audited_row_count: {manifest.get('patch_applied_audited_row_count', 0)}",
            f"- patch_applied_qa_pass_count: {manifest.get('patch_applied_qa_pass_count', 0)}",
            f"- patch_applied_qa_risk_count: {manifest.get('patch_applied_qa_risk_count', 0)}",
            f"- patch_applied_qa_fail_count: {manifest.get('patch_applied_qa_fail_count', 0)}",
            *patch_lines,
            "",
            "## Independent Recheck",
            f"- semantic_class_disagreement_count: {manifest.get('semantic_class_disagreement_count', 0)}",
            f"- unit_semantic_mismatch_count: {manifest.get('unit_semantic_mismatch_count', 0)}",
            f"- false_positive_guardrail_hit_count: {manifest.get('false_positive_guardrail_hit_count', 0)}",
            f"- evidence_weakness_count: {manifest.get('evidence_weakness_count', 0)}",
            f"- lineage_audit_passed: {manifest.get('lineage_audit_passed', False)}",
            "",
            "## Readiness",
            f"- qa_safe_to_larger_expansion: {manifest.get('qa_safe_to_larger_expansion', False)}",
            f"- qa_safe_to_larger_expansion_reason: {manifest.get('qa_safe_to_larger_expansion_reason', '')}",
            f"- recommended_larger_expansion_row_limit: {manifest.get('recommended_larger_expansion_row_limit', 0)}",
            f"- recommended_next_step: {manifest.get('recommended_next_step', '')}",
            "- Outputs remain demo-only sidecars with all formal/client/production gates closed.",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 346B4Q Artifact Index",
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
            "# 346B4Q Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            f"- Recommended larger expansion row limit: {manifest.get('recommended_larger_expansion_row_limit', 0)}",
            "- Even if larger controlled expansion is allowed, the scope remains demo-only and sidecar-only.",
            "- 346C0 Live VLM Pilot Request Execution still requires explicit approval before any spend.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
