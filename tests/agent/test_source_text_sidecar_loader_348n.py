"""Tests for the R7AF test-only source_text sidecar loader."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

import pytest

from datefac_agent.audit.evidence_checker import audit_evidence_presence
from datefac_agent.delivery.evidence_index_writer import write_evidence_index
from datefac_agent.review.review_queue_builder import build_row_audit_result, build_review_queue_rows
from datefac_agent.schemas.audit_models import AuditIssue, SourceTextEvidence, SpreadsheetRow
from tests.agent.source_text_sidecar_loader_348n import (
    SourceTextSidecarValidationError,
    load_source_text_sidecar_fixture,
)
from tools.run_agent_excel_intake_audit_348a import build_manifest

FIXTURE_PATH = (
    Path(__file__).with_name("fixtures")
    / "source_text_sidecars"
    / "r7af_source_text_sidecar__basic_positive_negative__v1.json"
)
SOURCE_PDF_ID = "source-pdf-001"
LOCATOR = "p3:table:row:revenue"
SOURCE_TEXT = "Revenue 2023 123.45"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _valid_record(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "source_text_id": "st-valid-001",
        "source_document_id": SOURCE_PDF_ID,
        "page_number": 3,
        "locator": LOCATOR,
        "text_kind": "table_row",
        "text": SOURCE_TEXT,
        "text_sha256": _sha256(SOURCE_TEXT),
        "char_count": len(SOURCE_TEXT),
        "trusted_source": True,
        "extraction_method": "fixture_manual",
    }
    values.update(overrides)
    return values


def _valid_payload(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "schema_version": 1,
        "fixture_scope": "test_only",
        "records": [_valid_record()],
    }
    values.update(overrides)
    return values


def _write_payload(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "source_text_sidecar.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_raw(tmp_path: Path, raw_json: str) -> Path:
    path = tmp_path / "source_text_sidecar.json"
    path.write_text(raw_json, encoding="utf-8")
    return path


def _make_row(
    *,
    metric_name: str = LOCATOR,
    explicit_evidence_ref: str = "page 3",
    period_values: dict[str, object] | None = None,
    row_type: str = "STRICT_FINANCIAL_TABLE_ROW",
) -> SpreadsheetRow:
    values = period_values or {"2023": "123.45"}
    return SpreadsheetRow(
        source_excel_path="demo.xlsx",
        sheet_name="source_text_sidecar_fixture",
        row_index=3,
        column_names=["metric", *values.keys()],
        raw_values={"metric": metric_name, **values},
        metric_name=metric_name,
        period_values=values,
        explicit_evidence_ref=explicit_evidence_ref,
        row_type=row_type,
    )


def _build_result(
    records: list[SourceTextEvidence] | None,
    *,
    row: SpreadsheetRow | None = None,
    pdf_id: str = SOURCE_PDF_ID,
    issues: list[AuditIssue] | None = None,
):
    row = row or _make_row()
    evidence_issues, evidence_refs, evidence_level = audit_evidence_presence(row, pdf_id)
    return build_row_audit_result(
        row,
        issues if issues is not None else [],
        evidence_refs,
        evidence_level,
        source_text_index=records,
    )


def _review_issue() -> AuditIssue:
    return AuditIssue(
        code="r7af_review_fixture",
        severity="warning",
        category="evidence",
        message="R7AF review queue fixture.",
    )


def _manifest() -> dict[str, object]:
    summary_values: dict[str, object] = {
        "fail_count": 0,
        "row_count_audited": 1,
        "pass_count": 0,
        "review_count": 1,
        "issue_count_total": 0,
        "unit_issue_count": 0,
        "period_issue_count": 0,
        "valuation_issue_count": 0,
        "evidence_issue_count": 0,
        "strong_evidence_count": 0,
        "weak_evidence_count": 1,
        "missing_evidence_count": 0,
        "not_applicable_evidence_count": 0,
        "weak_evidence_issue_count": 0,
        "missing_evidence_issue_count": 0,
        "strict_financial_table_row_count": 0,
        "market_reference_row_count": 1,
        "narrative_assertion_count": 0,
        "normalized_testset_record_row_count": 0,
        "testset_supporting_row_count": 0,
        "unknown_row_count": 0,
        "clean_data_row_count": 0,
        "review_queue_row_count": 1,
        "internal_clean_candidate_count": 0,
        "internal_reference_candidate_count": 0,
        "narrative_review_count": 0,
        "review_required_count": 1,
        "excluded_from_clean_data_count": 0,
    }
    return build_manifest(
        "REVIEW_REQUIRED",
        type("Intake", (), {"sheet_count": 1, "row_count_total": 1})(),
        type("Summary", (), summary_values)(),
        SOURCE_PDF_ID,
        "demo.xlsx",
        "output/demo",
    )


def test_r7af_valid_json_sidecar_loads_source_text_evidence() -> None:
    records = load_source_text_sidecar_fixture(FIXTURE_PATH)

    assert len(records) == 1
    record = records[0]
    assert record.source_text_id == "st-valid-001"
    assert record.source_document_id == SOURCE_PDF_ID
    assert record.page_number == 3
    assert record.locator == LOCATOR
    assert record.text_kind == "table_row"
    assert record.text == SOURCE_TEXT
    assert record.text_sha256 == _sha256(SOURCE_TEXT)
    assert record.char_count == len(SOURCE_TEXT)
    assert record.trusted_source is True
    assert record.extraction_method == "fixture_manual"


def test_r7af_loaded_fixture_can_verify_through_existing_wiring() -> None:
    records = load_source_text_sidecar_fixture(FIXTURE_PATH)
    result = _build_result(records)

    assert result.agreement_status == "VERIFIED"
    assert result.source_text_selection.status == "AVAILABLE_USED"
    assert result.source_text_selection.used_for_agreement is True
    assert result.evidence_level == "WEAK_EVIDENCE"


def test_r7af_loaded_fixture_numeric_mismatch_can_disagree(tmp_path: Path) -> None:
    text = "Revenue 2023 999.99"
    payload = _valid_payload(records=[_valid_record(text=text, text_sha256=_sha256(text), char_count=len(text))])
    records = load_source_text_sidecar_fixture(_write_payload(tmp_path, payload))
    result = _build_result(records)

    assert result.agreement_status == "DISAGREED"
    assert result.source_text_selection.status == "AVAILABLE_USED"
    assert result.evidence_level == "WEAK_EVIDENCE"


def test_r7af_loaded_fixture_writes_evidence_index_metadata_without_full_text() -> None:
    records = load_source_text_sidecar_fixture(FIXTURE_PATH)
    result = _build_result(records)

    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "evidence_index.json"
        write_evidence_index(out_path, [result])
        raw_payload = out_path.read_text(encoding="utf-8")
        payload = json.loads(raw_payload)

    assert SOURCE_TEXT not in raw_payload
    assert payload[0]["agreement_status"] == "VERIFIED"
    assert payload[0]["source_text_status"] == "AVAILABLE_USED"
    assert payload[0]["source_text_id"] == "st-valid-001"
    assert payload[0]["source_text_source_id"] == SOURCE_PDF_ID
    assert payload[0]["source_text_page_number"] == 3
    assert payload[0]["source_text_locator"] == LOCATOR
    assert payload[0]["source_text_kind"] == "table_row"
    assert payload[0]["source_text_sha256"] == _sha256(SOURCE_TEXT)
    assert payload[0]["source_text_char_count"] == len(SOURCE_TEXT)
    assert payload[0]["source_text_used_for_agreement"] is True
    assert payload[0]["source_text_unavailable_reason"] is None


def test_r7af_loaded_fixture_writes_review_queue_compact_fields_without_full_text() -> None:
    records = load_source_text_sidecar_fixture(FIXTURE_PATH)
    row = _make_row(row_type="MARKET_REFERENCE_ROW")
    result = _build_result(records, row=row, issues=[_review_issue()])
    queue_rows = build_review_queue_rows([result])
    serialized_queue = json.dumps(queue_rows, ensure_ascii=False)

    assert SOURCE_TEXT not in serialized_queue
    assert queue_rows[0]["agreement_status"] == "VERIFIED"
    assert queue_rows[0]["source_text_status"] == "AVAILABLE_USED"
    assert queue_rows[0]["source_text_page_number"] == "3"
    assert queue_rows[0]["source_text_locator"] == LOCATOR
    assert queue_rows[0]["source_text_unavailable_reason"] == ""


@pytest.mark.parametrize(
    ("mutate_payload", "match"),
    [
        (lambda payload: {**payload, "unknown": True}, "unknown keys"),
        (lambda payload: {**payload, "schema_version": 2}, "schema_version"),
        (lambda payload: {**payload, "fixture_scope": "production"}, "fixture_scope"),
        (lambda payload: {**payload, "records": "not-a-list"}, "records must be a list"),
    ],
)
def test_r7af_loader_rejects_invalid_top_level_payloads(
    tmp_path: Path,
    mutate_payload,
    match: str,
) -> None:
    with pytest.raises(SourceTextSidecarValidationError, match=match):
        load_source_text_sidecar_fixture(_write_payload(tmp_path, mutate_payload(_valid_payload())))


@pytest.mark.parametrize(
    ("mutate_record", "match"),
    [
        (lambda record: {**record, "unknown": True}, "unknown keys"),
        (lambda record: {key: value for key, value in record.items() if key != "text"}, "missing required keys"),
        (lambda record: {**record, "page_number": 0}, "page_number"),
        (lambda record: {**record, "text": ""}, "text"),
        (lambda record: {**record, "text_sha256": "bad-hash"}, "text_sha256 mismatch"),
        (lambda record: {**record, "char_count": 999}, "char_count mismatch"),
        (lambda record: {**record, "trusted_source": False}, "trusted_source"),
        (lambda record: {**record, "text_kind": ""}, "text_kind"),
        (lambda record: {**record, "source_document_id": ""}, "source_document_id"),
        (lambda record: {**record, "extraction_method": ""}, "extraction_method"),
    ],
)
def test_r7af_loader_rejects_invalid_records(
    tmp_path: Path,
    mutate_record,
    match: str,
) -> None:
    payload = _valid_payload(records=[mutate_record(_valid_record())])

    with pytest.raises(SourceTextSidecarValidationError, match=match):
        load_source_text_sidecar_fixture(_write_payload(tmp_path, payload))


def test_r7af_loader_rejects_invalid_json(tmp_path: Path) -> None:
    with pytest.raises(SourceTextSidecarValidationError, match="invalid JSON"):
        load_source_text_sidecar_fixture(_write_raw(tmp_path, "{"))


def test_r7af_loader_rejects_non_object_top_level_json(tmp_path: Path) -> None:
    with pytest.raises(SourceTextSidecarValidationError, match="top-level payload"):
        load_source_text_sidecar_fixture(_write_payload(tmp_path, []))


def test_r7af_loader_rejects_duplicate_source_text_id_without_partial_return(tmp_path: Path) -> None:
    payload = _valid_payload(records=[_valid_record(), _valid_record(locator="p3:table:row:other")])

    with pytest.raises(SourceTextSidecarValidationError, match="duplicate source_text_id"):
        load_source_text_sidecar_fixture(_write_payload(tmp_path, payload))


def test_r7af_loader_rejects_later_invalid_record_without_partial_return(tmp_path: Path) -> None:
    payload = _valid_payload(records=[_valid_record(), _valid_record(source_text_id="st-invalid-002", text="")])

    with pytest.raises(SourceTextSidecarValidationError, match="text"):
        load_source_text_sidecar_fixture(_write_payload(tmp_path, payload))


@pytest.mark.parametrize(
    ("row", "pdf_id", "expected_status"),
    [
        (_make_row(), "other-source-pdf", "SOURCE_ID_MISMATCH"),
        (_make_row(explicit_evidence_ref="page 4"), SOURCE_PDF_ID, "PAGE_NUMBER_MISMATCH"),
        (_make_row(metric_name="p3:table:row:other"), SOURCE_PDF_ID, "LOCATOR_MISMATCH"),
    ],
)
def test_r7af_loaded_sidecar_mismatch_cases_stay_unverified(
    row: SpreadsheetRow,
    pdf_id: str,
    expected_status: str,
) -> None:
    records = load_source_text_sidecar_fixture(FIXTURE_PATH)
    result = _build_result(records, row=row, pdf_id=pdf_id)

    assert result.agreement_status == "UNVERIFIED"
    assert result.source_text_selection.status == expected_status
    assert result.source_text_selection.used_for_agreement is False


def test_r7af_missing_source_text_stays_unverified() -> None:
    result = _build_result(None)

    assert result.agreement_status == "UNVERIFIED"
    assert result.source_text_selection.status == "MISSING"
    assert result.source_text_selection.used_for_agreement is False


def test_r7af_verified_fixture_keeps_clean_and_readiness_boundaries_closed() -> None:
    records = load_source_text_sidecar_fixture(FIXTURE_PATH)
    row = _make_row(row_type="MARKET_REFERENCE_ROW")
    result = _build_result(records, row=row)
    manifest = _manifest()

    assert result.agreement_status == "VERIFIED"
    assert result.evidence_level == "WEAK_EVIDENCE"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"
    assert manifest["demo_export_only"] is True
    assert manifest["formal_client_export_allowed"] is False
    assert manifest["client_ready"] is False
    assert manifest["production_ready"] is False
