from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "alias_candidates",
    "safety_checks",
    "qa_checks",
    "known_limitations",
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
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
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


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]] | pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = rows.to_dict(orient="records") if isinstance(rows, pd.DataFrame) else list(rows)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(_to_jsonable(record), ensure_ascii=False) + "\n")


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


def alias_official_rule_candidates_from_325i_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Alias Official Rule Candidates From 325I 325J",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Candidate Counts",
        f"- source_sandbox_rule_count: {summary.get('source_sandbox_rule_count', 0)}",
        f"- candidate_count: {summary.get('candidate_count', 0)}",
        f"- alias_candidate_count: {summary.get('alias_candidate_count', 0)}",
        f"- ready_for_controlled_proposal_count: {summary.get('ready_for_controlled_proposal_count', 0)}",
        f"- needs_review_candidate_count: {summary.get('needs_review_candidate_count', 0)}",
        f"- rejected_candidate_count: {summary.get('rejected_candidate_count', 0)}",
        "",
        "## Conflict Checks",
        f"- duplicate_candidate_id_count: {summary.get('duplicate_candidate_id_count', 0)}",
        f"- duplicate_alias_target_pair_count: {summary.get('duplicate_alias_target_pair_count', 0)}",
        f"- official_overlap_count: {summary.get('official_overlap_count', 0)}",
        f"- target_conflict_count: {summary.get('target_conflict_count', 0)}",
        f"- adjusted_metric_mismatch_count: {summary.get('adjusted_metric_mismatch_count', 0)}",
        f"- diluted_eps_mismatch_count: {summary.get('diluted_eps_mismatch_count', 0)}",
        "",
        "## Impact Carried Forward",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_325j: {summary.get('trusted_gain_325j', 0)}",
        f"- review_reduction_325j: {summary.get('review_reduction_325j', 0)}",
        f"- out_of_scope_or_rejected_gain_325j: {summary.get('out_of_scope_or_rejected_gain_325j', 0)}",
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
        "## Notes",
        "- 325J creates official alias rule candidates only.",
        "- 325J does not create controlled proposals, dry runs, or official patches.",
        "- Official mapping and override assets are read only in this stage.",
        "",
    ]
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    return "\n".join(lines)
