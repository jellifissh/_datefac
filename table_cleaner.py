import hashlib
import re
from typing import Dict, List, Optional

import pandas as pd


HTML_BREAK_RE = re.compile(r"(?i)<br\s*/?>")
HTML_TAG_RE = re.compile(r"(?i)</?(?:b|mark|strong|em|span|font|sup|sub)>")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
WHITESPACE_RE = re.compile(r"\s+")
MARKDOWN_SEPARATOR_RE = re.compile(r"^[\s\-\:\|]+$")
FINANCIAL_CHAR_RE = re.compile(r"[A-Za-z0-9\u4e00-\u9fff%\-\/\.,，\(\)（）:+]")

NOISE_KEYWORDS = (
    "敬请参阅",
    "末页重要声明",
    "证券研究报告",
    "资料来源",
    "公司公告",
    "华安证券研究所",
    "Table_",
    "_page_",
    "Picture",
    "Figure",
    ".jpeg",
    ".png",
)
DISCLAIMER_KEYWORDS = (
    "敬请参阅",
    "末页重要声明",
    "证券研究报告",
    "资料来源",
    "公司公告",
    "华安证券研究所",
)
IMAGE_RESIDUE_KEYWORDS = ("_page_", "Picture", "Figure", ".jpeg", ".png")
FINANCIAL_KEYWORDS = (
    "营业",
    "收入",
    "成本",
    "净利润",
    "利润",
    "资产",
    "负债",
    "现金",
    "股本",
    "毛利率",
    "ROE",
    "ROIC",
    "EPS",
    "P/E",
    "P/B",
    "EBITDA",
    "会计年度",
    "成长能力",
    "获利能力",
    "偿债能力",
    "营运能力",
    "每股指标",
    "估值比率",
    "单位",
)
KEEP_SECTION_LABELS = (
    "单位:百万元",
    "成长能力",
    "获利能力",
    "偿债能力",
    "营运能力",
    "每股指标(元)",
    "估值比率",
)
DEFAULT_TABLE_CLEANING_CONFIG: Dict[str, object] = {
    "enabled": True,
    "strict_dedup": True,
    "log_detail": True,
    "explain": False,
    "explain_sample_limit": 20,
}


def clean_cell(value):
    if value is None:
        return ""
    text = str(value)
    text = HTML_BREAK_RE.sub(" ", text)
    text = HTML_TAG_RE.sub("", text)
    text = CONTROL_CHAR_RE.sub("", text)
    text = text.strip()
    text = WHITESPACE_RE.sub(" ", text)
    return text


def _row_values(row) -> List[str]:
    return [clean_cell(v) for v in row.tolist()]


def _row_effective_count(row_values: List[str]) -> int:
    return sum(1 for v in row_values if v)


def _contains_financial_digit(joined: str) -> bool:
    numeric_tokens = re.findall(r"-?\d[\d,]*(?:\.\d+)?%?", joined)
    if not numeric_tokens:
        return False
    for token in numeric_tokens:
        digit_count = sum(1 for c in token if c.isdigit())
        if digit_count >= 2 or "." in token or "%" in token:
            return True
    return False


def _contains_financial_keyword(joined: str) -> bool:
    return any(keyword in joined for keyword in FINANCIAL_KEYWORDS)


def _is_markdown_separator_row(row_values: List[str]) -> bool:
    compact = "".join(row_values).strip()
    return bool(compact) and bool(MARKDOWN_SEPARATOR_RE.fullmatch(compact))


def _is_keep_section_label(row_values: List[str]) -> bool:
    nonempty = [v for v in row_values if v]
    return len(nonempty) == 1 and nonempty[0] in KEEP_SECTION_LABELS


def _is_image_residue_row(row_values: List[str]) -> bool:
    joined = " ".join(v for v in row_values if v).strip()
    if not joined:
        return False
    return any(keyword in joined for keyword in IMAGE_RESIDUE_KEYWORDS) and not _contains_financial_digit(joined)


def _is_disclaimer_row(row_values: List[str]) -> bool:
    joined = " ".join(v for v in row_values if v).strip()
    if not joined:
        return False
    if not any(keyword in joined for keyword in DISCLAIMER_KEYWORDS):
        return False
    return not _contains_financial_digit(joined)


def _contains_noise_keyword(row_values: List[str]) -> bool:
    joined = " ".join(v for v in row_values if v).strip()
    return any(keyword in joined for keyword in NOISE_KEYWORDS)


def _is_garbled_row(row_values: List[str]) -> bool:
    joined = " ".join(v for v in row_values if v).strip()
    if not joined:
        return False
    if _contains_financial_digit(joined) or _contains_financial_keyword(joined):
        return False
    visible_chars = [c for c in joined if not c.isspace()]
    if not visible_chars:
        return False
    financial_chars = sum(1 for c in visible_chars if FINANCIAL_CHAR_RE.match(c))
    symbol_ratio = 1 - (financial_chars / max(len(visible_chars), 1))
    nonempty_cells = len([v for v in row_values if v])
    has_letters_or_chinese = bool(re.search(r"[A-Za-z\u4e00-\u9fff]", joined))
    if nonempty_cells <= 3 and symbol_ratio > 0.55:
        return True
    return nonempty_cells <= 3 and (not has_letters_or_chinese or len(visible_chars) <= 12)


def _is_repeated_header_row(row_values: List[str], columns: List[str], threshold: float = 0.6) -> bool:
    if not row_values or not columns:
        return False
    normalized_row = [clean_cell(v) for v in row_values]
    normalized_columns = [clean_cell(v) for v in columns]
    compare_len = min(len(normalized_row), len(normalized_columns))
    if compare_len == 0:
        return False
    same_count = sum(
        1 for i in range(compare_len)
        if normalized_row[i] and normalized_columns[i] and normalized_row[i] == normalized_columns[i]
    )
    return (same_count / compare_len) >= threshold


def _drop_empty_rows_and_cols(df: pd.DataFrame):
    normalized = df.apply(lambda col: col.map(clean_cell))
    row_nonempty = normalized.apply(lambda row: any(v != "" for v in row), axis=1)
    col_nonempty = normalized.apply(lambda col: any(v != "" for v in col), axis=0)
    return df.loc[row_nonempty, col_nonempty], normalized, row_nonempty, col_nonempty


def _resolve_cleaning_config(table_cleaning_config=None):
    merged = DEFAULT_TABLE_CLEANING_CONFIG.copy()
    if table_cleaning_config:
        merged.update(table_cleaning_config)
    return merged


def _preview_text(parts, max_len=200):
    text = " | ".join([clean_cell(p) for p in parts if clean_cell(p)])
    text = text.encode("gbk", errors="replace").decode("gbk", errors="replace")
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _log_explain(logger, config, table_index, samples, kind):
    if not logger or not config.get("explain", False):
        return
    limit = int(config.get("explain_sample_limit", 20))
    for sample in samples[:limit]:
        logger.info(
            "TableCleaner explain: table_index=%s kind=%s %s",
            table_index,
            kind,
            sample,
        )


def clean_dataframe(df, logger=None, table_index: Optional[int] = None, table_cleaning_config=None):
    if df is None:
        return None

    config = _resolve_cleaning_config(table_cleaning_config)
    original_shape = df.shape
    cleaned = df.copy()
    cleaned.columns = [clean_cell(col) for col in cleaned.columns]
    cleaned = cleaned.apply(lambda col: col.map(clean_cell))

    before_cols = cleaned.shape[1]
    before_rows = cleaned.shape[0]
    cleaned, normalized, row_nonempty, col_nonempty = _drop_empty_rows_and_cols(cleaned)
    empty_row_removed = before_rows - cleaned.shape[0]
    empty_col_removed = before_cols - cleaned.shape[1]

    empty_row_samples = []
    for idx, keep in row_nonempty.items():
        if not keep:
            preview = _preview_text(normalized.loc[idx].tolist())
            empty_row_samples.append(f"row_index={idx} reason=empty_row content={preview}")

    empty_col_samples = []
    for col_name, keep in col_nonempty.items():
        if not keep:
            empty_col_samples.append(f"col_name={clean_cell(col_name)} reason=empty_column")

    _log_explain(logger, config, table_index, empty_row_samples, "row")
    _log_explain(logger, config, table_index, empty_col_samples, "column")

    if cleaned.empty or cleaned.shape[1] == 0:
        if logger and config["log_detail"]:
            logger.info(
                "表格清洗完成: table_index=%s, original_shape=%s, cleaned_shape=%s, empty_rows_removed=%s, empty_cols_removed=%s, noise_rows_removed=0, repeated_header_rows_removed=0",
                table_index,
                original_shape,
                cleaned.shape,
                empty_row_removed,
                empty_col_removed,
            )
        if logger and config.get("explain", False):
            logger.info(
                "TableCleaner explain: table_index=%s reason=empty_table_after_cleaning content=shape=%s",
                table_index,
                cleaned.shape,
            )
        return cleaned

    noise_drop_indices = []
    repeated_header_indices = []
    noise_samples = []
    repeated_header_samples = []
    columns = [clean_cell(c) for c in cleaned.columns.tolist()]
    for idx in cleaned.index:
        row_values = _row_values(cleaned.loc[idx])
        joined = " ".join(v for v in row_values if v).strip()
        preview = _preview_text(row_values)
        if _is_keep_section_label(row_values):
            continue
        if _row_effective_count(row_values) == 0:
            noise_drop_indices.append(idx)
            noise_samples.append(f"row_index={idx} reason=empty_row content={preview}")
            continue
        if _is_markdown_separator_row(row_values):
            noise_drop_indices.append(idx)
            noise_samples.append(f"row_index={idx} reason=markdown_separator_row content={preview}")
            continue
        if _is_image_residue_row(row_values):
            noise_drop_indices.append(idx)
            noise_samples.append(f"row_index={idx} reason=image_residue_row content={preview}")
            continue
        if _is_disclaimer_row(row_values):
            noise_drop_indices.append(idx)
            noise_samples.append(f"row_index={idx} reason=footer_disclaimer_row content={preview}")
            continue
        if _contains_noise_keyword(row_values) and not _contains_financial_digit(joined):
            noise_drop_indices.append(idx)
            noise_samples.append(f"row_index={idx} reason=footer_disclaimer_row content={preview}")
            continue
        if _is_garbled_row(row_values):
            noise_drop_indices.append(idx)
            noise_samples.append(f"row_index={idx} reason=ocr_noise_row content={preview}")
            continue
        if _is_repeated_header_row(row_values, columns) and idx != cleaned.index[0]:
            repeated_header_indices.append(idx)
            repeated_header_samples.append(f"row_index={idx} reason=repeated_header_row content={preview}")

    noise_rows_removed = len(noise_drop_indices)
    repeated_header_rows_removed = len(repeated_header_indices)
    _log_explain(logger, config, table_index, noise_samples, "row")
    _log_explain(logger, config, table_index, repeated_header_samples, "row")

    if noise_drop_indices:
        cleaned = cleaned.drop(index=noise_drop_indices)
    if repeated_header_indices:
        cleaned = cleaned.drop(index=repeated_header_indices)

    final_before_cols = cleaned.shape[1]
    final_before_rows = cleaned.shape[0]
    cleaned, normalized_after, row_nonempty_after, col_nonempty_after = _drop_empty_rows_and_cols(cleaned)

    additional_empty_row_samples = []
    for idx, keep in row_nonempty_after.items():
        if not keep:
            preview = _preview_text(normalized_after.loc[idx].tolist())
            additional_empty_row_samples.append(f"row_index={idx} reason=empty_row content={preview}")

    additional_empty_col_samples = []
    for col_name, keep in col_nonempty_after.items():
        if not keep:
            additional_empty_col_samples.append(f"col_name={clean_cell(col_name)} reason=empty_column")

    _log_explain(logger, config, table_index, additional_empty_row_samples, "row")
    _log_explain(logger, config, table_index, additional_empty_col_samples, "column")

    empty_row_removed += final_before_rows - cleaned.shape[0]
    empty_col_removed += final_before_cols - cleaned.shape[1]
    cleaned = cleaned.reset_index(drop=True)

    if logger and config["log_detail"]:
        logger.info(
            "表格清洗完成: table_index=%s, original_shape=%s, cleaned_shape=%s, empty_rows_removed=%s, empty_cols_removed=%s, noise_rows_removed=%s, repeated_header_rows_removed=%s",
            table_index,
            original_shape,
            cleaned.shape,
            empty_row_removed,
            empty_col_removed,
            noise_rows_removed,
            repeated_header_rows_removed,
        )
    return cleaned


def _table_fingerprint(df: pd.DataFrame) -> str:
    header = "|".join(clean_cell(c) for c in df.columns.tolist())
    preview_rows = []
    for _, row in df.head(8).iterrows():
        preview_rows.append("|".join(clean_cell(v) for v in row.tolist()))
    payload = f"{df.shape}|{header}|{'||'.join(preview_rows)}"
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def deduplicate_tables(df_list, logger=None, table_cleaning_config=None):
    config = _resolve_cleaning_config(table_cleaning_config)
    seen = {}
    deduped = []
    removed_indices = []
    for idx, df in enumerate(df_list):
        fingerprint = _table_fingerprint(df)
        if fingerprint in seen:
            removed_indices.append(idx)
            if logger and config.get("explain", False):
                logger.info(
                    "TableCleaner explain: table_index=%s reason=duplicate_table_fingerprint duplicate_of=%s fingerprint=%s",
                    idx,
                    seen[fingerprint],
                    fingerprint[:12],
                )
            continue
        seen[fingerprint] = idx
        deduped.append(df)
    if logger:
        logger.info(
            "表格去重结果: original_count=%s, deduped_count=%s, removed_duplicate_indices=%s",
            len(df_list),
            len(deduped),
            removed_indices,
        )
    return deduped


def clean_dataframe_list(df_list, logger=None, table_cleaning_config=None):
    config = _resolve_cleaning_config(table_cleaning_config)
    cleaned_tables = []
    original_count = len(df_list)
    dropped_empty_indices = []
    for idx, df in enumerate(df_list):
        cleaned = clean_dataframe(df, logger=logger, table_index=idx, table_cleaning_config=config)
        if cleaned is None or cleaned.empty or cleaned.shape[1] == 0:
            dropped_empty_indices.append(idx)
            if logger and config.get("explain", False):
                logger.info(
                    "TableCleaner explain: table_index=%s reason=empty_table_after_cleaning content=dropped",
                    idx,
                )
            continue
        cleaned_tables.append(cleaned)
    if logger:
        logger.info(
            "表格列表清洗结果: original_count=%s, non_empty_after_clean=%s",
            original_count,
            len(cleaned_tables),
        )
        if dropped_empty_indices and config.get("explain", False):
            logger.info(
                "TableCleaner explain: dropped_empty_table_indices=%s",
                dropped_empty_indices,
            )
        if not config["log_detail"]:
            logger.info(
                "TableCleaner summary: enabled=%s, strict_dedup=%s, log_detail=%s, explain=%s, explain_sample_limit=%s",
                config["enabled"],
                config["strict_dedup"],
                config["log_detail"],
                config["explain"],
                config["explain_sample_limit"],
            )
    if not config["strict_dedup"]:
        if logger:
            logger.info("strict dedup disabled")
        return cleaned_tables
    return deduplicate_tables(cleaned_tables, logger=logger, table_cleaning_config=config)
