from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


PREFERRED_JSON_FILES = ("vlm_output.json",)
PREFERRED_TEXT_FILES = ("raw_response.txt",)
TABLE_META_FILE = "table_meta.json"
YEAR_LIKE_RE = re.compile(r"^20\d{2}(?:[AE])?$", re.IGNORECASE)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_text(value: Any) -> Optional[str]:
    text = _norm(value)
    if not text or text.lower() in {"none", "null", "nan"}:
        return None
    return text


def canonicalize_column_label(value: Any) -> str:
    text = _norm(value).upper().replace(" ", "")
    text = text.replace("年", "")
    return text


def is_year_like_label(value: Any) -> bool:
    return bool(YEAR_LIKE_RE.match(canonicalize_column_label(value)))


def parse_json_like_text(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.IGNORECASE | re.DOTALL)
        if match:
            stripped = match.group(1).strip()
    if stripped:
        try:
            return json.loads(stripped)
        except Exception:
            pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return json.loads(stripped[start : end + 1])
    raise json.JSONDecodeError("No JSON object found", stripped, 0)


@dataclass
class VLMValueCell:
    column: str
    source_column_label: Optional[str]
    raw_value: Any
    normalized_value: Any
    value_index: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VLMRow:
    row_index: int
    source_row_index: Optional[int]
    row_name: Optional[str]
    metric_name_raw: Optional[str]
    metric_name_cn: Optional[str]
    confidence: Optional[float] = None
    uncertain: bool = False
    warnings: List[str] = field(default_factory=list)
    values: List[VLMValueCell] = field(default_factory=list)
    schema_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_index": self.row_index,
            "source_row_index": self.source_row_index,
            "row_name": self.row_name,
            "metric_name_raw": self.metric_name_raw,
            "metric_name_cn": self.metric_name_cn,
            "confidence": self.confidence,
            "uncertain": self.uncertain,
            "warnings": list(self.warnings),
            "values": [v.to_dict() for v in self.values],
            "schema_errors": list(self.schema_errors),
        }


@dataclass
class VLMTable:
    schema_shape: str
    is_table: bool
    table_title: Optional[str]
    unit: Optional[str]
    currency: Optional[str] = None
    columns: List[str] = field(default_factory=list)
    rows: List[VLMRow] = field(default_factory=list)
    table_warnings: List[str] = field(default_factory=list)
    schema_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_shape": self.schema_shape,
            "is_table": self.is_table,
            "table_title": self.table_title,
            "unit": self.unit,
            "currency": self.currency,
            "columns": list(self.columns),
            "rows": [r.to_dict() for r in self.rows],
            "table_warnings": list(self.table_warnings),
            "schema_errors": list(self.schema_errors),
        }


@dataclass
class VLMFolderRecord:
    folder_name: str
    folder_path: str
    source_files: List[Dict[str, Any]] = field(default_factory=list)
    source_json_path: Optional[str] = None
    raw_response_path: Optional[str] = None
    table_meta: Dict[str, Any] = field(default_factory=dict)
    table: Optional[VLMTable] = None
    parse_success: bool = False
    parse_error: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "folder_name": self.folder_name,
            "folder_path": self.folder_path,
            "source_files": list(self.source_files),
            "source_json_path": self.source_json_path,
            "raw_response_path": self.raw_response_path,
            "table_meta": dict(self.table_meta),
            "table": self.table.to_dict() if self.table else None,
            "parse_success": self.parse_success,
            "parse_error": self.parse_error,
            "warnings": list(self.warnings),
        }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def _read_json_file(path: Path) -> Tuple[Optional[Any], str]:
    try:
        return parse_json_like_text(_read_text(path)), ""
    except Exception as exc:
        return None, str(exc)


def _looks_like_table_payload(payload: Any) -> bool:
    if isinstance(payload, dict):
        if isinstance(payload.get("table"), dict):
            return _looks_like_table_payload(payload["table"])
        keys = set(payload.keys())
        return bool({"rows", "columns"} & keys)
    return False


def _first_present(mapping: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _detect_shape(data: Dict[str, Any], rows: List[Any]) -> str:
    if any(isinstance(row, dict) and "metric_name" in row for row in rows):
        return "B"
    if any(isinstance(row, dict) and "row_name" in row for row in rows):
        return "A"
    if any(isinstance(row, dict) and "metric_name_cn" in row for row in rows):
        return "C"
    return "UNKNOWN"


def _coerce_columns(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        text = _optional_text(item)
        if text is not None:
            out.append(text)
    return out


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _norm(value)


def _normalize_value_item(value: Any, value_index: int) -> Dict[str, Any]:
    if isinstance(value, dict):
        source_column_label = _optional_text(_first_present(value, ("column", "year", "header", "column_label")))
        raw_value = _normalize_scalar(_first_present(value, ("raw_value", "raw", "text", "value")))
        normalized_value = _normalize_scalar(_first_present(value, ("normalized_value", "normalized", "parsed_value")))
    else:
        source_column_label = None
        raw_value = _normalize_scalar(value)
        normalized_value = value if isinstance(value, (int, float)) else None
    return {
        "source_column_label": source_column_label,
        "raw_value": raw_value,
        "normalized_value": normalized_value,
        "value_index": value_index,
    }


def _build_empty_cells(columns: List[str]) -> List[VLMValueCell]:
    return [
        VLMValueCell(column=column, source_column_label=None, raw_value=None, normalized_value=None, value_index=idx)
        for idx, column in enumerate(columns)
    ]


def _normalize_row(row: Any, row_index: int, columns: List[str]) -> VLMRow:
    if not isinstance(row, dict):
        return VLMRow(
            row_index=row_index,
            source_row_index=None,
            row_name=None,
            metric_name_raw=None,
            metric_name_cn=None,
            values=_build_empty_cells(columns),
            schema_errors=["ROW_NOT_OBJECT"],
        )

    row_name = _optional_text(_first_present(row, ("row_name", "metric_name_cn", "metric_name", "metric_name_raw", "label", "name")))
    metric_name_raw = _optional_text(_first_present(row, ("metric_name_raw", "row_name", "metric_name", "label", "name")))
    metric_name_cn = _optional_text(_first_present(row, ("metric_name_cn", "row_name", "metric_name")))
    values_raw = _first_present(row, ("values", "cells", "data"))

    if not isinstance(values_raw, list):
        return VLMRow(
            row_index=row_index,
            source_row_index=None,
            row_name=row_name,
            metric_name_raw=metric_name_raw,
            metric_name_cn=metric_name_cn,
            values=_build_empty_cells(columns),
            schema_errors=["ROW_VALUES_MISSING_OR_INVALID"],
        )

    schema_errors: List[str] = []
    normalized_items = [_normalize_value_item(value, value_index=idx) for idx, value in enumerate(values_raw)]
    explicit_label_count = sum(1 for item in normalized_items if item["source_column_label"])

    if explicit_label_count == len(normalized_items) and normalized_items:
        header_map = {canonicalize_column_label(column): column for column in columns}
        cells_by_column: Dict[str, VLMValueCell] = {}
        extras: List[str] = []
        for item in normalized_items:
            source_label = _optional_text(item["source_column_label"])
            canonical = canonicalize_column_label(source_label)
            if canonical not in header_map:
                extras.append(source_label or "")
                continue
            target_column = header_map[canonical]
            if target_column in cells_by_column:
                schema_errors.append("DUPLICATE_VALUE_COLUMN_LABEL")
                continue
            cells_by_column[target_column] = VLMValueCell(
                column=target_column,
                source_column_label=source_label,
                raw_value=item["raw_value"],
                normalized_value=item["normalized_value"],
                value_index=item["value_index"],
            )
        if extras:
            schema_errors.append("UNKNOWN_VALUE_COLUMN_LABEL")
        values = [
            cells_by_column.get(
                column,
                VLMValueCell(
                    column=column,
                    source_column_label=None,
                    raw_value=None,
                    normalized_value=None,
                    value_index=idx,
                ),
            )
            for idx, column in enumerate(columns)
        ]
        missing_count = sum(1 for value in values if value.raw_value is None and value.normalized_value is None)
        if missing_count:
            schema_errors.append("ROW_MISSING_VALUES_FOR_COLUMNS")
    else:
        if 0 < explicit_label_count < len(normalized_items):
            schema_errors.append("PARTIAL_VALUE_COLUMN_LABELS")
        values = []
        for idx, column in enumerate(columns):
            item = normalized_items[idx] if idx < len(normalized_items) else None
            if item is None:
                values.append(
                    VLMValueCell(
                        column=column,
                        source_column_label=None,
                        raw_value=None,
                        normalized_value=None,
                        value_index=idx,
                    )
                )
            else:
                values.append(
                    VLMValueCell(
                        column=column,
                        source_column_label=item["source_column_label"],
                        raw_value=item["raw_value"],
                        normalized_value=item["normalized_value"],
                        value_index=item["value_index"],
                    )
                )
        if len(normalized_items) != len(columns):
            schema_errors.append("ROW_VALUE_COUNT_MISMATCH_COLUMNS")

    return VLMRow(
        row_index=row_index,
        source_row_index=(
            int(row["row_index"])
            if isinstance(row.get("row_index"), (int, float)) and not isinstance(row.get("row_index"), bool)
            else None
        ),
        row_name=row_name,
        metric_name_raw=metric_name_raw,
        metric_name_cn=metric_name_cn,
        confidence=(
            float(row["confidence"])
            if isinstance(row.get("confidence"), (int, float)) and not isinstance(row.get("confidence"), bool)
            else None
        ),
        uncertain=bool(row.get("uncertain", False)),
        warnings=[_norm(item) for item in row.get("warnings", []) if _norm(item)],
        values=values,
        schema_errors=schema_errors,
    )


def normalize_vlm_payload(payload: Any) -> VLMTable:
    if isinstance(payload, dict) and isinstance(payload.get("table"), dict):
        payload = payload["table"]

    if not isinstance(payload, dict):
        return VLMTable(
            schema_shape="UNKNOWN",
            is_table=False,
            table_title=None,
            unit=None,
            currency=None,
            columns=[],
            rows=[],
            table_warnings=[],
            schema_errors=["ROOT_JSON_NOT_OBJECT"],
        )

    rows_raw = payload.get("rows")
    columns = _coerce_columns(_first_present(payload, ("columns", "years", "header_columns")))
    schema_errors: List[str] = []

    if not columns:
        schema_errors.append("MISSING_COLUMNS")
    if not isinstance(rows_raw, list):
        schema_errors.append("MISSING_ROWS")
        rows_raw = []

    rows = [_normalize_row(row, row_index=idx, columns=columns) for idx, row in enumerate(rows_raw)]
    table = VLMTable(
        schema_shape=_detect_shape(payload, rows_raw),
        is_table=bool(payload.get("is_table", True)),
        table_title=_optional_text(_first_present(payload, ("table_title", "title"))),
        unit=_optional_text(payload.get("unit")),
        currency=_optional_text(payload.get("currency")),
        columns=columns,
        rows=rows,
        table_warnings=[_norm(item) for item in payload.get("table_warnings", []) if _norm(item)],
        schema_errors=schema_errors,
    )
    return table


def _build_source_files(folder: Path) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    for path in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file():
            continue
        files.append(
            {
                "folder_name": folder.name,
                "file_name": path.name,
                "file_path": str(path),
                "suffix": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            }
        )
    return files


def _candidate_payload_paths(folder: Path) -> Iterable[Path]:
    yielded: set[str] = set()
    for name in PREFERRED_JSON_FILES:
        path = folder / name
        if path.exists():
            yielded.add(path.name.lower())
            yield path
    for path in sorted(folder.glob("*.json"), key=lambda p: p.name.lower()):
        if path.name.lower() == TABLE_META_FILE.lower():
            continue
        if path.name.lower() not in yielded:
            yielded.add(path.name.lower())
            yield path
    for name in PREFERRED_TEXT_FILES:
        path = folder / name
        if path.exists():
            yielded.add(path.name.lower())
            yield path
    for path in sorted(folder.glob("*.txt"), key=lambda p: p.name.lower()):
        if path.name.lower() not in yielded:
            yield path


def read_vlm_output_folder(folder: Path) -> VLMFolderRecord:
    record = VLMFolderRecord(
        folder_name=folder.name,
        folder_path=str(folder),
        source_files=_build_source_files(folder),
    )

    meta_path = folder / TABLE_META_FILE
    if meta_path.exists():
        payload, error = _read_json_file(meta_path)
        if isinstance(payload, dict):
            record.table_meta = payload
        elif error:
            record.warnings.append(f"TABLE_META_PARSE_ERROR: {error}")

    raw_response_path = folder / "raw_response.txt"
    if raw_response_path.exists():
        record.raw_response_path = str(raw_response_path)

    parse_errors: List[str] = []
    for candidate in _candidate_payload_paths(folder):
        payload, error = _read_json_file(candidate)
        if payload is None:
            parse_errors.append(f"{candidate.name}: {error}")
            continue
        if not _looks_like_table_payload(payload):
            parse_errors.append(f"{candidate.name}: JSON_PARSED_BUT_NO_TABLE_SHAPE")
            continue
        record.source_json_path = str(candidate)
        record.table = normalize_vlm_payload(payload)
        record.parse_success = True
        record.parse_error = ""
        return record

    record.parse_success = False
    record.parse_error = " | ".join(parse_errors) if parse_errors else "NO_PARSEABLE_JSON_FOUND"
    return record


def scan_vlm_output_root(root: Path) -> List[VLMFolderRecord]:
    if not root.exists() or not root.is_dir():
        return []
    folders = sorted([path for path in root.iterdir() if path.is_dir()], key=lambda p: p.name.lower())
    return [read_vlm_output_folder(folder) for folder in folders]
