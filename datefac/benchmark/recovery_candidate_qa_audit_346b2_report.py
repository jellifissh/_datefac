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
    semantic_class_distribution: Dict[str, int],
    evidence_strength_distribution: Dict[str, int],
    top_unit_risks: Iterable[str],
) -> str:
    risk_lines = [f"- {item}" for item in top_unit_risks] or ["- none"]
    class_lines = [f"- {key}: {value}" for key, value in semantic_class_distribution.items()] or ["- none"]
    evidence_lines = [f"- {key}: {value}" for key, value in evidence_strength_distribution.items()] or ["- none"]
    return "\n".join(
        [
            "# 346B2 Executive Summary",
            "",
            "- 346B2 exists because 346B promoted 70 demo-only recovered candidates and the project needs a stricter QA audit before trusting those rules at scale.",
            f"- input_recovered_demo_candidate_count: {manifest.get('input_recovered_demo_candidate_count', 0)}",
            f"- audited_recovered_candidate_count: {manifest.get('audited_recovered_candidate_count', 0)}",
            "",
            "## Audit Result",
            f"- safe_recovered_candidate_count: {manifest.get('safe_recovered_candidate_count', 0)}",
            f"- risky_recovered_candidate_count: {manifest.get('risky_recovered_candidate_count', 0)}",
            f"- false_positive_suspect_count: {manifest.get('false_positive_suspect_count', 0)}",
            f"- needs_human_review_after_audit_count: {manifest.get('needs_human_review_after_audit_count', 0)}",
            f"- needs_rule_refinement_count: {manifest.get('needs_rule_refinement_count', 0)}",
            "",
            "## Unit Repair Audit",
            f"- unit_repair_audit_count: {manifest.get('unit_repair_audit_count', 0)}",
            f"- unit_repair_risk_count: {manifest.get('unit_repair_risk_count', 0)}",
            f"- ratio_multiple_unit_mismatch_count: {manifest.get('ratio_multiple_unit_mismatch_count', 0)}",
            f"- percentage_unit_mismatch_count: {manifest.get('percentage_unit_mismatch_count', 0)}",
            f"- per_share_unit_mismatch_count: {manifest.get('per_share_unit_mismatch_count', 0)}",
            f"- monetary_unit_mismatch_count: {manifest.get('monetary_unit_mismatch_count', 0)}",
            f"- unit_not_applicable_verified_count: {manifest.get('unit_not_applicable_verified_count', 0)}",
            f"- unit_not_applicable_risk_count: {manifest.get('unit_not_applicable_risk_count', 0)}",
            "",
            "## Semantic Class Distribution",
            *class_lines,
            "",
            "## Evidence Strength Distribution",
            *evidence_lines,
            "",
            "## UNIT_PERCENT_FROM_RATIO_CONTEXT Audit",
            f"- risky ratio/multiple or per-share applications were found: {manifest.get('ratio_multiple_unit_mismatch_count', 0) + manifest.get('per_share_unit_mismatch_count', 0)}",
            *risk_lines,
            "",
            "## Expansion Gate",
            f"- safe_to_expand_recovery: {manifest.get('safe_to_expand_recovery', False)}",
            f"- reason: {manifest.get('safe_to_expand_recovery_reason', '')}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            "- No live VLM/LLM calls were made.",
            "- Outputs remain demo-only QA sidecars and do not mutate upstream artifacts.",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 346B2 Artifact Index",
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
            "# 346B2 Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            "- 346B4 Full Quality-Limited Recovery Expansion is allowed only if safe_to_expand_recovery becomes true in a later approved task.",
            "- 346C0 Live VLM Pilot Request Execution still requires explicit approval before any spend.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
