from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple


YEAR_PATTERN = re.compile(r"^(20\d{2})(?:\s*年)?\s*([AE])?(?:_\d+)?$", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"^\(?-?\d[\d,\s]*\.?\d*\)?%?$")
MISSING_TOKEN_SET = {"", "-", "--", "—", "N/A", "n/a", "NA", "na"}
COMMA_SPACE_PATTERN = re.compile(r"\d,\s+\d")
SEPARATOR_PATTERN = re.compile(r"^:?-{3,}:?$")
FINANCIAL_COMMON_CHARS = set(
    "代码公司行业预测指标财务估值资产负债现金流利润收入成本毛利净利率增长股东每股"
    "营业合计其中货币资金应收账款存货固定资产负债所有者权益现金流量"
)
MOJIBAKE_MARKERS = (
    "锟",
    "锛",
    "鈥",
    "鍏",
    "鍒",
    "鍚",
    "褰",
    "姣",
    "鐜",
    "璐",
    "娑",
    "绌",
    "鎹",
    "鏈",
)
KNOWN_SHORT_LABELS = {"ROE", "ROA", "ROIC", "EPS", "PE", "PB", "PS", "EV", "CNY", "合计", "(+/-%)", "+/-%"}
UNIT_HINTS = ("百万元", "百亿", "亿元", "万元", "元/股", "元", "%", "X", "x")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in _norm(text))


def normalize_text(text: Any) -> str:
    normalized = _norm(text).replace("\u3000", " ").replace("\xa0", " ")
    normalized = normalized.replace("\r", " ").replace("\n", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def normalize_year_header(text: Any) -> str:
    normalized = normalize_text(text).replace(" ", "")
    match = YEAR_PATTERN.match(normalized)
    if not match:
        return normalized
    suffix = (match.group(2) or "").upper()
    return f"{match.group(1)}{suffix}" if suffix else match.group(1)


def is_valid_year_header(text: Any) -> bool:
    return bool(YEAR_PATTERN.match(normalize_text(text).replace(" ", "")))


def guess_cell_type(text: Any) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return "empty"
    if is_valid_year_header(normalized):
        return "year"
    if NUMBER_PATTERN.match(normalized):
        return "percent" if normalized.endswith("%") else "numeric"
    if contains_cjk(normalized):
        return "label"
    return "unknown"


def is_numeric_like(text: Any) -> bool:
    normalized = normalize_text(text)
    if normalized in MISSING_TOKEN_SET:
        return True
    return bool(NUMBER_PATTERN.match(normalized))


def parse_numeric_text(text: Any) -> Tuple[str, Optional[float], str, str]:
    normalized = normalize_text(text)
    if normalized in MISSING_TOKEN_SET:
        return "missing", None, "", "MISSING_TOKEN"

    issue_type = ""
    if COMMA_SPACE_PATTERN.search(normalized):
        issue_type = "COMMA_SPACE_NUMBER"

    working = normalized
    negative = False
    if working.startswith("(") and working.endswith(")"):
        negative = True
        working = working[1:-1]
    if working.startswith("-"):
        negative = True
        working = working[1:]

    is_percent = working.endswith("%")
    working = working.replace("%", "").replace(",", "").replace(" ", "")
    if not working:
        return "missing", None, issue_type, "MISSING_TOKEN"

    try:
        value = float(working)
    except Exception:
        return "failed", None, issue_type or "NON_NUMERIC", "NUMERIC_PARSE_FAILED"

    if negative:
        value = -value
    return "ok", value, issue_type or ("PERCENT_VALUE" if is_percent else ""), "NUMERIC_PARSE_OK"


def count_common_financial_chars(text: str) -> int:
    normalized = normalize_text(text)
    return sum(1 for ch in normalized if ch in FINANCIAL_COMMON_CHARS)


def mojibake_marker_count(text: str) -> int:
    normalized = normalize_text(text)
    return sum(normalized.count(marker) for marker in MOJIBAKE_MARKERS)


def score_text_quality(text: str) -> int:
    normalized = normalize_text(text)
    if not normalized:
        return 0
    cjk_bonus = sum(1 for ch in normalized if "\u4e00" <= ch <= "\u9fff")
    common_bonus = count_common_financial_chars(normalized) * 3
    mojibake_penalty = mojibake_marker_count(normalized) * 4
    replacement_penalty = normalized.count("\ufffd") * 12 + normalized.count("?") * 2
    return cjk_bonus + common_bonus - mojibake_penalty - replacement_penalty


def is_likely_corrupted_label(text: str) -> bool:
    normalized = normalize_text(text)
    if not normalized:
        return False
    if "\ufffd" in normalized or "????" in normalized or "锟" in normalized:
        return True
    if normalized in KNOWN_SHORT_LABELS:
        return False
    if not contains_cjk(normalized):
        return False
    common_hits = count_common_financial_chars(normalized)
    mojibake_hits = mojibake_marker_count(normalized)
    cjk_count = sum(1 for ch in normalized if "\u4e00" <= ch <= "\u9fff")
    if mojibake_hits >= 2 and common_hits == 0:
        return True
    if common_hits == 0 and cjk_count >= 3 and score_text_quality(normalized) <= 0:
        return True
    return False


def is_suspicious_short_label(text: str) -> bool:
    normalized = normalize_text(text)
    if not normalized or normalized in KNOWN_SHORT_LABELS:
        return False
    compact = re.sub(r"[\s\W_]+", "", normalized)
    if compact.upper() in KNOWN_SHORT_LABELS:
        return False
    return len(compact) <= 1


def detect_table_title(grid_rows: Sequence[Sequence[str]], run_meta_title: str = "") -> Tuple[str, Optional[int]]:
    meta_title = normalize_text(run_meta_title)
    if meta_title:
        return meta_title, None
    if len(grid_rows) >= 2:
        first_row = [normalize_text(value) for value in grid_rows[0]]
        second_row = [normalize_text(value) for value in grid_rows[1]]
        first_non_empty = [value for value in first_row if value]
        if len(first_non_empty) == 1 and sum(1 for value in second_row if is_valid_year_header(value)) >= 2:
            return first_non_empty[0], 0
    return "", None


def detect_header_row(grid_rows: Sequence[Sequence[str]]) -> int:
    limit = min(4, len(grid_rows))
    best_row = 0
    best_score = -1
    for row_index in range(limit):
        row = [normalize_text(value) for value in grid_rows[row_index]]
        year_hits = sum(1 for value in row if is_valid_year_header(value))
        numeric_hits = sum(1 for value in row if NUMBER_PATTERN.match(value))
        non_empty = sum(1 for value in row if value)
        score = year_hits * 10 + non_empty - numeric_hits
        if score > best_score:
            best_row = row_index
            best_score = score
    return best_row


def detect_year_columns(grid_rows: Sequence[Sequence[str]]) -> Tuple[int, List[Dict[str, Any]], List[Dict[str, Any]]]:
    if not grid_rows:
        return 0, [], []

    header_row_index = detect_header_row(grid_rows)
    audit_rows: List[Dict[str, Any]] = []
    accepted: List[Dict[str, Any]] = []
    max_cols = max((len(row) for row in grid_rows), default=0)

    for col_index in range(max_cols):
        header_texts: List[str] = []
        for row_index in range(0, min(header_row_index + 1, len(grid_rows))):
            value = normalize_text(grid_rows[row_index][col_index]) if col_index < len(grid_rows[row_index]) else ""
            if value:
                header_texts.append(value)
        raw_header = " | ".join(header_texts)
        candidate = ""
        valid = False
        for value in reversed(header_texts):
            if is_valid_year_header(value):
                candidate = normalize_year_header(value)
                valid = True
                break
        if not candidate and header_texts:
            candidate = normalize_text(header_texts[-1])
        audit_rows.append(
            {
                "col_index": col_index,
                "raw_header_text": raw_header,
                "normalized_header_text": candidate,
                "is_valid_year": valid,
                "reason": "VALID_YEAR_HEADER" if valid else "NON_YEAR_HEADER",
            }
        )
        if valid:
            accepted.append(
                {
                    "col_index": col_index,
                    "column": candidate,
                    "raw_header_text": raw_header,
                }
            )
    return header_row_index, accepted, audit_rows


def detect_unit(table_title: str, columns: Sequence[str], labels: Sequence[str]) -> str:
    haystacks = [normalize_text(table_title), *[normalize_text(value) for value in columns], *[normalize_text(value) for value in labels[:10]]]
    for hint in UNIT_HINTS:
        if any(hint and hint in haystack for haystack in haystacks):
            return hint
    return ""


def has_real_table_grid(row_count: int, col_count: int, year_column_count: int, numeric_cell_count: int) -> bool:
    if row_count < 2 or col_count < 2:
        return False
    if year_column_count >= 2:
        return True
    return numeric_cell_count >= 4 and row_count >= 4 and col_count >= 3
