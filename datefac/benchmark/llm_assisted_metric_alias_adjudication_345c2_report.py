from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


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


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
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


def prompt_audit_markdown(
    manifest: Dict[str, Any],
    request_rows: List[Dict[str, Any]],
) -> str:
    lines = [
        "# 345C2 Prompt Audit",
        "",
        f"- llm_mode: {manifest.get('llm_mode', '')}",
        f"- runtime_config_available: {manifest.get('runtime_config_available', False)}",
        f"- selected_alias_candidate_count: {manifest.get('selected_alias_candidate_count', 0)}",
        f"- live_llm_suggestions_generated: {manifest.get('live_llm_suggestions_generated', False)}",
        "",
        "## Prompt Boundaries",
        "- deterministic prompt payload only",
        "- raw metric alias adjudication only",
        "- no financial value invention allowed",
        "- JSON only response required",
        "- no normalization rule mutation allowed",
        "- no formal/client/production readiness claims allowed",
        "",
        "## Request Samples",
    ]
    for row in request_rows[:5]:
        lines.extend(
            [
                f"### {row.get('alias_adjudication_id', '')} / {row.get('raw_metric_name', '')}",
                f"- priority: {row.get('alias_candidate_priority', '')}",
                f"- frequency: {row.get('frequency', 0)}",
                f"- prompt_hash: {row.get('prompt_hash', '')}",
                f"- source_stages: {row.get('source_stages', '')}",
                f"- sample_row_ids: {row.get('sample_row_ids', '')}",
                "",
                "```json",
                row.get("prompt_text", ""),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def executive_summary_markdown(manifest: Dict[str, Any], suggestions: List[Dict[str, Any]]) -> str:
    high_conf = [
        row
        for row in suggestions
        if str(row.get("confidence", "")).upper() == "HIGH"
    ]
    proposed_new = [
        row
        for row in suggestions
        if row.get("suggested_action") == "PROPOSE_NEW_STANDARD_METRIC"
    ]
    review_rows = [
        row for row in suggestions if bool(row.get("needs_human_review"))
    ]
    insufficient = [
        row
        for row in suggestions
        if row.get("suggested_action") == "INSUFFICIENT_EVIDENCE"
    ]
    lines = [
        "# 345C2 LLM-Assisted Metric Alias Adjudication",
        "",
        "## Input Context",
        "- 345C alias candidates were used as sidecar-only adjudication input.",
        f"- input_alias_candidate_count: {manifest.get('input_alias_candidate_count', 0)}",
        f"- selected_alias_candidate_count: {manifest.get('selected_alias_candidate_count', 0)}",
        "",
        "## LLM Execution",
        f"- llm_mode: {manifest.get('llm_mode', '')}",
        f"- runtime_config_available: {manifest.get('runtime_config_available', False)}",
        f"- live_llm_suggestions_generated: {manifest.get('live_llm_suggestions_generated', False)}",
        "",
        "## Suggestion Distribution",
        f"- suggestion_row_count: {manifest.get('suggestion_row_count', 0)}",
        f"- map_to_existing_count: {manifest.get('map_to_existing_count', 0)}",
        f"- propose_new_standard_count: {manifest.get('propose_new_standard_count', 0)}",
        f"- exclude_non_core_count: {manifest.get('exclude_non_core_count', 0)}",
        f"- needs_human_review_count: {manifest.get('needs_human_review_count', 0)}",
        f"- insufficient_evidence_count: {manifest.get('insufficient_evidence_count', 0)}",
        "",
        "## High-Confidence Mappings",
    ]
    for row in high_conf[:10]:
        lines.append(
            f"- {row.get('raw_metric_name', '')} -> {row.get('suggested_standard_metric', '') or row.get('suggested_new_standard_metric', '')} ({row.get('suggested_action', '')})"
        )
    lines.extend(
        [
            "",
            "## Proposed New Standards",
        ]
    )
    for row in proposed_new[:10]:
        lines.append(
            f"- {row.get('raw_metric_name', '')} -> {row.get('suggested_new_standard_metric', '')}: {row.get('reason', '')}"
        )
    lines.extend(
        [
            "",
            "## Review Required / Insufficient Evidence",
            f"- review_required_rows: {len(review_rows)}",
            f"- insufficient_evidence_rows: {len(insufficient)}",
            "",
            "## Why No Rules Changed",
            "- 345C2 only generates sidecar suggestions and request packages.",
            "- No normalization rule, official alias asset, or upstream output was modified.",
            "",
            "## Gate Boundary",
            f"- formal_client_export_allowed = {manifest.get('formal_client_export_allowed', False)}",
            f"- client_ready = {manifest.get('client_ready', False)}",
            f"- production_ready = {manifest.get('production_ready', False)}",
            f"- global_strict_human_review_completed = {manifest.get('global_strict_human_review_completed', False)}",
            "",
            "## Next",
            "- 345C3 Alias Apply Simulation",
            "- 345C4 Human Review Package For Alias Suggestions when review volume remains high",
            "- 345D Full Structured Demo Export Package only after alias impact is measured",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
    return "\n".join(lines)


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345C2 Artifact Index",
        "",
        "| Artifact | Path | Use |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def next_plan_markdown(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 345C2 Next Plan",
            "",
            f"- Current mode outcome: {manifest.get('decision', '')}",
            "- 345C3 Alias Apply Simulation",
            "- 345C4 Human Review Package For Alias Suggestions if many rows remain review-required",
            "- 345D Full Structured Demo Export Package only after alias impact is measured",
            "",
            "Boundary reminder:",
            "- 345C2 did not modify normalization rules.",
            "- 345C2 did not modify official alias assets.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
