"""Tests for the R7AU test-only production-boundary review queue adapter contract."""

from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

import pytest

from tests.agent.production_boundary_review_queue_adapter_contract_348n import (
    CONTRACT_ITEM_FIELDS,
    CONTRACT_VERSION,
    READINESS_GATES_CLOSED,
    ProductionBoundaryContractError,
    build_boundary_output_from_fixture,
    build_production_boundary_review_queue_contract,
    load_contract_fixture,
)

FIXTURE_PATH = (
    Path(__file__).with_name("fixtures")
    / "discrepancy_review_queue"
    / "r7au_production_boundary_contract_fixture.json"
)
HELPER_PATH = Path(__file__).with_name("production_boundary_review_queue_adapter_contract_348n.py")


def _fixture() -> dict[str, object]:
    return load_contract_fixture(FIXTURE_PATH)


def _boundary_output() -> dict[str, object]:
    return build_boundary_output_from_fixture(_fixture())


def _contract(*, explicit_future_policy_gate: bool = False) -> dict[str, object]:
    return build_production_boundary_review_queue_contract(
        _boundary_output(),
        explicit_future_policy_gate=explicit_future_policy_gate,
    )


def test_r7au_fixture_loads_and_stays_curated() -> None:
    fixture = _fixture()
    rows = fixture["valid_comparison_boundary_payload"]["comparison_result_rows"]  # type: ignore[index]
    invalid_inputs = fixture["invalid_inputs"]  # type: ignore[index]

    assert fixture["fixture_scope"] == "test_only_r7au"
    assert FIXTURE_PATH.stat().st_size < 30000
    assert len(rows) == 8
    assert Counter(row["agreement_status"] for row in rows) == {
        "VERIFIED": 1,
        "DISAGREED": 2,
        "AMBIGUOUS": 1,
        "MISSING_EVIDENCE": 2,
        "PARSE_SKIPPED": 1,
        "UNVERIFIED": 1,
    }
    assert {case["case_id"] for case in invalid_inputs} == {
        "invalid_raw_mineru_like_input",
        "invalid_raw_excel_like_input",
        "invalid_full_source_text_input",
    }


def test_r7au_valid_discrepancy_boundary_output_is_accepted() -> None:
    contract = _contract()

    assert set(contract) == {
        "review_queue_contract_items",
        "discrepancy_report_contract_rows",
        "blocked_delivery_contract_rows",
        "delivery_reaudit_contract_rows",
        "audit_contract",
    }
    assert len(contract["review_queue_contract_items"]) == 7
    assert len(contract["discrepancy_report_contract_rows"]) == 7
    assert len(contract["blocked_delivery_contract_rows"]) == 6
    assert len(contract["delivery_reaudit_contract_rows"]) == 1
    assert contract["audit_contract"]["contract_version"] == CONTRACT_VERSION


def test_r7au_only_boundary_output_shape_is_accepted() -> None:
    fixture = _fixture()

    with pytest.raises(ProductionBoundaryContractError, match="boundary output missing required fields"):
        build_production_boundary_review_queue_contract(fixture["valid_comparison_boundary_payload"])  # type: ignore[arg-type]


def test_r7au_invalid_raw_inputs_are_rejected() -> None:
    fixture = _fixture()

    for case in fixture["invalid_inputs"]:  # type: ignore[index]
        with pytest.raises(ProductionBoundaryContractError):
            build_production_boundary_review_queue_contract(case["payload"])


def test_r7au_verified_rows_do_not_bypass_clean_data_gate() -> None:
    contract = _contract()
    items = contract["review_queue_contract_items"]

    assert all(item["agreement_status"] != "VERIFIED" for item in items)
    assert all(item["clean_data_eligible"] is False for item in items)
    assert contract["audit_contract"]["verified_review_queue_contract_count"] == 0
    assert contract["audit_contract"]["clean_data_eligible_contract_count"] == 0


def test_r7au_non_verified_rows_become_review_queue_contract_items() -> None:
    contract = _contract()
    items = contract["review_queue_contract_items"]

    assert Counter(item["agreement_status"] for item in items) == {
        "DISAGREED": 2,
        "AMBIGUOUS": 1,
        "MISSING_EVIDENCE": 2,
        "PARSE_SKIPPED": 1,
        "UNVERIFIED": 1,
    }
    assert Counter(item["subqueue"] for item in items) == {
        "evidence_conflict_queue": 2,
        "evidence_ambiguity_queue": 1,
        "missing_evidence_queue": 2,
        "parse_schema_queue": 1,
        "partial_anchor_queue": 1,
    }
    assert all(set(CONTRACT_ITEM_FIELDS).issubset(item) for item in items)
    assert {item["created_from"] for item in items} == {"r7as_discrepancy_boundary_output"}


def test_r7au_unresolved_rows_are_blocked_from_clean_delivery() -> None:
    contract = _contract()
    blocked_ids = {row["source_row_id"] for row in contract["blocked_delivery_contract_rows"]}
    reaudit_rows = contract["delivery_reaudit_contract_rows"]

    assert "unresolved-action:R8" in blocked_ids
    assert "resolved-correction:R7" not in blocked_ids
    assert reaudit_rows == [
        {
            "review_item_id": next(
                item["review_item_id"]
                for item in contract["review_queue_contract_items"]
                if item["source_row_id"] == "resolved-correction:R7"
            ),
            "source_row_id": "resolved-correction:R7",
            "agreement_status": "DISAGREED",
            "review_status": "RESOLVED_CORRECTED",
            "reviewer_action": "CORRECT_VALUE",
            "delivery_gate_status": "requires_reaudit_before_clean_delivery",
            "delivery_clean_admitted": False,
            "requires_reaudit_before_clean_delivery": True,
            "run_id": "r7au_fixture_run_001",
            "adapter_version": "r7as_integration_boundary_test_only_v1",
            "contract_version": CONTRACT_VERSION,
            "created_from": "r7as_discrepancy_boundary_output",
        }
    ]


def test_r7au_discrepancy_rows_are_metadata_first_and_bounded() -> None:
    contract = _contract()
    serialized = json.dumps(contract, ensure_ascii=False)
    forbidden_keys = {"source_text", "full_source_text", "source_text_full", "raw_mineru_block", "raw_excel_row"}

    assert max(len(row["evidence_preview"]) for row in contract["discrepancy_report_contract_rows"]) <= 160
    for collection_name in (
        "review_queue_contract_items",
        "discrepancy_report_contract_rows",
        "blocked_delivery_contract_rows",
        "delivery_reaudit_contract_rows",
    ):
        assert all(forbidden_keys.isdisjoint(row) for row in contract[collection_name])
    assert "full source text must not be accepted" not in serialized
    assert "raw MinerU block must not enter" not in serialized


def test_r7au_audit_fields_and_hashes_are_stable() -> None:
    first = _contract()
    second = _contract()

    assert [item["contract_item_id"] for item in first["review_queue_contract_items"]] == [
        item["contract_item_id"] for item in second["review_queue_contract_items"]
    ]
    assert [item["review_item_id"] for item in first["review_queue_contract_items"]] == [
        item["review_item_id"] for item in second["review_queue_contract_items"]
    ]
    assert [item["audit_hash"] for item in first["review_queue_contract_items"]] == [
        item["audit_hash"] for item in second["review_queue_contract_items"]
    ]
    assert first["audit_contract"]["audit_contract_hash"] == second["audit_contract"]["audit_contract_hash"]
    assert first["audit_contract"]["run_id"] == "r7au_fixture_run_001"
    assert first["audit_contract"]["adapter_version"] == "r7as_integration_boundary_test_only_v1"
    assert first["audit_contract"]["input_file_hashes"] == {
        "datefac_excel": "sha256:r7au-datefac-fixture",
        "mineru_content_list_v2": "sha256:r7au-mineru-fixture",
    }


def test_r7au_unsupported_reviewer_actions_fail_closed() -> None:
    boundary_output = _boundary_output()
    modified = deepcopy(boundary_output)
    modified["review_queue_items"][0]["reviewer_decision"] = "AUTO_PROMOTE_TO_CLEAN"  # type: ignore[index]

    with pytest.raises(ProductionBoundaryContractError, match="unsupported reviewer action"):
        build_production_boundary_review_queue_contract(modified)


def test_r7au_explicit_future_policy_gate_is_required_for_clean_data_eligibility() -> None:
    default_contract = _contract()
    gated_contract = _contract(explicit_future_policy_gate=True)

    default_resolved = next(
        item for item in default_contract["review_queue_contract_items"] if item["source_row_id"] == "resolved-correction:R7"
    )
    gated_resolved = next(
        item for item in gated_contract["review_queue_contract_items"] if item["source_row_id"] == "resolved-correction:R7"
    )
    assert default_resolved["clean_data_eligible"] is False
    assert gated_resolved["clean_data_eligible"] is True
    assert gated_contract["audit_contract"]["clean_data_eligible_contract_count"] == 1
    assert all(row["delivery_clean_admitted"] is False for row in gated_contract["delivery_reaudit_contract_rows"])


def test_r7au_readiness_gates_remain_closed_and_fail_closed_if_changed() -> None:
    contract = _contract()
    boundary_output = _boundary_output()
    modified = deepcopy(boundary_output)
    modified["audit_metadata"]["readiness_gates"]["client_ready"] = True  # type: ignore[index]

    assert contract["audit_contract"]["readiness_gates"] == READINESS_GATES_CLOSED
    with pytest.raises(ProductionBoundaryContractError, match="readiness gate"):
        build_production_boundary_review_queue_contract(modified)


def test_r7au_helper_has_no_production_imports_or_heavy_parser_hooks() -> None:
    tree = ast.parse(HELPER_PATH.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.add(node.module or "")

    assert not any(module == "datefac_agent" or module.startswith("datefac_agent.") for module in imported_modules)
    assert not {"subprocess", "requests", "openai", "fitz", "pdfplumber", "pypdf"} & imported_modules
