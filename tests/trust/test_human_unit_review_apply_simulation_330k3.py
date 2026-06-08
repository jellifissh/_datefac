from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.human_unit_review_apply_simulation_330k3 import (  # noqa: E402
    ACTION_BY_DECISION,
    READY_330K2_DECISION,
    _build_apply_plan,
    _contains_forbidden_claim,
    _decision_counts,
    validate_330k2_summary,
)


def test_validate_330k2_summary_accepts_expected_ready_state() -> None:
    checks = validate_330k2_summary(
        {
            "decision": READY_330K2_DECISION,
            "qa_fail_count": 0,
            "packaged_unit_review_row_count": 21,
            "source_page_missing_count": 0,
            "unit_missing_count": 18,
            "unit_conflict_risk_count": 12,
            "no_official_asset_modification_during_330k2": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_decision_counts_fill_all_allowed_buckets() -> None:
    df = pd.DataFrame({"reviewer_decision": ["REJECT_UNIT", "CONFIRM_UNIT", "NEEDS_MORE_CONTEXT"]})
    counts = _decision_counts(df)
    assert counts["REJECT_UNIT"] == 1
    assert counts["CONFIRM_UNIT"] == 1
    assert counts["NEEDS_MORE_CONTEXT"] == 1
    assert counts["KEEP_UNIT_UNKNOWN"] == 0


def test_build_apply_plan_maps_dry_run_actions() -> None:
    df = pd.DataFrame(
        [
            {
                "candidate_id": "a",
                "pdf_document_id": "doc.pdf",
                "normalized_metric": "eps",
                "year": "2025",
                "value": "1.2",
                "current_unit": "",
                "reviewer_unit": "RMB_per_share",
                "reviewer_decision": "CONFIRM_UNIT",
                "reviewer_notes": "ok",
            }
        ]
    )
    plan = _build_apply_plan(df)
    row = plan.to_dict(orient="records")[0]
    assert row["dry_run_action"] == ACTION_BY_DECISION["CONFIRM_UNIT"]
    assert row["would_write_back"] is False
    assert row["would_refresh_export"] is False
    assert row["would_modify_official_assets"] is False


def test_contains_forbidden_claim_respects_negation() -> None:
    assert _contains_forbidden_claim("This is production-ready.", ["production-ready"])
    assert not _contains_forbidden_claim("This is not production-ready.", ["production-ready"])

