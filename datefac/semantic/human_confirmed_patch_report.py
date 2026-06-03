from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "reviewed_proposal_inventory",
    "alias_patch_preview",
    "out_of_scope_patch_preview",
    "unit_inference_patch_preview",
    "rejected_noise_patch_preview",
    "candidate_before_after_diff_322h",
    "trusted_after_patch_preview_322h",
    "review_required_after_patch_preview_322h",
    "rejected_after_patch_preview_322h",
    "patch_impact_by_proposal_322h",
    "remaining_review_burden_322h",
    "official_rule_candidate_preview",
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


def write_jsonl(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in df.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def patch_preview_report_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Human Confirmed Semantic Patch Preview 322H",
        "",
        "## Decision",
        f"- human_confirmed_patch_preview_decision: {summary.get('human_confirmed_patch_preview_decision', '')}",
        "",
        "## Proposal Counts",
        f"- reviewed_proposal_count: {summary.get('reviewed_proposal_count', 0)}",
        f"- accepted_proposal_count: {summary.get('accepted_proposal_count', 0)}",
        f"- rejected_proposal_count: {summary.get('rejected_proposal_count', 0)}",
        f"- needs_more_info_proposal_count: {summary.get('needs_more_info_proposal_count', 0)}",
        f"- accepted_alias_patch_count: {summary.get('accepted_alias_patch_count', 0)}",
        f"- accepted_out_of_scope_patch_count: {summary.get('accepted_out_of_scope_patch_count', 0)}",
        f"- accepted_unit_inference_patch_count: {summary.get('accepted_unit_inference_patch_count', 0)}",
        f"- accepted_rejected_noise_patch_count: {summary.get('accepted_rejected_noise_patch_count', 0)}",
        "",
        "## Impact",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_322h: {summary.get('trusted_gain_322h', 0)}",
        f"- review_reduction_322h: {summary.get('review_reduction_322h', 0)}",
        f"- out_of_scope_or_rejected_gain_322h: {summary.get('out_of_scope_or_rejected_gain_322h', 0)}",
        f"- selected_core_trusted_rate_before_322h: {summary.get('selected_core_trusted_rate_before_322h', 0)}",
        f"- selected_core_trusted_rate_after_322h: {summary.get('selected_core_trusted_rate_after_322h', 0)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
        "## Notes",
        "- 322H is sandbox-only and does not update official mapping or override files.",
        "- official_rule_candidate_preview is a planning artifact for a later explicit rule proposal stage.",
        "",
    ]
    return "\n".join(lines)
