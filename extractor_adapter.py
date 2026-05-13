import re
import importlib.util
from typing import Any, Dict, List, Optional

import pandas as pd

from pdfplumber_table_extractor import extract_tables_from_pdf
from table_block import TableBlock, dataframe_to_table_block


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _unique_columns(columns: List[str]) -> List[str]:
    seen: Dict[str, int] = {}
    result: List[str] = []
    for col in columns:
        raw = _normalize_text(col) or "unnamed_col"
        if raw not in seen:
            seen[raw] = 0
            result.append(raw)
        else:
            seen[raw] += 1
            result.append(f"{raw}.{seen[raw]}")
    return result


def _extract_markdown_table_blocks(markdown_text: str) -> List[str]:
    lines = markdown_text.splitlines()
    blocks: List[str] = []
    current: List[str] = []
    non_table_gap = 0

    for line in lines:
        stripped = line.strip()
        if stripped.count("|") >= 2:
            current.append(stripped)
            non_table_gap = 0
            continue

        if current:
            non_table_gap += 1
            if non_table_gap >= 2:
                blocks.append("\n".join(current))
                current = []
                non_table_gap = 0

    if current:
        blocks.append("\n".join(current))
    return blocks


def _parse_markdown_table_to_df(table_block: str) -> Optional[pd.DataFrame]:
    lines = [line for line in table_block.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return None

    filtered = [line for line in lines if not re.match(r"^\s*\|?[\s:\-]+\|[\s\|\-:]*\|?\s*$", line)]
    if len(filtered) < 2:
        return None

    rows: List[List[str]] = []
    for line in filtered:
        segment = line.strip()
        if segment.startswith("|"):
            segment = segment[1:]
        if segment.endswith("|"):
            segment = segment[:-1]
        rows.append([cell.strip() for cell in segment.split("|")])

    width = max((len(r) for r in rows), default=0)
    if width == 0:
        return None

    rows = [r + [""] * (width - len(r)) for r in rows]
    header = _unique_columns(rows[0])
    body = rows[1:]
    if not body:
        return None

    df = pd.DataFrame(body, columns=header)
    normalized = df.fillna("").astype(str)
    normalized = normalized.apply(lambda col: col.map(lambda v: re.sub(r"\s+", " ", str(v)).strip()))
    normalized = normalized.loc[(normalized != "").any(axis=1), (normalized != "").any(axis=0)]
    if normalized.empty or normalized.shape[1] == 0:
        return None
    return normalized.reset_index(drop=True)


def extract_pdfplumber_table_blocks(pdf_path: str, config: Optional[dict], logger=None) -> List[TableBlock]:
    blocks: List[TableBlock] = []
    raw_blocks = extract_tables_from_pdf(pdf_path, pages="all", logger=logger, config=(config or {}))
    for item in raw_blocks or []:
        df = item.get("df")
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        block = dataframe_to_table_block(
            df=df,
            backend="pdfplumber",
            page=item.get("page"),
            table_index=item.get("table_index"),
            source_meta={
                "preview": item.get("preview", ""),
                "confidence": item.get("confidence"),
                "bbox": item.get("bbox"),
            },
        )
        block.confidence = item.get("confidence")
        block.bbox = item.get("bbox")
        blocks.append(block)
    return blocks


def extract_marker_table_blocks(markdown_text: str, config: Optional[dict], logger=None) -> List[TableBlock]:
    blocks: List[TableBlock] = []
    table_blocks = _extract_markdown_table_blocks(markdown_text or "")
    for idx, block_text in enumerate(table_blocks, start=1):
        df = _parse_markdown_table_to_df(block_text)
        if df is None or df.empty:
            continue
        block = dataframe_to_table_block(
            df=df,
            backend="marker",
            page=None,
            table_index=idx,
            source_meta={"markdown_block_index": idx},
        )
        block.raw_markdown = block_text
        blocks.append(block)
    return blocks


def extract_docling_table_blocks(pdf_path: str, config: Optional[dict], logger=None) -> List[TableBlock]:
    spec = importlib.util.find_spec("docling")
    if spec is None:
        if logger:
            logger.info("extract_docling_table_blocks: docling not installed")
        return []

    try:
        from docling.document_converter import DocumentConverter  # type: ignore
    except Exception:
        if logger:
            logger.exception("extract_docling_table_blocks: failed to import DocumentConverter")
        return []

    blocks: List[TableBlock] = []
    try:
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        doc = getattr(result, "document", None)
        if doc is None:
            if logger:
                logger.info("extract_docling_table_blocks: no document returned")
            return []

        tables = list(getattr(doc, "tables", []) or [])
        for idx, table in enumerate(tables, start=1):
            df: Optional[pd.DataFrame] = None
            raw_markdown = ""
            raw_html = ""
            page = None
            source_meta: Dict[str, Any] = {}

            for attr_name in ("page_no", "page", "page_number"):
                if hasattr(table, attr_name):
                    page = getattr(table, attr_name)
                    break

            if hasattr(table, "export_to_dataframe"):
                try:
                    candidate = table.export_to_dataframe()
                    if isinstance(candidate, pd.DataFrame):
                        df = candidate
                except Exception:
                    pass

            if df is None and hasattr(table, "to_dataframe"):
                try:
                    candidate = table.to_dataframe()
                    if isinstance(candidate, pd.DataFrame):
                        df = candidate
                except Exception:
                    pass

            if hasattr(table, "export_to_markdown"):
                try:
                    raw_markdown = str(table.export_to_markdown() or "")
                except Exception:
                    raw_markdown = ""

            if hasattr(table, "export_to_html"):
                try:
                    raw_html = str(table.export_to_html() or "")
                except Exception:
                    raw_html = ""

            if df is None and raw_markdown:
                df = _parse_markdown_table_to_df(raw_markdown)

            if df is None or df.empty:
                continue

            df = df.fillna("").astype(str)
            block = dataframe_to_table_block(
                df=df,
                backend="docling",
                page=page,
                table_index=idx,
                source_meta=source_meta,
            )
            block.raw_markdown = raw_markdown
            block.raw_html = raw_html
            blocks.append(block)
    except Exception:
        if logger:
            logger.exception("extract_docling_table_blocks failed")
        return []

    if logger:
        logger.info("extract_docling_table_blocks: extracted %s tables", len(blocks))
    return blocks
