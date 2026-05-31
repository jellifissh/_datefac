from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd

from datefac.domain.metric_candidate import MetricCandidate


KNOWN_METRIC_MAP: Dict[str, str] = {
    "net_profit": "Net Profit",
    "asset_impairment_provision": "Asset Impairment Provision",
    "depreciation_amortization": "Depreciation & Amortization",
    "fair_value_change_loss": "Fair Value Change Loss",
    "finance_expense": "Finance Expense",
    "working_capital_change": "Working Capital Change",
    "other_operating_cf": "Other Operating Cash Flow",
    "operating_cash_flow": "Operating Cash Flow",
    "capex": "Capex",
    "other_investing_cash_flow": "Other Investing Cash Flow",
    "investing_cash_flow": "Investing Cash Flow",
    "equity_financing": "Equity Financing",
    "debt_net_change": "Debt Net Change",
    "dividend_interest_paid": "Dividend & Interest Paid",
    "other_financing_cash_flow": "Other Financing Cash Flow",
    "financing_cash_flow": "Financing Cash Flow",
    "net_cash_change": "Net Cash Change",
    "cash_beginning_balance": "Cash Beginning Balance",
    "cash_ending_balance": "Cash Ending Balance",
    "free_cash_flow_firm": "Free Cash Flow to Firm",
    "free_cash_flow_equity": "Free Cash Flow to Equity",
    "eps": "EPS",
    "roe": "ROE",
    "pe": "PE",
    "pb": "PB",
    "ev_ebitda": "EV/EBITDA",
    "revenue": "Revenue",
    "gross_margin": "Gross Margin",
    "revenue_growth": "Revenue Growth",
    "net_profit_growth": "Net Profit Growth",
    "debt_ratio": "Debt Ratio",
}

PERCENT_METRICS = {"roe", "gross_margin", "revenue_growth", "net_profit_growth", "debt_ratio"}
MULTIPLE_METRICS = {"pe", "pb", "ev_ebitda"}
MONETARY_METRICS = {
    "net_profit",
    "asset_impairment_provision",
    "depreciation_amortization",
    "fair_value_change_loss",
    "finance_expense",
    "working_capital_change",
    "other_operating_cf",
    "operating_cash_flow",
    "capex",
    "other_investing_cash_flow",
    "investing_cash_flow",
    "equity_financing",
    "debt_net_change",
    "dividend_interest_paid",
    "other_financing_cash_flow",
    "financing_cash_flow",
    "net_cash_change",
    "cash_beginning_balance",
    "cash_ending_balance",
    "free_cash_flow_firm",
    "free_cash_flow_equity",
    "revenue",
}
MEANINGLESS_RAW_VALUES = {"", "--", "—", "N/A", "NA", "nan", "None"}
YEAR_RULE = re.compile(r"^(20\d{2})([AE])?$", re.IGNORECASE)
PERCENT_RULE = re.compile(r"^\(?-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%\)?$")
NUMERIC_RULE = re.compile(r"^\(?-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\)?$")
HEADER_YEAR_RULE = re.compile(r"\b20\d{2}[AEae]?\b")
CASHFLOW_TITLE_RULE = re.compile(r"现金流量表", re.IGNORECASE)


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _parse_confidence(v: Any) -> float:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return 0.0
    if isinstance(v, (int, float)):
        f = float(v)
        if f > 1:
            return max(0.0, min(1.0, f / 100.0))
        return max(0.0, min(1.0, f))
    t = _norm(v).lower()
    if t == "high":
        return 0.95
    if t == "medium":
        return 0.85
    if t == "low":
        return 0.65
    try:
        return max(0.0, min(1.0, float(t)))
    except Exception:
        return 0.0


def _normalize_value(raw_value: str) -> Tuple[Optional[float], Optional[str], List[str]]:
    tags: List[str] = []
    t = _norm(raw_value)
    if not t or t in MEANINGLESS_RAW_VALUES:
        tags.append("VALUE_MISSING")
        return None, None, tags

    t = t.replace("锛?", "(").replace("锛?", ")")
    is_percent = bool(PERCENT_RULE.match(t))
    if t.startswith("(") and t.endswith(")"):
        t = "-" + t[1:-1]
    t = t.replace(",", "")
    if t.endswith("%"):
        t = t[:-1]
        unit = "%"
    else:
        unit = None
    if is_percent and unit is None:
        unit = "%"

    if not NUMERIC_RULE.match(t) and not re.match(r"^-?\d+(?:\.\d+)?$", t):
        tags.append("VALUE_MISSING")
        return None, unit, tags
    try:
        value = float(t)
        return value, unit, tags
    except Exception:
        tags.append("VALUE_MISSING")
        return None, unit, tags


def _year_and_period(year_raw: str) -> Tuple[str, str, List[str]]:
    tags: List[str] = []
    y = _norm(year_raw).upper()
    if not y:
        tags.append("YEAR_MISSING")
        return "", "", tags
    m = YEAR_RULE.match(y)
    if not m:
        tags.append("INVALID_YEAR")
        return y, "", tags
    year_base = m.group(1)
    suffix = m.group(2) or ""
    if suffix == "E":
        return f"{year_base}E", "estimate", tags
    if suffix == "A":
        return f"{year_base}A", "actual", tags
    return year_base, "actual", tags


def _build_candidate_id(source_stage: str, source_file: str, source_table_id: str, row_index: Any, metric_code: str, year: str, raw_value: str) -> str:
    payload = "|".join(
        [
            _norm(source_stage),
            _norm(source_file),
            _norm(source_table_id),
            _norm(row_index),
            _norm(metric_code),
            _norm(year),
            _norm(raw_value),
        ]
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:24]


def _split_risk_tags(v: Any) -> List[str]:
    t = _norm(v)
    if not t:
        return []
    return [x.strip() for x in t.split("|") if x.strip()]


def _is_noise_leak(row_text: str) -> bool:
    low = _norm(row_text).lower()
    if "cell_bbox" in low:
        return True
    if low.startswith("{"):
        return True
    if "<table" in low or "<td" in low or "<html" in low:
        return True
    return False


def _read_sheet_safe(path: Path, name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, sheet_name=name)
    except Exception:
        return pd.DataFrame()


def _detect_table_context(in_excel: Path) -> Dict[str, Any]:
    cleaned_df = _read_sheet_safe(in_excel, "cleaned_row_texts")
    table_header_years: Set[str] = set()
    table_title = ""
    table_unit = ""

    if not cleaned_df.empty and "row_text_cleaned" in cleaned_df.columns:
        for txt in cleaned_df["row_text_cleaned"].astype(str).tolist():
            if CASHFLOW_TITLE_RULE.search(txt):
                if not table_title:
                    table_title = txt
                for y in HEADER_YEAR_RULE.findall(txt):
                    table_header_years.add(_norm(y).upper())
            if "百万元" in txt:
                table_unit = "百万元"
            elif not table_unit and "万元" in txt:
                table_unit = "万元"

    return {
        "table_title": table_title,
        "table_unit": table_unit,
        "table_header_years": sorted(table_header_years),
    }


def load_320c4_sources(input_dir: Path) -> Dict[str, Any]:
    in_excel = input_dir / "legacy_ppstructure_row_text_320c4.xlsx"
    if not in_excel.exists():
        return {
            "blocked": True,
            "blocked_code": "BLOCKED_MISSING_320C4_INPUT",
            "blocked_message": f"missing input workbook: {in_excel}",
            "source_candidate_rows_df": pd.DataFrame(),
            "smoke_passed_candidate_ids": set(),
            "smoke_passed_metric_codes": set(),
            "table_title": "",
            "table_unit": "",
            "table_header_years": [],
        }

    source_candidate_rows_df = _read_sheet_safe(in_excel, "metric_candidate_preview")
    evs_df = _read_sheet_safe(in_excel, "expected_vs_actual_matrix")
    smoke_passed_candidate_ids: Set[str] = set()
    smoke_passed_metric_codes: Set[str] = set()
    if not evs_df.empty:
        for _, row in evs_df.iterrows():
            if _norm(row.get("pass_fail")).upper() != "PASS":
                continue
            metric_code = _norm(row.get("expected_metric_code"))
            if metric_code:
                smoke_passed_metric_codes.add(metric_code)
            ids = _norm(row.get("matched_candidate_row_ids"))
            if ids:
                for cid in ids.split("|"):
                    c = _norm(cid)
                    if c:
                        smoke_passed_candidate_ids.add(c)

    ctx = _detect_table_context(in_excel)
    return {
        "blocked": False,
        "blocked_code": "",
        "blocked_message": "",
        "source_candidate_rows_df": source_candidate_rows_df,
        "smoke_passed_candidate_ids": smoke_passed_candidate_ids,
        "smoke_passed_metric_codes": smoke_passed_metric_codes,
        "table_title": ctx["table_title"],
        "table_unit": ctx["table_unit"],
        "table_header_years": ctx["table_header_years"],
    }


def _infer_unit_and_currency(
    metric_code: str,
    source_row_text: str,
    unit_from_value: Optional[str],
    table_title: str,
    table_unit: str,
) -> Tuple[Optional[str], str, Optional[str], List[str]]:
    tags: List[str] = []
    txt = _norm(source_row_text)
    txt_low = txt.lower()
    title_low = _norm(table_title).lower()
    currency: Optional[str] = None
    if ("人民币" in txt) or ("人民币" in table_title) or ("rmb" in txt_low) or ("cny" in txt_low):
        currency = "CNY"

    if unit_from_value:
        return unit_from_value, "VALUE_TOKEN", currency, tags
    if metric_code in PERCENT_METRICS:
        return "%", "METRIC_SEMANTIC", currency, tags
    if metric_code in MULTIPLE_METRICS:
        return "x", "METRIC_SEMANTIC", currency, tags
    if metric_code == "eps":
        return "yuan_per_share", "METRIC_SEMANTIC", currency, tags

    if metric_code in MONETARY_METRICS:
        if "百万元" in txt or "百万元" in table_title or table_unit == "百万元":
            return "百万元", "TABLE_TITLE", currency, tags
        if "万元" in txt or "万元" in table_title or table_unit == "万元":
            return "万元", "TABLE_TITLE", currency, tags
        if "元" in txt or "元" in table_title:
            return "元", "TABLE_TITLE", currency, tags
        tags.append("UNIT_UNKNOWN")
        return None, "UNKNOWN", currency, tags
    return None, "UNKNOWN", currency, tags


def _determine_year_source(year_norm: str, table_header_years: Set[str], smoke_passed: bool) -> str:
    yn = _norm(year_norm).upper()
    if yn in table_header_years:
        return "TABLE_HEADER"
    if yn.endswith("A") and yn[:-1] in table_header_years:
        return "TABLE_HEADER"
    if smoke_passed:
        return "SMOKE_CHECK_CONTEXT"
    return "INFERRED_SEQUENCE"


def map_row_text_candidates(
    source_candidate_rows_df: pd.DataFrame,
    table_title: str,
    table_unit: str,
    table_header_years: Set[str],
    smoke_passed_candidate_ids: Set[str],
    smoke_passed_metric_codes: Set[str],
) -> Tuple[List[MetricCandidate], List[Dict[str, Any]], List[Dict[str, Any]]]:
    candidates: List[MetricCandidate] = []
    mapping_audit_rows: List[Dict[str, Any]] = []
    context_audit_rows: List[Dict[str, Any]] = []

    if source_candidate_rows_df.empty:
        return candidates, mapping_audit_rows, context_audit_rows

    known_cols = {
        "candidate_row_id",
        "source_file",
        "extracted_table_id",
        "row_index",
        "row_text",
        "metric_code",
        "raw_metric_name",
        "year",
        "raw_value",
        "normalized_value",
        "raw_unit",
        "alignment_status",
        "risk_tags",
        "confidence",
        "source_row_text",
        "repaired_row_text",
        "repair_trace_id",
    }

    for _, row in source_candidate_rows_df.iterrows():
        row_dict = row.to_dict()
        source_row_text = _norm(row_dict.get("source_row_text") or row_dict.get("row_text"))
        metric_code = _norm(row_dict.get("metric_code"))
        raw_metric_name = _norm(row_dict.get("raw_metric_name"))
        year_norm, period_type, year_tags = _year_and_period(_norm(row_dict.get("year")))
        raw_value = _norm(row_dict.get("raw_value"))
        value_norm, value_unit, value_tags = _normalize_value(raw_value)
        confidence = _parse_confidence(row_dict.get("confidence"))
        risk_tags = _split_risk_tags(row_dict.get("risk_tags"))

        source_candidate_row_id = _norm(row_dict.get("candidate_row_id"))
        smoke_passed = (source_candidate_row_id in smoke_passed_candidate_ids) or (metric_code in smoke_passed_metric_codes)
        year_source = _determine_year_source(year_norm=year_norm, table_header_years=table_header_years, smoke_passed=smoke_passed)
        unit, unit_source, currency, unit_tags = _infer_unit_and_currency(
            metric_code=metric_code,
            source_row_text=source_row_text,
            unit_from_value=value_unit,
            table_title=table_title,
            table_unit=table_unit,
        )

        if confidence < 0.8:
            risk_tags.append("LOW_CONFIDENCE")
        if _is_noise_leak(source_row_text):
            risk_tags.append("NOISE_LEAK_BBOX_HTML")
        if metric_code not in KNOWN_METRIC_MAP:
            risk_tags.append("UNKNOWN_METRIC_CODE")
        if _norm(row_dict.get("alignment_status")) != "ALIGNED":
            risk_tags.append("NUMERIC_COUNT_MISMATCH")

        risk_tags.extend(year_tags)
        risk_tags.extend(value_tags)
        risk_tags.extend(unit_tags)
        if smoke_passed:
            risk_tags.append("SMOKE_VERIFIED_ROW")
        else:
            risk_tags.append("SMOKE_CHECK_FAILED")

        if year_source in {"TABLE_HEADER", "SMOKE_CHECK_CONTEXT"}:
            risk_tags = [x for x in risk_tags if x != "YEAR_INFERRED"]
        if unit_source == "TABLE_TITLE":
            risk_tags = [x for x in risk_tags if x != "UNIT_UNKNOWN"]
        risk_tags = sorted(set([x for x in risk_tags if x]))

        source_file = _norm(row_dict.get("source_file"))
        source_table_id = _norm(row_dict.get("extracted_table_id"))
        source_row_index = row_dict.get("row_index")
        candidate_id = _build_candidate_id(
            source_stage="mineru_ppstructure_row_text_320c4",
            source_file=source_file,
            source_table_id=source_table_id,
            row_index=source_row_index,
            metric_code=metric_code,
            year=year_norm,
            raw_value=raw_value,
        )
        extra_meta = {}
        for k, v in row_dict.items():
            if k not in known_cols:
                extra_meta[k] = v

        provenance = {
            "source_candidate_row_id": source_candidate_row_id,
            "alignment_status": _norm(row_dict.get("alignment_status")),
            "raw_row": row_dict,
            "source_meta_json": extra_meta,
            "year_source": year_source,
            "unit_source": unit_source,
            "table_title": table_title,
            "table_unit": table_unit,
            "smoke_check_status": "PASSED" if smoke_passed else "FAILED",
            "smoke_check_source": "320C4_EXPECTED_VS_ACTUAL" if smoke_passed else "",
        }

        c = MetricCandidate(
            candidate_id=candidate_id,
            source_stage="mineru_ppstructure_row_text_320c4",
            source_file=source_file,
            source_doc_name=Path(source_file).stem if source_file else None,
            source_table_id=source_table_id or None,
            source_row_index=int(source_row_index) if str(source_row_index).strip() not in {"", "nan", "None"} else None,
            source_row_text=source_row_text,
            metric_code=metric_code,
            canonical_metric_name=KNOWN_METRIC_MAP.get(metric_code, metric_code),
            raw_metric_name=raw_metric_name,
            year=year_norm,
            period_type=period_type or "unknown",
            raw_value=raw_value,
            normalized_value=value_norm,
            unit=unit,
            unit_source=unit_source,
            currency=currency,
            confidence=confidence,
            year_source=year_source,
            smoke_check_status="PASSED" if smoke_passed else "FAILED",
            smoke_check_source="320C4_EXPECTED_VS_ACTUAL" if smoke_passed else "",
            table_title=table_title or None,
            table_unit=table_unit or None,
            risk_tags=risk_tags,
            split_decision="review_required_preview",
            split_reason="PENDING_SPLIT",
            provenance_json=provenance,
        )
        candidates.append(c)
        mapping_audit_rows.append(
            {
                "candidate_id": c.candidate_id,
                "source_metric_code": metric_code,
                "canonical_metric_name": c.canonical_metric_name,
                "year": c.year,
                "raw_value": raw_value,
                "normalized_value": c.normalized_value,
                "unit": c.unit,
                "risk_tags": "|".join(c.risk_tags),
            }
        )
        context_audit_rows.append(
            {
                "candidate_id": c.candidate_id,
                "metric_code": c.metric_code,
                "year": c.year,
                "year_source": c.year_source,
                "unit": c.unit,
                "unit_source": c.unit_source,
                "table_title": c.table_title or "",
                "table_unit": c.table_unit or "",
                "smoke_check_status": c.smoke_check_status,
                "smoke_check_source": c.smoke_check_source,
                "risk_tags": "|".join(c.risk_tags),
            }
        )
    return candidates, mapping_audit_rows, context_audit_rows


def resolve_duplicates_and_conflicts(candidates: List[MetricCandidate]) -> Dict[str, Any]:
    key_to_rows: Dict[Tuple[str, str, str, str], List[MetricCandidate]] = {}
    for c in candidates:
        key = (c.source_file, c.source_table_id or "", c.metric_code, c.year)
        key_to_rows.setdefault(key, []).append(c)

    canonical: List[MetricCandidate] = []
    duplicates_rows: List[Dict[str, Any]] = []
    conflicts_rows: List[Dict[str, Any]] = []
    duplicate_same_value_count = 0
    conflict_count = 0

    for key, rows in key_to_rows.items():
        if len(rows) == 1:
            canonical.append(rows[0])
            continue

        values = sorted(set([str(r.normalized_value) for r in rows]))
        if len(values) == 1:
            rows_sorted = sorted(rows, key=lambda x: (-x.confidence, x.candidate_id))
            keep = rows_sorted[0]
            keep.risk_tags = sorted(set(keep.risk_tags + ["DUPLICATE_SAME_VALUE_COLLAPSED"]))
            canonical.append(keep)
            for dup in rows_sorted[1:]:
                dup.split_decision = "rejected_preview"
                dup.split_reason = "DUPLICATE_SAME_VALUE_COLLAPSED"
                duplicates_rows.append(
                    {
                        "group_key": "|".join(key),
                        "kept_candidate_id": keep.candidate_id,
                        "dropped_candidate_id": dup.candidate_id,
                        "metric_code": dup.metric_code,
                        "year": dup.year,
                        "normalized_value": dup.normalized_value,
                        "drop_reason": "DUPLICATE_SAME_VALUE_COLLAPSED",
                    }
                )
                duplicate_same_value_count += 1
            continue

        conflict_count += 1
        for r in rows:
            r.risk_tags = sorted(set(r.risk_tags + ["VALUE_CONFLICT"]))
            r.split_decision = "review_required_preview"
            r.split_reason = "VALUE_CONFLICT"
            canonical.append(r)
            conflicts_rows.append(
                {
                    "group_key": "|".join(key),
                    "candidate_id": r.candidate_id,
                    "metric_code": r.metric_code,
                    "year": r.year,
                    "normalized_value": r.normalized_value,
                    "confidence": r.confidence,
                    "risk_tags": "|".join(r.risk_tags),
                }
            )

    return {
        "canonical_candidates": canonical,
        "duplicates_rows": duplicates_rows,
        "conflicts_rows": conflicts_rows,
        "duplicate_same_value_count": duplicate_same_value_count,
        "conflict_count": conflict_count,
    }


def candidates_to_dataframe(candidates: Iterable[MetricCandidate]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for c in candidates:
        d = c.to_dict()
        d["risk_tags"] = "|".join(c.risk_tags)
        d["provenance_json"] = json.dumps(c.provenance_json, ensure_ascii=False)
        rows.append(d)
    return pd.DataFrame(rows)
