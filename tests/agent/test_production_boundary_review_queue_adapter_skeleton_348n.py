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
R7AY_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "discrepancy_review_queue"
    / "r7ay_negative_case_matrix_fixture.json"
)
R7AZ_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "discrepancy_review_queue"
    / "r7az_positive_path_minimal_contract_fixture.json"
)
MODULE_PATH = Path("datefac_agent/review/production_boundary_review_queue_adapter.py")


def _fixture() -> dict:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7aw"
    return payload


def _r7ay_fixture() -> dict:
    payload = json.loads(R7AY_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7ay"
    return payload


def _r7az_fixture() -> dict:
    payload = json.loads(R7AZ_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7az"
    return payload


def _r7az_payload(case_id: str) -> dict:
    record = next(case for case in _r7az_fixture()["positive_payloads"] if case["case_id"] == case_id)
    return deepcopy(record["payload"])


def _valid_boundary_payload() -> dict:
    return deepcopy(_r7ay_fixture()["valid_boundary_output"])


def _enabled_config() -> ProductionBoundaryReviewQueueAdapterConfig:
    return ProductionBoundaryReviewQueueAdapterConfig(enabled=True, test_only_enable_token=TEST_ONLY_ENABLE_TOKEN)


def _enabled_output() -> dict:
    return build_production_boundary_review_queue_adapter_output(
        _valid_boundary_payload(),
        _enabled_config(),
    )


def _apply_mutation(payload: dict, mutation: dict) -> dict:
    updated = deepcopy(payload)
    path = mutation["path"]
    parent = updated
    for key in path[:-1]:
        parent = parent[key]
    leaf = path[-1]
    if mutation["op"] == "delete":
        del parent[leaf]
    elif mutation["op"] == "set":
        parent[leaf] = mutation["value"]
    else:
        raise AssertionError(f"unsupported mutation op: {mutation['op']}")
    return updated


def _negative_case_ids() -> list[str]:
    return [case["case_id"] for case in _r7ay_fixture()["negative_case_matrix"]]


def _positive_case_ids() -> list[str]:
    return [case["case_id"] for case in _r7az_fixture()["positive_payloads"]]


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


def test_r7ay_negative_case_matrix_fixture_is_curated() -> None:
    fixture = _r7ay_fixture()
    valid = fixture["valid_boundary_output"]
    cases = fixture["negative_case_matrix"]

    assert R7AY_FIXTURE_PATH.stat().st_size < 50000
    assert valid["contract_version"] == ADAPTER_CONTRACT_VERSION
    assert len(cases) >= 29
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert {
        "input_contract",
        "reviewer_action",
        "clean_delivery",
        "evidence_preview",
        "audit_metadata",
    }.issubset({case["category"] for case in cases})


@pytest.mark.parametrize("case_id", _negative_case_ids())
def test_r7ay_negative_case_matrix_fails_closed(case_id: str) -> None:
    case = next(record for record in _r7ay_fixture()["negative_case_matrix"] if record["case_id"] == case_id)
    payload = deepcopy(case["payload"]) if "payload" in case else _apply_mutation(_valid_boundary_payload(), case["mutation"])

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match=case["expected_error"]):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7az_positive_path_fixture_is_curated_and_complete() -> None:
    fixture = _r7az_fixture()
    cases = fixture["positive_payloads"]
    case_ids = {case["case_id"] for case in cases}

    assert R7AZ_FIXTURE_PATH.stat().st_size < 50000
    assert len(cases) == 8
    assert len(case_ids) == len(cases)
    assert {
        "verified_only_minimal",
        "disagreed_only_minimal",
        "ambiguous_only_minimal",
        "missing_evidence_only_minimal",
        "unverified_only_minimal",
        "corrected_reaudit_only_minimal",
        "mixed_verified_and_non_verified_minimal",
        "bounded_preview_required_metadata_only",
    } == case_ids
    for case in cases:
        payload = case["payload"]
        assert set(payload) == {
            "contract_version",
            "review_queue_items",
            "discrepancy_report_rows",
            "delivery_clean_candidates",
            "blocked_delivery_rows",
            "audit_metadata",
        }
        assert payload["contract_version"] == ADAPTER_CONTRACT_VERSION
        assert set(payload["audit_metadata"]) == {
            "run_id",
            "adapter_version",
            "input_file_hashes",
            "comparison_row_count",
            "comparison_status_counts",
            "review_queue_count",
            "review_queue_status_counts",
            "discrepancy_report_count",
            "delivery_clean_candidate_count",
            "blocked_delivery_row_count",
            "verified_without_clean_gate_count",
            "readiness_gates",
            "external_call_counts",
            "boundary_flags",
            "audit_metadata_hash",
        }


@pytest.mark.parametrize("case_id", _positive_case_ids())
def test_r7az_minimal_positive_payloads_pass_only_when_explicitly_enabled(case_id: str) -> None:
    disabled = build_production_boundary_review_queue_adapter_output(_r7az_payload(case_id))

    assert disabled["adapter_status"] == "DISABLED"
    assert disabled["review_queue_candidate_items"] == []
    assert disabled["delivery_reaudit_candidate_rows"] == []
    assert disabled["audit_contract"]["readiness_gates"] == READINESS_GATES_CLOSED

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="test-only enable token"):
        build_production_boundary_review_queue_adapter_output(
            _r7az_payload(case_id),
            ProductionBoundaryReviewQueueAdapterConfig(enabled=True),
        )

    output = build_production_boundary_review_queue_adapter_output(_r7az_payload(case_id), _enabled_config())
    metadata = _r7az_payload(case_id)["audit_metadata"]

    assert output["adapter_status"] == "ENABLED_TEST_ONLY"
    assert output["audit_contract"]["contract_version"] == ADAPTER_CONTRACT_VERSION
    assert output["audit_contract"]["source_run_id"] == metadata["run_id"]
    assert output["audit_contract"]["adapter_version"] == metadata["adapter_version"]
    assert output["audit_contract"]["input_file_hashes"] == metadata["input_file_hashes"]
    assert output["audit_contract"]["readiness_gates"] == READINESS_GATES_CLOSED
    assert output["audit_contract"]["external_call_counts"] == EXTERNAL_CALL_COUNTS_ZERO
    assert output["audit_contract"]["clean_data_admitted_count"] == 0
    assert output["audit_contract"]["boundary_flags"]["writes_review_queue"] is False
    assert output["audit_contract"]["boundary_flags"]["writes_clean_data"] is False
    assert output["audit_contract"]["boundary_flags"]["writes_delivery"] is False


def test_r7az_candidate_output_schema_is_stable_for_review_bound_rows() -> None:
    output = build_production_boundary_review_queue_adapter_output(
        _r7az_payload("disagreed_only_minimal"),
        _enabled_config(),
    )
    item = output["review_queue_candidate_items"][0]
    discrepancy_row = output["discrepancy_report_candidate_rows"][0]
    blocked_row = output["blocked_delivery_candidate_rows"][0]

    assert set(item) == {
        "adapter_item_id",
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
        "created_from",
    }
    assert set(discrepancy_row) == {
        "review_item_id",
        "source_row_id",
        "candidate_metric_name",
        "candidate_period",
        "candidate_value",
        "candidate_unit",
        "agreement_status",
        "subqueue",
        "severity",
        "review_status",
        "reviewer_action",
        "source_text_status",
        "evidence_type",
        "matched_locator",
        "matched_text_sha256",
        "evidence_preview",
        "evidence_preview_sha256",
        "risk_reason",
        "suggested_action",
        "clean_data_eligible",
        "run_id",
        "adapter_version",
        "adapter_contract_version",
        "created_from",
    }
    assert set(blocked_row) == {
        "review_item_id",
        "source_row_id",
        "agreement_status",
        "subqueue",
        "severity",
        "review_status",
        "reviewer_action",
        "blocked_reason",
        "delivery_blocked",
        "run_id",
        "adapter_version",
        "adapter_contract_version",
        "created_from",
    }


@pytest.mark.parametrize(
    ("case_id", "status"),
    [
        ("disagreed_only_minimal", "DISAGREED"),
        ("ambiguous_only_minimal", "AMBIGUOUS"),
        ("missing_evidence_only_minimal", "MISSING_EVIDENCE"),
        ("unverified_only_minimal", "UNVERIFIED"),
    ],
)
def test_r7az_unresolved_non_verified_rows_are_review_bound(case_id: str, status: str) -> None:
    output = build_production_boundary_review_queue_adapter_output(_r7az_payload(case_id), _enabled_config())

    assert output["audit_contract"]["review_queue_candidate_status_counts"] == {status: 1}
    assert len(output["review_queue_candidate_items"]) == 1
    assert len(output["discrepancy_report_candidate_rows"]) == 1
    assert len(output["blocked_delivery_candidate_rows"]) == 1
    assert output["delivery_reaudit_candidate_rows"] == []
    assert output["review_queue_candidate_items"][0]["agreement_status"] == status
    assert output["review_queue_candidate_items"][0]["clean_data_eligible"] is False
    assert output["review_queue_candidate_items"][0]["delivery_blocked"] is True
    assert output["blocked_delivery_candidate_rows"][0]["delivery_blocked"] is True
    assert output["audit_contract"]["clean_data_admitted_count"] == 0


def test_r7az_verified_row_is_safe_delivery_reaudit_only() -> None:
    output = build_production_boundary_review_queue_adapter_output(
        _r7az_payload("verified_only_minimal"),
        _enabled_config(),
    )

    assert output["review_queue_candidate_items"] == []
    assert output["discrepancy_report_candidate_rows"] == []
    assert output["blocked_delivery_candidate_rows"] == []
    assert len(output["delivery_reaudit_candidate_rows"]) == 1
    delivery_row = output["delivery_reaudit_candidate_rows"][0]
    assert delivery_row["agreement_status"] == "VERIFIED"
    assert delivery_row["delivery_gate_status"] == "EXPLICIT_CLEAN_GATE_REQUIRED"
    assert delivery_row["delivery_clean_admitted"] is False
    assert delivery_row["requires_reaudit_before_clean_delivery"] is True
    assert output["audit_contract"]["verified_without_clean_gate_count"] == 1
    assert output["audit_contract"]["boundary_flags"]["verified_auto_clean"] is False
    assert output["audit_contract"]["boundary_flags"]["verified_promotes_to_strong_evidence"] is False


def test_r7az_corrected_row_remains_reaudit_only() -> None:
    output = build_production_boundary_review_queue_adapter_output(
        _r7az_payload("corrected_reaudit_only_minimal"),
        _enabled_config(),
    )

    assert output["review_queue_candidate_items"] == []
    assert output["blocked_delivery_candidate_rows"] == []
    assert len(output["delivery_reaudit_candidate_rows"]) == 1
    row = output["delivery_reaudit_candidate_rows"][0]
    assert row["agreement_status"] == "DISAGREED"
    assert row["review_status"] == "RESOLVED_CORRECTED"
    assert row["reviewer_action"] == "CORRECT_VALUE"
    assert row["delivery_gate_status"] == "REQUIRES_REAUDIT_BEFORE_CLEAN_DELIVERY"
    assert row["delivery_clean_admitted"] is False
    assert row["requires_reaudit_before_clean_delivery"] is True


def test_r7az_mixed_payload_preserves_deterministic_ordering_and_counts() -> None:
    first = build_production_boundary_review_queue_adapter_output(
        _r7az_payload("mixed_verified_and_non_verified_minimal"),
        _enabled_config(),
    )
    second = build_production_boundary_review_queue_adapter_output(
        _r7az_payload("mixed_verified_and_non_verified_minimal"),
        _enabled_config(),
    )

    assert [item["agreement_status"] for item in first["review_queue_candidate_items"]] == [
        "DISAGREED",
        "AMBIGUOUS",
        "MISSING_EVIDENCE",
        "UNVERIFIED",
    ]
    assert [item["adapter_item_id"] for item in first["review_queue_candidate_items"]] == [
        item["adapter_item_id"] for item in second["review_queue_candidate_items"]
    ]
    assert first["audit_contract"]["adapter_audit_hash"] == second["audit_contract"]["adapter_audit_hash"]
    assert first["audit_contract"]["review_queue_candidate_count"] == 4
    assert first["audit_contract"]["delivery_reaudit_candidate_count"] == 1
    assert first["audit_contract"]["verified_without_clean_gate_count"] == 1


def test_r7az_bounded_evidence_preview_and_metadata_are_retained() -> None:
    payload = _r7az_payload("bounded_preview_required_metadata_only")
    output = build_production_boundary_review_queue_adapter_output(payload, _enabled_config())
    item = output["review_queue_candidate_items"][0]

    assert len(payload["review_queue_items"][0]["evidence_preview"]) == 160
    assert item["evidence_preview"] == payload["review_queue_items"][0]["evidence_preview"]
    assert len(item["evidence_preview"]) == 160
    assert output["audit_contract"]["run_id"] == payload["audit_metadata"]["run_id"]
    assert output["audit_contract"]["adapter_version"] == payload["audit_metadata"]["adapter_version"]
    assert output["audit_contract"]["input_file_hashes"] == payload["audit_metadata"]["input_file_hashes"]
    assert output["audit_contract"]["source_audit_metadata_hash"] == payload["audit_metadata"]["audit_metadata_hash"]


def test_r7az_output_does_not_share_mutable_input_references() -> None:
    payload = _r7az_payload("disagreed_only_minimal")
    output = build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload["audit_metadata"]["input_file_hashes"]["datefac_excel"] = "sha256:mutated"
    payload["review_queue_items"][0]["input_file_hashes"]["datefac_excel"] = "sha256:item-mutated"
    payload["review_queue_items"][0]["evidence_preview"] = "mutated preview after output"
    payload["audit_metadata"]["readiness_gates"]["client_ready"] = True

    assert output["audit_contract"]["input_file_hashes"]["datefac_excel"] == "sha256:r7az-datefac-minimal-fixture"
    assert output["review_queue_candidate_items"][0]["input_file_hashes"]["datefac_excel"] == (
        "sha256:r7az-datefac-minimal-fixture"
    )
    assert output["review_queue_candidate_items"][0]["evidence_preview"] != "mutated preview after output"
    assert output["audit_contract"]["readiness_gates"] == READINESS_GATES_CLOSED


def test_r7ax_boundary_output_rejects_unexpected_top_level_fields() -> None:
    payload = _valid_boundary_payload()
    payload["comparison_result_rows"] = []

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="unexpected fields"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7aw_full_source_text_fields_are_not_accepted() -> None:
    payload = _valid_boundary_payload()
    payload["review_queue_items"][0]["source_text"] = "forbidden full source text"

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="forbidden field"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_nested_source_text_fields_are_rejected() -> None:
    payload = _valid_boundary_payload()
    payload["review_queue_items"][0]["alternative_evidence_candidates"] = [
        {"locator": "page:1:block:1", "metadata": {"source_text": "nested full text"}}
    ]

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="forbidden field"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_missing_required_audit_metadata_fails_closed() -> None:
    payload = _valid_boundary_payload()
    del payload["audit_metadata"]["input_file_hashes"]

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="audit_metadata missing"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_empty_input_file_hashes_fail_closed() -> None:
    payload = _valid_boundary_payload()
    payload["audit_metadata"]["input_file_hashes"]["datefac_excel"] = ""

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="input_file_hashes"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_status_count_mismatch_fails_closed() -> None:
    payload = _valid_boundary_payload()
    payload["audit_metadata"]["review_queue_status_counts"]["DISAGREED"] = 99

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="status counts"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_unknown_agreement_status_fails_closed() -> None:
    payload = _valid_boundary_payload()
    payload["review_queue_items"][0]["agreement_status"] = "AUTO_VERIFIED"

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="non-VERIFIED"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_unknown_reviewer_action_fails_closed_across_rows() -> None:
    payload = _valid_boundary_payload()
    payload["discrepancy_report_rows"][0]["reviewer_decision"] = "AUTO_PROMOTE_TO_CLEAN"

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="unsupported reviewer action"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload = _valid_boundary_payload()
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
    payload = _valid_boundary_payload()
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

    payload = _valid_boundary_payload()
    payload["review_queue_items"][0]["evidence_preview"] = "x" * 161
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="evidence_preview exceeds"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_missing_required_evidence_preview_fails_closed() -> None:
    payload = _valid_boundary_payload()
    payload["review_queue_items"][0]["evidence_preview"] = ""

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="evidence_preview is required"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload = _valid_boundary_payload()
    del payload["discrepancy_report_rows"][0]["evidence_preview"]

    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="missing required"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7aw_readiness_clean_and_strong_evidence_mutations_fail_closed() -> None:
    payload = _valid_boundary_payload()
    payload["audit_metadata"]["readiness_gates"]["production_ready"] = True
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="readiness"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload = _valid_boundary_payload()
    payload["review_queue_items"][0]["clean_data_eligible"] = True
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="clean_data"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload = _valid_boundary_payload()
    payload["review_queue_items"][0]["evidence_level"] = "STRONG_EVIDENCE"
    with pytest.raises(ProductionBoundaryReviewQueueAdapterError, match="STRONG_EVIDENCE"):
        build_production_boundary_review_queue_adapter_output(payload, _enabled_config())


def test_r7ax_output_does_not_share_mutable_input_references() -> None:
    payload = _valid_boundary_payload()
    output = build_production_boundary_review_queue_adapter_output(payload, _enabled_config())

    payload["audit_metadata"]["input_file_hashes"]["datefac_excel"] = "sha256:mutated"
    payload["review_queue_items"][0]["input_file_hashes"]["datefac_excel"] = "sha256:item-mutated"
    payload["review_queue_items"][0]["evidence_preview"] = "mutated preview after adapter output"
    payload["audit_metadata"]["readiness_gates"]["client_ready"] = True

    assert output["audit_contract"]["input_file_hashes"]["datefac_excel"] == "sha256:r7aw-datefac-fixture"
    assert output["review_queue_candidate_items"][0]["input_file_hashes"]["datefac_excel"] == "sha256:r7aw-datefac-fixture"
    assert output["review_queue_candidate_items"][0]["evidence_preview"] != "mutated preview after adapter output"
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
