from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "alias_mapping_proposals",
    "out_of_scope_proposals",
    "unit_inference_proposals",
    "rejected_noise_proposals",
    "candidate_impact_samples",
    "human_review_checklist",
    "remaining_review_burden_after_322f",
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


def proposal_report_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Semantic Mapping Proposals 322G",
        "",
        "## Decision",
        f"- semantic_mapping_proposals_decision: {summary.get('semantic_mapping_proposals_decision', '')}",
        "",
        "## Proposal Counts",
        f"- accepted_instruction_count: {summary.get('accepted_instruction_count', 0)}",
        f"- proposal_total_count: {summary.get('proposal_total_count', 0)}",
        f"- alias_mapping_proposal_count: {summary.get('alias_mapping_proposal_count', 0)}",
        f"- out_of_scope_proposal_count: {summary.get('out_of_scope_proposal_count', 0)}",
        f"- unit_inference_proposal_count: {summary.get('unit_inference_proposal_count', 0)}",
        f"- rejected_noise_proposal_count: {summary.get('rejected_noise_proposal_count', 0)}",
        "",
        "## Impact",
        f"- trusted_gain_total: {summary.get('trusted_gain_total', 0)}",
        f"- review_reduction_total: {summary.get('review_reduction_total', 0)}",
        f"- candidate_impact_sample_count: {summary.get('candidate_impact_sample_count', 0)}",
        f"- remaining_manual_review_count_after_322f: {summary.get('remaining_manual_review_count_after_322f', 0)}",
        f"- selected_core_trusted_rate_before_322f: {summary.get('selected_core_trusted_rate_before_322f', 0)}",
        f"- selected_core_trusted_rate_after_322f: {summary.get('selected_core_trusted_rate_after_322f', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
        "## Notes",
        "- 322G produces human-confirmation proposals only.",
        "- No official mapping, override, or production pipeline files are changed by this stage.",
        "",
    ]
    return "\n".join(lines)
