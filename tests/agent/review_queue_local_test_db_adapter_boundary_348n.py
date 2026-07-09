"""Test-only local test DB adapter boundary skeleton for R7BX.

This module models the activation and payload boundary for a future local test
database adapter. It intentionally stays planned-disabled and performs no
persistence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, fields
from typing import Any

LOCAL_TEST_DB_ADAPTER_BOUNDARY_VERSION = "r7bx_local_test_db_adapter_boundary_skeleton_test_only_v1"
TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN = "R7BX_LOCAL_TEST_DB_ADAPTER_BOUNDARY_ENABLE"
BOUNDARY_MODE = "test_only_local_test_db_adapter_boundary_skeleton"
DISABLED_STATUS = "DISABLED"
PLANNED_DISABLED_STATUS = "PLANNED_DISABLED_NO_DATABASE_CONNECTION"
VALID_LOCAL_TEST_ENVIRONMENT = "local_test"
DEFAULT_PREVIEW_LIMIT = 160

READINESS_GATES_CLOSED: dict[str, bool] = {
    "client_ready": False,
    "production_ready": False,
    "formal_client_export_allowed": False,
    "demo_export_only": True,
}

ALLOWED_TEST_DB_SELECTIONS: frozenset[str] = frozenset({"sqlite_memory", "sqlite_temp_file"})

AUTO_ACTIVATION_SOURCES: frozenset[str] = frozenset(
    {
        "environment",
        "env",
        "schema_alignment_preview",
        "repository_skeleton_factory",
        "review_queue_repository_factory",
    }
)

FORBIDDEN_CONFIG_KEYS: frozenset[str] = frozenset(
    {
        "api_key",
        "connection_string",
        "database_url",
        "db_api_key",
        "db_password",
        "db_secret",
        "db_token",
        "delivery_export_intent",
        "delivery_payload",
        "endpoint",
        "export_intent",
        "file_path",
        "host",
        "migration",
        "migration_name",
        "network_endpoint",
        "output_path",
        "password",
        "port",
        "production_writer_config",
        "readiness_gates",
        "readiness_override",
        "repository_skeleton_factory_output",
        "schema",
        "schema_alignment_preview",
        "schema_name",
        "secret",
        "server",
        "table_name",
        "clean_data_intent",
        "clean_data_payload",
        "token",
    }
)

FORBIDDEN_CONFIG_VALUE_MARKERS: tuple[str, ...] = (
    "postgresql://",
    "postgres://",
    "mysql://",
    "mariadb://",
    "sqlserver://",
    "http://",
    "https://",
    "server=",
    "password=",
    "pwd=",
    "secret",
    "prod",
    "production",
    "endpoint",
    "d:/",
    "c:/",
    "\\\\",
    "/output/",
    "\\output\\",
)

FORBIDDEN_CANDIDATE_KEYS: frozenset[str] = frozenset(
    {
        "adapter_internal_state",
        "adapter_state",
        "approved_export_payload",
        "caller_supplied_db_row",
        "caller_supplied_db_primary_key",
        "clean_data_intent",
        "clean_data_payload",
        "committed_receipt",
        "committed_db_receipt",
        "database_row",
        "db_primary_key",
        "db_row",
        "db_receipt",
        "delivery_export_intent",
        "delivery_payload",
        "export_payload",
        "full_evidence_text",
        "full_source_text",
        "internal_adapter_state",
        "local_test_db_adapter_state",
        "normalized_clean_data",
        "primary_key",
        "production_timestamp_override",
        "raw_excel_payload",
        "raw_llm_payload",
        "raw_mineru_payload",
        "raw_ocr_payload",
        "raw_parser_payload",
        "raw_vlm_payload",
        "readiness_gates",
        "readiness_override",
        "receipt",
        "source_text",
        "source_text_full",
        "unbounded_evidence_text",
        "write_receipt",
    }
)

REQUIRED_CANDIDATE_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "idempotency_key",
    "record_payload_hash",
)


class LocalTestDBAdapterBoundaryError(ValueError):
    """Base error for the planned-disabled test-only boundary."""


class LocalTestDBAdapterActivationError(LocalTestDBAdapterBoundaryError):
    """Raised when local test DB boundary activation fails closed."""


class LocalTestDBAdapterCandidateError(LocalTestDBAdapterBoundaryError):
    """Raised when future local DB candidate payload validation fails closed."""


@dataclass(frozen=True, slots=True)
class LocalTestDBAdapterConfig:
    """Explicit test-only config for a future local test DB adapter boundary."""

    enabled: bool = False
    test_only: bool = False
    environment: str = ""
    db_selection: str = ""
    dsn: str = ""
    activation_source: str = "explicit"
    test_only_enable_token: str = ""


@dataclass(frozen=True, slots=True)
class LocalTestDBAdapterBoundary:
    """Planned-disabled boundary object; it owns no persistence state."""

    boundary_version: str = LOCAL_TEST_DB_ADAPTER_BOUNDARY_VERSION
    boundary_mode: str = BOUNDARY_MODE
    boundary_status: str = DISABLED_STATUS

    def metadata(self) -> dict[str, Any]:
        """Return metadata proving no DB behavior is active."""

        return _disabled_metadata()

    def validate_activation_request(self, config: LocalTestDBAdapterConfig | Mapping[str, Any]) -> dict[str, Any]:
        """Validate a future activation request but keep the boundary disabled."""

        return validate_local_test_db_activation_request(config)

    def validate_candidate_batch(self, candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Validate candidate payload shape for a future DB adapter without storing it."""

        return validate_local_test_db_candidate_batch(candidates)

    def write_batch(
        self,
        candidates: Sequence[Mapping[str, Any]],
        *,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Fail closed for writes; R7BX does not implement persistence."""

        raise LocalTestDBAdapterBoundaryError(
            "local test DB adapter boundary is planned-disabled by default; "
            "write_batch is not available; no persistence occurred"
        )


def make_disabled_local_test_db_adapter_boundary() -> LocalTestDBAdapterBoundary:
    """Return the only R7BX boundary object: planned-disabled and test-only."""

    return LocalTestDBAdapterBoundary()


def validate_local_test_db_activation_request(
    config: LocalTestDBAdapterConfig | Mapping[str, Any],
) -> dict[str, Any]:
    """Validate future local DB activation while returning no active adapter."""

    config_data = _config_to_dict(config)
    _validate_no_forbidden_config(config_data)

    if config_data.get("activation_source") in AUTO_ACTIVATION_SOURCES:
        _raise_activation_rejected()
    if config_data.get("enabled") is not True:
        _raise_activation_rejected()
    if config_data.get("test_only") is not True:
        _raise_activation_rejected()
    if config_data.get("test_only_enable_token") != TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN:
        _raise_activation_rejected()
    if config_data.get("environment") != VALID_LOCAL_TEST_ENVIRONMENT:
        _raise_activation_rejected()
    if config_data.get("db_selection") not in ALLOWED_TEST_DB_SELECTIONS:
        _raise_activation_rejected()

    db_selection = config_data.get("db_selection")
    dsn = config_data.get("dsn")
    if db_selection == "sqlite_memory" and dsn != ":memory:":
        _raise_activation_rejected()
    if db_selection == "sqlite_temp_file" and dsn != "planned_pytest_tmp_path_only":
        _raise_activation_rejected()

    result = _disabled_metadata()
    result.update(
        {
            "activation_request_validated": True,
            "planned_adapter_only": True,
            "test_only": True,
            "environment": VALID_LOCAL_TEST_ENVIRONMENT,
            "db_selection": db_selection,
            "future_activation_status": PLANNED_DISABLED_STATUS,
            "transaction_policy": transaction_idempotency_policy(),
        }
    )
    return result


def validate_local_test_db_candidate_batch(
    candidates: Sequence[Mapping[str, Any]],
    *,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> dict[str, Any]:
    """Validate future persistence candidates without retaining or storing rows."""

    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
        _raise_candidate_rejected()

    idempotency_to_hash: dict[str, str] = {}
    review_item_to_idempotency: dict[str, str] = {}
    candidate_count = 0

    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            _raise_candidate_rejected()
        candidate_count += 1
        _validate_no_forbidden_candidate(candidate)
        _validate_required_candidate_fields(candidate)
        _validate_evidence_preview(candidate, preview_limit=preview_limit)

        review_item_id = str(candidate["review_item_id"])
        idempotency_key = str(candidate["idempotency_key"])
        record_payload_hash = str(candidate["record_payload_hash"])
        _validate_hash_like(idempotency_key)
        _validate_hash_like(record_payload_hash)

        if idempotency_key in idempotency_to_hash:
            _raise_candidate_rejected()
        if review_item_id in review_item_to_idempotency:
            _raise_candidate_rejected()

        idempotency_to_hash[idempotency_key] = record_payload_hash
        review_item_to_idempotency[review_item_id] = idempotency_key

    result = _disabled_metadata()
    result.update(
        {
            "candidate_validation_status": "VALIDATED_FOR_FUTURE_LOCAL_TEST_DB_ONLY",
            "candidate_count": candidate_count,
            "batch_atomic_by_contract": True,
            "no_partial_success_by_contract": True,
            "stores_records": False,
            "transaction_policy": transaction_idempotency_policy(),
        }
    )
    return result


def transaction_idempotency_policy() -> dict[str, Any]:
    """Expose planned future transaction/idempotency semantics as metadata."""

    return {
        "batch_atomic_by_contract": True,
        "no_partial_success_by_default": True,
        "invalid_row_rejects_entire_batch": True,
        "same_idempotency_key_same_record_payload_hash": "planned_deterministic_retry_no_duplicate",
        "same_idempotency_key_different_record_payload_hash": "planned_conflict_fail_closed",
        "same_review_item_id_conflicting_identity": "planned_conflict_fail_closed",
        "record_payload_hash_required": True,
        "silent_duplicate_insert_allowed": False,
    }


def _disabled_metadata() -> dict[str, Any]:
    return {
        "boundary_version": LOCAL_TEST_DB_ADAPTER_BOUNDARY_VERSION,
        "boundary_mode": BOUNDARY_MODE,
        "boundary_status": PLANNED_DISABLED_STATUS,
        "test_only": True,
        "database_connection_opened": False,
        "schema_created": False,
        "migration_created": False,
        "table_created": False,
        "storage_write_count": 0,
        "database_write_count": 0,
        "filesystem_write_count": 0,
        "network_call_count": 0,
        "clean_data_write_count": 0,
        "delivery_write_count": 0,
        "export_write_count": 0,
        "writes_review_queue": False,
        "writes_clean_data": False,
        "writes_delivery": False,
        "writes_export": False,
        "persists_records": False,
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
    }


def _config_to_dict(config: LocalTestDBAdapterConfig | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(config, LocalTestDBAdapterConfig):
        return {field.name: getattr(config, field.name) for field in fields(config)}
    if isinstance(config, Mapping):
        return deepcopy(dict(config))
    _raise_activation_rejected()


def _validate_no_forbidden_config(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_CONFIG_KEYS:
                _raise_activation_rejected()
            _validate_no_forbidden_config(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            _validate_no_forbidden_config(child)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_CONFIG_VALUE_MARKERS):
            _raise_activation_rejected()


def _validate_no_forbidden_candidate(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_CANDIDATE_KEYS:
                _raise_candidate_rejected()
            _validate_no_forbidden_candidate(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            _validate_no_forbidden_candidate(child)


def _validate_required_candidate_fields(candidate: Mapping[str, Any]) -> None:
    for field_name in REQUIRED_CANDIDATE_FIELDS:
        if not candidate.get(field_name):
            _raise_candidate_rejected()


def _validate_evidence_preview(candidate: Mapping[str, Any], *, preview_limit: int) -> None:
    preview = candidate.get("evidence_preview")
    if preview is not None:
        if not isinstance(preview, str) or len(preview) > preview_limit:
            _raise_candidate_rejected()


def _validate_hash_like(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        _raise_candidate_rejected()


def _raise_activation_rejected() -> None:
    raise LocalTestDBAdapterActivationError(
        "local test DB adapter boundary is planned-disabled by default; "
        "activation request is not accepted; no database connection occurred"
    )


def _raise_candidate_rejected() -> None:
    raise LocalTestDBAdapterCandidateError(
        "local test DB adapter boundary is planned-disabled by default; "
        "candidate payload is not accepted; no persistence occurred"
    )


__all__ = [
    "ALLOWED_TEST_DB_SELECTIONS",
    "BOUNDARY_MODE",
    "DEFAULT_PREVIEW_LIMIT",
    "DISABLED_STATUS",
    "LOCAL_TEST_DB_ADAPTER_BOUNDARY_VERSION",
    "LocalTestDBAdapterActivationError",
    "LocalTestDBAdapterBoundary",
    "LocalTestDBAdapterBoundaryError",
    "LocalTestDBAdapterCandidateError",
    "LocalTestDBAdapterConfig",
    "PLANNED_DISABLED_STATUS",
    "READINESS_GATES_CLOSED",
    "TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN",
    "VALID_LOCAL_TEST_ENVIRONMENT",
    "make_disabled_local_test_db_adapter_boundary",
    "transaction_idempotency_policy",
    "validate_local_test_db_activation_request",
    "validate_local_test_db_candidate_batch",
]
