from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import fields
from pathlib import Path

import pytest

import datefac_agent.review.review_queue_repository as repository_module
from datefac_agent.review.review_queue_repository import (
    DISABLED_REASON,
    READINESS_GATES_CLOSED,
    DisabledReviewQueueRepository,
    ReviewQueueRepositoryDisabledError,
    ReviewQueueRepositoryWriteReceipt,
    create_disabled_review_queue_repository,
)

MODULE_PATH = Path("datefac_agent/review/review_queue_repository.py")


def _candidate_with_sensitive_payloads() -> dict[str, object]:
    return {
        "review_item_id": "review:r7bv:1",
        "run_id": "run:r7bv",
        "agreement_status": "DISAGREED",
        "metric_name": "营业收入",
        "period": "2026Q1",
        "candidate_value": "47.10",
        "source_text": "sensitive full source text",
        "raw_mineru_payload": {"content_list_v2": "raw mineru"},
        "raw_excel_payload": {"sheet": "raw excel"},
        "raw_parser_payload": {"pages": ["raw parser"]},
        "raw_ocr_payload": "raw ocr",
        "raw_llm_payload": "raw llm",
        "raw_vlm_payload": "raw vlm",
        "connection_string": "Server=prod;Password=secret",
        "fake_repository_write_receipt": {"status": "forged"},
        "repository_internal_state": {"records": [{"secret": "state"}]},
        "clean_data_intent": True,
        "delivery_export_intent": True,
        "readiness_gates": {"client_ready": True},
    }


def test_r7bv_repository_module_imports_without_db_storage_network_dependencies() -> None:
    assert repository_module.REPOSITORY_INTERFACE_VERSION == "r7bu_review_queue_repository_disabled_skeleton_v1"
    assert repository_module.READINESS_GATES_CLOSED == READINESS_GATES_CLOSED


def test_r7bv_public_factory_remains_disabled_by_default() -> None:
    repository = create_disabled_review_queue_repository()

    assert isinstance(repository, DisabledReviewQueueRepository)
    assert repository.disabled_reason == DISABLED_REASON
    assert tuple(field.name for field in fields(repository)) == (
        "disabled_reason",
        "repository_interface_version",
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"enabled": True},
        {"allow_persistence": True},
        {"test_only_enable_token": "R7BV_TEST_TOKEN"},
        {"production_ready": True},
        {"readiness_gates": {"production_ready": True}},
        {"repository_config": {"enabled": True}},
        {"database": {"dsn": "postgresql://user:secret@prod/review"}},
    ],
)
def test_r7bv_factory_cannot_be_enabled_by_arbitrary_kwargs(kwargs: dict[str, object]) -> None:
    before = deepcopy(kwargs)

    with pytest.raises(ReviewQueueRepositoryDisabledError, match="configuration is not accepted") as error:
        create_disabled_review_queue_repository(**kwargs)

    assert kwargs == before
    _assert_message_is_generic(str(error.value))


@pytest.mark.parametrize(
    "config_key, config_value",
    [
        ("dsn", "postgresql://user:secret@prod/review_queue"),
        ("connection_string", "Server=prod;Password=secret"),
        ("table_name", "review_queue_items"),
        ("output_path", "D:/unsafe/review_queue.json"),
        ("file_path", "D:/unsafe/review_queue.sqlite"),
        ("endpoint", "https://prod.example.invalid/review_queue"),
        ("production_flag", True),
        ("readiness_override", {"client_ready": True}),
    ],
)
def test_r7bv_production_like_config_values_fail_closed_without_echo(
    config_key: str,
    config_value: object,
) -> None:
    config = {config_key: config_value}
    before = deepcopy(config)

    with pytest.raises(ReviewQueueRepositoryDisabledError) as error:
        create_disabled_review_queue_repository(**config)

    assert config == before
    message = str(error.value)
    _assert_message_is_generic(message)
    assert config_key not in message


def test_r7bv_factory_cannot_be_enabled_by_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATEFAC_REVIEW_QUEUE_REPOSITORY_ENABLED", "true")
    monkeypatch.setenv("DATEFAC_REVIEW_QUEUE_DB_DSN", "postgresql://user:secret@prod/review")

    repository = create_disabled_review_queue_repository()

    assert isinstance(repository, DisabledReviewQueueRepository)
    with pytest.raises(ReviewQueueRepositoryDisabledError, match="disabled by default"):
        repository.write_batch([{"review_item_id": "review:r7bv:env"}], run_id="run:r7bv")


def test_r7bv_write_batch_always_fails_closed_and_does_not_grow_state() -> None:
    repository = create_disabled_review_queue_repository()
    candidate = _candidate_with_sensitive_payloads()
    candidates = [candidate]
    before_candidates = deepcopy(candidates)
    before_state = _repository_public_state(repository)

    for _ in range(3):
        with pytest.raises(ReviewQueueRepositoryDisabledError, match="write_batch") as error:
            repository.write_batch(candidates, run_id="run:r7bv")
        assert "no persistence occurred" in str(error.value)
        _assert_message_is_generic(str(error.value))
        assert candidates == before_candidates
        assert _repository_public_state(repository) == before_state


def test_r7bv_get_and_list_fail_closed_with_stable_error_type() -> None:
    repository = create_disabled_review_queue_repository()

    for operation in (
        lambda: repository.get_by_review_item_id("review:r7bv:1"),
        lambda: repository.list_by_run_id("run:r7bv"),
    ):
        with pytest.raises(ReviewQueueRepositoryDisabledError) as error:
            operation()
        assert isinstance(error.value, ReviewQueueRepositoryDisabledError)
        assert isinstance(error.value, ValueError)
        _assert_message_is_generic(str(error.value))


@pytest.mark.parametrize(
    "field_name",
    [
        "fake_repository_write_receipt",
        "write_receipt",
        "receipt",
        "repository_internal_state",
        "internal_state",
        "repository_state",
    ],
)
def test_r7bv_caller_supplied_receipt_or_internal_state_fails_closed(field_name: str) -> None:
    repository = create_disabled_review_queue_repository()
    candidates = [{**_candidate_with_sensitive_payloads(), field_name: {"secret": "do not echo"}}]
    before = deepcopy(candidates)

    with pytest.raises(ReviewQueueRepositoryDisabledError) as error:
        repository.write_batch(candidates, run_id="run:r7bv")

    assert candidates == before
    assert field_name not in str(error.value)
    _assert_message_is_generic(str(error.value))


def test_r7bv_receipt_is_disabled_only_and_mutation_safe() -> None:
    repository = create_disabled_review_queue_repository()
    receipt = repository.disabled_receipt()
    first = receipt.as_dict()
    first["readiness_gates"]["client_ready"] = True
    second = receipt.as_dict()

    assert isinstance(receipt, ReviewQueueRepositoryWriteReceipt)
    assert second["persistence_status"] == "NOT_PERSISTED"
    assert second["writes_database"] is False
    assert second["writes_review_queue"] is False
    assert second["writes_clean_data"] is False
    assert second["writes_delivery"] is False
    assert second["writes_export"] is False
    assert second["readiness_gates"] == READINESS_GATES_CLOSED
    assert not _forbidden_keys_in(second)


def test_r7bv_custom_receipt_and_disabled_reason_are_rejected_without_echo() -> None:
    with pytest.raises(ReviewQueueRepositoryDisabledError) as receipt_error:
        ReviewQueueRepositoryWriteReceipt(disabled_reason="secret raw source_text")
    with pytest.raises(ReviewQueueRepositoryDisabledError) as repository_error:
        DisabledReviewQueueRepository(disabled_reason="secret raw source_text")

    assert "custom disabled reasons are not accepted" in str(receipt_error.value)
    assert "custom disabled reasons are not accepted" in str(repository_error.value)
    assert "secret" not in str(receipt_error.value).lower()
    assert "source_text" not in str(repository_error.value)


def test_r7bv_clean_data_delivery_export_and_readiness_intents_are_not_stateful() -> None:
    repository = create_disabled_review_queue_repository()
    candidates = [
        {
            **_candidate_with_sensitive_payloads(),
            "clean_data_write_intent": True,
            "delivery_write_intent": True,
            "export_intent": True,
            "readiness_override": {"production_ready": True},
        }
    ]

    with pytest.raises(ReviewQueueRepositoryDisabledError):
        repository.write_batch(candidates, run_id="run:r7bv")

    receipt = repository.disabled_receipt().as_dict()
    assert receipt["writes_clean_data"] is False
    assert receipt["writes_delivery"] is False
    assert receipt["writes_export"] is False
    assert receipt["readiness_gates"] == READINESS_GATES_CLOSED


def test_r7bv_source_has_no_forbidden_db_io_network_or_fake_repository_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "asyncpg",
        "boto3",
        "botocore",
        "datefac_agent.delivery",
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
        "tests",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
                assert alias.name not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
            assert node.module not in forbidden_import_roots


def test_r7bv_source_has_no_sql_filesystem_or_network_execution_markers() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
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
        "get",
        "post",
        "put",
        "patch",
        "delete",
    }
    source_lower = MODULE_PATH.read_text(encoding="utf-8").lower()

    for marker in (
        "select ",
        "insert ",
        "update ",
        "delete from",
        "create table",
        "alter table",
        "drop table",
        "sqlite",
        "postgres",
        "mysql",
        "dsn",
        "connection_string",
    ):
        assert marker not in source_lower

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def test_r7bv_source_does_not_define_persistence_state_or_activation_flags() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    for forbidden in (
        "_records",
        "_records_by_idempotency_key",
        "records_by_idempotency_key",
        "table_name",
        "TEST_ONLY_ENABLE_TOKEN",
        "ENABLE_TOKEN",
        "os.environ",
        "getenv",
        "enabled: bool = True",
        "production_ready\": True",
        "formal_client_export_allowed\": True",
        "clean_data_eligible",
        "delivery_clean_admitted",
        "STRONG_EVIDENCE",
    ):
        assert forbidden not in source


def _repository_public_state(repository: DisabledReviewQueueRepository) -> dict[str, object]:
    return {field.name: getattr(repository, field.name) for field in fields(repository)}


def _assert_message_is_generic(message: str) -> None:
    lowered = message.lower()
    assert "disabled by default" in lowered
    for forbidden in (
        "secret",
        "source_text",
        "sensitive full source",
        "raw mineru",
        "raw excel",
        "raw parser",
        "raw ocr",
        "raw llm",
        "raw vlm",
        "postgresql",
        "password",
        "review_queue_items",
        "d:/unsafe",
        "prod.example",
    ):
        assert forbidden not in lowered


def _forbidden_keys_in(value: object) -> set[str]:
    forbidden = {
        "source_text",
        "full_source_text",
        "raw_mineru_payload",
        "raw_excel_payload",
        "raw_parser_payload",
        "raw_ocr_payload",
        "raw_llm_payload",
        "raw_vlm_payload",
        "dsn",
        "connection_string",
        "table_name",
        "output_path",
        "file_path",
        "endpoint",
        "production_writer_config",
        "clean_data_intent",
        "delivery_export_intent",
        "readiness_override",
    }
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if key_text in forbidden:
                found.add(key_text)
            found.update(_forbidden_keys_in(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_forbidden_keys_in(child))
    return found
