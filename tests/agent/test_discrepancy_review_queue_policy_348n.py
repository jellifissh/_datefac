"""Tests for the R7AQ test-only discrepancy review queue policy prototype."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import pytest

from tests.agent.discrepancy_review_queue_policy_348n import (
    REQUIRED_REVIEW_ITEM_FIELDS,
    REVIEWER_ACTIONS,
    apply_reviewer_action,
    build_discrepancy_review_item,
    build_discrepancy_review_queue_items,
    candidate_clean_data_eligible,
    discrepancy_subtype,
    load_discrepancy_rows_fixture,
    unresolved_export_bucket,
)

FIXTURE_PATH = (
    Path(__file__).with_name("fixtures")
    / "discrepancy_review_queue"
    / "r7aq_discrepancy_rows_fixture.json"
)

REQUIRED_REVIEWER_ACTIONS = {
    "ACCEPT_CANDIDATE",
    "REJECT_CANDIDATE",
    "CORRECT_VALUE",
    "CORRECT_UNIT",
    "CORRECT_PERIOD",
    "CORRECT_METRIC",
    "MARK_NOT_IN_REPORT",
    "MARK_EVIDENCE_INSUFFICIENT",
    "REQUEST_REEXTRACTION",
    "REQUEST_MANUAL_SOURCE_CHECK",
}


def _fixture() -> dict[str, object]:
    return load_discrepancy_rows_fixture(FIXTURE_PATH)


def _rows() -> list[dict[str, object]]:
    return list(_fixture()["rows"])  # type: ignore[arg-type]


def _row(source_row_id: str) -> dict[str, object]:
    for row in _rows():
        if row["source_row_id"] == source_row_id:
            return row
    raise AssertionError(f"missing fixture row: {source_row_id}")


def _queue(preview_limit: int = 120) -> list[dict[str, object]]:
    payload = _fixture()
    return build_discrepancy_review_queue_items(
        payload["rows"],  # type: ignore[arg-type]
        run_id=str(payload["run_id"]),
        adapter_version=str(payload["adapter_version"]),
        input_file_hashes=payload["input_file_hashes"],  # type: ignore[arg-type]
        preview_limit=preview_limit,
    )


def test_r7aq_fixture_is_small_curated_and_covers_required_statuses() -> None:
    payload = _fixture()
    rows = _rows()

    assert payload["fixture_scope"] == "test_only_r7aq"
    assert FIXTURE_PATH.stat().st_size < 20000
    assert len(rows) == 8
    assert Counter(row["agreement_status"] for row in rows) == {
        "VERIFIED": 1,
        "DISAGREED": 2,
        "AMBIGUOUS": 2,
        "MISSING_EVIDENCE": 1,
        "PARSE_SKIPPED": 1,
        "UNVERIFIED": 1,
    }
    assert _row("table-conflict:R8:2026E")["evidence_type"] == "mineru_table_html_vs_paragraph"
    assert _row("repeated-ambiguous:R3")["risk_reason"] == "repeated ambiguous value"


def test_r7aq_verified_row_does_not_enter_discrepancy_queue_or_clean_data() -> None:
    payload = _fixture()
    verified = _row("verified:R1")

    item = build_discrepancy_review_item(
        verified,
        run_id=str(payload["run_id"]),
        adapter_version=str(payload["adapter_version"]),
        input_file_hashes=payload["input_file_hashes"],  # type: ignore[arg-type]
    )

    assert item is None
    assert candidate_clean_data_eligible(verified) is False
    assert all(item["source_row_id"] != "verified:R1" for item in _queue())


def test_r7aq_all_non_verified_statuses_enter_review_queue_with_expected_subqueues() -> None:
    queue = _queue()

    assert len(queue) == 7
    assert Counter(item["agreement_status"] for item in queue) == {
        "DISAGREED": 2,
        "AMBIGUOUS": 2,
        "MISSING_EVIDENCE": 1,
        "PARSE_SKIPPED": 1,
        "UNVERIFIED": 1,
    }
    assert {item["review_subqueue"] for item in queue} == {
        "evidence_conflict_queue",
        "evidence_ambiguity_queue",
        "missing_evidence_queue",
        "parse_schema_queue",
        "partial_anchor_queue",
    }


def test_r7aq_severity_policy_matches_discrepancy_design() -> None:
    by_row = {item["source_row_id"]: item for item in _queue()}

    assert by_row["disagreed:R7:2026E"]["severity"] == "HIGH"
    assert by_row["ambiguous:R10:2026E"]["severity"] == "MEDIUM_HIGH"
    assert by_row["missing:R14"]["severity"] == "MEDIUM"
    assert by_row["parse:R4"]["severity"] == "LOW"
    assert by_row["unverified:R12"]["severity"] == "MEDIUM"
    assert by_row["repeated-ambiguous:R3"]["severity"] == "MEDIUM_HIGH"


def test_r7aq_non_verified_items_are_clean_data_ineligible_and_review_only_export() -> None:
    for item in _queue():
        assert item["clean_data_eligible"] is False
        assert item["export_bucket"] == "discrepancy_review_output"
        assert unresolved_export_bucket(item) == "discrepancy_review_output"


def test_r7aq_review_item_schema_is_metadata_first() -> None:
    item = _queue()[0]

    assert set(REQUIRED_REVIEW_ITEM_FIELDS).issubset(item)
    assert "source_text" not in item
    assert "full_source_text" not in item
    assert "source_text_full" not in item
    assert "text" not in item
    assert "matched_text_sha256" in item
    assert "input_file_hashes" in item


def test_r7aq_evidence_preview_is_bounded_and_does_not_dump_full_source_text() -> None:
    payload = _fixture()
    row = _row("table-conflict:R8:2026E")
    item = build_discrepancy_review_item(
        row,
        run_id=str(payload["run_id"]),
        adapter_version=str(payload["adapter_version"]),
        input_file_hashes=payload["input_file_hashes"],  # type: ignore[arg-type]
        preview_limit=48,
    )

    assert item is not None
    assert len(item["evidence_preview"]) <= 48
    assert row["full_source_text"] not in json.dumps(item, ensure_ascii=False)
    for alternative in item["alternative_evidence_candidates"]:
        assert len(alternative["preview"]) <= 48


def test_r7aq_review_item_id_and_audit_hash_are_deterministic() -> None:
    payload = _fixture()
    row = _row("ambiguous:R10:2026E")

    first = build_discrepancy_review_item(
        row,
        run_id=str(payload["run_id"]),
        adapter_version=str(payload["adapter_version"]),
        input_file_hashes=payload["input_file_hashes"],  # type: ignore[arg-type]
    )
    second = build_discrepancy_review_item(
        row,
        run_id=str(payload["run_id"]),
        adapter_version=str(payload["adapter_version"]),
        input_file_hashes=payload["input_file_hashes"],  # type: ignore[arg-type]
    )

    assert first is not None
    assert second is not None
    assert first["review_item_id"] == second["review_item_id"]
    assert first["audit_hash"] == second["audit_hash"]


def test_r7aq_reviewer_actions_cover_required_model_and_do_not_bypass_policy_gate() -> None:
    item = _queue()[0]

    assert REQUIRED_REVIEWER_ACTIONS.issubset(set(REVIEWER_ACTIONS))

    accepted_without_gate = apply_reviewer_action(
        item,
        "ACCEPT_CANDIDATE",
        reviewer_note="Human reviewer accepts candidate for re-audit.",
    )
    accepted_with_gate = apply_reviewer_action(
        item,
        "ACCEPT_CANDIDATE",
        reviewer_note="Human reviewer accepts candidate for re-audit.",
        explicit_policy_gate=True,
    )

    assert accepted_without_gate["review_status"] == "RESOLVED_ACCEPTED"
    assert accepted_without_gate["clean_data_eligible"] is False
    assert accepted_with_gate["clean_data_eligible"] is True
    assert unresolved_export_bucket(accepted_with_gate) == "requires_reaudit_before_clean_delivery"


def test_r7aq_reviewer_action_validation_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="unsupported reviewer action"):
        apply_reviewer_action(_queue()[0], "AUTO_PROMOTE_TO_CLEAN")


def test_r7aq_parse_skipped_is_separate_from_true_evidence_disagreement() -> None:
    by_row = {item["source_row_id"]: item for item in _queue()}

    assert by_row["parse:R4"]["review_subqueue"] == "parse_schema_queue"
    assert by_row["parse:R4"]["discrepancy_subtype"] == "PARSE_SCHEMA_ISSUE"
    assert by_row["disagreed:R7:2026E"]["review_subqueue"] == "evidence_conflict_queue"
    assert by_row["disagreed:R7:2026E"]["discrepancy_subtype"] == "DISAGREED"


def test_r7aq_table_vs_paragraph_conflict_and_repeated_ambiguity_are_explicit() -> None:
    table_conflict = build_discrepancy_review_item(
        _row("table-conflict:R8:2026E"),
        run_id="r7aq_fixture_run_001",
        adapter_version="r7aq_discrepancy_policy_test_only_v1",
        input_file_hashes={"datefac_excel": "sha256:x", "mineru_content_list_v2": "sha256:y"},
    )
    repeated = build_discrepancy_review_item(
        _row("repeated-ambiguous:R3"),
        run_id="r7aq_fixture_run_001",
        adapter_version="r7aq_discrepancy_policy_test_only_v1",
        input_file_hashes={"datefac_excel": "sha256:x", "mineru_content_list_v2": "sha256:y"},
    )

    assert table_conflict is not None
    assert repeated is not None
    assert discrepancy_subtype(_row("table-conflict:R8:2026E")) == "TABLE_PARAGRAPH_CONFLICT"
    assert table_conflict["discrepancy_subtype"] == "TABLE_PARAGRAPH_CONFLICT"
    assert len(table_conflict["alternative_evidence_candidates"]) == 2
    assert repeated["discrepancy_subtype"] == "REPEATED_AMBIGUOUS_VALUE"
    assert len(repeated["alternative_evidence_candidates"]) == 2
