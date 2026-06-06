from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "delivery_metrics",
    "distribution",
    "limitations",
    "prepared_manifest",
    "prepared_candidate_rows",
    "official_asset_proof",
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
            sheets.get(name, pd.DataFrame()).to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def end_to_end_delivery_quality_report_330g_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# End-to-End Delivery Quality Report 330G",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            f"- delivery_readiness_judgment: {summary.get('delivery_readiness_judgment', '')}",
            "",
            "## Validation",
            f"- validated_330f4_smoke_export: {summary.get('validated_330f4_smoke_export', False)}",
            f"- validated_330f_unfamiliar_benchmark: {summary.get('validated_330f_unfamiliar_benchmark', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Counts",
            f"- processed_pdf_count: {summary.get('processed_pdf_count', 0)}",
            f"- prepared_candidate_row_count: {summary.get('prepared_candidate_row_count', 0)}",
            f"- artifact_row_count: {summary.get('artifact_row_count', 0)}",
            f"- strict_deduped_candidate_count: {summary.get('strict_deduped_candidate_count', 0)}",
            f"- artifact_duplication_factor: {summary.get('artifact_duplication_factor', 0)}",
            "",
            "## Sidecar Routing",
            f"- sidecar_trusted_suggestion_count: {summary.get('sidecar_trusted_suggestion_count', 0)}",
            f"- sidecar_review_required_suggestion_count: {summary.get('sidecar_review_required_suggestion_count', 0)}",
            f"- sidecar_auto_trusted_ratio_artifact_row: {summary.get('sidecar_auto_trusted_ratio_artifact_row', 0)}",
            f"- sidecar_auto_trusted_ratio_strict_deduped: {json.dumps(summary.get('sidecar_auto_trusted_ratio_strict_deduped'), ensure_ascii=False)}",
            "",
            "## Data Gaps",
            f"- unit_missing_count: {summary.get('unit_missing_count', 0)}",
            f"- source_page_missing_count: {summary.get('source_page_missing_count', 0)}",
            "",
            "## Distributions",
            f"- confidence_level_distribution: {json.dumps(summary.get('confidence_level_distribution', {}), ensure_ascii=False)}",
            f"- routing_decision_distribution: {json.dumps(summary.get('routing_decision_distribution', {}), ensure_ascii=False)}",
            f"- risk_flag_distribution: {json.dumps(summary.get('risk_flag_distribution', {}), ensure_ascii=False)}",
            "",
            "## Limitations",
            f"- smoke_limitations: {json.dumps(summary.get('smoke_limitations', []), ensure_ascii=False)}",
            "",
            "## Recommendation",
            f"- recommended_next_step: {summary.get('recommended_next_step', '')}",
            f"- recommended_next_step_secondary: {summary.get('recommended_next_step_secondary', '')}",
            "",
            "## Safety",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330g: {summary.get('no_official_asset_modification_during_330g', False)}",
            "",
        ]
    )
