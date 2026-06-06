from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (  # noqa: E402
    WAITING_DECISION,
    convert_to_prepared_rows,
    missing_field_counts,
    validate_previous_preparation_summary,
)


def test_validate_previous_preparation_summary_accepts_expected_waiting_state() -> None:
    checks = validate_previous_preparation_summary(
        {
            "decision": "UNFAMILIAR_OUTPUT_PREPARATION_330F2_WAITING",
            "unfamiliar_output_preparation_status": "WAITING_FOR_PARSER_OUTPUTS",
            "discovered_unfamiliar_input_pdf_count": 13,
            "matched_cached_output_count": 0,
            "prepared_candidate_row_count": 0,
            "qa_fail_count": 0,
        }
    )

    assert all(row["status"] == "PASS" for row in checks)


def test_convert_to_prepared_rows_produces_deterministic_candidate_id() -> None:
    source_rows = [
        {
            "metric_label_raw": "Revenue",
            "normalized_metric": "revenue",
            "value": 100.0,
            "unit": "CNY_million",
            "year": "2025E",
            "parser_sources": ["pdfplumber"],
            "evidence_refs": ["page=1", "row=2"],
            "risk_flags": [],
            "existing_status": "REVIEW_REQUIRED",
            "source_page": "1",
            "source_table": "table_01",
            "source_artifact": "demo_candidates.jsonl",
            "provenance": {
                "upstream_provenance": {
                    "source_report_name": "H3_AP202606061823322397_1.pdf",
                    "source_row_text": "Revenue 2025E 100",
                }
            },
        }
    ]

    first = convert_to_prepared_rows(source_rows)
    second = convert_to_prepared_rows(source_rows)

    assert first.iloc[0]["candidate_id"] == second.iloc[0]["candidate_id"]
    assert first.iloc[0]["source_pdf"] == "H3_AP202606061823322397_1.pdf"
    assert first.iloc[0]["row_text"] == "Revenue 2025E 100"


def test_missing_field_counts_handles_list_fields() -> None:
    frame = pd.DataFrame(
        [
            {
                "candidate_id": "x",
                "metric_label_raw": "",
                "normalized_metric": "revenue",
                "value": 1,
                "unit": "",
                "year": "2024A",
                "parser_sources": [],
                "evidence_refs": ["page=1"],
                "risk_flags": [],
                "existing_status": "",
                "source_pdf": "demo.pdf",
                "source_artifact": "demo.jsonl",
                "source_page": "",
                "row_text": "Revenue",
                "table_id": "",
            }
        ]
    )

    counts = missing_field_counts(frame)

    assert counts["metric_label_raw"] == 1
    assert counts["parser_sources"] == 1
    assert counts["risk_flags"] == 1
    assert WAITING_DECISION == "UNFAMILIAR_CANDIDATE_OUTPUT_GENERATION_330F3_WAITING_FOR_SAFE_EXPORT_PATH"
