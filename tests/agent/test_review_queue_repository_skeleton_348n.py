from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from datefac_agent.review.review_queue_repository import (
    DISABLED_REASON,
    DISABLED_STATUS,
    READINESS_GATES_CLOSED,
    REPOSITORY_INTERFACE_VERSION,
    DisabledReviewQueueRepository,
    ReviewQueueRepositoryDisabledError,
    ReviewQueueRepositoryWriteReceipt,
    create_disabled_review_queue_repository,
)

MODULE_PATH = Path("datefac_agent/review/review_queue_repository.py")


def _candidate() -> dict[str, object]:
    return {
        "review_item_id": "review:r7bu:1",
        "run_id": "run:r7bu",
        "agreement_status": "DISAGREED",
        "evidence_preview": "bounded preview only",
        "record_payload_hash": "a" * 64,
        "source_trace": {"matched_locator": "page:1:block:1"},
    }


def test_r7bu_factory_returns_disabled_repository_by_default() -> None:
    repository = create_disabled_review_queue_repository()

    assert isinstance(repository, DisabledReviewQueueRepository)
    assert repository.disabled_reason == DISABLED_REASON
    assert repository.repository_interface_version == REPOSITORY_INTERFACE_VERSION


def test_r7bu_write_batch_fails_closed_and_does_not_mutate_input() -> None:
    repository = create_disabled_review_queue_repository()
    candidates = [_candidate()]
    before = deepcopy(candidates)

    with pytest.raises(ReviewQueueRepositoryDisabledError, match="disabled by default") as error:
        repository.write_batch(candidates, run_id="run:r7bu")

    assert candidates == before
    assert "no persistence occurred" in str(error.value)


def test_r7bu_read_methods_fail_closed() -> None:
    repository = create_disabled_review_queue_repository()

    with pytest.raises(ReviewQueueRepositoryDisabledError, match="get_by_review_item_id"):
        repository.get_by_review_item_id("review:r7bu:1")
    with pytest.raises(ReviewQueueRepositoryDisabledError, match="list_by_run_id"):
        repository.list_by_run_id("run:r7bu")


@pytest.mark.parametrize(
    "config",
    [
        {"dsn": "postgresql://user:secret@example/review_queue"},
        {"connection_string": "Server=example;Password=secret"},
        {"table_name": "review_queue_items"},
        {"output_path": "D:/unsafe/review_queue.json"},
        {"file_path": "D:/unsafe/review_queue.sqlite"},
        {"production_writer_config": {"enabled": True}},
        {"runtime_endpoint": "https://example.invalid/review_queue"},
    ],
)
def test_r7bu_arbitrary_production_config_is_rejected_without_leaking_values(config: dict[str, object]) -> None:
    with pytest.raises(ReviewQueueRepositoryDisabledError) as error:
        create_disabled_review_queue_repository(**config)

    message = str(error.value)
    assert "configuration is not accepted" in message
    assert "secret" not in message.lower()
    assert "postgresql" not in message.lower()
    assert "review_queue_items" not in message
    assert "D:/unsafe" not in message
    assert "example.invalid" not in message


def test_r7bu_custom_disabled_reason_is_not_accepted() -> None:
    with pytest.raises(ReviewQueueRepositoryDisabledError) as error:
        DisabledReviewQueueRepository(disabled_reason="secret source_text payload")

    assert "custom disabled reasons are not accepted" in str(error.value)
    assert "secret" not in str(error.value).lower()
    assert "source_text" not in str(error.value)


def test_r7bu_failure_message_does_not_leak_raw_payloads_or_secrets() -> None:
    repository = create_disabled_review_queue_repository()
    candidates = [
        {
            **_candidate(),
            "source_text": "full source text must not appear",
            "raw_mineru": {"content_list_v2": "raw"},
            "raw_excel": "raw workbook",
            "raw_ocr": "raw ocr",
            "raw_llm_response": "raw llm",
            "connection_string": "Server=example;Password=secret",
        }
    ]

    with pytest.raises(ReviewQueueRepositoryDisabledError) as error:
        repository.write_batch(candidates, run_id="run:r7bu")

    message = str(error.value)
    assert "full source text" not in message
    assert "raw" not in message.lower()
    assert "secret" not in message.lower()
    assert "connection" not in message.lower()


def test_r7bu_disabled_receipt_is_metadata_only_and_non_persisting() -> None:
    receipt = create_disabled_review_queue_repository().disabled_receipt()
    receipt_dict = receipt.as_dict()

    assert isinstance(receipt, ReviewQueueRepositoryWriteReceipt)
    assert receipt_dict["repository_status"] == DISABLED_STATUS
    assert receipt_dict["persistence_status"] == "NOT_PERSISTED"
    assert receipt_dict["writes_database"] is False
    assert receipt_dict["writes_filesystem"] is False
    assert receipt_dict["writes_network"] is False
    assert receipt_dict["writes_review_queue"] is False
    assert receipt_dict["writes_clean_data"] is False
    assert receipt_dict["writes_delivery"] is False
    assert receipt_dict["writes_export"] is False
    assert receipt_dict["database_write_count"] == 0
    assert receipt_dict["clean_data_write_count"] == 0
    assert receipt_dict["delivery_write_count"] == 0
    assert receipt_dict["readiness_gates"] == READINESS_GATES_CLOSED
    assert not (
        set(_walk_keys(receipt_dict))
        & {
            "source_text",
            "raw_mineru",
            "raw_excel",
            "raw_ocr",
            "raw_llm_response",
            "dsn",
            "connection_string",
            "output_path",
            "file_path",
            "production_writer_config",
            "clean_data_intent",
            "delivery_export_intent",
        }
    )


def test_r7bu_disabled_receipt_readiness_copy_is_mutation_safe() -> None:
    receipt = create_disabled_review_queue_repository().disabled_receipt()
    first = receipt.as_dict()
    first["readiness_gates"]["client_ready"] = True

    second = receipt.as_dict()

    assert second["readiness_gates"] == READINESS_GATES_CLOSED


def test_r7bu_module_has_no_db_io_network_storage_or_fake_repository_imports() -> None:
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
    forbidden_calls = {
        "connect",
        "dump",
        "dumps_to_file",
        "execute",
        "mkdir",
        "open",
        "remove",
        "rename",
        "replace",
        "rmdir",
        "to_csv",
        "to_excel",
        "unlink",
        "write",
        "write_text",
        "writelines",
    }

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


def test_r7bu_skeleton_has_no_runtime_enable_token_or_environment_activation() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "TEST_ONLY_ENABLE_TOKEN" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    assert "enabled: bool = True" not in source
    assert "sqlite3" not in source
    assert "sqlalchemy" not in source
    assert "psycopg" not in source


def test_r7bu_safety_rules_are_not_claimed_as_enabled_behavior() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "STRONG_EVIDENCE" not in source
    assert "clean_data_eligible" not in source
    assert "delivery_clean_admitted" not in source
    assert "production_ready\": True" not in source
    assert "formal_client_export_allowed\": True" not in source


def _walk_keys(value: object) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(_walk_keys(child))
    return keys
