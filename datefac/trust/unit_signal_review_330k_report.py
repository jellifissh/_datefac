from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "status_distribution",
    "category_distribution",
    "review_burden",
    "review_candidates",
    "reviewed_rows",
    "fixed_manifest",
    "optional_fixed_manifest",
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


def unit_signal_review_330k_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Unit Signal Review 330K",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Validation",
            f"- validated_330j_delivery_refresh: {summary.get('validated_330j_delivery_refresh', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Input Counts",
            f"- input_candidate_row_count: {summary.get('input_candidate_row_count', 0)}",
            f"- unit_missing_count_input: {summary.get('unit_missing_count_input', 0)}",
            f"- unit_conflict_count_input: {summary.get('unit_conflict_count_input', 0)}",
            "",
            "## Review Outcome",
            f"- additional_safe_unit_fix_count: {summary.get('additional_safe_unit_fix_count', 0)}",
            f"- unit_missing_count_after_330k: {summary.get('unit_missing_count_after_330k', 0)}",
            f"- review_sample_row_count: {summary.get('review_sample_row_count', 0)}",
            f"- human_review_workbook_generated: {summary.get('human_review_workbook_generated', False)}",
            f"- human_review_workbook_path: {summary.get('human_review_workbook_path', '')}",
            "",
            "## Review Burden",
            f"- unit_review_required_count: {summary.get('unit_review_required_count', 0)}",
            f"- unit_conflict_review_count: {summary.get('unit_conflict_review_count', 0)}",
            f"- unit_unknown_review_count: {summary.get('unit_unknown_review_count', 0)}",
            f"- high_confidence_with_unit_risk_count: {summary.get('high_confidence_with_unit_risk_count', 0)}",
            f"- pdfs_affected_by_unit_risk_count: {summary.get('pdfs_affected_by_unit_risk_count', 0)}",
            "",
            "## Recommendation",
            f"- recommended_next_step: {summary.get('recommended_next_step', '')}",
            f"- secondary_next_step: {summary.get('secondary_next_step', '')}",
            "",
            "## Safety",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330k: {summary.get('no_official_asset_modification_during_330k', False)}",
            "",
        ]
    )
