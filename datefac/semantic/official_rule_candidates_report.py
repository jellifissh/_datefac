from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "official_alias_rule_candidates",
    "official_scope_rule_candidates",
    "candidate_impact_evidence",
    "duplicate_conflict_audit",
    "official_patch_json_preview",
    "human_approval_checklist",
    "remaining_review_burden_after_candidate_rules",
    "qa_checks",
    "known_limitations",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


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


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def official_rule_candidates_report_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Official Semantic Rule Candidates 322I",
        "",
        "## Decision",
        f"- official_rule_candidates_decision: {summary.get('official_rule_candidates_decision', '')}",
        "",
        "## Candidate Counts",
        f"- input_official_rule_candidate_count: {summary.get('input_official_rule_candidate_count', 0)}",
        f"- alias_rule_candidate_count: {summary.get('alias_rule_candidate_count', 0)}",
        f"- scope_rule_candidate_count: {summary.get('scope_rule_candidate_count', 0)}",
        f"- duplicate_rule_candidate_count: {summary.get('duplicate_rule_candidate_count', 0)}",
        f"- conflict_rule_candidate_count: {summary.get('conflict_rule_candidate_count', 0)}",
        f"- ready_for_sandbox_application_count: {summary.get('ready_for_sandbox_application_count', 0)}",
        f"- needs_additional_review_count: {summary.get('needs_additional_review_count', 0)}",
        "",
        "## Expected Impact",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- expected_trusted_gain: {summary.get('expected_trusted_gain', 0)}",
        f"- expected_review_reduction: {summary.get('expected_review_reduction', 0)}",
        f"- expected_out_of_scope_or_rejected_gain: {summary.get('expected_out_of_scope_or_rejected_gain', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
        "## Notes",
        "- 322I only packages official rule candidates; it does not modify official mapping or override files.",
        "- Any later rule application still requires an explicit controlled stage and human approval.",
        "",
    ]
    return "\n".join(lines)
