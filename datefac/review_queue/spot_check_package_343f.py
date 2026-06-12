from __future__ import annotations

from typing import Any, Dict, List

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text


ALLOWED_SPOT_CHECK_DECISIONS = [
    "CONFIRM_AI_ASSISTED_RESULT",
    "CORRECT_AI_ASSISTED_RESULT",
    "REJECT_AI_ASSISTED_RESULT",
    "SOURCE_CHECK_REQUIRED",
    "KEEP_HOLD",
    "SKIP_SPOT_CHECK",
]

EDITABLE_SPOT_CHECK_COLUMNS = [
    "spot_check_decision",
    "spot_check_metric_standardized",
    "spot_check_year_standardized",
    "spot_check_value_numeric",
    "spot_check_normalized_unit",
    "spot_check_note",
    "spot_checker_id",
    "spot_checked_at",
]

PRIORITY_BY_ACTION = {
    "HOLD_SOURCE_CHECK_REQUIRED": "P0_SOURCE_CHECK_REQUIRED",
    "SIMULATE_CONFIRM_APPLY": "P1_AI_ASSISTED_SIM_APPLIED",
    "SIMULATE_CORRECTION_APPLY": "P1_AI_ASSISTED_SIM_APPLIED",
    "HOLD_SKIPPED": "P2_SKIPPED_OR_AMBIGUOUS",
}


def validate_apply_plan_row(row: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    for field in [
        "queue_item_id",
        "review_item_id",
        "simulated_downstream_action",
        "review_source_type",
        "not_pure_human_review",
        "strict_human_review_completed",
        "requires_human_spot_check",
        "apply_mode",
    ]:
        if field not in row or normalize_text(row.get(field)) == "":
            errors.append(f"missing required apply-plan field: {field}")
    if normalize_text(row.get("review_source_type")) != "AI_ASSISTED_REVIEW":
        errors.append("review_source_type must remain AI_ASSISTED_REVIEW")
    if not normalize_bool(row.get("not_pure_human_review")):
        errors.append("not_pure_human_review must remain true")
    if normalize_bool(row.get("strict_human_review_completed")):
        errors.append("strict_human_review_completed must remain false")
    if not normalize_bool(row.get("requires_human_spot_check")):
        errors.append("requires_human_spot_check must remain true")
    if normalize_text(row.get("apply_mode")) != "SIMULATION_ONLY":
        errors.append("apply_mode must remain SIMULATION_ONLY")
    for field in ["formal_client_export_allowed", "client_ready", "production_ready"]:
        if normalize_bool(row.get(field)):
            errors.append(f"{field} must remain false")
    return {
        "validation_status": "FAIL" if errors else "PASS",
        "errors": errors,
    }


def recommended_spot_check_decision(action: str) -> str:
    if action == "HOLD_SOURCE_CHECK_REQUIRED":
        return "SOURCE_CHECK_REQUIRED"
    if action in {"SIMULATE_CONFIRM_APPLY", "SIMULATE_CORRECTION_APPLY"}:
        return "CONFIRM_AI_ASSISTED_RESULT"
    if action == "HOLD_SKIPPED":
        return "KEEP_HOLD"
    if action == "HOLD_REJECTED":
        return "KEEP_HOLD"
    return "SKIP_SPOT_CHECK"


def build_spot_check_item(row: Dict[str, Any]) -> Dict[str, Any]:
    action = normalize_text(row.get("simulated_downstream_action"))
    priority_tier = PRIORITY_BY_ACTION.get(action, "P3_AUDIT_BOUNDARY_ONLY")
    item = dict(row)
    item["priority_tier"] = priority_tier
    item["recommended_spot_check_decision"] = recommended_spot_check_decision(action)
    for field in EDITABLE_SPOT_CHECK_COLUMNS:
        item[field] = ""
    item["waiting_for_spot_check"] = True
    item["spot_check_result_ingested"] = False
    item["formal_client_export_allowed"] = False
    item["client_ready"] = False
    item["production_ready"] = False
    return item


def build_source_check_todo_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "metric_standardized": normalize_text(row.get("metric_standardized")),
        "year_standardized": normalize_text(row.get("year_standardized")),
        "value_numeric": normalize_text(row.get("value_numeric")),
        "normalized_unit": normalize_text(row.get("normalized_unit")),
        "source_stage": normalize_text(row.get("source_stage")),
        "source_artifact_path": normalize_text(row.get("source_artifact_path")),
        "source_artifact_sheet": normalize_text(row.get("source_artifact_sheet")),
        "source_row_id": normalize_text(row.get("source_row_id")),
        "reason_for_source_check": "HOLD_SOURCE_CHECK_REQUIRED from AI-assisted review apply simulation",
        "suggested_reviewer_action": "SOURCE_CHECK_REQUIRED",
        "review_source_type": "AI_ASSISTED_REVIEW",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "apply_mode": "SIMULATION_ONLY",
        "no_write_back_required": True,
    }


def build_expected_import_contract(output_dir_hint: str) -> Dict[str, Any]:
    return {
        "contract_version": "343F.ai_assisted_spot_check.v1",
        "required_sheet_name": "04_REVIEW_TEMPLATE",
        "required_identity_columns": [
            "queue_item_id",
            "review_item_id",
            "simulated_downstream_action",
            "priority_tier",
        ],
        "editable_spot_check_columns": EDITABLE_SPOT_CHECK_COLUMNS,
        "allowed_spot_check_decisions": ALLOWED_SPOT_CHECK_DECISIONS,
        "correction_required_columns": [
            "spot_check_metric_standardized",
            "spot_check_year_standardized",
            "spot_check_value_numeric",
            "spot_check_normalized_unit",
        ],
        "expected_input_path_pattern": "D:/_datefac/input/review_queue_spot_check_package_343f_filled/*.xlsx",
        "waiting_for_spot_check": True,
        "spot_check_result_ingested": False,
        "recommended_output_dir_hint": output_dir_hint,
    }


def priority_plan_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for item in items:
        tier = normalize_text(item.get("priority_tier"))
        counts[tier] = counts.get(tier, 0) + 1
    rows: List[Dict[str, Any]] = []
    for tier in [
        "P0_SOURCE_CHECK_REQUIRED",
        "P1_AI_ASSISTED_SIM_APPLIED",
        "P2_SKIPPED_OR_AMBIGUOUS",
        "P3_AUDIT_BOUNDARY_ONLY",
    ]:
        rows.append({"priority_tier": tier, "row_count": counts.get(tier, 0)})
    return rows
