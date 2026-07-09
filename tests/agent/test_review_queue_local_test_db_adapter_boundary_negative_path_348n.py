from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from tests.agent.review_queue_local_test_db_adapter_boundary_348n import (
    DEFAULT_PREVIEW_LIMIT,
    PLANNED_DISABLED_STATUS,
    READINESS_GATES_CLOSED,
    TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
    LocalTestDBAdapterActivationError,
    LocalTestDBAdapterCandidateError,
    LocalTestDBAdapterConfig,
    make_disabled_local_test_db_adapter_boundary,
    transaction_idempotency_policy,
    validate_local_test_db_activation_request,
    validate_local_test_db_candidate_batch,
)

MODULE_PATH = Path("tests/agent/review_queue_local_test_db_adapter_boundary_348n.py")


def _valid_activation_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "enabled": True,
        "test_only": True,
        "environment": "local_test",
        "db_selection": "sqlite_memory",
        "dsn": ":memory:",
        "activation_source": "explicit",
        "test_only_enable_token": TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,
    }
    payload.update(overrides)
    return payload


def _valid_candidate(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "review_item_id": "review:r7by:1",
        "idempotency_key": "a" * 64,
        "record_payload_hash": "b" * 64,
        "agreement_status": "DISAGREED",
        "evidence_preview": "bounded preview only",
        "source_trace": {
            "source_document_id": "doc:r7by",
            "matched_locator": "page:1:block:1",
            "matched_text_sha256": "c" * 64,
        },
    }
    candidate.update(overrides)
    return candidate


def _assert_activation_rejected_without_leak(payload: dict[str, object], leak_terms: tuple[str, ...] = ()) -> None:
    before = deepcopy(payload)

    with pytest.raises(LocalTestDBAdapterActivationError) as error:
        validate_local_test_db_activation_request(payload)

    assert payload == before
    _assert_generic_message(str(error.value), leak_terms)


def _assert_candidate_rejected_without_leak(candidates: list[dict[str, object]], leak_terms: tuple[str, ...] = ()) -> None:
    before = deepcopy(candidates)

    with pytest.raises(LocalTestDBAdapterCandidateError) as error:
        validate_local_test_db_candidate_batch(candidates)

    assert candidates == before
    _assert_generic_message(str(error.value), leak_terms)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.pop("test_only"),
        lambda payload: payload.update({"test_only": False}),
        lambda payload: payload.pop("environment"),
        lambda payload: payload.update({"environment": ""}),
        lambda payload: payload.update({"environment": "production"}),
        lambda payload: payload.update({"environment": "staging"}),
        lambda payload: payload.update({"environment": "local_test_prod"}),
        lambda payload: payload.pop("db_selection"),
        lambda payload: payload.update({"db_selection": "postgres_local"}),
        lambda payload: payload.update({"activation_source": "schema_alignment_preview"}),
        lambda payload: payload.update({"activation_source": "repository_skeleton_factory"}),
    ],
)
def test_r7by_activation_required_conditions_fail_closed(mutator: object) -> None:
    payload = _valid_activation_payload()
    mutator(payload)

    _assert_activation_rejected_without_leak(payload, ("production", "staging", "postgres"))


def test_r7by_valid_activation_shape_still_returns_planned_disabled_metadata_only() -> None:
    result = validate_local_test_db_activation_request(_valid_activation_payload())

    assert result["activation_request_validated"] is True
    assert result["future_activation_status"] == PLANNED_DISABLED_STATUS
    assert result["planned_adapter_only"] is True
    assert result["database_connection_opened"] is False
    assert result["schema_created"] is False
    assert result["migration_created"] is False
    assert result["table_created"] is False
    assert result["database_write_count"] == 0
    assert result["filesystem_write_count"] == 0
    assert result["network_call_count"] == 0
    assert result["persists_records"] is False
    assert result["readiness_gates"] == READINESS_GATES_CLOSED


@pytest.mark.parametrize(
    "extra_config, leak_terms",
    [
        ({"dsn": "postgres://user:secret@prod.example.invalid/review"}, ("postgres", "secret", "prod.example")),
        ({"dsn": "postgresql://user:secret@prod.example.invalid/review"}, ("postgresql", "secret", "prod.example")),
        ({"dsn": "mysql://user:secret@prod.example.invalid/review"}, ("mysql", "secret", "prod.example")),
        ({"dsn": "sqlite:///C:/unsafe/review_queue.db"}, ("sqlite://", "c:/unsafe")),
        ({"database_url": "sqlite:///D:/unsafe/review_queue.db"}, ("sqlite://", "d:/unsafe")),
        ({"host": "prod-db.internal"}, ("prod-db",)),
        ({"host": "10.10.0.5"}, ("10.10.0.5",)),
        ({"host": "rds.amazonaws.com"}, ("amazonaws",)),
        ({"endpoint": "db.example.invalid:5432"}, ("db.example", "5432")),
        ({"endpoint": "http://db.example.invalid"}, ("http://", "db.example")),
        ({"endpoint": "https://db.example.invalid"}, ("https://", "db.example")),
        ({"connection_string": "Server=prod;Password=secret"}, ("server=", "password", "secret")),
        ({"db_password": "secret-password"}, ("secret-password",)),
        ({"db_secret": "secret-value"}, ("secret-value",)),
        ({"api_key": "sk-prod-secret"}, ("sk-prod-secret",)),
        ({"token": "db-token-secret"}, ("db-token-secret",)),
        ({"schema_name": "review_queue_schema"}, ("review_queue_schema",)),
        ({"table_name": "review_queue_items"}, ("review_queue_items",)),
        ({"migration_name": "001_create_review_queue"}, ("001_create",)),
        ({"output_path": "D:/unsafe/review_queue.db"}, ("d:/unsafe",)),
        ({"file_path": "D:/unsafe/review_queue.db"}, ("d:/unsafe",)),
        ({"production_writer_config": {"enabled": True}}, ("production_writer_config",)),
        ({"readiness_override": {"production_ready": True}}, ("production_ready",)),
    ],
)
def test_r7by_production_looking_config_rejections_do_not_echo_values(
    extra_config: dict[str, object],
    leak_terms: tuple[str, ...],
) -> None:
    payload = _valid_activation_payload(**extra_config)

    _assert_activation_rejected_without_leak(payload, leak_terms)


def test_r7by_environment_variables_cannot_activate_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATEFAC_LOCAL_TEST_DB_ENABLED", "true")
    monkeypatch.setenv("DATEFAC_LOCAL_TEST_DB_ENVIRONMENT", "local_test")
    monkeypatch.setenv("DATEFAC_LOCAL_TEST_DB_DSN", "postgresql://user:secret@prod.example.invalid/review")
    monkeypatch.setenv("DATEFAC_LOCAL_TEST_DB_TOKEN", TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN)

    _assert_activation_rejected_without_leak({}, ("postgresql", "secret", TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN))
    _assert_activation_rejected_without_leak(
        _valid_activation_payload(activation_source="environment"),
        (TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,),
    )
    _assert_activation_rejected_without_leak(
        _valid_activation_payload(activation_source="env"),
        (TEST_ONLY_LOCAL_TEST_DB_ENABLE_TOKEN,),
    )


@pytest.mark.parametrize(
    "auto_activation_payload",
    [
        {"schema_alignment_preview": {"activation": True, "db_selection": "sqlite_memory"}},
        {"repository_skeleton_factory_output": {"repository_status": "DISABLED", "auto_activate": True}},
        {"activation_source": "schema_alignment_preview"},
        {"activation_source": "repository_skeleton_factory"},
        {"activation_source": "review_queue_repository_factory"},
    ],
)
def test_r7by_schema_preview_and_repository_factory_auto_activation_rejected(
    auto_activation_payload: dict[str, object],
) -> None:
    payload = _valid_activation_payload(**auto_activation_payload)

    _assert_activation_rejected_without_leak(payload, ("auto_activate", "sqlite_memory"))


@pytest.mark.parametrize(
    "field_name, field_value, leak_terms",
    [
        ("source_text", "sensitive source text", ("sensitive source text",)),
        ("full_source_text", "full source text", ("full source text",)),
        ("raw_mineru_payload", {"content_list_v2": "raw mineru"}, ("raw mineru",)),
        ("raw_excel_payload", {"sheet": "raw excel"}, ("raw excel",)),
        ("raw_parser_payload", {"page": "raw parser"}, ("raw parser",)),
        ("raw_ocr_payload", "raw ocr", ("raw ocr",)),
        ("raw_llm_payload", "raw llm", ("raw llm",)),
        ("raw_vlm_payload", "raw vlm", ("raw vlm",)),
        ("unbounded_evidence_text", "x" * 1000, ("x" * 32,)),
        ("evidence_preview", "y" * (DEFAULT_PREVIEW_LIMIT + 1), ("y" * 32,)),
    ],
)
def test_r7by_candidate_raw_payloads_and_unbounded_text_fail_closed(
    field_name: str,
    field_value: object,
    leak_terms: tuple[str, ...],
) -> None:
    _assert_candidate_rejected_without_leak([_valid_candidate(**{field_name: field_value})], leak_terms)


@pytest.mark.parametrize(
    "field_name, field_value",
    [
        ("clean_data_payload", {"row": "clean"}),
        ("normalized_clean_data", {"metric": "trusted"}),
        ("approved_export_payload", {"path": "D:/unsafe/export.csv"}),
        ("delivery_payload", {"export": True}),
        ("export_payload", {"path": "D:/unsafe/export.csv"}),
        ("delivery_export_intent", True),
        ("readiness_override", {"formal_client_export_allowed": True}),
        ("readiness_gates", {"client_ready": True}),
        ("production_timestamp_override", "2026-07-09T00:00:00Z"),
    ],
)
def test_r7by_clean_data_delivery_export_and_readiness_intents_fail_closed(
    field_name: str,
    field_value: object,
) -> None:
    _assert_candidate_rejected_without_leak(
        [_valid_candidate(**{field_name: field_value})],
        ("formal_client_export_allowed", "d:/unsafe", "2026-07-09"),
    )


@pytest.mark.parametrize(
    "field_name, field_value",
    [
        ("caller_supplied_db_primary_key", "db:primary-key:1"),
        ("db_primary_key", 1001),
        ("primary_key", "pk-1001"),
        ("caller_supplied_db_row", {"id": 1, "table": "review_queue_items"}),
        ("database_row", {"id": 1}),
        ("db_row", {"id": 1}),
        ("committed_db_receipt", {"database_write_count": 1}),
        ("committed_receipt", {"persistence_status": "COMMITTED"}),
        ("db_receipt", {"table": "review_queue_items"}),
        ("adapter_internal_state", {"records": ["should not exist"]}),
        ("internal_adapter_state", {"records": ["should not exist"]}),
        ("local_test_db_adapter_state", {"records": ["should not exist"]}),
        ("adapter_state", {"records": ["should not exist"]}),
    ],
)
def test_r7by_caller_supplied_db_state_receipts_and_internals_fail_closed(
    field_name: str,
    field_value: object,
) -> None:
    _assert_candidate_rejected_without_leak(
        [_valid_candidate(**{field_name: field_value})],
        ("review_queue_items", "committed", "should not exist"),
    )


@pytest.mark.parametrize(
    "candidate",
    [
        _valid_candidate(idempotency_key=""),
        _valid_candidate(idempotency_key="not-a-64-char-hex-value"),
        _valid_candidate(idempotency_key="g" * 64),
        _valid_candidate(record_payload_hash=""),
        _valid_candidate(record_payload_hash="not-a-64-char-hex-value"),
        _valid_candidate(record_payload_hash="g" * 64),
    ],
)
def test_r7by_malformed_idempotency_or_record_hash_fails_closed(candidate: dict[str, object]) -> None:
    _assert_candidate_rejected_without_leak([candidate], ("not-a-64",))


def test_r7by_missing_required_identity_fields_fail_closed() -> None:
    for field_name in ("review_item_id", "idempotency_key", "record_payload_hash"):
        candidate = _valid_candidate()
        candidate.pop(field_name)
        _assert_candidate_rejected_without_leak([candidate])


def test_r7by_transaction_conflicts_fail_closed_without_partial_success() -> None:
    conflicting_idempotency = [
        _valid_candidate(review_item_id="review:r7by:1", idempotency_key="a" * 64, record_payload_hash="b" * 64),
        _valid_candidate(review_item_id="review:r7by:2", idempotency_key="a" * 64, record_payload_hash="c" * 64),
    ]
    conflicting_review_item = [
        _valid_candidate(review_item_id="review:r7by:1", idempotency_key="a" * 64, record_payload_hash="b" * 64),
        _valid_candidate(review_item_id="review:r7by:1", idempotency_key="d" * 64, record_payload_hash="c" * 64),
    ]

    _assert_candidate_rejected_without_leak(conflicting_idempotency)
    _assert_candidate_rejected_without_leak(conflicting_review_item)

    policy = transaction_idempotency_policy()
    assert policy["invalid_row_rejects_entire_batch"] is True
    assert policy["silent_duplicate_insert_allowed"] is False
    assert policy["same_idempotency_key_different_record_payload_hash"] == "planned_conflict_fail_closed"
    assert policy["same_review_item_id_conflicting_identity"] == "planned_conflict_fail_closed"


@pytest.mark.parametrize(
    "candidates",
    [
        [_valid_candidate(raw_llm_payload="invalid first"), _valid_candidate(review_item_id="review:r7by:2", idempotency_key="d" * 64)],
        [_valid_candidate(), _valid_candidate(review_item_id="review:r7by:2", idempotency_key="d" * 64, raw_vlm_payload="invalid later")],
        [_valid_candidate(), _valid_candidate(review_item_id="review:r7by:2")],
    ],
)
def test_r7by_invalid_batch_fails_whole_batch_and_returns_no_partial_success(
    candidates: list[dict[str, object]],
) -> None:
    _assert_candidate_rejected_without_leak(candidates, ("invalid first", "invalid later"))


def test_r7by_nested_forbidden_config_and_candidate_fields_fail_closed_without_mutation() -> None:
    config = _valid_activation_payload(
        nested={
            "safe_level": {
                "deeper": {
                    "db_secret": "nested-secret",
                    "endpoint": "https://prod.example.invalid",
                }
            }
        }
    )
    candidates = [
        _valid_candidate(
            source_trace={
                "source_document_id": "doc:r7by",
                "nested": {
                    "raw_excel_payload": {"sheet": "raw nested"},
                    "readiness_override": {"production_ready": True},
                },
            }
        )
    ]

    _assert_activation_rejected_without_leak(config, ("nested-secret", "prod.example"))
    _assert_candidate_rejected_without_leak(candidates, ("raw nested", "production_ready"))


def test_r7by_candidate_validation_accepts_only_bounded_metadata_and_stores_nothing() -> None:
    candidate = _valid_candidate(evidence_preview="short metadata preview")
    before = deepcopy(candidate)

    result = validate_local_test_db_candidate_batch([candidate])

    assert candidate == before
    assert result["candidate_validation_status"] == "VALIDATED_FOR_FUTURE_LOCAL_TEST_DB_ONLY"
    assert result["candidate_count"] == 1
    assert result["stores_records"] is False
    assert result["persists_records"] is False
    assert result["database_write_count"] == 0
    assert result["filesystem_write_count"] == 0
    assert result["network_call_count"] == 0
    assert result["writes_clean_data"] is False
    assert result["writes_delivery"] is False
    assert result["writes_export"] is False
    assert result["readiness_gates"] == READINESS_GATES_CLOSED


def test_r7by_source_inspection_has_no_db_io_network_or_sql_execution_markers() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    source_lower = source.lower()
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncpg",
        "boto",
        "boto3",
        "botocore",
        "docker",
        "httpx",
        "mysql",
        "psycopg",
        "psycopg2",
        "pymysql",
        "redis",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "urllib",
    }
    forbidden_call_names = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "executescript",
        "fetchall",
        "fetchone",
        "open",
        "post",
        "put",
        "request",
        "write",
        "write_text",
        "writelines",
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
                assert func.id not in forbidden_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names

    for marker in (
        "create table",
        "alter table",
        "insert ",
        "insert into",
        "select ",
        "update ",
        "delete from",
        "drop table",
        "docker",
    ):
        assert marker not in source_lower


def test_r7by_boundary_metadata_keeps_clean_data_delivery_and_readiness_closed() -> None:
    metadata = make_disabled_local_test_db_adapter_boundary().metadata()

    assert metadata["database_connection_opened"] is False
    assert metadata["writes_review_queue"] is False
    assert metadata["writes_clean_data"] is False
    assert metadata["writes_delivery"] is False
    assert metadata["writes_export"] is False
    assert metadata["readiness_gates"] == READINESS_GATES_CLOSED


def _assert_generic_message(message: str, leak_terms: tuple[str, ...] = ()) -> None:
    lowered = message.lower()
    assert "planned-disabled" in lowered
    assert "no " in lowered
    for term in leak_terms:
        assert term.lower() not in lowered
    for always_forbidden in (
        "source_text",
        "raw_mineru_payload",
        "raw_excel_payload",
        "postgresql://",
        "postgres://",
        "mysql://",
        "password",
        "secret",
        "prod.example",
        "d:/unsafe",
        "c:/unsafe",
        "review_queue_items",
        "https://",
        "http://",
    ):
        assert always_forbidden not in lowered
