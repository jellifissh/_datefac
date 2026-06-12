from __future__ import annotations

from typing import Any, Dict, Iterable, List

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text


READY_DECISION_343I = "STRICT_HUMAN_REVIEW_PACKAGE_343I_WAITING_FOR_STRICT_REVIEW"
NOT_READY_DECISION_343I = "STRICT_HUMAN_REVIEW_PACKAGE_343I_NOT_READY"
RECOMMENDED_343J_SCOPE = "strict_human_review_result_ingestion_after_user_fills_workbook"

ALLOWED_STRICT_REVIEW_DECISIONS = [
    "STRICT_CONFIRM",
    "STRICT_CORRECT",
    "STRICT_REJECT",
    "STRICT_NEEDS_SOURCE_CHECK",
    "STRICT_DEFER",
]

EDITABLE_STRICT_REVIEW_COLUMNS = [
    "strict_review_decision",
    "strict_review_metric_standardized",
    "strict_review_year_standardized",
    "strict_review_value_numeric",
    "strict_review_normalized_unit",
    "strict_review_note",
    "strict_reviewer_id",
    "strict_reviewed_at",
]

STRICT_CORRECT_REQUIRED_COLUMNS = [
    "strict_review_metric_standardized",
    "strict_review_year_standardized",
    "strict_review_value_numeric",
    "strict_review_normalized_unit",
]

REQUIRED_IDENTITY_COLUMNS = [
    "queue_item_id",
    "review_item_id",
    "resulting_status",
    "simulated_downstream_action",
    "priority_tier",
]

WORKBOOK_SHEETS_343I = [
    "00_README",
    "01_PACKAGE_SUMMARY",
    "02_INPUT_343H_SUMMARY",
    "03_STRICT_REVIEW_ITEMS",
    "04_REVIEW_TEMPLATE",
    "05_EVIDENCE_CONTEXT",
    "06_DECISION_RULES",
    "07_VALIDATION_RULES",
    "08_CLIENT_EXPORT_BOUNDARY",
    "09_IMPORT_CONTRACT",
    "10_343J_READINESS",
    "11_NO_WRITE_BACK",
    "12_NEXT_STEPS",
]


def build_strict_review_item(row: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(row)
    for field in EDITABLE_STRICT_REVIEW_COLUMNS:
        item[field] = ""
    item["waiting_for_strict_human_review"] = True
    item["strict_human_review_result_ingested"] = False
    item["strict_human_review_completed"] = False
    item["requires_strict_human_review"] = True
    item["formal_client_export_allowed"] = False
    item["client_ready"] = False
    item["production_ready"] = False
    item["strict_review_package_scope_note"] = (
        "AI-assisted confirmed only; strict human review still pending"
    )
    return item


def build_strict_review_items(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [build_strict_review_item(row) for row in rows]


def build_evidence_context_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    context_rows: List[Dict[str, Any]] = []
    for row in rows:
        context_rows.append(
            {
                "queue_item_id": normalize_text(row.get("queue_item_id")),
                "review_item_id": normalize_text(row.get("review_item_id")),
                "row_index": row.get("row_index", ""),
                "resulting_status": normalize_text(row.get("resulting_status")),
                "resulting_spot_check_status": normalize_text(
                    row.get("resulting_spot_check_status")
                ),
                "simulated_downstream_action": normalize_text(
                    row.get("simulated_downstream_action")
                ),
                "apply_eligibility_classification": normalize_text(
                    row.get("apply_eligibility_classification")
                ),
                "priority_tier": normalize_text(row.get("priority_tier")),
                "metric_standardized": normalize_text(row.get("metric_standardized")),
                "year_standardized": normalize_text(row.get("year_standardized")),
                "value_numeric": normalize_text(row.get("value_numeric")),
                "normalized_unit": normalize_text(row.get("normalized_unit")),
                "final_metric_standardized": normalize_text(
                    row.get("final_metric_standardized")
                ),
                "final_year_standardized": normalize_text(
                    row.get("final_year_standardized")
                ),
                "final_value_numeric": normalize_text(row.get("final_value_numeric")),
                "final_normalized_unit": normalize_text(
                    row.get("final_normalized_unit")
                ),
                "spot_check_note": normalize_text(row.get("spot_check_note")),
                "spot_checker_id": normalize_text(row.get("spot_checker_id")),
                "spot_checked_at": normalize_text(row.get("spot_checked_at")),
                "confirmation_scope_note": normalize_text(
                    row.get("confirmation_scope_note")
                ),
                "spot_check_source_disclosure": normalize_text(
                    row.get("spot_check_source_disclosure")
                ),
            }
        )
    return context_rows


def strict_review_decision_rules() -> List[Dict[str, str]]:
    return [
        {
            "strict_review_decision": "STRICT_CONFIRM",
            "when_to_use": "Strict human reviewer independently confirms the AI-assisted row.",
            "corrected_fields_required": "No",
        },
        {
            "strict_review_decision": "STRICT_CORRECT",
            "when_to_use": "Strict human reviewer accepts the row only after correcting metric/year/value/unit.",
            "corrected_fields_required": "Yes",
        },
        {
            "strict_review_decision": "STRICT_REJECT",
            "when_to_use": "Strict human reviewer rejects the row and it must stay out of export candidacy.",
            "corrected_fields_required": "No",
        },
        {
            "strict_review_decision": "STRICT_NEEDS_SOURCE_CHECK",
            "when_to_use": "Strict human reviewer still cannot verify the row from current evidence.",
            "corrected_fields_required": "No",
        },
        {
            "strict_review_decision": "STRICT_DEFER",
            "when_to_use": "Strict human reviewer intentionally defers the row for a later batch.",
            "corrected_fields_required": "No",
        },
    ]


def strict_review_validation_rules() -> List[Dict[str, str]]:
    return [
        {
            "rule_id": "identity_preserved",
            "rule": "Identity and evidence columns must remain unchanged for 343J row matching.",
        },
        {
            "rule_id": "decision_allowed",
            "rule": "strict_review_decision must be one of the five allowed STRICT_* decisions when filled.",
        },
        {
            "rule_id": "strict_correct_requires_payload",
            "rule": "STRICT_CORRECT requires strict_review_metric_standardized / strict_review_year_standardized / strict_review_value_numeric / strict_review_normalized_unit.",
        },
        {
            "rule_id": "strict_reject_requires_note",
            "rule": "STRICT_REJECT requires strict_review_note.",
        },
        {
            "rule_id": "source_check_requires_note",
            "rule": "STRICT_NEEDS_SOURCE_CHECK requires strict_review_note.",
        },
        {
            "rule_id": "boundary_flags_false",
            "rule": "formal_client_export_allowed, client_ready, production_ready, and strict_human_review_completed must remain false in 343I.",
        },
        {
            "rule_id": "waiting_only",
            "rule": "343I generates a package only and must not ingest strict human review results yet.",
        },
    ]


def build_expected_import_contract(
    *,
    review_queue_schema_version: str,
    output_dir_hint: str,
) -> Dict[str, Any]:
    return {
        "contract_version": "343I.strict_human_review_package.v1",
        "source_review_queue_schema_version": review_queue_schema_version,
        "required_sheet_name": "04_REVIEW_TEMPLATE",
        "required_identity_columns": REQUIRED_IDENTITY_COLUMNS,
        "editable_strict_review_columns": EDITABLE_STRICT_REVIEW_COLUMNS,
        "allowed_strict_review_decisions": ALLOWED_STRICT_REVIEW_DECISIONS,
        "strict_correct_required_columns": STRICT_CORRECT_REQUIRED_COLUMNS,
        "validation_rules": [
            row["rule_id"] for row in strict_review_validation_rules()
        ],
        "expected_input_path_pattern": "D:/_datefac/input/review_queue_strict_human_review_343i_filled/*.xlsx",
        "waiting_for_strict_human_review": True,
        "strict_human_review_result_ingested": False,
        "recommended_output_dir_hint": output_dir_hint,
    }


def build_boundary_rows() -> List[Dict[str, Any]]:
    return [
        {
            "review_source_type": "AI_ASSISTED_REVIEW",
            "spot_check_source_type": "AI_ASSISTED_SPOT_CHECK",
            "strict_human_review_completed": False,
            "requires_strict_human_review": True,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "boundary_note": "343I packages strict human review work only; it does not approve export.",
        }
    ]


def build_readiness_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "gate": "strict_human_review_package_generated",
            "value": summary.get("strict_human_review_package_generated", False),
            "meaning": "Required 343I package artifacts exist for user strict review.",
        },
        {
            "gate": "waiting_for_strict_human_review",
            "value": summary.get("waiting_for_strict_human_review", False),
            "meaning": "343I intentionally stops before ingestion.",
        },
        {
            "gate": "strict_human_review_result_ingested",
            "value": summary.get("strict_human_review_result_ingested", False),
            "meaning": "Must remain false until 343J.",
        },
        {
            "gate": "ready_for_343j",
            "value": summary.get("ready_for_343j", False),
            "meaning": "Must remain false until user supplies a filled strict review workbook.",
        },
        {
            "gate": "recommended_343j_scope",
            "value": summary.get("recommended_343j_scope", ""),
            "meaning": "Expected next ingestion scope after user fills the workbook.",
        },
    ]


def build_next_steps_rows() -> List[Dict[str, str]]:
    return [
        {
            "step": "open_strict_review_template",
            "recommendation": "Open the dedicated 343I strict human review template workbook.",
        },
        {
            "step": "fill_only_strict_review_columns",
            "recommendation": "Fill only strict_review_* columns plus strict_reviewer_id and strict_reviewed_at.",
        },
        {
            "step": "save_filled_copy_for_343j",
            "recommendation": "Save the filled workbook under D:/_datefac/input/review_queue_strict_human_review_343i_filled/ for later 343J ingestion.",
        },
        {
            "step": "preserve_export_boundary",
            "recommendation": "Do not treat 343I as completed strict human review or formal client export approval.",
        },
    ]


def strict_review_decisions_blank(rows: Iterable[Dict[str, Any]]) -> bool:
    for row in rows:
        if any(normalize_text(row.get(field)) for field in EDITABLE_STRICT_REVIEW_COLUMNS):
            return False
    return True


def client_export_gate_is_safe(gate: Dict[str, Any]) -> bool:
    return bool(
        not normalize_bool(gate.get("formal_client_export_allowed"))
        and not normalize_bool(gate.get("client_ready"))
        and not normalize_bool(gate.get("production_ready"))
        and not normalize_bool(gate.get("strict_human_review_completed"))
        and normalize_bool(gate.get("requires_strict_human_review"))
    )
