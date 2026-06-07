from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "source_attribution",
    "unit_fix_summary",
    "confidence_distribution",
    "risk_flag_updates",
    "prepared_manifest",
    "fixed_candidate_rows",
    "rerun_330f_summary",
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


def source_attribution_unit_signal_fix_330i_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Source Attribution Unit Signal Fix 330I",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Validation",
            f"- validated_330h_full_benchmark: {summary.get('validated_330h_full_benchmark', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Counts",
            f"- input_candidate_row_count: {summary.get('input_candidate_row_count', 0)}",
            f"- output_candidate_row_count: {summary.get('output_candidate_row_count', 0)}",
            "",
            "## Source Attribution",
            f"- source_pdf_nonempty_count: {summary.get('source_pdf_nonempty_count', 0)}",
            f"- source_pdf_unique_count: {summary.get('source_pdf_unique_count', 0)}",
            f"- source_page_nonempty_count: {summary.get('source_page_nonempty_count', 0)}",
            f"- source_page_missing_count_after: {summary.get('source_page_missing_count_after', 0)}",
            f"- source_artifact_nonempty_count: {summary.get('source_artifact_nonempty_count', 0)}",
            f"- candidate_id_stability_check: {summary.get('candidate_id_stability_check', False)}",
            "",
            "## Unit Fix",
            f"- unit_missing_count_before: {summary.get('unit_missing_count_before', 0)}",
            f"- unit_missing_count_after: {summary.get('unit_missing_count_after', 0)}",
            f"- unit_filled_count: {summary.get('unit_filled_count', 0)}",
            f"- unit_inference_high_confidence_count: {summary.get('unit_inference_high_confidence_count', 0)}",
            f"- unit_inference_medium_confidence_count: {summary.get('unit_inference_medium_confidence_count', 0)}",
            f"- unit_inference_low_confidence_count: {summary.get('unit_inference_low_confidence_count', 0)}",
            f"- unit_unknown_risk_added_count: {summary.get('unit_unknown_risk_added_count', 0)}",
            "",
            "## Prepared Output",
            f"- prepared_output_dir: {summary.get('prepared_output_dir', '')}",
            f"- prepared_output_dir_for_330f: {summary.get('prepared_output_dir_for_330f', '')}",
            "",
            "## 330F Rerun",
            f"- reran_330f: {summary.get('reran_330f', False)}",
            f"- 330f_unfamiliar_source_status: {summary.get('330f_unfamiliar_source_status', '')}",
            f"- 330f_scored_unfamiliar_record_count: {summary.get('330f_scored_unfamiliar_record_count', 0)}",
            f"- 330f_decision: {summary.get('330f_decision', '')}",
            "",
            "## Safety",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330i: {summary.get('no_official_asset_modification_during_330i', False)}",
            "",
        ]
    )
