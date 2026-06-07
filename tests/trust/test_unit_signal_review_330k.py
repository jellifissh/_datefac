from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.unit_signal_review_330k import (  # noqa: E402
    READY_330J_DECISION,
    _additional_safe_fix,
    _candidate_status,
    _categorize_missing_row,
    validate_330j_summary,
)


def test_validate_330j_summary_accepts_expected_ready_state() -> None:
    checks = validate_330j_summary(
        {
            "decision": READY_330J_DECISION,
            "qa_fail_count": 0,
            "prepared_candidate_row_count": 117,
            "strict_deduped_candidate_count": 117,
            "unit_missing_count": 54,
            "unit_unknown_risk_count": 54,
            "unit_conflict_risk_count": 12,
            "source_page_missing_count": 0,
            "delivery_readiness_judgment": "DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS",
            "no_official_asset_modification_during_330j": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_candidate_status_identifies_conflict_and_missing_states() -> None:
    assert _candidate_status({"unit": "", "risk_flags": ["UNIT_CONFLICT"]}) == "unit_conflict"
    assert _candidate_status({"unit": "", "risk_flags": ["UNIT_UNKNOWN"]}) == "unit_missing_with_unit_unknown"
    assert _candidate_status({"unit": "x", "risk_flags": []}) == "unit_present"


def test_categorize_missing_row_routes_multiple_metrics() -> None:
    category = _categorize_missing_row(
        {
            "normalized_metric": "pe",
            "metric_label_raw": "p/e",
            "row_text": "市盈率（P/E） 35.36 25.16 17.32 12.63",
        }
    )
    assert category == "COUNT_OR_VOLUME_LIKE_METRIC"


def test_additional_safe_fix_fills_multiple_unit_from_row_text() -> None:
    fix = _additional_safe_fix(
        {
            "unit": "",
            "risk_flags": ["UNIT_UNKNOWN"],
            "normalized_metric": "pb",
            "metric_label_raw": "p/b",
            "row_text": "市净率（P/B） 6.72 6.53 6.26 5.88",
        }
    )
    assert fix is not None
    assert fix["unit"] == "x"
    assert fix["confidence"] == "HIGH"
