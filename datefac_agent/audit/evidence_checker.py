"""Evidence presence checks for the 348A pilot."""

from __future__ import annotations

from pathlib import Path

from datefac_agent.schemas.audit_models import AuditIssue, EvidenceRef, SpreadsheetRow


def build_evidence_refs(row: SpreadsheetRow, pdf_path: str | Path) -> list[EvidenceRef]:
    """Build minimal row-level evidence references without parsing the PDF."""

    refs = [
        EvidenceRef(
            source_type="source_pdf",
            source_id=str(pdf_path),
            locator=row.sheet_name,
        ),
        EvidenceRef(
            source_type="workbook_row",
            source_id=f"{row.sheet_name}:{row.row_index}",
            locator=row.metric_name,
        ),
    ]
    if row.explicit_evidence_ref:
        refs.append(
            EvidenceRef(
                source_type="explicit_workbook_evidence",
                source_id=row.explicit_evidence_ref,
                locator=row.metric_name,
                is_explicit=True,
            )
        )
    return refs


def audit_evidence_presence(row: SpreadsheetRow, pdf_path: str | Path) -> tuple[list[AuditIssue], list[EvidenceRef]]:
    """Make missing explicit evidence visible without running OCR or PDF parsing."""

    evidence_refs = build_evidence_refs(row, pdf_path)
    issues: list[AuditIssue] = []

    if not row.explicit_evidence_ref:
        issues.append(
            AuditIssue(
                code="missing_evidence",
                severity="warning",
                category="evidence",
                checker="evidence_checker",
                message=(
                    f"Row '{row.metric_name}' has source workbook and PDF context but no explicit page or evidence reference."
                ),
                evidence=evidence_refs,
            )
        )

    return issues, evidence_refs
