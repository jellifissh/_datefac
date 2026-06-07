from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.delivery_report_refresh_330j import (  # noqa: E402
    READY_330I_DECISION,
    _build_comparison,
    _build_refreshed_metrics,
    _delivery_readiness_judgment,
    validate_330i_summary,
)


def test_validate_330i_summary_accepts_expected_ready_state() -> None:
    checks = validate_330i_summary(
        {
            "decision": READY_330I_DECISION,
            "qa_fail_count": 0,
            "input_candidate_row_count": 117,
            "output_candidate_row_count": 117,
            "source_page_missing_count_after": 0,
            "unit_missing_count_after": 54,
            "no_official_asset_modification_during_330i": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_build_refreshed_metrics_counts_units_and_risks() -> None:
    fixed_rows = [
        {
            "source_pdf": "a.pdf",
            "unit": "",
            "source_page": "1",
            "risk_flags": ["UNIT_UNKNOWN"],
        },
        {
            "source_pdf": "b.pdf",
            "unit": "RMB_mn",
            "source_page": "2",
            "risk_flags": ["UNIT_CONFLICT", "UNIT_UNKNOWN"],
        },
    ]
    rerun_summary = {
        "unfamiliar_candidate_artifact_row_count": 4,
        "unfamiliar_strict_deduped_candidate_count": 2,
        "sidecar_trusted_suggestion_count": 3,
        "sidecar_review_required_suggestion_count": 1,
        "confidence_level_distribution": {"HIGH": 3, "MEDIUM": 1},
        "routing_decision_distribution": {"TRUSTED": 3, "REVIEW_REQUIRED": 1},
        "risk_flag_distribution": {"UNIT_UNKNOWN": 2, "UNIT_CONFLICT": 1},
    }
    metrics = _build_refreshed_metrics(fixed_rows=fixed_rows, rerun_summary=rerun_summary)
    assert metrics["processed_pdf_count"] == 2
    assert metrics["source_pdf_unique_count"] == 2
    assert metrics["prepared_candidate_row_count"] == 2
    assert metrics["unit_missing_count"] == 1
    assert metrics["source_page_missing_count"] == 0
    assert metrics["unit_unknown_risk_count"] == 2
    assert metrics["unit_conflict_risk_count"] == 1
    assert metrics["sidecar_auto_trusted_ratio_artifact_row"] == 0.75
    assert metrics["sidecar_auto_trusted_ratio_strict_deduped"] == 1.5


def test_build_comparison_uses_expected_baselines() -> None:
    comparison = _build_comparison(
        summary_330g={"source_page_missing_count": 83, "prepared_candidate_row_count": 83, "artifact_row_count": 166, "risk_flag_distribution": {}},
        summary_330h={"unit_missing_count": 64, "330f_sidecar_trusted_suggestion_count": 226, "330f_sidecar_review_required_suggestion_count": 8},
        summary_330i={"unit_missing_count_after": 54, "unit_filled_count": 19, "source_page_missing_count_after": 0},
        refreshed_metrics={"sidecar_trusted_suggestion_count": 220, "sidecar_review_required_suggestion_count": 14, "artifact_row_count": 234, "prepared_candidate_row_count": 117, "risk_flag_distribution": {"UNIT_UNKNOWN": 54}},
    )
    assert comparison["unit_missing_before_330i"] == 64
    assert comparison["unit_missing_after_330i"] == 54
    assert comparison["unit_filled_count"] == 19
    assert comparison["source_page_missing_before_330h"] == 83
    assert comparison["source_page_missing_after_330i"] == 0
    assert comparison["trusted_suggestion_delta"] == -6
    assert comparison["review_required_delta"] == 6
    assert comparison["artifact_row_delta_vs_330g"] == 68
    assert comparison["prepared_candidate_row_delta_vs_330g"] == 34


def test_delivery_readiness_judgment_reflects_manual_review_caveat() -> None:
    judgment = _delivery_readiness_judgment(
        reran_330f=True,
        rerun_summary={"unfamiliar_source_status": "loaded"},
        refreshed_metrics={"source_page_missing_count": 0, "unit_missing_count": 54},
    )
    assert judgment == "DEMO_READY_WITH_MANUAL_REVIEW_CAVEATS"
