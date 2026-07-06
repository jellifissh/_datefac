"""Tests for the R7AM test-only MinerU artifact adapter prototype."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from datefac_agent.review.review_queue_builder import build_row_audit_result
from datefac_agent.schemas.audit_models import AuditIssue, EvidenceRef, SpreadsheetRow
from tests.agent import mineru_artifact_adapter_348n as adapter_module
from tests.agent.mineru_artifact_adapter_348n import (
    EXTRACTION_METHOD,
    TEXT_KIND_PARAGRAPH,
    TEXT_KIND_TABLE,
    MinerUEvidenceBlock,
    find_mineru_evidence_for_candidate,
    load_mineru_content_list_v2_fixture,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "mineru_artifacts"
    / "anjing_minimal_content_list_v2__r7am.json"
)
SOURCE_DOCUMENT_ID = "H3_AP202606081823352906_1.pdf"


def _blocks() -> list[MinerUEvidenceBlock]:
    return load_mineru_content_list_v2_fixture(FIXTURE_PATH, source_document_id=SOURCE_DOCUMENT_ID)


def _candidate(metric_name: str, period: str, value: str, page_number: int | None) -> dict[str, object]:
    return {
        "metric_name": metric_name,
        "period": period,
        "value": value,
        "page_number": page_number,
    }


def test_r7am_loads_minimal_content_list_v2_fixture() -> None:
    blocks = _blocks()

    assert len(blocks) == 7
    assert {block.page_number for block in blocks} == {1, 2, 3}
    assert any(block.text_kind == TEXT_KIND_PARAGRAPH for block in blocks)
    assert any(block.text_kind == TEXT_KIND_TABLE for block in blocks)


def test_r7am_extracts_page_number_from_outer_page_index_and_locator() -> None:
    paragraph = _blocks()[0]

    assert paragraph.page_idx == 0
    assert paragraph.page_number == 1
    assert paragraph.block_index == 0
    assert paragraph.locator == "mineru:v2:page:1:block:0:bbox:356,205,947,266"
    assert paragraph.source_document_id == SOURCE_DOCUMENT_ID


def test_r7am_emits_deterministic_hash_char_count_and_source_text_id() -> None:
    first_run = _blocks()[0]
    second_run = _blocks()[0]

    assert first_run.text_sha256 == hashlib.sha256(first_run.text.encode("utf-8")).hexdigest()
    assert first_run.char_count == len(first_run.text)
    assert first_run.source_text_id == second_run.source_text_id
    assert first_run.trusted_source is True
    assert first_run.extraction_method == EXTRACTION_METHOD


def test_r7am_extracts_text_paragraph_evidence() -> None:
    paragraph = _blocks()[0]

    assert paragraph.type == "paragraph"
    assert paragraph.text_kind == TEXT_KIND_PARAGRAPH
    assert "2026Q1 实现营业收入 47.10 亿元" in paragraph.text
    assert paragraph.caption_preview == ""
    assert paragraph.footnote_preview == ""


def test_r7am_extracts_table_html_evidence_with_caption_and_footnote() -> None:
    table = [block for block in _blocks() if block.text_kind == TEXT_KIND_TABLE][0]

    assert table.type == "table"
    assert table.page_number == 2
    assert "<table>" in table.text
    assert "EPS(摊薄/元)" in table.text
    assert table.caption_preview == "财务数据与估值"
    assert table.footnote_preview == "资料来源：山西证券研究所"


def test_r7am_converts_block_to_existing_source_text_evidence_shape() -> None:
    block = _blocks()[0]
    evidence = block.to_source_text_evidence()

    assert evidence.source_text_id == block.source_text_id
    assert evidence.source_document_id == SOURCE_DOCUMENT_ID
    assert evidence.page_number == 1
    assert evidence.locator == block.locator
    assert evidence.text_kind == "snippet_text"
    assert evidence.text_sha256 == block.text_sha256
    assert evidence.char_count == block.char_count
    assert evidence.trusted_source is True


def test_r7am_verifies_2026q1_revenue_from_text_block() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("营业收入", "2026Q1", "47.10", 1), _blocks())

    assert result.agreement_status == "VERIFIED"
    assert result.evidence is not None
    assert result.evidence.text_kind == TEXT_KIND_PARAGRAPH


def test_r7am_verifies_2026q1_net_profit_from_text_block() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("归母净利润", "2026Q1", "5.63", 1), _blocks())

    assert result.agreement_status == "VERIFIED"
    assert result.evidence is not None


def test_r7am_verifies_2026q1_gross_margin_from_text_block() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("毛利率", "2026Q1", "24.99", 1), _blocks())

    assert result.agreement_status == "VERIFIED"
    assert result.evidence is not None


def test_r7am_verifies_2026e_eps_from_table_cell() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("EPS", "2026E", "5.37", 2), _blocks())

    assert result.agreement_status == "VERIFIED"
    assert result.evidence is not None
    assert result.evidence.text_kind == TEXT_KIND_TABLE


def test_r7am_verifies_2026e_pe_from_table_cell() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("PE", "2026E", "18.3", 2), _blocks())

    assert result.agreement_status == "VERIFIED"
    assert result.evidence is not None


def test_r7am_verifies_2026e_revenue_with_comma_normalization() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("营业收入", "2026E", "18379", 2), _blocks())

    assert result.agreement_status == "VERIFIED"
    assert result.evidence is not None


def test_r7am_verifies_2026e_profit_roe_and_pb_from_table_cell() -> None:
    blocks = _blocks()

    profit = find_mineru_evidence_for_candidate(_candidate("净利润", "2026E", "1,791", 2), blocks)
    roe = find_mineru_evidence_for_candidate(_candidate("ROE", "2026E", "10.3", 2), blocks)
    pb = find_mineru_evidence_for_candidate(_candidate("P/B", "2026E", "1.9", 2), blocks)

    assert profit.agreement_status == "VERIFIED"
    assert roe.agreement_status == "VERIFIED"
    assert pb.agreement_status == "VERIFIED"


def test_r7am_value_only_match_does_not_verify() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("不存在指标", "2026Q1", "47.10", 1), _blocks())

    assert result.agreement_status == "UNVERIFIED"
    assert result.evidence is not None
    assert "not enough anchors" in result.risk_reason


def test_r7am_metric_only_match_does_not_verify() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("营业收入", "2026Q1", "999.99", 1), _blocks())

    assert result.agreement_status == "DISAGREED"
    assert result.evidence is not None
    assert result.risk_reason == "value conflict"


def test_r7am_ambiguous_duplicate_numeric_evidence_is_conservative() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("营业收入", "2026Q1", "47.10", 3), _blocks())

    assert result.agreement_status == "AMBIGUOUS"
    assert result.evidence is not None
    assert result.risk_reason == "ambiguous duplicate evidence"


def test_r7am_missing_evidence_when_no_block_matches() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("营业收入", "2026Q1", "47.10", 99), _blocks())

    assert result.agreement_status == "MISSING_EVIDENCE"
    assert result.evidence is None


def test_r7am_disagreed_when_metric_period_exist_but_value_conflicts() -> None:
    result = find_mineru_evidence_for_candidate(_candidate("毛利率", "2026Q1", "24.99", 3), _blocks())

    assert result.agreement_status == "DISAGREED"
    assert result.evidence is not None


def test_r7am_verified_does_not_promote_to_strong_evidence_or_clean_admission() -> None:
    match = find_mineru_evidence_for_candidate(_candidate("营业收入", "2026Q1", "47.10", 1), _blocks())
    assert match.evidence is not None
    evidence = match.evidence.to_source_text_evidence()
    row = SpreadsheetRow(
        source_excel_path="anjing_fixture.xlsx",
        sheet_name="r7am_mineru_fixture",
        row_index=1,
        column_names=["metric", "2026Q1"],
        raw_values={"metric": "营业收入", "2026Q1": "47.10"},
        metric_name="营业收入",
        unit_hint="亿元",
        period_values={"2026Q1": "47.10"},
        explicit_evidence_ref="page 1",
        row_type="MARKET_REFERENCE_ROW",
    )
    evidence_refs = [
        EvidenceRef(source_type="source_pdf", source_id=SOURCE_DOCUMENT_ID, locator="fixture.pdf"),
        EvidenceRef(source_type="workbook_row", source_id="r7am_mineru_fixture:1", locator="营业收入"),
        EvidenceRef(
            source_type="explicit_workbook_evidence",
            source_id="page 1",
            page_number=1,
            locator=evidence.locator,
            is_explicit=True,
        ),
    ]
    result = build_row_audit_result(
        row,
        [AuditIssue(code="test_only_review", severity="warning", category="evidence", message="test-only")],
        evidence_refs,
        "WEAK_EVIDENCE",
        source_text_index=[evidence],
    )
    manifest = {
        "client_ready": False,
        "production_ready": False,
        "formal_client_export_allowed": False,
        "demo_export_only": True,
        "mineru_run_count": 0,
        "ocr_run_count": 0,
        "llm_api_call_count": 0,
        "vlm_api_call_count": 0,
    }

    assert match.agreement_status == "VERIFIED"
    assert result.agreement_status == "VERIFIED"
    assert result.evidence_level == "WEAK_EVIDENCE"
    assert result.clean_candidate_type == "REVIEW_REQUIRED"
    assert manifest["client_ready"] is False
    assert manifest["production_ready"] is False
    assert manifest["formal_client_export_allowed"] is False


def test_r7am_adapter_has_no_heavy_parser_or_external_call_imports() -> None:
    helper_path = Path(adapter_module.__file__).resolve()
    source = helper_path.read_text(encoding="utf-8")
    parsed_source = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(parsed_source):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".")[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".")[0].lower())

    assert helper_path.name == "mineru_artifact_adapter_348n.py"
    assert helper_path.parent.name == "agent"
    assert helper_path.parent.parent.name == "tests"
    assert imported_modules.isdisjoint(
        {"fitz", "pymupdf", "pdfplumber", "pypdf", "pdfminer", "mineru", "ocr", "llm", "vlm"}
    )


def test_r7am_fixture_is_small_and_not_full_mineru_output_dump() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    block_count = sum(len(page) for page in payload)

    assert FIXTURE_PATH.stat().st_size < 10_000
    assert block_count == 7
