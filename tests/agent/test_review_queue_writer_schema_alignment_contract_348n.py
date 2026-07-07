import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from tests.agent.review_queue_writer_dry_run_integration_boundary_348n import (
    TEST_ONLY_INTEGRATION_ENABLE_TOKEN,
    ReviewQueueWriterDryRunIntegrationBoundaryConfig,
    build_review_queue_writer_dry_run_integration_preview,
)
from tests.agent.review_queue_writer_schema_alignment_contract_348n import (
    FIELD_CLASSIFICATIONS,
    FUTURE_PERSISTENCE_PREVIEW_FIELDS,
    FUTURE_REVIEW_QUEUE_SCHEMA_VERSION,
    SCHEMA_ALIGNMENT_CONTRACT_VERSION,
    TEST_ONLY_SCHEMA_ALIGNMENT_ENABLE_TOKEN,
    ReviewQueueWriterSchemaAlignmentContractConfig,
    ReviewQueueWriterSchemaAlignmentContractError,
    build_review_queue_writer_schema_alignment_preview,
    field_classifications,
)

R7BI_FIXTURE_PATH = Path("tests/agent/fixtures/discrepancy_review_queue/r7bi_schema_alignment_contract_fixture.json")
R7BC_FIXTURE_PATH = Path("tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json")
MODULE_PATH = Path("tests/agent/review_queue_writer_schema_alignment_contract_348n.py")


def _fixture() -> dict:
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


def _adapter_candidate_for_case(case_id: str) -> dict:
    fixture = _fixture()
    r7bc_key = fixture["valid_cases"][case_id]["r7bc_fixture_key"]
    return deepcopy(_r7bc_fixture()[r7bc_key])


def _integration_output(case_id: str = "valid_mixed_review_records") -> dict:
    return build_review_queue_writer_dry_run_integration_preview(
        _adapter_candidate_for_case(case_id),
        _integration_config(),
    )


def _schema_alignment_preview(case_id: str = "valid_mixed_review_records") -> dict:
    return build_review_queue_writer_schema_alignment_preview(
        _integration_output(case_id),
        _schema_config(),
    )


def _negative_case(case_id: str) -> dict:
    cases = {case["case_id"]: case for case in _fixture()["negative_cases"]}
    return deepcopy(cases[case_id])


def _mutated_integration_output(case_id: str) -> dict:
    case = _negative_case(case_id)
    payload = _integration_output(case["base_case"])
    mutation = case["mutation"]
    _apply_mutation(payload, mutation["path"], mutation["action"], deepcopy(mutation.get("value")))
    if mutation["path"].startswith("writer_dry_run_preview."):
        payload["integration_summary"]["writer_preview_hash"] = _hash_json(payload["writer_dry_run_preview"])
    return payload


def _apply_mutation(payload: dict, path: str, action: str, value: object = None) -> None:
    current: object = payload
    parts = path.split(".")
    for part in parts[:-1]:
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    leaf = parts[-1]
    if isinstance(current, list):
        index = int(leaf)
        if action == "delete":
            del current[index]
        elif action == "set":
            current[index] = value
        else:
            raise AssertionError(f"unsupported fixture mutation action: {action}")
    else:
        if action == "delete":
            del current[leaf]
        elif action == "set":
            current[leaf] = value
        else:
            raise AssertionError(f"unsupported fixture mutation action: {action}")


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


def test_r7bi_fixture_is_small_curated_and_complete() -> None:
    fixture = _fixture()

    assert set(fixture) == {"schema_version", "fixture_scope", "valid_cases", "negative_cases", "wrong_layer_payloads"}
    assert fixture["schema_version"] == "r7bi_schema_alignment_contract_fixture_v1"
    assert set(fixture["valid_cases"]) == {
        "valid_mixed_review_records",
        "valid_unresolved_blocked_delivery",
        "valid_corrected_reaudit_required",
        "valid_verified_without_clean_gate",
    }
    assert {case["case_id"] for case in fixture["negative_cases"]} == {
        "missing_required_audit_fields",
        "missing_idempotency_key",
        "malformed_idempotency_key",
        "non_deterministic_timestamp_field",
        "full_source_text",
        "raw_extraction_payload",
        "clean_data_intent",
        "delivery_export_intent",
        "production_config",
        "readiness_open",
        "writer_preview_missing_dry_run_only",
        "test_only_config_leak",
    }
    assert R7BI_FIXTURE_PATH.stat().st_size < 20000


def test_r7bi_default_disabled_fails_closed() -> None:
    result = build_review_queue_writer_schema_alignment_preview(_integration_output())

    assert result["schema_alignment_status"] == "DISABLED"
    assert result["dry_run_only"] is True
    assert result["future_review_queue_record_previews"] == []
    assert result["schema_alignment_summary"]["future_preview_record_count"] == 0
    assert result["schema_alignment_summary"]["clean_data_write_count"] == 0
    assert result["schema_alignment_summary"]["database_write_count"] == 0


def test_r7bi_explicit_test_only_enable_required() -> None:
    with pytest.raises(ReviewQueueWriterSchemaAlignmentContractError, match="test-only schema alignment enable token"):
        build_review_queue_writer_schema_alignment_preview(
            _integration_output(),
            ReviewQueueWriterSchemaAlignmentContractConfig(enabled=True),
        )


def test_r7bi_valid_dry_run_integration_output_produces_schema_alignment_preview() -> None:
    result = _schema_alignment_preview()

    assert result["schema_alignment_status"] == "ENABLED_TEST_ONLY_SCHEMA_ALIGNMENT"
    assert result["dry_run_only"] is True
    assert result["schema_alignment_contract_version"] == SCHEMA_ALIGNMENT_CONTRACT_VERSION
    assert result["future_review_queue_schema_version"] == FUTURE_REVIEW_QUEUE_SCHEMA_VERSION
    assert len(result["future_review_queue_record_previews"]) == 2
    assert result["schema_alignment_summary"]["future_preview_record_count"] == 2
    assert result["schema_alignment_summary"]["clean_data_write_count"] == 0
    assert result["schema_alignment_summary"]["delivery_write_count"] == 0
    assert result["schema_alignment_summary"]["filesystem_write_count"] == 0
    assert result["schema_alignment_summary"]["database_write_count"] == 0


def test_r7bi_required_fields_are_classified() -> None:
    required_fields = {
        "run_id",
        "adapter_version",
        "contract_version",
        "integration_boundary_version",
        "writer_contract_version",
        "input_file_hashes",
        "source_file_hash",
        "review_item_id",
        "audit_hash",
        "idempotency_key",
        "metric_name",
        "period",
        "candidate_value",
        "normalized_candidate_value",
        "agreement_status",
        "review_status",
        "review_reason",
        "reviewer_action",
        "blocked_delivery_reason",
        "re_audit_required",
        "evidence_preview",
        "source_trace",
        "dry_run_only",
        "readiness_gates",
        "schema_version",
        "validation_errors",
    }
    categories = set(field_classifications().values())

    assert required_fields.issubset(FIELD_CLASSIFICATIONS)
    assert {
        "required_persistence_safe",
        "required_audit",
        "required_idempotency",
        "required_delivery_blocking",
        "required_reaudit",
        "optional_bounded_evidence",
        "normalized_derived",
        "dry_run_only",
        "test_only_only",
    }.issubset(categories)


def test_r7bi_future_preview_keeps_audit_idempotency_and_blocking_fields() -> None:
    result = _schema_alignment_preview()
    record = result["future_review_queue_record_previews"][0]

    assert set(FUTURE_PERSISTENCE_PREVIEW_FIELDS).issubset(record)
    assert record["schema_version"] == FUTURE_REVIEW_QUEUE_SCHEMA_VERSION
    assert record["review_item_id"]
    assert record["run_id"] == result["run_id"]
    assert record["input_file_hashes"] == result["input_file_hashes"]
    assert record["audit_hash"]
    assert record["idempotency_key"]
    assert record["record_payload_hash"]
    assert record["blocked_delivery_reason"]
    assert record["source_trace"]["matched_locator"]
    assert record["source_trace"]["matched_text_sha256"]


def test_r7bi_future_preview_excludes_test_only_config_and_forbidden_fields() -> None:
    result = _schema_alignment_preview()
    preview_keys = _walk_keys(result["future_review_queue_record_previews"])

    assert "dry_run_only" not in preview_keys
    assert "integration_boundary_version" not in preview_keys
    assert "validation_errors" not in preview_keys
    assert "test_only_enable_token" not in preview_keys
    assert "test_only_writer_config" not in preview_keys
    assert "writer_config" not in preview_keys
    assert "source_text" not in preview_keys
    assert "content_list_v2" not in preview_keys
    assert "raw_excel_row" not in preview_keys
    assert "clean_data_payload" not in preview_keys
    assert "formal_delivery_payload" not in preview_keys


@pytest.mark.parametrize(
    ("case_id", "match"),
    [
        ("missing_required_audit_fields", "run_id"),
        ("missing_idempotency_key", "idempotency_key"),
        ("malformed_idempotency_key", "idempotency_key"),
        ("non_deterministic_timestamp_field", "non-deterministic"),
        ("full_source_text", "forbidden field"),
        ("raw_extraction_payload", "forbidden field"),
        ("clean_data_intent", "clean_data"),
        ("delivery_export_intent", "forbidden field"),
        ("production_config", "forbidden field"),
        ("readiness_open", "readiness gate"),
        ("writer_preview_missing_dry_run_only", "dry_run_only"),
        ("test_only_config_leak", "forbidden field"),
    ],
)
def test_r7bi_negative_cases_fail_closed(case_id: str, match: str) -> None:
    with pytest.raises(ReviewQueueWriterSchemaAlignmentContractError, match=match):
        build_review_queue_writer_schema_alignment_preview(
            _mutated_integration_output(case_id),
            _schema_config(),
        )


def test_r7bi_direct_writer_preview_payload_is_rejected() -> None:
    direct_writer_preview = _integration_output()["writer_dry_run_preview"]

    with pytest.raises(ReviewQueueWriterSchemaAlignmentContractError, match="missing required fields"):
        build_review_queue_writer_schema_alignment_preview(direct_writer_preview, _schema_config())


def test_r7bi_adapter_only_payload_is_rejected() -> None:
    adapter_only_payload = _adapter_candidate_for_case("valid_mixed_review_records")

    with pytest.raises(ReviewQueueWriterSchemaAlignmentContractError, match="missing required fields"):
        build_review_queue_writer_schema_alignment_preview(adapter_only_payload, _schema_config())


def test_r7bi_normalization_is_deterministic() -> None:
    first = _schema_alignment_preview()
    second = _schema_alignment_preview()
    first_records = first["future_review_queue_record_previews"]
    second_records = second["future_review_queue_record_previews"]

    assert first_records == second_records
    assert [
        record["normalized_candidate_value"] for record in first_records
    ] == [
        record["candidate_value"].replace(",", "").strip() for record in first_records
    ]


def test_r7bi_idempotency_is_stable_across_retries() -> None:
    first = _schema_alignment_preview()
    second = _schema_alignment_preview()

    assert [
        record["idempotency_key"] for record in first["future_review_queue_record_previews"]
    ] == [
        record["idempotency_key"] for record in second["future_review_queue_record_previews"]
    ]
    assert first["schema_alignment_summary"]["schema_alignment_preview_hash"] == second["schema_alignment_summary"][
        "schema_alignment_preview_hash"
    ]


def test_r7bi_input_mutation_after_call_cannot_mutate_output() -> None:
    payload = _integration_output()
    result = build_review_queue_writer_schema_alignment_preview(payload, _schema_config())

    payload["integration_summary"]["input_file_hashes"]["datefac_excel"] = "sha256:mutated"
    payload["writer_dry_run_preview"]["review_queue_dry_run_records"][0]["evidence_preview"] = "mutated"

    record = result["future_review_queue_record_previews"][0]
    assert record["input_file_hashes"]["datefac_excel"] == "sha256:r7bc-datefac-fixture"
    assert record["evidence_preview"] != "mutated"


def test_r7bi_verified_does_not_become_clean_data_or_strong_evidence() -> None:
    result = _schema_alignment_preview("valid_verified_without_clean_gate")

    assert result["future_review_queue_record_previews"] == []
    assert result["schema_alignment_summary"]["verified_without_clean_gate_count"] == 1
    assert result["schema_alignment_summary"]["clean_data_write_count"] == 0
    assert result["schema_alignment_summary"]["delivery_write_count"] == 0
    assert result["schema_alignment_summary"]["boundary_flags"]["verified_auto_clean"] is False
    assert result["schema_alignment_summary"]["boundary_flags"]["verified_promotes_to_strong_evidence"] is False


def test_r7bi_non_verified_remains_review_bound() -> None:
    result = _schema_alignment_preview()
    records = result["future_review_queue_record_previews"]

    assert all(record["agreement_status"] != "VERIFIED" for record in records)
    assert all(record["clean_data_eligible"] is False for record in records)
    assert all(record["delivery_blocked"] is True for record in records)
    assert result["schema_alignment_summary"]["status_counts"] == {"DISAGREED": 1, "AMBIGUOUS": 1}


def test_r7bi_unresolved_retains_blocked_delivery_reason() -> None:
    result = _schema_alignment_preview("valid_unresolved_blocked_delivery")
    records = result["future_review_queue_record_previews"]

    assert len(records) == 1
    assert records[0]["agreement_status"] == "PARSE_SKIPPED"
    assert records[0]["blocked_delivery_reason"] == "unresolved_or_not_clean_data_eligible"
    assert records[0]["delivery_blocked"] is True


def test_r7bi_corrected_retains_reaudit_required_without_clean_delivery() -> None:
    result = _schema_alignment_preview("valid_corrected_reaudit_required")

    assert result["future_review_queue_record_previews"] == []
    assert result["schema_alignment_summary"]["re_audit_required_count"] == 1
    assert result["schema_alignment_summary"]["clean_data_write_count"] == 0
    assert result["schema_alignment_summary"]["delivery_write_count"] == 0


def test_r7bi_module_has_no_io_db_export_or_production_hook() -> None:
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
