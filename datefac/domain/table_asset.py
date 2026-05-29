from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TableAsset:
    source_root: str
    source_file: str
    source_kind: str
    block_index: int
    page_idx: Optional[int] = None
    bbox: Optional[List[float]] = None
    image_path: str = ""
    caption: str = ""
    footnote: str = ""
    nearby_text: str = ""
    table_role_guess: str = "general_table"
    table_role_reason: str = ""
    raw_block_type: str = ""
    raw_block_id: str = ""
    source_doc_id: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TableAssetWarning:
    source_file: str
    warning_code: str
    warning_message: str
    block_index: Optional[int] = None
    block_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MineruSourceFile:
    source_file: str
    source_kind: str
    file_exists: bool
    file_size: int = 0
    related_images_dir: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def make_source_file(path: Path, source_kind: str, related_images_dir: str = "", notes: str = "") -> MineruSourceFile:
    exists = path.exists()
    return MineruSourceFile(
        source_file=str(path),
        source_kind=source_kind,
        file_exists=bool(exists),
        file_size=int(path.stat().st_size) if exists else 0,
        related_images_dir=related_images_dir,
        notes=notes,
    )

