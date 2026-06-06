from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "before_after_hashes",
    "official_rule_visibility",
    "impact_metrics",
    "duplicate_conflict",
    "rollback_artifacts",
    "semantic_constraints",
    "qa_summary",
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
    path.write_text(
        json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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


def post_patch_regression_validation_325o_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Post-Patch Regression Validation 325O",
        "",
        "## Decision",
        f"- decision: {summary.get('decision', '')}",
        "",
        "## Official Rule Visibility",
        f"- official_rule_visibility_total: {summary.get('official_rule_visibility_total', 0)}",
        f"- official_alias_rules_visible: {summary.get('official_alias_rules_visible', 0)}",
        f"- missing_official_alias_rule_count: {summary.get('missing_official_alias_rule_count', 0)}",
        f"- wrong_target_metric_count: {summary.get('wrong_target_metric_count', 0)}",
        "",
        "## Impact Metrics",
        f"- affected_candidate_count: {summary.get('affected_candidate_count', 0)}",
        f"- trusted_gain_325o: {summary.get('trusted_gain_325o', 0)}",
        f"- review_reduction_325o: {summary.get('review_reduction_325o', 0)}",
        f"- out_of_scope_or_rejected_gain_325o: {summary.get('out_of_scope_or_rejected_gain_325o', 0)}",
        "",
        "## Safety",
        f"- duplicate_delta_count: {summary.get('duplicate_delta_count', 0)}",
        f"- target_conflict_count: {summary.get('target_conflict_count', 0)}",
        f"- adjusted_metric_mismatch_count: {summary.get('adjusted_metric_mismatch_count', 0)}",
        f"- diluted_eps_mismatch_count: {summary.get('diluted_eps_mismatch_count', 0)}",
        f"- core_false_mapping_count: {summary.get('core_false_mapping_count', 0)}",
        f"- rollback_artifact_check_passed: {summary.get('rollback_artifact_check_passed', False)}",
        f"- no_official_asset_modification_during_325o: {summary.get('no_official_asset_modification_during_325o', False)}",
        "",
        "## QA",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
    ]
    blocking = summary.get("blocking_reasons") or []
    if blocking:
        lines.extend(["## Blocking Reasons", *[f"- {item}" for item in blocking], ""])
    lines.extend(
        [
            "## Notes",
            "- 325O is validation-only and reads official assets without modifying them.",
            "- Impact reproduction is based on cached 325I replay evidence plus 325N applied-rule outputs.",
            "- The validation scope is limited to the six official alias rules introduced by 325N.",
            "",
        ]
    )
    return "\n".join(lines)
