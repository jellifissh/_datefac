from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.table_bakeoff.structtable_output_audit import _load_root_batch_summary
from datefac.table_bakeoff.structtable_output_reader import (
    StructTableNormalizedTable,
    discover_structtable_groups,
    parse_structtable_group,
)
from datefac.table_bakeoff.structtable_table_normalizer import (
    detect_unit,
    detect_year_columns,
    is_likely_corrupted_label,
    normalize_text,
    parse_numeric_text,
    score_text_quality,
)


NON_ROW_TABLE_WARNING = "NON_ROW_METRIC_LAYOUT"
SECTION_CONTEXT_WARNING = "SECTION_CONTEXT_REQUIRED"
TABLE_SCHEMA_UNCERTAIN = "TABLE_SCHEMA_UNCERTAIN"
QUALITY_REVIEW_WARNING = "QUALITY_REVIEW_REQUIRED_FROM_321E3"
ROW_LABEL_CODE_LIKE = re.compile(r"^(?:\d{6}(?:\.[A-Z]{2})?|[A-Z]{3,5}|[A-Z]{1,5}\d{1,4})$")
GENERIC_HEADER_LABELS = {"项目", "指标", "预测指标", "会计年度"}
NON_ROW_FIRST_COL_HINTS = {"代码", "公司", "货币", "收盘价", "市值"}
TITLE_HINTS = ("资产负债表", "利润表", "现金流量表", "盈利预测", "财务指标", "预测指标")
UNIT_TEXT_VARIANTS = {
    "百万人民币": "百万元",
    "百万元人民币": "百万元",
    "百万元": "百万元",
    "百万": "百万元",
    "亿元": "亿元",
    "亿": "亿元",
    "万元": "万元",
}
MOJIBAKE_TITLE_REPAIRS = {
    "棰勬祴鎸囨爣": "预测指标",
    "璧勪骇璐熷€鸿〃": "资产负债表",
    "鍒╂鼎琛": "利润表",
    "鐜伴噾娴侀噺琛": "现金流量表",
    "鐩堝埄棰勬祴": "盈利预测",
    "璐㈠姟鎸囨爣": "财务指标",
}


@dataclass
class StructTableUnifiedValueCell:
    column: str
    raw_value: str
    normalized_value: Optional[float]
    source_cells: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructTableUnifiedTableRow:
    row_index: int
    metric_name_raw: str
    metric_name_cn: str
    values: List[StructTableUnifiedValueCell]
    source_cells: List[Dict[str, Any]] = field(default_factory=list)
    source_row_text: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["values"] = [value.to_dict() for value in self.values]
        return payload


@dataclass
class StructTableUnifiedTable:
    tool: str
    recognition_source: str
    image_name: str
    table_id: str
    table_title: str
    unit: str
    currency: Optional[str]
    table_type_guess: str
    columns: List[str]
    rows: List[StructTableUnifiedTableRow]
    provenance: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "recognition_source": self.recognition_source,
            "image_name": self.image_name,
            "table_id": self.table_id,
            "table_title": self.table_title,
            "unit": self.unit,
            "currency": self.currency,
            "table_type_guess": self.table_type_guess,
            "columns": list(self.columns),
            "rows": [row.to_dict() for row in self.rows],
            "provenance": self.provenance,
            "warnings": list(self.warnings),
        }


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _read_sheet_safe(path: Path, sheet_name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in _norm(text))


def _is_code_like(text: str) -> bool:
    return bool(ROW_LABEL_CODE_LIKE.match(_norm(text).upper()))


def _is_corrupted_title(text: str) -> bool:
    normalized = normalize_text(text)
    if not normalized:
        return False
    if any(hint in normalized for hint in TITLE_HINTS):
        return False
    if normalized in MOJIBAKE_TITLE_REPAIRS:
        return True
    return is_likely_corrupted_label(normalized) and score_text_quality(normalized) <= 0


def _infer_currency(unit: str, title: str) -> Optional[str]:
    joined = f"{normalize_text(unit)} {normalize_text(title)}".lower()
    if any(token in joined for token in ("人民币", "cny", "rmb")):
        return "CNY"
    if unit in {"百万元", "百亿", "亿元", "万元", "元", "元/股"}:
        return "CNY"
    return None


def _canonical_unit_for_mapping(unit: str) -> str:
    normalized = normalize_text(unit)
    if normalized in UNIT_TEXT_VARIANTS:
        return UNIT_TEXT_VARIANTS[normalized]
    if normalized in {"元/股", "元"}:
        return normalized
    if normalized in {"x", "X"}:
        return "x"
    return normalized


def _repair_title_text(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return ""
    for bad_text, repaired_text in MOJIBAKE_TITLE_REPAIRS.items():
        normalized = normalized.replace(bad_text, repaired_text)
    return normalized


def _extract_unit_hint(*texts: str) -> str:
    for text in texts:
        normalized = _repair_title_text(text)
        for variant, canonical in UNIT_TEXT_VARIANTS.items():
            if variant and variant in normalized:
                return canonical
    return ""


def _derive_title_candidate_from_rows(table: StructTableNormalizedTable, grid_rows: Sequence[Sequence[str]]) -> str:
    markdown_rows = table.markdown_grid_rows or []
    if len(markdown_rows) >= 2:
        first_row = [_repair_title_text(value) for value in markdown_rows[0]]
        second_row = [_repair_title_text(value) for value in markdown_rows[1]]
        first_non_empty = [value for value in first_row if value]
        if len(first_non_empty) == 1 and sum(1 for value in second_row if re.match(r"^20\d{2}", value.replace(" ", ""))) >= 2:
            candidate = first_non_empty[0]
            if not _is_corrupted_title(candidate):
                return candidate
    if grid_rows:
        first_cell = _repair_title_text(grid_rows[0][0]) if grid_rows[0] else ""
        if first_cell and first_cell not in GENERIC_HEADER_LABELS and any(hint in first_cell for hint in TITLE_HINTS):
            return first_cell
    return ""


def _is_section_header_row(row: Sequence[str], year_column_indexes: Sequence[int]) -> bool:
    label = normalize_text(row[0]) if row else ""
    if not label:
        return False
    year_values = [normalize_text(row[col_index]) if col_index < len(row) else "" for col_index in year_column_indexes]
    return bool(year_values) and not any(year_values)


def _table_type_guess(
    title: str,
    header_row: Sequence[str],
    row_labels: Sequence[str],
    year_columns: Sequence[Dict[str, Any]],
) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    normalized_title = normalize_text(title)
    header_values = [normalize_text(value) for value in header_row]
    first_non_empty_header = next((value for value in header_values if value), "")
    code_like_rows = sum(1 for label in row_labels if _is_code_like(label))
    cjk_rows = sum(1 for label in row_labels if _contains_cjk(label))

    if first_non_empty_header in NON_ROW_FIRST_COL_HINTS or code_like_rows >= 2:
        warnings.append(NON_ROW_TABLE_WARNING)
        return "peer_comparison_table", warnings
    if any("资产负债表" in normalized_title for _ in [0]):
        return "balance_sheet", warnings
    if "现金流量表" in normalized_title:
        return "cash_flow_table", warnings
    if "利润表" in normalized_title:
        return "income_statement", warnings
    if "预测指标" in normalized_title or "财务指标" in normalized_title or "盈利预测" in normalized_title:
        return "forecast_indicator_table", warnings
    if len(year_columns) >= 3 and cjk_rows >= 3:
        return "year_metric_table", warnings
    warnings.append(TABLE_SCHEMA_UNCERTAIN)
    return "uncertain_metric_table", warnings


def _select_title(table: StructTableNormalizedTable, grid_rows: Sequence[Sequence[str]]) -> str:
    normalized_title = _repair_title_text(table.table_title)
    row_derived_title = _derive_title_candidate_from_rows(table, grid_rows)
    if row_derived_title and (
        not normalized_title
        or _is_corrupted_title(table.table_title)
        or (not any(hint in normalized_title for hint in TITLE_HINTS) and any(hint in row_derived_title for hint in TITLE_HINTS))
    ):
        return row_derived_title
    if normalized_title and not _is_corrupted_title(normalized_title):
        return normalized_title
    return row_derived_title


def _table_fingerprint(table: StructTableNormalizedTable, grid_rows: Sequence[Sequence[str]]) -> str:
    payload = {
        "image_name": table.image_name,
        "table_title": _select_title(table, grid_rows),
        "rows": [[normalize_text(cell) for cell in row] for row in grid_rows],
    }
    return hashlib.sha1(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _row_label_issue_lookup(label_audit_df: pd.DataFrame) -> Dict[Tuple[str, int], List[str]]:
    lookup: Dict[Tuple[str, int], List[str]] = {}
    if label_audit_df.empty:
        return lookup
    for _, row in label_audit_df.iterrows():
        issue = _norm(row.get("label_issue_type"))
        if not issue:
            continue
        key = (_norm(row.get("image_name")), int(row.get("row_index", 0)))
        lookup.setdefault(key, []).append(issue)
    return lookup


def load_321e3_audit_support(audit_dir: Path) -> Dict[str, Any]:
    workbook_path = audit_dir / "structtable_output_audit_321e3.xlsx"
    summary_path = audit_dir / "structtable_output_audit_321e3_summary.json"

    quality_df = _read_sheet_safe(workbook_path, "structtable_quality_summary") if workbook_path.exists() else pd.DataFrame()
    label_audit_df = _read_sheet_safe(workbook_path, "structtable_label_audit") if workbook_path.exists() else pd.DataFrame()
    summary = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            summary = {}

    quality_lookup: Dict[str, Dict[str, Any]] = {}
    if not quality_df.empty:
        for _, row in quality_df.iterrows():
            quality_lookup[_norm(row.get("image_name"))] = row.to_dict()

    return {
        "summary": summary,
        "quality_lookup": quality_lookup,
        "label_issue_lookup": _row_label_issue_lookup(label_audit_df),
        "workbook_path": str(workbook_path),
    }


def _normalize_single_structtable(
    table: StructTableNormalizedTable,
    audit_support: Dict[str, Any],
) -> Tuple[StructTableUnifiedTable, Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], int, int]:
    grid_rows = table.csv_grid_rows or table.markdown_grid_rows or table.xlsx_grid_rows
    header_grid = table.markdown_grid_rows or grid_rows
    title = _select_title(table, grid_rows)
    header_row_index, year_columns, year_audit_rows = detect_year_columns(header_grid)
    year_column_indexes = [int(item["col_index"]) for item in year_columns]
    header_row = header_grid[header_row_index] if header_grid and header_row_index < len(header_grid) else []
    data_start = header_row_index + 1
    row_labels = [normalize_text(row[0]) for row in grid_rows[data_start:] if row]
    table_type_guess, type_warnings = _table_type_guess(title, header_row, row_labels, year_columns)
    warnings = list(type_warnings)
    if not year_columns:
        warnings.append("NO_YEAR_COLUMNS")
    if table.parse_status == "PARSE_FAILED":
        warnings.append("PARSE_FAILED")
    if table.raw_response_timeout_warning_count > 0:
        warnings.append("TIMEOUT_WARNING_PRESENT")

    quality_info = audit_support.get("quality_lookup", {}).get(table.image_name, {})
    quality_decision = _norm(quality_info.get("decision"))
    if quality_decision and quality_decision != "STRUCTTABLE_TABLE_EXTRACTION_GOOD_CANDIDATE":
        warnings.append(QUALITY_REVIEW_WARNING)

    label_issue_lookup = audit_support.get("label_issue_lookup", {})
    rows: List[StructTableUnifiedTableRow] = []
    normalized_row_rows: List[Dict[str, Any]] = []
    diagnostics_rows: List[Dict[str, Any]] = []
    comma_space_fixed_count = 0
    possible_missing_value_count = 0
    current_section = ""
    seen_metric_names: Dict[str, int] = {}

    if NON_ROW_TABLE_WARNING not in warnings:
        for source_row_index in range(data_start, len(grid_rows)):
            row = grid_rows[source_row_index]
            label = normalize_text(row[0]) if row else ""
            if _is_section_header_row(row, year_column_indexes):
                current_section = label
                diagnostics_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_id": table.table_id,
                        "row_index": source_row_index,
                        "raw_metric_name": label,
                        "metric_code": "",
                        "year": "",
                        "raw_value": "",
                        "normalized_value": None,
                        "issue_type": "SECTION_HEADER_ROW",
                        "recommended_action": "KEEP_CONTEXT_ONLY",
                        "reason": label,
                    }
                )
                continue

            row_warnings: List[str] = []
            row_warnings.extend(label_issue_lookup.get((table.image_name, source_row_index), []))
            if not label:
                row_warnings.append("ROW_LABEL_MISSING")
            if label and _is_code_like(label):
                row_warnings.append("ROW_LABEL_CODE_LIKE")

            values: List[StructTableUnifiedValueCell] = []
            source_cells: List[Dict[str, Any]] = []
            year_values_status: List[Tuple[int, str]] = []
            for year_column in year_columns:
                col_index = int(year_column["col_index"])
                raw_text = normalize_text(row[col_index]) if col_index < len(row) else ""
                year_values_status.append((col_index, raw_text))
                if raw_text in {"", "-", "--", "—"}:
                    continue
                parse_status, normalized_value, issue_type, _ = parse_numeric_text(raw_text)
                value_warnings: List[str] = []
                if issue_type == "COMMA_SPACE_NUMBER":
                    value_warnings.append("COMMA_SPACE_NUMBER_FIXED")
                    comma_space_fixed_count += 1
                if parse_status == "failed":
                    value_warnings.append("VALUE_PARSE_FAILED")
                values.append(
                    StructTableUnifiedValueCell(
                        column=_norm(year_column["column"]),
                        raw_value=raw_text,
                        normalized_value=normalized_value,
                        source_cells=[
                            {
                                "row_index": source_row_index,
                                "col_index": col_index,
                                "text": raw_text,
                            }
                        ],
                        warnings=sorted(set(value_warnings)),
                    )
                )
                source_cells.extend(
                    [
                        {
                            "row_index": source_row_index,
                            "col_index": col_index,
                            "text": raw_text,
                        }
                    ]
                )

            if current_section and label and seen_metric_names.get(label, 0) >= 1:
                row_warnings.append(SECTION_CONTEXT_WARNING)

            non_empty_positions = [idx for idx, (_, value) in enumerate(year_values_status) if value not in {"", "-", "--", "—"}]
            if len(non_empty_positions) >= 2:
                first_non_empty = min(non_empty_positions)
                last_non_empty = max(non_empty_positions)
                for position, (_, value) in enumerate(year_values_status):
                    if value in {"", "-", "--", "—"} and first_non_empty < position < last_non_empty:
                        row_warnings.append("POSSIBLE_MISSING_VALUE_RISK")
                        possible_missing_value_count += 1
                        break

            if not label and not values:
                continue

            metric_name_raw = label
            metric_name_cn = label
            if current_section and label:
                seen_metric_names[label] = seen_metric_names.get(label, 0) + 1
            section_prefix = f"[{current_section}] " if current_section else ""
            source_row_text = section_prefix + " | ".join(normalize_text(value) for value in row if normalize_text(value))
            unified_row = StructTableUnifiedTableRow(
                row_index=len(rows) + 1,
                metric_name_raw=metric_name_raw,
                metric_name_cn=metric_name_cn,
                values=values,
                source_cells=source_cells,
                source_row_text=source_row_text,
                warnings=sorted(set(tag for tag in row_warnings if _norm(tag))),
            )
            rows.append(unified_row)
            normalized_row_rows.append(
                {
                    "image_name": table.image_name,
                    "table_id": table.table_id,
                    "row_index": unified_row.row_index,
                    "metric_name_raw": unified_row.metric_name_raw,
                    "metric_name_cn": unified_row.metric_name_cn,
                    "values_count": len(unified_row.values),
                    "row_warnings": "|".join(unified_row.warnings),
                }
            )

            if not values:
                diagnostics_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_id": table.table_id,
                        "row_index": unified_row.row_index,
                        "raw_metric_name": metric_name_raw,
                        "metric_code": "",
                        "year": "",
                        "raw_value": "",
                        "normalized_value": None,
                        "issue_type": "ROW_HAS_NO_VALUES",
                        "recommended_action": "KEEP_REVIEW",
                        "reason": source_row_text,
                    }
                )
    else:
        diagnostics_rows.append(
            {
                "image_name": table.image_name,
                "table_id": table.table_id,
                "row_index": None,
                "raw_metric_name": "",
                "metric_code": "",
                "year": "",
                "raw_value": "",
                "normalized_value": None,
                "issue_type": NON_ROW_TABLE_WARNING,
                "recommended_action": "KEEP_TABLE_LEVEL_REVIEW",
                "reason": "|".join(warnings),
            }
        )

    if any(count > 1 for count in seen_metric_names.values()):
        warnings.append(SECTION_CONTEXT_WARNING)

    detected_unit = detect_unit(title, [_norm(item["column"]) for item in year_columns], [row.metric_name_raw for row in rows])
    if not detected_unit:
        detected_unit = _extract_unit_hint(title, *[_norm(item["column"]) for item in year_columns], *[row.metric_name_raw for row in rows[:10]])
    unit = _canonical_unit_for_mapping(detected_unit)
    currency = _infer_currency(unit, title)
    fingerprint = _table_fingerprint(table, grid_rows)
    table_id = hashlib.sha1(f"{table.image_name}|{fingerprint}".encode("utf-8")).hexdigest()[:16]
    provenance = {
        "source_stage": "structtable_unified_mapping_321e4",
        "recognition_source": "STRUCTTABLE_MARKDOWN",
        "input_image_path": table.input_image_path,
        "output_folder": table.provenance.get("output_folder", ""),
        "raw_response_path": table.provenance.get("raw_response_path", ""),
        "markdown_path": table.provenance.get("markdown_path", ""),
        "csv_path": table.provenance.get("csv_path", ""),
        "xlsx_path": table.provenance.get("xlsx_path", ""),
        "run_meta_path": table.provenance.get("run_meta_path", ""),
        "source_format": table.provenance.get("source_format", ""),
        "quality_decision_321e3": quality_decision,
        "header_row_index": header_row_index,
        "year_columns": year_columns,
        "fingerprint": fingerprint,
    }

    unified_table = StructTableUnifiedTable(
        tool="structtable_intervl2",
        recognition_source="STRUCTTABLE_MARKDOWN",
        image_name=table.image_name,
        table_id=table_id,
        table_title=title,
        unit=unit,
        currency=currency,
        table_type_guess=table_type_guess,
        columns=[_norm(item["column"]) for item in year_columns],
        rows=rows,
        provenance=provenance,
        warnings=sorted(set(tag for tag in warnings if _norm(tag))),
    )
    unified_table_row = {
        "image_name": unified_table.image_name,
        "table_id": unified_table.table_id,
        "table_title": unified_table.table_title,
        "unit": unified_table.unit,
        "table_type_guess": unified_table.table_type_guess,
        "columns": _safe_json(unified_table.columns),
        "row_count": len(unified_table.rows),
        "value_cell_count": int(sum(len(row.values) for row in unified_table.rows)),
        "warnings": "|".join(unified_table.warnings),
    }
    return unified_table, unified_table_row, normalized_row_rows, diagnostics_rows, possible_missing_value_count, comma_space_fixed_count


def _is_likely_section_context(section_label: str) -> bool:
    return bool(section_label)


def normalize_structtable_to_unified_tables(
    audit_dir: Path,
    structtable_output_dir: Path,
    input_image_dir: Path,
) -> Dict[str, Any]:
    audit_support = load_321e3_audit_support(audit_dir)
    groups = discover_structtable_groups(input_image_dir, structtable_output_dir)
    batch_summary_index = _load_root_batch_summary(structtable_output_dir)

    unified_tables: List[StructTableUnifiedTable] = []
    unified_table_rows: List[Dict[str, Any]] = []
    normalized_rows: List[Dict[str, Any]] = []
    diagnostics_rows: List[Dict[str, Any]] = []
    possible_missing_value_count = 0
    comma_space_fixed_count = 0

    for group in groups:
        table = parse_structtable_group(group, batch_summary_row=batch_summary_index.get(group.image_name, {}))
        unified_table, unified_table_row, normalized_row_rows, table_diagnostics_rows, missing_count, fixed_count = _normalize_single_structtable(
            table=table,
            audit_support=audit_support,
        )
        unified_tables.append(unified_table)
        unified_table_rows.append(unified_table_row)
        normalized_rows.extend(normalized_row_rows)
        diagnostics_rows.extend(table_diagnostics_rows)
        possible_missing_value_count += missing_count
        comma_space_fixed_count += fixed_count

    return {
        "audit_support": audit_support,
        "structtable_table_count": len(groups),
        "unified_tables": unified_tables,
        "unified_tables_df": pd.DataFrame(unified_table_rows),
        "normalized_rows_df": pd.DataFrame(normalized_rows),
        "normalization_diagnostics_df": pd.DataFrame(diagnostics_rows),
        "possible_missing_value_count": possible_missing_value_count,
        "comma_space_number_fixed_count": comma_space_fixed_count,
    }


def unified_tables_to_jsonl_rows(unified_tables: Sequence[StructTableUnifiedTable]) -> pd.DataFrame:
    return pd.DataFrame([table.to_dict() for table in unified_tables])
