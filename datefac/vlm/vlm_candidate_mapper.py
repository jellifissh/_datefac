from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.domain.metric_candidate import MetricCandidate
from datefac.vlm.vlm_output_reader import VLMFolderRecord


YEAR_RULE = re.compile(r"^(20\d{2})([AE])?$", re.IGNORECASE)
MONETARY_UNIT_HINTS = ("亿元", "百万元", "万元", "元")
UNKNOWN_METRIC_CODE = "unknown_metric"
SAFE_RATIO_METRICS = {
    "gross_margin",
    "ebit_margin",
    "ebitda_margin",
    "net_margin",
    "roe",
    "roic",
    "revenue_growth",
    "net_profit_growth",
    "dividend_yield",
    "debt_ratio",
    "revenue_share",
    "pe",
    "pb",
    "ev_ebitda",
}
PER_SHARE_METRICS = {"eps", "dps", "bvps"}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _optional_text(value: Any) -> Optional[str]:
    text = _norm(value)
    if not text or text.lower() in {"none", "null", "nan"}:
        return None
    return text


def _as_float(value: Any) -> Optional[float]:
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
        parsed = float(text)
    except Exception:
        return None
    return -parsed if negative else parsed


def _normalize_label(label: str) -> str:
    text = _norm(label)
    text = (
        text.replace("（", "(")
        .replace("）", ")")
        .replace("：", ":")
        .replace("、", "")
        .replace(" ", "")
        .replace("\u3000", "")
        .replace("－", "-")
    )
    text = text.replace("&", "及")
    return text.lower()


def _contains_corruption(text: str) -> bool:
    return ("?" in text) or ("？" in text) or ("\ufffd" in text) or ("�" in text)


def _meaningless_raw_value(raw_value: Any) -> bool:
    return _norm(raw_value) in {"", "--", "—", "-", "n/a", "N/A", "NA", "nan", "None", "null"}


@dataclass(frozen=True)
class MetricSpec:
    metric_code: str
    canonical_name: str
    metric_family: str
    aliases: Tuple[str, ...]


METRIC_SPECS: Sequence[MetricSpec] = (
    MetricSpec("operating_cash_flow", "Operating Cash Flow", "cash_flow", ("经营活动现金流",)),
    MetricSpec("net_profit", "Net Profit", "profitability", ("净利润",)),
    MetricSpec("parent_net_profit", "Parent Net Profit", "profitability", ("归属于母公司净利润", "归母净利润", "归属于上市公司股东的净利润", "归母净利", "归母净利润(百万元)", "归母净利润（百万元）")),
    MetricSpec("depreciation_amortization", "Depreciation & Amortization", "cash_flow", ("折旧摊销",)),
    MetricSpec("finance_expense", "Finance Expense", "income_statement", ("财务费用",)),
    MetricSpec("investment_loss", "Investment Loss", "cash_flow", ("投资损失",)),
    MetricSpec("working_capital_change", "Working Capital Change", "cash_flow", ("营运资金变动", "营运资本变动")),
    MetricSpec("other_operating_cf", "Other Operating Cash Flow", "cash_flow", ("其他经营现金流", "其它", "其他", "其他经营活动现金流")),
    MetricSpec("investing_cash_flow", "Investing Cash Flow", "cash_flow", ("投资活动现金流",)),
    MetricSpec("capex", "Capex", "cash_flow", ("资本支出", "资本开支", "资本开支/资本支出")),
    MetricSpec("long_term_investment", "Long-Term Investment", "cash_flow", ("长期投资", "长期股权投资")),
    MetricSpec("other_investing_cash_flow", "Other Investing Cash Flow", "cash_flow", ("其他投资现金流", "其它投资现金流")),
    MetricSpec("financing_cash_flow", "Financing Cash Flow", "cash_flow", ("筹资活动现金流", "融资活动现金流")),
    MetricSpec("short_term_borrowings", "Short-Term Borrowings", "balance_sheet", ("短期借款", "短期借款及交易性金融负债")),
    MetricSpec("long_term_borrowings", "Long-Term Borrowings", "balance_sheet", ("长期借款",)),
    MetricSpec("equity_financing", "Equity Financing", "cash_flow", ("普通股增加", "权益性融资")),
    MetricSpec("capital_reserve_increase", "Capital Reserve Increase", "cash_flow", ("资本公积增加",)),
    MetricSpec("other_financing_cash_flow", "Other Financing Cash Flow", "cash_flow", ("其他筹资现金流", "其它融资现金流", "其他融资现金流")),
    MetricSpec("net_cash_change", "Net Cash Change", "cash_flow", ("现金净增加额", "现金净变动",)),
    MetricSpec("cash_beginning_balance", "Cash Beginning Balance", "cash_flow", ("期初现金余额", "现金期初余额")),
    MetricSpec("cash_ending_balance", "Cash Ending Balance", "cash_flow", ("期末现金余额", "现金期末余额")),
    MetricSpec("free_cash_flow_firm", "Free Cash Flow to Firm", "cash_flow", ("企业自由现金流",)),
    MetricSpec("free_cash_flow_equity", "Free Cash Flow to Equity", "cash_flow", ("权益自由现金流",)),
    MetricSpec("cash_and_equivalents", "Cash & Equivalents", "balance_sheet", ("现金及现金等价物", "货币资金")),
    MetricSpec("accounts_receivable", "Accounts Receivable", "balance_sheet", ("应收款项", "应收账款")),
    MetricSpec("inventory", "Inventory", "balance_sheet", ("存货净额", "存货")),
    MetricSpec("other_current_assets", "Other Current Assets", "balance_sheet", ("其他流动资产",)),
    MetricSpec("current_assets_total", "Current Assets Total", "balance_sheet", ("流动资产合计",)),
    MetricSpec("fixed_assets", "Fixed Assets", "balance_sheet", ("固定资产",)),
    MetricSpec("intangible_assets", "Intangible Assets", "balance_sheet", ("无形资产", "无形资产及其他")),
    MetricSpec("investment_property", "Investment Property", "balance_sheet", ("投资性房地产",)),
    MetricSpec("total_assets", "Total Assets", "balance_sheet", ("资产总计", "资产总额")),
    MetricSpec("accounts_payable", "Accounts Payable", "balance_sheet", ("应付款项", "应付账款")),
    MetricSpec("current_liabilities_total", "Current Liabilities Total", "balance_sheet", ("流动负债合计",)),
    MetricSpec("total_liabilities", "Total Liabilities", "balance_sheet", ("负债合计",)),
    MetricSpec("shareholders_equity", "Shareholders' Equity", "balance_sheet", ("股东权益", "所有者权益", "归母股东权益")),
    MetricSpec("minority_interest", "Minority Interest", "balance_sheet", ("少数股东权益",)),
    MetricSpec("total_liabilities_and_equity", "Total Liabilities & Equity", "balance_sheet", ("负债和股东权益合计",)),
    MetricSpec("revenue", "Revenue", "income_statement", ("营业收入", "营业总收入", "收入合计", "营业收入(百万元)", "营业收入（百万元）", "营业总收入(百万元)", "营业总收入（百万元）", "营业收入(亿元)", "营业收入（亿元）")),
    MetricSpec("operating_cost", "Operating Cost", "income_statement", ("营业成本", "营业成本(含金融类)")),
    MetricSpec("gross_profit", "Gross Profit", "income_statement", ("毛利润", "毛利润(亿元)", "毛利润（亿元）")),
    MetricSpec("gross_margin", "Gross Margin", "margin", ("毛利率", "综合毛利率", "燃机业务毛利率", "毛利率(%)", "毛利率（%）")),
    MetricSpec("selling_expense", "Selling Expense", "income_statement", ("销售费用", "营业费用")),
    MetricSpec("admin_expense", "Administrative Expense", "income_statement", ("管理费用",)),
    MetricSpec("rd_expense", "R&D Expense", "income_statement", ("研发费用",)),
    MetricSpec("other_income", "Other Income", "income_statement", ("加:其他收益", "其他收益", "其他收入")),
    MetricSpec("investment_income", "Investment Income", "income_statement", ("投资净收益", "投资收益")),
    MetricSpec("fair_value_change", "Fair Value Change", "income_statement", ("公允价值变动", "公允价值变动收益")),
    MetricSpec("fair_value_change_loss", "Fair Value Change Loss", "cash_flow", ("公允价值变动损失",)),
    MetricSpec("asset_impairment_loss", "Asset Impairment Loss", "income_statement", ("减值损失", "资产减值损失", "资产及信用减值损失")),
    MetricSpec("asset_impairment_provision", "Asset Impairment Provision", "cash_flow", ("资产减值准备",)),
    MetricSpec("asset_disposal_income", "Asset Disposal Income", "income_statement", ("资产处置收益",)),
    MetricSpec("operating_profit", "Operating Profit", "income_statement", ("营业利润",)),
    MetricSpec("pretax_profit", "Pretax Profit", "income_statement", ("利润总额",)),
    MetricSpec("income_tax_expense", "Income Tax Expense", "income_statement", ("所得税费用",)),
    MetricSpec("non_operating_balance", "Non-operating Balance", "income_statement", ("营业外净收支",)),
    MetricSpec("roe", "ROE", "profitability", ("roe", "净资产收益率", "roe(%)")),
    MetricSpec("roic", "ROIC", "profitability", ("roic",)),
    MetricSpec("eps", "EPS", "valuation", ("每股收益", "eps", "eps(摊薄/元)", "eps-最新摊薄(元/股)", "eps-最新摊薄（元/股）")),
    MetricSpec("dps", "DPS", "valuation", ("每股红利", "dps")),
    MetricSpec("bvps", "BVPS", "valuation", ("每股净资产", "bvps")),
    MetricSpec("ebit_margin", "EBIT Margin", "margin", ("ebitmargin", "ebit margin")),
    MetricSpec("ebitda_margin", "EBITDA Margin", "margin", ("ebitdamargin", "ebitda margin")),
    MetricSpec("revenue_growth", "Revenue Growth", "growth", ("收入增长",)),
    MetricSpec("net_profit_growth", "Net Profit Growth", "growth", ("净利润增长率",)),
    MetricSpec("net_margin", "Net Margin", "margin", ("净利率", "归母净利润率")),
    MetricSpec("debt_ratio", "Debt Ratio", "margin", ("资产负债率",)),
    MetricSpec("dividend_yield", "Dividend Yield", "valuation", ("息率", "股息率")),
    MetricSpec("pe", "PE", "valuation", ("p/e", "市盈率", "pe", "p/e(现价&最新摊薄)", "p/e（现价&最新摊薄）")),
    MetricSpec("pb", "PB", "valuation", ("p/b", "市净率", "pb")),
    MetricSpec("ev_ebitda", "EV/EBITDA", "valuation", ("ev/ebitda",)),
    MetricSpec("revenue_share", "Revenue Share", "other", ("收入占比",)),
    MetricSpec("tax_surcharge", "Taxes & Surcharges", "income_statement", ("营业税金及附加", "税金及附加")),
)


KNOWN_METRICS: Dict[str, Dict[str, str]] = {
    spec.metric_code: {
        "canonical_name": spec.canonical_name,
        "metric_family": spec.metric_family,
    }
    for spec in METRIC_SPECS
}

ALIAS_TO_METRIC: Dict[str, str] = {}
for spec in METRIC_SPECS:
    for alias in spec.aliases:
        ALIAS_TO_METRIC[_normalize_label(alias)] = spec.metric_code


def _canonical_metric_name(metric_code: str, raw_metric_name: str) -> str:
    if metric_code in KNOWN_METRICS:
        return KNOWN_METRICS[metric_code]["canonical_name"]
    return raw_metric_name or UNKNOWN_METRIC_CODE


def _metric_family(metric_code: str) -> str:
    if metric_code in KNOWN_METRICS:
        return KNOWN_METRICS[metric_code]["metric_family"]
    return "other"


def _metric_code_is_known(metric_code: str) -> bool:
    return metric_code in KNOWN_METRICS


def _period_from_year(year_label: str) -> Tuple[str, str, List[str]]:
    tags: List[str] = []
    year_text = _norm(year_label).upper().replace("年", "")
    if not year_text:
        tags.append("YEAR_MISSING")
        return "", "unknown", tags
    match = YEAR_RULE.match(year_text)
    if not match:
        tags.append("INVALID_YEAR")
        return year_text, "unknown", tags
    suffix = (match.group(2) or "").upper()
    if suffix == "E":
        return f"{match.group(1)}E", "estimate", tags
    if suffix == "A":
        return f"{match.group(1)}A", "actual", tags
    return match.group(1), "actual", tags


def _derive_report_name(source_image_path: Optional[str], folder_name: str) -> str:
    if source_image_path:
        try:
            path = Path(source_image_path)
            if path.parent.name == "images" and len(path.parents) >= 3:
                return path.parents[2].name
            if len(path.parents) >= 1:
                return path.stem
        except Exception:
            pass
    return folder_name


def _extract_inline_unit(text: str) -> Optional[str]:
    for hint in ("元/股", "百万元", "亿元", "万元", "%", "元"):
        if hint in text:
            return hint
    return None


def _infer_currency(explicit_currency: Optional[str], text_parts: Sequence[str], unit: Optional[str]) -> Optional[str]:
    if explicit_currency:
        return explicit_currency
    joined = " ".join([_norm(part).lower() for part in text_parts if _norm(part)])
    if any(token in joined for token in ("人民币", "cny", "rmb")):
        return "CNY"
    if unit in {"元", "元/股", "万元", "百万元", "亿元"}:
        return "CNY"
    return None


def _infer_unit(
    metric_code: str,
    raw_metric_name: str,
    table_title: str,
    table_unit: Optional[str],
    raw_value: Any,
) -> Tuple[Optional[str], str, List[str]]:
    tags: List[str] = []
    label_text = _norm(raw_metric_name)
    title_text = _norm(table_title)
    inline_unit = _extract_inline_unit(label_text) or _extract_inline_unit(title_text)
    raw_value_text = _norm(raw_value)

    if "%" in raw_value_text:
        return "%", "VALUE_TOKEN", tags
    if inline_unit == "%":
        return "%", "ROW_LABEL", tags
    if metric_code in {"pe", "pb", "ev_ebitda"}:
        return "x", "METRIC_SEMANTIC", tags
    if metric_code in PER_SHARE_METRICS:
        if inline_unit in {"元/股", "元"}:
            return inline_unit, "ROW_LABEL", tags
        tags.append("UNIT_INFERRED_PER_SHARE")
        return "元/股", "METRIC_SEMANTIC", tags
    if metric_code in SAFE_RATIO_METRICS:
        return "%", "METRIC_SEMANTIC", tags
    if inline_unit in MONETARY_UNIT_HINTS:
        return inline_unit, "ROW_LABEL", tags
    if _optional_text(table_unit):
        return table_unit, "TABLE_UNIT", tags
    if metric_code == UNKNOWN_METRIC_CODE:
        tags.append("UNIT_UNKNOWN")
        return None, "UNKNOWN", tags
    tags.append("UNIT_UNKNOWN")
    return None, "UNKNOWN", tags


def _growth_metric_from_context(raw_metric_name: str, previous_metric_code: Optional[str], previous_metric_label: str) -> Optional[str]:
    normalized = _normalize_label(raw_metric_name)
    if normalized not in {
        "同比",
        "同比(%)",
        "同比增长率(%)",
        "增长率(%)",
        "yoy",
        "总yoy",
    }:
        return None
    context_code = previous_metric_code or ""
    context_label = _normalize_label(previous_metric_label)
    if context_code in {"parent_net_profit", "net_profit"} or "净利润" in context_label:
        return "net_profit_growth"
    return "revenue_growth"


def _map_metric_code(raw_metric_name: str, previous_metric_code: Optional[str], previous_metric_label: str) -> str:
    growth_metric = _growth_metric_from_context(raw_metric_name, previous_metric_code, previous_metric_label)
    if growth_metric:
        return growth_metric

    normalized = _normalize_label(raw_metric_name)
    if not normalized:
        return UNKNOWN_METRIC_CODE
    if normalized in ALIAS_TO_METRIC:
        return ALIAS_TO_METRIC[normalized]

    if "营业收入" in normalized or "营业总收入" in normalized:
        return "revenue"
    if "净利润增长率" in normalized:
        return "net_profit_growth"
    if normalized.endswith("毛利率") or "毛利率" in normalized:
        return "gross_margin"
    if normalized.endswith("增长率(%)") and ("收入" in previous_metric_label or "收入" in normalized):
        return "revenue_growth"
    return UNKNOWN_METRIC_CODE


def _build_candidate_id(
    source_stage: str,
    source_file: str,
    source_table_id: str,
    source_row_index: Any,
    metric_code: str,
    year: str,
    raw_value: Any,
) -> str:
    payload = "|".join(
        [
            _norm(source_stage),
            _norm(source_file),
            _norm(source_table_id),
            _norm(source_row_index),
            _norm(metric_code),
            _norm(year),
            _norm(raw_value),
        ]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:24]


def _table_inventory_lookup(table_inventory_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    if table_inventory_df.empty:
        return lookup
    for _, row in table_inventory_df.iterrows():
        row_dict = row.to_dict()
        folder_name = _norm(row_dict.get("table_folder"))
        if not folder_name:
            continue
        lookup[folder_name] = row_dict
    return lookup


def _normalize_table_decision(table_row: Dict[str, Any]) -> Tuple[str, str, bool]:
    decision = _norm(table_row.get("current_decision"))
    main_issue = _norm(table_row.get("main_issue"))
    is_ready = decision == "VLM_TABLE_READY_FOR_MAPPING"
    return decision, main_issue, is_ready


def map_vlm_outputs_to_candidates(
    folder_records: Sequence[VLMFolderRecord],
    table_inventory_df: pd.DataFrame,
) -> Dict[str, Any]:
    inventory_lookup = _table_inventory_lookup(table_inventory_df)
    normalized_rows: List[Dict[str, Any]] = []
    candidates: List[MetricCandidate] = []
    mapping_audit_rows: List[Dict[str, Any]] = []
    table_summary_rows: List[Dict[str, Any]] = []

    for record in folder_records:
        source_image_path = _optional_text(record.table_meta.get("source_image_path"))
        report_name = _derive_report_name(source_image_path, record.folder_name)
        inventory_row = inventory_lookup.get(record.folder_name, {})
        quality_decision, quality_issue, table_ready = _normalize_table_decision(inventory_row)

        if not record.parse_success or record.table is None:
            table_summary_rows.append(
                {
                    "table_folder": record.folder_name,
                    "report_name": report_name,
                    "table_title": "",
                    "quality_decision": quality_decision or "VLM_PARSE_FAILED",
                    "main_issue": quality_issue or record.parse_error or "NO_PARSEABLE_JSON_FOUND",
                    "mapped_row_count": 0,
                    "candidate_count": 0,
                }
            )
            continue

        table = record.table
        previous_metric_code: Optional[str] = None
        previous_metric_label = ""
        table_candidate_start = len(candidates)
        table_row_start = len(normalized_rows)

        for row in table.rows:
            raw_metric_name = _optional_text(row.metric_name_cn) or _optional_text(row.metric_name_raw) or _optional_text(row.row_name) or ""
            if not raw_metric_name:
                raw_metric_name = ""
            metric_code = _map_metric_code(raw_metric_name, previous_metric_code, previous_metric_label)
            metric_name_known = _metric_code_is_known(metric_code)
            row_any_value = any(
                (_optional_text(cell.raw_value) is not None) or (cell.normalized_value is not None)
                for cell in row.values
            )
            row_all_values_missing = not row_any_value
            row_confidence = float(row.confidence) if row.confidence is not None else 1.0

            if row_any_value:
                previous_metric_code = metric_code if metric_code != UNKNOWN_METRIC_CODE else previous_metric_code
                previous_metric_label = raw_metric_name or previous_metric_label

            for cell in row.values:
                year_norm, period_type, year_tags = _period_from_year(cell.column)
                parsed_value = _as_float(cell.normalized_value)
                if parsed_value is None and not _meaningless_raw_value(cell.raw_value):
                    parsed_value = _as_float(cell.raw_value)
                unit, unit_source, unit_tags = _infer_unit(
                    metric_code=metric_code,
                    raw_metric_name=raw_metric_name,
                    table_title=_norm(table.table_title),
                    table_unit=table.unit,
                    raw_value=cell.raw_value,
                )
                currency = _infer_currency(
                    explicit_currency=_optional_text(table.currency),
                    text_parts=[raw_metric_name, _norm(table.table_title), _norm(table.unit)],
                    unit=unit,
                )

                normalized_row = {
                    "table_folder": record.folder_name,
                    "report_name": report_name,
                    "source_json_path": record.source_json_path or "",
                    "source_image_path": source_image_path or "",
                    "table_title": _norm(table.table_title),
                    "table_unit": _norm(table.unit),
                    "table_currency": _norm(table.currency),
                    "schema_shape": table.schema_shape,
                    "quality_decision": quality_decision,
                    "quality_main_issue": quality_issue,
                    "table_ready_321a": table_ready,
                    "row_index": row.row_index,
                    "source_row_index": row.source_row_index if row.source_row_index is not None else row.row_index + 1,
                    "raw_metric_name": raw_metric_name,
                    "metric_name_cn": _norm(row.metric_name_cn),
                    "metric_code": metric_code,
                    "metric_family": _metric_family(metric_code),
                    "metric_name_known": metric_name_known,
                    "year": year_norm,
                    "period_type": period_type,
                    "column_label": cell.column,
                    "source_column_label": _norm(cell.source_column_label),
                    "raw_value": cell.raw_value,
                    "normalized_value": parsed_value,
                    "unit": unit or "",
                    "unit_source": unit_source,
                    "currency": currency or "",
                    "row_confidence": row_confidence,
                    "row_uncertain": bool(row.uncertain),
                    "row_warnings": "|".join(row.warnings),
                    "row_schema_errors": "|".join(row.schema_errors),
                    "table_warnings": "|".join(table.table_warnings),
                    "year_tags": "|".join(year_tags),
                    "unit_tags": "|".join(unit_tags),
                    "row_all_values_missing": row_all_values_missing,
                    "candidate_should_exist": row_any_value,
                }
                normalized_rows.append(normalized_row)

                if not row_any_value:
                    continue

                risk_tags: List[str] = []
                if metric_code == UNKNOWN_METRIC_CODE:
                    risk_tags.append("UNKNOWN_METRIC_CODE")
                risk_tags.extend(year_tags)
                risk_tags.extend(unit_tags)
                if _contains_corruption(raw_metric_name):
                    risk_tags.append("CHINESE_LABEL_CORRUPTED")
                if parsed_value is None:
                    if _meaningless_raw_value(cell.raw_value):
                        risk_tags.append("VALUE_MISSING")
                    else:
                        risk_tags.append("VALUE_PARSE_FAILED")
                if quality_decision and quality_decision != "VLM_TABLE_READY_FOR_MAPPING":
                    risk_tags.append("TABLE_NOT_READY_321A")
                if table.schema_errors or row.schema_errors:
                    risk_tags.append("SCHEMA_REVIEW_REQUIRED")
                if table.table_warnings or row.warnings:
                    risk_tags.extend([warning for warning in table.table_warnings if _norm(warning)])
                    risk_tags.extend([warning for warning in row.warnings if _norm(warning)])
                if bool(row.uncertain):
                    risk_tags.append("VLM_ROW_UNCERTAIN")
                if row_confidence < 0.80:
                    risk_tags.append("LOW_CONFIDENCE")

                source_row_index = row.source_row_index if row.source_row_index is not None else row.row_index + 1
                candidate_id = _build_candidate_id(
                    source_stage="vlm_strict_json_321a_rerun",
                    source_file=source_image_path or record.folder_path,
                    source_table_id=record.folder_name,
                    source_row_index=source_row_index,
                    metric_code=metric_code,
                    year=year_norm,
                    raw_value=cell.raw_value,
                )
                candidate = MetricCandidate(
                    candidate_id=candidate_id,
                    source_stage="vlm_strict_json_321a_rerun",
                    source_file=source_image_path or record.folder_path,
                    source_doc_name=report_name,
                    source_table_id=record.folder_name,
                    source_row_index=source_row_index,
                    source_row_text=raw_metric_name,
                    metric_code=metric_code,
                    canonical_metric_name=_canonical_metric_name(metric_code, raw_metric_name),
                    raw_metric_name=raw_metric_name,
                    year=year_norm,
                    period_type=period_type,
                    raw_value=_norm(cell.raw_value),
                    normalized_value=parsed_value,
                    unit=unit,
                    unit_source=unit_source,
                    currency=currency,
                    confidence=row_confidence,
                    year_source="TABLE_HEADER" if not year_tags else "INVALID",
                    smoke_check_status="NOT_APPLICABLE",
                    smoke_check_source="",
                    table_title=_optional_text(table.table_title),
                    table_unit=_optional_text(table.unit),
                    risk_tags=sorted(set([tag for tag in risk_tags if _norm(tag)])),
                    split_decision="review_required_preview",
                    split_reason="PENDING_VLM_TRUST_SPLIT",
                    provenance_json={
                        "source_candidate_row_id": candidate_id,
                        "source_json_path": record.source_json_path or "",
                        "source_image_path": source_image_path or "",
                        "table_folder": record.folder_name,
                        "report_name": report_name,
                        "table_title": _norm(table.table_title),
                        "table_unit": _norm(table.unit),
                        "table_currency": _norm(table.currency),
                        "schema_shape": table.schema_shape,
                        "quality_decision": quality_decision,
                        "quality_main_issue": quality_issue,
                        "row_warnings": list(row.warnings),
                        "table_warnings": list(table.table_warnings),
                        "row_schema_errors": list(row.schema_errors),
                        "table_schema_errors": list(table.schema_errors),
                        "source_row_index": source_row_index,
                        "source_column_label": _norm(cell.source_column_label) or cell.column,
                        "year_source": "TABLE_HEADER" if not year_tags else "INVALID",
                        "unit_source": unit_source,
                    },
                )
                candidates.append(candidate)
                mapping_audit_rows.append(
                    {
                        "candidate_id": candidate.candidate_id,
                        "table_folder": record.folder_name,
                        "report_name": report_name,
                        "raw_metric_name": raw_metric_name,
                        "metric_code": metric_code,
                        "metric_family": _metric_family(metric_code),
                        "year": year_norm,
                        "raw_value": _norm(cell.raw_value),
                        "normalized_value": parsed_value,
                        "unit": unit or "",
                        "unit_source": unit_source,
                        "risk_tags": "|".join(candidate.risk_tags),
                        "quality_decision": quality_decision,
                    }
                )

        table_summary_rows.append(
            {
                "table_folder": record.folder_name,
                "report_name": report_name,
                "table_title": _norm(table.table_title),
                "quality_decision": quality_decision,
                "main_issue": quality_issue,
                "mapped_row_count": len(normalized_rows) - table_row_start,
                "candidate_count": len(candidates) - table_candidate_start,
            }
        )

    return {
        "normalized_rows": normalized_rows,
        "candidates": candidates,
        "mapping_audit_rows": mapping_audit_rows,
        "table_mapping_summary_rows": table_summary_rows,
    }


def resolve_vlm_duplicates_and_conflicts(candidates: Sequence[MetricCandidate]) -> Dict[str, Any]:
    grouped: Dict[Tuple[str, str, str, str], List[MetricCandidate]] = {}
    for candidate in candidates:
        metric_key = candidate.metric_code if candidate.metric_code != UNKNOWN_METRIC_CODE else candidate.raw_metric_name
        group_key = (candidate.source_file, candidate.source_table_id or "", metric_key, candidate.year)
        grouped.setdefault(group_key, []).append(candidate)

    canonical_candidates: List[MetricCandidate] = []
    duplicate_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []
    conflict_group_count = 0

    for group_key, rows in grouped.items():
        if len(rows) == 1:
            canonical_candidates.append(rows[0])
            continue

        unique_values = sorted(set(["" if row.normalized_value is None else str(row.normalized_value) for row in rows]))
        if len(unique_values) == 1:
            rows_sorted = sorted(rows, key=lambda row: (-row.confidence, row.candidate_id))
            keep = rows_sorted[0]
            keep.risk_tags = sorted(set(keep.risk_tags + ["DUPLICATE_SAME_VALUE_COLLAPSED"]))
            canonical_candidates.append(keep)
            for dropped in rows_sorted[1:]:
                dropped.split_decision = "rejected_preview"
                dropped.split_reason = "DUPLICATE_SAME_VALUE_COLLAPSED"
                duplicate_rows.append(
                    {
                        "group_key": "|".join(group_key),
                        "kept_candidate_id": keep.candidate_id,
                        "dropped_candidate_id": dropped.candidate_id,
                        "metric_code": dropped.metric_code,
                        "raw_metric_name": dropped.raw_metric_name,
                        "year": dropped.year,
                        "normalized_value": dropped.normalized_value,
                        "drop_reason": "DUPLICATE_SAME_VALUE_COLLAPSED",
                    }
                )
            continue

        conflict_group_count += 1
        for row in rows:
            row.risk_tags = sorted(set(row.risk_tags + ["VALUE_CONFLICT"]))
            canonical_candidates.append(row)
            conflict_rows.append(
                {
                    "group_key": "|".join(group_key),
                    "candidate_id": row.candidate_id,
                    "metric_code": row.metric_code,
                    "raw_metric_name": row.raw_metric_name,
                    "year": row.year,
                    "normalized_value": row.normalized_value,
                    "confidence": row.confidence,
                    "risk_tags": "|".join(row.risk_tags),
                }
            )

    return {
        "canonical_candidates": canonical_candidates,
        "duplicate_rows": duplicate_rows,
        "conflict_rows": conflict_rows,
        "conflict_group_count": conflict_group_count,
    }


def split_vlm_candidates_for_sandbox_preview(candidates: Iterable[MetricCandidate]) -> Dict[str, Any]:
    trusted: List[MetricCandidate] = []
    review_required: List[MetricCandidate] = []
    rejected: List[MetricCandidate] = []
    audit_rows: List[Dict[str, Any]] = []

    for candidate in candidates:
        tags = set(candidate.risk_tags)

        def _final(decision: str, reason: str, bucket: List[MetricCandidate]) -> None:
            candidate.split_decision = decision
            candidate.split_reason = reason
            bucket.append(candidate)
            audit_rows.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "table_folder": _norm(candidate.source_table_id),
                    "report_name": _norm(candidate.source_doc_name),
                    "metric_code": candidate.metric_code,
                    "raw_metric_name": candidate.raw_metric_name,
                    "year": candidate.year,
                    "normalized_value": candidate.normalized_value,
                    "confidence": candidate.confidence,
                    "decision": decision,
                    "reason": reason,
                    "risk_tags": "|".join(candidate.risk_tags),
                }
            )

        if candidate.split_decision == "rejected_preview" and candidate.split_reason == "DUPLICATE_SAME_VALUE_COLLAPSED":
            _final("rejected_preview", "DUPLICATE_SAME_VALUE_COLLAPSED", rejected)
            continue

        if any(tag in tags for tag in {"NOT_A_TABLE", "CHINESE_LABEL_CORRUPTED", "INVALID_JSON_SCHEMA_SEVERE", "MEANINGLESS_VALUE"}):
            _final("rejected_preview", "STRICT_REJECT_TAG", rejected)
            continue

        if any(tag in tags for tag in {"UNKNOWN_METRIC_CODE", "TABLE_NOT_READY_321A", "SCHEMA_REVIEW_REQUIRED", "VLM_ROW_UNCERTAIN", "LOW_CONFIDENCE", "VALUE_CONFLICT", "INVALID_YEAR", "YEAR_MISSING", "VALUE_MISSING", "VALUE_PARSE_FAILED"}):
            _final("review_required_preview", "HAS_VLM_REVIEW_TAG", review_required)
            continue

        if candidate.normalized_value is None:
            _final("review_required_preview", "VALUE_MISSING_OR_INVALID", review_required)
            continue

        if candidate.metric_code == UNKNOWN_METRIC_CODE:
            _final("review_required_preview", "UNKNOWN_METRIC_CODE", review_required)
            continue

        if candidate.year_source != "TABLE_HEADER":
            _final("review_required_preview", "INVALID_OR_NON_HEADER_YEAR", review_required)
            continue

        if not candidate.unit and candidate.metric_code not in SAFE_RATIO_METRICS and candidate.metric_code not in PER_SHARE_METRICS:
            _final("review_required_preview", "UNIT_UNKNOWN", review_required)
            continue

        if candidate.confidence < 0.80:
            _final("review_required_preview", "LOW_CONFIDENCE_GATE", review_required)
            continue

        _final("trusted_preview", "PASS_VLM_TRUST_GATE", trusted)

    return {
        "trusted_preview": trusted,
        "review_required_preview": review_required,
        "rejected_preview": rejected,
        "trust_gate_audit_rows": audit_rows,
    }


def candidates_to_dataframe(candidates: Iterable[MetricCandidate]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for candidate in candidates:
        candidate_dict = candidate.to_dict()
        candidate_dict["risk_tags"] = "|".join(candidate.risk_tags)
        candidate_dict["provenance_json"] = json.dumps(candidate.provenance_json, ensure_ascii=False)
        candidate_dict["metric_family"] = _metric_family(candidate.metric_code)
        rows.append(candidate_dict)
    return pd.DataFrame(rows)
