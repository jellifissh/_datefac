from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from tests.agent.review_queue_local_test_db_adapter_boundary_348n import (
    BOUNDARY_MODE,
    DEFAULT_PREVIEW_LIMIT,
    LOCAL_TEST_DB_ADAPTER_BOUNDARY_VERSION,
    PLANNED_DISABLED_STATUS,
    READINESS_GATES_CLOSED,
    TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
    VALID_LOCAL_TEST_ENVIRONMENT,
    LocalTestDBAdapterActivationError,
    LocalTestDBAdapterBoundary,
    LocalTestDBAdapterBoundaryError,
    LocalTestDBAdapterCandidateError,
    LocalTestDBAdapterConfig,
    make_disabled_local_test_db_adapter_boundary,
    transaction_idempotency_policy,
    validate_local_test_db_activation_request,
    validate_local_test_db_candidate_batch,
)

MODULE_PATH = Path("tests/agent/review_queue_local_test_db_adapter_boundary_348n.py")


def _valid_config() -> LocalTestDBAdapterConfig:
    return LocalTestDBAdapterConfig(
        enabled=True,
        test_only=True,
        environment=VALID_LOCAL_TEST_ENVIRONMENT,
        db_selection="sqlite_memory",
        dsn=":memory:",
        test_only_enable_token=TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
    )


def _valid_candidate(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "review_item_id": "review:r7bx:1",
        "idempotency_key": "a" * 64,
        "record_payload_hash": "b" * 64,
        "agreement_status": "DISAGREED",
        "evidence_preview": "bounded preview only",
        "source_trace": {
            "source_document_id": "doc:r7bx",
            "matched_locator": "page:1:block:2",
            "matched_text_sha256": "c" * 64,
        },
    }
    candidate.update(overrides)
    return candidate


def test_r7bx_boundary_module_imports_without_db_storage_network_dependencies() -> None:
    boundary = make_disabled_local_test_db_adapter_boundary()

    assert isinstance(boundary, LocalTestDBAdapterBoundary)
    assert boundary.boundary_version == LOCAL_TEST_DB_ADAPTER_BOUNDARY_VERSION
    assert boundary.boundary_mode == BOUNDARY_MODE
    assert boundary.metadata()["database_connection_opened"] is False


def test_r7bx_boundary_is_test_only_by_path_name_and_metadata() -> None:
    boundary = make_disabled_local_test_db_adapter_boundary()
    metadata = boundary.metadata()

    assert "tests/agent" in MODULE_PATH.as_posix()
    assert "test_only" in BOUNDARY_MODE
    assert metadata["test_only"] is True
    assert metadata["boundary_status"] == PLANNED_DISABLED_STATUS
    assert metadata["readiness_gates"] == READINESS_GATES_CLOSED


def test_r7bx_activation_fails_closed_by_default() -> None:
    with pytest.raises(LocalTestDBAdapterActivationError, match="planned-disabled") as error:
        validate_local_test_db_activation_request(LocalTestDBAdapterConfig())

    _assert_error_is_generic(str(error.value))


def test_r7bx_explicit_valid_activation_returns_planned_disabled_result() -> None:
    result = validate_local_test_db_activation_request(_valid_config())

    assert result["activation_request_validated"] is True
    assert result["planned_adapter_only"] is True
    assert result["database_connection_opened"] is False
    assert result["schema_created"] is False
    assert result["migration_created"] is False
    assert result["table_created"] is False
    assert result["database_write_count"] == 0
    assert result["future_activation_status"] == PLANNED_DISABLED_STATUS
    assert result["readiness_gates"] == READINESS_GATES_CLOSED


def test_r7bx_activation_cannot_be_driven_only_by_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATEFAC_LOCAL_TEST_DB_ENABLED", "true")
    monkeypatch.setenv("DATEFAC_LOCAL_TEST_DB_DSN", "postgresql://prod.example.invalid/review")

    with pytest.raises(LocalTestDBAdapterActivationError):
        validate_local_test_db_activation_request(LocalTestDBAdapterConfig())
    with pytest.raises(LocalTestDBAdapterActivationError):
        validate_local_test_db_activation_request(
            {
                "enabled": True,
                "test_only": True,
                "environment": "local_test",
                "db_selection": "sqlite_memory",
                "dsn": ":memory:",
                "activation_source": "environment",
                "test_only_enable_token": TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
            }
        )


@pytest.mark.parametrize(
    "config",
    [
        LocalTestDBAdapterConfig(
            enabled=True,
            environment=VALID_LOCAL_TEST_ENVIRONMENT,
            db_selection="sqlite_memory",
            dsn=":memory:",
            test_only_enable_token=TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
        ),
        LocalTestDBAdapterConfig(
            enabled=True,
            test_only=True,
            db_selection="sqlite_memory",
            dsn=":memory:",
            test_only_enable_token=TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
        ),
        LocalTestDBAdapterConfig(
            enabled=True,
            test_only=True,
            environment="production",
            db_selection="sqlite_memory",
            dsn=":memory:",
            test_only_enable_token=TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
        ),
        LocalTestDBAdapterConfig(
            enabled=True,
            test_only=True,
            environment="staging",
            db_selection="sqlite_memory",
            dsn=":memory:",
            test_only_enable_token=TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
        ),
        LocalTestDBAdapterConfig(
            enabled=True,
            test_only=True,
            environment=VALID_LOCAL_TEST_ENVIRONMENT,
            db_selection="sqlite_memory",
            dsn="postgresql://user:secret@prod.example.invalid/review",
            test_only_enable_token=TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
        ),
        LocalTestDBAdapterConfig(
            enabled=True,
            test_only=True,
            environment=VALID_LOCAL_TEST_ENVIRONMENT,
            db_selection="sqlite_memory",
            dsn=":memory:",
            activation_source="schema_alignment_preview",
            test_only_enable_token=TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
        ),
        LocalTestDBAdapterConfig(
            enabled=True,
            test_only=True,
            environment=VALID_LOCAL_TEST_ENVIRONMENT,
            db_selection="sqlite_memory",
            dsn=":memory:",
            activation_source="repository_skeleton_factory",
            test_only_enable_token=TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
        ),
    ],
)
def test_r7bx_activation_rejects_missing_or_unsafe_config(config: LocalTestDBAdapterConfig) -> None:
    before = deepcopy(config)

    with pytest.raises(LocalTestDBAdapterActivationError) as error:
        validate_local_test_db_activation_request(config)

    assert config == before
    _assert_error_is_generic(str(error.value))


@pytest.mark.parametrize(
    "config",
    [
        {"endpoint": "https://prod.example.invalid/review"},
        {"connection_string": "Server=prod;Password=secret"},
        {"db_secret": "secret-password"},
        {"output_path": "D:/unsafe/review_queue.db"},
        {"file_path": "D:/unsafe/review_queue.db"},
        {"table_name": "review_queue_items"},
        {"production_writer_config": {"enabled": True}},
        {"readiness_override": {"production_ready": True}},
        {"clean_data_intent": True},
        {"delivery_export_intent": True},
        {"host": "10.0.0.10"},
        {"schema_alignment_preview": {"activation": True}},
        {"repository_skeleton_factory_output": {"status": "disabled"}},
    ],
)
def test_r7bx_activation_rejects_production_config_without_echo(config: dict[str, object]) -> None:
    payload = {
        "enabled": True,
        "test_only": True,
        "environment": VALID_LOCAL_TEST_ENVIRONMENT,
        "db_selection": "sqlite_memory",
        "dsn": ":memory:",
        "test_only_enable_token": TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
        **config,
    }
    before = deepcopy(payload)

    with pytest.raises(LocalTestDBAdapterActivationError) as error:
        validate_local_test_db_activation_request(payload)

    assert payload == before
    _assert_error_is_generic(str(error.value))


def test_r7bx_boundary_write_batch_remains_unavailable_even_after_valid_shapes() -> None:
    boundary = make_disabled_local_test_db_adapter_boundary()

    with pytest.raises(LocalTestDBAdapterBoundaryError, match="planned-disabled") as error:
        boundary.write_batch([_valid_candidate()], run_id="run:r7bx")

    _assert_error_is_generic(str(error.value))


def test_r7bx_candidate_validation_accepts_bounded_metadata_only_for_future_design() -> None:
    candidates = [_valid_candidate()]
    before = deepcopy(candidates)

    result = validate_local_test_db_candidate_batch(candidates)

    assert candidates == before
    assert result["candidate_validation_status"] == "VALIDATED_FOR_FUTURE_LOCAL_TEST_DB_ONLY"
    assert result["candidate_count"] == 1
    assert result["batch_atomic_by_contract"] is True
    assert result["no_partial_success_by_contract"] is True
    assert result["stores_records"] is False
    assert result["database_write_count"] == 0
    assert result["readiness_gates"] == READINESS_GATES_CLOSED


@pytest.mark.parametrize(
    "field_name, field_value",
    [
        ("source_text", "full source text"),
        ("full_source_text", "full source text"),
        ("raw_mineru_payload", {"content_list_v2": "raw mineru"}),
        ("raw_excel_payload", {"sheet": "raw excel"}),
        ("raw_parser_payload", {"page": "raw parser"}),
        ("raw_ocr_payload", "raw ocr"),
        ("raw_llm_payload", "raw llm"),
        ("raw_vlm_payload", "raw vlm"),
        ("unbounded_evidence_text", "x" * 1000),
    ],
)
def test_r7bx_candidate_validation_rejects_raw_payloads_and_full_text(
    field_name: str,
    field_value: object,
) -> None:
    candidates = [_valid_candidate(**{field_name: field_value})]
    before = deepcopy(candidates)

    with pytest.raises(LocalTestDBAdapterCandidateError) as error:
        validate_local_test_db_candidate_batch(candidates)

    assert candidates == before
    assert field_name not in str(error.value)
    _assert_error_is_generic(str(error.value))


@pytest.mark.parametrize(
    "field_name, field_value",
    [
        ("clean_data_payload", {"row": "clean"}),
        ("delivery_payload", {"export": True}),
        ("export_payload", {"path": "D:/unsafe/export.csv"}),
        ("readiness_override", {"client_ready": True}),
        ("caller_supplied_db_row", {"id": 1}),
        ("committed_db_receipt", {"database_write_count": 1}),
        ("local_test_db_adapter_state", {"records": ["do not store"]}),
        ("production_timestamp_override", "2026-07-09T00:00:00Z"),
    ],
)
def test_r7bx_candidate_validation_rejects_stateful_or_boundary_bypass_fields(
    field_name: str,
    field_value: object,
) -> None:
    with pytest.raises(LocalTestDBAdapterCandidateError) as error:
        validate_local_test_db_candidate_batch([_valid_candidate(**{field_name: field_value})])

    assert field_name not in str(error.value)
    _assert_error_is_generic(str(error.value))


def test_r7bx_candidate_validation_rejects_unbounded_evidence_preview() -> None:
    with pytest.raises(LocalTestDBAdapterCandidateError):
        validate_local_test_db_candidate_batch([_valid_candidate(evidence_preview="x" * (DEFAULT_PREVIEW_LIMIT + 1))])


@pytest.mark.parametrize(
    "candidate",
    [
        {"idempotency_key": "a" * 64, "record_payload_hash": "b" * 64},
        {"review_item_id": "review:r7bx", "record_payload_hash": "b" * 64},
        {"review_item_id": "review:r7bx", "idempotency_key": "a" * 64},
        _valid_candidate(record_payload_hash="bad-hash"),
    ],
)
def test_r7bx_candidate_validation_rejects_missing_identity_or_bad_hash(candidate: dict[str, object]) -> None:
    with pytest.raises(LocalTestDBAdapterCandidateError):
        validate_local_test_db_candidate_batch([candidate])


def test_r7bx_invalid_batch_fails_as_a_whole_and_does_not_mutate_inputs() -> None:
    candidates = [
        _valid_candidate(),
        _valid_candidate(review_item_id="review:r7bx:2", idempotency_key="d" * 64, raw_llm_payload="raw llm"),
    ]
    before = deepcopy(candidates)

    with pytest.raises(LocalTestDBAdapterCandidateError) as error:
        validate_local_test_db_candidate_batch(candidates)

    assert candidates == before
    _assert_error_is_generic(str(error.value))


def test_r7bx_duplicate_idempotency_and_review_conflicts_fail_closed() -> None:
    with pytest.raises(LocalTestDBAdapterCandidateError):
        validate_local_test_db_candidate_batch(
            [
                _valid_candidate(),
                _valid_candidate(review_item_id="review:r7bx:2"),
            ]
        )
    with pytest.raises(LocalTestDBAdapterCandidateError):
        validate_local_test_db_candidate_batch(
            [
                _valid_candidate(),
                _valid_candidate(idempotency_key="d" * 64),
            ]
        )


def test_r7bx_transaction_and_idempotency_policy_is_explicit_and_fail_closed() -> None:
    policy = transaction_idempotency_policy()

    assert policy["batch_atomic_by_contract"] is True
    assert policy["no_partial_success_by_default"] is True
    assert policy["invalid_row_rejects_entire_batch"] is True
    assert policy["same_idempotency_key_same_record_payload_hash"] == "planned_deterministic_retry_no_duplicate"
    assert policy["same_idempotency_key_different_record_payload_hash"] == "planned_conflict_fail_closed"
    assert policy["same_review_item_id_conflicting_identity"] == "planned_conflict_fail_closed"
    assert policy["record_payload_hash_required"] is True
    assert policy["silent_duplicate_insert_allowed"] is False


def test_r7bx_error_messages_do_not_echo_payloads_secrets_dsns_or_paths() -> None:
    with pytest.raises(LocalTestDBAdapterActivationError) as activation_error:
        validate_local_test_db_activation_request(
            {
                "enabled": True,
                "test_only": True,
                "environment": "production",
                "db_selection": "sqlite_memory",
                "dsn": "postgresql://user:secret@prod.example.invalid/review",
                "test_only_enable_token": TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
                "output_path": "D:/unsafe/review.db",
            }
        )
    with pytest.raises(LocalTestDBAdapterCandidateError) as candidate_error:
        validate_local_test_db_candidate_batch(
            [
                _valid_candidate(
                    source_text="sensitive full source",
                    raw_mineru_payload={"secret": "raw mineru"},
                )
            ]
        )

    _assert_error_is_generic(str(activation_error.value))
    _assert_error_is_generic(str(candidate_error.value))


def test_r7bx_source_has_no_forbidden_imports_calls_or_side_effect_markers() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    source_lower = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_import_roots = {
        "asyncpg",
        "boto3",
        "botocore",
        "datefac_agent",
        "docker",
        "httpx",
        "mysql",
        "openai",
        "os",
        "pathlib",
        "psycopg",
        "psycopg2",
        "pymysql",
        "redis",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "executescript",
        "fetchone",
        "fetchall",
        "open",
        "write",
        "write_text",
        "writelines",
        "mkdir",
        "remove",
        "rename",
        "replace",
        "rmdir",
        "unlink",
        "request",
        "post",
        "put",
        "patch",
        "delete",
    }

    for marker in (
        "create table",
        "insert into",
        "select ",
        "update ",
        "delete from",
        "drop table",
        "alter table",
        "docker",
    ):
        assert marker not in source_lower

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
                assert alias.name not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
            assert node.module not in forbidden_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def test_r7bx_readiness_gates_remain_closed_and_receipt_is_metadata_only() -> None:
    metadata = make_disabled_local_test_db_adapter_boundary().metadata()
    metadata["readiness_gates"]["client_ready"] = True
    fresh_metadata = make_disabled_local_test_db_adapter_boundary().metadata()

    assert fresh_metadata["readiness_gates"] == READINESS_GATES_CLOSED
    assert fresh_metadata["writes_clean_data"] is False
    assert fresh_metadata["writes_delivery"] is False
    assert fresh_metadata["writes_export"] is False
    assert fresh_metadata["database_write_count"] == 0
    assert fresh_metadata["filesystem_write_count"] == 0
    assert fresh_metadata["network_call_count"] == 0


def _assert_error_is_generic(message: str) -> None:
    lowered = message.lower()
    assert "planned-disabled" in lowered
    assert "no " in lowered
    for forbidden in (
        "sensitive full source",
        "raw mineru",
        "source_text",
        "secret",
        "postgresql",
        "password",
        "prod.example",
        "d:/unsafe",
        "review_queue_items",
        "https://",
        "endpoint",
    ):
        assert forbidden not in lowered
