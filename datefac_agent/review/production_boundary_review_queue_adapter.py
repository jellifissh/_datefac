"""Disabled production-boundary review queue adapter skeleton.

This module intentionally has no pipeline hook and performs no I/O. It only
validates already-built boundary output when explicitly enabled by tests.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Any

ADAPTER_CONTRACT_VERSION = "r7aw_disabled_production_boundary_adapter_skeleton_v1"
CREATED_FROM = "validated_discrepancy_boundary_output"
DEFAULT_PREVIEW_LIMIT = 160
TEST_ONLY_ENABLE_TOKEN = "R7AW_TEST_ONLY_ENABLE"

READINESS_GATES_CLOSED: dict[str, bool] = {
    "client_ready": False,
    "production_ready": False,
    "formal_client_export_allowed": False,
    "demo_export_only": True,
}

EXTERNAL_CALL_COUNTS_ZERO: dict[str, int] = {
    "mineru_run_count": 0,
    "ocr_run_count": 0,
    "llm_api_call_count": 0,
    "vlm_api_call_count": 0,
}

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

REQUIRED_BOUNDARY_OUTPUT_FIELDS: tuple[str, ...] = (
    "contract_version",
    "review_queue_items",
    "discrepancy_report_rows",
    "delivery_clean_candidates",
    "blocked_delivery_rows",
    "audit_metadata",
)

REQUIRED_AUDIT_METADATA_FIELDS: tuple[str, ...] = (
    "run_id",
    "adapter_version",
    "input_file_hashes",
    "comparison_row_count",
    "comparison_status_counts",
    "review_queue_count",
    "review_queue_status_counts",
    "discrepancy_report_count",
    "delivery_clean_candidate_count",
    "blocked_delivery_row_count",
    "verified_without_clean_gate_count",
    "readiness_gates",
    "external_call_counts",
    "boundary_flags",
    "audit_metadata_hash",
)

REQUIRED_REVIEW_ITEM_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "source_document_id",
    "source_row_id",
    "candidate_metric_name",
    "candidate_period",
    "candidate_value",
    "candidate_unit",
    "agreement_status",
    "risk_reason",
    "severity",
    "review_status",
    "reviewer_decision",
    "clean_data_eligible",
    "evidence_preview",
    "matched_locator",
    "run_id",
    "adapter_version",
    "input_file_hashes",
    "audit_hash",
    "review_subqueue",
)

REQUIRED_DISCREPANCY_REPORT_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "source_row_id",
    "candidate_metric_name",
    "candidate_period",
    "candidate_value",
    "candidate_unit",
    "agreement_status",
    "review_subqueue",
    "severity",
    "review_status",
    "reviewer_decision",
    "source_text_status",
    "evidence_type",
    "matched_locator",
    "matched_text_sha256",
    "evidence_preview",
    "risk_reason",
    "suggested_action",
)

REQUIRED_BLOCKED_DELIVERY_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "source_row_id",
    "agreement_status",
    "review_subqueue",
    "severity",
    "review_status",
    "reviewer_decision",
    "blocked_reason",
)

REQUIRED_DELIVERY_CANDIDATE_FIELDS: tuple[str, ...] = (
    "source_row_id",
    "source_document_id",
    "candidate_metric_name",
    "candidate_period",
    "candidate_value",
    "candidate_unit",
    "agreement_status",
    "delivery_gate_status",
    "delivery_clean_admitted",
    "requires_reaudit_before_clean_delivery",
    "run_id",
    "adapter_version",
    "input_file_hashes",
)

FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {
        "source_text",
        "full_source_text",
        "source_text_full",
        "full_text",
        "raw_source_text",
        "raw_mineru_block",
        "raw_mineru_artifact",
        "content_list_v2",
        "full_table_html",
        "raw_pdf_text",
        "raw_excel_row",
        "raw_datefac_excel_row",
        "datefac_excel_rows",
        "workbook_sheets",
        "worksheets",
        "cells",
        "blocks",
        "extracted_pages",
        "extracted_text",
        "html",
        "markdown",
        "mineru_output",
        "ocr_output",
        "page_texts",
        "parser_output",
        "pdf_parser_output",
        "pdf_pages",
        "raw_pdf_pages",
        "table_blocks",
        "tables",
        "text_layer",
    }
)


@dataclass(frozen=True, slots=True)
class ProductionBoundaryReviewQueueAdapterConfig:
    """Explicit feature flag for the inert R7AW adapter skeleton."""

    enabled: bool = False
    contract_version: str = ADAPTER_CONTRACT_VERSION
    test_only_enable_token: str = ""


class ProductionBoundaryReviewQueueAdapterError(ValueError):
    """Raised when the disabled adapter skeleton fails closed."""


def build_production_boundary_review_queue_adapter_output(
    payload: dict[str, Any],
    config: ProductionBoundaryReviewQueueAdapterConfig | None = None,
    *,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> dict[str, Any]:
    """Build in-memory adapter output only when explicitly test-enabled."""

    adapter_config = config or ProductionBoundaryReviewQueueAdapterConfig()
    _validate_config(adapter_config)
    if not adapter_config.enabled:
        return _disabled_result(adapter_config)
    if adapter_config.test_only_enable_token != TEST_ONLY_ENABLE_TOKEN:
        raise ProductionBoundaryReviewQueueAdapterError("explicit R7AW test-only enable token is required")

    validate_boundary_output_payload(payload, preview_limit=preview_limit)

    audit_metadata = payload["audit_metadata"]
    blocked_review_item_ids = {_clean(row.get("review_item_id")) for row in payload["blocked_delivery_rows"]}
    review_queue_candidate_items = [
        _review_queue_candidate_item(
            item,
            contract_version=adapter_config.contract_version,
            blocked_review_item_ids=blocked_review_item_ids,
            preview_limit=preview_limit,
        )
        for item in payload["review_queue_items"]
    ]
    discrepancy_report_candidate_rows = [
        _discrepancy_report_candidate_row(row, audit_metadata=audit_metadata, preview_limit=preview_limit)
        for row in payload["discrepancy_report_rows"]
    ]
    blocked_delivery_candidate_rows = [
        _blocked_delivery_candidate_row(row, audit_metadata=audit_metadata, contract_version=adapter_config.contract_version)
        for row in payload["blocked_delivery_rows"]
    ]
    delivery_reaudit_candidate_rows = [
        _delivery_reaudit_candidate_row(row, audit_metadata=audit_metadata, contract_version=adapter_config.contract_version)
        for row in payload["delivery_clean_candidates"]
    ]
    audit_contract = _audit_contract(
        payload=payload,
        config=adapter_config,
        review_queue_candidate_items=review_queue_candidate_items,
        discrepancy_report_candidate_rows=discrepancy_report_candidate_rows,
        blocked_delivery_candidate_rows=blocked_delivery_candidate_rows,
        delivery_reaudit_candidate_rows=delivery_reaudit_candidate_rows,
    )
    output = {
        "adapter_status": "ENABLED_TEST_ONLY",
        "review_queue_candidate_items": review_queue_candidate_items,
        "discrepancy_report_candidate_rows": discrepancy_report_candidate_rows,
        "blocked_delivery_candidate_rows": blocked_delivery_candidate_rows,
        "delivery_reaudit_candidate_rows": delivery_reaudit_candidate_rows,
        "audit_contract": audit_contract,
    }
    validate_no_forbidden_fields(output, preview_limit=preview_limit)
    return output


def validate_boundary_output_payload(payload: Any, *, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> None:
    """Validate the only accepted input shape for the skeleton."""

    if not isinstance(payload, dict):
        raise ProductionBoundaryReviewQueueAdapterError("boundary output must be an object")
    validate_no_forbidden_fields(payload, preview_limit=preview_limit)
    missing = [field for field in REQUIRED_BOUNDARY_OUTPUT_FIELDS if field not in payload]
    if missing:
        raise ProductionBoundaryReviewQueueAdapterError(f"boundary output missing required fields: {missing}")
    extra = sorted(set(payload) - set(REQUIRED_BOUNDARY_OUTPUT_FIELDS))
    if extra:
        raise ProductionBoundaryReviewQueueAdapterError(f"boundary output has unexpected fields: {extra}")
    if payload["contract_version"] != ADAPTER_CONTRACT_VERSION:
        raise ProductionBoundaryReviewQueueAdapterError("unexpected boundary output contract_version")
    for field in ("review_queue_items", "discrepancy_report_rows", "delivery_clean_candidates", "blocked_delivery_rows"):
        if not isinstance(payload[field], list):
            raise ProductionBoundaryReviewQueueAdapterError(f"{field} must be a list")
    _validate_audit_metadata(payload["audit_metadata"])

    metadata = payload["audit_metadata"]
    if len(payload["review_queue_items"]) != metadata["review_queue_count"]:
        raise ProductionBoundaryReviewQueueAdapterError("review_queue_count does not match review_queue_items")
    if len(payload["discrepancy_report_rows"]) != metadata["discrepancy_report_count"]:
        raise ProductionBoundaryReviewQueueAdapterError("discrepancy_report_count does not match discrepancy_report_rows")
    if len(payload["delivery_clean_candidates"]) != metadata["delivery_clean_candidate_count"]:
        raise ProductionBoundaryReviewQueueAdapterError("delivery_clean_candidate_count does not match delivery_clean_candidates")
    if len(payload["blocked_delivery_rows"]) != metadata["blocked_delivery_row_count"]:
        raise ProductionBoundaryReviewQueueAdapterError("blocked_delivery_row_count does not match blocked_delivery_rows")

    for item in payload["review_queue_items"]:
        _validate_review_item(item, metadata=metadata, preview_limit=preview_limit)
    for row in payload["discrepancy_report_rows"]:
        _validate_discrepancy_report_row(row, preview_limit=preview_limit)
    for row in payload["blocked_delivery_rows"]:
        _validate_blocked_delivery_row(row)
    for row in payload["delivery_clean_candidates"]:
        _validate_delivery_candidate_row(row, metadata=metadata)


def validate_no_forbidden_fields(value: Any, *, preview_limit: int = DEFAULT_PREVIEW_LIMIT, path: str = "$") -> None:
    """Recursively reject raw artifacts, full text, readiness, and clean mutations."""

    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                raise ProductionBoundaryReviewQueueAdapterError(f"forbidden field at {path}.{key}: {key}")
            if key == "evidence_level" and _clean(child) == "STRONG_EVIDENCE":
                raise ProductionBoundaryReviewQueueAdapterError("STRONG_EVIDENCE promotion is forbidden")
            if key in {"client_ready", "production_ready", "formal_client_export_allowed"} and child is True:
                raise ProductionBoundaryReviewQueueAdapterError(f"readiness gate opened at {path}.{key}")
            if key in {"delivery_clean_admitted", "clean_data_admitted"} and child is True:
                raise ProductionBoundaryReviewQueueAdapterError("clean delivery admission is forbidden")
            if key == "clean_data_eligible" and child is True:
                raise ProductionBoundaryReviewQueueAdapterError("clean_data eligibility is disabled in R7AW")
            if key == "production_hook" and child is True:
                raise ProductionBoundaryReviewQueueAdapterError("production hooks are forbidden")
            if key == "evidence_preview":
                _validate_bounded_preview(child, preview_limit)
            validate_no_forbidden_fields(child, preview_limit=preview_limit, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_no_forbidden_fields(child, preview_limit=preview_limit, path=f"{path}[{index}]")


def _validate_config(config: ProductionBoundaryReviewQueueAdapterConfig) -> None:
    if config.contract_version != ADAPTER_CONTRACT_VERSION:
        raise ProductionBoundaryReviewQueueAdapterError("unexpected adapter contract_version")


def _disabled_result(config: ProductionBoundaryReviewQueueAdapterConfig) -> dict[str, Any]:
    audit_contract = {
        "adapter_status": "DISABLED",
        "enabled": False,
        "contract_version": config.contract_version,
        "reason": "disabled_by_default",
        "review_queue_candidate_count": 0,
        "discrepancy_report_candidate_count": 0,
        "blocked_delivery_candidate_count": 0,
        "delivery_reaudit_candidate_count": 0,
        "clean_data_admitted_count": 0,
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        "external_call_counts": deepcopy(EXTERNAL_CALL_COUNTS_ZERO),
        "boundary_flags": {
            "production_hook": False,
            "writes_review_queue": False,
            "writes_clean_data": False,
            "writes_delivery": False,
            "verified_auto_clean": False,
            "verified_promotes_to_strong_evidence": False,
            "full_source_text_serialized": False,
        },
    }
    audit_contract["adapter_audit_hash"] = _hash_json(audit_contract)
    return {
        "adapter_status": "DISABLED",
        "review_queue_candidate_items": [],
        "discrepancy_report_candidate_rows": [],
        "blocked_delivery_candidate_rows": [],
        "delivery_reaudit_candidate_rows": [],
        "audit_contract": audit_contract,
    }


def _validate_audit_metadata(metadata: Any) -> None:
    if not isinstance(metadata, dict):
        raise ProductionBoundaryReviewQueueAdapterError("audit_metadata must be an object")
    missing = [field for field in REQUIRED_AUDIT_METADATA_FIELDS if field not in metadata]
    if missing:
        raise ProductionBoundaryReviewQueueAdapterError(f"audit_metadata missing required fields: {missing}")
    if not _clean(metadata.get("run_id")):
        raise ProductionBoundaryReviewQueueAdapterError("run_id is required")
    if not _clean(metadata.get("adapter_version")):
        raise ProductionBoundaryReviewQueueAdapterError("adapter_version is required")
    if not isinstance(metadata.get("input_file_hashes"), dict) or not metadata["input_file_hashes"]:
        raise ProductionBoundaryReviewQueueAdapterError("input_file_hashes must be a non-empty object")
    if not all(
        isinstance(key, str) and isinstance(value, str) and _clean(key) and _clean(value)
        for key, value in metadata["input_file_hashes"].items()
    ):
        raise ProductionBoundaryReviewQueueAdapterError("input_file_hashes must contain non-empty string keys and values")
    if not _clean(metadata.get("audit_metadata_hash")):
        raise ProductionBoundaryReviewQueueAdapterError("audit_metadata_hash is required")
    if metadata.get("readiness_gates") != READINESS_GATES_CLOSED:
        raise ProductionBoundaryReviewQueueAdapterError("readiness gates must remain closed")
    if metadata.get("external_call_counts") != EXTERNAL_CALL_COUNTS_ZERO:
        raise ProductionBoundaryReviewQueueAdapterError("external call counts must stay zero")
    boundary_flags = metadata.get("boundary_flags")
    if not isinstance(boundary_flags, dict):
        raise ProductionBoundaryReviewQueueAdapterError("boundary_flags must be an object")
    for key in (
        "production_hook",
        "verified_auto_clean",
        "verified_promotes_to_strong_evidence",
        "full_source_text_serialized",
    ):
        if boundary_flags.get(key) is True:
            raise ProductionBoundaryReviewQueueAdapterError(f"{key} is forbidden")
    if sum(metadata.get("comparison_status_counts", {}).values()) != metadata["comparison_row_count"]:
        raise ProductionBoundaryReviewQueueAdapterError("comparison status counts do not match comparison_row_count")
    if sum(metadata.get("review_queue_status_counts", {}).values()) != metadata["review_queue_count"]:
        raise ProductionBoundaryReviewQueueAdapterError("review_queue status counts do not match review_queue_count")


def _validate_review_item(item: Any, *, metadata: dict[str, Any], preview_limit: int) -> None:
    if not isinstance(item, dict):
        raise ProductionBoundaryReviewQueueAdapterError("review_queue_items must contain objects")
    missing = [field for field in REQUIRED_REVIEW_ITEM_FIELDS if field not in item]
    if missing:
        raise ProductionBoundaryReviewQueueAdapterError(f"review item missing required fields: {missing}")
    _validate_required_identity_fields(
        item,
        fields=("review_item_id", "source_row_id", "candidate_metric_name", "candidate_period", "candidate_value", "audit_hash"),
        row_label="review item",
    )
    if not isinstance(item["agreement_status"], str) or item["agreement_status"] not in REVIEW_QUEUE_STATUSES:
        raise ProductionBoundaryReviewQueueAdapterError(f"review item status must be non-VERIFIED: {item['agreement_status']}")
    if item.get("run_id") != metadata["run_id"]:
        raise ProductionBoundaryReviewQueueAdapterError("review item run_id mismatch")
    if item.get("adapter_version") != metadata["adapter_version"]:
        raise ProductionBoundaryReviewQueueAdapterError("review item adapter_version mismatch")
    if item.get("input_file_hashes") != metadata["input_file_hashes"]:
        raise ProductionBoundaryReviewQueueAdapterError("review item input_file_hashes mismatch")
    if item.get("clean_data_eligible") is True:
        raise ProductionBoundaryReviewQueueAdapterError("review item clean_data_eligible must remain false")
    _validate_review_status_action_alignment(
        _clean(item.get("review_status")),
        item.get("reviewer_decision"),
        row_label="review item",
    )
    reviewer_decision = _clean(item.get("reviewer_decision"))
    if reviewer_decision and reviewer_decision not in REVIEWER_ACTIONS:
        raise ProductionBoundaryReviewQueueAdapterError(f"unsupported reviewer action: {reviewer_decision}")
    _validate_required_bounded_preview(item.get("evidence_preview", ""), preview_limit)


def _validate_discrepancy_report_row(row: Any, *, preview_limit: int) -> None:
    if not isinstance(row, dict):
        raise ProductionBoundaryReviewQueueAdapterError("discrepancy_report_rows must contain objects")
    missing = [field for field in REQUIRED_DISCREPANCY_REPORT_FIELDS if field not in row]
    if missing:
        raise ProductionBoundaryReviewQueueAdapterError(f"discrepancy report row missing required fields: {missing}")
    _validate_required_identity_fields(
        row,
        fields=("review_item_id", "source_row_id", "candidate_metric_name", "candidate_period", "candidate_value"),
        row_label="discrepancy report row",
    )
    if not isinstance(row["agreement_status"], str) or row["agreement_status"] not in REVIEW_QUEUE_STATUSES:
        raise ProductionBoundaryReviewQueueAdapterError("discrepancy report rows must be non-VERIFIED")
    _validate_review_status_action_alignment(
        _clean(row.get("review_status")),
        row.get("reviewer_decision"),
        row_label="discrepancy report row",
    )
    reviewer_decision = _clean(row.get("reviewer_decision"))
    if reviewer_decision and reviewer_decision not in REVIEWER_ACTIONS:
        raise ProductionBoundaryReviewQueueAdapterError(f"unsupported reviewer action: {reviewer_decision}")
    _validate_required_bounded_preview(row.get("evidence_preview", ""), preview_limit)


def _validate_blocked_delivery_row(row: Any) -> None:
    if not isinstance(row, dict):
        raise ProductionBoundaryReviewQueueAdapterError("blocked_delivery_rows must contain objects")
    missing = [field for field in REQUIRED_BLOCKED_DELIVERY_FIELDS if field not in row]
    if missing:
        raise ProductionBoundaryReviewQueueAdapterError(f"blocked delivery row missing required fields: {missing}")
    _validate_required_identity_fields(
        row,
        fields=("review_item_id", "source_row_id"),
        row_label="blocked delivery row",
    )
    if not isinstance(row["agreement_status"], str) or row["agreement_status"] not in REVIEW_QUEUE_STATUSES:
        raise ProductionBoundaryReviewQueueAdapterError("blocked delivery rows must be non-VERIFIED")
    if _clean(row.get("review_status")).startswith("RESOLVED_"):
        raise ProductionBoundaryReviewQueueAdapterError("resolved rows must not be blocked delivery rows")
    if "delivery_blocked" in row and row["delivery_blocked"] is not True:
        raise ProductionBoundaryReviewQueueAdapterError("blocked delivery rows must stay delivery_blocked")
    _validate_review_status_action_alignment(
        _clean(row.get("review_status")),
        row.get("reviewer_decision"),
        row_label="blocked delivery row",
    )
    reviewer_decision = _clean(row.get("reviewer_decision"))
    if reviewer_decision and reviewer_decision not in REVIEWER_ACTIONS:
        raise ProductionBoundaryReviewQueueAdapterError(f"unsupported reviewer action: {reviewer_decision}")


def _validate_delivery_candidate_row(row: Any, *, metadata: dict[str, Any]) -> None:
    if not isinstance(row, dict):
        raise ProductionBoundaryReviewQueueAdapterError("delivery_clean_candidates must contain objects")
    missing = [field for field in REQUIRED_DELIVERY_CANDIDATE_FIELDS if field not in row]
    if missing:
        raise ProductionBoundaryReviewQueueAdapterError(f"delivery candidate missing required fields: {missing}")
    _validate_required_identity_fields(
        row,
        fields=("source_row_id", "candidate_metric_name", "candidate_period", "candidate_value"),
        row_label="delivery candidate",
    )
    if row.get("delivery_clean_admitted") is True:
        raise ProductionBoundaryReviewQueueAdapterError("delivery clean admission is forbidden")
    if row.get("requires_reaudit_before_clean_delivery") is not True:
        raise ProductionBoundaryReviewQueueAdapterError("delivery candidates must require re-audit")
    if row.get("run_id") != metadata["run_id"]:
        raise ProductionBoundaryReviewQueueAdapterError("delivery candidate run_id mismatch")
    if row.get("adapter_version") != metadata["adapter_version"]:
        raise ProductionBoundaryReviewQueueAdapterError("delivery candidate adapter_version mismatch")
    if row.get("input_file_hashes") != metadata["input_file_hashes"]:
        raise ProductionBoundaryReviewQueueAdapterError("delivery candidate input_file_hashes mismatch")
    agreement_status = _clean(row.get("agreement_status"))
    if agreement_status == "VERIFIED":
        return
    if agreement_status not in REVIEW_QUEUE_STATUSES:
        raise ProductionBoundaryReviewQueueAdapterError(f"unsupported delivery candidate agreement_status: {agreement_status}")
    if not _clean(row.get("review_item_id")):
        raise ProductionBoundaryReviewQueueAdapterError("non-VERIFIED delivery candidates require review_item_id")
    if not _clean(row.get("review_status")).startswith("RESOLVED_"):
        raise ProductionBoundaryReviewQueueAdapterError("unresolved non-VERIFIED delivery candidates are forbidden")
    _validate_review_status_action_alignment(
        _clean(row.get("review_status")),
        row.get("reviewer_decision"),
        row_label="delivery candidate",
    )
    reviewer_decision = _clean(row.get("reviewer_decision"))
    if not reviewer_decision or reviewer_decision not in REVIEWER_ACTIONS:
        raise ProductionBoundaryReviewQueueAdapterError("resolved non-VERIFIED delivery candidates require valid reviewer action")
    if row.get("delivery_gate_status") != "REQUIRES_REAUDIT_BEFORE_CLEAN_DELIVERY":
        raise ProductionBoundaryReviewQueueAdapterError("non-VERIFIED delivery candidates must be re-audit only")


def _validate_required_identity_fields(row: dict[str, Any], *, fields: tuple[str, ...], row_label: str) -> None:
    for field in fields:
        if not _clean(row.get(field)):
            raise ProductionBoundaryReviewQueueAdapterError(f"{row_label} {field} is required")


def _validate_review_status_action_alignment(review_status: str, reviewer_decision: Any, *, row_label: str) -> None:
    action = _clean(reviewer_decision)
    if action and action not in REVIEWER_ACTIONS:
        raise ProductionBoundaryReviewQueueAdapterError(f"unsupported reviewer action: {action}")
    if review_status == "OPEN" and action:
        raise ProductionBoundaryReviewQueueAdapterError(f"{row_label} OPEN review_status must not include reviewer_action")
    if review_status == "RESOLVED_CORRECTED" and not action.startswith("CORRECT_"):
        raise ProductionBoundaryReviewQueueAdapterError(f"{row_label} corrected review_status requires CORRECT_* action")
    if review_status == "RESOLVED_REJECTED" and action not in {"REJECT_CANDIDATE", "MARK_NOT_IN_REPORT"}:
        raise ProductionBoundaryReviewQueueAdapterError(f"{row_label} rejected review_status requires reject action")
    if review_status == "RESOLVED_ACCEPTED" and action not in {"ACCEPT_CANDIDATE", "SELECT_EVIDENCE"}:
        raise ProductionBoundaryReviewQueueAdapterError(f"{row_label} accepted review_status requires accept action")
    if review_status == "UNRESOLVED_NEEDS_SOURCE_CHECK" and action not in {
        "MARK_EVIDENCE_INSUFFICIENT",
        "REQUEST_REEXTRACTION",
        "REQUEST_MANUAL_SOURCE_CHECK",
    }:
        raise ProductionBoundaryReviewQueueAdapterError(f"{row_label} unresolved source check requires source-check action")


def _review_queue_candidate_item(
    item: dict[str, Any],
    *,
    contract_version: str,
    blocked_review_item_ids: set[str],
    preview_limit: int,
) -> dict[str, Any]:
    seed = {
        "contract_version": contract_version,
        "review_item_id": item["review_item_id"],
        "audit_hash": item["audit_hash"],
        "run_id": item["run_id"],
    }
    evidence_preview = _bounded_preview(item.get("evidence_preview", ""), preview_limit)
    return {
        "adapter_item_id": "r7aw:" + _hash_json(seed)[:24],
        "review_item_id": item["review_item_id"],
        "source_document_id": item["source_document_id"],
        "source_row_id": item["source_row_id"],
        "candidate_metric_name": item["candidate_metric_name"],
        "candidate_period": item["candidate_period"],
        "candidate_value": item["candidate_value"],
        "candidate_unit": item["candidate_unit"],
        "agreement_status": item["agreement_status"],
        "subqueue": item["review_subqueue"],
        "risk_reason": item["risk_reason"],
        "severity": item["severity"],
        "review_status": item["review_status"],
        "reviewer_action": _clean(item.get("reviewer_decision")),
        "clean_data_eligible": False,
        "delivery_blocked": item["review_item_id"] in blocked_review_item_ids,
        "evidence_preview": evidence_preview,
        "evidence_preview_sha256": _sha256(evidence_preview),
        "matched_locator": item["matched_locator"],
        "matched_text_sha256": _clean(item.get("matched_text_sha256")),
        "run_id": item["run_id"],
        "adapter_version": item["adapter_version"],
        "input_file_hashes": dict(item["input_file_hashes"]),
        "audit_hash": item["audit_hash"],
        "adapter_contract_version": contract_version,
        "created_from": CREATED_FROM,
    }


def _discrepancy_report_candidate_row(
    row: dict[str, Any],
    *,
    audit_metadata: dict[str, Any],
    preview_limit: int,
) -> dict[str, Any]:
    evidence_preview = _bounded_preview(row.get("evidence_preview", ""), preview_limit)
    return {
        "review_item_id": row["review_item_id"],
        "source_row_id": row["source_row_id"],
        "candidate_metric_name": row["candidate_metric_name"],
        "candidate_period": row["candidate_period"],
        "candidate_value": row["candidate_value"],
        "candidate_unit": row["candidate_unit"],
        "agreement_status": row["agreement_status"],
        "subqueue": row["review_subqueue"],
        "severity": row["severity"],
        "review_status": row["review_status"],
        "reviewer_action": _clean(row.get("reviewer_decision")),
        "source_text_status": row["source_text_status"],
        "evidence_type": row["evidence_type"],
        "matched_locator": row["matched_locator"],
        "matched_text_sha256": row["matched_text_sha256"],
        "evidence_preview": evidence_preview,
        "evidence_preview_sha256": _sha256(evidence_preview),
        "risk_reason": row["risk_reason"],
        "suggested_action": row["suggested_action"],
        "clean_data_eligible": False,
        "run_id": audit_metadata["run_id"],
        "adapter_version": audit_metadata["adapter_version"],
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "created_from": CREATED_FROM,
    }


def _blocked_delivery_candidate_row(
    row: dict[str, Any],
    *,
    audit_metadata: dict[str, Any],
    contract_version: str,
) -> dict[str, Any]:
    return {
        "review_item_id": row["review_item_id"],
        "source_row_id": row["source_row_id"],
        "agreement_status": row["agreement_status"],
        "subqueue": row["review_subqueue"],
        "severity": row["severity"],
        "review_status": row["review_status"],
        "reviewer_action": _clean(row.get("reviewer_decision")),
        "blocked_reason": row["blocked_reason"],
        "delivery_blocked": True,
        "run_id": audit_metadata["run_id"],
        "adapter_version": audit_metadata["adapter_version"],
        "adapter_contract_version": contract_version,
        "created_from": CREATED_FROM,
    }


def _delivery_reaudit_candidate_row(
    row: dict[str, Any],
    *,
    audit_metadata: dict[str, Any],
    contract_version: str,
) -> dict[str, Any]:
    if row.get("delivery_clean_admitted") is True:
        raise ProductionBoundaryReviewQueueAdapterError("delivery clean admission is forbidden")
    return {
        "review_item_id": _clean(row.get("review_item_id")),
        "source_row_id": row["source_row_id"],
        "agreement_status": row["agreement_status"],
        "review_status": _clean(row.get("review_status")),
        "reviewer_action": _clean(row.get("reviewer_decision")),
        "delivery_gate_status": row["delivery_gate_status"],
        "delivery_clean_admitted": False,
        "requires_reaudit_before_clean_delivery": True,
        "run_id": audit_metadata["run_id"],
        "adapter_version": audit_metadata["adapter_version"],
        "adapter_contract_version": contract_version,
        "created_from": CREATED_FROM,
    }


def _audit_contract(
    *,
    payload: dict[str, Any],
    config: ProductionBoundaryReviewQueueAdapterConfig,
    review_queue_candidate_items: list[dict[str, Any]],
    discrepancy_report_candidate_rows: list[dict[str, Any]],
    blocked_delivery_candidate_rows: list[dict[str, Any]],
    delivery_reaudit_candidate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    audit_metadata = payload["audit_metadata"]
    status_counts = Counter(item["agreement_status"] for item in review_queue_candidate_items)
    audit_contract: dict[str, Any] = {
        "adapter_status": "ENABLED_TEST_ONLY",
        "enabled": True,
        "contract_version": config.contract_version,
        "created_from": CREATED_FROM,
        "source_run_id": audit_metadata["run_id"],
        "run_id": audit_metadata["run_id"],
        "adapter_version": audit_metadata["adapter_version"],
        "input_file_hashes": dict(audit_metadata["input_file_hashes"]),
        "source_audit_metadata_hash": audit_metadata["audit_metadata_hash"],
        "review_queue_candidate_count": len(review_queue_candidate_items),
        "review_queue_candidate_status_counts": dict(status_counts),
        "discrepancy_report_candidate_count": len(discrepancy_report_candidate_rows),
        "blocked_delivery_candidate_count": len(blocked_delivery_candidate_rows),
        "delivery_reaudit_candidate_count": len(delivery_reaudit_candidate_rows),
        "verified_without_clean_gate_count": audit_metadata["verified_without_clean_gate_count"],
        "clean_data_admitted_count": 0,
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        "external_call_counts": deepcopy(EXTERNAL_CALL_COUNTS_ZERO),
        "boundary_flags": {
            "production_hook": False,
            "writes_review_queue": False,
            "writes_clean_data": False,
            "writes_delivery": False,
            "verified_auto_clean": False,
            "verified_promotes_to_strong_evidence": False,
            "full_source_text_serialized": False,
        },
    }
    audit_contract["adapter_audit_hash"] = _hash_json(audit_contract)
    return audit_contract


def _validate_bounded_preview(value: Any, preview_limit: int) -> None:
    if len(_clean(value)) > preview_limit:
        raise ProductionBoundaryReviewQueueAdapterError("evidence_preview exceeds preview_limit")


def _validate_required_bounded_preview(value: Any, preview_limit: int) -> None:
    if not _clean(value):
        raise ProductionBoundaryReviewQueueAdapterError("evidence_preview is required")
    _validate_bounded_preview(value, preview_limit)


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


__all__ = [
    "ADAPTER_CONTRACT_VERSION",
    "EXTERNAL_CALL_COUNTS_ZERO",
    "READINESS_GATES_CLOSED",
    "TEST_ONLY_ENABLE_TOKEN",
    "ProductionBoundaryReviewQueueAdapterConfig",
    "ProductionBoundaryReviewQueueAdapterError",
    "build_production_boundary_review_queue_adapter_output",
    "validate_boundary_output_payload",
]
