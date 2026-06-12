from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_float, normalize_text
from datefac.review_queue.real_excel_review_343c import (
    ALLOWED_REVIEWER_DECISIONS,
    EDITABLE_REVIEWER_COLUMNS,
    REQUIRED_CORRECT_COLUMNS,
    REQUIRED_IDENTITY_COLUMNS,
)


REVIEWER_DECISION_TO_STATUS_343D = {
    "CONFIRM": "REVIEWED_CONFIRMED",
    "CORRECT": "REVIEWED_CORRECTED",
    "REJECT": "REJECTED",
    "NEEDS_SOURCE_CHECK": "NEEDS_SOURCE_CHECK",
    "SKIP": "SKIPPED",
}

AI_ASSISTED_DISCLOSURE = (
    "filled by AI assistant from available workbook evidence; not strict pure human review"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_filled_review_row(row: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    for field in REQUIRED_IDENTITY_COLUMNS:
        if not normalize_text(row.get(field)):
            errors.append(f"missing required identity field: {field}")

    if not normalize_text(row.get("source_stage")):
        errors.append("missing required identity field: source_stage")

    for field in EDITABLE_REVIEWER_COLUMNS:
        if field not in row:
            errors.append(f"missing reviewer column: {field}")

    decision = normalize_text(row.get("reviewer_decision"))
    if not decision:
        errors.append("reviewer_decision must not be empty")
    elif decision not in ALLOWED_REVIEWER_DECISIONS:
        errors.append(f"invalid reviewer_decision: {decision}")

    if decision == "CORRECT":
        for field in REQUIRED_CORRECT_COLUMNS:
            if not normalize_text(row.get(field)):
                errors.append(f"missing correction field for CORRECT: {field}")
        if normalize_text(row.get("reviewer_value_numeric")) and normalize_float(row.get("reviewer_value_numeric")) is None:
            errors.append("reviewer_value_numeric must be numeric for CORRECT")

    if decision in {"REJECT", "NEEDS_SOURCE_CHECK"} and not normalize_text(row.get("reviewer_note")):
        errors.append(f"{decision} requires reviewer_note")

    if decision == "SKIP" and not normalize_text(row.get("reviewer_note")):
        warnings.append("SKIP should include reviewer_note when available")

    for field in ["formal_client_export_allowed", "client_ready", "production_ready"]:
        if normalize_bool(row.get(field)):
            errors.append(f"{field} must remain false")
    if not normalize_bool(row.get("not_final_confirmation", True)):
        errors.append("not_final_confirmation must remain true")
    if not normalize_bool(row.get("no_write_back_required", True)):
        errors.append("no_write_back_required must remain true")

    validation_status = "PASS"
    if errors:
        validation_status = "FAIL"
    elif warnings:
        validation_status = "PASS_WITH_WARNING"

    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "reviewer_decision": decision,
        "resulting_status": REVIEWER_DECISION_TO_STATUS_343D.get(decision, ""),
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
    }


def build_reviewed_result_row(row: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_filled_review_row(row)
    decision = validation["reviewer_decision"]
    corrected_metric = normalize_text(row.get("reviewer_metric_standardized"))
    corrected_year = normalize_text(row.get("reviewer_year_standardized"))
    corrected_value = normalize_text(row.get("reviewer_value_numeric"))
    corrected_unit = normalize_text(row.get("reviewer_normalized_unit"))

    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "source_stage": normalize_text(row.get("source_stage")),
        "source_artifact_path": normalize_text(row.get("source_artifact_path")),
        "source_artifact_sheet": normalize_text(row.get("source_artifact_sheet")),
        "source_row_id": normalize_text(row.get("source_row_id")),
        "source_detail_level": normalize_text(row.get("source_detail_level")),
        "source_pdf_id": normalize_text(row.get("source_pdf_id")),
        "metric_standardized": normalize_text(row.get("metric_standardized")),
        "year_standardized": normalize_text(row.get("year_standardized")),
        "value_numeric": normalize_text(row.get("value_numeric")),
        "normalized_unit": normalize_text(row.get("normalized_unit")),
        "reviewer_decision": decision,
        "reviewer_metric_standardized": corrected_metric,
        "reviewer_year_standardized": corrected_year,
        "reviewer_value_numeric": corrected_value,
        "reviewer_normalized_unit": corrected_unit,
        "reviewer_note": normalize_text(row.get("reviewer_note")),
        "reviewer_id": normalize_text(row.get("reviewer_id")),
        "reviewed_at": normalize_text(row.get("reviewed_at")) or utc_now(),
        "resulting_status": validation["resulting_status"],
        "validation_status": validation["validation_status"],
        "validation_errors": validation["errors"],
        "validation_warnings": validation["warnings"],
        "review_source_type": "AI_ASSISTED_REVIEW",
        "not_pure_human_review": True,
        "strict_human_review_completed": False,
        "requires_human_spot_check": True,
        "review_source_disclosure": AI_ASSISTED_DISCLOSURE,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "no_write_back_required": True,
    }


def decision_summary_rows(reviewed_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = {decision: 0 for decision in ALLOWED_REVIEWER_DECISIONS}
    status_counts = {status: 0 for status in REVIEWER_DECISION_TO_STATUS_343D.values()}
    for row in reviewed_rows:
        decision = normalize_text(row.get("reviewer_decision"))
        status = normalize_text(row.get("resulting_status"))
        if decision in counts:
            counts[decision] += 1
        if status in status_counts:
            status_counts[status] += 1
    rows: List[Dict[str, Any]] = []
    for decision in ALLOWED_REVIEWER_DECISIONS:
        rows.append(
            {
                "reviewer_decision": decision,
                "resulting_status": REVIEWER_DECISION_TO_STATUS_343D[decision],
                "row_count": counts[decision],
            }
        )
    return rows


def status_mapping_rows() -> List[Dict[str, str]]:
    return [
        {
            "reviewer_decision": decision,
            "resulting_status": status,
        }
        for decision, status in REVIEWER_DECISION_TO_STATUS_343D.items()
    ]
