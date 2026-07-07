"""Test-only production-boundary review queue adapter contract prototype for R7AU."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from tests.agent.discrepancy_review_queue_integration_boundary_348n import (
    EXTERNAL_CALL_COUNTS_ZERO,
    READINESS_GATES_CLOSED,
    load_integration_boundary_fixture,
    run_discrepancy_review_integration_boundary,
)
from tests.agent.discrepancy_review_queue_policy_348n import REVIEWER_ACTIONS, REVIEW_QUEUE_STATUSES

CONTRACT_VERSION = "r7au_production_boundary_review_queue_contract_test_only_v1"
CREATED_FROM = "r7as_discrepancy_boundary_output"
DEFAULT_PREVIEW_LIMIT = 160

REQUIRED_BOUNDARY_OUTPUT_FIELDS: tuple[str, ...] = (
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
    "review_queue_count",
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

CONTRACT_ITEM_FIELDS: tuple[str, ...] = (
    "contract_item_id",
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
    "matched_locator",
    "run_id",
    "adapter_version",
    "input_file_hashes",
    "audit_hash",
    "contract_version",
    "created_from",
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
    }
)


class ProductionBoundaryContractError(ValueError):
    """Raised when the R7AU test-only production boundary contract fails closed."""


def load_contract_fixture(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProductionBoundaryContractError("contract fixture must be a JSON object")
    if payload.get("fixture_scope") != "test_only_r7au":
        raise ProductionBoundaryContractError("fixture_scope must be test_only_r7au")
    if not isinstance(payload.get("valid_comparison_boundary_payload"), dict):
        raise ProductionBoundaryContractError("valid_comparison_boundary_payload must be an object")
    if not isinstance(payload.get("invalid_inputs"), list):
        raise ProductionBoundaryContractError("invalid_inputs must be a list")
    return payload


def build_boundary_output_from_fixture(payload: dict[str, Any], *, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> dict[str, Any]:
    comparison_payload = deepcopy(payload["valid_comparison_boundary_payload"])
    validate_no_forbidden_fields(comparison_payload, allow_comparison_input=True)
    return run_discrepancy_review_integration_boundary(comparison_payload, preview_limit=preview_limit)


def load_boundary_output_from_comparison_fixture(
    path: str | Path,
    *,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
) -> dict[str, Any]:
    comparison_payload = load_integration_boundary_fixture(path)
    validate_no_forbidden_fields(comparison_payload, allow_comparison_input=True)
    return run_discrepancy_review_integration_boundary(comparison_payload, preview_limit=preview_limit)


def build_production_boundary_review_queue_contract(
    boundary_output: dict[str, Any],
    *,
    preview_limit: int = DEFAULT_PREVIEW_LIMIT,
    explicit_future_policy_gate: bool = False,
) -> dict[str, Any]:
    validate_boundary_output_shape(boundary_output, preview_limit=preview_limit)

    audit_metadata = boundary_output["audit_metadata"]
    run_id = _clean(audit_metadata["run_id"])
    adapter_version = _clean(audit_metadata["adapter_version"])
    input_file_hashes = dict(audit_metadata["input_file_hashes"])
    blocked_review_item_ids = {
        _clean(row.get("review_item_id")) for row in boundary_output["blocked_delivery_rows"]
    }

    review_queue_contract_items = [
        _contract_item_from_review_item(
            item,
            blocked_review_item_ids=blocked_review_item_ids,
            explicit_future_policy_gate=explicit_future_policy_gate,
            preview_limit=preview_limit,
        )
        for item in boundary_output["review_queue_items"]
    ]
    discrepancy_report_contract_rows = [
        _discrepancy_contract_row(row, audit_metadata=audit_metadata, preview_limit=preview_limit)
        for row in boundary_output["discrepancy_report_rows"]
    ]
    blocked_delivery_contract_rows = [
        _blocked_delivery_contract_row(row, audit_metadata=audit_metadata)
        for row in boundary_output["blocked_delivery_rows"]
    ]
    delivery_reaudit_contract_rows = [
        _delivery_reaudit_contract_row(row, audit_metadata=audit_metadata)
        for row in boundary_output["delivery_clean_candidates"]
    ]
    audit_contract = _audit_contract(
        boundary_output=boundary_output,
        review_queue_contract_items=review_queue_contract_items,
        discrepancy_report_contract_rows=discrepancy_report_contract_rows,
        blocked_delivery_contract_rows=blocked_delivery_contract_rows,
        delivery_reaudit_contract_rows=delivery_reaudit_contract_rows,
        explicit_future_policy_gate=explicit_future_policy_gate,
    )

    output = {
        "review_queue_contract_items": review_queue_contract_items,
        "discrepancy_report_contract_rows": discrepancy_report_contract_rows,
        "blocked_delivery_contract_rows": blocked_delivery_contract_rows,
        "delivery_reaudit_contract_rows": delivery_reaudit_contract_rows,
        "audit_contract": audit_contract,
    }
    validate_no_forbidden_fields(output)
    if run_id != audit_contract["run_id"] or adapter_version != audit_contract["adapter_version"]:
        raise ProductionBoundaryContractError("audit contract lost run_id or adapter_version")
    if input_file_hashes != audit_contract["input_file_hashes"]:
        raise ProductionBoundaryContractError("audit contract lost input_file_hashes")
    return output


def validate_boundary_output_shape(boundary_output: Any, *, preview_limit: int = DEFAULT_PREVIEW_LIMIT) -> None:
    if not isinstance(boundary_output, dict):
        raise ProductionBoundaryContractError("boundary output must be an object")
    validate_no_forbidden_fields(boundary_output)

    missing = [field for field in REQUIRED_BOUNDARY_OUTPUT_FIELDS if field not in boundary_output]
    if missing:
        raise ProductionBoundaryContractError(f"boundary output missing required fields: {missing}")
    for field in ("review_queue_items", "discrepancy_report_rows", "delivery_clean_candidates", "blocked_delivery_rows"):
        if not isinstance(boundary_output[field], list):
            raise ProductionBoundaryContractError(f"{field} must be a list")
    _validate_audit_metadata(boundary_output["audit_metadata"])

    metadata = boundary_output["audit_metadata"]
    if len(boundary_output["review_queue_items"]) != metadata["review_queue_count"]:
        raise ProductionBoundaryContractError("review_queue_count does not match review_queue_items")
    if len(boundary_output["discrepancy_report_rows"]) != metadata["discrepancy_report_count"]:
        raise ProductionBoundaryContractError("discrepancy_report_count does not match discrepancy_report_rows")
    if len(boundary_output["blocked_delivery_rows"]) != metadata["blocked_delivery_row_count"]:
        raise ProductionBoundaryContractError("blocked_delivery_row_count does not match blocked_delivery_rows")
    if len(boundary_output["delivery_clean_candidates"]) != metadata["delivery_clean_candidate_count"]:
        raise ProductionBoundaryContractError("delivery_clean_candidate_count does not match delivery_clean_candidates")

    for item in boundary_output["review_queue_items"]:
        _validate_review_item(item, metadata=metadata, preview_limit=preview_limit)
    for report_row in boundary_output["discrepancy_report_rows"]:
        _validate_bounded_preview(report_row.get("evidence_preview", ""), preview_limit)
    for delivery_candidate in boundary_output["delivery_clean_candidates"]:
        if delivery_candidate.get("delivery_clean_admitted") is True:
            raise ProductionBoundaryContractError("delivery clean admission is forbidden")
        if delivery_candidate.get("requires_reaudit_before_clean_delivery") is not True:
            raise ProductionBoundaryContractError("delivery candidates must require re-audit before clean delivery")


def validate_no_forbidden_fields(value: Any, *, allow_comparison_input: bool = False, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS and not (allow_comparison_input and key == "full_source_text_negative_control"):
                raise ProductionBoundaryContractError(f"forbidden input field at {path}.{key}: {key}")
            if key == "evidence_level" and _clean(child) == "STRONG_EVIDENCE":
                raise ProductionBoundaryContractError("STRONG_EVIDENCE promotion is forbidden")
            if key in {"client_ready", "production_ready", "formal_client_export_allowed"} and child is True:
                raise ProductionBoundaryContractError(f"readiness gate opened at {path}.{key}")
            validate_no_forbidden_fields(child, allow_comparison_input=allow_comparison_input, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_no_forbidden_fields(child, allow_comparison_input=allow_comparison_input, path=f"{path}[{index}]")


def _validate_audit_metadata(metadata: Any) -> None:
    if not isinstance(metadata, dict):
        raise ProductionBoundaryContractError("audit_metadata must be an object")
    missing = [field for field in REQUIRED_AUDIT_METADATA_FIELDS if field not in metadata]
    if missing:
        raise ProductionBoundaryContractError(f"audit_metadata missing required fields: {missing}")
    if not _clean(metadata.get("run_id")):
        raise ProductionBoundaryContractError("run_id is required")
    if not _clean(metadata.get("adapter_version")):
        raise ProductionBoundaryContractError("adapter_version is required")
    if not isinstance(metadata.get("input_file_hashes"), dict) or not metadata["input_file_hashes"]:
        raise ProductionBoundaryContractError("input_file_hashes must be a non-empty object")
    if metadata.get("readiness_gates") != READINESS_GATES_CLOSED:
        raise ProductionBoundaryContractError("readiness gates must remain closed")
    if metadata.get("external_call_counts") != EXTERNAL_CALL_COUNTS_ZERO:
        raise ProductionBoundaryContractError("external call counts must stay zero")
    boundary_flags = metadata.get("boundary_flags")
    if not isinstance(boundary_flags, dict):
        raise ProductionBoundaryContractError("boundary_flags must be an object")
    if boundary_flags.get("production_hook") is True:
        raise ProductionBoundaryContractError("production hooks are forbidden")
    if boundary_flags.get("verified_auto_clean") is True:
        raise ProductionBoundaryContractError("VERIFIED auto-clean is forbidden")
    if boundary_flags.get("verified_promotes_to_strong_evidence") is True:
        raise ProductionBoundaryContractError("VERIFIED promotion to STRONG_EVIDENCE is forbidden")
    if boundary_flags.get("full_source_text_serialized") is True:
        raise ProductionBoundaryContractError("full source text serialization is forbidden")


def _validate_review_item(item: Any, *, metadata: dict[str, Any], preview_limit: int) -> None:
    if not isinstance(item, dict):
        raise ProductionBoundaryContractError("review_queue_items must contain objects")
    missing = [field for field in REQUIRED_REVIEW_ITEM_FIELDS if field not in item]
    if missing:
        raise ProductionBoundaryContractError(f"review item missing required fields: {missing}")
    if item["agreement_status"] not in REVIEW_QUEUE_STATUSES:
        raise ProductionBoundaryContractError(f"review item status must be non-VERIFIED: {item['agreement_status']}")
    if item.get("run_id") != metadata["run_id"]:
        raise ProductionBoundaryContractError("review item run_id mismatch")
    if item.get("adapter_version") != metadata["adapter_version"]:
        raise ProductionBoundaryContractError("review item adapter_version mismatch")
    if item.get("input_file_hashes") != metadata["input_file_hashes"]:
        raise ProductionBoundaryContractError("review item input_file_hashes mismatch")
    if not _clean(item.get("review_item_id")) or not _clean(item.get("audit_hash")):
        raise ProductionBoundaryContractError("review item id and audit_hash are required")
    reviewer_decision = _clean(item.get("reviewer_decision"))
    if reviewer_decision and reviewer_decision not in REVIEWER_ACTIONS:
        raise ProductionBoundaryContractError(f"unsupported reviewer action: {reviewer_decision}")
    _validate_bounded_preview(item.get("evidence_preview", ""), preview_limit)


def _validate_bounded_preview(value: Any, preview_limit: int) -> None:
    if len(_clean(value)) > preview_limit:
        raise ProductionBoundaryContractError("evidence_preview exceeds preview_limit")


def _contract_item_from_review_item(
    item: dict[str, Any],
    *,
    blocked_review_item_ids: set[str],
    explicit_future_policy_gate: bool,
    preview_limit: int,
) -> dict[str, Any]:
    clean_data_eligible = bool(
        explicit_future_policy_gate
        and item.get("clean_data_eligible") is True
        and _clean(item.get("reviewer_decision")) in REVIEWER_ACTIONS
        and _clean(item.get("reviewer_note"))
        and _clean(item.get("review_status")).startswith("RESOLVED_")
    )
    contract_seed = {
        "contract_version": CONTRACT_VERSION,
        "review_item_id": item["review_item_id"],
        "audit_hash": item["audit_hash"],
        "run_id": item["run_id"],
    }
    contract_item = {
        "contract_item_id": "r7au:" + _hash_json(contract_seed)[:24],
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
        "clean_data_eligible": clean_data_eligible,
        "delivery_blocked": item["review_item_id"] in blocked_review_item_ids,
        "evidence_preview": _bounded_preview(item.get("evidence_preview", ""), preview_limit),
        "matched_locator": item["matched_locator"],
        "run_id": item["run_id"],
        "adapter_version": item["adapter_version"],
        "input_file_hashes": dict(item["input_file_hashes"]),
        "audit_hash": item["audit_hash"],
        "contract_version": CONTRACT_VERSION,
        "created_from": CREATED_FROM,
    }
    missing = [field for field in CONTRACT_ITEM_FIELDS if field not in contract_item]
    if missing:
        raise ProductionBoundaryContractError(f"contract item missing fields: {missing}")
    return contract_item


def _discrepancy_contract_row(
    row: dict[str, Any],
    *,
    audit_metadata: dict[str, Any],
    preview_limit: int,
) -> dict[str, Any]:
    _validate_bounded_preview(row.get("evidence_preview", ""), preview_limit)
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
        "evidence_preview": _bounded_preview(row.get("evidence_preview", ""), preview_limit),
        "risk_reason": row["risk_reason"],
        "suggested_action": row["suggested_action"],
        "clean_data_eligible": False,
        "run_id": audit_metadata["run_id"],
        "adapter_version": audit_metadata["adapter_version"],
        "contract_version": CONTRACT_VERSION,
        "created_from": CREATED_FROM,
    }


def _blocked_delivery_contract_row(row: dict[str, Any], *, audit_metadata: dict[str, Any]) -> dict[str, Any]:
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
        "contract_version": CONTRACT_VERSION,
        "created_from": CREATED_FROM,
    }


def _delivery_reaudit_contract_row(row: dict[str, Any], *, audit_metadata: dict[str, Any]) -> dict[str, Any]:
    if row.get("delivery_clean_admitted") is True:
        raise ProductionBoundaryContractError("delivery clean admission is forbidden")
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
        "contract_version": CONTRACT_VERSION,
        "created_from": CREATED_FROM,
    }


def _audit_contract(
    *,
    boundary_output: dict[str, Any],
    review_queue_contract_items: list[dict[str, Any]],
    discrepancy_report_contract_rows: list[dict[str, Any]],
    blocked_delivery_contract_rows: list[dict[str, Any]],
    delivery_reaudit_contract_rows: list[dict[str, Any]],
    explicit_future_policy_gate: bool,
) -> dict[str, Any]:
    metadata = boundary_output["audit_metadata"]
    contract = {
        "contract_version": CONTRACT_VERSION,
        "created_from": CREATED_FROM,
        "run_id": metadata["run_id"],
        "adapter_version": metadata["adapter_version"],
        "input_file_hashes": dict(metadata["input_file_hashes"]),
        "review_queue_contract_count": len(review_queue_contract_items),
        "review_queue_contract_status_counts": dict(
            Counter(item["agreement_status"] for item in review_queue_contract_items)
        ),
        "discrepancy_report_contract_count": len(discrepancy_report_contract_rows),
        "blocked_delivery_contract_count": len(blocked_delivery_contract_rows),
        "delivery_reaudit_contract_count": len(delivery_reaudit_contract_rows),
        "clean_data_eligible_contract_count": sum(
            1 for item in review_queue_contract_items if item["clean_data_eligible"] is True
        ),
        "verified_review_queue_contract_count": sum(
            1 for item in review_queue_contract_items if item["agreement_status"] == "VERIFIED"
        ),
        "explicit_future_policy_gate": explicit_future_policy_gate,
        "source_audit_metadata_hash": metadata["audit_metadata_hash"],
        "readiness_gates": dict(metadata["readiness_gates"]),
        "external_call_counts": dict(metadata["external_call_counts"]),
        "boundary_flags": {
            "test_only": True,
            "production_hook": False,
            "metadata_first": True,
            "full_source_text_serialized": False,
            "verified_auto_clean": False,
            "verified_promotes_to_strong_evidence": False,
        },
    }
    contract["audit_contract_hash"] = _hash_json(contract)
    return contract


def _bounded_preview(value: Any, limit: int) -> str:
    normalized = " ".join(_clean(value).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 3)] + "..."


def _hash_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
