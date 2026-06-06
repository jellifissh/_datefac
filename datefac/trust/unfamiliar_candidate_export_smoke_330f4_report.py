from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "scan_inventory",
    "prepared_candidate_rows",
    "missing_field_counts",
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


def unfamiliar_candidate_export_smoke_330f4_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Unfamiliar Candidate Export Smoke 330F4",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Selection",
            f"- selected_pdf_count: {summary.get('selected_pdf_count', 0)}",
            f"- selected_pdfs: {json.dumps(summary.get('selected_pdfs', []), ensure_ascii=False)}",
            "",
            "## Output",
            f"- processed_pdf_count: {summary.get('processed_pdf_count', 0)}",
            f"- prepared_candidate_row_count: {summary.get('prepared_candidate_row_count', 0)}",
            f"- extraction_export_approach_used: {summary.get('extraction_export_approach_used', '')}",
            f"- can_rerun_330f: {summary.get('can_rerun_330f', False)}",
            "",
            "## Missing Fields",
            f"- missing_field_counts: {json.dumps(summary.get('missing_field_counts', {}), ensure_ascii=False)}",
            "",
            "## Safety",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330f4: {summary.get('no_official_asset_modification_during_330f4', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
        ]
    )
