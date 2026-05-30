from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class ExtractedTable:
    extracted_table_id: str
    table_asset_id: str
    source_doc_name: str
    table_role_guess: str
    image_path: str
    recognizer_name: str
    recognizer_version: str
    recognition_status: str
    row_count: int
    col_count: int
    cell_count: int
    non_empty_cell_count: int
    raw_text: str
    row_texts: List[str] = field(default_factory=list)
    table_grid: List[List[str]] = field(default_factory=list)
    cells: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
