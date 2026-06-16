"""Smoke tests for the DateFac Agent foundation package."""

import datefac_agent
from datefac_agent.schemas.audit_models import AuditResult, EvidenceRef


def test_datefac_agent_package_is_importable() -> None:
    assert datefac_agent.__doc__ == "DateFac Agent foundation package."


def test_audit_models_are_importable() -> None:
    evidence = EvidenceRef(source_type="pdf_page", source_id="demo", page_number=1)
    result = AuditResult(status="review")

    assert evidence.source_type == "pdf_page"
    assert result.status == "review"
