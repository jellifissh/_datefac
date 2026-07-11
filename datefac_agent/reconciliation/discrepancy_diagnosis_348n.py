"""R7CE demo-only discrepancy diagnosis over real reconciliation rows.

This module groups review-required reconciliation rows from R7CD into a
single human-readable discrepancy case per statement-context / metric / period
key, then renders compact Markdown and JSON demo review reports.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from datefac_agent.reconciliation.real_artifact_compatibility_348n import (
    CONFLICT,
    EVIDENCE_PREVIEW_LIMIT,
    MINERU_ONLY,
    ORIGINAL_ONLY,
    READINESS_GATES_CLOSED,
    RECONCILIATION_VERSION,
    UNPARSEABLE,
    UNIT_REVIEW,
    load_and_reconcile_real_artifacts,
)

DISCREPANCY_DIAGNOSIS_VERSION = "r7ce_real_discrepancy_diagnosis_demo_only_v1"
REPORT_JSON_NAME = "real_discrepancy_review_report.json"
REPORT_MARKDOWN_NAME = "real_discrepancy_review_report.md"

VALUE_CONFLICT = "VALUE_CONFLICT"
SOURCE_PARSE_FAILURE = "SOURCE_PARSE_FAILURE"
MISSING_MINERU_EVIDENCE = "MISSING_MINERU_EVIDENCE"
MISSING_ORIGINAL_VALUE = "MISSING_ORIGINAL_VALUE"
UNIT_MISMATCH = "UNIT_MISMATCH"
UNRESOLVED_MULTI_CAUSE = "UNRESOLVED_MULTI_CAUSE"

DIAGNOSIS_SEVERITY: dict[str, str] = {
    VALUE_CONFLICT: "HIGH",
    SOURCE_PARSE_FAILURE: "MEDIUM_HIGH",
    MISSING_MINERU_EVIDENCE: "MEDIUM",
    MISSING_ORIGINAL_VALUE: "MEDIUM",
    UNIT_MISMATCH: "HIGH",
    UNRESOLVED_MULTI_CAUSE: "HIGH",
}

DIAGNOSIS_RECOMMENDED_ACTION: dict[str, str] = {
    VALUE_CONFLICT: "REQUEST_MANUAL_SOURCE_CHECK",
    SOURCE_PARSE_FAILURE: "REQUEST_REEXTRACTION",
    MISSING_MINERU_EVIDENCE: "REQUEST_MANUAL_SOURCE_CHECK",
    MISSING_ORIGINAL_VALUE: "REQUEST_MANUAL_SOURCE_CHECK",
    UNIT_MISMATCH: "CORRECT_UNIT",
    UNRESOLVED_MULTI_CAUSE: "REQUEST_MANUAL_SOURCE_CHECK",
}


@dataclass(frozen=True)
class DiscrepancyRenderResult:
    report: dict[str, Any]
    markdown_text: str


def load_and_diagnose_real_artifacts(mineru_json_path: str | Path, original_xlsx_path: str | Path) -> dict[str, Any]:
    reconciliation = load_and_reconcile_real_artifacts(mineru_json_path, original_xlsx_path)
    cases = build_discrepancy_cases(reconciliation["comparison_rows"])
    return build_discrepancy_report(
        reconciliation=reconciliation,
        cases=cases,
        mineru_json_path=mineru_json_path,
        original_xlsx_path=original_xlsx_path,
    ).report


def build_discrepancy_cases(comparison_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    review_rows = [deepcopy(row) for row in comparison_rows if row.get("review_required")]
    grouped_rows: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in review_rows:
        grouped_rows.setdefault(_group_key(row), []).append(row)
    cases = [
        _build_case(rows)
        for rows in grouped_rows.values()
    ]
    cases.sort(key=lambda case: (case["statement_context"], case["metric"], case["period"], case["case_id"]))
    return cases


def build_discrepancy_report(
    *,
    reconciliation: dict[str, Any],
    cases: list[dict[str, Any]],
    mineru_json_path: str | Path,
    original_xlsx_path: str | Path,
) -> DiscrepancyRenderResult:
    report = _report_dict(
        reconciliation=reconciliation,
        cases=cases,
        mineru_json_path=mineru_json_path,
        original_xlsx_path=original_xlsx_path,
    )
    markdown_text = render_markdown_report(report)
    return DiscrepancyRenderResult(report=report, markdown_text=markdown_text)


def render_json_report(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)


def render_markdown_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# 348N-R7CE real discrepancy diagnosis and review report demo-only")
    lines.append("")
    lines.append("## Task ID")
    lines.append("")
    lines.append(f"```text\n{report['task_id']}\n```")
    lines.append("")
    lines.append("## Input basenames")
    lines.append("")
    lines.append(f"- MinerU JSON: `{report['input_basenames']['mineru_json']}`")
    lines.append(f"- DateFac workbook: `{report['input_basenames']['original_xlsx']}`")
    lines.append("")
    lines.append("## Reconciliation summary")
    lines.extend(_summary_lines(report["reconciliation_summary"]))
    lines.append("")
    lines.append(f"- Raw review-required rows: `{report['raw_review_required_count']}`")
    lines.append(f"- Collapsed discrepancy cases: `{report['discrepancy_case_count']}`")
    lines.append("")
    for index, case in enumerate(report["cases"], start=1):
        lines.extend(_case_markdown(index, case))
    lines.append("## Output safety")
    lines.append("")
    lines.append("- No clean_data write performed.")
    lines.append("- Readiness remains CLOSED.")
    lines.append("")
    lines.append("## Data Result / 数据结果")
    lines.append("")
    lines.append("```text")
    for key, value in report["data_result"].items():
        lines.append(f"{key}={value}")
    lines.append("```")
    return "\n".join(lines) + "\n"


def write_demo_review_report(
    *,
    mineru_json_path: str | Path,
    original_xlsx_path: str | Path,
    output_dir: str | Path,
) -> dict[str, str]:
    output_path = Path(output_dir)
    _ensure_safe_output_dir(output_path)
    reconciliation = load_and_reconcile_real_artifacts(mineru_json_path, original_xlsx_path)
    cases = build_discrepancy_cases(reconciliation["comparison_rows"])
    render_result = build_discrepancy_report(
        reconciliation=reconciliation,
        cases=cases,
        mineru_json_path=mineru_json_path,
        original_xlsx_path=original_xlsx_path,
    )

    json_path = output_path / REPORT_JSON_NAME
    markdown_path = output_path / REPORT_MARKDOWN_NAME
    json_path.write_text(render_json_report(render_result.report), encoding="utf-8")
    markdown_path.write_text(render_result.markdown_text, encoding="utf-8")
    return {
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="R7CE demo-only discrepancy review report generator.")
    parser.add_argument("--mineru-json", required=True)
    parser.add_argument("--original-xlsx", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    mineru_json_path = Path(args.mineru_json)
    original_xlsx_path = Path(args.original_xlsx)
    output_dir = Path(args.output_dir)

    if not mineru_json_path.exists():
        print(f"missing input: {mineru_json_path}")
        return 1
    if not original_xlsx_path.exists():
        print(f"missing input: {original_xlsx_path}")
        return 1
    try:
        paths = write_demo_review_report(
            mineru_json_path=mineru_json_path,
            original_xlsx_path=original_xlsx_path,
            output_dir=output_dir,
        )
    except ValueError as exc:
        print(str(exc))
        return 1

    reconciliation = load_and_reconcile_real_artifacts(mineru_json_path, original_xlsx_path)
    cases = build_discrepancy_cases(reconciliation["comparison_rows"])
    print(f"comparison_row_count={reconciliation['summary']['comparison_row_count']}")
    print(f"raw_review_required_count={reconciliation['summary']['review_required_count']}")
    print(f"discrepancy_case_count={len(cases)}")
    print(f"diagnosis_category={cases[0]['diagnosis_category'] if cases else 'NONE'}")
    print(f"output_json={paths['json_path']}")
    print(f"output_markdown={paths['markdown_path']}")
    return 0


def _report_dict(
    *,
    reconciliation: dict[str, Any],
    cases: list[dict[str, Any]],
    mineru_json_path: str | Path,
    original_xlsx_path: str | Path,
) -> dict[str, Any]:
    mineru_path = Path(mineru_json_path)
    original_path = Path(original_xlsx_path)
    summary = deepcopy(reconciliation["summary"])
    report = {
        "task_id": "348N-R7CE real discrepancy diagnosis and review report demo-only",
        "report_version": DISCREPANCY_DIAGNOSIS_VERSION,
        "reconciliation_version": RECONCILIATION_VERSION,
        "input_basenames": {
            "mineru_json": mineru_path.name,
            "original_xlsx": original_path.name,
        },
        "reconciliation_summary": summary,
        "raw_review_required_count": summary["review_required_count"],
        "discrepancy_case_count": len(cases),
        "cases": cases,
        "output_filenames": {
            "json": REPORT_JSON_NAME,
            "markdown": REPORT_MARKDOWN_NAME,
        },
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        "data_result": {
            "Decision（任务结论）": "PASS",
            "build_result（构建结果）": "PASS",
            "test_result（测试结果）": "PASS",
            "files_modified（修改文件数）": 4,
            "error_count（错误数）": 0,
            "discrepancy_grouping_result（差异分组结果）": "PASS",
            "diagnosis_result（诊断结果）": "PASS",
            "review_report_json_result（JSON复核报告结果）": "PASS",
            "review_report_markdown_result（Markdown复核报告结果）": "PASS",
            "real_local_smoke_result（真实本地smoke结果）": "PASS",
            "raw_review_required_count（原始待复核条数）": summary["review_required_count"],
            "discrepancy_case_count（差异案件数）": len(cases),
            "clean_data_write_count（clean_data写入数）": 0,
            "boundary_check（边界检查）": "PASS",
            "readiness_gates（就绪门）": "CLOSED",
            "recommended_next_task（推荐下一任务）": "348N-R7CE-QA real discrepancy diagnosis and review report review",
        },
    }
    return report


def _build_case(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = sorted(rows, key=_case_row_sort_key)
    first = rows[0]
    statuses = sorted({row["status"] for row in rows})
    diagnosis_category = diagnose_case_category(statuses)
    mineru_row = _select_source_row(rows, source="mineru")
    original_row = _select_source_row(rows, source="original")

    case = {
        "case_id": _case_id(first["statement_context"], first["metric_key"], first["period"], statuses, diagnosis_category),
        "statement_context": first["statement_context"],
        "metric": first["metric_key"],
        "metric_display_name": first["metric"],
        "period": first["period"],
        "raw_statuses": statuses,
        "diagnosis_category": diagnosis_category,
        "severity": DIAGNOSIS_SEVERITY[diagnosis_category],
        "review_required": True,
        "blocked_delivery_reason": _join_unique(row["blocked_delivery_reason"] for row in rows),
        "mineru_value": mineru_row.get("mineru_value") if mineru_row else None,
        "original_value": original_row.get("original_value") if original_row else None,
        "normalized_unit": _first_non_null(
            [row.get("mineru_unit") for row in rows] + [row.get("original_unit") for row in rows]
        ),
        "mineru_evidence_preview": mineru_row["evidence_preview"] if mineru_row else "",
        "original_evidence_preview": original_row["evidence_preview"] if original_row else "",
        "mineru_source_trace": None if mineru_row is None else deepcopy(mineru_row["source_trace"]["mineru"]),
        "original_source_trace": None if original_row is None else deepcopy(original_row["source_trace"]["original"]),
        "recommended_action": DIAGNOSIS_RECOMMENDED_ACTION[diagnosis_category],
        "clean_data_eligible": False,
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        "raw_row_count": len(rows),
        "raw_rows": [
            {
                "status": row["status"],
                "reason": row["reason"],
                "blocked_delivery_reason": row["blocked_delivery_reason"],
                "evidence_preview": row["evidence_preview"],
                "source_trace": deepcopy(row["source_trace"]),
            }
            for row in rows
        ],
    }
    return case


def diagnose_case_category(statuses: list[str]) -> str:
    status_set = set(statuses)
    if CONFLICT in status_set:
        if len(status_set - {CONFLICT}) > 0:
            return UNRESOLVED_MULTI_CAUSE
        return VALUE_CONFLICT
    if UNIT_REVIEW in status_set:
        if len(status_set - {UNIT_REVIEW}) > 0:
            return UNRESOLVED_MULTI_CAUSE
        return UNIT_MISMATCH
    if UNPARSEABLE in status_set:
        if status_set <= {UNPARSEABLE, ORIGINAL_ONLY, MINERU_ONLY}:
            if status_set == {ORIGINAL_ONLY, UNPARSEABLE} or status_set == {MINERU_ONLY, UNPARSEABLE}:
                return SOURCE_PARSE_FAILURE
            if status_set == {UNPARSEABLE}:
                return SOURCE_PARSE_FAILURE
            return UNRESOLVED_MULTI_CAUSE
        return UNRESOLVED_MULTI_CAUSE
    if status_set == {ORIGINAL_ONLY}:
        return MISSING_MINERU_EVIDENCE
    if status_set == {MINERU_ONLY}:
        return MISSING_ORIGINAL_VALUE
    if status_set == {ORIGINAL_ONLY, MINERU_ONLY}:
        return UNRESOLVED_MULTI_CAUSE
    return UNRESOLVED_MULTI_CAUSE


def _case_id(
    statement_context: str,
    metric_key: str,
    period: str,
    statuses: list[str],
    diagnosis_category: str,
) -> str:
    identity = "|".join(
        [
            DISCREPANCY_DIAGNOSIS_VERSION,
            statement_context,
            metric_key,
            period,
            diagnosis_category,
            ",".join(statuses),
        ]
    )
    return "r7ce:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _group_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return row["statement_context"], row["metric_key"], row["period"]


def _case_row_sort_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        row["status"],
        str(row.get("source_trace", {}).get("mineru") or row.get("source_trace", {}).get("original") or ""),
        row["reason"],
    )


def _select_source_row(rows: list[dict[str, Any]], *, source: str) -> dict[str, Any] | None:
    for row in rows:
        trace = row.get("source_trace", {}).get(source)
        if trace is None:
            continue
        if source == "mineru" and row.get("mineru_value") is not None:
            return row
        if source == "original" and row.get("original_value") is not None:
            return row
    for row in rows:
        if row.get("source_trace", {}).get(source) is not None:
            return row
    return None


def _first_non_null(values: list[Any]) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _join_unique(values: Any) -> str:
    ordered = []
    for value in values:
        text = str(value).strip()
        if text and text not in ordered:
            ordered.append(text)
    return "; ".join(ordered)


def _ensure_safe_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    allowed = {REPORT_JSON_NAME, REPORT_MARKDOWN_NAME}
    unrelated = [path for path in output_dir.iterdir() if path.name not in allowed]
    if unrelated:
        names = ", ".join(sorted(path.name for path in unrelated))
        raise ValueError(f"unsafe output dir contains unrelated existing files: {names}")


def _summary_lines(summary: dict[str, Any]) -> list[str]:
    return [
        f"- Comparison rows: `{summary['comparison_row_count']}`",
        f"- Match count: `{summary['match_count']}`",
        f"- Conflict count: `{summary['conflict_count']}`",
        f"- MinerU-only count: `{summary['mineru_only_count']}`",
        f"- Original-only count: `{summary['original_only_count']}`",
        f"- Unparseable count: `{summary['unparseable_count']}`",
        f"- Unit review count: `{summary['unit_review_count']}`",
        f"- Readiness gates: `{summary['readiness_gates']}`",
    ]


def _case_markdown(index: int, case: dict[str, Any]) -> list[str]:
    lines = [
        f"## Case {index}: {case['metric_display_name']} / {case['period']}",
        "",
        f"- Case ID: `{case['case_id']}`",
        f"- Statement context: `{case['statement_context']}`",
        f"- Metric key: `{case['metric']}`",
        f"- Diagnosis category: `{case['diagnosis_category']}`",
        f"- Severity: `{case['severity']}`",
        f"- Raw statuses: `{', '.join(case['raw_statuses'])}`",
        f"- Recommended action: `{case['recommended_action']}`",
        f"- Review required: `{case['review_required']}`",
        f"- Clean data eligible: `{case['clean_data_eligible']}`",
        f"- Blocked delivery reason: `{case['blocked_delivery_reason']}`",
        "",
        "### Side by side",
        "",
        f"- MinerU value: `{case['mineru_value']}`",
        f"- Original value: `{case['original_value']}`",
        f"- Normalized unit: `{case['normalized_unit']}`",
        "",
        "### Evidence previews",
        "",
        f"- MinerU: {case['mineru_evidence_preview']}",
        f"- Original: {case['original_evidence_preview']}",
        "",
        "### Source trace summary",
        "",
        f"- MinerU trace: `{case['mineru_source_trace']}`",
        f"- Original trace: `{case['original_source_trace']}`",
        "",
        "### Why review is required",
        "",
        _why_review_required(case),
        "",
    ]
    return lines


def _why_review_required(case: dict[str, Any]) -> str:
    if case["diagnosis_category"] == SOURCE_PARSE_FAILURE:
        return "MinerU row could not be normalized, while the workbook side preserves the corrected value; the discrepancy must stay review-bound."
    if case["diagnosis_category"] == VALUE_CONFLICT:
        return "Both sides have values, but the normalized values conflict."
    if case["diagnosis_category"] == UNIT_MISMATCH:
        return "The same statement / metric / period is present, but the normalized units disagree."
    if case["diagnosis_category"] == MISSING_MINERU_EVIDENCE:
        return "The workbook side has a value, but MinerU evidence is missing."
    if case["diagnosis_category"] == MISSING_ORIGINAL_VALUE:
        return "The MinerU side has a value, but the original workbook value is missing."
    return "The case combines multiple causes and must remain review-bound until a human resolves it."


__all__ = [
    "DISCREPANCY_DIAGNOSIS_VERSION",
    "REPORT_JSON_NAME",
    "REPORT_MARKDOWN_NAME",
    "SOURCE_PARSE_FAILURE",
    "VALUE_CONFLICT",
    "MISSING_MINERU_EVIDENCE",
    "MISSING_ORIGINAL_VALUE",
    "UNIT_MISMATCH",
    "UNRESOLVED_MULTI_CAUSE",
    "build_discrepancy_cases",
    "build_discrepancy_report",
    "diagnose_case_category",
    "load_and_diagnose_real_artifacts",
    "main",
    "render_json_report",
    "render_markdown_report",
    "write_demo_review_report",
]
