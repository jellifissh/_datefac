from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.source_check_backlog_package_344a import (
    ALLOWED_SOURCE_CHECK_DECISIONS,
    EDITABLE_SOURCE_CHECK_COLUMNS_344A,
    EVIDENCE_COLUMNS_344A,
    REQUIRED_IDENTITY_COLUMNS_344A,
    SOURCE_CORRECT_REQUIRED_COLUMNS_344A,
)


WAITING_DECISION_344A2 = (
    "SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_WAITING_FOR_SOURCE_CHECK_REVIEW"
)
NOT_READY_DECISION_344A2 = "SOURCE_CHECK_EVIDENCE_ENRICHMENT_344A2_NOT_READY"
RECOMMENDED_344B_SCOPE_344A2 = (
    "source_check_evidence_review_result_ingestion_after_user_fills_workbook"
)

EVIDENCE_RESOLUTION_RESOLVED = "RESOLVED"
EVIDENCE_RESOLUTION_PARTIAL = "PARTIAL"
EVIDENCE_RESOLUTION_UNRESOLVED = "UNRESOLVED"

MATCH_CONFIDENCE_HIGH = "HIGH"
MATCH_CONFIDENCE_MEDIUM = "MEDIUM"
MATCH_CONFIDENCE_LOW = "LOW"

WORKBOOK_SHEETS_344A2 = [
    "00_README",
    "01_ENRICH_SUMMARY",
    "02_INPUT_344A_SUMMARY",
    "03_ENRICHED_BACKLOG",
    "04_REVIEW_TEMPLATE",
    "05_EVIDENCE_MAP",
    "06_MATCH_CANDIDATES",
    "07_UNRESOLVED_REPORT",
    "08_IMPORT_CONTRACT",
    "09_SCOPE_BOUNDARY",
    "10_NO_WRITE_BACK",
    "11_NEXT_STEPS",
]

REVIEW_TEMPLATE_WORKBOOK_SHEETS_344A2 = [
    "00_README",
    "04_REVIEW_TEMPLATE",
    "08_IMPORT_CONTRACT",
    "09_SCOPE_BOUNDARY",
    "11_NEXT_STEPS",
]

MATCH_APPLIED_FIELDS = [
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
]

ENRICHED_EVIDENCE_COLUMNS = EVIDENCE_COLUMNS_344A + [
    "match_type",
    "match_confidence",
    "match_reason",
]


def _strip_html_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _clean_bbox(value: Any) -> str:
    text = normalize_text(value)
    return text


def _to_int_if_possible(value: Any) -> Any:
    text = normalize_text(value)
    if text == "":
        return ""
    try:
        return int(float(text))
    except Exception:
        return text


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = normalize_text(value)
        if text != "":
            return text
    return ""


def _bool_or_default(value: Any, default: bool) -> bool:
    normalized = normalize_text(value).lower()
    if normalized == "":
        return default
    return normalize_bool(value)


def classify_evidence_resolution(item: Dict[str, Any]) -> tuple[str, str]:
    has_pdf_locator = any(
        normalize_text(item.get(field)) != ""
        for field in ["source_pdf_name", "source_pdf_path", "source_pdf_id"]
    )
    has_page = normalize_text(item.get("page_number")) != ""
    has_locator = any(
        normalize_text(item.get(field)) != ""
        for field in ["table_id", "cell_id", "bbox", "image_path"]
    )
    has_snippet = any(
        normalize_text(item.get(field)) != ""
        for field in ["source_text_snippet", "source_html_snippet"]
    )
    has_any = any(
        normalize_text(item.get(field)) != ""
        for field in ENRICHED_EVIDENCE_COLUMNS
        if field not in {"evidence_resolution_status", "evidence_gap_reason"}
    )
    if has_pdf_locator and has_page and (has_locator or has_snippet):
        return (EVIDENCE_RESOLUTION_RESOLVED, "")
    if has_any:
        missing: List[str] = []
        if not has_pdf_locator:
            missing.append("source_pdf locator")
        if not has_page:
            missing.append("page_number")
        if not (has_locator or has_snippet):
            missing.append("table/image/snippet locator")
        return (
            EVIDENCE_RESOLUTION_PARTIAL,
            "missing key source locator fields: " + ", ".join(missing),
        )
    return (
        EVIDENCE_RESOLUTION_UNRESOLVED,
        "source PDF/page/table evidence not present in scanned upstream artifacts",
    )


def build_search_keys(item: Dict[str, Any]) -> Dict[str, str]:
    return {
        "queue_item_id": normalize_text(item.get("queue_item_id")),
        "review_item_id": normalize_text(item.get("review_item_id")),
        "metric_standardized": normalize_text(item.get("metric_standardized")),
        "year_standardized": normalize_text(item.get("year_standardized")),
        "value_numeric": normalize_text(item.get("value_numeric")),
        "normalized_unit": normalize_text(item.get("normalized_unit")),
    }


def build_searchable_record(
    row: Dict[str, Any],
    *,
    source_stage: str,
    artifact_path: str,
    artifact_type: str,
    sheet_name: str = "",
    row_number: int = 0,
) -> Dict[str, Any]:
    metric_standardized = _first_non_empty(
        row.get("metric_standardized"),
        row.get("source_check_metric_standardized"),
        row.get("reviewer_metric_standardized"),
        row.get("original_metric_standardized"),
        row.get("metric_candidate_raw"),
    )
    year_standardized = _first_non_empty(
        row.get("year_standardized"),
        row.get("source_check_year_standardized"),
        row.get("reviewer_year_standardized"),
    )
    value_numeric = _first_non_empty(
        row.get("value_numeric"),
        row.get("source_check_value_numeric"),
        row.get("reviewer_value_numeric"),
    )
    normalized_unit = _first_non_empty(
        row.get("normalized_unit"),
        row.get("source_check_normalized_unit"),
        row.get("reviewer_normalized_unit"),
        row.get("original_normalized_unit"),
    )
    source_html_snippet = _first_non_empty(
        row.get("source_html_snippet"),
        row.get("evidence"),
        row.get("html"),
    )
    source_text_snippet = _first_non_empty(
        row.get("source_text_snippet"),
        row.get("row_text"),
        row.get("table_text"),
        row.get("evidence_text"),
        row.get("matched_text"),
        row.get("context_text"),
    )
    if source_text_snippet == "" and source_html_snippet != "":
        source_text_snippet = _strip_html_tags(source_html_snippet)
    return {
        "queue_item_id": _first_non_empty(row.get("queue_item_id"), row.get("item_id")),
        "review_item_id": _first_non_empty(
            row.get("review_item_id"),
            row.get("candidate_id"),
            row.get("source_candidate_id"),
        ),
        "candidate_id": _first_non_empty(
            row.get("source_row_id"),
            row.get("export_candidate_row_id"),
            row.get("row_id"),
        ),
        "metric_standardized": metric_standardized,
        "year_standardized": year_standardized,
        "value_numeric": value_numeric,
        "normalized_unit": normalized_unit,
        "source_pdf_name": _first_non_empty(
            row.get("source_pdf_name"),
            row.get("file_name"),
            row.get("pdf_name"),
            row.get("source_file_name"),
        ),
        "source_pdf_path": _first_non_empty(
            row.get("source_pdf_path"),
            row.get("pdf_path"),
            row.get("source_file"),
        ),
        "source_pdf_id": _first_non_empty(
            row.get("source_pdf_id"),
            row.get("corpus_pdf_id"),
            row.get("pdf_id"),
        ),
        "page_number": _to_int_if_possible(
            _first_non_empty(
                row.get("page_number"),
                row.get("source_page"),
                row.get("page_idx"),
                row.get("page"),
            )
        ),
        "table_id": _first_non_empty(row.get("table_id")),
        "cell_id": _first_non_empty(row.get("cell_id")),
        "bbox": _clean_bbox(_first_non_empty(row.get("bbox"))),
        "image_path": _first_non_empty(row.get("image_path"), row.get("table_image_path")),
        "source_text_snippet": source_text_snippet,
        "source_html_snippet": source_html_snippet,
        "metric_candidate_raw": _first_non_empty(
            row.get("metric_candidate_raw"),
            row.get("metric_standardized"),
        ),
        "evidence_source_stage": source_stage,
        "evidence_source_artifact": artifact_path,
        "source_artifact_path": _first_non_empty(row.get("source_artifact_path"), artifact_path),
        "source_artifact_sheet": _first_non_empty(row.get("source_artifact_sheet"), sheet_name),
        "source_row_id": _first_non_empty(
            row.get("source_row_id"),
            row.get("export_candidate_row_id"),
            row.get("row_id"),
            str(row_number) if row_number else "",
        ),
        "matched_artifact_type": artifact_type,
        "matched_sheet_or_line": _first_non_empty(sheet_name, str(row_number) if row_number else ""),
    }


def build_match_candidate(
    item: Dict[str, Any],
    record: Dict[str, Any],
    *,
    match_type: str,
    match_confidence: str,
    match_reason: str,
) -> Dict[str, Any]:
    candidate = {
        "backlog_item_key": normalize_text(item.get("backlog_item_key")),
        "queue_item_id": normalize_text(item.get("queue_item_id")),
        "review_item_id": normalize_text(item.get("review_item_id")),
        "match_type": match_type,
        "match_confidence": match_confidence,
        "match_reason": match_reason,
        "matched_artifact_path": normalize_text(record.get("evidence_source_artifact")),
        "matched_artifact_type": normalize_text(record.get("matched_artifact_type")),
        "matched_sheet_or_line": normalize_text(record.get("matched_sheet_or_line")),
    }
    for field in MATCH_APPLIED_FIELDS:
        candidate[field] = record.get(field, "")
    return candidate


def apply_match_to_item(
    base_item: Dict[str, Any],
    match_candidate: Dict[str, Any] | None,
) -> Dict[str, Any]:
    item = dict(base_item)
    item["match_type"] = ""
    item["match_confidence"] = ""
    item["match_reason"] = ""
    if match_candidate is not None:
        for field in MATCH_APPLIED_FIELDS:
            if normalize_text(item.get(field)) == "" and normalize_text(match_candidate.get(field)) != "":
                item[field] = match_candidate.get(field)
        item["match_type"] = normalize_text(match_candidate.get("match_type"))
        item["match_confidence"] = normalize_text(match_candidate.get("match_confidence"))
        item["match_reason"] = normalize_text(match_candidate.get("match_reason"))
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
        "contract_version": "344A2.source_check_evidence_enrichment.v1",
        "source_review_queue_schema_version": review_queue_schema_version,
        "required_sheet_name": "04_REVIEW_TEMPLATE",
        "required_identity_columns": REQUIRED_IDENTITY_COLUMNS_344A,
        "enriched_evidence_columns": ENRICHED_EVIDENCE_COLUMNS,
        "editable_source_check_columns": EDITABLE_SOURCE_CHECK_COLUMNS_344A,
        "allowed_source_check_decisions": ALLOWED_SOURCE_CHECK_DECISIONS,
        "source_correct_required_columns": SOURCE_CORRECT_REQUIRED_COLUMNS_344A,
        "expected_input_path_pattern": "D:/_datefac/input/review_queue_source_check_evidence_344a2_filled/*.xlsx",
        "waiting_for_source_check_review": True,
        "source_check_result_ingested": False,
        "recommended_output_dir_hint": output_dir_hint,
    }


def build_match_confidence_rows(candidates: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for candidate in candidates:
        rows.append(
            {
                "backlog_item_key": normalize_text(candidate.get("backlog_item_key")),
                "queue_item_id": normalize_text(candidate.get("queue_item_id")),
                "review_item_id": normalize_text(candidate.get("review_item_id")),
                "match_type": normalize_text(candidate.get("match_type")),
                "match_confidence": normalize_text(candidate.get("match_confidence")),
                "match_reason": normalize_text(candidate.get("match_reason")),
                "matched_artifact_path": normalize_text(candidate.get("matched_artifact_path")),
                "matched_sheet_or_line": normalize_text(candidate.get("matched_sheet_or_line")),
            }
        )
    return rows


def build_resolution_map_payload(items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in items:
        rows.append(
            {
                "backlog_item_key": normalize_text(item.get("backlog_item_key")),
                "queue_item_id": normalize_text(item.get("queue_item_id")),
                "review_item_id": normalize_text(item.get("review_item_id")),
                "evidence_resolution_status": normalize_text(item.get("evidence_resolution_status")),
                "evidence_gap_reason": normalize_text(item.get("evidence_gap_reason")),
                "source_pdf_name": normalize_text(item.get("source_pdf_name")),
                "page_number": normalize_text(item.get("page_number")),
                "table_id": normalize_text(item.get("table_id")),
                "image_path": normalize_text(item.get("image_path")),
                "match_type": normalize_text(item.get("match_type")),
                "match_confidence": normalize_text(item.get("match_confidence")),
                "evidence_source_stage": normalize_text(item.get("evidence_source_stage")),
                "evidence_source_artifact": normalize_text(item.get("evidence_source_artifact")),
            }
        )
    return {
        "items": rows,
        "resolved_count": sum(
            1
            for row in rows
            if row["evidence_resolution_status"] == EVIDENCE_RESOLUTION_RESOLVED
        ),
        "partial_count": sum(
            1
            for row in rows
            if row["evidence_resolution_status"] == EVIDENCE_RESOLUTION_PARTIAL
        ),
        "unresolved_count": sum(
            1
            for row in rows
            if row["evidence_resolution_status"] == EVIDENCE_RESOLUTION_UNRESOLVED
        ),
    }


def build_unresolved_rows(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        dict(item)
        for item in items
        if normalize_text(item.get("evidence_resolution_status"))
        == EVIDENCE_RESOLUTION_UNRESOLVED
    ]


def decisions_blank(rows: Iterable[Dict[str, Any]]) -> bool:
    for row in rows:
        if any(normalize_text(row.get(field)) != "" for field in EDITABLE_SOURCE_CHECK_COLUMNS_344A):
            return False
    return True


def build_reviewer_instruction_rows(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "step": "open_04_review_template",
            "instruction": "Open 04_REVIEW_TEMPLATE and review only the 19 backlog rows in this package.",
        },
        {
            "step": "inspect_locator_fields",
            "instruction": "Use source_pdf_name, page_number, table_id, bbox, image_path, and snippets before making any source-check decision.",
        },
        {
            "step": "keep_decision_blank_until_review",
            "instruction": "344A2 prefilled no source_check_decision; reviewer must decide manually after inspecting evidence.",
        },
        {
            "step": "preserve_waiting_state",
            "instruction": f"Current task stays waiting_for_source_check_review={summary.get('waiting_for_source_check_review', False)} until a filled workbook is later ingested.",
        },
    ]


def build_next_steps_rows() -> List[Dict[str, str]]:
    return [
        {
            "step": "open_enriched_review_template",
            "recommendation": "Open the enriched review template and sort by evidence_resolution_status to prioritize RESOLVED rows first.",
        },
        {
            "step": "review_partial_or_unresolved_rows",
            "recommendation": "For PARTIAL or UNRESOLVED rows, inspect match candidates and unresolved report before deciding whether evidence is sufficient.",
        },
        {
            "step": "save_filled_workbook",
            "recommendation": "Save the filled workbook under D:/_datefac/input/review_queue_source_check_evidence_344a2_filled/ for later 344B ingestion.",
        },
        {
            "step": "do_not_claim_export_readiness",
            "recommendation": "Do not treat this evidence enrichment package as formal client export or production-ready output.",
        },
    ]


def build_scope_boundary_lines() -> List[str]:
    return [
        "344A2 only enriches evidence fields for existing source-check backlog rows.",
        "344A2 does not confirm, correct, reject, or defer any row automatically.",
        "344A2 does not write back to upstream workbooks or production assets.",
        "formal_client_export_allowed must remain false.",
        "client_ready must remain false.",
        "production_ready must remain false.",
        "ready_for_344b remains false until the user fills the enriched review workbook.",
    ]

