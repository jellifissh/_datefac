from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "unfamiliar_inputs",
    "cached_matches",
    "prepared_candidate_rows",
    "recommendation",
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


def unfamiliar_output_preparation_330f2_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Unfamiliar Output Preparation 330F2",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Status",
            f"- unfamiliar_output_preparation_status: {summary.get('unfamiliar_output_preparation_status', '')}",
            f"- discovered_unfamiliar_input_pdf_count: {summary.get('discovered_unfamiliar_input_pdf_count', 0)}",
            f"- matched_cached_output_count: {summary.get('matched_cached_output_count', 0)}",
            f"- prepared_candidate_row_count: {summary.get('prepared_candidate_row_count', 0)}",
            "",
            "## Prepared Output",
            f"- prepared_output_dir: {summary.get('prepared_output_dir', '')}",
            f"- alternative_prepared_output_dir: {summary.get('alternative_prepared_output_dir', '')}",
            f"- can_rerun_330f: {summary.get('can_rerun_330f', False)}",
            "",
            "## Recommendation",
            f"- recommended_next_action: {summary.get('recommended_next_action', '')}",
            "",
            "## Safety",
            f"- production_routing_modified: {summary.get('production_routing_modified', False)}",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330f2: {summary.get('no_official_asset_modification_during_330f2', False)}",
            "",
        ]
    )
