from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path

from datefac_agent.reconciliation.mineru_original_reconciliation_348n import (
    CONFLICT,
    EVIDENCE_PREVIEW_LIMIT,
    MATCH,
    MINERU_ONLY,
    ORIGINAL_ONLY,
    READINESS_GATES_CLOSED,
    build_review_queue_candidates,
    extract_mineru_records,
    extract_original_records,
    load_and_reconcile,
    load_json_artifact,
    normalize_metric_name,
    normalize_numeric_value,
    normalize_period,
    reconcile_mineru_original,
)

MINERU_FIXTURE_PATH = Path(
    "tests/agent/fixtures/mineru_original_reconciliation/mineru_content_list_sample.json"
)
ORIGINAL_FIXTURE_PATH = Path(
    "tests/agent/fixtures/mineru_original_reconciliation/original_extraction_sample.json"
)
MODULE_PATH = Path("datefac_agent/reconciliation/mineru_original_reconciliation_348n.py")


def _mineru_fixture() -> list:
    return json.loads(MINERU_FIXTURE_PATH.read_text(encoding="utf-8"))


def _original_fixture() -> dict:
    return json.loads(ORIGINAL_FIXTURE_PATH.read_text(encoding="utf-8"))


def _rows_by_metric(result: dict) -> dict[str, dict]:
    return {row["metric"]: row for row in result["comparison_rows"]}


def test_r7cc_loads_tiny_fixtures() -> None:
    mineru = load_json_artifact(MINERU_FIXTURE_PATH)
    original = load_json_artifact(ORIGINAL_FIXTURE_PATH)

    assert isinstance(mineru, list)
    assert isinstance(original, dict)
    assert MINERU_FIXTURE_PATH.stat().st_size < 10000
    assert ORIGINAL_FIXTURE_PATH.stat().st_size < 10000


def test_r7cc_metric_normalization_aliases() -> None:
    assert normalize_metric_name("Revenue") == "revenue"
    assert normalize_metric_name("营业收入") == "revenue"
    assert normalize_metric_name("归母净利润") == "net_profit"
    assert normalize_metric_name("EPS") == "eps"
    assert normalize_metric_name("净资产收益率") == "roe"
    assert normalize_metric_name("unknown metric") is None


def test_r7cc_numeric_and_period_normalization() -> None:
    assert normalize_numeric_value("1,000.00") == "1000"
    assert normalize_numeric_value("12.50%") == "12.5"
    assert normalize_numeric_value("(12.00)") == "-12"
    assert normalize_numeric_value("not numeric") is None
    assert normalize_period("2023年度") == "2023"
    assert normalize_period("FY2023") == "2023"


def test_r7cc_extracts_mineru_and_original_records() -> None:
    mineru_records = extract_mineru_records(_mineru_fixture())
    original_records = extract_original_records(_original_fixture())

    assert [record["metric"] for record in mineru_records] == ["Revenue", "Net Profit", "EPS"]
    assert [record["metric"] for record in original_records] == ["Revenue", "Net Profit", "ROE"]
    assert mineru_records[0]["source_trace"]["page_number"] == 1
    assert original_records[0]["source_trace"]["source_row_id"] == "original:revenue:2023"


def test_r7cc_comparison_statuses_cover_required_demo_cases() -> None:
    result = reconcile_mineru_original(_mineru_fixture(), _original_fixture())
    rows = _rows_by_metric(result)

    assert rows["Revenue"]["status"] == MATCH
    assert rows["Revenue"]["mineru_value"] == "1000"
    assert rows["Revenue"]["original_value"] == "1000"
    assert rows["Revenue"]["review_required"] is False

    assert rows["Net Profit"]["status"] == CONFLICT
    assert rows["Net Profit"]["mineru_value"] == "200"
    assert rows["Net Profit"]["original_value"] == "210"
    assert rows["Net Profit"]["review_required"] is True

    assert rows["EPS"]["status"] == MINERU_ONLY
    assert rows["EPS"]["mineru_value"] == "2.5"
    assert rows["EPS"]["original_value"] is None

    assert rows["ROE"]["status"] == ORIGINAL_ONLY
    assert rows["ROE"]["mineru_value"] is None
    assert rows["ROE"]["original_value"] == "12.5"


def test_r7cc_review_candidates_only_for_review_required_statuses() -> None:
    result = reconcile_mineru_original(_mineru_fixture(), _original_fixture())
    candidates = result["review_queue_candidates"]

    assert [candidate["agreement_status"] for candidate in candidates] == [
        CONFLICT,
        MINERU_ONLY,
        ORIGINAL_ONLY,
    ]
    assert all(candidate["review_status"] == "PENDING_REVIEW" for candidate in candidates)
    assert all(candidate["clean_data_eligible"] is False for candidate in candidates)
    assert all(candidate["readiness_gates"] == READINESS_GATES_CLOSED for candidate in candidates)
    assert all(candidate["blocked_delivery_reason"] for candidate in candidates)


def test_r7cc_bounded_evidence_preview() -> None:
    mineru = _mineru_fixture()
    mineru[0][0]["content"]["rows"][1]["evidence_preview"] = "x" * 1000

    result = reconcile_mineru_original(mineru, _original_fixture())

    assert all(len(row["evidence_preview"]) <= EVIDENCE_PREVIEW_LIMIT for row in result["comparison_rows"])
    assert all(len(candidate["evidence_preview"]) <= EVIDENCE_PREVIEW_LIMIT for candidate in result["review_queue_candidates"])


def test_r7cc_inputs_are_not_mutated() -> None:
    mineru = _mineru_fixture()
    original = _original_fixture()
    mineru_before = deepcopy(mineru)
    original_before = deepcopy(original)

    reconcile_mineru_original(mineru, original)

    assert mineru == mineru_before
    assert original == original_before


def test_r7cc_deterministic_output() -> None:
    first = reconcile_mineru_original(_mineru_fixture(), _original_fixture())
    second = reconcile_mineru_original(_mineru_fixture(), _original_fixture())

    assert first == second
    assert load_and_reconcile(MINERU_FIXTURE_PATH, ORIGINAL_FIXTURE_PATH) == first


def test_r7cc_review_candidates_can_be_rebuilt_from_comparison_rows() -> None:
    result = reconcile_mineru_original(_mineru_fixture(), _original_fixture())

    assert build_review_queue_candidates(result["comparison_rows"]) == result["review_queue_candidates"]
    assert result["summary"] == {
        "comparison_row_count": 4,
        "review_required_count": 3,
        "match_count": 1,
        "conflict_count": 1,
        "mineru_only_count": 1,
        "original_only_count": 1,
        "unparseable_count": 0,
        "readiness_gates": READINESS_GATES_CLOSED,
    }


def test_r7cc_module_has_no_db_network_llm_ocr_imports() -> None:
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
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "psycopg2",
        "pymysql",
        "mysql",
        "asyncpg",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "pytesseract",
        "easyocr",
        "paddleocr",
        "mineru",
    }

    assert imported_names.isdisjoint(forbidden_imports)
    assert all(module not in forbidden_imports for module in imported_from)
    assert "client_ready = true" not in source.lower()
    assert "production_ready = true" not in source.lower()
