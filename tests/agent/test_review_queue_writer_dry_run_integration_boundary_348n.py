import ast
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

import pytest

from tests.agent import review_queue_writer_dry_run_integration_boundary_348n as boundary
from tests.agent.review_queue_writer_contract_348n import (
    TEST_ONLY_WRITER_ENABLE_TOKEN,
    WRITER_CONTRACT_VERSION,
    ReviewQueueWriterContractConfig,
    build_review_queue_writer_dry_run_preview,
)
from tests.agent.review_queue_writer_dry_run_integration_boundary_348n import (
    TEST_ONLY_INTEGRATION_ENABLE_TOKEN,
    ReviewQueueWriterDryRunIntegrationBoundaryConfig,
    ReviewQueueWriterDryRunIntegrationBoundaryError,
    build_review_queue_writer_dry_run_integration_preview,
)

FIXTURE_PATH = Path("tests/agent/fixtures/discrepancy_review_queue/r7be_dry_run_integration_boundary_fixture.json")
MODULE_PATH = Path("tests/agent/review_queue_writer_dry_run_integration_boundary_348n.py")


def _fixture() -> dict:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7be"
    return payload


def _enabled_config() -> ReviewQueueWriterDryRunIntegrationBoundaryConfig:
    return ReviewQueueWriterDryRunIntegrationBoundaryConfig(
        enabled=True,
        test_only_enable_token=TEST_ONLY_INTEGRATION_ENABLE_TOKEN,
    )


def _writer_config() -> ReviewQueueWriterContractConfig:
    return ReviewQueueWriterContractConfig(
        enabled=True,
        test_only_enable_token=TEST_ONLY_WRITER_ENABLE_TOKEN,
    )


def _candidate_payload(case_key: str = "valid_adapter_candidate_to_writer_preview") -> dict:
    fixture = _fixture()
    case = fixture[case_key]
    shared = fixture["shared"]
    review_items = [_review_candidate(row_key, fixture=fixture) for row_key in case["review_rows"]]
    blocked_rows = [_blocked_delivery_candidate(item, shared=shared) for item in review_items]
    reaudit_rows = [_delivery_reaudit_candidate(row_key, fixture=fixture) for row_key in case["reaudit_rows"]]
    status_counts = Counter(item["agreement_status"] for item in review_items)
    audit_contract = {
        "adapter_status": "ENABLED_TEST_ONLY",
        "enabled": True,
        "contract_version": shared["adapter_contract_version"],
        "created_from": shared["created_from"],
        "source_run_id": shared["run_id"],
        "run_id": shared["run_id"],
        "adapter_version": shared["adapter_version"],
        "input_file_hashes": deepcopy(shared["input_file_hashes"]),
        "source_audit_metadata_hash": "sha256-r7be-source-audit-metadata",
        "review_queue_candidate_count": len(review_items),
        "review_queue_candidate_status_counts": dict(status_counts),
        "discrepancy_report_candidate_count": 0,
        "blocked_delivery_candidate_count": len(blocked_rows),
        "delivery_reaudit_candidate_count": len(reaudit_rows),
        "verified_without_clean_gate_count": case["verified_without_clean_gate_count"],
        "clean_data_admitted_count": 0,
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
        "boundary_flags": {
            "production_hook": False,
            "writes_review_queue": False,
            "writes_clean_data": False,
            "writes_delivery": False,
            "writes_filesystem": False,
            "writes_database": False,
            "verified_auto_clean": False,
            "verified_promotes_to_strong_evidence": False,
            "full_source_text_serialized": False,
        },
        "adapter_audit_hash": f"sha256-r7be-adapter-audit-{case_key}",
    }
    return {
        "adapter_status": "ENABLED_TEST_ONLY",
        "review_queue_candidate_items": review_items,
        "discrepancy_report_candidate_rows": [],
        "blocked_delivery_candidate_rows": blocked_rows,
        "delivery_reaudit_candidate_rows": reaudit_rows,
        "audit_contract": audit_contract,
    }


def _review_candidate(row_key: str, *, fixture: dict) -> dict:
    shared = fixture["shared"]
    template = fixture["review_row_templates"][row_key]
    return {
        "review_item_id": template["review_item_id"],
        "source_document_id": shared["source_document_id"],
        "source_row_id": template["source_row_id"],
        "candidate_metric_name": template["candidate_metric_name"],
        "candidate_period": template["candidate_period"],
        "candidate_value": template["candidate_value"],
        "candidate_unit": template["candidate_unit"],
        "agreement_status": template["agreement_status"],
        "subqueue": template["subqueue"],
        "risk_reason": template["risk_reason"],
        "severity": template["severity"],
        "review_status": "OPEN",
        "reviewer_action": "",
        "clean_data_eligible": False,
        "delivery_blocked": True,
        "evidence_preview": template["evidence_preview"],
        "evidence_preview_sha256": template["evidence_preview_sha256"],
        "matched_locator": template["matched_locator"],
        "matched_text_sha256": template["matched_text_sha256"],
        "run_id": shared["run_id"],
        "adapter_version": shared["adapter_version"],
        "input_file_hashes": deepcopy(shared["input_file_hashes"]),
        "audit_hash": template["audit_hash"],
        "adapter_contract_version": shared["adapter_contract_version"],
        "adapter_item_id": f"r7be-adapter-{row_key}",
        "created_from": shared["created_from"],
    }


def _blocked_delivery_candidate(item: dict, *, shared: dict) -> dict:
    return {
        "review_item_id": item["review_item_id"],
        "source_row_id": item["source_row_id"],
        "agreement_status": item["agreement_status"],
        "blocked_reason": "unresolved_or_not_clean_data_eligible",
        "delivery_blocked": True,
        "run_id": shared["run_id"],
        "adapter_version": shared["adapter_version"],
        "adapter_contract_version": shared["adapter_contract_version"],
    }


def _delivery_reaudit_candidate(row_key: str, *, fixture: dict) -> dict:
    shared = fixture["shared"]
    template = fixture["reaudit_row_templates"][row_key]
    return {
        "source_row_id": template["source_row_id"],
        "agreement_status": template["agreement_status"],
        "delivery_gate_status": template["delivery_gate_status"],
        "delivery_clean_admitted": False,
        "requires_reaudit_before_clean_delivery": template["requires_reaudit_before_clean_delivery"],
        "run_id": shared["run_id"],
        "adapter_version": shared["adapter_version"],
        "adapter_contract_version": shared["adapter_contract_version"],
    }


def _invalid_payload(case_key: str) -> dict:
    fixture = _fixture()
    case = fixture[case_key]
    if "derive_from" not in case:
        return deepcopy(case)
    payload = _candidate_payload(case["derive_from"])
    _set_path(payload, case["set_path"], case["value"])
    return payload


def _set_path(payload: dict, path: str, value: object) -> None:
    current: object = payload
    parts = path.split(".")
    for part in parts[:-1]:
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    if isinstance(current, list):
        current[int(parts[-1])] = value
    else:
        current[parts[-1]] = value


def test_r7be_fixture_is_small_curated_and_complete() -> None:
    fixture = _fixture()
    expected_keys = {
        "schema_version",
        "fixture_scope",
        "shared",
        "valid_adapter_candidate_to_writer_preview",
        "valid_mixed_verified_and_non_verified_candidate",
        "valid_unresolved_blocked_delivery_candidate",
        "valid_corrected_reaudit_required_candidate",
        "review_row_templates",
        "reaudit_row_templates",
        "invalid_raw_mineru_like_payload",
        "invalid_raw_excel_like_payload",
        "invalid_raw_parser_like_payload",
        "invalid_direct_user_payload",
        "invalid_full_source_text_payload",
        "invalid_readiness_open_payload",
        "invalid_schema_mismatch_payload",
        "invalid_clean_data_intent_payload",
        "invalid_empty_payload",
        "invalid_minimal_adapter_like_payload",
        "invalid_direct_writer_preview_payload",
    }

    assert set(fixture) == expected_keys
    assert FIXTURE_PATH.stat().st_size < 20000
    assert "content_list_v2" in fixture["invalid_raw_mineru_like_payload"]
    assert "raw_excel_row" in fixture["invalid_raw_excel_like_payload"]
    assert "parser_output" in fixture["invalid_raw_parser_like_payload"]
    assert "source_text" in fixture["invalid_full_source_text_payload"]
    assert fixture["invalid_empty_payload"] == {}
    assert fixture["invalid_minimal_adapter_like_payload"] == {"adapter_status": "ENABLED_TEST_ONLY"}


def test_r7be_default_disabled_integration_fails_closed_without_writer_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("writer must not be called when integration boundary is disabled")

    monkeypatch.setattr(boundary, "build_review_queue_writer_dry_run_preview", fail_if_called)
    result = build_review_queue_writer_dry_run_integration_preview(_candidate_payload())

    assert result["integration_status"] == "DISABLED"
    assert result["dry_run_only"] is True
    assert result["writer_dry_run_preview"] is None
    assert result["integration_summary"]["writer_called"] is False
    assert result["integration_summary"]["database_write_count"] == 0
    assert result["integration_summary"]["filesystem_write_count"] == 0


def test_r7be_explicit_test_only_enable_required() -> None:
    with pytest.raises(ReviewQueueWriterDryRunIntegrationBoundaryError, match="test-only integration enable token"):
        build_review_queue_writer_dry_run_integration_preview(
            _candidate_payload(),
            ReviewQueueWriterDryRunIntegrationBoundaryConfig(enabled=True),
        )


def test_r7bf_missing_explicit_token_rejects_before_writer_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("writer dry-run must not be called without explicit integration token")

    monkeypatch.setattr(boundary, "build_review_queue_writer_dry_run_preview", fail_if_called)
    with pytest.raises(ReviewQueueWriterDryRunIntegrationBoundaryError, match="test-only integration enable token"):
        build_review_queue_writer_dry_run_integration_preview(
            _candidate_payload(),
            ReviewQueueWriterDryRunIntegrationBoundaryConfig(enabled=True),
        )


def test_r7bf_invalid_explicit_token_rejects_before_writer_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("writer dry-run must not be called with invalid integration token")

    monkeypatch.setattr(boundary, "build_review_queue_writer_dry_run_preview", fail_if_called)
    with pytest.raises(ReviewQueueWriterDryRunIntegrationBoundaryError, match="test-only integration enable token"):
        build_review_queue_writer_dry_run_integration_preview(
            _candidate_payload(),
            ReviewQueueWriterDryRunIntegrationBoundaryConfig(
                enabled=True,
                test_only_enable_token="R7BE_INVALID_OR_PRODUCTION_TOKEN",
            ),
        )


def test_r7bf_disabled_path_does_not_validate_or_call_writer_for_malformed_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("writer dry-run must not be called when integration boundary is disabled")

    monkeypatch.setattr(boundary, "build_review_queue_writer_dry_run_preview", fail_if_called)
    result = build_review_queue_writer_dry_run_integration_preview(_invalid_payload("invalid_raw_mineru_like_payload"))

    assert result["integration_status"] == "DISABLED"
    assert result["dry_run_only"] is True
    assert result["writer_dry_run_preview"] is None
    assert result["integration_summary"]["writer_called"] is False
    assert result["integration_summary"]["clean_data_write_count"] == 0
    assert result["integration_summary"]["database_write_count"] == 0


def test_r7bf_valid_path_constructs_only_test_writer_config(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _candidate_payload()
    expected_writer_preview = build_review_queue_writer_dry_run_preview(payload, _writer_config())
    observed_configs: list[ReviewQueueWriterContractConfig] = []

    def fake_writer(
        adapter_candidate_output: dict,
        config: ReviewQueueWriterContractConfig,
        **kwargs: object,
    ) -> dict:
        observed_configs.append(config)
        assert adapter_candidate_output == payload
        assert kwargs["existing_record_hashes"] is None
        assert config.enabled is True
        assert config.contract_version == WRITER_CONTRACT_VERSION
        assert config.test_only_enable_token == TEST_ONLY_WRITER_ENABLE_TOKEN
        return deepcopy(expected_writer_preview)

    monkeypatch.setattr(boundary, "build_review_queue_writer_dry_run_preview", fake_writer)
    result = build_review_queue_writer_dry_run_integration_preview(payload, _enabled_config())

    assert len(observed_configs) == 1
    assert result["writer_dry_run_preview"] == expected_writer_preview
    assert result["integration_summary"]["writer_called"] is True


def test_r7be_valid_adapter_candidate_reaches_test_only_writer_preview() -> None:
    payload = _candidate_payload()
    result = build_review_queue_writer_dry_run_integration_preview(payload, _enabled_config())
    direct_writer_preview = build_review_queue_writer_dry_run_preview(payload, _writer_config())

    assert result["integration_status"] == "ENABLED_TEST_ONLY_DRY_RUN"
    assert result["dry_run_only"] is True
    assert result["writer_dry_run_preview"] == direct_writer_preview
    assert result["integration_summary"]["writer_called"] is True
    assert result["integration_summary"]["review_queue_dry_run_record_count"] == 2
    assert result["integration_summary"]["would_insert_count"] == 2
    assert result["integration_summary"]["clean_data_write_count"] == 0
    assert result["integration_summary"]["delivery_write_count"] == 0
    assert result["integration_summary"]["filesystem_write_count"] == 0
    assert result["integration_summary"]["database_write_count"] == 0
    assert result["integration_summary"]["export_write_count"] == 0


def test_r7be_writer_preview_records_are_preserved_conservatively() -> None:
    payload = _candidate_payload()
    result = build_review_queue_writer_dry_run_integration_preview(payload, _enabled_config())
    direct_writer_preview = build_review_queue_writer_dry_run_preview(payload, _writer_config())

    assert result["writer_dry_run_preview"]["review_queue_dry_run_records"] == direct_writer_preview[
        "review_queue_dry_run_records"
    ]
    assert [
        record["review_item_id"] for record in result["writer_dry_run_preview"]["review_queue_dry_run_records"]
    ] == ["r7be-review-disagreed", "r7be-review-ambiguous"]
    assert all(
        record["agreement_status"] in {"DISAGREED", "AMBIGUOUS"}
        for record in result["writer_dry_run_preview"]["review_queue_dry_run_records"]
    )


def test_r7be_adapter_metadata_passes_through_unchanged_and_is_deep_copied() -> None:
    payload = _candidate_payload()
    result = build_review_queue_writer_dry_run_integration_preview(payload, _enabled_config())

    assert result["adapter_audit_contract"] == payload["audit_contract"]
    assert result["integration_summary"]["run_id"] == payload["audit_contract"]["run_id"]
    assert result["integration_summary"]["adapter_version"] == payload["audit_contract"]["adapter_version"]
    assert result["integration_summary"]["input_file_hashes"] == payload["audit_contract"]["input_file_hashes"]
    assert result["integration_summary"]["adapter_audit_hash"] == payload["audit_contract"]["adapter_audit_hash"]

    payload["audit_contract"]["input_file_hashes"]["datefac_excel"] = "sha256:mutated"
    payload["review_queue_candidate_items"][0]["evidence_preview"] = "mutated"

    assert result["adapter_audit_contract"]["input_file_hashes"]["datefac_excel"] == "sha256:r7be-datefac-fixture"
    assert result["writer_dry_run_preview"]["review_queue_dry_run_records"][0]["evidence_preview"] != "mutated"


def test_r7be_idempotency_is_stable_end_to_end() -> None:
    first = build_review_queue_writer_dry_run_integration_preview(_candidate_payload(), _enabled_config())
    second = build_review_queue_writer_dry_run_integration_preview(_candidate_payload(), _enabled_config())

    assert first == second
    first_keys = [record["idempotency_key"] for record in first["writer_dry_run_preview"]["review_queue_dry_run_records"]]
    second_keys = [record["idempotency_key"] for record in second["writer_dry_run_preview"]["review_queue_dry_run_records"]]
    assert first_keys == second_keys
    assert first["integration_summary"]["integration_envelope_hash"] == second["integration_summary"]["integration_envelope_hash"]


def test_r7be_retry_same_input_can_pass_duplicate_skip_plan_without_writes() -> None:
    first = build_review_queue_writer_dry_run_integration_preview(_candidate_payload(), _enabled_config())
    existing_hashes = {
        record["idempotency_key"]: record["record_payload_hash"]
        for record in first["writer_dry_run_preview"]["review_queue_dry_run_records"]
    }

    retry = build_review_queue_writer_dry_run_integration_preview(
        _candidate_payload(),
        _enabled_config(),
        existing_record_hashes=existing_hashes,
    )

    assert {record["dry_run_action"] for record in retry["writer_dry_run_preview"]["review_queue_dry_run_records"]} == {
        "WOULD_SKIP_DUPLICATE"
    }
    assert retry["integration_summary"]["would_insert_count"] == 0
    assert retry["integration_summary"]["duplicate_plan_count"] == 2
    assert retry["integration_summary"]["database_write_count"] == 0


@pytest.mark.parametrize(
    ("fixture_key", "match"),
    [
        ("invalid_raw_mineru_like_payload", "forbidden field"),
        ("invalid_raw_excel_like_payload", "forbidden field"),
        ("invalid_raw_parser_like_payload", "forbidden field"),
        ("invalid_direct_user_payload", "missing required"),
        ("invalid_full_source_text_payload", "forbidden field"),
        ("invalid_readiness_open_payload", "readiness gate"),
        ("invalid_schema_mismatch_payload", "enabled test-only"),
        ("invalid_clean_data_intent_payload", "clean_data"),
        ("invalid_empty_payload", "missing required"),
        ("invalid_minimal_adapter_like_payload", "missing required"),
        ("invalid_direct_writer_preview_payload", "missing required"),
    ],
)
def test_r7be_invalid_inputs_rejected_before_writer_call(
    fixture_key: str,
    match: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("writer dry-run must not be called for invalid input")

    monkeypatch.setattr(boundary, "build_review_queue_writer_dry_run_preview", fail_if_called)
    with pytest.raises(ReviewQueueWriterDryRunIntegrationBoundaryError, match=match):
        build_review_queue_writer_dry_run_integration_preview(
            _invalid_payload(fixture_key),
            _enabled_config(),
        )


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (lambda preview: preview.update({"writer_status": "ENABLED_PRODUCTION"}), "test-only dry-run"),
        (lambda preview: preview.update({"dry_run_only": False}), "dry-run only"),
        (lambda preview: preview["dry_run_summary"].update({"writer_status": "ENABLED_PRODUCTION"}), "test-only dry-run"),
        (lambda preview: preview["dry_run_summary"].update({"database_write_count": 1}), "database_write_count"),
        (lambda preview: preview["dry_run_summary"]["boundary_flags"].update({"production_hook": True}), "forbidden"),
        (lambda preview: preview["review_queue_dry_run_records"][0].update({"dry_run_only": False}), "dry-run only"),
        (lambda preview: preview["review_queue_dry_run_records"][0].update({"agreement_status": "VERIFIED"}), "review-bound"),
    ],
)
def test_r7bf_unsafe_or_production_like_writer_preview_is_blocked(
    mutation: object,
    match: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _candidate_payload()
    unsafe_preview = build_review_queue_writer_dry_run_preview(payload, _writer_config())
    mutation(unsafe_preview)

    def fake_writer(*args: object, **kwargs: object) -> dict:
        return deepcopy(unsafe_preview)

    monkeypatch.setattr(boundary, "build_review_queue_writer_dry_run_preview", fake_writer)
    with pytest.raises(ReviewQueueWriterDryRunIntegrationBoundaryError, match=match):
        build_review_queue_writer_dry_run_integration_preview(payload, _enabled_config())


def test_r7be_verified_rows_do_not_become_clean_data() -> None:
    result = build_review_queue_writer_dry_run_integration_preview(
        _candidate_payload("valid_mixed_verified_and_non_verified_candidate"),
        _enabled_config(),
    )

    assert [record["agreement_status"] for record in result["writer_dry_run_preview"]["review_queue_dry_run_records"]] == [
        "MISSING_EVIDENCE"
    ]
    assert result["integration_summary"]["verified_without_clean_gate_count"] == 1
    assert result["integration_summary"]["reaudit_required_count"] == 1
    assert result["integration_summary"]["clean_data_write_count"] == 0
    assert result["integration_summary"]["delivery_write_count"] == 0
    assert result["integration_summary"]["boundary_flags"]["verified_auto_clean"] is False
    assert result["integration_summary"]["boundary_flags"]["verified_promotes_to_strong_evidence"] is False


def test_r7be_non_verified_rows_remain_review_bound() -> None:
    result = build_review_queue_writer_dry_run_integration_preview(_candidate_payload(), _enabled_config())
    records = result["writer_dry_run_preview"]["review_queue_dry_run_records"]

    assert all(record["agreement_status"] != "VERIFIED" for record in records)
    assert all(record["dry_run_only"] is True for record in records)
    assert all(record["blocked_delivery_reason"] for record in records)
    assert result["integration_summary"]["status_counts"] == {"DISAGREED": 1, "AMBIGUOUS": 1}


def test_r7be_unresolved_rows_retain_blocked_delivery_reason() -> None:
    result = build_review_queue_writer_dry_run_integration_preview(
        _candidate_payload("valid_unresolved_blocked_delivery_candidate"),
        _enabled_config(),
    )
    records = result["writer_dry_run_preview"]["review_queue_dry_run_records"]

    assert len(records) == 1
    assert records[0]["agreement_status"] == "PARSE_SKIPPED"
    assert records[0]["blocked_delivery_reason"] == "unresolved_or_not_clean_data_eligible"
    assert result["integration_summary"]["blocked_delivery_count"] == 1


def test_r7be_corrected_rows_retain_reaudit_requirement_without_clean_delivery() -> None:
    result = build_review_queue_writer_dry_run_integration_preview(
        _candidate_payload("valid_corrected_reaudit_required_candidate"),
        _enabled_config(),
    )

    assert result["writer_dry_run_preview"]["review_queue_dry_run_records"] == []
    assert result["integration_summary"]["review_queue_dry_run_record_count"] == 0
    assert result["integration_summary"]["reaudit_required_count"] == 1
    assert result["integration_summary"]["clean_data_write_count"] == 0
    assert result["integration_summary"]["delivery_write_count"] == 0


def test_r7be_full_source_text_absent_from_serialized_integration_output() -> None:
    result = build_review_queue_writer_dry_run_integration_preview(_candidate_payload(), _enabled_config())
    forbidden_keys = {"source_text", "full_source_text", "raw_source_text", "content_list_v2", "raw_excel_row", "parser_output"}

    def walk(value: object) -> None:
        if isinstance(value, dict):
            assert not (set(value) & forbidden_keys)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(result)


def test_r7be_integration_boundary_module_has_no_io_db_export_or_production_hooks() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "datefac_agent",
        "fitz",
        "openai",
        "os",
        "pathlib",
        "pdfplumber",
        "pypdf",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
    }
    forbidden_calls = {
        "connect",
        "mkdir",
        "open",
        "remove",
        "rename",
        "replace",
        "rmdir",
        "unlink",
        "write",
        "write_text",
    }

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
