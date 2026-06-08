from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.reviewed_export_refresh_330k4 import (  # noqa: E402
    READY_330K3_DECISION,
    _build_baseline_trusted_df,
    _build_preview_subset,
    _build_trace_df,
    _contains_forbidden_claim,
    _decision_counts,
    validate_330k3_summary,
)


def test_validate_330k3_summary_accepts_expected_ready_state() -> None:
    checks = validate_330k3_summary(
        {
            "decision": READY_330K3_DECISION,
            "qa_fail_count": 0,
            "apply_plan_row_count": 21,
            "confirm_unit_count": 2,
            "reject_unit_count": 18,
            "needs_more_context_count": 1,
            "keep_unit_unknown_count": 0,
            "no_official_asset_modification_during_330k3": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_decision_counts_fill_all_expected_buckets() -> None:
    df = pd.DataFrame(
        {"reviewer_decision": ["REJECT_UNIT", "CONFIRM_UNIT", "NEEDS_MORE_CONTEXT"]}
    )
    counts = _decision_counts(df)
    assert counts["REJECT_UNIT"] == 1
    assert counts["CONFIRM_UNIT"] == 1
    assert counts["NEEDS_MORE_CONTEXT"] == 1
    assert counts["KEEP_UNIT_UNKNOWN"] == 0


def test_build_trace_df_merges_review_context() -> None:
    apply_plan_df = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "pdf_document_id": "doc.pdf",
                "normalized_metric": "gross_margin",
                "year": "2025",
                "value": "15.3",
                "current_unit": "percent",
                "reviewer_unit": "percent",
                "reviewer_decision": "CONFIRM_UNIT",
                "reviewer_notes": "ok",
                "dry_run_action": "WOULD_CONFIRM_OR_SET_UNIT",
            }
        ]
    )
    reviewed_df = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "metric_label_raw": "gross margin",
                "source_page": "26",
                "source_evidence_text": "margin text",
                "source_evidence_refs": "table_id=t1",
                "parser_sources": "pdfplumber",
                "provenance_summary": "artifact|t1",
            }
        ]
    )
    review_required_df = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "confidence_level": "LOW",
                "confidence_score": "44",
                "routing_decision": "REVIEW_REQUIRED",
                "risk_flags": "UNIT_CONFLICT",
                "row_text": "margin text",
            }
        ]
    )
    trace_df = _build_trace_df(apply_plan_df, reviewed_df, review_required_df)
    row = trace_df.to_dict(orient="records")[0]
    assert row["final_unit_preview"] == "percent"
    assert row["preview_routing_bucket"] == "REVIEWED_UNIT_CONFIRMED"
    assert row["source_page"] == "26"
    assert row["confidence_level"] == "LOW"


def test_build_baseline_and_subset_keep_preview_shape() -> None:
    trusted_df = pd.DataFrame(
        [
            {
                "candidate_id": "base1",
                "source_pdf": "doc.pdf",
                "source_page": 2,
                "metric_label_raw": "revenue",
                "normalized_metric": "revenue",
                "year": "2025",
                "value": "529",
                "unit": "RMB_mn",
                "confidence_level": "HIGH",
                "confidence_score": 100,
                "routing_decision": "TRUSTED",
                "risk_flags": "",
                "evidence_refs": "t1",
                "row_text": "revenue row",
            }
        ]
    )
    baseline = _build_baseline_trusted_df(trusted_df)
    subset = _build_preview_subset(
        pd.DataFrame(
            [
                {
                    "candidate_id": "c1",
                    "pdf_document_id": "doc.pdf",
                    "source_page": "3",
                    "metric_label_raw": "eps",
                    "normalized_metric": "eps",
                    "year": "2025",
                    "value": "1.2",
                    "final_unit_preview": "RMB_per_share",
                    "current_unit": "",
                    "reviewer_unit": "RMB_per_share",
                    "confidence_level": "LOW",
                    "confidence_score": "44",
                    "upstream_routing_decision": "REVIEW_REQUIRED",
                    "preview_routing_bucket": "REMAINING_REVIEW_REQUIRED",
                    "risk_flags": "UNIT_UNKNOWN",
                    "source_evidence_refs": "t2",
                    "source_evidence_text": "eps row",
                    "reviewer_decision": "NEEDS_MORE_CONTEXT",
                    "reviewer_notes": "check source",
                    "dry_run_action": "WOULD_KEEP_REVIEW_REQUIRED_FOR_SOURCE_CHECK",
                    "preview_row_origin": "330K3_STILL_REVIEW_REQUIRED",
                }
            ]
        ),
        ["NEEDS_MORE_CONTEXT"],
    )
    assert len(baseline) == 1
    assert len(subset) == 1
    assert "preview_row_origin" in subset.columns


def test_contains_forbidden_claim_respects_negation() -> None:
    assert _contains_forbidden_claim("This is production-ready.", ["production-ready"])
    assert not _contains_forbidden_claim(
        "This is not production-ready.", ["production-ready"]
    )
