from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "source_artifacts",
    "scored_records",
    "confidence_distribution",
    "routing_distribution",
    "risk_distribution",
    "score_bucket_distribution",
    "existing_status_distribution",
    "sidecar_vs_existing_status",
    "calibration_summary",
    "official_asset_proof",
    "qa_summary",
    "qa_checks",
    "known_limitations",
]

CALIBRATION_SHEET_ORDER = [
    "summary",
    "potential_false_trusted",
    "trusted_with_warning",
    "trusted_with_low_evidence",
    "review_required_high_score",
    "rejected_or_needs_more_info_high",
    "missing_evidence",
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


def cached_candidate_benchmark_330c_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Cached Candidate Trust Scoring Benchmark 330C",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Readiness",
            f"- validated_330b_scoring: {summary.get('validated_330b_scoring', False)}",
            f"- candidate_source_dir_count: {summary.get('candidate_source_dir_count', 0)}",
            f"- candidate_source_status: {summary.get('candidate_source_status', '')}",
            "",
            "## Record Counts",
            f"- cached_candidate_count: {summary.get('cached_candidate_count', 0)}",
            f"- fallback_fixture_count: {summary.get('fallback_fixture_count', 0)}",
            f"- scored_record_count: {summary.get('scored_record_count', 0)}",
            "",
            "## Calibration",
            f"- potential_false_trusted_count: {summary.get('potential_false_trusted_count', 0)}",
            f"- trusted_with_warning_risk_count: {summary.get('trusted_with_warning_risk_count', 0)}",
            f"- trusted_with_low_evidence_count: {summary.get('trusted_with_low_evidence_count', 0)}",
            f"- review_required_high_score_count: {summary.get('review_required_high_score_count', 0)}",
            f"- rejected_or_needs_more_info_high_score_count: {summary.get('rejected_or_needs_more_info_high_score_count', 0)}",
            f"- missing_evidence_count: {summary.get('missing_evidence_count', 0)}",
            f"- calibration_sample_count: {summary.get('calibration_sample_count', 0)}",
            "",
            "## Safety",
            f"- no_official_asset_modification_during_330c: {summary.get('no_official_asset_modification_during_330c', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Notes",
            "- 330C is a sidecar benchmark over cached artifacts only.",
            "- Sidecar scores do not overwrite existing trusted/review/rejected routing.",
            "- Fallback fixtures are used only when no compatible cached candidate-level artifacts can be loaded.",
            "",
        ]
    )
