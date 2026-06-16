"""Shared schemas for the minimal DateFac Agent audit pilot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

EvidenceLevel = Literal["STRONG_EVIDENCE", "WEAK_EVIDENCE", "MISSING_EVIDENCE", "NOT_APPLICABLE"]
RowType = Literal["STRICT_FINANCIAL_TABLE_ROW", "MARKET_REFERENCE_ROW", "NARRATIVE_ASSERTION", "UNKNOWN_ROW"]


@dataclass(slots=True)
class EvidenceRef:
    """Reference to source evidence for an extracted value."""

    source_type: str
    source_id: str
    page_number: int | None = None
    locator: str | None = None
    is_explicit: bool = False


@dataclass(slots=True)
class ExtractedMetric:
    """Structured extracted metric before audit decisions are applied."""

    metric_name: str
    period_label: str
    value_text: str
    unit: str | None = None
    evidence: list[EvidenceRef] = field(default_factory=list)


@dataclass(slots=True)
class SpreadsheetRow:
    """Lightweight workbook row preserved for audit."""

    source_excel_path: str
    sheet_name: str
    row_index: int
    column_names: list[str]
    raw_values: dict[str, Any]
    metric_name: str
    unit_hint: str | None = None
    period_values: dict[str, Any] = field(default_factory=dict)
    explicit_evidence_ref: str | None = None
    row_type: RowType = "UNKNOWN_ROW"


@dataclass(slots=True)
class WorkbookIntakeResult:
    """Workbook intake result for the 348A pilot."""

    source_excel_path: str
    sheet_names: list[str]
    rows: list[SpreadsheetRow]
    sheet_count: int
    row_count_total: int


@dataclass(slots=True)
class AuditIssue:
    """Issue raised during audit checks."""

    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    category: Literal["general", "unit", "period", "valuation", "evidence"] = "general"
    checker: str | None = None
    evidence: list[EvidenceRef] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class AuditDecision:
    """Final row-level audit decision."""

    decision: Literal["PASS", "REVIEW", "FAIL"]
    reason_codes: list[str] = field(default_factory=list)
    issue_count: int = 0


@dataclass(slots=True)
class AuditRowResult:
    """Audit result for a single spreadsheet row."""

    row: SpreadsheetRow
    issues: list[AuditIssue] = field(default_factory=list)
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    evidence_level: EvidenceLevel = "MISSING_EVIDENCE"
    row_type: RowType = "UNKNOWN_ROW"
    decision: AuditDecision | None = None


@dataclass(slots=True)
class AuditSummary:
    """Aggregate counts for the 348A pilot."""

    row_count_audited: int = 0
    pass_count: int = 0
    review_count: int = 0
    fail_count: int = 0
    issue_count_total: int = 0
    unit_issue_count: int = 0
    period_issue_count: int = 0
    valuation_issue_count: int = 0
    evidence_issue_count: int = 0
    strong_evidence_count: int = 0
    weak_evidence_count: int = 0
    missing_evidence_count: int = 0
    not_applicable_evidence_count: int = 0
    weak_evidence_issue_count: int = 0
    missing_evidence_issue_count: int = 0
    strict_financial_table_row_count: int = 0
    market_reference_row_count: int = 0
    narrative_assertion_count: int = 0
    unknown_row_count: int = 0
    clean_data_row_count: int = 0
    review_queue_row_count: int = 0


@dataclass(slots=True)
class AuditResult:
    """Aggregate audit result for a single record or batch."""

    status: Literal["pass", "review", "fail"]
    issues: list[AuditIssue] = field(default_factory=list)
    metrics: list[ExtractedMetric] = field(default_factory=list)
    row_results: list[AuditRowResult] = field(default_factory=list)
    summary: AuditSummary | None = None


@dataclass(slots=True)
class ReviewDecision:
    """Minimal human-review decision placeholder."""

    decision: Literal["approve", "revise", "reject"]
    reviewer: str | None = None
    notes: str | None = None
