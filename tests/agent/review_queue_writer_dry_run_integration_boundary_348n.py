"""Test-only dry-run integration boundary for R7BE.

This helper intentionally lives under tests, performs no I/O, and has no
production hook. It accepts already-validated adapter candidate output, calls
only the R7BC in-memory writer contract, and returns a deterministic dry-run
preview envelope.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from tests.agent.review_queue_writer_contract_348n import (
    DEFAULT_PREVIEW_LIMIT,
    TEST_ONLY_WRITER_ENABLE_TOKEN,
    WRITER_CONTRACT_VERSION,
    ReviewQueueWriterContractConfig,
    ReviewQueueWriterContractError,
    build_review_queue_writer_dry_run_preview,
    validate_adapter_candidate_output,
    validate_no_forbidden_fields,
)

INTEGRATION_BOUNDARY_CONTRACT_VERSION = "r7be_writer_dry_run_integration_boundary_test_only_v1"
TEST_ONLY_INTEGRATION_ENABLE_TOKEN = "R7BE_TEST_ONLY_INTEGRATION_ENABLE"


@dataclass(frozen=True, slots=True)
class ReviewQueueWriterDryRunIntegrationBoundaryConfig:
    """Explicit test-only feature flag for the R7BE integration boundary."""

    enabled: bool = False
    contract_version: str = INTEGRATION_BOUNDARY_CONTRACT_VERSION
    test_only_enable_token: str = ""


class ReviewQueueWriterDryRunIntegrationBoundaryError(ValueError):
    """Raised when the test-only integration boundary fails closed."""


def build_review_queue_writer_dry_run_integration_preview(
    adapter_candidate_output: dict[str, Any],
    config: ReviewQueueWriterDryRunIntegrationBoundaryConfig | None = None,
    *,
    existing_record_hashes: dict[str, str] | None = None,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> dict[str, Any]:
    """Return a deterministic in-memory adapter-to-writer dry-run preview."""

    integration_config = config or ReviewQueueWriterDryRunIntegrationBoundaryConfig()
    _validate_config(integration_config)
    if not integration_config.enabled:
        return _disabled_result(integration_config)
    if integration_config.test_only_enable_token != TEST_ONLY_INTEGRATION_ENABLE_TOKEN:
        raise ReviewQueueWriterDryRunIntegrationBoundaryError(
            "explicit R7BE test-only integration enable token is required"
        )

    _validate_adapter_candidate_before_writer_call(adapter_candidate_output, preview_limit=preview_limit)
    adapter_payload = deepcopy(adapter_candidate_output)
    audit_contract = deepcopy(adapter_payload["audit_contract"])
    writer_config = ReviewQueueWriterContractConfig(
        enabled=True,
        contract_version=WRITER_CONTRACT_VERSION,
        test_only_enable_token=TEST_ONLY_WRITER_ENABLE_TOKEN,
    )
    try:
        writer_preview = build_review_queue_writer_dry_run_preview(
            adapter_payload,
            writer_config,
            existing_record_hashes=existing_record_hashes,
            preview_limit=preview_limit,
        )
    except ReviewQueueWriterContractError as exc:
        raise ReviewQueueWriterDryRunIntegrationBoundaryError(
            f"writer dry-run contract rejected adapter candidate output: {exc}"
        ) from exc

    output = _enabled_result(
        integration_config=integration_config,
        audit_contract=audit_contract,
        writer_preview=writer_preview,
    )
    _validate_enabled_output(output, preview_limit=preview_limit)
    return deepcopy(output)


def _validate_adapter_candidate_before_writer_call(value: Any, *, preview_limit: int) -> None:
    try:
        validate_adapter_candidate_output(value, preview_limit=preview_limit)
    except ReviewQueueWriterContractError as exc:
        raise ReviewQueueWriterDryRunIntegrationBoundaryError(
            f"invalid adapter candidate output before writer call: {exc}"
        ) from exc


def _validate_config(config: ReviewQueueWriterDryRunIntegrationBoundaryConfig) -> None:
    if config.contract_version != INTEGRATION_BOUNDARY_CONTRACT_VERSION:
        raise ReviewQueueWriterDryRunIntegrationBoundaryError("unexpected integration boundary contract_version")


def _disabled_result(config: ReviewQueueWriterDryRunIntegrationBoundaryConfig) -> dict[str, Any]:
    return {
        "integration_status": "DISABLED",
        "dry_run_only": True,
        "integration_contract_version": config.contract_version,
        "writer_dry_run_preview": None,
        "integration_summary": {
            "integration_status": "DISABLED",
            "enabled": False,
            "reason": "disabled_by_default",
            "dry_run_only": True,
            "dry_run_preview_only": True,
            "writer_called": False,
            "review_queue_dry_run_record_count": 0,
            "clean_data_write_count": 0,
            "delivery_write_count": 0,
            "filesystem_write_count": 0,
            "database_write_count": 0,
            "export_write_count": 0,
            "readiness_gates": {
                "client_ready": False,
                "production_ready": False,
                "formal_client_export_allowed": False,
                "demo_export_only": True,
            },
            "external_call_counts": {
                "mineru_run_count": 0,
                "ocr_run_count": 0,
                "llm_api_call_count": 0,
                "vlm_api_call_count": 0,
            },
            "boundary_flags": _closed_boundary_flags(),
        },
    }


def _enabled_result(
    *,
    integration_config: ReviewQueueWriterDryRunIntegrationBoundaryConfig,
    audit_contract: dict[str, Any],
    writer_preview: dict[str, Any],
) -> dict[str, Any]:
    writer_summary = deepcopy(writer_preview["dry_run_summary"])
    envelope_metadata = {
        "integration_status": "ENABLED_TEST_ONLY_DRY_RUN",
        "dry_run_only": True,
        "integration_contract_version": integration_config.contract_version,
        "writer_contract_version": writer_summary["writer_contract_version"],
        "source_adapter_contract_version": audit_contract["contract_version"],
        "run_id": audit_contract["run_id"],
        "adapter_version": audit_contract["adapter_version"],
        "input_file_hashes": deepcopy(audit_contract["input_file_hashes"]),
        "adapter_audit_hash": audit_contract["adapter_audit_hash"],
        "review_queue_dry_run_record_count": len(writer_preview["review_queue_dry_run_records"]),
        "writer_preview_hash": _hash_json(writer_preview),
    }
    integration_summary = {
        **envelope_metadata,
        "enabled": True,
        "writer_called": True,
        "dry_run_preview_only": True,
        "would_insert_count": writer_summary["would_insert_count"],
        "duplicate_plan_count": writer_summary["duplicate_plan_count"],
        "conflict_count": writer_summary["conflict_count"],
        "rejected_count": writer_summary["rejected_count"],
        "clean_data_write_count": writer_summary["clean_data_write_count"],
        "delivery_write_count": writer_summary["delivery_write_count"],
        "filesystem_write_count": writer_summary["filesystem_write_count"],
        "database_write_count": writer_summary["database_write_count"],
        "export_write_count": 0,
        "blocked_delivery_count": writer_summary["blocked_delivery_count"],
        "reaudit_required_count": writer_summary["reaudit_required_count"],
        "verified_without_clean_gate_count": writer_summary["verified_without_clean_gate_count"],
        "status_counts": deepcopy(writer_summary["status_counts"]),
        "readiness_gates": deepcopy(writer_summary["readiness_gates"]),
        "external_call_counts": deepcopy(writer_summary["external_call_counts"]),
        "boundary_flags": _closed_boundary_flags(),
    }
    integration_summary["integration_envelope_hash"] = _hash_json(envelope_metadata)
    return {
        "integration_status": "ENABLED_TEST_ONLY_DRY_RUN",
        "dry_run_only": True,
        "integration_contract_version": integration_config.contract_version,
        "adapter_audit_contract": audit_contract,
        "writer_dry_run_preview": deepcopy(writer_preview),
        "integration_summary": integration_summary,
    }


def _validate_enabled_output(value: dict[str, Any], *, preview_limit: int) -> None:
    validate_no_forbidden_fields(value, preview_limit=preview_limit)
    summary = value["integration_summary"]
    if value["dry_run_only"] is not True or summary["dry_run_only"] is not True:
        raise ReviewQueueWriterDryRunIntegrationBoundaryError("integration output must remain dry-run only")
    if summary["readiness_gates"] != {
        "client_ready": False,
        "production_ready": False,
        "formal_client_export_allowed": False,
        "demo_export_only": True,
    }:
        raise ReviewQueueWriterDryRunIntegrationBoundaryError("readiness gates must remain closed")
    for key in ("clean_data_write_count", "delivery_write_count", "filesystem_write_count", "database_write_count", "export_write_count"):
        if summary[key] != 0:
            raise ReviewQueueWriterDryRunIntegrationBoundaryError(f"{key} must remain zero")
    if summary["boundary_flags"] != _closed_boundary_flags():
        raise ReviewQueueWriterDryRunIntegrationBoundaryError("integration boundary flags must remain closed")


def _closed_boundary_flags() -> dict[str, bool]:
    return {
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
    }


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
