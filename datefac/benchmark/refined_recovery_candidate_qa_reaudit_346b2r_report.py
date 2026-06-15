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
    evidence_strength_distribution: Dict[str, int],
    semantic_distribution: Dict[str, int],
) -> str:
    evidence_lines = [f"- {key}: {value}" for key, value in sorted(evidence_strength_distribution.items())] or ["- none"]
    semantic_lines = [f"- {key}: {value}" for key, value in sorted(semantic_distribution.items())] or ["- none"]
    return "\n".join(
        [
            "# 346B2R Executive Summary",
            "",
            "- 346B2R independently re-audits the 346B3 refined sidecar candidates instead of trusting the 346B3 verdict directly.",
            f"- input_refined_candidate_count: {manifest.get('input_refined_candidate_count', 0)}",
            f"- reaudit_candidate_count: {manifest.get('reaudit_candidate_count', 0)}",
            f"- reaudit_safe_candidate_count: {manifest.get('reaudit_safe_candidate_count', 0)}",
            f"- reaudit_risky_candidate_count: {manifest.get('reaudit_risky_candidate_count', 0)}",
            f"- reaudit_false_positive_suspect_count: {manifest.get('reaudit_false_positive_suspect_count', 0)}",
            f"- false_positive_regression_fixed_count: {manifest.get('false_positive_regression_fixed_count', 0)}",
            f"- false_positive_regression_still_risky_count: {manifest.get('false_positive_regression_still_risky_count', 0)}",
            "",
            "## Unit Re-audit",
            f"- ratio_multiple_unit_mismatch_count: {manifest.get('ratio_multiple_unit_mismatch_count', 0)}",
            f"- per_share_unit_mismatch_count: {manifest.get('per_share_unit_mismatch_count', 0)}",
            f"- percentage_margin_unit_mismatch_count: {manifest.get('percentage_margin_unit_mismatch_count', 0)}",
            f"- monetary_unit_mismatch_count: {manifest.get('monetary_unit_mismatch_count', 0)}",
            "",
            "## Semantic Class Distribution",
            *semantic_lines,
            "",
            "## Evidence Strength Distribution",
            *evidence_lines,
            "",
            "## Readiness",
            f"- lineage_audit_passed: {manifest.get('lineage_audit_passed', False)}",
            f"- evidence_weakness_count: {manifest.get('evidence_weakness_count', 0)}",
            f"- safe_to_expand_recovery: {manifest.get('safe_to_expand_recovery', False)}",
            f"- safe_to_expand_recovery_reason: {manifest.get('safe_to_expand_recovery_reason', '')}",
            f"- recommended_expansion_scope: {manifest.get('recommended_expansion_scope', '')}",
            "- No live VLM/LLM calls were made.",
            "- Outputs remain demo-only sidecars and do not mutate upstream artifacts.",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 346B2R Artifact Index",
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
            "# 346B2R Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            "- 346C0 Live VLM Pilot Request Execution still requires explicit approval before any spend.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
