import re
from typing import Any, Dict, List, Tuple

from table_block import TableBlock


FINANCE_KEYWORDS = [
    "营业收入",
    "归属母公司净利润",
    "净利润",
    "资产总计",
    "负债合计",
    "所有者权益",
    "经营活动现金流",
    "投资活动现金流",
    "筹资活动现金流",
    "毛利率",
    "ROE",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "EPS",
    "会计年度",
]


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _extract_text_from_block(block: TableBlock, max_chars: int = 20000) -> str:
    if block.raw_markdown:
        return block.raw_markdown[:max_chars]
    df = block.raw_df
    if df is None:
        return ""
    try:
        parts = []
        parts.extend(_normalize_text(c) for c in getattr(df, "columns", []))
        for row in df.head(60).itertuples(index=False):
            parts.extend(_normalize_text(v) for v in row)
        text = "\n".join([p for p in parts if p])
        return text[:max_chars]
    except Exception:
        return ""


def _has_year_token(text: str) -> bool:
    if not text:
        return False
    compact = re.sub(r"\s+", "", text)
    return bool(re.search(r"20\d{2}[A-Z]?", compact))


def _keyword_hits(text: str, keywords: List[str]) -> List[str]:
    hits = []
    for kw in keywords:
        if kw in text:
            hits.append(kw)
    return hits


def score_table_block(block: TableBlock) -> Dict[str, Any]:
    flags: List[str] = []
    score = 0.0

    rows = int(block.row_count or 0)
    cols = int(block.col_count or 0)
    non_empty = int(block.non_empty_cell_count or 0)
    empty_ratio = float(block.empty_cell_ratio or 0.0)

    if rows <= 1:
        flags.append("too_few_rows")
    if cols <= 1:
        flags.append("single_column")
    if non_empty <= 6:
        flags.append("too_few_non_empty_cells")
    if empty_ratio >= 0.85:
        flags.append("mostly_empty")

    # Base score: shape and density
    if rows >= 3:
        score += 0.2
    if rows >= 8:
        score += 0.2
    if cols >= 3:
        score += 0.2
    if non_empty >= 20:
        score += 0.2
    if empty_ratio <= 0.5:
        score += 0.2

    text = _extract_text_from_block(block)
    year_hit = _has_year_token(text)
    finance_hits = _keyword_hits(text, FINANCE_KEYWORDS)
    if year_hit:
        score += 0.15
    if finance_hits:
        score += min(0.25, 0.05 * len(finance_hits))

    # Suspicious: glued tables / mixed content heuristic
    if rows >= 40 and cols >= 6 and year_hit and len(finance_hits) >= 6:
        flags.append("possible_glued_table")
        score -= 0.1

    if rows <= 2 and year_hit and len(finance_hits) <= 2:
        flags.append("header_only_like")
        score -= 0.2

    score = max(0.0, min(1.0, round(score, 4)))

    if score >= 0.75:
        level = "GOOD"
    elif score >= 0.45:
        level = "OK"
    else:
        level = "BAD"

    return {
        "quality_score": score,
        "quality_level": level,
        "quality_flags": ",".join(flags),
        "year_token_hit": year_hit,
        "finance_keyword_hits": ",".join(finance_hits[:20]),
    }

