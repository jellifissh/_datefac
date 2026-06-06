from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.routing_policy_calibration_330d import (  # noqa: E402
    analyze_potential_false_trusted,
    analyze_target_metric_ambiguous,
    build_best_effort_dedupe_view,
    build_policy_proposal,
)


def test_build_best_effort_dedupe_view_counts_candidate_id_duplicates() -> None:
    frame = pd.DataFrame(
        [
            {
                "candidate_id": "cand_001",
                "metric_label_raw": "Revenue",
                "normalized_metric": "revenue",
                "value": 10,
                "unit": "CNY",
                "year": "2024A",
                "source_table": "t1",
                "source_row": "r1",
                "source_page": "1",
                "source_dir_name": "dir_a",
                "provenance": {},
            },
            {
                "candidate_id": "cand_001",
                "metric_label_raw": "Revenue",
                "normalized_metric": "revenue",
                "value": 10,
                "unit": "CNY",
                "year": "2024A",
                "source_table": "t1",
                "source_row": "r1",
                "source_page": "1",
                "source_dir_name": "dir_a",
                "provenance": {},
            },
            {
                "candidate_id": "",
                "metric_label_raw": "EBIT",
                "normalized_metric": "EBIT",
                "value": 8,
                "unit": "CNY",
                "year": "2024A",
                "source_table": "t2",
                "source_row": "r2",
                "source_page": "2",
                "source_dir_name": "dir_b",
                "provenance": {},
            },
        ]
    )

    result = build_best_effort_dedupe_view(frame)

    assert result["dedupe_summary"]["artifact_row_count"] == 3
    assert result["dedupe_summary"]["deduped_candidate_count"] == 2
    assert result["dedupe_summary"]["duplicate_artifact_row_count"] == 1
    assert len(result["candidate_identity_duplicates_df"]) == 2


def test_analyze_potential_false_trusted_reproduces_subset_logic() -> None:
    frame = pd.DataFrame(
        [
            {
                "routing_decision": "TRUSTED",
                "existing_status": "REVIEW_REQUIRED",
                "source_artifact": "a.jsonl",
                "score_bucket": "85-100",
                "confidence_level": "HIGH",
                "risk_flags": [],
            },
            {
                "routing_decision": "TRUSTED",
                "existing_status": "TRUSTED",
                "source_artifact": "a.jsonl",
                "score_bucket": "85-100",
                "confidence_level": "HIGH",
                "risk_flags": [],
            },
            {
                "routing_decision": "REVIEW_REQUIRED",
                "existing_status": "REJECTED",
                "source_artifact": "b.xlsx",
                "score_bucket": "60-84",
                "confidence_level": "MEDIUM",
                "risk_flags": ["TARGET_METRIC_AMBIGUOUS"],
            },
        ]
    )

    result = analyze_potential_false_trusted(frame)

    assert result["summary"]["potential_false_trusted_count"] == 1
    assert result["summary"]["existing_status_distribution"] == {"REVIEW_REQUIRED": 1}
    assert result["summary"]["source_artifact_distribution"] == {"a.jsonl": 1}


def test_analyze_target_metric_ambiguous_uses_risk_flag_membership() -> None:
    frame = pd.DataFrame(
        [
            {
                "risk_flags": ["TARGET_METRIC_AMBIGUOUS"],
                "routing_decision": "REVIEW_REQUIRED",
                "score_bucket": "60-84",
                "confidence_level": "MEDIUM",
                "source_artifact": "a.jsonl",
            },
            {
                "risk_flags": [],
                "routing_decision": "TRUSTED",
                "score_bucket": "85-100",
                "confidence_level": "HIGH",
                "source_artifact": "b.xlsx",
            },
        ]
    )

    result = analyze_target_metric_ambiguous(frame)

    assert result["summary"]["target_metric_ambiguous_count"] == 1
    assert result["summary"]["target_metric_ambiguous_routing_distribution"] == {"REVIEW_REQUIRED": 1}
    assert result["summary"]["target_metric_ambiguous_score_distribution"] == {"60-84": 1}


def test_build_policy_proposal_matches_safe_default_thresholds() -> None:
    proposal = build_policy_proposal(
        scored_record_count=12076,
        potential_false_trusted_count=252,
        target_metric_ambiguous_count=6720,
    )

    assert proposal["policy_proposal_generated"] is True
    assert proposal["production_apply_allowed"] is False
    assert proposal["recommended_trusted_min_score"] == 85
    assert proposal["recommended_review_min_score"] == 60
    assert "TARGET_METRIC_AMBIGUOUS" in proposal["trusted_requirements"]["disallowed_risks"]
