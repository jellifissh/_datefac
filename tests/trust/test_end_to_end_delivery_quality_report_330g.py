from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.end_to_end_delivery_quality_report_330g import (  # noqa: E402
    READY_330F4_DECISION,
    READY_330F_DECISION,
    build_delivery_metrics,
    build_smoke_limitations,
    validate_330f4_summary,
    validate_330f_summary,
)


def test_validate_330f4_summary_accepts_expected_readiness() -> None:
    checks = validate_330f4_summary(
        {
            "decision": READY_330F4_DECISION,
            "qa_fail_count": 0,
            "selected_pdf_count": 3,
            "prepared_candidate_row_count": 83,
            "can_rerun_330f": True,
            "no_official_asset_modification_during_330f4": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_validate_330f_summary_accepts_expected_readiness() -> None:
    checks = validate_330f_summary(
        {
            "decision": READY_330F_DECISION,
            "qa_fail_count": 0,
            "unfamiliar_source_status": "loaded",
            "unfamiliar_candidate_artifact_row_count": 166,
            "unfamiliar_strict_deduped_candidate_count": 83,
            "scored_unfamiliar_record_count": 166,
            "sidecar_trusted_suggestion_count": 153,
            "sidecar_review_required_suggestion_count": 13,
            "no_official_asset_modification_during_330f": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_build_delivery_metrics_reports_duplication_and_fallback_issue() -> None:
    prepared_rows = [
        {
            "candidate_id": "c1",
            "source_pdf": "a.pdf",
            "unit": "",
            "source_page": "",
        },
        {
            "candidate_id": "c2",
            "source_pdf": "b.pdf",
            "unit": "",
            "source_page": "",
        },
    ]
    metrics = build_delivery_metrics(
        export_summary={},
        benchmark_summary={
            "unfamiliar_candidate_artifact_row_count": 4,
            "sidecar_trusted_suggestion_count": 3,
            "sidecar_review_required_suggestion_count": 1,
            "estimated_human_review_burden_count": 1,
            "risk_flag_distribution": {},
            "confidence_level_distribution": {"HIGH": 3, "MEDIUM": 1},
            "routing_decision_distribution": {"TRUSTED": 3, "REVIEW_REQUIRED": 1},
            "source_artifact_distribution": {"demo.jsonl": 2, "demo.xlsx": 2},
            "source_pdf_distribution": {"demo": 4},
        },
        prepared_manifest={"missing_field_counts": {"unit": 2, "source_page": 2}},
        prepared_rows=prepared_rows,
    )

    assert metrics["processed_pdf_count"] == 2
    assert metrics["strict_deduped_candidate_count"] == 2
    assert metrics["artifact_duplication_factor"] == 2.0
    assert metrics["sidecar_auto_trusted_ratio_strict_deduped"] is None
    assert metrics["source_pdf_distribution_fallback_issue"] is True

    limitations = build_smoke_limitations(metrics)
    assert any(row["limitation"] == "artifact_row_duplication_due_to_jsonl_xlsx" and row["status"] == "PRESENT" for row in limitations)
