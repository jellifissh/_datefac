from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


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


def executive_summary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 345C5 Reviewed Alias Decision Ingestion",
            "",
            "## Input",
            f"- input_345c4_package_dir: {summary.get('input_345c4_package_dir', '')}",
            f"- reviewed_alias_workbook: {summary.get('reviewed_alias_workbook', '')}",
            f"- reviewed_row_count: {summary.get('reviewed_row_count', 0)}",
            "",
            "## Decision Distribution",
            f"- approved_existing_mapping_count: {summary.get('approved_existing_mapping_count', 0)}",
            f"- approved_new_standard_count: {summary.get('approved_new_standard_count', 0)}",
            f"- rejected_alias_count: {summary.get('rejected_alias_count', 0)}",
            f"- needs_more_context_count: {summary.get('needs_more_context_count', 0)}",
            f"- deferred_count: {summary.get('deferred_count', 0)}",
            "",
            "## Validation",
            f"- validation_issue_count: {summary.get('validation_issue_count', 0)}",
            f"- apply_simulation_eligible_count: {summary.get('apply_simulation_eligible_count', 0)}",
            "",
            "## Boundary",
            "- 345C5 only ingests reviewed workbook decisions into a no-write-back package.",
            "- No normalization rules were updated.",
            "- No official alias assets were updated.",
            f"- formal_client_export_allowed = {summary.get('formal_client_export_allowed', False)}",
            f"- client_ready = {summary.get('client_ready', False)}",
            f"- production_ready = {summary.get('production_ready', False)}",
            "",
            "## Next",
            "- 345C6 Reviewed Alias Apply Simulation",
            "- 345D Full Structured Demo Export Package only after simulation impact is measured",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345C5 Artifact Index",
        "",
        "| Artifact | Path | Use |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def next_plan_markdown() -> str:
    return "\n".join(
        [
            "# 345C5 Next Plan",
            "",
            "- 345C6 Reviewed Alias Apply Simulation",
            "- 345D Full Structured Demo Export Package only after simulation impact is measured",
            "",
            "Boundary reminder:",
            "- 345C5 does not modify normalization rules.",
            "- 345C5 does not modify official alias assets.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
