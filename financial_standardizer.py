import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_FINANCIAL_STANDARDIZATION_CONFIG: Dict[str, object] = {
    "enabled": True,
    "output_report": True,
    "log_detail": True,
}

STANDARD_METRIC_ALIASES: Dict[str, List[str]] = {
    "营业收入": ["营业收入"],
    "归属母公司净利润": [
        "归属母公司净利润",
        "归属于母公司净利润",
        "归属母公司股东净利润",
        "归属于母公司股东的净利润",
        "归属于母公司所有者的净利润",
        "归属于上市公司股东的净利润",
        "归母净利润",
        "归母净利",
        "母公司股东净利润",
    ],
    "毛利率": ["毛利率", "毛利率(%)", "毛利率%"],
    "ROE": ["ROE", "ROE(%)", "ROE %"],
    "每股收益": [
        "每股收益",
        "EPS",
        "EPS(元)",
        "EPS（元）",
        "EPS（摊薄/元）",
        "EPS(摊薄/元)",
        "EPS摊薄",
        "摊薄EPS",
        "摊薄每股收益",
        "基本每股收益",
        "稀释每股收益",
        "每股收益(最新摊薄)",
    ],
    "P/E": ["P/E", "PE"],
    "P/B": ["P/B", "PB"],
    "EV/EBITDA": ["EV/EBITDA", "EVEBITDA"],
}

SOURCE_TYPE_PRIORITY: Dict[str, int] = {
    "主要财务指标": 1,
    "财务比率表": 2,
    "财务三表混合表": 3,
    "利润表": 4,
    "未知表": 5,
}

YEAR_COLUMN_RE = re.compile(r"^(20\d{2})([A-Z])?$")
YEAR_TOKEN_RE = re.compile(r"(20\d{2})([AE])?", re.IGNORECASE)
YOY_GUARD_TERMS = ("同比", "增速", "增长率", "YOY")
YOY_GUARD_METRICS = {"营业收入", "归属母公司净利润"}
NET_PROFIT_EXCLUDE_TERMS = (
    "净利润增长率",
    "归母净利润同比",
    "归母净利润增速",
    "归母净利润增长率",
    "扣非归母净利润",
    "少数股东损益",
)
EV_PREFIXES = ("EV/EBITDA", "EVEBITDA")
EV_OTHER_METRIC_TERMS = (
    "营业收入",
    "归属母公司",
    "归母净利润",
    "毛利率",
    "ROE",
    "EPS",
    "每股收益",
    "P/E",
    "PE",
    "P/B",
    "PB",
)
VALUE_LABEL_TOKENS = (
    "营业收入",
    "净利润",
    "归母",
    "归属母公司",
    "毛利率",
    "ROE",
    "EPS",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "税金",
    "营业成本",
    "资产",
    "负债",
    "现金流",
    "现金流量",
)
AMOUNT_METRICS = {"营业收入", "归属母公司净利润"}
RATIO_METRICS = {"毛利率", "ROE"}
EPS_METRICS = {"每股收益"}
MULTIPLE_METRICS = {"P/E", "P/B", "EV/EBITDA"}
AMOUNT_FORBID_TOKENS = ("税金", "资产", "负债", "现金流", "现金流量", "营业成本")
VALUE_REPAIR_FORBID_TOKENS = (
    "税金",
    "营业成本",
    "成本",
    "资产",
    "负债",
    "现金流",
    "少数股东",
    "扣非",
    "减值",
    "费用",
)
FORBIDDEN_ACCOUNT_ROW_TERMS = (
    "管理费用",
    "财务费用",
    "销售费用",
    "研发费用",
    "应收票据",
    "应收账款",
    "预付款项",
    "存货",
    "固定资产",
    "无形资产",
    "资产总计",
    "负债合计",
    "短期借款",
    "应付账款",
    "现金流量",
    "经营性现金流",
    "投资收益",
    "税金及附加",
)
SEMANTIC_GUARD_METRICS = {"毛利率", "ROE", "每股收益", "P/E", "P/B", "EV/EBITDA"}


def _resolve_config(config=None) -> Dict[str, object]:
    merged = DEFAULT_FINANCIAL_STANDARDIZATION_CONFIG.copy()
    if config:
        merged.update(config)
    return merged


def _normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _compact_text(value) -> str:
    text = _normalize_text(value)
    text = text.replace("（", "(").replace("）", ")").replace("％", "%")
    text = re.sub(r"\s+", "", text)
    return text.upper()


def _clean_metric_label_noise(label: str) -> str:
    text = _normalize_text(label)
    if not text:
        return ""
    text = text.replace("（", "(").replace("）", ")").replace("／", "/")
    text = re.sub(r"\s+", " ", text).strip()

    compact = _compact_text(text)
    has_metric_token = any(
        token in compact
        for token in (
            "EV/EBITDA",
            "EVEBITDA",
            "EPS",
            "ROE",
            "P/E",
            "P/B",
            "营业收入",
            "归属母公司",
            "归母净利润",
            "毛利率",
            "每股收益",
        )
    )
    if not has_metric_token:
        return text

    # Remove trailing numeric-like glue noise for metric labels only.
    text = re.sub(
        r"([\s\|,:：;；]+[-+]?\d*\.?\d+(?:[%％])?)+\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    return text


def _match_ev_prefix_with_noise(label: str) -> bool:
    compact = _compact_text(label)
    if not compact:
        return False

    prefix = ""
    for p in EV_PREFIXES:
        if compact.startswith(p):
            prefix = p
            break
    if not prefix:
        return False

    for term in EV_OTHER_METRIC_TERMS:
        if _compact_text(term) in compact:
            return False

    tail = compact[len(prefix) :]
    if not tail:
        return True
    # Allow only numeric/punctuation glue noise after EV prefix.
    return bool(re.fullmatch(r"[0-9\.\,\:\;\|\-_/\\]+", tail))


def _normalize_year_token(value: str) -> str:
    compact = _compact_text(value)
    if not compact:
        return ""
    compact = compact.replace("年", "")
    compact = re.sub(r"[（）()\[\]{}<>《》【】.,。:：;；'\"`·]", "", compact)
    match = YEAR_TOKEN_RE.search(compact)
    if not match:
        return ""
    year = match.group(1)
    suffix = (match.group(2) or "").upper()
    normalized = f"{year}{suffix}"
    return normalized if YEAR_COLUMN_RE.fullmatch(normalized) else ""


def _is_year_column(column_name: str) -> bool:
    return bool(_normalize_year_token(column_name))


def _make_unique_columns(columns: List[str]) -> List[str]:
    seen: Dict[str, int] = {}
    result: List[str] = []
    for col in columns:
        base = _normalize_text(col) or "未命名列"
        if base not in seen:
            seen[base] = 0
            result.append(base)
        else:
            seen[base] += 1
            result.append(f"{base}.{seen[base]}")
    return result


def _extract_year_columns(df: pd.DataFrame) -> List[Tuple[str, str]]:
    year_columns = []
    for col in df.columns.tolist():
        token = _normalize_year_token(str(col))
        if token:
            year_columns.append((str(col), token))
    return year_columns


def _year_sort_key(year_value: str) -> Tuple[int, str]:
    compact = _compact_text(year_value)
    match = YEAR_COLUMN_RE.fullmatch(compact)
    if not match:
        return (9999, compact)
    return (int(match.group(1)), match.group(2) or "")


def _is_probably_numeric(text: str) -> bool:
    if not text:
        return False
    compact = text.replace(",", "").replace("%", "").replace(" ", "")
    return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?", compact))


def _extract_numeric_tokens(text: str) -> List[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []
    return re.findall(r"[-+]?\d*\.?\d+", normalized)


def _parse_numeric_value(raw_value: str) -> Tuple[Optional[float], str]:
    raw = _normalize_text(raw_value)
    if not raw:
        return None, "empty"
    compact = raw.replace(",", "").replace(" ", "").replace("（", "(").replace("）", ")")
    compact = compact.replace("％", "%")
    is_percent = compact.endswith("%")
    if is_percent:
        compact = compact[:-1]
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", compact):
        return float(compact), ("percent" if is_percent else "numeric")
    tokens = re.findall(r"[-+]?\d+(?:\.\d+)?", compact)
    if tokens:
        return float(tokens[0]), "mixed_text_numeric"
    return None, "text"


def _count_issue_flags(issue_flags: str) -> int:
    flags = [x for x in _normalize_text(issue_flags).split("|") if x]
    return len(flags)


def _table_row_sort_key(value) -> int:
    text = _normalize_text(value)
    if not text:
        return 999999
    m = re.search(r"-?\d+", text)
    if not m:
        return 999999
    try:
        return int(m.group(0))
    except Exception:
        return 999999


def _value_status_rank(status: str) -> int:
    order = {"valid": 0, "suspicious": 1, "invalid": 2, "empty": 3}
    return order.get(_normalize_text(status), 9)


def _raw_column_priority(raw_col: str) -> Tuple[int, int, str]:
    text = _normalize_text(raw_col)
    if not text:
        return (9, 9999, "")
    m = re.match(r"^(.*?)(?:\.(\d+))?$", text)
    if not m:
        return (9, 9999, text)
    suffix = m.group(2)
    if suffix is None:
        return (0, 0, text)
    try:
        return (1, int(suffix), text)
    except Exception:
        return (1, 9999, text)


def _decouple_amount_percent_year_values(
    year_values: Dict[str, str],
) -> Tuple[Dict[str, str], List[str]]:
    normalized_groups: Dict[str, List[Dict[str, object]]] = {}
    selected_values: Dict[str, str] = {}
    issue_flags: List[str] = []
    did_decouple = False
    ignored_percent = False

    for raw_col, raw_val in (year_values or {}).items():
        raw = _normalize_text(raw_val)
        if not raw:
            continue
        normalized_year = _normalize_year_token(str(raw_col))
        if not normalized_year:
            selected_values[raw_col] = raw
            continue
        parsed, parse_type = _parse_numeric_value(raw)
        normalized_groups.setdefault(normalized_year, []).append(
            {
                "raw_col": str(raw_col),
                "raw_val": raw,
                "parsed": parsed,
                "parse_type": parse_type,
                "has_percent": ("%" in raw or "％" in raw),
            }
        )

    for _, items in normalized_groups.items():
        if not items:
            continue

        sorted_items = sorted(items, key=lambda x: _raw_column_priority(str(x.get("raw_col", ""))))
        non_percent_numeric = [
            item
            for item in sorted_items
            if (item.get("parsed") is not None) and (not bool(item.get("has_percent", False)))
        ]
        percent_like = [item for item in sorted_items if bool(item.get("has_percent", False))]

        if non_percent_numeric and percent_like:
            chosen = non_percent_numeric[0]
            selected_values[str(chosen["raw_col"])] = _normalize_text(chosen.get("raw_val", ""))
            did_decouple = True
            ignored_percent = True
            continue

        chosen = sorted_items[0]
        selected_values[str(chosen["raw_col"])] = _normalize_text(chosen.get("raw_val", ""))

    if did_decouple:
        issue_flags.append("amount_percent_group_decoupled")
    if ignored_percent:
        issue_flags.append("ignored_percent_year_group")
    return selected_values, issue_flags


def _validate_metric_candidate_values(
    standard_metric: str,
    year_values: Dict[str, str],
    source_row_label: Optional[str] = None,
) -> Dict[str, object]:
    parsed_values: Dict[str, object] = {}
    issues: List[str] = []
    valid_year_count = 0
    invalid_year_count = 0

    row_label = _normalize_text(source_row_label)
    row_label_compact = _compact_text(row_label)
    has_non_empty = False

    validation_year_values = {k: _normalize_text(v) for k, v in (year_values or {}).items()}
    decouple_flags: List[str] = []
    if standard_metric in AMOUNT_METRICS:
        validation_year_values, decouple_flags = _decouple_amount_percent_year_values(validation_year_values)
        issues.extend(decouple_flags)

    semantic_mismatch_detected = False

    for year_col, raw_val in validation_year_values.items():
        raw = _normalize_text(raw_val)
        if not raw:
            continue
        has_non_empty = True
        parsed, parse_type = _parse_numeric_value(raw)
        parsed_values[year_col] = parsed if parsed is not None else ""

        raw_compact = _compact_text(raw)
        local_invalid = False
        local_suspicious = False

        if any(_compact_text(tok) in raw_compact for tok in VALUE_LABEL_TOKENS):
            issues.append("label_value_glued")
            local_suspicious = True

        if parse_type == "mixed_text_numeric":
            issues.append("mixed_text_values")
            local_suspicious = True
            if standard_metric in MULTIPLE_METRICS:
                issues.append("multiple_mixed_text_source")
                local_invalid = True

        if standard_metric in SEMANTIC_GUARD_METRICS:
            raw_compact = _compact_text(raw)
            if any(_compact_text(term) in raw_compact for term in FORBIDDEN_ACCOUNT_ROW_TERMS):
                issues.append("source_row_semantic_mismatch")
                issues.append("forbidden_account_row_as_metric_source")
                semantic_mismatch_detected = True
                local_invalid = True

        if parsed is None:
            issues.append("non_numeric_value")
            invalid_year_count += 1
            continue

        if standard_metric in AMOUNT_METRICS:
            if "%" in raw or "％" in raw:
                issues.append("amount_has_percent")
                local_invalid = True
            if any(tok in raw for tok in AMOUNT_FORBID_TOKENS):
                issues.append("likely_wrong_row")
                local_suspicious = True
            if abs(parsed) > 1e12:
                issues.append("suspicious_amount_extreme")
                local_suspicious = True

        if standard_metric in RATIO_METRICS:
            if abs(parsed) > 300:
                issues.append("invalid_ratio_too_large")
                local_invalid = True
            if any(tok in row_label for tok in ("资产", "负债", "现金流", "现金流量")):
                issues.append("likely_wrong_row")
                local_suspicious = True

        if standard_metric in EPS_METRICS:
            if abs(parsed) > 100:
                issues.append("invalid_eps_too_large")
                local_invalid = True
            if any(tok in row_label for tok in ("资产", "负债", "现金流", "现金流量")):
                issues.append("likely_wrong_row")
                local_suspicious = True

        if standard_metric in MULTIPLE_METRICS:
            if standard_metric == "P/B" and abs(parsed) > 100:
                issues.append("suspicious_pb_too_large")
                local_suspicious = True
            if standard_metric in {"P/E", "EV/EBITDA"} and abs(parsed) > 1000:
                issues.append("suspicious_multiple_extreme")
                local_suspicious = True

        if local_invalid:
            invalid_year_count += 1
        elif local_suspicious:
            pass
        else:
            valid_year_count += 1

    uniq_issues: List[str] = []
    seen = set()
    for item in issues:
        if item and item not in seen:
            uniq_issues.append(item)
            seen.add(item)

    hard_invalid_flags = {
        "label_value_glued",
        "non_numeric_value",
        "amount_has_percent",
        "invalid_ratio_too_large",
        "invalid_eps_too_large",
        "multiple_mixed_text_source",
        "source_row_semantic_mismatch",
        "forbidden_account_row_as_metric_source",
    }
    if standard_metric in SEMANTIC_GUARD_METRICS and semantic_mismatch_detected:
        issue_set = set(uniq_issues)
        issue_set.add("source_row_semantic_mismatch")
        issue_set.add("forbidden_account_row_as_metric_source")
        uniq_issues = [x for x in uniq_issues if x]
        if "source_row_semantic_mismatch" not in uniq_issues:
            uniq_issues.append("source_row_semantic_mismatch")
        if "forbidden_account_row_as_metric_source" not in uniq_issues:
            uniq_issues.append("forbidden_account_row_as_metric_source")
    issue_set = set(uniq_issues)
    if not has_non_empty:
        status = "empty"
    elif issue_set & hard_invalid_flags:
        # Candidate-level hard block: do not allow obviously wrong values into wide table.
        status = "invalid"
    elif invalid_year_count > 0:
        status = "suspicious"
    elif uniq_issues:
        status = "suspicious"
    else:
        status = "valid"

    return {
        "value_validation_status": status,
        "value_issue_flags": "|".join(uniq_issues),
        "valid_year_count": int(valid_year_count),
        "invalid_year_count": int(invalid_year_count),
        "parsed_values": parsed_values,
        "selected_year_values": validation_year_values,
    }


def _metric_strong_aliases(standard_metric: str, matched_alias: Optional[str] = None) -> List[str]:
    aliases = []
    for alias in STANDARD_METRIC_ALIASES.get(standard_metric, []):
        text = _normalize_text(alias)
        if text:
            aliases.append(text)
    if _normalize_text(matched_alias):
        aliases.append(_normalize_text(matched_alias))

    if standard_metric == "归属母公司净利润":
        aliases.extend(
            [
                "归母净利润",
                "归母净利",
                "归属于母公司净利润",
                "归属于母公司股东的净利润",
            ]
        )
    if standard_metric == "EV/EBITDA":
        aliases.extend(["EV EBITDA", "EVEBITDA"])
    if standard_metric == "每股收益":
        aliases.extend(["EPS（元）", "EPS(元)", "EPS（摊薄/元）", "EPS(摊薄/元)"])

    uniq: List[str] = []
    seen = set()
    for alias in aliases + [standard_metric]:
        if alias and alias not in seen:
            seen.add(alias)
            uniq.append(alias)
    return uniq


def _contains_forbid_repair_context(text: str) -> bool:
    value = _normalize_text(text)
    if not value:
        return False
    return any(tok in value for tok in VALUE_REPAIR_FORBID_TOKENS)


def _raw_starts_with_alias(raw_value: str, alias_texts: List[str]) -> bool:
    raw_compact = _compact_text(raw_value)
    if not raw_compact:
        return False
    for alias in alias_texts:
        compact_alias = _compact_text(alias)
        if compact_alias and raw_compact.startswith(compact_alias):
            return True
    return False


def _is_label_high_match(label: str, alias_texts: List[str]) -> bool:
    label_compact = _compact_text(label)
    if not label_compact:
        return False
    for alias in alias_texts:
        compact_alias = _compact_text(alias)
        if not compact_alias:
            continue
        if label_compact == compact_alias:
            return True
        if compact_alias in label_compact and len(label_compact) - len(compact_alias) <= 3:
            return True
    return False


def _safe_numeric_to_text(number: Optional[float]) -> str:
    if number is None:
        return ""
    try:
        value = float(number)
    except Exception:
        return ""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return str(value)


def _repair_metric_candidate_values(
    standard_metric: str,
    year_values: Dict[str, str],
    source_row_label: Optional[str] = None,
    matched_alias: Optional[str] = None,
) -> Dict[str, object]:
    repaired_values = {k: _normalize_text(v) for k, v in (year_values or {}).items()}
    alias_texts = _metric_strong_aliases(standard_metric, matched_alias=matched_alias)
    source_label = _normalize_text(source_row_label)
    source_label_match = _is_label_high_match(source_label, alias_texts)

    repair_applied = False
    repaired_year_count = 0
    issue_flags: List[str] = []
    used_strategies: List[str] = []

    source_has_forbid_context = _contains_forbid_repair_context(source_label)

    for year_col, raw_val in repaired_values.items():
        raw = _normalize_text(raw_val)
        if not raw:
            continue
        raw_has_forbid_context = _contains_forbid_repair_context(raw)
        if source_has_forbid_context or raw_has_forbid_context:
            issue_flags.append("forbid_context_no_repair")
            continue
        if standard_metric in AMOUNT_METRICS and ("%" in raw or "％" in raw):
            issue_flags.append("amount_percent_no_repair")
            continue

        numeric_tokens = re.findall(r"[-+]?\d+(?:\.\d+)?", raw)
        repaired_number: Optional[float] = None
        strategy = ""

        # Strategy 1: trailing number from matching label prefix.
        if _raw_starts_with_alias(raw, alias_texts) and numeric_tokens:
            try:
                repaired_number = float(numeric_tokens[-1])
                strategy = "trailing_number_from_matching_label"
            except Exception:
                repaired_number = None

        # Strategy 2: exact/synonym row label + one text label and one number.
        if repaired_number is None:
            if source_label_match and _raw_starts_with_alias(raw, alias_texts) and len(numeric_tokens) == 1:
                try:
                    repaired_number = float(numeric_tokens[0])
                    strategy = "numeric_tail_if_source_label_exact"
                except Exception:
                    repaired_number = None

        if repaired_number is None:
            continue

        # Safety guard: do not "repair" obviously wrong extreme values.
        if standard_metric in RATIO_METRICS and abs(repaired_number) > 300:
            issue_flags.append("ratio_extreme_no_repair")
            continue
        if standard_metric in EPS_METRICS and abs(repaired_number) > 100:
            issue_flags.append("eps_extreme_no_repair")
            continue

        repaired_text = _safe_numeric_to_text(repaired_number)
        if not repaired_text:
            issue_flags.append("repair_parse_failed")
            continue

        if repaired_text != raw:
            repaired_values[year_col] = repaired_text
            repair_applied = True
            repaired_year_count += 1
            used_strategies.append(strategy)

    unique_flags: List[str] = []
    seen_flags = set()
    for flag in issue_flags:
        if flag and flag not in seen_flags:
            unique_flags.append(flag)
            seen_flags.add(flag)

    if not used_strategies:
        repair_strategy = ""
    elif len(set(used_strategies)) == 1:
        repair_strategy = used_strategies[0]
    else:
        repair_strategy = "mixed_strategies"

    return {
        "repaired_year_values": repaired_values,
        "repair_applied": repair_applied,
        "repair_strategy": repair_strategy,
        "repair_issue_flags": "|".join(unique_flags),
        "repaired_year_count": int(repaired_year_count),
    }


def _is_yoy_like_label(label: str) -> bool:
    compact = _compact_text(label)
    if not compact:
        return False
    return any(term in compact for term in YOY_GUARD_TERMS)


def _is_excluded_net_profit_label(label: str) -> bool:
    compact = _compact_text(label)
    if not compact:
        return False
    return any(_compact_text(term) in compact for term in NET_PROFIT_EXCLUDE_TERMS)


def _prepare_df_for_financial_standardization(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, object]]:
    metadata: Dict[str, object] = {
        "header_repaired": False,
        "header_source_row": "",
        "original_columns": "|".join([str(c) for c in df.columns.tolist()]),
        "prepared_columns": "|".join([str(c) for c in df.columns.tolist()]),
        "detected_year_columns": "",
    }

    if df is None or df.empty:
        return df, metadata

    existing_year_columns = _extract_year_columns(df)
    if existing_year_columns:
        metadata["detected_year_columns"] = "|".join([norm for _, norm in existing_year_columns])
        return df, metadata

    scan_rows = min(5, len(df))
    best_row_idx = -1
    best_year_count = 0
    for ridx in range(scan_rows):
        row = df.iloc[ridx]
        tokens = []
        for val in row.tolist():
            token = _normalize_year_token(_normalize_text(val))
            if token:
                tokens.append(token)
        unique_count = len(set(tokens))
        if unique_count > best_year_count:
            best_year_count = unique_count
            best_row_idx = ridx

    if best_row_idx < 0 or best_year_count < 2:
        return df, metadata

    header_row = df.iloc[best_row_idx]
    new_columns: List[str] = []
    for original_col, header_val in zip(df.columns.tolist(), header_row.tolist()):
        token = _normalize_year_token(_normalize_text(header_val))
        if token:
            new_columns.append(token)
            continue
        candidate = _normalize_text(header_val)
        if candidate:
            new_columns.append(candidate)
        else:
            new_columns.append(str(original_col))
    new_columns = _make_unique_columns(new_columns)

    prepared_df = df.iloc[best_row_idx + 1 :].copy().reset_index(drop=True)
    prepared_df.columns = new_columns

    detected_after = _extract_year_columns(prepared_df)
    metadata["header_repaired"] = True
    metadata["header_source_row"] = int(best_row_idx)
    metadata["prepared_columns"] = "|".join([str(c) for c in prepared_df.columns.tolist()])
    metadata["detected_year_columns"] = "|".join([norm for _, norm in detected_after])
    return prepared_df, metadata


def _find_row_label(row: pd.Series) -> Tuple[str, str]:
    candidate_columns = row.index.tolist()[:2]
    for col in candidate_columns:
        value = _normalize_text(row[col])
        if not value:
            continue
        if _is_year_column(col):
            continue
        if _is_probably_numeric(value):
            continue
        return value, str(col)
    for col in candidate_columns:
        value = _normalize_text(row[col])
        if value:
            return value, str(col)
    return "", ""


def _is_unit_like_label(text: str) -> bool:
    compact = _compact_text(text)
    if not compact:
        return False
    unit_keywords = ("单位", "币种", "百万", "亿元", "万元", "元")
    return any(k in compact for k in unit_keywords) and len(compact) <= 12


def _find_metric_label_candidates(
    row: pd.Series, max_scan_cols: int = 8
) -> List[Tuple[str, str, Dict[str, object]]]:
    candidates: List[Tuple[str, str, Dict[str, object]]] = []
    seen_metrics = set()
    scan_columns = row.index.tolist()[: max(1, int(max_scan_cols))]
    for col in scan_columns:
        value = _normalize_text(row[col])
        if not value:
            continue
        if _is_probably_numeric(value):
            continue
        metric_match = _match_standard_metric(value)
        if not metric_match:
            if _is_unit_like_label(value):
                continue
            continue
        standard_metric = metric_match.get("standard_metric")
        if standard_metric in seen_metrics:
            continue
        seen_metrics.add(standard_metric)
        candidates.append((value, str(col), metric_match))
    return candidates


def _match_standard_metric(label: str) -> Optional[Dict[str, object]]:
    cleaned_label = _clean_metric_label_noise(label)
    normalized = _normalize_text(cleaned_label)
    compact = _compact_text(cleaned_label)
    if not normalized:
        return None
    is_yoy_like = _is_yoy_like_label(label)
    is_excluded_net_profit = _is_excluded_net_profit_label(label)

    if _match_ev_prefix_with_noise(cleaned_label):
        return {
            "standard_metric": "EV/EBITDA",
            "matched_alias": "EV/EBITDA",
            "match_method": "ev_prefix_noise_guard",
            "confidence": 0.92,
        }

    for standard_metric, aliases in STANDARD_METRIC_ALIASES.items():
        if is_yoy_like and standard_metric in YOY_GUARD_METRICS:
            continue
        if is_excluded_net_profit and standard_metric == "归属母公司净利润":
            continue
        canonical = aliases[0]
        if normalized == canonical:
            return {
                "standard_metric": standard_metric,
                "matched_alias": canonical,
                "match_method": "exact",
                "confidence": 0.95,
            }
        for alias in aliases[1:]:
            if normalized == alias:
                return {
                    "standard_metric": standard_metric,
                    "matched_alias": alias,
                    "match_method": "synonym",
                    "confidence": 0.90,
                }

    for standard_metric, aliases in STANDARD_METRIC_ALIASES.items():
        if is_yoy_like and standard_metric in YOY_GUARD_METRICS:
            continue
        if is_excluded_net_profit and standard_metric == "归属母公司净利润":
            continue
        for alias in aliases:
            if compact == _compact_text(alias):
                return {
                    "standard_metric": standard_metric,
                    "matched_alias": alias,
                    "match_method": "normalized_fuzzy",
                    "confidence": 0.80,
                }
    return None


def _classification_map(classification_results=None) -> Dict[int, Dict[str, object]]:
    if not classification_results:
        return {}
    result_map = {}
    for item in classification_results:
        idx = item.get("table_index")
        if idx is not None:
            result_map[idx] = item
    return result_map


def _source_type_rank(source_table_type: str) -> int:
    if source_table_type in SOURCE_TYPE_PRIORITY:
        return SOURCE_TYPE_PRIORITY[source_table_type]
    if not source_table_type:
        return 99
    return 6


def _build_detail_row(
    metric_match: Dict[str, object],
    values: Dict[str, str],
    year_columns: List[Tuple[str, str]],
    source_table_index: int,
    source_table_type: str,
    source_row_index: int,
    source_row_label: str,
    source_label_column: str,
    label_detect_method: str,
    header_repaired: bool,
    header_source_row: object,
) -> Dict[str, object]:
    non_empty_year_count = sum(1 for raw_col, _ in year_columns if _normalize_text(values.get(raw_col, "")))
    detail_row = {
        "标准指标": metric_match["standard_metric"],
        "source_row_label": source_row_label,
        "source_table_index": source_table_index,
        "source_table_type": source_table_type,
        "source_row_index": source_row_index,
        "source_label_column": source_label_column,
        "label_detect_method": label_detect_method,
        "source_column": ",".join(raw_col for raw_col, _ in year_columns),
        "matched_alias": metric_match["matched_alias"],
        "match_method": metric_match["match_method"],
        "confidence": metric_match["confidence"],
        "non_empty_year_count": non_empty_year_count,
        "header_repaired": header_repaired,
        "header_source_row": header_source_row,
        "raw_year_values": "",
        "value_repair_applied": False,
        "value_repair_strategy": "",
        "value_repair_issue_flags": "",
        "repaired_year_count": 0,
    }
    for raw_col, _ in year_columns:
        detail_row[raw_col] = _normalize_text(values.get(raw_col, ""))
    return detail_row


def standardize_core_financials(df_list, classification_results=None, logger=None, config=None):
    config = _resolve_config(config)
    result_map = _classification_map(classification_results)
    detail_rows: List[Dict[str, object]] = []
    year_display_map: Dict[str, str] = {}
    year_template_columns: List[Tuple[str, str]] = []
    prepared_tables: List[Tuple[int, pd.DataFrame, Dict[str, object], str]] = []

    for table_index, df in enumerate(df_list):
        if df is None or df.empty:
            continue

        source_table_type = result_map.get(table_index, {}).get("table_type", "其他")
        prepared_df, header_meta = _prepare_df_for_financial_standardization(df)
        if prepared_df is None or prepared_df.empty:
            continue
        prepared_tables.append((table_index, prepared_df, header_meta, source_table_type))

        year_columns = _extract_year_columns(prepared_df)
        if len(year_columns) > len(year_template_columns):
            year_template_columns = list(year_columns)

    for table_index, prepared_df, header_meta, source_table_type in prepared_tables:
        year_columns = _extract_year_columns(prepared_df)
        fallback_use_template = False
        if not year_columns and year_template_columns:
            # Fallback only when this table has no year columns but the document already
            # has a valid year template from other financial tables.
            year_columns = list(year_template_columns)
            fallback_use_template = True
        if not year_columns:
            continue

        for raw_col, normalized_col in year_columns:
            year_display_map.setdefault(normalized_col, raw_col)
        for row_index, row in prepared_df.iterrows():
            values = {}
            if fallback_use_template:
                row_tokens: List[str] = []
                for cell in row.tolist():
                    row_tokens.extend(_extract_numeric_tokens(cell))
                for i, (raw_col, _) in enumerate(year_columns):
                    values[raw_col] = row_tokens[i] if i < len(row_tokens) else ""
            else:
                values = {raw_col: _normalize_text(row[raw_col]) for raw_col, _ in year_columns}
            if not any(values.values()):
                continue
            metric_candidates = _find_metric_label_candidates(
                row,
                max_scan_cols=int(config.get("max_scan_label_cols", 8)),
            )
            selected_hits: List[Tuple[str, str, Dict[str, object], str]] = []
            if metric_candidates:
                for source_row_label, source_label_column, metric_match in metric_candidates:
                    selected_hits.append(
                        (source_row_label, source_label_column, metric_match, "metric_candidate_scan")
                    )
            else:
                source_row_label, source_label_column = _find_row_label(row)
                metric_match = _match_standard_metric(source_row_label)
                if metric_match:
                    selected_hits.append(
                        (source_row_label, source_label_column, metric_match, "fallback_first_columns")
                    )

            for source_row_label, source_label_column, metric_match, label_detect_method in selected_hits:
                if (
                    fallback_use_template
                    and metric_match.get("standard_metric") != "EV/EBITDA"
                ):
                    continue
                detail_row = _build_detail_row(
                    metric_match=metric_match,
                    values=values,
                    year_columns=year_columns,
                    source_table_index=table_index,
                    source_table_type=source_table_type,
                    source_row_index=int(row_index),
                    source_row_label=source_row_label,
                    source_label_column=source_label_column,
                    label_detect_method=label_detect_method,
                    header_repaired=bool(header_meta.get("header_repaired", False)),
                    header_source_row=header_meta.get("header_source_row", ""),
                )
                raw_year_values = {raw_col: detail_row.get(raw_col, "") for raw_col, _ in year_columns}
                detail_row["raw_year_values"] = "|".join(
                    f"{raw_col}:{_normalize_text(raw_year_values.get(raw_col, ''))}" for raw_col, _ in year_columns
                )
                repair_result = _repair_metric_candidate_values(
                    metric_match["standard_metric"],
                    raw_year_values,
                    source_row_label=source_row_label,
                    matched_alias=metric_match.get("matched_alias"),
                )
                candidate_year_values = repair_result.get("repaired_year_values", raw_year_values) or raw_year_values
                if bool(repair_result.get("repair_applied", False)):
                    for raw_col, _ in year_columns:
                        detail_row[raw_col] = _normalize_text(candidate_year_values.get(raw_col, ""))
                value_validation = _validate_metric_candidate_values(
                    metric_match["standard_metric"],
                    candidate_year_values,
                    source_row_label=source_row_label,
                )
                detail_row["_selected_year_values"] = candidate_year_values
                detail_row["value_repair_applied"] = bool(repair_result.get("repair_applied", False))
                detail_row["value_repair_strategy"] = repair_result.get("repair_strategy", "")
                detail_row["value_repair_issue_flags"] = repair_result.get("repair_issue_flags", "")
                detail_row["repaired_year_count"] = int(repair_result.get("repaired_year_count", 0))
                detail_row["value_validation_status"] = value_validation["value_validation_status"]
                detail_row["value_issue_flags"] = value_validation["value_issue_flags"]
                detail_row["valid_year_count"] = value_validation["valid_year_count"]
                detail_row["invalid_year_count"] = value_validation["invalid_year_count"]
                detail_row["_selected_year_values"] = (
                    value_validation.get("selected_year_values", candidate_year_values) or candidate_year_values
                )
                detail_rows.append(detail_row)
                if logger and config.get("log_detail", True):
                    logger.info(
                        "FinancialStandardizer hit: metric=%s table_index=%s table_type=%s row_index=%s label=%s label_detect_method=%s match_method=%s confidence=%.2f non_empty_year_count=%s value_repair_applied=%s value_repair_strategy=%s repaired_year_count=%s value_validation_status=%s value_issue_flags=%s header_repaired=%s header_source_row=%s",
                        detail_row["标准指标"],
                        table_index,
                        source_table_type,
                        row_index,
                        source_row_label,
                        detail_row["label_detect_method"],
                        detail_row["match_method"],
                        detail_row["confidence"],
                        detail_row["non_empty_year_count"],
                        detail_row["value_repair_applied"],
                        detail_row["value_repair_strategy"],
                        detail_row["repaired_year_count"],
                        detail_row["value_validation_status"],
                        detail_row["value_issue_flags"],
                        detail_row["header_repaired"],
                        detail_row["header_source_row"],
                    )

    ordered_year_columns = [
        year_display_map[key]
        for key in sorted(year_display_map.keys(), key=_year_sort_key)
    ]

    best_rows: Dict[str, Dict[str, object]] = {}
    for detail_row in detail_rows:
        metric = detail_row["标准指标"]
        current_best = best_rows.get(metric)
        if current_best is None:
            best_rows[metric] = detail_row
            continue
        current_key = (
            _value_status_rank(detail_row.get("value_validation_status", "")),
            -int(detail_row.get("valid_year_count", 0)),
            _count_issue_flags(detail_row.get("value_issue_flags", "")),
            -float(detail_row.get("confidence", 0) or 0),
            _source_type_rank(detail_row["source_table_type"]),
            -int(detail_row["non_empty_year_count"]),
            _table_row_sort_key(detail_row["source_table_index"]),
            _table_row_sort_key(detail_row["source_row_index"]),
        )
        best_key = (
            _value_status_rank(current_best.get("value_validation_status", "")),
            -int(current_best.get("valid_year_count", 0)),
            _count_issue_flags(current_best.get("value_issue_flags", "")),
            -float(current_best.get("confidence", 0) or 0),
            _source_type_rank(current_best["source_table_type"]),
            -int(current_best["non_empty_year_count"]),
            _table_row_sort_key(current_best["source_table_index"]),
            _table_row_sort_key(current_best["source_row_index"]),
        )
        if current_key < best_key:
            best_rows[metric] = detail_row

    wide_rows: List[Dict[str, object]] = []
    for metric in STANDARD_METRIC_ALIASES.keys():
        selected = best_rows.get(metric)
        row = {
            "指标": metric,
            "来源表": "",
            "来源类型": "",
            "来源行号": "",
            "来源指标名": "",
            "来源列": "",
            "置信度": "",
            "value_repair_applied": "",
            "value_repair_strategy": "",
            "value_validation_status": "",
            "value_issue_flags": "",
        }
        for year_col in ordered_year_columns:
            row[year_col] = ""
        if selected:
            selected_status = _normalize_text(selected.get("value_validation_status", ""))
            if selected_status != "invalid":
                selected_year_values = selected.get("_selected_year_values", {}) or {}
                for year_col in ordered_year_columns:
                    row[year_col] = selected_year_values.get(year_col, selected.get(year_col, ""))
            row["来源表"] = selected["source_table_index"]
            row["来源类型"] = selected["source_table_type"]
            row["来源行号"] = selected["source_row_index"]
            row["来源指标名"] = selected["source_row_label"]
            row["来源列"] = selected["source_column"]
            row["置信度"] = selected["confidence"]
            row["value_repair_applied"] = selected.get("value_repair_applied", False)
            row["value_repair_strategy"] = selected.get("value_repair_strategy", "")
            row["value_validation_status"] = selected_status
            row["value_issue_flags"] = selected.get("value_issue_flags", "")
        wide_rows.append(row)

    wide_columns = ["指标"] + ordered_year_columns + ["来源表", "来源类型", "来源行号", "来源指标名", "来源列", "置信度", "value_repair_applied", "value_repair_strategy", "value_validation_status", "value_issue_flags"]
    detail_columns = [
        "标准指标",
        "source_row_label",
        "source_table_index",
        "source_table_type",
        "source_row_index",
        "source_label_column",
        "label_detect_method",
        "source_column",
        "matched_alias",
        "match_method",
        "confidence",
        "non_empty_year_count",
        "raw_year_values",
        "value_repair_applied",
        "value_repair_strategy",
        "value_repair_issue_flags",
        "repaired_year_count",
        "value_validation_status",
        "value_issue_flags",
        "valid_year_count",
        "invalid_year_count",
        "header_repaired",
        "header_source_row",
    ] + ordered_year_columns

    wide_df = pd.DataFrame(wide_rows, columns=wide_columns)
    detail_df = pd.DataFrame(detail_rows)
    if detail_df.empty:
        detail_df = pd.DataFrame(columns=detail_columns)
    else:
        detail_df = detail_df.reindex(columns=detail_columns)

    if logger:
        logger.info(
            "FinancialStandardizer summary: extracted_candidates=%s selected_metrics=%s year_columns=%s",
            len(detail_rows),
            sum(1 for row in wide_rows if row["来源表"] != ""),
            ordered_year_columns,
        )
    return {
        "wide_df": wide_df,
        "detail_df": detail_df,
    }


def export_standardized_financials(result, pkg_path, save_excel_func=None, logger=None):
    wide_df = result.get("wide_df", pd.DataFrame())
    detail_df = result.get("detail_df", pd.DataFrame())
    target_path = os.path.join(pkg_path, "05_核心财务指标标准化.xlsx")
    final_path = target_path

    if os.path.exists(target_path):
        try:
            with open(target_path, "a"):
                pass
        except PermissionError:
            timestamp = datetime.now().strftime("%H%M%S")
            final_path = target_path.replace(".xlsx", f"_副本_{timestamp}.xlsx")

    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        wide_df.to_excel(writer, sheet_name="核心指标宽表", index=False)
        detail_df.to_excel(writer, sheet_name="抽取明细", index=False)

    if logger:
        logger.info("核心财务指标标准化输出: %s", final_path)
    return final_path
