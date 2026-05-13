from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class TableBlock:
    backend: str
    page: Any = None
    table_index: Any = None
    bbox: Any = None
    confidence: Optional[float] = None
    raw_df: Any = None
    raw_markdown: str = ""
    raw_html: str = ""
    row_count: int = 0
    col_count: int = 0
    non_empty_cell_count: int = 0
    empty_cell_ratio: float = 0.0
    extraction_warnings: Optional[List[str]] = None
    source_meta: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.extraction_warnings is None:
            self.extraction_warnings = []
        if self.source_meta is None:
            self.source_meta = {}


def compute_table_quality_features(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "row_count": 0,
            "col_count": 0,
            "non_empty_cell_count": 0,
            "empty_cell_ratio": 1.0,
        }

    normalized = df.fillna("").astype(str)
    row_count, col_count = normalized.shape
    total_cells = row_count * col_count
    stripped = normalized.replace(r"^\s*$", "", regex=True)
    non_empty = int((stripped != "").sum().sum()) if total_cells > 0 else 0
    empty_ratio = 1.0
    if total_cells > 0:
        empty_ratio = max(0.0, min(1.0, 1 - (non_empty / total_cells)))
    return {
        "row_count": int(row_count),
        "col_count": int(col_count),
        "non_empty_cell_count": int(non_empty),
        "empty_cell_ratio": float(round(empty_ratio, 4)),
    }


def dataframe_to_table_block(
    df: Optional[pd.DataFrame],
    backend: str,
    page: Any = None,
    table_index: Any = None,
    source_meta: Optional[Dict[str, Any]] = None,
) -> TableBlock:
    features = compute_table_quality_features(df)
    return TableBlock(
        backend=backend,
        page=page,
        table_index=table_index,
        raw_df=df,
        row_count=features["row_count"],
        col_count=features["col_count"],
        non_empty_cell_count=features["non_empty_cell_count"],
        empty_cell_ratio=features["empty_cell_ratio"],
        source_meta=source_meta or {},
    )
