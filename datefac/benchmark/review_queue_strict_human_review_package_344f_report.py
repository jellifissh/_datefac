from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

from datefac.benchmark.review_queue_expanded_demo_audit_snapshot_344e_report import (
    write_excel,
)


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
            )


def report_review_rows_json(path: Path, rows: List[Dict[str, Any]]) -> None:
    write_json(path, rows)


def _md_bool(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def reviewer_checklist_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 344F Strict Human Review Checklist",
            "",
            "1. This package is for strict human review only.",
            "2. The 29 rows come from:",
            "   - 10 rows from the 343O prior demo trusted arc.",
            "   - 19 rows from the 344A-344D source-check resolved backlog.",
            "3. 344F does not mean the package is ready for formal client delivery.",
            "4. The reviewer must check each row for:",
            "   - metric name correctness",
            "   - value correctness",
            "   - unit correctness",
            "   - period correctness",
            "   - source evidence support",
            "   - correction reasonableness",
            "   - whether the row should be allowed into a later formal export candidate",
            "5. The reviewer should only fill or edit:",
            "   - strict_human_review_decision",
            "   - strict_human_reviewer",
            "   - strict_human_reviewed_at",
            "   - strict_human_review_notes",
            "6. The reviewer must not edit original evidence fields, metric fields, or source fields.",
            "7. 344G will ingest the completed human review result later.",
            "",
            "## Current Gate Boundary",
            f"- formal_client_export_allowed = {_md_bool(summary.get('formal_client_export_allowed'))}",
            f"- client_ready = {_md_bool(summary.get('client_ready'))}",
            f"- production_ready = {_md_bool(summary.get('production_ready'))}",
            f"- global_strict_human_review_completed = {_md_bool(summary.get('global_strict_human_review_completed'))}",
        ]
    )


def executive_summary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 344F Strict Human Review Package Executive Summary",
            "",
            f"- decision: {summary.get('decision', '')}",
            f"- input_344e_dir: {summary.get('input_344e_dir', '')}",
            f"- output_dir: {summary.get('output_directory', '')}",
            f"- strict_review_row_count: {summary.get('strict_review_row_count', 0)}",
            f"- source_split: prior_demo_trusted_row_count = {summary.get('prior_demo_trusted_row_count', 0)}, source_check_trusted_row_count = {summary.get('source_check_trusted_row_count', 0)}",
            f"- source_check_result_split: source_check_confirmed_row_count = {summary.get('source_check_confirmed_row_count', 0)}, corrected_row_count = {summary.get('corrected_row_count', 0)}",
            "",
            "## Gate Status",
            f"- formal_client_export_allowed = {_md_bool(summary.get('formal_client_export_allowed'))}",
            f"- client_ready = {_md_bool(summary.get('client_ready'))}",
            f"- production_ready = {_md_bool(summary.get('production_ready'))}",
            f"- global_strict_human_review_completed = {_md_bool(summary.get('global_strict_human_review_completed'))}",
            "",
            "## Recommended Next Steps",
            "- 344G ingest strict human review result.",
            "- 344H strict reviewed final gate snapshot.",
        ]
    )


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 344F Artifact Index",
        "",
        "| Artifact | Path | Use |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def build_dataframe(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    return frame.astype(object).where(pd.notna(frame), "")


__all__ = [
    "artifact_index_markdown",
    "build_dataframe",
    "executive_summary_markdown",
    "report_review_rows_json",
    "reviewer_checklist_markdown",
    "write_csv",
    "write_excel",
    "write_json",
]
