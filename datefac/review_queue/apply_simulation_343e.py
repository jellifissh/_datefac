from __future__ import annotations

from typing import Any, Dict, List

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text


SIM_ACTION_BY_STATUS = {
    "REVIEWED_CONFIRMED": "SIMULATE_CONFIRM_APPLY",
    "REVIEWED_CORRECTED": "SIMULATE_CORRECTION_APPLY",
    "REJECTED": "HOLD_REJECTED",
    "NEEDS_SOURCE_CHECK": "HOLD_SOURCE_CHECK_REQUIRED",
    "SKIPPED": "HOLD_SKIPPED",
}

APPLY_MODE = "SIMULATION_ONLY"


def validate_reviewed_result_row(row: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    for field in [
        "queue_item_id",
        "review_item_id",
        "reviewer_decision",
        "resulting_status",
        "review_source_type",
        "not_pure_human_review",
        "strict_human_review_completed",
        "requires_human_spot_check",
    ]:
        if field not in row or normalize_text(row.get(field)) == "":
            errors.append(f"missing required reviewed-result field: {field}")

    if normalize_text(row.get("review_source_type")) != "AI_ASSISTED_REVIEW":
        errors.append("review_source_type must remain AI_ASSISTED_REVIEW")
    if not normalize_bool(row.get("not_pure_human_review")):
        errors.append("not_pure_human_review must remain true")
    if normalize_bool(row.get("strict_human_review_completed")):
        errors.append("strict_human_review_completed must remain false")
    if not normalize_bool(row.get("requires_human_spot_check")):
        errors.append("requires_human_spot_check must remain true")

    for field in ["formal_client_export_allowed", "client_ready", "production_ready"]:
        if normalize_bool(row.get(field)):
            errors.append(f"{field} must remain false")

    status = normalize_text(row.get("resulting_status"))
    if status not in SIM_ACTION_BY_STATUS:
        errors.append(f"unsupported resulting_status for simulation: {status}")

    validation_status = "PASS"
    if errors:
        validation_status = "FAIL"
    elif warnings:
        validation_status = "PASS_WITH_WARNING"

    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "resulting_status": status,
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
    }


def build_apply_plan_row(row: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_reviewed_result_row(row)
    status = validation["resulting_status"]
    action = SIM_ACTION_BY_STATUS.get(status, "HOLD_UNSUPPORTED")
    is_apply_candidate = action in {"SIMULATE_CONFIRM_APPLY", "SIMULATE_CORRECTION_APPLY"}
    risk_notes: List[str] = []
    if normalize_bool(row.get("requires_human_spot_check")):
        risk_notes.append("human spot-check still required")
    if status == "NEEDS_SOURCE_CHECK":
        risk_notes.append("source check required before stronger trust claim")
    if status == "SKIPPED":
        risk_notes.append("row intentionally unresolved in current batch")
    if status == "REJECTED":
        risk_notes.append("rejected row must not be carried into simulated apply sidecar")

    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "reviewer_decision": normalize_text(row.get("reviewer_decision")),
        "resulting_status": status,
        "simulated_downstream_action": action,
        "apply_eligibility_classification": "SIMULATION_ELIGIBLE" if is_apply_candidate else "HOLD_ONLY",
        "apply_mode": APPLY_MODE,
        "review_source_type": "AI_ASSISTED_REVIEW",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "not_formal_export": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "risk_notes": risk_notes,
        "validation_status": validation["validation_status"],
        "validation_errors": validation["errors"],
        "validation_warnings": validation["warnings"],
        "no_write_back_required": True,
    }


def build_simulated_sidecar_row(plan_row: Dict[str, Any], source_row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "queue_item_id": plan_row["queue_item_id"],
        "review_item_id": plan_row["review_item_id"],
        "metric_standardized": normalize_text(source_row.get("reviewer_metric_standardized")) or normalize_text(source_row.get("metric_standardized")),
        "year_standardized": normalize_text(source_row.get("reviewer_year_standardized")) or normalize_text(source_row.get("year_standardized")),
        "value_numeric": normalize_text(source_row.get("reviewer_value_numeric")) or normalize_text(source_row.get("value_numeric")),
        "normalized_unit": normalize_text(source_row.get("reviewer_normalized_unit")) or normalize_text(source_row.get("normalized_unit")),
        "simulated_downstream_action": plan_row["simulated_downstream_action"],
        "apply_mode": APPLY_MODE,
        "review_source_type": "AI_ASSISTED_REVIEW",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "not_formal_export": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "no_write_back_required": True,
    }


def build_audit_gate(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "apply_mode": APPLY_MODE,
        "audit_gate_passed_for_spot_check_package": bool(summary.get("apply_simulation_completed")),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "review_source_type": "AI_ASSISTED_REVIEW",
        "decision": summary.get("decision", ""),
    }


def build_risk_register(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    risks = [
        {
            "risk_id": "ai_assisted_review_source",
            "severity": "HIGH",
            "risk": "Reviewed result comes from AI-assisted review, not strict pure human review.",
        },
        {
            "risk_id": "human_spot_check_required",
            "severity": "HIGH",
            "risk": "Human spot-check remains required before stronger downstream trust claims.",
        },
    ]
    if int(summary.get("hold_source_check_required_count", 0)) > 0:
        risks.append(
            {
                "risk_id": "source_check_backlog",
                "severity": "HIGH",
                "risk": f"{summary.get('hold_source_check_required_count', 0)} rows still require source check.",
            }
        )
    if int(summary.get("hold_skipped_count", 0)) > 0:
        risks.append(
            {
                "risk_id": "skipped_rows",
                "severity": "MEDIUM",
                "risk": f"{summary.get('hold_skipped_count', 0)} rows remain skipped and unresolved.",
            }
        )
    return risks
