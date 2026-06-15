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


def render_refined_unit_policy_markdown(policy: Dict[str, Any]) -> str:
    lines = [
        "# 346B3 Refined Unit Policy",
        "",
        f"- semantic_unit_policy_applied: {policy.get('semantic_unit_policy_applied', False)}",
        f"- unit_percent_from_ratio_context_deprecated: {policy.get('unit_percent_from_ratio_context_deprecated', False)}",
        "",
        "## Semantic Classes",
    ]
    for item in policy.get("semantic_classes", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Allowed / Forbidden Notes",
            f"- ratio_multiple_policy: {policy.get('ratio_multiple_policy', '')}",
            f"- percentage_margin_policy: {policy.get('percentage_margin_policy', '')}",
            f"- per_share_policy: {policy.get('per_share_policy', '')}",
            f"- monetary_amount_policy: {policy.get('monetary_amount_policy', '')}",
            f"- unknown_policy: {policy.get('unknown_policy', '')}",
        ]
    )
    return "\n".join(lines)


def render_rule_change_log_markdown(change_log: List[Dict[str, Any]]) -> str:
    lines = [
        "# 346B3 Rule Change Log",
        "",
        "| Change | Before | After | Scope |",
        "| --- | --- | --- | --- |",
    ]
    for row in change_log:
        lines.append(
            f"| {row.get('change_id', '')} | {row.get('before_rule', '')} | {row.get('after_rule', '')} | {row.get('scope', '')} |"
        )
    return "\n".join(lines)


def render_executive_summary_markdown(
    manifest: Dict[str, Any],
    *,
    replacement_summary: Iterable[str],
) -> str:
    replacement_lines = [f"- {item}" for item in replacement_summary] or ["- none"]
    return "\n".join(
        [
            "# 346B3 Executive Summary",
            "",
            "- 346B3 follows 346B2 because the previous deterministic unit recovery misapplied `%` to ratio/multiple and per-share rows.",
            f"- input_recovered_candidate_count: {manifest.get('input_recovered_candidate_count', 0)}",
            f"- input_safe_recovered_candidate_count: {manifest.get('input_safe_recovered_candidate_count', 0)}",
            f"- input_false_positive_suspect_count: {manifest.get('input_false_positive_suspect_count', 0)}",
            "",
            "## Refined Result",
            f"- refined_candidate_count: {manifest.get('refined_candidate_count', 0)}",
            f"- refined_safe_candidate_count: {manifest.get('refined_safe_candidate_count', 0)}",
            f"- remaining_false_positive_suspect_count: {manifest.get('remaining_false_positive_suspect_count', 0)}",
            f"- corrected_ratio_multiple_unit_count: {manifest.get('corrected_ratio_multiple_unit_count', 0)}",
            f"- corrected_per_share_unit_count: {manifest.get('corrected_per_share_unit_count', 0)}",
            f"- preserved_percentage_margin_unit_count: {manifest.get('preserved_percentage_margin_unit_count', 0)}",
            f"- demoted_candidate_count: {manifest.get('demoted_candidate_count', 0)}",
            f"- needs_human_review_count: {manifest.get('needs_human_review_count', 0)}",
            f"- needs_rule_refinement_count: {manifest.get('needs_rule_refinement_count', 0)}",
            "",
            "## UNIT_PERCENT_FROM_RATIO_CONTEXT Replacement",
            *replacement_lines,
            "",
            "## Readiness",
            f"- safe_to_reaudit: {manifest.get('safe_to_reaudit', False)}",
            f"- safe_to_expand_recovery: {manifest.get('safe_to_expand_recovery', False)}",
            f"- safe_to_expand_recovery_reason: {manifest.get('safe_to_expand_recovery_reason', '')}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            "- No live VLM/LLM calls were made.",
            "- Outputs remain demo-only sidecars and do not mutate upstream artifacts.",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 346B3 Artifact Index",
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
            "# 346B3 Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            "- 346B4 Full Quality-Limited Recovery Expansion stays blocked until a refined re-audit confirms safe_to_expand_recovery = true.",
            "- 346C0 Live VLM Pilot Request Execution still requires explicit approval before any spend.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
