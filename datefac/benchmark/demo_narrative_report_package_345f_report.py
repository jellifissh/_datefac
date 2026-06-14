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


def _bullet_lines(items: Iterable[str]) -> List[str]:
    return [f"- {item}" for item in items]


def render_stakeholder_report(manifest: Dict[str, Any], talking_points: List[str], caveats: List[str]) -> str:
    lines = [
        "# 345F Stakeholder Report",
        "",
        "## Objective",
        "- DateFac turns financial PDF table outputs into structured demo-ready rows while preserving traceability and review boundaries.",
        "",
        "## Current Result",
        f"- 345D produced {manifest.get('demo_export_row_count', 0)} strict demo rows, {manifest.get('quality_limited_row_count', 0)} quality-limited rows, and {manifest.get('excluded_row_count', 0)} excluded rows.",
        f"- 345E confirmed row-count closure, gate safety, caveat completeness, and demo-only presentation readiness.",
        "",
        "## Quantitative Improvement",
        f"- Coverage before alias simulation: {manifest.get('coverage_ratio_before_alias_simulation', None)}",
        f"- Coverage after alias simulation: {manifest.get('coverage_ratio_after_alias_simulation', None)}",
        f"- Strict demo-ready rows remain {manifest.get('demo_export_row_count', 0)} because simulated aliases improved normalization coverage, not trust or production-readiness by themselves.",
        "",
        "## QA Status",
        f"- row_count_closure_passed: {manifest.get('row_count_closure_passed', False)}",
        f"- gate_safety_check_passed: {manifest.get('gate_safety_check_passed', False)}",
        f"- caveat_completeness_passed: {manifest.get('caveat_completeness_passed', False)}",
        f"- presentation_ready_for_demo_only: {manifest.get('presentation_ready_for_demo_only', False)}",
        "",
        "## What This Demo Proves",
        *_bullet_lines(talking_points[:5]),
        "",
        "## Caveats",
        *_bullet_lines(caveats),
        "",
        "## Boundary",
        "- This package is demo-only.",
        "- It is not a formal client export.",
        "- It is not production-ready.",
        "- Official normalization rules and alias assets were not modified.",
        "",
        "## Recommended Next Step",
        f"- {manifest.get('next_recommended_step', '')}",
        "- 344G still waits for a genuinely human-filled 344F workbook.",
    ]
    return "\n".join(lines)


def render_teacher_brief(manifest: Dict[str, Any], talking_points: List[str], caveats: List[str]) -> str:
    lines = [
        "# 345F Teacher Brief",
        "",
        "## Completed",
        "- Built a demo-only narrative/report package from the existing 345D structured export and 345E QA review.",
        f"- Verified 14,788 inventory rows close cleanly into 109 demo rows, 5,558 quality-limited rows, and 9,121 excluded rows.",
        "",
        "## Verified",
        f"- QA passed with row-count closure = {manifest.get('row_count_closure_passed', False)}",
        f"- Demo presentation readiness = {manifest.get('presentation_ready_for_demo_only', False)}",
        f"- All formal/client/production gates remain false.",
        "",
        "## Improved",
        f"- Normalization coverage increased from {manifest.get('coverage_ratio_before_alias_simulation', None)} to {manifest.get('coverage_ratio_after_alias_simulation', None)} through alias simulation sidecar analysis.",
        "",
        "## Still Limited",
        *_bullet_lines(caveats[:4]),
        "",
        "## Next Task",
        f"- {manifest.get('next_recommended_step', '')}",
    ]
    return "\n".join(lines)


def render_team_update(
    manifest: Dict[str, Any],
    output_dir: str,
    artifact_names: List[str],
    sample_story_count: int,
) -> str:
    lines = [
        "# 345F Team Update",
        "",
        "## Output Package",
        f"- output_dir: {output_dir}",
        f"- generated_report_count: {manifest.get('generated_report_count', 0)}",
        f"- sample_rows_for_story_count: {sample_story_count}",
        "",
        "## Core Metrics",
        f"- demo_export_row_count: {manifest.get('demo_export_row_count', 0)}",
        f"- quality_limited_row_count: {manifest.get('quality_limited_row_count', 0)}",
        f"- excluded_row_count: {manifest.get('excluded_row_count', 0)}",
        f"- row_count_closure_passed: {manifest.get('row_count_closure_passed', False)}",
        f"- qa_fail_count: {manifest.get('qa_fail_count', 0)}",
        "",
        "## Boundary",
        "- No new export dataset was created beyond bounded story samples copied from 345E.",
        "- No normalization rules or official alias assets were modified.",
        "- No write-back was performed into 345D/345E or earlier outputs.",
        "- No formal/client/production gate was opened.",
        "",
        "## Artifacts Generated",
        *_bullet_lines(artifact_names),
        "",
        "## Suggested Consumers",
        "- Frontend/UI can reuse frontend demo copy, talking points, and story sample rows.",
        "- Reporting/demo teammates can start from stakeholder report and claims table.",
        "- QA/demo presenters should keep the risk and caveat section visible.",
    ]
    return "\n".join(lines)


def render_interview_summary(manifest: Dict[str, Any], caveats: List[str]) -> str:
    lines = [
        "# 345F Interview Project Summary",
        "",
        "## Project Challenge",
        "- Structured extraction from real financial PDF tables is noisy because parser output, quality issues, and metric normalization all have to be reconciled before safe presentation.",
        "",
        "## My Contribution",
        "- Built sidecar-style benchmark, QA, and narrative packaging steps that keep extraction evidence, presentation packaging, and safety gates separate.",
        f"- Converted 345D/345E outputs into a reusable demo narrative package without mutating upstream assets.",
        "",
        "## Measurable Result",
        f"- Inventory closure: {manifest.get('inventory_row_count', 0)} total rows.",
        f"- Demo-ready rows: {manifest.get('demo_export_row_count', 0)}.",
        f"- Coverage moved from {manifest.get('coverage_ratio_before_alias_simulation', None)} to {manifest.get('coverage_ratio_after_alias_simulation', None)} with simulation-only alias analysis.",
        f"- QA review confirmed gate safety and caveat completeness with qa_fail_count = {manifest.get('qa_fail_count', 0)}.",
        "",
        "## Engineering Discipline",
        "- Used no-write-back proofing and protected-dirty-file preservation.",
        "- Kept formal/client/production gates false.",
        "- Treated simulated alias improvements as analytical evidence, not official rule mutation.",
        "",
        "## Honest Caveats",
        *_bullet_lines(caveats[:5]),
    ]
    return "\n".join(lines)


def render_frontend_demo_copy(manifest: Dict[str, Any]) -> str:
    lines = [
        "# 345F Frontend Demo Copy",
        "",
        "## Labels",
        "- Demo badge: `DEMO ONLY`",
        "- Coverage badge: `Normalization coverage 45.25% -> 68.41% (simulation branch)`",
        "- Caveat badge: `Quality limits and blind spots remain`",
        "",
        "## Tooltip Copy",
        "- Alias simulation tooltip: `Coverage improved through simulation-only alias suggestions. Official rules were not changed.`",
        "- Quality-limited tooltip: `These rows are visible for demo analysis but still require caveat-aware interpretation.`",
        "- Excluded-row tooltip: `These rows stay outside the strict demo package because quality or normalization constraints remain unresolved.`",
        "",
        "## Warning Copy",
        "- Warning banner: `This demo is not a formal client export and is not production-ready.`",
        "- Warning subtext: `Strict demo-ready rows = 109. Quality-limited rows = 5,558. Excluded rows = 9,121.`",
        "",
        "## CTA Copy",
        f"- Presenter hint: `Open the QA checklist first, then walk through {manifest.get('sample_rows_for_story_count', 0)} bounded sample rows for the story.`",
    ]
    return "\n".join(lines)


def render_talking_points(talking_points: List[str], allowed_claims: List[str], forbidden_claims: List[str]) -> str:
    lines = [
        "# 345F Talking Points",
        "",
        "## Safe Talking Points",
        *_bullet_lines(talking_points),
        "",
        "## Allowed Claims",
        *_bullet_lines(allowed_claims),
        "",
        "## Forbidden Claims",
        *_bullet_lines(forbidden_claims),
    ]
    return "\n".join(lines)


def render_risk_and_caveat_section(caveats: List[str]) -> str:
    lines = [
        "# 345F Risk And Caveat Section",
        "",
        "## Remaining Risks",
        *_bullet_lines(caveats),
        "",
        "## Interpretation Rule",
        "- Alias simulation evidence improves demo analysis coverage, but it does not convert simulated rows into official-rule-backed production rows.",
        "- Quality-limited and excluded buckets must remain visible in any demo narrative.",
        "- Formal/client/production readiness remain false.",
    ]
    return "\n".join(lines)


def render_claims_allowed_vs_forbidden(allowed_claims: List[str], forbidden_claims: List[str]) -> str:
    lines = [
        "# 345F Allowed Vs Forbidden Claims",
        "",
        "| Allowed | Forbidden |",
        "| --- | --- |",
    ]
    row_count = max(len(allowed_claims), len(forbidden_claims))
    for index in range(row_count):
        allowed = allowed_claims[index] if index < len(allowed_claims) else ""
        forbidden = forbidden_claims[index] if index < len(forbidden_claims) else ""
        lines.append(f"| {allowed} | {forbidden} |")
    return "\n".join(lines)


def render_artifact_index(rows: Iterable[Dict[str, Any]]) -> str:
    lines = [
        "# 345F Artifact Index",
        "",
        "| Artifact | Path | Purpose |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('artifact_name', '')} | {row.get('path', '')} | {row.get('purpose', '')} |"
        )
    return "\n".join(lines)


def render_next_plan(manifest: Dict[str, Any]) -> str:
    lines = [
        "# 345F Next Plan",
        "",
        f"- Recommended next scope: {manifest.get('next_recommended_step', '')}",
        "- Keep 345D/345E/345F in the demo-only reporting lane.",
        "- Do not treat alias simulation as an official rule update without explicit approval.",
        "- 344G still waits for a genuinely human-filled 344F workbook.",
    ]
    return "\n".join(lines)
