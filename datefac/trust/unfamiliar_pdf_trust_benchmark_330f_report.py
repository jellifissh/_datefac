from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "source_inventory",
    "coverage",
    "distribution",
    "delivery_summary",
    "official_asset_proof",
    "known_limitations",
]

SAMPLES_SHEET_ORDER = [
    "summary",
    "artifact_row_view",
    "strict_deduped_view",
    "cross_artifact_deduped_view",
    "strict_duplicate_rows",
    "cross_artifact_duplicate_rows",
    "qa_checks",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    base = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    out = base
    index = 1
    while out in used:
        suffix = f"_{index}"
        out = f"{base[:31 - len(suffix)]}{suffix}"
        index += 1
    used.add(out)
    return out


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame], order: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in order:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def unfamiliar_pdf_trust_benchmark_330f_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Unfamiliar PDF Trust Benchmark 330F",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## 330E Validation",
        f"- validated_330e_benchmark: {summary.get('validated_330e_benchmark', False)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
        "## Source Status",
        f"- unfamiliar_source_status: {summary.get('unfamiliar_source_status', '')}",
        f"- unfamiliar_source_dir_count: {summary.get('unfamiliar_source_dir_count', 0)}",
        f"- unfamiliar_source_dirs_checked: {json.dumps(summary.get('unfamiliar_source_dirs_checked', []), ensure_ascii=False)}",
        "",
    ]
    if summary.get("unfamiliar_source_status") == "loaded":
        lines.extend(
            [
                "## Counts",
                f"- unfamiliar_candidate_artifact_row_count: {summary.get('unfamiliar_candidate_artifact_row_count', 0)}",
                f"- unfamiliar_strict_deduped_candidate_count: {summary.get('unfamiliar_strict_deduped_candidate_count', 0)}",
                f"- unfamiliar_cross_artifact_deduped_candidate_count: {summary.get('unfamiliar_cross_artifact_deduped_candidate_count', 0)}",
                f"- scored_unfamiliar_record_count: {summary.get('scored_unfamiliar_record_count', 0)}",
                "",
                "## Distributions",
                f"- confidence_level_distribution: {json.dumps(summary.get('confidence_level_distribution', {}), ensure_ascii=False)}",
                f"- routing_decision_distribution: {json.dumps(summary.get('routing_decision_distribution', {}), ensure_ascii=False)}",
                f"- risk_flag_distribution: {json.dumps(summary.get('risk_flag_distribution', {}), ensure_ascii=False)}",
                f"- score_bucket_distribution: {json.dumps(summary.get('score_bucket_distribution', {}), ensure_ascii=False)}",
                "",
                "## Delivery Summary",
                f"- sidecar_trusted_suggestion_count: {summary.get('sidecar_trusted_suggestion_count', 0)}",
                f"- sidecar_review_required_suggestion_count: {summary.get('sidecar_review_required_suggestion_count', 0)}",
                f"- sidecar_needs_more_info_or_rejected_count: {summary.get('sidecar_needs_more_info_or_rejected_count', 0)}",
                f"- estimated_human_review_burden_count: {summary.get('estimated_human_review_burden_count', 0)}",
                f"- estimated_auto_trusted_ratio: {summary.get('estimated_auto_trusted_ratio', 0)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommendation",
            f"- recommended_next_step: {summary.get('recommended_next_step', '')}",
            "",
            "## Safety",
            f"- production_routing_modified: {summary.get('production_routing_modified', False)}",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330f: {summary.get('no_official_asset_modification_during_330f', False)}",
            "",
        ]
    )
    return "\n".join(lines)
