"""Tests for the R7AS test-only discrepancy review integration boundary."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

import pytest

from tests.agent.discrepancy_review_queue_integration_boundary_348n import (
    IntegrationBoundaryValidationError,
    load_integration_boundary_fixture,
    run_discrepancy_review_integration_boundary,
)

FIXTURE_PATH = (
    Path(__file__).with_name("fixtures")
    / "discrepancy_review_queue"
    / "r7as_integration_boundary_fixture.json"
)


def _payload() -> dict[str, object]:
    return load_integration_boundary_fixture(FIXTURE_PATH)


def _outputs() -> dict[str, object]:
    return run_discrepancy_review_integration_boundary(_payload())


def test_r7as_fixture_is_small_curated_and_covers_required_rows() -> None:
    payload = _payload()
    rows = payload["comparison_result_rows"]  # type: ignore[index]

    assert payload["fixture_scope"] == "test_only_r7as"
    assert FIXTURE_PATH.stat().st_size < 25000
    assert len(rows) == 8
    assert Counter(row["agreement_status"] for row in rows) == {
        "VERIFIED": 1,
        "DISAGREED": 2,
        "AMBIGUOUS": 1,
        "MISSING_EVIDENCE": 2,
        "PARSE_SKIPPED": 1,
        "UNVERIFIED": 1,
    }
    assert any(row["row_id"] == "resolved-correction:R8" for row in rows)
    assert any(row["row_id"] == "unresolved-action:R21" for row in rows)


def test_r7as_generates_required_boundary_outputs() -> None:
    outputs = _outputs()

    assert set(outputs) == {
        "review_queue_items",
        "discrepancy_report_rows",
        "delivery_clean_candidates",
        "blocked_delivery_rows",
        "audit_metadata",
    }
    assert len(outputs["review_queue_items"]) == 7
    assert len(outputs["discrepancy_report_rows"]) == 7
    assert len(outputs["delivery_clean_candidates"]) == 1
    assert len(outputs["blocked_delivery_rows"]) == 6


def test_r7as_verified_rows_do_not_enter_discrepancy_queue_or_auto_clean() -> None:
    outputs = _outputs()

    assert all(item["source_row_id"] != "verified:R1" for item in outputs["review_queue_items"])
    assert all(row["source_row_id"] != "verified:R1" for row in outputs["delivery_clean_candidates"])
    assert outputs["audit_metadata"]["verified_without_clean_gate_count"] == 1


def test_r7as_verified_rows_require_explicit_clean_gate_even_when_verified() -> None:
    payload = _payload()
    modified = deepcopy(payload)
    for row in modified["comparison_result_rows"]:  # type: ignore[index]
        if row["row_id"] == "verified:R1":
            row["explicit_clean_gate"] = True
            row["clean_gate_passed"] = True
    outputs = run_discrepancy_review_integration_boundary(modified)

    verified_candidates = [
        row for row in outputs["delivery_clean_candidates"] if row["source_row_id"] == "verified:R1"
    ]
    assert len(verified_candidates) == 1
    assert verified_candidates[0]["delivery_clean_admitted"] is False
    assert verified_candidates[0]["requires_reaudit_before_clean_delivery"] is True


def test_r7as_non_verified_rows_map_to_review_queue_subqueues() -> None:
    outputs = _outputs()
    items = outputs["review_queue_items"]

    assert Counter(item["agreement_status"] for item in items) == {
        "DISAGREED": 2,
        "AMBIGUOUS": 1,
        "MISSING_EVIDENCE": 2,
        "PARSE_SKIPPED": 1,
        "UNVERIFIED": 1,
    }
    assert Counter(item["review_subqueue"] for item in items) == {
        "evidence_conflict_queue": 2,
        "evidence_ambiguity_queue": 1,
        "missing_evidence_queue": 2,
        "parse_schema_queue": 1,
        "partial_anchor_queue": 1,
    }


def test_r7as_discrepancy_report_rows_are_metadata_first_and_bounded() -> None:
    outputs = _outputs()
    report_rows = outputs["discrepancy_report_rows"]

    assert report_rows
    assert max(len(row["evidence_preview"]) for row in report_rows) <= 160
    assert all("full_source_text" not in row for row in report_rows)
    assert all("source_text" not in row for row in report_rows)
    assert all("matched_text_sha256" in row for row in report_rows)
    assert all("matched_locator" in row for row in report_rows)


def test_r7as_unresolved_non_verified_rows_are_blocked_from_delivery_clean_output() -> None:
    outputs = _outputs()
    delivery_ids = {row["source_row_id"] for row in outputs["delivery_clean_candidates"]}
    blocked_ids = {row["source_row_id"] for row in outputs["blocked_delivery_rows"]}

    assert "resolved-correction:R8" in delivery_ids
    assert "unresolved-action:R21" in blocked_ids
    assert delivery_ids.isdisjoint(blocked_ids)
    assert all(row["delivery_clean_admitted"] is False for row in outputs["delivery_clean_candidates"])


def test_r7as_audit_metadata_retains_run_adapter_hashes_and_closed_gates() -> None:
    outputs = _outputs()
    metadata = outputs["audit_metadata"]

    assert metadata["run_id"] == "r7as_fixture_run_001"
    assert metadata["adapter_version"] == "r7as_integration_boundary_test_only_v1"
    assert metadata["input_file_hashes"] == {
        "datefac_excel": "sha256:r7as-datefac-fixture",
        "mineru_content_list_v2": "sha256:r7as-mineru-fixture",
    }
    assert metadata["comparison_row_count"] == 8
    assert metadata["review_queue_count"] == 7
    assert metadata["discrepancy_report_count"] == 7
    assert metadata["delivery_clean_candidate_count"] == 1
    assert metadata["blocked_delivery_row_count"] == 6
    assert metadata["readiness_gates"] == {
        "client_ready": False,
        "production_ready": False,
        "formal_client_export_allowed": False,
        "demo_export_only": True,
    }
    assert metadata["external_call_counts"] == {
        "mineru_run_count": 0,
        "ocr_run_count": 0,
        "llm_api_call_count": 0,
        "vlm_api_call_count": 0,
    }
    assert len(metadata["audit_metadata_hash"]) == 64


def test_r7as_review_item_ids_and_hashes_are_deterministic() -> None:
    first = _outputs()["review_queue_items"]
    second = _outputs()["review_queue_items"]

    assert [item["review_item_id"] for item in first] == [item["review_item_id"] for item in second]
    assert [item["audit_hash"] for item in first] == [item["audit_hash"] for item in second]


def test_r7as_rejects_full_source_text_inputs_fail_closed() -> None:
    payload = _payload()
    modified = deepcopy(payload)
    modified["comparison_result_rows"][0]["full_source_text"] = "do not serialize me"  # type: ignore[index]

    with pytest.raises(IntegrationBoundaryValidationError, match="forbidden full source text"):
        run_discrepancy_review_integration_boundary(modified)


def test_r7as_rejects_missing_audit_metadata_fail_closed() -> None:
    payload = _payload()
    modified = deepcopy(payload)
    del modified["input_file_hashes"]

    with pytest.raises(IntegrationBoundaryValidationError, match="payload missing required fields"):
        run_discrepancy_review_integration_boundary(modified)


def test_r7as_unsupported_reviewer_action_fails_closed() -> None:
    payload = _payload()
    modified = deepcopy(payload)
    modified["comparison_result_rows"][1]["reviewer_action"] = "AUTO_PROMOTE_TO_CLEAN"  # type: ignore[index]

    with pytest.raises(ValueError, match="unsupported reviewer action"):
        run_discrepancy_review_integration_boundary(modified)


def test_r7as_readiness_gate_changes_are_rejected() -> None:
    payload = _payload()
    modified = deepcopy(payload)
    modified["readiness_gates"]["client_ready"] = True  # type: ignore[index]

    with pytest.raises(IntegrationBoundaryValidationError, match="readiness_gates must remain closed"):
        run_discrepancy_review_integration_boundary(modified)


def test_r7as_output_does_not_copy_full_source_text_values() -> None:
    outputs = _outputs()
    outputs_json = json.dumps(outputs, ensure_ascii=False)
    forbidden_keys = {"source_text", "full_source_text", "source_text_full", "full_text"}

    for collection_name in ("review_queue_items", "discrepancy_report_rows", "delivery_clean_candidates", "blocked_delivery_rows"):
        assert all(forbidden_keys.isdisjoint(row) for row in outputs[collection_name])
    assert "do not serialize me" not in outputs_json
