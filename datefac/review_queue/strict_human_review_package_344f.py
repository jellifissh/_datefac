from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from datefac.review_queue.excel_round_trip_343b import normalize_text


READY_DECISION_344F = "STRICT_HUMAN_REVIEW_PACKAGE_344F_READY"
NOT_READY_DECISION_344F = "STRICT_HUMAN_REVIEW_PACKAGE_344F_NOT_READY"
EXPORT_USAGE_344F = "STRICT_HUMAN_REVIEW_ONLY"
INPUT_STAGE_344F = "344E"

MANIFEST_FILE_NAME = "review_queue_strict_human_review_package_344f_manifest.json"
WORKBOOK_FILE_NAME = "review_queue_strict_human_review_package_344f.xlsx"
REVIEW_ROWS_CSV_FILE_NAME = "review_queue_strict_human_review_package_344f_review_rows.csv"
REVIEW_ROWS_JSON_FILE_NAME = "review_queue_strict_human_review_package_344f_review_rows.json"
REVIEWER_CHECKLIST_FILE_NAME = (
    "review_queue_strict_human_review_package_344f_reviewer_checklist.md"
)
EXECUTIVE_SUMMARY_FILE_NAME = (
    "review_queue_strict_human_review_package_344f_executive_summary.md"
)
ARTIFACT_INDEX_FILE_NAME = "review_queue_strict_human_review_package_344f_artifact_index.md"
FINAL_GATE_SNAPSHOT_FILE_NAME = (
    "review_queue_strict_human_review_package_344f_final_gate_snapshot.json"
)

REVIEW_ROW_FIELDS_344F = [
    "review_row_id",
    "source_scope",
    "source_stage",
    "source_row_id",
    "metric_name",
    "normalized_metric_name",
    "reported_value",
    "normalized_value",
    "unit",
    "period",
    "source_document",
    "source_page",
    "source_evidence_ref",
    "audit_label",
    "trust_status",
    "source_check_status",
    "correction_status",
    "needs_strict_human_review",
    "strict_human_review_decision",
    "strict_human_reviewer",
    "strict_human_reviewed_at",
    "strict_human_review_notes",
    "client_export_allowed",
]

WORKBOOK_SHEETS_344F = [
    "00_README",
    "01_PACKAGE_SUMMARY",
    "02_INPUT_344E_SUMMARY",
    "03_REVIEW_ROWS",
    "04_REVIEW_TEMPLATE",
    "05_EVIDENCE_CONTEXT",
    "06_CHECKLIST_RULES",
    "07_FIELD_MAPPING",
    "08_FINAL_GATE",
    "09_NO_WRITE_BACK",
    "10_NEXT_STEPS",
]

DEFAULT_EXPANDED_DEMO_AUDIT_SNAPSHOT_344E_DIR = Path(
    r"D:\_datefac\output\review_queue_expanded_demo_audit_snapshot_344e"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\review_queue_strict_human_review_package_344f"
)


def build_review_row_id(index: int) -> str:
    return f"344f::strict_review_row::{index:04d}"


def _audit_label_text(row: Dict[str, Any]) -> str:
    labels = row.get("audit_labels", [])
    if isinstance(labels, list):
        return " | ".join(str(label) for label in labels)
    return normalize_text(labels)


def _correction_status(row: Dict[str, Any]) -> str:
    source_check_status = normalize_text(row.get("source_check_status"))
    if source_check_status == "CORRECTED":
        return "CORRECTED_SOURCE_CHECK_ROW"
    if source_check_status == "CONFIRMED":
        return "CONFIRMED_SOURCE_CHECK_ROW"
    if normalize_text(row.get("source_lineage_stage")) == "343N_DEMO":
        return "PRIOR_DEMO_ROW"
    return ""


def build_strict_review_row(index: int, row: Dict[str, Any]) -> Dict[str, Any]:
    source_stage = normalize_text(row.get("source_lineage_stage"))
    review_row = {
        "review_row_id": build_review_row_id(index),
        "source_scope": normalize_text(row.get("expanded_export_scope")),
        "source_stage": source_stage,
        "source_row_id": normalize_text(row.get("queue_item_id"))
        or normalize_text(row.get("review_item_id")),
        "metric_name": normalize_text(row.get("metric_standardized")),
        "normalized_metric_name": normalize_text(row.get("metric_standardized")),
        "reported_value": normalize_text(row.get("value_numeric")),
        "normalized_value": normalize_text(row.get("value_numeric")),
        "unit": normalize_text(row.get("normalized_unit")),
        "period": normalize_text(row.get("year_standardized")),
        "source_document": normalize_text(row.get("source_pdf_name")),
        "source_page": normalize_text(row.get("page_number")),
        "source_evidence_ref": normalize_text(row.get("image_path"))
        or normalize_text(row.get("table_id"))
        or normalize_text(row.get("source_text_snippet"))[:120],
        "audit_label": _audit_label_text(row),
        "trust_status": normalize_text(row.get("source_lineage_summary"))
        or normalize_text(row.get("expanded_trust_source")),
        "source_check_status": normalize_text(row.get("source_check_status")),
        "correction_status": _correction_status(row),
        "needs_strict_human_review": True,
        "strict_human_review_decision": "",
        "strict_human_reviewer": "",
        "strict_human_reviewed_at": "",
        "strict_human_review_notes": "",
        "client_export_allowed": False,
    }
    return review_row


def build_review_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [build_strict_review_row(index, row) for index, row in enumerate(rows, start=1)]


def build_field_mapping() -> List[Dict[str, str]]:
    return [
        {"source_field": "queue_item_id", "review_field": "source_row_id", "note": "Prefer queue_item_id; fall back to review_item_id when missing."},
        {"source_field": "metric_standardized", "review_field": "metric_name / normalized_metric_name", "note": "Carry forward normalized metric naming from 344D."},
        {"source_field": "value_numeric", "review_field": "reported_value / normalized_value", "note": "Preserve the 344D normalized numeric value as text."},
        {"source_field": "normalized_unit", "review_field": "unit", "note": "Carry forward unit without enabling export approval."},
        {"source_field": "year_standardized", "review_field": "period", "note": "Preserve normalized period from 344D."},
        {"source_field": "source_pdf_name", "review_field": "source_document", "note": "Primary document locator."},
        {"source_field": "page_number", "review_field": "source_page", "note": "Primary page locator."},
        {"source_field": "image_path / table_id / source_text_snippet", "review_field": "source_evidence_ref", "note": "Conservative compatibility mapping for reviewer evidence reference."},
        {"source_field": "audit_labels", "review_field": "audit_label", "note": "Flatten audit labels into a readable text field."},
        {"source_field": "source_lineage_summary / expanded_trust_source", "review_field": "trust_status", "note": "Human-readable trust lineage summary."},
    ]


def build_checklist_rules() -> List[Dict[str, str]]:
    return [
        {"rule": "Check metric name correctness", "detail": "Confirm the normalized metric name matches the source evidence."},
        {"rule": "Check value correctness", "detail": "Confirm reported_value / normalized_value against source evidence."},
        {"rule": "Check unit correctness", "detail": "Verify unit is consistent with the source table and correction context."},
        {"rule": "Check period correctness", "detail": "Verify the period/year matches the source evidence."},
        {"rule": "Check source evidence support", "detail": "Use source_document / source_page / source_evidence_ref to verify the row."},
        {"rule": "Check correction reasonableness", "detail": "Rows with correction_status != empty require extra care, especially YOY/% rows."},
        {"rule": "Only edit strict human review fields", "detail": "Reviewers must edit only decision / reviewer / reviewed_at / notes fields."},
    ]


def build_evidence_context_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    context_rows: List[Dict[str, Any]] = []
    for row in rows:
        context_rows.append(
            {
                "queue_item_id": normalize_text(row.get("queue_item_id")),
                "review_item_id": normalize_text(row.get("review_item_id")),
                "source_lineage_stage": normalize_text(row.get("source_lineage_stage")),
                "source_lineage_summary": normalize_text(row.get("source_lineage_summary")),
                "metric_standardized": normalize_text(row.get("metric_standardized")),
                "year_standardized": normalize_text(row.get("year_standardized")),
                "value_numeric": normalize_text(row.get("value_numeric")),
                "normalized_unit": normalize_text(row.get("normalized_unit")),
                "source_pdf_name": normalize_text(row.get("source_pdf_name")),
                "page_number": normalize_text(row.get("page_number")),
                "table_id": normalize_text(row.get("table_id")),
                "bbox": normalize_text(row.get("bbox")),
                "image_path": normalize_text(row.get("image_path")),
                "source_text_snippet": normalize_text(row.get("source_text_snippet")),
                "source_check_status": normalize_text(row.get("source_check_status")),
                "expanded_export_scope": normalize_text(row.get("expanded_export_scope")),
                "export_usage": normalize_text(row.get("export_usage")),
            }
        )
    return context_rows


def build_output_artifact_rows(output_dir: Path) -> List[Dict[str, str]]:
    return [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "Core 344F manifest, decision, counts, compatibility mapping, and QA summary.",
        },
        {
            "artifact_name": WORKBOOK_FILE_NAME,
            "path": str(output_dir / WORKBOOK_FILE_NAME),
            "purpose": "Excel workbook packaging the same 29 strict review rows, evidence context, mapping, and gate sheets.",
        },
        {
            "artifact_name": REVIEW_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / REVIEW_ROWS_CSV_FILE_NAME),
            "purpose": "Fillable strict human review rows in CSV form for quick filtering and line-by-line review.",
        },
        {
            "artifact_name": REVIEW_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / REVIEW_ROWS_JSON_FILE_NAME),
            "purpose": "Machine-readable strict human review rows preserving all required review fields.",
        },
        {
            "artifact_name": REVIEWER_CHECKLIST_FILE_NAME,
            "path": str(output_dir / REVIEWER_CHECKLIST_FILE_NAME),
            "purpose": "Reviewer instructions, allowed edits, and strict human review boundary reminders.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_FILE_NAME),
            "purpose": "One-page summary of 344F inputs, counts, gate status, and next steps.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_FILE_NAME),
            "purpose": "Index of all 344F outputs and how each should be used.",
        },
        {
            "artifact_name": FINAL_GATE_SNAPSHOT_FILE_NAME,
            "path": str(output_dir / FINAL_GATE_SNAPSHOT_FILE_NAME),
            "purpose": "Strict review package gate snapshot confirming formal export remains blocked.",
        },
    ]
