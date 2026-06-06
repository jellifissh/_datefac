from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.full_unfamiliar_export_benchmark_330h import (  # noqa: E402
    READY_330G_DECISION,
    _infer_unit_from_context,
    _prepared_row_from_candidate_330h,
    validate_330g_summary,
)


def test_validate_330g_summary_accepts_expected_ready_state() -> None:
    checks = validate_330g_summary(
        {
            "decision": READY_330G_DECISION,
            "qa_fail_count": 0,
            "processed_pdf_count": 3,
            "prepared_candidate_row_count": 83,
            "strict_deduped_candidate_count": 83,
            "delivery_readiness_judgment": "SMOKE_DEMO_READY_INTERNAL_ONLY",
            "recommended_next_step": "330H_FULL_13_PDF_UNFAMILIAR_EXPORT_AND_BENCHMARK",
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_infer_unit_from_context_prefers_percent_value() -> None:
    unit = _infer_unit_from_context(
        {"raw_unit": "", "raw_value": "18.5%", "normalized_value": "18.5%"},
        {"row_text": "毛利率 18.5%", "source_page": "3"},
        ["毛利率（%）"],
    )
    assert unit == "%"


def test_prepared_row_from_candidate_330h_preserves_source_pdf_and_page() -> None:
    candidate = {
        "raw_metric_name": "eps",
        "metric_code": "eps",
        "normalized_value": "1.25",
        "raw_value": "1.25",
        "year": "2025E",
        "risk_tags": "ROW_TEXT_ONLY|YEAR_INFERRED",
        "extracted_table_id": "demo|p7|t1|pdfplumber",
        "row_index": 2,
    }
    row = _prepared_row_from_candidate_330h(
        candidate,
        row_context={
            "source_page": "7",
            "row_text": "EPS（元/股） 2025E 1.25",
            "source_file": "demo.pdf",
        },
        table_context_rows=["EPS（元/股）", "PE（x）"],
    )
    assert row["source_pdf"] == "demo.pdf"
    assert row["source_page"] == "7"
    assert row["unit"] == "元/股"
    assert row["candidate_id"].startswith("330h::")
