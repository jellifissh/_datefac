"""Evidence presence checks for the 348A pilot."""

from __future__ import annotations

from pathlib import Path

from datefac_agent.schemas.audit_models import AuditIssue, EvidenceLevel, EvidenceRef, SpreadsheetRow


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


def classify_evidence_level(row: SpreadsheetRow, pdf_path: str | Path, evidence_refs: list[EvidenceRef]) -> EvidenceLevel:
    """Classify evidence strength for a single row."""

    has_explicit = any(ref.is_explicit or ref.page_number is not None for ref in evidence_refs) or bool(row.explicit_evidence_ref)
    has_pdf_identity = bool(str(pdf_path).strip())
    has_sheet_identity = bool(row.sheet_name.strip())
    has_row_identity = row.row_index > 0
    has_metric_identity = bool(row.metric_name.strip())
    has_workbook_row_ref = any(ref.source_type == "workbook_row" for ref in evidence_refs)

    if has_explicit:
        return "STRONG_EVIDENCE"

    if has_pdf_identity and has_sheet_identity and has_row_identity and has_metric_identity and has_workbook_row_ref:
        return "WEAK_EVIDENCE"

    if not has_pdf_identity and not has_sheet_identity and not has_row_identity and not has_metric_identity and not has_workbook_row_ref:
        return "MISSING_EVIDENCE"

    return "MISSING_EVIDENCE"


def audit_evidence_presence(
    row: SpreadsheetRow,
    pdf_path: str | Path,
) -> tuple[list[AuditIssue], list[EvidenceRef], EvidenceLevel]:
    """Classify evidence issues without running OCR or PDF parsing."""

    evidence_refs = build_evidence_refs(row, pdf_path)
    evidence_level = classify_evidence_level(row, pdf_path, evidence_refs)
    issues: list[AuditIssue] = []

    if evidence_level == "WEAK_EVIDENCE":
        issues.append(
            AuditIssue(
                code="weak_evidence",
                severity="warning",
                category="evidence",
                checker="evidence_checker",
                message=(
                    f"Row '{row.metric_name}' has workbook lineage and source PDF identity but no explicit page or evidence reference."
                ),
                metadata={"evidence_level": evidence_level, "row_type": row.row_type},
                evidence=evidence_refs,
            )
        )
    elif evidence_level == "MISSING_EVIDENCE":
        issues.append(
            AuditIssue(
                code="missing_evidence",
                severity="warning",
                category="evidence",
                checker="evidence_checker",
                message=f"Row '{row.metric_name}' lacks usable evidence lineage beyond raw value presence.",
                metadata={"evidence_level": evidence_level, "row_type": row.row_type},
                evidence=evidence_refs,
            )
        )

    return issues, evidence_refs, evidence_level
