import re
from typing import Dict, List, Optional

import pandas as pd


def _normalize_df(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    if df is None:
        return None
    normalized = df.fillna("").astype(str)
    normalized = normalized.apply(lambda col: col.map(lambda v: re.sub(r"\s+", " ", v).strip()))
    normalized = normalized.loc[(normalized != "").any(axis=1), (normalized != "").any(axis=0)]
    if normalized.empty or normalized.shape[1] == 0:
        return None
    return normalized.reset_index(drop=True)


def _build_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 5, max_len: int = 300) -> str:
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        lines.append(" | ".join(cell.strip() for cell in row.tolist()))
    text = " || ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def extract_tables_from_pdf(pdf_path, pages="all", logger=None, config=None) -> List[Dict]:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        if logger:
            logger.warning("pdfplumber not installed, skip pdfplumber extraction")
        return []

    table_blocks: List[Dict] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            if pages == "all":
                target_pages = list(range(1, total_pages + 1))
            else:
                target_pages = [p for p in pages if isinstance(p, int) and 1 <= p <= total_pages]
                if not target_pages:
                    target_pages = list(range(1, total_pages + 1))

            for page_no in target_pages:
                try:
                    page = pdf.pages[page_no - 1]
                    tables = page.extract_tables() or []
                    for table_idx, table in enumerate(tables, start=1):
                        raw_df = pd.DataFrame(table) if table else None
                        df = _normalize_df(raw_df)
                        if df is None:
                            continue
                        table_blocks.append(
                            {
                                "backend": "pdfplumber",
                                "page": page_no,
                                "table_index": table_idx,
                                "df": df,
                                "rows": int(df.shape[0]),
                                "cols": int(df.shape[1]),
                                "preview": _build_preview(df),
                                "confidence": 0.8,
                                "title": "",
                                "bbox": "",
                            }
                        )
                except Exception as page_exc:
                    if logger:
                        logger.warning("pdfplumber page extraction failed: page=%s err=%s", page_no, page_exc)
                    continue
    except Exception as exc:
        if logger:
            logger.warning("pdfplumber extraction failed for file=%s err=%s", pdf_path, exc)
        return []
    return table_blocks


def table_blocks_to_dfs(table_blocks: List[Dict]) -> List[pd.DataFrame]:
    dfs: List[pd.DataFrame] = []
    for block in table_blocks or []:
        df = block.get("df")
        if isinstance(df, pd.DataFrame) and not df.empty:
            dfs.append(df)
    return dfs


def build_table_index_dataframe(table_blocks: List[Dict], sheet_names: List[str]) -> pd.DataFrame:
    rows = []
    for idx, block in enumerate(table_blocks or []):
        rows.append(
            {
                "sheet_name": sheet_names[idx] if idx < len(sheet_names) else "",
                "backend": block.get("backend", ""),
                "page": block.get("page", ""),
                "table_index": block.get("table_index", ""),
                "rows": block.get("rows", ""),
                "cols": block.get("cols", ""),
                "preview": block.get("preview", ""),
                "confidence": block.get("confidence", ""),
                "business_hint": block.get("business_hint", ""),
                "source_blocks": ",".join(block.get("source_blocks", [])) if isinstance(block.get("source_blocks"), list) else block.get("source_blocks", ""),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "sheet_name",
            "backend",
            "page",
            "table_index",
            "rows",
            "cols",
            "preview",
            "confidence",
            "business_hint",
            "source_blocks",
        ],
    )
