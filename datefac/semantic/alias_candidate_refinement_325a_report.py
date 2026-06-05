from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "refined_alias_candidates",
    "safe_batch",
    "holdout_candidates",
    "already_official_overlap",
    "risk_bucket_summary",
    "qa_summary",
    "qa_checks",
    "notes",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


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


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


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


def alias_candidate_refinement_325a_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Alias Candidate Refinement 325A",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Counts",
        f"- input_alias_inventory_count: {summary.get('input_alias_inventory_count', 0)}",
        f"- safe_alias_review_batch_count: {summary.get('safe_alias_review_batch_count', 0)}",
        f"- holdout_count: {summary.get('holdout_count', 0)}",
        "",
        "## Exclusion Counts",
        f"- HOLDOUT_ALREADY_OFFICIAL: {summary.get('excluded_already_official_count', 0)}",
        f"- HOLDOUT_CATEGORY_MISMATCH: {summary.get('excluded_category_mismatch_count', 0)}",
        f"- HOLDOUT_SCOPE_NOISE_OR_DISCLOSURE_TEXT: {summary.get('excluded_scope_noise_or_disclosure_text_count', 0)}",
        f"- HOLDOUT_UNIT_RELATED: {summary.get('excluded_unit_related_count', 0)}",
        f"- HOLDOUT_GENERIC_AMBIGUOUS_LABEL: {summary.get('excluded_generic_ambiguous_label_count', 0)}",
        f"- HOLDOUT_WEAK_EVIDENCE: {summary.get('excluded_weak_evidence_count', 0)}",
        f"- HOLDOUT_DUPLICATE_OR_CONFLICT: {summary.get('excluded_duplicate_or_conflict_count', 0)}",
        f"- HOLDOUT_NEEDS_MORE_INFO: {summary.get('excluded_needs_more_info_count', 0)}",
        "",
        "## Safety",
        f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
        f"- official_assets_written: {summary.get('official_assets_written', [])}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    examples = summary.get("top_safe_alias_examples") or []
    if examples:
        lines.extend(["## Top Safe Alias Examples"])
        for item in examples:
            lines.append(
                f"- {item.get('alias_refinement_candidate_id', '')}: {item.get('repaired_label', '')} "
                f"(affected_review_required_count={item.get('affected_review_required_count', 0)}, "
                f"priority_score={item.get('priority_score', 0)})"
            )
        lines.append("")
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    lines.extend(
        [
            "## Notes",
            "- 325A is refinement and batch planning only.",
            "- 325A does not call an LLM/adjudicator, apply semantic rules, create official candidates, create proposals, or produce sandbox replay packages.",
            "",
        ]
    )
    return "\n".join(lines)
