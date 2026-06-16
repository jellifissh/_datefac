"""Workbook intake helpers for the 348A Excel audit pilot."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from datefac_agent.schemas.audit_models import SpreadsheetRow, WorkbookIntakeResult

PERIOD_LABEL_RE = re.compile(r"^(?:19|20)\d{2}(?:A|E|Q[1-4])?$", re.IGNORECASE)
EVIDENCE_HEADER_HINTS = ("页", "page", "evidence", "source", "出处", "来源")


def _stringify_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_header(value: Any, column_index: int) -> str:
    text = _stringify_cell(value)
    return text or f"column_{column_index}"


def _extract_unit_hint(metric_name: str) -> str | None:
    match = re.search(r"[（(]([^()（）]+)[)）]", metric_name)
    if match:
        return match.group(1).strip() or None
    return None


def _extract_metric_name(values: list[Any]) -> str:
    for value in values[:2]:
        text = _stringify_cell(value)
        if text:
            return text
    for value in values:
        text = _stringify_cell(value)
        if text:
            return text
    return "UNLABELED_ROW"


def _extract_explicit_evidence_ref(headers: list[str], values: list[Any]) -> str | None:
    for header, value in zip(headers, values):
        lower_header = header.lower()
        if any(hint in lower_header for hint in EVIDENCE_HEADER_HINTS):
            text = _stringify_cell(value)
            if text:
                return text
    return None


def detect_period_labels(column_names: list[str]) -> list[str]:
    """Return period labels found in workbook header cells."""

    labels: list[str] = []
    for name in column_names:
        text = _stringify_cell(name)
        if PERIOD_LABEL_RE.match(text):
            labels.append(text)
    return labels


def read_excel_workbook(excel_path: str | Path) -> WorkbookIntakeResult:
    """Read an extracted workbook into lightweight structured rows."""

    path = Path(excel_path)
    workbook = load_workbook(path, read_only=True, data_only=True)
    rows: list[SpreadsheetRow] = []

    for sheet_name in workbook.sheetnames:
        worksheet = workbook[sheet_name]
        header_values: list[Any] | None = None
        header_names: list[str] = []

        for row_index, raw_row in enumerate(worksheet.iter_rows(values_only=True), start=1):
            values = list(raw_row)
            if header_values is None:
                header_values = values
                header_names = [
                    _normalize_header(value, column_index)
                    for column_index, value in enumerate(values, start=1)
                ]
                continue

            if not any(value is not None and str(value).strip() for value in values):
                continue

            padded_values = values + [None] * (len(header_names) - len(values))
            raw_values = {
                header_names[column_index]: padded_values[column_index]
                for column_index in range(len(header_names))
            }
            metric_name = _extract_metric_name(values)
            period_values = {
                header: raw_values[header]
                for header in detect_period_labels(header_names)
                if raw_values.get(header) is not None and str(raw_values.get(header)).strip() != ""
            }
            rows.append(
                SpreadsheetRow(
                    source_excel_path=str(path),
                    sheet_name=sheet_name,
                    row_index=row_index,
                    column_names=header_names,
                    raw_values=raw_values,
                    metric_name=metric_name,
                    unit_hint=_extract_unit_hint(metric_name),
                    period_values=period_values,
                    explicit_evidence_ref=_extract_explicit_evidence_ref(header_names, padded_values),
                )
            )

    return WorkbookIntakeResult(
        source_excel_path=str(path),
        sheet_names=list(workbook.sheetnames),
        rows=rows,
        sheet_count=len(workbook.sheetnames),
        row_count_total=len(rows),
    )
