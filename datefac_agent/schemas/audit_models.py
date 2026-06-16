"""Minimal schema placeholders for the DateFac Agent foundation stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(slots=True)
class EvidenceRef:
    """Reference to source evidence for an extracted value."""

    source_type: str
    source_id: str
    page_number: int | None = None
    locator: str | None = None


@dataclass(slots=True)
class ExtractedMetric:
    """Structured extracted metric before audit decisions are applied."""

    metric_name: str
    period_label: str
    value_text: str
    unit: str | None = None
    evidence: list[EvidenceRef] = field(default_factory=list)


@dataclass(slots=True)
class AuditIssue:
    """Issue raised during audit checks."""

    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    evidence: list[EvidenceRef] = field(default_factory=list)


@dataclass(slots=True)
class AuditResult:
    """Aggregate audit result for a single record or batch."""

    status: Literal["pass", "review", "fail"]
    issues: list[AuditIssue] = field(default_factory=list)
    metrics: list[ExtractedMetric] = field(default_factory=list)


@dataclass(slots=True)
class ReviewDecision:
    """Minimal human-review decision placeholder."""

    decision: Literal["approve", "revise", "reject"]
    reviewer: str | None = None
    notes: str | None = None
