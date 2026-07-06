"""Tests for the R7AH test-only lightweight PDF evidence bridge."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from datefac_agent.delivery.evidence_index_writer import write_evidence_index
from datefac_agent.review.review_queue_builder import build_review_queue_rows, build_row_audit_result
from datefac_agent.schemas.audit_models import AuditIssue, EvidenceRef, SourceTextEvidence, SpreadsheetRow
from tests.agent import lightweight_pdf_evidence_bridge_348n as bridge_module
from tests.agent.lightweight_pdf_evidence_bridge_348n import (
    AMBIGUOUS_DUPLICATE_VALUE,
    EXTRACTION_METHOD,
    MATCHED_SNIPPET,
    NO_KEYWORD_PROXIMITY,
    NO_VALUE_MATCH,
    PAGE_TEXT_MISSING,
    SCANNED_IMAGE_ONLY_MARKER,
    SCANNED_OR_IMAGE_ONLY_FALLBACK_REQUIRED,
    TEXT_KIND,
    LightweightRowHint,
    SyntheticPageTextProvider,
    build_lightweight_pdf_source_text_evidence,
)

SOURCE_DOCUMENT_ID = "synthetic-source-pdf-001"
SOURCE_FILE_SHA256 = "abc123def4567890abc123def4567890abc123def4567890abc123def4567890"
POSITIVE_PAGE_TEXT = "Revenue 2023 123.45\nOperating costs 2023 88.00"


def _row_hint(**overrides: object) -> LightweightRowHint:
    values: dict[str, object] = {
        "source_document_id": SOURCE_DOCUMENT_ID,
        "source_file_sha256": SOURCE_FILE_SHA256,
        "page_number": 3,
        "metric_name": "Revenue",
        "period": "2023",
        "value": "123.45",
        "unit": "RMB million",
        "row_id": "row-revenue-2023",
    }
    values.update(overrides)
    return LightweightRowHint(**values)


def _provider(pages: dict[int, str | None]) -> SyntheticPageTextProvider:
    return SyntheticPageTextProvider({SOURCE_DOCUMENT_ID: pages})


def _spreadsheet_row(
    evidence: SourceTextEvidence,
    *,
    row_type: str = "STRICT_FINANCIAL_TABLE_ROW",
    period_values: dict[str, object] | None = None,
) -> SpreadsheetRow:
    values = period_values or {"2023": "123.45"}
    return SpreadsheetRow(
        source_excel_path="synthetic.xlsx",
        sheet_name="r7ah_lightweight_bridge",
        row_index=7,
        column_names=["metric", *values.keys()],
        raw_values={"metric": "Revenue", **values},
        metric_name="Revenue",
        unit_hint="RMB million",
        period_values=values,
        explicit_evidence_ref=f"page {evidence.page_number}",
        row_type=row_type,
    )


def _evidence_refs(evidence: SourceTextEvidence) -> list[EvidenceRef]:
    return [
        EvidenceRef(source_type="source_pdf", source_id=evidence.source_document_id, locator="synthetic.pdf"),
        EvidenceRef(source_type="workbook_row", source_id="r7ah_lightweight_bridge:7", locator="Revenue"),
        EvidenceRef(
            source_type="explicit_workbook_evidence",
            source_id=f"page {evidence.page_number}",
            page_number=evidence.page_number,
            locator=evidence.locator,
            is_explicit=True,
        ),
    ]


def _build_result(
    evidence: SourceTextEvidence,
    *,
    row_type: str = "STRICT_FINANCIAL_TABLE_ROW",
    issues: list[AuditIssue] | None = None,
):
    row = _spreadsheet_row(evidence, row_type=row_type)
    return build_row_audit_result(
        row,
        issues if issues is not None else [],
        _evidence_refs(evidence),
        "WEAK_EVIDENCE",
        source_text_index=[evidence],
    )


def _review_issue() -> AuditIssue:
    return AuditIssue(
        code="r7ah_review_fixture",
        severity="warning",
        category="evidence",
        message="R7AH lightweight bridge review fixture.",
    )


def _manifest() -> dict[str, Any]:
    return {
        "demo_export_only": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "llm_api_call_count": 0,
        "mineru_run_count": 0,
        "ocr_run_count": 0,
    }


def test_r7ah_page_number_row_with_value_metric_period_produces_source_text_evidence() -> None:
    provider = _provider({3: POSITIVE_PAGE_TEXT})

    result = build_lightweight_pdf_source_text_evidence(_row_hint(), provider)

    assert result.status == MATCHED_SNIPPET
    assert result.matched_page_number == 3
    assert provider.requested_pages == [(SOURCE_DOCUMENT_ID, 3)]
    assert provider.searched_sources == []
    assert result.evidence is not None
    evidence = result.evidence
    assert evidence.source_document_id == SOURCE_DOCUMENT_ID
    assert evidence.page_number == 3
    assert evidence.locator == "page:3:text_anchor:13-19"
    assert evidence.text_kind == TEXT_KIND
    assert evidence.text == "Revenue 2023 123.45"
    assert evidence.text_sha256 == hashlib.sha256(evidence.text.encode("utf-8")).hexdigest()
    assert evidence.char_count == len(evidence.text)
    assert evidence.trusted_source is True
    assert evidence.extraction_method == EXTRACTION_METHOD
    assert evidence.source_text_id.startswith(f"r7ah:{SOURCE_FILE_SHA256[:12]}:p3:13-19:")


def test_r7ah_no_page_number_row_uses_capped_candidate_search_for_full_anchor_match() -> None:
    provider = _provider(
        {
            1: "Only a stray value 123.45 appears here.",
            2: POSITIVE_PAGE_TEXT,
            3: "Revenue 2022 123.45",
        }
    )

    result = build_lightweight_pdf_source_text_evidence(_row_hint(page_number=None, candidate_page_limit=2), provider)

    assert result.status == MATCHED_SNIPPET
    assert result.evidence is not None
    assert result.evidence.page_number == 2
    assert provider.requested_pages == []
    assert provider.searched_sources == [(SOURCE_DOCUMENT_ID, 2)]


def test_r7ah_accepted_snippet_drives_existing_agreement_checker_to_verified() -> None:
    bridge_result = build_lightweight_pdf_source_text_evidence(_row_hint(), _provider({3: POSITIVE_PAGE_TEXT}))
    assert bridge_result.evidence is not None

    row_result = _build_result(bridge_result.evidence)

    assert row_result.agreement_status == "VERIFIED"
    assert row_result.source_text_selection.status == "AVAILABLE_USED"
    assert row_result.source_text_selection.used_for_agreement is True
    assert row_result.evidence_level == "WEAK_EVIDENCE"


def test_r7ah_evidence_index_metadata_excludes_full_source_text(tmp_path: Path) -> None:
    bridge_result = build_lightweight_pdf_source_text_evidence(_row_hint(), _provider({3: POSITIVE_PAGE_TEXT}))
    assert bridge_result.evidence is not None
    row_result = _build_result(bridge_result.evidence)
    output_path = tmp_path / "evidence_index.json"

    write_evidence_index(output_path, [row_result])
    raw_payload = output_path.read_text(encoding="utf-8")
    payload = json.loads(raw_payload)

    assert bridge_result.evidence.text not in raw_payload
    assert payload[0]["agreement_status"] == "VERIFIED"
    assert payload[0]["source_text_status"] == "AVAILABLE_USED"
    assert payload[0]["source_text_id"] == bridge_result.evidence.source_text_id
    assert payload[0]["source_text_source_id"] == SOURCE_DOCUMENT_ID
    assert payload[0]["source_text_page_number"] == 3
    assert payload[0]["source_text_locator"] == bridge_result.evidence.locator
    assert payload[0]["source_text_kind"] == TEXT_KIND
    assert payload[0]["source_text_sha256"] == bridge_result.evidence.text_sha256
    assert payload[0]["source_text_char_count"] == len(bridge_result.evidence.text)
    assert payload[0]["source_text_used_for_agreement"] is True
    assert payload[0]["source_text_unavailable_reason"] is None


def test_r7ah_review_queue_compact_fields_exclude_full_source_text() -> None:
    bridge_result = build_lightweight_pdf_source_text_evidence(_row_hint(), _provider({3: POSITIVE_PAGE_TEXT}))
    assert bridge_result.evidence is not None
    row_result = _build_result(bridge_result.evidence, row_type="MARKET_REFERENCE_ROW", issues=[_review_issue()])

    queue_rows = build_review_queue_rows([row_result])
    serialized_queue = json.dumps(queue_rows, ensure_ascii=False)

    assert bridge_result.evidence.text not in serialized_queue
    assert queue_rows[0]["agreement_status"] == "VERIFIED"
    assert queue_rows[0]["source_text_status"] == "AVAILABLE_USED"
    assert queue_rows[0]["source_text_page_number"] == "3"
    assert queue_rows[0]["source_text_locator"] == bridge_result.evidence.locator
    assert queue_rows[0]["source_text_unavailable_reason"] == ""


@pytest.mark.parametrize(
    ("page_text", "expected_status"),
    [
        ("123.45 appears without metric or period.", NO_KEYWORD_PROXIMITY),
        ("Revenue 2023 has no numeric value here.", NO_VALUE_MATCH),
        ("Revenue 2023 999.99", NO_VALUE_MATCH),
    ],
)
def test_r7ah_conservative_failure_cases_do_not_create_trusted_source_text(
    page_text: str,
    expected_status: str,
) -> None:
    result = build_lightweight_pdf_source_text_evidence(_row_hint(), _provider({3: page_text}))

    assert result.status == expected_status
    assert result.evidence is None


def test_r7ah_page_number_row_does_not_search_wrong_page_for_value() -> None:
    provider = _provider({3: "Revenue 2023 999.99", 4: POSITIVE_PAGE_TEXT})

    result = build_lightweight_pdf_source_text_evidence(_row_hint(page_number=3), provider)

    assert result.status == NO_VALUE_MATCH
    assert result.evidence is None
    assert provider.requested_pages == [(SOURCE_DOCUMENT_ID, 3)]
    assert provider.searched_sources == []


def test_r7ah_ambiguous_duplicate_value_does_not_create_trusted_source_text() -> None:
    page_text = "Revenue 2023 123.45\nRevenue 2023 123.45"

    result = build_lightweight_pdf_source_text_evidence(_row_hint(), _provider({3: page_text}))

    assert result.status == AMBIGUOUS_DUPLICATE_VALUE
    assert result.evidence is None


def test_r7ah_missing_page_text_does_not_create_trusted_source_text() -> None:
    result = build_lightweight_pdf_source_text_evidence(_row_hint(), _provider({3: None}))

    assert result.status == PAGE_TEXT_MISSING
    assert result.evidence is None
    assert result.fallback_needed is False


def test_r7ah_scanned_marker_requires_fallback_without_trusted_source_text() -> None:
    result = build_lightweight_pdf_source_text_evidence(_row_hint(), _provider({3: SCANNED_IMAGE_ONLY_MARKER}))

    assert result.status == SCANNED_OR_IMAGE_ONLY_FALLBACK_REQUIRED
    assert result.evidence is None
    assert result.fallback_needed is True


@pytest.mark.parametrize(
    ("page_text", "row_value"),
    [
        ("Revenue 2023 1,234.56", "1234.56"),
        ("Revenue 2023 (123.45)", "-123.45"),
        ("Revenue 2023 12.3%", "12.3"),
        ("Revenue 2023 123.45 万", "123.45"),
    ],
)
def test_r7ah_narrow_numeric_normalization_supports_common_synthetic_formats(
    page_text: str,
    row_value: str,
) -> None:
    result = build_lightweight_pdf_source_text_evidence(_row_hint(value=row_value), _provider({3: page_text}))

    assert result.status == MATCHED_SNIPPET
    assert result.evidence is not None
    assert result.evidence.text == page_text


def test_r7ah_verified_fixture_keeps_clean_and_readiness_boundaries_closed() -> None:
    bridge_result = build_lightweight_pdf_source_text_evidence(_row_hint(), _provider({3: POSITIVE_PAGE_TEXT}))
    assert bridge_result.evidence is not None

    row_result = _build_result(bridge_result.evidence, row_type="MARKET_REFERENCE_ROW")
    manifest = _manifest()

    assert row_result.agreement_status == "VERIFIED"
    assert row_result.evidence_level == "WEAK_EVIDENCE"
    assert row_result.clean_candidate_type == "REVIEW_REQUIRED"
    assert manifest["demo_export_only"] is True
    assert manifest["formal_client_export_allowed"] is False
    assert manifest["client_ready"] is False
    assert manifest["production_ready"] is False
    assert manifest["llm_api_call_count"] == 0
    assert manifest["mineru_run_count"] == 0
    assert manifest["ocr_run_count"] == 0


def test_r7ah_helper_has_no_heavy_parser_or_production_hook_imports() -> None:
    helper_path = Path(bridge_module.__file__).resolve()
    source = helper_path.read_text(encoding="utf-8")
    parsed_source = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(parsed_source):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".")[0].lower())

    assert helper_path.name == "lightweight_pdf_evidence_bridge_348n.py"
    assert helper_path.parent.name == "agent"
    assert helper_path.parent.parent.name == "tests"
    assert imported_modules.isdisjoint({"fitz", "pymupdf", "pdfplumber", "pypdf", "mineru", "ocr", "llm", "vlm"})
