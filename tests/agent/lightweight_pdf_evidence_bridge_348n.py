"""Test-only lightweight PDF evidence bridge prototype for R7AH."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import hashlib
import re

from datefac_agent.schemas.audit_models import SourceTextEvidence

BridgeStatus = str

MATCHED_SNIPPET = "MATCHED_SNIPPET"
NO_VALUE_MATCH = "NO_VALUE_MATCH"
NO_KEYWORD_PROXIMITY = "NO_KEYWORD_PROXIMITY"
NO_PERIOD_PROXIMITY = "NO_PERIOD_PROXIMITY"
PAGE_TEXT_MISSING = "PAGE_TEXT_MISSING"
AMBIGUOUS_DUPLICATE_VALUE = "AMBIGUOUS_DUPLICATE_VALUE"
SCANNED_OR_IMAGE_ONLY_FALLBACK_REQUIRED = "SCANNED_OR_IMAGE_ONLY_FALLBACK_REQUIRED"

EXTRACTION_METHOD = "lightweight_pdf_text_bridge_test_fixture"
TEXT_KIND = "lightweight_page_text_snippet"
SCANNED_IMAGE_ONLY_MARKER = "__SCANNED_IMAGE_ONLY__"

_NUMERIC_TOKEN_RE = re.compile(
    r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?(?:\s*[万亿])?(?![\w.])"
    r"|\(\s*\d[\d,]*(?:\.\d+)?%?\s*\)(?:\s*[万亿])?"
)


@dataclass(frozen=True, slots=True)
class LightweightRowHint:
    source_document_id: str
    source_file_sha256: str
    metric_name: str
    period: str
    value: object
    page_number: int | None = None
    unit: str | None = None
    row_id: str = "row-1"
    candidate_page_limit: int = 3


@dataclass(slots=True)
class SyntheticPageTextProvider:
    pages_by_source: dict[str, dict[int, str | None]]
    requested_pages: list[tuple[str, int]] = field(default_factory=list)
    searched_sources: list[tuple[str, int | None]] = field(default_factory=list)

    def get_page_text(self, source_document_id: str, page_number: int) -> str | None:
        self.requested_pages.append((source_document_id, page_number))
        return self.pages_by_source.get(source_document_id, {}).get(page_number)

    def search_pages(self, source_document_id: str, max_pages: int | None = None) -> Iterable[tuple[int, str | None]]:
        self.searched_sources.append((source_document_id, max_pages))
        pages = sorted(self.pages_by_source.get(source_document_id, {}).items())
        if max_pages is not None:
            pages = pages[:max_pages]
        return pages


@dataclass(frozen=True, slots=True)
class BridgeMatchResult:
    status: BridgeStatus
    evidence: SourceTextEvidence | None = None
    matched_page_number: int | None = None
    fallback_needed: bool = False


@dataclass(frozen=True, slots=True)
class _NumericOccurrence:
    value: Decimal
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class _AnchorCandidate:
    value_occurrence: _NumericOccurrence
    snippet_start: int
    snippet_end: int
    snippet_text: str


def build_lightweight_pdf_source_text_evidence(
    row_hint: LightweightRowHint,
    provider: SyntheticPageTextProvider,
) -> BridgeMatchResult:
    if row_hint.page_number is not None:
        page_text = provider.get_page_text(row_hint.source_document_id, row_hint.page_number)
        return _build_result_for_page(row_hint, row_hint.page_number, page_text)

    matches: list[BridgeMatchResult] = []
    fallback_seen = False
    for page_number, page_text in provider.search_pages(row_hint.source_document_id, row_hint.candidate_page_limit):
        page_result = _build_result_for_page(row_hint, page_number, page_text)
        if page_result.status == MATCHED_SNIPPET:
            matches.append(page_result)
        elif page_result.fallback_needed:
            fallback_seen = True

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return BridgeMatchResult(status=AMBIGUOUS_DUPLICATE_VALUE)
    if fallback_seen:
        return BridgeMatchResult(status=SCANNED_OR_IMAGE_ONLY_FALLBACK_REQUIRED, fallback_needed=True)
    return BridgeMatchResult(status=NO_VALUE_MATCH)


def _build_result_for_page(
    row_hint: LightweightRowHint,
    page_number: int,
    page_text: str | None,
) -> BridgeMatchResult:
    if page_text is None:
        return BridgeMatchResult(status=PAGE_TEXT_MISSING, matched_page_number=page_number)
    if not page_text.strip() or SCANNED_IMAGE_ONLY_MARKER in page_text:
        return BridgeMatchResult(
            status=SCANNED_OR_IMAGE_ONLY_FALLBACK_REQUIRED,
            matched_page_number=page_number,
            fallback_needed=True,
        )

    page_match = _find_anchor_match(row_hint, page_text)
    if isinstance(page_match, str):
        return BridgeMatchResult(status=page_match, matched_page_number=page_number)

    evidence = _make_source_text_evidence(row_hint, page_number, page_match)
    return BridgeMatchResult(status=MATCHED_SNIPPET, evidence=evidence, matched_page_number=page_number)


def _find_anchor_match(row_hint: LightweightRowHint, page_text: str) -> _AnchorCandidate | BridgeStatus:
    target_value = _normalize_numeric_value(row_hint.value)
    if target_value is None:
        return NO_VALUE_MATCH

    value_occurrences = [
        occurrence for occurrence in _iter_numeric_occurrences(page_text) if occurrence.value == target_value
    ]
    if not value_occurrences:
        return NO_VALUE_MATCH

    candidates: list[_AnchorCandidate] = []
    saw_keyword_near_value = False
    for occurrence in value_occurrences:
        snippet_start, snippet_end = _snippet_bounds(page_text, occurrence.start, occurrence.end)
        snippet_text = page_text[snippet_start:snippet_end].strip()
        has_metric = _contains_metric(snippet_text, row_hint.metric_name)
        has_period = _contains_period(snippet_text, row_hint.period)
        saw_keyword_near_value = saw_keyword_near_value or has_metric
        if has_metric and has_period:
            candidates.append(
                _AnchorCandidate(
                    value_occurrence=occurrence,
                    snippet_start=snippet_start,
                    snippet_end=snippet_end,
                    snippet_text=snippet_text,
                )
            )

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        return AMBIGUOUS_DUPLICATE_VALUE
    if saw_keyword_near_value:
        return NO_PERIOD_PROXIMITY
    return NO_KEYWORD_PROXIMITY


def _make_source_text_evidence(
    row_hint: LightweightRowHint,
    page_number: int,
    match: _AnchorCandidate,
) -> SourceTextEvidence:
    snippet_hash = hashlib.sha256(match.snippet_text.encode("utf-8")).hexdigest()
    locator = f"page:{page_number}:text_anchor:{match.value_occurrence.start}-{match.value_occurrence.end}"
    source_text_id = (
        f"r7ah:{row_hint.source_file_sha256[:12]}:"
        f"p{page_number}:{match.value_occurrence.start}-{match.value_occurrence.end}:{snippet_hash[:12]}"
    )
    return SourceTextEvidence(
        source_text_id=source_text_id,
        source_document_id=row_hint.source_document_id,
        page_number=page_number,
        locator=locator,
        text_kind=TEXT_KIND,
        text=match.snippet_text,
        text_sha256=snippet_hash,
        char_count=len(match.snippet_text),
        trusted_source=True,
        extraction_method=EXTRACTION_METHOD,
    )


def _iter_numeric_occurrences(text: str) -> Iterable[_NumericOccurrence]:
    for match in _NUMERIC_TOKEN_RE.finditer(text):
        value = _normalize_numeric_value(match.group(0))
        if value is not None:
            yield _NumericOccurrence(value=value, start=match.start(), end=match.end())


def _normalize_numeric_value(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if not text or text in {"-", "--", "—", "N/A", "n/a"}:
        return None

    is_negative_parentheses = text.startswith("(") and text.endswith(")")
    if is_negative_parentheses:
        text = text[1:-1].strip()
    text = text.replace("−", "-").replace("–", "-").replace(",", "")
    text = text.replace("万", "").replace("亿", "")
    text = text.strip()
    if text.endswith("%"):
        text = text[:-1].strip()
    if not text:
        return None

    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    if is_negative_parentheses:
        number = -number
    return number


def _snippet_bounds(text: str, match_start: int, match_end: int) -> tuple[int, int]:
    line_start = text.rfind("\n", 0, match_start) + 1
    line_end = text.find("\n", match_end)
    if line_end == -1:
        line_end = len(text)
    if line_end - line_start <= 160:
        return line_start, line_end
    return max(0, match_start - 80), min(len(text), match_end + 80)


def _contains_metric(text: str, metric_name: str) -> bool:
    metric_tokens = _tokens(metric_name)
    text_tokens = set(_tokens(text))
    return bool(metric_tokens) and all(token in text_tokens for token in metric_tokens)


def _contains_period(text: str, period: str) -> bool:
    period_tokens = _tokens(period)
    text_tokens = set(_tokens(text))
    return bool(period_tokens) and all(token in text_tokens for token in period_tokens)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
