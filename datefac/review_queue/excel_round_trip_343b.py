from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


REVIEWER_DECISION_TO_STATUS = {
    "CONFIRM": "REVIEWED_CONFIRMED",
    "CORRECT": "REVIEWED_CORRECTED",
    "REJECT": "REJECTED",
    "NEEDS_SOURCE_CHECK": "NEEDS_SOURCE_CHECK",
    "ESCALATE": "NEEDS_ESCALATION",
    "SKIP": "SKIPPED",
}

REVIEW_SAFE_COLUMN_ORDER = [
    "queue_item_id",
    "review_item_id",
    "source_stage",
    "source_commit_sha",
    "source_artifact_path",
    "source_artifact_sheet",
    "source_row_id",
    "source_detail_level",
    "source_pdf_id",
    "page_number",
    "table_id",
    "bbox",
    "image_path",
    "source_html_snippet",
    "source_text_snippet",
    "metric_standardized",
    "year_standardized",
    "value_numeric",
    "normalized_unit",
    "original_metric_standardized",
    "original_normalized_unit",
    "correction_pattern",
    "correction_reason",
    "data_trust_level",
    "audit_label",
    "preview_source_type",
    "risk_level",
    "risk_tags",
    "queue_reason_code",
    "confidence_score",
    "collision_group_id",
    "requires_disclaimer",
    "requires_later_audit",
    "formal_client_export_allowed",
    "client_ready",
    "production_ready",
    "not_final_confirmation",
    "review_status",
    "review_priority",
    "assigned_reviewer_id",
    "reviewer_decision",
    "reviewer_metric_standardized",
    "reviewer_year_standardized",
    "reviewer_value_numeric",
    "reviewer_normalized_unit",
    "reviewer_note",
    "reviewed_at",
    "review_round",
    "no_write_back_required",
    "audit_log_ref",
]

HAPPY_PATH_DECISION_CYCLE = [
    "CONFIRM",
    "CORRECT",
    "REJECT",
    "NEEDS_SOURCE_CHECK",
    "SKIP",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = normalize_text(value).casefold()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    return bool(value)


def normalize_float(value: Any) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return float(value)
    except Exception:
        try:
            return float(text)
        except Exception:
            return None


def export_template_columns(excel_template_spec: Dict[str, Any]) -> List[str]:
    available = {column["column_name"] for column in excel_template_spec.get("columns", [])}
    return [column for column in REVIEW_SAFE_COLUMN_ORDER if column in available]


def build_review_template_rows(
    sample_items: List[Dict[str, Any]],
    *,
    excel_template_spec: Dict[str, Any],
) -> List[Dict[str, Any]]:
    columns = export_template_columns(excel_template_spec)
    rows: List[Dict[str, Any]] = []
    for item in sample_items:
        row = {column: item.get(column, "") for column in columns}
        row["review_status"] = normalize_text(row.get("review_status")) or "QUEUED"
        row["review_priority"] = normalize_text(row.get("review_priority")) or "P2_STANDARD_REVIEW"
        row["assigned_reviewer_id"] = ""
        row["reviewer_decision"] = ""
        row["reviewer_metric_standardized"] = ""
        row["reviewer_year_standardized"] = ""
        row["reviewer_value_numeric"] = ""
        row["reviewer_normalized_unit"] = ""
        row["reviewer_note"] = ""
        row["reviewed_at"] = ""
        rows.append(row)
    return rows


def _corrected_payload(row: Dict[str, Any], row_index: int) -> Dict[str, Any]:
    metric = normalize_text(row.get("metric_standardized"))
    year = normalize_text(row.get("year_standardized"))
    unit = normalize_text(row.get("normalized_unit"))
    value = normalize_float(row.get("value_numeric"))
    corrected_value = value + 0.01 if value is not None else 0.01
    corrected_metric = metric
    corrected_year = year
    corrected_unit = unit
    if "SIMULATED_CORRECTION" in normalize_text(row.get("data_trust_level")) and normalize_text(row.get("original_metric_standardized")):
        corrected_metric = normalize_text(row.get("metric_standardized"))
    if metric == "EPS" and unit:
        corrected_unit = unit
    if row_index % 2 == 0 and corrected_year.endswith("A"):
        corrected_year = corrected_year
    return {
        "reviewer_metric_standardized": corrected_metric,
        "reviewer_year_standardized": corrected_year,
        "reviewer_value_numeric": corrected_value,
        "reviewer_normalized_unit": corrected_unit,
    }


def build_import_simulation_rows(template_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(template_rows):
        simulated = dict(row)
        simulated["assigned_reviewer_id"] = f"pilot_reviewer_{(index % 3) + 1}"
        simulated["review_status"] = "IN_REVIEW"
        if normalize_text(simulated.get("source_detail_level")) == "SUMMARY_DERIVED":
            decision = "NEEDS_SOURCE_CHECK"
        else:
            decision = HAPPY_PATH_DECISION_CYCLE[index % len(HAPPY_PATH_DECISION_CYCLE)]
        simulated["reviewer_decision"] = decision
        simulated["reviewer_note"] = f"343B deterministic import simulation decision={decision.lower()}"
        simulated["reviewed_at"] = f"2026-06-12T00:{index:02d}:00+00:00"
        if decision == "CORRECT":
            simulated.update(_corrected_payload(simulated, index))
        else:
            simulated["reviewer_metric_standardized"] = ""
            simulated["reviewer_year_standardized"] = ""
            simulated["reviewer_value_numeric"] = ""
            simulated["reviewer_normalized_unit"] = ""
        rows.append(simulated)
    return rows


def build_intentional_error_cases(template_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not template_rows:
        return []
    base = dict(template_rows[0])
    invalid_decision = dict(base)
    invalid_decision["assigned_reviewer_id"] = "error_case_1"
    invalid_decision["review_status"] = "IN_REVIEW"
    invalid_decision["reviewer_decision"] = "FINAL_EXPORT"
    invalid_decision["reviewer_note"] = "intentional invalid decision for validation proof"

    missing_correction = dict(template_rows[min(1, len(template_rows) - 1)])
    missing_correction["assigned_reviewer_id"] = "error_case_2"
    missing_correction["review_status"] = "IN_REVIEW"
    missing_correction["reviewer_decision"] = "CORRECT"
    missing_correction["reviewer_note"] = "intentional missing correction fields for validation proof"
    missing_correction["reviewer_metric_standardized"] = ""
    missing_correction["reviewer_year_standardized"] = ""
    missing_correction["reviewer_value_numeric"] = ""
    missing_correction["reviewer_normalized_unit"] = ""
    return [invalid_decision, missing_correction]


def validate_import_row(row: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    required_identity_fields = [
        "queue_item_id",
        "review_item_id",
        "source_artifact_path",
        "source_artifact_sheet",
        "source_row_id",
    ]
    for field in required_identity_fields:
        if not normalize_text(row.get(field)):
            errors.append(f"missing required identity field: {field}")

    decision = normalize_text(row.get("reviewer_decision"))
    if decision not in REVIEWER_DECISION_TO_STATUS:
        errors.append(f"invalid reviewer_decision: {decision or '__EMPTY__'}")

    if decision == "CORRECT":
        for field in [
            "reviewer_metric_standardized",
            "reviewer_year_standardized",
            "reviewer_value_numeric",
            "reviewer_normalized_unit",
        ]:
            if not normalize_text(row.get(field)):
                errors.append(f"missing correction field for CORRECT: {field}")
        if normalize_text(row.get("reviewer_value_numeric")) and normalize_float(row.get("reviewer_value_numeric")) is None:
            errors.append("reviewer_value_numeric must be numeric for CORRECT")

    for field in ["formal_client_export_allowed", "client_ready", "production_ready"]:
        if normalize_bool(row.get(field)):
            errors.append(f"{field} must remain false")
    if not normalize_bool(row.get("not_final_confirmation", True)):
        errors.append("not_final_confirmation must remain true")

    if normalize_text(row.get("source_detail_level")) == "SUMMARY_DERIVED":
        warnings.append("summary-derived placeholder row remains planning-only and should not be treated as completed real review")

    validation_status = "PASS"
    if errors:
        validation_status = "FAIL"
    elif warnings:
        validation_status = "PASS_WITH_WARNING"

    resulting_status = REVIEWER_DECISION_TO_STATUS.get(decision, "")
    eligible_for_future_apply_simulation = decision in {"CONFIRM", "CORRECT"} and not errors

    return {
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "reviewer_decision": decision,
        "resulting_status": resulting_status,
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
        "eligible_for_future_apply_simulation": eligible_for_future_apply_simulation,
        "audit_note": normalize_text(row.get("reviewer_note")),
        "reviewed_at": normalize_text(row.get("reviewed_at")) or utc_now(),
        "no_write_back_required": normalize_bool(row.get("no_write_back_required", True)),
    }


def build_reviewed_result_rows(import_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for row in import_rows:
        validation = validate_import_row(row)
        results.append(
            {
                "queue_item_id": normalize_text(row.get("queue_item_id")),
                "review_item_id": normalize_text(row.get("review_item_id")),
                "reviewer_decision": validation["reviewer_decision"],
                "reviewer_metric_standardized": normalize_text(row.get("reviewer_metric_standardized")),
                "reviewer_year_standardized": normalize_text(row.get("reviewer_year_standardized")),
                "reviewer_value_numeric": normalize_text(row.get("reviewer_value_numeric")),
                "reviewer_normalized_unit": normalize_text(row.get("reviewer_normalized_unit")),
                "resulting_status": validation["resulting_status"],
                "validation_status": validation["validation_status"],
                "validation_errors": validation["errors"],
                "validation_warnings": validation["warnings"],
                "eligible_for_future_apply_simulation": validation["eligible_for_future_apply_simulation"],
                "audit_note": validation["audit_note"],
                "reviewed_at": validation["reviewed_at"],
                "no_write_back_required": validation["no_write_back_required"],
            }
        )
    return results


def validation_rules_catalog() -> List[Dict[str, str]]:
    return [
        {"rule_id": "identity_required", "rule": "queue_item_id/review_item_id/source_artifact_path/source_artifact_sheet/source_row_id must exist"},
        {"rule_id": "decision_allowed", "rule": "reviewer_decision must be CONFIRM/CORRECT/REJECT/NEEDS_SOURCE_CHECK/ESCALATE/SKIP"},
        {"rule_id": "correct_payload", "rule": "CORRECT must provide reviewer metric/year/value/unit fields"},
        {"rule_id": "numeric_value", "rule": "reviewer_value_numeric must be numeric when provided"},
        {"rule_id": "safety_flags", "rule": "formal_client_export_allowed/client_ready/production_ready must remain false"},
        {"rule_id": "not_final_confirmation", "rule": "not_final_confirmation must remain true"},
        {"rule_id": "no_write_back", "rule": "no_write_back_required must remain true"},
    ]


def decision_mapping_rows() -> List[Dict[str, str]]:
    return [
        {"reviewer_decision": decision, "resulting_status": status}
        for decision, status in REVIEWER_DECISION_TO_STATUS.items()
    ]
