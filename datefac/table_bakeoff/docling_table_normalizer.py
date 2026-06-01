from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from datefac.table_bakeoff.docling_output_reader import DoclingNormalizedCell, DoclingNormalizedTable


YEAR_PATTERN = re.compile(r"^(20\d{2})([AE])?$", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"^\(?-?\d[\d,\s]*\.?\d*\)?%?$")
COMMA_SPACE_PATTERN = re.compile(r"\d,\s+\d")
MISSING_TOKEN_SET = {"-", "--", "—", "–", "N/A", "n/a"}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in _norm(text))


def normalize_header_text(text: str) -> str:
    out = _norm(text).replace("\n", " ").replace("\u3000", " ")
    out = re.sub(r"\s+", " ", out).strip()
    out = out.replace("（", "(").replace("）", ")")
    return out


def is_valid_year_header(text: str) -> bool:
    normalized = normalize_header_text(text).replace("年", "")
    return bool(YEAR_PATTERN.match(normalized))


def normalize_year_header(text: str) -> str:
    normalized = normalize_header_text(text).replace("年", "")
    match = YEAR_PATTERN.match(normalized)
    if not match:
        return normalized
    suffix = (match.group(2) or "").upper()
    return f"{match.group(1)}{suffix}" if suffix else match.group(1)


def guess_cell_type(text: str) -> str:
    normalized = normalize_header_text(text)
    if not normalized:
        return "empty"
    if is_valid_year_header(normalized):
        return "year_header"
    if NUMBER_PATTERN.match(normalized):
        return "numeric"
    if contains_cjk(normalized):
        return "cjk_text"
    return "text"


def is_numeric_like(text: str) -> bool:
    normalized = normalize_header_text(text)
    if not normalized:
        return False
    if normalized in MISSING_TOKEN_SET:
        return True
    return bool(NUMBER_PATTERN.match(normalized))


def parse_numeric_text(text: str) -> Tuple[str, Any, str, str]:
    normalized = normalize_header_text(text)
    if not normalized:
        return "empty", None, "", "EMPTY_TEXT"
    if normalized in MISSING_TOKEN_SET:
        return "missing", None, "", "MISSING_TOKEN"

    issue_type = ""
    if COMMA_SPACE_PATTERN.search(normalized):
        issue_type = "COMMA_SPACE_NUMBER"

    negative = False
    working = normalized
    if working.startswith("(") and working.endswith(")"):
        negative = True
        working = working[1:-1]
    if working.startswith("-"):
        negative = True
        working = working[1:]

    is_percent = "%" in working
    working = working.replace("%", "").replace(",", "").replace(" ", "")

    try:
        value = float(working)
    except Exception:
        return "failed", None, issue_type or "NON_NUMERIC", "NUMERIC_PARSE_FAILED"

    if negative:
        value = -value
    return "ok", value, issue_type or ("PERCENT_VALUE" if is_percent else ""), "NUMERIC_PARSE_OK"


def build_grid(table: DoclingNormalizedTable) -> Dict[Tuple[int, int], DoclingNormalizedCell]:
    grid: Dict[Tuple[int, int], DoclingNormalizedCell] = {}
    for cell in table.cells:
        for row_idx in range(cell.row_index, cell.row_index + max(1, cell.row_span)):
            for col_idx in range(cell.col_index, cell.col_index + max(1, cell.col_span)):
                grid[(row_idx, col_idx)] = cell
    return grid


def header_rows(table: DoclingNormalizedTable) -> List[int]:
    return sorted(set(cell.row_index for cell in table.cells if cell.is_header))


def detected_year_columns(table: DoclingNormalizedTable) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    grid = build_grid(table)
    header_row_ids = header_rows(table) or [0]
    accepted: List[str] = []
    rejected: List[str] = []
    audit_rows: List[Dict[str, Any]] = []
    seen_cols = sorted(set(col for (_, col) in grid.keys()))

    for col_idx in seen_cols:
        header_texts: List[str] = []
        for row_idx in header_row_ids:
            cell = grid.get((row_idx, col_idx))
            if cell and _norm(cell.text):
                header_texts.append(normalize_header_text(cell.text))

        raw_header = " | ".join(header_texts)
        valid_header = next((text for text in reversed(header_texts) if is_valid_year_header(text)), "")
        candidate_header = valid_header or (header_texts[-1] if header_texts else "")
        normalized_header = normalize_year_header(candidate_header)
        valid = bool(valid_header)
        reason = "VALID_YEAR_HEADER" if valid else "NON_YEAR_HEADER"

        audit_rows.append(
            {
                "table_index": table.table_index,
                "raw_header_text": raw_header,
                "normalized_header_text": normalized_header,
                "is_valid_year": valid,
                "reason": reason,
                "col_index": col_idx,
            }
        )
        if valid:
            accepted.append(normalized_header)
        elif raw_header:
            rejected.append(raw_header)

    return accepted, rejected, audit_rows
