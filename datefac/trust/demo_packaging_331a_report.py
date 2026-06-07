from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "milestone_summary",
    "docs_manifest",
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


def demo_packaging_331a_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Demo Packaging 331A",
            "",
            "## Project Status",
            f"- project_status: {summary.get('project_status', '')}",
            f"- production_ready: {summary.get('production_ready', False)}",
            f"- client_ready: {summary.get('client_ready', False)}",
            "",
            "## Validation",
            f"- validated_330l_export_preview: {summary.get('validated_330l_export_preview', False)}",
            f"- preview_workbook_path: {summary.get('preview_workbook_path', '')}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Demo Metrics",
            f"- prepared_candidate_row_count: {summary.get('prepared_candidate_row_count', 0)}",
            f"- trusted_sheet_row_count: {summary.get('trusted_sheet_row_count', 0)}",
            f"- review_required_sheet_row_count: {summary.get('review_required_sheet_row_count', 0)}",
            f"- unit_review_sheet_row_count: {summary.get('unit_review_sheet_row_count', 0)}",
            "",
            "## Generated Artifacts",
            f"- project_brief_generated: {summary.get('project_brief_generated', False)}",
            f"- resume_bullets_generated: {summary.get('resume_bullets_generated', False)}",
            f"- github_readme_section_generated: {summary.get('github_readme_section_generated', False)}",
            f"- demo_script_generated: {summary.get('demo_script_generated', False)}",
            f"- generated_demo_artifacts: {json.dumps(summary.get('generated_demo_artifacts', {}), ensure_ascii=False)}",
            "",
            "## Safety",
            f"- no_official_asset_modification_during_331a: {summary.get('no_official_asset_modification_during_331a', False)}",
            f"- decision: {summary.get('decision', '')}",
            "",
        ]
    )
