from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.demo_release_audit_332a import (  # noqa: E402
    READY_330K4_DECISION,
    READY_331A_DECISION,
    READY_331B_DECISION,
    _build_checklist_markdown,
    _build_interview_talking_points,
    _contains_forbidden_claim,
    _doc_has_boundary_terms,
    _extract_metric_values,
    validate_330k4_summary,
    validate_331a_summary,
    validate_331b_summary,
)


def test_validate_331b_summary_accepts_expected_ready_state() -> None:
    checks = validate_331b_summary(
        {
            "decision": READY_331B_DECISION,
            "qa_fail_count": 0,
            "project_status": "DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW",
            "client_ready": False,
            "production_ready": False,
            "original_trusted_sheet_row_count": 96,
            "reviewed_unit_confirmed_count": 2,
            "reviewed_trusted_preview_row_count": 98,
            "human_rejected_row_count": 18,
            "remaining_review_required_after_unit_review_count": 1,
            "apply_plan_row_count": 21,
            "no_official_asset_modification_during_332a": True,
            "no_official_asset_modification_during_331b": True,
        }
    )
    # validate_331b_summary checks the 331b field, not the 332a field
    assert checks[0]["status"] == "PASS"


def test_validate_330k4_and_331a_summaries_accept_expected_ready_state() -> None:
    checks_330k4 = validate_330k4_summary(
        {
            "decision": READY_330K4_DECISION,
            "qa_fail_count": 0,
            "original_trusted_sheet_row_count": 96,
            "reviewed_unit_confirmed_count": 2,
            "reviewed_trusted_preview_row_count": 98,
            "human_rejected_row_count": 18,
            "remaining_review_required_after_unit_review_count": 1,
            "apply_plan_row_count": 21,
        }
    )
    checks_331a = validate_331a_summary(
        {
            "decision": READY_331A_DECISION,
            "qa_fail_count": 0,
            "project_status": "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
        }
    )
    assert all(row["status"] == "PASS" for row in checks_330k4)
    assert all(row["status"] == "PASS" for row in checks_331a)


def test_metric_extraction_and_boundary_detection_work() -> None:
    text = "\n".join(
        [
            "Original trusted preview rows: 96",
            "Reviewed unit-confirmed rows added or surfaced: 2",
            "Reviewed trusted preview rows: 98",
            "Human-rejected rows isolated from trusted preview: 18",
            "Remaining review-required rows after unit review: 1",
            "It is not production-ready and not client-ready yet.",
            "This is a sidecar demo preview with no-write-back constraints.",
        ]
    )
    metrics = _extract_metric_values(text)
    boundaries = _doc_has_boundary_terms(text)
    assert metrics["original_trusted_sheet_row_count"] == 96
    assert metrics["reviewed_trusted_preview_row_count"] == 98
    assert boundaries["sidecar"] is True
    assert boundaries["preview"] is True
    assert boundaries["no_write_back"] is True


def test_claim_guard_detects_forbidden_claims() -> None:
    assert _contains_forbidden_claim("This mentions production deployment.", ["production deployment"])
    assert not _contains_forbidden_claim("This is a sidecar preview only.", ["production deployment"])


def test_checklist_and_interview_docs_include_required_sections() -> None:
    checklist = _build_checklist_markdown(
        {"project_status": "DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW"},
        {
            "reviewed_trusted_preview_row_count": 98,
            "human_rejected_row_count": 18,
            "remaining_review_required_after_unit_review_count": 1,
        },
    )
    talking_points = _build_interview_talking_points()
    assert "## 1. Safe To Show On GitHub" in checklist
    assert "## 5. Suggested Next Engineering Milestones" in checklist
    assert "Why Parser Quality Alone Is Not Enough" in talking_points
    assert "What Changed From 331A To 331B" in talking_points
