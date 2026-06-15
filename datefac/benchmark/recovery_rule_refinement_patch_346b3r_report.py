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


def render_patched_unit_policy_preview_markdown(preview: Dict[str, Any]) -> str:
    lines = [
        "# 346B3R Patched Unit Policy Preview",
        "",
        f"- replay_scope: {preview.get('replay_scope', '')}",
        f"- sidecar_only: {preview.get('sidecar_only', False)}",
        f"- no_write_back: {preview.get('no_write_back', False)}",
        "",
        "## Baseline",
        f"- baseline_policy_source: {preview.get('baseline_policy_source', '')}",
        f"- baseline_decision: {preview.get('baseline_decision', '')}",
        "",
        "## Semantic Patch Families",
    ]
    for row in preview.get("semantic_classifier_patch_preview", []):
        lines.append(
            f"- {row.get('metric_family', '')}: {row.get('proposed_semantic_class', '')} via {row.get('patch_candidate_type', '')}"
        )
    lines.extend(
        [
            "",
            "## Unit Policy Preview",
        ]
    )
    for row in preview.get("unit_policy_patch_preview", []):
        lines.append(
            f"- {row.get('metric_family', '')}: {row.get('preview_policy', '')}"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
        ]
    )
    for item in preview.get("guardrails", []):
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_executive_summary_markdown(
    manifest: Dict[str, Any],
    *,
    family_distribution: Dict[str, int],
    triage_distribution: Dict[str, int],
) -> str:
    family_lines = [f"- {key}: {value}" for key, value in sorted(family_distribution.items())] or ["- none"]
    triage_lines = [f"- {key}: {value}" for key, value in sorted(triage_distribution.items())] or ["- none"]
    return "\n".join(
        [
            "# 346B3R Executive Summary",
            "",
            "- 346B3R follows 346B4 because controlled expansion stayed safe overall but surfaced 22 `semantic_class_unknown` rule gaps.",
            "- This task audits only the 346B4 unknown/refinement rows and prepares deterministic patch previews.",
            "- No live VLM/LLM calls, OCR runs, MinerU reruns, or upstream write-back were performed.",
            "",
            "## Input Snapshot",
            f"- input_346b4_controlled_expansion_input_row_count: {manifest.get('input_346b4_controlled_expansion_input_row_count', 0)}",
            f"- input_346b4_safe_recovered_candidate_count: {manifest.get('input_346b4_safe_recovered_candidate_count', 0)}",
            f"- input_346b4_semantic_class_unknown_count: {manifest.get('input_346b4_semantic_class_unknown_count', 0)}",
            f"- input_346b4_needs_rule_refinement_count: {manifest.get('input_346b4_needs_rule_refinement_count', 0)}",
            "",
            "## Audited Unknown Families",
            *family_lines,
            "",
            "## Patch Triage Distribution",
            *triage_lines,
            "",
            "## Outcome",
            f"- audited_unknown_row_count: {manifest.get('audited_unknown_row_count', 0)}",
            f"- patchable_rule_gap_count: {manifest.get('patchable_rule_gap_count', 0)}",
            f"- non_patchable_row_count: {manifest.get('non_patchable_row_count', 0)}",
            f"- proposed_semantic_classifier_patch_count: {manifest.get('proposed_semantic_classifier_patch_count', 0)}",
            f"- proposed_unit_policy_patch_count: {manifest.get('proposed_unit_policy_patch_count', 0)}",
            f"- rows_converted_from_unknown_to_known_semantic_class_count: {manifest.get('rows_converted_from_unknown_to_known_semantic_class_count', 0)}",
            f"- rows_kept_quality_limited_count: {manifest.get('rows_kept_quality_limited_count', 0)}",
            f"- rows_kept_human_review_count: {manifest.get('rows_kept_human_review_count', 0)}",
            f"- rows_requiring_future_vlm_count: {manifest.get('rows_requiring_future_vlm_count', 0)}",
            "",
            "## Replay Posture",
            f"- patch_safe_to_replay_count: {manifest.get('patch_safe_to_replay_count', 0)}",
            f"- patch_requires_reaudit_count: {manifest.get('patch_requires_reaudit_count', 0)}",
            f"- patch_unsafe_count: {manifest.get('patch_unsafe_count', 0)}",
            f"- safe_to_replay_346b4: {manifest.get('safe_to_replay_346b4', False)}",
            f"- safe_to_continue_expansion: {manifest.get('safe_to_continue_expansion', False)}",
            f"- safe_to_continue_expansion_reason: {manifest.get('safe_to_continue_expansion_reason', '')}",
            "",
            "## Boundary Reminder",
            "- Outputs remain demo-only sidecars and patch previews.",
            "- Formal client export, client_ready, and production_ready all remain false.",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 346B3R Artifact Index",
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
            "# 346B3R Next Plan",
            "",
            f"- Recommended next step: {manifest.get('recommended_next_step', '')}",
            f"- Reason: {manifest.get('recommended_next_step_reason', '')}",
            "- 346B4 replay is still sidecar-only and must be re-audited before any broader expansion is considered.",
            "- 346C0 Live VLM Pilot Request Execution still requires explicit approval before any spend.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
