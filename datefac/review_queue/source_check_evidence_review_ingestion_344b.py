from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from datefac.review_queue.excel_round_trip_343b import (
    normalize_bool,
    normalize_float,
    normalize_text,
)
from datefac.review_queue.source_check_backlog_package_344a import (
    ALLOWED_SOURCE_CHECK_DECISIONS,
    EDITABLE_SOURCE_CHECK_COLUMNS_344A,
    REQUIRED_IDENTITY_COLUMNS_344A,
    SOURCE_CORRECT_REQUIRED_COLUMNS_344A,
)


READY_DECISION_344B = "SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_READY"
VALIDATION_FAILED_DECISION_344B = (
    "SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_VALIDATION_FAILED"
)
NOT_READY_DECISION_344B = "SOURCE_CHECK_EVIDENCE_REVIEW_INGESTION_344B_NOT_READY"
RECOMMENDED_344C_SCOPE_344B = (
    "source_check_confirmed_sidecar_apply_simulation_and_expanded_trust_gate"
)

SOURCE_CHECK_DECISION_TO_STATUS_344B = {
    "SOURCE_CONFIRM": "CONFIRMED",
    "SOURCE_CORRECT": "CORRECTED",
    "SOURCE_REJECT": "REJECTED",
    "SOURCE_STILL_INSUFFICIENT": "STILL_INSUFFICIENT",
    "SOURCE_DEFER": "DEFERRED",
}

SOURCE_CHECK_DECISION_TO_ACTION_344B = {
    "SOURCE_CONFIRM": "SOURCE_CHECK_CONFIRMED",
    "SOURCE_CORRECT": "SOURCE_CHECK_CORRECTED",
    "SOURCE_REJECT": "SOURCE_CHECK_REJECTED",
    "SOURCE_STILL_INSUFFICIENT": "SOURCE_CHECK_STILL_INSUFFICIENT",
    "SOURCE_DEFER": "SOURCE_CHECK_DEFERRED",
}

SOURCE_CHECK_REVIEW_SOURCE_TYPE_344B = "INDEPENDENT_WORKBOOK_REVIEW"

SOURCE_CHECK_RESULT_DISCLOSURE_344B = (
    "Source-check decisions were imported from a filled sidecar workbook; "
    "no production write-back or formal client export occurred."
)

REQUIRED_COLUMNS_BY_DECISION_344B = {
    "SOURCE_CONFIRM": [
        "source_checker_id",
        "source_checked_at",
        "source_check_metric_standardized",
        "source_check_year_standardized",
        "source_check_value_numeric",
        "source_check_normalized_unit",
    ],
    "SOURCE_CORRECT": [
        "source_checker_id",
        "source_checked_at",
        *SOURCE_CORRECT_REQUIRED_COLUMNS_344A,
        "source_check_note",
    ],
    "SOURCE_REJECT": [
        "source_checker_id",
        "source_checked_at",
        "source_check_note",
    ],
    "SOURCE_STILL_INSUFFICIENT": [
        "source_checker_id",
        "source_checked_at",
        "source_check_note",
    ],
    "SOURCE_DEFER": [
        "source_checker_id",
        "source_checked_at",
    ],
}

PRESERVED_ROW_FIELDS_344B = [
    "backlog_item_key",
    "queue_item_id",
    "review_item_id",
    "source_status",
    "priority_tier",
    "backlog_reason",
    "review_source_type",
    "spot_check_source_type",
    "not_pure_human_review",
    "strict_human_review_completed",
    "requires_strict_human_review",
    "requires_human_spot_check",
    "apply_mode",
    "source_pdf_name",
    "source_pdf_path",
    "source_pdf_id",
    "page_number",
    "table_id",
    "cell_id",
    "bbox",
    "image_path",
    "source_text_snippet",
    "source_html_snippet",
    "metric_candidate_raw",
    "metric_standardized",
    "year_standardized",
    "value_numeric",
    "normalized_unit",
    "evidence_source_stage",
    "evidence_source_artifact",
    "source_artifact_path",
    "source_artifact_sheet",
    "source_row_id",
    "backlog_sources",
    "evidence_resolution_status",
    "evidence_gap_reason",
    "match_type",
    "match_confidence",
    "match_reason",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalized_numeric_text(value: Any) -> str:
    numeric = normalize_float(value)
    if numeric is None:
        return normalize_text(value)
    return f"{numeric:g}"


def validate_filled_source_check_row(
    row: Dict[str, Any],
    *,
    expected_row: Dict[str, Any] | None,
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    for field in REQUIRED_IDENTITY_COLUMNS_344A:
        if not normalize_text(row.get(field)):
            errors.append(f"missing required identity field: {field}")

    for field in EDITABLE_SOURCE_CHECK_COLUMNS_344A:
        if field not in row:
            errors.append(f"missing source-check column: {field}")

    decision = normalize_text(row.get("source_check_decision"))
    if not decision:
        errors.append("source_check_decision must not be empty")
    elif decision not in ALLOWED_SOURCE_CHECK_DECISIONS:
        errors.append(f"invalid source_check_decision: {decision}")

    if decision in REQUIRED_COLUMNS_BY_DECISION_344B:
        for field in REQUIRED_COLUMNS_BY_DECISION_344B[decision]:
            if not normalize_text(row.get(field)):
                errors.append(f"missing required field for {decision}: {field}")

    evidence_checked = normalize_bool(row.get("source_evidence_checked"))
    evidence_sufficient = normalize_bool(row.get("source_evidence_sufficient"))
    if decision in {"SOURCE_CONFIRM", "SOURCE_CORRECT", "SOURCE_REJECT"} and not evidence_checked:
        errors.append(f"{decision} requires source_evidence_checked = true")
    if decision in {"SOURCE_CONFIRM", "SOURCE_CORRECT"} and not evidence_sufficient:
        errors.append(f"{decision} requires source_evidence_sufficient = true")

    if decision in {"SOURCE_CONFIRM", "SOURCE_CORRECT"}:
        value = normalize_text(row.get("source_check_value_numeric"))
        if value and normalize_float(row.get("source_check_value_numeric")) is None:
            errors.append(
                f"source_check_value_numeric must be numeric for {decision}"
            )

    if decision == "SOURCE_DEFER" and not normalize_text(row.get("source_check_note")):
        warnings.append("SOURCE_DEFER should include source_check_note when available")

    if normalize_text(row.get("review_source_type")) != "AI_ASSISTED_REVIEW":
        errors.append("review_source_type must remain AI_ASSISTED_REVIEW")
    if normalize_text(row.get("spot_check_source_type")) != "AI_ASSISTED_SPOT_CHECK":
        errors.append("spot_check_source_type must remain AI_ASSISTED_SPOT_CHECK")
    if not normalize_bool(row.get("not_pure_human_review")):
        errors.append("not_pure_human_review must remain true")
    if normalize_bool(row.get("strict_human_review_completed")):
        errors.append("strict_human_review_completed must remain false")
    if not normalize_bool(row.get("requires_strict_human_review")):
        errors.append("requires_strict_human_review must remain true")
    if not normalize_bool(row.get("requires_human_spot_check")):
        errors.append("requires_human_spot_check must remain true")
    if normalize_text(row.get("apply_mode")) != "SIMULATION_ONLY":
        errors.append("apply_mode must remain SIMULATION_ONLY")
    if normalize_bool(row.get("formal_client_export_allowed")):
        errors.append("formal_client_export_allowed must remain false")
    if normalize_bool(row.get("client_ready")):
        errors.append("client_ready must remain false")
    if normalize_bool(row.get("production_ready")):
        errors.append("production_ready must remain false")

    if expected_row:
        for field in ["backlog_item_key", "queue_item_id", "review_item_id"]:
            if normalize_text(row.get(field)) != normalize_text(expected_row.get(field)):
                errors.append(f"identity mismatch: {field}")
        expected_source_row_id = normalize_text(expected_row.get("source_row_id"))
        if expected_source_row_id and normalize_text(row.get("source_row_id")) != expected_source_row_id:
            errors.append("identity mismatch: source_row_id")

    correction_semantics_ok = True
    if decision == "SOURCE_CORRECT":
        original_metric = normalize_text(row.get("metric_standardized"))
        original_unit = normalize_text(row.get("normalized_unit"))
        corrected_metric = normalize_text(row.get("source_check_metric_standardized"))
        corrected_unit = normalize_text(row.get("source_check_normalized_unit"))
        corrected_year = normalize_text(row.get("source_check_year_standardized"))
        original_year = normalize_text(row.get("year_standardized"))
        corrected_value = _normalized_numeric_text(row.get("source_check_value_numeric"))
        original_value = _normalized_numeric_text(row.get("value_numeric"))

        if original_metric == "revenue" and corrected_metric != "YOY":
            errors.append("SOURCE_CORRECT revenue rows must correct metric to YOY")
            correction_semantics_ok = False
        if original_unit == "亿元" and corrected_unit != "%":
            errors.append("SOURCE_CORRECT revenue rows must correct unit to %")
            correction_semantics_ok = False
        if corrected_year != original_year:
            errors.append("SOURCE_CORRECT must preserve year_standardized from source row")
            correction_semantics_ok = False
        if corrected_value != original_value:
            errors.append("SOURCE_CORRECT must preserve value_numeric from source row")
            correction_semantics_ok = False

    validation_status = "PASS"
    if errors:
        validation_status = "FAIL"
    elif warnings:
        validation_status = "PASS_WITH_WARNING"

    return {
        "backlog_item_key": normalize_text(row.get("backlog_item_key")),
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "source_check_decision": decision,
        "source_check_status": SOURCE_CHECK_DECISION_TO_STATUS_344B.get(decision, ""),
        "sidecar_action": SOURCE_CHECK_DECISION_TO_ACTION_344B.get(decision, ""),
        "validation_status": validation_status,
        "correction_semantics_ok": correction_semantics_ok,
        "errors": errors,
        "warnings": warnings,
    }


def build_source_check_result_row(
    row: Dict[str, Any],
    *,
    validation: Dict[str, Any],
) -> Dict[str, Any]:
    result = {field: row.get(field, "") for field in PRESERVED_ROW_FIELDS_344B}
    decision = validation["source_check_decision"]
    result.update(
        {
            "source_check_decision": decision,
            "source_check_metric_standardized": normalize_text(
                row.get("source_check_metric_standardized")
            ),
            "source_check_year_standardized": normalize_text(
                row.get("source_check_year_standardized")
            ),
            "source_check_value_numeric": _normalized_numeric_text(
                row.get("source_check_value_numeric")
            ),
            "source_check_normalized_unit": normalize_text(
                row.get("source_check_normalized_unit")
            ),
            "source_check_note": normalize_text(row.get("source_check_note")),
            "source_checker_id": normalize_text(row.get("source_checker_id")),
            "source_checked_at": normalize_text(row.get("source_checked_at")) or utc_now(),
            "source_evidence_checked": normalize_bool(row.get("source_evidence_checked")),
            "source_evidence_sufficient": normalize_bool(
                row.get("source_evidence_sufficient")
            ),
            "source_check_status": validation["source_check_status"],
            "sidecar_action": validation["sidecar_action"],
            "validation_status": validation["validation_status"],
            "validation_errors": validation["errors"],
            "validation_warnings": validation["warnings"],
            "source_check_review_source_type": SOURCE_CHECK_REVIEW_SOURCE_TYPE_344B,
            "source_check_result_ingested": False,
            "source_check_backlog_resolved": False,
            "validated_sidecar_generated": False,
            "correction_sidecar_generated": False,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "global_strict_human_review_completed": False,
            "no_write_back_required": True,
            "review_source_disclosure": SOURCE_CHECK_RESULT_DISCLOSURE_344B,
        }
    )
    if decision in {"SOURCE_CONFIRM", "SOURCE_CORRECT"}:
        result["final_metric_standardized"] = normalize_text(
            row.get("source_check_metric_standardized")
        )
        result["final_year_standardized"] = normalize_text(
            row.get("source_check_year_standardized")
        )
        result["final_value_numeric"] = _normalized_numeric_text(
            row.get("source_check_value_numeric")
        )
        result["final_normalized_unit"] = normalize_text(
            row.get("source_check_normalized_unit")
        )
    else:
        result["final_metric_standardized"] = ""
        result["final_year_standardized"] = ""
        result["final_value_numeric"] = ""
        result["final_normalized_unit"] = ""
    return result


def build_validated_sidecar_row(result_row: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(result_row)
    row["validated_sidecar_scope"] = "SOURCE_CHECK_BACKLOG_19_ROWS_ONLY"
    row["validated_sidecar_status"] = "READY_FOR_344C_SIMULATION"
    return row


def build_correction_row(result_row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "backlog_item_key": normalize_text(result_row.get("backlog_item_key")),
        "queue_item_id": normalize_text(result_row.get("queue_item_id")),
        "review_item_id": normalize_text(result_row.get("review_item_id")),
        "source_row_id": normalize_text(result_row.get("source_row_id")),
        "source_pdf_name": normalize_text(result_row.get("source_pdf_name")),
        "page_number": normalize_text(result_row.get("page_number")),
        "original_metric_standardized": normalize_text(
            result_row.get("metric_standardized")
        ),
        "original_year_standardized": normalize_text(
            result_row.get("year_standardized")
        ),
        "original_value_numeric": _normalized_numeric_text(
            result_row.get("value_numeric")
        ),
        "original_normalized_unit": normalize_text(result_row.get("normalized_unit")),
        "corrected_metric_standardized": normalize_text(
            result_row.get("source_check_metric_standardized")
        ),
        "corrected_year_standardized": normalize_text(
            result_row.get("source_check_year_standardized")
        ),
        "corrected_value_numeric": _normalized_numeric_text(
            result_row.get("source_check_value_numeric")
        ),
        "corrected_normalized_unit": normalize_text(
            result_row.get("source_check_normalized_unit")
        ),
        "correction_note": normalize_text(result_row.get("source_check_note")),
        "correction_semantics": (
            "metric revenue -> YOY, unit 亿元 -> %, preserve year/value"
        ),
    }


def decision_summary_rows(result_rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = {decision: 0 for decision in ALLOWED_SOURCE_CHECK_DECISIONS}
    for row in result_rows:
        decision = normalize_text(row.get("source_check_decision"))
        if decision in counts:
            counts[decision] += 1
    return [
        {
            "source_check_decision": decision,
            "source_check_status": SOURCE_CHECK_DECISION_TO_STATUS_344B[decision],
            "sidecar_action": SOURCE_CHECK_DECISION_TO_ACTION_344B[decision],
            "row_count": counts[decision],
        }
        for decision in ALLOWED_SOURCE_CHECK_DECISIONS
    ]


def build_validation_issue_rows(
    validation_rows: Iterable[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for row in validation_rows:
        for error in row.get("errors", []):
            issues.append(
                {
                    "row_index": row.get("row_index", ""),
                    "backlog_item_key": row.get("backlog_item_key", ""),
                    "queue_item_id": row.get("queue_item_id", ""),
                    "review_item_id": row.get("review_item_id", ""),
                    "issue_type": "ERROR",
                    "message": error,
                }
            )
        for warning in row.get("warnings", []):
            issues.append(
                {
                    "row_index": row.get("row_index", ""),
                    "backlog_item_key": row.get("backlog_item_key", ""),
                    "queue_item_id": row.get("queue_item_id", ""),
                    "review_item_id": row.get("review_item_id", ""),
                    "issue_type": "WARNING",
                    "message": warning,
                }
            )
    return issues


def build_audit_gate(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_check_result_ingested": summary.get("source_check_result_ingested", False),
        "source_check_backlog_resolved": summary.get(
            "source_check_backlog_resolved", False
        ),
        "source_check_resolved_row_count": summary.get(
            "validated_sidecar_row_count", 0
        ),
        "source_check_confirm_count": summary.get("source_confirm_count", 0),
        "source_check_correct_count": summary.get("source_correct_count", 0),
        "source_check_reject_count": summary.get("source_reject_count", 0),
        "source_check_still_insufficient_count": summary.get(
            "source_still_insufficient_count", 0
        ),
        "source_check_defer_count": summary.get("source_defer_count", 0),
        "validated_sidecar_generated": summary.get("validated_sidecar_generated", False),
        "correction_sidecar_generated": summary.get("correction_sidecar_generated", False),
        "audit_gate_generated": summary.get("audit_gate_generated", False),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "ready_for_344c": summary.get("ready_for_344c", False),
        "recommended_344c_scope": summary.get("recommended_344c_scope", ""),
        "reason": (
            "Source-check backlog is resolved only as a sidecar review result. "
            "No production write-back or formal client export is allowed."
        ),
    }


def build_scope_boundary_lines() -> List[str]:
    return [
        "344B only ingests the 19-row 344A2 source-check review workbook.",
        "344B does not modify the already closed 343O 10-row demo arc.",
        "344B does not write back to production or upstream workbooks.",
        "10 rows are confirmed and 9 rows are corrected from revenue/亿元 to YOY/%.",
        "formal_client_export_allowed must remain false.",
        "client_ready must remain false.",
        "production_ready must remain false.",
        "global_strict_human_review_completed must remain false.",
        "The next safe task is 344C source-check confirmed sidecar apply simulation and expanded trust gate.",
    ]

