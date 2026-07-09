from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from tests.agent.review_queue_local_test_db_prototype_348n import (
    DEFAULT_EVIDENCE_PREVIEW_LIMIT,
    LOCAL_TEST_DB_PROTOTYPE_VERSION,
    READINESS_GATES_CLOSED,
    TEST_ONLY_LOCAL_TEST_DB_PROTOTYPE_ENABLE_TOKEN,
    VALID_LOCAL_TEST_ENVIRONMENT,
    LocalTestDBActivationError,
    LocalTestDBCandidateError,
    LocalTestDBClosedError,
    LocalTestDBPrototypeConfig,
    LocalTestDBWriteConflictError,
    make_local_test_db_prototype,
)

MODULE_PATH = Path("tests/agent/review_queue_local_test_db_prototype_348n.py")
BOUNDARY_MODULE_PATH = Path("tests/agent/review_queue_local_test_db_adapter_boundary_348n.py")
REPOSITORY_MODULE_PATH = Path("datefac_agent/review/review_queue_repository.py")


def _valid_config(**overrides: object) -> LocalTestDBPrototypeConfig:
    values: dict[str, object] = {
        "test_only": True,
        "environment": VALID_LOCAL_TEST_ENVIRONMENT,
        "storage": "sqlite_memory",
        "explicit_prototype_enabled": True,
        "activation_source": "explicit",
        "test_only_enable_token": TEST_ONLY_LOCAL_TEST_DB_PROTOTYPE_ENABLE_TOKEN,
    }
    values.update(overrides)
    return LocalTestDBPrototypeConfig(**values)


def _valid_config_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "test_only": True,
        "environment": VALID_LOCAL_TEST_ENVIRONMENT,
        "storage": "sqlite_memory",
        "explicit_prototype_enabled": True,
        "activation_source": "explicit",
        "test_only_enable_token": TEST_ONLY_LOCAL_TEST_DB_PROTOTYPE_ENABLE_TOKEN,
    }
    payload.update(overrides)
    return payload


def _candidate(
    *,
    review_item_id: str = "review:r7cb:1",
    run_id: str = "run:r7cb",
    candidate_id: str = "candidate:r7cb:1",
    idempotency_key: str = "a" * 64,
    record_payload_hash: str = "b" * 64,
    **overrides: object,
) -> dict[str, object]:
    candidate: dict[str, object] = {
        "review_item_id": review_item_id,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "idempotency_key": idempotency_key,
        "record_payload_hash": record_payload_hash,
        "status": "DISAGREED",
        "blocked_delivery_reason": "requires reviewer decision",
        "evidence_preview": "bounded evidence preview",
        "source_trace": {
            "source_document_id": "doc:r7cb",
            "matched_locator": "page:1:block:2",
            "matched_text_sha256": "c" * 64,
        },
        "created_at": "2026-07-09T00:00:00Z",
    }
    candidate.update(overrides)
    return candidate


def _assert_generic_error(message: str, leak_terms: tuple[str, ...] = ()) -> None:
    lowered = message.lower()
    for term in leak_terms:
        assert term.lower() not in lowered
    assert "secret" not in lowered
    assert "postgres" not in lowered
    assert "mysql" not in lowered
    assert "prod.example" not in lowered
    assert "d:/unsafe" not in lowered
    assert "source text" not in lowered


def test_r7cb_module_lives_under_tests_agent_and_is_marked_test_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    prototype = make_local_test_db_prototype(_valid_config())

    assert "tests/agent" in MODULE_PATH.as_posix()
    assert "test-only" in source.lower()
    assert prototype.metadata()["prototype_version"] == LOCAL_TEST_DB_PROTOTYPE_VERSION
    assert prototype.metadata()["test_only"] is True
    assert prototype.metadata()["readiness_gates"] == READINESS_GATES_CLOSED


def test_r7cb_prototype_uses_in_memory_sqlite_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    prototype = make_local_test_db_prototype(_valid_config())
    metadata = prototype.metadata()

    assert 'sqlite3.connect(":memory:")' in source
    assert "sqlite:///" not in source
    assert "storage_identifier" in metadata
    assert metadata["storage_identifier"] == ":memory:"
    assert metadata["database_connection_scope"] == "test_owned_in_memory"
    assert metadata["writes_production_database"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {},
        _valid_config_payload(test_only=False),
        _valid_config_payload(environment=""),
        _valid_config_payload(environment="production"),
        _valid_config_payload(environment="staging"),
        _valid_config_payload(environment="dev"),
        _valid_config_payload(storage="postgres"),
        _valid_config_payload(storage="sqlite_file"),
        _valid_config_payload(explicit_prototype_enabled=False),
        _valid_config_payload(activation_source="environment"),
        _valid_config_payload(activation_source="env"),
        _valid_config_payload(test_only_enable_token="wrong-token"),
    ],
)
def test_r7cb_cannot_be_constructed_without_all_explicit_gates(payload: dict[str, object]) -> None:
    before = deepcopy(payload)

    with pytest.raises(LocalTestDBActivationError) as error:
        make_local_test_db_prototype(payload)

    assert payload == before
    _assert_generic_error(str(error.value), ("production", "staging", "wrong-token"))


@pytest.mark.parametrize(
    "extra_config, leak_terms",
    [
        ({"dsn": "postgresql://user:secret@prod.example.invalid/review"}, ("postgresql", "secret", "prod.example")),
        ({"database_url": "sqlite:///D:/unsafe/review_queue.db"}, ("sqlite://", "d:/unsafe")),
        ({"host": "prod-db.internal"}, ("prod-db",)),
        ({"endpoint": "https://db.example.invalid"}, ("https://", "db.example")),
        ({"file_path": "D:/unsafe/review_queue.db"}, ("d:/unsafe",)),
        ({"connection_string": "Server=prod;Password=secret"}, ("server=", "password", "secret")),
        ({"production_writer_config": {"enabled": True}}, ("production_writer_config",)),
        ({"readiness_override": {"production_ready": True}}, ("production_ready",)),
        ({"clean_data_intent": True}, ("clean_data_intent",)),
        ({"delivery_export_intent": True}, ("delivery_export_intent",)),
    ],
)
def test_r7cb_rejects_dsn_host_path_production_like_config_without_echo(
    extra_config: dict[str, object],
    leak_terms: tuple[str, ...],
) -> None:
    payload = _valid_config_payload(**extra_config)
    before = deepcopy(payload)

    with pytest.raises(LocalTestDBActivationError) as error:
        make_local_test_db_prototype(payload)

    assert payload == before
    _assert_generic_error(str(error.value), leak_terms)


def test_r7cb_environment_variables_are_not_sufficient_activation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATEFAC_LOCAL_TEST_DB_ENABLED", "true")
    monkeypatch.setenv("DATEFAC_LOCAL_TEST_DB_DSN", "postgresql://user:secret@prod.example.invalid/review")
    monkeypatch.setenv("DATEFAC_LOCAL_TEST_DB_TOKEN", TEST_ONLY_LOCAL_TEST_DB_PROTOTYPE_ENABLE_TOKEN)

    with pytest.raises(LocalTestDBActivationError) as error:
        make_local_test_db_prototype({})
    _assert_generic_error(str(error.value), ("postgresql", "secret", TEST_ONLY_LOCAL_TEST_DB_PROTOTYPE_ENABLE_TOKEN))

    with pytest.raises(LocalTestDBActivationError):
        make_local_test_db_prototype(_valid_config_payload(activation_source="environment"))


def test_r7cb_schema_is_created_only_in_test_owned_in_memory_connection() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    metadata = prototype.metadata()

    assert metadata["schema_created"] is True
    assert metadata["table_created"] is True
    assert metadata["table_name_owned_by_module"] is True
    assert metadata["storage_identifier"] == ":memory:"
    assert metadata["filesystem_write_count"] == 0
    assert prototype.list_by_run_id("run:r7cb") == []


def test_r7cb_successful_insert_and_readback_of_one_minimal_candidate() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    candidate = _candidate()

    receipt = prototype.write_batch([candidate])
    stored = prototype.get_by_review_item_id("review:r7cb:1")

    assert receipt["persistence_status"] == "TEST_ONLY_IN_MEMORY_SQLITE_WRITTEN"
    assert receipt["inserted_count"] == 1
    assert receipt["deduplicated_count"] == 0
    assert receipt["writes_production_database"] is False
    assert receipt["readiness_gates"] == READINESS_GATES_CLOSED
    assert stored is not None
    assert stored["review_item_id"] == candidate["review_item_id"]
    assert stored["source_trace"] == candidate["source_trace"]
    assert "source_text" not in stored


def test_r7cb_batch_insert_is_atomic_for_valid_rows() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    candidates = [
        _candidate(review_item_id="review:r7cb:1", candidate_id="candidate:r7cb:1", idempotency_key="a" * 64),
        _candidate(review_item_id="review:r7cb:2", candidate_id="candidate:r7cb:2", idempotency_key="b" * 64),
    ]

    receipt = prototype.write_batch(candidates)

    assert receipt["batch_atomic"] is True
    assert receipt["inserted_count"] == 2
    assert len(prototype.list_by_run_id("run:r7cb")) == 2


def test_r7cb_invalid_first_row_rolls_back_whole_batch() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    invalid = _candidate(review_item_id="review:r7cb:bad")
    invalid.pop("record_payload_hash")
    valid = _candidate(review_item_id="review:r7cb:2", candidate_id="candidate:r7cb:2", idempotency_key="b" * 64)

    with pytest.raises(LocalTestDBCandidateError):
        prototype.write_batch([invalid, valid])

    assert prototype.list_by_run_id("run:r7cb") == []


def test_r7cb_invalid_later_row_rolls_back_whole_batch() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    valid = _candidate(review_item_id="review:r7cb:1", candidate_id="candidate:r7cb:1", idempotency_key="a" * 64)
    invalid = _candidate(review_item_id="review:r7cb:bad", candidate_id="candidate:r7cb:bad", idempotency_key="b" * 64)
    invalid.pop("record_payload_hash")

    with pytest.raises(LocalTestDBCandidateError):
        prototype.write_batch([valid, invalid])

    assert prototype.list_by_run_id("run:r7cb") == []


def test_r7cb_same_idempotency_key_and_hash_is_deterministic_no_duplicate_retry() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    candidate = _candidate()

    first = prototype.write_batch([candidate])
    second = prototype.write_batch([deepcopy(candidate)])

    assert first["inserted_count"] == 1
    assert second["inserted_count"] == 0
    assert second["deduplicated_count"] == 1
    assert len(prototype.list_by_run_id("run:r7cb")) == 1


def test_r7cb_same_idempotency_key_different_hash_conflicts_fail_closed() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    prototype.write_batch([_candidate()])
    conflicting = _candidate(
        review_item_id="review:r7cb:2",
        candidate_id="candidate:r7cb:2",
        idempotency_key="a" * 64,
        record_payload_hash="c" * 64,
    )

    with pytest.raises(LocalTestDBWriteConflictError) as error:
        prototype.write_batch([conflicting])

    _assert_generic_error(str(error.value))
    assert len(prototype.list_by_run_id("run:r7cb")) == 1


def test_r7cb_same_review_item_id_conflicting_identity_fails_closed() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    prototype.write_batch([_candidate()])
    conflicting = _candidate(
        review_item_id="review:r7cb:1",
        candidate_id="candidate:r7cb:other",
        idempotency_key="d" * 64,
        record_payload_hash="e" * 64,
    )

    with pytest.raises(LocalTestDBWriteConflictError):
        prototype.write_batch([conflicting])

    assert len(prototype.list_by_run_id("run:r7cb")) == 1


def test_r7cb_record_payload_hash_is_required() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    candidate = _candidate(record_payload_hash="")

    with pytest.raises(LocalTestDBCandidateError):
        prototype.write_batch([candidate])

    assert prototype.list_by_run_id("run:r7cb") == []


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
        ("evidence_preview", "y" * (DEFAULT_EVIDENCE_PREVIEW_LIMIT + 1), ("y" * 32,)),
    ],
)
def test_r7cb_raw_payload_fields_are_rejected_before_db_write(
    field_name: str,
    field_value: object,
    leak_terms: tuple[str, ...],
) -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    candidate = _candidate(**{field_name: field_value})

    with pytest.raises(LocalTestDBCandidateError) as error:
        prototype.write_batch([candidate])

    _assert_generic_error(str(error.value), leak_terms)
    assert prototype.list_by_run_id("run:r7cb") == []


@pytest.mark.parametrize(
    "field_name, field_value",
    [
        ("clean_data_payload", {"row": "clean"}),
        ("clean_data_intent", True),
        ("delivery_payload", {"export": True}),
        ("delivery_export_intent", True),
        ("export_payload", {"path": "D:/unsafe/export.csv"}),
        ("readiness_override", {"production_ready": True}),
        ("readiness_gates", {"client_ready": True}),
    ],
)
def test_r7cb_clean_data_delivery_export_readiness_intent_rejected_before_db_write(
    field_name: str,
    field_value: object,
) -> None:
    prototype = make_local_test_db_prototype(_valid_config())

    with pytest.raises(LocalTestDBCandidateError):
        prototype.write_batch([_candidate(**{field_name: field_value})])

    assert prototype.list_by_run_id("run:r7cb") == []


def test_r7cb_input_candidate_and_config_objects_are_not_mutated() -> None:
    config = _valid_config_payload()
    candidates = [_candidate()]
    config_before = deepcopy(config)
    candidates_before = deepcopy(candidates)

    prototype = make_local_test_db_prototype(config)
    prototype.write_batch(candidates)

    assert config == config_before
    assert candidates == candidates_before


def test_r7cb_error_messages_do_not_echo_payload_dsn_secret_host_or_path() -> None:
    with pytest.raises(LocalTestDBActivationError) as activation_error:
        make_local_test_db_prototype(
            _valid_config_payload(dsn="postgresql://user:secret@prod.example.invalid/review")
        )
    _assert_generic_error(str(activation_error.value), ("postgresql", "secret", "prod.example"))

    prototype = make_local_test_db_prototype(_valid_config())
    with pytest.raises(LocalTestDBCandidateError) as candidate_error:
        prototype.write_batch([_candidate(source_text="sensitive source text")])
    _assert_generic_error(str(candidate_error.value), ("sensitive source text",))


def test_r7cb_close_teardown_rejects_later_operations() -> None:
    prototype = make_local_test_db_prototype(_valid_config())
    prototype.write_batch([_candidate()])

    prototype.close()

    with pytest.raises(LocalTestDBClosedError):
        prototype.list_by_run_id("run:r7cb")
    with pytest.raises(LocalTestDBClosedError):
        prototype.write_batch([_candidate(review_item_id="review:r7cb:2", idempotency_key="b" * 64)])


def test_r7cb_repeated_test_runs_use_independent_in_memory_state() -> None:
    first = make_local_test_db_prototype(_valid_config())
    second = make_local_test_db_prototype(_valid_config())

    first.write_batch([_candidate()])

    assert len(first.list_by_run_id("run:r7cb")) == 1
    assert second.list_by_run_id("run:r7cb") == []


def test_r7cb_source_inspection_sqlite3_only_in_new_test_only_prototype() -> None:
    prototype_source = MODULE_PATH.read_text(encoding="utf-8")
    boundary_source = BOUNDARY_MODULE_PATH.read_text(encoding="utf-8")
    repository_source = REPOSITORY_MODULE_PATH.read_text(encoding="utf-8")
    production_sources = [
        path.read_text(encoding="utf-8")
        for path in Path("datefac_agent").rglob("*.py")
    ]

    assert "import sqlite3" in prototype_source
    assert "sqlite3" not in boundary_source
    assert "sqlite3" not in repository_source
    assert "review_queue_local_test_db_prototype_348n" not in repository_source
    assert all("sqlite3" not in source for source in production_sources)
    assert all("review_queue_local_test_db_prototype_348n" not in source for source in production_sources)


def test_r7cb_source_inspection_has_no_network_docker_file_db_writes_or_production_imports() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    parsed = ast.parse(source)
    imported_names = {
        alias.name
        for node in ast.walk(parsed)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from = {
        node.module
        for node in ast.walk(parsed)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    forbidden_imports = {
        "datefac_agent",
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "docker",
        "sqlalchemy",
        "psycopg",
        "psycopg2",
        "pymysql",
        "mysql",
        "asyncpg",
    }
    assert imported_names.isdisjoint(forbidden_imports)
    assert all(not module.startswith("datefac_agent") for module in imported_from)
    assert "sqlite3.connect(\":memory:\")" in source
    assert "sqlite:///" not in source
    forbidden_call_names = {"open"}
    forbidden_call_attrs = {"write"}
    for node in ast.walk(parsed):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_call_names
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_attrs
