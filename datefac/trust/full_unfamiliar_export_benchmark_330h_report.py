from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "full_pdf_list",
    "per_pdf_summary",
    "prepared_manifest",
    "prepared_candidate_rows",
    "missing_field_counts",
    "rerun_330f_summary",
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


def full_unfamiliar_export_benchmark_330h_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Full Unfamiliar Export Benchmark 330H",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Validation",
            f"- validated_330g_delivery_report: {summary.get('validated_330g_delivery_report', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Inventory",
            f"- unfamiliar_pdf_count: {summary.get('unfamiliar_pdf_count', 0)}",
            f"- unfamiliar_pdf_list: {json.dumps(summary.get('unfamiliar_pdf_list', []), ensure_ascii=False)}",
            "",
            "## Processing",
            f"- processed_pdf_count: {summary.get('processed_pdf_count', 0)}",
            f"- failed_pdf_count: {summary.get('failed_pdf_count', 0)}",
            f"- no_candidate_pdf_count: {summary.get('no_candidate_pdf_count', 0)}",
            f"- pdf_with_candidate_count: {summary.get('pdf_with_candidate_count', 0)}",
            "",
            "## Prepared Output",
            f"- prepared_output_dir: {summary.get('prepared_output_dir', '')}",
            f"- prepared_candidate_row_count: {summary.get('prepared_candidate_row_count', 0)}",
            f"- source_pdf_preserved: {summary.get('source_pdf_preserved', False)}",
            f"- missing_required_field_count_by_field: {json.dumps(summary.get('missing_required_field_count_by_field', {}), ensure_ascii=False)}",
            "",
            "## 330F Rerun",
            f"- reran_330f: {summary.get('reran_330f', False)}",
            f"- 330f_unfamiliar_source_status: {summary.get('330f_unfamiliar_source_status', '')}",
            f"- 330f_scored_unfamiliar_record_count: {summary.get('330f_scored_unfamiliar_record_count', 0)}",
            f"- 330f_decision: {summary.get('330f_decision', '')}",
            "",
            "## Recommendation",
            f"- recommended_next_step: {summary.get('recommended_next_step', '')}",
            "",
            "## Safety",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330h: {summary.get('no_official_asset_modification_during_330h', False)}",
            "",
        ]
    )
