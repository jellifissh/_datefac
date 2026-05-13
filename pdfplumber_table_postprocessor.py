import re
from typing import Dict, List, Tuple

import pandas as pd


# Keep merge behavior unchanged.
CORE_HEAD_KEYWORDS = ("营业收入", "归属母公司净利润", "毛利率", "roe")
CORE_TAIL_KEYWORDS = ("每股收益", "p/e", "p/b", "ev/ebitda")

DIAG_LEFT_KEYWORDS = (
    "营业收入",
    "收入同比",
    "归属母公司净利润",
    "归母净利润",
    "净利润同比",
    "毛利率",
    "roe",
)
DIAG_RIGHT_CONT_KEYWORDS = (
    "每股收益",
    "eps",
    "p/e",
    "pe",
    "p/b",
    "pb",
    "ev/ebitda",
    "evebitda",
)
DIAG_RIGHT_NEW_TABLE_KEYWORDS = (
    "资产负债表",
    "利润表",
    "现金流量表",
    "主要财务比率",
    "财务比率",
    "成长能力",
    "获利能力",
    "偿债能力",
    "营运能力",
    "估值比率",
)

QUALITY_FINANCE_KEYWORDS = (
    "营业收入",
    "净利润",
    "资产",
    "负债",
    "现金流",
    "毛利率",
    "roe",
    "p/e",
    "eps",
    "会计年度",
)
QUALITY_HEADER_HINTS = ("会计年度", "主要财务指标", "报告日期")


def _normalize_text(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return text


def _match_keywords(values: List[str], keywords: Tuple[str, ...]) -> List[str]:
    matched: List[str] = []
    if not values:
        return matched
    for keyword in keywords:
        norm_kw = _normalize_text(keyword)
        if any(norm_kw in v for v in values):
            matched.append(keyword)
    return matched


def _extract_year_tokens(df: pd.DataFrame) -> List[str]:
    tokens: List[str] = []
    for col in df.columns.tolist():
        token = _normalize_text(col)
        if re.match(r"20\d{2}[a-z]?$", token):
            tokens.append(token)
    if not tokens and not df.empty:
        row0 = df.iloc[0].fillna("").astype(str).tolist()
        for cell in row0:
            token = _normalize_text(cell)
            if re.match(r"20\d{2}[a-z]?$", token):
                tokens.append(token)
    return sorted(set(tokens))


def _flatten_cells(df: pd.DataFrame) -> List[str]:
    if df is None or df.empty:
        return []
    values = df.fillna("").astype(str).values.tolist()
    flat: List[str] = []
    for row in values:
        for cell in row:
            flat.append(_normalize_text(cell))
    return flat


def _contains_any(values: List[str], keywords: Tuple[str, ...]) -> bool:
    return len(_match_keywords(values, keywords)) > 0


def _first_col_preview(df: pd.DataFrame, max_rows: int = 6, max_len: int = 180) -> str:
    if df is None or df.empty or df.shape[1] == 0:
        return ""
    col = df.iloc[:max_rows, 0].fillna("").astype(str).tolist()
    text = " | ".join([re.sub(r"\s+", " ", x).strip() for x in col if str(x).strip()])
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _block_id(block: Dict) -> str:
    return f"p{block.get('page')}_t{block.get('table_index')}"


def _count_non_empty_cells(df: pd.DataFrame) -> int:
    if df is None or df.empty:
        return 0
    normalized = df.fillna("").astype(str).apply(lambda col: col.map(lambda x: x.strip()))
    return int((normalized != "").sum().sum())


def _looks_header_only(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return True
    rows = int(df.shape[0])
    cells = _flatten_cells(df)
    year_hits = sum(1 for token in cells if re.match(r"20\d{2}[a-z]?$", token))
    finance_hits = len(_match_keywords(cells, QUALITY_FINANCE_KEYWORDS))
    header_hint_hits = len(_match_keywords(cells, QUALITY_HEADER_HINTS))
    # Conservative header-only heuristic.
    if rows <= 2 and (finance_hits <= 1 or header_hint_hits >= 1):
        return True
    if finance_hits == 0 and year_hits > 0:
        return True
    return False


def evaluate_pdfplumber_table_quality(table_blocks, logger=None, config=None) -> Dict:
    cfg = config or {}
    min_valid_tables = int(cfg.get("pdfplumber_min_valid_tables", 1) or 1)
    min_quality_score = float(cfg.get("pdfplumber_min_quality_score", 0.5))

    blocks = table_blocks or []
    raw_count = len(blocks)
    valid_count = 0
    header_only_count = 0
    total_non_empty_cells = 0
    total_rows = 0
    total_cols = 0
    finance_keyword_hits = 0

    for block in blocks:
        df = block.get("df")
        if not isinstance(df, pd.DataFrame):
            continue
        rows = int(df.shape[0])
        cols = int(df.shape[1])
        total_rows += rows
        total_cols += cols
        non_empty_cells = _count_non_empty_cells(df)
        total_non_empty_cells += non_empty_cells
        cells = _flatten_cells(df)
        finance_hits_this = len(_match_keywords(cells, QUALITY_FINANCE_KEYWORDS))
        finance_keyword_hits += finance_hits_this

        header_only = _looks_header_only(df)
        if header_only:
            header_only_count += 1

        # Majority-like valid signal.
        signals = 0
        if rows >= 3:
            signals += 1
        if cols >= 3:
            signals += 1
        if non_empty_cells >= 8:
            signals += 1
        if rows - 1 >= 2:
            signals += 1
        if finance_hits_this > 0:
            signals += 1
        if signals >= 3 and not header_only:
            valid_count += 1

    avg_rows = (total_rows / raw_count) if raw_count else 0.0
    avg_cols = (total_cols / raw_count) if raw_count else 0.0
    header_ratio = (header_only_count / raw_count) if raw_count else 1.0
    valid_ratio = (valid_count / raw_count) if raw_count else 0.0
    keyword_factor = min(finance_keyword_hits / max(raw_count * 2, 1), 1.0)

    # Weighted quality score in [0,1].
    quality_score = 0.5 * valid_ratio + 0.3 * keyword_factor + 0.2 * (1 - header_ratio)
    quality_score = max(0.0, min(1.0, quality_score))

    should_use = (
        raw_count > 0
        and valid_count >= min_valid_tables
        and quality_score >= min_quality_score
        and header_ratio <= 0.8
    )

    blocked: List[str] = []
    if raw_count == 0:
        blocked.append("raw_table_count_zero")
    if valid_count < min_valid_tables:
        blocked.append("valid_table_count_too_low")
    if quality_score < min_quality_score:
        blocked.append("quality_score_too_low")
    if header_ratio > 0.8:
        blocked.append("header_only_ratio_too_high")
    fallback_reason = ",".join(blocked)

    summary = {
        "raw_table_count": raw_count,
        "valid_table_count": valid_count,
        "header_only_table_count": header_only_count,
        "total_non_empty_cells": total_non_empty_cells,
        "avg_rows": round(avg_rows, 4),
        "avg_cols": round(avg_cols, 4),
        "finance_keyword_hits": finance_keyword_hits,
        "quality_score": round(quality_score, 4),
        "should_use_pdfplumber": bool(should_use),
        "fallback_reason": fallback_reason,
    }
    if logger:
        logger.info(
            "pdfplumber quality summary: raw_table_count=%s valid_table_count=%s header_only_table_count=%s total_non_empty_cells=%s avg_rows=%.2f avg_cols=%.2f finance_keyword_hits=%s quality_score=%.4f should_use_pdfplumber=%s",
            summary["raw_table_count"],
            summary["valid_table_count"],
            summary["header_only_table_count"],
            summary["total_non_empty_cells"],
            summary["avg_rows"],
            summary["avg_cols"],
            summary["finance_keyword_hits"],
            summary["quality_score"],
            summary["should_use_pdfplumber"],
        )
        logger.info("fallback_reason=%s", summary["fallback_reason"] or "")
    return summary


def _is_strong_cross_page_continuation(prev_block: Dict, next_block: Dict) -> bool:
    prev_page = prev_block.get("page")
    next_page = next_block.get("page")
    if not isinstance(prev_page, int) or not isinstance(next_page, int) or next_page != prev_page + 1:
        return False

    prev_df = prev_block.get("df")
    next_df = next_block.get("df")
    if not isinstance(prev_df, pd.DataFrame) or not isinstance(next_df, pd.DataFrame):
        return False
    if prev_df.empty or next_df.empty:
        return False

    prev_cols = prev_df.shape[1]
    next_cols = next_df.shape[1]
    if abs(prev_cols - next_cols) > 1:
        return False

    prev_years = set(_extract_year_tokens(prev_df))
    next_years = set(_extract_year_tokens(next_df))
    if len(prev_years & next_years) < 2:
        return False

    prev_cells = _flatten_cells(prev_df)
    next_cells = _flatten_cells(next_df)
    has_head = _contains_any(prev_cells, CORE_HEAD_KEYWORDS)
    has_tail = _contains_any(next_cells, CORE_TAIL_KEYWORDS)
    return has_head and has_tail


def diagnose_cross_page_merge_candidates(table_blocks, logger=None, config=None) -> List[Dict]:
    blocks = sorted(table_blocks or [], key=lambda x: (int(x.get("page") or 0), int(x.get("table_index") or 0)))
    diagnostics: List[Dict] = []
    if not blocks:
        return diagnostics

    by_page: Dict[int, List[Dict]] = {}
    for block in blocks:
        page = block.get("page")
        if isinstance(page, int):
            by_page.setdefault(page, []).append(block)

    pages = sorted(by_page.keys())
    for left_page in pages:
        right_page = left_page + 1
        if right_page not in by_page:
            continue
        for left in by_page[left_page]:
            for right in by_page[right_page]:
                left_df = left.get("df")
                right_df = right.get("df")
                if not isinstance(left_df, pd.DataFrame) or not isinstance(right_df, pd.DataFrame):
                    continue
                left_id = _block_id(left)
                right_id = _block_id(right)
                left_years = _extract_year_tokens(left_df)
                right_years = _extract_year_tokens(right_df)
                year_overlap = len(set(left_years) & set(right_years))
                left_cells = _flatten_cells(left_df)
                right_cells = _flatten_cells(right_df)
                left_kw = _match_keywords(left_cells, DIAG_LEFT_KEYWORDS)
                right_cont_kw = _match_keywords(right_cells, DIAG_RIGHT_CONT_KEYWORDS)
                right_new_kw = _match_keywords(right_cells, DIAG_RIGHT_NEW_TABLE_KEYWORDS)
                left_cols = int(left_df.shape[1])
                right_cols = int(right_df.shape[1])
                col_diff = abs(left_cols - right_cols)
                should_merge = _is_strong_cross_page_continuation(left, right)

                blocked_reasons: List[str] = []
                if col_diff > 1:
                    blocked_reasons.append("col_diff_too_large")
                if year_overlap < 2:
                    blocked_reasons.append("year_overlap_too_low")
                if not left_kw:
                    blocked_reasons.append("left_key_metric_keywords_missing")
                if not right_cont_kw:
                    blocked_reasons.append("right_continuation_keywords_missing")
                if right_new_kw:
                    blocked_reasons.append("right_looks_like_new_table")
                if not should_merge:
                    blocked_reasons.append("current_rule_false")

                diagnostics.append(
                    {
                        "left_block_id": left_id,
                        "right_block_id": right_id,
                        "left_page": left.get("page", ""),
                        "right_page": right.get("page", ""),
                        "left_table_index": left.get("table_index", ""),
                        "right_table_index": right.get("table_index", ""),
                        "is_adjacent_page": True,
                        "left_rows": int(left_df.shape[0]),
                        "right_rows": int(right_df.shape[0]),
                        "left_cols": left_cols,
                        "right_cols": right_cols,
                        "col_diff": col_diff,
                        "left_year_tokens": ",".join(left_years),
                        "right_year_tokens": ",".join(right_years),
                        "year_overlap_count": year_overlap,
                        "left_key_metric_keywords": ",".join(left_kw),
                        "right_continuation_keywords": ",".join(right_cont_kw),
                        "right_new_table_keywords": ",".join(right_new_kw),
                        "should_merge_by_current_rule": should_merge,
                        "blocked_reasons": ",".join(blocked_reasons),
                        "left_first_col_preview": _first_col_preview(left_df),
                        "right_first_col_preview": _first_col_preview(right_df),
                    }
                )

    if logger:
        logger.info("pdfplumber merge candidate count=%s", len(diagnostics))
        for row in diagnostics[:30]:
            logger.info(
                "merge candidate %s -> %s overlap=%s left_kw=%s right_kw=%s right_new=%s blocked=%s should_merge=%s",
                row["left_block_id"],
                row["right_block_id"],
                row["year_overlap_count"],
                row["left_key_metric_keywords"],
                row["right_continuation_keywords"],
                row["right_new_table_keywords"],
                row["blocked_reasons"],
                row["should_merge_by_current_rule"],
            )
    return diagnostics


def _merge_two_blocks(prev_block: Dict, next_block: Dict) -> Dict:
    prev_df = prev_block["df"].copy()
    next_df = next_block["df"].copy()
    if next_df.shape[1] != prev_df.shape[1]:
        max_cols = max(prev_df.shape[1], next_df.shape[1])
        prev_df = prev_df.reindex(columns=list(range(max_cols)), fill_value="")
        next_df = next_df.reindex(columns=list(range(max_cols)), fill_value="")
    else:
        next_df.columns = prev_df.columns

    merged_df = pd.concat([prev_df, next_df], ignore_index=True)
    source_blocks: List[str] = []
    source_blocks.extend(prev_block.get("source_blocks") or [_block_id(prev_block)])
    source_blocks.extend(next_block.get("source_blocks") or [_block_id(next_block)])
    merged_page = f"{prev_block.get('page')}-{next_block.get('page')}"
    preview = ""
    if not merged_df.empty:
        sample = merged_df.iloc[:3, :5].fillna("").astype(str)
        lines = []
        for _, row in sample.iterrows():
            lines.append(" | ".join(cell.strip() for cell in row.tolist()))
        preview = " || ".join(lines)[:300]

    return {
        "backend": "pdfplumber",
        "page": merged_page,
        "table_index": f"{prev_block.get('table_index')}+{next_block.get('table_index')}",
        "df": merged_df,
        "rows": int(merged_df.shape[0]),
        "cols": int(merged_df.shape[1]),
        "preview": preview,
        "confidence": min(float(prev_block.get("confidence", 0.8)), float(next_block.get("confidence", 0.8))),
        "business_hint": "主要财务指标",
        "source_blocks": source_blocks,
        "sheet_name_hint": "主要财务指标",
    }


def postprocess_pdfplumber_blocks(table_blocks, logger=None, config=None) -> List[Dict]:
    blocks = sorted(table_blocks or [], key=lambda x: (int(x.get("page") or 0), int(x.get("table_index") or 0)))
    if not blocks:
        return []
    normalized_blocks: List[Dict] = []
    for block in blocks:
        b = dict(block)
        if "source_blocks" not in b or not b["source_blocks"]:
            b["source_blocks"] = [_block_id(b)]
        b.setdefault("business_hint", "")
        b.setdefault("sheet_name_hint", "")
        normalized_blocks.append(b)

    merged_flags = [False] * len(normalized_blocks)
    processed: List[Dict] = []
    merge_count = 0
    i = 0
    while i < len(normalized_blocks):
        if merged_flags[i]:
            i += 1
            continue
        current = normalized_blocks[i]
        if i + 1 < len(normalized_blocks) and not merged_flags[i + 1]:
            nxt = normalized_blocks[i + 1]
            if _is_strong_cross_page_continuation(current, nxt):
                merged = _merge_two_blocks(current, nxt)
                processed.append(merged)
                merged_flags[i] = True
                merged_flags[i + 1] = True
                merge_count += 1
                if logger:
                    logger.info(
                        "pdfplumber postprocess merged cross-page continuation: source_blocks=%s",
                        ",".join(merged.get("source_blocks", [])),
                    )
                i += 2
                continue
        processed.append(current)
        merged_flags[i] = True
        i += 1

    if logger:
        logger.info(
            "pdfplumber postprocess summary: input_blocks=%s processed_blocks=%s merges=%s",
            len(normalized_blocks),
            len(processed),
            merge_count,
        )
    return processed
