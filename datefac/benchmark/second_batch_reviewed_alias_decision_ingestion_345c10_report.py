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
            "# 345C10 Second Batch Reviewed Alias Decision Ingestion",
            "",
            "## Input",
            f"- input_345c9_package_dir: {summary.get('input_345c9_package_dir', '')}",
            f"- reviewed_blind_spot_workbook: {summary.get('reviewed_blind_spot_workbook', '')}",
            f"- input_345c9_decision: {summary.get('input_345c9_decision', '')}",
            f"- reviewed_row_count: {summary.get('reviewed_row_count', 0)}",
            "",
            "## Decision Distribution",
            f"- approved_existing_mapping_count: {summary.get('approved_existing_mapping_count', 0)}",
            f"- approved_new_standard_count: {summary.get('approved_new_standard_count', 0)}",
            f"- rejected_too_generic_count: {summary.get('rejected_too_generic_count', 0)}",
            f"- needs_source_context_count: {summary.get('needs_source_context_count', 0)}",
            f"- deferred_count: {summary.get('deferred_count', 0)}",
            f"- missing_decision_count: {summary.get('missing_decision_count', 0)}",
            f"- invalid_decision_count: {summary.get('invalid_decision_count', 0)}",
            "",
            "## Validation",
            f"- validation_issue_count: {summary.get('validation_issue_count', 0)}",
            f"- apply_simulation_eligible_count: {summary.get('apply_simulation_eligible_count', 0)}",
            f"- needs_alias_family_expansion_count: {summary.get('needs_alias_family_expansion_count', 0)}",
            f"- source_context_boolean_count: {summary.get('source_context_boolean_count', 0)}",
            "",
            "## Boundary",
            "- 345C10 only ingests second-batch reviewed workbook decisions into a no-write-back package.",
            "- No normalization rules were updated.",
            "- No official alias assets were updated.",
            f"- formal_client_export_allowed = {summary.get('formal_client_export_allowed', False)}",
            f"- client_ready = {summary.get('client_ready', False)}",
            f"- production_ready = {summary.get('production_ready', False)}",
            "",
            "## Next",
            "- 345C11 Second Batch Alias Apply Simulation",
            "- Then explicitly decide whether alias governance stops before returning to 345D Full Structured Demo Export Package",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )


def artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345C10 Artifact Index",
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
            "# 345C10 Next Plan",
            "",
            "- 345C11 Second Batch Alias Apply Simulation",
            "- After second-batch simulation, decide explicitly whether alias governance stops before returning to 345D Full Structured Demo Export Package",
            "",
            "Boundary reminder:",
            "- 345C10 does not modify normalization rules.",
            "- 345C10 does not modify official alias assets.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )

