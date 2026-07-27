"""Adapter for page-grouped MinerU ``content_list_v2`` JSON."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Any, Callable, Mapping, Sequence

from ..models import NormalizedRecord, UNPARSEABLE
from ..normalization import bounded_preview, compact_text, normalize_metric_key, normalize_numeric, normalize_period, normalize_unit


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[tuple[str, int, int]]] = []
        self._row: list[tuple[str, int, int]] | None = None
        self._parts: list[str] | None = None
        self._rowspan = 1
        self._colspan = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        if lowered == "tr":
            self._row = []
        elif lowered in {"td", "th"}:
            values = dict(attrs)
            self._parts = []
            self._rowspan = _positive_int(values.get("rowspan"))
            self._colspan = _positive_int(values.get("colspan"))
        elif lowered == "br" and self._parts is not None:
            self._parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._parts is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered in {"td", "th"} and self._parts is not None and self._row is not None:
            self._row.append((compact_text("".join(self._parts)), self._rowspan, self._colspan))
            self._parts = None
            self._rowspan = 1
            self._colspan = 1
        elif lowered == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


def expand_html_table(html: Any) -> list[list[str]]:
    if not isinstance(html, str) or not html.strip():
        return []
    parser = _TableParser()
    parser.feed(html)
    parser.close()
    return _expand_cells(parser.rows)


def extract_mineru_records(
    artifact: Any,
    *,
    source: str = "left",
    metric_normalizer: Callable[[Any], str] = normalize_metric_key,
) -> list[NormalizedRecord]:
    records: list[NormalizedRecord] = []
    for page_index, blocks in enumerate(_page_groups(artifact)):
        if not isinstance(blocks, list):
            continue
        for block_index, block in enumerate(blocks):
            if not isinstance(block, Mapping):
                continue
            records.extend(
                _records_from_block(
                    block,
                    source=source,
                    page_index=page_index,
                    block_index=block_index,
                    metric_normalizer=metric_normalizer,
                )
            )
    return records


def extract_mineru_blocks(artifact: Any) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for page_index, page_blocks in enumerate(_page_groups(artifact)):
        if not isinstance(page_blocks, list):
            continue
        for block_index, block in enumerate(page_blocks):
            if not isinstance(block, Mapping):
                continue
            content = _content_mapping(block)
            text = _block_text(block, content)
            blocks.append(
                {
                    "page_number": page_index + 1,
                    "page_idx": page_index,
                    "block_index": block_index,
                    "type": compact_text(block.get("type", "unknown")).casefold() or "unknown",
                    "bbox": list(block.get("bbox", [])) if isinstance(block.get("bbox"), Sequence) and not isinstance(block.get("bbox"), str) else [],
                    "caption_preview": bounded_preview(_caption(block, content)),
                    "footnote_preview": bounded_preview(_footnote(block, content)),
                    "text_preview": bounded_preview(text),
                }
            )
    return blocks


def _records_from_block(
    block: Mapping[str, Any],
    *,
    source: str,
    page_index: int,
    block_index: int,
    metric_normalizer: Callable[[Any], str],
) -> list[NormalizedRecord]:
    content = _content_mapping(block)
    block_type = compact_text(block.get("type", "")).casefold()
    trace_base = _trace_base(block, content, source=source, page_index=page_index, block_index=block_index)
    if block_type == "table":
        html = content.get("html", block.get("html"))
        return _records_from_table(
            expand_html_table(html),
            source=source,
            trace_base=trace_base,
            context=_caption(block, content) or f"page_{page_index + 1}",
            default_unit=_unit_from_context(_caption(block, content)),
            metric_normalizer=metric_normalizer,
        )
    explicit_records = content.get("records", block.get("records"))
    if not isinstance(explicit_records, list):
        return []
    output: list[NormalizedRecord] = []
    for item_index, item in enumerate(explicit_records):
        if not isinstance(item, Mapping):
            continue
        metric_display_name = compact_text(item.get("metric_display_name", item.get("metric", "")))
        period = normalize_period(item.get("period"))
        raw_value = item.get("value", item.get("normalized_value"))
        normalized_value = normalize_numeric(raw_value)
        if not metric_display_name or not period or raw_value is None:
            continue
        trace = dict(trace_base)
        trace.update({"row": item_index + 1, "column": 1, "locator": f"page:{page_index + 1}:block:{block_index}:record:{item_index + 1}"})
        output.append(
            NormalizedRecord(
                source=source,
                context=compact_text(item.get("context", trace_base["caption_preview"] or f"page_{page_index + 1}")),
                metric_key=metric_normalizer(metric_display_name),
                metric_display_name=metric_display_name,
                period=period,
                normalized_value=normalized_value,
                normalized_unit=normalize_unit(item.get("unit")),
                evidence_preview=bounded_preview(_block_text(block, content) or f"{metric_display_name} {period} {raw_value}"),
                source_trace=trace,
                parse_status="PARSED" if normalized_value is not None else UNPARSEABLE,
            )
        )
    return output


def _records_from_table(
    matrix: list[list[str]],
    *,
    source: str,
    trace_base: Mapping[str, Any],
    context: str,
    default_unit: str | None,
    metric_normalizer: Callable[[Any], str],
) -> list[NormalizedRecord]:
    header_index, period_columns = _find_period_header(matrix)
    if header_index is None or not period_columns:
        return []
    header = matrix[header_index]
    metric_column = next((index for index in range(len(header)) if index not in {item[0] for item in period_columns}), 0)
    records: list[NormalizedRecord] = []
    for row_index, row in enumerate(matrix[header_index + 1 :], start=header_index + 1):
        metric_display_name = _cell(row, metric_column)
        if not metric_display_name:
            continue
        for column_index, period in period_columns:
            raw_value = _cell(row, column_index)
            if not raw_value:
                continue
            normalized_value = normalize_numeric(raw_value)
            trace = dict(trace_base)
            trace.update(
                {
                    "row": row_index + 1,
                    "column": column_index + 1,
                    "locator": f"page:{trace_base['page_number']}:block:{trace_base['block_index']}:row:{row_index + 1}:col:{column_index + 1}",
                }
            )
            records.append(
                NormalizedRecord(
                    source=source,
                    context=compact_text(context),
                    metric_key=metric_normalizer(metric_display_name),
                    metric_display_name=metric_display_name,
                    period=period,
                    normalized_value=normalized_value,
                    normalized_unit=default_unit,
                    evidence_preview=bounded_preview(f"{context} | {metric_display_name} | {period} | {raw_value}"),
                    source_trace=trace,
                    parse_status="PARSED" if normalized_value is not None else UNPARSEABLE,
                )
            )
    return records


def _page_groups(artifact: Any) -> list[Any]:
    if isinstance(artifact, list):
        return artifact
    if isinstance(artifact, Mapping):
        for key in ("pages", "content_list_v2", "content_list"):
            value = artifact.get(key)
            if isinstance(value, list):
                return value
    return []


def _content_mapping(block: Mapping[str, Any]) -> Mapping[str, Any]:
    content = block.get("content")
    return content if isinstance(content, Mapping) else {}


def _caption(block: Mapping[str, Any], content: Mapping[str, Any]) -> str:
    return compact_text(content.get("table_caption", content.get("caption", block.get("caption", block.get("table_caption", "")))))


def _footnote(block: Mapping[str, Any], content: Mapping[str, Any]) -> str:
    return compact_text(content.get("table_footnote", content.get("footnote", block.get("footnote", block.get("table_footnote", "")))))


def _block_text(block: Mapping[str, Any], content: Mapping[str, Any]) -> str:
    for value in (block.get("text"), content.get("text"), content.get("text_content"), block.get("text_content")):
        if isinstance(value, str) and compact_text(value):
            return compact_text(value)
    return ""


def _trace_base(block: Mapping[str, Any], content: Mapping[str, Any], *, source: str, page_index: int, block_index: int) -> dict[str, Any]:
    bbox = block.get("bbox")
    return {
        "source": source,
        "page_number": page_index + 1,
        "page_idx": page_index,
        "block_index": block_index,
        "block_type": compact_text(block.get("type", "unknown")).casefold() or "unknown",
        "bbox": list(bbox) if isinstance(bbox, Sequence) and not isinstance(bbox, str) else [],
        "caption_preview": bounded_preview(_caption(block, content)),
        "footnote_preview": bounded_preview(_footnote(block, content)),
    }


def _find_period_header(matrix: list[list[str]]) -> tuple[int | None, list[tuple[int, str]]]:
    for row_index, row in enumerate(matrix):
        period_columns = [(column_index, period) for column_index, value in enumerate(row) if (period := normalize_period(value))]
        if period_columns:
            return row_index, period_columns
    return None, []


def _expand_cells(rows: list[list[tuple[str, int, int]]]) -> list[list[str]]:
    grid: list[list[str | None]] = []
    for row_index, cells in enumerate(rows):
        _ensure_grid_row(grid, row_index)
        column_index = 0
        for text, rowspan, colspan in cells:
            while _grid_value(grid, row_index, column_index) is not None:
                column_index += 1
            for target_row in range(row_index, row_index + rowspan):
                _ensure_grid_row(grid, target_row)
                for target_column in range(column_index, column_index + colspan):
                    _ensure_grid_column(grid[target_row], target_column)
                    grid[target_row][target_column] = text
            column_index += colspan
    width = max((len(row) for row in grid), default=0)
    return [[value or "" for value in row + [None] * (width - len(row))] for row in grid]


def _positive_int(value: Any) -> int:
    try:
        return max(int(value or 1), 1)
    except (TypeError, ValueError):
        return 1


def _cell(row: list[str], index: int) -> str:
    return compact_text(row[index]) if 0 <= index < len(row) else ""


def _unit_from_context(value: Any) -> str | None:
    text = compact_text(value)
    for unit in ("百万元", "亿元", "万元", "千元", "元", "%", "倍"):
        if unit in text:
            return normalize_unit(unit)
    return None


def _ensure_grid_row(grid: list[list[str | None]], index: int) -> None:
    while len(grid) <= index:
        grid.append([])


def _ensure_grid_column(row: list[str | None], index: int) -> None:
    while len(row) <= index:
        row.append(None)


def _grid_value(grid: list[list[str | None]], row_index: int, column_index: int) -> str | None:
    row = grid[row_index]
    return row[column_index] if column_index < len(row) else None
