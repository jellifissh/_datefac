"""Deterministic row type classification for the 348A workbook audit."""

from __future__ import annotations

import re

from datefac_agent.schemas.audit_models import RowType, SpreadsheetRow

STRICT_FINANCIAL_SHEETS = {"财务估值", "资产负债表", "利润表", "现金流量表"}
MARKET_REFERENCE_SHEETS = {"市场与基础数据"}
NARRATIVE_SHEETS = {"核心观点"}
PERIOD_LABEL_RE = re.compile(r"^(?:19|20)\d{2}(?:A|E|Q[1-4])?$", re.IGNORECASE)


def _has_period_headers(row: SpreadsheetRow) -> bool:
    return any(PERIOD_LABEL_RE.match(str(name).strip()) for name in row.column_names)


def classify_row_type(row: SpreadsheetRow) -> RowType:
    """Classify a workbook row from sheet name and light structural cues."""

    if row.sheet_name in STRICT_FINANCIAL_SHEETS:
        return "STRICT_FINANCIAL_TABLE_ROW"
    if row.sheet_name in MARKET_REFERENCE_SHEETS:
        return "MARKET_REFERENCE_ROW"
    if row.sheet_name in NARRATIVE_SHEETS:
        return "NARRATIVE_ASSERTION"
    if _has_period_headers(row):
        return "STRICT_FINANCIAL_TABLE_ROW"
    return "UNKNOWN_ROW"
