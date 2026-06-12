from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from datefac.review_queue.excel_round_trip_343b import (
    normalize_bool,
    normalize_float,
    normalize_text,
)
from datefac.review_queue.spot_check_package_343f import (
    ALLOWED_SPOT_CHECK_DECISIONS,
    EDITABLE_SPOT_CHECK_COLUMNS,
)


REQUIRED_IDENTITY_COLUMNS_343G = [
    "queue_item_id",
    "review_item_id",
    "simulated_downstream_action",
    "priority_tier",
]

REQUIRED_CORRECT_COLUMNS_343G = [
    "spot_check_metric_standardized",
    "spot_check_year_standardized",
    "spot_check_value_numeric",
    "spot_check_normalized_unit",
]

SPOT_CHECK_DECISION_TO_STATUS_343G = {
    "CONFIRM_AI_ASSISTED_RESULT": "SPOT_CHECK_CONFIRMED_AI_ASSISTED",
    "CORRECT_AI_ASSISTED_RESULT": "SPOT_CHECK_CORRECTED_AI_ASSISTED",
    "REJECT_AI_ASSISTED_RESULT": "SPOT_CHECK_REJECTED_AI_ASSISTED",
    "SOURCE_CHECK_REQUIRED": "SPOT_CHECK_SOURCE_CHECK_REQUIRED",
    "KEEP_HOLD": "SPOT_CHECK_KEEP_HOLD",
    "SKIP_SPOT_CHECK": "SPOT_CHECK_SKIPPED",
}

AI_ASSISTED_SPOT_CHECK_DISCLOSURE = (
    "filled by AI assistant from available workbook evidence; "
    "not strict pure human spot-check"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_filled_spot_check_row(row: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    for field in REQUIRED_IDENTITY_COLUMNS_343G:
        if not normalize_text(row.get(field)):
            errors.append(f"missing required identity field: {field}")

    for field in EDITABLE_SPOT_CHECK_COLUMNS:
        if field not in row:
            errors.append(f"missing spot-check column: {field}")

    decision = normalize_text(row.get("spot_check_decision"))
    if not decision:
        errors.append("spot_check_decision must not be empty")
    elif decision not in ALLOWED_SPOT_CHECK_DECISIONS:
        errors.append(f"invalid spot_check_decision: {decision}")

    if decision == "CORRECT_AI_ASSISTED_RESULT":
        for field in REQUIRED_CORRECT_COLUMNS_343G:
            if not normalize_text(row.get(field)):
                errors.append(f"missing correction field for CORRECT_AI_ASSISTED_RESULT: {field}")
        corrected_value = normalize_text(row.get("spot_check_value_numeric"))
        if corrected_value and normalize_float(row.get("spot_check_value_numeric")) is None:
            errors.append("spot_check_value_numeric must be numeric for CORRECT_AI_ASSISTED_RESULT")

    note = normalize_text(row.get("spot_check_note"))
    if decision in {"REJECT_AI_ASSISTED_RESULT", "SOURCE_CHECK_REQUIRED"} and not note:
        errors.append(f"{decision} requires spot_check_note")
    if decision == "KEEP_HOLD" and not note:
        warnings.append("KEEP_HOLD should include spot_check_note when available")

    if normalize_text(row.get("review_source_type")) != "AI_ASSISTED_REVIEW":
        errors.append("review_source_type must remain AI_ASSISTED_REVIEW")
    if not normalize_bool(row.get("not_pure_human_review")):
        errors.append("not_pure_human_review must remain true")
    if normalize_bool(row.get("strict_human_review_completed")):
        errors.append("strict_human_review_completed must remain false")
    if "requires_human_spot_check" in row and not normalize_bool(row.get("requires_human_spot_check")):
        errors.append("requires_human_spot_check must remain true")
    if normalize_text(row.get("apply_mode")) != "SIMULATION_ONLY":
        errors.append("apply_mode must remain SIMULATION_ONLY")

    for field in ["formal_client_export_allowed", "client_ready", "production_ready"]:
        if normalize_bool(row.get(field)):
            errors.append(f"{field} must remain false")

    validation_status = "PASS"
    if errors:
        validation_status = "FAIL"
    elif warnings:
        validation_status = "PASS_WITH_WARNING"

    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "spot_check_decision": decision,
        "resulting_spot_check_status": SPOT_CHECK_DECISION_TO_STATUS_343G.get(decision, ""),
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
    }


def build_spot_check_result_row(row: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_filled_spot_check_row(row)
    decision = validation["spot_check_decision"]
    final_metric = normalize_text(row.get("spot_check_metric_standardized")) or normalize_text(row.get("metric_standardized"))
    final_year = normalize_text(row.get("spot_check_year_standardized")) or normalize_text(row.get("year_standardized"))
    final_value = normalize_text(row.get("spot_check_value_numeric")) or normalize_text(row.get("value_numeric"))
    final_unit = normalize_text(row.get("spot_check_normalized_unit")) or normalize_text(row.get("normalized_unit"))

    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "resulting_status": normalize_text(row.get("resulting_status")),
        "simulated_downstream_action": normalize_text(row.get("simulated_downstream_action")),
        "apply_eligibility_classification": normalize_text(row.get("apply_eligibility_classification")),
        "priority_tier": normalize_text(row.get("priority_tier")),
        "recommended_spot_check_decision": normalize_text(row.get("recommended_spot_check_decision")),
        "metric_standardized": normalize_text(row.get("metric_standardized")),
        "year_standardized": normalize_text(row.get("year_standardized")),
        "value_numeric": normalize_text(row.get("value_numeric")),
        "normalized_unit": normalize_text(row.get("normalized_unit")),
        "spot_check_decision": decision,
        "spot_check_metric_standardized": normalize_text(row.get("spot_check_metric_standardized")),
        "spot_check_year_standardized": normalize_text(row.get("spot_check_year_standardized")),
        "spot_check_value_numeric": normalize_text(row.get("spot_check_value_numeric")),
        "spot_check_normalized_unit": normalize_text(row.get("spot_check_normalized_unit")),
        "spot_check_note": normalize_text(row.get("spot_check_note")),
        "spot_checker_id": normalize_text(row.get("spot_checker_id")),
        "spot_checked_at": normalize_text(row.get("spot_checked_at")) or utc_now(),
        "resulting_spot_check_status": validation["resulting_spot_check_status"],
        "final_metric_standardized": final_metric,
        "final_year_standardized": final_year,
        "final_value_numeric": final_value,
        "final_normalized_unit": final_unit,
        "validation_status": validation["validation_status"],
        "validation_errors": validation["errors"],
        "validation_warnings": validation["warnings"],
        "review_source_type": "AI_ASSISTED_REVIEW",
        "spot_check_source_type": "AI_ASSISTED_SPOT_CHECK",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "requires_strict_human_review": True,
        "apply_mode": "SIMULATION_ONLY",
        "spot_check_source_disclosure": AI_ASSISTED_SPOT_CHECK_DISCLOSURE,
        "spot_check_result_ingested": True,
        "ai_assisted_spot_check_completed": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "no_write_back_required": True,
    }


def decision_summary_rows(result_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = {decision: 0 for decision in ALLOWED_SPOT_CHECK_DECISIONS}
    status_counts = {status: 0 for status in SPOT_CHECK_DECISION_TO_STATUS_343G.values()}
    for row in result_rows:
        decision = normalize_text(row.get("spot_check_decision"))
        status = normalize_text(row.get("resulting_spot_check_status"))
        if decision in counts:
            counts[decision] += 1
        if status in status_counts:
            status_counts[status] += 1
    rows: List[Dict[str, Any]] = []
    for decision in ALLOWED_SPOT_CHECK_DECISIONS:
        rows.append(
            {
                "spot_check_decision": decision,
                "resulting_spot_check_status": SPOT_CHECK_DECISION_TO_STATUS_343G[decision],
                "row_count": counts[decision],
            }
        )
    return rows


def status_mapping_rows() -> List[Dict[str, str]]:
    return [
        {
            "spot_check_decision": decision,
            "resulting_spot_check_status": status,
        }
        for decision, status in SPOT_CHECK_DECISION_TO_STATUS_343G.items()
    ]
