from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from datefac.review_queue.excel_round_trip_343b import (
    REVIEW_SAFE_COLUMN_ORDER,
    build_review_template_rows,
    normalize_bool,
    normalize_text,
)


ALLOWED_REVIEWER_DECISIONS = [
    "CONFIRM",
    "CORRECT",
    "REJECT",
    "NEEDS_SOURCE_CHECK",
    "SKIP",
]

EDITABLE_REVIEWER_COLUMNS = [
    "reviewer_decision",
    "reviewer_metric_standardized",
    "reviewer_year_standardized",
    "reviewer_value_numeric",
    "reviewer_normalized_unit",
    "reviewer_note",
    "reviewer_id",
    "reviewed_at",
]

REQUIRED_CORRECT_COLUMNS = [
    "reviewer_metric_standardized",
    "reviewer_year_standardized",
    "reviewer_value_numeric",
    "reviewer_normalized_unit",
]

REQUIRED_IDENTITY_COLUMNS = [
    "queue_item_id",
    "review_item_id",
    "source_artifact_path",
    "source_artifact_sheet",
    "source_row_id",
]

DEFAULT_REVIEW_TEMPLATE_LIMIT = 30

REVIEW_QUEUE_REAL_EXCEL_SHEETS = [
    "00_README",
    "01_REVIEW_SUMMARY",
    "02_INPUT_343B_SUMMARY",
    "03_REVIEW_QUEUE_ITEMS",
    "04_FILLABLE_REVIEW",
    "05_DECISION_RULES",
    "06_VALIDATION_RULES",
    "07_FIELD_GUIDE",
    "08_RISK_CONTEXT",
    "09_IMPORT_CONTRACT",
    "10_WAITING_FOR_REVIEW",
    "11_343D_READINESS",
    "12_NO_WRITE_BACK",
    "13_NEXT_STEPS",
]


def build_blank_template_rows(
    sample_items: List[Dict[str, Any]],
    *,
    excel_template_spec: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows = build_review_template_rows(sample_items, excel_template_spec=excel_template_spec)
    for row in rows:
        row["reviewer_id"] = ""
        row["reviewed_at"] = ""
    return rows


def _bucket_name(row: Dict[str, Any]) -> str:
    source_detail_level = normalize_text(row.get("source_detail_level"))
    trust_level = normalize_text(row.get("data_trust_level"))
    preview_source_type = normalize_text(row.get("preview_source_type"))
    if source_detail_level == "SUMMARY_DERIVED":
        return "summary_derived"
    if trust_level == "HUMAN_REVIEWED":
        return "human_reviewed"
    if trust_level == "SIMULATED_DIRECT_ADOPTED" or preview_source_type == "SIMULATED_DIRECT":
        return "simulated_direct"
    if trust_level == "SIMULATED_CORRECTION_ADOPTED" or "CORRECT" in preview_source_type:
        return "simulated_corrected"
    return "other"


def _with_real_review_defaults(row: Dict[str, Any]) -> Dict[str, Any]:
    copied = {column: row.get(column, "") for column in REVIEW_SAFE_COLUMN_ORDER if column in row}
    for editable in EDITABLE_REVIEWER_COLUMNS:
        copied[editable] = ""
    copied["assigned_reviewer_id"] = ""
    copied["reviewer_id"] = ""
    copied["review_status"] = "QUEUED_FOR_REAL_HUMAN_REVIEW"
    copied["review_round"] = row.get("review_round", 1) or 1
    copied["formal_client_export_allowed"] = False
    copied["client_ready"] = False
    copied["production_ready"] = False
    copied["not_final_confirmation"] = True
    copied["no_write_back_required"] = True
    copied["reviewed_result_ingested"] = False
    copied["waiting_for_human_review"] = True
    return copied


def _take_rows(
    rows: Sequence[Dict[str, Any]],
    selected_ids: set[str],
    *,
    bucket_name: str,
    limit: int,
) -> List[Dict[str, Any]]:
    taken: List[Dict[str, Any]] = []
    if limit <= 0:
        return taken
    for row in rows:
        row_id = normalize_text(row.get("queue_item_id")) or normalize_text(row.get("review_item_id"))
        if not row_id or row_id in selected_ids:
            continue
        if _bucket_name(row) != bucket_name:
            continue
        taken.append(_with_real_review_defaults(row))
        selected_ids.add(row_id)
        if len(taken) >= limit:
            break
    return taken


def select_real_review_pilot_rows(
    rows: Sequence[Dict[str, Any]],
    *,
    max_rows: int = DEFAULT_REVIEW_TEMPLATE_LIMIT,
) -> Dict[str, Any]:
    selected: List[Dict[str, Any]] = []
    selected_ids: set[str] = set()

    category_plan = [
        ("human_reviewed", 10),
        ("simulated_direct", 10),
        ("simulated_corrected", 9),
        ("summary_derived", 1),
    ]
    for bucket_name, bucket_limit in category_plan:
        remaining = max_rows - len(selected)
        if remaining <= 0:
            break
        selected.extend(
            _take_rows(
                rows,
                selected_ids,
                bucket_name=bucket_name,
                limit=min(bucket_limit, remaining),
            )
        )

    if len(selected) < max_rows:
        for row in rows:
            row_id = normalize_text(row.get("queue_item_id")) or normalize_text(row.get("review_item_id"))
            if not row_id or row_id in selected_ids:
                continue
            selected.append(_with_real_review_defaults(row))
            selected_ids.add(row_id)
            if len(selected) >= max_rows:
                break

    counts = {
        "human_reviewed_audit_row_count": 0,
        "simulated_direct_review_row_count": 0,
        "simulated_corrected_review_row_count": 0,
        "summary_derived_review_row_count": 0,
    }
    for row in selected:
        bucket_name = _bucket_name(row)
        if bucket_name == "human_reviewed":
            counts["human_reviewed_audit_row_count"] += 1
        elif bucket_name == "simulated_direct":
            counts["simulated_direct_review_row_count"] += 1
        elif bucket_name == "simulated_corrected":
            counts["simulated_corrected_review_row_count"] += 1
        elif bucket_name == "summary_derived":
            counts["summary_derived_review_row_count"] += 1

    return {
        "selected_rows": selected,
        **counts,
    }


def reviewer_decision_rules() -> List[Dict[str, str]]:
    return [
        {
            "reviewer_decision": "CONFIRM",
            "when_to_use": "Candidate row is correct enough to retain as-is for later sidecar ingestion.",
            "corrected_fields_required": "No",
        },
        {
            "reviewer_decision": "CORRECT",
            "when_to_use": "Candidate row is usable only after reviewer fixes metric/year/value/unit fields.",
            "corrected_fields_required": "Yes",
        },
        {
            "reviewer_decision": "REJECT",
            "when_to_use": "Candidate row should not move forward into a reviewed sidecar result.",
            "corrected_fields_required": "No",
        },
        {
            "reviewer_decision": "NEEDS_SOURCE_CHECK",
            "when_to_use": "Evidence is insufficient or ambiguous and source material must be checked again.",
            "corrected_fields_required": "No",
        },
        {
            "reviewer_decision": "SKIP",
            "when_to_use": "Reviewer intentionally leaves the row unresolved in this batch.",
            "corrected_fields_required": "No",
        },
    ]


def validation_rules_catalog_343c() -> List[Dict[str, str]]:
    return [
        {
            "rule_id": "identity_required",
            "rule": "All required identity columns must stay unchanged so 343D can match rows safely.",
        },
        {
            "rule_id": "editable_decision_allowed",
            "rule": "reviewer_decision must be one of CONFIRM/CORRECT/REJECT/NEEDS_SOURCE_CHECK/SKIP when filled.",
        },
        {
            "rule_id": "correct_requires_payload",
            "rule": "CORRECT requires reviewer_metric_standardized / reviewer_year_standardized / reviewer_value_numeric / reviewer_normalized_unit.",
        },
        {
            "rule_id": "simulated_caution",
            "rule": "SIMULATED_* rows are not human evidence. They require cautious confirmation before any future sidecar carry-forward.",
        },
        {
            "rule_id": "flags_must_remain_false",
            "rule": "formal_client_export_allowed, client_ready, and production_ready must remain false.",
        },
        {
            "rule_id": "waiting_only",
            "rule": "343C only prepares a workbook and must not ingest reviewed results yet.",
        },
        {
            "rule_id": "no_write_back",
            "rule": "No reviewer action in this workbook may write back to upstream workbooks.",
        },
    ]


def field_guide_rows() -> List[Dict[str, str]]:
    return [
        {
            "field_name": "reviewer_decision",
            "editable": "Yes",
            "description": "Primary human decision for the row.",
        },
        {
            "field_name": "reviewer_metric_standardized",
            "editable": "Yes",
            "description": "Required when reviewer_decision=CORRECT.",
        },
        {
            "field_name": "reviewer_year_standardized",
            "editable": "Yes",
            "description": "Required when reviewer_decision=CORRECT.",
        },
        {
            "field_name": "reviewer_value_numeric",
            "editable": "Yes",
            "description": "Required when reviewer_decision=CORRECT; keep numeric only.",
        },
        {
            "field_name": "reviewer_normalized_unit",
            "editable": "Yes",
            "description": "Required when reviewer_decision=CORRECT.",
        },
        {
            "field_name": "reviewer_note",
            "editable": "Yes",
            "description": "Free-form rationale, especially for REJECT, NEEDS_SOURCE_CHECK, or tricky corrections.",
        },
        {
            "field_name": "reviewer_id",
            "editable": "Yes",
            "description": "Human reviewer identifier for traceability.",
        },
        {
            "field_name": "reviewed_at",
            "editable": "Yes",
            "description": "Human review timestamp entered by the reviewer.",
        },
        {
            "field_name": "queue_item_id / review_item_id",
            "editable": "No",
            "description": "Identity keys for later 343D ingestion. Do not change.",
        },
    ]


def build_expected_import_contract(
    *,
    review_queue_schema_version: str,
    output_dir_hint: str,
) -> Dict[str, Any]:
    return {
        "contract_version": "343C.real_excel_review.v1",
        "source_review_queue_schema_version": review_queue_schema_version,
        "required_sheets": ["04_FILLABLE_REVIEW"],
        "required_identity_columns": REQUIRED_IDENTITY_COLUMNS,
        "editable_reviewer_columns": EDITABLE_REVIEWER_COLUMNS,
        "allowed_reviewer_decisions": ALLOWED_REVIEWER_DECISIONS,
        "correct_required_columns": REQUIRED_CORRECT_COLUMNS,
        "validation_rules": [row["rule_id"] for row in validation_rules_catalog_343c()],
        "next_expected_input_path_pattern": "D:/_datefac/input/review_queue_real_excel_review_343c_reviewed/*.xlsx",
        "reviewed_result_ingested": False,
        "waiting_for_human_review": True,
        "recommended_output_dir_hint": output_dir_hint,
    }


def build_waiting_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "state": "WAITING_FOR_HUMAN_REVIEW",
            "waiting_for_human_review": summary.get("waiting_for_human_review", False),
            "reviewed_result_ingested": summary.get("reviewed_result_ingested", False),
            "ready_for_343d": summary.get("ready_for_343d", False),
            "next_user_action": "Fill reviewer_* columns in the dedicated 343C review template workbook.",
        }
    ]


def build_readiness_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "gate": "real_review_template_generated",
            "value": summary.get("real_review_template_generated", False),
            "meaning": "Required fillable workbook package exists for user review.",
        },
        {
            "gate": "waiting_for_human_review",
            "value": summary.get("waiting_for_human_review", False),
            "meaning": "343C intentionally stops before ingestion.",
        },
        {
            "gate": "reviewed_result_ingested",
            "value": summary.get("reviewed_result_ingested", False),
            "meaning": "Must remain false until 343D.",
        },
        {
            "gate": "ready_for_343d",
            "value": summary.get("ready_for_343d", False),
            "meaning": "Must remain false until user provides a filled workbook.",
        },
        {
            "gate": "recommended_343d_scope",
            "value": summary.get("recommended_343d_scope", ""),
            "meaning": "Expected next ingestion scope after manual workbook fill.",
        },
    ]


def build_next_steps_rows() -> List[Dict[str, str]]:
    return [
        {
            "step": "open_review_template",
            "recommendation": "Open the dedicated 343C review template workbook and fill only reviewer_* columns plus reviewer_id/reviewed_at.",
        },
        {
            "step": "save_filled_copy",
            "recommendation": "Save a filled copy for later 343D ingestion; keep the identity/evidence columns unchanged.",
        },
        {
            "step": "do_not_treat_as_export",
            "recommendation": "Do not treat 343C output as a client export or a completed human-reviewed result package.",
        },
        {
            "step": "next_task",
            "recommendation": "Run 343D only after a real human-filled workbook is available.",
        },
    ]


def build_risk_context_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    risk_rows: List[Dict[str, Any]] = []
    for row in rows:
        risk_rows.append(
            {
                "queue_item_id": normalize_text(row.get("queue_item_id")),
                "review_item_id": normalize_text(row.get("review_item_id")),
                "data_trust_level": normalize_text(row.get("data_trust_level")),
                "source_detail_level": normalize_text(row.get("source_detail_level")),
                "risk_level": normalize_text(row.get("risk_level")),
                "risk_tags": row.get("risk_tags", []),
                "queue_reason_code": normalize_text(row.get("queue_reason_code")),
                "requires_later_audit": normalize_bool(row.get("requires_later_audit")),
                "source_text_snippet": normalize_text(row.get("source_text_snippet")),
            }
        )
    return risk_rows
