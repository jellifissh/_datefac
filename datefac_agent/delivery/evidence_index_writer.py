"""Evidence index writing for the 348A pilot."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from datefac_agent.schemas.audit_models import AuditRowResult


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def write_evidence_index(output_path: str | Path, row_results: list[AuditRowResult]) -> None:
    """Write row-level evidence metadata to JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = []
    for result in row_results:
        payload.append(
            {
                "sheet_name": result.row.sheet_name,
                "row_index": result.row.row_index,
                "metric_name": result.row.metric_name,
                "decision": result.decision.decision if result.decision else "",
                "evidence_level": result.evidence_level,
                "row_type": result.row_type,
                "explicit_evidence_ref": result.row.explicit_evidence_ref,
                "evidence_refs": [
                    {
                        "source_type": ref.source_type,
                        "source_id": ref.source_id,
                        "page_number": ref.page_number,
                        "locator": ref.locator,
                        "is_explicit": ref.is_explicit,
                    }
                    for ref in result.evidence_refs
                ],
                "raw_values": {key: _json_safe(value) for key, value in result.row.raw_values.items()},
            }
        )
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv_rows(output_path: str | Path, rows: list[dict[str, Any]]) -> None:
    """Write flat CSV rows."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8", newline="")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
