from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class DoclingDiscoveredGroup:
    image_name: str
    input_image_path: str
    matched_output_folder: str
    json_paths: List[str]
    md_paths: List[str]
    html_paths: List[str]
    stdout_path: str
    stderr_path: str
    returncode_path: str
    warnings: List[str]


@dataclass
class DoclingNormalizedCell:
    row_index: int
    col_index: int
    row_span: int
    col_span: int
    text: str
    is_header: bool
    provenance: Dict[str, Any]


@dataclass
class DoclingNormalizedTable:
    tool: str
    image_name: str
    input_image_path: str
    docling_json_path: str
    table_index: int
    table_title: str
    unit: str
    num_rows: int
    num_cols: int
    cells: List[DoclingNormalizedCell]
    warnings: List[str]
    returncode: Optional[int]
    stderr_text: str


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def discover_docling_groups(input_image_dir: Path, docling_output_dir: Path) -> Tuple[List[DoclingDiscoveredGroup], List[Path]]:
    input_images = sorted(path for path in input_image_dir.iterdir() if path.is_file()) if input_image_dir.exists() else []
    root_jsons = sorted(docling_output_dir.glob("*.json")) if docling_output_dir.exists() else []
    groups: List[DoclingDiscoveredGroup] = []

    for image_path in input_images:
        stem = image_path.stem
        folder = docling_output_dir / stem
        warnings: List[str] = []
        json_paths: List[str] = []
        md_paths: List[str] = []
        html_paths: List[str] = []
        stdout_path = ""
        stderr_path = ""
        returncode_path = ""
        matched_output_folder = ""

        if folder.exists() and folder.is_dir():
            matched_output_folder = str(folder)
            json_paths.extend(str(path) for path in sorted(folder.glob("*.json")))
            md_paths.extend(str(path) for path in sorted(folder.glob("*.md")))
            html_paths.extend(str(path) for path in sorted(folder.glob("*.html")))
            stdout_path = str(folder / "stdout.txt") if (folder / "stdout.txt").exists() else ""
            stderr_path = str(folder / "stderr.txt") if (folder / "stderr.txt").exists() else ""
            returncode_path = str(folder / "returncode.txt") if (folder / "returncode.txt").exists() else ""
        else:
            warnings.append("OUTPUT_FOLDER_MISSING")

        for root_json in root_jsons:
            if root_json.stem == stem and str(root_json) not in json_paths:
                json_paths.append(str(root_json))

        if not json_paths:
            warnings.append("JSON_OUTPUT_MISSING")

        groups.append(
            DoclingDiscoveredGroup(
                image_name=image_path.name,
                input_image_path=str(image_path),
                matched_output_folder=matched_output_folder,
                json_paths=json_paths,
                md_paths=md_paths,
                html_paths=html_paths,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                returncode_path=returncode_path,
                warnings=warnings,
            )
        )

    return groups, root_jsons


def _table_title_from_cells(cells: Sequence[DoclingNormalizedCell]) -> str:
    header_cells = sorted((cell for cell in cells if cell.is_header), key=lambda cell: (cell.row_index, cell.col_index))
    if not header_cells:
        return ""
    first_row_index = header_cells[0].row_index
    first_row = [cell.text for cell in header_cells if cell.row_index == first_row_index and cell.text]
    if len(first_row) == 1:
        return first_row[0]
    return ""


def _extract_cells_from_table_data(data: Dict[str, Any]) -> Tuple[List[DoclingNormalizedCell], int, int, List[str]]:
    warnings: List[str] = []
    table_cells = data.get("table_cells") or data.get("cells") or []
    cells: List[DoclingNormalizedCell] = []
    max_row = 0
    max_col = 0

    for idx, cell in enumerate(table_cells):
        if not isinstance(cell, dict):
            warnings.append("NON_DICT_CELL_SKIPPED")
            continue

        row_index = int(cell.get("start_row_offset_idx", cell.get("row_index", 0)) or 0)
        col_index = int(cell.get("start_col_offset_idx", cell.get("col_index", 0)) or 0)
        row_span = int(cell.get("row_span", 1) or 1)
        col_span = int(cell.get("col_span", 1) or 1)
        text = _norm(cell.get("text") or cell.get("label") or cell.get("value"))
        is_header = bool(cell.get("column_header") or cell.get("row_header") or cell.get("is_header"))

        cells.append(
            DoclingNormalizedCell(
                row_index=row_index,
                col_index=col_index,
                row_span=row_span,
                col_span=col_span,
                text=text,
                is_header=is_header,
                provenance={
                    "cell_index": idx,
                    "bbox": cell.get("bbox"),
                    "row_header": bool(cell.get("row_header", False)),
                    "column_header": bool(cell.get("column_header", False)),
                    "row_section": bool(cell.get("row_section", False)),
                },
            )
        )
        max_row = max(max_row, row_index + row_span)
        max_col = max(max_col, col_index + col_span)

    num_rows = int(data.get("num_rows") or max_row)
    num_cols = int(data.get("num_cols") or max_col)
    return cells, num_rows, num_cols, warnings


def _detect_unit(table_title: str) -> str:
    for hint in ["百万元", "亿元", "万元", "元", "%", "百万"]:
        if hint in table_title:
            return hint
    return ""


def parse_docling_json(
    json_path: Path,
    image_name: str,
    input_image_path: str,
    returncode: Optional[int],
    stderr_text: str,
) -> Tuple[List[DoclingNormalizedTable], List[str]]:
    warnings: List[str] = []
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception as exc:
        return [], [f"JSON_PARSE_FAILED:{exc}"]

    table_nodes: List[Dict[str, Any]] = []
    if isinstance(payload, dict):
        top_tables = payload.get("tables")
        if isinstance(top_tables, list):
            table_nodes.extend(item for item in top_tables if isinstance(item, dict))
        if not table_nodes:
            body = payload.get("body")
            if isinstance(body, dict):
                nested_tables = body.get("tables")
                if isinstance(nested_tables, list):
                    table_nodes.extend(item for item in nested_tables if isinstance(item, dict))
    elif isinstance(payload, list):
        table_nodes.extend(item for item in payload if isinstance(item, dict))

    if not table_nodes:
        return [], ["NO_TABLE_NODES_FOUND"]

    normalized_tables: List[DoclingNormalizedTable] = []
    for table_index, table_node in enumerate(table_nodes):
        data = table_node.get("data") if isinstance(table_node.get("data"), dict) else table_node
        if not isinstance(data, dict):
            warnings.append("TABLE_DATA_MISSING")
            continue

        cells, num_rows, num_cols, cell_warnings = _extract_cells_from_table_data(data)
        table_title = _table_title_from_cells(cells)
        normalized_tables.append(
            DoclingNormalizedTable(
                tool="docling",
                image_name=image_name,
                input_image_path=input_image_path,
                docling_json_path=str(json_path),
                table_index=table_index,
                table_title=table_title,
                unit=_detect_unit(table_title),
                num_rows=num_rows,
                num_cols=num_cols,
                cells=cells,
                warnings=cell_warnings,
                returncode=returncode,
                stderr_text=stderr_text,
            )
        )

    return normalized_tables, warnings
