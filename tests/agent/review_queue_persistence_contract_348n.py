"""Test-only review_queue persistence contract for R7BL.

This module validates an R7BI schema alignment preview and maps it into an
in-memory persistence candidate batch. It performs no I/O, no DB writes, no
exports, and has no production hook.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from tests.agent.review_queue_writer_schema_alignment_contract_348n import (
    EXTERNAL_CALL_COUNTS_ZERO,
    FUTURE_REVIEW_QUEUE_SCHEMA_VERSION,
    READINESS_GATES_CLOSED,
    SCHEMA_ALIGNMENT_CONTRACT_VERSION,
)

PERSISTENCE_CONTRACT_VERSION = "r7bl_review_queue_persistence_contract_test_only_v1"
PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION = "review_queue_persistence_candidate_batch_test_only_v1"
TEST_ONLY_PERSISTENCE_ENABLE_TOKEN = "R7BL_TEST_ONLY_PERSISTENCE_ENABLE"
DEFAULT_PREVIEW_LIMIT = 160

ENABLED_STATUS = "ENABLED_TEST_ONLY_PERSISTENCE_CANDIDATE"
DISABLED_STATUS = "DISABLED"

REVIEW_BOUND_STATUSES: frozenset[str] = frozenset(
    {
        "UNVERIFIED",
        "DISAGREED",
        "AMBIGUOUS",
        "MISSING_EVIDENCE",
        "PARSE_SKIPPED",
    }
)

CORRECTIVE_REVIEWER_ACTIONS: frozenset[str] = frozenset(
    {
        "CORRECT_VALUE",
        "CORRECT_UNIT",
        "CORRECT_PERIOD",
        "CORRECT_METRIC",
    }
)

REQUIRED_SCHEMA_ALIGNMENT_FIELDS: tuple[str, ...] = (
    "schema_alignment_status",
    "dry_run_only",
    "schema_alignment_contract_version",
    "future_review_queue_schema_version",
    "integration_boundary_version",
    "writer_contract_version",
    "source_adapter_contract_version",
    "run_id",
    "adapter_version",
    "input_file_hashes",
    "field_classification",
    "future_review_queue_record_previews",
    "schema_alignment_summary",
)

REQUIRED_SCHEMA_RECORD_FIELDS: tuple[str, ...] = (
    "schema_version",
    "review_item_id",
    "run_id",
    "source_file_hash",
    "input_file_hashes",
    "adapter_version",
    "adapter_contract_version",
    "writer_contract_version",
    "source_document_id",
    "source_row_id",
    "metric_name",
    "period",
    "candidate_value",
    "candidate_unit",
    "normalized_candidate_value",
    "agreement_status",
    "review_status",
    "review_reason",
    "reviewer_action",
    "severity",
    "blocked_delivery_reason",
    "re_audit_required",
    "evidence_preview",
    "source_trace",
    "audit_hash",
    "idempotency_key",
    "record_payload_hash",
    "clean_data_eligible",
    "delivery_blocked",
)

REQUIRED_SOURCE_TRACE_FIELDS: tuple[str, ...] = (
    "source_document_id",
    "source_row_id",
    "adapter_item_id",
    "matched_locator",
    "matched_text_sha256",
    "subqueue",
    "evidence_preview_sha256",
)

REQUIRED_PERSISTENCE_CANDIDATE_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "run_id",
    "source_file_hash",
    "input_file_hashes",
    "adapter_version",
    "contract_version",
    "writer_contract_version",
    "schema_version",
    "audit_hash",
    "idempotency_key",
    "metric_name",
    "period",
    "candidate_value",
    "normalized_candidate_value",
    "agreement_status",
    "review_status",
    "review_reason",
    "reviewer_action",
    "blocked_delivery_reason",
    "re_audit_required",
    "evidence_preview",
    "source_trace",
    "created_by_system",
    "record_payload_hash",
)

FORBIDDEN_INPUT_KEYS: frozenset[str] = frozenset(
    {
        "source_text",
        "full_source_text",
        "source_text_full",
        "full_text",
        "raw_source_text",
        "raw_mineru",
        "raw_mineru_block",
        "raw_mineru_artifact",
        "content_list_v2",
        "full_table_html",
        "raw_pdf_text",
        "raw_excel",
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
        "raw_extraction_payload",
        "raw_parser_payload",
        "llm_response",
        "vlm_response",
        "raw_llm_response",
        "raw_vlm_response",
        "clean_data",
        "clean_data_record",
        "clean_data_records",
        "clean_data_payload",
        "clean_data_intent",
        "clean_data_write_intent",
        "delivery_payload",
        "delivery_export_intent",
        "delivery_write_intent",
        "export_payload",
        "export_intent",
        "formal_delivery_payload",
        "formal_export_payload",
        "formal_export_intent",
        "persistence_destination",
        "persistence_target",
        "storage_destination",
        "output_path",
        "export_path",
        "file_path",
        "filesystem_path",
        "storage_path",
        "database_url",
        "db_url",
        "dsn",
        "production_writer_config",
        "production_config",
        "writer_config",
        "direct_writer_preview",
        "user_provided_writer_preview",
        "adapter_candidate_output",
        "review_queue_candidate_items",
        "writer_dry_run_preview",
        "review_queue_dry_run_records",
        "review_queue_persistence_candidate_batch",
        "persistence_candidate",
        "persistence_candidate_rows",
        "user_direct_persistence_candidate",
        "test_only_enable_token",
        "test_only_writer_config",
        "test_only_persistence_config",
        "test_only_config",
        "database_id",
        "migration_id",
        "connection_string",
        "table_name",
        "database_table",
        "repository_class",
    }
)

FORBIDDEN_CANDIDATE_KEYS: frozenset[str] = frozenset(
    {
        "source_text",
        "full_source_text",
        "raw_source_text",
        "content_list_v2",
        "raw_excel_row",
        "clean_data",
        "clean_data_eligible",
        "clean_data_admitted",
        "delivery_clean_admitted",
        "delivery_payload",
        "export_payload",
        "production_writer_config",
        "test_only_enable_token",
        "database_id",
        "migration_id",
        "connection_string",
        "table_name",
    }
)

NON_DETERMINISTIC_KEYS: frozenset[str] = frozenset(
    {
        "created_at",
        "updated_at",
        "timestamp",
        "generated_at",
        "wall_clock_time",
        "execution_time",
        "run_started_at",
        "run_finished_at",
        "utcnow",
        "now",
        "created_at_policy",
        "timestamp_policy",
    }
)

SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ReviewQueuePersistenceContractConfig:
    """Explicit test-only feature flag for the R7BL persistence contract."""

    enabled: bool = False
    contract_version: str = PERSISTENCE_CONTRACT_VERSION
    test_only_enable_token: str = ""


class ReviewQueuePersistenceContractError(ValueError):
    """Raised when persistence candidate validation fails closed."""


def build_review_queue_persistence_candidate_batch(
    schema_alignment_preview: dict[str, Any],
    config: ReviewQueuePersistenceContractConfig | None = None,
    *,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> dict[str, Any]:
    """Return a deterministic in-memory review_queue persistence candidate batch."""

    contract_config = config or ReviewQueuePersistenceContractConfig()
    _validate_config(contract_config)
    if not contract_config.enabled:
        return _disabled_result(contract_config)
    if contract_config.test_only_enable_token != TEST_ONLY_PERSISTENCE_ENABLE_TOKEN:
        raise ReviewQueuePersistenceContractError("explicit R7BL test-only persistence enable token is required")

    validate_schema_alignment_preview(schema_alignment_preview, preview_limit=preview_limit)
    payload = deepcopy(schema_alignment_preview)
    records = payload["future_review_queue_record_previews"]
    candidates = [_persistence_candidate(record, contract_config=contract_config) for record in records]
    candidates.sort(key=lambda item: (item["run_id"], item["review_item_id"], item["idempotency_key"]))
    _validate_no_duplicate_idempotency(candidates)
    for candidate in candidates:
        _validate_persistence_candidate(candidate, preview_limit=preview_limit)
    summary = _persistence_summary(
        payload=payload,
        candidates=candidates,
        contract_config=contract_config,
    )
    output = {
        "persistence_status": ENABLED_STATUS,
        "in_memory_only": True,
        "persistence_candidate_only": True,
        "persistence_contract_version": contract_config.contract_version,
        "persistence_candidate_batch_schema_version": PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION,
        "source_schema_alignment_contract_version": payload["schema_alignment_contract_version"],
        "future_review_queue_schema_version": payload["future_review_queue_schema_version"],
        "run_id": payload["run_id"],
        "adapter_version": payload["adapter_version"],
        "input_file_hashes": deepcopy(payload["input_file_hashes"]),
        "review_queue_persistence_candidate_batch": candidates,
        "persistence_summary": summary,
    }
    return deepcopy(output)


def validate_schema_alignment_preview(value: Any, *, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> None:
    """Validate the only accepted input layer: R7BI schema alignment preview."""

    if not isinstance(value, dict):
        raise ReviewQueuePersistenceContractError("schema alignment preview must be an object")
    validate_no_forbidden_input_fields(value, preview_limit=preview_limit)
    _require_exact_fields(value, REQUIRED_SCHEMA_ALIGNMENT_FIELDS, "schema alignment preview")
    if value["schema_alignment_status"] != "ENABLED_TEST_ONLY_SCHEMA_ALIGNMENT":
        raise ReviewQueuePersistenceContractError("input must be enabled R7BI schema alignment preview")
    if value["dry_run_only"] is not True:
        raise ReviewQueuePersistenceContractError("schema alignment preview must remain dry_run_only")
    if value["schema_alignment_contract_version"] != SCHEMA_ALIGNMENT_CONTRACT_VERSION:
        raise ReviewQueuePersistenceContractError("unexpected schema alignment contract version")
    if value["future_review_queue_schema_version"] != FUTURE_REVIEW_QUEUE_SCHEMA_VERSION:
        raise ReviewQueuePersistenceContractError("unexpected future review_queue schema version")
    _validate_non_empty_string(value, "run_id", "schema alignment preview")
    _validate_non_empty_string(value, "adapter_version", "schema alignment preview")
    _validate_hash_identity(value.get("input_file_hashes"), "schema alignment input_file_hashes")
    if not isinstance(value["field_classification"], dict) or not value["field_classification"]:
        raise ReviewQueuePersistenceContractError("field_classification is required")
    records = value["future_review_queue_record_previews"]
    if not isinstance(records, list):
        raise ReviewQueuePersistenceContractError("future_review_queue_record_previews must be a list")
    summary = value["schema_alignment_summary"]
    _validate_schema_alignment_summary(summary, value=value)
    if summary["future_preview_record_count"] != len(records):
        raise ReviewQueuePersistenceContractError("schema alignment record count mismatch")
    seen_review_item_ids: set[str] = set()
    seen_idempotency_keys: set[str] = set()
    for record in records:
        if isinstance(record, dict):
            idempotency_key = record.get("idempotency_key")
            if isinstance(idempotency_key, str) and idempotency_key in seen_idempotency_keys:
                raise ReviewQueuePersistenceContractError("duplicate idempotency_key rejected")
            if isinstance(idempotency_key, str):
                seen_idempotency_keys.add(idempotency_key)
        _validate_schema_record(record, parent=value, preview_limit=preview_limit)
        review_item_id = record["review_item_id"]
        if review_item_id in seen_review_item_ids:
            raise ReviewQueuePersistenceContractError("duplicate review_item_id rejected")
        seen_review_item_ids.add(review_item_id)
    _validate_summary_record_counts(summary, records=records)
    _validate_schema_alignment_preview_hash(summary, records=records)


def validate_no_forbidden_input_fields(
    value: Any,
    *,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
    path: str = "$",
) -> None:
    """Reject raw artifacts, write intents, production configs, and opened gates."""

    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_INPUT_KEYS:
                raise ReviewQueuePersistenceContractError(f"forbidden field at {path}.{key}: {key}")
            if key in NON_DETERMINISTIC_KEYS:
                raise ReviewQueuePersistenceContractError(f"non-deterministic field at {path}.{key}: {key}")
            if key == "evidence_level" and _clean(child) == "STRONG_EVIDENCE":
                raise ReviewQueuePersistenceContractError("STRONG_EVIDENCE promotion is forbidden")
            if key in {"client_ready", "production_ready", "formal_client_export_allowed"} and child is True:
                raise ReviewQueuePersistenceContractError(f"readiness gate opened at {path}.{key}")
            if key in {"clean_data_eligible", "clean_data_admitted", "delivery_clean_admitted"} and child is True:
                raise ReviewQueuePersistenceContractError("clean_data or delivery admission is forbidden")
            if key in {
                "writes_review_queue",
                "writes_clean_data",
                "writes_delivery",
                "writes_filesystem",
                "writes_database",
                "writes_export",
            } and child is True:
                raise ReviewQueuePersistenceContractError(f"write intent is forbidden at {path}.{key}")
            if key == "production_hook" and child is True:
                raise ReviewQueuePersistenceContractError("production hooks are forbidden")
            if key == "evidence_preview":
                _validate_bounded_preview(child, preview_limit)
            validate_no_forbidden_input_fields(child, preview_limit=preview_limit, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_no_forbidden_input_fields(child, preview_limit=preview_limit, path=f"{path}[{index}]")


def required_persistence_candidate_fields() -> tuple[str, ...]:
    """Return required persistence candidate fields for tests and reports."""

    return REQUIRED_PERSISTENCE_CANDIDATE_FIELDS


def _validate_config(config: ReviewQueuePersistenceContractConfig) -> None:
    if config.contract_version != PERSISTENCE_CONTRACT_VERSION:
        raise ReviewQueuePersistenceContractError("unexpected persistence contract version")


def _disabled_result(config: ReviewQueuePersistenceContractConfig) -> dict[str, Any]:
    return {
        "persistence_status": DISABLED_STATUS,
        "enabled": False,
        "in_memory_only": True,
        "persistence_candidate_only": True,
        "persistence_contract_version": config.contract_version,
        "review_queue_persistence_candidate_batch": [],
        "persistence_summary": {
            "persistence_status": DISABLED_STATUS,
            "enabled": False,
            "reason": "disabled_by_default",
            "candidate_count": 0,
            "clean_data_write_count": 0,
            "delivery_write_count": 0,
            "filesystem_write_count": 0,
            "database_write_count": 0,
            "export_write_count": 0,
            "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
            "external_call_counts": deepcopy(EXTERNAL_CALL_COUNTS_ZERO),
            "boundary_flags": _closed_boundary_flags(),
            "validation_errors": [],
        },
    }


def _validate_schema_alignment_summary(summary: Any, *, value: dict[str, Any]) -> None:
    if not isinstance(summary, dict):
        raise ReviewQueuePersistenceContractError("schema_alignment_summary must be an object")
    for field in (
        "schema_alignment_status",
        "enabled",
        "dry_run_only",
        "schema_alignment_contract_version",
        "future_review_queue_schema_version",
        "run_id",
        "adapter_version",
        "input_file_hashes",
        "future_preview_record_count",
        "clean_data_write_count",
        "delivery_write_count",
        "filesystem_write_count",
        "database_write_count",
        "export_write_count",
        "readiness_gates",
        "external_call_counts",
        "boundary_flags",
        "validation_errors",
        "schema_alignment_preview_hash",
    ):
        if field not in summary:
            raise ReviewQueuePersistenceContractError(f"schema_alignment_summary {field} is required")
    if summary["schema_alignment_status"] != value["schema_alignment_status"]:
        raise ReviewQueuePersistenceContractError("schema alignment status mismatch")
    if summary["enabled"] is not True or summary["dry_run_only"] is not True:
        raise ReviewQueuePersistenceContractError("schema alignment summary must be enabled dry-run")
    if summary["schema_alignment_contract_version"] != value["schema_alignment_contract_version"]:
        raise ReviewQueuePersistenceContractError("schema alignment summary contract mismatch")
    if summary["future_review_queue_schema_version"] != value["future_review_queue_schema_version"]:
        raise ReviewQueuePersistenceContractError("schema alignment summary schema mismatch")
    if summary["run_id"] != value["run_id"] or summary["adapter_version"] != value["adapter_version"]:
        raise ReviewQueuePersistenceContractError("schema alignment summary metadata mismatch")
    if summary["input_file_hashes"] != value["input_file_hashes"]:
        raise ReviewQueuePersistenceContractError("schema alignment summary input_file_hashes mismatch")
    if summary["readiness_gates"] != READINESS_GATES_CLOSED:
        raise ReviewQueuePersistenceContractError("readiness gates must remain CLOSED")
    if summary["external_call_counts"] != EXTERNAL_CALL_COUNTS_ZERO:
        raise ReviewQueuePersistenceContractError("external call counts must stay zero")
    if summary["validation_errors"] != []:
        raise ReviewQueuePersistenceContractError("schema alignment summary must have no validation errors")
    for key in ("clean_data_write_count", "delivery_write_count", "filesystem_write_count", "database_write_count", "export_write_count"):
        if summary.get(key) != 0:
            raise ReviewQueuePersistenceContractError(f"{key} must remain zero")
    if not _boundary_flags_are_closed(summary["boundary_flags"]):
        raise ReviewQueuePersistenceContractError("schema alignment boundary flags must remain closed")


def _validate_schema_record(record: Any, *, parent: dict[str, Any], preview_limit: int) -> None:
    if not isinstance(record, dict):
        raise ReviewQueuePersistenceContractError("future_review_queue_record_previews must contain objects")
    _require_exact_fields(record, REQUIRED_SCHEMA_RECORD_FIELDS, "future review_queue record preview")
    for field in (
        "review_item_id",
        "run_id",
        "source_file_hash",
        "adapter_version",
        "writer_contract_version",
        "metric_name",
        "period",
        "candidate_value",
        "agreement_status",
        "review_status",
        "review_reason",
        "audit_hash",
        "idempotency_key",
        "record_payload_hash",
    ):
        _validate_non_empty_string(record, field, "future review_queue record preview")
    for field in (
        "review_item_id",
        "run_id",
        "source_file_hash",
        "adapter_version",
        "writer_contract_version",
        "metric_name",
        "period",
        "candidate_value",
        "normalized_candidate_value",
    ):
        _validate_string_field(record, field, "future review_queue record preview")
    if record["schema_version"] != parent["future_review_queue_schema_version"]:
        raise ReviewQueuePersistenceContractError("record schema_version mismatch")
    if record["run_id"] != parent["run_id"]:
        raise ReviewQueuePersistenceContractError("record run_id mismatch")
    if record["adapter_version"] != parent["adapter_version"]:
        raise ReviewQueuePersistenceContractError("record adapter_version mismatch")
    if record["writer_contract_version"] != parent["writer_contract_version"]:
        raise ReviewQueuePersistenceContractError("record writer_contract_version mismatch")
    if record["agreement_status"] not in REVIEW_BOUND_STATUSES:
        raise ReviewQueuePersistenceContractError("persistence candidates must remain non-VERIFIED review-bound records")
    if record.get("clean_data_eligible") is not False:
        raise ReviewQueuePersistenceContractError("clean_data_eligible must remain false before persistence")
    if record.get("delivery_blocked") is not True:
        raise ReviewQueuePersistenceContractError("delivery must remain blocked before persistence")
    _validate_hash_identity(record.get("input_file_hashes"), "record input_file_hashes")
    if record["input_file_hashes"] != parent["input_file_hashes"]:
        raise ReviewQueuePersistenceContractError("record input_file_hashes mismatch")
    if not SHA256_HEX_RE.match(record["idempotency_key"]):
        raise ReviewQueuePersistenceContractError("malformed idempotency_key")
    if record["idempotency_key"] != _expected_idempotency_key(record):
        raise ReviewQueuePersistenceContractError("idempotency_key inconsistent with row payload")
    if not SHA256_HEX_RE.match(record["record_payload_hash"]):
        raise ReviewQueuePersistenceContractError("record_payload_hash is required hash identity")
    if not _clean(record["blocked_delivery_reason"]):
        raise ReviewQueuePersistenceContractError("unresolved records require blocked_delivery_reason")
    if _is_corrected(record) and record["re_audit_required"] is not True:
        raise ReviewQueuePersistenceContractError("corrected records require re_audit_required")
    _validate_source_trace(record["source_trace"], record=record)
    if not _clean(record["evidence_preview"]):
        raise ReviewQueuePersistenceContractError("evidence_preview is required")
    _validate_bounded_preview(record["evidence_preview"], preview_limit)
    _validate_candidate_value(record["candidate_value"], record["normalized_candidate_value"])
    _validate_no_auto_clean_or_delivery_status(record)


def _persistence_candidate(
    record: dict[str, Any],
    *,
    contract_config: ReviewQueuePersistenceContractConfig,
) -> dict[str, Any]:
    candidate = {
        "review_item_id": record["review_item_id"],
        "run_id": record["run_id"],
        "source_file_hash": record["source_file_hash"],
        "input_file_hashes": deepcopy(record["input_file_hashes"]),
        "adapter_version": record["adapter_version"],
        "contract_version": contract_config.contract_version,
        "writer_contract_version": record["writer_contract_version"],
        "schema_version": PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION,
        "audit_hash": record["audit_hash"],
        "idempotency_key": record["idempotency_key"],
        "metric_name": record["metric_name"],
        "period": record["period"],
        "candidate_value": record["candidate_value"],
        "normalized_candidate_value": record["normalized_candidate_value"],
        "agreement_status": record["agreement_status"],
        "review_status": record["review_status"],
        "review_reason": record["review_reason"],
        "reviewer_action": record["reviewer_action"],
        "blocked_delivery_reason": record["blocked_delivery_reason"],
        "re_audit_required": bool(record["re_audit_required"]),
        "evidence_preview": record["evidence_preview"],
        "source_trace": deepcopy(record["source_trace"]),
        "created_by_system": "r7bl_test_only_persistence_contract",
    }
    candidate["record_payload_hash"] = _hash_record_payload(candidate)
    return candidate


def _validate_persistence_candidate(candidate: dict[str, Any], *, preview_limit: int) -> None:
    _require_exact_fields(candidate, REQUIRED_PERSISTENCE_CANDIDATE_FIELDS, "persistence candidate")
    for key in candidate:
        if key in FORBIDDEN_CANDIDATE_KEYS:
            raise ReviewQueuePersistenceContractError(f"forbidden persistence candidate field: {key}")
    for field in (
        "review_item_id",
        "run_id",
        "source_file_hash",
        "adapter_version",
        "contract_version",
        "writer_contract_version",
        "schema_version",
        "audit_hash",
        "idempotency_key",
        "metric_name",
        "period",
        "candidate_value",
        "agreement_status",
        "review_status",
        "review_reason",
        "blocked_delivery_reason",
        "created_by_system",
        "record_payload_hash",
    ):
        _validate_non_empty_string(candidate, field, "persistence candidate")
    if candidate["contract_version"] != PERSISTENCE_CONTRACT_VERSION:
        raise ReviewQueuePersistenceContractError("persistence candidate contract mismatch")
    if candidate["schema_version"] != PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION:
        raise ReviewQueuePersistenceContractError("persistence candidate schema mismatch")
    if candidate["agreement_status"] not in REVIEW_BOUND_STATUSES:
        raise ReviewQueuePersistenceContractError("persistence candidate must be review-bound")
    if candidate["reviewer_action"] in CORRECTIVE_REVIEWER_ACTIONS and candidate["re_audit_required"] is not True:
        raise ReviewQueuePersistenceContractError("corrected candidate requires re_audit_required")
    _validate_hash_identity(candidate.get("input_file_hashes"), "candidate input_file_hashes")
    if not _clean(candidate["evidence_preview"]):
        raise ReviewQueuePersistenceContractError("evidence_preview is required")
    _validate_bounded_preview(candidate["evidence_preview"], preview_limit)
    _validate_candidate_value(candidate["candidate_value"], candidate["normalized_candidate_value"])
    _validate_no_auto_clean_or_delivery_status(candidate)


def _persistence_summary(
    *,
    payload: dict[str, Any],
    candidates: list[dict[str, Any]],
    contract_config: ReviewQueuePersistenceContractConfig,
) -> dict[str, Any]:
    status_counts = dict(Counter(candidate["agreement_status"] for candidate in candidates))
    summary = {
        "persistence_status": ENABLED_STATUS,
        "enabled": True,
        "in_memory_only": True,
        "persistence_candidate_only": True,
        "persistence_contract_version": contract_config.contract_version,
        "persistence_candidate_batch_schema_version": PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION,
        "source_schema_alignment_contract_version": payload["schema_alignment_contract_version"],
        "future_review_queue_schema_version": payload["future_review_queue_schema_version"],
        "run_id": payload["run_id"],
        "adapter_version": payload["adapter_version"],
        "input_file_hashes": deepcopy(payload["input_file_hashes"]),
        "source_preview_record_count": len(payload["future_review_queue_record_previews"]),
        "candidate_count": len(candidates),
        "review_bound_record_count": len(candidates),
        "status_counts": status_counts,
        "clean_data_write_count": 0,
        "delivery_write_count": 0,
        "filesystem_write_count": 0,
        "database_write_count": 0,
        "export_write_count": 0,
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        "external_call_counts": deepcopy(EXTERNAL_CALL_COUNTS_ZERO),
        "boundary_flags": _closed_boundary_flags(),
        "validation_errors": [],
    }
    summary["persistence_candidate_batch_hash"] = _hash_json(candidates)
    return summary


def _validate_no_duplicate_idempotency(candidates: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate["idempotency_key"]
        if key in seen:
            raise ReviewQueuePersistenceContractError("duplicate idempotency_key rejected")
        seen.add(key)


def _validate_schema_alignment_preview_hash(summary: dict[str, Any], *, records: list[dict[str, Any]]) -> None:
    expected_hash = _hash_json(
        {
            "schema_alignment_contract_version": summary["schema_alignment_contract_version"],
            "future_review_queue_schema_version": summary["future_review_queue_schema_version"],
            "run_id": summary["run_id"],
            "records": records,
            "status_counts": summary["status_counts"],
        }
    )
    if summary["schema_alignment_preview_hash"] != expected_hash:
        raise ReviewQueuePersistenceContractError("schema_alignment_preview_hash mismatch")


def _validate_summary_record_counts(summary: dict[str, Any], *, records: list[dict[str, Any]]) -> None:
    status_counts = dict(Counter(record["agreement_status"] for record in records))
    if summary.get("status_counts") != status_counts:
        raise ReviewQueuePersistenceContractError("schema alignment status_counts mismatch")
    if summary.get("review_bound_record_count") != len(records):
        raise ReviewQueuePersistenceContractError("schema alignment review_bound_record_count mismatch")


def _validate_source_trace(value: Any, *, record: dict[str, Any]) -> None:
    if not isinstance(value, dict) or not value:
        raise ReviewQueuePersistenceContractError("source_trace is required")
    _require_exact_fields(value, REQUIRED_SOURCE_TRACE_FIELDS, "source_trace")
    for field in REQUIRED_SOURCE_TRACE_FIELDS:
        _validate_string_field(value, field, "source_trace")
    for field in (
        "source_document_id",
        "source_row_id",
        "matched_locator",
        "matched_text_sha256",
        "evidence_preview_sha256",
    ):
        _validate_non_empty_string(value, field, "source_trace")
    if value["source_document_id"] != record["source_document_id"]:
        raise ReviewQueuePersistenceContractError("source_trace source_document_id mismatch")
    if value["source_row_id"] != record["source_row_id"]:
        raise ReviewQueuePersistenceContractError("source_trace source_row_id mismatch")


def _expected_idempotency_key(record: dict[str, Any]) -> str:
    payload = {
        "contract_version": record["writer_contract_version"],
        "run_id": record["run_id"],
        "review_item_id": record["review_item_id"],
        "source_row_id": record["source_row_id"],
        "agreement_status": record["agreement_status"],
        "audit_hash": record["audit_hash"],
        "input_file_hashes": dict(sorted(record["input_file_hashes"].items())),
    }
    return _hash_json(payload)


def _validate_candidate_value(candidate_value: Any, normalized_candidate_value: Any) -> None:
    raw = _clean(candidate_value).lower()
    normalized = _clean(normalized_candidate_value).lower()
    if raw in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        raise ReviewQueuePersistenceContractError("candidate_value must not be NaN or Infinity")
    if normalized in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
        raise ReviewQueuePersistenceContractError("candidate_value must not be NaN or Infinity")


def _validate_no_auto_clean_or_delivery_status(record: dict[str, Any]) -> None:
    reviewer_action = _clean(record.get("reviewer_action")).upper()
    review_status = _clean(record.get("review_status")).upper()
    if reviewer_action in {
        "ACCEPT_CANDIDATE",
        "AUTO_APPROVE_CLEAN_DATA",
        "APPROVE_CLEAN_DATA",
        "MARK_CLEAN_DATA_ELIGIBLE",
        "UNBLOCK_DELIVERY",
        "APPROVE_DELIVERY",
    }:
        raise ReviewQueuePersistenceContractError("reviewer_action cannot imply clean_data or delivery unblock")
    if review_status in {
        "CLEAN_DATA_APPROVED",
        "AUTO_CLEAN_APPROVED",
        "DELIVERY_UNBLOCKED",
        "READY_FOR_DELIVERY",
        "APPROVED_FOR_EXPORT",
    }:
        raise ReviewQueuePersistenceContractError("review_status cannot imply clean_data or delivery unblock")


def _require_exact_fields(value: dict[str, Any], required_fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in required_fields if field not in value]
    if missing:
        raise ReviewQueuePersistenceContractError(f"{label} missing required fields: {missing}")
    extra = sorted(set(value) - set(required_fields))
    if extra:
        raise ReviewQueuePersistenceContractError(f"{label} has unexpected fields: {extra}")


def _validate_hash_identity(value: Any, label: str) -> None:
    if not isinstance(value, dict) or not value:
        raise ReviewQueuePersistenceContractError(f"{label} must be a non-empty object")
    for key, child in value.items():
        if not _clean(key) or not _clean(child):
            raise ReviewQueuePersistenceContractError(f"{label} must contain non-empty hash identity")


def _validate_string_field(value: dict[str, Any], field: str, label: str) -> None:
    if not isinstance(value.get(field), str):
        raise ReviewQueuePersistenceContractError(f"{label} {field} must be a string")


def _validate_non_empty_string(value: dict[str, Any], field: str, label: str) -> None:
    if not _clean(value.get(field)):
        raise ReviewQueuePersistenceContractError(f"{label} {field} is required")


def _validate_bounded_preview(value: Any, preview_limit: int) -> None:
    if len(_clean(value)) > preview_limit:
        raise ReviewQueuePersistenceContractError("evidence_preview exceeds preview_limit")


def _boundary_flags_are_closed(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for key in (
        "production_hook",
        "writes_review_queue",
        "writes_clean_data",
        "writes_delivery",
        "writes_filesystem",
        "writes_database",
        "writes_export",
        "verified_auto_clean",
        "verified_promotes_to_strong_evidence",
        "full_source_text_serialized",
    ):
        if value.get(key) is True:
            return False
    return True


def _closed_boundary_flags() -> dict[str, bool]:
    return {
        "production_hook": False,
        "writes_review_queue": False,
        "writes_clean_data": False,
        "writes_delivery": False,
        "writes_filesystem": False,
        "writes_database": False,
        "writes_export": False,
        "in_memory_candidate_only": True,
        "verified_auto_clean": False,
        "verified_promotes_to_strong_evidence": False,
        "full_source_text_serialized": False,
    }


def _is_corrected(record: dict[str, Any]) -> bool:
    return record.get("review_status") == "CORRECTED" or record.get("reviewer_action") in CORRECTIVE_REVIEWER_ACTIONS


def _hash_record_payload(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "record_payload_hash"}
    return _hash_json(payload)


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "DEFAULT_PREVIEW_LIMIT",
    "PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION",
    "PERSISTENCE_CONTRACT_VERSION",
    "REQUIRED_PERSISTENCE_CANDIDATE_FIELDS",
    "TEST_ONLY_PERSISTENCE_ENABLE_TOKEN",
    "ReviewQueuePersistenceContractConfig",
    "ReviewQueuePersistenceContractError",
    "build_review_queue_persistence_candidate_batch",
    "required_persistence_candidate_fields",
    "validate_no_forbidden_input_fields",
    "validate_schema_alignment_preview",
]
