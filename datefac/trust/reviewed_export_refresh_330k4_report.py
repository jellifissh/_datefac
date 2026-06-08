from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


WORKBOOK_SHEET_ORDER = [
    "00_README",
    "01_REVIEWED_TRUSTED_PREVIEW",
    "02_REMAINING_REVIEW_REQUIRED",
    "03_HUMAN_REJECTED_BY_UNIT_REV",
    "04_APPLY_PLAN_TRACE",
    "05_QA_CONTEXT",
]


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


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name in WORKBOOK_SHEET_ORDER:
            sheets.get(sheet_name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )


def reviewed_export_refresh_330k4_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Reviewed Export Refresh 330K4",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Reviewed Preview Counts",
            f"- original_trusted_sheet_row_count: {summary.get('original_trusted_sheet_row_count', 0)}",
            f"- reviewed_unit_confirmed_count: {summary.get('reviewed_unit_confirmed_count', 0)}",
            f"- human_rejected_row_count: {summary.get('human_rejected_row_count', 0)}",
            f"- remaining_review_required_after_unit_review_count: {summary.get('remaining_review_required_after_unit_review_count', 0)}",
            f"- reviewed_trusted_preview_row_count: {summary.get('reviewed_trusted_preview_row_count', 0)}",
            "",
            "## Apply Plan",
            f"- apply_plan_row_count: {summary.get('apply_plan_row_count', 0)}",
            f"- confirm_unit_count: {summary.get('confirm_unit_count', 0)}",
            f"- reject_unit_count: {summary.get('reject_unit_count', 0)}",
            f"- needs_more_context_count: {summary.get('needs_more_context_count', 0)}",
            f"- keep_unit_unknown_count: {summary.get('keep_unit_unknown_count', 0)}",
            "",
            "## Safety",
            f"- duplicate_confirmed_candidate_overlap_count: {summary.get('duplicate_confirmed_candidate_overlap_count', 0)}",
            f"- no_official_asset_modification_during_330k4: {summary.get('no_official_asset_modification_during_330k4', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
        ]
    )
