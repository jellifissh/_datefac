from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.strict_human_review_package_343i import (
    ALLOWED_STRICT_REVIEW_DECISIONS,
    EDITABLE_STRICT_REVIEW_COLUMNS,
    REQUIRED_IDENTITY_COLUMNS,
    STRICT_CORRECT_REQUIRED_COLUMNS,
)


READY_DECISION_343I2 = "SOURCE_EVIDENCE_ENRICHMENT_343I2_WAITING_FOR_STRICT_REVIEW"
NOT_READY_DECISION_343I2 = "SOURCE_EVIDENCE_ENRICHMENT_343I2_NOT_READY"
RECOMMENDED_343J_SCOPE_343I2 = (
    "strict_human_review_result_ingestion_after_user_fills_enriched_workbook"
)

EVIDENCE_RESOLUTION_RESOLVED = "RESOLVED"
EVIDENCE_RESOLUTION_PARTIAL = "PARTIAL"
EVIDENCE_RESOLUTION_UNRESOLVED = "UNRESOLVED"

EVIDENCE_LOCATOR_COLUMNS = [
    "source_stage",
    "source_artifact_path",
    "source_artifact_sheet",
    "source_row_id",
    "source_detail_level",
    "source_pdf_id",
    "source_pdf_name",
    "source_pdf_path",
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
    "evidence_resolution_status",
    "evidence_gap_reason",
]

WORKBOOK_SHEETS_343I2 = [
    "00_README",
    "01_ENRICH_SUMMARY",
    "02_INPUT_343I_SUMMARY",
    "03_ENRICHED_ITEMS",
    "04_REVIEW_TEMPLATE",
    "05_EVIDENCE_FIELDS",
    "06_RESOLUTION_MAP",
    "07_UNRESOLVED_EVIDENCE",
    "08_DECISION_GUIDE",
    "09_IMPORT_CONTRACT",
    "10_343J_READINESS",
    "11_NO_WRITE_BACK",
    "12_NEXT_STEPS",
]


def _strip_html_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _to_int_if_possible(value: Any) -> Any:
    text = normalize_text(value)
    if text == "":
        return ""
    try:
        return int(text)
    except Exception:
        return text


def classify_evidence_resolution(item: Dict[str, Any]) -> tuple[str, str]:
    has_pdf_name = normalize_text(item.get("source_pdf_name")) != ""
    has_page = normalize_text(item.get("page_number")) != ""
    has_locator = any(
        normalize_text(item.get(field)) != ""
        for field in ["table_id", "bbox", "image_path", "source_html_snippet", "source_text_snippet"]
    )
    has_any = any(
        normalize_text(item.get(field)) != ""
        for field in EVIDENCE_LOCATOR_COLUMNS
        if field not in {"evidence_resolution_status", "evidence_gap_reason"}
    )
    if has_pdf_name and has_page and has_locator:
        return (EVIDENCE_RESOLUTION_RESOLVED, "")
    if has_any:
        missing: List[str] = []
        if not has_pdf_name:
            missing.append("source_pdf_name")
        if not has_page:
            missing.append("page_number")
        if not has_locator:
            missing.append("table locator fields")
        return (
            EVIDENCE_RESOLUTION_PARTIAL,
            "missing key source locator fields: " + ", ".join(missing),
        )
    return (
        EVIDENCE_RESOLUTION_UNRESOLVED,
        "source PDF/page/table evidence not present in available upstream artifacts",
    )


def build_enriched_item(
    base_item: Dict[str, Any],
    *,
    reviewed_row_343d: Dict[str, Any] | None,
    export_row_342r: Dict[str, Any] | None,
) -> Dict[str, Any]:
    item = dict(base_item)

    reviewed = reviewed_row_343d or {}
    export_row = export_row_342r or {}

    item["source_stage"] = normalize_text(reviewed.get("source_stage"))
    item["source_artifact_path"] = normalize_text(reviewed.get("source_artifact_path"))
    item["source_artifact_sheet"] = normalize_text(reviewed.get("source_artifact_sheet"))
    item["source_row_id"] = normalize_text(reviewed.get("source_row_id"))
    item["source_detail_level"] = normalize_text(reviewed.get("source_detail_level"))
    item["source_pdf_id"] = normalize_text(reviewed.get("source_pdf_id")) or normalize_text(
        export_row.get("corpus_pdf_id")
    )
    item["source_pdf_name"] = normalize_text(export_row.get("file_name"))
    item["source_pdf_path"] = normalize_text(reviewed.get("source_pdf_path"))
    item["page_number"] = _to_int_if_possible(export_row.get("source_page"))
    item["table_id"] = normalize_text(export_row.get("table_id"))
    item["cell_id"] = normalize_text(reviewed.get("cell_id"))
    item["bbox"] = normalize_text(export_row.get("bbox"))
    item["image_path"] = normalize_text(export_row.get("image_path"))
    item["source_html_snippet"] = normalize_text(export_row.get("evidence"))
    item["source_text_snippet"] = _strip_html_tags(item["source_html_snippet"]) if item["source_html_snippet"] else ""
    item["metric_candidate_raw"] = normalize_text(export_row.get("metric_standardized"))

    for field in [
        "metric_standardized",
        "year_standardized",
        "value_numeric",
        "normalized_unit",
    ]:
        if normalize_text(item.get(field)) == "":
            item[field] = normalize_text(reviewed.get(field)) or normalize_text(export_row.get(field))

    item["evidence_source_stage"] = "342R" if export_row else ("343D" if reviewed else "")
    item["evidence_source_artifact"] = normalize_text(item.get("source_artifact_path"))
    if export_row:
        item["evidence_source_artifact"] = normalize_text(
            export_row.get("__source_artifact", item["evidence_source_artifact"])
        )

    status, gap_reason = classify_evidence_resolution(item)
    item["evidence_resolution_status"] = status
    item["evidence_gap_reason"] = gap_reason
    return item


def build_expected_import_contract(
    *,
    review_queue_schema_version: str,
    output_dir_hint: str,
) -> Dict[str, Any]:
    return {
        "contract_version": "343I2.source_evidence_enrichment.v1",
        "source_review_queue_schema_version": review_queue_schema_version,
        "required_sheet_name": "04_REVIEW_TEMPLATE",
        "required_identity_columns": REQUIRED_IDENTITY_COLUMNS,
        "source_evidence_columns": EVIDENCE_LOCATOR_COLUMNS,
        "editable_strict_review_columns": EDITABLE_STRICT_REVIEW_COLUMNS,
        "allowed_strict_review_decisions": ALLOWED_STRICT_REVIEW_DECISIONS,
        "strict_correct_required_columns": STRICT_CORRECT_REQUIRED_COLUMNS,
        "expected_input_path_pattern": "D:/_datefac/input/review_queue_strict_human_review_343i2_filled/*.xlsx",
        "waiting_for_strict_human_review": True,
        "strict_human_review_result_ingested": False,
        "recommended_output_dir_hint": output_dir_hint,
    }


def build_evidence_field_rows(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    items_list = list(items)
    for field in EVIDENCE_LOCATOR_COLUMNS:
        count = sum(1 for item in items_list if normalize_text(item.get(field)) != "")
        rows.append(
            {
                "field_name": field,
                "filled_count": count,
                "item_count": len(items_list),
                "description": "Evidence locator field carried into the enriched strict review package.",
            }
        )
    return rows


def build_resolution_map_rows(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in items:
        rows.append(
            {
                "queue_item_id": normalize_text(item.get("queue_item_id")),
                "review_item_id": normalize_text(item.get("review_item_id")),
                "source_row_id": normalize_text(item.get("source_row_id")),
                "source_pdf_id": normalize_text(item.get("source_pdf_id")),
                "source_pdf_name": normalize_text(item.get("source_pdf_name")),
                "page_number": normalize_text(item.get("page_number")),
                "table_id": normalize_text(item.get("table_id")),
                "evidence_resolution_status": normalize_text(
                    item.get("evidence_resolution_status")
                ),
                "evidence_source_stage": normalize_text(item.get("evidence_source_stage")),
                "evidence_source_artifact": normalize_text(
                    item.get("evidence_source_artifact")
                ),
                "evidence_gap_reason": normalize_text(item.get("evidence_gap_reason")),
            }
        )
    return rows


def build_unresolved_items(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        dict(item)
        for item in items
        if normalize_text(item.get("evidence_resolution_status"))
        == EVIDENCE_RESOLUTION_UNRESOLVED
    ]


def build_decision_guide_rows() -> List[Dict[str, str]]:
    return [
        {
            "evidence_resolution_status": "RESOLVED",
            "reviewer_guidance": "Reviewer can inspect the located PDF/page/table evidence before deciding.",
            "recommended_default": "Any STRICT_* decision based on actual verification.",
        },
        {
            "evidence_resolution_status": "PARTIAL",
            "reviewer_guidance": "Evidence is incomplete; reviewer should prefer stricter re-check behavior.",
            "recommended_default": "STRICT_NEEDS_SOURCE_CHECK unless the reviewer can independently locate the missing evidence.",
        },
        {
            "evidence_resolution_status": "UNRESOLVED",
            "reviewer_guidance": "No sufficient source locator was found in available upstream artifacts.",
            "recommended_default": "STRICT_NEEDS_SOURCE_CHECK",
        },
    ]


def build_readiness_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "gate": "source_evidence_enrichment_completed",
            "value": summary.get("source_evidence_enrichment_completed", False),
            "meaning": "Enriched evidence locator package exists for user strict review.",
        },
        {
            "gate": "waiting_for_strict_human_review",
            "value": summary.get("waiting_for_strict_human_review", False),
            "meaning": "343I2 intentionally stops before ingestion.",
        },
        {
            "gate": "strict_human_review_result_ingested",
            "value": summary.get("strict_human_review_result_ingested", False),
            "meaning": "Must remain false until 343J.",
        },
        {
            "gate": "ready_for_343j",
            "value": summary.get("ready_for_343j", False),
            "meaning": "Must remain false until the user fills the enriched workbook.",
        },
        {
            "gate": "recommended_343j_scope",
            "value": summary.get("recommended_343j_scope", ""),
            "meaning": "Expected next ingestion scope after user fills the enriched workbook.",
        },
    ]


def build_next_steps_rows() -> List[Dict[str, str]]:
    return [
        {
            "step": "open_enriched_review_template",
            "recommendation": "Open the enriched strict human review template with PDF/page/table locator fields visible.",
        },
        {
            "step": "inspect_resolved_or_partial_evidence",
            "recommendation": "Use source_pdf_name, page_number, table_id, bbox, image_path, and snippets before deciding.",
        },
        {
            "step": "keep_unresolved_items_conservative",
            "recommendation": "For UNRESOLVED evidence rows, prefer STRICT_NEEDS_SOURCE_CHECK instead of confirmation.",
        },
        {
            "step": "save_filled_copy_for_343j",
            "recommendation": "Save the filled workbook under D:/_datefac/input/review_queue_strict_human_review_343i2_filled/ for later 343J ingestion.",
        },
    ]


def enriched_decisions_blank(rows: Iterable[Dict[str, Any]]) -> bool:
    for row in rows:
        if any(normalize_text(row.get(field)) for field in EDITABLE_STRICT_REVIEW_COLUMNS):
            return False
    return True


def build_resolution_map_payload(items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = build_resolution_map_rows(items)
    return {
        "resolution_rows": rows,
        "resolved_count": sum(
            1 for row in rows if row["evidence_resolution_status"] == EVIDENCE_RESOLUTION_RESOLVED
        ),
        "partial_count": sum(
            1 for row in rows if row["evidence_resolution_status"] == EVIDENCE_RESOLUTION_PARTIAL
        ),
        "unresolved_count": sum(
            1 for row in rows if row["evidence_resolution_status"] == EVIDENCE_RESOLUTION_UNRESOLVED
        ),
    }
