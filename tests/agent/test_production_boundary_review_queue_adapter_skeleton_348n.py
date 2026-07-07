"""Tests for the R7AW disabled production-boundary adapter skeleton."""

from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path

import pytest

from datefac_agent.review.production_boundary_review_queue_adapter import (
    EXTERNAL_CALL_COUNTS_ZERO,
    READINESS_GATES_CLOSED,
    TEST_ONLY_ENABLE_TOKEN,
    ProductionBoundaryReviewQueueAdapterConfig,
    ProductionBoundaryReviewQueueAdapterError,
    build_production_boundary_review_queue_adapter_output,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "discrepancy_review_queue"
    / "r7aw_disabled_adapter_skeleton_fixture.json"
)
MODULE_PATH = Path("datefac_agent/review/production_boundary_review_queue_adapter.py")


def _fixture() -> dict:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7aw"
    return payload


def _enabled_config() -> ProductionBoundaryReviewQueueAdapterConfig:
    return ProductionBoundaryReviewQueueAdapterConfig(enabled=True, test_only_enable_token=TEST_ONLY_ENABLE_TOKEN)


def _enabled_output() -> dict:
    return build_production_boundary_review_queue_adapter_output(
        deepcopy(_fixture()["valid_boundary_output"]),
        _enabled_config(),
    )


def test_r7aw_default_disabled_fail_closed_behavior() -> None:
    result = build_production_boundary_review_queue_adapter_output(_fixture()["valid_boundary_output"])

    assert result["adapter_status"] == "DISABLED"
    assert result["review_queue_candidate_items"] == []
    assert result["blocked_delivery_candidate_rows"] == []
    assert result["delivery_reaudit_candidate_rows"] == []
    assert result["audit_contract"]["enabled"] is False
    assert result["audit_contract"]["readiness_gates"] == READINESS_GATES_CLOSED
    assert result["audit_contract"]["external_call_counts"] == EXTERNAL_CALL_COUNTS_ZERO
    assert result["audit_contract"]["boundary_flags"]["writes_clean_data"] is False


def test_r7aw_enabled_requires_explicit_test_token() -> None:
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="test-only enable token"):
        build_production_boundary_review_queue_adapter_output(
            _fixture()["valid_boundary_output"],
            ProductionBoundaryReviewQueueAdapterConfig(enabled=True),
        )


def test_r7aw_valid_boundary_output_is_accepted_only_under_test_enable() -> None:
    output = _enabled_output()

    assert output["adapter_status"] == "ENABLED_TEST_ONLY"
    assert len(output["review_queue_candidate_items"]) == 3
    assert len(output["blocked_delivery_candidate_rows"]) == 2
    assert len(output["delivery_reaudit_candidate_rows"]) == 2
    assert output["audit_contract"]["source_run_id"] == "r7aw_fixture_run_001"
    assert output["audit_contract"]["input_file_hashes"] == {
        "datefac_excel": "sha256:r7aw-datefac-fixture",
        "mineru_content_list_v2": "sha256:r7aw-mineru-fixture",
    }


def test_r7aw_invalid_inputs_are_rejected_when_enabled() -> None:
    for case in _fixture()["invalid_inputs"]:
        with pytest.raises(ProductionBoundaryReviewQueueAdapterError):
            build_production_boundary_review_queue_adapter_output(case["payload"], _enabled_config())


def test_r7aw_full_source_text_fields_are_not_accepted() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["review_queue_items"][0]["source_text"] = "forbidden full source text"

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="forbidden field"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7aw_verified_rows_do_not_auto_enter_review_queue_or_clean_data() -> None:
    output = _enabled_output()

    assert all(item["agreement_status"] != "VERIFIED" for item in output["review_queue_candidate_items"])
    assert all(item["clean_data_eligible"] is False for item in output["review_queue_candidate_items"])
    assert all(row["delivery_clean_admitted"] is False for row in output["delivery_reaudit_candidate_rows"])
    assert all(row["requires_reaudit_before_clean_delivery"] is True for row in output["delivery_reaudit_candidate_rows"])
    assert output["audit_contract"]["verified_without_clean_gate_count"] == 1
    assert output["audit_contract"]["clean_data_admitted_count"] == 0
    assert output["audit_contract"]["boundary_flags"]["verified_promotes_to_strong_evidence"] is False


def test_r7aw_non_verified_rows_map_to_review_queue_candidates() -> None:
    output = _enabled_output()
    status_counts = output["audit_contract"]["review_queue_candidate_status_counts"]

    assert status_counts == {"DISAGREED": 2, "AMBIGUOUS": 1}
    assert {item["subqueue"] for item in output["review_queue_candidate_items"]} == {
        "evidence_conflict_queue",
        "evidence_ambiguity_queue",
    }
    assert all(item["adapter_item_id"].startswith("r7aw:") for item in output["review_queue_candidate_items"])


def test_r7aw_unresolved_rows_map_to_blocked_delivery_candidates() -> None:
    output = _enabled_output()

    blocked_ids = {row["review_item_id"] for row in output["blocked_delivery_candidate_rows"]}
    assert blocked_ids == {"r7aw-review-disagreed-001", "r7aw-review-ambiguous-001"}
    assert all(row["delivery_blocked"] is True for row in output["blocked_delivery_candidate_rows"])
    assert all(row["review_status"] == "OPEN" for row in output["blocked_delivery_candidate_rows"])


def test_r7aw_corrected_rows_remain_reaudit_only() -> None:
    output = _enabled_output()
    corrected = next(row for row in output["delivery_reaudit_candidate_rows"] if row["source_row_id"] == "corrected:R4")

    assert corrected["delivery_clean_admitted"] is False
    assert corrected["requires_reaudit_before_clean_delivery"] is True
    assert corrected["delivery_gate_status"] == "REQUIRES_REAUDIT_BEFORE_CLEAN_DELIVERY"


def test_r7aw_audit_metadata_is_preserved_and_readiness_closed() -> None:
    output = _enabled_output()
    audit_contract = output["audit_contract"]

    assert audit_contract["run_id"] == "r7aw_fixture_run_001"
    assert audit_contract["adapter_version"] == "r7as_integration_boundary_test_only_v1"
    assert audit_contract["readiness_gates"] == READINESS_GATES_CLOSED
    assert audit_contract["external_call_counts"] == EXTERNAL_CALL_COUNTS_ZERO
    assert audit_contract["boundary_flags"]["production_hook"] is False


def test_r7aw_ids_and_hashes_are_deterministic() -> None:
    first = _enabled_output()
    second = _enabled_output()

    assert first["audit_contract"]["adapter_audit_hash"] == second["audit_contract"]["adapter_audit_hash"]
    assert [item["adapter_item_id"] for item in first["review_queue_candidate_items"]] == [
        item["adapter_item_id"] for item in second["review_queue_candidate_items"]
    ]
    assert [item["audit_hash"] for item in first["review_queue_candidate_items"]] == [
        item["audit_hash"] for item in second["review_queue_candidate_items"]
    ]


def test_r7aw_evidence_preview_is_bounded_and_unbounded_input_fails_closed() -> None:
    output = _enabled_output()
    assert max(len(row["evidence_preview"]) for row in output["discrepancy_report_candidate_rows"]) <= 160

    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["review_queue_items"][0]["evidence_preview"] = "x" * 161
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="evidence_preview exceeds"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7aw_readiness_clean_and_strong_evidence_mutations_fail_closed() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["audit_metadata"]["readiness_gates"]["production_ready"] = True
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="readiness"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["review_queue_items"][0]["clean_data_eligible"] = True
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="clean_data"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["review_queue_items"][0]["evidence_level"] = "STRONG_EVIDENCE"
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="STRONG_EVIDENCE"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7aw_module_has_no_io_heavy_parser_or_model_hooks() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "datefac",
        "fitz",
        "openai",
        "os",
        "pathlib",
        "pdfplumber",
        "pypdf",
        "requests",
        "socket",
        "subprocess",
        "tests",
    }
    forbidden_calls = {"open", "write_text", "mkdir", "unlink", "remove", "replace", "rename"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def test_r7aw_adapter_has_no_production_pipeline_import_hook() -> None:
    references: list[str] = []
    for path in Path("datefac_agent").rglob("*.py"):
        if path == MODULE_PATH:
            continue
        text = path.read_text(encoding="utf-8")
        if "production_boundary_review_queue_adapter" in text:
            references.append(str(path))

    assert references == []
