from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.unfamiliar_candidate_export_smoke_330f4 import (  # noqa: E402
    READY_DECISION,
    _prepared_row_from_candidate,
    _stable_candidate_id,
    validate_330f3_summary,
)


def test_validate_330f3_summary_accepts_expected_waiting_state() -> None:
    checks = validate_330f3_summary(
        {
            "decision": "UNFAMILIAR_CANDIDATE_OUTPUT_GENERATION_330F3_WAITING_FOR_SAFE_EXPORT_PATH",
            "unfamiliar_pdf_count": 13,
            "prepared_candidate_row_count": 0,
            "qa_fail_count": 0,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_prepared_row_from_candidate_is_deterministic() -> None:
    candidate = {
        "raw_metric_name": "Revenue",
        "metric_code": "revenue",
        "normalized_value": "100",
        "raw_unit": "CNY_million",
        "year": "2025E",
        "risk_tags": "ROW_TEXT_ONLY|YEAR_INFERRED",
        "source_file": "demo.pdf",
        "row_text": "Revenue 2025E 100",
        "extracted_table_id": "demo|p1|t1|pdfplumber",
        "row_index": 1,
    }
    row1 = _prepared_row_from_candidate(candidate, "1")
    row2 = _prepared_row_from_candidate(candidate, "1")
    assert row1["candidate_id"] == row2["candidate_id"]
    assert row1["normalized_metric"] == "revenue"
    assert row1["existing_status"] == "REVIEW_REQUIRED"


def test_stable_candidate_id_changes_when_key_fields_change() -> None:
    base = {
        "source_pdf": "demo.pdf",
        "source_page": "1",
        "table_id": "t1",
        "row_text": "Revenue",
        "normalized_metric": "revenue",
        "year": "2024A",
        "value": "100",
    }
    first = _stable_candidate_id(base)
    changed = dict(base)
    changed["value"] = "101"
    second = _stable_candidate_id(changed)
    assert first != second
    assert READY_DECISION == "UNFAMILIAR_CANDIDATE_EXPORT_SMOKE_330F4_READY_FOR_330F_RERUN"
