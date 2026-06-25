"""Evidence presence checks for the 348A pilot."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from datefac_agent.schemas.audit_models import AuditIssue, EvidenceAgreementStatus, EvidenceLevel, EvidenceRef, SpreadsheetRow

# R7X: deterministic page-reference parser. Matches a leading or embedded page
# number in common Chinese / English reference forms. Captures the first page
# number of a range so page_number stays a single int while the raw locator
# string is preserved separately on the EvidenceRef.
_PAGE_NUMBER_RE = re.compile(r"(\d+)")
_NUMERIC_TOKEN_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?(?![\w.])|\(\s*\d[\d,]*(?:\.\d+)?%?\s*\)")


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


def _normalize_numeric_value(value: object) -> Decimal | None:
    """Normalize common financial numeric values for deterministic equality."""

    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if not text or text in {"-", "--", "—", "N/A", "n/a"}:
        return None

    is_negative_parentheses = text.startswith("(") and text.endswith(")")
    if is_negative_parentheses:
        text = text[1:-1].strip()
    if text.endswith("%"):
        text = text[:-1].strip()
    text = text.replace(",", "")
    if not text:
        return None

    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    if is_negative_parentheses:
        number = -number
    return number


def _extract_numeric_tokens(text: str) -> set[Decimal]:
    tokens: set[Decimal] = set()
    for match in _NUMERIC_TOKEN_RE.finditer(text):
        number = _normalize_numeric_value(match.group(0))
        if number is not None:
            tokens.add(number)
    return tokens


def _numeric_period_values(row: SpreadsheetRow) -> list[Decimal]:
    values: list[Decimal] = []
    for value in row.period_values.values():
        number = _normalize_numeric_value(value)
        if number is not None:
            values.append(number)
    return values


def classify_agreement_status(
    row: SpreadsheetRow,
    evidence_refs: list[EvidenceRef],
    source_text: str | None = None,
) -> EvidenceAgreementStatus:
    """Classify deterministic source-value agreement for a single row.

    R7Y keeps production row-building conservative: explicit/page provenance
    without supplied source text remains UNVERIFIED. VERIFIED / DISAGREED are
    returned only by deterministic numeric comparison against trusted source text.
    """

    has_explicit = any(ref.is_explicit or ref.page_number is not None for ref in evidence_refs) or bool(row.explicit_evidence_ref)
    if not has_explicit:
        return "MISSING"
    if not source_text:
        return "UNVERIFIED"

    row_numbers = _numeric_period_values(row)
    if not row_numbers:
        return "UNVERIFIED"

    source_numbers = _extract_numeric_tokens(source_text)
    if not source_numbers:
        return "UNVERIFIED"

    matched_count = sum(1 for value in row_numbers if value in source_numbers)
    if matched_count == len(row_numbers):
        return "VERIFIED"
    if matched_count == 0:
        return "DISAGREED"
    return "UNVERIFIED"


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
