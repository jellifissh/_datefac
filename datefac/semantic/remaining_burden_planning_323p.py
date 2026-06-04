from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


EXPECTED_323O_DECISION = "OFFICIAL_SEMANTIC_PATCH_CYCLE_323O_CLOSED_READY_FOR_NEXT_CYCLE_PLANNING"
EXPECTED_323N_DECISION = "POST_PATCH_REGRESSION_VALIDATION_323N_READY_WITH_WARNINGS"
EXPECTED_322O_DECISION = "POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE"
EXPECTED_323A_DECISION = "HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_READY_FOR_323B_OR_323A_ADJUDICATION_BATCH_PREP"
EXPECTED_323AR_DECISION = "CANDIDATE_TEXT_REPAIR_323AR_READY_FOR_ADJUDICATION_BATCH_PREP"
EXPECTED_323P_DECISION = "REMAINING_BURDEN_PLANNING_323P_READY_FOR_NEXT_CYCLE_DECISION"
EXPECTED_323P_NOT_READY = "REMAINING_BURDEN_PLANNING_323P_NOT_READY"

DEFAULT_CLOSURE_323O_DIR = Path(r"D:\_datefac\output\official_semantic_patch_cycle_closure_323o")
DEFAULT_REFERENCE_323N_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_323n")
DEFAULT_REFERENCE_322O_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_322o")
DEFAULT_TRUST_SPLIT_322B2_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_MINING_323A_DIR = Path(r"D:\_datefac\output\high_impact_semantic_candidates_mining_323a")
DEFAULT_REPAIR_323AR_DIR = Path(r"D:\_datefac\output\candidate_text_repair_323ar")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\remaining_burden_planning_323p")

EXPECTED_COUNTS = {
    "official_rule_count_total": 16,
    "trusted_gain_total": 93,
    "review_reduction_total": 416,
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def load_remaining_burden_planning_323p_inputs(
    closure_323o_dir: Path,
    reference_323n_dir: Path,
    reference_322o_dir: Path,
    trust_split_322b2_dir: Path,
    mining_323a_dir: Path,
    repair_323ar_dir: Path,
) -> Dict[str, Any]:
    return {
        "closure_323o_summary": _read_json(
            closure_323o_dir / "official_semantic_patch_cycle_closure_323o_summary.json"
        ),
        "summary_323n": _read_json(
            reference_323n_dir / "post_patch_regression_validation_323n_summary.json"
        ),
        "summary_322o": _read_json(
            reference_322o_dir / "post_patch_regression_validation_322o_summary.json"
        ),
        "summary_322b2": _read_json(
            trust_split_322b2_dir / "router_mineru_trust_split_322b2_summary.json"
        ),
        "summary_323a": _read_json(
            mining_323a_dir / "high_impact_semantic_candidates_mining_323a_summary.json"
        ),
        "summary_323ar": _read_json(
            repair_323ar_dir / "candidate_text_repair_323ar_summary.json"
        ),
    }


def _build_option_rows(
    summary_323n: Dict[str, Any],
    summary_323a: Dict[str, Any],
    summary_323ar: Dict[str, Any],
) -> List[Dict[str, Any]]:
    historical_duplicate_warning = _norm(summary_323n.get("decision")) == EXPECTED_323N_DECISION
    duplicate_cleanup_count = _safe_int(summary_323n.get("current_duplicate_count"))

    return [
        {
            "option_name": "alias_candidates",
            "total_group_count": _safe_int(summary_323a.get("alias_opportunity_group_count")),
            "review_ready_group_count": _safe_int(summary_323ar.get("review_ready_alias_count")),
            "safety_level": "MEDIUM",
            "impact_level": "HIGH",
            "readiness": "READY_AFTER_EXTRA_GATING",
            "key_evidence": "largest review-ready pool after 323A-R, but high-priority examples still include risky 其中-prefixed labels",
            "why_not_primary": "higher upside than scope, but lower safety because alias overreach can create incorrect trusted promotion pressure",
            "recommended_rank": 2,
        },
        {
            "option_name": "scope_noise_candidates",
            "total_group_count": _safe_int(summary_323a.get("scope_noise_group_count")),
            "review_ready_group_count": _safe_int(summary_323ar.get("review_ready_scope_count")),
            "safety_level": "HIGH",
            "impact_level": "MEDIUM",
            "readiness": "READY_NOW",
            "key_evidence": "small but review-ready pool, and 322/323 already proved out-of-scope closure path can safely reduce review burden",
            "why_not_primary": "",
            "recommended_rank": 1,
        },
        {
            "option_name": "unit_related_holdout",
            "total_group_count": _safe_int(summary_323a.get("unit_related_group_count")),
            "review_ready_group_count": 0,
            "safety_level": "LOW",
            "impact_level": "MEDIUM",
            "readiness": "NOT_READY",
            "key_evidence": "large holdout inventory but still blocked by unit reasoning and deterministic interpretation gaps",
            "why_not_primary": "too much unresolved unit semantics for a safe next official patch cycle",
            "recommended_rank": 4,
        },
        {
            "option_name": "ambiguous_holdout",
            "total_group_count": _safe_int(summary_323a.get("ambiguous_group_count")),
            "review_ready_group_count": 0,
            "safety_level": "LOW",
            "impact_level": "LOW",
            "readiness": "NOT_READY",
            "key_evidence": "ambiguity holdouts remain broad and should not be promoted without stronger deterministic evidence",
            "why_not_primary": "lowest safety and lowest immediate conversion readiness",
            "recommended_rank": 5,
        },
        {
            "option_name": "duplicate_cleanup",
            "total_group_count": duplicate_cleanup_count,
            "review_ready_group_count": duplicate_cleanup_count if historical_duplicate_warning else 0,
            "safety_level": "HIGH",
            "impact_level": "LOW",
            "readiness": "MAINTENANCE_ONLY",
            "key_evidence": "323N warning is historical duplicates unchanged only, with zero new duplicate delta",
            "why_not_primary": "good hygiene work but not the highest-impact semantic extraction direction",
            "recommended_rank": 3,
        },
    ]


def build_remaining_burden_planning_323p(
    closure_323o_summary: Dict[str, Any],
    summary_323n: Dict[str, Any],
    summary_322o: Dict[str, Any],
    summary_322b2: Dict[str, Any],
    summary_323a: Dict[str, Any],
    summary_323ar: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::323o_closed",
        "PASS" if _norm(closure_323o_summary.get("decision")) == EXPECTED_323O_DECISION else "FAIL",
        _norm(closure_323o_summary.get("decision")),
    )
    add_qa(
        "readiness::323o_qa_fail_count",
        "PASS" if _safe_int(closure_323o_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(closure_323o_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323n_ready_with_warning_only",
        "PASS" if _norm(summary_323n.get("decision")) == EXPECTED_323N_DECISION else "FAIL",
        _norm(summary_323n.get("decision")),
    )
    add_qa(
        "readiness::323n_qa_fail_count",
        "PASS" if _safe_int(summary_323n.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_323n.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::322o_closed",
        "PASS" if _norm(summary_322o.get("decision")) == EXPECTED_322O_DECISION else "FAIL",
        _norm(summary_322o.get("decision")),
    )
    add_qa(
        "readiness::322o_qa_fail_count",
        "PASS" if _safe_int(summary_322o.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_322o.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323a_ready",
        "PASS" if _norm(summary_323a.get("decision")) == EXPECTED_323A_DECISION else "FAIL",
        _norm(summary_323a.get("decision")),
    )
    add_qa(
        "readiness::323ar_ready",
        "PASS" if _norm(summary_323ar.get("decision")) == EXPECTED_323AR_DECISION else "FAIL",
        _norm(summary_323ar.get("decision")),
    )

    official_rule_count_total = _safe_int(closure_323o_summary.get("combined_rules"))
    trusted_gain_total = _safe_int(closure_323o_summary.get("combined_trusted_gain"))
    review_reduction_total = _safe_int(closure_323o_summary.get("combined_review_reduction"))

    add_qa(
        "closed_cycle::official_rule_count_total",
        "PASS" if official_rule_count_total == EXPECTED_COUNTS["official_rule_count_total"] else "FAIL",
        f"expected={EXPECTED_COUNTS['official_rule_count_total']} actual={official_rule_count_total}",
    )
    add_qa(
        "closed_cycle::trusted_gain_total",
        "PASS" if trusted_gain_total == EXPECTED_COUNTS["trusted_gain_total"] else "FAIL",
        f"expected={EXPECTED_COUNTS['trusted_gain_total']} actual={trusted_gain_total}",
    )
    add_qa(
        "closed_cycle::review_reduction_total",
        "PASS" if review_reduction_total == EXPECTED_COUNTS["review_reduction_total"] else "FAIL",
        f"expected={EXPECTED_COUNTS['review_reduction_total']} actual={review_reduction_total}",
    )

    # Use the latest explicit global remaining-burden metrics available in the provided summaries.
    remaining_unknown_metric_candidate_count = _safe_int(
        summary_322o.get("remaining_unknown_metric_candidate_count")
    )
    remaining_unit_unknown_candidate_count = _safe_int(
        summary_322o.get("remaining_unit_unknown_candidate_count")
    )
    remaining_manual_review_count = _safe_int(summary_322o.get("remaining_manual_review_count"))
    historical_duplicate_warning_status = (
        "historical duplicates unchanged only"
        if _safe_int(summary_323n.get("qa_warn_count")) > 0
        and _safe_int(summary_323n.get("new_duplicate_delta_count")) == 0
        else "none"
    )

    add_qa(
        "remaining_burden::unknown_metric_candidate_count_present",
        "PASS" if remaining_unknown_metric_candidate_count > 0 else "FAIL",
        str(remaining_unknown_metric_candidate_count),
    )
    add_qa(
        "remaining_burden::unit_unknown_candidate_count_present",
        "PASS" if remaining_unit_unknown_candidate_count >= 0 else "FAIL",
        str(remaining_unit_unknown_candidate_count),
    )
    add_qa(
        "remaining_burden::manual_review_count_present",
        "PASS" if remaining_manual_review_count > 0 else "FAIL",
        str(remaining_manual_review_count),
    )
    add_qa(
        "remaining_burden::historical_duplicate_warning_status",
        "PASS" if historical_duplicate_warning_status == "historical duplicates unchanged only" else "FAIL",
        historical_duplicate_warning_status,
    )

    option_rows = _build_option_rows(
        summary_323n=summary_323n,
        summary_323a=summary_323a,
        summary_323ar=summary_323ar,
    )
    option_df = pd.DataFrame(option_rows).fillna("").sort_values("recommended_rank").reset_index(drop=True)

    primary_row = option_df.iloc[0].to_dict() if not option_df.empty else {}
    secondary_row = option_df.iloc[1].to_dict() if len(option_df) > 1 else {}

    primary_direction = _norm(primary_row.get("option_name"))
    secondary_direction = _norm(secondary_row.get("option_name"))

    add_qa(
        "recommendation::primary_direction_selected",
        "PASS" if primary_direction == "scope_noise_candidates" else "FAIL",
        primary_direction,
    )
    add_qa(
        "recommendation::secondary_direction_selected",
        "PASS" if secondary_direction == "alias_candidates" else "FAIL",
        secondary_direction,
    )
    add_qa(
        "recommendation::primary_ready_now",
        "PASS" if _norm(primary_row.get("readiness")) == "READY_NOW" else "FAIL",
        _norm(primary_row.get("readiness")),
    )

    remaining_burden_df = pd.DataFrame(
        [
            {
                "metric_name": "remaining_unknown_metric_candidate_count",
                "value": remaining_unknown_metric_candidate_count,
                "source_stage": "322O",
                "note": "latest explicit post-patch global remaining burden count available in provided summaries",
            },
            {
                "metric_name": "remaining_unit_unknown_candidate_count",
                "value": remaining_unit_unknown_candidate_count,
                "source_stage": "322O",
                "note": "latest explicit post-patch global remaining burden count available in provided summaries",
            },
            {
                "metric_name": "remaining_manual_review_count",
                "value": remaining_manual_review_count,
                "source_stage": "322O",
                "note": "latest explicit post-patch global remaining burden count available in provided summaries",
            },
            {
                "metric_name": "historical_duplicate_warning_status",
                "value": historical_duplicate_warning_status,
                "source_stage": "323N",
                "note": "warning-only because new duplicate delta stayed at zero",
            },
        ]
    ).fillna("")

    cycle_summary_df = pd.DataFrame(
        [
            {
                "official_rule_count_total": official_rule_count_total,
                "trusted_gain_total": trusted_gain_total,
                "review_reduction_total": review_reduction_total,
                "unknown_metric_candidate_count_baseline_322b2": _safe_int(summary_322b2.get("unknown_metric_candidate_count")),
                "manual_review_count_baseline_322b2": _safe_int(summary_322b2.get("review_required_total_after_322b2")),
                "warning_323": historical_duplicate_warning_status,
            }
        ]
    ).fillna("")

    recommendation_df = pd.DataFrame(
        [
            {
                "recommendation_type": "primary",
                "direction": primary_direction,
                "safety_level": _norm(primary_row.get("safety_level")),
                "impact_level": _norm(primary_row.get("impact_level")),
                "rationale": "best safety-to-impact tradeoff for the next cycle because the pool is small, review-ready, and already aligned with successful 322/323 scope closure patterns",
            },
            {
                "recommendation_type": "secondary",
                "direction": secondary_direction,
                "safety_level": _norm(secondary_row.get("safety_level")),
                "impact_level": _norm(secondary_row.get("impact_level")),
                "rationale": "highest remaining upside after additional gating, but should stay secondary because alias overreach risk is materially higher than scope noise",
            },
        ]
    ).fillna("")

    caution_rows = [
        {
            "caution": "do_not_start_next_cycle_yet",
            "detail": "323P is a planning stage only and intentionally does not open, adjudicate, or apply a new semantic cycle.",
        },
        {
            "caution": "duplicate_cleanup_is_maintenance",
            "detail": "historical duplicate cleanup is worth tracking, but it should not displace safer review-reduction work as the main cycle goal.",
        },
    ]
    caution_df = pd.DataFrame(caution_rows).fillna("")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "323P",
        "output_dir": str(output_dir),
        "official_rule_count_total": official_rule_count_total,
        "trusted_gain_total": trusted_gain_total,
        "review_reduction_total": review_reduction_total,
        "remaining_unknown_metric_candidate_count": remaining_unknown_metric_candidate_count,
        "remaining_unit_unknown_candidate_count": remaining_unit_unknown_candidate_count,
        "remaining_manual_review_count": remaining_manual_review_count,
        "historical_duplicate_warning_status": historical_duplicate_warning_status,
        "alias_candidate_group_count": _safe_int(summary_323a.get("alias_opportunity_group_count")),
        "scope_noise_candidate_group_count": _safe_int(summary_323a.get("scope_noise_group_count")),
        "unit_related_holdout_group_count": _safe_int(summary_323a.get("unit_related_group_count")),
        "ambiguous_holdout_group_count": _safe_int(summary_323a.get("ambiguous_group_count")),
        "duplicate_cleanup_candidate_count": _safe_int(summary_323n.get("current_duplicate_count")),
        "review_ready_alias_count": _safe_int(summary_323ar.get("review_ready_alias_count")),
        "review_ready_scope_count": _safe_int(summary_323ar.get("review_ready_scope_count")),
        "primary_next_cycle_direction": primary_direction,
        "secondary_next_cycle_direction": secondary_direction,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_323P_DECISION if qa_fail_count == 0 else EXPECTED_323P_NOT_READY,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    decision_json = {
        "decision": summary["decision"],
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "primary_next_cycle_direction": primary_direction,
        "secondary_next_cycle_direction": secondary_direction,
        "do_not_start_next_cycle_yet": True,
    }
    planning_json = {
        "closed_cycle_impact": cycle_summary_df.iloc[0].to_dict() if not cycle_summary_df.empty else {},
        "remaining_burden_summary": remaining_burden_df.to_dict(orient="records"),
        "option_comparison": option_df.to_dict(orient="records"),
        "recommendations": recommendation_df.to_dict(orient="records"),
        "cautions": caution_df.to_dict(orient="records"),
    }

    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "summary_only_planning",
                "detail": "323P compares next-cycle directions using only the existing summary artifacts and does not reopen candidate-level adjudication batches.",
            },
            {
                "limitation": "remaining_burden_count_source",
                "detail": "global remaining-burden counts come from the latest explicit post-patch summary available in the provided inputs, while 323A/323A-R contribute directional opportunity evidence.",
            },
        ]
    ).fillna("")

    return {
        "summary": summary,
        "qa_json": qa_json,
        "decision_json": decision_json,
        "planning_json": planning_json,
        "cycle_summary_df": cycle_summary_df,
        "remaining_burden_df": remaining_burden_df,
        "option_comparison_df": option_df,
        "recommendation_df": recommendation_df,
        "caution_df": caution_df,
        "qa_checks_df": qa_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
    }
