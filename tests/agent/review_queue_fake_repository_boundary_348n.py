"""Test-only fake review_queue repository boundary for R7BQ.

This module accepts only the R7BL/R7BM in-memory persistence candidate batch
shape and writes only to an in-memory fake repository. It performs no I/O, no
DB writes, no exports, and has no production hook.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any

from tests.agent.review_queue_persistence_contract_348n import (
    DEFAULT_PREVIEW_LIMIT,
    PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION,
    PERSISTENCE_CONTRACT_VERSION,
    REQUIRED_PERSISTENCE_CANDIDATE_FIELDS,
)

FAKE_REPOSITORY_BOUNDARY_VERSION = "r7bq_fake_repository_boundary_test_only_v1"
TEST_ONLY_FAKE_REPOSITORY_ENABLE_TOKEN = "R7BQ_TEST_ONLY_FAKE_REPOSITORY_ENABLE"

ENABLED_STATUS = "ENABLED_TEST_ONLY_FAKE_REPOSITORY_WRITE"
DISABLED_STATUS = "DISABLED"
MODE = "test_only_fake_repository"

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

REVIEW_BOUND_STATUSES: frozenset[str] = frozenset(
    {
        "UNVERIFIED",
        "DISAGREED",
        "AMBIGUOUS",
        "MISSING_EVIDENCE",
        "PARSE_SKIPPED",
    }
)

REQUIRED_PERSISTENCE_BATCH_FIELDS: tuple[str, ...] = (
    "persistence_status",
    "in_memory_only",
    "persistence_candidate_only",
    "persistence_contract_version",
    "persistence_candidate_batch_schema_version",
    "source_schema_alignment_contract_version",
    "future_review_queue_schema_version",
    "run_id",
    "adapter_version",
    "input_file_hashes",
    "review_queue_persistence_candidate_batch",
    "persistence_summary",
)

SAFE_FAKE_REPOSITORY_ROW_FIELDS: tuple[str, ...] = REQUIRED_PERSISTENCE_CANDIDATE_FIELDS

FORBIDDEN_FAKE_REPOSITORY_KEYS: frozenset[str] = frozenset(
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
        "mineru_output",
        "raw_excel",
        "raw_excel_row",
        "raw_datefac_excel_row",
        "datefac_excel_rows",
        "workbook_sheets",
        "worksheets",
        "cells",
        "raw_parser_payload",
        "parser_output",
        "pdf_parser_output",
        "raw_pdf_text",
        "raw_pdf_pages",
        "raw_extraction_payload",
        "ocr_output",
        "llm_response",
        "vlm_response",
        "raw_llm_response",
        "raw_vlm_response",
        "html",
        "markdown",
        "schema_alignment_status",
        "future_review_queue_record_previews",
        "schema_alignment_preview",
        "writer_dry_run_preview",
        "review_queue_dry_run_records",
        "direct_writer_preview",
        "adapter_candidate_output",
        "review_queue_candidate_items",
        "audit_contract",
        "fake_repository_rows",
        "fake_repository_state_snapshot",
        "fake_repository_write_receipt",
        "caller_supplied_receipt",
        "internal_state",
        "repository_internal_state",
        "repository_rows",
        "repository_state",
        "repository_state_snapshot",
        "state_payload_hash",
        "write_receipt",
        "receipt",
        "user_direct_fake_repository_row",
        "user_direct_fake_repository_rows",
        "production_repository_config",
        "production_writer_config",
        "production_config",
        "production_mode",
        "repository_config",
        "writer_config",
        "db_connection",
        "database_connection",
        "database_url",
        "db_url",
        "dsn",
        "connection_string",
        "database_id",
        "migration_id",
        "table_name",
        "database_table",
        "repository_class",
        "storage_destination",
        "storage_client",
        "storage_client_config",
        "storage_dependency",
        "network_client",
        "network_dependency",
        "http_client",
        "api_client",
        "s3_uri",
        "persistence_destination",
        "persistence_candidate_rows",
        "persistence_target",
        "output_path",
        "export_path",
        "file_path",
        "filesystem_path",
        "storage_path",
        "clean_data",
        "clean_data_record",
        "clean_data_records",
        "clean_data_payload",
        "clean_data_intent",
        "clean_data_write_intent",
        "clean_data_eligible",
        "clean_data_admitted",
        "delivery_clean_admitted",
        "delivery_payload",
        "delivery_export_intent",
        "delivery_write_intent",
        "export_payload",
        "export_intent",
        "formal_delivery_payload",
        "formal_export_payload",
        "formal_export_intent",
        "production_hook_intent",
        "test_only_enable_token",
        "test_only_writer_config",
        "test_only_persistence_config",
        "test_only_fake_repository_config",
        "test_only_config",
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
    }
)

SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


class FakeReviewQueueRepositoryBoundaryError(ValueError):
    """Raised when the test-only fake repository boundary fails closed."""


@dataclass(slots=True)
class FakeReviewQueueRepository348N:
    """In-memory fake repository state for repository-boundary tests only."""

    boundary_version: str = FAKE_REPOSITORY_BOUNDARY_VERSION
    _records_by_idempotency_key: dict[str, dict[str, Any]] = field(default_factory=dict, init=False)
    _review_item_to_idempotency_key: dict[str, str] = field(default_factory=dict, init=False)

    def state_snapshot(self) -> dict[str, Any]:
        """Return a deep-copied safe state snapshot."""

        records = [
            deepcopy(record)
            for _, record in sorted(self._records_by_idempotency_key.items(), key=lambda item: item[0])
        ]
        snapshot = {
            "mode": MODE,
            "boundary_version": self.boundary_version,
            "in_memory_only": True,
            "record_count": len(records),
            "records": records,
            "state_payload_hash": _hash_json(records),
            "clean_data_write_count": 0,
            "delivery_write_count": 0,
            "filesystem_write_count": 0,
            "database_write_count": 0,
            "export_write_count": 0,
            "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
            "boundary_flags": _closed_boundary_flags(),
        }
        return deepcopy(snapshot)

    def _replace_state(
        self,
        records_by_idempotency_key: dict[str, dict[str, Any]],
        review_item_to_idempotency_key: dict[str, str],
    ) -> None:
        self._records_by_idempotency_key = deepcopy(records_by_idempotency_key)
        self._review_item_to_idempotency_key = deepcopy(review_item_to_idempotency_key)


def persist_candidate_batch_to_fake_repository_348n(
    candidate_batch: Any,
    *,
    allow_test_only_fake_repository: bool = False,
    test_only_enable_token: str = "",
    repository: FakeReviewQueueRepository348N | None = None,
    repository_config: Any = None,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> dict[str, Any]:
    """Persist a validated candidate batch to an in-memory fake repository."""

    target_repository = repository or FakeReviewQueueRepository348N()
    if not allow_test_only_fake_repository:
        return _disabled_result(target_repository)
    if test_only_enable_token != TEST_ONLY_FAKE_REPOSITORY_ENABLE_TOKEN:
        raise FakeReviewQueueRepositoryBoundaryError("explicit R7BQ test-only fake repository token is required")
    _validate_repository_config(repository_config)

    candidates = validate_persistence_candidate_batch_for_fake_repository_348n(
        candidate_batch,
        preview_limit=preview_limit,
    )
    next_records = deepcopy(target_repository._records_by_idempotency_key)
    next_review_index = deepcopy(target_repository._review_item_to_idempotency_key)
    incoming_idempotency_keys: set[str] = set()
    incoming_review_item_ids: dict[str, str] = {}
    written_candidates: list[dict[str, Any]] = []
    noop_candidates: list[dict[str, Any]] = []

    for candidate in candidates:
        idempotency_key = candidate["idempotency_key"]
        review_item_id = candidate["review_item_id"]
        record_payload_hash = candidate["record_payload_hash"]
        if idempotency_key in incoming_idempotency_keys:
            raise FakeReviewQueueRepositoryBoundaryError("duplicate idempotency_key in candidate batch rejected")
        incoming_idempotency_keys.add(idempotency_key)
        previous_key = incoming_review_item_ids.get(review_item_id)
        if previous_key is not None and previous_key != idempotency_key:
            raise FakeReviewQueueRepositoryBoundaryError("duplicate review_item_id in candidate batch rejected")
        incoming_review_item_ids[review_item_id] = idempotency_key

        existing_by_key = next_records.get(idempotency_key)
        if existing_by_key is not None:
            if existing_by_key["record_payload_hash"] != record_payload_hash:
                raise FakeReviewQueueRepositoryBoundaryError(
                    "idempotency_key conflict with different record_payload_hash rejected"
                )
            noop_candidates.append(candidate)
            continue

        existing_key_for_review_item = next_review_index.get(review_item_id)
        if existing_key_for_review_item is not None and existing_key_for_review_item != idempotency_key:
            raise FakeReviewQueueRepositoryBoundaryError(
                "review_item_id conflict with different idempotency_key rejected"
            )

        safe_candidate = _safe_repository_row(candidate, preview_limit=preview_limit)
        next_records[idempotency_key] = safe_candidate
        next_review_index[review_item_id] = idempotency_key
        written_candidates.append(safe_candidate)

    target_repository._replace_state(next_records, next_review_index)
    receipt = _write_receipt(
        candidates=candidates,
        written_candidates=written_candidates,
        noop_candidates=noop_candidates,
        repository=target_repository,
    )
    output = {
        "fake_repository_status": ENABLED_STATUS,
        "mode": MODE,
        "in_memory_only": True,
        "fake_repository_boundary_version": FAKE_REPOSITORY_BOUNDARY_VERSION,
        "fake_repository_write_receipt": receipt,
        "fake_repository_state_snapshot": target_repository.state_snapshot(),
    }
    return deepcopy(output)


def validate_persistence_candidate_batch_for_fake_repository_348n(
    value: Any,
    *,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> list[dict[str, Any]]:
    """Validate the only accepted fake repository input: R7BL candidate batch."""

    if not isinstance(value, dict):
        raise FakeReviewQueueRepositoryBoundaryError("persistence candidate batch must be an object")
    _validate_no_forbidden_fields(value, preview_limit=preview_limit)
    _require_exact_fields(value, REQUIRED_PERSISTENCE_BATCH_FIELDS, "persistence candidate batch")
    if value["persistence_status"] != "ENABLED_TEST_ONLY_PERSISTENCE_CANDIDATE":
        raise FakeReviewQueueRepositoryBoundaryError("input must be enabled test-only persistence candidate batch")
    if value["in_memory_only"] is not True or value["persistence_candidate_only"] is not True:
        raise FakeReviewQueueRepositoryBoundaryError("input must remain in-memory persistence candidate only")
    if value["persistence_contract_version"] != PERSISTENCE_CONTRACT_VERSION:
        raise FakeReviewQueueRepositoryBoundaryError("unexpected persistence contract version")
    if value["persistence_candidate_batch_schema_version"] != PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION:
        raise FakeReviewQueueRepositoryBoundaryError("unexpected persistence candidate batch schema version")
    _validate_non_empty_string(value, "run_id", "persistence candidate batch")
    _validate_non_empty_string(value, "adapter_version", "persistence candidate batch")
    _validate_hash_identity(value.get("input_file_hashes"), "persistence candidate batch input_file_hashes")

    candidates = value["review_queue_persistence_candidate_batch"]
    if not isinstance(candidates, list):
        raise FakeReviewQueueRepositoryBoundaryError("review_queue_persistence_candidate_batch must be a list")
    summary = value["persistence_summary"]
    _validate_persistence_summary(summary, value=value, candidates=candidates)

    safe_candidates: list[dict[str, Any]] = []
    seen_idempotency_keys: set[str] = set()
    seen_review_item_ids: set[str] = set()
    for candidate in candidates:
        _validate_candidate_row(candidate, parent=value, preview_limit=preview_limit)
        idempotency_key = candidate["idempotency_key"]
        review_item_id = candidate["review_item_id"]
        if idempotency_key in seen_idempotency_keys:
            raise FakeReviewQueueRepositoryBoundaryError("duplicate idempotency_key rejected")
        if review_item_id in seen_review_item_ids:
            raise FakeReviewQueueRepositoryBoundaryError("duplicate review_item_id rejected")
        seen_idempotency_keys.add(idempotency_key)
        seen_review_item_ids.add(review_item_id)
        safe_candidates.append(_safe_repository_row(candidate, preview_limit=preview_limit))
    safe_candidates.sort(key=lambda item: (item["run_id"], item["review_item_id"], item["idempotency_key"]))
    expected_hash = _hash_json(safe_candidates)
    if summary["persistence_candidate_batch_hash"] != expected_hash:
        raise FakeReviewQueueRepositoryBoundaryError("persistence_candidate_batch_hash mismatch")
    return deepcopy(safe_candidates)


def required_fake_repository_row_fields_348n() -> tuple[str, ...]:
    """Return safe fake repository row fields for tests and reports."""

    return SAFE_FAKE_REPOSITORY_ROW_FIELDS


def _disabled_result(repository: FakeReviewQueueRepository348N) -> dict[str, Any]:
    return {
        "fake_repository_status": DISABLED_STATUS,
        "mode": MODE,
        "enabled": False,
        "reason": "disabled_by_default",
        "in_memory_only": True,
        "fake_repository_boundary_version": repository.boundary_version,
        "fake_repository_write_receipt": None,
        "fake_repository_state_snapshot": repository.state_snapshot(),
        "clean_data_write_count": 0,
        "delivery_write_count": 0,
        "filesystem_write_count": 0,
        "database_write_count": 0,
        "export_write_count": 0,
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        "boundary_flags": _closed_boundary_flags(),
    }


def _validate_repository_config(value: Any) -> None:
    if value is None:
        return
    raise FakeReviewQueueRepositoryBoundaryError("production repository config is forbidden")


def _validate_persistence_summary(summary: Any, *, value: dict[str, Any], candidates: list[Any]) -> None:
    if not isinstance(summary, dict):
        raise FakeReviewQueueRepositoryBoundaryError("persistence_summary must be an object")
    for field_name in (
        "persistence_status",
        "enabled",
        "in_memory_only",
        "persistence_candidate_only",
        "persistence_contract_version",
        "persistence_candidate_batch_schema_version",
        "run_id",
        "adapter_version",
        "input_file_hashes",
        "candidate_count",
        "review_bound_record_count",
        "status_counts",
        "clean_data_write_count",
        "delivery_write_count",
        "filesystem_write_count",
        "database_write_count",
        "export_write_count",
        "readiness_gates",
        "external_call_counts",
        "boundary_flags",
        "validation_errors",
        "persistence_candidate_batch_hash",
    ):
        if field_name not in summary:
            raise FakeReviewQueueRepositoryBoundaryError(f"persistence_summary {field_name} is required")
    if summary["persistence_status"] != value["persistence_status"]:
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary status mismatch")
    if summary["enabled"] is not True:
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary must be enabled")
    if summary["in_memory_only"] is not True or summary["persistence_candidate_only"] is not True:
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary must remain candidate-only")
    if summary["persistence_contract_version"] != value["persistence_contract_version"]:
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary contract mismatch")
    if summary["persistence_candidate_batch_schema_version"] != value["persistence_candidate_batch_schema_version"]:
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary schema mismatch")
    if summary["run_id"] != value["run_id"] or summary["adapter_version"] != value["adapter_version"]:
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary metadata mismatch")
    if summary["input_file_hashes"] != value["input_file_hashes"]:
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary input_file_hashes mismatch")
    if summary["candidate_count"] != len(candidates) or summary["review_bound_record_count"] != len(candidates):
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary candidate count mismatch")
    if summary["readiness_gates"] != READINESS_GATES_CLOSED:
        raise FakeReviewQueueRepositoryBoundaryError("readiness gates must remain CLOSED")
    if summary["external_call_counts"] != EXTERNAL_CALL_COUNTS_ZERO:
        raise FakeReviewQueueRepositoryBoundaryError("external call counts must stay zero")
    if summary["validation_errors"] != []:
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary must have no validation errors")
    for field_name in (
        "clean_data_write_count",
        "delivery_write_count",
        "filesystem_write_count",
        "database_write_count",
        "export_write_count",
    ):
        if summary[field_name] != 0:
            raise FakeReviewQueueRepositoryBoundaryError(f"{field_name} must remain zero")
    if not _boundary_flags_are_closed(summary["boundary_flags"]):
        raise FakeReviewQueueRepositoryBoundaryError("persistence boundary flags must remain closed")
    expected_status_counts: dict[str, int] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise FakeReviewQueueRepositoryBoundaryError("persistence candidates must be objects")
        status = candidate.get("agreement_status")
        expected_status_counts[status] = expected_status_counts.get(status, 0) + 1
    if summary["status_counts"] != expected_status_counts:
        raise FakeReviewQueueRepositoryBoundaryError("persistence summary status_counts mismatch")


def _validate_candidate_row(candidate: Any, *, parent: dict[str, Any], preview_limit: int) -> None:
    if not isinstance(candidate, dict):
        raise FakeReviewQueueRepositoryBoundaryError("persistence candidate rows must be objects")
    _require_exact_fields(candidate, REQUIRED_PERSISTENCE_CANDIDATE_FIELDS, "persistence candidate row")
    _validate_no_forbidden_fields(candidate, preview_limit=preview_limit)
    for field_name in (
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
        "normalized_candidate_value",
        "agreement_status",
        "review_status",
        "review_reason",
        "blocked_delivery_reason",
        "created_by_system",
        "record_payload_hash",
    ):
        _validate_non_empty_string(candidate, field_name, "persistence candidate row")
    if candidate["run_id"] != parent["run_id"]:
        raise FakeReviewQueueRepositoryBoundaryError("candidate run_id mismatch")
    if candidate["adapter_version"] != parent["adapter_version"]:
        raise FakeReviewQueueRepositoryBoundaryError("candidate adapter_version mismatch")
    if candidate["contract_version"] != PERSISTENCE_CONTRACT_VERSION:
        raise FakeReviewQueueRepositoryBoundaryError("candidate contract_version mismatch")
    if candidate["schema_version"] != PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION:
        raise FakeReviewQueueRepositoryBoundaryError("candidate schema_version mismatch")
    if candidate["input_file_hashes"] != parent["input_file_hashes"]:
        raise FakeReviewQueueRepositoryBoundaryError("candidate input_file_hashes mismatch")
    _validate_hash_identity(candidate.get("input_file_hashes"), "candidate input_file_hashes")
    _validate_sha256_hex(candidate["idempotency_key"], "idempotency_key")
    _validate_sha256_hex(candidate["record_payload_hash"], "record_payload_hash")
    if candidate["agreement_status"] not in REVIEW_BOUND_STATUSES:
        raise FakeReviewQueueRepositoryBoundaryError("fake repository accepts only review-bound non-VERIFIED candidates")
    if _clean(candidate.get("evidence_preview")) == "":
        raise FakeReviewQueueRepositoryBoundaryError("evidence_preview is required")
    _validate_bounded_preview(candidate["evidence_preview"], preview_limit)
    if candidate["re_audit_required"] not in {True, False}:
        raise FakeReviewQueueRepositoryBoundaryError("re_audit_required must be boolean")
    if candidate["record_payload_hash"] != _hash_record_payload(candidate):
        raise FakeReviewQueueRepositoryBoundaryError("record_payload_hash mismatch")
    _validate_source_trace(candidate["source_trace"])
    _validate_no_clean_or_delivery_promotion(candidate)


def _safe_repository_row(candidate: dict[str, Any], *, preview_limit: int) -> dict[str, Any]:
    row = {field_name: deepcopy(candidate[field_name]) for field_name in SAFE_FAKE_REPOSITORY_ROW_FIELDS}
    _require_exact_fields(row, SAFE_FAKE_REPOSITORY_ROW_FIELDS, "fake repository row")
    _validate_no_forbidden_fields(row, preview_limit=preview_limit)
    return deepcopy(row)


def _write_receipt(
    *,
    candidates: list[dict[str, Any]],
    written_candidates: list[dict[str, Any]],
    noop_candidates: list[dict[str, Any]],
    repository: FakeReviewQueueRepository348N,
) -> dict[str, Any]:
    snapshot = repository.state_snapshot()
    receipt = {
        "status": "WRITE_ACCEPTED",
        "mode": MODE,
        "row_count": len(candidates),
        "written_count": len(written_candidates),
        "idempotent_noop_count": len(noop_candidates),
        "idempotency_keys": [candidate["idempotency_key"] for candidate in candidates],
        "record_payload_hashes": [candidate["record_payload_hash"] for candidate in candidates],
        "batch_payload_hash": _hash_json(candidates),
        "repository_state_hash": snapshot["state_payload_hash"],
        "boundary_version": FAKE_REPOSITORY_BOUNDARY_VERSION,
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        "clean_data_write_count": 0,
        "delivery_write_count": 0,
        "filesystem_write_count": 0,
        "database_write_count": 0,
        "export_write_count": 0,
        "boundary_flags": _closed_boundary_flags(),
    }
    return deepcopy(receipt)


def _validate_no_forbidden_fields(
    value: Any,
    *,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
    path: str = "$",
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_FAKE_REPOSITORY_KEYS:
                raise FakeReviewQueueRepositoryBoundaryError(f"forbidden field at {path}.{key}: {key}")
            if key in NON_DETERMINISTIC_KEYS:
                raise FakeReviewQueueRepositoryBoundaryError(f"non-deterministic field at {path}.{key}: {key}")
            if key == "evidence_level" and _clean(child).upper() == "STRONG_EVIDENCE":
                raise FakeReviewQueueRepositoryBoundaryError("STRONG_EVIDENCE promotion is forbidden")
            if key in {"client_ready", "production_ready", "formal_client_export_allowed"} and child is True:
                raise FakeReviewQueueRepositoryBoundaryError(f"readiness gate opened at {path}.{key}")
            if key == "readiness_gates" and child != READINESS_GATES_CLOSED:
                raise FakeReviewQueueRepositoryBoundaryError("readiness gates must remain CLOSED")
            if key in {
                "writes_review_queue",
                "writes_clean_data",
                "writes_delivery",
                "writes_filesystem",
                "writes_database",
                "writes_export",
            } and child is True:
                raise FakeReviewQueueRepositoryBoundaryError(f"write intent is forbidden at {path}.{key}")
            if key in {"clean_data_write_count", "delivery_write_count", "database_write_count", "export_write_count"}:
                if child != 0:
                    raise FakeReviewQueueRepositoryBoundaryError(f"{key} must remain zero")
            if key == "production_hook" and child is True:
                raise FakeReviewQueueRepositoryBoundaryError("production hooks are forbidden")
            if key == "evidence_preview":
                _validate_bounded_preview(child, preview_limit)
            _validate_no_forbidden_fields(child, preview_limit=preview_limit, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_forbidden_fields(child, preview_limit=preview_limit, path=f"{path}[{index}]")


def _validate_source_trace(value: Any) -> None:
    if not isinstance(value, dict) or not value:
        raise FakeReviewQueueRepositoryBoundaryError("source_trace is required")
    for field_name, child in value.items():
        if not _clean(field_name):
            raise FakeReviewQueueRepositoryBoundaryError("source_trace field names must be non-empty")
        if not _clean(child):
            raise FakeReviewQueueRepositoryBoundaryError("source_trace values must be non-empty")


def _validate_no_clean_or_delivery_promotion(candidate: dict[str, Any]) -> None:
    if candidate["agreement_status"] == "VERIFIED":
        raise FakeReviewQueueRepositoryBoundaryError("VERIFIED cannot enter fake repository persistence")
    if _clean(candidate.get("reviewer_action")).upper() in {
        "ACCEPT_CANDIDATE",
        "AUTO_APPROVE_CLEAN_DATA",
        "APPROVE_CLEAN_DATA",
        "MARK_CLEAN_DATA_ELIGIBLE",
        "UNBLOCK_DELIVERY",
        "APPROVE_DELIVERY",
    }:
        raise FakeReviewQueueRepositoryBoundaryError("reviewer_action cannot imply clean_data or delivery")
    if _clean(candidate.get("review_status")).upper() in {
        "CLEAN_DATA_APPROVED",
        "AUTO_CLEAN_APPROVED",
        "DELIVERY_UNBLOCKED",
        "READY_FOR_DELIVERY",
        "APPROVED_FOR_EXPORT",
    }:
        raise FakeReviewQueueRepositoryBoundaryError("review_status cannot imply clean_data or delivery")


def _require_exact_fields(value: dict[str, Any], required_fields: tuple[str, ...], label: str) -> None:
    missing = [field_name for field_name in required_fields if field_name not in value]
    if missing:
        raise FakeReviewQueueRepositoryBoundaryError(f"{label} missing required fields: {missing}")
    extra = sorted(set(value) - set(required_fields))
    if extra:
        raise FakeReviewQueueRepositoryBoundaryError(f"{label} has unexpected fields: {extra}")


def _validate_hash_identity(value: Any, label: str) -> None:
    if not isinstance(value, dict) or not value:
        raise FakeReviewQueueRepositoryBoundaryError(f"{label} must be a non-empty object")
    for key, child in value.items():
        if not _clean(key) or not _clean(child):
            raise FakeReviewQueueRepositoryBoundaryError(f"{label} must contain non-empty hash identity")


def _validate_non_empty_string(value: dict[str, Any], field_name: str, label: str) -> None:
    if not _clean(value.get(field_name)):
        raise FakeReviewQueueRepositoryBoundaryError(f"{label} {field_name} is required")


def _validate_sha256_hex(value: Any, label: str) -> None:
    if not isinstance(value, str) or not SHA256_HEX_RE.fullmatch(value):
        raise FakeReviewQueueRepositoryBoundaryError(f"{label} must be a 64-character SHA-256 hex string")


def _validate_bounded_preview(value: Any, preview_limit: int) -> None:
    if len(_clean(value)) > preview_limit:
        raise FakeReviewQueueRepositoryBoundaryError("evidence_preview exceeds preview_limit")


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
        if value.get(key) is not False:
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
        "in_memory_fake_repository_only": True,
        "verified_auto_clean": False,
        "verified_promotes_to_strong_evidence": False,
        "full_source_text_serialized": False,
    }


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
    "ENABLED_STATUS",
    "FAKE_REPOSITORY_BOUNDARY_VERSION",
    "READINESS_GATES_CLOSED",
    "SAFE_FAKE_REPOSITORY_ROW_FIELDS",
    "TEST_ONLY_FAKE_REPOSITORY_ENABLE_TOKEN",
    "FakeReviewQueueRepository348N",
    "FakeReviewQueueRepositoryBoundaryError",
    "persist_candidate_batch_to_fake_repository_348n",
    "required_fake_repository_row_fields_348n",
    "validate_persistence_candidate_batch_for_fake_repository_348n",
]
