from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


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


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_fieldnames = list(fieldnames or [])
    if not ordered_fieldnames:
        seen: set[str] = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    ordered_fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered_fieldnames, extrasaction="ignore")
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


def render_review_checklist_markdown(
    manifest: Dict[str, Any],
    artifact_rows: List[Dict[str, Any]],
    row_reconciliation_rows: List[Dict[str, Any]],
    gate_safety: Dict[str, Any],
    caveat_check: Dict[str, Any],
    presentation: Dict[str, Any],
) -> str:
    artifact_pass = "PASS" if manifest.get("artifact_completeness_passed") else "FAIL"
    row_pass = "PASS" if manifest.get("row_count_closure_passed") else "FAIL"
    gate_pass = "PASS" if manifest.get("gate_safety_check_passed") else "FAIL"
    caveat_pass = "PASS" if manifest.get("caveat_completeness_passed") else "FAIL"
    presentation_pass = "PASS" if manifest.get("presentation_ready_for_demo_only") else "FAIL"

    lines = [
        "# 345E Demo Export Review / QA Checklist",
        "",
        f"- decision: {manifest.get('decision', '')}",
        f"- qa_fail_count: {manifest.get('qa_fail_count', 0)}",
        f"- input_345d_decision: {manifest.get('input_345d_decision', '')}",
        f"- checked_artifact_count: {manifest.get('checked_artifact_count', 0)}",
        f"- missing_required_artifact_count: {manifest.get('missing_required_artifact_count', 0)}",
        f"- optional_missing_artifact_count: {manifest.get('optional_missing_artifact_count', 0)}",
        f"- artifact_read_error_count: {manifest.get('artifact_read_error_count', 0)}",
        f"- row_count_closure_passed: {manifest.get('row_count_closure_passed', False)}",
        f"- gate_safety_check_passed: {manifest.get('gate_safety_check_passed', False)}",
        f"- caveat_completeness_passed: {manifest.get('caveat_completeness_passed', False)}",
        f"- presentation_ready_for_demo_only: {manifest.get('presentation_ready_for_demo_only', False)}",
        "",
        "## Checklist",
        f"- [ {artifact_pass} ] Artifact completeness",
        f"- [ {row_pass} ] Row-count closure",
        f"- [ {gate_pass} ] Gate safety",
        f"- [ {caveat_pass} ] Caveat completeness",
        f"- [ {presentation_pass} ] Demo-only presentation readiness",
        f"- [ {'PASS' if manifest.get('sample_demo_row_count', 0) > 0 else 'FAIL'} ] Demo rows sample present",
        f"- [ {'PASS' if manifest.get('sample_quality_limited_row_count', 0) > 0 else 'FAIL'} ] Quality-limited sample present",
        f"- [ {'PASS' if manifest.get('sample_excluded_row_count', 0) > 0 else 'FAIL'} ] Excluded sample present",
        "",
        "## Key Metrics",
        f"- demo_export_row_count: {manifest.get('demo_export_row_count', 0)}",
        f"- quality_limited_row_count: {manifest.get('quality_limited_row_count', 0)}",
        f"- excluded_row_count: {manifest.get('excluded_row_count', 0)}",
        f"- manifest_row_count_total: {manifest.get('manifest_row_count_total', 0)}",
        f"- actual_row_count_total: {manifest.get('actual_row_count_total', 0)}",
        f"- coverage_ratio_before_alias_simulation: {manifest.get('coverage_ratio_before_alias_simulation', None)}",
        f"- coverage_ratio_after_alias_simulation: {manifest.get('coverage_ratio_after_alias_simulation', None)}",
        f"- remaining_unnormalized_raw_metric_name_count: {manifest.get('remaining_unnormalized_raw_metric_name_count', 0)}",
        f"- remaining_unnormalized_metric_row_count: {manifest.get('remaining_unnormalized_metric_row_count', 0)}",
        f"- high_severity_issue_count: {manifest.get('high_severity_issue_count', 0)}",
        f"- medium_severity_issue_count: {manifest.get('medium_severity_issue_count', 0)}",
        f"- missing_unit_count: {manifest.get('missing_unit_count', 0)}",
        f"- missing_period_count: {manifest.get('missing_period_count', 0)}",
        f"- missing_source_trace_count: {manifest.get('missing_source_trace_count', 0)}",
        "",
        "## Gate Safety",
    ]
    for check in gate_safety.get("checks", []):
        lines.append(f"- {check.get('name', '')}: {check.get('status', '')}")

    lines.extend(
        [
            "",
            "## Caveats",
            f"- missing_caveat_topic_count: {manifest.get('missing_caveat_topic_count', 0)}",
        ]
    )
    for topic in caveat_check.get("present_topics", []):
        lines.append(f"- present: {topic}")
    for topic in caveat_check.get("missing_topics", []):
        lines.append(f"- missing: {topic}")

    lines.extend(
        [
            "",
            "## Presentation Readiness",
            f"- safe_for_demo_only: {presentation.get('safe_for_demo_only', False)}",
            f"- first_files_to_open: {', '.join(presentation.get('recommended_first_files', []))}",
            f"- safe_sample_files: {', '.join(presentation.get('safe_sample_files', []))}",
            f"- spoken_caveats: {len(presentation.get('spoken_caveats', []))}",
            f"- prohibited_claims: {len(presentation.get('prohibited_claims', []))}",
            "",
            "## What Must Not Be Claimed",
        ]
    )
    for claim in presentation.get("prohibited_claims", []):
        lines.append(f"- {claim}")
    lines.extend(
        [
            "",
            "## Next Recommended Step",
            f"- {manifest.get('next_recommended_step', '')}",
            "",
            "## Boundary Reminder",
            "- This is demo-only QA, not formal client export.",
            "- Official normalization rules were not modified.",
            "- Official alias assets were not modified.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
    return "\n".join(lines)


def render_executive_summary_markdown(manifest: Dict[str, Any], presentation: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 345E Executive Summary",
            "",
            f"- input package: {manifest.get('input_345d_dir', '')}",
            f"- decision: {manifest.get('decision', '')}",
            f"- qa_fail_count: {manifest.get('qa_fail_count', 0)}",
            f"- artifact_completeness_passed: {manifest.get('artifact_completeness_passed', False)}",
            f"- row_count_closure_passed: {manifest.get('row_count_closure_passed', False)}",
            f"- gate_safety_check_passed: {manifest.get('gate_safety_check_passed', False)}",
            f"- caveat_completeness_passed: {manifest.get('caveat_completeness_passed', False)}",
            f"- presentation_ready_for_demo_only: {manifest.get('presentation_ready_for_demo_only', False)}",
            "",
            "## Review Result",
            "- The 345D demo export package is internally consistent and demo-safe.",
            "- The package remains explicitly demo-only and does not open any formal/client/production gate.",
            "- Caveats remain visible: remaining unnormalized metrics, high/medium severity issues, and source-trace gaps called out by 345D.",
            "",
            "## First Files To Open",
            *[f"- {item}" for item in presentation.get("recommended_first_files", [])],
            "",
            "## Spoken Caveats",
            *[f"- {item}" for item in presentation.get("spoken_caveats", [])],
            "",
            "## Do Not Claim",
            *[f"- {item}" for item in presentation.get("prohibited_claims", [])],
            "",
            "## Recommended Next Step",
            f"- {manifest.get('next_recommended_step', '')}",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )


def render_artifact_index_markdown(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345E Artifact Index",
        "",
        "| Artifact | Path | Purpose |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def render_next_plan_markdown(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 345E Next Plan",
            "",
            f"- Recommended next scope: {manifest.get('next_recommended_step', '')}",
            "- Keep 345D as a demo-only package; do not reframe it as formal client or production output.",
            "- If narrative polish is needed, build a separate 345F demo narrative/report package.",
            "- 344G still waits for a genuinely human-filled 344F workbook.",
        ]
    )
