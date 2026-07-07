"""Test-only schema alignment contract for R7BI.

This module validates an already-built R7BE dry-run integration output and
maps its R7BC writer preview records into a future review_queue record preview.
It performs no I/O and has no production hook.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from tests.agent.review_queue_writer_contract_348n import WRITER_CONTRACT_VERSION
from tests.agent.review_queue_writer_dry_run_integration_boundary_348n import INTEGRATION_BOUNDARY_CONTRACT_VERSION

SCHEMA_ALIGNMENT_CONTRACT_VERSION = "r7bi_review_queue_writer_schema_alignment_contract_test_only_v1"
FUTURE_REVIEW_QUEUE_SCHEMA_VERSION = "future_review_queue_record_preview_v1"
TEST_ONLY_SCHEMA_ALIGNMENT_ENABLE_TOKEN = "R7BI_TEST_ONLY_SCHEMA_ALIGNMENT_ENABLE"
DEFAULT_PREVIEW_LIMIT = 160

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

REVIEW_BOUND_STATUSES: tuple[str, ...] = (
    "UNVERIFIED",
    "DISAGREED",
    "AMBIGUOUS",
    "MISSING_EVIDENCE",
    "PARSE_SKIPPED",
)

REQUIRED_INTEGRATION_FIELDS: tuple[str, ...] = (
    "integration_status",
    "dry_run_only",
    "integration_contract_version",
    "adapter_audit_contract",
    "writer_dry_run_preview",
    "integration_summary",
)

REQUIRED_WRITER_PREVIEW_FIELDS: tuple[str, ...] = (
    "writer_status",
    "dry_run_only",
    "review_queue_dry_run_records",
    "dry_run_summary",
)

REQUIRED_WRITER_RECORD_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "run_id",
    "source_file_hash",
    "input_file_hashes",
    "adapter_version",
    "contract_version",
    "adapter_contract_version",
    "audit_hash",
    "metric_name",
    "period",
    "candidate_value",
    "candidate_unit",
    "agreement_status",
    "review_status",
    "reviewer_action",
    "review_reason",
    "blocked_delivery_reason",
    "evidence_preview",
    "source_trace",
    "idempotency_key",
    "dry_run_only",
    "dry_run_action",
    "record_payload_hash",
)

FUTURE_PERSISTENCE_PREVIEW_FIELDS: tuple[str, ...] = (
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
    "reviewer_action",
    "review_reason",
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

FIELD_CLASSIFICATIONS: dict[str, str] = {
    "run_id": "required_audit",
    "adapter_version": "required_audit",
    "contract_version": "test_only_only",
    "integration_boundary_version": "dry_run_only",
    "writer_contract_version": "required_audit",
    "input_file_hashes": "required_audit",
    "source_file_hash": "required_persistence_safe",
    "review_item_id": "required_persistence_safe",
    "audit_hash": "required_audit",
    "idempotency_key": "required_idempotency",
    "metric_name": "required_persistence_safe",
    "period": "required_persistence_safe",
    "candidate_value": "required_persistence_safe",
    "normalized_candidate_value": "normalized_derived",
    "agreement_status": "required_persistence_safe",
    "review_status": "required_persistence_safe",
    "review_reason": "required_persistence_safe",
    "reviewer_action": "required_persistence_safe",
    "blocked_delivery_reason": "required_delivery_blocking",
    "re_audit_required": "required_reaudit",
    "evidence_preview": "optional_bounded_evidence",
    "source_trace": "required_audit",
    "dry_run_only": "dry_run_only",
    "readiness_gates": "required_audit",
    "schema_version": "required_persistence_safe",
    "validation_errors": "dry_run_only",
}

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
        "raw_extraction_payload",
        "llm_response",
        "vlm_response",
        "raw_llm_response",
        "raw_vlm_response",
        "clean_data",
        "clean_data_record",
        "clean_data_records",
        "clean_data_payload",
        "clean_data_intent",
        "delivery_payload",
        "export_payload",
        "formal_delivery_payload",
        "formal_export_payload",
        "production_writer_config",
        "production_config",
        "writer_config",
        "direct_writer_preview",
        "user_provided_writer_preview",
        "test_only_enable_token",
        "test_only_writer_config",
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
        "database_id",
        "execution_id",
    }
)


@dataclass(frozen=True, slots=True)
class ReviewQueueWriterSchemaAlignmentContractConfig:
    """Explicit test-only feature flag for the R7BI schema alignment contract."""

    enabled: bool = False
    contract_version: str = SCHEMA_ALIGNMENT_CONTRACT_VERSION
    test_only_enable_token: str = ""


class ReviewQueueWriterSchemaAlignmentContractError(ValueError):
    """Raised when schema alignment validation fails closed."""


def build_review_queue_writer_schema_alignment_preview(
    dry_run_integration_output: dict[str, Any],
    config: ReviewQueueWriterSchemaAlignmentContractConfig | None = None,
    *,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> dict[str, Any]:
    """Return an in-memory future review_queue schema alignment preview."""

    contract_config = config or ReviewQueueWriterSchemaAlignmentContractConfig()
    _validate_config(contract_config)
    if not contract_config.enabled:
        return _disabled_result(contract_config)
    if contract_config.test_only_enable_token != TEST_ONLY_SCHEMA_ALIGNMENT_ENABLE_TOKEN:
        raise ReviewQueueWriterSchemaAlignmentContractError(
            "explicit R7BI test-only schema alignment enable token is required"
        )

    validate_dry_run_integration_output(dry_run_integration_output, preview_limit=preview_limit)
    payload = deepcopy(dry_run_integration_output)
    integration_summary = payload["integration_summary"]
    writer_preview = payload["writer_dry_run_preview"]
    writer_summary = writer_preview["dry_run_summary"]
    records = [
        _future_review_queue_record_preview(record, writer_contract_version=writer_summary["writer_contract_version"])
        for record in writer_preview["review_queue_dry_run_records"]
    ]
    summary = _schema_alignment_summary(
        config=contract_config,
        integration_summary=integration_summary,
        writer_summary=writer_summary,
        records=records,
    )
    output = {
        "schema_alignment_status": "ENABLED_TEST_ONLY_SCHEMA_ALIGNMENT",
        "dry_run_only": True,
        "schema_alignment_contract_version": contract_config.contract_version,
        "future_review_queue_schema_version": FUTURE_REVIEW_QUEUE_SCHEMA_VERSION,
        "integration_boundary_version": payload["integration_contract_version"],
        "writer_contract_version": writer_summary["writer_contract_version"],
        "source_adapter_contract_version": writer_summary["source_adapter_contract_version"],
        "run_id": integration_summary["run_id"],
        "adapter_version": integration_summary["adapter_version"],
        "input_file_hashes": deepcopy(integration_summary["input_file_hashes"]),
        "field_classification": deepcopy(FIELD_CLASSIFICATIONS),
        "future_review_queue_record_previews": records,
        "schema_alignment_summary": summary,
    }
    validate_no_forbidden_fields(output, preview_limit=preview_limit)
    return deepcopy(output)


def validate_dry_run_integration_output(value: Any, *, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> None:
    """Validate the only accepted input layer: R7BE dry-run integration output."""

    if not isinstance(value, dict):
        raise ReviewQueueWriterSchemaAlignmentContractError("dry-run integration output must be an object")
    validate_no_forbidden_fields(value, preview_limit=preview_limit)
    _require_exact_fields(value, REQUIRED_INTEGRATION_FIELDS, "dry-run integration output")
    if value["integration_status"] != "ENABLED_TEST_ONLY_DRY_RUN":
        raise ReviewQueueWriterSchemaAlignmentContractError("integration output must be enabled test-only dry-run output")
    if value["dry_run_only"] is not True:
        raise ReviewQueueWriterSchemaAlignmentContractError("integration output must remain dry_run_only")
    if value["integration_contract_version"] != INTEGRATION_BOUNDARY_CONTRACT_VERSION:
        raise ReviewQueueWriterSchemaAlignmentContractError("unexpected integration boundary contract version")

    adapter_audit_contract = value["adapter_audit_contract"]
    integration_summary = value["integration_summary"]
    writer_preview = value["writer_dry_run_preview"]
    _validate_adapter_audit_contract(adapter_audit_contract)
    _validate_integration_summary(
        integration_summary,
        adapter_audit_contract=adapter_audit_contract,
        writer_preview=writer_preview,
        preview_limit=preview_limit,
    )
    _validate_writer_preview(writer_preview, integration_summary=integration_summary, preview_limit=preview_limit)


def validate_no_forbidden_fields(value: Any, *, preview_limit: int = DEFAULT_PREVIEW_LIMIT, path: str = "$") -> None:
    """Reject raw artifacts, non-deterministic fields, writes, readiness, and clean intent."""

    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                raise ReviewQueueWriterSchemaAlignmentContractError(f"forbidden field at {path}.{key}: {key}")
            if key in NON_DETERMINISTIC_KEYS:
                raise ReviewQueueWriterSchemaAlignmentContractError(f"non-deterministic field at {path}.{key}: {key}")
            if key == "evidence_level" and _clean(child) == "STRONG_EVIDENCE":
                raise ReviewQueueWriterSchemaAlignmentContractError("STRONG_EVIDENCE promotion is forbidden")
            if key in {"client_ready", "production_ready", "formal_client_export_allowed"} and child is True:
                raise ReviewQueueWriterSchemaAlignmentContractError(f"readiness gate opened at {path}.{key}")
            if key in {"clean_data_eligible", "clean_data_admitted", "delivery_clean_admitted"} and child is True:
                raise ReviewQueueWriterSchemaAlignmentContractError("clean_data or delivery admission is forbidden")
            if key in {
                "writes_review_queue",
                "writes_clean_data",
                "writes_delivery",
                "writes_filesystem",
                "writes_database",
                "writes_export",
            } and child is True:
                raise ReviewQueueWriterSchemaAlignmentContractError(f"write intent is forbidden at {path}.{key}")
            if key == "production_hook" and child is True:
                raise ReviewQueueWriterSchemaAlignmentContractError("production hooks are forbidden")
            if key == "evidence_preview":
                _validate_bounded_preview(child, preview_limit)
            validate_no_forbidden_fields(child, preview_limit=preview_limit, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_no_forbidden_fields(child, preview_limit=preview_limit, path=f"{path}[{index}]")


def field_classifications() -> dict[str, str]:
    """Return field classifications for tests and reports."""

    return deepcopy(FIELD_CLASSIFICATIONS)


def _validate_config(config: ReviewQueueWriterSchemaAlignmentContractConfig) -> None:
    if config.contract_version != SCHEMA_ALIGNMENT_CONTRACT_VERSION:
        raise ReviewQueueWriterSchemaAlignmentContractError("unexpected schema alignment contract version")


def _disabled_result(config: ReviewQueueWriterSchemaAlignmentContractConfig) -> dict[str, Any]:
    return {
        "schema_alignment_status": "DISABLED",
        "enabled": False,
        "dry_run_only": True,
        "schema_alignment_contract_version": config.contract_version,
        "future_review_queue_record_previews": [],
        "schema_alignment_summary": {
            "schema_alignment_status": "DISABLED",
            "enabled": False,
            "reason": "disabled_by_default",
            "future_preview_record_count": 0,
            "clean_data_write_count": 0,
            "delivery_write_count": 0,
            "filesystem_write_count": 0,
            "database_write_count": 0,
            "export_write_count": 0,
            "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
            "external_call_counts": deepcopy(EXTERNAL_CALL_COUNTS_ZERO),
            "validation_errors": [],
        },
    }


def _validate_adapter_audit_contract(value: Any) -> None:
    if not isinstance(value, dict):
        raise ReviewQueueWriterSchemaAlignmentContractError("adapter_audit_contract must be an object")
    for field in ("run_id", "adapter_version", "contract_version", "input_file_hashes", "adapter_audit_hash"):
        if not _clean(value.get(field)):
            raise ReviewQueueWriterSchemaAlignmentContractError(f"adapter_audit_contract {field} is required")
    if value.get("readiness_gates") != READINESS_GATES_CLOSED:
        raise ReviewQueueWriterSchemaAlignmentContractError("adapter readiness gates must remain closed")
    if value.get("external_call_counts") != EXTERNAL_CALL_COUNTS_ZERO:
        raise ReviewQueueWriterSchemaAlignmentContractError("adapter external call counts must stay zero")
    boundary_flags = value.get("boundary_flags")
    if not _boundary_flags_are_closed(boundary_flags, allow_filesystem_flags_absent=True):
        raise ReviewQueueWriterSchemaAlignmentContractError("adapter boundary flags must remain closed")


def _validate_integration_summary(
    value: Any,
    *,
    adapter_audit_contract: dict[str, Any],
    writer_preview: Any,
    preview_limit: int,
) -> None:
    if not isinstance(value, dict):
        raise ReviewQueueWriterSchemaAlignmentContractError("integration_summary must be an object")
    for field in (
        "integration_status",
        "dry_run_only",
        "integration_contract_version",
        "writer_contract_version",
        "source_adapter_contract_version",
        "run_id",
        "adapter_version",
        "input_file_hashes",
        "adapter_audit_hash",
        "review_queue_dry_run_record_count",
        "writer_preview_hash",
        "readiness_gates",
        "external_call_counts",
        "boundary_flags",
    ):
        if field not in value:
            raise ReviewQueueWriterSchemaAlignmentContractError(f"integration_summary {field} is required")
    if value["integration_status"] != "ENABLED_TEST_ONLY_DRY_RUN":
        raise ReviewQueueWriterSchemaAlignmentContractError("integration summary must be enabled test-only dry-run")
    if value["dry_run_only"] is not True:
        raise ReviewQueueWriterSchemaAlignmentContractError("integration summary must remain dry_run_only")
    if value["integration_contract_version"] != INTEGRATION_BOUNDARY_CONTRACT_VERSION:
        raise ReviewQueueWriterSchemaAlignmentContractError("integration summary contract mismatch")
    if value["writer_contract_version"] != WRITER_CONTRACT_VERSION:
        raise ReviewQueueWriterSchemaAlignmentContractError("unexpected writer contract version")
    if value["run_id"] != adapter_audit_contract["run_id"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("run_id mismatch between integration and adapter audit")
    if value["adapter_version"] != adapter_audit_contract["adapter_version"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("adapter_version mismatch")
    if value["input_file_hashes"] != adapter_audit_contract["input_file_hashes"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("input_file_hashes mismatch")
    if value["adapter_audit_hash"] != adapter_audit_contract["adapter_audit_hash"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("adapter_audit_hash mismatch")
    if value["readiness_gates"] != READINESS_GATES_CLOSED:
        raise ReviewQueueWriterSchemaAlignmentContractError("integration readiness gates must remain closed")
    if value["external_call_counts"] != EXTERNAL_CALL_COUNTS_ZERO:
        raise ReviewQueueWriterSchemaAlignmentContractError("integration external call counts must stay zero")
    if not _boundary_flags_are_closed(value["boundary_flags"]):
        raise ReviewQueueWriterSchemaAlignmentContractError("integration boundary flags must remain closed")
    for key in ("clean_data_write_count", "delivery_write_count", "filesystem_write_count", "database_write_count", "export_write_count"):
        if value.get(key) != 0:
            raise ReviewQueueWriterSchemaAlignmentContractError(f"integration {key} must remain zero")
    if _hash_json(writer_preview) != value["writer_preview_hash"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer_preview_hash mismatch")
    _validate_bounded_preview(json.dumps(value, ensure_ascii=False, sort_keys=True), max(preview_limit * 100, preview_limit))


def _validate_writer_preview(value: Any, *, integration_summary: dict[str, Any], preview_limit: int) -> None:
    if not isinstance(value, dict):
        raise ReviewQueueWriterSchemaAlignmentContractError("writer_dry_run_preview must be an object")
    _require_exact_fields(value, REQUIRED_WRITER_PREVIEW_FIELDS, "writer_dry_run_preview")
    if value["writer_status"] != "ENABLED_TEST_ONLY_DRY_RUN":
        raise ReviewQueueWriterSchemaAlignmentContractError("writer preview must be enabled test-only dry-run")
    if value["dry_run_only"] is not True:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer preview must remain dry_run_only")
    records = value["review_queue_dry_run_records"]
    if not isinstance(records, list):
        raise ReviewQueueWriterSchemaAlignmentContractError("writer preview records must be a list")
    summary = value["dry_run_summary"]
    _validate_writer_summary(summary, records=records, integration_summary=integration_summary)
    for record in records:
        _validate_writer_record(record, writer_summary=summary, preview_limit=preview_limit)


def _validate_writer_summary(value: Any, *, records: list[Any], integration_summary: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ReviewQueueWriterSchemaAlignmentContractError("writer dry_run_summary must be an object")
    for field in (
        "writer_status",
        "dry_run_only",
        "writer_contract_version",
        "source_adapter_contract_version",
        "run_id",
        "adapter_version",
        "input_file_hashes",
        "dry_run_record_count",
        "readiness_gates",
        "external_call_counts",
        "boundary_flags",
    ):
        if field not in value:
            raise ReviewQueueWriterSchemaAlignmentContractError(f"writer dry_run_summary {field} is required")
    if value["writer_status"] != "ENABLED_TEST_ONLY_DRY_RUN":
        raise ReviewQueueWriterSchemaAlignmentContractError("writer summary must be enabled test-only dry-run")
    if value["dry_run_only"] is not True:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer summary must remain dry_run_only")
    if value["writer_contract_version"] != WRITER_CONTRACT_VERSION:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer contract version mismatch")
    if value["run_id"] != integration_summary["run_id"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer run_id mismatch")
    if value["adapter_version"] != integration_summary["adapter_version"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer adapter_version mismatch")
    if value["input_file_hashes"] != integration_summary["input_file_hashes"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer input_file_hashes mismatch")
    if value["dry_run_record_count"] != len(records):
        raise ReviewQueueWriterSchemaAlignmentContractError("writer dry_run_record_count mismatch")
    if integration_summary["review_queue_dry_run_record_count"] != len(records):
        raise ReviewQueueWriterSchemaAlignmentContractError("integration review_queue_dry_run_record_count mismatch")
    if value["readiness_gates"] != READINESS_GATES_CLOSED:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer readiness gates must remain closed")
    if value["external_call_counts"] != EXTERNAL_CALL_COUNTS_ZERO:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer external call counts must stay zero")
    if not _boundary_flags_are_closed(value["boundary_flags"]):
        raise ReviewQueueWriterSchemaAlignmentContractError("writer boundary flags must remain closed")
    for key in ("clean_data_write_count", "delivery_write_count", "filesystem_write_count", "database_write_count"):
        if value.get(key) != 0:
            raise ReviewQueueWriterSchemaAlignmentContractError(f"writer {key} must remain zero")


def _validate_writer_record(record: Any, *, writer_summary: dict[str, Any], preview_limit: int) -> None:
    if not isinstance(record, dict):
        raise ReviewQueueWriterSchemaAlignmentContractError("writer preview records must be objects")
    missing = [field for field in REQUIRED_WRITER_RECORD_FIELDS if field not in record]
    if missing:
        raise ReviewQueueWriterSchemaAlignmentContractError(f"writer preview record missing required fields: {missing}")
    if record["run_id"] != writer_summary["run_id"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer record run_id mismatch")
    if record["adapter_version"] != writer_summary["adapter_version"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer record adapter_version mismatch")
    if record["input_file_hashes"] != writer_summary["input_file_hashes"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer record input_file_hashes mismatch")
    if record["contract_version"] != writer_summary["writer_contract_version"]:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer record contract_version mismatch")
    if record["dry_run_only"] is not True:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer record must remain dry_run_only")
    if record["agreement_status"] not in REVIEW_BOUND_STATUSES:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer record must remain non-VERIFIED review-bound")
    if record.get("clean_data_write_count") != 0 or record.get("delivery_write_count") != 0:
        raise ReviewQueueWriterSchemaAlignmentContractError("writer record write counts must remain zero")
    for field in ("review_item_id", "audit_hash", "metric_name", "period", "candidate_value", "blocked_delivery_reason"):
        if not _clean(record.get(field)):
            raise ReviewQueueWriterSchemaAlignmentContractError(f"writer record {field} is required")
    if not _is_sha256_hex(record["idempotency_key"]):
        raise ReviewQueueWriterSchemaAlignmentContractError("idempotency_key must be a deterministic sha256 hex digest")
    if not _is_sha256_hex(record["record_payload_hash"]):
        raise ReviewQueueWriterSchemaAlignmentContractError("record_payload_hash must be a deterministic sha256 hex digest")
    if not isinstance(record["source_trace"], dict):
        raise ReviewQueueWriterSchemaAlignmentContractError("source_trace must be an object")
    for field in ("source_document_id", "source_row_id", "matched_locator", "matched_text_sha256"):
        if field not in record["source_trace"]:
            raise ReviewQueueWriterSchemaAlignmentContractError(f"source_trace {field} is required")
    _validate_bounded_preview(record["evidence_preview"], preview_limit)


def _future_review_queue_record_preview(record: dict[str, Any], *, writer_contract_version: str) -> dict[str, Any]:
    source_trace = deepcopy(record["source_trace"])
    return {
        "schema_version": FUTURE_REVIEW_QUEUE_SCHEMA_VERSION,
        "review_item_id": record["review_item_id"],
        "run_id": record["run_id"],
        "source_file_hash": record["source_file_hash"],
        "input_file_hashes": deepcopy(record["input_file_hashes"]),
        "adapter_version": record["adapter_version"],
        "adapter_contract_version": record["adapter_contract_version"],
        "writer_contract_version": writer_contract_version,
        "source_document_id": _clean(source_trace.get("source_document_id")),
        "source_row_id": _clean(source_trace.get("source_row_id")),
        "metric_name": _normalize_text(record["metric_name"]),
        "period": _normalize_text(record["period"]),
        "candidate_value": _clean(record["candidate_value"]),
        "candidate_unit": _clean(record.get("candidate_unit")),
        "normalized_candidate_value": _normalize_candidate_value(record["candidate_value"]),
        "agreement_status": record["agreement_status"],
        "review_status": record["review_status"],
        "reviewer_action": _clean(record.get("reviewer_action")),
        "review_reason": _normalize_text(record["review_reason"]),
        "severity": _severity_from_status(record["agreement_status"]),
        "blocked_delivery_reason": record["blocked_delivery_reason"],
        "re_audit_required": _re_audit_required(record),
        "evidence_preview": record["evidence_preview"],
        "source_trace": source_trace,
        "audit_hash": record["audit_hash"],
        "idempotency_key": record["idempotency_key"],
        "record_payload_hash": record["record_payload_hash"],
        "clean_data_eligible": False,
        "delivery_blocked": True,
    }


def _schema_alignment_summary(
    *,
    config: ReviewQueueWriterSchemaAlignmentContractConfig,
    integration_summary: dict[str, Any],
    writer_summary: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for record in records:
        status_counts[record["agreement_status"]] = status_counts.get(record["agreement_status"], 0) + 1
    summary = {
        "schema_alignment_status": "ENABLED_TEST_ONLY_SCHEMA_ALIGNMENT",
        "enabled": True,
        "dry_run_only": True,
        "schema_alignment_contract_version": config.contract_version,
        "future_review_queue_schema_version": FUTURE_REVIEW_QUEUE_SCHEMA_VERSION,
        "integration_boundary_version": integration_summary["integration_contract_version"],
        "writer_contract_version": writer_summary["writer_contract_version"],
        "source_adapter_contract_version": writer_summary["source_adapter_contract_version"],
        "run_id": integration_summary["run_id"],
        "adapter_version": integration_summary["adapter_version"],
        "input_file_hashes": deepcopy(integration_summary["input_file_hashes"]),
        "future_preview_record_count": len(records),
        "review_bound_record_count": len(records),
        "status_counts": status_counts,
        "re_audit_required_count": writer_summary.get("reaudit_required_count", 0),
        "verified_without_clean_gate_count": writer_summary.get("verified_without_clean_gate_count", 0),
        "clean_data_write_count": 0,
        "delivery_write_count": 0,
        "filesystem_write_count": 0,
        "database_write_count": 0,
        "export_write_count": 0,
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        "external_call_counts": deepcopy(EXTERNAL_CALL_COUNTS_ZERO),
        "boundary_flags": {
            "production_hook": False,
            "writes_review_queue": False,
            "writes_clean_data": False,
            "writes_delivery": False,
            "writes_filesystem": False,
            "writes_database": False,
            "writes_export": False,
            "dry_run_preview_only": True,
            "verified_auto_clean": False,
            "verified_promotes_to_strong_evidence": False,
            "full_source_text_serialized": False,
        },
        "validation_errors": [],
    }
    summary["schema_alignment_preview_hash"] = _hash_json(
        {
            "schema_alignment_contract_version": config.contract_version,
            "future_review_queue_schema_version": FUTURE_REVIEW_QUEUE_SCHEMA_VERSION,
            "run_id": summary["run_id"],
            "records": records,
            "status_counts": status_counts,
        }
    )
    return summary


def _require_exact_fields(value: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ReviewQueueWriterSchemaAlignmentContractError(f"{label} missing required fields: {missing}")
    extra = sorted(set(value) - set(fields))
    if extra:
        raise ReviewQueueWriterSchemaAlignmentContractError(f"{label} has unexpected fields: {extra}")


def _boundary_flags_are_closed(value: Any, *, allow_filesystem_flags_absent: bool = False) -> bool:
    if not isinstance(value, dict):
        return False
    expected_false = (
        "production_hook",
        "writes_review_queue",
        "writes_clean_data",
        "writes_delivery",
        "verified_auto_clean",
        "verified_promotes_to_strong_evidence",
        "full_source_text_serialized",
    )
    if any(value.get(key) is not False for key in expected_false):
        return False
    filesystem_flags = ("writes_filesystem", "writes_database")
    for key in filesystem_flags:
        if key in value:
            if value.get(key) is not False:
                return False
        elif not allow_filesystem_flags_absent:
            return False
    if "writes_export" in value and value.get("writes_export") is not False:
        return False
    if "dry_run_preview_only" in value and value.get("dry_run_preview_only") is not True:
        return False
    return True


def _severity_from_status(status: str) -> str:
    return {
        "DISAGREED": "HIGH",
        "AMBIGUOUS": "MEDIUM_HIGH",
        "MISSING_EVIDENCE": "MEDIUM",
        "PARSE_SKIPPED": "MEDIUM",
        "UNVERIFIED": "MEDIUM",
    }.get(status, "MEDIUM")


def _re_audit_required(record: dict[str, Any]) -> bool:
    return _clean(record.get("review_status")).startswith("RESOLVED_") or _clean(record.get("reviewer_action")).startswith(
        "CORRECT_"
    )


def _normalize_text(value: Any) -> str:
    return " ".join(_clean(value).split())


def _normalize_candidate_value(value: Any) -> str:
    return "".join(char for char in _normalize_text(value) if char != ",")


def _validate_bounded_preview(value: Any, preview_limit: int) -> None:
    if len(_clean(value)) > preview_limit:
        raise ReviewQueueWriterSchemaAlignmentContractError("evidence_preview exceeds preview_limit")


def _is_sha256_hex(value: Any) -> bool:
    text = _clean(value)
    if len(text) != 64:
        return False
    return all(char in "0123456789abcdef" for char in text)


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "FIELD_CLASSIFICATIONS",
    "FUTURE_PERSISTENCE_PREVIEW_FIELDS",
    "FUTURE_REVIEW_QUEUE_SCHEMA_VERSION",
    "SCHEMA_ALIGNMENT_CONTRACT_VERSION",
    "TEST_ONLY_SCHEMA_ALIGNMENT_ENABLE_TOKEN",
    "ReviewQueueWriterSchemaAlignmentContractConfig",
    "ReviewQueueWriterSchemaAlignmentContractError",
    "build_review_queue_writer_schema_alignment_preview",
    "field_classifications",
    "validate_dry_run_integration_output",
    "validate_no_forbidden_fields",
]
