from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.table_bakeoff.docling_output_reader import (
    DoclingNormalizedCell,
    DoclingNormalizedTable,
    discover_docling_groups,
    parse_docling_json,
)


YEAR_PATTERN = re.compile(r"^(20\d{2})([AE])?$", re.IGNORECASE)
CODE_LIKE_PATTERN = re.compile(r"^(?:\d{6}(?:\.[A-Z]{2})?|[A-Z]{3,5}|[A-Z]{1,5}\d{1,4})$")
COMMA_SPACE_PATTERN = re.compile(r"\d,\s+\d")
UNIT_HINTS = ("百万元", "百万", "亿元", "万元", "元/股", "元", "%", "x")
ROW_METRIC_HINTS = (
    "营业收入",
    "营业成本",
    "毛利率",
    "归母净利润",
    "归属母公司净利润",
    "每股收益",
    "ROE",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "货币资金",
    "资产",
    "负债",
    "现金流",
)
NON_ROW_FIRST_COL_HINTS = {"代码", "公司", "货币", "收盘价", "市值"}
NON_ROW_TABLE_WARNING = "NON_ROW_METRIC_LAYOUT"


@dataclass
class DoclingUnifiedValueCell:
    column: str
    raw_value: str
    normalized_value: Optional[float]
    source_cells: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DoclingUnifiedTableRow:
    row_index: int
    metric_name_raw: str
    metric_name_cn: str
    values: List[DoclingUnifiedValueCell]
    source_row_text: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["values"] = [value.to_dict() for value in self.values]
        return payload


@dataclass
class DoclingUnifiedTable:
    tool: str
    recognition_source: str
    image_name: str
    table_id: str
    table_index: int
    table_title: str
    unit: str
    currency: Optional[str]
    columns: List[str]
    rows: List[DoclingUnifiedTableRow]
    provenance: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "recognition_source": self.recognition_source,
            "image_name": self.image_name,
            "table_id": self.table_id,
            "table_index": self.table_index,
            "table_title": self.table_title,
            "unit": self.unit,
            "currency": self.currency,
            "columns": list(self.columns),
            "rows": [row.to_dict() for row in self.rows],
            "provenance": self.provenance,
            "warnings": list(self.warnings),
        }


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in _norm(text))


def _normalize_text(text: Any) -> str:
    value = _norm(text).replace("\n", " ").replace("\u3000", " ")
    value = re.sub(r"\s+", " ", value).strip()
    value = value.replace("（", "(").replace("）", ")")
    return value


def _is_year(text: Any) -> bool:
    normalized = _normalize_text(text).replace("年", "")
    return bool(YEAR_PATTERN.match(normalized))


def _normalize_year(text: Any) -> str:
    normalized = _normalize_text(text).replace("年", "")
    match = YEAR_PATTERN.match(normalized)
    if not match:
        return normalized
    suffix = (match.group(2) or "").upper()
    return f"{match.group(1)}{suffix}" if suffix else match.group(1)


def _parse_numeric_value(raw_value: Any) -> Tuple[Optional[float], List[str]]:
    text = _normalize_text(raw_value)
    warnings: List[str] = []
    if not text or text in {"-", "--", "—", "–", "N/A", "n/a"}:
        return None, warnings

    negative = False
    working = text
    if working.startswith("(") and working.endswith(")"):
        negative = True
        working = working[1:-1]
    if working.startswith("-"):
        negative = True
        working = working[1:]
    if COMMA_SPACE_PATTERN.search(text):
        warnings.append("COMMA_SPACE_NUMBER_FIXED")

    is_percent = working.endswith("%")
    working = working.replace("%", "").replace(",", "").replace(" ", "")
    if not working:
        return None, warnings
    try:
        value = float(working)
    except Exception:
        warnings.append("VALUE_PARSE_FAILED")
        return None, warnings
    if negative:
        value = -value
    if is_percent:
        return value, warnings
    return value, warnings


def _cell_to_source(cell: DoclingNormalizedCell) -> Dict[str, Any]:
    return {
        "row_index": cell.row_index,
        "col_index": cell.col_index,
        "row_span": cell.row_span,
        "col_span": cell.col_span,
        "text": cell.text,
        "provenance": cell.provenance,
    }


def _build_grid(table: DoclingNormalizedTable) -> Dict[Tuple[int, int], DoclingNormalizedCell]:
    grid: Dict[Tuple[int, int], DoclingNormalizedCell] = {}
    for cell in table.cells:
        for row_index in range(cell.row_index, cell.row_index + max(1, cell.row_span)):
            for col_index in range(cell.col_index, cell.col_index + max(1, cell.col_span)):
                grid[(row_index, col_index)] = cell
    return grid


def _header_rows(table: DoclingNormalizedTable) -> List[int]:
    # Docling often marks row headers as generic headers, so prioritize true column-header provenance.
    rows = sorted(
        set(
            cell.row_index
            for cell in table.cells
            if bool(cell.provenance.get("column_header"))
        )
    )
    if rows:
        return rows
    heuristic_rows: List[int] = []
    for row_index in range(min(table.num_rows, 3)):
        row_texts = [_normalize_text(cell.text) for cell in table.cells if cell.row_index == row_index and _normalize_text(cell.text)]
        if not row_texts:
            continue
        year_hits = sum(1 for text in row_texts if _is_year(text))
        if year_hits >= 2 or any(text in NON_ROW_FIRST_COL_HINTS.union({"预测指标", "指标", "项目"}) for text in row_texts):
            heuristic_rows.append(row_index)
    return heuristic_rows or [0]


def _year_columns(table: DoclingNormalizedTable, grid: Dict[Tuple[int, int], DoclingNormalizedCell]) -> List[Dict[str, Any]]:
    header_row_ids = _header_rows(table)
    result: List[Dict[str, Any]] = []
    for col_index in sorted(set(col for (_, col) in grid.keys())):
        header_texts: List[str] = []
        valid_year = ""
        for row_index in header_row_ids:
            cell = grid.get((row_index, col_index))
            if not cell:
                continue
            text = _normalize_text(cell.text)
            if not text:
                continue
            header_texts.append(text)
            if _is_year(text):
                valid_year = _normalize_year(text)
        if valid_year:
            result.append(
                {
                    "col_index": col_index,
                    "column": valid_year,
                    "raw_header_text": " | ".join(header_texts),
                }
            )
    return result


def _detect_title(table: DoclingNormalizedTable, grid: Dict[Tuple[int, int], DoclingNormalizedCell], header_row_ids: Sequence[int]) -> str:
    if _normalize_text(table.table_title):
        return _normalize_text(table.table_title)
    zero_zero = grid.get((0, 0))
    zero_zero_text = _normalize_text(zero_zero.text) if zero_zero else ""
    zero_row_other = [
        _normalize_text(grid[(0, col_index)].text)
        for col_index in sorted(set(col for (_, col) in grid.keys()))
        if col_index != 0 and (0, col_index) in grid and _normalize_text(grid[(0, col_index)].text)
    ]
    if zero_zero_text and any(_is_year(text) for text in zero_row_other):
        if zero_zero_text not in {"预测指标", "指标", "项目"}:
            return zero_zero_text
    if not header_row_ids:
        return ""
    first_row = header_row_ids[0]
    first_cell = grid.get((first_row, 0))
    first_cell_text = _normalize_text(first_cell.text) if first_cell else ""
    other_texts = [
        _normalize_text(grid[(first_row, col_index)].text)
        for col_index in sorted(set(col for (_, col) in grid.keys()))
        if col_index != 0 and (first_row, col_index) in grid and _normalize_text(grid[(first_row, col_index)].text)
    ]
    if first_cell_text and any(_is_year(text) for text in other_texts):
        if first_cell_text not in {"预测指标", "指标", "项目"}:
            return first_cell_text
    first_row_texts = [
        _normalize_text(grid[(first_row, col_index)].text)
        for col_index in sorted(set(col for (_, col) in grid.keys()))
        if (first_row, col_index) in grid and _normalize_text(grid[(first_row, col_index)].text)
    ]
    if len(first_row_texts) == 1:
        return first_row_texts[0]
    return ""


def _detect_unit(*texts: str) -> str:
    for text in texts:
        normalized = _normalize_text(text)
        if "百万" in normalized and "百万元" not in normalized:
            return "百万元"
        for hint in UNIT_HINTS:
            if hint and hint in normalized:
                return hint
    return ""


def _detect_currency(unit: str, title: str) -> Optional[str]:
    text = f"{_normalize_text(unit)} {_normalize_text(title)}".lower()
    if any(token in text for token in ("人民币", "cny", "rmb")):
        return "CNY"
    if unit in {"百万元", "亿元", "万元", "元", "元/股"}:
        return "CNY"
    return None


def _is_code_like(text: str) -> bool:
    normalized = _normalize_text(text).upper()
    return bool(CODE_LIKE_PATTERN.match(normalized))


def _is_row_metric_layout(
    table: DoclingNormalizedTable,
    grid: Dict[Tuple[int, int], DoclingNormalizedCell],
    header_row_ids: Sequence[int],
    year_columns: Sequence[Dict[str, Any]],
) -> Tuple[bool, str]:
    if len(year_columns) < 2:
        return False, "NO_YEAR_COLUMNS"

    data_start = max(header_row_ids) + 1 if header_row_ids else 1
    first_col_header = _normalize_text(grid.get((header_row_ids[-1], 0)).text) if header_row_ids and grid.get((header_row_ids[-1], 0)) else ""
    if first_col_header in {"预测指标", "指标", "项目"}:
        return True, ""

    first_col_values: List[str] = []
    cjk_like = 0
    code_like = 0
    metric_hint_hits = 0
    for row_index in range(data_start, table.num_rows):
        cell = grid.get((row_index, 0))
        text = _normalize_text(cell.text) if cell else ""
        if not text:
            continue
        first_col_values.append(text)
        if _contains_cjk(text):
            cjk_like += 1
        if _is_code_like(text):
            code_like += 1
        if any(hint.lower() in text.lower() for hint in ROW_METRIC_HINTS):
            metric_hint_hits += 1

    if not first_col_values:
        return False, "FIRST_COLUMN_EMPTY"
    if first_col_header in NON_ROW_FIRST_COL_HINTS:
        return False, "FIRST_COLUMN_ENTITY_HEADER"
    if metric_hint_hits >= 2:
        return True, ""
    if cjk_like >= max(3, len(first_col_values) // 2) and cjk_like > code_like:
        return True, ""
    return False, "FIRST_COLUMN_NOT_METRIC_LABELS"


def _table_fingerprint(table: DoclingNormalizedTable) -> str:
    rows = [
        (
            cell.row_index,
            cell.col_index,
            cell.row_span,
            cell.col_span,
            _normalize_text(cell.text),
            bool(cell.is_header),
        )
        for cell in sorted(table.cells, key=lambda item: (item.row_index, item.col_index, item.row_span, item.col_span, _normalize_text(item.text)))
    ]
    payload = {
        "image_name": table.image_name,
        "table_title": _normalize_text(table.table_title),
        "num_rows": table.num_rows,
        "num_cols": table.num_cols,
        "rows": rows,
    }
    return hashlib.sha1(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _read_sheet_safe(path: Path, sheet_name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def load_321e1_audit_support(audit_dir: Path) -> Dict[str, Any]:
    workbook_path = audit_dir / "docling_output_audit_321e1.xlsx"
    summary_path = audit_dir / "docling_output_audit_321e1_summary.json"

    missing_df = _read_sheet_safe(workbook_path, "docling_missing_cell_audit") if workbook_path.exists() else pd.DataFrame()
    quality_df = _read_sheet_safe(workbook_path, "docling_quality_summary") if workbook_path.exists() else pd.DataFrame()
    summary = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            summary = {}

    missing_lookup: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
    if not missing_df.empty:
        for _, row in missing_df.iterrows():
            key = (_norm(row.get("image_name")), int(row.get("table_index", 0)))
            missing_lookup.setdefault(key, []).append(row.to_dict())

    quality_lookup: Dict[str, Dict[str, Any]] = {}
    if not quality_df.empty and "image_name" in quality_df.columns:
        for _, row in quality_df.iterrows():
            quality_lookup[_norm(row.get("image_name"))] = row.to_dict()

    return {
        "summary": summary,
        "missing_lookup": missing_lookup,
        "quality_lookup": quality_lookup,
        "workbook_path": str(workbook_path),
    }


def _normalize_single_docling_table(
    table: DoclingNormalizedTable,
    input_image_path: str,
    audit_support: Dict[str, Any],
) -> Tuple[DoclingUnifiedTable, Dict[str, Any], List[Dict[str, Any]], int, int]:
    grid = _build_grid(table)
    header_row_ids = _header_rows(table)
    year_columns = _year_columns(table, grid)
    table_title = _detect_title(table, grid, header_row_ids)
    texts_for_unit: List[str] = [table_title]
    for header_row in header_row_ids[:2]:
        for col_index in sorted(set(col for (_, col) in grid.keys())):
            header_cell = grid.get((header_row, col_index))
            if header_cell and _normalize_text(header_cell.text):
                texts_for_unit.append(_normalize_text(header_cell.text))
    unit = _detect_unit(*texts_for_unit)
    currency = _detect_currency(unit, table_title)

    table_warnings = sorted(set(_norm(warning) for warning in table.warnings if _norm(warning)))
    missing_entries = audit_support.get("missing_lookup", {}).get((table.image_name, table.table_index), [])
    missing_positions = {(int(_norm(item.get("row_index")) or 0), int(_norm(item.get("col_index")) or 0)) for item in missing_entries}
    if missing_positions:
        table_warnings.append("POSSIBLE_MISSING_VALUE_RISK")
    if not year_columns:
        table_warnings.append("NO_YEAR_COLUMNS")

    is_row_metric_layout, layout_reason = _is_row_metric_layout(table, grid, header_row_ids, year_columns)
    if not is_row_metric_layout:
        table_warnings.append(NON_ROW_TABLE_WARNING)
        if layout_reason:
            table_warnings.append(layout_reason)

    data_start = max(header_row_ids) + 1 if header_row_ids else 1
    rows: List[DoclingUnifiedTableRow] = []
    normalized_row_rows: List[Dict[str, Any]] = []
    comma_space_fixed_count = 0

    if is_row_metric_layout:
        for row_index in range(data_start, table.num_rows):
            row_cells = []
            for col_index in sorted(set(col for (_, col) in grid.keys())):
                cell = grid.get((row_index, col_index))
                if not cell:
                    continue
                text = _normalize_text(cell.text)
                if not text:
                    continue
                row_cells.append((col_index, cell, text))
            if not row_cells:
                continue

            row_label_cell = grid.get((row_index, 0))
            metric_name = _normalize_text(row_label_cell.text) if row_label_cell else ""
            values: List[DoclingUnifiedValueCell] = []
            row_warnings: List[str] = []
            if not metric_name:
                row_warnings.append("ROW_LABEL_MISSING")
            if row_label_cell and _is_code_like(metric_name):
                row_warnings.append("ROW_LABEL_CODE_LIKE")

            for year_column in year_columns:
                col_index = int(year_column["col_index"])
                value_cell = grid.get((row_index, col_index))
                if not value_cell or not _normalize_text(value_cell.text):
                    if (row_index, col_index) in missing_positions:
                        row_warnings.append("SUSPICIOUS_MISSING_CELL_RISK")
                    continue
                normalized_value, value_warnings = _parse_numeric_value(value_cell.text)
                if "COMMA_SPACE_NUMBER_FIXED" in value_warnings:
                    comma_space_fixed_count += 1
                values.append(
                    DoclingUnifiedValueCell(
                        column=year_column["column"],
                        raw_value=_normalize_text(value_cell.text),
                        normalized_value=normalized_value,
                        source_cells=[_cell_to_source(value_cell)],
                        warnings=sorted(set(value_warnings)),
                    )
                )
                if normalized_value is None and _normalize_text(value_cell.text):
                    row_warnings.append("VALUE_PARSE_FAILED")

            if not metric_name and not values:
                continue
            if values and any((row_index, int(year_column["col_index"])) in missing_positions for year_column in year_columns):
                row_warnings.append("SUSPICIOUS_MISSING_CELL_RISK")

            source_row_text = " | ".join(text for _, _, text in row_cells)
            unified_row = DoclingUnifiedTableRow(
                row_index=len(rows) + 1,
                metric_name_raw=metric_name,
                metric_name_cn=metric_name,
                values=values,
                source_row_text=source_row_text,
                warnings=sorted(set(row_warnings)),
            )
            rows.append(unified_row)
            normalized_row_rows.append(
                {
                    "image_name": table.image_name,
                    "table_index": table.table_index,
                    "row_index": unified_row.row_index,
                    "metric_name_raw": unified_row.metric_name_raw,
                    "metric_name_cn": unified_row.metric_name_cn,
                    "values_count": len(unified_row.values),
                    "row_warnings": "|".join(unified_row.warnings),
                }
            )

    quality_info = audit_support.get("quality_lookup", {}).get(table.image_name, {})
    quality_decision = _norm(quality_info.get("decision"))
    if quality_decision and quality_decision != "DOCLING_TABLE_EXTRACTION_GOOD_CANDIDATE":
        table_warnings.append("QUALITY_REVIEW_REQUIRED_FROM_321E1")

    fingerprint = _table_fingerprint(table)
    table_id = hashlib.sha1(f"{table.image_name}|{table.table_index}|{fingerprint}".encode("utf-8")).hexdigest()[:16]
    unified_table = DoclingUnifiedTable(
        tool="docling",
        recognition_source="DOCLING_TABLE_GRID",
        image_name=table.image_name,
        table_id=table_id,
        table_index=table.table_index,
        table_title=table_title,
        unit=unit,
        currency=currency,
        columns=[item["column"] for item in year_columns],
        rows=rows,
        provenance={
            "source_stage": "docling_unified_mapping_321e2",
            "recognition_source": "DOCLING_TABLE_GRID",
            "input_image_path": input_image_path,
            "docling_json_path": table.docling_json_path,
            "table_index": table.table_index,
            "raw_num_rows": table.num_rows,
            "raw_num_cols": table.num_cols,
            "header_rows": list(header_row_ids),
            "year_columns": list(year_columns),
            "fingerprint": fingerprint,
            "quality_decision_321e1": quality_decision,
            "possible_missing_value_count_321e1": len(missing_positions),
        },
        warnings=sorted(set(table_warnings)),
    )
    unified_table_row = {
        "image_name": unified_table.image_name,
        "table_id": unified_table.table_id,
        "table_title": unified_table.table_title,
        "unit": unified_table.unit,
        "columns": json.dumps(unified_table.columns, ensure_ascii=False),
        "row_count": len(unified_table.rows),
        "value_cell_count": int(sum(len(row.values) for row in unified_table.rows)),
        "warnings": "|".join(unified_table.warnings),
    }
    return unified_table, unified_table_row, normalized_row_rows, len(missing_positions), comma_space_fixed_count


def normalize_docling_to_unified_tables(
    audit_dir: Path,
    docling_output_dir: Path,
    input_image_dir: Path,
) -> Dict[str, Any]:
    audit_support = load_321e1_audit_support(audit_dir)
    groups, _ = discover_docling_groups(input_image_dir, docling_output_dir)

    raw_docling_table_count = 0
    deduplicated_tables: List[DoclingUnifiedTable] = []
    unified_table_rows: List[Dict[str, Any]] = []
    normalized_rows: List[Dict[str, Any]] = []
    diagnostics_rows: List[Dict[str, Any]] = []
    seen_fingerprints: set[str] = set()
    possible_missing_value_count = 0
    comma_space_fixed_count = 0

    for group in groups:
        stderr_text = Path(group.stderr_path).read_text(encoding="utf-8", errors="ignore") if group.stderr_path else ""
        returncode = None
        if group.returncode_path:
            try:
                returncode = int(float(Path(group.returncode_path).read_text(encoding="utf-8", errors="ignore").strip()))
            except Exception:
                returncode = None

        for json_path_str in group.json_paths:
            json_path = Path(json_path_str)
            parsed_tables, warnings = parse_docling_json(
                json_path=json_path,
                image_name=group.image_name,
                input_image_path=group.input_image_path,
                returncode=returncode,
                stderr_text=stderr_text,
            )
            if any(str(warning).startswith("JSON_PARSE_FAILED:") for warning in warnings):
                diagnostics_rows.append(
                    {
                        "image_name": group.image_name,
                        "table_id": "",
                        "row_index": None,
                        "raw_metric_name": "",
                        "metric_code": "",
                        "year": "",
                        "raw_value": "",
                        "normalized_value": None,
                        "issue_type": "JSON_PARSE_FAILED",
                        "recommended_action": "CHECK_SOURCE_JSON",
                        "reason": "|".join(warnings),
                    }
                )
                continue

            for parsed_table in parsed_tables:
                raw_docling_table_count += 1
                unified_table, unified_table_row, normalized_row_rows, missing_count, fixed_count = _normalize_single_docling_table(
                    table=parsed_table,
                    input_image_path=group.input_image_path,
                    audit_support=audit_support,
                )
                fingerprint = _norm(unified_table.provenance.get("fingerprint"))
                if fingerprint in seen_fingerprints:
                    diagnostics_rows.append(
                        {
                            "image_name": unified_table.image_name,
                            "table_id": unified_table.table_id,
                            "row_index": None,
                            "raw_metric_name": "",
                            "metric_code": "",
                            "year": "",
                            "raw_value": "",
                            "normalized_value": None,
                            "issue_type": "DUPLICATE_TABLE_SUPPRESSED",
                            "recommended_action": "KEEP_FIRST_INSTANCE_ONLY",
                            "reason": unified_table.provenance.get("docling_json_path", ""),
                        }
                    )
                    continue

                seen_fingerprints.add(fingerprint)
                deduplicated_tables.append(unified_table)
                unified_table_rows.append(unified_table_row)
                normalized_rows.extend(normalized_row_rows)
                possible_missing_value_count += missing_count
                comma_space_fixed_count += fixed_count
                if NON_ROW_TABLE_WARNING in unified_table.warnings:
                    diagnostics_rows.append(
                        {
                            "image_name": unified_table.image_name,
                            "table_id": unified_table.table_id,
                            "row_index": None,
                            "raw_metric_name": "",
                            "metric_code": "",
                            "year": "",
                            "raw_value": "",
                            "normalized_value": None,
                            "issue_type": NON_ROW_TABLE_WARNING,
                            "recommended_action": "KEEP_TABLE_LEVEL_REVIEW",
                            "reason": "|".join(unified_table.warnings),
                        }
                    )

    return {
        "audit_support": audit_support,
        "docling_table_count": raw_docling_table_count,
        "unified_tables": deduplicated_tables,
        "unified_tables_df": pd.DataFrame(unified_table_rows),
        "normalized_rows_df": pd.DataFrame(normalized_rows),
        "normalization_diagnostics_df": pd.DataFrame(diagnostics_rows),
        "possible_missing_value_count": possible_missing_value_count,
        "comma_space_number_fixed_count": comma_space_fixed_count,
    }


def unified_tables_to_jsonl_rows(unified_tables: Sequence[DoclingUnifiedTable]) -> pd.DataFrame:
    return pd.DataFrame([table.to_dict() for table in unified_tables])
