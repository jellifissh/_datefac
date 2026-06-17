"""Deterministic row type classification for the 348A workbook audit."""

from __future__ import annotations

import re

from datefac_agent.schemas.audit_models import RowType, SpreadsheetRow

STRICT_FINANCIAL_SHEETS = {
    "财务估值",
    "资产负债表",
    "利润表",
    "现金流量表",
    "盈利预测与估值",
    "重要财务与估值指标",
    "盈利预测分业务",
}
MARKET_REFERENCE_SHEETS = {"市场与基础数据", "可比公司估值"}
NARRATIVE_SHEETS = {"核心观点", "报告概要", "核心摘要", "投资要点"}
PERIOD_LABEL_RE = re.compile(r"(?:19|20)\d{2}(?:\s*(?:A|E|Q[1-4]|FY))?", re.IGNORECASE)
NARRATIVE_METRIC_HINTS = (
    "报告标题",
    "报告日期",
    "投资评级",
    "行业分类",
    "证券分析师",
    "核心投资逻辑",
    "要点",
    "盈利预测摘要",
)
MARKET_METRIC_HINTS = (
    "收盘价",
    "最低",
    "最高",
    "市净率",
    "市盈率",
    "总市值",
    "流通a股",
    "总股本",
    "每股净资产",
    "资产负债率",
    "roe",
    "roic",
    "p/e",
    "p/b",
)


def _has_period_headers(row: SpreadsheetRow) -> bool:
    return sum(1 for name in row.column_names if PERIOD_LABEL_RE.search(str(name).strip())) >= 2


def _metric_text(row: SpreadsheetRow) -> str:
    return row.metric_name.strip().lower()


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    return any(hint in text for hint in hints)


def classify_row_type(row: SpreadsheetRow) -> RowType:
    """Classify a workbook row from sheet name and light structural cues."""

    metric_text = _metric_text(row)

    if row.sheet_name in STRICT_FINANCIAL_SHEETS:
        return "STRICT_FINANCIAL_TABLE_ROW"
    if row.sheet_name in MARKET_REFERENCE_SHEETS:
        return "MARKET_REFERENCE_ROW"
    if row.sheet_name in NARRATIVE_SHEETS:
        if _contains_any(metric_text, MARKET_METRIC_HINTS):
            return "MARKET_REFERENCE_ROW"
        return "NARRATIVE_ASSERTION"
    if _has_period_headers(row):
        return "STRICT_FINANCIAL_TABLE_ROW"
    if _contains_any(metric_text, NARRATIVE_METRIC_HINTS):
        return "NARRATIVE_ASSERTION"
    if _contains_any(metric_text, MARKET_METRIC_HINTS):
        return "MARKET_REFERENCE_ROW"
    return "UNKNOWN_ROW"
