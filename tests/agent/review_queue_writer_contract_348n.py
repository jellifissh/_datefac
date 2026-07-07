"""Test-only review_queue writer contract prototype for R7BC.

This module intentionally performs no I/O and has no production hook. It
validates adapter candidate output and returns an in-memory dry-run preview of
review_queue records that a future persistence layer could write.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from datefac_agent.review.production_boundary_review_queue_adapter import (
    ADAPTER_CONTRACT_VERSION,
    EXTERNAL_CALL_COUNTS_ZERO,
    FORBIDDEN_KEYS,
    READINESS_GATES_CLOSED,
)

WRITER_CONTRACT_VERSION = "r7bc_review_queue_writer_contract_test_only_v1"
TEST_ONLY_WRITER_ENABLE_TOKEN = "R7BC_TEST_ONLY_WRITER_ENABLE"
DEFAULT_PREVIEW_LIMIT = 160

REVIEW_QUEUE_STATUSES: tuple[str, ...] = (
    "UNVERIFIED",
    "DISAGREED",
    "AMBIGUOUS",
    "MISSING_EVIDENCE",
    "PARSE_SKIPPED",
)

REQUIRED_ADAPTER_OUTPUT_FIELDS: tuple[str, ...] = (
    "adapter_status",
    "review_queue_candidate_items",
    "discrepancy_report_candidate_rows",
    "blocked_delivery_candidate_rows",
    "delivery_reaudit_candidate_rows",
    "audit_contract",
)

REQUIRED_AUDIT_CONTRACT_FIELDS: tuple[str, ...] = (
    "adapter_status",
    "enabled",
    "contract_version",
    "created_from",
    "run_id",
    "adapter_version",
    "input_file_hashes",
    "review_queue_candidate_count",
    "review_queue_candidate_status_counts",
    "discrepancy_report_candidate_count",
    "blocked_delivery_candidate_count",
    "delivery_reaudit_candidate_count",
    "verified_without_clean_gate_count",
    "clean_data_admitted_count",
    "readiness_gates",
    "external_call_counts",
    "boundary_flags",
    "adapter_audit_hash",
)

REQUIRED_REVIEW_CANDIDATE_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "source_document_id",
    "source_row_id",
    "candidate_metric_name",
    "candidate_period",
    "candidate_value",
    "candidate_unit",
    "agreement_status",
    "subqueue",
    "risk_reason",
    "severity",
    "review_status",
    "reviewer_action",
    "clean_data_eligible",
    "delivery_blocked",
    "evidence_preview",
    "evidence_preview_sha256",
    "matched_locator",
    "matched_text_sha256",
    "run_id",
    "adapter_version",
    "input_file_hashes",
    "audit_hash",
    "adapter_contract_version",
)

REQUIRED_BLOCKED_DELIVERY_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "source_row_id",
    "agreement_status",
    "blocked_reason",
    "delivery_blocked",
    "run_id",
    "adapter_version",
    "adapter_contract_version",
)

REQUIRED_DELIVERY_REAUDIT_FIELDS: tuple[str, ...] = (
    "source_row_id",
    "agreement_status",
    "delivery_gate_status",
    "delivery_clean_admitted",
    "requires_reaudit_before_clean_delivery",
    "run_id",
    "adapter_version",
    "adapter_contract_version",
)

REQUIRED_DRY_RUN_RECORD_FIELDS: tuple[str, ...] = (
    "review_item_id",
    "run_id",
    "source_file_hash",
    "input_file_hashes",
    "adapter_version",
    "contract_version",
    "audit_hash",
    "metric_name",
    "period",
    "candidate_value",
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


@dataclass(frozen=True, slots=True)
class ReviewQueueWriterContractConfig:
    """Explicit test-only feature flag for the in-memory R7BC writer."""

    enabled: bool = False
    contract_version: str = WRITER_CONTRACT_VERSION
    test_only_enable_token: str = ""


class ReviewQueueWriterContractError(ValueError):
    """Raised when the test-only writer contract fails closed."""


def build_review_queue_writer_dry_run_preview(
    adapter_candidate_output: dict[str, Any],
    config: ReviewQueueWriterContractConfig | None = None,
    *,
    existing_record_hashes: dict[str, str] | None = None,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> dict[str, Any]:
    """Return an in-memory dry-run preview of future review_queue records."""

    writer_config = config or ReviewQueueWriterContractConfig()
    _validate_config(writer_config)
    if not writer_config.enabled:
        return _disabled_result(writer_config)
    if writer_config.test_only_enable_token != TEST_ONLY_WRITER_ENABLE_TOKEN:
        raise ReviewQueueWriterContractError("explicit R7BC test-only writer enable token is required")

    validate_adapter_candidate_output(adapter_candidate_output, preview_limit=preview_limit)
    existing_hashes = _validate_existing_record_hashes(existing_record_hashes)
    payload = deepcopy(adapter_candidate_output)
    audit_contract = payload["audit_contract"]
    blocked_reasons = {
        _clean(row.get("review_item_id")): _clean(row.get("blocked_reason"))
        for row in payload["blocked_delivery_candidate_rows"]
    }

    dry_run_records: list[dict[str, Any]] = []
    seen_idempotency_keys: set[str] = set()
    duplicate_plan_count = 0
    for item in payload["review_queue_candidate_items"]:
        record = _dry_run_record(
            item,
            audit_contract=audit_contract,
            blocked_delivery_reason=blocked_reasons.get(item["review_item_id"], _default_blocked_reason(item)),
            writer_contract_version=writer_config.contract_version,
        )
        idempotency_key = record["idempotency_key"]
        if idempotency_key in seen_idempotency_keys:
            raise ReviewQueueWriterContractError("duplicate idempotency_key within dry-run batch")
        seen_idempotency_keys.add(idempotency_key)

        record_payload_hash = _hash_record_payload(record)
        existing_hash = existing_hashes.get(idempotency_key)
        if existing_hash is None:
            dry_run_action = "WOULD_INSERT"
        elif existing_hash == record_payload_hash:
            dry_run_action = "WOULD_SKIP_DUPLICATE"
            duplicate_plan_count += 1
        else:
            raise ReviewQueueWriterContractError("idempotency collision with different payload hash")

        record["dry_run_action"] = dry_run_action
        record["record_payload_hash"] = record_payload_hash
        dry_run_records.append(record)

    summary = {
        "writer_status": "ENABLED_TEST_ONLY_DRY_RUN",
        "dry_run_only": True,
        "writer_contract_version": writer_config.contract_version,
        "source_adapter_contract_version": audit_contract["contract_version"],
        "run_id": audit_contract["run_id"],
        "adapter_version": audit_contract["adapter_version"],
        "input_file_hashes": dict(audit_contract["input_file_hashes"]),
        "candidate_count": audit_contract["review_queue_candidate_count"],
        "dry_run_record_count": len(dry_run_records),
        "would_insert_count": sum(record["dry_run_action"] == "WOULD_INSERT" for record in dry_run_records),
        "duplicate_plan_count": duplicate_plan_count,
        "conflict_count": 0,
        "rejected_count": 0,
        "clean_data_write_count": 0,
        "delivery_write_count": 0,
        "filesystem_write_count": 0,
        "database_write_count": 0,
        "blocked_delivery_count": len(payload["blocked_delivery_candidate_rows"]),
        "reaudit_required_count": _reaudit_required_count(payload["delivery_reaudit_candidate_rows"]),
        "verified_without_clean_gate_count": audit_contract["verified_without_clean_gate_count"],
        "status_counts": dict(Counter(record["agreement_status"] for record in dry_run_records)),
        "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
        "external_call_counts": deepcopy(EXTERNAL_CALL_COUNTS_ZERO),
        "boundary_flags": {
            "production_hook": False,
            "writes_review_queue": False,
            "writes_clean_data": False,
            "writes_delivery": False,
            "writes_filesystem": False,
            "writes_database": False,
            "dry_run_preview_only": True,
            "verified_auto_clean": False,
            "verified_promotes_to_strong_evidence": False,
            "full_source_text_serialized": False,
        },
    }
    output = {
        "writer_status": "ENABLED_TEST_ONLY_DRY_RUN",
        "dry_run_only": True,
        "review_queue_dry_run_records": dry_run_records,
        "dry_run_summary": summary,
    }
    validate_no_forbidden_fields(output, preview_limit=preview_limit)
    return deepcopy(output)


def validate_adapter_candidate_output(value: Any, *, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> None:
    """Validate the only accepted input shape for the test-only writer."""

    if not isinstance(value, dict):
        raise ReviewQueueWriterContractError("adapter candidate output must be an object")
    validate_no_forbidden_fields(value, preview_limit=preview_limit)
    missing = [field for field in REQUIRED_ADAPTER_OUTPUT_FIELDS if field not in value]
    if missing:
        raise ReviewQueueWriterContractError(f"adapter candidate output missing required fields: {missing}")
    extra = sorted(set(value) - set(REQUIRED_ADAPTER_OUTPUT_FIELDS))
    if extra:
        raise ReviewQueueWriterContractError(f"adapter candidate output has unexpected fields: {extra}")
    if value["adapter_status"] != "ENABLED_TEST_ONLY":
        raise ReviewQueueWriterContractError("adapter candidate output must come from enabled test-only adapter output")
    for field in (
        "review_queue_candidate_items",
        "discrepancy_report_candidate_rows",
        "blocked_delivery_candidate_rows",
        "delivery_reaudit_candidate_rows",
    ):
        if not isinstance(value[field], list):
            raise ReviewQueueWriterContractError(f"{field} must be a list")

    audit_contract = value["audit_contract"]
    _validate_audit_contract(
        audit_contract,
        review_queue_candidate_count=len(value["review_queue_candidate_items"]),
        discrepancy_report_candidate_count=len(value["discrepancy_report_candidate_rows"]),
        blocked_delivery_candidate_count=len(value["blocked_delivery_candidate_rows"]),
        delivery_reaudit_candidate_count=len(value["delivery_reaudit_candidate_rows"]),
    )
    for item in value["review_queue_candidate_items"]:
        _validate_review_candidate(item, audit_contract=audit_contract, preview_limit=preview_limit)
    status_counts = Counter(item["agreement_status"] for item in value["review_queue_candidate_items"])
    if audit_contract.get("review_queue_candidate_status_counts") != dict(status_counts):
        raise ReviewQueueWriterContractError("review_queue_candidate_status_counts mismatch")
    for row in value["blocked_delivery_candidate_rows"]:
        _validate_blocked_delivery_candidate(row, audit_contract=audit_contract)
    for row in value["delivery_reaudit_candidate_rows"]:
        _validate_delivery_reaudit_candidate(row, audit_contract=audit_contract)


def validate_no_forbidden_fields(value: Any, *, preview_limit: int = DEFAULT_PREVIEW_LIMIT, path: str = "$") -> None:
    """Reject raw artifacts, full text, readiness, clean, and delivery writes."""

    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                raise ReviewQueueWriterContractError(f"forbidden field at {path}.{key}: {key}")
            if key == "evidence_level" and _clean(child) == "STRONG_EVIDENCE":
                raise ReviewQueueWriterContractError("STRONG_EVIDENCE promotion is forbidden")
            if key in {"client_ready", "production_ready", "formal_client_export_allowed"} and child is True:
                raise ReviewQueueWriterContractError(f"readiness gate opened at {path}.{key}")
            if key in {"clean_data_eligible", "clean_data_admitted", "delivery_clean_admitted"} and child is True:
                raise ReviewQueueWriterContractError("clean_data or delivery write intent is forbidden")
            if key in {"writes_review_queue", "writes_clean_data", "writes_delivery", "writes_filesystem", "writes_database"}:
                if child is True:
                    raise ReviewQueueWriterContractError(f"write intent is forbidden at {path}.{key}")
            if key == "production_hook" and child is True:
                raise ReviewQueueWriterContractError("production hooks are forbidden")
            if key == "evidence_preview":
                _validate_bounded_preview(child, preview_limit)
            validate_no_forbidden_fields(child, preview_limit=preview_limit, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_no_forbidden_fields(child, preview_limit=preview_limit, path=f"{path}[{index}]")


def _validate_config(config: ReviewQueueWriterContractConfig) -> None:
    if config.contract_version != WRITER_CONTRACT_VERSION:
        raise ReviewQueueWriterContractError("unexpected writer contract_version")


def _disabled_result(config: ReviewQueueWriterContractConfig) -> dict[str, Any]:
    return {
        "writer_status": "DISABLED",
        "dry_run_only": True,
        "review_queue_dry_run_records": [],
        "dry_run_summary": {
            "writer_status": "DISABLED",
            "enabled": False,
            "writer_contract_version": config.contract_version,
            "reason": "disabled_by_default",
            "candidate_count": 0,
            "dry_run_record_count": 0,
            "would_insert_count": 0,
            "duplicate_plan_count": 0,
            "conflict_count": 0,
            "rejected_count": 0,
            "clean_data_write_count": 0,
            "delivery_write_count": 0,
            "filesystem_write_count": 0,
            "database_write_count": 0,
            "readiness_gates": deepcopy(READINESS_GATES_CLOSED),
            "external_call_counts": deepcopy(EXTERNAL_CALL_COUNTS_ZERO),
            "boundary_flags": {
                "production_hook": False,
                "writes_review_queue": False,
                "writes_clean_data": False,
                "writes_delivery": False,
                "writes_filesystem": False,
                "writes_database": False,
                "dry_run_preview_only": True,
                "verified_auto_clean": False,
                "verified_promotes_to_strong_evidence": False,
                "full_source_text_serialized": False,
            },
        },
    }


def _validate_audit_contract(
    audit_contract: Any,
    *,
    review_queue_candidate_count: int,
    discrepancy_report_candidate_count: int,
    blocked_delivery_candidate_count: int,
    delivery_reaudit_candidate_count: int,
) -> None:
    if not isinstance(audit_contract, dict):
        raise ReviewQueueWriterContractError("audit_contract must be an object")
    missing = [field for field in REQUIRED_AUDIT_CONTRACT_FIELDS if field not in audit_contract]
    if missing:
        raise ReviewQueueWriterContractError(f"audit_contract missing required fields: {missing}")
    if audit_contract["adapter_status"] != "ENABLED_TEST_ONLY" or audit_contract.get("enabled") is not True:
        raise ReviewQueueWriterContractError("audit_contract must be enabled test-only adapter output")
    if audit_contract["contract_version"] != ADAPTER_CONTRACT_VERSION:
        raise ReviewQueueWriterContractError("unexpected adapter contract_version")
    if not _clean(audit_contract.get("run_id")):
        raise ReviewQueueWriterContractError("run_id is required")
    if not _clean(audit_contract.get("adapter_version")):
        raise ReviewQueueWriterContractError("adapter_version is required")
    input_file_hashes = audit_contract.get("input_file_hashes")
    if not isinstance(input_file_hashes, dict) or not input_file_hashes:
        raise ReviewQueueWriterContractError("input_file_hashes must be a non-empty object")
    if not all(_clean(key) and _clean(value) for key, value in input_file_hashes.items()):
        raise ReviewQueueWriterContractError("input_file_hashes must contain non-empty keys and values")
    if audit_contract.get("readiness_gates") != READINESS_GATES_CLOSED:
        raise ReviewQueueWriterContractError("readiness gates must remain closed")
    if audit_contract.get("external_call_counts") != EXTERNAL_CALL_COUNTS_ZERO:
        raise ReviewQueueWriterContractError("external call counts must stay zero")
    if audit_contract.get("review_queue_candidate_count") != review_queue_candidate_count:
        raise ReviewQueueWriterContractError("review_queue_candidate_count mismatch")
    if audit_contract.get("discrepancy_report_candidate_count") != discrepancy_report_candidate_count:
        raise ReviewQueueWriterContractError("discrepancy_report_candidate_count mismatch")
    if audit_contract.get("blocked_delivery_candidate_count") != blocked_delivery_candidate_count:
        raise ReviewQueueWriterContractError("blocked_delivery_candidate_count mismatch")
    if audit_contract.get("delivery_reaudit_candidate_count") != delivery_reaudit_candidate_count:
        raise ReviewQueueWriterContractError("delivery_reaudit_candidate_count mismatch")
    if audit_contract.get("clean_data_admitted_count") != 0:
        raise ReviewQueueWriterContractError("clean_data_admitted_count must remain zero")
    boundary_flags = audit_contract.get("boundary_flags")
    if not isinstance(boundary_flags, dict):
        raise ReviewQueueWriterContractError("boundary_flags must be an object")
    for key in (
        "production_hook",
        "writes_review_queue",
        "writes_clean_data",
        "writes_delivery",
        "verified_auto_clean",
        "verified_promotes_to_strong_evidence",
        "full_source_text_serialized",
    ):
        if boundary_flags.get(key) is True:
            raise ReviewQueueWriterContractError(f"{key} is forbidden")


def _validate_review_candidate(item: Any, *, audit_contract: dict[str, Any], preview_limit: int) -> None:
    if not isinstance(item, dict):
        raise ReviewQueueWriterContractError("review_queue_candidate_items must contain objects")
    missing = [field for field in REQUIRED_REVIEW_CANDIDATE_FIELDS if field not in item]
    if missing:
        raise ReviewQueueWriterContractError(f"review candidate missing required fields: {missing}")
    for field in ("review_item_id", "source_row_id", "candidate_metric_name", "candidate_period", "candidate_value", "audit_hash"):
        if not _clean(item.get(field)):
            raise ReviewQueueWriterContractError(f"review candidate {field} is required")
    if item["agreement_status"] not in REVIEW_QUEUE_STATUSES:
        raise ReviewQueueWriterContractError("review_queue candidates must be non-VERIFIED review-bound statuses")
    if item["run_id"] != audit_contract["run_id"]:
        raise ReviewQueueWriterContractError("review candidate run_id mismatch")
    if item["adapter_version"] != audit_contract["adapter_version"]:
        raise ReviewQueueWriterContractError("review candidate adapter_version mismatch")
    if item["input_file_hashes"] != audit_contract["input_file_hashes"]:
        raise ReviewQueueWriterContractError("review candidate input_file_hashes mismatch")
    if item["adapter_contract_version"] != audit_contract["contract_version"]:
        raise ReviewQueueWriterContractError("review candidate adapter_contract_version mismatch")
    if item.get("clean_data_eligible") is not False:
        raise ReviewQueueWriterContractError("review candidate clean_data_eligible must remain false")
    if item.get("delivery_blocked") is not True:
        raise ReviewQueueWriterContractError("review candidate delivery_blocked must remain true")
    if not _clean(item.get("evidence_preview")):
        raise ReviewQueueWriterContractError("evidence_preview is required")
    _validate_bounded_preview(item["evidence_preview"], preview_limit)


def _validate_blocked_delivery_candidate(row: Any, *, audit_contract: dict[str, Any]) -> None:
    if not isinstance(row, dict):
        raise ReviewQueueWriterContractError("blocked_delivery_candidate_rows must contain objects")
    missing = [field for field in REQUIRED_BLOCKED_DELIVERY_FIELDS if field not in row]
    if missing:
        raise ReviewQueueWriterContractError(f"blocked delivery row missing required fields: {missing}")
    if row["agreement_status"] not in REVIEW_QUEUE_STATUSES:
        raise ReviewQueueWriterContractError("blocked delivery rows must be review-bound statuses")
    if row.get("delivery_blocked") is not True:
        raise ReviewQueueWriterContractError("blocked delivery rows must stay blocked")
    if row["run_id"] != audit_contract["run_id"] or row["adapter_version"] != audit_contract["adapter_version"]:
        raise ReviewQueueWriterContractError("blocked delivery row metadata mismatch")
    if row["adapter_contract_version"] != audit_contract["contract_version"]:
        raise ReviewQueueWriterContractError("blocked delivery row adapter_contract_version mismatch")


def _validate_delivery_reaudit_candidate(row: Any, *, audit_contract: dict[str, Any]) -> None:
    if not isinstance(row, dict):
        raise ReviewQueueWriterContractError("delivery_reaudit_candidate_rows must contain objects")
    missing = [field for field in REQUIRED_DELIVERY_REAUDIT_FIELDS if field not in row]
    if missing:
        raise ReviewQueueWriterContractError(f"delivery re-audit row missing required fields: {missing}")
    if row.get("delivery_clean_admitted") is not False:
        raise ReviewQueueWriterContractError("delivery_clean_admitted must remain false")
    if row.get("requires_reaudit_before_clean_delivery") is not True:
        raise ReviewQueueWriterContractError("delivery re-audit rows must require re-audit")
    if row["run_id"] != audit_contract["run_id"] or row["adapter_version"] != audit_contract["adapter_version"]:
        raise ReviewQueueWriterContractError("delivery re-audit row metadata mismatch")
    if row["adapter_contract_version"] != audit_contract["contract_version"]:
        raise ReviewQueueWriterContractError("delivery re-audit row adapter_contract_version mismatch")


def _dry_run_record(
    item: dict[str, Any],
    *,
    audit_contract: dict[str, Any],
    blocked_delivery_reason: str,
    writer_contract_version: str,
) -> dict[str, Any]:
    input_file_hashes = dict(audit_contract["input_file_hashes"])
    source_trace = {
        "source_document_id": item["source_document_id"],
        "source_row_id": item["source_row_id"],
        "adapter_item_id": item.get("adapter_item_id", ""),
        "matched_locator": item.get("matched_locator", ""),
        "matched_text_sha256": item.get("matched_text_sha256", ""),
        "subqueue": item.get("subqueue", ""),
        "evidence_preview_sha256": item.get("evidence_preview_sha256", ""),
    }
    record = {
        "review_item_id": item["review_item_id"],
        "run_id": audit_contract["run_id"],
        "source_file_hash": _source_file_hash(input_file_hashes),
        "input_file_hashes": input_file_hashes,
        "adapter_version": audit_contract["adapter_version"],
        "contract_version": writer_contract_version,
        "adapter_contract_version": audit_contract["contract_version"],
        "audit_hash": item["audit_hash"],
        "metric_name": item["candidate_metric_name"],
        "period": item["candidate_period"],
        "candidate_value": item["candidate_value"],
        "candidate_unit": item["candidate_unit"],
        "agreement_status": item["agreement_status"],
        "review_status": item["review_status"],
        "reviewer_action": item["reviewer_action"],
        "review_reason": item["risk_reason"],
        "blocked_delivery_reason": blocked_delivery_reason,
        "evidence_preview": item["evidence_preview"],
        "source_trace": source_trace,
        "idempotency_key": _idempotency_key(item, audit_contract=audit_contract, writer_contract_version=writer_contract_version),
        "dry_run_only": True,
        "clean_data_write_count": 0,
        "delivery_write_count": 0,
    }
    return record


def _idempotency_key(
    item: dict[str, Any],
    *,
    audit_contract: dict[str, Any],
    writer_contract_version: str,
) -> str:
    payload = {
        "contract_version": writer_contract_version,
        "run_id": audit_contract["run_id"],
        "review_item_id": item["review_item_id"],
        "source_row_id": item["source_row_id"],
        "agreement_status": item["agreement_status"],
        "audit_hash": item["audit_hash"],
        "input_file_hashes": dict(sorted(audit_contract["input_file_hashes"].items())),
    }
    return _hash_json(payload)


def _hash_record_payload(record: dict[str, Any]) -> str:
    payload = {
        key: value
        for key, value in record.items()
        if key not in {"dry_run_action", "record_payload_hash"}
    }
    return _hash_json(payload)


def _source_file_hash(input_file_hashes: dict[str, str]) -> str:
    for key in ("source_file", "source_pdf", "mineru_content_list_v2", "datefac_excel"):
        if key in input_file_hashes:
            return input_file_hashes[key]
    first_key = sorted(input_file_hashes)[0]
    return input_file_hashes[first_key]


def _default_blocked_reason(item: dict[str, Any]) -> str:
    status = item["agreement_status"]
    return {
        "DISAGREED": "EVIDENCE_DISAGREEMENT_UNRESOLVED",
        "AMBIGUOUS": "EVIDENCE_AMBIGUITY_UNRESOLVED",
        "MISSING_EVIDENCE": "EVIDENCE_MISSING_UNRESOLVED",
        "PARSE_SKIPPED": "PARSE_SKIPPED_REVIEW_REQUIRED",
        "UNVERIFIED": "UNVERIFIED_REVIEW_REQUIRED",
    }.get(status, "REVIEW_REQUIRED")


def _reaudit_required_count(rows: list[dict[str, Any]]) -> int:
    return sum(row.get("requires_reaudit_before_clean_delivery") is True for row in rows)


def _validate_existing_record_hashes(value: dict[str, str] | None) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ReviewQueueWriterContractError("existing_record_hashes must be an object")
    for key, record_hash in value.items():
        if not _clean(key) or not _clean(record_hash):
            raise ReviewQueueWriterContractError("existing_record_hashes must contain non-empty keys and values")
    return dict(value)


def _validate_bounded_preview(value: Any, preview_limit: int) -> None:
    if len(_clean(value)) > preview_limit:
        raise ReviewQueueWriterContractError("evidence_preview exceeds preview_limit")


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "DEFAULT_PREVIEW_LIMIT",
    "REQUIRED_DRY_RUN_RECORD_FIELDS",
    "TEST_ONLY_WRITER_ENABLE_TOKEN",
    "WRITER_CONTRACT_VERSION",
    "ReviewQueueWriterContractConfig",
    "ReviewQueueWriterContractError",
    "build_review_queue_writer_dry_run_preview",
    "validate_adapter_candidate_output",
    "validate_no_forbidden_fields",
]
