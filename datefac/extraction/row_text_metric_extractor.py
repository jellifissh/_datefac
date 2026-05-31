from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


CORE_METRIC_RULES: List[Tuple[str, List[str]]] = [
    ("eps", ["每股收益", "eps"]),
    ("roe", ["roe", "净资产收益率"]),
    ("pe", ["p/e", "pe", "市盈率"]),
    ("pb", ["p/b", "pb", "市净率"]),
    ("ev_ebitda", ["ev/ebitda"]),
    ("revenue", ["营业收入", "revenue"]),
    ("net_profit", ["归母净利润", "归属于母公司净利润", "净利润"]),
    ("gross_margin", ["毛利率", "gross margin"]),
    ("revenue_growth", ["收入增长"]),
    ("net_profit_growth", ["净利润增长率", "净利润增长"]),
    ("debt_ratio", ["资产负债率", "debt ratio"]),
    ("operating_cash_flow", ["经营活动现金流", "operating cash flow"]),
]

CASHFLOW_RULES: List[Tuple[str, List[str]]] = [
    ("net_profit", ["净利润"]),
    ("asset_impairment_provision", ["资产减值准备"]),
    ("depreciation_amortization", ["折旧摊销"]),
    ("fair_value_change_loss", ["公允价值变动损失"]),
    ("finance_expense", ["财务费用"]),
    ("working_capital_change", ["营运资本变动"]),
    ("other_operating_cf", ["其他"]),
    ("operating_cash_flow", ["经营活动现金流"]),
    ("capex", ["资本开支"]),
    ("other_investing_cash_flow", ["其他投资现金流"]),
    ("investing_cash_flow", ["投资活动现金流"]),
    ("equity_financing", ["权益性融资"]),
    ("debt_net_change", ["负债净变化"]),
    ("dividend_interest_paid", ["支付股利", "利息"]),
    ("other_financing_cash_flow", ["其他融资现金流"]),
    ("financing_cash_flow", ["融资活动现金流"]),
    ("net_cash_change", ["现金净变动"]),
    ("cash_beginning_balance", ["货币资金的期初余额"]),
    ("cash_ending_balance", ["货币资金的期末余额"]),
    ("free_cash_flow_firm", ["企业自由现金流"]),
    ("free_cash_flow_equity", ["权益自由现金流"]),
]

YEAR_TOKEN_RULE = re.compile(r"\b(20[0-9]{2}(?:[AEae])?)\b")
# important: do not split 1974 -> 197 + 4
NUM_TOKEN_RULE = re.compile(r"(?<![A-Za-z0-9])(?:\(?-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?\)?)(?![A-Za-z0-9])")

CANONICAL_YEARS = ["2024", "2025", "2026E", "2027E", "2028E"]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _normalize_value(token: str) -> str:
    t = _norm(token).replace("（", "(").replace("）", ")")
    if re.match(r"^\([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?\)$", t):
        t = "-" + t[1:-1]
    return t


def _is_bbox_like_row(row_text: str) -> bool:
    # long float metadata rows
    if "cell_bbox" in row_text.lower():
        return True
    if len(re.findall(r"-?\d+\.\d+", row_text)) >= 4 and len(re.findall(r"[a-zA-Z\u4e00-\u9fff]", row_text)) < 4:
        return True
    return False


def _detect_years(rows: List[str]) -> Tuple[List[str], bool]:
    years: List[str] = []
    for row in rows[:10]:
        toks = YEAR_TOKEN_RULE.findall(_norm(row))
        if len(toks) >= 3:
            years = [x.upper().replace("A", "A").replace("E", "E") for x in toks]
            break
    if years:
        return years, False
    return CANONICAL_YEARS, True


def _metric_match(row_text: str, cashflow_context: bool) -> Tuple[str, str]:
    txt = row_text.lower()
    rules = CASHFLOW_RULES + CORE_METRIC_RULES if cashflow_context else CORE_METRIC_RULES + CASHFLOW_RULES
    for code, kws in rules:
        for kw in kws:
            if kw.lower() in txt:
                return code, kw
    return "", ""


def _looks_cashflow_context(rows: List[str]) -> bool:
    joined = " ".join(rows[:20]).lower()
    keys = ["现金流量表", "经营活动现金流", "投资活动现金流", "融资活动现金流", "自由现金流", "现金净变动"]
    return any(k.lower() in joined for k in keys)


def extract_metric_candidates_from_repaired_rows(
    repaired_rows: List[Dict[str, Any]],
    expected_year_count: int = 5,
) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = []
    unmatched_rows: List[Dict[str, Any]] = []
    parse_warnings: List[Dict[str, Any]] = []

    rows = [_norm(r.get("row_text_repaired") or r.get("row_text_cleaned") or r.get("row_text") or "") for r in repaired_rows]
    rows = [x for x in rows if x]
    years, inferred = _detect_years(rows)
    cashflow_context = _looks_cashflow_context(rows)

    year_inferred_count = 1 if inferred else 0
    numeric_count_mismatch_count = 0
    matched_metric_row_count = 0
    total_row_text_count = len(rows)

    split_1974_detected = False

    for ridx, rr in enumerate(repaired_rows):
        row_text = _norm(rr.get("row_text_repaired") or rr.get("row_text_cleaned") or rr.get("row_text") or "")
        if not row_text:
            continue
        if _is_bbox_like_row(row_text):
            parse_warnings.append(
                {
                    "source_file": _norm(rr.get("source_file")),
                    "extracted_table_id": _norm(rr.get("extracted_table_id")),
                    "row_index": rr.get("row_index"),
                    "warning_code": "SKIPPED_RAW_BBOX_METADATA",
                    "warning_message": row_text[:200],
                }
            )
            continue

        metric_code, raw_metric_name = _metric_match(row_text, cashflow_context=cashflow_context)
        if not metric_code:
            unmatched_rows.append(
                {
                    "source_file": _norm(rr.get("source_file")),
                    "extracted_table_id": _norm(rr.get("extracted_table_id")),
                    "row_index": rr.get("row_index"),
                    "row_text": row_text,
                }
            )
            continue

        matched_metric_row_count += 1
        nums = [_normalize_value(x) for x in NUM_TOKEN_RULE.findall(row_text)]
        # sanity check: no 197 / 4 split style
        if "1974" in row_text and ("197" in nums and "4" in nums):
            split_1974_detected = True

        if len(nums) == 0:
            parse_warnings.append(
                {
                    "source_file": _norm(rr.get("source_file")),
                    "extracted_table_id": _norm(rr.get("extracted_table_id")),
                    "row_index": rr.get("row_index"),
                    "warning_code": "NO_NUMERIC_FOUND",
                    "warning_message": row_text,
                }
            )
            unmatched_rows.append(
                {
                    "source_file": _norm(rr.get("source_file")),
                    "extracted_table_id": _norm(rr.get("extracted_table_id")),
                    "row_index": rr.get("row_index"),
                    "row_text": row_text,
                }
            )
            continue

        risk_tags = ["ROW_TEXT_ONLY"]
        if inferred:
            risk_tags.append("YEAR_INFERRED")
        repair_tags = _norm(rr.get("repair_tags"))
        if repair_tags:
            risk_tags.append(repair_tags)

        if len(nums) != expected_year_count:
            risk_tags.append("NUMERIC_COUNT_MISMATCH")
            numeric_count_mismatch_count += 1

        n = min(len(nums), len(years), expected_year_count)
        for i in range(n):
            raw_value = nums[i]
            normalized_value = raw_value.replace(",", "")
            tags = risk_tags[:]
            if raw_value.startswith("-") or "(" in raw_value:
                tags.append("NEGATIVE_PARENTHESES")
            candidates.append(
                {
                    "source_file": _norm(rr.get("source_file")),
                    "extracted_table_id": _norm(rr.get("extracted_table_id")),
                    "row_index": rr.get("row_index"),
                    "row_text": row_text,
                    "metric_code": metric_code,
                    "raw_metric_name": raw_metric_name,
                    "year": years[i],
                    "raw_value": raw_value,
                    "normalized_value": normalized_value,
                    "raw_unit": "",
                    "alignment_status": "ALIGNED" if len(nums) == expected_year_count else "PARTIAL_ALIGNED",
                    "risk_tags": "|".join(tags),
                    "confidence": "high" if len(nums) == expected_year_count and not repair_tags else ("medium" if len(nums) >= 4 else "low"),
                }
            )

    return {
        "metric_candidate_preview": candidates,
        "parse_warnings": parse_warnings,
        "unmatched_rows": unmatched_rows,
        "year_inferred_count": year_inferred_count,
        "numeric_count_mismatch_count": numeric_count_mismatch_count,
        "matched_metric_row_count": matched_metric_row_count,
        "total_row_text_count": total_row_text_count,
        "numeric_tokenizer_split_1974_detected": split_1974_detected,
    }

