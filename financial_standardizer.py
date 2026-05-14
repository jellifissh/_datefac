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
                detail_rows.append(detail_row)
                if logger and config.get("log_detail", True):
                    logger.info(
                        "FinancialStandardizer hit: metric=%s table_index=%s table_type=%s row_index=%s label=%s label_detect_method=%s match_method=%s confidence=%.2f non_empty_year_count=%s header_repaired=%s header_source_row=%s",
                        detail_row["标准指标"],
                        table_index,
                        source_table_type,
                        row_index,
                        source_row_label,
                        detail_row["label_detect_method"],
                        detail_row["match_method"],
                        detail_row["confidence"],
                        detail_row["non_empty_year_count"],
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
            _source_type_rank(detail_row["source_table_type"]),
            -int(detail_row["non_empty_year_count"]),
            int(detail_row["source_table_index"]),
            int(detail_row["source_row_index"]),
        )
        best_key = (
            _source_type_rank(current_best["source_table_type"]),
            -int(current_best["non_empty_year_count"]),
            int(current_best["source_table_index"]),
            int(current_best["source_row_index"]),
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
        }
        for year_col in ordered_year_columns:
            row[year_col] = ""
        if selected:
            for year_col in ordered_year_columns:
                row[year_col] = selected.get(year_col, "")
            row["来源表"] = selected["source_table_index"]
            row["来源类型"] = selected["source_table_type"]
            row["来源行号"] = selected["source_row_index"]
            row["来源指标名"] = selected["source_row_label"]
            row["来源列"] = selected["source_column"]
            row["置信度"] = selected["confidence"]
        wide_rows.append(row)

    wide_columns = ["指标"] + ordered_year_columns + ["来源表", "来源类型", "来源行号", "来源指标名", "来源列", "置信度"]
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
