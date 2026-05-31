from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pandas as pd

from datefac.vlm.vlm_output_reader import VLMFolderRecord, VLMRow, VLMTable, canonicalize_column_label, is_year_like_label, scan_vlm_output_root
from datefac.vlm.vlm_prompt_templates import build_vlm_rerun_prompt_321a


SHEET_ORDER = [
    "summary",
    "table_inventory",
    "row_quality",
    "cell_quality",
    "corrupted_labels",
    "numeric_quality",
    "schema_errors",
    "rerun_worklist",
    "recommended_prompt",
    "source_files",
]

YEAR_VALUE_RE = re.compile(r"[-(]?\d[\d,\s]*(?:\.\d+)?%?[)]?")
CORE_TABLE_HINTS = ("利润表", "现金流量表", "资产负债表", "指标", "估值")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_text(value: Any) -> Optional[str]:
    text = _norm(value)
    if not text or text.lower() in {"none", "null", "nan"}:
        return None
    return text


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    cleaned = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    base = cleaned
    idx = 1
    while cleaned in used:
        suffix = f"_{idx}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used.add(cleaned)
    return cleaned


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name in SHEET_ORDER:
            df = sheets.get(sheet_name, pd.DataFrame())
            df.to_excel(writer, sheet_name=_safe_sheet_name(sheet_name, used), index=False)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _empty_df(columns: Sequence[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=list(columns))


def _coerce_number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
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


def _raw_looks_numeric(value: Any) -> bool:
    text = _norm(value)
    if not text:
        return False
    if isinstance(value, (int, float)):
        return True
    return bool(re.search(r"\d", text))


def _split_digit_issue(value: Any) -> bool:
    text = _norm(value)
    if not text:
        return False
    return bool(re.search(r"\d\s+\d", text))


def _is_unit_text_valid(text: str) -> bool:
    if not text:
        return False
    if re.search(r"[\u4e00-\u9fffA-Za-z]", text):
        return True
    return bool(re.fullmatch(r"[%¥$€£0-9.,/\-]+", text))


def _label_issue_tags(text: Optional[str], location: str) -> List[str]:
    s = _norm(text)
    tags: List[str] = []
    if location == "row" and not s:
        tags.append("EMPTY_ROW_LABEL")
    if not s:
        return tags

    has_question_mark = "?" in s or "？" in s
    has_replacement = "\ufffd" in s or "�" in s
    stripped_letters = re.sub(r"[\s\W\d_]+", "", s, flags=re.UNICODE)

    corrupted = False
    if has_question_mark or has_replacement:
        corrupted = True
    if location in {"title", "row"} and not re.search(r"[\u4e00-\u9fffA-Za-z]", s):
        corrupted = True
    if location == "unit" and not _is_unit_text_valid(s):
        corrupted = True
    if stripped_letters == "" and (has_question_mark or has_replacement):
        corrupted = True

    if corrupted:
        tags.append("CHINESE_LABEL_CORRUPTED")
        if location == "title":
            tags.append("TABLE_TITLE_CORRUPTED")
        elif location == "unit":
            tags.append("UNIT_CORRUPTED")
        elif location == "row":
            tags.append("ROW_LABEL_CORRUPTED")
    return tags


def _column_check_tags(columns: Sequence[str]) -> List[str]:
    tags: List[str] = []
    if not columns:
        tags.append("MISSING_COLUMNS")
        return tags
    invalid = [column for column in columns if not is_year_like_label(column)]
    if invalid:
        tags.append("INVALID_YEAR_COLUMNS")
    return tags


def _table_main_issue(schema_errors: List[str], corrupted_tags: List[str], numeric_issue_count: int, decision: str) -> str:
    if decision == "VLM_TABLE_EMPTY_OR_NOT_TABLE":
        return "EMPTY_OR_NOT_TABLE"
    if schema_errors:
        return schema_errors[0]
    if corrupted_tags:
        return corrupted_tags[0]
    if numeric_issue_count > 0:
        return "NUMERIC_VALIDATION_FAILED"
    return decision


def _recommended_action(decision: str, main_issue: str, table_title: str) -> str:
    if decision == "VLM_TABLE_VALUES_OK_LABELS_CORRUPTED":
        return "rerun_vlm_preserve_chinese_labels"
    if decision == "VLM_TABLE_SCHEMA_INVALID":
        return "rerun_with_strict_json_schema"
    if decision == "VLM_TABLE_NUMERIC_WEAK":
        return "manual_check_image_quality"
    if decision == "VLM_TABLE_EMPTY_OR_NOT_TABLE":
        if any(hint in table_title for hint in CORE_TABLE_HINTS):
            return "manual_check_image_quality"
        return "skip_not_core_table"
    if main_issue.startswith("MISSING_"):
        return "rerun_with_strict_json_schema"
    return "rerun_vlm_preserve_chinese_labels"


def _table_priority(table_title: str, decision: str) -> str:
    if any(hint in table_title for hint in ("利润表", "现金流量表", "资产负债表")):
        return "P1"
    if any(hint in table_title for hint in ("指标", "估值")):
        return "P2"
    if decision == "VLM_TABLE_EMPTY_OR_NOT_TABLE":
        return "P3"
    return "P2"


def _build_blocked_outputs(output_dir: Path, vlm_output_root: Path, blocked_code: str) -> Dict[str, Any]:
    summary_payload = {
        "stage": "321A",
        "blocked": True,
        "blocked_code": blocked_code,
        "vlm_output_root": str(vlm_output_root),
        "output_dir": str(output_dir),
        "vlm_folder_count": 0,
        "parsed_json_count": 0,
        "table_output_count": 0,
        "table_ready_count": 0,
        "values_ok_labels_corrupted_count": 0,
        "schema_invalid_count": 0,
        "total_row_count": 0,
        "corrupted_label_row_count": 0,
        "corrupted_label_rate": 0.0,
        "numeric_cell_count": 0,
        "numeric_parse_success_count": 0,
        "numeric_parse_success_rate": 0.0,
        "column_alignment_pass_count": 0,
        "unit_detected_count": 0,
        "table_title_detected_count": 0,
        "global_vlm_quality_decision": blocked_code,
        "top_quality_issues": [],
    }

    rerun_prompt = build_vlm_rerun_prompt_321a(summary_payload, [])
    excel_path = output_dir / "vlm_output_quality_321a.xlsx"
    summary_json_path = output_dir / "vlm_output_quality_321a_summary.json"
    report_path = output_dir / "vlm_output_quality_321a_report.md"
    prompt_path = output_dir / "vlm_rerun_prompt_321a.md"

    sheets = {
        "summary": pd.DataFrame([summary_payload]),
        "table_inventory": _empty_df(
            [
                "table_folder",
                "parse_success",
                "current_decision",
                "main_issue",
            ]
        ),
        "row_quality": _empty_df(["table_folder", "row_index", "row_name", "row_label_status"]),
        "cell_quality": _empty_df(["table_folder", "row_index", "column", "raw_value", "normalized_value"]),
        "corrupted_labels": _empty_df(["table_folder", "location_type", "issue_tag", "text"]),
        "numeric_quality": _empty_df(["table_folder", "numeric_cell_count", "numeric_parse_success_rate"]),
        "schema_errors": _empty_df(["table_folder", "schema_error"]),
        "rerun_worklist": _empty_df(
            [
                "priority",
                "table_folder",
                "image_filename",
                "source_image_path",
                "current_decision",
                "main_issue",
                "recommended_action",
            ]
        ),
        "recommended_prompt": pd.DataFrame([{"section": "prompt", "content": rerun_prompt}]),
        "source_files": _empty_df(["folder_name", "file_name", "file_path"]),
    }
    _write_excel(excel_path, sheets)
    _write_json(summary_json_path, summary_payload)
    _write_text(
        report_path,
        "\n".join(
            [
                "# 321A VLM Output Quality Gate",
                "",
                f"- decision: `{blocked_code}`",
                f"- vlm_output_root: `{vlm_output_root}`",
                "",
                "Input root is missing, so no VLM folders were scanned.",
                "",
                f"- summary_json: `{summary_json_path}`",
                f"- excel: `{excel_path}`",
                f"- rerun_prompt: `{prompt_path}`",
            ]
        )
        + "\n",
    )
    _write_text(prompt_path, rerun_prompt)
    summary_payload["excel_path"] = str(excel_path)
    summary_payload["summary_json_path"] = str(summary_json_path)
    summary_payload["report_md_path"] = str(report_path)
    summary_payload["rerun_prompt_path"] = str(prompt_path)
    return summary_payload


def _evaluate_table(record: VLMFolderRecord) -> Dict[str, Any]:
    table = record.table
    meta = record.table_meta if isinstance(record.table_meta, dict) else {}
    inventory_row: Dict[str, Any] = {
        "table_folder": record.folder_name,
        "folder_path": record.folder_path,
        "source_json_path": record.source_json_path or "",
        "image_filename": _norm(meta.get("image_filename")),
        "source_image_path": _norm(meta.get("source_image_path")),
        "parse_success": record.parse_success,
        "schema_shape": "",
        "table_title": "",
        "unit": "",
        "column_count": 0,
        "row_count": 0,
        "table_title_detected": False,
        "unit_detected": False,
        "column_years_valid": False,
        "column_alignment_ok": False,
        "numeric_cell_count": 0,
        "numeric_parse_success_count": 0,
        "numeric_parse_success_rate": 0.0,
        "numeric_completeness_rate": 0.0,
        "corrupted_label_row_count": 0,
        "corrupted_label_rate": 0.0,
        "current_decision": "VLM_TABLE_SCHEMA_INVALID",
        "main_issue": "",
        "schema_errors": _norm(record.parse_error),
        "issue_tags": "",
    }

    row_quality_rows: List[Dict[str, Any]] = []
    cell_quality_rows: List[Dict[str, Any]] = []
    corrupted_rows: List[Dict[str, Any]] = []
    numeric_rows: List[Dict[str, Any]] = []
    schema_rows: List[Dict[str, Any]] = []

    if not record.parse_success or table is None:
        schema_rows.append(
            {
                "table_folder": record.folder_name,
                "source_json_path": record.source_json_path or "",
                "schema_error": record.parse_error or "NO_PARSEABLE_JSON_FOUND",
            }
        )
        inventory_row["main_issue"] = record.parse_error or "NO_PARSEABLE_JSON_FOUND"
        inventory_row["schema_errors"] = record.parse_error or "NO_PARSEABLE_JSON_FOUND"
        return {
            "inventory": inventory_row,
            "row_quality": row_quality_rows,
            "cell_quality": cell_quality_rows,
            "corrupted_labels": corrupted_rows,
            "numeric_quality": numeric_rows,
            "schema_errors": schema_rows,
        }

    table_title = _norm(table.table_title)
    unit = _norm(table.unit)
    title_tags = _label_issue_tags(table.table_title, location="title")
    unit_tags = _label_issue_tags(table.unit, location="unit")
    columns = list(table.columns)
    column_tags = _column_check_tags(columns)
    column_alignment_ok = not column_tags
    total_cells = len(columns) * len(table.rows)
    non_empty_cell_count = 0
    numeric_cell_count = 0
    numeric_parse_success_count = 0
    corrupted_label_row_count = 0
    numeric_issue_count = 0
    table_issue_tags: List[str] = []
    table_issue_tags.extend(title_tags)
    table_issue_tags.extend(unit_tags)
    table_issue_tags.extend(column_tags)

    if title_tags:
        for tag in title_tags:
            corrupted_rows.append(
                {
                    "table_folder": record.folder_name,
                    "location_type": "table_title",
                    "row_index": None,
                    "issue_tag": tag,
                    "text": table_title,
                }
            )
    if unit_tags:
        for tag in unit_tags:
            corrupted_rows.append(
                {
                    "table_folder": record.folder_name,
                    "location_type": "unit",
                    "row_index": None,
                    "issue_tag": tag,
                    "text": unit,
                }
            )

    for schema_error in table.schema_errors:
        schema_rows.append(
            {
                "table_folder": record.folder_name,
                "source_json_path": record.source_json_path or "",
                "schema_error": schema_error,
            }
        )

    for row in table.rows:
        row_tags = _label_issue_tags(row.row_name, location="row")
        row_label_status = "OK" if not row_tags else "CORRUPTED"
        if any(tag in {"CHINESE_LABEL_CORRUPTED", "ROW_LABEL_CORRUPTED", "EMPTY_ROW_LABEL"} for tag in row_tags):
            corrupted_label_row_count += 1
        for tag in row_tags:
            corrupted_rows.append(
                {
                    "table_folder": record.folder_name,
                    "location_type": "row_label",
                    "row_index": row.row_index,
                    "issue_tag": tag,
                    "text": _norm(row.row_name),
                }
            )
        if row_tags:
            table_issue_tags.extend(row_tags)

        row_non_empty_count = 0
        row_numeric_count = 0
        row_numeric_success_count = 0
        row_alignment_ok = True
        row_numeric_issue_count = 0

        for schema_error in row.schema_errors:
            schema_rows.append(
                {
                    "table_folder": record.folder_name,
                    "source_json_path": record.source_json_path or "",
                    "schema_error": f"row[{row.row_index}]: {schema_error}",
                }
            )

        for cell in row.values:
            raw_text = _norm(cell.raw_value)
            normalized_number = _coerce_number(cell.normalized_value)
            raw_number = _coerce_number(cell.raw_value)
            expected_column = cell.column
            source_column = _norm(cell.source_column_label)
            numeric_candidate = _raw_looks_numeric(cell.raw_value) or normalized_number is not None
            numeric_parse_success = (not numeric_candidate) or normalized_number is not None
            paren_negative_expected = raw_text.startswith("(") and raw_text.endswith(")")
            paren_negative_zero = paren_negative_expected and raw_number is not None and math.isclose(raw_number, 0.0, rel_tol=1e-9, abs_tol=1e-9)
            paren_negative_ok = (not paren_negative_expected) or paren_negative_zero or (normalized_number is not None and normalized_number < 0)
            negative_sign_expected = raw_text.startswith("-")
            negative_sign_ok = (not negative_sign_expected) or (normalized_number is not None and normalized_number < 0)
            source_alignment_ok = True
            if source_column:
                source_alignment_ok = canonicalize_column_label(source_column) == canonicalize_column_label(expected_column)
            split_digit_risk = _split_digit_issue(cell.raw_value)
            normalized_matches_raw = True
            if raw_number is not None and normalized_number is not None:
                normalized_matches_raw = math.isclose(raw_number, normalized_number, rel_tol=1e-9, abs_tol=1e-9)

            if raw_text or cell.normalized_value is not None:
                non_empty_cell_count += 1
                row_non_empty_count += 1
            if numeric_candidate:
                numeric_cell_count += 1
                row_numeric_count += 1
                if normalized_number is not None:
                    numeric_parse_success_count += 1
                    row_numeric_success_count += 1
            cell_issue_tags: List[str] = []
            if numeric_candidate and not numeric_parse_success:
                cell_issue_tags.append("NORMALIZED_VALUE_NOT_NUMERIC")
            if paren_negative_expected and not paren_negative_ok:
                cell_issue_tags.append("PAREN_NEGATIVE_NOT_PRESERVED")
            if negative_sign_expected and not negative_sign_ok:
                cell_issue_tags.append("NEGATIVE_SIGN_NOT_PRESERVED")
            if split_digit_risk:
                cell_issue_tags.append("VALUE_SPLIT_SUSPECT")
            if source_column and not source_alignment_ok:
                cell_issue_tags.append("VALUE_COLUMN_MISMATCH")
            if raw_number is not None and normalized_number is not None and not normalized_matches_raw:
                cell_issue_tags.append("NORMALIZED_VALUE_MISMATCH_RAW")

            if cell_issue_tags:
                row_numeric_issue_count += len(cell_issue_tags)
                numeric_issue_count += len(cell_issue_tags)
                if "VALUE_COLUMN_MISMATCH" in cell_issue_tags:
                    row_alignment_ok = False
                    column_alignment_ok = False
                table_issue_tags.extend(cell_issue_tags)

            cell_quality_rows.append(
                {
                    "table_folder": record.folder_name,
                    "row_index": row.row_index,
                    "row_name": _norm(row.row_name),
                    "column": expected_column,
                    "source_column_label": source_column,
                    "raw_value": raw_text,
                    "normalized_value": cell.normalized_value,
                    "numeric_candidate": numeric_candidate,
                    "numeric_parse_success": numeric_parse_success,
                    "paren_negative_expected": paren_negative_expected,
                    "paren_negative_ok": paren_negative_ok,
                    "paren_negative_zero": paren_negative_zero,
                    "negative_sign_expected": negative_sign_expected,
                    "negative_sign_ok": negative_sign_ok,
                    "normalized_matches_raw": normalized_matches_raw,
                    "value_column_alignment_ok": source_alignment_ok,
                    "split_digit_risk": split_digit_risk,
                    "issue_tags": "|".join(cell_issue_tags),
                }
            )

        row_quality_rows.append(
            {
                "table_folder": record.folder_name,
                "row_index": row.row_index,
                "row_name": _norm(row.row_name),
                "metric_name_raw": _norm(row.metric_name_raw),
                "metric_name_cn": _norm(row.metric_name_cn),
                "row_label_status": row_label_status,
                "label_issue_tags": "|".join(row_tags),
                "schema_errors": "|".join(row.schema_errors),
                "value_count": len(row.values),
                "non_empty_value_count": row_non_empty_count,
                "numeric_candidate_count": row_numeric_count,
                "numeric_parse_success_count": row_numeric_success_count,
                "numeric_parse_success_rate": float(row_numeric_success_count / row_numeric_count) if row_numeric_count else 1.0,
                "column_alignment_ok": row_alignment_ok,
                "numeric_issue_count": row_numeric_issue_count,
            }
        )

    numeric_parse_success_rate = float(numeric_parse_success_count / numeric_cell_count) if numeric_cell_count else 0.0
    numeric_completeness_rate = float(non_empty_cell_count / total_cells) if total_cells else 0.0
    corrupted_label_rate = float(corrupted_label_row_count / len(table.rows)) if table.rows else 0.0

    if not table.is_table or (not table.rows and not table.columns):
        decision = "VLM_TABLE_EMPTY_OR_NOT_TABLE"
    elif table.schema_errors or any(row.schema_errors for row in table.rows) or not table.columns or not table.rows or column_tags:
        decision = "VLM_TABLE_SCHEMA_INVALID"
    elif numeric_parse_success_rate < 0.95 or numeric_issue_count > 0:
        decision = "VLM_TABLE_NUMERIC_WEAK"
    elif any(tag in {"CHINESE_LABEL_CORRUPTED", "TABLE_TITLE_CORRUPTED", "UNIT_CORRUPTED", "ROW_LABEL_CORRUPTED", "EMPTY_ROW_LABEL"} for tag in table_issue_tags):
        decision = "VLM_TABLE_VALUES_OK_LABELS_CORRUPTED"
    else:
        decision = "VLM_TABLE_READY_FOR_MAPPING"

    main_issue = _table_main_issue(table.schema_errors + [error["schema_error"] for error in schema_rows if error["table_folder"] == record.folder_name], table_issue_tags, numeric_issue_count, decision)

    inventory_row.update(
        {
            "schema_shape": table.schema_shape,
            "table_title": table_title,
            "unit": unit,
            "column_count": len(columns),
            "row_count": len(table.rows),
            "table_title_detected": bool(table_title and not title_tags),
            "unit_detected": bool(unit and not unit_tags),
            "column_years_valid": not column_tags,
            "column_alignment_ok": column_alignment_ok,
            "numeric_cell_count": numeric_cell_count,
            "numeric_parse_success_count": numeric_parse_success_count,
            "numeric_parse_success_rate": numeric_parse_success_rate,
            "numeric_completeness_rate": numeric_completeness_rate,
            "corrupted_label_row_count": corrupted_label_row_count,
            "corrupted_label_rate": corrupted_label_rate,
            "current_decision": decision,
            "main_issue": main_issue,
            "schema_errors": "|".join(table.schema_errors),
            "issue_tags": "|".join(sorted(set(table_issue_tags))),
        }
    )

    numeric_rows.append(
        {
            "table_folder": record.folder_name,
            "table_title": table_title,
            "row_count": len(table.rows),
            "column_count": len(columns),
            "expected_cell_count": total_cells,
            "non_empty_cell_count": non_empty_cell_count,
            "numeric_cell_count": numeric_cell_count,
            "numeric_parse_success_count": numeric_parse_success_count,
            "numeric_parse_success_rate": numeric_parse_success_rate,
            "numeric_completeness_rate": numeric_completeness_rate,
            "corrupted_label_row_count": corrupted_label_row_count,
            "corrupted_label_rate": corrupted_label_rate,
            "column_alignment_ok": column_alignment_ok,
            "current_decision": decision,
        }
    )

    return {
        "inventory": inventory_row,
        "row_quality": row_quality_rows,
        "cell_quality": cell_quality_rows,
        "corrupted_labels": corrupted_rows,
        "numeric_quality": numeric_rows,
        "schema_errors": schema_rows,
    }


def _global_decision(summary: Dict[str, Any], inventory_rows: List[Dict[str, Any]]) -> str:
    if summary["parsed_json_count"] == 0:
        return "VLM_OUTPUT_QUALITY_BLOCKED_NO_JSON"
    title_corrupted_count = sum(1 for row in inventory_rows if "TABLE_TITLE_CORRUPTED" in _norm(row.get("issue_tags")).split("|"))
    unit_corrupted_count = sum(1 for row in inventory_rows if "UNIT_CORRUPTED" in _norm(row.get("issue_tags")).split("|"))
    mostly_corrupted_title_or_unit = False
    if summary["table_output_count"] > 0:
        mostly_corrupted_title_or_unit = (
            title_corrupted_count > summary["table_output_count"] / 2
            or unit_corrupted_count > summary["table_output_count"] / 2
        )
    if summary["corrupted_label_rate"] > 0.05 or mostly_corrupted_title_or_unit:
        return "VLM_OUTPUT_NOT_READY_LABEL_CORRUPTION"
    if summary["numeric_parse_success_rate"] < 0.95:
        return "VLM_OUTPUT_NOT_READY_NUMERIC_WEAK"
    if (
        summary["table_ready_count"] >= 7
        and summary["numeric_parse_success_rate"] >= 0.98
        and summary["corrupted_label_rate"] <= 0.02
    ):
        return "VLM_OUTPUT_READY_FOR_321B_MAPPING_BENCHMARK"
    return "VLM_OUTPUT_PARTIAL_NEEDS_RERUN_OR_PROMPT_FIX"


def _build_report(summary: Dict[str, Any], rerun_worklist: List[Dict[str, Any]], top_issues: List[Dict[str, Any]]) -> str:
    lines = [
        "# 321A VLM Output Quality Gate",
        "",
        f"- global_vlm_quality_decision: `{summary.get('global_vlm_quality_decision', '')}`",
        f"- vlm_folder_count: `{summary.get('vlm_folder_count', 0)}`",
        f"- parsed_json_count: `{summary.get('parsed_json_count', 0)}`",
        f"- table_output_count: `{summary.get('table_output_count', 0)}`",
        f"- table_ready_count: `{summary.get('table_ready_count', 0)}`",
        f"- values_ok_labels_corrupted_count: `{summary.get('values_ok_labels_corrupted_count', 0)}`",
        f"- corrupted_label_rate: `{summary.get('corrupted_label_rate', 0.0):.4f}`",
        f"- numeric_parse_success_rate: `{summary.get('numeric_parse_success_rate', 0.0):.4f}`",
        f"- unit_detected_count: `{summary.get('unit_detected_count', 0)}`",
        f"- table_title_detected_count: `{summary.get('table_title_detected_count', 0)}`",
        "",
        "## Top Quality Issues",
    ]
    if top_issues:
        for issue in top_issues:
            lines.append(f"- `{issue['issue_tag']}`: `{issue['count']}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Rerun Worklist"])
    if rerun_worklist:
        for row in rerun_worklist[:20]:
            lines.append(
                f"- `{row.get('priority', '')}` `{row.get('table_folder', '')}` -> `{row.get('main_issue', '')}` / `{row.get('recommended_action', '')}`"
            )
    else:
        lines.append("- No rerun required.")
    return "\n".join(lines) + "\n"


def run_vlm_output_quality_gate(vlm_output_root: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    if not vlm_output_root.exists() or not vlm_output_root.is_dir():
        return _build_blocked_outputs(output_dir, vlm_output_root, "BLOCKED_MISSING_VLM_OUTPUT_ROOT")

    records = scan_vlm_output_root(vlm_output_root)
    evaluations = [_evaluate_table(record) for record in records]

    inventory_rows = [item["inventory"] for item in evaluations]
    row_quality_rows = [row for item in evaluations for row in item["row_quality"]]
    cell_quality_rows = [row for item in evaluations for row in item["cell_quality"]]
    corrupted_rows = [row for item in evaluations for row in item["corrupted_labels"]]
    numeric_rows = [row for item in evaluations for row in item["numeric_quality"]]
    schema_rows = [row for item in evaluations for row in item["schema_errors"]]
    source_file_rows = [row for record in records for row in record.source_files]

    parsed_json_count = sum(1 for record in records if record.parse_success)
    table_ready_count = sum(1 for row in inventory_rows if row["current_decision"] == "VLM_TABLE_READY_FOR_MAPPING")
    values_ok_labels_corrupted_count = sum(
        1 for row in inventory_rows if row["current_decision"] == "VLM_TABLE_VALUES_OK_LABELS_CORRUPTED"
    )
    schema_invalid_count = sum(1 for row in inventory_rows if row["current_decision"] == "VLM_TABLE_SCHEMA_INVALID")
    total_row_count = int(sum(int(row.get("row_count", 0)) for row in inventory_rows))
    corrupted_label_row_count = int(sum(int(row.get("corrupted_label_row_count", 0)) for row in inventory_rows))
    numeric_cell_count = int(sum(int(row.get("numeric_cell_count", 0)) for row in inventory_rows))
    numeric_parse_success_count = int(sum(int(row.get("numeric_parse_success_count", 0)) for row in inventory_rows))
    column_alignment_pass_count = sum(1 for row in inventory_rows if bool(row.get("column_alignment_ok", False)))
    unit_detected_count = sum(1 for row in inventory_rows if bool(row.get("unit_detected", False)))
    table_title_detected_count = sum(1 for row in inventory_rows if bool(row.get("table_title_detected", False)))

    summary_payload: Dict[str, Any] = {
        "stage": "321A",
        "blocked": False,
        "blocked_code": "",
        "vlm_output_root": str(vlm_output_root),
        "output_dir": str(output_dir),
        "vlm_folder_count": len(records),
        "parsed_json_count": parsed_json_count,
        "table_output_count": len(inventory_rows),
        "table_ready_count": table_ready_count,
        "values_ok_labels_corrupted_count": values_ok_labels_corrupted_count,
        "schema_invalid_count": schema_invalid_count,
        "total_row_count": total_row_count,
        "corrupted_label_row_count": corrupted_label_row_count,
        "corrupted_label_rate": float(corrupted_label_row_count / total_row_count) if total_row_count else 0.0,
        "numeric_cell_count": numeric_cell_count,
        "numeric_parse_success_count": numeric_parse_success_count,
        "numeric_parse_success_rate": float(numeric_parse_success_count / numeric_cell_count) if numeric_cell_count else 0.0,
        "column_alignment_pass_count": column_alignment_pass_count,
        "unit_detected_count": unit_detected_count,
        "table_title_detected_count": table_title_detected_count,
    }

    issue_counter: Counter[str] = Counter()
    for row in corrupted_rows:
        issue_counter[_norm(row.get("issue_tag"))] += 1
    for row in schema_rows:
        issue_counter[_norm(row.get("schema_error"))] += 1
    for row in cell_quality_rows:
        for tag in [tag for tag in _norm(row.get("issue_tags")).split("|") if tag]:
            issue_counter[tag] += 1

    top_issues = [{"issue_tag": issue, "count": count} for issue, count in issue_counter.most_common(10)]
    summary_payload["top_quality_issues"] = top_issues
    summary_payload["global_vlm_quality_decision"] = _global_decision(summary_payload, inventory_rows)

    rerun_worklist: List[Dict[str, Any]] = []
    for row in inventory_rows:
        decision = _norm(row.get("current_decision"))
        if decision in {"VLM_TABLE_READY_FOR_MAPPING"}:
            continue
        rerun_worklist.append(
            {
                "priority": _table_priority(_norm(row.get("table_title")), decision),
                "table_folder": row.get("table_folder", ""),
                "image_filename": row.get("image_filename", ""),
                "source_image_path": row.get("source_image_path", ""),
                "current_decision": decision,
                "main_issue": row.get("main_issue", ""),
                "recommended_action": _recommended_action(decision, _norm(row.get("main_issue")), _norm(row.get("table_title"))),
            }
        )

    rerun_prompt = build_vlm_rerun_prompt_321a(summary_payload, rerun_worklist)
    report_text = _build_report(summary_payload, rerun_worklist, top_issues)

    excel_path = output_dir / "vlm_output_quality_321a.xlsx"
    summary_json_path = output_dir / "vlm_output_quality_321a_summary.json"
    report_path = output_dir / "vlm_output_quality_321a_report.md"
    prompt_path = output_dir / "vlm_rerun_prompt_321a.md"

    sheets = {
        "summary": pd.DataFrame([summary_payload]),
        "table_inventory": pd.DataFrame(inventory_rows),
        "row_quality": pd.DataFrame(row_quality_rows),
        "cell_quality": pd.DataFrame(cell_quality_rows),
        "corrupted_labels": pd.DataFrame(corrupted_rows),
        "numeric_quality": pd.DataFrame(numeric_rows),
        "schema_errors": pd.DataFrame(schema_rows),
        "rerun_worklist": pd.DataFrame(rerun_worklist),
        "recommended_prompt": pd.DataFrame([{"section": "full_prompt", "content": rerun_prompt}]),
        "source_files": pd.DataFrame(source_file_rows),
    }
    _write_excel(excel_path, sheets)
    _write_json(summary_json_path, summary_payload)
    _write_text(report_path, report_text)
    _write_text(prompt_path, rerun_prompt)

    summary_payload["excel_path"] = str(excel_path)
    summary_payload["summary_json_path"] = str(summary_json_path)
    summary_payload["report_md_path"] = str(report_path)
    summary_payload["rerun_prompt_path"] = str(prompt_path)
    return summary_payload
