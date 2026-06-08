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
    "apply_plan",
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


def human_unit_review_apply_simulation_330k3_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Human Unit Review Apply Simulation 330K3",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Reviewed Counts",
            f"- reviewed_row_count: {summary.get('reviewed_row_count', 0)}",
            f"- confirm_unit_count: {summary.get('confirm_unit_count', 0)}",
            f"- reject_unit_count: {summary.get('reject_unit_count', 0)}",
            f"- needs_more_context_count: {summary.get('needs_more_context_count', 0)}",
            f"- keep_unit_unknown_count: {summary.get('keep_unit_unknown_count', 0)}",
            f"- apply_plan_row_count: {summary.get('apply_plan_row_count', 0)}",
            "",
            "## Upstream Constraints",
            f"- source_page_missing_count: {summary.get('source_page_missing_count', 0)}",
            f"- unit_missing_count: {summary.get('unit_missing_count', 0)}",
            f"- unit_conflict_risk_count: {summary.get('unit_conflict_risk_count', 0)}",
            "",
            "## Safety",
            f"- no_official_asset_modification_during_330k3: {summary.get('no_official_asset_modification_during_330k3', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
        ]
    )
