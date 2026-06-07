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
    "review_queue",
    "upstream_context",
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


def human_unit_review_330k2_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Human Unit Review 330K2",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            f"- project_status: {summary.get('project_status', '')}",
            "",
            "## Validation",
            f"- validated_330l_export_preview: {summary.get('validated_330l_export_preview', False)}",
            f"- validated_331a_demo_packaging: {summary.get('validated_331a_demo_packaging', False)}",
            f"- review_template_workbook_generated: {summary.get('review_template_workbook_generated', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Review Package",
            f"- review_template_workbook_path: {summary.get('review_template_workbook_path', '')}",
            f"- packaged_unit_review_row_count: {summary.get('packaged_unit_review_row_count', 0)}",
            f"- source_page_missing_count: {summary.get('source_page_missing_count', 0)}",
            f"- unit_missing_count: {summary.get('unit_missing_count', 0)}",
            f"- unit_conflict_risk_count: {summary.get('unit_conflict_risk_count', 0)}",
            "",
            "## Safety",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330k2: {summary.get('no_official_asset_modification_during_330k2', False)}",
            f"- protected_dirty_files_staged: {json.dumps(summary.get('protected_dirty_files_staged', []), ensure_ascii=False)}",
            "",
        ]
    )
