from __future__ import annotations

import json
import re
from io import StringIO
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.mineru_body.mineru_table_body_reader import ExtractedTableBody


YEAR_PATTERN = re.compile(r"^(20\d{2})([AE])?$", re.IGNORECASE)
UNIT_HINTS = ("百万元", "亿元", "万元", "元", "%", "元/股", "倍")


@dataclass
class UnifiedValueCell:
    column: str
    raw_value: str
    normalized_value: Optional[float]


@dataclass
class UnifiedTableRow:
    row_index: int
    metric_name_raw: str
    metric_name_cn: str
    values: List[UnifiedValueCell]
    source_row_text: str
    warnings: List[str]


@dataclass
class UnifiedTable:
    table_id: str
    source_report_name: str
    table_asset_id: str
    table_title: str
    unit: str
    currency: Optional[str]
    columns: List[str]
    rows: List[UnifiedTableRow]
    provenance: Dict[str, Any]
    warnings: List[str]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_value(value: Any) -> Optional[float]:
    text = _norm(value)
    if not text:
        return None
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    if text.startswith("-"):
        negative = True
        text = text[1:]
    text = text.replace(",", "").replace("%", "").replace(" ", "")
    if not text:
        return None
    try:
        number = float(text)
    except Exception:
        return None
    return -number if negative else number


def _looks_like_year(value: Any) -> bool:
    return bool(YEAR_PATTERN.match(_norm(value).replace("年", "")))


def _normalize_year(value: Any) -> str:
    text = _norm(value).replace("年", "")
    match = YEAR_PATTERN.match(text)
    if not match:
        return text
    suffix = (match.group(2) or "").upper()
    if suffix:
        return f"{match.group(1)}{suffix}"
    return match.group(1)


def _detect_unit(*texts: str) -> str:
    for text in texts:
        normalized = _norm(text)
        for hint in UNIT_HINTS:
            if hint in normalized:
                return hint
    return ""


def _normalize_html_table(table_html: str) -> Tuple[pd.DataFrame, List[str]]:
    warnings: List[str] = []
    try:
        tables = pd.read_html(StringIO(table_html))
    except Exception:
        return pd.DataFrame(), ["HTML_TABLE_PARSE_FAILED"]
    if not tables:
        return pd.DataFrame(), ["HTML_TABLE_EMPTY"]
    df = tables[0].fillna("")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join([_norm(item) for item in col if _norm(item)]) for col in df.columns]
    else:
        df.columns = [_norm(col) for col in df.columns]
    if df.empty:
        warnings.append("HTML_TABLE_EMPTY")
    return df, warnings


def _header_and_title(df: pd.DataFrame, fallback_title: str) -> Tuple[str, List[str], int, List[str]]:
    warnings: List[str] = []
    if df.empty:
        return fallback_title, [], 0, ["EMPTY_DATAFRAME"]

    first_row = [_norm(item) for item in df.iloc[0].tolist()]
    second_row = [_norm(item) for item in df.iloc[1].tolist()] if len(df) > 1 else []

    title = fallback_title
    data_start = 0
    first_row_year_count = sum(1 for item in first_row[1:] if _looks_like_year(item))
    if first_row_year_count >= 2:
        title = fallback_title or _norm(first_row[0])
        return title, first_row, 1, warnings
    if sum(1 for item in first_row if item) == 1 and not any(_looks_like_year(item) for item in first_row[1:]):
        title = first_row[0] or fallback_title
        data_start = 1

    header_source = first_row if data_start == 0 else second_row
    if not header_source:
        return title, [], data_start, warnings + ["HEADER_ROW_MISSING"]

    columns = [_normalize_year(item) if _looks_like_year(item) else _norm(item) for item in header_source]
    if data_start == 1:
        data_start = 2 if len(df) > 1 else 1
    return title, columns, data_start, warnings


def _coerce_columns(columns: Sequence[str]) -> List[str]:
    out: List[str] = []
    for idx, column in enumerate(columns):
        text = _norm(column)
        if idx == 0:
            out.append(text or "metric_name")
        else:
            out.append(text)
    return out


def normalize_extracted_tables(extracted_tables: Sequence[ExtractedTableBody]) -> Tuple[List[UnifiedTable], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    unified_tables: List[UnifiedTable] = []
    normalized_rows: List[Dict[str, Any]] = []
    normalization_audit_rows: List[Dict[str, Any]] = []

    for item in extracted_tables:
        warnings = list(item.warnings)
        if not item.has_table_body or not item.raw_table_html:
            warnings.append("TABLE_NOT_PARSEABLE")
            normalization_audit_rows.append(
                {
                    "table_id": item.table_asset_id,
                    "raw_table_title": item.raw_table_title,
                    "normalized_table_title": item.table_title_final,
                    "raw_columns": "",
                    "normalized_columns": "",
                    "unit_detected": "",
                    "unit_source": "",
                    "row_count": 0,
                    "value_cell_count": 0,
                    "warnings": "|".join(sorted(set(warnings))),
                }
            )
            continue

        df, parse_warnings = _normalize_html_table(item.raw_table_html)
        warnings.extend(parse_warnings)
        title, raw_columns, data_start, header_warnings = _header_and_title(df, item.raw_table_title or item.table_title_final)
        warnings.extend(header_warnings)
        columns = _coerce_columns(raw_columns)
        if len(columns) < 2:
            warnings.append("INSUFFICIENT_COLUMNS")
            normalization_audit_rows.append(
                {
                    "table_id": item.table_asset_id,
                    "raw_table_title": item.raw_table_title,
                    "normalized_table_title": title,
                    "raw_columns": "|".join(raw_columns),
                    "normalized_columns": "|".join(columns),
                    "unit_detected": "",
                    "unit_source": "",
                    "row_count": 0,
                    "value_cell_count": 0,
                    "warnings": "|".join(sorted(set(warnings))),
                }
            )
            continue

        year_columns = [column for column in columns[1:] if _looks_like_year(column)]
        if not year_columns:
            warnings.append("NO_YEAR_COLUMNS")

        detected_unit = _detect_unit(title, item.raw_table_title, item.table_title_final, item.raw_table_text)
        unit_source = "table_title_or_text" if detected_unit else ""

        rows: List[UnifiedTableRow] = []
        value_cell_count = 0
        for df_row_index in range(data_start, len(df)):
            raw_cells = [_norm(value) for value in df.iloc[df_row_index].tolist()]
            if not any(raw_cells):
                continue
            metric_name = raw_cells[0]
            row_warnings: List[str] = []
            if not metric_name:
                row_warnings.append("ROW_LABEL_MISSING")
                metric_name = ""
            values: List[UnifiedValueCell] = []
            source_row_text = " | ".join(cell for cell in raw_cells if cell)
            for col_idx, column in enumerate(columns[1:], start=1):
                raw_value = raw_cells[col_idx] if col_idx < len(raw_cells) else ""
                normalized_value = _normalize_value(raw_value)
                values.append(
                    UnifiedValueCell(
                        column=column,
                        raw_value=raw_value,
                        normalized_value=normalized_value,
                    )
                )
                if raw_value:
                    value_cell_count += 1
            unified_row = UnifiedTableRow(
                row_index=len(rows) + 1,
                metric_name_raw=metric_name,
                metric_name_cn=metric_name,
                values=values,
                source_row_text=source_row_text,
                warnings=row_warnings,
            )
            rows.append(unified_row)
            for value_cell in values:
                normalized_rows.append(
                    {
                        "table_id": item.table_asset_id,
                        "source_report_name": item.source_report_name,
                        "table_asset_id": item.table_asset_id,
                        "table_title": title,
                        "unit": detected_unit,
                        "row_index": unified_row.row_index,
                        "raw_metric_name": metric_name,
                        "metric_name_cn": metric_name,
                        "column": value_cell.column,
                        "raw_value": value_cell.raw_value,
                        "normalized_value": value_cell.normalized_value,
                        "source_row_text": source_row_text,
                        "warnings": "|".join(unified_row.warnings),
                    }
                )

        unified_table = UnifiedTable(
            table_id=item.table_asset_id,
            source_report_name=item.source_report_name,
            table_asset_id=item.table_asset_id,
            table_title=title,
            unit=detected_unit,
            currency="CNY" if detected_unit in {"百万元", "亿元", "万元", "元", "元/股"} else None,
            columns=year_columns,
            rows=rows,
            provenance={
                **item.provenance,
                "matched_by": item.matched_by,
                "content_source_file": item.content_source_file,
                "content_item_index": item.content_item_index,
                "effective_role_category": item.effective_role_category,
                "table_title_final": item.table_title_final,
            },
            warnings=sorted(set(warnings)),
        )
        unified_tables.append(unified_table)
        normalization_audit_rows.append(
            {
                "table_id": item.table_asset_id,
                "raw_table_title": item.raw_table_title,
                "normalized_table_title": title,
                "raw_columns": "|".join(raw_columns),
                "normalized_columns": "|".join(columns),
                "unit_detected": detected_unit,
                "unit_source": unit_source,
                "row_count": len(rows),
                "value_cell_count": value_cell_count,
                "warnings": "|".join(sorted(set(warnings))),
            }
        )

    unified_tables_df = pd.DataFrame(
        [
            {
                "table_id": table.table_id,
                "source_report_name": table.source_report_name,
                "table_asset_id": table.table_asset_id,
                "table_title": table.table_title,
                "unit": table.unit,
                "currency": table.currency,
                "columns": json.dumps(table.columns, ensure_ascii=False),
                "row_count": len(table.rows),
                "warnings": "|".join(table.warnings),
                "provenance_json": json.dumps(table.provenance, ensure_ascii=False),
            }
            for table in unified_tables
        ]
    )
    normalized_rows_df = pd.DataFrame(normalized_rows)
    normalization_audit_df = pd.DataFrame(normalization_audit_rows)
    return unified_tables, unified_tables_df, normalized_rows_df, normalization_audit_df
