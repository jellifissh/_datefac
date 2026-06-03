from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from datefac.semantic.human_confirmed_patch_preview import (
    _candidate_passes_trust_gate,
    _normalize_label,
    _prepare_candidate_frames,
    _split_tags,
    apply_human_confirmed_patches,
    build_remaining_review_burden,
    read_jsonl,
)


EXPECTED_PACKAGE_COUNTS = {
    "input_official_rule_candidate_count": 10,
    "alias_rule_candidate_count": 3,
    "scope_rule_candidate_count": 7,
    "unit_rule_candidate_count": 0,
    "rejected_noise_rule_candidate_count": 0,
    "duplicate_rule_candidate_count": 0,
    "conflict_rule_candidate_count": 0,
    "ready_for_sandbox_application_count": 10,
    "needs_additional_review_count": 0,
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _safe_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


def _safe_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _join_unique(items: List[str], limit: int = 8) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _build_accepted_proposals_from_package(
    alias_candidates: List[Dict[str, Any]],
    scope_candidates: List[Dict[str, Any]],
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for row in alias_candidates:
        rows.append(
            {
                "proposal_id": _norm(row.get("source_proposal_id")),
                "proposal_type": "alias",
                "source_case_id": _norm(row.get("source_case_id")),
                "normalized_label": _norm(row.get("normalized_label")),
                "proposed_metric_code": _norm(row.get("proposed_metric_code")),
                "proposed_metric_family": _norm(row.get("proposed_metric_family")),
                "sample_table_titles": _norm(row.get("evidence_table_titles")),
                "sample_row_labels": _norm(row.get("sample_row_labels")),
                "sample_values": _norm(row.get("sample_values")),
                "risk_flags": _norm(row.get("risk_flags")),
                "affected_candidate_count": _safe_int(row.get("affected_candidate_count")),
                "trusted_gain": _safe_int(row.get("trusted_gain")),
                "review_reduction": _safe_int(row.get("review_reduction")),
                "reviewer_decision": "ACCEPT",
                "reviewer_comment": "322I official rule candidate package replay in sandbox only",
            }
        )
    for row in scope_candidates:
        rows.append(
            {
                "proposal_id": _norm(row.get("source_proposal_id")),
                "proposal_type": "out_of_scope",
                "source_case_id": _norm(row.get("source_case_id")),
                "normalized_label": _norm(row.get("normalized_label")),
                "proposed_scope_action": _norm(row.get("proposed_scope_action")) or "exclude_from_core_metric_mapping",
                "sample_table_titles": _norm(row.get("evidence_table_titles")),
                "sample_row_labels": _norm(row.get("sample_row_labels")),
                "sample_values": _norm(row.get("sample_values")),
                "risk_flags": _norm(row.get("risk_flags")),
                "affected_candidate_count": _safe_int(row.get("affected_candidate_count")),
                "review_reduction": _safe_int(row.get("review_reduction")),
                "rejected_or_out_of_scope_gain": _safe_int(row.get("rejected_or_out_of_scope_gain")),
                "reviewer_decision": "ACCEPT",
                "reviewer_comment": "322I official rule candidate package replay in sandbox only",
            }
        )
    return pd.DataFrame(rows).fillna("")


def load_official_rule_candidates_322j_inputs(
    official_rule_candidate_dir: Path,
    trust_split_dir: Path,
    patch_preview_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    package_summary = _read_json(official_rule_candidate_dir / "official_semantic_rule_candidates_322i_summary.json")
    package_json = _read_json(official_rule_candidate_dir / "official_rule_candidate_package_322i.json")
    trust_summary = _read_json(trust_split_dir / "router_mineru_trust_split_322b2_summary.json")
    patch_summary = _read_json((patch_preview_dir or Path()) / "human_confirmed_semantic_patch_preview_322h_summary.json") if patch_preview_dir else {}

    alias_candidates = package_json.get("alias_rule_candidates", [])
    scope_candidates = package_json.get("scope_rule_candidates", [])
    alias_candidates = alias_candidates if isinstance(alias_candidates, list) else []
    scope_candidates = scope_candidates if isinstance(scope_candidates, list) else []

    return {
        "package_summary": package_summary,
        "package_json": package_json,
        "alias_candidates": alias_candidates,
        "scope_candidates": scope_candidates,
        "trust_summary": trust_summary,
        "patch_summary": patch_summary,
        "selected_candidates_df": read_jsonl(trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"),
    }


def _build_rule_application_log(
    accepted_proposals_df: pd.DataFrame,
    patch_impact_df: pd.DataFrame,
    package_lookup: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    impact_lookup = {
        _norm(row.get("proposal_id")): row.to_dict()
        for _, row in patch_impact_df.iterrows()
    } if not patch_impact_df.empty else {}

    rows: List[Dict[str, Any]] = []
    for _, proposal in accepted_proposals_df.iterrows():
        proposal_id = _norm(proposal.get("proposal_id"))
        package_row = package_lookup.get(proposal_id, {})
        impact_row = impact_lookup.get(proposal_id, {})
        proposal_type = _norm(proposal.get("proposal_type"))
        rows.append(
            {
                "proposal_id": proposal_id,
                "rule_candidate_id": _norm(package_row.get("rule_candidate_id")),
                "rule_type": proposal_type,
                "normalized_label": _norm(proposal.get("normalized_label")),
                "sandbox_action": (
                    "apply_alias_metric_mapping"
                    if proposal_type == "alias"
                    else "apply_scope_exclusion"
                    if proposal_type == "out_of_scope"
                    else "unsupported"
                ),
                "proposed_metric_code": _norm(proposal.get("proposed_metric_code")),
                "proposed_metric_family": _norm(proposal.get("proposed_metric_family")),
                "proposed_scope_action": _norm(proposal.get("proposed_scope_action")),
                "expected_affected_candidate_count": _safe_int(package_row.get("affected_candidate_count")),
                "actual_affected_candidate_count": _safe_int(impact_row.get("affected_candidate_count")),
                "expected_trusted_gain": _safe_int(package_row.get("trusted_gain")),
                "actual_trusted_gain": _safe_int(impact_row.get("trusted_gain")),
                "expected_review_reduction": _safe_int(package_row.get("review_reduction")),
                "actual_review_reduction": _safe_int(impact_row.get("review_reduction")),
                "expected_rejected_or_out_of_scope_gain": _safe_int(package_row.get("rejected_or_out_of_scope_gain")),
                "actual_rejected_or_out_of_scope_gain": _safe_int(impact_row.get("rejected_or_out_of_scope_count")),
                "application_status": _norm(impact_row.get("notes")).upper() or "NOT_APPLIED",
                "application_detail": _norm(package_row.get("recommended_action")) or "READY_FOR_322J_SANDBOX_RULE_APPLICATION",
            }
        )
    return pd.DataFrame(rows).fillna("")


def _build_before_after_overview(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "metric": "trusted_total",
            "before": _safe_int(summary.get("trusted_total_before_322j")),
            "after": _safe_int(summary.get("trusted_total_after_322j")),
            "delta": _safe_int(summary.get("trusted_gain_322j")),
        },
        {
            "metric": "review_required_total",
            "before": _safe_int(summary.get("review_required_total_before_322j")),
            "after": _safe_int(summary.get("review_required_total_after_322j")),
            "delta": _safe_int(summary.get("review_required_total_after_322j")) - _safe_int(summary.get("review_required_total_before_322j")),
        },
        {
            "metric": "rejected_total",
            "before": _safe_int(summary.get("rejected_total_before_322j")),
            "after": _safe_int(summary.get("rejected_total_after_322j")),
            "delta": _safe_int(summary.get("rejected_total_after_322j")) - _safe_int(summary.get("rejected_total_before_322j")),
        },
        {
            "metric": "selected_core_trusted_rate",
            "before": _safe_float(summary.get("selected_core_trusted_rate_before_322j")),
            "after": _safe_float(summary.get("selected_core_trusted_rate_after_322j")),
            "delta": round(
                _safe_float(summary.get("selected_core_trusted_rate_after_322j"))
                - _safe_float(summary.get("selected_core_trusted_rate_before_322j")),
                6,
            ),
        },
        {
            "metric": "remaining_unknown_metric_candidate_count",
            "before": "",
            "after": _safe_int(summary.get("remaining_unknown_metric_candidate_count")),
            "delta": "",
        },
        {
            "metric": "remaining_unit_unknown_candidate_count",
            "before": "",
            "after": _safe_int(summary.get("remaining_unit_unknown_candidate_count")),
            "delta": "",
        },
        {
            "metric": "remaining_manual_review_count",
            "before": "",
            "after": _safe_int(summary.get("remaining_manual_review_count")),
            "delta": "",
        },
    ]
    return pd.DataFrame(rows).fillna("")


def _build_rule_application_overview(log_df: pd.DataFrame) -> pd.DataFrame:
    if log_df.empty:
        return pd.DataFrame(
            columns=[
                "rule_type",
                "rule_count",
                "expected_affected_candidate_count",
                "actual_affected_candidate_count",
                "expected_trusted_gain",
                "actual_trusted_gain",
                "expected_review_reduction",
                "actual_review_reduction",
                "expected_rejected_or_out_of_scope_gain",
                "actual_rejected_or_out_of_scope_gain",
            ]
        )
    rows: List[Dict[str, Any]] = []
    for rule_type, group in log_df.groupby("rule_type", dropna=False):
        rows.append(
            {
                "rule_type": rule_type,
                "rule_count": int(len(group)),
                "expected_affected_candidate_count": _safe_numeric_sum(group, "expected_affected_candidate_count"),
                "actual_affected_candidate_count": _safe_numeric_sum(group, "actual_affected_candidate_count"),
                "expected_trusted_gain": _safe_numeric_sum(group, "expected_trusted_gain"),
                "actual_trusted_gain": _safe_numeric_sum(group, "actual_trusted_gain"),
                "expected_review_reduction": _safe_numeric_sum(group, "expected_review_reduction"),
                "actual_review_reduction": _safe_numeric_sum(group, "actual_review_reduction"),
                "expected_rejected_or_out_of_scope_gain": _safe_numeric_sum(group, "expected_rejected_or_out_of_scope_gain"),
                "actual_rejected_or_out_of_scope_gain": _safe_numeric_sum(group, "actual_rejected_or_out_of_scope_gain"),
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values("rule_type").reset_index(drop=True)


def _build_affected_candidate_deltas_by_rule(diff_df: pd.DataFrame) -> pd.DataFrame:
    if diff_df.empty:
        return pd.DataFrame(
            columns=[
                "proposal_id",
                "patch_id",
                "affected_candidate_count",
                "trusted_after_count",
                "rejected_after_count",
                "sample_labels",
                "sample_table_titles",
            ]
        )
    temp = diff_df.copy()
    rows: List[Dict[str, Any]] = []
    for (proposal_id, patch_id), group in temp.groupby(["proposal_id", "patch_id"], dropna=False):
        rows.append(
            {
                "proposal_id": _norm(proposal_id),
                "patch_id": _norm(patch_id),
                "affected_candidate_count": int(len(group)),
                "trusted_after_count": int(group["decision_after"].astype(str).eq("trusted_preview").sum()),
                "rejected_after_count": int(group["decision_after"].astype(str).eq("rejected_preview").sum()),
                "sample_labels": _join_unique(group["row_label"].astype(str).tolist(), limit=5),
                "sample_table_titles": _join_unique(group.get("table_title", pd.Series(dtype=str)).astype(str).tolist() if "table_title" in group.columns else [], limit=5),
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values(["proposal_id", "patch_id"]).reset_index(drop=True)


def _package_counts_from_inputs(
    package_summary: Dict[str, Any],
    alias_candidates: List[Dict[str, Any]],
    scope_candidates: List[Dict[str, Any]],
) -> Dict[str, int]:
    return {
        "input_official_rule_candidate_count": _safe_int(package_summary.get("input_official_rule_candidate_count")) or (len(alias_candidates) + len(scope_candidates)),
        "alias_rule_candidate_count": _safe_int(package_summary.get("alias_rule_candidate_count")) or len(alias_candidates),
        "scope_rule_candidate_count": _safe_int(package_summary.get("scope_rule_candidate_count")) or len(scope_candidates),
        "unit_rule_candidate_count": _safe_int(package_summary.get("unit_rule_candidate_count")),
        "rejected_noise_rule_candidate_count": _safe_int(package_summary.get("rejected_noise_rule_candidate_count")),
        "duplicate_rule_candidate_count": _safe_int(package_summary.get("duplicate_rule_candidate_count")),
        "conflict_rule_candidate_count": _safe_int(package_summary.get("conflict_rule_candidate_count")),
        "ready_for_sandbox_application_count": _safe_int(package_summary.get("ready_for_sandbox_application_count")),
        "needs_additional_review_count": _safe_int(package_summary.get("needs_additional_review_count")),
    }


def _compute_remaining_counts(review_after_df: pd.DataFrame) -> Tuple[int, int, int]:
    if review_after_df.empty:
        return 0, 0, 0
    remaining_unknown_metric_candidate_count = int(
        review_after_df["risk_tags_after"].astype(str).str.contains(
            r"(?:^|\|)UNKNOWN_METRIC_CODE(?:$|\|)",
            regex=True,
        ).sum()
    )
    remaining_unit_unknown_candidate_count = int(
        review_after_df["risk_tags_after"].astype(str).str.contains(
            r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)",
            regex=True,
        ).sum()
    )
    return (
        remaining_unknown_metric_candidate_count,
        remaining_unit_unknown_candidate_count,
        int(len(review_after_df)),
    )


def _build_expected_lookup(alias_candidates: List[Dict[str, Any]], scope_candidates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for row in alias_candidates + scope_candidates:
        proposal_id = _norm(row.get("source_proposal_id"))
        if proposal_id:
            lookup[proposal_id] = row
    return lookup


def build_official_rule_candidates_322j_sandbox_application(
    package_summary: Dict[str, Any],
    alias_candidates: List[Dict[str, Any]],
    scope_candidates: List[Dict[str, Any]],
    trust_summary: Dict[str, Any],
    patch_summary: Dict[str, Any],
    selected_candidates_df: pd.DataFrame,
) -> Dict[str, Any]:
    package_counts = _package_counts_from_inputs(package_summary, alias_candidates, scope_candidates)
    accepted_proposals_df = _build_accepted_proposals_from_package(alias_candidates, scope_candidates)
    applied = apply_human_confirmed_patches(
        accepted_proposals_df=accepted_proposals_df,
        selected_candidates_df=selected_candidates_df,
    )

    trusted_before_df = applied["trusted_before_df"]
    review_before_df = applied["review_before_df"]
    rejected_before_df = applied["rejected_before_df"]
    trusted_after_df = applied["trusted_after_df"]
    review_after_df = applied["review_after_df"]
    rejected_after_df = applied["rejected_after_df"]
    diff_df = applied["candidate_before_after_diff_df"].copy()
    impact_df = applied["patch_impact_by_proposal_df"].copy()
    remaining_review_burden_df = build_remaining_review_burden(review_after_df)

    expected_lookup = _build_expected_lookup(alias_candidates, scope_candidates)
    rule_application_log_df = _build_rule_application_log(
        accepted_proposals_df=accepted_proposals_df,
        patch_impact_df=impact_df,
        package_lookup=expected_lookup,
    )

    trusted_total_before_322j = int(len(trusted_before_df))
    trusted_total_after_322j = int(len(trusted_after_df))
    review_required_total_before_322j = int(len(review_before_df))
    review_required_total_after_322j = int(len(review_after_df))
    rejected_total_before_322j = int(len(rejected_before_df))
    rejected_total_after_322j = int(len(rejected_after_df))
    trusted_gain_322j = trusted_total_after_322j - trusted_total_before_322j
    review_reduction_322j = review_required_total_before_322j - review_required_total_after_322j
    out_of_scope_or_rejected_gain_322j = rejected_total_after_322j - rejected_total_before_322j

    (
        remaining_unknown_metric_candidate_count,
        remaining_unit_unknown_candidate_count,
        remaining_manual_review_count,
    ) = _compute_remaining_counts(review_after_df)

    expected_trusted_gain = _safe_int(package_summary.get("expected_trusted_gain"))
    expected_review_reduction = _safe_int(package_summary.get("expected_review_reduction"))
    expected_out_of_scope_or_rejected_gain = _safe_int(package_summary.get("expected_out_of_scope_or_rejected_gain"))
    expected_affected_candidate_count = _safe_int(package_summary.get("affected_candidate_count"))
    actual_affected_candidate_count = int(len(diff_df))

    selected_core_trusted_rate_before_322j = _safe_float(
        trust_summary.get("selected_core_trusted_rate_after_322b2")
    )
    selected_core_trusted_rate_after_322j = round(
        trusted_total_after_322j / len(selected_candidates_df),
        6,
    ) if len(selected_candidates_df) else 0.0

    summary: Dict[str, Any] = {
        "stage": "322J",
        "output_dir": "",
        **package_counts,
        "trusted_total_before_322j": trusted_total_before_322j,
        "trusted_total_after_322j": trusted_total_after_322j,
        "review_required_total_before_322j": review_required_total_before_322j,
        "review_required_total_after_322j": review_required_total_after_322j,
        "rejected_total_before_322j": rejected_total_before_322j,
        "rejected_total_after_322j": rejected_total_after_322j,
        "trusted_gain_322j": trusted_gain_322j,
        "review_reduction_322j": review_reduction_322j,
        "out_of_scope_or_rejected_gain_322j": out_of_scope_or_rejected_gain_322j,
        "affected_candidate_count": actual_affected_candidate_count,
        "expected_trusted_gain_322i": expected_trusted_gain,
        "expected_review_reduction_322i": expected_review_reduction,
        "expected_out_of_scope_or_rejected_gain_322i": expected_out_of_scope_or_rejected_gain,
        "expected_affected_candidate_count_322i": expected_affected_candidate_count,
        "trusted_gain_delta_vs_322i_expected": trusted_gain_322j - expected_trusted_gain,
        "review_reduction_delta_vs_322i_expected": review_reduction_322j - expected_review_reduction,
        "out_of_scope_or_rejected_gain_delta_vs_322i_expected": out_of_scope_or_rejected_gain_322j - expected_out_of_scope_or_rejected_gain,
        "affected_candidate_count_delta_vs_322i_expected": actual_affected_candidate_count - expected_affected_candidate_count,
        "selected_core_trusted_rate_before_322j": selected_core_trusted_rate_before_322j,
        "selected_core_trusted_rate_after_322j": selected_core_trusted_rate_after_322j,
        "remaining_unknown_metric_candidate_count": remaining_unknown_metric_candidate_count,
        "remaining_unit_unknown_candidate_count": remaining_unit_unknown_candidate_count,
        "remaining_manual_review_count": remaining_manual_review_count,
        "reference_322h_trusted_gain": _safe_int(patch_summary.get("trusted_gain_322h")),
        "reference_322h_review_reduction": _safe_int(patch_summary.get("review_reduction_322h")),
        "reference_322h_out_of_scope_or_rejected_gain": _safe_int(patch_summary.get("out_of_scope_or_rejected_gain_322h")),
        "reference_322h_affected_candidate_count": _safe_int(patch_summary.get("affected_candidate_count")),
        "blocking_reasons": [],
    }

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    for key, expected in EXPECTED_PACKAGE_COUNTS.items():
        actual = package_counts.get(key, 0)
        add_qa(
            f"package_validation::{key}",
            "PASS" if actual == expected else "FAIL",
            f"expected={expected} actual={actual}",
        )

    add_qa(
        "package_validation::alias_plus_scope_matches_total",
        "PASS" if package_counts["input_official_rule_candidate_count"] == package_counts["alias_rule_candidate_count"] + package_counts["scope_rule_candidate_count"] else "FAIL",
        f"total={package_counts['input_official_rule_candidate_count']} alias_plus_scope={package_counts['alias_rule_candidate_count'] + package_counts['scope_rule_candidate_count']}",
    )

    add_qa(
        "rule_application::all_package_candidates_loaded",
        "PASS" if len(accepted_proposals_df) == package_counts["input_official_rule_candidate_count"] else "FAIL",
        f"accepted_proposals_loaded={len(accepted_proposals_df)}",
    )
    add_qa(
        "rule_application::rule_application_log_count_matches_package",
        "PASS" if len(rule_application_log_df) == package_counts["input_official_rule_candidate_count"] else "FAIL",
        f"log_count={len(rule_application_log_df)}",
    )

    all_rules_applied = True
    if not rule_application_log_df.empty:
        all_rules_applied = rule_application_log_df["application_status"].astype(str).str.startswith("APPLIED_").all()
    add_qa(
        "rule_application::all_rules_applied_to_review_pool",
        "PASS" if all_rules_applied else "FAIL",
        f"applied_rule_count={int(rule_application_log_df['application_status'].astype(str).str.startswith('APPLIED_').sum()) if not rule_application_log_df.empty else 0}",
    )

    add_qa(
        "before_after_consistency::candidate_counts_reconcile",
        "PASS" if len(selected_candidates_df) == trusted_total_after_322j + review_required_total_after_322j + rejected_total_after_322j else "FAIL",
        f"input={len(selected_candidates_df)} after_total={trusted_total_after_322j + review_required_total_after_322j + rejected_total_after_322j}",
    )
    add_qa(
        "before_after_consistency::trusted_gain_matches_delta",
        "PASS" if trusted_gain_322j == _safe_numeric_sum(impact_df, "trusted_gain") else "FAIL",
        f"summary={trusted_gain_322j} impact_sum={_safe_numeric_sum(impact_df, 'trusted_gain')}",
    )
    add_qa(
        "before_after_consistency::review_reduction_matches_delta",
        "PASS" if review_reduction_322j == _safe_numeric_sum(impact_df, "review_reduction") else "FAIL",
        f"summary={review_reduction_322j} impact_sum={_safe_numeric_sum(impact_df, 'review_reduction')}",
    )
    add_qa(
        "before_after_consistency::rejected_gain_matches_delta",
        "PASS" if out_of_scope_or_rejected_gain_322j == _safe_numeric_sum(impact_df, "rejected_or_out_of_scope_count") else "FAIL",
        f"summary={out_of_scope_or_rejected_gain_322j} impact_sum={_safe_numeric_sum(impact_df, 'rejected_or_out_of_scope_count')}",
    )
    add_qa(
        "before_after_consistency::affected_count_matches_diff_rows",
        "PASS" if actual_affected_candidate_count == _safe_numeric_sum(impact_df, "affected_candidate_count") else "FAIL",
        f"diff_rows={actual_affected_candidate_count} impact_sum={_safe_numeric_sum(impact_df, 'affected_candidate_count')}",
    )

    no_duplicate = int(rule_application_log_df["proposal_id"].astype(str).nunique()) == len(rule_application_log_df) if not rule_application_log_df.empty else True
    add_qa(
        "rule_application::no_duplicate_rule_application",
        "PASS" if no_duplicate else "FAIL",
        f"unique_proposal_id_count={int(rule_application_log_df['proposal_id'].astype(str).nunique()) if not rule_application_log_df.empty else 0}",
    )
    add_qa(
        "rule_application::no_conflict_candidates_in_package",
        "PASS" if package_counts["conflict_rule_candidate_count"] == 0 else "FAIL",
        f"conflict_rule_candidate_count={package_counts['conflict_rule_candidate_count']}",
    )

    core_false_exclusion = False
    if not diff_df.empty:
        rejected_after = diff_df[diff_df["decision_after"].astype(str) == "rejected_preview"].copy()
        if not rejected_after.empty:
            core_false_exclusion = rejected_after["metric_code_after"].astype(str).isin(
                ["revenue", "net_profit", "gross_margin", "roe", "eps", "pe", "pb", "ev_ebitda"]
            ).any()
    add_qa(
        "safety::no_core_metric_false_exclusion",
        "PASS" if not core_false_exclusion else "FAIL",
        f"rejected_diff_rows={int(diff_df['decision_after'].astype(str).eq('rejected_preview').sum()) if not diff_df.empty else 0}",
    )

    trusted_regression = trusted_total_after_322j < trusted_total_before_322j
    add_qa(
        "safety::no_trusted_regression",
        "PASS" if not trusted_regression else "FAIL",
        f"before={trusted_total_before_322j} after={trusted_total_after_322j}",
    )

    rate_not_down = selected_core_trusted_rate_after_322j >= selected_core_trusted_rate_before_322j
    add_qa(
        "safety::selected_core_trusted_rate_not_down",
        "PASS" if rate_not_down else "FAIL",
        f"before={selected_core_trusted_rate_before_322j} after={selected_core_trusted_rate_after_322j}",
    )

    trusted_gate_ok = True
    if not trusted_after_df.empty:
        trusted_gate_ok = trusted_after_df.apply(_candidate_passes_trust_gate, axis=1).all()
    add_qa(
        "safety::trusted_after_candidates_still_pass_deterministic_gate",
        "PASS" if trusted_gate_ok else "FAIL",
        f"trusted_after_count={len(trusted_after_df)}",
    )

    add_qa(
        "alignment::trusted_gain_matches_322i_expected",
        "PASS" if trusted_gain_322j == expected_trusted_gain else "WARN",
        f"expected={expected_trusted_gain} actual={trusted_gain_322j}",
    )
    add_qa(
        "alignment::review_reduction_matches_322i_expected",
        "PASS" if review_reduction_322j == expected_review_reduction else "WARN",
        f"expected={expected_review_reduction} actual={review_reduction_322j}",
    )
    add_qa(
        "alignment::out_of_scope_gain_matches_322i_expected",
        "PASS" if out_of_scope_or_rejected_gain_322j == expected_out_of_scope_or_rejected_gain else "WARN",
        f"expected={expected_out_of_scope_or_rejected_gain} actual={out_of_scope_or_rejected_gain_322j}",
    )
    add_qa(
        "alignment::affected_candidate_count_matches_322i_expected",
        "PASS" if actual_affected_candidate_count == expected_affected_candidate_count else "WARN",
        f"expected={expected_affected_candidate_count} actual={actual_affected_candidate_count}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    blocking_reasons: List[str] = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["blocking_reasons"] = blocking_reasons
    summary["official_rule_candidates_322j_decision"] = (
        "OFFICIAL_RULE_CANDIDATES_322J_READY_FOR_322K_CONTROLLED_OFFICIAL_PATCH_PROPOSAL"
        if qa_fail_count == 0
        else "OFFICIAL_RULE_CANDIDATES_322J_NOT_READY_FOR_OFFICIAL_PATCH"
    )

    before_after_overview_df = _build_before_after_overview(summary)
    rule_application_overview_df = _build_rule_application_overview(rule_application_log_df)
    affected_candidate_deltas_by_rule_df = _build_affected_candidate_deltas_by_rule(diff_df)

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "sandbox_only",
                "detail": "322J applies official rule candidates in runtime only and does not write official mapping or overrides.",
            },
            {
                "limitation": "baseline_scope",
                "detail": "322J replays only against 322B2 selected_candidate_reclassified_322b2.jsonl.",
            },
            {
                "limitation": "no_recognizer_execution",
                "detail": "322J does not run MinerU, StructEqTable, Docling, PPStructure, or VLM.",
            },
        ]
    )

    return {
        "summary": summary,
        "official_alias_rule_candidates_df": pd.DataFrame(alias_candidates).fillna(""),
        "official_scope_rule_candidates_df": pd.DataFrame(scope_candidates).fillna(""),
        "trusted_after_preview_df": trusted_after_df,
        "review_required_after_preview_df": review_after_df,
        "rejected_after_preview_df": rejected_after_df,
        "candidate_before_after_diff_df": diff_df,
        "rule_application_log_df": rule_application_log_df,
        "affected_candidate_deltas_by_rule_df": affected_candidate_deltas_by_rule_df,
        "remaining_review_burden_322j_df": remaining_review_burden_df,
        "before_after_overview_df": before_after_overview_df,
        "rule_application_overview_df": rule_application_overview_df,
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
