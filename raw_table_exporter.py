import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

from artifact_names import ARTIFACT_RAW_TABLES
from extractor_quality import score_table_block
from table_block import TableBlock, dataframe_to_table_block


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_preview(df: Any, max_rows: int = 3, max_cols: int = 5, max_len: int = 300) -> str:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines: List[str] = []
    for _, row in sample.iterrows():
        lines.append(" | ".join(_normalize_text(x) for x in row.tolist()))
    text = " || ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _safe_sheet_name(raw_name: str, used_names: set) -> str:
    clean_name = re.sub(r"[\\/*?:\[\]]", "_", _normalize_text(raw_name) or "sheet")
    clean_name = clean_name[:31]
    base = clean_name
    idx = 1
    while clean_name in used_names:
        suffix = f"_{idx}"
        clean_name = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used_names.add(clean_name)
    return clean_name


def _to_table_block(item: Any) -> TableBlock | None:
    if isinstance(item, TableBlock):
        return item

    if isinstance(item, dict):
        df = item.get("raw_df")
        if not isinstance(df, pd.DataFrame):
            df = item.get("df")
        if not isinstance(df, pd.DataFrame):
            return None
        block = dataframe_to_table_block(
            df=df,
            backend=_normalize_text(item.get("backend") or "unknown"),
            page=item.get("page"),
            table_index=item.get("table_index"),
            source_meta=item.get("source_meta") or {},
        )
        block.raw_markdown = _normalize_text(item.get("raw_markdown"))
        block.raw_html = _normalize_text(item.get("raw_html"))
        block.confidence = item.get("confidence")
        block.bbox = item.get("bbox")
        return block

    return None


def _iter_blocks(table_blocks: Iterable[Any]) -> List[TableBlock]:
    blocks: List[TableBlock] = []
    for item in table_blocks or []:
        block = _to_table_block(item)
        if block is None:
            continue
        if not isinstance(block.raw_df, pd.DataFrame):
            continue
        blocks.append(block)
    return blocks


def _build_sheet_base_name(block: TableBlock) -> str:
    backend = _normalize_text(block.backend or "unknown")
    page = _normalize_text(block.page) or "NA"
    table_index = _normalize_text(block.table_index) or "NA"
    return f"raw_{backend}_p{page}_t{table_index}"


def export_raw_table_assets(
    table_blocks,
    pkg_path,
    source_pdf,
    save_workbook_func,
    logger=None,
):
    blocks = _iter_blocks(table_blocks)
    used_sheet_names: set = set()
    sheet_map: Dict[str, pd.DataFrame] = {}
    index_rows: List[Dict[str, Any]] = []

    for block in blocks:
        raw_df = block.raw_df.copy() if isinstance(block.raw_df, pd.DataFrame) else pd.DataFrame()
        score = score_table_block(block)
        sheet_name = _safe_sheet_name(_build_sheet_base_name(block), used_sheet_names)
        sheet_map[sheet_name] = raw_df
        index_rows.append(
            {
                "source_pdf": source_pdf,
                "backend": _normalize_text(block.backend),
                "page": block.page,
                "table_index": block.table_index,
                "sheet_name": sheet_name,
                "row_count": block.row_count,
                "col_count": block.col_count,
                "non_empty_cell_count": block.non_empty_cell_count,
                "empty_cell_ratio": block.empty_cell_ratio,
                "quality_score": score.get("quality_score", 0.0),
                "quality_level": score.get("quality_level", ""),
                "quality_flags": score.get("quality_flags", ""),
                "preview": _build_preview(raw_df),
            }
        )

    index_df = pd.DataFrame(
        index_rows,
        columns=[
            "source_pdf",
            "backend",
            "page",
            "table_index",
            "sheet_name",
            "row_count",
            "col_count",
            "non_empty_cell_count",
            "empty_cell_ratio",
            "quality_score",
            "quality_level",
            "quality_flags",
            "preview",
        ],
    )
    workbook_data = {"00_表格索引": index_df}
    workbook_data.update(sheet_map)

    target_path = str(Path(pkg_path) / ARTIFACT_RAW_TABLES)
    final_path = save_workbook_func(workbook_data, target_path)
    if logger:
        logger.info(
            "Raw table assets exported: path=%s index_rows=%s raw_sheet_count=%s",
            final_path,
            len(index_rows),
            len(sheet_map),
        )
    return final_path
