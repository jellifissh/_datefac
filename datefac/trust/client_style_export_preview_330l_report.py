from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "readme",
    "exec_summary",
    "trusted_suggestions",
    "review_required",
    "unit_review_sample",
    "source_provenance",
    "qa_caveats",
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
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def client_style_export_preview_330l_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Client Style Export Preview 330L",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            f"- delivery_readiness_judgment: {summary.get('delivery_readiness_judgment', '')}",
            "",
            "## Validation",
            f"- validated_330j2_delivery_refresh: {summary.get('validated_330j2_delivery_refresh', False)}",
            f"- preview_workbook_generated: {summary.get('preview_workbook_generated', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Preview Metrics",
            f"- source_pdf_unique_count: {summary.get('source_pdf_unique_count', 0)}",
            f"- prepared_candidate_row_count: {summary.get('prepared_candidate_row_count', 0)}",
            f"- strict_deduped_candidate_count: {summary.get('strict_deduped_candidate_count', 0)}",
            f"- unit_missing_count: {summary.get('unit_missing_count', 0)}",
            f"- unit_conflict_risk_count: {summary.get('unit_conflict_risk_count', 0)}",
            f"- trusted_sheet_row_count: {summary.get('trusted_sheet_row_count', 0)}",
            f"- review_required_sheet_row_count: {summary.get('review_required_sheet_row_count', 0)}",
            f"- unit_review_sheet_row_count: {summary.get('unit_review_sheet_row_count', 0)}",
            f"- source_provenance_sheet_row_count: {summary.get('source_provenance_sheet_row_count', 0)}",
            f"- qa_caveat_count: {summary.get('qa_caveat_count', 0)}",
            "",
            "## Wording",
            f"- recommended_next_step: {summary.get('recommended_next_step', '')}",
            "- wording_mode: conservative_demo_only",
            "",
            "## Safety",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330l: {summary.get('no_official_asset_modification_during_330l', False)}",
            "",
        ]
    )
