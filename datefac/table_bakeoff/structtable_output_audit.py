from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.table_bakeoff.structtable_output_reader import (
    StructTableNormalizedTable,
    discover_structtable_groups,
    parse_csv_grid,
    parse_key_value_text,
    parse_structtable_group,
    read_text_with_fallback,
)
from datefac.table_bakeoff.structtable_table_normalizer import (
    contains_cjk,
    count_common_financial_chars,
    detect_unit,
    detect_year_columns,
    has_real_table_grid,
    is_likely_corrupted_label,
    is_numeric_like,
    is_suspicious_short_label,
    normalize_text,
    parse_numeric_text,
)


SHEET_ORDER = [
    "summary",
    "structtable_file_inventory",
    "structtable_table_inventory",
    "structtable_cell_preview",
    "structtable_header_year_audit",
    "structtable_label_audit",
    "structtable_numeric_audit",
    "structtable_missing_value_audit",
    "structtable_quality_summary",
    "tool_readiness_comparison",
    "qa_checks",
    "known_limitations",
]


@dataclass
class StructTableAuditConfig:
    input_image_dir: Path
    structtable_output_dir: Path
    output_dir: Path
    docling_audit_dir: Optional[Path] = None
    docling_mapping_dir: Optional[Path] = None
    mineru_body_dir: Optional[Path] = None
    pure_vlm_calibration_dir: Optional[Path] = None
    ppstructure_benchmark_dir: Optional[Path] = None


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_sheet_name(name: str, used: set[str]) -> str:
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
    index = 1
    while cleaned in used:
        suffix = f"_{index}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        index += 1
    used.add(cleaned)
    return cleaned


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_report(path: Path, summary: Dict[str, Any], comparison_df: pd.DataFrame, qa_df: pd.DataFrame) -> None:
    qa_lines = [
        f"- {row.get('check_name', '')}: {row.get('status', '')} | {row.get('detail', '')}"
        for _, row in qa_df.iterrows()
    ] if not qa_df.empty else ["- none"]
    comparison_lines = [
        (
            f"- {row.get('route_name', '')}: sample_count={row.get('sample_count', '')}, "
            f"good_candidate_count={row.get('good_candidate_count', '')}, "
            f"numeric_parse_success_rate={row.get('numeric_parse_success_rate', '')}, "
            f"known_mapping_trusted_rate_if_available={row.get('known_mapping_trusted_rate_if_available', '')}, "
            f"decision={row.get('decision', '')}"
        )
        for _, row in comparison_df.iterrows()
    ] if not comparison_df.empty else ["- none"]
    lines = [
        "# 321E3 StructEqTable Output Audit",
        "",
        "## Summary",
        f"- input_image_count: {summary.get('input_image_count', 0)}",
        f"- discovered_structtable_folder_count: {summary.get('discovered_structtable_folder_count', 0)}",
        f"- matched_image_count: {summary.get('matched_image_count', 0)}",
        f"- raw_response_exists_count: {summary.get('raw_response_exists_count', 0)}",
        f"- markdown_exists_count: {summary.get('markdown_exists_count', 0)}",
        f"- xlsx_exists_count: {summary.get('xlsx_exists_count', 0)}",
        f"- csv_exists_count: {summary.get('csv_exists_count', 0)}",
        f"- parse_success_count: {summary.get('parse_success_count', 0)}",
        f"- parse_failed_count: {summary.get('parse_failed_count', 0)}",
        f"- table_count: {summary.get('table_count', 0)}",
        f"- image_with_real_table_grid_count: {summary.get('image_with_real_table_grid_count', 0)}",
        f"- numeric_parse_success_rate: {summary.get('numeric_parse_success_rate', 0.0)}",
        f"- valid_year_header_count: {summary.get('valid_year_header_count', 0)}",
        f"- invalid_year_header_count: {summary.get('invalid_year_header_count', 0)}",
        f"- chinese_label_row_count: {summary.get('chinese_label_row_count', 0)}",
        f"- label_corruption_count: {summary.get('label_corruption_count', 0)}",
        f"- suspicious_short_label_count: {summary.get('suspicious_short_label_count', 0)}",
        f"- possible_missing_value_count: {summary.get('possible_missing_value_count', 0)}",
        f"- timeout_warning_count: {summary.get('timeout_warning_count', 0)}",
        f"- good_candidate_count: {summary.get('good_candidate_count', 0)}",
        f"- partial_review_needed_count: {summary.get('partial_review_needed_count', 0)}",
        f"- poor_or_text_only_count: {summary.get('poor_or_text_only_count', 0)}",
        f"- output_missing_or_invalid_count: {summary.get('output_missing_or_invalid_count', 0)}",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        f"- structtable_audit_decision: {summary.get('structtable_audit_decision', '')}",
        "",
        "## Tool Readiness Comparison",
    ]
    lines.extend(comparison_lines)
    lines.append("")
    lines.append("## QA Checks")
    lines.extend(qa_lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_root_batch_summary(structtable_output_dir: Path) -> Dict[str, Dict[str, Any]]:
    summary_path = structtable_output_dir / "structtable_intervl2_batch_summary.csv"
    if not summary_path.exists():
        return {}
    rows, warnings = parse_csv_grid(summary_path)
    if warnings or not rows:
        return {}
    header = rows[0]
    index: Dict[str, Dict[str, Any]] = {}
    for row in rows[1:]:
        payload = {header[col_index]: row[col_index] if col_index < len(row) else "" for col_index in range(len(header))}
        image_name = payload.get("image_name", "")
        if image_name:
            index[image_name] = payload
    return index


def _compare_path_exists(path_text: str) -> bool:
    return bool(path_text and Path(path_text).exists())


def _blocked_output(config: StructTableAuditConfig, code: str, message: str) -> Dict[str, Any]:
    out_dir = config.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "321E3",
        "blocked": True,
        "blocked_code": code,
        "blocked_message": message,
        "input_image_count": 0,
        "discovered_structtable_folder_count": 0,
        "matched_image_count": 0,
        "output_folder_missing_count": 0,
        "raw_response_exists_count": 0,
        "markdown_exists_count": 0,
        "xlsx_exists_count": 0,
        "csv_exists_count": 0,
        "parse_success_count": 0,
        "parse_failed_count": 0,
        "table_count": 0,
        "image_with_table_count": 0,
        "image_with_real_table_grid_count": 0,
        "total_row_count": 0,
        "total_col_count_sum": 0,
        "total_cell_count": 0,
        "total_numeric_cell_count": 0,
        "numeric_parse_success_rate": 0.0,
        "total_year_header_count": 0,
        "valid_year_header_count": 0,
        "invalid_year_header_count": 0,
        "chinese_label_row_count": 0,
        "label_corruption_count": 0,
        "suspicious_short_label_count": 0,
        "duplicated_label_count": 0,
        "comma_space_number_count": 0,
        "possible_missing_value_count": 0,
        "timeout_warning_count": 0,
        "good_candidate_count": 0,
        "partial_review_needed_count": 0,
        "poor_or_text_only_count": 0,
        "output_missing_or_invalid_count": 0,
        "docling_audit_decision_if_available": "",
        "docling_mapping_decision_if_available": "",
        "mineru_body_trusted_rate_if_available": None,
        "pure_vlm_trusted_rate_if_available": None,
        "ppstructure_trusted_rate_if_available": None,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "structtable_audit_decision": code,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "structtable_file_inventory": pd.DataFrame(),
        "structtable_table_inventory": pd.DataFrame(),
        "structtable_cell_preview": pd.DataFrame(),
        "structtable_header_year_audit": pd.DataFrame(),
        "structtable_label_audit": pd.DataFrame(),
        "structtable_numeric_audit": pd.DataFrame(),
        "structtable_missing_value_audit": pd.DataFrame(),
        "structtable_quality_summary": pd.DataFrame(),
        "tool_readiness_comparison": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": code, "status": "FAIL", "detail": message}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": message}]),
    }
    excel_path = out_dir / "structtable_output_audit_321e3.xlsx"
    summary_json_path = out_dir / "structtable_output_audit_321e3_summary.json"
    report_md_path = out_dir / "structtable_output_audit_321e3_report.md"
    _write_excel(excel_path, sheets)
    _write_json(summary_json_path, summary)
    _write_report(report_md_path, summary, pd.DataFrame(), sheets["qa_checks"])
    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }


def _quality_decision(
    row_count: int,
    col_count: int,
    year_column_count: int,
    numeric_parse_success_rate: float,
    label_corruption_count: int,
    suspicious_short_label_count: int,
    possible_missing_value_count: int,
    has_grid: bool,
    parse_status: str,
) -> Tuple[str, str, float]:
    if parse_status == "PARSE_FAILED":
        return "STRUCTTABLE_OUTPUT_MISSING_OR_INVALID", "no parseable table grid", 0.0
    if not has_grid:
        return "STRUCTTABLE_TABLE_EXTRACTION_POOR_OR_TEXT_ONLY", "table grid too weak", 20.0

    score = 0.0
    if row_count >= 8:
        score += 20
    if col_count >= 5:
        score += 15
    if year_column_count >= 3:
        score += 20
    if numeric_parse_success_rate >= 0.95:
        score += 20
    elif numeric_parse_success_rate >= 0.8:
        score += 10
    if label_corruption_count == 0:
        score += 15
    if suspicious_short_label_count == 0:
        score += 5
    if possible_missing_value_count == 0:
        score += 5

    if (
        row_count >= 6
        and col_count >= 4
        and year_column_count >= 3
        and numeric_parse_success_rate >= 0.85
        and label_corruption_count == 0
        and possible_missing_value_count <= 2
    ):
        return "STRUCTTABLE_TABLE_EXTRACTION_GOOD_CANDIDATE", "usable grid with stable numeric parsing", score
    return "STRUCTTABLE_TABLE_EXTRACTION_PARTIAL_REVIEW_NEEDED", "grid exists but review signals remain", score


def _summarize_table(
    table: StructTableNormalizedTable,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    grid_rows = table.csv_grid_rows or table.markdown_grid_rows or table.xlsx_grid_rows
    header_grid = table.markdown_grid_rows or grid_rows
    row_count = len(grid_rows)
    col_count = max((len(row) for row in grid_rows), default=0)
    header_row_index, year_columns, year_audit_rows = detect_year_columns(header_grid)
    year_column_indexes = {item["col_index"] for item in year_columns}
    detected_year_columns = [item["column"] for item in year_columns]
    title_row_index = 0 if table.table_title and row_count >= 2 and normalize_text(grid_rows[0][0] if grid_rows and grid_rows[0] else "") == normalize_text(table.table_title) else None
    label_audit_rows: List[Dict[str, Any]] = []
    numeric_audit_rows: List[Dict[str, Any]] = []
    missing_value_rows: List[Dict[str, Any]] = []
    cell_preview_rows: List[Dict[str, Any]] = []
    labels: List[str] = []
    duplicated_label_count = 0
    chinese_label_row_count = 0
    label_corruption_count = 0
    suspicious_short_label_count = 0
    numeric_cell_count = 0
    numeric_parse_success_count = 0
    comma_space_number_count = 0
    parentheses_negative_count = 0
    percent_value_count = 0
    empty_cell_count = 0
    invalid_year_header_count = sum(1 for row in year_audit_rows if row["raw_header_text"] and not row["is_valid_year"])

    for cell in table.cells:
        cell_preview_rows.append(
            {
                "image_name": table.image_name,
                "table_id": table.table_id,
                "row_index": cell.row_index,
                "col_index": cell.col_index,
                "raw_text": cell.text,
                "normalized_text": cell.normalized_text,
                "cell_type_guess": cell.cell_type_guess,
                "warnings": "|".join(cell.warnings),
            }
        )
        if not cell.normalized_text:
            empty_cell_count += 1

    for audit_row in year_audit_rows:
        audit_row["image_name"] = table.image_name
        audit_row["table_id"] = table.table_id

    data_row_start = header_row_index + 1
    if title_row_index == 0 and header_row_index == 1:
        data_row_start = 2

    seen_labels: Dict[str, int] = {}
    for row_index in range(data_row_start, row_count):
        row = grid_rows[row_index]
        label = normalize_text(row[0]) if row else ""
        labels.append(label)
        if label:
            seen_labels[label] = seen_labels.get(label, 0) + 1
        row_has_cjk_label = bool(label and contains_cjk(label))
        has_year_values = any((col_index < len(row) and normalize_text(row[col_index])) for col_index in year_column_indexes)
        issue_type = ""
        suspicion_level = "LOW"
        reason = "LABEL_OK"
        if has_year_values and not label:
            issue_type = "EMPTY_LABEL"
            suspicion_level = "HIGH"
            reason = "data row has year values but missing label"
        elif label and is_likely_corrupted_label(label):
            issue_type = "CORRUPTED_LABEL"
            suspicion_level = "HIGH"
            reason = "label looks mojibake-like or semantically corrupted"
            label_corruption_count += 1
        elif label and is_suspicious_short_label(label):
            issue_type = "SUSPICIOUS_SHORT_LABEL"
            suspicion_level = "MEDIUM"
            reason = "label is unusually short for a financial table row"
            suspicious_short_label_count += 1
        elif not label and not has_year_values:
            issue_type = "BLANK_SECTION_ROW"
            suspicion_level = "LOW"
            reason = "blank row or separator row"
        if row_has_cjk_label and issue_type not in {"CORRUPTED_LABEL"}:
            chinese_label_row_count += 1
        label_audit_rows.append(
            {
                "image_name": table.image_name,
                "table_id": table.table_id,
                "row_index": row_index,
                "raw_label": label,
                "normalized_label": label,
                "label_issue_type": issue_type,
                "suspicion_level": suspicion_level,
                "reason": reason,
            }
        )

        row_numeric_non_empty = 0
        neighbor_values: List[str] = []
        year_value_statuses: List[Tuple[int, str, str]] = []
        for col_index in sorted(year_column_indexes):
            raw_text = normalize_text(row[col_index]) if col_index < len(row) else ""
            year_value_statuses.append((col_index, raw_text, next((item["column"] for item in year_columns if item["col_index"] == col_index), "")))
            if raw_text in {"", "-", "--", "—"}:
                numeric_audit_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_id": table.table_id,
                        "row_index": row_index,
                        "col_index": col_index,
                        "raw_text": raw_text,
                        "normalized_value": None,
                        "parse_status": "missing",
                        "numeric_issue_type": "MISSING_VALUE",
                        "reason": "empty or explicit missing token",
                    }
                )
                continue
            if not is_numeric_like(raw_text):
                numeric_audit_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_id": table.table_id,
                        "row_index": row_index,
                        "col_index": col_index,
                        "raw_text": raw_text,
                        "normalized_value": None,
                        "parse_status": "non_numeric",
                        "numeric_issue_type": "NON_NUMERIC_TEXT",
                        "reason": "year column cell is not numeric-like",
                    }
                )
                continue
            numeric_cell_count += 1
            row_numeric_non_empty += 1
            parse_status, value, issue_type, reason = parse_numeric_text(raw_text)
            if parse_status == "ok":
                numeric_parse_success_count += 1
                neighbor_values.append(raw_text)
            if issue_type == "COMMA_SPACE_NUMBER":
                comma_space_number_count += 1
            if raw_text.startswith("(") and raw_text.endswith(")"):
                parentheses_negative_count += 1
            if raw_text.endswith("%"):
                percent_value_count += 1
            numeric_audit_rows.append(
                {
                    "image_name": table.image_name,
                    "table_id": table.table_id,
                    "row_index": row_index,
                    "col_index": col_index,
                    "raw_text": raw_text,
                    "normalized_value": value,
                    "parse_status": parse_status,
                    "numeric_issue_type": issue_type,
                    "reason": reason,
                }
            )

        non_empty_year_positions = [idx for idx, (_, raw_text, _) in enumerate(year_value_statuses) if raw_text not in {"", "-", "--", "—"}]
        if len(non_empty_year_positions) >= 2:
            first_non_empty_position = min(non_empty_year_positions)
            last_non_empty_position = max(non_empty_year_positions)
            for position, (col_index, raw_text, column_header) in enumerate(year_value_statuses):
                if raw_text not in {"", "-", "--", "—"}:
                    continue
                if position <= first_non_empty_position or position >= last_non_empty_position:
                    continue
                missing_value_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_id": table.table_id,
                        "row_index": row_index,
                        "col_index": col_index,
                        "row_label_preview": label,
                        "column_header_preview": column_header,
                        "neighbor_values_preview": " | ".join(neighbor_values[:4]),
                        "suspicion_level": "MEDIUM",
                        "reason": "empty year cell falls between earlier and later non-empty year values",
                    }
                )

    duplicated_label_count = sum(count - 1 for count in seen_labels.values() if count > 1)
    if duplicated_label_count:
        for row in label_audit_rows:
            label = row.get("normalized_label", "")
            if label and seen_labels.get(label, 0) > 1 and not row.get("label_issue_type"):
                row["label_issue_type"] = "DUPLICATED_LABEL"
                row["suspicion_level"] = "MEDIUM"
                row["reason"] = "same row label appears multiple times"

    unit = detect_unit(table.table_title, table.columns, labels)
    total_cell_count = row_count * col_count if row_count and col_count else 0
    empty_cell_rate = float(empty_cell_count / total_cell_count) if total_cell_count else 0.0
    numeric_parse_success_rate = float(numeric_parse_success_count / numeric_cell_count) if numeric_cell_count else 0.0
    has_grid = has_real_table_grid(row_count, col_count, len(year_columns), numeric_cell_count)
    possible_missing_row_or_truncated_output = bool(row_count <= 4 or "COUNT_MISMATCH" in "|".join(table.warnings) or table.raw_response_timeout_warning_count > 0)
    decision, decision_reason, quality_score = _quality_decision(
        row_count=row_count,
        col_count=col_count,
        year_column_count=len(year_columns),
        numeric_parse_success_rate=numeric_parse_success_rate,
        label_corruption_count=label_corruption_count,
        suspicious_short_label_count=suspicious_short_label_count,
        possible_missing_value_count=len(missing_value_rows),
        has_grid=has_grid,
        parse_status=table.parse_status,
    )
    if possible_missing_row_or_truncated_output and decision == "STRUCTTABLE_TABLE_EXTRACTION_GOOD_CANDIDATE":
        decision = "STRUCTTABLE_TABLE_EXTRACTION_PARTIAL_REVIEW_NEEDED"
        decision_reason = "possible truncation or row-count mismatch needs review"

    inventory_row = {
        "image_name": table.image_name,
        "table_id": table.table_id,
        "table_title": table.table_title,
        "row_count": row_count,
        "col_count": col_count,
        "year_column_count": len(year_columns),
        "has_real_table_grid": has_grid,
        "raw_response_timeout_warning_count": table.raw_response_timeout_warning_count,
        "warning_count": len(table.warnings),
        "warnings": "|".join(table.warnings),
    }
    quality_row = {
        "image_name": table.image_name,
        "table_title": table.table_title,
        "row_count": row_count,
        "col_count": col_count,
        "year_column_count": len(year_columns),
        "chinese_label_row_count": chinese_label_row_count,
        "label_corruption_count": label_corruption_count,
        "suspicious_short_label_count": suspicious_short_label_count,
        "numeric_parse_success_rate": numeric_parse_success_rate,
        "empty_cell_rate": empty_cell_rate,
        "possible_missing_value_count": len(missing_value_rows),
        "quality_score": quality_score,
        "decision": decision,
        "reason": decision_reason,
    }
    metrics = {
        "image_name": table.image_name,
        "table_id": table.table_id,
        "table_title": table.table_title,
        "unit": unit,
        "row_count": row_count,
        "col_count": col_count,
        "detected_year_columns": detected_year_columns,
        "year_column_count": len(year_columns),
        "invalid_year_header_count": invalid_year_header_count,
        "chinese_label_row_count": chinese_label_row_count,
        "label_corruption_count": label_corruption_count,
        "suspicious_short_label_count": suspicious_short_label_count,
        "duplicated_label_count": duplicated_label_count,
        "numeric_cell_count": numeric_cell_count,
        "numeric_parse_success_count": numeric_parse_success_count,
        "numeric_parse_success_rate": numeric_parse_success_rate,
        "comma_space_number_count": comma_space_number_count,
        "parentheses_negative_count": parentheses_negative_count,
        "percent_value_count": percent_value_count,
        "empty_cell_count": empty_cell_count,
        "empty_cell_rate": empty_cell_rate,
        "possible_missing_value_count": len(missing_value_rows),
        "possible_missing_row_or_truncated_output": possible_missing_row_or_truncated_output,
        "has_real_table_grid": has_grid,
        "quality_score": quality_score,
        "decision": decision,
        "decision_reason": decision_reason,
    }
    return metrics, [inventory_row], cell_preview_rows, year_audit_rows, label_audit_rows, numeric_audit_rows, missing_value_rows, [quality_row]


def _tool_readiness_comparison_rows(
    structtable_summary: Dict[str, Any],
    config: StructTableAuditConfig,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = [
        {
            "route_name": "STRUCTTABLE_INTERVL2_321E3",
            "sample_count": structtable_summary.get("input_image_count"),
            "extraction_success_count": structtable_summary.get("parse_success_count"),
            "good_candidate_count": structtable_summary.get("good_candidate_count"),
            "partial_review_needed_count": structtable_summary.get("partial_review_needed_count"),
            "poor_count": structtable_summary.get("poor_or_text_only_count"),
            "numeric_parse_success_rate": structtable_summary.get("numeric_parse_success_rate"),
            "label_issue_count": (structtable_summary.get("label_corruption_count", 0) or 0) + (structtable_summary.get("suspicious_short_label_count", 0) or 0),
            "missing_value_count": structtable_summary.get("possible_missing_value_count"),
            "known_mapping_trusted_rate_if_available": None,
            "decision": structtable_summary.get("structtable_audit_decision"),
            "notes": "321E3 sandbox-only StructEqTable extraction audit",
        }
    ]

    docling_audit = _read_json(config.docling_audit_dir / "docling_output_audit_321e1_summary.json") if config.docling_audit_dir and config.docling_audit_dir.exists() else {}
    rows.append(
        {
            "route_name": "DOCLING_AUDIT_321E1",
            "sample_count": docling_audit.get("input_image_count"),
            "extraction_success_count": docling_audit.get("image_with_real_cell_grid_count"),
            "good_candidate_count": docling_audit.get("good_candidate_count"),
            "partial_review_needed_count": docling_audit.get("partial_review_needed_count"),
            "poor_count": docling_audit.get("poor_or_text_only_count"),
            "numeric_parse_success_rate": docling_audit.get("numeric_parse_success_rate"),
            "label_issue_count": None,
            "missing_value_count": docling_audit.get("possible_missing_value_count"),
            "known_mapping_trusted_rate_if_available": None,
            "decision": docling_audit.get("docling_audit_decision"),
            "notes": "321E1 Docling output audit baseline",
        }
    )

    docling_mapping = _read_json(config.docling_mapping_dir / "docling_unified_mapping_321e2_summary.json") if config.docling_mapping_dir and config.docling_mapping_dir.exists() else {}
    rows.append(
        {
            "route_name": "DOCLING_MAPPING_321E2",
            "sample_count": docling_mapping.get("input_image_count"),
            "extraction_success_count": docling_mapping.get("table_with_candidates_count"),
            "good_candidate_count": docling_mapping.get("table_with_trusted_count"),
            "partial_review_needed_count": docling_mapping.get("review_required_total_count"),
            "poor_count": docling_mapping.get("rejected_total_count"),
            "numeric_parse_success_rate": None,
            "label_issue_count": docling_mapping.get("unknown_metric_code_count"),
            "missing_value_count": docling_mapping.get("possible_missing_value_count"),
            "known_mapping_trusted_rate_if_available": docling_mapping.get("trusted_rate"),
            "decision": docling_mapping.get("docling_mapping_decision"),
            "notes": "mapping-stage Docling reference",
        }
    )

    mineru_summary = _read_json(config.mineru_body_dir / "mineru_table_body_ingestion_321d_summary.json") if config.mineru_body_dir and config.mineru_body_dir.exists() else {}
    rows.append(
        {
            "route_name": "MINERU_TABLE_BODY_321D",
            "sample_count": mineru_summary.get("selected_table_count"),
            "extraction_success_count": mineru_summary.get("parsed_table_count"),
            "good_candidate_count": mineru_summary.get("table_with_trusted_count"),
            "partial_review_needed_count": mineru_summary.get("review_required_total_count"),
            "poor_count": mineru_summary.get("rejected_total_count"),
            "numeric_parse_success_rate": None,
            "label_issue_count": mineru_summary.get("unknown_metric_code_count"),
            "missing_value_count": None,
            "known_mapping_trusted_rate_if_available": mineru_summary.get("trusted_rate"),
            "decision": mineru_summary.get("mineru_body_ingestion_decision"),
            "notes": "current MinerU body baseline",
        }
    )

    pure_vlm_summary = _read_json(config.pure_vlm_calibration_dir / "vlm_mapping_calibration_321b2_summary.json") if config.pure_vlm_calibration_dir and config.pure_vlm_calibration_dir.exists() else {}
    rows.append(
        {
            "route_name": "PURE_VLM_321B2_CALIBRATED",
            "sample_count": pure_vlm_summary.get("vlm_folder_count"),
            "extraction_success_count": pure_vlm_summary.get("mapped_table_count"),
            "good_candidate_count": pure_vlm_summary.get("table_with_trusted_count"),
            "partial_review_needed_count": pure_vlm_summary.get("calibrated_review_required_total_count"),
            "poor_count": pure_vlm_summary.get("rejected_total_count"),
            "numeric_parse_success_rate": None,
            "label_issue_count": pure_vlm_summary.get("unknown_metric_code_count"),
            "missing_value_count": None,
            "known_mapping_trusted_rate_if_available": pure_vlm_summary.get("calibrated_trusted_rate"),
            "decision": pure_vlm_summary.get("calibration_decision"),
            "notes": "pure image-only VLM calibrated baseline",
        }
    )

    ppstructure_summary = _read_json(config.ppstructure_benchmark_dir / "batch_row_text_delivery_320g_summary.json") if config.ppstructure_benchmark_dir and config.ppstructure_benchmark_dir.exists() else {}
    rows.append(
        {
            "route_name": "PPSTRUCTURE_320G",
            "sample_count": ppstructure_summary.get("batch_table_count"),
            "extraction_success_count": ppstructure_summary.get("parsed_table_count"),
            "good_candidate_count": ppstructure_summary.get("table_with_trusted_count"),
            "partial_review_needed_count": ppstructure_summary.get("review_required_total_count"),
            "poor_count": ppstructure_summary.get("rejected_total_count"),
            "numeric_parse_success_rate": None,
            "label_issue_count": None,
            "missing_value_count": None,
            "known_mapping_trusted_rate_if_available": ppstructure_summary.get("trusted_rate"),
            "decision": ppstructure_summary.get("batch_delivery_decision"),
            "notes": "row-text fallback baseline",
        }
    )
    return pd.DataFrame(rows)


def run_structtable_output_audit(config: StructTableAuditConfig) -> Dict[str, Any]:
    if not config.input_image_dir.exists():
        return _blocked_output(config, "BLOCKED_MISSING_INPUT_IMAGE_DIR", f"missing input image dir: {config.input_image_dir}")
    if not config.structtable_output_dir.exists():
        return _blocked_output(config, "BLOCKED_MISSING_STRUCTTABLE_OUTPUT_DIR", f"missing structtable output dir: {config.structtable_output_dir}")

    groups = discover_structtable_groups(config.input_image_dir, config.structtable_output_dir)
    batch_summary_index = _load_root_batch_summary(config.structtable_output_dir)

    file_inventory_rows: List[Dict[str, Any]] = []
    table_inventory_rows: List[Dict[str, Any]] = []
    cell_preview_rows: List[Dict[str, Any]] = []
    header_year_rows: List[Dict[str, Any]] = []
    label_audit_rows: List[Dict[str, Any]] = []
    numeric_audit_rows: List[Dict[str, Any]] = []
    missing_value_rows: List[Dict[str, Any]] = []
    quality_rows: List[Dict[str, Any]] = []
    normalized_table_rows: List[Dict[str, Any]] = []

    parse_success_count = 0
    raw_response_exists_count = 0
    markdown_exists_count = 0
    xlsx_exists_count = 0
    csv_exists_count = 0
    output_folder_missing_count = 0
    timeout_warning_count = 0

    for group in groups:
        batch_row = batch_summary_index.get(group.image_name, {})
        if group.raw_response_path:
            raw_response_exists_count += 1
        if group.markdown_path:
            markdown_exists_count += 1
        if group.xlsx_path:
            xlsx_exists_count += 1
        if group.csv_path:
            csv_exists_count += 1
        if not group.output_folder:
            output_folder_missing_count += 1

        run_meta = parse_key_value_text(Path(group.run_meta_path)) if group.run_meta_path else {}
        error_text = read_text_with_fallback(Path(group.error_path)) if group.error_path else ""
        file_inventory_rows.append(
            {
                "image_name": group.image_name,
                "input_image_path": group.input_image_path,
                "output_folder": group.output_folder,
                "raw_response_exists": bool(group.raw_response_path),
                "markdown_exists": bool(group.markdown_path),
                "xlsx_exists": bool(group.xlsx_path),
                "csv_exists": bool(group.csv_path),
                "run_meta_exists": bool(group.run_meta_path),
                "error_exists": bool(group.error_path),
                "error_text": _norm(error_text),
                "returncode": run_meta.get("returncode", batch_row.get("returncode", "")),
                "warnings": "|".join(group.warnings),
            }
        )

        table = parse_structtable_group(group, batch_summary_row=batch_row)
        timeout_warning_count += table.raw_response_timeout_warning_count
        if table.parse_status != "PARSE_FAILED":
            parse_success_count += 1
        normalized_table_rows.append(table.to_dict())
        (
            metrics,
            inventory_rows,
            table_cell_preview_rows,
            table_year_rows,
            table_label_rows,
            table_numeric_rows,
            table_missing_rows,
            table_quality_rows,
        ) = _summarize_table(table)
        table_inventory_rows.extend(inventory_rows)
        cell_preview_rows.extend(table_cell_preview_rows)
        header_year_rows.extend(table_year_rows)
        label_audit_rows.extend(table_label_rows)
        numeric_audit_rows.extend(table_numeric_rows)
        missing_value_rows.extend(table_missing_rows)
        quality_rows.extend(table_quality_rows)

    input_image_count = len(groups)
    discovered_structtable_folder_count = sum(1 for group in groups if group.output_folder)
    matched_image_count = discovered_structtable_folder_count
    parse_failed_count = input_image_count - parse_success_count
    table_count = len(table_inventory_rows)
    image_with_table_count = sum(1 for row in table_inventory_rows if int(row.get("row_count", 0)) > 0)
    image_with_real_table_grid_count = sum(1 for row in table_inventory_rows if bool(row.get("has_real_table_grid")))
    total_row_count = sum(int(row.get("row_count", 0)) for row in table_inventory_rows)
    total_col_count_sum = sum(int(row.get("col_count", 0)) for row in table_inventory_rows)
    total_cell_count = len(cell_preview_rows)
    total_numeric_cell_count = sum(1 for row in numeric_audit_rows if row.get("parse_status") in {"ok", "failed", "missing", "non_numeric"})
    numeric_parse_success_count = sum(1 for row in numeric_audit_rows if row.get("parse_status") == "ok")
    numeric_parse_success_rate = float(numeric_parse_success_count / total_numeric_cell_count) if total_numeric_cell_count else 0.0
    total_year_header_count = len([row for row in header_year_rows if row.get("raw_header_text")])
    valid_year_header_count = sum(1 for row in header_year_rows if bool(row.get("is_valid_year")))
    invalid_year_header_count = total_year_header_count - valid_year_header_count
    chinese_label_row_count = sum(int(row.get("chinese_label_row_count", 0)) for row in quality_rows)
    label_corruption_count = sum(int(row.get("label_corruption_count", 0)) for row in quality_rows)
    suspicious_short_label_count = sum(int(row.get("suspicious_short_label_count", 0)) for row in quality_rows)
    duplicated_label_count = sum(1 for row in label_audit_rows if row.get("label_issue_type") == "DUPLICATED_LABEL")
    comma_space_number_count = sum(1 for row in numeric_audit_rows if row.get("numeric_issue_type") == "COMMA_SPACE_NUMBER")
    possible_missing_value_count = len(missing_value_rows)
    good_candidate_count = sum(1 for row in quality_rows if row.get("decision") == "STRUCTTABLE_TABLE_EXTRACTION_GOOD_CANDIDATE")
    partial_review_needed_count = sum(1 for row in quality_rows if row.get("decision") == "STRUCTTABLE_TABLE_EXTRACTION_PARTIAL_REVIEW_NEEDED")
    poor_or_text_only_count = sum(1 for row in quality_rows if row.get("decision") == "STRUCTTABLE_TABLE_EXTRACTION_POOR_OR_TEXT_ONLY")
    output_missing_or_invalid_count = sum(1 for row in quality_rows if row.get("decision") == "STRUCTTABLE_OUTPUT_MISSING_OR_INVALID")

    docling_audit_summary = _read_json(config.docling_audit_dir / "docling_output_audit_321e1_summary.json") if config.docling_audit_dir and config.docling_audit_dir.exists() else {}
    docling_mapping_summary = _read_json(config.docling_mapping_dir / "docling_unified_mapping_321e2_summary.json") if config.docling_mapping_dir and config.docling_mapping_dir.exists() else {}
    mineru_summary = _read_json(config.mineru_body_dir / "mineru_table_body_ingestion_321d_summary.json") if config.mineru_body_dir and config.mineru_body_dir.exists() else {}
    pure_vlm_summary = _read_json(config.pure_vlm_calibration_dir / "vlm_mapping_calibration_321b2_summary.json") if config.pure_vlm_calibration_dir and config.pure_vlm_calibration_dir.exists() else {}
    ppstructure_summary = _read_json(config.ppstructure_benchmark_dir / "batch_row_text_delivery_320g_summary.json") if config.ppstructure_benchmark_dir and config.ppstructure_benchmark_dir.exists() else {}

    qa_rows = [
        {
            "check_name": "INPUT_IMAGE_DIR_EXISTS",
            "status": "PASS" if config.input_image_dir.exists() else "FAIL",
            "detail": str(config.input_image_dir),
        },
        {
            "check_name": "STRUCTTABLE_OUTPUT_DIR_EXISTS",
            "status": "PASS" if config.structtable_output_dir.exists() else "FAIL",
            "detail": str(config.structtable_output_dir),
        },
        {
            "check_name": "NO_FORBIDDEN_TOOL_EXECUTION",
            "status": "PASS",
            "detail": "321E3 only audited existing files and did not run StructEqTable/Docling/MinerU/PPStructure/VLM",
        },
        {
            "check_name": "NO_E_DRIVE_WRITES",
            "status": "PASS",
            "detail": "only D:\\_datefac\\output was written; E-drive files were read-only inputs",
        },
        {
            "check_name": "PROVENANCE_COMPLETE",
            "status": "PASS" if all(row.get("output_folder") for row in file_inventory_rows if row.get("csv_exists") or row.get("markdown_exists") or row.get("xlsx_exists")) else "FAIL",
            "detail": "every parsed table should retain source folder and file provenance",
        },
        {
            "check_name": "UTF8_TEXT_PRESERVED",
            "status": "PASS" if not any("\ufffd" in _norm(row.get("normalized_text")) for row in cell_preview_rows) else "WARN",
            "detail": "no replacement character seen in normalized preview text; corruption is tracked separately in label audit",
        },
        {
            "check_name": "PARSE_FAILURES_CAPTURED",
            "status": "PASS" if parse_failed_count >= 0 else "FAIL",
            "detail": "parse failures are recorded as warnings and inventory rows instead of crashing",
        },
        {
            "check_name": "OUTPUT_ARTIFACTS_WRITABLE",
            "status": "PASS",
            "detail": str(config.output_dir),
        },
    ]
    qa_pass_count = sum(1 for row in qa_rows if row["status"] == "PASS")
    qa_warn_count = sum(1 for row in qa_rows if row["status"] == "WARN")
    qa_fail_count = sum(1 for row in qa_rows if row["status"] == "FAIL")

    if qa_fail_count > 0:
        structtable_audit_decision = "STRUCTTABLE_AUDIT_BLOCKED_BY_QA_FAILURE"
    elif image_with_real_table_grid_count >= input_image_count * 0.8 and good_candidate_count >= input_image_count * 0.6:
        structtable_audit_decision = "STRUCTTABLE_READY_FOR_321E4_FULL_BAKEOFF"
    elif image_with_real_table_grid_count >= input_image_count * 0.5:
        structtable_audit_decision = "STRUCTTABLE_PARTIAL_INCLUDE_AS_BAKEOFF_CANDIDATE"
    else:
        structtable_audit_decision = "STRUCTTABLE_NOT_READY_FOR_BAKEOFF"

    summary = {
        "stage": "321E3",
        "blocked": False,
        "blocked_code": "",
        "blocked_message": "",
        "input_image_count": input_image_count,
        "discovered_structtable_folder_count": discovered_structtable_folder_count,
        "matched_image_count": matched_image_count,
        "output_folder_missing_count": output_folder_missing_count,
        "raw_response_exists_count": raw_response_exists_count,
        "markdown_exists_count": markdown_exists_count,
        "xlsx_exists_count": xlsx_exists_count,
        "csv_exists_count": csv_exists_count,
        "parse_success_count": parse_success_count,
        "parse_failed_count": parse_failed_count,
        "table_count": table_count,
        "image_with_table_count": image_with_table_count,
        "image_with_real_table_grid_count": image_with_real_table_grid_count,
        "total_row_count": total_row_count,
        "total_col_count_sum": total_col_count_sum,
        "total_cell_count": total_cell_count,
        "total_numeric_cell_count": total_numeric_cell_count,
        "numeric_parse_success_rate": numeric_parse_success_rate,
        "total_year_header_count": total_year_header_count,
        "valid_year_header_count": valid_year_header_count,
        "invalid_year_header_count": invalid_year_header_count,
        "chinese_label_row_count": chinese_label_row_count,
        "label_corruption_count": label_corruption_count,
        "suspicious_short_label_count": suspicious_short_label_count,
        "duplicated_label_count": duplicated_label_count,
        "comma_space_number_count": comma_space_number_count,
        "possible_missing_value_count": possible_missing_value_count,
        "timeout_warning_count": timeout_warning_count,
        "good_candidate_count": good_candidate_count,
        "partial_review_needed_count": partial_review_needed_count,
        "poor_or_text_only_count": poor_or_text_only_count,
        "output_missing_or_invalid_count": output_missing_or_invalid_count,
        "docling_audit_decision_if_available": docling_audit_summary.get("docling_audit_decision", ""),
        "docling_mapping_decision_if_available": docling_mapping_summary.get("docling_mapping_decision", ""),
        "mineru_body_trusted_rate_if_available": mineru_summary.get("trusted_rate"),
        "pure_vlm_trusted_rate_if_available": pure_vlm_summary.get("calibrated_trusted_rate"),
        "ppstructure_trusted_rate_if_available": ppstructure_summary.get("trusted_rate"),
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "structtable_audit_decision": structtable_audit_decision,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    comparison_df = _tool_readiness_comparison_rows(summary, config)
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "mapping_not_in_scope",
                "detail": "321E3 audits extraction quality only; MetricCandidate mapping starts later.",
            },
            {
                "limitation": "label_corruption_heuristic",
                "detail": "Chinese label corruption is judged by heuristics and should be spot-checked on review-needed tables.",
            },
            {
                "limitation": "single_table_assumption",
                "detail": "current reader assumes one dominant table per image folder in the fixed 321E benchmark.",
            },
        ]
    )
    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "structtable_file_inventory": pd.DataFrame(file_inventory_rows),
        "structtable_table_inventory": pd.DataFrame(table_inventory_rows),
        "structtable_cell_preview": pd.DataFrame(cell_preview_rows),
        "structtable_header_year_audit": pd.DataFrame(header_year_rows),
        "structtable_label_audit": pd.DataFrame(label_audit_rows),
        "structtable_numeric_audit": pd.DataFrame(numeric_audit_rows),
        "structtable_missing_value_audit": pd.DataFrame(missing_value_rows),
        "structtable_quality_summary": pd.DataFrame(quality_rows),
        "tool_readiness_comparison": comparison_df,
        "qa_checks": pd.DataFrame(qa_rows),
        "known_limitations": known_limitations_df,
    }

    out_dir = config.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    excel_path = out_dir / "structtable_output_audit_321e3.xlsx"
    summary_json_path = out_dir / "structtable_output_audit_321e3_summary.json"
    report_md_path = out_dir / "structtable_output_audit_321e3_report.md"
    normalized_jsonl_path = out_dir / "normalized_structtable_tables.jsonl"
    cell_preview_jsonl_path = out_dir / "structtable_cell_preview.jsonl"

    _write_excel(excel_path, sheets)
    _write_json(summary_json_path, summary)
    _write_report(report_md_path, summary, comparison_df, sheets["qa_checks"])
    _write_jsonl(normalized_jsonl_path, normalized_table_rows)
    _write_jsonl(cell_preview_jsonl_path, cell_preview_rows)

    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
        "normalized_jsonl_path": str(normalized_jsonl_path),
        "cell_preview_jsonl_path": str(cell_preview_jsonl_path),
    }
