from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SUMMARY_SHEET_ORDER = [
    "summary",
    "qa_summary",
    "qa_checks",
    "policy_preview",
    "dedupe_summary",
    "potential_false_trusted_distribution",
    "target_metric_ambiguous_distribution",
    "official_asset_proof",
    "risk_registry",
    "known_limitations",
]

SAMPLES_SHEET_ORDER = [
    "summary",
    "potential_false_trusted",
    "target_metric_ambiguous",
    "candidate_identity_duplicates",
    "row_fingerprint_duplicates",
    "policy_preview",
    "qa_checks",
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


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame], order: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in order:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def routing_policy_calibration_330d_markdown(summary: Dict[str, Any], policy_proposal: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Routing Policy Calibration 330D",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            f"- decision_warning: {summary.get('decision_warning', '')}",
            "",
            "## 330C Validation",
            f"- validated_330c_benchmark: {summary.get('validated_330c_benchmark', False)}",
            f"- scored_record_count: {summary.get('scored_record_count', 0)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Benchmark Mode",
            f"- artifact_row_benchmark: {summary.get('artifact_row_benchmark', False)}",
            f"- deduped_candidate_benchmark: {summary.get('deduped_candidate_benchmark', False)}",
            f"- artifact_row_count: {summary.get('artifact_row_count', 0)}",
            f"- deduped_candidate_count: {summary.get('deduped_candidate_count', 0)}",
            f"- duplicate_artifact_row_count: {summary.get('duplicate_artifact_row_count', 0)}",
            f"- cross_artifact_row_fingerprint_duplicate_artifact_row_count: {summary.get('cross_artifact_row_fingerprint_duplicate_artifact_row_count', 0)}",
            "",
            "## Potential False Trusted",
            f"- potential_false_trusted_count: {summary.get('potential_false_trusted_count', 0)}",
            f"- potential_false_trusted_source_artifact_distribution: {json.dumps(summary.get('potential_false_trusted_source_artifact_distribution', {}), ensure_ascii=False)}",
            f"- potential_false_trusted_score_distribution: {json.dumps(summary.get('potential_false_trusted_score_distribution', {}), ensure_ascii=False)}",
            f"- potential_false_trusted_top_risk_flags: {json.dumps(summary.get('potential_false_trusted_top_risk_flags', {}), ensure_ascii=False)}",
            "",
            "## Target Metric Ambiguity",
            f"- target_metric_ambiguous_count: {summary.get('target_metric_ambiguous_count', 0)}",
            f"- target_metric_ambiguous_routing_distribution: {json.dumps(summary.get('target_metric_ambiguous_routing_distribution', {}), ensure_ascii=False)}",
            f"- target_metric_ambiguous_score_distribution: {json.dumps(summary.get('target_metric_ambiguous_score_distribution', {}), ensure_ascii=False)}",
            "",
            "## Proposed Policy",
            f"- recommended_trusted_min_score: {policy_proposal.get('recommended_trusted_min_score', '')}",
            f"- recommended_review_min_score: {policy_proposal.get('recommended_review_min_score', '')}",
            f"- blocking_risk_policy: {json.dumps(policy_proposal.get('blocking_risk_policy', {}), ensure_ascii=False)}",
            f"- warning_risk_policy: {json.dumps(policy_proposal.get('warning_risk_policy', {}), ensure_ascii=False)}",
            f"- target_metric_ambiguous_policy: {json.dumps(policy_proposal.get('target_metric_ambiguous_policy', {}), ensure_ascii=False)}",
            f"- value_parse_failed_policy: {json.dumps(policy_proposal.get('value_parse_failed_policy', {}), ensure_ascii=False)}",
            f"- unit_unknown_policy: {json.dumps(policy_proposal.get('unit_unknown_policy', {}), ensure_ascii=False)}",
            "",
            "## Safety",
            f"- production_routing_modified: {summary.get('production_routing_modified', False)}",
            f"- official_assets_modified: {summary.get('official_assets_modified', False)}",
            f"- no_official_asset_modification_during_330d: {summary.get('no_official_asset_modification_during_330d', False)}",
            "",
            "## Residual Risks",
            "- 330D remains a sidecar calibration and does not validate a canonical deduped candidate benchmark.",
            "- Cross-artifact duplicate risk is quantified but not fully resolved in this stage.",
            "- Policy proposal is explicit preview-only and must not override production routing.",
            "",
        ]
    )
