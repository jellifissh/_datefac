from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.demo_packaging_331b import (  # noqa: E402
    READY_330K4_DECISION,
    READY_331A_DECISION,
    _build_demo_script,
    _build_github_readme_section,
    _build_project_brief,
    _build_resume_bullets,
    _contains_forbidden_claim,
    validate_330k4_summary,
    validate_331a_summary,
)


def test_validate_331a_summary_accepts_expected_ready_state() -> None:
    checks = validate_331a_summary(
        {
            "decision": READY_331A_DECISION,
            "qa_fail_count": 0,
            "project_status": "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
            "trusted_sheet_row_count": 96,
            "review_required_sheet_row_count": 21,
            "no_official_asset_modification_during_331a": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_validate_330k4_summary_accepts_expected_ready_state() -> None:
    checks = validate_330k4_summary(
        {
            "decision": READY_330K4_DECISION,
            "qa_fail_count": 0,
            "original_trusted_sheet_row_count": 96,
            "reviewed_unit_confirmed_count": 2,
            "reviewed_trusted_preview_row_count": 98,
            "human_rejected_row_count": 18,
            "remaining_review_required_after_unit_review_count": 1,
            "apply_plan_row_count": 21,
            "no_official_asset_modification_during_330k4": True,
        }
    )
    assert all(row["status"] == "PASS" for row in checks)


def test_claim_guard_detects_forbidden_claims() -> None:
    assert _contains_forbidden_claim("This is production-ready.", ["production-ready"])
    assert _contains_forbidden_claim("This is client-ready.", ["client-ready"])
    assert not _contains_forbidden_claim(
        "This is not production-ready and not client-ready yet.",
        ["production-ready", "client-ready"],
    )


def test_project_brief_uses_reviewed_preview_narrative() -> None:
    text = _build_project_brief(
        {"project_status": "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS"},
        {
            "original_trusted_sheet_row_count": 96,
            "reviewed_unit_confirmed_count": 2,
            "reviewed_trusted_preview_row_count": 98,
            "human_rejected_row_count": 18,
            "remaining_review_required_after_unit_review_count": 1,
        },
        {
            "scope_closure_324n": {"scope_rule_count_324": 1},
            "alias_closure_325p": {"official_alias_rule_count_325": 6},
        },
    )
    assert "Current status: demo-ready after human unit review preview." in text
    assert "330K4 refreshed the preview state" in text
    assert "not production-ready and not client-ready yet" in text


def test_resume_readme_and_script_remain_conservative() -> None:
    resume = _build_resume_bullets(
        {
            "reviewed_unit_confirmed_count": 2,
            "human_rejected_row_count": 18,
            "remaining_review_required_after_unit_review_count": 1,
        }
    )
    readme = _build_github_readme_section(
        {"project_status": "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS"},
        {
            "reviewed_trusted_preview_row_count": 98,
            "human_rejected_row_count": 18,
            "remaining_review_required_after_unit_review_count": 1,
        },
        {"trust_engine_330a": {"risk_registry_count": 18}, "trust_engine_330b": {"scoring_model_component_count": 7}},
    )
    script = _build_demo_script(
        {
            "original_trusted_sheet_row_count": 96,
            "reviewed_trusted_preview_row_count": 98,
            "human_rejected_row_count": 18,
            "remaining_review_required_after_unit_review_count": 1,
        }
    )
    assert "not production-ready and not client-ready yet" in readme
    assert "sidecar demo-packaging flow after human unit review" in resume
    assert "96 baseline trusted rows to 98 reviewed trusted rows" in script
