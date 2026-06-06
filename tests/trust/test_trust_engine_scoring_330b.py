from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust import (
    ROUTING_NEEDS_MORE_INFO,
    ROUTING_REJECTED,
    ROUTING_REVIEW_REQUIRED,
    ROUTING_TRUSTED,
    confidence_level_from_score,
    score_trust_record,
)
from datefac.trust.confidence_scoring import calculate_risk_penalty, scoring_model_summary


def test_confidence_level_zero_is_unknown() -> None:
    assert confidence_level_from_score(0) == "UNKNOWN"
    assert confidence_level_from_score(0.1) == "LOW"


def test_special_risk_penalties_override_base_severity() -> None:
    penalties = calculate_risk_penalty(
        ["OFFICIAL_RULE_CONFLICT", "VALUE_PARSE_FAILED", "MOJIBAKE_ENCODING_ARTIFACT"]
    )
    assert penalties["risk_penalty"] == (-45 - 40 - 2)


def test_scoring_model_summary_components() -> None:
    summary = scoring_model_summary()
    assert summary["scoring_model_component_count"] >= 5
    assert "confidence_score" in summary["scoring_components"]


def test_score_trust_record_routes_expected_examples() -> None:
    trusted = score_trust_record(
        {
            "candidate_id": "330b_t1",
            "metric_label_raw": "ROE",
            "normalized_metric": "roe",
            "value": 14.0,
            "unit": "%",
            "year": "2025E",
            "parser_sources": ["pdfplumber", "table_postprocess"],
            "parser_agreement_signal": True,
            "evidence_refs": ["page=11", "row=2"],
            "official_alias_match_signal": True,
            "semantic_target_unambiguous": True,
            "value_parse_success": True,
            "risk_flags": [],
            "provenance": {"fixture": True},
        }
    )
    assert trusted["routing_decision"] == ROUTING_TRUSTED
    assert trusted["confidence_level"] == "HIGH"
    assert "source_evidence_present" in trusted["decision_reasons"]

    review = score_trust_record(
        {
            "candidate_id": "330b_t2",
            "metric_label_raw": "璇爜ROE",
            "normalized_metric": "roe",
            "value": 12.0,
            "unit": "%",
            "year": "2024A",
            "parser_sources": ["pdfplumber"],
            "evidence_refs": ["cached_fixture://mojibake_review"],
            "semantic_target_unambiguous": True,
            "value_parse_success": True,
            "risk_flags": ["MOJIBAKE_ENCODING_ARTIFACT", "LOW_EVIDENCE_STRENGTH"],
            "provenance": {"fixture": True},
        }
    )
    assert review["routing_decision"] == ROUTING_REVIEW_REQUIRED
    assert "warning_risk_penalty_applied" in review["decision_reasons"]

    needs_more_info = score_trust_record(
        {
            "candidate_id": "330b_t3",
            "metric_label_raw": "可能利润率",
            "normalized_metric": "net_margin",
            "value": None,
            "unit": "",
            "year": "",
            "parser_sources": ["pdfplumber"],
            "evidence_refs": ["single-ref"],
            "semantic_target_unambiguous": False,
            "risk_flags": ["LOW_EVIDENCE_STRENGTH"],
            "provenance": {"fixture": True},
        }
    )
    assert needs_more_info["routing_decision"] == ROUTING_NEEDS_MORE_INFO

    rejected = score_trust_record(
        {
            "candidate_id": "330b_t4",
            "metric_label_raw": "P/E?",
            "normalized_metric": "price_earnings_ratio",
            "value": None,
            "unit": "x",
            "year": "",
            "parser_sources": ["pdfplumber", "marker_cached"],
            "evidence_refs": ["page=3", "table=1"],
            "risk_flags": ["OFFICIAL_RULE_CONFLICT", "VALUE_PARSE_FAILED", "TARGET_METRIC_AMBIGUOUS"],
            "provenance": {"fixture": True},
        },
        blocking_policy="reject",
        low_score_policy="reject",
    )
    assert rejected["routing_decision"] == ROUTING_REJECTED
    assert "blocking_risk_penalty_applied" in rejected["decision_reasons"]
