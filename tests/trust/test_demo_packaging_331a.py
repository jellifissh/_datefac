from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.demo_packaging_331a import (  # noqa: E402
    READY_330L_DECISION,
    _build_demo_script,
    _build_github_readme_section,
    _build_project_brief,
    _build_resume_bullets,
    _contains_forbidden_claim,
    validate_330l_summary,
)


def test_validate_330l_summary_accepts_expected_ready_state() -> None:
    checks = validate_330l_summary(
        {
            "decision": READY_330L_DECISION,
            "qa_fail_count": 0,
            "preview_workbook_generated": True,
            "prepared_candidate_row_count": 117,
            "strict_deduped_candidate_count": 117,
            "unit_missing_count": 18,
            "unit_conflict_risk_count": 12,
            "delivery_readiness_judgment": "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
            "no_official_asset_modification_during_330l": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_claim_guard_detects_forbidden_claims() -> None:
    assert _contains_forbidden_claim("This is production-ready.", ["production-ready"])
    assert _contains_forbidden_claim("This is client-ready.", ["client-ready"])
    assert not _contains_forbidden_claim("This is not production-ready yet.", ["production-ready"])


def test_project_brief_uses_required_demo_wording() -> None:
    text = _build_project_brief(
        {
            "preview_workbook_path": "demo.xlsx",
            "prepared_candidate_row_count": 117,
            "trusted_sheet_row_count": 96,
            "review_required_sheet_row_count": 21,
            "unit_review_sheet_row_count": 21,
        },
        {"scope_closure_324n": {"scope_rule_count_324": 1}, "alias_closure_325p": {"official_alias_rule_count_325": 6, "cumulative_trusted_gain_after_325": 138, "cumulative_review_reduction_after_325": 503}},
    )
    assert "DateFac is a financial PDF core-metric extraction and trust-routing demo." in text
    assert "It is not production-ready or client-ready yet." in text


def test_resume_and_readme_sections_remain_conservative() -> None:
    resume = _build_resume_bullets(
        {"prepared_candidate_row_count": 117},
        {"scope_closure_324n": {"scope_rule_count_324": 1}, "alias_closure_325p": {"official_alias_rule_count_325": 6, "cumulative_trusted_gain_after_325": 138, "cumulative_review_reduction_after_325": 503}},
    )
    readme = _build_github_readme_section(
        {
            "trusted_sheet_row_count": 96,
            "review_required_sheet_row_count": 21,
        },
        {"trust_engine_330a": {"risk_registry_count": 18}, "trust_engine_330b": {"scoring_model_component_count": 7}, "trust_engine_330c": {"cached_candidate_count": 12076}},
    )
    assert "not production-ready or client-ready yet" in readme
    assert "production-ready" not in resume.casefold()


def test_demo_script_mentions_unit_caveats_and_next_step() -> None:
    script = _build_demo_script({"preview_workbook_path": "demo.xlsx", "trusted_sheet_row_count": 96, "review_required_sheet_row_count": 21, "unit_review_sheet_row_count": 21})
    assert "unit-risk rows remain" in script
    assert "330K2 human unit review" in script
