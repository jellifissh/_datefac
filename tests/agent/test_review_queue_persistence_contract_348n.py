import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from tests.agent.review_queue_persistence_contract_348n import (
    PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION,
    PERSISTENCE_CONTRACT_VERSION,
    REQUIRED_PERSISTENCE_CANDIDATE_FIELDS,
    TEST_ONLY_PERSISTENCE_ENABLE_TOKEN,
    ReviewQueuePersistenceContractConfig,
    ReviewQueuePersistenceContractError,
    build_review_queue_persistence_candidate_batch,
)
from tests.agent.review_queue_writer_dry_run_integration_boundary_348n import (
    TEST_ONLY_INTEGRATION_ENABLE_TOKEN,
    ReviewQueueWriterDryRunIntegrationBoundaryConfig,
    build_review_queue_writer_dry_run_integration_preview,
)
from tests.agent.review_queue_writer_schema_alignment_contract_348n import (
    TEST_ONLY_SCHEMA_ALIGNMENT_ENABLE_TOKEN,
    ReviewQueueWriterSchemaAlignmentContractConfig,
    build_review_queue_writer_schema_alignment_preview,
)

R7BL_FIXTURE_PATH = Path("tests/agent/fixtures/discrepancy_review_queue/r7bl_persistence_contract_fixture.json")
R7BI_FIXTURE_PATH = Path("tests/agent/fixtures/discrepancy_review_queue/r7bi_schema_alignment_contract_fixture.json")
R7BC_FIXTURE_PATH = Path("tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json")
MODULE_PATH = Path("tests/agent/review_queue_persistence_contract_348n.py")


def _fixture() -> dict:
    payload = json.loads(R7BL_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7bl"
    return payload


def _r7bi_fixture() -> dict:
    payload = json.loads(R7BI_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7bi"
    return payload


def _r7bc_fixture() -> dict:
    payload = json.loads(R7BC_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7bc"
    return payload


def _integration_config() -> ReviewQueueWriterDryRunIntegrationBoundaryConfig:
    return ReviewQueueWriterDryRunIntegrationBoundaryConfig(
        enabled=True,
        test_only_enable_token=TEST_ONLY_INTEGRATION_ENABLE_TOKEN,
    )


def _schema_config() -> ReviewQueueWriterSchemaAlignmentContractConfig:
    return ReviewQueueWriterSchemaAlignmentContractConfig(
        enabled=True,
        test_only_enable_token=TEST_ONLY_SCHEMA_ALIGNMENT_ENABLE_TOKEN,
    )


def _persistence_config() -> ReviewQueuePersistenceContractConfig:
    return ReviewQueuePersistenceContractConfig(
        enabled=True,
        test_only_enable_token=TEST_ONLY_PERSISTENCE_ENABLE_TOKEN,
    )


def _schema_alignment_preview(case_id: str = "valid_schema_alignment_preview_mixed_records") -> dict:
    valid_case = _fixture()["valid_cases"][case_id]
    r7bi_case = _r7bi_fixture()["valid_cases"][valid_case["r7bi_case"]]
    adapter_payload = deepcopy(_r7bc_fixture()[r7bi_case["r7bc_fixture_key"]])
    integration_output = build_review_queue_writer_dry_run_integration_preview(
        adapter_payload,
        _integration_config(),
    )
    preview = build_review_queue_writer_schema_alignment_preview(
        integration_output,
        _schema_config(),
    )
    mutation = valid_case.get("mutation")
    if mutation:
        _apply_mutation(preview, mutation)
    return preview


def _direct_integration_output() -> dict:
    adapter_payload = deepcopy(_r7bc_fixture()["valid_adapter_candidate_payload"])
    return build_review_queue_writer_dry_run_integration_preview(adapter_payload, _integration_config())


def _payload_for_negative_case(case_id: str) -> dict:
    case = _negative_case(case_id)
    payload_kind = case.get("payload_kind")
    if payload_kind == "minimal_schema_like":
        return {"schema_alignment_status": "ENABLED_TEST_ONLY_SCHEMA_ALIGNMENT"}
    if payload_kind == "dry_run_integration_output":
        return _direct_integration_output()
    if payload_kind == "writer_preview_output":
        return _direct_integration_output()["writer_dry_run_preview"]
    if payload_kind == "adapter_candidate_output":
        return deepcopy(_r7bc_fixture()["valid_adapter_candidate_payload"])
    if payload_kind == "raw_mineru_output":
        return {"content_list_v2": [[{"type": "text", "text": "raw mineru text"}]]}
    if payload_kind == "raw_excel_workbook_data":
        return {"workbook_sheets": [{"cells": [["raw", "excel"]]}]}
    if payload_kind == "raw_parser_payload":
        return {"raw_parser_payload": {"pages": [{"text": "raw parser"}]}}
    if payload_kind == "raw_llm_vlm_response":
        return {"llm_response": "raw llm", "vlm_response": "raw vlm"}
    if payload_kind == "user_direct_persistence_candidate":
        return {"review_queue_persistence_candidate_batch": [{"review_item_id": "direct-user-row"}]}
    payload = _schema_alignment_preview(case["base_case"])
    _apply_mutation(payload, case["mutation"])
    return payload


def _negative_case(case_id: str) -> dict:
    cases = {case["case_id"]: case for case in _fixture()["negative_cases"]}
    return deepcopy(cases[case_id])


def _apply_mutation(payload: dict, mutation: dict) -> None:
    action = mutation["action"]
    if action == "set_many":
        record = payload["future_review_queue_record_previews"][mutation["record_index"]]
        record.update(mutation["values"])
        return
    if action == "copy":
        _set_path(payload, mutation["to_path"], deepcopy(_get_path(payload, mutation["from_path"])))
        return
    if action == "delete":
        _delete_path(payload, mutation["path"])
        return
    if action == "set":
        _set_path(payload, mutation["path"], mutation["value"])
        return
    raise AssertionError(f"unsupported mutation action: {action}")


def _get_path(payload: dict, path: str) -> object:
    current: object = payload
    for part in path.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def _set_path(payload: dict, path: str, value: object) -> None:
    parts = path.split(".")
    current: object = payload
    for part in parts[:-1]:
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current.setdefault(part, {})
    last = parts[-1]
    if isinstance(current, list):
        current[int(last)] = value
    else:
        current[last] = value


def _delete_path(payload: dict, path: str) -> None:
    parts = path.split(".")
    current: object = payload
    for part in parts[:-1]:
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    last = parts[-1]
    if isinstance(current, list):
        del current[int(last)]
    else:
        del current[last]


def _hash_json(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _walk_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for child in value.values():
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_walk_keys(child))
    return keys


def test_r7bl_fixture_is_small_curated_and_complete() -> None:
    fixture = _fixture()

    assert set(fixture) == {"schema_version", "fixture_scope", "valid_cases", "negative_cases"}
    assert fixture["schema_version"] == "r7bl_persistence_contract_fixture_v1"
    assert set(fixture["valid_cases"]) == {
        "valid_schema_alignment_preview_mixed_records",
        "valid_unresolved_blocked_delivery_record",
        "valid_corrected_reaudit_required_record",
    }
    assert {case["case_id"] for case in fixture["negative_cases"]} == {
        "invalid_default_disabled",
        "invalid_missing_test_persistence_flag",
        "invalid_schema_alignment_bypass",
        "invalid_direct_dry_run_integration_output",
        "invalid_direct_writer_preview_output",
        "invalid_direct_adapter_candidate_output",
        "invalid_missing_review_item_id",
        "invalid_missing_run_id",
        "invalid_missing_audit_hash",
        "invalid_missing_idempotency_key",
        "invalid_malformed_idempotency_key",
        "invalid_missing_hash_identity",
        "invalid_unresolved_without_blocked_delivery_reason",
        "invalid_corrected_without_re_audit_required",
        "invalid_duplicate_idempotency_key",
        "invalid_full_source_text",
        "invalid_unbounded_evidence_text",
        "invalid_raw_mineru_output",
        "invalid_raw_excel_workbook_data",
        "invalid_raw_parser_payload",
        "invalid_raw_llm_vlm_response",
        "invalid_clean_data_write_intent",
        "invalid_delivery_export_intent",
        "invalid_production_writer_config",
        "invalid_readiness_open",
        "invalid_user_direct_persistence_candidate",
    }
    assert R7BL_FIXTURE_PATH.stat().st_size < 25000


def test_r7bl_default_disabled_fails_closed() -> None:
    result = build_review_queue_persistence_candidate_batch(_schema_alignment_preview())

    assert result["persistence_status"] == "DISABLED"
    assert result["in_memory_only"] is True
    assert result["review_queue_persistence_candidate_batch"] == []
    assert result["persistence_summary"]["candidate_count"] == 0
    assert result["persistence_summary"]["database_write_count"] == 0
    assert result["persistence_summary"]["boundary_flags"]["writes_review_queue"] is False


def test_r7bl_explicit_test_only_persistence_flag_required() -> None:
    with pytest.raises(ReviewQueuePersistenceContractError, match="test-only persistence enable token"):
        build_review_queue_persistence_candidate_batch(
            _schema_alignment_preview(),
            ReviewQueuePersistenceContractConfig(enabled=True),
        )


def test_r7bl_valid_schema_alignment_preview_returns_in_memory_candidate_batch() -> None:
    result = build_review_queue_persistence_candidate_batch(_schema_alignment_preview(), _persistence_config())

    assert result["persistence_status"] == "ENABLED_TEST_ONLY_PERSISTENCE_CANDIDATE"
    assert result["in_memory_only"] is True
    assert result["persistence_candidate_only"] is True
    assert result["persistence_contract_version"] == PERSISTENCE_CONTRACT_VERSION
    assert result["persistence_candidate_batch_schema_version"] == PERSISTENCE_CANDIDATE_BATCH_SCHEMA_VERSION
    assert len(result["review_queue_persistence_candidate_batch"]) == 2
    assert result["persistence_summary"]["candidate_count"] == 2
    assert result["persistence_summary"]["clean_data_write_count"] == 0
    assert result["persistence_summary"]["delivery_write_count"] == 0
    assert result["persistence_summary"]["filesystem_write_count"] == 0
    assert result["persistence_summary"]["database_write_count"] == 0
    assert result["persistence_summary"]["export_write_count"] == 0


def test_r7bl_valid_unresolved_and_corrected_cases_remain_blocked_or_reaudit_required() -> None:
    unresolved = build_review_queue_persistence_candidate_batch(
        _schema_alignment_preview("valid_unresolved_blocked_delivery_record"),
        _persistence_config(),
    )
    corrected = build_review_queue_persistence_candidate_batch(
        _schema_alignment_preview("valid_corrected_reaudit_required_record"),
        _persistence_config(),
    )
    corrected_records = [
        record
        for record in corrected["review_queue_persistence_candidate_batch"]
        if record["reviewer_action"] == "CORRECT_VALUE"
    ]

    assert unresolved["review_queue_persistence_candidate_batch"][0]["agreement_status"] == "PARSE_SKIPPED"
    assert unresolved["review_queue_persistence_candidate_batch"][0]["blocked_delivery_reason"]
    assert len(corrected_records) == 1
    assert corrected_records[0]["re_audit_required"] is True
    assert corrected["persistence_summary"]["database_write_count"] == 0


def test_r7bl_required_persistence_candidate_fields_are_present() -> None:
    result = build_review_queue_persistence_candidate_batch(_schema_alignment_preview(), _persistence_config())
    record = result["review_queue_persistence_candidate_batch"][0]

    assert set(REQUIRED_PERSISTENCE_CANDIDATE_FIELDS) == set(record)
    assert record["review_item_id"]
    assert record["run_id"] == result["run_id"]
    assert record["source_file_hash"]
    assert record["input_file_hashes"] == result["input_file_hashes"]
    assert record["audit_hash"]
    assert record["idempotency_key"]
    assert record["record_payload_hash"]
    assert record["created_by_system"] == "r7bl_test_only_persistence_contract"


def test_r7bl_future_candidate_excludes_forbidden_fields_and_test_only_config() -> None:
    result = build_review_queue_persistence_candidate_batch(_schema_alignment_preview(), _persistence_config())
    keys = _walk_keys(result["review_queue_persistence_candidate_batch"])

    assert not keys & {
        "source_text",
        "full_source_text",
        "raw_source_text",
        "content_list_v2",
        "raw_excel_row",
        "clean_data",
        "clean_data_eligible",
        "delivery_payload",
        "export_payload",
        "production_writer_config",
        "test_only_enable_token",
        "database_id",
        "migration_id",
        "connection_string",
        "table_name",
    }
    assert "TEST_ONLY_PERSISTENCE_ENABLE_TOKEN" not in json.dumps(result, ensure_ascii=False)


@pytest.mark.parametrize(
    "case_id",
    [
        "invalid_schema_alignment_bypass",
        "invalid_direct_dry_run_integration_output",
        "invalid_direct_writer_preview_output",
        "invalid_direct_adapter_candidate_output",
        "invalid_missing_review_item_id",
        "invalid_missing_run_id",
        "invalid_missing_audit_hash",
        "invalid_missing_idempotency_key",
        "invalid_malformed_idempotency_key",
        "invalid_missing_hash_identity",
        "invalid_unresolved_without_blocked_delivery_reason",
        "invalid_corrected_without_re_audit_required",
        "invalid_duplicate_idempotency_key",
        "invalid_full_source_text",
        "invalid_unbounded_evidence_text",
        "invalid_raw_mineru_output",
        "invalid_raw_excel_workbook_data",
        "invalid_raw_parser_payload",
        "invalid_raw_llm_vlm_response",
        "invalid_clean_data_write_intent",
        "invalid_delivery_export_intent",
        "invalid_production_writer_config",
        "invalid_readiness_open",
        "invalid_user_direct_persistence_candidate",
    ],
)
def test_r7bl_negative_cases_fail_closed(case_id: str) -> None:
    case = _negative_case(case_id)

    with pytest.raises(ReviewQueuePersistenceContractError, match=case["expected_error"]):
        build_review_queue_persistence_candidate_batch(_payload_for_negative_case(case_id), _persistence_config())


def test_r7bl_batch_failure_returns_no_partial_candidate_batch() -> None:
    with pytest.raises(ReviewQueuePersistenceContractError, match="duplicate idempotency_key") as error:
        build_review_queue_persistence_candidate_batch(
            _payload_for_negative_case("invalid_duplicate_idempotency_key"),
            _persistence_config(),
        )

    assert "review_queue_persistence_candidate_batch" not in str(error.value)


def test_r7bl_record_payload_hash_idempotency_and_ordering_are_deterministic() -> None:
    first = build_review_queue_persistence_candidate_batch(_schema_alignment_preview(), _persistence_config())
    second = build_review_queue_persistence_candidate_batch(_schema_alignment_preview(), _persistence_config())
    reversed_preview = _schema_alignment_preview()
    reversed_preview["future_review_queue_record_previews"] = list(reversed(reversed_preview["future_review_queue_record_previews"]))
    reversed_output = build_review_queue_persistence_candidate_batch(reversed_preview, _persistence_config())

    assert first == second
    assert first == reversed_output
    records = first["review_queue_persistence_candidate_batch"]
    assert [record["review_item_id"] for record in records] == sorted(record["review_item_id"] for record in records)
    for record in records:
        expected_hash = _hash_json({key: value for key, value in record.items() if key != "record_payload_hash"})
        assert record["record_payload_hash"] == expected_hash


def test_r7bl_input_mutation_after_call_cannot_mutate_output() -> None:
    preview = _schema_alignment_preview()
    result = build_review_queue_persistence_candidate_batch(preview, _persistence_config())

    preview["future_review_queue_record_previews"][0]["evidence_preview"] = "mutated after persistence contract"
    preview["input_file_hashes"]["datefac_excel"] = "mutated"

    record = result["review_queue_persistence_candidate_batch"][0]
    assert record["evidence_preview"] != "mutated after persistence contract"
    assert result["input_file_hashes"]["datefac_excel"] == "sha256:r7bc-datefac-fixture"


def test_r7bl_verified_rows_do_not_promote_or_enter_clean_data() -> None:
    verified_preview = build_review_queue_writer_schema_alignment_preview(
        build_review_queue_writer_dry_run_integration_preview(
            deepcopy(_r7bc_fixture()["candidate_payload_with_verified_only"]),
            _integration_config(),
        ),
        _schema_config(),
    )
    result = build_review_queue_persistence_candidate_batch(verified_preview, _persistence_config())

    assert result["review_queue_persistence_candidate_batch"] == []
    assert result["persistence_summary"]["candidate_count"] == 0
    assert result["persistence_summary"]["clean_data_write_count"] == 0
    assert result["persistence_summary"]["boundary_flags"]["verified_promotes_to_strong_evidence"] is False
    assert result["persistence_summary"]["boundary_flags"]["verified_auto_clean"] is False

    promoted = _schema_alignment_preview()
    promoted["future_review_queue_record_previews"][0]["evidence_level"] = "STRONG_EVIDENCE"
    with pytest.raises(ReviewQueuePersistenceContractError, match="STRONG_EVIDENCE"):
        build_review_queue_persistence_candidate_batch(promoted, _persistence_config())


def test_r7bl_non_verified_rows_remain_review_bound_and_delivery_blocked() -> None:
    result = build_review_queue_persistence_candidate_batch(_schema_alignment_preview(), _persistence_config())

    assert {record["agreement_status"] for record in result["review_queue_persistence_candidate_batch"]} == {
        "DISAGREED",
        "AMBIGUOUS",
    }
    assert all(record["blocked_delivery_reason"] for record in result["review_queue_persistence_candidate_batch"])
    assert result["persistence_summary"]["boundary_flags"]["writes_delivery"] is False
    assert result["persistence_summary"]["boundary_flags"]["writes_review_queue"] is False
    assert result["persistence_summary"]["readiness_gates"]["production_ready"] is False


def test_r7bl_persistence_contract_module_has_no_io_db_export_or_production_hook() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "datefac_agent",
        "os",
        "pathlib",
        "sqlite3",
        "sqlalchemy",
        "psycopg2",
        "pymysql",
        "subprocess",
        "requests",
        "httpx",
        "pandas",
        "openpyxl",
        "mineru",
        "fitz",
        "pdfplumber",
        "pypdf",
    }
    forbidden_calls = {
        "open",
        "write",
        "write_text",
        "writelines",
        "mkdir",
        "connect",
        "execute",
        "commit",
        "to_excel",
        "to_csv",
        "dump",
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
