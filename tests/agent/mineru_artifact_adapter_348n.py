"""Test-only MinerU content_list_v2 adapter prototype for R7AM."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from html import unescape
from html.parser import HTMLParser
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal

from datefac_agent.schemas.audit_models import SourceTextEvidence

AgreementStatus = Literal["VERIFIED", "UNVERIFIED", "DISAGREED", "AMBIGUOUS", "MISSING_EVIDENCE"]

EXTRACTION_METHOD = "mineru_content_list_v2_test_fixture"
TEXT_KIND_PARAGRAPH = "mineru_text_block"
TEXT_KIND_TABLE = "mineru_table_html"

_NUMBER_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?(?![\w.])|\(\s*\d[\d,]*(?:\.\d+)?%?\s*\)")
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

_METRIC_ALIASES: dict[str, tuple[str, ...]] = {
    "营业收入": ("营业收入", "营收", "收入"),
    "归母净利润": ("归母净利润", "归母净利", "归属于母公司所有者的净利润", "归属于母公司股东的净利润"),
    "扣非归母净利润": ("扣非归母净利润", "扣非归母净利"),
    "毛利率": ("毛利率", "销售毛利率"),
    "净利润": ("净利润", "归母净利润", "归属于母公司所有者的净利润"),
    "EPS": ("EPS", "基本每股收益", "每股收益"),
    "PE": ("PE", "P/E", "市盈率"),
    "P/E": ("PE", "P/E", "市盈率"),
    "ROE": ("ROE", "净资产收益率", "加权平均净资产收益率"),
    "P/B": ("P/B", "PB", "市净率"),
    "PB": ("P/B", "PB", "市净率"),
}


@dataclass(frozen=True, slots=True)
class MinerUEvidenceBlock:
    source_document_id: str
    page_number: int
    page_idx: int
    block_index: int
    type: str
    bbox: tuple[int | float, ...]
    locator: str
    text_kind: str
    text: str
    text_sha256: str
    char_count: int
    trusted_source: bool
    extraction_method: str
    caption_preview: str
    footnote_preview: str
    source_text_id: str

    def to_source_text_evidence(self) -> SourceTextEvidence:
        return SourceTextEvidence(
            source_text_id=self.source_text_id,
            source_document_id=self.source_document_id,
            page_number=self.page_number,
            locator=self.locator,
            text_kind="snippet_text",
            text=self.text,
            text_sha256=self.text_sha256,
            char_count=self.char_count,
            trusted_source=self.trusted_source,
            extraction_method=self.extraction_method,
        )


@dataclass(frozen=True, slots=True)
class MinerUMatchResult:
    agreement_status: AgreementStatus
    evidence: MinerUEvidenceBlock | None = None
    match_reason: str = ""
    risk_reason: str = ""


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self._row = []
        elif tag.lower() in {"td", "th"}:
            self._cell = []
            self._in_cell = True

    def handle_data(self, data: str) -> None:
        if self._in_cell and self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lower_tag = tag.lower()
        if lower_tag in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append(_normalize_space("".join(self._cell)))
            self._cell = None
            self._in_cell = False
        elif lower_tag == "tr" and self._row is not None:
            if any(cell for cell in self._row):
                self.rows.append(self._row)
            self._row = None


def load_mineru_content_list_v2_fixture(path: str | Path, *, source_document_id: str) -> list[MinerUEvidenceBlock]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return extract_mineru_evidence_blocks(payload, source_document_id=source_document_id)


def extract_mineru_evidence_blocks(payload: Any, *, source_document_id: str) -> list[MinerUEvidenceBlock]:
    if not isinstance(payload, list):
        raise ValueError("content_list_v2 payload must be a page-list")

    blocks: list[MinerUEvidenceBlock] = []
    for page_idx, page_blocks in enumerate(payload):
        if not isinstance(page_blocks, list):
            raise ValueError(f"page {page_idx} must be a block-list")
        page_number = page_idx + 1
        for block_index, block in enumerate(page_blocks):
            if not isinstance(block, dict):
                raise ValueError(f"page {page_idx} block {block_index} must be an object")
            extracted = _extract_block(
                block,
                source_document_id=source_document_id,
                page_idx=page_idx,
                page_number=page_number,
                block_index=block_index,
            )
            if extracted is not None:
                blocks.append(extracted)
    return blocks


def find_mineru_evidence_for_candidate(row: dict[str, Any], blocks: list[MinerUEvidenceBlock]) -> MinerUMatchResult:
    metric_name = _clean(row.get("metric_name"))
    period = _clean(row.get("period"))
    value = _first_number(row.get("value"))
    if not metric_name or not period or value is None:
        return MinerUMatchResult(
            agreement_status="MISSING_EVIDENCE",
            match_reason="candidate row lacks metric, period, or single numeric value",
        )

    page_number = _coerce_positive_int(row.get("page_number"))
    candidate_blocks = [block for block in blocks if page_number is None or block.page_number == page_number]
    if not candidate_blocks:
        return MinerUMatchResult(agreement_status="MISSING_EVIDENCE", match_reason="no blocks for candidate page")

    verified: list[MinerUEvidenceBlock] = []
    disagreed: list[MinerUEvidenceBlock] = []
    partial: list[MinerUEvidenceBlock] = []

    for block in candidate_blocks:
        status = _match_block(metric_name=metric_name, period=period, value=value, block=block)
        if status == "VERIFIED":
            verified.append(block)
        elif status == "DISAGREED":
            disagreed.append(block)
        elif status == "UNVERIFIED":
            partial.append(block)

    if len(verified) == 1:
        return MinerUMatchResult(
            agreement_status="VERIFIED",
            evidence=verified[0],
            match_reason="value + metric + period matched in one MinerU block",
        )
    if len(verified) > 1:
        return MinerUMatchResult(
            agreement_status="AMBIGUOUS",
            evidence=verified[0],
            match_reason="multiple MinerU blocks matched value + metric + period",
            risk_reason="ambiguous duplicate evidence",
        )
    if disagreed:
        return MinerUMatchResult(
            agreement_status="DISAGREED",
            evidence=disagreed[0],
            match_reason="metric + period present but expected value absent with conflicting numeric candidates",
            risk_reason="value conflict",
        )
    if partial:
        return MinerUMatchResult(
            agreement_status="UNVERIFIED",
            evidence=partial[0],
            match_reason="partial value/metric/period evidence only",
            risk_reason="not enough anchors for VERIFIED",
        )
    return MinerUMatchResult(agreement_status="MISSING_EVIDENCE", match_reason="no usable MinerU evidence block")


def _extract_block(
    block: dict[str, Any],
    *,
    source_document_id: str,
    page_idx: int,
    page_number: int,
    block_index: int,
) -> MinerUEvidenceBlock | None:
    block_type = _clean(block.get("type"))
    if block_type not in {"paragraph", "title", "page_header", "page_footer", "page_number", "table"}:
        return None
    content = block.get("content") if isinstance(block.get("content"), dict) else {}
    bbox = tuple(block.get("bbox") if isinstance(block.get("bbox"), list) else ())
    locator = f"mineru:v2:page:{page_number}:block:{block_index}:bbox:{_bbox_string(bbox)}"
    if block_type == "table":
        html = _clean(content.get("html")) if isinstance(content, dict) else ""
        if not html:
            return None
        text = html
        text_kind = TEXT_KIND_TABLE
    else:
        text = _flatten_content(content)
        text_kind = TEXT_KIND_PARAGRAPH
    if not text:
        return None

    text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    source_text_id = _source_text_id(source_document_id, locator, text_sha256)
    return MinerUEvidenceBlock(
        source_document_id=source_document_id,
        page_number=page_number,
        page_idx=page_idx,
        block_index=block_index,
        type=block_type,
        bbox=bbox,
        locator=locator,
        text_kind=text_kind,
        text=text,
        text_sha256=text_sha256,
        char_count=len(text),
        trusted_source=True,
        extraction_method=EXTRACTION_METHOD,
        caption_preview=_preview(_flatten_content(content.get("table_caption", [])) if isinstance(content, dict) else ""),
        footnote_preview=_preview(_flatten_content(content.get("table_footnote", [])) if isinstance(content, dict) else ""),
        source_text_id=source_text_id,
    )


def _match_block(*, metric_name: str, period: str, value: Decimal, block: MinerUEvidenceBlock) -> AgreementStatus:
    if block.text_kind == TEXT_KIND_TABLE:
        table_status = _match_table(metric_name=metric_name, period=period, value=value, html=block.text)
        if table_status != "MISSING_EVIDENCE":
            return table_status

    plain_text = _html_to_text(block.text) if block.text_kind == TEXT_KIND_TABLE else block.text
    value_hit = _number_in_text(value, plain_text)
    metric_hit = _metric_present(metric_name, plain_text)
    period_hit = _period_present(period, plain_text)
    if value_hit and metric_hit and period_hit:
        return "VERIFIED"
    if metric_hit and period_hit and not value_hit and _numeric_values(plain_text):
        return "DISAGREED"
    if value_hit or metric_hit or period_hit:
        return "UNVERIFIED"
    return "MISSING_EVIDENCE"


def _match_table(*, metric_name: str, period: str, value: Decimal, html: str) -> AgreementStatus:
    rows = _parse_table_rows(html)
    if not rows:
        return "MISSING_EVIDENCE"
    period_columns: list[int] = []
    for row in rows[:3]:
        for column_index, cell in enumerate(row):
            if _period_present(period, cell):
                period_columns.append(column_index)
    metric_rows = [row for row in rows if _metric_present(metric_name, " ".join(row))]
    if not period_columns or not metric_rows:
        return "MISSING_EVIDENCE"
    for row in metric_rows:
        for column_index in period_columns:
            if column_index >= len(row):
                continue
            cell = row[column_index]
            if _number_in_text(value, cell):
                return "VERIFIED"
            if _numeric_values(cell):
                return "DISAGREED"
    return "MISSING_EVIDENCE"


def _parse_table_rows(html: str) -> list[list[str]]:
    parser = _TableParser()
    parser.feed(html)
    return parser.rows


def _flatten_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _normalize_space(value)
    if isinstance(value, list):
        return _normalize_space(" ".join(_flatten_content(item) for item in value))
    if isinstance(value, dict):
        parts: list[str] = []
        for key in (
            "content",
            "text",
            "paragraph_content",
            "title_content",
            "page_header_content",
            "page_footer_content",
            "page_number_content",
        ):
            if key in value:
                parts.append(_flatten_content(value[key]))
        return _normalize_space(" ".join(part for part in parts if part))
    return _clean(value)


def _html_to_text(html: str) -> str:
    text = re.sub(r"</t[dh]>", " | ", html, flags=re.IGNORECASE)
    text = re.sub(r"</tr>", "\n", text, flags=re.IGNORECASE)
    return _normalize_space(unescape(_TAG_RE.sub(" ", text)))


def _metric_present(metric_name: str, text: str) -> bool:
    compact_text = _compact(text).upper()
    for alias in _metric_aliases(metric_name):
        compact_alias = _compact(alias).upper()
        if compact_alias and compact_alias in compact_text:
            return True
    return False


def _metric_aliases(metric_name: str) -> tuple[str, ...]:
    metric = _clean(metric_name)
    aliases = {metric}
    for key, values in _METRIC_ALIASES.items():
        if _compact(metric).upper() == _compact(key).upper() or _compact(key) in _compact(metric):
            aliases.update(values)
    if "扣非" in metric and "归母" in metric:
        aliases.update(_METRIC_ALIASES["扣非归母净利润"])
    elif "归母" in metric:
        aliases.update(_METRIC_ALIASES["归母净利润"])
    return tuple(alias for alias in aliases if alias)


def _period_present(period: str, text: str) -> bool:
    compact_text = _compact(text).upper()
    return any(_compact(variant).upper() in compact_text for variant in _period_variants(period) if _compact(variant))


def _period_variants(period: str) -> tuple[str, ...]:
    period_text = _clean(period)
    variants = {period_text, period_text.replace(" ", "")}
    match = re.search(r"(20\d{2})", period_text)
    if match:
        year = match.group(1)
        compact_period = _compact(period_text).upper()
        if "Q1" in compact_period or "一季度" in period_text:
            variants.update({f"{year}Q1", f"{year}年Q1", f"{year}年一季度", f"{year}一季度"})
        if period_text.upper().endswith("E"):
            variants.update({f"{year}E", f"{year} E"})
    return tuple(variant for variant in variants if variant)


def _number_in_text(value: Decimal, text: str) -> bool:
    return any(number == value for number in _numeric_values(text))


def _first_number(value: Any) -> Decimal | None:
    values = _numeric_values(_clean(value))
    if len(values) != 1:
        return None
    return values[0]


def _numeric_values(text: str) -> list[Decimal]:
    values: list[Decimal] = []
    for match in _NUMBER_RE.finditer(text.replace("，", ",")):
        value = _normalize_numeric_value(match.group(0))
        if value is not None:
            values.append(value.normalize())
    return values


def _normalize_numeric_value(value: str) -> Decimal | None:
    text = value.strip().replace("，", ",")
    if not text:
        return None
    is_negative_parentheses = text.startswith("(") and text.endswith(")")
    if is_negative_parentheses:
        text = text[1:-1].strip()
    text = text.replace(",", "").replace("+", "").replace("％", "%")
    if text.endswith("%"):
        text = text[:-1]
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    return -number if is_negative_parentheses else number


def _source_text_id(source_document_id: str, locator: str, text_sha256: str) -> str:
    digest = hashlib.sha256(f"{source_document_id}|{locator}|{text_sha256}".encode("utf-8")).hexdigest()
    return f"r7am:{digest[:24]}"


def _bbox_string(bbox: tuple[int | float, ...]) -> str:
    return ",".join(_clean(value) for value in bbox[:4])


def _coerce_positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = int(str(value).replace("P", "").replace("p", "").strip())
    except ValueError:
        return None
    return number if number > 0 else None


def _preview(text: str, limit: int = 120) -> str:
    normalized = _normalize_space(text)
    return normalized if len(normalized) <= limit else normalized[: limit - 3] + "..."


def _compact(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff%/]+", "", _clean(text).replace("／", "/"))


def _normalize_space(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", _clean(text)).strip()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
