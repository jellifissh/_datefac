"""Test-only in-memory local DB prototype for R7CB.

This module is intentionally under tests/agent. It uses a test-owned
sqlite3 in-memory connection to prove minimum review_queue persistence
semantics without production integration.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, fields
from typing import Any

LOCAL_TEST_DB_PROTOTYPE_VERSION = "r7cb_local_test_db_prototype_minimum_test_only_v1"
TEST_ONLY_LOCAL_TEST_DB_PROTOTYPE_ENABLE_TOKEN = "R7CB_LOCAL_TEST_DB_PROTOTYPE_ENABLE"
VALID_LOCAL_TEST_ENVIRONMENT = "local_test"
VALID_LOCAL_TEST_STORAGES: frozenset[str] = frozenset({"sqlite_memory", "in_memory_sqlite"})
TABLE_NAME = "review_queue_items"
DEFAULT_EVIDENCE_PREVIEW_LIMIT = 160

READINESS_GATES_CLOSED: dict[str, bool] = {
    "client_ready": False,
    "production_ready": False,
    "formal_client_export_allowed": False,
    "demo_export_only": True,
}

FORBIDDEN_CONFIG_KEYS: frozenset[str] = frozenset(
    {
        "api_key",
        "clean_data_intent",
        "clean_data_payload",
        "connection_string",
        "database_path",
        "database_url",
        "db_password",
        "db_secret",
        "db_token",
        "delivery_export_intent",
        "delivery_payload",
        "dsn",
        "endpoint",
        "export_intent",
        "export_payload",
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
        "schema",
        "schema_name",
        "secret",
        "server",
        "table_name",
    }
)

FORBIDDEN_VALUE_MARKERS: tuple[str, ...] = (
    "postgresql://",
    "postgres://",
    "mysql://",
    "mariadb://",
    "sqlserver://",
    "sqlite://",
    "http://",
    "https://",
    "server=",
    "password=",
    "pwd=",
    "secret",
    "prod",
    "production",
    "staging",
    "endpoint",
    "rds.",
    "amazonaws",
    "c:/",
    "d:/",
    "\\\\",
    "/output/",
    "\\output\\",
)

FORBIDDEN_CANDIDATE_KEYS: frozenset[str] = frozenset(
    {
        "approved_export_payload",
        "caller_supplied_db_primary_key",
        "caller_supplied_db_receipt",
        "caller_supplied_db_row",
        "clean_data",
        "clean_data_intent",
        "clean_data_payload",
        "committed_db_receipt",
        "database_row",
        "db_primary_key",
        "db_receipt",
        "db_row",
        "delivery_export_intent",
        "delivery_payload",
        "export_intent",
        "export_payload",
        "full_source_text",
        "internal_adapter_state",
        "raw_excel_payload",
        "raw_llm_payload",
        "raw_mineru_payload",
        "raw_ocr_payload",
        "raw_parser_payload",
        "raw_vlm_payload",
        "readiness_gates",
        "readiness_override",
        "source_text",
        "source_text_full",
        "unbounded_evidence_text",
    }
)

REQUIRED_CANDIDATE_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "run_id",
    "candidate_id",
    "idempotency_key",
    "record_payload_hash",
    "status",
    "blocked_delivery_reason",
    "source_trace",
    "created_at",
)


class LocalTestDBPrototypeError(ValueError):
    """Base error for the R7CB test-only local DB prototype."""


class LocalTestDBActivationError(LocalTestDBPrototypeError):
    """Raised when explicit local-test activation gates are not satisfied."""


class LocalTestDBCandidateError(LocalTestDBPrototypeError):
    """Raised when a review_queue candidate fails closed before/during write."""


class LocalTestDBWriteConflictError(LocalTestDBPrototypeError):
    """Raised when local idempotency or identity constraints conflict."""


class LocalTestDBClosedError(LocalTestDBPrototypeError):
    """Raised when operations are attempted after teardown."""


@dataclass(frozen=True, slots=True)
class LocalTestDBPrototypeConfig:
    """Explicit test-only config for the R7CB in-memory prototype."""

    test_only: bool = False
    environment: str = ""
    storage: str = ""
    explicit_prototype_enabled: bool = False
    activation_source: str = "explicit"
    test_only_enable_token: str = ""


class LocalTestDBPrototype:
    """Minimum test-only SQLite :memory: review_queue prototype."""

    def __init__(self, config: LocalTestDBPrototypeConfig | Mapping[str, Any]) -> None:
        self._config = _validate_activation_config(config)
        self._connection = sqlite3.connect(":memory:")
        self._connection.row_factory = sqlite3.Row
        self._closed = False
        self._create_schema()

    def metadata(self) -> dict[str, Any]:
        """Return metadata making the test-only boundary explicit."""

        return {
            "prototype_version": LOCAL_TEST_DB_PROTOTYPE_VERSION,
            "test_only": True,
            "environment": VALID_LOCAL_TEST_ENVIRONMENT,
            "storage": "sqlite_memory",
            "storage_identifier": ":memory:",
            "database_connection_scope": "test_owned_in_memory",
            "schema_created": True,
            "table_created": True,
            "table_name_owned_by_module": True,
            "writes_test_only_database": True,
            "writes_production_database": False,
            "writes_filesystem": False,
            "writes_network": False,
            "writes_clean_data": False,
            "writes_delivery": False,
            "writes_export": False,
            "filesystem_write_count": 0,
            "network_call_count": 0,
            "clean_data_write_count": 0,
            "delivery_write_count": 0,
            "export_write_count": 0,
            "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        }

    def write_batch(self, candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Write a candidate batch atomically to the test-only in-memory DB."""

        self._ensure_open()
        if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
            _raise_candidate_rejected()

        candidate_copies: list[dict[str, Any]] = []
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                _raise_candidate_rejected()
            candidate_copies.append(deepcopy(dict(candidate)))
        _precheck_forbidden_candidate_payloads(candidate_copies)

        inserted_count = 0
        deduplicated_count = 0
        try:
            with self._connection:
                for candidate in candidate_copies:
                    normalized = _normalize_candidate(candidate)
                    existing_by_idempotency = self._get_by_idempotency_key(normalized["idempotency_key"])
                    existing_by_review_item = self.get_by_review_item_id(normalized["review_item_id"])

                    if existing_by_idempotency is not None:
                        if existing_by_idempotency["record_payload_hash"] != normalized["record_payload_hash"]:
                            _raise_write_conflict()
                        if existing_by_idempotency["review_item_id"] != normalized["review_item_id"]:
                            _raise_write_conflict()
                        deduplicated_count += 1
                        continue

                    if existing_by_review_item is not None:
                        _raise_write_conflict()

                    self._connection.execute(
                        f"""
                        INSERT INTO {TABLE_NAME} (
                            review_item_id,
                            run_id,
                            candidate_id,
                            idempotency_key,
                            record_payload_hash,
                            status,
                            blocked_delivery_reason,
                            evidence_preview,
                            source_trace_json,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            normalized["review_item_id"],
                            normalized["run_id"],
                            normalized["candidate_id"],
                            normalized["idempotency_key"],
                            normalized["record_payload_hash"],
                            normalized["status"],
                            normalized["blocked_delivery_reason"],
                            normalized["evidence_preview"],
                            normalized["source_trace_json"],
                            normalized["created_at"],
                        ),
                    )
                    inserted_count += 1
        except sqlite3.IntegrityError as error:
            raise LocalTestDBWriteConflictError(
                "local test DB write conflict; no production persistence occurred"
            ) from error

        return {
            "prototype_version": LOCAL_TEST_DB_PROTOTYPE_VERSION,
            "test_only": True,
            "persistence_status": "TEST_ONLY_IN_MEMORY_SQLITE_WRITTEN",
            "storage": "sqlite_memory",
            "batch_atomic": True,
            "inserted_count": inserted_count,
            "deduplicated_count": deduplicated_count,
            "input_count": len(candidate_copies),
            "database_write_count": inserted_count,
            "writes_production_database": False,
            "filesystem_write_count": 0,
            "network_call_count": 0,
            "clean_data_write_count": 0,
            "delivery_write_count": 0,
            "export_write_count": 0,
            "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        }

    def get_by_review_item_id(self, review_item_id: str) -> dict[str, Any] | None:
        """Return one metadata-only row from the test-owned in-memory DB."""

        self._ensure_open()
        row = self._connection.execute(
            f"SELECT * FROM {TABLE_NAME} WHERE review_item_id = ?",
            (review_item_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_dict(row)

    def list_by_run_id(self, run_id: str) -> list[dict[str, Any]]:
        """Return metadata-only rows for one run from the test-owned DB."""

        self._ensure_open()
        rows = self._connection.execute(
            f"SELECT * FROM {TABLE_NAME} WHERE run_id = ? ORDER BY review_item_id",
            (run_id,),
        ).fetchall()
        return [_row_to_dict(row) for row in rows]

    def close(self) -> None:
        """Close the in-memory connection and make future operations fail closed."""

        if not self._closed:
            self._connection.close()
            self._closed = True

    def _create_schema(self) -> None:
        self._connection.execute(
            f"""
            CREATE TABLE {TABLE_NAME} (
                review_item_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                record_payload_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                blocked_delivery_reason TEXT NOT NULL,
                evidence_preview TEXT,
                source_trace_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise LocalTestDBClosedError("local test DB prototype is closed")

    def _get_by_idempotency_key(self, idempotency_key: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            f"SELECT * FROM {TABLE_NAME} WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_dict(row)


def make_local_test_db_prototype(config: LocalTestDBPrototypeConfig | Mapping[str, Any]) -> LocalTestDBPrototype:
    """Create the minimum test-only in-memory DB prototype after gates pass."""

    return LocalTestDBPrototype(config)


def _validate_activation_config(config: LocalTestDBPrototypeConfig | Mapping[str, Any]) -> dict[str, Any]:
    config_data = _config_to_dict(config)
    _validate_no_forbidden_config(config_data)

    if config_data.get("activation_source") in {"environment", "env", "production", "repository_factory"}:
        _raise_activation_rejected()
    if config_data.get("test_only") is not True:
        _raise_activation_rejected()
    if config_data.get("environment") != VALID_LOCAL_TEST_ENVIRONMENT:
        _raise_activation_rejected()
    if config_data.get("storage") not in VALID_LOCAL_TEST_STORAGES:
        _raise_activation_rejected()
    if config_data.get("explicit_prototype_enabled") is not True:
        _raise_activation_rejected()
    if config_data.get("test_only_enable_token") != TEST_ONLY_LOCAL_TEST_DB_PROTOTYPE_ENABLE_TOKEN:
        _raise_activation_rejected()

    return config_data


def _config_to_dict(config: LocalTestDBPrototypeConfig | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(config, LocalTestDBPrototypeConfig):
        return {field.name: getattr(config, field.name) for field in fields(config)}
    if isinstance(config, Mapping):
        return deepcopy(dict(config))
    _raise_activation_rejected()


def _normalize_candidate(candidate: Mapping[str, Any]) -> dict[str, str | None]:
    _validate_candidate_shape(candidate)
    source_trace_json = json.dumps(candidate["source_trace"], sort_keys=True, separators=(",", ":"))
    return {
        "review_item_id": str(candidate["review_item_id"]),
        "run_id": str(candidate["run_id"]),
        "candidate_id": str(candidate["candidate_id"]),
        "idempotency_key": str(candidate["idempotency_key"]),
        "record_payload_hash": str(candidate["record_payload_hash"]),
        "status": str(candidate["status"]),
        "blocked_delivery_reason": str(candidate["blocked_delivery_reason"]),
        "evidence_preview": None if candidate.get("evidence_preview") is None else str(candidate["evidence_preview"]),
        "source_trace_json": source_trace_json,
        "created_at": str(candidate["created_at"]),
    }


def _validate_candidate_shape(candidate: Mapping[str, Any]) -> None:
    if not isinstance(candidate, Mapping):
        _raise_candidate_rejected()
    for field_name in REQUIRED_CANDIDATE_FIELDS:
        if candidate.get(field_name) in (None, ""):
            _raise_candidate_rejected()
    if not _is_hash_like(str(candidate["idempotency_key"])):
        _raise_candidate_rejected()
    if not _is_hash_like(str(candidate["record_payload_hash"])):
        _raise_candidate_rejected()
    if not isinstance(candidate["source_trace"], Mapping):
        _raise_candidate_rejected()
    evidence_preview = candidate.get("evidence_preview")
    if evidence_preview is not None:
        if not isinstance(evidence_preview, str):
            _raise_candidate_rejected()
        if len(evidence_preview) > DEFAULT_EVIDENCE_PREVIEW_LIMIT:
            _raise_candidate_rejected()


def _precheck_forbidden_candidate_payloads(candidates: Sequence[Mapping[str, Any]]) -> None:
    for candidate in candidates:
        _validate_no_forbidden_candidate(candidate)


def _validate_no_forbidden_config(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in FORBIDDEN_CONFIG_KEYS:
                _raise_activation_rejected()
            _validate_no_forbidden_config(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            _validate_no_forbidden_config(child)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_VALUE_MARKERS):
            _raise_activation_rejected()


def _validate_no_forbidden_candidate(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in FORBIDDEN_CANDIDATE_KEYS:
                _raise_candidate_rejected()
            _validate_no_forbidden_candidate(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            _validate_no_forbidden_candidate(child)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    source_trace = json.loads(row["source_trace_json"])
    return {
        "review_item_id": row["review_item_id"],
        "run_id": row["run_id"],
        "candidate_id": row["candidate_id"],
        "idempotency_key": row["idempotency_key"],
        "record_payload_hash": row["record_payload_hash"],
        "status": row["status"],
        "blocked_delivery_reason": row["blocked_delivery_reason"],
        "evidence_preview": row["evidence_preview"],
        "source_trace": source_trace,
        "created_at": row["created_at"],
    }


def _is_hash_like(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _raise_activation_rejected() -> None:
    raise LocalTestDBActivationError(
        "local test DB prototype activation rejected; no database connection occurred"
    )


def _raise_candidate_rejected() -> None:
    raise LocalTestDBCandidateError(
        "local test DB candidate rejected; no production persistence occurred"
    )


def _raise_write_conflict() -> None:
    raise LocalTestDBWriteConflictError(
        "local test DB write conflict; no production persistence occurred"
    )


__all__ = [
    "DEFAULT_EVIDENCE_PREVIEW_LIMIT",
    "LOCAL_TEST_DB_PROTOTYPE_VERSION",
    "LocalTestDBActivationError",
    "LocalTestDBCandidateError",
    "LocalTestDBClosedError",
    "LocalTestDBPrototype",
    "LocalTestDBPrototypeConfig",
    "LocalTestDBPrototypeError",
    "LocalTestDBWriteConflictError",
    "READINESS_GATES_CLOSED",
    "TEST_ONLY_LOCAL_TEST_DB_PROTOTYPE_ENABLE_TOKEN",
    "VALID_LOCAL_TEST_ENVIRONMENT",
    "VALID_LOCAL_TEST_STORAGES",
    "make_local_test_db_prototype",
]
