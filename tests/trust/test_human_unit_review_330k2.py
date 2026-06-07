from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.human_unit_review_330k2 import (  # noqa: E402
    READY_330L_DECISION,
    _build_review_queue,
    _contains_forbidden_claim,
    validate_330l_summary,
)


def test_validate_330l_summary_accepts_expected_ready_state() -> None:
    checks = validate_330l_summary(
        {
            "decision": READY_330L_DECISION,
            "qa_fail_count": 0,
            "preview_workbook_generated": True,
            "prepared_candidate_row_count": 117,
            "strict_deduped_candidate_count": 117,
            "unit_missing_count": 18,
            "unit_conflict_risk_count": 12,
            "delivery_readiness_judgment": "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
            "no_official_asset_modification_during_330l": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_contains_forbidden_claim_respects_negation() -> None:
    assert _contains_forbidden_claim("This is production-ready.", ["production-ready"])
    assert not _contains_forbidden_claim("This is not production-ready.", ["production-ready"])


def test_build_review_queue_merges_context_fields() -> None:
    review_sample_df = pd.DataFrame(
        [
            {
                "candidate_id": "a",
                "source_pdf": "doc.pdf",
                "metric_label_raw": "eps",
                "normalized_metric": "eps",
                "source_page": "2",
                "unit": "",
                "risk_flags": "UNIT_CONFLICT | UNIT_UNKNOWN",
                "recommended_human_decision": "REJECT_UNIT",
                "row_text": "EPS text",
            }
        ]
    )
    review_required_df = pd.DataFrame(
        [
            {
                "candidate_id": "a",
                "year": "2025",
                "value": "1.2",
                "evidence_refs": "table_id=t1 | row_index=2",
                "row_text": "EPS text",
            }
        ]
    )
    prepared = {
        "a": {
            "parser_sources": ["pdfplumber", "row_text_full_330h"],
            "source_artifact": "artifact",
            "table_id": "t1",
        }
    }
    queue = _build_review_queue(review_sample_df, review_required_df, prepared)
    assert len(queue) == 1
    row = queue.to_dict(orient="records")[0]
    assert row["year"] == "2025"
    assert row["value"] == "1.2"
    assert row["unit_missing_flag"] is True
    assert row["unit_conflict_risk_flag"] is True
    assert "pdfplumber" in row["parser_sources"]

