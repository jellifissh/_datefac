from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "coverage",
    "comparison",
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


def deduped_candidate_benchmark_330e_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Deduped Candidate Trust Benchmark 330E",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## 330D Validation",
            f"- validated_330d_calibration: {summary.get('validated_330d_calibration', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Benchmark Units",
            "- artifact_row",
            "- strict_deduped_view",
            "- cross_artifact_deduped_view",
            "",
            "## Counts",
            f"- artifact_row_count: {summary.get('artifact_row_count', 0)}",
            f"- strict_deduped_candidate_count: {summary.get('strict_deduped_candidate_count', 0)}",
            f"- cross_artifact_deduped_candidate_count: {summary.get('cross_artifact_deduped_candidate_count', 0)}",
            f"- strict_duplicate_count: {summary.get('strict_duplicate_count', 0)}",
            f"- cross_artifact_duplicate_count: {summary.get('cross_artifact_duplicate_count', 0)}",
            "",
            "## Coverage",
            f"- source_candidate_id_coverage_count: {summary.get('source_candidate_id_coverage_count', 0)}",
            f"- source_candidate_id_coverage_rate: {summary.get('source_candidate_id_coverage_rate', 0)}",
            f"- candidate_id_coverage_count: {summary.get('candidate_id_coverage_count', 0)}",
            f"- candidate_id_coverage_rate: {summary.get('candidate_id_coverage_rate', 0)}",
            f"- content_fingerprint_coverage_rate: {summary.get('content_fingerprint_coverage_rate', 0)}",
            f"- dedup_reliability_level: {summary.get('dedup_reliability_level', '')}",
            "",
            "## Artifact vs Strict/Cross Deltas",
            f"- strict_deltas_vs_artifact_row: {json.dumps(summary.get('strict_deltas_vs_artifact_row', {}), ensure_ascii=False)}",
            f"- cross_artifact_deltas_vs_artifact_row: {json.dumps(summary.get('cross_artifact_deltas_vs_artifact_row', {}), ensure_ascii=False)}",
            "",
            "## Recommendation",
            f"- policy_calibration_safe_to_continue: {summary.get('policy_calibration_safe_to_continue', False)}",
            f"- recommended_next_step: {summary.get('recommended_next_step', '')}",
            "",
            "## Safety",
            f"- production_routing_modified: {summary.get('production_routing_modified', False)}",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330e: {summary.get('no_official_asset_modification_during_330e', False)}",
            "",
            "## Residual Risks",
            "- Cross-artifact dedupe is still fingerprint-based because source_candidate_id coverage is absent.",
            "- 330E remains sidecar-only and does not override existing trusted/review routing.",
            "",
        ]
    )
