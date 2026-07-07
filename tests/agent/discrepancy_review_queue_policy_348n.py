"""Test-only discrepancy review queue policy prototype for R7AQ."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

AgreementStatus = Literal[
    "VERIFIED",
    "UNVERIFIED",
    "DISAGREED",
    "AMBIGUOUS",
    "MISSING_EVIDENCE",
    "PARSE_SKIPPED",
]

REVIEW_QUEUE_STATUSES: tuple[str, ...] = (
    "UNVERIFIED",
    "DISAGREED",
    "AMBIGUOUS",
    "MISSING_EVIDENCE",
    "PARSE_SKIPPED",
)

REVIEWER_ACTIONS: tuple[str, ...] = (
    "ACCEPT_CANDIDATE",
    "REJECT_CANDIDATE",
    "CORRECT_VALUE",
    "CORRECT_UNIT",
    "CORRECT_PERIOD",
    "CORRECT_METRIC",
    "MARK_NOT_IN_REPORT",
    "MARK_EVIDENCE_INSUFFICIENT",
    "REQUEST_REEXTRACTION",
    "REQUEST_MANUAL_SOURCE_CHECK",
    "SELECT_EVIDENCE",
)

MUTABLE_REVIEW_FIELDS: tuple[str, ...] = (
    "review_status",
    "reviewer_decision",
    "reviewer_corrected_value",
    "reviewer_corrected_unit",
    "reviewer_note",
    "clean_data_eligible",
)

REQUIRED_REVIEW_ITEM_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "source_document_id",
    "source_row_id",
    "candidate_metric_name",
    "candidate_period",
    "candidate_value",
    "candidate_unit",
    "candidate_page_number",
    "agreement_status",
    "source_text_status",
    "evidence_type",
    "matched_page_number",
    "matched_locator",
    "matched_block_index",
    "evidence_preview",
    "candidate_raw_text",
    "match_reason",
    "risk_reason",
    "suggested_action",
    "severity",
    "review_status",
    "reviewer_decision",
    "reviewer_corrected_value",
    "reviewer_corrected_unit",
    "reviewer_note",
    "audit_hash",
    "run_id",
    "adapter_version",
    "input_file_hashes",
    "clean_data_eligible",
)

SEVERITY_BY_STATUS: dict[str, str] = {
    "VERIFIED": "INFO",
    "UNVERIFIED": "MEDIUM",
    "DISAGREED": "HIGH",
    "AMBIGUOUS": "MEDIUM_HIGH",
    "MISSING_EVIDENCE": "MEDIUM",
    "PARSE_SKIPPED": "LOW",
}

REVIEW_SUBQUEUE_BY_STATUS: dict[str, str] = {
    "UNVERIFIED": "partial_anchor_queue",
    "DISAGREED": "evidence_conflict_queue",
    "AMBIGUOUS": "evidence_ambiguity_queue",
    "MISSING_EVIDENCE": "missing_evidence_queue",
    "PARSE_SKIPPED": "parse_schema_queue",
}


class DiscrepancyFixtureError(ValueError):
    """Raised when a test-only discrepancy fixture is malformed."""


def load_discrepancy_rows_fixture(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DiscrepancyFixtureError("fixture payload must be a JSON object")
    if payload.get("fixture_scope") != "test_only_r7aq":
        raise DiscrepancyFixtureError("fixture_scope must be test_only_r7aq")
    if not isinstance(payload.get("rows"), list):
        raise DiscrepancyFixtureError("rows must be a list")
    for row in payload["rows"]:
        _validate_row(row)
    return payload


def should_enter_discrepancy_review_queue(agreement_status: str) -> bool:
    return agreement_status in REVIEW_QUEUE_STATUSES


def candidate_clean_data_eligible(row: dict[str, Any]) -> bool:
    return False


def build_discrepancy_review_queue_items(
    rows: list[dict[str, Any]],
    *,
    run_id: str,
    adapter_version: str,
    input_file_hashes: dict[str, str],
    preview_limit: int = 160,
) -> list[dict[str, Any]]:
    return [
        item
        for row in rows
        if (item := build_discrepancy_review_item(
            row,
            run_id=run_id,
            adapter_version=adapter_version,
            input_file_hashes=input_file_hashes,
            preview_limit=preview_limit,
        ))
        is not None
    ]


def build_discrepancy_review_item(
    row: dict[str, Any],
    *,
    run_id: str,
    adapter_version: str,
    input_file_hashes: dict[str, str],
    preview_limit: int = 160,
) -> dict[str, Any] | None:
    _validate_row(row)
    agreement_status = _clean(row["agreement_status"])
    if not should_enter_discrepancy_review_queue(agreement_status):
        return None

    evidence_preview = _bounded_preview(row.get("evidence_preview", ""), preview_limit)
    candidate_raw_text = _bounded_preview(row.get("candidate_raw_text", ""), preview_limit)
    alternatives = _compact_alternatives(row.get("alternative_evidence_candidates", []), preview_limit)
    item_seed = {
        "run_id": run_id,
        "source_row_id": row.get("source_row_id", ""),
        "agreement_status": agreement_status,
        "candidate_value": row.get("candidate_value", ""),
        "matched_locator": row.get("matched_locator", ""),
        "matched_text_sha256": row.get("matched_text_sha256", ""),
    }
    review_item_id = "r7aq:" + _hash_json(item_seed)[:24]
    item: dict[str, Any] = {
        "review_item_id": review_item_id,
        "source_document_id": _clean(row.get("source_document_id")),
        "source_row_id": _clean(row.get("source_row_id")),
        "candidate_metric_name": _clean(row.get("candidate_metric_name")),
        "candidate_period": _clean(row.get("candidate_period")),
        "candidate_value": _clean(row.get("candidate_value")),
        "candidate_unit": _clean(row.get("candidate_unit")),
        "candidate_page_number": row.get("candidate_page_number"),
        "agreement_status": agreement_status,
        "source_text_status": _clean(row.get("source_text_status")),
        "evidence_type": _clean(row.get("evidence_type")),
        "matched_page_number": row.get("matched_page_number"),
        "matched_locator": _clean(row.get("matched_locator")),
        "matched_block_index": row.get("matched_block_index"),
        "evidence_preview": evidence_preview,
        "candidate_raw_text": candidate_raw_text,
        "match_reason": _clean(row.get("match_reason")),
        "risk_reason": _clean(row.get("risk_reason")),
        "suggested_action": _clean(row.get("suggested_action")),
        "severity": severity_for_row(row),
        "review_status": "OPEN",
        "reviewer_decision": "",
        "reviewer_corrected_value": "",
        "reviewer_corrected_unit": "",
        "reviewer_note": "",
        "audit_hash": "",
        "run_id": run_id,
        "adapter_version": adapter_version,
        "input_file_hashes": dict(input_file_hashes),
        "clean_data_eligible": False,
        "review_subqueue": REVIEW_SUBQUEUE_BY_STATUS[agreement_status],
        "discrepancy_subtype": discrepancy_subtype(row),
        "matched_text_sha256": _clean(row.get("matched_text_sha256")),
        "matched_char_count": row.get("matched_char_count"),
        "evidence_preview_sha256": _sha256(evidence_preview),
        "alternative_evidence_candidates": alternatives,
        "export_bucket": "discrepancy_review_output",
    }
    item["audit_hash"] = _hash_json({key: value for key, value in item.items() if key not in MUTABLE_REVIEW_FIELDS})
    _validate_review_item(item, preview_limit=preview_limit)
    return item


def severity_for_row(row: dict[str, Any]) -> str:
    agreement_status = _clean(row.get("agreement_status"))
    severity = SEVERITY_BY_STATUS.get(agreement_status, "MEDIUM")
    if row.get("core_metric") is True and severity in {"LOW", "MEDIUM"}:
        return "MEDIUM_HIGH"
    return severity


def discrepancy_subtype(row: dict[str, Any]) -> str:
    agreement_status = _clean(row.get("agreement_status"))
    evidence_type = _clean(row.get("evidence_type"))
    risk_reason = _clean(row.get("risk_reason")).lower()
    if agreement_status == "DISAGREED" and "vs" in evidence_type:
        return "TABLE_PARAGRAPH_CONFLICT"
    if agreement_status == "AMBIGUOUS" and ("repeat" in risk_reason or "duplicate" in risk_reason):
        return "REPEATED_AMBIGUOUS_VALUE"
    if agreement_status == "PARSE_SKIPPED":
        return "PARSE_SCHEMA_ISSUE"
    return agreement_status


def apply_reviewer_action(
    item: dict[str, Any],
    action: str,
    *,
    reviewer_note: str = "",
    reviewer_corrected_value: str = "",
    reviewer_corrected_unit: str = "",
    explicit_policy_gate: bool = False,
) -> dict[str, Any]:
    if action not in REVIEWER_ACTIONS:
        raise ValueError(f"unsupported reviewer action: {action}")

    updated = deepcopy(item)
    updated["reviewer_decision"] = action
    updated["reviewer_note"] = reviewer_note
    updated["reviewer_corrected_value"] = reviewer_corrected_value
    updated["reviewer_corrected_unit"] = reviewer_corrected_unit

    if action in {"REJECT_CANDIDATE", "MARK_NOT_IN_REPORT"}:
        updated["review_status"] = "RESOLVED_REJECTED"
    elif action in {"REQUEST_REEXTRACTION", "REQUEST_MANUAL_SOURCE_CHECK", "MARK_EVIDENCE_INSUFFICIENT"}:
        updated["review_status"] = "UNRESOLVED_NEEDS_SOURCE_CHECK"
    elif action.startswith("CORRECT_"):
        updated["review_status"] = "RESOLVED_CORRECTED"
    else:
        updated["review_status"] = "RESOLVED_ACCEPTED"

    updated["clean_data_eligible"] = bool(
        explicit_policy_gate
        and action in {"ACCEPT_CANDIDATE", "CORRECT_VALUE", "CORRECT_UNIT", "CORRECT_PERIOD", "CORRECT_METRIC", "SELECT_EVIDENCE"}
        and reviewer_note
    )
    return updated


def unresolved_export_bucket(item: dict[str, Any]) -> str:
    if item.get("clean_data_eligible") is True:
        return "requires_reaudit_before_clean_delivery"
    return "discrepancy_review_output"


def _validate_row(row: Any) -> None:
    if not isinstance(row, dict):
        raise DiscrepancyFixtureError("each row must be an object")
    required = {
        "source_document_id",
        "source_row_id",
        "candidate_metric_name",
        "candidate_period",
        "candidate_value",
        "agreement_status",
        "source_text_status",
        "evidence_type",
        "match_reason",
        "risk_reason",
        "suggested_action",
    }
    missing = sorted(field for field in required if field not in row)
    if missing:
        raise DiscrepancyFixtureError(f"row missing required fields: {missing}")
    status = _clean(row.get("agreement_status"))
    if status not in {"VERIFIED", *REVIEW_QUEUE_STATUSES}:
        raise DiscrepancyFixtureError(f"unsupported agreement_status: {status}")


def _validate_review_item(item: dict[str, Any], *, preview_limit: int) -> None:
    missing = sorted(field for field in REQUIRED_REVIEW_ITEM_FIELDS if field not in item)
    if missing:
        raise AssertionError(f"review item missing required fields: {missing}")
    if len(item["evidence_preview"]) > preview_limit:
        raise AssertionError("evidence_preview exceeds preview_limit")
    forbidden = {"source_text", "full_source_text", "source_text_full", "text"}
    if forbidden & set(item):
        raise AssertionError("review item contains forbidden full source text fields")


def _compact_alternatives(value: Any, preview_limit: int) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    alternatives: list[dict[str, Any]] = []
    for record in value[:5]:
        if not isinstance(record, dict):
            continue
        alternatives.append(
            {
                "source_text_id": _clean(record.get("source_text_id")),
                "page_number": record.get("page_number"),
                "locator": _clean(record.get("locator")),
                "text_sha256": _clean(record.get("text_sha256")),
                "evidence_type": _clean(record.get("evidence_type")),
                "preview": _bounded_preview(record.get("preview", ""), preview_limit),
            }
        )
    return alternatives


def _bounded_preview(value: Any, limit: int) -> str:
    normalized = " ".join(_clean(value).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 3)] + "..."


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256(payload)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
