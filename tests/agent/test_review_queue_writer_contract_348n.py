import ast
from copy import deepcopy
import json
from pathlib import Path

import pytest

from tests.agent.review_queue_writer_contract_348n import (
    REQUIRED_DRY_RUN_RECORD_FIELDS,
    TEST_ONLY_WRITER_ENABLE_TOKEN,
    ReviewQueueWriterContractConfig,
    ReviewQueueWriterContractError,
    build_review_queue_writer_dry_run_preview,
)

FIXTURE_PATH = Path("tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json")
MODULE_PATH = Path("tests/agent/review_queue_writer_contract_348n.py")


def _fixture() -> dict:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7bc"
    return payload


def _enabled_config() -> ReviewQueueWriterContractConfig:
    return ReviewQueueWriterContractConfig(
        enabled=True,
        test_only_enable_token=TEST_ONLY_WRITER_ENABLE_TOKEN,
    )


def _valid_payload() -> dict:
    return deepcopy(_fixture()["valid_adapter_candidate_payload"])


def test_r7bc_fixture_is_small_curated_and_complete() -> None:
    fixture = _fixture()
    expected_keys = {
        "schema_version",
        "fixture_scope",
        "valid_adapter_candidate_payload",
        "candidate_payload_with_verified_only",
        "candidate_payload_with_non_verified_review_bound_rows",
        "candidate_payload_with_unresolved_blocked_delivery_rows",
        "candidate_payload_with_corrected_reaudit_required_row",
        "invalid_raw_mineru_like_payload",
        "invalid_raw_excel_like_payload",
        "invalid_full_source_text_payload",
        "invalid_readiness_open_payload",
        "invalid_clean_data_write_payload",
        "invalid_missing_audit_metadata_payload",
        "invalid_duplicate_idempotency_collision_payload",
    }

    assert set(fixture) == expected_keys
    assert FIXTURE_PATH.stat().st_size < 60000
    assert "content_list_v2" in fixture["invalid_raw_mineru_like_payload"]
    assert "raw_excel_row" in fixture["invalid_raw_excel_like_payload"]
    assert "source_text" in fixture["invalid_full_source_text_payload"]


def test_r7bc_default_disabled_writer_fails_closed() -> None:
    result = build_review_queue_writer_dry_run_preview(_valid_payload())

    assert result["writer_status"] == "DISABLED"
    assert result["dry_run_only"] is True
    assert result["review_queue_dry_run_records"] == []
    assert result["dry_run_summary"]["clean_data_write_count"] == 0
    assert result["dry_run_summary"]["delivery_write_count"] == 0
    assert result["dry_run_summary"]["filesystem_write_count"] == 0
    assert result["dry_run_summary"]["database_write_count"] == 0


def test_r7bc_explicit_test_only_enable_required() -> None:
    with pytest.raises(ReviewQueueWriterContractError, match="test-only writer enable token"):
        build_review_queue_writer_dry_run_preview(
            _valid_payload(),
            ReviewQueueWriterContractConfig(enabled=True),
        )


def test_r7bc_valid_candidate_output_produces_dry_run_preview_only() -> None:
    result = build_review_queue_writer_dry_run_preview(_valid_payload(), _enabled_config())

    assert result["writer_status"] == "ENABLED_TEST_ONLY_DRY_RUN"
    assert result["dry_run_only"] is True
    assert len(result["review_queue_dry_run_records"]) == 2
    assert result["dry_run_summary"]["would_insert_count"] == 2
    assert result["dry_run_summary"]["clean_data_write_count"] == 0
    assert result["dry_run_summary"]["delivery_write_count"] == 0
    assert result["dry_run_summary"]["filesystem_write_count"] == 0
    assert result["dry_run_summary"]["database_write_count"] == 0
    assert result["dry_run_summary"]["boundary_flags"]["dry_run_preview_only"] is True
    assert result["dry_run_summary"]["boundary_flags"]["writes_review_queue"] is False


def test_r7bc_preview_records_contain_required_review_queue_fields() -> None:
    result = build_review_queue_writer_dry_run_preview(_valid_payload(), _enabled_config())
    record = result["review_queue_dry_run_records"][0]

    assert set(REQUIRED_DRY_RUN_RECORD_FIELDS).issubset(record)
    assert record["dry_run_only"] is True
    assert record["dry_run_action"] == "WOULD_INSERT"
    assert record["agreement_status"] in {"DISAGREED", "AMBIGUOUS"}
    assert record["source_trace"]["matched_locator"]
    assert record["source_trace"]["matched_text_sha256"]
    assert record["clean_data_write_count"] == 0
    assert record["delivery_write_count"] == 0


def test_r7bc_preview_records_are_not_clean_data_records() -> None:
    result = build_review_queue_writer_dry_run_preview(_valid_payload(), _enabled_config())

    assert all(record["agreement_status"] != "VERIFIED" for record in result["review_queue_dry_run_records"])
    assert all(record["dry_run_only"] is True for record in result["review_queue_dry_run_records"])
    assert result["dry_run_summary"]["verified_without_clean_gate_count"] == 0
    assert result["dry_run_summary"]["clean_data_write_count"] == 0


def test_r7bc_verified_only_input_does_not_create_clean_persistence() -> None:
    payload = deepcopy(_fixture()["candidate_payload_with_verified_only"])
    result = build_review_queue_writer_dry_run_preview(payload, _enabled_config())

    assert result["review_queue_dry_run_records"] == []
    assert result["dry_run_summary"]["candidate_count"] == 0
    assert result["dry_run_summary"]["verified_without_clean_gate_count"] == 1
    assert result["dry_run_summary"]["reaudit_required_count"] == 1
    assert result["dry_run_summary"]["clean_data_write_count"] == 0
    assert result["dry_run_summary"]["delivery_write_count"] == 0


def test_r7bc_non_verified_rows_produce_review_bound_preview_records() -> None:
    payload = deepcopy(_fixture()["candidate_payload_with_non_verified_review_bound_rows"])
    result = build_review_queue_writer_dry_run_preview(payload, _enabled_config())

    assert [record["agreement_status"] for record in result["review_queue_dry_run_records"]] == [
        "MISSING_EVIDENCE",
        "UNVERIFIED",
    ]
    assert result["dry_run_summary"]["status_counts"] == {"MISSING_EVIDENCE": 1, "UNVERIFIED": 1}
    assert all(record["blocked_delivery_reason"] for record in result["review_queue_dry_run_records"])


def test_r7bc_unresolved_rows_keep_blocked_delivery_reason() -> None:
    payload = deepcopy(_fixture()["candidate_payload_with_unresolved_blocked_delivery_rows"])
    result = build_review_queue_writer_dry_run_preview(payload, _enabled_config())
    record = result["review_queue_dry_run_records"][0]

    assert record["agreement_status"] == "PARSE_SKIPPED"
    assert record["blocked_delivery_reason"] == "unresolved_or_not_clean_data_eligible"
    assert result["dry_run_summary"]["blocked_delivery_count"] == 1


def test_r7bc_corrected_rows_remain_reaudit_required() -> None:
    payload = deepcopy(_fixture()["candidate_payload_with_corrected_reaudit_required_row"])
    result = build_review_queue_writer_dry_run_preview(payload, _enabled_config())

    assert result["review_queue_dry_run_records"] == []
    assert result["dry_run_summary"]["reaudit_required_count"] == 1
    assert result["dry_run_summary"]["clean_data_write_count"] == 0
    assert result["dry_run_summary"]["delivery_write_count"] == 0


def test_r7bc_idempotency_key_is_deterministic() -> None:
    first = build_review_queue_writer_dry_run_preview(_valid_payload(), _enabled_config())
    second = build_review_queue_writer_dry_run_preview(_valid_payload(), _enabled_config())

    assert first == second
    assert [record["idempotency_key"] for record in first["review_queue_dry_run_records"]] == [
        record["idempotency_key"] for record in second["review_queue_dry_run_records"]
    ]
    assert [record["record_payload_hash"] for record in first["review_queue_dry_run_records"]] == [
        record["record_payload_hash"] for record in second["review_queue_dry_run_records"]
    ]


def test_r7bc_retry_same_input_yields_duplicate_skip_plan_without_writes() -> None:
    first = build_review_queue_writer_dry_run_preview(_valid_payload(), _enabled_config())
    existing_hashes = {
        record["idempotency_key"]: record["record_payload_hash"]
        for record in first["review_queue_dry_run_records"]
    }

    retry = build_review_queue_writer_dry_run_preview(
        _valid_payload(),
        _enabled_config(),
        existing_record_hashes=existing_hashes,
    )

    assert [record["idempotency_key"] for record in retry["review_queue_dry_run_records"]] == list(existing_hashes)
    assert {record["dry_run_action"] for record in retry["review_queue_dry_run_records"]} == {"WOULD_SKIP_DUPLICATE"}
    assert retry["dry_run_summary"]["would_insert_count"] == 0
    assert retry["dry_run_summary"]["duplicate_plan_count"] == 2
    assert retry["dry_run_summary"]["database_write_count"] == 0


def test_r7bc_input_mutation_after_call_cannot_mutate_output() -> None:
    payload = _valid_payload()
    result = build_review_queue_writer_dry_run_preview(payload, _enabled_config())

    payload["review_queue_candidate_items"][0]["evidence_preview"] = "mutated after dry-run"
    payload["audit_contract"]["input_file_hashes"]["datefac_excel"] = "sha256:mutated"

    record = result["review_queue_dry_run_records"][0]
    assert record["evidence_preview"] != "mutated after dry-run"
    assert record["input_file_hashes"]["datefac_excel"] == "sha256:r7bc-datefac-fixture"


@pytest.mark.parametrize(
    ("fixture_key", "match"),
    [
        ("invalid_raw_mineru_like_payload", "forbidden field"),
        ("invalid_raw_excel_like_payload", "forbidden field"),
        ("invalid_full_source_text_payload", "forbidden field"),
        ("invalid_readiness_open_payload", "readiness gate"),
        ("invalid_clean_data_write_payload", "clean_data"),
        ("invalid_missing_audit_metadata_payload", "missing required"),
    ],
)
def test_r7bc_invalid_inputs_fail_closed(fixture_key: str, match: str) -> None:
    with pytest.raises(ReviewQueueWriterContractError, match=match):
        build_review_queue_writer_dry_run_preview(
            deepcopy(_fixture()[fixture_key]),
            _enabled_config(),
        )


def test_r7bc_schema_mismatch_rejected() -> None:
    payload = _valid_payload()
    payload["adapter_status"] = "DISABLED"

    with pytest.raises(ReviewQueueWriterContractError, match="enabled test-only"):
        build_review_queue_writer_dry_run_preview(payload, _enabled_config())

    payload = _valid_payload()
    payload["unexpected_field"] = "not allowed"

    with pytest.raises(ReviewQueueWriterContractError, match="unexpected fields"):
        build_review_queue_writer_dry_run_preview(payload, _enabled_config())


def test_r7bc_verified_review_queue_candidate_rejected() -> None:
    payload = _valid_payload()
    payload["review_queue_candidate_items"][0]["agreement_status"] = "VERIFIED"
    payload["audit_contract"]["review_queue_candidate_status_counts"] = {"VERIFIED": 1, "AMBIGUOUS": 1}

    with pytest.raises(ReviewQueueWriterContractError, match="non-VERIFIED"):
        build_review_queue_writer_dry_run_preview(payload, _enabled_config())


def test_r7bc_duplicate_idempotency_collision_rejected() -> None:
    case = deepcopy(_fixture()["invalid_duplicate_idempotency_collision_payload"])

    with pytest.raises(ReviewQueueWriterContractError, match="idempotency collision"):
        build_review_queue_writer_dry_run_preview(
            case["adapter_candidate_output"],
            _enabled_config(),
            existing_record_hashes=case["existing_record_hashes"],
        )


def test_r7bc_full_source_text_absent_from_serialized_preview() -> None:
    result = build_review_queue_writer_dry_run_preview(_valid_payload(), _enabled_config())

    forbidden_keys = {"source_text", "full_source_text", "raw_source_text", "content_list_v2", "raw_excel_row"}

    def walk(value: object) -> None:
        if isinstance(value, dict):
            assert not (set(value) & forbidden_keys)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(result)


def test_r7bc_writer_contract_module_has_no_io_or_heavy_hooks() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
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
