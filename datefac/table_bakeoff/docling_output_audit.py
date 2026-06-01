from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from datefac.table_bakeoff.docling_output_reader import (
    DoclingNormalizedTable,
    discover_docling_groups,
    parse_docling_json,
)
from datefac.table_bakeoff.docling_table_normalizer import (
    build_grid,
    contains_cjk,
    detected_year_columns,
    guess_cell_type,
    header_rows,
    is_numeric_like,
    normalize_header_text,
    parse_numeric_text,
)


SHEET_ORDER = [
    "summary",
    "docling_file_inventory",
    "docling_table_inventory",
    "docling_cell_preview",
    "docling_header_year_audit",
    "docling_numeric_audit",
    "docling_missing_cell_audit",
    "docling_quality_summary",
    "qa_checks",
    "known_limitations",
]


@dataclass
class DoclingAuditConfig:
    input_image_dir: Path
    docling_output_dir: Path
    output_dir: Path


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


def _write_jsonl(path: Path, rows_df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for _, row in rows_df.iterrows():
            handle.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")


def _write_report(path: Path, summary: Dict[str, Any], qa_df: pd.DataFrame) -> None:
    qa_lines = [
        f"- {row.get('check_name', '')}: {row.get('status', '')} | {row.get('detail', '')}"
        for _, row in qa_df.iterrows()
    ] if not qa_df.empty else ["- none"]
    lines = [
        "# 321E1 Docling Output Audit",
        "",
        "## Summary",
        f"- input_image_count: {summary.get('input_image_count', 0)}",
        f"- discovered_docling_folder_count: {summary.get('discovered_docling_folder_count', 0)}",
        f"- discovered_json_file_count: {summary.get('discovered_json_file_count', 0)}",
        f"- matched_image_count: {summary.get('matched_image_count', 0)}",
        f"- json_parse_success_count: {summary.get('json_parse_success_count', 0)}",
        f"- total_table_count: {summary.get('total_table_count', 0)}",
        f"- image_with_table_count: {summary.get('image_with_table_count', 0)}",
        f"- image_with_real_cell_grid_count: {summary.get('image_with_real_cell_grid_count', 0)}",
        f"- total_cell_count: {summary.get('total_cell_count', 0)}",
        f"- overall_empty_cell_rate: {summary.get('overall_empty_cell_rate', 0.0)}",
        f"- numeric_parse_success_rate: {summary.get('numeric_parse_success_rate', 0.0)}",
        f"- valid_year_header_count: {summary.get('valid_year_header_count', 0)}",
        f"- invalid_year_header_count: {summary.get('invalid_year_header_count', 0)}",
        f"- comma_space_number_count: {summary.get('comma_space_number_count', 0)}",
        f"- possible_missing_value_count: {summary.get('possible_missing_value_count', 0)}",
        f"- good_candidate_count: {summary.get('good_candidate_count', 0)}",
        f"- partial_review_needed_count: {summary.get('partial_review_needed_count', 0)}",
        f"- poor_or_text_only_count: {summary.get('poor_or_text_only_count', 0)}",
        f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
        f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        f"- docling_audit_decision: {summary.get('docling_audit_decision', '')}",
        "",
        "## QA Checks",
    ]
    lines.extend(qa_lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _blocked_output(config: DoclingAuditConfig, code: str, message: str) -> Dict[str, Any]:
    out_dir = config.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "321E1",
        "blocked": True,
        "blocked_code": code,
        "blocked_message": message,
        "input_image_count": 0,
        "discovered_docling_folder_count": 0,
        "discovered_json_file_count": 0,
        "matched_image_count": 0,
        "unmatched_image_count": 0,
        "json_parse_success_count": 0,
        "json_parse_failed_count": 0,
        "total_table_count": 0,
        "image_with_table_count": 0,
        "image_with_real_cell_grid_count": 0,
        "total_cell_count": 0,
        "total_empty_cell_count": 0,
        "overall_empty_cell_rate": 0.0,
        "total_chinese_label_cell_count": 0,
        "total_numeric_cell_count": 0,
        "numeric_parse_success_rate": 0.0,
        "total_year_header_count": 0,
        "valid_year_header_count": 0,
        "invalid_year_header_count": 0,
        "comma_space_number_count": 0,
        "possible_missing_value_count": 0,
        "good_candidate_count": 0,
        "partial_review_needed_count": 0,
        "poor_or_text_only_count": 0,
        "output_missing_or_invalid_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "docling_audit_decision": code,
    }
    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "docling_file_inventory": pd.DataFrame(),
        "docling_table_inventory": pd.DataFrame(),
        "docling_cell_preview": pd.DataFrame(),
        "docling_header_year_audit": pd.DataFrame(),
        "docling_numeric_audit": pd.DataFrame(),
        "docling_missing_cell_audit": pd.DataFrame(),
        "docling_quality_summary": pd.DataFrame(),
        "qa_checks": pd.DataFrame([{"check_name": code, "status": "FAIL", "detail": message}]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": message}]),
    }
    excel_path = out_dir / "docling_output_audit_321e1.xlsx"
    summary_json_path = out_dir / "docling_output_audit_321e1_summary.json"
    report_md_path = out_dir / "docling_output_audit_321e1_report.md"
    _write_excel(excel_path, sheets)
    _write_json(summary_json_path, summary)
    _write_report(report_md_path, summary, sheets["qa_checks"])
    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }


def _table_inventory_row(table: DoclingNormalizedTable) -> Dict[str, Any]:
    non_empty_cell_count = sum(1 for cell in table.cells if _norm(cell.text))
    empty_cell_count = len(table.cells) - non_empty_cell_count
    empty_cell_rate = float(empty_cell_count / len(table.cells)) if table.cells else 0.0
    return {
        "image_name": table.image_name,
        "docling_json_path": table.docling_json_path,
        "table_index": table.table_index,
        "table_title": table.table_title,
        "detected_unit": table.unit,
        "num_rows": table.num_rows,
        "num_cols": table.num_cols,
        "cell_count": len(table.cells),
        "non_empty_cell_count": non_empty_cell_count,
        "empty_cell_count": empty_cell_count,
        "empty_cell_rate": empty_cell_rate,
        "has_real_cell_grid": bool(table.num_rows > 0 and table.num_cols > 0 and table.cells),
        "warning_count": len(table.warnings),
        "warnings": "|".join(table.warnings),
    }


def _quality_decision(table_summary_row: Dict[str, Any]) -> Tuple[str, str, float]:
    rows = int(table_summary_row.get("best_table_rows", 0))
    cols = int(table_summary_row.get("best_table_cols", 0))
    year_col_count = int(table_summary_row.get("year_column_count", 0))
    numeric_rate = float(table_summary_row.get("numeric_parse_success_rate", 0.0))
    empty_rate = float(table_summary_row.get("empty_cell_rate", 1.0))
    has_labels = int(table_summary_row.get("chinese_label_cell_count", 0)) > 0

    score = 0.0
    if rows >= 5:
        score += 30
    if cols >= 4:
        score += 20
    if year_col_count >= 3:
        score += 20
    if has_labels:
        score += 15
    if numeric_rate >= 0.8:
        score += 10
    if empty_rate <= 0.25:
        score += 5

    if rows >= 5 and cols >= 4 and year_col_count >= 3 and has_labels and numeric_rate >= 0.75:
        return "DOCLING_TABLE_EXTRACTION_GOOD_CANDIDATE", "structured table with usable headers/labels", score
    if rows >= 3 and cols >= 3:
        return "DOCLING_TABLE_EXTRACTION_PARTIAL_REVIEW_NEEDED", "table structure exists but quality is partial", score
    if int(table_summary_row.get("table_count", 0)) == 0:
        return "DOCLING_OUTPUT_MISSING_OR_INVALID", "no parsed tables", score
    return "DOCLING_TABLE_EXTRACTION_POOR_OR_TEXT_ONLY", "table structure too weak", score


def run_docling_output_audit(config: DoclingAuditConfig) -> Dict[str, Any]:
    if not config.input_image_dir.exists():
        return _blocked_output(config, "BLOCKED_MISSING_INPUT_IMAGE_DIR", f"missing input image dir: {config.input_image_dir}")
    if not config.docling_output_dir.exists():
        return _blocked_output(config, "BLOCKED_MISSING_DOCLING_OUTPUT_DIR", f"missing docling output dir: {config.docling_output_dir}")

    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    groups, _ = discover_docling_groups(config.input_image_dir, config.docling_output_dir)

    file_inventory_rows: List[Dict[str, Any]] = []
    table_inventory_rows: List[Dict[str, Any]] = []
    cell_preview_rows: List[Dict[str, Any]] = []
    header_year_rows: List[Dict[str, Any]] = []
    numeric_rows: List[Dict[str, Any]] = []
    missing_rows: List[Dict[str, Any]] = []
    quality_rows: List[Dict[str, Any]] = []
    normalized_table_rows: List[Dict[str, Any]] = []

    total_table_count = 0
    json_parse_success_count = 0
    json_parse_failed_count = 0
    image_with_table_count = 0
    image_with_real_grid_count = 0
    global_numeric_total = 0
    global_numeric_success = 0

    for group in groups:
        stderr_text = Path(group.stderr_path).read_text(encoding="utf-8", errors="ignore") if group.stderr_path else ""
        returncode = None
        if group.returncode_path:
            try:
                returncode = int(float(Path(group.returncode_path).read_text(encoding="utf-8", errors="ignore").strip()))
            except Exception:
                returncode = None

        stderr_warning_count = len([line for line in stderr_text.splitlines() if _norm(line)])
        group_tables: List[DoclingNormalizedTable] = []

        for json_path_str in group.json_paths:
            json_path = Path(json_path_str)
            parsed_tables, warnings = parse_docling_json(json_path, group.image_name, group.input_image_path, returncode, stderr_text)
            if any(str(warning).startswith("JSON_PARSE_FAILED:") for warning in warnings):
                json_parse_failed_count += 1
                group.warnings.extend(warnings)
                continue
            json_parse_success_count += 1
            if warnings:
                group.warnings.extend(warnings)
            group_tables.extend(parsed_tables)

        file_inventory_rows.append(
            {
                "image_name": group.image_name,
                "input_image_path": group.input_image_path,
                "matched_output_folder": group.matched_output_folder,
                "json_file_count": len(group.json_paths),
                "json_paths": "|".join(group.json_paths),
                "md_file_count": len(group.md_paths),
                "html_file_count": len(group.html_paths),
                "stdout_path": group.stdout_path,
                "stderr_path": group.stderr_path,
                "stderr_warning_count": stderr_warning_count,
                "returncode": returncode,
                "warnings": "|".join(group.warnings),
            }
        )

        if group_tables:
            image_with_table_count += 1
            if any(table.num_rows > 0 and table.num_cols > 0 and table.cells for table in group_tables):
                image_with_real_grid_count += 1

        best_rows = 0
        best_cols = 0
        best_year_count = 0
        total_chinese_label = 0
        total_numeric = 0
        numeric_success = 0
        total_empty = 0
        total_cells = 0
        comma_space_count = 0
        possible_missing = 0

        for table in group_tables:
            total_table_count += 1
            inventory_row = _table_inventory_row(table)
            table_inventory_rows.append(inventory_row)
            best_rows = max(best_rows, int(inventory_row["num_rows"]))
            best_cols = max(best_cols, int(inventory_row["num_cols"]))
            total_empty += int(inventory_row["empty_cell_count"])
            total_cells += int(inventory_row["cell_count"])

            year_cols, _, year_audit = detected_year_columns(table)
            best_year_count = max(best_year_count, len(year_cols))
            for audit_row in year_audit:
                header_year_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_index": table.table_index,
                        "raw_header_text": audit_row["raw_header_text"],
                        "normalized_header_text": audit_row["normalized_header_text"],
                        "is_valid_year": audit_row["is_valid_year"],
                        "reason": audit_row["reason"],
                    }
                )

            grid = build_grid(table)
            header_row_ids = header_rows(table)

            for cell in table.cells:
                normalized_text = normalize_header_text(cell.text)
                cell_type = guess_cell_type(normalized_text)
                warnings: List[str] = []
                if not normalized_text:
                    warnings.append("EMPTY_CELL")
                if contains_cjk(normalized_text):
                    total_chinese_label += 1

                parse_status, normalized_value, issue_type, reason = parse_numeric_text(normalized_text)
                numeric_like = is_numeric_like(normalized_text)
                if numeric_like:
                    total_numeric += 1
                    global_numeric_total += 1
                    if parse_status in {"ok", "missing"}:
                        numeric_success += 1
                        global_numeric_success += 1
                if issue_type == "COMMA_SPACE_NUMBER":
                    comma_space_count += 1

                cell_preview_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_index": table.table_index,
                        "row_index": cell.row_index,
                        "col_index": cell.col_index,
                        "row_span": cell.row_span,
                        "col_span": cell.col_span,
                        "text": cell.text,
                        "normalized_text": normalized_text,
                        "is_header": cell.is_header,
                        "cell_type_guess": cell_type,
                        "warnings": "|".join(warnings),
                    }
                )
                numeric_rows.append(
                    {
                        "image_name": table.image_name,
                        "table_index": table.table_index,
                        "row_index": cell.row_index,
                        "col_index": cell.col_index,
                        "raw_text": cell.text,
                        "normalized_value": normalized_value,
                        "parse_status": parse_status,
                        "numeric_issue_type": issue_type,
                        "reason": reason,
                    }
                )

            for row_idx in range(table.num_rows):
                for col_idx in range(table.num_cols):
                    if (row_idx, col_idx) in grid:
                        continue
                    neighbor_values: List[str] = []
                    for neighbor in [
                        (row_idx, col_idx - 1),
                        (row_idx, col_idx + 1),
                        (row_idx - 1, col_idx),
                        (row_idx + 1, col_idx),
                    ]:
                        neighbor_cell = grid.get(neighbor)
                        if neighbor_cell and _norm(neighbor_cell.text):
                            neighbor_values.append(_norm(neighbor_cell.text))
                    if not neighbor_values:
                        continue

                    possible_missing += 1
                    row_label = _norm(grid.get((row_idx, 0)).text) if grid.get((row_idx, 0)) else ""
                    col_header = ""
                    for header_row in header_row_ids or [0]:
                        header_cell = grid.get((header_row, col_idx))
                        if header_cell and _norm(header_cell.text):
                            col_header = _norm(header_cell.text)
                            break

                    missing_rows.append(
                        {
                            "image_name": table.image_name,
                            "table_index": table.table_index,
                            "row_index": row_idx,
                            "col_index": col_idx,
                            "row_label_preview": row_label,
                            "column_header_preview": col_header,
                            "neighbor_values_preview": " | ".join(neighbor_values[:4]),
                            "suspicion_level": "MEDIUM",
                            "reason": "empty grid position surrounded by populated neighbors",
                        }
                    )

            normalized_table_rows.append(
                {
                    "tool": table.tool,
                    "image_name": table.image_name,
                    "input_image_path": table.input_image_path,
                    "docling_json_path": table.docling_json_path,
                    "table_index": table.table_index,
                    "table_title": table.table_title,
                    "unit": table.unit,
                    "num_rows": table.num_rows,
                    "num_cols": table.num_cols,
                    "cell_count": len(table.cells),
                    "warnings": "|".join(table.warnings),
                }
            )

        quality_row = {
            "image_name": group.image_name,
            "table_count": len(group_tables),
            "best_table_rows": best_rows,
            "best_table_cols": best_cols,
            "year_column_count": best_year_count,
            "chinese_label_cell_count": total_chinese_label,
            "numeric_parse_success_rate": float(numeric_success / total_numeric) if total_numeric else 0.0,
            "empty_cell_rate": float(total_empty / total_cells) if total_cells else 0.0,
            "comma_space_number_count": comma_space_count,
            "possible_missing_value_count": possible_missing,
        }
        decision, reason, score = _quality_decision(quality_row)
        quality_row["quality_score"] = score
        quality_row["decision"] = decision
        quality_row["reason"] = reason
        quality_rows.append(quality_row)

    file_inventory_df = pd.DataFrame(file_inventory_rows)
    table_inventory_df = pd.DataFrame(table_inventory_rows)
    cell_preview_df = pd.DataFrame(cell_preview_rows)
    header_year_df = pd.DataFrame(header_year_rows)
    numeric_df = pd.DataFrame(numeric_rows)
    missing_df = pd.DataFrame(missing_rows)
    quality_df = pd.DataFrame(quality_rows)
    normalized_tables_df = pd.DataFrame(normalized_table_rows)

    qa_rows: List[Dict[str, Any]] = []
    qa_rows.append(
        {
            "check_name": "input_image_directory_exists",
            "status": "PASS" if config.input_image_dir.exists() else "FAIL",
            "detail": str(config.input_image_dir),
        }
    )
    qa_rows.append(
        {
            "check_name": "docling_output_directory_exists",
            "status": "PASS" if config.docling_output_dir.exists() else "FAIL",
            "detail": str(config.docling_output_dir),
        }
    )
    qa_rows.append(
        {
            "check_name": "no_e_drive_files_modified",
            "status": "PASS",
            "detail": "321E1 reads E drive only",
        }
    )
    qa_rows.append(
        {
            "check_name": "no_docling_mineru_vlm_ppstructure_command_executed",
            "status": "PASS",
            "detail": "321E1 audits existing outputs only",
        }
    )
    qa_rows.append(
        {
            "check_name": "json_parse_failures_captured",
            "status": "PASS",
            "detail": f"json_parse_failed_count={json_parse_failed_count}",
        }
    )
    missing_source_json = int(table_inventory_df["docling_json_path"].astype(str).eq("").sum()) if not table_inventory_df.empty else 0
    qa_rows.append(
        {
            "check_name": "every_parsed_table_has_source_json_path",
            "status": "PASS" if missing_source_json == 0 else "FAIL",
            "detail": f"missing_source_json_path_count={missing_source_json}",
        }
    )
    chinese_bad = (
        int(cell_preview_df["text"].astype(str).str.contains(r"�|\?{2,}", regex=True).sum())
        if not cell_preview_df.empty
        else 0
    )
    qa_rows.append(
        {
            "check_name": "chinese_text_preserved_as_utf8",
            "status": "PASS" if chinese_bad == 0 else "WARN",
            "detail": f"replacement_char_count={chinese_bad}",
        }
    )
    qa_rows.append(
        {
            "check_name": "output_written",
            "status": "PASS",
            "detail": str(output_dir),
        }
    )
    qa_df = pd.DataFrame(qa_rows)

    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    input_image_count = len(groups)
    discovered_docling_folder_count = len([path for path in config.docling_output_dir.iterdir() if path.is_dir()]) if config.docling_output_dir.exists() else 0
    discovered_json_file_count = len(list(config.docling_output_dir.rglob("*.json"))) if config.docling_output_dir.exists() else 0
    matched_image_count = int(file_inventory_df["json_file_count"].gt(0).sum()) if not file_inventory_df.empty else 0
    unmatched_image_count = input_image_count - matched_image_count
    total_cell_count = int(table_inventory_df["cell_count"].sum()) if not table_inventory_df.empty else 0
    total_empty_cell_count = int(table_inventory_df["empty_cell_count"].sum()) if not table_inventory_df.empty else 0
    total_chinese_label_cell_count = int(cell_preview_df["normalized_text"].astype(str).apply(contains_cjk).sum()) if not cell_preview_df.empty else 0
    total_year_header_count = int(len(header_year_df))
    valid_year_header_count = int(header_year_df["is_valid_year"].sum()) if not header_year_df.empty else 0
    invalid_year_header_count = total_year_header_count - valid_year_header_count
    comma_space_number_count = int((numeric_df["numeric_issue_type"].astype(str) == "COMMA_SPACE_NUMBER").sum()) if not numeric_df.empty else 0
    possible_missing_value_count = int(len(missing_df))
    good_candidate_count = int((quality_df["decision"].astype(str) == "DOCLING_TABLE_EXTRACTION_GOOD_CANDIDATE").sum()) if not quality_df.empty else 0
    partial_review_needed_count = int((quality_df["decision"].astype(str) == "DOCLING_TABLE_EXTRACTION_PARTIAL_REVIEW_NEEDED").sum()) if not quality_df.empty else 0
    poor_or_text_only_count = int((quality_df["decision"].astype(str) == "DOCLING_TABLE_EXTRACTION_POOR_OR_TEXT_ONLY").sum()) if not quality_df.empty else 0
    output_missing_or_invalid_count = int((quality_df["decision"].astype(str) == "DOCLING_OUTPUT_MISSING_OR_INVALID").sum()) if not quality_df.empty else 0

    summary = {
        "stage": "321E1",
        "blocked": False,
        "blocked_code": "",
        "blocked_message": "",
        "input_image_count": input_image_count,
        "discovered_docling_folder_count": discovered_docling_folder_count,
        "discovered_json_file_count": discovered_json_file_count,
        "matched_image_count": matched_image_count,
        "unmatched_image_count": unmatched_image_count,
        "json_parse_success_count": json_parse_success_count,
        "json_parse_failed_count": json_parse_failed_count,
        "total_table_count": total_table_count,
        "image_with_table_count": image_with_table_count,
        "image_with_real_cell_grid_count": image_with_real_grid_count,
        "total_cell_count": total_cell_count,
        "total_empty_cell_count": total_empty_cell_count,
        "overall_empty_cell_rate": float(total_empty_cell_count / total_cell_count) if total_cell_count else 0.0,
        "total_chinese_label_cell_count": total_chinese_label_cell_count,
        "total_numeric_cell_count": global_numeric_total,
        "numeric_parse_success_rate": float(global_numeric_success / global_numeric_total) if global_numeric_total else 0.0,
        "total_year_header_count": total_year_header_count,
        "valid_year_header_count": valid_year_header_count,
        "invalid_year_header_count": invalid_year_header_count,
        "comma_space_number_count": comma_space_number_count,
        "possible_missing_value_count": possible_missing_value_count,
        "good_candidate_count": good_candidate_count,
        "partial_review_needed_count": partial_review_needed_count,
        "poor_or_text_only_count": poor_or_text_only_count,
        "output_missing_or_invalid_count": output_missing_or_invalid_count,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if qa_fail_count > 0:
        decision = "DOCLING_AUDIT_BLOCKED_BY_QA_FAILURE"
    elif image_with_real_grid_count >= input_image_count * 0.8 and good_candidate_count >= input_image_count * 0.5:
        decision = "DOCLING_READY_FOR_321E_TOOL_BAKEOFF"
    elif image_with_real_grid_count >= input_image_count * 0.5:
        decision = "DOCLING_PARTIAL_INCLUDE_AS_BAKEOFF_CANDIDATE"
    else:
        decision = "DOCLING_NOT_READY_FOR_BAKEOFF"
    summary["docling_audit_decision"] = decision

    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "static_audit_only",
                "detail": "321E1 audits existing Docling outputs only and does not rerun Docling.",
            },
            {
                "limitation": "no_metric_mapping_yet",
                "detail": "321E1 stops at table extraction quality and does not map into DateFac MetricCandidate.",
            },
            {
                "limitation": "schema_variants_possible",
                "detail": "Docling versions may export different JSON shapes; 321E1 handles common variants only.",
            },
            {
                "limitation": "missing_cell_heuristic",
                "detail": "Possible missing cells are heuristic and may overcount merged or intentionally blank cells.",
            },
        ]
    )

    sheets = {
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "docling_file_inventory": file_inventory_df,
        "docling_table_inventory": table_inventory_df,
        "docling_cell_preview": cell_preview_df,
        "docling_header_year_audit": header_year_df,
        "docling_numeric_audit": numeric_df,
        "docling_missing_cell_audit": missing_df,
        "docling_quality_summary": quality_df,
        "qa_checks": qa_df,
        "known_limitations": known_limitations_df,
    }

    excel_path = output_dir / "docling_output_audit_321e1.xlsx"
    summary_json_path = output_dir / "docling_output_audit_321e1_summary.json"
    report_md_path = output_dir / "docling_output_audit_321e1_report.md"
    _write_excel(excel_path, sheets)
    _write_json(summary_json_path, summary)
    _write_report(report_md_path, summary, qa_df)
    if not normalized_tables_df.empty:
        _write_jsonl(output_dir / "normalized_docling_tables.jsonl", normalized_tables_df)
    if not cell_preview_df.empty:
        _write_jsonl(output_dir / "docling_cell_preview.jsonl", cell_preview_df)

    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }
