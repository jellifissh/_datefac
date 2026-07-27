"""Deterministic grouping and compact rendering of discrepancy cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .normalization import bounded_preview, stable_hash
from .reconciliation import CONFLICT, LEFT_ONLY, RIGHT_ONLY, UNIT_REVIEW, UNPARSEABLE, comparison_summary


_DIAGNOSIS = {
    CONFLICT: ("VALUE_CONFLICT", "HIGH", "REQUEST_SOURCE_CHECK"),
    LEFT_ONLY: ("MISSING_RIGHT_RECORD", "MEDIUM", "CHECK_RIGHT_INPUT"),
    RIGHT_ONLY: ("MISSING_LEFT_RECORD", "MEDIUM", "CHECK_LEFT_INPUT"),
    UNPARSEABLE: ("PARSE_FAILURE", "MEDIUM_HIGH", "REPAIR_INPUT_FORMAT"),
    UNIT_REVIEW: ("UNIT_MISMATCH", "MEDIUM_HIGH", "CONFIRM_UNIT"),
}


def build_discrepancy_cases(comparison_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for source_row in comparison_rows:
        row = dict(source_row)
        if not row.get("review_required"):
            continue
        key = (str(row.get("context", "")), str(row.get("metric_key", "")), str(row.get("period", "")))
        grouped.setdefault(key, []).append(row)
    cases = [_build_case(key, rows) for key, rows in grouped.items()]
    return sorted(cases, key=lambda case: (case["context"], case["metric_key"], case["period"], case["case_id"]))


def build_discrepancy_report(
    comparison_rows: Iterable[Mapping[str, Any]],
    *,
    left_label: str = "left",
    right_label: str = "right",
) -> dict[str, Any]:
    rows = [dict(row) for row in comparison_rows]
    cases = build_discrepancy_cases(rows)
    return {
        "report_version": "1",
        "left_label": left_label,
        "right_label": right_label,
        "comparison_summary": comparison_summary(rows),
        "discrepancy_case_count": len(cases),
        "cases": cases,
    }


def render_json_report(report: Mapping[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_markdown_report(report: Mapping[str, Any]) -> str:
    lines = ["# Document reconciliation review report", ""]
    lines.extend(["## Summary", ""])
    for key, value in sorted(dict(report.get("comparison_summary", {})).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", f"- discrepancy_case_count: {report.get('discrepancy_case_count', 0)}", ""])
    for index, case in enumerate(report.get("cases", []), start=1):
        lines.extend(
            [
                f"## Case {index}: {case['metric_display_name']} {case['period']}",
                "",
                f"- case_id: `{case['case_id']}`",
                f"- context: {case['context']}",
                f"- statuses: {', '.join(case['statuses'])}",
                f"- diagnosis: {case['diagnosis_category']}",
                f"- severity: {case['severity']}",
                f"- recommended_action: {case['recommended_action']}",
                f"- evidence_preview: {case['evidence_preview']}",
                "",
            ]
        )
    return "\n".join(lines)


def write_review_report(comparison_rows: Iterable[Mapping[str, Any]], output_dir: str | Path) -> dict[str, str]:
    output_path = _safe_empty_output_dir(output_dir)
    report = build_discrepancy_report(comparison_rows)
    json_path = output_path / "discrepancy_report.json"
    markdown_path = output_path / "discrepancy_report.md"
    json_path.write_text(render_json_report(report), encoding="utf-8")
    markdown_path.write_text(render_markdown_report(report), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(markdown_path)}


def _build_case(key: tuple[str, str, str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (str(row.get("status", "")), str(row.get("reason", ""))))
    statuses = sorted({str(row.get("status", "")) for row in ordered})
    categories = [_DIAGNOSIS.get(status, ("UNRESOLVED", "MEDIUM", "REQUEST_SOURCE_CHECK")) for status in statuses]
    diagnosis = categories[0] if len(categories) == 1 else ("MULTIPLE_ISSUES", "HIGH", "REQUEST_SOURCE_CHECK")
    first = ordered[0]
    case_id = "case:" + stable_hash({"identity": key, "statuses": statuses, "diagnosis": diagnosis[0]})
    source_trace = {"left": [], "right": []}
    for row in ordered:
        trace = row.get("source_trace") if isinstance(row.get("source_trace"), Mapping) else {}
        for label in source_trace:
            value = trace.get(label)
            if isinstance(value, Mapping) and value:
                source_trace[label].append(dict(value))
    return {
        "case_id": case_id,
        "context": key[0],
        "metric_key": key[1],
        "metric_display_name": str(first.get("metric_display_name", key[1])),
        "period": key[2],
        "statuses": statuses,
        "diagnosis_category": diagnosis[0],
        "severity": diagnosis[1],
        "recommended_action": diagnosis[2],
        "left_value": _first_value(ordered, "left_value"),
        "right_value": _first_value(ordered, "right_value"),
        "left_unit": _first_value(ordered, "left_unit"),
        "right_unit": _first_value(ordered, "right_unit"),
        "evidence_preview": bounded_preview(" | ".join(str(row.get("evidence_preview", "")) for row in ordered if row.get("evidence_preview"))),
        "source_trace": source_trace,
        "reason": " | ".join(sorted({str(row.get("reason", "")) for row in ordered if row.get("reason")})),
        "review_required": True,
    }


def _first_value(rows: Iterable[Mapping[str, Any]], field: str) -> Any:
    for row in rows:
        value = row.get(field)
        if value not in {None, ""}:
            return value
    return None


def _safe_empty_output_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir)
    if path.exists() and not path.is_dir():
        raise ValueError(f"output path is not a directory: {path}")
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"output directory is not empty: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path
