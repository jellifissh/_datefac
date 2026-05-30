from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from datefac.domain.extracted_table import ExtractedTable


METRIC_RULES: List[Tuple[str, List[str]]] = [
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

YEAR_TOKEN_RULE = re.compile(r"\b(20[0-9]{2}(?:[AE])?)\b", re.IGNORECASE)
NUM_TOKEN_RULE = re.compile(
    r"(?<![A-Za-z])(?:\(?-?[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?%?\)?|-?[0-9]+(?:\.[0-9]+)?%?)(?![A-Za-z])"
)

CANONICAL_YEARS = ["2024", "2025", "2026E", "2027E", "2028E"]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _normalize_value(token: str) -> str:
    t = _norm(token).replace("（", "(").replace("）", ")")
    if re.match(r"^\([+-]?[0-9,]+(\.[0-9]+)?%?\)$", t):
        t = "-" + t[1:-1]
    return t


def _metric_match(row_text: str) -> Tuple[str, str]:
    t = row_text.lower()
    for code, kws in METRIC_RULES:
        for kw in kws:
            if kw.lower() in t:
                return code, kw
    return "", ""


def _detect_years(row_texts: List[str]) -> Tuple[List[str], bool]:
    years: List[str] = []
    for row in row_texts[:8]:
        tokens = YEAR_TOKEN_RULE.findall(_norm(row))
        if len(tokens) >= 3:
            years = tokens
            break
    if years:
        # normalize like 2026e -> 2026E
        years = [y.upper() for y in years]
        return years, False
    return CANONICAL_YEARS, True


def extract_metric_candidates_from_row_text(extracted_tables: List[ExtractedTable]) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = []
    unmatched_rows: List[Dict[str, Any]] = []
    parse_warnings: List[Dict[str, Any]] = []
    year_inferred_count = 0
    numeric_count_mismatch_count = 0
    matched_metric_row_count = 0
    total_row_text_count = 0

    for et in extracted_tables:
        row_texts = getattr(et, "row_texts", None)
        if not isinstance(row_texts, list) or len(row_texts) == 0:
            row_texts = [x.get("text", "") for x in et.cells if int(x.get("col", 0)) == 0] if et.cells else []
            if not row_texts and et.raw_text:
                row_texts = [x.strip() for x in et.raw_text.splitlines() if x.strip()]

        row_texts = [_norm(x) for x in row_texts if _norm(x)]
        total_row_text_count += len(row_texts)
        years, inferred = _detect_years(row_texts)
        if inferred:
            year_inferred_count += 1

        for ridx, row in enumerate(row_texts):
            metric_code, matched_kw = _metric_match(row)
            if not metric_code:
                unmatched_rows.append(
                    {
                        "source_file": et.source_doc_name,
                        "extracted_table_id": et.extracted_table_id,
                        "row_index": ridx,
                        "row_text": row,
                    }
                )
                continue

            matched_metric_row_count += 1
            nums = [_normalize_value(x) for x in NUM_TOKEN_RULE.findall(row)]
            if len(nums) == 0:
                parse_warnings.append(
                    {
                        "source_file": et.source_doc_name,
                        "extracted_table_id": et.extracted_table_id,
                        "row_index": ridx,
                        "warning_code": "NO_NUMERIC_FOUND",
                        "warning_message": row,
                    }
                )
                unmatched_rows.append(
                    {
                        "source_file": et.source_doc_name,
                        "extracted_table_id": et.extracted_table_id,
                        "row_index": ridx,
                        "row_text": row,
                    }
                )
                continue

            risk_tags = ["ROW_TEXT_ONLY"]
            if inferred:
                risk_tags.append("YEAR_INFERRED")
            if len(nums) != len(years):
                risk_tags.append("NUMERIC_COUNT_MISMATCH")
                numeric_count_mismatch_count += 1

            # align by min length
            n = min(len(nums), len(years))
            if n == 0:
                continue
            for i in range(n):
                raw_value = nums[i]
                normalized_value = raw_value.replace(",", "")
                c = {
                    "source_file": et.source_doc_name,
                    "extracted_table_id": et.extracted_table_id,
                    "row_index": ridx,
                    "row_text": row,
                    "metric_code": metric_code,
                    "raw_metric_name": matched_kw,
                    "year": years[i],
                    "raw_value": raw_value,
                    "normalized_value": normalized_value,
                    "raw_unit": "",
                    "alignment_status": "ALIGNED" if len(nums) == len(years) else "PARTIAL_ALIGNED",
                    "risk_tags": "|".join(risk_tags),
                    "confidence": "medium" if "NUMERIC_COUNT_MISMATCH" not in risk_tags else "low",
                }
                if raw_value.startswith("-") or "(" in row or "（" in row:
                    c["risk_tags"] = c["risk_tags"] + "|NEGATIVE_PARENTHESES"
                candidates.append(c)

    return {
        "metric_candidate_preview": candidates,
        "parse_warnings": parse_warnings,
        "unmatched_rows": unmatched_rows,
        "year_inferred_count": year_inferred_count,
        "numeric_count_mismatch_count": numeric_count_mismatch_count,
        "matched_metric_row_count": matched_metric_row_count,
        "total_row_text_count": total_row_text_count,
    }

