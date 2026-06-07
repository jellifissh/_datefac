from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.client_style_export_preview_330l import (  # noqa: E402
    READY_330J2_DECISION,
    _build_qa_caveats_df,
    _build_source_provenance_df,
    _dedupe_scored_rows,
    _merge_prepared_with_scored,
    validate_330j2_summary,
)


def test_validate_330j2_summary_accepts_expected_ready_state() -> None:
    checks = validate_330j2_summary(
        {
            "decision": READY_330J2_DECISION,
            "qa_fail_count": 0,
            "prepared_candidate_row_count": 117,
            "strict_deduped_candidate_count": 117,
            "source_page_missing_count": 0,
            "unit_missing_count": 18,
            "unit_unknown_risk_count": 18,
            "unit_conflict_risk_count": 12,
            "sidecar_trusted_suggestion_count": 192,
            "sidecar_review_required_suggestion_count": 42,
            "delivery_readiness_judgment": "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
            "no_official_asset_modification_during_330j2": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_dedupe_scored_rows_keeps_first_candidate_id() -> None:
    rows = [
        {"candidate_id": "a", "routing_decision": "TRUSTED"},
        {"candidate_id": "a", "routing_decision": "REVIEW_REQUIRED"},
        {"candidate_id": "b", "routing_decision": "REVIEW_REQUIRED"},
    ]
    deduped = _dedupe_scored_rows(rows)
    assert [row["candidate_id"] for row in deduped] == ["a", "b"]


def test_merge_prepared_with_scored_preserves_330k_rows() -> None:
    fixed_rows = [
        {"candidate_id": "a", "source_pdf": "a.pdf", "risk_flags": ["UNIT_UNKNOWN"]},
        {"candidate_id": "b", "source_pdf": "b.pdf", "risk_flags": []},
    ]
    scored_rows = [
        {"candidate_id": "a", "routing_decision": "REVIEW_REQUIRED", "confidence_level": "LOW"},
        {"candidate_id": "b", "routing_decision": "TRUSTED", "confidence_level": "HIGH"},
    ]
    merged = _merge_prepared_with_scored(fixed_rows, scored_rows)
    assert len(merged) == 2
    assert merged.loc[0, "routing_decision"] == "REVIEW_REQUIRED"
    assert merged.loc[1, "routing_decision"] == "TRUSTED"


def test_build_source_provenance_df_groups_pdf_page_counts() -> None:
    frame = pd.DataFrame(
        [
            {"source_pdf": "a.pdf", "source_page": "1", "routing_decision": "TRUSTED", "risk_flags": []},
            {"source_pdf": "a.pdf", "source_page": "1", "routing_decision": "REVIEW_REQUIRED", "risk_flags": ["UNIT_UNKNOWN"]},
            {"source_pdf": "b.pdf", "source_page": "2", "routing_decision": "REVIEW_REQUIRED", "risk_flags": ["UNIT_CONFLICT"]},
        ]
    )
    provenance = _build_source_provenance_df(frame)
    assert len(provenance) == 2
    first = provenance.to_dict(orient="records")[0]
    assert "candidate_count" in first
    assert "unit_risk_count" in first


def test_build_qa_caveats_df_contains_required_caveats() -> None:
    caveats = _build_qa_caveats_df({"unit_missing_count": 18, "artifact_row_count": 234, "prepared_candidate_row_count": 117, "unit_conflict_risk_count": 12})
    codes = set(caveats["caveat_code"].tolist())
    assert "sidecar_only_not_production_routing" in codes
    assert "not_client_ready" in codes
    assert "no_official_assets_modified" in codes
