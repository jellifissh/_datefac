"""Test-only discrepancy review queue integration boundary prototype for R7AS."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from tests.agent.discrepancy_review_queue_policy_348n import (
    REVIEW_QUEUE_STATUSES,
    apply_reviewer_action,
    build_discrepancy_review_item,
    unresolved_export_bucket,
)

FORBIDDEN_INPUT_FIELDS: frozenset[str] = frozenset(
    {
        "source_text",
        "full_source_text",
        "source_text_full",
        "full_text",
        "raw_mineru_block",
        "full_table_html",
    }
)

REQUIRED_PAYLOAD_FIELDS: tuple[str, ...] = (
    "fixture_scope",
    "run_id",
    "adapter_version",
    "input_file_hashes",
    "comparison_result_rows",
)

REQUIRED_COMPARISON_FIELDS: tuple[str, ...] = (
    "row_id",
    "source_document_id",
    "metric_name",
    "period",
    "value",
    "agreement_status",
    "source_text_status",
    "evidence_type",
    "match_reason",
    "risk_reason",
    "suggested_action",
)

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


class IntegrationBoundaryValidationError(ValueError):
    """Raised when integration-boundary inputs fail closed."""


def load_integration_boundary_fixture(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_integration_payload(payload)
    return payload


def run_discrepancy_review_integration_boundary(
    payload: dict[str, Any],
    *,
    preview_limit: int = 160,
) -> dict[str, Any]:
    validate_integration_payload(payload, preview_limit=preview_limit)

    run_id = _clean(payload["run_id"])
    adapter_version = _clean(payload["adapter_version"])
    input_file_hashes = dict(payload["input_file_hashes"])
    readiness_gates = dict(payload.get("readiness_gates", READINESS_GATES_CLOSED))
    comparison_rows = list(payload["comparison_result_rows"])

    review_queue_items: list[dict[str, Any]] = []
    discrepancy_report_rows: list[dict[str, Any]] = []
    delivery_clean_candidates: list[dict[str, Any]] = []
    blocked_delivery_rows: list[dict[str, Any]] = []
    verified_without_clean_gate: list[dict[str, Any]] = []

    for comparison_row in comparison_rows:
        normalized_row = normalize_comparison_result_row(comparison_row)
        agreement_status = normalized_row["agreement_status"]

        if agreement_status == "VERIFIED":
            if comparison_row.get("explicit_clean_gate") is True and comparison_row.get("clean_gate_passed") is True:
                delivery_clean_candidates.append(
                    _delivery_candidate_from_verified(
                        normalized_row,
                        run_id=run_id,
                        adapter_version=adapter_version,
                        input_file_hashes=input_file_hashes,
                    )
                )
            else:
                verified_without_clean_gate.append(
                    {
                        "source_row_id": normalized_row["source_row_id"],
                        "agreement_status": "VERIFIED",
                        "delivery_status": "NOT_DELIVERY_CLEAN_WITHOUT_EXPLICIT_CLEAN_GATE",
                    }
                )
            continue

        review_item = build_discrepancy_review_item(
            normalized_row,
            run_id=run_id,
            adapter_version=adapter_version,
            input_file_hashes=input_file_hashes,
            preview_limit=preview_limit,
        )
        if review_item is None:
            continue

        reviewer_action = _clean(comparison_row.get("reviewer_action"))
        if reviewer_action:
            review_item = apply_reviewer_action(
                review_item,
                reviewer_action,
                reviewer_note=_clean(comparison_row.get("reviewer_note")),
                reviewer_corrected_value=_clean(comparison_row.get("reviewer_corrected_value")),
                reviewer_corrected_unit=_clean(comparison_row.get("reviewer_corrected_unit")),
                explicit_policy_gate=comparison_row.get("explicit_policy_gate") is True,
            )

        review_queue_items.append(review_item)
        discrepancy_report_rows.append(_discrepancy_report_row(review_item))

        if review_item.get("clean_data_eligible") is True:
            delivery_clean_candidates.append(_delivery_candidate_from_review_item(review_item))
        else:
            blocked_delivery_rows.append(_blocked_delivery_row(review_item))

    audit_metadata = _audit_metadata(
        payload=payload,
        review_queue_items=review_queue_items,
        discrepancy_report_rows=discrepancy_report_rows,
        delivery_clean_candidates=delivery_clean_candidates,
        blocked_delivery_rows=blocked_delivery_rows,
        verified_without_clean_gate=verified_without_clean_gate,
        readiness_gates=readiness_gates,
    )

    return {
        "review_queue_items": review_queue_items,
        "discrepancy_report_rows": discrepancy_report_rows,
        "delivery_clean_candidates": delivery_clean_candidates,
        "blocked_delivery_rows": blocked_delivery_rows,
        "audit_metadata": audit_metadata,
    }


def validate_integration_payload(payload: Any, *, preview_limit: int = 160) -> None:
    if not isinstance(payload, dict):
        raise IntegrationBoundaryValidationError("payload must be a JSON object")
    missing_payload_fields = [field for field in REQUIRED_PAYLOAD_FIELDS if field not in payload]
    if missing_payload_fields:
        raise IntegrationBoundaryValidationError(f"payload missing required fields: {missing_payload_fields}")
    if payload.get("fixture_scope") != "test_only_r7as":
        raise IntegrationBoundaryValidationError("fixture_scope must be test_only_r7as")
    if not _clean(payload.get("run_id")):
        raise IntegrationBoundaryValidationError("run_id is required")
    if not _clean(payload.get("adapter_version")):
        raise IntegrationBoundaryValidationError("adapter_version is required")
    if not isinstance(payload.get("input_file_hashes"), dict) or not payload["input_file_hashes"]:
        raise IntegrationBoundaryValidationError("input_file_hashes must be a non-empty object")
    if payload.get("readiness_gates", READINESS_GATES_CLOSED) != READINESS_GATES_CLOSED:
        raise IntegrationBoundaryValidationError("readiness_gates must remain closed")
    if not isinstance(payload.get("comparison_result_rows"), list):
        raise IntegrationBoundaryValidationError("comparison_result_rows must be a list")

    for row in payload["comparison_result_rows"]:
        validate_comparison_result_row(row, preview_limit=preview_limit)


def validate_comparison_result_row(row: Any, *, preview_limit: int = 160) -> None:
    if not isinstance(row, dict):
        raise IntegrationBoundaryValidationError("comparison_result row must be an object")
    forbidden = sorted(FORBIDDEN_INPUT_FIELDS & set(row))
    if forbidden:
        raise IntegrationBoundaryValidationError(f"forbidden full source text fields present: {forbidden}")
    missing = [field for field in REQUIRED_COMPARISON_FIELDS if field not in row]
    if missing:
        raise IntegrationBoundaryValidationError(f"comparison_result row missing required fields: {missing}")
    agreement_status = _clean(row.get("agreement_status"))
    if agreement_status not in {"VERIFIED", *REVIEW_QUEUE_STATUSES}:
        raise IntegrationBoundaryValidationError(f"unsupported agreement_status: {agreement_status}")
    if len(_clean(row.get("evidence_preview"))) > preview_limit:
        raise IntegrationBoundaryValidationError("evidence_preview exceeds preview_limit")


def normalize_comparison_result_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_document_id": _clean(row.get("source_document_id")),
        "source_row_id": _clean(row.get("row_id")),
        "candidate_metric_name": _clean(row.get("metric_name")),
        "candidate_period": _clean(row.get("period")),
        "candidate_value": _clean(row.get("value")),
        "candidate_unit": _clean(row.get("unit")),
        "candidate_page_number": row.get("page_number"),
        "agreement_status": _clean(row.get("agreement_status")),
        "source_text_status": _clean(row.get("source_text_status")),
        "evidence_type": _clean(row.get("evidence_type")),
        "matched_page_number": row.get("matched_page"),
        "matched_locator": _clean(row.get("matched_locator")),
        "matched_block_index": row.get("matched_block_index"),
        "matched_text_sha256": _clean(row.get("matched_text_sha256")),
        "matched_char_count": row.get("matched_char_count"),
        "evidence_preview": _clean(row.get("evidence_preview")),
        "candidate_raw_text": _clean(row.get("raw_text")),
        "match_reason": _clean(row.get("match_reason")),
        "risk_reason": _clean(row.get("risk_reason")),
        "suggested_action": _clean(row.get("suggested_action")),
        "alternative_evidence_candidates": deepcopy(row.get("alternative_evidence_candidates", [])),
        "core_metric": row.get("core_metric") is True,
    }


def _delivery_candidate_from_verified(
    row: dict[str, Any],
    *,
    run_id: str,
    adapter_version: str,
    input_file_hashes: dict[str, str],
) -> dict[str, Any]:
    return {
        "source_row_id": row["source_row_id"],
        "source_document_id": row["source_document_id"],
        "candidate_metric_name": row["candidate_metric_name"],
        "candidate_period": row["candidate_period"],
        "candidate_value": row["candidate_value"],
        "candidate_unit": row["candidate_unit"],
        "agreement_status": "VERIFIED",
        "delivery_gate_status": "EXPLICIT_CLEAN_GATE_PASSED",
        "delivery_clean_admitted": False,
        "requires_reaudit_before_clean_delivery": True,
        "run_id": run_id,
        "adapter_version": adapter_version,
        "input_file_hashes": dict(input_file_hashes),
    }


def _delivery_candidate_from_review_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_item_id": item["review_item_id"],
        "source_row_id": item["source_row_id"],
        "source_document_id": item["source_document_id"],
        "candidate_metric_name": item["candidate_metric_name"],
        "candidate_period": item["candidate_period"],
        "candidate_value": item["candidate_value"],
        "candidate_unit": item["candidate_unit"],
        "agreement_status": item["agreement_status"],
        "review_status": item["review_status"],
        "reviewer_decision": item["reviewer_decision"],
        "delivery_gate_status": unresolved_export_bucket(item),
        "delivery_clean_admitted": False,
        "requires_reaudit_before_clean_delivery": True,
        "run_id": item["run_id"],
        "adapter_version": item["adapter_version"],
        "input_file_hashes": dict(item["input_file_hashes"]),
    }


def _blocked_delivery_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_item_id": item["review_item_id"],
        "source_row_id": item["source_row_id"],
        "agreement_status": item["agreement_status"],
        "review_subqueue": item["review_subqueue"],
        "severity": item["severity"],
        "review_status": item["review_status"],
        "reviewer_decision": item["reviewer_decision"],
        "blocked_reason": "unresolved_or_not_clean_data_eligible",
        "export_bucket": "blocked_delivery_rows",
    }


def _discrepancy_report_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_item_id": item["review_item_id"],
        "source_row_id": item["source_row_id"],
        "candidate_metric_name": item["candidate_metric_name"],
        "candidate_period": item["candidate_period"],
        "candidate_value": item["candidate_value"],
        "candidate_unit": item["candidate_unit"],
        "agreement_status": item["agreement_status"],
        "review_subqueue": item["review_subqueue"],
        "severity": item["severity"],
        "review_status": item["review_status"],
        "reviewer_decision": item["reviewer_decision"],
        "source_text_status": item["source_text_status"],
        "evidence_type": item["evidence_type"],
        "matched_locator": item["matched_locator"],
        "matched_text_sha256": item["matched_text_sha256"],
        "evidence_preview": item["evidence_preview"],
        "risk_reason": item["risk_reason"],
        "suggested_action": item["suggested_action"],
        "clean_data_eligible": item["clean_data_eligible"],
    }


def _audit_metadata(
    *,
    payload: dict[str, Any],
    review_queue_items: list[dict[str, Any]],
    discrepancy_report_rows: list[dict[str, Any]],
    delivery_clean_candidates: list[dict[str, Any]],
    blocked_delivery_rows: list[dict[str, Any]],
    verified_without_clean_gate: list[dict[str, Any]],
    readiness_gates: dict[str, bool],
) -> dict[str, Any]:
    row_status_counts = Counter(row["agreement_status"] for row in payload["comparison_result_rows"])
    review_status_counts = Counter(item["agreement_status"] for item in review_queue_items)
    metadata = {
        "run_id": payload["run_id"],
        "adapter_version": payload["adapter_version"],
        "input_file_hashes": dict(payload["input_file_hashes"]),
        "comparison_row_count": len(payload["comparison_result_rows"]),
        "comparison_status_counts": dict(row_status_counts),
        "review_queue_count": len(review_queue_items),
        "review_queue_status_counts": dict(review_status_counts),
        "discrepancy_report_count": len(discrepancy_report_rows),
        "delivery_clean_candidate_count": len(delivery_clean_candidates),
        "blocked_delivery_row_count": len(blocked_delivery_rows),
        "verified_without_clean_gate_count": len(verified_without_clean_gate),
        "readiness_gates": readiness_gates,
        "external_call_counts": EXTERNAL_CALL_COUNTS_ZERO,
        "boundary_flags": {
            "test_only": True,
            "production_hook": False,
            "verified_auto_clean": False,
            "verified_promotes_to_strong_evidence": False,
            "full_source_text_serialized": False,
        },
    }
    metadata["audit_metadata_hash"] = _hash_json(metadata)
    return metadata


def _hash_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
