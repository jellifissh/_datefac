from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.source_attribution_unit_signal_fix_330i import (  # noqa: E402
    READY_330H_DECISION,
    _extract_parenthetical_tokens,
    _fix_single_row,
    _normalize_unit_text,
    validate_330h_summary,
)


def test_validate_330h_summary_accepts_expected_ready_state() -> None:
    checks = validate_330h_summary(
        {
            "decision": READY_330H_DECISION,
            "qa_fail_count": 0,
            "unfamiliar_pdf_count": 13,
            "processed_pdf_count": 13,
            "failed_pdf_count": 0,
            "prepared_candidate_row_count": 117,
            "source_pdf_preserved": True,
            "source_page_missing_count": 0,
            "unit_missing_count": 64,
            "no_official_asset_modification_during_330h": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_extract_parenthetical_tokens_supports_fullwidth_and_ascii() -> None:
    tokens = _extract_parenthetical_tokens(
        "\u8425\u4e1a\u6536\u5165\uff08\u767e\u4e07\u5143\uff09 EPS(\u5143/\u80a1)"
    )
    assert tokens == ["\u767e\u4e07\u5143", "\u5143/\u80a1"]


def test_fix_single_row_fills_missing_unit_from_explicit_row_text() -> None:
    row = {
        "candidate_id": "demo-1",
        "metric_label_raw": "\u8425\u4e1a\u6536\u5165",
        "normalized_metric": "revenue",
        "value": "529",
        "unit": "",
        "year": "2025",
        "parser_sources": ["pdfplumber"],
        "evidence_refs": ["table_id=demo|p2|t1"],
        "risk_flags": ["ROW_TEXT_ONLY"],
        "existing_status": "REVIEW_REQUIRED",
        "source_pdf": "demo.pdf",
        "source_artifact": "full_unfamiliar_export_benchmark_330h",
        "source_page": "2",
        "row_text": "\u8425\u4e1a\u6536\u5165\uff08\u767e\u4e07\u5143\uff09 529 639 800 1010",
        "table_id": "demo|p2|t1|pdfplumber",
    }
    fixed = _fix_single_row(row)
    assert fixed["unit"] == "RMB_mn"
    assert fixed["unit_fix_method"] == "INFERRED_FROM_EXPLICIT_PARENTHESES"
    assert fixed["unit_fix_confidence"] == "HIGH"
    assert "UNIT_UNKNOWN" not in fixed["risk_flags"]


def test_fix_single_row_clears_conflicting_eps_unit_and_marks_unknown() -> None:
    row = {
        "candidate_id": "demo-2",
        "metric_label_raw": "eps",
        "normalized_metric": "eps",
        "value": "2026",
        "unit": "\u4ebf\u5143",
        "year": "2024",
        "parser_sources": ["pdfplumber"],
        "evidence_refs": ["table_id=demo|p19|t1"],
        "risk_flags": ["ROW_TEXT_ONLY"],
        "existing_status": "REVIEW_REQUIRED",
        "source_pdf": "demo.pdf",
        "source_artifact": "full_unfamiliar_export_benchmark_330h",
        "source_page": "19",
        "row_text": "\u516c\u53f8\u4ee3\u7801 | EPS | PE 2026 6 2 2026",
        "table_id": "demo|p19|t1|pdfplumber",
    }
    fixed = _fix_single_row(row)
    assert fixed["unit"] == ""
    assert fixed["unit_fix_method"] == "CLEARED_SEMANTIC_CONFLICT"
    assert "UNIT_CONFLICT" in fixed["risk_flags"]
    assert "UNIT_UNKNOWN" in fixed["risk_flags"]


def test_normalize_unit_text_maps_expected_examples() -> None:
    assert _normalize_unit_text("\u5143/\u80a1") == "RMB_per_share"
    assert _normalize_unit_text("%") == "percent"
    assert _normalize_unit_text("\u4ebf\u5143") == "RMB_100m"
