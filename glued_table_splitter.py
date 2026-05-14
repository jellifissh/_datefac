from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd

from financial_standardizer import standardize_core_financials


DEFAULT_SPLITTER_CONFIG: Dict[str, object] = {
    "enabled": True,
    "append_split_tables": True,
    "min_col_count": 10,
    "min_row_count": 10,
    "trigger_flags": ["possible_glued_table"],
    "output_diagnostics": True,
    "max_split_tables_per_source": 5,
}

STATEMENT_KEYWORDS = ["利润表", "资产负债表", "现金流量表", "财务比率"]
CORE_METRICS = [
    "营业收入",
    "归属母公司净利润",
    "毛利率",
    "ROE",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
]
YEAR_PATTERN = re.compile(r"(20\d{2}\s*[AE]?|20\d{2}\s*年)", flags=re.IGNORECASE)


def _normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    if df.empty:
        return df.copy()
    normalized = df.fillna("").astype(str)
    normalized = normalized.apply(lambda col: col.map(lambda v: re.sub(r"\s+", " ", v).strip()))
    normalized = normalized.loc[(normalized != "").any(axis=1), (normalized != "").any(axis=0)]
    if normalized.empty:
        return pd.DataFrame()
    return normalized.reset_index(drop=True)


def _to_int(value, default=0) -> int:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return default
        return int(float(value))
    except Exception:
        return default


def _build_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 6, max_len: int = 320) -> str:
    if df is None or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        lines.append(" | ".join([_normalize_text(v) for v in row.tolist()]))
    text = " || ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _count_statement_keywords(text: str) -> int:
    compact = _normalize_text(text)
    return sum(1 for kw in STATEMENT_KEYWORDS if kw in compact)


def _table_text(df: pd.DataFrame, max_cells: int = 2500) -> str:
    if df is None or df.empty:
        return ""
    cells = df.fillna("").astype(str).values.flatten().tolist()
    cells = [c.strip() for c in cells if str(c).strip()]
    if len(cells) > max_cells:
        cells = cells[:max_cells]
    return " ".join(cells)


def _should_split(
    df: pd.DataFrame,
    meta: Optional[Dict[str, object]],
    cfg: Dict[str, object],
) -> Tuple[bool, str, int]:
    row_count, col_count = df.shape if df is not None else (0, 0)
    min_col = _to_int(cfg.get("min_col_count", 10), 10)
    min_row = _to_int(cfg.get("min_row_count", 10), 10)
    trigger_flags = [str(x).strip() for x in (cfg.get("trigger_flags", []) or [])]

    flags_text = _normalize_text((meta or {}).get("quality_flags", ""))
    flag_hit = any(flag and flag in flags_text for flag in trigger_flags)
    text = _table_text(df)
    statement_keyword_count = _count_statement_keywords(text)
    size_gate = col_count >= min_col and row_count >= min_row

    should = size_gate or flag_hit or statement_keyword_count >= 2
    reason_parts: List[str] = []
    if size_gate:
        reason_parts.append("size_gate")
    if flag_hit:
        reason_parts.append("flag_trigger")
    if statement_keyword_count >= 2:
        reason_parts.append("statement_keyword_multi")
    reason = "|".join(reason_parts) if reason_parts else "not_triggered"
    return should, reason, statement_keyword_count


def _column_gap_split(df: pd.DataFrame, min_rows: int = 5, min_cols: int = 3) -> List[Dict[str, object]]:
    if df is None or df.empty:
        return []
    n_rows, n_cols = df.shape
    if n_cols < min_cols:
        return []

    non_empty_ratio = []
    for col_idx in range(n_cols):
        col = df.iloc[:, col_idx].fillna("").astype(str).str.strip()
        ratio = float((col != "").sum()) / float(max(1, n_rows))
        non_empty_ratio.append(ratio)

    separator_cols = [i for i, ratio in enumerate(non_empty_ratio) if ratio <= 0.10]
    if not separator_cols:
        return []

    bounds: List[Tuple[int, int]] = []
    left = 0
    for sep in separator_cols:
        if sep - left >= min_cols:
            bounds.append((left, sep - 1))
        left = sep + 1
    if n_cols - left >= min_cols:
        bounds.append((left, n_cols - 1))

    candidates = []
    split_index = 1
    for c0, c1 in bounds:
        sub = _normalize_df(df.iloc[:, c0 : c1 + 1])
        if sub.empty:
            continue
        r, c = sub.shape
        if r < min_rows or c < min_cols:
            continue
        candidates.append(
            {
                "split_index": split_index,
                "split_method": "column_gap_split",
                "row_start": 1,
                "row_end": int(n_rows),
                "col_start": int(c0 + 1),
                "col_end": int(c1 + 1),
                "df": sub,
            }
        )
        split_index += 1
    return candidates


def _probe_financial_metrics(candidate_df: pd.DataFrame) -> Dict[str, object]:
    try:
        result = standardize_core_financials([candidate_df], classification_results=None, logger=None, config=None)
        detail_df = result.get("detail_df", pd.DataFrame())
        if detail_df is None:
            detail_df = pd.DataFrame()
        hit_metrics: List[str] = []
        if not detail_df.empty and "标准指标" in detail_df.columns:
            hit_metrics = [
                str(v).strip()
                for v in detail_df["标准指标"].dropna().astype(str).tolist()
                if str(v).strip()
            ]
            hit_metrics = list(dict.fromkeys(hit_metrics))
        missing = [m for m in CORE_METRICS if m not in hit_metrics]
        return {
            "financial_detail_count": int(len(detail_df)),
            "financial_metric_hit_count": int(len(hit_metrics)),
            "financial_hit_metrics": "|".join(hit_metrics),
            "financial_missing_metrics": "|".join(missing),
            "probe_error": "",
        }
    except Exception as exc:
        return {
            "financial_detail_count": 0,
            "financial_metric_hit_count": 0,
            "financial_hit_metrics": "",
            "financial_missing_metrics": "|".join(CORE_METRICS),
            "probe_error": str(exc),
        }


def split_glued_tables(
    df_list,
    table_meta_list=None,
    config=None,
    logger=None,
):
    cfg = dict(DEFAULT_SPLITTER_CONFIG)
    cfg.update(config or {})

    base_tables = list(df_list or [])
    if not bool(cfg.get("enabled", True)) or not bool(cfg.get("append_split_tables", True)):
        return base_tables, pd.DataFrame()

    max_split_per_source = _to_int(cfg.get("max_split_tables_per_source", 5), 5)
    enhanced_df_list: List[pd.DataFrame] = list(base_tables)
    diagnostics_rows: List[Dict[str, object]] = []

    for source_idx, raw_df in enumerate(base_tables):
        if not isinstance(raw_df, pd.DataFrame) or raw_df.empty:
            diagnostics_rows.append(
                {
                    "source_table_index": source_idx,
                    "split_index": 0,
                    "split_method": "column_gap_split",
                    "row_start": 0,
                    "row_end": 0,
                    "col_start": 0,
                    "col_end": 0,
                    "row_count": 0,
                    "col_count": 0,
                    "financial_metric_hit_count": 0,
                    "financial_hit_metrics": "",
                    "appended": False,
                    "reason": "source_empty_or_invalid",
                    "preview": "",
                }
            )
            continue

        df = _normalize_df(raw_df)
        if df.empty:
            diagnostics_rows.append(
                {
                    "source_table_index": source_idx,
                    "split_index": 0,
                    "split_method": "column_gap_split",
                    "row_start": 0,
                    "row_end": 0,
                    "col_start": 0,
                    "col_end": 0,
                    "row_count": 0,
                    "col_count": 0,
                    "financial_metric_hit_count": 0,
                    "financial_hit_metrics": "",
                    "appended": False,
                    "reason": "source_normalized_empty",
                    "preview": "",
                }
            )
            continue

        meta = {}
        if isinstance(table_meta_list, list) and source_idx < len(table_meta_list):
            meta = table_meta_list[source_idx] or {}

        should_split, trigger_reason, statement_kw_count = _should_split(df, meta, cfg)
        if not should_split:
            diagnostics_rows.append(
                {
                    "source_table_index": source_idx,
                    "split_index": 0,
                    "split_method": "column_gap_split",
                    "row_start": 1,
                    "row_end": int(df.shape[0]),
                    "col_start": 1,
                    "col_end": int(df.shape[1]),
                    "row_count": int(df.shape[0]),
                    "col_count": int(df.shape[1]),
                    "financial_metric_hit_count": 0,
                    "financial_hit_metrics": "",
                    "appended": False,
                    "reason": f"not_triggered(statement_keywords={statement_kw_count})",
                    "preview": _build_preview(df),
                }
            )
            continue

        candidates = _column_gap_split(df, min_rows=5, min_cols=3)
        if not candidates:
            diagnostics_rows.append(
                {
                    "source_table_index": source_idx,
                    "split_index": 0,
                    "split_method": "column_gap_split",
                    "row_start": 1,
                    "row_end": int(df.shape[0]),
                    "col_start": 1,
                    "col_end": int(df.shape[1]),
                    "row_count": int(df.shape[0]),
                    "col_count": int(df.shape[1]),
                    "financial_metric_hit_count": 0,
                    "financial_hit_metrics": "",
                    "appended": False,
                    "reason": f"{trigger_reason}|no_valid_column_gap_candidates",
                    "preview": _build_preview(df),
                }
            )
            continue

        appended_count = 0
        for candidate in candidates:
            sub_df = candidate["df"]
            probe = _probe_financial_metrics(sub_df)
            hit_count = _to_int(probe.get("financial_metric_hit_count", 0), 0)
            appended = False
            reason = trigger_reason
            if hit_count < 2:
                reason = f"{trigger_reason}|hit_count_lt_2"
            elif appended_count >= max_split_per_source:
                reason = f"{trigger_reason}|max_split_limit_reached"
            else:
                enhanced_df_list.append(sub_df)
                appended_count += 1
                appended = True
                reason = f"{trigger_reason}|appended"

            diagnostics_rows.append(
                {
                    "source_table_index": source_idx,
                    "split_index": _to_int(candidate.get("split_index", 0), 0),
                    "split_method": _normalize_text(candidate.get("split_method", "column_gap_split")),
                    "row_start": _to_int(candidate.get("row_start", 1), 1),
                    "row_end": _to_int(candidate.get("row_end", df.shape[0]), int(df.shape[0])),
                    "col_start": _to_int(candidate.get("col_start", 1), 1),
                    "col_end": _to_int(candidate.get("col_end", df.shape[1]), int(df.shape[1])),
                    "row_count": int(sub_df.shape[0]),
                    "col_count": int(sub_df.shape[1]),
                    "financial_metric_hit_count": hit_count,
                    "financial_hit_metrics": _normalize_text(probe.get("financial_hit_metrics", "")),
                    "appended": bool(appended),
                    "reason": reason,
                    "preview": _build_preview(sub_df),
                }
            )

    diagnostics_df = pd.DataFrame(
        diagnostics_rows,
        columns=[
            "source_table_index",
            "split_index",
            "split_method",
            "row_start",
            "row_end",
            "col_start",
            "col_end",
            "row_count",
            "col_count",
            "financial_metric_hit_count",
            "financial_hit_metrics",
            "appended",
            "reason",
            "preview",
        ],
    )

    if logger:
        appended_count = int(diagnostics_df[diagnostics_df["appended"] == True].shape[0]) if not diagnostics_df.empty else 0
        logger.info(
            "GluedTableSplitter summary: source_tables=%s appended_splits=%s enhanced_tables=%s",
            len(base_tables),
            appended_count,
            len(enhanced_df_list),
        )
    return enhanced_df_list, diagnostics_df

