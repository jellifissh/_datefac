import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from tests.agent.review_queue_fake_repository_boundary_348n import (
    MODE,
    READINESS_GATES_CLOSED,
    SAFE_FAKE_REPOSITORY_ROW_FIELDS,
    TEST_ONLY_FAKE_REPOSITORY_ENABLE_TOKEN,
    FakeReviewQueueRepository348N,
    FakeReviewQueueRepositoryBoundaryError,
    persist_candidate_batch_to_fake_repository_348n,
    required_fake_repository_row_fields_348n,
    validate_persistence_candidate_batch_for_fake_repository_348n,
)
from tests.agent.review_queue_persistence_contract_348n import (
    TEST_ONLY_PERSISTENCE_ENABLE_TOKEN,
    ReviewQueuePersistenceContractConfig,
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


R7BQ_FIXTURE_PATH = Path("tests/agent/fixtures/discrepancy_review_queue/r7bq_fake_repository_boundary_fixture.json")
R7BC_FIXTURE_PATH = Path("tests/agent/fixtures/discrepancy_review_queue/r7bc_review_queue_writer_contract_fixture.json")
MODULE_PATH = Path("tests/agent/review_queue_fake_repository_boundary_348n.py")


def _fixture() -> dict:
    payload = json.loads(R7BQ_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_scope"] == "test_only_r7bq"
    return payload


def _r7bc_fixture() -> dict:
    return json.loads(R7BC_FIXTURE_PATH.read_text(encoding="utf-8"))


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


def _valid_adapter_candidate() -> dict:
    return deepcopy(_r7bc_fixture()["valid_adapter_candidate_payload"])


def _dry_run_integration_output() -> dict:
    return build_review_queue_writer_dry_run_integration_preview(_valid_adapter_candidate(), _integration_config())


def _schema_alignment_preview() -> dict:
    return build_review_queue_writer_schema_alignment_preview(_dry_run_integration_output(), _schema_config())


def _candidate_batch() -> dict:
    return build_review_queue_persistence_candidate_batch(_schema_alignment_preview(), _persistence_config())


def _persist(batch: dict, repository: FakeReviewQueueRepository348N | None = None) -> dict:
    return persist_candidate_batch_to_fake_repository_348n(
        batch,
        allow_test_only_fake_repository=True,
        test_only_enable_token=TEST_ONLY_FAKE_REPOSITORY_ENABLE_TOKEN,
        repository=repository,
    )


def _negative_case(case_id: str) -> dict:
    cases = {case["case_id"]: case for case in _fixture()["negative_cases"]}
    return deepcopy(cases[case_id])


def _payload_for_negative_case(case_id: str) -> dict:
    case = _negative_case(case_id)
    payload_kind = case.get("payload_kind")
    if payload_kind == "schema_alignment_preview":
        return _schema_alignment_preview()
    if payload_kind == "dry_run_integration_output":
        return _dry_run_integration_output()
    if payload_kind == "writer_preview":
        return _dry_run_integration_output()["writer_dry_run_preview"]
    if payload_kind == "adapter_candidate":
        return _valid_adapter_candidate()
    if payload_kind == "user_direct_fake_repository_row":
        return {
            "fake_repository_rows": [
                {
                    "review_item_id": "user-direct-row",
                    "record_payload_hash": "0" * 64,
                }
            ]
        }
    payload = _candidate_batch()
    mutation = case.get("mutation")
    if mutation:
        _apply_mutation(payload, mutation)
    return payload


def _apply_mutation(payload: dict, mutation: dict) -> None:
    action = mutation["action"]
    if action == "set":
        _set_path(payload, mutation["path"], deepcopy(mutation["value"]))
        return
    if action == "delete":
        _delete_path(payload, mutation["path"])
        return
    if action == "duplicate_key_different_hash":
        records = payload["review_queue_persistence_candidate_batch"]
        records[1]["idempotency_key"] = records[0]["idempotency_key"]
        records[1]["candidate_value"] = f'{records[1]["candidate_value"]}-changed'
        records[1]["normalized_candidate_value"] = f'{records[1]["normalized_candidate_value"]}-changed'
        _refresh_candidate_hash(records[1])
        _refresh_batch_summary(payload)
        return
    if action == "duplicate_review_item_different_key":
        records = payload["review_queue_persistence_candidate_batch"]
        records[1]["review_item_id"] = records[0]["review_item_id"]
        records[1]["candidate_value"] = f'{records[1]["candidate_value"]}-changed'
        records[1]["normalized_candidate_value"] = f'{records[1]["normalized_candidate_value"]}-changed'
        records[1]["idempotency_key"] = _hash_json(
            {
                "r7bq": "different-idempotency-key",
                "review_item_id": records[1]["review_item_id"],
                "candidate_value": records[1]["candidate_value"],
            }
        )
        _refresh_candidate_hash(records[1])
        _refresh_batch_summary(payload)
        return
    raise AssertionError(f"unsupported mutation action: {action}")


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


def _refresh_candidate_hash(candidate: dict) -> None:
    candidate["record_payload_hash"] = _hash_json(
        {key: value for key, value in candidate.items() if key != "record_payload_hash"}
    )


def _refresh_batch_summary(payload: dict) -> None:
    records = payload["review_queue_persistence_candidate_batch"]
    status_counts: dict[str, int] = {}
    for record in records:
        status_counts[record["agreement_status"]] = status_counts.get(record["agreement_status"], 0) + 1
    summary = payload["persistence_summary"]
    summary["candidate_count"] = len(records)
    summary["review_bound_record_count"] = len(records)
    summary["status_counts"] = status_counts
    summary["persistence_candidate_batch_hash"] = _hash_json(records)


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


def test_r7bq_fixture_is_small_curated_and_complete() -> None:
    fixture = _fixture()

    assert set(fixture) == {"schema_version", "fixture_scope", "base_case", "valid_cases", "negative_cases"}
    assert fixture["schema_version"] == "r7bq_fake_repository_boundary_fixture_v1"
    assert fixture["base_case"] == "valid_schema_alignment_preview_mixed_records"
    assert set(fixture["valid_cases"]) == {
        "valid_candidate_batch",
        "valid_duplicate_retry_same_key_same_hash",
    }
    assert {case["case_id"] for case in fixture["negative_cases"]} == {
        "invalid_missing_test_fake_repo_flag",
        "invalid_direct_schema_alignment_preview",
        "invalid_direct_dry_run_integration_output",
        "invalid_direct_writer_preview",
        "invalid_direct_adapter_candidate",
        "invalid_user_direct_fake_repository_row",
        "invalid_db_dsn",
        "invalid_output_path",
        "invalid_readiness_open",
        "invalid_clean_data_intent",
        "invalid_delivery_export_intent",
        "invalid_nested_forbidden_payload",
        "invalid_duplicate_idempotency_conflict",
        "invalid_review_item_conflict",
        "invalid_mixed_batch_partial_write_attempt",
    }
    assert R7BQ_FIXTURE_PATH.stat().st_size < 12000


def test_r7bq_default_disabled_fails_closed_without_write() -> None:
    repository = FakeReviewQueueRepository348N()
    result = persist_candidate_batch_to_fake_repository_348n(_candidate_batch(), repository=repository)

    assert result["fake_repository_status"] == "DISABLED"
    assert result["reason"] == "disabled_by_default"
    assert result["fake_repository_write_receipt"] is None
    assert result["fake_repository_state_snapshot"]["record_count"] == 0
    assert repository.state_snapshot()["record_count"] == 0


def test_r7bq_explicit_test_only_fake_repository_token_required() -> None:
    with pytest.raises(FakeReviewQueueRepositoryBoundaryError, match="test-only fake repository token"):
        persist_candidate_batch_to_fake_repository_348n(
            _candidate_batch(),
            allow_test_only_fake_repository=True,
            test_only_enable_token="wrong-token",
        )


def test_r7bq_valid_candidate_batch_writes_only_in_memory() -> None:
    repository = FakeReviewQueueRepository348N()
    result = _persist(_candidate_batch(), repository=repository)
    receipt = result["fake_repository_write_receipt"]
    state = result["fake_repository_state_snapshot"]

    assert result["fake_repository_status"] == "ENABLED_TEST_ONLY_FAKE_REPOSITORY_WRITE"
    assert result["mode"] == MODE
    assert receipt["mode"] == MODE
    assert receipt["row_count"] == 2
    assert receipt["written_count"] == 2
    assert receipt["idempotent_noop_count"] == 0
    assert state["record_count"] == 2
    assert state["database_write_count"] == 0
    assert state["filesystem_write_count"] == 0
    assert state["export_write_count"] == 0
    assert state["readiness_gates"] == READINESS_GATES_CLOSED
    assert repository.state_snapshot() == state


def test_r7bq_write_receipt_contains_safe_deterministic_metadata() -> None:
    repository_a = FakeReviewQueueRepository348N()
    repository_b = FakeReviewQueueRepository348N()
    first = _persist(_candidate_batch(), repository=repository_a)["fake_repository_write_receipt"]
    second = _persist(_candidate_batch(), repository=repository_b)["fake_repository_write_receipt"]

    assert first == second
    assert set(first) == {
        "status",
        "mode",
        "row_count",
        "written_count",
        "idempotent_noop_count",
        "idempotency_keys",
        "record_payload_hashes",
        "batch_payload_hash",
        "repository_state_hash",
        "boundary_version",
        "readiness_gates",
        "clean_data_write_count",
        "delivery_write_count",
        "filesystem_write_count",
        "database_write_count",
        "export_write_count",
        "boundary_flags",
    }
    assert first["status"] == "WRITE_ACCEPTED"
    assert first["readiness_gates"] == READINESS_GATES_CLOSED
    assert first["boundary_flags"]["writes_database"] is False
    assert first["boundary_flags"]["writes_clean_data"] is False
    assert first["boundary_flags"]["verified_promotes_to_strong_evidence"] is False


def test_r7bq_state_contains_safe_candidate_rows_only() -> None:
    state = _persist(_candidate_batch())["fake_repository_state_snapshot"]
    forbidden = {
        "source_text",
        "full_source_text",
        "raw_mineru",
        "raw_excel",
        "raw_parser_payload",
        "llm_response",
        "vlm_response",
        "clean_data",
        "clean_data_eligible",
        "delivery_payload",
        "export_payload",
        "database_url",
        "dsn",
        "output_path",
        "production_repository_config",
        "test_only_enable_token",
    }

    assert required_fake_repository_row_fields_348n() == SAFE_FAKE_REPOSITORY_ROW_FIELDS
    for record in state["records"]:
        assert tuple(record) == SAFE_FAKE_REPOSITORY_ROW_FIELDS
        assert not (_walk_keys(record) & forbidden)
        assert record["agreement_status"] in {"DISAGREED", "AMBIGUOUS", "MISSING_EVIDENCE", "PARSE_SKIPPED", "UNVERIFIED"}
        assert record["record_payload_hash"] == _hash_json(
            {key: value for key, value in record.items() if key != "record_payload_hash"}
        )


@pytest.mark.parametrize(
    "case_id",
    [
        "invalid_direct_schema_alignment_preview",
        "invalid_direct_dry_run_integration_output",
        "invalid_direct_writer_preview",
        "invalid_direct_adapter_candidate",
        "invalid_user_direct_fake_repository_row",
        "invalid_db_dsn",
        "invalid_output_path",
        "invalid_readiness_open",
        "invalid_clean_data_intent",
        "invalid_delivery_export_intent",
        "invalid_nested_forbidden_payload",
        "invalid_duplicate_idempotency_conflict",
        "invalid_review_item_conflict",
        "invalid_mixed_batch_partial_write_attempt",
    ],
)
def test_r7bq_negative_cases_fail_closed(case_id: str) -> None:
    case = _negative_case(case_id)

    with pytest.raises(FakeReviewQueueRepositoryBoundaryError, match=case["expected_error"]):
        _persist(_payload_for_negative_case(case_id))


def test_r7bq_missing_required_candidate_fields_rejected() -> None:
    payload = _candidate_batch()
    _delete_path(payload, "review_queue_persistence_candidate_batch.0.audit_hash")
    _refresh_batch_summary(payload)

    with pytest.raises(FakeReviewQueueRepositoryBoundaryError, match="audit_hash"):
        _persist(payload)


def test_r7bq_raw_artifacts_full_text_and_unbounded_evidence_rejected() -> None:
    raw_cases = [
        ("review_queue_persistence_candidate_batch.0.source_trace.raw_excel", {"sheet": "raw"}),
        ("review_queue_persistence_candidate_batch.0.source_trace.raw_parser_payload", {"pages": []}),
        ("review_queue_persistence_candidate_batch.0.source_trace.raw_llm_response", "raw llm"),
        ("review_queue_persistence_candidate_batch.0.full_source_text", "forbidden full source text"),
        ("review_queue_persistence_candidate_batch.0.evidence_preview", "X" * 200),
    ]
    for path, value in raw_cases:
        payload = _candidate_batch()
        _set_path(payload, path, value)
        if path.endswith("evidence_preview"):
            _refresh_candidate_hash(payload["review_queue_persistence_candidate_batch"][0])
            _refresh_batch_summary(payload)
        with pytest.raises(FakeReviewQueueRepositoryBoundaryError):
            _persist(payload)


def test_r7bq_same_batch_retry_is_idempotent_noop_without_duplicate_rows() -> None:
    repository = FakeReviewQueueRepository348N()
    first = _persist(_candidate_batch(), repository=repository)
    second = _persist(_candidate_batch(), repository=repository)

    assert first["fake_repository_write_receipt"]["written_count"] == 2
    assert first["fake_repository_write_receipt"]["idempotent_noop_count"] == 0
    assert second["fake_repository_write_receipt"]["written_count"] == 0
    assert second["fake_repository_write_receipt"]["idempotent_noop_count"] == 2
    assert repository.state_snapshot()["record_count"] == 2


def test_r7bq_same_idempotency_key_different_hash_fails_and_rolls_back() -> None:
    repository = FakeReviewQueueRepository348N()
    _persist(_candidate_batch(), repository=repository)
    before = repository.state_snapshot()
    payload = _candidate_batch()
    payload["review_queue_persistence_candidate_batch"][0]["candidate_value"] = "999999"
    payload["review_queue_persistence_candidate_batch"][0]["normalized_candidate_value"] = "999999"
    _refresh_candidate_hash(payload["review_queue_persistence_candidate_batch"][0])
    _refresh_batch_summary(payload)

    with pytest.raises(FakeReviewQueueRepositoryBoundaryError, match="idempotency_key conflict"):
        _persist(payload, repository=repository)

    assert repository.state_snapshot() == before


def test_r7bq_same_review_item_different_idempotency_fails_and_rolls_back() -> None:
    repository = FakeReviewQueueRepository348N()
    _persist(_candidate_batch(), repository=repository)
    before = repository.state_snapshot()
    payload = _candidate_batch()
    payload["review_queue_persistence_candidate_batch"][0]["idempotency_key"] = _hash_json(
        {
            "r7bq": "conflicting-review-item",
            "review_item_id": payload["review_queue_persistence_candidate_batch"][0]["review_item_id"],
        }
    )
    _refresh_candidate_hash(payload["review_queue_persistence_candidate_batch"][0])
    _refresh_batch_summary(payload)

    with pytest.raises(FakeReviewQueueRepositoryBoundaryError, match="review_item_id conflict"):
        _persist(payload, repository=repository)

    assert repository.state_snapshot() == before


def test_r7bq_invalid_row_anywhere_leaves_state_unchanged() -> None:
    repository = FakeReviewQueueRepository348N()
    _persist(_candidate_batch(), repository=repository)
    before = repository.state_snapshot()
    payload = _candidate_batch()
    _set_path(payload, "review_queue_persistence_candidate_batch.1.source_trace.raw_mineru", {"raw": "forbidden"})

    with pytest.raises(FakeReviewQueueRepositoryBoundaryError):
        _persist(payload, repository=repository)

    assert repository.state_snapshot() == before


def test_r7bq_mutation_isolation_for_input_state_and_receipt() -> None:
    repository = FakeReviewQueueRepository348N()
    payload = _candidate_batch()
    result = _persist(payload, repository=repository)
    receipt = result["fake_repository_write_receipt"]
    state = result["fake_repository_state_snapshot"]

    payload["review_queue_persistence_candidate_batch"][0]["evidence_preview"] = "mutated input"
    receipt["idempotency_keys"][0] = "mutated-receipt"
    state["records"][0]["evidence_preview"] = "mutated-state-snapshot"

    fresh_state = repository.state_snapshot()
    assert fresh_state["records"][0]["evidence_preview"] != "mutated input"
    assert fresh_state["records"][0]["evidence_preview"] != "mutated-state-snapshot"
    assert fresh_state["records"][0]["idempotency_key"] != "mutated-receipt"


def test_r7bq_verified_clean_delivery_and_readiness_boundaries_remain_closed() -> None:
    payload = _candidate_batch()
    promoted = deepcopy(payload)
    promoted["review_queue_persistence_candidate_batch"][0]["evidence_level"] = "STRONG_EVIDENCE"
    with pytest.raises(FakeReviewQueueRepositoryBoundaryError, match="STRONG_EVIDENCE"):
        _persist(promoted)

    verified = deepcopy(payload)
    verified["review_queue_persistence_candidate_batch"][0]["agreement_status"] = "VERIFIED"
    _refresh_candidate_hash(verified["review_queue_persistence_candidate_batch"][0])
    _refresh_batch_summary(verified)
    with pytest.raises(FakeReviewQueueRepositoryBoundaryError, match="non-VERIFIED"):
        _persist(verified)

    result = _persist(payload)
    receipt = result["fake_repository_write_receipt"]
    assert receipt["clean_data_write_count"] == 0
    assert receipt["delivery_write_count"] == 0
    assert receipt["readiness_gates"] == READINESS_GATES_CLOSED
    assert result["fake_repository_state_snapshot"]["boundary_flags"]["verified_auto_clean"] is False


def test_r7bq_repository_config_and_production_intents_are_rejected() -> None:
    payload = _candidate_batch()
    with pytest.raises(FakeReviewQueueRepositoryBoundaryError, match="production repository config"):
        persist_candidate_batch_to_fake_repository_348n(
            payload,
            allow_test_only_fake_repository=True,
            test_only_enable_token=TEST_ONLY_FAKE_REPOSITORY_ENABLE_TOKEN,
            repository_config={"database_url": "postgres://forbidden"},
        )

    for path, value in (
        ("metadata.production_repository_config", {"enabled": True}),
        ("metadata.production_hook", True),
        ("metadata.writes_database", True),
        ("metadata.writes_export", True),
    ):
        unsafe = _candidate_batch()
        _set_path(unsafe, path, value)
        with pytest.raises(FakeReviewQueueRepositoryBoundaryError):
            _persist(unsafe)


def test_r7bq_validate_candidate_batch_returns_deepcopy() -> None:
    batch = _candidate_batch()
    candidates = validate_persistence_candidate_batch_for_fake_repository_348n(batch)
    candidates[0]["evidence_preview"] = "mutated returned candidate"

    fresh_candidates = validate_persistence_candidate_batch_for_fake_repository_348n(batch)
    assert fresh_candidates[0]["evidence_preview"] != "mutated returned candidate"


def test_r7bq_module_has_no_io_db_export_or_production_hook() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "datefac_agent",
        "fitz",
        "httpx",
        "mineru",
        "openai",
        "os",
        "pandas",
        "pathlib",
        "pdfplumber",
        "psycopg2",
        "pymysql",
        "pypdf",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
    }
    forbidden_calls = {
        "connect",
        "dump",
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
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
