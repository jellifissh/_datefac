from datefac.trust import (
    ROUTING_REJECTED,
    ROUTING_REVIEW_REQUIRED,
    ROUTING_TRUSTED,
    RISK_REGISTRY,
    build_trust_record,
    normalize_risk_flags,
    routing_policy_smoke_cases,
)


def test_risk_registry_minimum_count() -> None:
    assert len(RISK_REGISTRY) >= 18


def test_risk_normalization_deduplicates() -> None:
    assert normalize_risk_flags(["unit_unknown", "UNIT_UNKNOWN", "long_narrative_label"]) == [
        "UNIT_UNKNOWN",
        "LONG_NARRATIVE_LABEL",
    ]


def test_trust_record_routes_by_policy() -> None:
    trusted = build_trust_record(
        {
            "candidate_id": "c1",
            "metric_label_raw": "ROE",
            "normalized_metric": "roe",
            "value": 12.1,
            "unit": "%",
            "year": "2025E",
            "parser_sources": ["pdfplumber"],
            "evidence_refs": ["fixture://trusted"],
            "risk_flags": [],
            "evidence_score": 95,
            "semantic_score": 92,
            "unit_year_score": 90,
            "parser_agreement_score": 91,
            "risk_penalty": 0,
            "provenance": {"fixture": True},
        }
    )
    assert trusted["routing_decision"] == ROUTING_TRUSTED

    review = build_trust_record(
        {
            "candidate_id": "c2",
            "metric_label_raw": "调整后ROE说明",
            "normalized_metric": "roe",
            "value": 11.0,
            "unit": "%",
            "year": "2025E",
            "parser_sources": ["pdfplumber"],
            "evidence_refs": ["fixture://review"],
            "risk_flags": ["LOW_EVIDENCE_STRENGTH"],
            "evidence_score": 70,
            "semantic_score": 68,
            "unit_year_score": 74,
            "parser_agreement_score": 72,
            "risk_penalty": 2,
            "provenance": {"fixture": True},
        }
    )
    assert review["routing_decision"] == ROUTING_REVIEW_REQUIRED

    rejected = build_trust_record(
        {
            "candidate_id": "c3",
            "metric_label_raw": "P/E?",
            "normalized_metric": "price_earnings_ratio",
            "value": None,
            "unit": "x",
            "year": "",
            "parser_sources": ["pdfplumber"],
            "evidence_refs": ["fixture://rejected"],
            "risk_flags": ["OFFICIAL_RULE_CONFLICT", "VALUE_PARSE_FAILED"],
            "evidence_score": 10,
            "semantic_score": 25,
            "unit_year_score": 10,
            "parser_agreement_score": 20,
            "risk_penalty": 5,
            "provenance": {"fixture": True},
        },
        blocking_policy="reject",
        low_score_policy="reject",
    )
    assert rejected["routing_decision"] == ROUTING_REJECTED


def test_routing_smoke_cases_pass() -> None:
    assert all(case["passed"] for case in routing_policy_smoke_cases())
