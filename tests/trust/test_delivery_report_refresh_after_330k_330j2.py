from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.delivery_report_refresh_after_330k_330j2 import (  # noqa: E402
    READY_330K_DECISION,
    _build_comparison_vs_330j,
    _build_refreshed_metrics,
    _delivery_readiness_judgment,
    validate_330k_summary,
)


def test_validate_330k_summary_accepts_expected_ready_state() -> None:
    checks = validate_330k_summary(
        {
            "decision": READY_330K_DECISION,
            "qa_fail_count": 0,
            "input_candidate_row_count": 117,
            "unit_missing_count_input": 54,
            "additional_safe_unit_fix_count": 36,
            "unit_missing_count_after_330k": 18,
            "review_sample_row_count": 21,
            "human_review_workbook_generated": True,
            "no_official_asset_modification_during_330k": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_build_refreshed_metrics_counts_residual_unit_risk_after_330k() -> None:
    fixed_rows = [
        {
            "source_pdf": "a.pdf",
            "unit": "",
            "source_page": "1",
            "risk_flags": ["UNIT_UNKNOWN"],
        },
        {
            "source_pdf": "b.pdf",
            "unit": "x",
            "source_page": "2",
            "risk_flags": ["UNIT_CONFLICT"],
        },
        {
            "source_pdf": "b.pdf",
            "unit": "RMB_mn",
            "source_page": "3",
            "risk_flags": [],
        },
    ]
    rerun_summary = {
        "unfamiliar_candidate_artifact_row_count": 6,
        "unfamiliar_strict_deduped_candidate_count": 3,
        "sidecar_trusted_suggestion_count": 2,
        "sidecar_review_required_suggestion_count": 4,
        "confidence_level_distribution": {"HIGH": 2, "MEDIUM": 3, "LOW": 1},
        "routing_decision_distribution": {"TRUSTED": 2, "REVIEW_REQUIRED": 4},
        "risk_flag_distribution": {"UNIT_UNKNOWN": 2, "UNIT_CONFLICT": 2},
    }
    metrics = _build_refreshed_metrics(fixed_rows=fixed_rows, rerun_summary=rerun_summary)
    assert metrics["prepared_candidate_row_count"] == 3
    assert metrics["artifact_row_count"] == 6
    assert metrics["strict_deduped_candidate_count"] == 3
    assert metrics["source_pdf_unique_count"] == 2
    assert metrics["source_page_missing_count"] == 0
    assert metrics["unit_missing_count"] == 1
    assert metrics["unit_unknown_risk_count"] == 1
    assert metrics["unit_conflict_risk_count"] == 1
    assert metrics["sidecar_auto_trusted_ratio_artifact_row"] == 0.333333


def test_build_comparison_vs_330j_uses_expected_baseline() -> None:
    comparison = _build_comparison_vs_330j(
        {
            "unit_missing_count": 18,
            "unit_unknown_risk_count": 9,
            "unit_conflict_risk_count": 12,
            "sidecar_trusted_suggestion_count": 126,
            "sidecar_review_required_suggestion_count": 108,
            "confidence_level_distribution": {"HIGH": 126, "MEDIUM": 90, "LOW": 18},
            "routing_decision_distribution": {"TRUSTED": 126, "REVIEW_REQUIRED": 108},
            "risk_flag_distribution": {"UNIT_UNKNOWN": 18, "UNIT_CONFLICT": 24, "LABEL_AMBIGUOUS": 16},
        }
    )
    assert comparison["unit_missing_delta_vs_330j"] == -36
    assert comparison["unit_unknown_risk_delta_vs_330j"] == -45
    assert comparison["unit_conflict_risk_delta_vs_330j"] == 0
    assert comparison["trusted_suggestion_delta_vs_330j"] == 6
    assert comparison["review_required_delta_vs_330j"] == -6


def test_delivery_readiness_judgment_promotes_unit_review_caveat_when_threshold_met() -> None:
    judgment = _delivery_readiness_judgment(
        rerun_success=True,
        refreshed_metrics={"source_page_missing_count": 0, "unit_missing_count": 18},
    )
    assert judgment == "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS"
