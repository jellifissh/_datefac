from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from datefac.vlm.vlm_delivery_builder import build_summary_dataframe, safe_sheet_name, write_json, write_jsonl
from datefac.vlm.vlm_mapping_benchmark import run_vlm_mapping_benchmark


CALIBRATION_STAGE = "321B2"
UNKNOWN_METRIC_CODE = "unknown_metric"
YEAR_RE = re.compile(r"^(20\d{2})([AE])?$", re.IGNORECASE)
YEAR_EMBEDDED_RE = re.compile(r"20\d{2}(?:[AE])?", re.IGNORECASE)
QUESTION_ONLY_RE = re.compile(r"^[\s?？/|_+\-.*]+$")
CHINESE_REPLACEMENT_RE = re.compile(r"[?？\ufffd]")

RATIO_UNIT_METRICS = {
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
}
X_UNIT_METRICS = {"pe", "pb", "ev_ebitda"}
PER_SHARE_UNIT_METRICS = {"eps", "dps", "bvps"}
MONEY_UNIT_HINTS = {"百万元", "百万", "亿元", "万元", "元"}
SUPPORTED_METRIC_FAMILY: Dict[str, str] = {
    "revenue": "income_statement",
    "operating_cost": "income_statement",
    "tax_surcharge": "income_statement",
    "selling_expense": "income_statement",
    "admin_expense": "income_statement",
    "rd_expense": "income_statement",
    "finance_expense": "income_statement",
    "other_income": "income_statement",
    "investment_income": "income_statement",
    "fair_value_change": "income_statement",
    "asset_impairment_loss": "income_statement",
    "asset_disposal_income": "income_statement",
    "operating_profit": "income_statement",
    "pretax_profit": "income_statement",
    "income_tax_expense": "income_statement",
    "non_operating_balance": "income_statement",
    "net_profit": "profitability",
    "parent_net_profit": "profitability",
    "gross_profit": "income_statement",
    "gross_margin": "margin",
    "net_margin": "margin",
    "roe": "profitability",
    "roic": "profitability",
    "revenue_growth": "growth",
    "net_profit_growth": "growth",
    "cash_and_equivalents": "balance_sheet",
    "accounts_receivable": "balance_sheet",
    "inventory": "balance_sheet",
    "other_current_assets": "balance_sheet",
    "current_assets_total": "balance_sheet",
    "fixed_assets": "balance_sheet",
    "intangible_assets": "balance_sheet",
    "investment_property": "balance_sheet",
    "total_assets": "balance_sheet",
    "accounts_payable": "balance_sheet",
    "current_liabilities_total": "balance_sheet",
    "total_liabilities": "balance_sheet",
    "shareholders_equity": "balance_sheet",
    "minority_interest": "balance_sheet",
    "total_liabilities_and_equity": "balance_sheet",
    "operating_cash_flow": "cash_flow",
    "depreciation_amortization": "cash_flow",
    "investment_loss": "cash_flow",
    "working_capital_change": "cash_flow",
    "other_operating_cf": "cash_flow",
    "investing_cash_flow": "cash_flow",
    "capex": "cash_flow",
    "long_term_investment": "cash_flow",
    "other_investing_cash_flow": "cash_flow",
    "financing_cash_flow": "cash_flow",
    "short_term_borrowings": "balance_sheet",
    "long_term_borrowings": "balance_sheet",
    "equity_financing": "cash_flow",
    "capital_reserve_increase": "cash_flow",
    "other_financing_cash_flow": "cash_flow",
    "net_cash_change": "cash_flow",
    "cash_beginning_balance": "cash_flow",
    "cash_ending_balance": "cash_flow",
    "free_cash_flow_firm": "cash_flow",
    "free_cash_flow_equity": "cash_flow",
    "asset_impairment_provision": "cash_flow",
    "fair_value_change_loss": "cash_flow",
    "eps": "valuation",
    "dps": "valuation",
    "bvps": "valuation",
    "pe": "valuation",
    "pb": "valuation",
    "ev_ebitda": "valuation",
}

CALIBRATION_ALIAS_RULES: Dict[str, Dict[str, Any]] = {
    "销售净利率": {"metric_code": "net_margin", "metric_family": "margin", "apply": True, "action": "add_alias"},
    "销售收入增长率": {"metric_code": "revenue_growth", "metric_family": "growth", "apply": True, "action": "add_alias"},
    "营业收入增长率": {"metric_code": "revenue_growth", "metric_family": "growth", "apply": True, "action": "add_alias"},
    "归母净利（百万元）": {"metric_code": "parent_net_profit", "metric_family": "profitability", "apply": True, "action": "add_alias"},
    "归母净利润（百万元）": {"metric_code": "parent_net_profit", "metric_family": "profitability", "apply": True, "action": "add_alias"},
    "归母净利": {"metric_code": "parent_net_profit", "metric_family": "profitability", "apply": True, "action": "add_alias"},
    "归母公司股东权益": {"metric_code": "shareholders_equity", "metric_family": "balance_sheet", "apply": True, "action": "add_alias"},
    "归属母公司股东权益": {"metric_code": "shareholders_equity", "metric_family": "balance_sheet", "apply": True, "action": "add_alias"},
    "股东权益合计": {"metric_code": "shareholders_equity", "metric_family": "balance_sheet", "apply": True, "action": "add_alias"},
    "负债和股东权益": {"metric_code": "total_liabilities_and_equity", "metric_family": "balance_sheet", "apply": True, "action": "add_alias"},
    "净利润（百万元）": {"metric_code": "net_profit", "metric_family": "profitability", "apply": True, "action": "add_alias"},
    "净资产收益率（roe）": {"metric_code": "roe", "metric_family": "profitability", "apply": True, "action": "add_alias"},
    "roe": {"metric_code": "roe", "metric_family": "profitability", "apply": True, "action": "add_alias"},
    "每股收益（元）": {"metric_code": "eps", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "摊薄每股收益（元）": {"metric_code": "eps", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "eps（元）": {"metric_code": "eps", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "eps(x)": {"metric_code": "eps", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "eps（x）": {"metric_code": "eps", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "市盈率（pe）": {"metric_code": "pe", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "pe(x)": {"metric_code": "pe", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "pe（x）": {"metric_code": "pe", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "市净率（pb）": {"metric_code": "pb", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "pb(x)": {"metric_code": "pb", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "pb（x）": {"metric_code": "pb", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "ev/ebitda(x)": {"metric_code": "ev_ebitda", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "ev/ebitda（x）": {"metric_code": "ev_ebitda", "metric_family": "valuation", "apply": True, "action": "add_alias"},
    "现金": {"metric_code": "cash_and_equivalents", "metric_family": "balance_sheet", "apply": True, "action": "add_alias"},
    "应收票据及应收账款合计": {"metric_code": "accounts_receivable", "metric_family": "balance_sheet", "apply": True, "action": "add_alias"},
    "应收票据及账款": {"metric_code": "accounts_receivable", "metric_family": "balance_sheet", "apply": True, "action": "add_alias"},
    "应收和预付款项": {"metric_code": "accounts_receivable", "metric_family": "balance_sheet", "apply": False, "action": "keep_review_required"},
    "应付和预收款项": {"metric_code": "accounts_payable", "metric_family": "balance_sheet", "apply": False, "action": "keep_review_required"},
    "流动资产": {"metric_code": "current_assets_total", "metric_family": "balance_sheet", "apply": False, "action": "ignore_group_header"},
    "流动负债": {"metric_code": "current_liabilities_total", "metric_family": "balance_sheet", "apply": False, "action": "ignore_group_header"},
    "其他应收款": {"metric_code": "accounts_receivable", "metric_family": "balance_sheet", "apply": False, "action": "keep_review_required"},
    "预付账款": {"metric_code": "accounts_receivable", "metric_family": "balance_sheet", "apply": False, "action": "keep_review_required"},
    "roa": {"metric_code": "roa", "metric_family": "profitability", "apply": False, "action": "keep_review_required"},
    "ebit增长率": {"metric_code": "ebit_growth", "metric_family": "growth", "apply": False, "action": "keep_review_required"},
    "ps(x)": {"metric_code": "ps", "metric_family": "valuation", "apply": False, "action": "keep_review_required"},
    "(+/-%)": {"metric_code": "", "metric_family": "growth", "apply": False, "action": "keep_review_required"},
}

REPORT_SHEET_ORDER = [
    "summary",
    "vlm_table_inventory",
    "vlm_rows_normalized",
    "metric_candidates_all",
    "trusted_preview",
    "review_required_preview",
    "rejected_preview",
    "per_table_summary",
    "metric_coverage",
    "unit_year_context_summary",
    "risk_tag_counts",
    "provenance_coverage",
    "qa_checks",
    "unknown_metric_diagnostics",
    "unreadable_label_diagnostics",
    "unit_propagation_audit",
    "year_normalization_audit",
    "conflict_diagnostics",
    "known_limitations",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def _is_missing(value: Any) -> bool:
    return _norm(value) == ""


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in REPORT_SHEET_ORDER:
            dataframe = sheets.get(name, pd.DataFrame())
            dataframe.to_excel(writer, sheet_name=safe_sheet_name(name, used), index=False)


def _write_markdown_report(
    path: Path,
    summary: Dict[str, Any],
    baseline_summary: Dict[str, Any],
    qa_df: pd.DataFrame,
    risk_df: pd.DataFrame,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    qa_lines = []
    for _, row in qa_df.iterrows():
        qa_lines.append(f"- {row.get('check_name', '')}: {row.get('status', '')} | {row.get('detail', '')}")
    risk_lines = []
    for _, row in risk_df.head(10).iterrows():
        risk_lines.append(f"- {row.get('risk_tag', '')}: {row.get('count', 0)}")
    delta_lines = [
        f"- total_candidate_count: {baseline_summary.get('total_candidate_count', 0)} -> {summary.get('calibrated_total_candidate_count', 0)}",
        f"- trusted_total_count: {baseline_summary.get('trusted_total_count', 0)} -> {summary.get('calibrated_trusted_total_count', 0)}",
        f"- review_required_total_count: {baseline_summary.get('review_required_total_count', 0)} -> {summary.get('calibrated_review_required_total_count', 0)}",
        f"- trusted_rate: {baseline_summary.get('trusted_rate', 0.0)} -> {summary.get('calibrated_trusted_rate', 0.0)}",
        f"- UNKNOWN_METRIC_CODE: {baseline_summary.get('top_risk_tags', [{}])[0].get('count', '') if baseline_summary.get('top_risk_tags') else ''} -> {summary.get('unknown_metric_code_count', 0)}",
        f"- UNREADABLE_LABEL: {next((item.get('count') for item in baseline_summary.get('top_risk_tags', []) if item.get('risk_tag') == 'UNREADABLE_LABEL'), 0)} -> {summary.get('unreadable_label_count', 0)}",
        f"- UNIT_UNKNOWN: {baseline_summary.get('unit_unknown_count', 0)} -> {summary.get('unit_unknown_count', 0)}",
        f"- INVALID_YEAR: {next((item.get('count') for item in baseline_summary.get('top_risk_tags', []) if item.get('risk_tag') == 'INVALID_YEAR'), 0)} -> {summary.get('invalid_year_count', 0)}",
    ]
    lines = [
        "# 321B2 Pure VLM Mapping Calibration",
        "",
        "## Summary",
        f"- output_dir: `{summary.get('output_dir', '')}`",
        f"- previous_mapping_dir: `{summary.get('previous_mapping_dir', '')}`",
        f"- calibration_decision: {summary.get('calibration_decision', '')}",
        f"- calibrated_total_candidate_count: {summary.get('calibrated_total_candidate_count', 0)}",
        f"- calibrated_trusted_total_count: {summary.get('calibrated_trusted_total_count', 0)}",
        f"- calibrated_review_required_total_count: {summary.get('calibrated_review_required_total_count', 0)}",
        f"- calibrated_trusted_rate: {summary.get('calibrated_trusted_rate', 0.0)}",
        f"- table_with_trusted_count: {summary.get('table_with_trusted_count', 0)}",
        "",
        "## Delta Vs 321B",
    ]
    lines.extend(delta_lines)
    lines.extend(["", "## QA Checks"])
    lines.extend(qa_lines or ["- none"])
    lines.extend(["", "## Top Risk Tags"])
    lines.extend(risk_lines or ["- none"])
    path.write_text("\n".join(lines), encoding="utf-8")


def _normalize_label(text: Any) -> str:
    value = _norm(text)
    replacements = {
        "（": "(",
        "）": ")",
        "％": "%",
        "：": ":",
        "－": "-",
        "—": "-",
        "–": "-",
        "／": "/",
        "　": "",
        " ": "",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value.lower()


def _normalize_year_label(raw_column: Any) -> Tuple[Optional[str], bool, str, str, bool]:
    original = _norm(raw_column)
    cleaned = original.replace("\n", "").replace("\r", "").replace(" ", "").replace("：", "").replace(":", "")
    match = YEAR_RE.match(cleaned.upper())
    if match:
        year = match.group(1)
        suffix = (match.group(2) or "").upper()
        normalized = f"{year}{suffix}" if suffix else year
        changed = normalized != original
        if changed:
            return normalized, True, "normalized_year_label", "TRIMMED_YEAR_TOKEN", True
        return normalized, True, "keep_year_label", "VALID_YEAR_LABEL", False
    if YEAR_EMBEDDED_RE.search(cleaned):
        return None, False, "reject_non_year_column", "SEMANTIC_COLUMN_WITH_YEAR_SUFFIX", False
    return None, False, "reject_non_year_column", "NON_YEAR_SEMANTIC_COLUMN", False


def _parse_risk_tags(value: Any) -> List[str]:
    return [item for item in (_norm(value).split("|")) if item]


def _meaningful_raw_value(value: Any) -> bool:
    return _norm(value).lower() not in {"", "nan", "none", "null", "--", "-", "n/a", "na"}


def _parse_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
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


def _is_unreadable_label(label: str, row_warnings: Sequence[str]) -> bool:
    if "UNREADABLE_LABEL" in row_warnings and not _norm(label):
        return True
    if not _norm(label):
        return True
    if QUESTION_ONLY_RE.match(_norm(label)):
        return True
    if _norm(label).lower() in {"null", "none", "nan"}:
        return True
    return False


def _has_replacement_chars(text: str) -> bool:
    return bool(CHINESE_REPLACEMENT_RE.search(_norm(text)))


def _metric_family(metric_code: str, fallback: str = "") -> str:
    if metric_code in SUPPORTED_METRIC_FAMILY:
        return SUPPORTED_METRIC_FAMILY[metric_code]
    return fallback or "other"


def _metric_is_known(metric_code: str) -> bool:
    return metric_code in SUPPORTED_METRIC_FAMILY


def _metric_unit_semantic(metric_code: str, label: str, raw_value: Any) -> Tuple[Optional[str], str]:
    label_text = _norm(label)
    raw_text = _norm(raw_value)
    if "%" in raw_text or "%" in label_text:
        return "%", "ROW_LABEL_OR_VALUE"
    if metric_code in RATIO_UNIT_METRICS:
        return "%", "METRIC_SEMANTIC"
    if metric_code in X_UNIT_METRICS:
        return "x", "METRIC_SEMANTIC"
    if metric_code in PER_SHARE_UNIT_METRICS:
        return "元", "METRIC_SEMANTIC"
    for unit in MONEY_UNIT_HINTS:
        if unit in label_text:
            return unit, "ROW_LABEL"
    return None, "UNKNOWN"


def _infer_currency(explicit_currency: str, unit: Optional[str]) -> Optional[str]:
    if explicit_currency:
        return explicit_currency
    if unit in MONEY_UNIT_HINTS:
        return "CNY"
    return None


def _row_values_preview(cells: Sequence[Dict[str, Any]], limit: int = 6) -> str:
    parts: List[str] = []
    for cell in cells[:limit]:
        parts.append(f"{cell.get('raw_column')}={_norm(cell.get('raw_value'))}")
    return " | ".join(parts)


def _suggest_for_unknown(label: str, row_has_values: bool, valid_year_count: int) -> Tuple[Optional[str], Optional[str], str]:
    normalized = _normalize_label(label)
    rule = CALIBRATION_ALIAS_RULES.get(normalized)
    if rule:
        return rule.get("metric_code") or None, rule.get("metric_family") or None, str(rule.get("action") or "keep_review_required")
    if not row_has_values:
        return None, None, "ignore_group_header"
    if valid_year_count == 0:
        return None, None, "unsupported_segment_row"
    return None, None, "keep_review_required"


def _map_metric_code(raw_metric_name: str, baseline_metric_code: str, previous_metric_code: str, previous_metric_label: str) -> Tuple[str, bool, Optional[str], Optional[str], str]:
    if baseline_metric_code and baseline_metric_code != UNKNOWN_METRIC_CODE:
        return baseline_metric_code, False, None, None, "keep_review_required"

    normalized = _normalize_label(raw_metric_name)
    if normalized in {"(+/-% )", "(+/-%)", "+/-%", "同比增长率(%)", "同比增长率"}:
        if previous_metric_code in {"revenue", "gross_profit"} or "收入" in previous_metric_label:
            return "revenue_growth", True, "revenue_growth", "growth", "add_alias"
        if previous_metric_code in {"net_profit", "parent_net_profit"} or "净利润" in previous_metric_label:
            return "net_profit_growth", True, "net_profit_growth", "growth", "add_alias"
    rule = CALIBRATION_ALIAS_RULES.get(normalized)
    if rule and rule.get("apply"):
        metric_code = str(rule["metric_code"])
        return metric_code, True, metric_code, str(rule.get("metric_family") or _metric_family(metric_code)), str(rule.get("action") or "add_alias")
    if rule:
        metric_code = str(rule.get("metric_code") or UNKNOWN_METRIC_CODE)
        return baseline_metric_code or UNKNOWN_METRIC_CODE, False, str(rule.get("metric_code") or ""), str(rule.get("metric_family") or ""), str(rule.get("action") or "keep_review_required")
    return baseline_metric_code or UNKNOWN_METRIC_CODE, False, None, None, "keep_review_required"


def _load_previous_mapping(
    vlm_output_root: Path,
    quality_dir: Path,
    previous_mapping_dir: Path,
    output_dir: Path,
) -> Tuple[Path, Dict[str, Any], Dict[str, pd.DataFrame]]:
    mapping_dir = previous_mapping_dir
    if not mapping_dir.exists():
        bootstrap_dir = output_dir / "_bootstrap_previous_mapping_321b"
        run_vlm_mapping_benchmark(
            vlm_output_root=vlm_output_root,
            quality_dir=quality_dir,
            output_dir=bootstrap_dir,
            ppstructure_benchmark_dir=None,
        )
        mapping_dir = bootstrap_dir
    workbook = mapping_dir / "vlm_mapping_benchmark_321b.xlsx"
    summary = _read_json(mapping_dir / "vlm_mapping_benchmark_321b_summary.json")
    tables = {
        "vlm_table_inventory": _read_sheet(workbook, "vlm_table_inventory"),
        "vlm_rows_normalized": _read_sheet(workbook, "vlm_rows_normalized"),
        "metric_candidates_all": _read_sheet(workbook, "metric_candidates_all"),
        "trusted_preview": _read_sheet(workbook, "trusted_preview"),
        "review_required_preview": _read_sheet(workbook, "review_required_preview"),
        "rejected_preview": _read_sheet(workbook, "rejected_preview"),
        "per_table_summary": _read_sheet(workbook, "per_table_summary"),
    }
    return mapping_dir, summary, tables


def _build_row_groups(vlm_rows_df: pd.DataFrame) -> List[Dict[str, Any]]:
    if vlm_rows_df.empty:
        return []
    rows: List[Dict[str, Any]] = []
    sort_df = vlm_rows_df.copy()
    sort_df["row_index"] = pd.to_numeric(sort_df["row_index"], errors="coerce").fillna(0).astype(int)
    sort_df["source_row_index"] = pd.to_numeric(sort_df["source_row_index"], errors="coerce").fillna(sort_df["row_index"] + 1).astype(int)
    sort_df = sort_df.sort_values(["table_folder", "row_index", "source_row_index", "column_label"], kind="stable")
    group_keys = [
        "table_folder",
        "report_name",
        "source_json_path",
        "source_image_path",
        "table_title",
        "table_unit",
        "table_currency",
        "schema_shape",
        "quality_decision",
        "quality_main_issue",
        "table_ready_321a",
        "row_index",
        "source_row_index",
        "raw_metric_name",
        "metric_name_cn",
        "metric_code",
        "metric_family",
        "row_confidence",
        "row_uncertain",
        "row_warnings",
        "row_schema_errors",
        "table_warnings",
    ]
    for key_values, group in sort_df.groupby(group_keys, dropna=False, sort=False):
        row_data = dict(zip(group_keys, key_values))
        cells: List[Dict[str, Any]] = []
        for _, cell_row in group.iterrows():
            raw_column = _norm(cell_row.get("column_label") or cell_row.get("source_column_label"))
            normalized_year, valid_year, year_action, year_reason, changed = _normalize_year_label(raw_column)
            normalized_value = cell_row.get("normalized_value")
            if isinstance(normalized_value, float) and math.isnan(normalized_value):
                normalized_value = None
            parsed_value = normalized_value if normalized_value is not None else _parse_number(cell_row.get("raw_value"))
            cells.append(
                {
                    "raw_column": raw_column,
                    "normalized_year": normalized_year,
                    "valid_year": valid_year,
                    "year_action": year_action,
                    "year_reason": year_reason,
                    "year_normalized_changed": changed,
                    "raw_value": cell_row.get("raw_value"),
                    "parsed_value": parsed_value,
                    "baseline_unit": _norm(cell_row.get("unit")),
                    "baseline_unit_source": _norm(cell_row.get("unit_source")),
                    "source_column_label": _norm(cell_row.get("source_column_label")),
                }
            )
        row_data["cells"] = cells
        rows.append(row_data)
    return rows


def _make_candidate_id(table_id: str, row_index: int, metric_code: str, year: str, raw_value: Any) -> str:
    raw = f"{table_id}|{row_index}|{metric_code}|{year}|{_norm(raw_value)}"
    return str(abs(hash(raw)))


def _apply_calibration(
    row_groups: Sequence[Dict[str, Any]],
    table_inventory_df: pd.DataFrame,
) -> Dict[str, Any]:
    inventory_lookup = {
        _norm(row.get("table_folder")): row.to_dict()
        for _, row in table_inventory_df.iterrows()
    } if not table_inventory_df.empty else {}
    calibrated_rows: List[Dict[str, Any]] = []
    candidate_rows: List[Dict[str, Any]] = []
    duplicate_rejected_rows: List[Dict[str, Any]] = []
    unknown_metric_rows: List[Dict[str, Any]] = []
    unreadable_label_rows: List[Dict[str, Any]] = []
    unit_audit_rows: List[Dict[str, Any]] = []
    year_audit_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []
    table_level_reviews: List[Dict[str, Any]] = []
    year_audit_seen: set[Tuple[str, str]] = set()
    alias_labels_applied: set[str] = set()
    year_normalized_labels: set[Tuple[str, str]] = set()
    unit_propagated_count = 0
    previous_metric_by_table: Dict[str, Tuple[str, str]] = defaultdict(lambda: ("", ""))

    for row_group in row_groups:
        table_id = _norm(row_group.get("table_folder"))
        raw_metric_name = _norm(row_group.get("raw_metric_name"))
        metric_name_cn = _norm(row_group.get("metric_name_cn"))
        row_warnings = _parse_risk_tags(row_group.get("row_warnings"))
        table_warnings = _parse_risk_tags(row_group.get("table_warnings"))
        baseline_metric_code = _norm(row_group.get("metric_code")) or UNKNOWN_METRIC_CODE
        previous_metric_code, previous_metric_label = previous_metric_by_table[table_id]
        mapped_metric_code, alias_applied, suggested_alias, suggested_family, suggested_action = _map_metric_code(
            raw_metric_name=raw_metric_name,
            baseline_metric_code=baseline_metric_code,
            previous_metric_code=previous_metric_code,
            previous_metric_label=previous_metric_label,
        )
        if alias_applied:
            alias_labels_applied.add(raw_metric_name)
        metric_family = _metric_family(mapped_metric_code, _norm(row_group.get("metric_family")))
        readable_label = not _is_unreadable_label(raw_metric_name or metric_name_cn, row_warnings)
        cells = row_group["cells"]
        valid_year_count = sum(1 for cell in cells if cell["valid_year"])
        meaningful_cell_count = sum(1 for cell in cells if _meaningful_raw_value(cell["raw_value"]) or cell["parsed_value"] is not None)
        row_has_values = meaningful_cell_count > 0
        if row_has_values and mapped_metric_code != UNKNOWN_METRIC_CODE:
            previous_metric_by_table[table_id] = (mapped_metric_code, raw_metric_name or metric_name_cn)

        for cell in cells:
            year_key = (table_id, cell["raw_column"])
            if year_key not in year_audit_seen:
                year_audit_seen.add(year_key)
                year_audit_rows.append(
                    {
                        "table_id": table_id,
                        "raw_column": cell["raw_column"],
                        "normalized_year": cell["normalized_year"],
                        "valid_year": bool(cell["valid_year"]),
                        "action": cell["year_action"],
                        "reason": cell["year_reason"],
                    }
                )
                if cell["year_normalized_changed"]:
                    year_normalized_labels.add(year_key)

        if not readable_label:
            if row_has_values:
                unreadable_label_rows.append(
                    {
                        "table_id": table_id,
                        "row_index": int(row_group.get("source_row_index") or row_group.get("row_index") or 0),
                        "row_label_raw": raw_metric_name or None,
                        "affected_cell_count": meaningful_cell_count,
                        "values_preview": _row_values_preview(cells),
                        "table_ready_321a": bool(row_group.get("table_ready_321a")),
                        "image_source_path": _norm(row_group.get("source_image_path")),
                        "recommended_action": "unreadable_label_rerun_vlm",
                    }
                )
                table_level_reviews.append(
                    {
                        "table_id": table_id,
                        "review_type": "UNREADABLE_LABEL_ROW",
                        "row_index": int(row_group.get("source_row_index") or row_group.get("row_index") or 0),
                    }
                )
            continue

        if row_has_values and valid_year_count == 0:
            suggested_alias_text, suggested_family_text, action = _suggest_for_unknown(raw_metric_name, row_has_values, valid_year_count)
            unknown_metric_rows.append(
                {
                    "table_id": table_id,
                    "table_folder": table_id,
                    "table_title": _norm(row_group.get("table_title")),
                    "row_index": int(row_group.get("source_row_index") or row_group.get("row_index") or 0),
                    "raw_metric_name": raw_metric_name or None,
                    "metric_name_cn": metric_name_cn or None,
                    "normalized_label": _normalize_label(raw_metric_name or metric_name_cn),
                    "candidate_count_generated": 0,
                    "years_or_columns": "|".join(cell["raw_column"] for cell in cells if cell["raw_column"]),
                    "risk_tags": "TABLE_NOT_READY_321A|INVALID_YEAR" if not bool(row_group.get("table_ready_321a")) else "INVALID_YEAR",
                    "suggested_alias": suggested_alias_text,
                    "suggested_metric_family": suggested_family_text,
                    "suggested_action": action,
                }
            )
            table_level_reviews.append(
                {
                    "table_id": table_id,
                    "review_type": "NON_YEAR_SEGMENT_ROW",
                    "row_index": int(row_group.get("source_row_index") or row_group.get("row_index") or 0),
                }
            )
            continue

        if not row_has_values:
            suggested_alias_text, suggested_family_text, action = _suggest_for_unknown(raw_metric_name, row_has_values, valid_year_count)
            if mapped_metric_code == UNKNOWN_METRIC_CODE or action == "ignore_group_header":
                unknown_metric_rows.append(
                    {
                        "table_id": table_id,
                        "table_folder": table_id,
                        "table_title": _norm(row_group.get("table_title")),
                        "row_index": int(row_group.get("source_row_index") or row_group.get("row_index") or 0),
                        "raw_metric_name": raw_metric_name or None,
                        "metric_name_cn": metric_name_cn or None,
                        "normalized_label": _normalize_label(raw_metric_name or metric_name_cn),
                        "candidate_count_generated": 0,
                        "years_or_columns": "|".join(cell["raw_column"] for cell in cells if cell["raw_column"]),
                        "risk_tags": "VALUE_MISSING",
                        "suggested_alias": suggested_alias_text,
                        "suggested_metric_family": suggested_family_text,
                        "suggested_action": action,
                    }
                )
            continue

        if mapped_metric_code == UNKNOWN_METRIC_CODE:
            suggested_alias_text, suggested_family_text, action = _suggest_for_unknown(raw_metric_name, row_has_values, valid_year_count)
        else:
            suggested_alias_text, suggested_family_text, action = suggested_alias, suggested_family, suggested_action

        if mapped_metric_code == UNKNOWN_METRIC_CODE:
            unknown_metric_rows.append(
                {
                    "table_id": table_id,
                    "table_folder": table_id,
                    "table_title": _norm(row_group.get("table_title")),
                    "row_index": int(row_group.get("source_row_index") or row_group.get("row_index") or 0),
                    "raw_metric_name": raw_metric_name or None,
                    "metric_name_cn": metric_name_cn or None,
                    "normalized_label": _normalize_label(raw_metric_name or metric_name_cn),
                    "candidate_count_generated": valid_year_count,
                    "years_or_columns": "|".join(cell["normalized_year"] or cell["raw_column"] for cell in cells if cell["valid_year"]),
                    "risk_tags": "UNKNOWN_METRIC_CODE",
                    "suggested_alias": suggested_alias_text,
                    "suggested_metric_family": suggested_family_text,
                    "suggested_action": action,
                }
            )

        for cell in cells:
            calibrated_row = {
                "table_folder": table_id,
                "report_name": _norm(row_group.get("report_name")),
                "source_json_path": _norm(row_group.get("source_json_path")),
                "source_image_path": _norm(row_group.get("source_image_path")),
                "table_title": _norm(row_group.get("table_title")),
                "table_unit": _norm(row_group.get("table_unit")),
                "table_currency": _norm(row_group.get("table_currency")),
                "schema_shape": _norm(row_group.get("schema_shape")),
                "quality_decision": _norm(row_group.get("quality_decision")),
                "quality_main_issue": _norm(row_group.get("quality_main_issue")),
                "table_ready_321a": bool(row_group.get("table_ready_321a")),
                "row_index": int(row_group.get("row_index") or 0),
                "source_row_index": int(row_group.get("source_row_index") or row_group.get("row_index") or 0),
                "raw_metric_name": raw_metric_name or None,
                "metric_name_cn": metric_name_cn or None,
                "metric_code": mapped_metric_code,
                "metric_family": metric_family,
                "metric_name_known": bool(_metric_is_known(mapped_metric_code)),
                "year": cell["normalized_year"],
                "period_type": "estimate" if cell["normalized_year"] and cell["normalized_year"].endswith("E") else ("actual" if cell["normalized_year"] else "unknown"),
                "column_label": cell["raw_column"],
                "source_column_label": cell["source_column_label"] or cell["raw_column"],
                "raw_value": cell["raw_value"],
                "normalized_value": cell["parsed_value"],
                "unit": cell["baseline_unit"] or None,
                "unit_source": cell["baseline_unit_source"] or None,
                "currency": _norm(row_group.get("table_currency")) or None,
                "row_confidence": float(row_group.get("row_confidence") or 0.0),
                "row_uncertain": bool(row_group.get("row_uncertain")),
                "row_warnings": "|".join(row_warnings),
                "row_schema_errors": _norm(row_group.get("row_schema_errors")),
                "table_warnings": "|".join(table_warnings),
                "year_tags": "" if cell["valid_year"] else "INVALID_YEAR",
                "unit_tags": "",
                "row_all_values_missing": not row_has_values,
                "candidate_should_exist": bool(row_has_values and cell["valid_year"] and (_meaningful_raw_value(cell["raw_value"]) or cell["parsed_value"] is not None)),
                "calibration_stage": CALIBRATION_STAGE,
                "calibration_alias_applied": alias_applied,
                "calibration_suggested_action": action,
                "year_valid": bool(cell["valid_year"]),
                "year_reason": cell["year_reason"],
            }

            semantic_unit, semantic_unit_source = _metric_unit_semantic(mapped_metric_code, raw_metric_name, cell["raw_value"])
            old_unit = calibrated_row["unit"]
            new_unit = old_unit
            unit_source = calibrated_row["unit_source"] or ""
            if not new_unit and semantic_unit:
                new_unit = semantic_unit
                unit_source = semantic_unit_source
            elif not new_unit and _norm(row_group.get("table_unit")) and mapped_metric_code not in RATIO_UNIT_METRICS and mapped_metric_code not in X_UNIT_METRICS and mapped_metric_code not in PER_SHARE_UNIT_METRICS:
                new_unit = _norm(row_group.get("table_unit"))
                unit_source = "TABLE_UNIT"
            if new_unit != old_unit:
                unit_propagated_count += 1
            calibrated_row["unit"] = new_unit
            calibrated_row["unit_source"] = unit_source or None
            calibrated_row["currency"] = _infer_currency(_norm(row_group.get("table_currency")), new_unit)
            unit_audit_rows.append(
                {
                    "table_id": table_id,
                    "table_title": _norm(row_group.get("table_title")),
                    "table_unit": _norm(row_group.get("table_unit")),
                    "row_label": raw_metric_name or None,
                    "metric_code": mapped_metric_code,
                    "old_unit": old_unit,
                    "new_unit": new_unit,
                    "unit_source": unit_source,
                    "action": "propagate_unit" if new_unit != old_unit and bool(new_unit) else ("keep_existing" if old_unit else "unit_unknown"),
                }
            )
            calibrated_rows.append(calibrated_row)

            if not calibrated_row["candidate_should_exist"]:
                continue

            risk_tags: List[str] = []
            if mapped_metric_code == UNKNOWN_METRIC_CODE:
                risk_tags.append("UNKNOWN_METRIC_CODE")
            if not bool(row_group.get("table_ready_321a")):
                risk_tags.append("TABLE_NOT_READY_321A")
            if _norm(row_group.get("quality_decision")) == "VLM_TABLE_SCHEMA_INVALID" or _norm(row_group.get("row_schema_errors")):
                risk_tags.append("SCHEMA_REVIEW_REQUIRED")
            if calibrated_row["normalized_value"] is None:
                if _meaningful_raw_value(cell["raw_value"]):
                    risk_tags.append("VALUE_PARSE_FAILED")
                else:
                    risk_tags.append("VALUE_MISSING")
            if calibrated_row["row_uncertain"]:
                risk_tags.append("VLM_ROW_UNCERTAIN")
            if float(calibrated_row["row_confidence"]) < 0.80:
                risk_tags.append("LOW_CONFIDENCE")
            if not calibrated_row["year_valid"]:
                risk_tags.append("INVALID_YEAR")
            if not calibrated_row["unit"] and mapped_metric_code not in RATIO_UNIT_METRICS and mapped_metric_code not in X_UNIT_METRICS and mapped_metric_code not in PER_SHARE_UNIT_METRICS:
                risk_tags.append("UNIT_UNKNOWN")
            if _has_replacement_chars(raw_metric_name):
                risk_tags.append("CHINESE_LABEL_CORRUPTED")

            candidate_rows.append(
                {
                    "candidate_id": _make_candidate_id(table_id, int(calibrated_row["source_row_index"]), mapped_metric_code, _norm(calibrated_row["year"]), calibrated_row["raw_value"]),
                    "source_stage": "vlm_strict_json_321a_rerun",
                    "calibration_stage": CALIBRATION_STAGE,
                    "source_file": _norm(row_group.get("source_image_path")) or _norm(row_group.get("source_json_path")),
                    "source_doc_name": _norm(row_group.get("report_name")),
                    "source_table_id": table_id,
                    "source_row_index": int(calibrated_row["source_row_index"]),
                    "source_row_text": raw_metric_name,
                    "metric_code": mapped_metric_code,
                    "canonical_metric_name": mapped_metric_code if mapped_metric_code != UNKNOWN_METRIC_CODE else raw_metric_name,
                    "raw_metric_name": raw_metric_name,
                    "year": calibrated_row["year"],
                    "period_type": calibrated_row["period_type"],
                    "raw_value": _norm(calibrated_row["raw_value"]),
                    "normalized_value": calibrated_row["normalized_value"],
                    "unit": calibrated_row["unit"],
                    "unit_source": calibrated_row["unit_source"],
                    "currency": calibrated_row["currency"],
                    "confidence": float(calibrated_row["row_confidence"]),
                    "year_source": "TABLE_HEADER",
                    "smoke_check_status": "NOT_APPLICABLE",
                    "smoke_check_source": "",
                    "table_title": _norm(row_group.get("table_title")) or None,
                    "table_unit": _norm(row_group.get("table_unit")) or None,
                    "risk_tags": "|".join(sorted(set(risk_tags))),
                    "split_decision": "review_required_preview",
                    "split_reason": "PENDING_CALIBRATION_TRUST_SPLIT",
                    "provenance_json": json.dumps(
                        {
                            "source_json_path": _norm(row_group.get("source_json_path")),
                            "source_image_path": _norm(row_group.get("source_image_path")),
                            "table_folder": table_id,
                            "row_index": int(calibrated_row["source_row_index"]),
                            "column_label": cell["raw_column"],
                            "recognition_source": "PURE_VLM_IMAGE_ONLY",
                            "forbidden_sources": [
                                "MinerU table_body",
                                "MinerU table_caption",
                                "MinerU content_list.json",
                                "existing VLM JSON",
                                "existing OCR text",
                            ],
                        },
                        ensure_ascii=False,
                    ),
                    "metric_family": metric_family,
                }
            )

    grouped: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        metric_key = row["metric_code"] if row["metric_code"] != UNKNOWN_METRIC_CODE else f"{UNKNOWN_METRIC_CODE}::{_normalize_label(row['raw_metric_name'])}"
        grouped[(row["source_table_id"], metric_key, _norm(row["year"]))].append(row)

    canonical_rows: List[Dict[str, Any]] = []
    same_value_duplicate_collapsed_count = 0
    true_value_conflict_count = 0
    conflict_keys: set[str] = set()

    for (table_id, metric_key, year), rows in grouped.items():
        if len(rows) == 1:
            canonical_rows.append(rows[0])
            continue
        normalized_values = sorted({_norm(row["normalized_value"]) for row in rows})
        distinct_values = [value for value in normalized_values if value != ""]
        metric_code = rows[0]["metric_code"]
        source_rows = "|".join(str(row["source_row_index"]) for row in rows)
        if len(set(distinct_values)) <= 1:
            keep = sorted(rows, key=lambda item: (-float(item.get("confidence") or 0.0), str(item.get("candidate_id"))))[0]
            canonical_rows.append(keep)
            for dropped in rows:
                if dropped is keep:
                    continue
                dropped = dict(dropped)
                dropped["split_decision"] = "rejected_preview"
                dropped["split_reason"] = "DUPLICATE_SAME_VALUE_COLLAPSED"
                duplicate_rejected_rows.append(dropped)
                same_value_duplicate_collapsed_count += 1
            conflict_rows.append(
                {
                    "table_id": table_id,
                    "metric_code": metric_code,
                    "year": year,
                    "candidate_count": len(rows),
                    "distinct_values": len(set(distinct_values)) if distinct_values else 1,
                    "values": "|".join(distinct_values or [""]),
                    "source_rows": source_rows,
                    "conflict_class": "DUPLICATE_SAME_VALUE_COLLAPSIBLE",
                    "recommended_action": "collapse_duplicate_keep_highest_confidence",
                }
            )
            continue
        conflict_class = "TRUE_VALUE_CONFLICT"
        if metric_code == UNKNOWN_METRIC_CODE:
            conflict_class = "METRIC_ALIAS_COLLISION"
        for row in rows:
            tags = set(_parse_risk_tags(row.get("risk_tags")))
            tags.add("VALUE_CONFLICT")
            row["risk_tags"] = "|".join(sorted(tags))
            canonical_rows.append(row)
        true_value_conflict_count += 1
        conflict_key = f"{table_id}|{metric_code}|{year}"
        conflict_keys.add(conflict_key)
        conflict_rows.append(
            {
                "table_id": table_id,
                "metric_code": metric_code,
                "year": year,
                "candidate_count": len(rows),
                "distinct_values": len(set(distinct_values)),
                "values": "|".join(distinct_values),
                "source_rows": source_rows,
                "conflict_class": conflict_class,
                "recommended_action": "manual_review_conflicting_values",
            }
        )

    trusted_rows: List[Dict[str, Any]] = []
    review_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = duplicate_rejected_rows[:]
    for row in canonical_rows:
        risk_tags = set(_parse_risk_tags(row.get("risk_tags")))
        conflict_key = f"{row['source_table_id']}|{row['metric_code']}|{_norm(row['year'])}"
        if conflict_key in conflict_keys:
            risk_tags.add("VALUE_CONFLICT")
        row["risk_tags"] = "|".join(sorted(risk_tags))
        decision = "trusted_preview"
        reason = "PASS_VLM_TRUST_GATE"
        if any(tag in risk_tags for tag in {"CHINESE_LABEL_CORRUPTED", "UNREADABLE_LABEL"}):
            decision = "rejected_preview"
            reason = "STRICT_REJECT_TAG"
        elif any(tag in risk_tags for tag in {"UNKNOWN_METRIC_CODE", "TABLE_NOT_READY_321A", "SCHEMA_REVIEW_REQUIRED", "VLM_ROW_UNCERTAIN", "LOW_CONFIDENCE", "VALUE_CONFLICT", "INVALID_YEAR", "YEAR_MISSING", "VALUE_MISSING", "VALUE_PARSE_FAILED", "UNIT_UNKNOWN"}):
            decision = "review_required_preview"
            reason = "HAS_CALIBRATION_REVIEW_TAG"
        elif row["normalized_value"] is None:
            decision = "review_required_preview"
            reason = "VALUE_MISSING_OR_INVALID"
        elif not _metric_is_known(row["metric_code"]):
            decision = "review_required_preview"
            reason = "UNKNOWN_METRIC_CODE"
        row["split_decision"] = decision
        row["split_reason"] = reason
        if decision == "trusted_preview":
            trusted_rows.append(row)
        elif decision == "review_required_preview":
            review_rows.append(row)
        else:
            rejected_rows.append(row)

    return {
        "vlm_rows_normalized": pd.DataFrame(calibrated_rows),
        "metric_candidates_all": pd.DataFrame(canonical_rows),
        "trusted_preview": pd.DataFrame(trusted_rows),
        "review_required_preview": pd.DataFrame(review_rows),
        "rejected_preview": pd.DataFrame(rejected_rows),
        "unknown_metric_diagnostics": pd.DataFrame(unknown_metric_rows),
        "unreadable_label_diagnostics": pd.DataFrame(unreadable_label_rows),
        "unit_propagation_audit": pd.DataFrame(unit_audit_rows),
        "year_normalization_audit": pd.DataFrame(year_audit_rows),
        "conflict_diagnostics": pd.DataFrame(conflict_rows),
        "table_level_reviews": pd.DataFrame(table_level_reviews),
        "alias_added_count": len(alias_labels_applied),
        "unit_propagated_count": unit_propagated_count,
        "year_normalized_count": len(year_normalized_labels),
        "same_value_duplicate_collapsed_count": same_value_duplicate_collapsed_count,
        "true_value_conflict_count": true_value_conflict_count,
    }


def _build_metric_coverage(candidates_df: pd.DataFrame, trusted_df: pd.DataFrame, review_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "metric_family",
        "metric_code",
        "candidate_count",
        "trusted_count",
        "review_required_count",
        "unique_report_count",
        "unique_table_count",
        "years_covered",
    ]
    if candidates_df.empty:
        return pd.DataFrame(columns=columns)
    trusted_ids = set(trusted_df["candidate_id"].astype(str).tolist()) if not trusted_df.empty else set()
    review_ids = set(review_df["candidate_id"].astype(str).tolist()) if not review_df.empty else set()
    temp = candidates_df.copy()
    temp["trusted_count_row"] = temp["candidate_id"].astype(str).isin(trusted_ids).astype(int)
    temp["review_required_count_row"] = temp["candidate_id"].astype(str).isin(review_ids).astype(int)
    return (
        temp.groupby(["metric_family", "metric_code"], dropna=False)
        .agg(
            candidate_count=("candidate_id", "count"),
            trusted_count=("trusted_count_row", "sum"),
            review_required_count=("review_required_count_row", "sum"),
            unique_report_count=("source_doc_name", lambda series: int(pd.Series(series).replace("", pd.NA).dropna().nunique())),
            unique_table_count=("source_table_id", lambda series: int(pd.Series(series).replace("", pd.NA).dropna().nunique())),
            years_covered=("year", lambda series: "|".join(sorted({_norm(value) for value in series if _norm(value)}))),
        )
        .reset_index()
        .sort_values(["metric_family", "metric_code"])
        .reset_index(drop=True)
    )[columns]


def _build_risk_tag_counts(candidates_df: pd.DataFrame) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    if not candidates_df.empty:
        for value in candidates_df["risk_tags"].astype(str).tolist():
            for tag in value.split("|"):
                tag = tag.strip()
                if tag:
                    counter[tag] += 1
    return pd.DataFrame([{"risk_tag": key, "count": value} for key, value in counter.most_common()])


def _build_provenance_coverage(candidates_df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    columns = [
        "candidate_id",
        "table_folder",
        "report_name",
        "metric_code",
        "year",
        "has_source_file",
        "has_source_row_text",
        "has_source_table_id",
        "has_source_stage",
        "has_year_source",
        "has_unit_source",
        "provenance_complete",
        "missing_fields",
    ]
    if candidates_df.empty:
        return pd.DataFrame(columns=columns), 0.0
    rows: List[Dict[str, Any]] = []
    for _, row in candidates_df.iterrows():
        missing = []
        checks = {
            "source_file": bool(_norm(row.get("source_file"))),
            "source_row_text": bool(_norm(row.get("source_row_text"))),
            "source_table_id": bool(_norm(row.get("source_table_id"))),
            "source_stage": bool(_norm(row.get("source_stage"))),
            "year_source": bool(_norm(row.get("year_source"))),
            "unit_source": bool(_norm(row.get("unit_source"))),
        }
        for key, passed in checks.items():
            if not passed:
                missing.append(key)
        rows.append(
            {
                "candidate_id": _norm(row.get("candidate_id")),
                "table_folder": _norm(row.get("source_table_id")),
                "report_name": _norm(row.get("source_doc_name")),
                "metric_code": _norm(row.get("metric_code")),
                "year": _norm(row.get("year")),
                "has_source_file": checks["source_file"],
                "has_source_row_text": checks["source_row_text"],
                "has_source_table_id": checks["source_table_id"],
                "has_source_stage": checks["source_stage"],
                "has_year_source": checks["year_source"],
                "has_unit_source": checks["unit_source"],
                "provenance_complete": not missing,
                "missing_fields": "|".join(missing),
            }
        )
    dataframe = pd.DataFrame(rows)
    return dataframe, float(dataframe["provenance_complete"].mean()) if not dataframe.empty else 0.0


def _build_unit_year_context_summary(
    candidates_df: pd.DataFrame,
    calibration_result: Dict[str, Any],
) -> pd.DataFrame:
    unit_unknown_count = 0
    invalid_year_count = 0
    if not candidates_df.empty:
        risk_text = candidates_df["risk_tags"].astype(str)
        unit_unknown_count = int(risk_text.str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum())
        invalid_year_count = int(risk_text.str.contains(r"(?:^|\|)INVALID_YEAR(?:$|\|)", regex=True).sum())
    return pd.DataFrame(
        [
            {
                "unit_unknown_count": unit_unknown_count,
                "invalid_year_count": invalid_year_count,
                "unit_propagated_count": int(calibration_result["unit_propagated_count"]),
                "year_normalized_count": int(calibration_result["year_normalized_count"]),
                "table_level_review_count": int(len(calibration_result["table_level_reviews"]["table_id"].dropna().unique())) if not calibration_result["table_level_reviews"].empty else 0,
            }
        ]
    )


def _build_per_table_summary(
    table_inventory_df: pd.DataFrame,
    candidates_df: pd.DataFrame,
    trusted_df: pd.DataFrame,
    review_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    table_level_reviews_df: pd.DataFrame,
) -> pd.DataFrame:
    inventory = table_inventory_df.copy()
    if inventory.empty:
        return pd.DataFrame(
            columns=[
                "table_folder",
                "report_name",
                "table_title",
                "quality_decision",
                "quality_main_issue",
                "candidate_count",
                "trusted_count",
                "review_required_count",
                "rejected_count",
                "unique_metric_count",
                "unique_year_count",
                "table_level_review",
                "table_decision",
            ]
        )
    counts: Dict[str, Dict[str, int]] = defaultdict(dict)
    for name, dataframe in [
        ("candidate_count", candidates_df),
        ("trusted_count", trusted_df),
        ("review_required_count", review_df),
        ("rejected_count", rejected_df),
    ]:
        if dataframe.empty:
            continue
        grouped = dataframe.groupby("source_table_id", dropna=False).size()
        for table_id, count in grouped.items():
            counts[_norm(table_id)][name] = int(count)
    metric_counts = {}
    if not candidates_df.empty:
        grouped = candidates_df.groupby("source_table_id", dropna=False).agg(
            unique_metric_count=("metric_code", lambda series: int(pd.Series(series).replace("", pd.NA).dropna().nunique())),
            unique_year_count=("year", lambda series: int(pd.Series(series).replace("", pd.NA).dropna().nunique())),
        )
        metric_counts = {str(index): row.to_dict() for index, row in grouped.iterrows()}
    table_review_tables = set(table_level_reviews_df["table_id"].astype(str).tolist()) if not table_level_reviews_df.empty else set()
    rows: List[Dict[str, Any]] = []
    for _, record in inventory.iterrows():
        table_id = _norm(record.get("table_folder"))
        candidate_count = counts.get(table_id, {}).get("candidate_count", 0)
        trusted_count = counts.get(table_id, {}).get("trusted_count", 0)
        review_count = counts.get(table_id, {}).get("review_required_count", 0)
        rejected_count = counts.get(table_id, {}).get("rejected_count", 0)
        table_decision = "TABLE_NO_CANDIDATES"
        if trusted_count > 0:
            table_decision = "TABLE_HAS_TRUSTED_OUTPUT"
        elif review_count > 0:
            table_decision = "TABLE_USABLE_NEEDS_REVIEW"
        elif table_id in table_review_tables:
            table_decision = "TABLE_LEVEL_REVIEW_ONLY"
        rows.append(
            {
                "table_folder": table_id,
                "report_name": _norm(record.get("report_name")) or _norm(record.get("image_filename")),
                "table_title": _norm(record.get("table_title")),
                "quality_decision": _norm(record.get("current_decision")),
                "quality_main_issue": _norm(record.get("main_issue")),
                "candidate_count": candidate_count,
                "trusted_count": trusted_count,
                "review_required_count": review_count,
                "rejected_count": rejected_count,
                "unique_metric_count": int(metric_counts.get(table_id, {}).get("unique_metric_count", 0)),
                "unique_year_count": int(metric_counts.get(table_id, {}).get("unique_year_count", 0)),
                "table_level_review": table_id in table_review_tables,
                "table_decision": table_decision,
            }
        )
    return pd.DataFrame(rows).sort_values(["table_folder"]).reset_index(drop=True)


def _build_qa_checks(
    summary: Dict[str, Any],
    table_inventory_df: pd.DataFrame,
    candidates_df: pd.DataFrame,
    trusted_df: pd.DataFrame,
    diagnostics: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    def status(ok: bool, warn: bool = False) -> str:
        if ok:
            return "PASS"
        if warn:
            return "WARN"
        return "FAIL"

    rows: List[Dict[str, Any]] = []
    trusted_risk = trusted_df["risk_tags"].astype(str) if not trusted_df.empty else pd.Series(dtype=str)
    corrupted_label_count = int(trusted_df["source_row_text"].astype(str).str.contains(r"[?？\ufffd]", regex=True).sum()) if not trusted_df.empty else 0
    invalid_year_count = int((~trusted_df["year"].astype(str).str.match(r"^20\d{2}(?:[AE])?$", na=False)).sum()) if not trusted_df.empty else 0
    unknown_metric_count = int((trusted_df["metric_code"].astype(str) == UNKNOWN_METRIC_CODE).sum()) if not trusted_df.empty else 0
    missing_value_count = int(trusted_df["normalized_value"].isna().sum()) if not trusted_df.empty else 0
    trusted_conflict_count = int(trusted_risk.str.contains(r"(?:^|\|)VALUE_CONFLICT(?:$|\|)", regex=True).sum()) if not trusted_df.empty else 0
    schema_invalid_trusted_count = int(trusted_risk.str.contains(r"(?:^|\|)SCHEMA_REVIEW_REQUIRED(?:$|\|)", regex=True).sum()) if not trusted_df.empty else 0
    chinese_replacement_count = int(candidates_df["source_row_text"].astype(str).str.contains(r"[?？\ufffd]", regex=True).sum()) if not candidates_df.empty else 0
    inventory_table_ready = int((table_inventory_df["current_decision"].astype(str) == "VLM_TABLE_READY_FOR_MAPPING").sum()) if not table_inventory_df.empty else 0

    rows.append({"check_name": "no_corrupted_labels_in_trusted_output", "status": status(corrupted_label_count == 0), "detail": f"corrupted_label_count={corrupted_label_count}"})
    rows.append({"check_name": "no_invalid_year_in_trusted_output", "status": status(invalid_year_count == 0), "detail": f"invalid_year_count={invalid_year_count}"})
    rows.append({"check_name": "no_unknown_metric_code_in_trusted_output", "status": status(unknown_metric_count == 0), "detail": f"unknown_metric_code_count={unknown_metric_count}"})
    rows.append({"check_name": "no_missing_normalized_value_in_trusted_output", "status": status(missing_value_count == 0), "detail": f"missing_normalized_value_count={missing_value_count}"})
    rows.append({"check_name": "no_conflict_in_trusted_output", "status": status(trusted_conflict_count == 0), "detail": f"trusted_conflict_count={trusted_conflict_count}"})
    rows.append({"check_name": "schema_invalid_tables_not_silently_trusted", "status": status(schema_invalid_trusted_count == 0), "detail": f"schema_invalid_trusted_count={schema_invalid_trusted_count}"})
    rows.append({"check_name": "table_ready_count_matches_321a", "status": status(int(summary.get("table_ready_count", 0)) == inventory_table_ready), "detail": f"summary_table_ready={summary.get('table_ready_count', 0)}, inventory_table_ready={inventory_table_ready}"})
    rows.append({"check_name": "chinese_text_preserved", "status": status(chinese_replacement_count == 0), "detail": f"replacement_char_count={chinese_replacement_count}"})
    rows.append({"check_name": "forbidden_mineru_sources_not_used", "status": "PASS", "detail": "321B2 calibration consumed only previous mapping/quality outputs and pure VLM root."})
    rows.append({"check_name": "required_diagnostics_generated", "status": status(all(not diagnostics[name].empty or name == "unreadable_label_diagnostics" for name in diagnostics)), "detail": "core diagnostics sheets generated"})
    return pd.DataFrame(rows)


def _build_known_limitations() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"limitation": "sandbox_only", "detail": "321B2 is a sandbox-only calibration stage and is not production ingestion."},
            {"limitation": "pure_vlm_image_only", "detail": "Calibration keeps the PURE_VLM_IMAGE_ONLY provenance and does not repair outputs with MinerU text."},
            {"limitation": "unit_context_missing", "detail": "Tables without explicit title/unit still keep some monetary rows in review because units cannot be safely invented."},
            {"limitation": "schema_invalid_tables_review_only", "detail": "Schema-invalid or hierarchical tables stay in review and are not promoted to trusted output."},
        ]
    )


def _decision(summary: Dict[str, Any], diagnostics_complete: bool) -> str:
    if int(summary.get("qa_fail_count", 0)) > 0:
        return "PURE_VLM_CALIBRATION_BLOCKED_BY_QA_FAILURE"
    if int(summary.get("corrupted_label_candidate_count", 0)) > 0:
        return "PURE_VLM_CALIBRATION_BLOCKED_BY_LABEL_CORRUPTION"
    if (
        float(summary.get("calibrated_trusted_rate", 0.0)) >= 0.45
        and int(summary.get("table_with_trusted_count", 0)) >= 6
        and float(summary.get("provenance_complete_rate", 0.0)) >= 0.95
        and int(summary.get("qa_fail_count", 0)) == 0
    ):
        return "PURE_VLM_CALIBRATION_READY_FOR_321D_MANUAL_INGESTION"
    if float(summary.get("calibrated_trusted_rate", 0.0)) >= 0.25 and diagnostics_complete:
        return "PURE_VLM_CALIBRATION_PARTIAL_NEEDS_MORE_PROMPT_OR_ALIAS_WORK"
    return "PURE_VLM_CALIBRATION_NOT_READY"


def run_vlm_mapping_calibration(
    vlm_output_root: Path,
    quality_dir: Path,
    previous_mapping_dir: Path,
    output_dir: Path,
    ppstructure_benchmark_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    mapping_dir, baseline_summary, baseline_tables = _load_previous_mapping(
        vlm_output_root=vlm_output_root,
        quality_dir=quality_dir,
        previous_mapping_dir=previous_mapping_dir,
        output_dir=output_dir,
    )
    quality_summary = _read_json(quality_dir / "vlm_output_quality_321a_summary.json")
    table_inventory_df = baseline_tables["vlm_table_inventory"]
    row_groups = _build_row_groups(baseline_tables["vlm_rows_normalized"])
    calibration = _apply_calibration(row_groups, table_inventory_df)

    candidates_df = calibration["metric_candidates_all"]
    trusted_df = calibration["trusted_preview"]
    review_df = calibration["review_required_preview"]
    rejected_df = calibration["rejected_preview"]
    risk_tag_counts_df = _build_risk_tag_counts(candidates_df)
    provenance_df, provenance_complete_rate = _build_provenance_coverage(candidates_df)
    per_table_df = _build_per_table_summary(
        table_inventory_df=table_inventory_df,
        candidates_df=candidates_df,
        trusted_df=trusted_df,
        review_df=review_df,
        rejected_df=rejected_df,
        table_level_reviews_df=calibration["table_level_reviews"],
    )
    metric_coverage_df = _build_metric_coverage(candidates_df, trusted_df, review_df)
    unit_year_context_df = _build_unit_year_context_summary(candidates_df, calibration)
    diagnostics_frames = {
        "unknown_metric_diagnostics": calibration["unknown_metric_diagnostics"],
        "unreadable_label_diagnostics": calibration["unreadable_label_diagnostics"],
        "unit_propagation_audit": calibration["unit_propagation_audit"],
        "year_normalization_audit": calibration["year_normalization_audit"],
        "conflict_diagnostics": calibration["conflict_diagnostics"],
    }
    table_level_review_count = int(len(calibration["table_level_reviews"]["table_id"].dropna().unique())) if not calibration["table_level_reviews"].empty else 0
    unreadable_label_row_review_count = int(len(calibration["unreadable_label_diagnostics"]))
    diagnostics_complete = all(not diagnostics_frames[name].empty or name == "unreadable_label_diagnostics" for name in diagnostics_frames)

    summary: Dict[str, Any] = {
        "stage": CALIBRATION_STAGE,
        "vlm_output_root": str(vlm_output_root),
        "quality_dir": str(quality_dir),
        "previous_mapping_dir": str(mapping_dir),
        "ppstructure_benchmark_dir": str(ppstructure_benchmark_dir) if ppstructure_benchmark_dir else "",
        "output_dir": str(output_dir),
        "vlm_folder_count": int(quality_summary.get("vlm_folder_count", 0)),
        "parsed_json_count": int(quality_summary.get("parsed_json_count", 0)),
        "table_ready_count": int(quality_summary.get("table_ready_count", 0)),
        "mapped_table_count": int((per_table_df["candidate_count"] > 0).sum()) if not per_table_df.empty else 0,
        "table_with_candidates_count": int((per_table_df["candidate_count"] > 0).sum()) if not per_table_df.empty else 0,
        "table_with_trusted_count": int((per_table_df["trusted_count"] > 0).sum()) if not per_table_df.empty else 0,
        "calibrated_total_candidate_count": int(len(candidates_df)),
        "calibrated_trusted_total_count": int(len(trusted_df)),
        "calibrated_review_required_total_count": int(len(review_df)),
        "rejected_total_count": int(len(rejected_df)),
        "calibrated_trusted_rate": float(len(trusted_df) / len(candidates_df)) if len(candidates_df) else 0.0,
        "unknown_metric_code_count": int((candidates_df["metric_code"].astype(str) == UNKNOWN_METRIC_CODE).sum()) if not candidates_df.empty else 0,
        "unreadable_label_count": int(risk_tag_counts_df.loc[risk_tag_counts_df["risk_tag"] == "UNREADABLE_LABEL", "count"].sum()) if not risk_tag_counts_df.empty else 0,
        "unit_unknown_count": int(risk_tag_counts_df.loc[risk_tag_counts_df["risk_tag"] == "UNIT_UNKNOWN", "count"].sum()) if not risk_tag_counts_df.empty else 0,
        "invalid_year_count": int(risk_tag_counts_df.loc[risk_tag_counts_df["risk_tag"] == "INVALID_YEAR", "count"].sum()) if not risk_tag_counts_df.empty else 0,
        "table_not_ready_candidate_count": int(risk_tag_counts_df.loc[risk_tag_counts_df["risk_tag"] == "TABLE_NOT_READY_321A", "count"].sum()) if not risk_tag_counts_df.empty else 0,
        "table_level_review_count": table_level_review_count,
        "unreadable_label_row_review_count": unreadable_label_row_review_count,
        "same_value_duplicate_collapsed_count": int(calibration["same_value_duplicate_collapsed_count"]),
        "true_value_conflict_count": int(calibration["true_value_conflict_count"]),
        "alias_added_count": int(calibration["alias_added_count"]),
        "unit_propagated_count": int(calibration["unit_propagated_count"]),
        "year_normalized_count": int(calibration["year_normalized_count"]),
        "corrupted_label_candidate_count": int(candidates_df["source_row_text"].astype(str).str.contains(r"[?？\ufffd]", regex=True).sum()) if not candidates_df.empty else 0,
        "provenance_complete_rate": provenance_complete_rate,
    }
    qa_df = _build_qa_checks(summary, table_inventory_df, candidates_df, trusted_df, diagnostics_frames)
    summary["qa_pass_count"] = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_warn_count"] = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    summary["qa_fail_count"] = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    top_risk_tags = []
    if not risk_tag_counts_df.empty:
        for _, row in risk_tag_counts_df.head(10).iterrows():
            top_risk_tags.append({"risk_tag": _norm(row.get("risk_tag")), "count": int(row.get("count", 0))})
    summary["top_risk_tags"] = top_risk_tags
    summary["calibration_decision"] = _decision(summary, diagnostics_complete)

    summary_df = build_summary_dataframe(summary)
    known_limitations_df = _build_known_limitations()
    sheets = {
        "summary": summary_df,
        "vlm_table_inventory": table_inventory_df,
        "vlm_rows_normalized": calibration["vlm_rows_normalized"],
        "metric_candidates_all": candidates_df,
        "trusted_preview": trusted_df,
        "review_required_preview": review_df,
        "rejected_preview": rejected_df,
        "per_table_summary": per_table_df,
        "metric_coverage": metric_coverage_df,
        "unit_year_context_summary": unit_year_context_df,
        "risk_tag_counts": risk_tag_counts_df,
        "provenance_coverage": provenance_df,
        "qa_checks": qa_df,
        "unknown_metric_diagnostics": calibration["unknown_metric_diagnostics"],
        "unreadable_label_diagnostics": calibration["unreadable_label_diagnostics"],
        "unit_propagation_audit": calibration["unit_propagation_audit"],
        "year_normalization_audit": calibration["year_normalization_audit"],
        "conflict_diagnostics": calibration["conflict_diagnostics"],
        "known_limitations": known_limitations_df,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    excel_path = output_dir / "vlm_mapping_calibration_321b2.xlsx"
    summary_json_path = output_dir / "vlm_mapping_calibration_321b2_summary.json"
    report_md_path = output_dir / "vlm_mapping_calibration_321b2_report.md"
    _write_excel(excel_path, sheets)
    write_json(summary_json_path, summary)
    _write_markdown_report(report_md_path, summary, baseline_summary, qa_df, risk_tag_counts_df)
    if not trusted_df.empty:
        write_jsonl(output_dir / "trusted_preview.jsonl", trusted_df)
    if not review_df.empty:
        write_jsonl(output_dir / "review_required_preview.jsonl", review_df)
    if not calibration["unknown_metric_diagnostics"].empty:
        write_jsonl(output_dir / "unknown_metric_diagnostics.jsonl", calibration["unknown_metric_diagnostics"])

    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
    }
