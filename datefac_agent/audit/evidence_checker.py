"""Evidence presence checks for the 348A pilot."""

from __future__ import annotations

import re
from pathlib import Path

from datefac_agent.schemas.audit_models import AuditIssue, EvidenceAgreementStatus, EvidenceLevel, EvidenceRef, SpreadsheetRow

# R7X: deterministic page-reference parser. Matches a leading or embedded page
# number in common Chinese / English reference forms. Captures the first page
# number of a range so page_number stays a single int while the raw locator
# string is preserved separately on the EvidenceRef.
_PAGE_NUMBER_RE = re.compile(r"(\d+)")


def parse_page_number(ref_text: str | None) -> int | None:
    """Parse a deterministic page number from an explicit evidence reference.

    Returns the first page number as an int when the reference contains an
    Arabic page number (e.g. "第12页", "page 12", "p.12", "pp. 12-13",
    "第12-13页", "页码：12"). Returns None for non-numeric references such as
    "附录A" or empty input. Does not OCR or inspect the PDF.
    """

    if not ref_text:
        return None
    text = ref_text.strip()
    if not text:
        return None
    match = _PAGE_NUMBER_RE.search(text)
    if match is None:
        return None
    return int(match.group(1))


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
        # R7X: parse a deterministic page number into the structured field while
        # preserving the raw reference text as the locator. page_number stays
        # None when the reference is non-numeric (e.g. "附录A").
        refs.append(
            EvidenceRef(
                source_type="explicit_workbook_evidence",
                source_id=row.explicit_evidence_ref,
                locator=row.metric_name,
                page_number=parse_page_number(row.explicit_evidence_ref),
                is_explicit=True,
            )
        )
    return refs


def classify_evidence_level(row: SpreadsheetRow, pdf_path: str | Path, evidence_refs: list[EvidenceRef]) -> EvidenceLevel:
    """Classify evidence strength for a single row.

    R7X: explicit/page provenance that has not been value-verified is treated as
    WEAK_EVIDENCE, not STRONG_EVIDENCE. A page number being parsed is better
    provenance, but without a deterministic source-value agreement check it is
    not verified strong evidence. agreement_status on the AuditRowResult carries
    the verification state separately.
    """

    has_explicit = any(ref.is_explicit or ref.page_number is not None for ref in evidence_refs) or bool(row.explicit_evidence_ref)
    has_pdf_identity = bool(str(pdf_path).strip())
    has_sheet_identity = bool(row.sheet_name.strip())
    has_row_identity = row.row_index > 0
    has_metric_identity = bool(row.metric_name.strip())
    has_workbook_row_ref = any(ref.source_type == "workbook_row" for ref in evidence_refs)

    if has_explicit:
        # R7X: explicit provenance is UNVERIFIED until a future value-agreement
        # checker confirms it. Keep the row at WEAK_EVIDENCE so the pipeline
        # does not over-claim verified strong evidence merely because a page
        # reference was present.
        if has_pdf_identity and has_sheet_identity and has_row_identity and has_metric_identity and has_workbook_row_ref:
            return "WEAK_EVIDENCE"
        return "MISSING_EVIDENCE"

    if has_pdf_identity and has_sheet_identity and has_row_identity and has_metric_identity and has_workbook_row_ref:
        return "WEAK_EVIDENCE"

    if not has_pdf_identity and not has_sheet_identity and not has_row_identity and not has_metric_identity and not has_workbook_row_ref:
        return "MISSING_EVIDENCE"

    return "MISSING_EVIDENCE"


def classify_agreement_status(row: SpreadsheetRow, evidence_refs: list[EvidenceRef]) -> EvidenceAgreementStatus:
    """Classify evidence agreement status for a single row.

    R7X populates only MISSING and UNVERIFIED because no PDF value-agreement
    checker exists yet. VERIFIED / DISAGREED are reserved for a future task.
    """

    has_explicit = any(ref.is_explicit or ref.page_number is not None for ref in evidence_refs) or bool(row.explicit_evidence_ref)
    if has_explicit:
        return "UNVERIFIED"
    return "MISSING"


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
