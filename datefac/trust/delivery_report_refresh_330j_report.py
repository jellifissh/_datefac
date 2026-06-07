from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "refreshed_metrics",
    "comparison",
    "risk_flag_delta",
    "distribution",
    "rerun_330f_summary",
    "fixed_manifest",
    "fixed_candidate_rows",
    "official_asset_proof",
    "known_limitations",
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


def delivery_report_refresh_330j_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Delivery Report Refresh 330J",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            f"- delivery_readiness_judgment: {summary.get('delivery_readiness_judgment', '')}",
            "",
            "## Validation",
            f"- validated_330i_unit_fix: {summary.get('validated_330i_unit_fix', False)}",
            f"- reran_330f: {summary.get('reran_330f', False)}",
            f"- 330f_unfamiliar_source_status: {summary.get('330f_unfamiliar_source_status', '')}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Refreshed Metrics",
            f"- processed_pdf_count: {summary.get('processed_pdf_count', 0)}",
            f"- source_pdf_unique_count: {summary.get('source_pdf_unique_count', 0)}",
            f"- prepared_candidate_row_count: {summary.get('prepared_candidate_row_count', 0)}",
            f"- artifact_row_count: {summary.get('artifact_row_count', 0)}",
            f"- strict_deduped_candidate_count: {summary.get('strict_deduped_candidate_count', 0)}",
            f"- sidecar_trusted_suggestion_count: {summary.get('sidecar_trusted_suggestion_count', 0)}",
            f"- sidecar_review_required_suggestion_count: {summary.get('sidecar_review_required_suggestion_count', 0)}",
            f"- sidecar_auto_trusted_ratio_artifact_row: {summary.get('sidecar_auto_trusted_ratio_artifact_row', 0)}",
            f"- sidecar_auto_trusted_ratio_strict_deduped: {summary.get('sidecar_auto_trusted_ratio_strict_deduped', 0)}",
            f"- unit_missing_count: {summary.get('unit_missing_count', 0)}",
            f"- source_page_missing_count: {summary.get('source_page_missing_count', 0)}",
            f"- unit_unknown_risk_count: {summary.get('unit_unknown_risk_count', 0)}",
            f"- unit_conflict_risk_count: {summary.get('unit_conflict_risk_count', 0)}",
            "",
            "## Comparison",
            f"- unit_missing_before_330i: {summary.get('unit_missing_before_330i', 0)}",
            f"- unit_missing_after_330i: {summary.get('unit_missing_after_330i', 0)}",
            f"- unit_filled_count: {summary.get('unit_filled_count', 0)}",
            f"- source_page_missing_before_330h: {summary.get('source_page_missing_before_330h', 0)}",
            f"- source_page_missing_after_330i: {summary.get('source_page_missing_after_330i', 0)}",
            f"- trusted_suggestion_delta: {summary.get('trusted_suggestion_delta', 0)}",
            f"- review_required_delta: {summary.get('review_required_delta', 0)}",
            "",
            "## Distributions",
            f"- confidence_level_distribution: {json.dumps(summary.get('confidence_level_distribution', {}), ensure_ascii=False)}",
            f"- routing_decision_distribution: {json.dumps(summary.get('routing_decision_distribution', {}), ensure_ascii=False)}",
            f"- risk_flag_distribution: {json.dumps(summary.get('risk_flag_distribution', {}), ensure_ascii=False)}",
            "",
            "## Recommendation",
            f"- recommended_next_step: {summary.get('recommended_next_step', '')}",
            f"- recommended_next_step_secondary: {summary.get('recommended_next_step_secondary', '')}",
            "",
            "## Safety",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330j: {summary.get('no_official_asset_modification_during_330j', False)}",
            "",
        ]
    )
