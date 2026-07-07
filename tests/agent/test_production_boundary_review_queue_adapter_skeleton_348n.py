"""Tests for the R7AW disabled production-boundary adapter skeleton."""

from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path

import pytest

from datefac_agent.review.production_boundary_review_queue_adapter import (
    ADAPTER_CONTRACT_VERSION,
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


def test_r7ax_unexpected_contract_version_fails_closed_even_when_disabled() -> None:
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="contract_version"):
        build_production_boundary_review_queue_adapter_output(
            _fixture()["valid_boundary_output"],
            ProductionBoundaryReviewQueueAdapterConfig(contract_version="unexpected-contract"),
        )


def test_r7aw_valid_boundary_output_is_accepted_only_under_test_enable() -> None:
    output = _enabled_output()

    assert output["adapter_status"] == "ENABLED_TEST_ONLY"
    assert output["audit_contract"]["contract_version"] == ADAPTER_CONTRACT_VERSION
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


def test_r7ax_boundary_output_rejects_unexpected_top_level_fields() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["comparison_result_rows"] = []

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="unexpected fields"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7aw_full_source_text_fields_are_not_accepted() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["review_queue_items"][0]["source_text"] = "forbidden full source text"

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="forbidden field"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_nested_source_text_fields_are_rejected() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["review_queue_items"][0]["alternative_evidence_candidates"] = [
        {"locator": "page:1:block:1", "metadata": {"source_text": "nested full text"}}
    ]

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="forbidden field"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_missing_required_audit_metadata_fails_closed() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    del payload["audit_metadata"]["input_file_hashes"]

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="audit_metadata missing"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_empty_input_file_hashes_fail_closed() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["audit_metadata"]["input_file_hashes"]["datefac_excel"] = ""

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="input_file_hashes"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_status_count_mismatch_fails_closed() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["audit_metadata"]["review_queue_status_counts"]["DISAGREED"] = 99

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="status counts"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_unknown_agreement_status_fails_closed() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["review_queue_items"][0]["agreement_status"] = "AUTO_VERIFIED"

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="non-VERIFIED"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_unknown_reviewer_action_fails_closed_across_rows() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["discrepancy_report_rows"][0]["reviewer_decision"] = "AUTO_PROMOTE_TO_CLEAN"

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="unsupported reviewer action"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["blocked_delivery_rows"][0]["reviewer_decision"] = "AUTO_PROMOTE_TO_CLEAN"

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="unsupported reviewer action"):
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


def test_r7ax_unresolved_non_verified_delivery_candidate_fails_closed() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["delivery_clean_candidates"].append(
        {
            "review_item_id": "r7aw-review-unresolved-extra",
            "source_row_id": "unresolved-extra:R9",
            "source_document_id": "synthetic-r7aw-report.pdf",
            "candidate_metric_name": "Gross margin",
            "candidate_period": "2026E",
            "candidate_value": "24.9",
            "candidate_unit": "%",
            "agreement_status": "DISAGREED",
            "review_status": "OPEN",
            "reviewer_decision": "",
            "delivery_gate_status": "REQUIRES_REAUDIT_BEFORE_CLEAN_DELIVERY",
            "delivery_clean_admitted": False,
            "requires_reaudit_before_clean_delivery": True,
            "run_id": "r7aw_fixture_run_001",
            "adapter_version": "r7as_integration_boundary_test_only_v1",
            "input_file_hashes": {
                "datefac_excel": "sha256:r7aw-datefac-fixture",
                "mineru_content_list_v2": "sha256:r7aw-mineru-fixture",
            },
        }
    )
    payload["audit_metadata"]["delivery_clean_candidate_count"] += 1

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="unresolved non-VERIFIED"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


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


def test_r7ax_missing_required_evidence_preview_fails_closed() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    payload["review_queue_items"][0]["evidence_preview"] = ""

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="evidence_preview is required"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload = deepcopy(_fixture()["valid_boundary_output"])
    del payload["discrepancy_report_rows"][0]["evidence_preview"]

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="missing required"):
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


def test_r7ax_output_does_not_share_mutable_input_references() -> None:
    payload = deepcopy(_fixture()["valid_boundary_output"])
    output = build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload["audit_metadata"]["input_file_hashes"]["datefac_excel"] = "sha256:mutated"
    payload["review_queue_items"][0]["input_file_hashes"]["datefac_excel"] = "sha256:item-mutated"
    payload["audit_metadata"]["readiness_gates"]["client_ready"] = True

    assert output["audit_contract"]["input_file_hashes"]["datefac_excel"] == "sha256:r7aw-datefac-fixture"
    assert output["review_queue_candidate_items"][0]["input_file_hashes"]["datefac_excel"] == "sha256:r7aw-datefac-fixture"
    assert output["audit_contract"]["readiness_gates"] == READINESS_GATES_CLOSED


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
