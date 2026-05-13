import os
import time
import json
import sys
import traceback
import re
import tempfile
from datetime import datetime
import logging
import pandas as pd
import multiprocessing
from pathlib import Path

from artifact_names import (
    ARTIFACT_MARKDOWN,
    ARTIFACT_TABLES,
    ARTIFACT_SUMMARY,
    ARTIFACT_MERGE_DIAGNOSTICS,
    ARTIFACT_SEGMENT_MAP,
)
from ai_summary_service import generate_investment_summary
from config_manager import ConfigManager, DEFAULT_CONFIG
from logger_utils import setup_logging
from table_cleaner import clean_dataframe_list
from table_classifier import classify_tables, export_classification_report
from financial_standardizer import standardize_core_financials, export_standardized_financials
from pdfplumber_table_extractor import (
    extract_tables_from_pdf,
    table_blocks_to_dfs,
    build_table_index_dataframe,
)
from pdfplumber_table_postprocessor import postprocess_pdfplumber_blocks
from pdfplumber_table_postprocessor import diagnose_cross_page_merge_candidates
from pdfplumber_table_postprocessor import evaluate_pdfplumber_table_quality
from extractor_adapter import extract_marker_table_blocks
from raw_table_exporter import export_raw_table_assets
from segment_validator import validate_segments
from table_segmenter import (
    segment_tables,
    build_segment_index_dataframe,
    build_segment_map_dataframe,
    build_source_table_preview_dataframe,
)
from run_state import DocumentRunState
from vision_runtime import build_vision_env, write_vision_env_diagnostics

# ========================================================
# 1. 运行时环境初始化
BASE_AI_PATH = DEFAULT_CONFIG["paths"]["base_ai_path"]
OLLAMA_URL = DEFAULT_CONFIG["ollama"]["url"]
MODEL_NAME = DEFAULT_CONFIG["ollama"]["model"]
OLLAMA_TIMEOUT = DEFAULT_CONFIG["ollama"]["timeout"]
INPUT_DIR = DEFAULT_CONFIG["paths"]["input_dir"]
OUTPUT_DIR = DEFAULT_CONFIG["paths"]["output_dir"]
TEMP_CACHE_DIR = DEFAULT_CONFIG["paths"]["temp_cache_dir"]
RUNTIME_FLAGS = DEFAULT_CONFIG["runtime"].copy()
LOGGER = logging.getLogger("factory_core")
ARTIFACT_BATCH_STATUS = "09_batch_run_status.xlsx"


def safe_console_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        fallback = message.encode("gbk", errors="ignore").decode("gbk", errors="ignore")
        print(fallback)


def apply_runtime_config(config):
    global BASE_AI_PATH, OLLAMA_URL, MODEL_NAME, OLLAMA_TIMEOUT, INPUT_DIR, OUTPUT_DIR, TEMP_CACHE_DIR, RUNTIME_FLAGS

    BASE_AI_PATH = config["paths"]["base_ai_path"]
    OLLAMA_URL = config["ollama"]["url"]
    MODEL_NAME = config["ollama"]["model"]
    OLLAMA_TIMEOUT = config["ollama"].get("timeout", DEFAULT_CONFIG["ollama"]["timeout"])
    INPUT_DIR = config["paths"]["input_dir"]
    OUTPUT_DIR = config["paths"]["output_dir"]
    TEMP_CACHE_DIR = config["paths"]["temp_cache_dir"]
    RUNTIME_FLAGS = config["runtime"].copy()


def initialize_runtime(config_path="config.yaml"):
    config_manager = ConfigManager(config_path=config_path)
    config = config_manager.load()
    config_manager.ensure_directories()
    config_manager.apply_environment()
    apply_runtime_config(config)

    logger, log_path = setup_logging(config["paths"]["logs_dir"])
    if config_manager.load_warning:
        logger.warning(config_manager.load_warning)
    logger.info("当前配置摘要: %s", json.dumps(config_manager.build_summary(), ensure_ascii=False))
    return config_manager, logger, log_path


def is_valid_markdown_cache(cache_path):
    return os.path.exists(cache_path) and os.path.getsize(cache_path) > 0


def build_asset_package_path(output_dir, doc_name):
    base_name = os.path.splitext(doc_name)[0]
    return os.path.join(output_dir, f"{base_name}_资产包")

# ========================================================
# 2. 核心表格处理流程（含 marker fallback）
# ========================================================

def make_columns_unique(cols):
    seen = {}
    new_cols = []
    for col in cols:
        clean_col = col.strip() if col.strip() else "未命名列"
        if clean_col in seen:
            seen[clean_col] += 1
            new_cols.append(f"{clean_col}.{seen[clean_col]}")
        else:
            seen[clean_col] = 0
            new_cols.append(clean_col)
    return new_cols

def vertical_split_table(table_str):
    """Split potential left-right glued markdown tables."""
    lines = table_str.strip().split("\n")
    if not lines:
        return [table_str]

    grid = []
    for line in lines:
        content = line.strip()
        if content.startswith("|"):
            content = content[1:]
        if content.endswith("|"):
            content = content[:-1]
        grid.append([c.strip() for c in content.split("|")])

    if not grid or len(grid[0]) < 6:
        return [table_str]

    split_idx = -1
    keywords = ["会计年度", "科目", "项目", "利润表", "负债表", "现金流量表"]
    for col_i in range(2, len(grid[0]) - 1):
        for row_i in range(min(4, len(grid))):
            if any(k in grid[row_i][col_i] for k in keywords):
                split_idx = col_i
                break
        if split_idx != -1:
            break

    if split_idx != -1:
        left_table, right_table = [], []
        for row in grid:
            left_table.append("| " + " | ".join(row[:split_idx]) + " |")
            right_table.append("| " + " | ".join(row[split_idx:]) + " |")
        return ["\n".join(left_table), "\n".join(right_table)]

    return [table_str]


def parse_md_to_df(table_str):
    """Parse markdown table string to dataframe."""
    lines = [l for l in table_str.strip().split("\n") if not re.match(r"^[\|\s:\-]+$", l.strip())]
    if len(lines) < 2:
        return None

    rows = []
    for line in lines:
        content = line.strip()
        if content.startswith("|"):
            content = content[1:]
        if content.endswith("|"):
            content = content[:-1]
        rows.append([c.strip() for c in content.split("|")])

    if not rows:
        return None

    max_cols = max(len(r) for r in rows)
    data = [r + [""] * (max_cols - len(r)) for r in rows]

    header_idx = 0
    for i, row in enumerate(data[:4]):
        row_str = "".join(row)
        valid_cells = [c for c in row if c.strip()]
        if len(valid_cells) >= 3 and ("项目" in row_str or "会计年度" in row_str or "科目" in row_str or "202" in row_str):
            header_idx = i
            break

    raw_header = data[header_idx]
    data_rows = data[header_idx + 1 :]
    if not data_rows:
        return None

    header = make_columns_unique(raw_header)
    df = pd.DataFrame(data_rows, columns=header)
    df.dropna(how="all", inplace=True)
    return df

def stage3_waterfall_engine(
    text,
    pkg_path,
    source_pdf="",
    logger=None,
    table_cleaning_config=None,
    table_classification_config=None,
    financial_standardization_config=None,
    table_segmentation_config=None,
    segment_validation_config=None,
):
    """Marker Markdown table extraction engine (kept as fallback backend)."""
    try:
        marker_raw_blocks = extract_marker_table_blocks(text or "", config={}, logger=logger)
        if marker_raw_blocks:
            export_raw_table_assets(
                marker_raw_blocks,
                pkg_path=pkg_path,
                source_pdf=source_pdf or "",
                save_workbook_func=save_workbook_robustly,
                logger=logger,
            )
        elif logger:
            logger.info("Raw table asset export skipped for marker: no raw tables parsed")
    except Exception:
        if logger:
            logger.exception("Raw table asset export failed for marker markdown blocks")

    lines = text.split("\n")
    extracted_streams = []
    current_table_lines = []
    gap_count = 0

    for line in lines:
        if line.count('|') >= 2:
            current_table_lines.append(line)
            gap_count = 0
        else:
            if current_table_lines:
                gap_count += 1
                if gap_count > 5:
                    raw_table_str = "\n".join(current_table_lines)
                    split_tables = vertical_split_table(raw_table_str)
                    for idx, sub_table in enumerate(split_tables):
                        df = parse_md_to_df(sub_table)
                        if df is not None and not df.empty:
                            extracted_streams.append({"df": df, "stream_id": idx})
                    current_table_lines = []
                    gap_count = 0

    if current_table_lines:
        for idx, sub_table in enumerate(vertical_split_table("\n".join(current_table_lines))):
            df = parse_md_to_df(sub_table)
            if df is not None and not df.empty:
                extracted_streams.append({"df": df, "stream_id": idx})

    if not extracted_streams:
        return 0

    final_dfs = []
    for item in extracted_streams:
        df = item["df"]
        stream_id = item["stream_id"]

        if not final_dfs:
            final_dfs.append({"df": df, "stream_id": stream_id})
            continue

        prev_item = final_dfs[-1]
        prev_df = prev_item["df"]

        col_overlap = len(set(df.columns) & set(prev_df.columns))
        is_same_structure = len(df.columns) == len(prev_df.columns) and col_overlap >= len(df.columns) // 2

        if is_same_structure and stream_id == prev_item["stream_id"]:
            fake_header_row = pd.DataFrame([df.columns.tolist()], columns=prev_df.columns)
            current_data = df.copy()
            current_data.columns = prev_df.columns
            final_dfs[-1]["df"] = pd.concat([prev_df, fake_header_row, current_data], ignore_index=True)
        else:
            final_dfs.append({"df": df, "stream_id": stream_id})

    pure_dfs = [item["df"] for item in final_dfs]
    return postprocess_and_export_tables(
        pure_dfs,
        pkg_path,
        logger=logger,
        table_cleaning_config=table_cleaning_config,
        table_classification_config=table_classification_config,
        financial_standardization_config=financial_standardization_config,
        segment_validation_config=segment_validation_config,
        backend="marker",
        table_segmentation_config=table_segmentation_config,
    )

def save_excel_robustly(df_list, target_path):
    final_path = target_path
    if os.path.exists(target_path):
        try:
            with open(target_path, 'a'): pass
        except PermissionError:
            timestamp = datetime.now().strftime("%H%M%S")
            final_path = target_path.replace(".xlsx", f"_副本_{timestamp}.xlsx")

    with pd.ExcelWriter(final_path, engine='openpyxl') as writer:
        for i, df in enumerate(df_list):
            raw_name = str(df.columns[0]).strip() if not df.empty else f"Table{i+1}"
            sheet_title = re.sub(r'[\\/*?:\[\]]', '', raw_name)[:20].strip()
            if not sheet_title or len(sheet_title) < 2: sheet_title = f"Table_{i+1}"
            df.to_excel(writer, sheet_name=sheet_title, index=False)
    return final_path


def _safe_sheet_name(raw_name, used_names=None):
    clean_name = re.sub(r"[\\/*?:\[\]]", "_", str(raw_name or "").strip()) or "Sheet"
    clean_name = clean_name[:31]
    if used_names is None:
        return clean_name
    base = clean_name
    idx = 1
    while clean_name in used_names:
        suffix = f"_{idx}"
        clean_name = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used_names.add(clean_name)
    return clean_name


def save_excel_with_named_sheets(df_list, sheet_names, target_path, index_df=None, add_index_sheet=False):
    final_path = target_path
    if os.path.exists(target_path):
        try:
            with open(target_path, "a"):
                pass
        except PermissionError:
            timestamp = datetime.now().strftime("%H%M%S")
            final_path = target_path.replace(".xlsx", f"_副本_{timestamp}.xlsx")

    used_names = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        if add_index_sheet and index_df is not None:
            index_sheet_name = _safe_sheet_name("00_目录", used_names)
            index_df.to_excel(writer, sheet_name=index_sheet_name, index=False)

        for i, df in enumerate(df_list):
            sheet_name = sheet_names[i] if i < len(sheet_names) else f"Table_{i+1}"
            safe_name = _safe_sheet_name(sheet_name, used_names)
            df.to_excel(writer, sheet_name=safe_name, index=False)
    return final_path


def save_single_df_robustly(df, target_path, sheet_name="sheet1"):
    final_path = target_path
    if os.path.exists(target_path):
        try:
            with open(target_path, "a"):
                pass
        except PermissionError:
            timestamp = datetime.now().strftime("%H%M%S")
            final_path = target_path.replace(".xlsx", f"_副本_{timestamp}.xlsx")
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        safe_name = _safe_sheet_name(sheet_name)
        df.to_excel(writer, sheet_name=safe_name, index=False)
    return final_path


def save_workbook_robustly(sheet_df_map, target_path):
    final_path = target_path
    if os.path.exists(target_path):
        try:
            with open(target_path, "a"):
                pass
        except PermissionError:
            timestamp = datetime.now().strftime("%H%M%S")
            final_path = target_path.replace(".xlsx", f"_副本_{timestamp}.xlsx")

    used_names = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for raw_name, df in (sheet_df_map or {}).items():
            safe_name = _safe_sheet_name(raw_name, used_names)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe_name, index=False)
    return final_path


def export_batch_run_status(run_states, output_dir, logger=None):
    rows = []
    for state in run_states or []:
        rows.append(
            {
                "doc_name": state.doc_name,
                "status": state.status,
                "markdown_available": state.markdown_available,
                "vision_attempted": state.vision_attempted,
                "vision_success": state.vision_success,
                "vision_error": state.vision_error,
                "pdfplumber_attempted": state.pdfplumber_attempted,
                "pdfplumber_success": state.pdfplumber_success,
                "table_count": state.table_count,
                "ai_summary_success": state.ai_summary_success,
                "error_message": state.error_message,
                "asset_package_path": state.asset_package_path,
            }
        )
    df = pd.DataFrame(rows)
    target_path = os.path.join(output_dir, ARTIFACT_BATCH_STATUS)
    final_path = save_single_df_robustly(df, target_path, sheet_name="batch_status")
    if logger:
        logger.info("批次状态输出: %s", final_path)
    return final_path


def postprocess_and_export_tables(
    df_list,
    pkg_path,
    logger=None,
    table_cleaning_config=None,
    table_classification_config=None,
    financial_standardization_config=None,
    segment_validation_config=None,
    sheet_names=None,
    add_index_sheet=False,
    index_df=None,
    backend="marker",
    table_segmentation_config=None,
):
    excel_path = os.path.join(pkg_path, ARTIFACT_TABLES)
    pure_dfs = df_list or []
    cleaned_dfs = pure_dfs
    cleaning_config = table_cleaning_config or {}
    if logger:
        logger.info(
            "TableCleaner enabled=%s strict_dedup=%s log_detail=%s explain=%s explain_sample_limit=%s",
            cleaning_config.get("enabled", True),
            cleaning_config.get("strict_dedup", True),
            cleaning_config.get("log_detail", True),
            cleaning_config.get("explain", False),
            cleaning_config.get("explain_sample_limit", 20),
        )

    if cleaning_config.get("enabled", True):
        try:
            cleaned_dfs = clean_dataframe_list(pure_dfs, logger=logger, table_cleaning_config=cleaning_config)
        except Exception:
            cleaned_dfs = pure_dfs
            if logger:
                logger.exception("表格清洗层异常，已回退使用原始表格导出。")
    else:
        cleaned_dfs = pure_dfs
        if logger:
            logger.info("TableCleaner disabled, export raw tables")
    if logger:
        logger.info("TableCleaner cleaned table count=%s", len(cleaned_dfs))

    source_tables_for_segment_diag = list(cleaned_dfs)

    segment_config = table_segmentation_config or {}
    segmenter_enabled = bool(segment_config.get("enabled", True))
    apply_to_backend = str(segment_config.get("apply_to_backend", "marker")).strip().lower()
    segment_add_index_sheet = bool(segment_config.get("add_index_sheet", True))
    segmenter_applied = False
    segment_metadata = []
    if logger:
        logger.info(
            "TableSegmenter enabled=%s backend=%s apply_to_backend=%s",
            segmenter_enabled,
            backend,
            apply_to_backend,
        )

    if segmenter_enabled and backend == apply_to_backend:
        try:
            segmented_dfs, segment_metadata = segment_tables(
                cleaned_dfs,
                logger=logger,
                config=segment_config,
            )
            if logger:
                logger.info(
                    "TableSegmenter input table count=%s output segment count=%s",
                    len(cleaned_dfs),
                    len(segmented_dfs),
                )
            if segmented_dfs and len(segmented_dfs) >= len(cleaned_dfs):
                cleaned_dfs = segmented_dfs
                segmenter_applied = True
                if logger:
                    logger.info("TableSegmenter applied on marker backend")
            elif logger:
                logger.info("TableSegmenter skipped apply due to insufficient segments")
        except Exception:
            if logger:
                logger.exception("TableSegmenter exception, fallback to cleaned tables")
            segmenter_applied = False
            segment_metadata = []

    cleaned_sheet_names = sheet_names or []
    cleaned_index_df = index_df
    if segmenter_applied and segment_metadata:
        cleaned_sheet_names = [str(m.get("sheet_name", "")) for m in segment_metadata]
        if segment_add_index_sheet:
            cleaned_index_df = build_segment_index_dataframe(segment_metadata)
            add_index_sheet = True
        if logger:
            logger.info("TableSegmenter final sheet_names=%s", cleaned_sheet_names)

    if sheet_names:
        if len(cleaned_dfs) == len(sheet_names):
            cleaned_sheet_names = list(sheet_names)
        elif len(cleaned_dfs) < len(sheet_names):
            cleaned_sheet_names = list(sheet_names[: len(cleaned_dfs)])
            if index_df is not None and not index_df.empty:
                cleaned_index_df = index_df.iloc[: len(cleaned_dfs)].reset_index(drop=True)
            if logger:
                logger.warning(
                    "sheet_names mismatch: raw_sheet_names=%s cleaned_count=%s use_first_n_sheet_names",
                    len(sheet_names),
                    len(cleaned_dfs),
                )
        else:
            cleaned_sheet_names = []
            cleaned_index_df = None
            if logger:
                logger.warning(
                    "sheet_names mismatch: cleaned_count(%s) > raw_sheet_names(%s), fallback unnamed export",
                    len(cleaned_dfs),
                    len(sheet_names),
                )

    try:
        if cleaned_sheet_names:
            final_excel_path = save_excel_with_named_sheets(
                cleaned_dfs,
                cleaned_sheet_names,
                excel_path,
                index_df=cleaned_index_df,
                add_index_sheet=add_index_sheet,
            )
        else:
            final_excel_path = save_excel_robustly(cleaned_dfs, excel_path)

        if logger:
            logger.info("Final exported table count=%s", len(cleaned_dfs))
            logger.info("final_excel_path=%s", final_excel_path)
            logger.info("结构化 Excel 输出: %s", final_excel_path)

        segment_map_df = None
        source_preview_df = None
        if segmenter_applied and segment_metadata:
            try:
                segment_map_df = build_segment_map_dataframe(segment_metadata)
                source_preview_df = build_source_table_preview_dataframe(
                    source_tables_for_segment_diag,
                    segment_metadata,
                    context_rows=3,
                    max_cols=8,
                )
            except Exception:
                segment_map_df = None
                source_preview_df = None
                if logger:
                    logger.exception("TableSegmenter diagnostics dataframe build failed")

        classification_config = table_classification_config or {}
        classification_results = None
        if classification_config.get("enabled", True):
            try:
                if logger:
                    logger.info(
                        "TableClassifier enabled=%s output_report=%s min_confidence=%s log_detail=%s",
                        classification_config.get("enabled", True),
                        classification_config.get("output_report", True),
                        classification_config.get("min_confidence", 0.25),
                        classification_config.get("log_detail", True),
                    )
                classification_results = classify_tables(cleaned_dfs, logger=logger, config=classification_config)
                if classification_config.get("output_report", True):
                    export_classification_report(classification_results, pkg_path, save_excel_robustly, logger=logger)
            except Exception:
                if logger:
                    logger.exception("表格分类层异常，已跳过分类输出。")
        else:
            if logger:
                logger.info("TableClassifier disabled")

        # Segment validation diagnostics (no behavior change; best-effort only)
        validation_cfg = segment_validation_config or {}
        if bool(validation_cfg.get("enabled", True)) and bool(validation_cfg.get("output_report", True)):
            try:
                validation_df = validate_segments(
                    cleaned_dfs,
                    sheet_names=cleaned_sheet_names if cleaned_sheet_names else None,
                    classification_results=classification_results,
                    segment_metadata=segment_metadata if segmenter_applied else None,
                    logger=logger,
                    config=validation_cfg,
                )
                segment_diag_path = os.path.join(pkg_path, ARTIFACT_SEGMENT_MAP)
                sheet_map = {"segment_validation": validation_df}
                if segment_map_df is not None:
                    sheet_map["segment_map"] = segment_map_df
                if source_preview_df is not None:
                    sheet_map["source_table_preview"] = source_preview_df
                final_validation_path = save_workbook_robustly(sheet_map, segment_diag_path)
                if logger:
                    logger.info("Segment validation diagnostics output: %s", final_validation_path)
            except Exception:
                if logger:
                    logger.exception("Segment validation diagnostics failed (ignored)")
        else:
            # Keep existing segment_map diagnostics behavior when validation is disabled.
            if segment_map_df is not None and source_preview_df is not None:
                try:
                    segment_diag_path = os.path.join(pkg_path, ARTIFACT_SEGMENT_MAP)
                    final_segment_diag_path = save_workbook_robustly(
                        {
                            "segment_map": segment_map_df,
                            "source_table_preview": source_preview_df,
                        },
                        segment_diag_path,
                    )
                    if logger:
                        logger.info("TableSegmenter diagnostics output: %s", final_segment_diag_path)
                except Exception:
                    if logger:
                        logger.exception("TableSegmenter diagnostics export failed")

        standardization_config = financial_standardization_config or {}
        if standardization_config.get("enabled", True):
            try:
                if logger:
                    logger.info(
                        "FinancialStandardizer enabled=%s output_report=%s log_detail=%s",
                        standardization_config.get("enabled", True),
                        standardization_config.get("output_report", True),
                        standardization_config.get("log_detail", True),
                    )
                standardization_result = standardize_core_financials(
                    cleaned_dfs,
                    classification_results=classification_results,
                    logger=logger,
                    config=standardization_config,
                )
                if standardization_config.get("output_report", True):
                    export_standardized_financials(
                        standardization_result,
                        pkg_path,
                        save_excel_func=save_excel_robustly,
                        logger=logger,
                    )
            except Exception:
                if logger:
                    logger.exception("核心财务指标标准化异常，已跳过 05 输出。")
        else:
            if logger:
                logger.info("FinancialStandardizer disabled")
        return len(cleaned_dfs)
    except Exception as e:
        print(f"[!] 资产包 Excel 生成失败: {e}")
        if logger:
            logger.exception("资产包 Excel 生成失败: %s", excel_path)
        return 0

def _build_pdfplumber_sheet_name(table_block, strategy="page_table"):
    hint = str(table_block.get("sheet_name_hint") or "").strip()
    if hint:
        return hint
    page = table_block.get("page", "NA")
    table_index = table_block.get("table_index", "NA")
    if strategy == "page_table":
        return f"p{page}_t{table_index}"
    return f"p{page}_t{table_index}"


def generate_structured_tables(
    full_text,
    pkg_path,
    config,
    logger,
    pdf_path=None,
    run_state=None,
):
    extraction_config = config.get("table_extraction", {})
    preferred_backend = str(extraction_config.get("preferred_backend", "pdfplumber")).strip().lower()
    pdfplumber_enabled = bool(extraction_config.get("pdfplumber_enabled", True))
    fallback_to_marker = bool(extraction_config.get("fallback_to_marker", True))
    min_pdfplumber_tables = int(extraction_config.get("min_pdfplumber_tables", 1) or 1)
    add_index_sheet = bool(extraction_config.get("add_index_sheet", True))
    sheet_name_strategy = str(extraction_config.get("sheet_name_strategy", "page_table")).strip().lower()

    marker_kwargs = {
        "logger": logger,
        "table_cleaning_config": config.get("table_cleaning", {}),
        "table_classification_config": config.get("table_classification", {}),
        "financial_standardization_config": config.get("financial_standardization", {}),
        "table_segmentation_config": config.get("table_segmentation", {}),
        "segment_validation_config": config.get("segment_validation", {}),
    }

    should_try_pdfplumber = (
        preferred_backend == "pdfplumber"
        and pdfplumber_enabled
        and pdf_path
        and os.path.exists(pdf_path)
    )
    if run_state and should_try_pdfplumber:
        run_state.pdfplumber_attempted = True
    if should_try_pdfplumber:
        try:
            raw_blocks = extract_tables_from_pdf(pdf_path, pages="all", logger=logger, config=extraction_config)
            if len(raw_blocks) >= min_pdfplumber_tables:
                logger.info("Structured table extraction backend=pdfplumber, tables=%s", len(raw_blocks))
                logger.info("pdfplumber raw table count=%s", len(raw_blocks))
                try:
                    export_raw_table_assets(
                        raw_blocks,
                        pkg_path=pkg_path,
                        source_pdf=pdf_path or "",
                        save_workbook_func=save_workbook_robustly,
                        logger=logger,
                    )
                except Exception:
                    logger.exception("Raw table asset export failed for pdfplumber raw blocks")
                quality_gate_enabled = bool(extraction_config.get("pdfplumber_quality_gate", True))
                quality_summary = evaluate_pdfplumber_table_quality(raw_blocks, logger=logger, config=extraction_config)
                if quality_gate_enabled and not quality_summary.get("should_use_pdfplumber", False):
                    reason = quality_summary.get("fallback_reason", "") or "quality_gate_failed"
                    logger.warning("pdfplumber quality gate failed, fallback to marker")
                    logger.warning("fallback_reason=%s", reason)
                    if fallback_to_marker:
                        logger.info("Structured table extraction backend=marker")
                        return stage3_waterfall_engine(
                            full_text,
                            pkg_path,
                            source_pdf=pdf_path or "",
                            **marker_kwargs,
                        )
                    return 0
                diagnostics = []
                if extraction_config.get("merge_diagnostics_enabled", True):
                    diagnostics = diagnose_cross_page_merge_candidates(raw_blocks, logger=logger, config=extraction_config)
                    if extraction_config.get("output_merge_diagnostics", True):
                        try:
                            diagnostics_df = pd.DataFrame(diagnostics)
                            diag_path = os.path.join(pkg_path, ARTIFACT_MERGE_DIAGNOSTICS)
                            final_diag_path = save_single_df_robustly(diagnostics_df, diag_path, sheet_name="merge_diagnostics")
                            logger.info("pdfplumber merge diagnostics output: %s", final_diag_path)
                        except Exception:
                            logger.exception("pdfplumber merge diagnostics export failed")
                processed_blocks = postprocess_pdfplumber_blocks(raw_blocks, logger=logger, config=extraction_config)
                logger.info("pdfplumber processed table count=%s", len(processed_blocks))
                for block in processed_blocks:
                    logger.info(
                        "processed block source_blocks=%s business_hint=%s",
                        block.get("source_blocks", []),
                        block.get("business_hint", ""),
                    )
                def _page_sort_key(value):
                    if isinstance(value, int):
                        return value
                    s = str(value or "")
                    if "-" in s:
                        left = s.split("-", 1)[0]
                        return int(left) if left.isdigit() else 0
                    return int(s) if s.isdigit() else 0

                def _table_sort_key(value):
                    if isinstance(value, int):
                        return value
                    s = str(value or "")
                    if "+" in s:
                        left = s.split("+", 1)[0]
                        return int(left) if left.isdigit() else 0
                    return int(s) if s.isdigit() else 0

                processed_blocks = sorted(
                    processed_blocks,
                    key=lambda x: (_page_sort_key(x.get("page")), _table_sort_key(x.get("table_index"))),
                )
                raw_dfs = table_blocks_to_dfs(processed_blocks)
                sheet_names = [
                    _build_pdfplumber_sheet_name(block, strategy=sheet_name_strategy)
                    for block in processed_blocks
                ]
                logger.info("raw sheet_names=%s", sheet_names)
                index_df = build_table_index_dataframe(processed_blocks, sheet_names) if add_index_sheet else None
                pdf_cleaning_config = (config.get("table_cleaning", {}) or {}).copy()
                pdf_cleaning_config["strict_dedup"] = False
                logger.info(
                    "pdfplumber branch strict_dedup override applied: strict_dedup=%s",
                    pdf_cleaning_config.get("strict_dedup"),
                )
                table_count = postprocess_and_export_tables(
                    raw_dfs,
                    pkg_path,
                    logger=logger,
                    table_cleaning_config=pdf_cleaning_config,
                    table_classification_config=config.get("table_classification", {}),
                    financial_standardization_config=config.get("financial_standardization", {}),
                    segment_validation_config=config.get("segment_validation", {}),
                    sheet_names=sheet_names,
                    add_index_sheet=add_index_sheet,
                    index_df=index_df,
                    backend="pdfplumber",
                    table_segmentation_config=config.get("table_segmentation", {}),
                )
                if run_state:
                    run_state.pdfplumber_success = table_count > 0
                return table_count
            reason = f"insufficient_tables({len(raw_blocks)} < {min_pdfplumber_tables})"
            logger.warning("Structured table extraction backend=pdfplumber fallback to marker, reason=%s", reason)
        except Exception as exc:
            logger.warning("Structured table extraction backend=pdfplumber fallback to marker, reason=%s", exc)
        if fallback_to_marker:
            logger.info("Structured table extraction backend=marker")
            if run_state:
                run_state.marker_attempted = True
            return stage3_waterfall_engine(
                full_text,
                pkg_path,
                source_pdf=pdf_path or "",
                **marker_kwargs,
            )
        return 0

    if preferred_backend == "pdfplumber" and (not pdf_path or not os.path.exists(pdf_path)):
        logger.info("Structured table extraction backend=marker (pdf_path unavailable)")
    elif preferred_backend == "pdfplumber" and not pdfplumber_enabled:
        logger.info("Structured table extraction backend=marker (pdfplumber disabled)")
    else:
        logger.info("Structured table extraction backend=marker")
    if run_state:
        run_state.marker_attempted = True
    return stage3_waterfall_engine(
        full_text,
        pkg_path,
        source_pdf=pdf_path or "",
        **marker_kwargs,
    )

# ========================================================
# 3. 视觉子进程与 AI 摘要
# ========================================================
def write_vision_error(error_log_path, current_pdf):
    if not error_log_path:
        return
    os.makedirs(os.path.dirname(error_log_path), exist_ok=True)
    c_datalab_path = r"C:\Users\哥哥\AppData\Local\datalab"
    with open(error_log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] PDF: {current_pdf or 'UNKNOWN'}\n")
        f.write(traceback.format_exc())
        f.write("\n")
        f.write(f"DATALAB_CACHE_DIR={os.environ.get('DATALAB_CACHE_DIR', '')}\n")
        f.write(f"LOCALAPPDATA={os.environ.get('LOCALAPPDATA', '')}\n")
        f.write(f"APPDATA={os.environ.get('APPDATA', '')}\n")
        f.write(f"USERPROFILE={os.environ.get('USERPROFILE', '')}\n")
        f.write(f"HOME={os.environ.get('HOME', '')}\n")
        f.write(f"pathlib.Path.home={Path.home()}\n")
        f.write(f"tempfile.gettempdir={tempfile.gettempdir()}\n")
        f.write(f"{c_datalab_path} exists={os.path.exists(c_datalab_path)}\n")
        f.write("\n")


def configure_vision_runtime_env(base_ai_path, cache_dir, logger=None):
    env = build_vision_env(base_ai_path, cache_dir)
    os.environ.update(env)
    write_vision_env_diagnostics(env, cache_dir, phase="legacy_configure_vision_runtime_env")


def vision_worker_process(input_dir, cache_dir, files, require_cuda=True, error_log_path=None, base_ai_path=None):
    current_pdf = None
    try:
        env = build_vision_env(base_ai_path or BASE_AI_PATH, cache_dir)
        os.environ.update(env)
        write_vision_env_diagnostics(env, cache_dir, phase="before_import_marker")
        import torch
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
        write_vision_env_diagnostics(dict(os.environ), cache_dir, phase="after_import_marker")
        if require_cuda and not torch.cuda.is_available():
            raise RuntimeError("CUDA 不可用，marker 视觉解析已中止。")
        model_dict = create_model_dict() 
        converter = PdfConverter(artifact_dict=model_dict)
        for f_name in files:
            current_pdf = f_name
            rendered = converter(os.path.join(input_dir, f_name))
            txt, _, _ = text_from_rendered(rendered)
            with open(os.path.join(cache_dir, f"{f_name}.txt"), "w", encoding="utf-8") as f:
                f.write(txt)
        sys.exit(0)
    except Exception:
        write_vision_error(error_log_path, current_pdf)
        sys.exit(1)


def run_single_pdf_vision(pdf_name, logger):
    error_log_path = os.path.join(TEMP_CACHE_DIR, f"vision_error_{os.path.splitext(pdf_name)[0]}.log")
    if os.path.exists(error_log_path):
        os.remove(error_log_path)
    p = multiprocessing.Process(
        target=vision_worker_process,
        args=(
            INPUT_DIR,
            TEMP_CACHE_DIR,
            [pdf_name],
            RUNTIME_FLAGS.get("require_cuda", True),
            error_log_path,
            BASE_AI_PATH,
        ),
        name=f"marker_vision_worker_{pdf_name}",
    )
    p.start()
    p.join()
    if p.exitcode == 0:
        return True, ""
    error_message = f"vision process exitcode={p.exitcode}"
    if os.path.exists(error_log_path):
        try:
            with open(error_log_path, "r", encoding="utf-8") as f:
                detail = f.read().strip()
            if detail:
                error_message = detail[-3000:]
        except Exception:
            pass
    logger.error("单PDF vision失败: pdf=%s, error=%s", pdf_name, error_message)
    return False, error_message

def process_markdown_document(doc_name, full_text, pkg_path, config, logger, pdf_path=None, run_state=None):
    os.makedirs(pkg_path, exist_ok=True)
    markdown_path = os.path.join(pkg_path, ARTIFACT_MARKDOWN)
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    logger.info("Markdown 底稿输出: %s", markdown_path)
    if run_state:
        run_state.markdown_available = bool(full_text and full_text.strip())

    if not full_text or not full_text.strip():
        logger.warning("检测到空 Markdown: doc=%s", doc_name)
        t_count = 0
        if pdf_path and os.path.exists(pdf_path):
            logger.info("空 Markdown 场景下尝试结构化抽表: doc=%s", doc_name)
            t_count = generate_structured_tables(
                full_text="",
                pkg_path=pkg_path,
                config=config,
                logger=logger,
                pdf_path=pdf_path,
                run_state=run_state,
            )
        final_summary_df = pd.DataFrame([{
            "研报名称": doc_name,
            "解析表数": t_count,
            "状态": "空 Markdown，已跳过表格和 AI 处理",
        }])
        summary_path = os.path.join(pkg_path, ARTIFACT_SUMMARY)
        try:
            final_summary_df.to_excel(summary_path, index=False)
            actual_summary_path = summary_path
        except PermissionError:
            ts = datetime.now().strftime("%H%M%S")
            actual_summary_path = summary_path.replace(".xlsx", f"_副本_{ts}.xlsx")
            final_summary_df.to_excel(actual_summary_path, index=False)
        logger.info("空 Markdown 摘要输出: %s", actual_summary_path)
        return {
            "markdown_path": markdown_path,
            "summary_path": actual_summary_path,
            "table_count": t_count,
            "ai_summary_success": False,
        }

    t_count = generate_structured_tables(
        full_text=full_text,
        pkg_path=pkg_path,
        config=config,
        logger=logger,
        pdf_path=pdf_path,
        run_state=run_state,
    )
    logger.info("提取表格数量: doc=%s, count=%s", doc_name, t_count)

    ai_data = generate_investment_summary(full_text, doc_name, config, logger)
    ai_summary_success = "状态" not in ai_data
    if run_state:
        run_state.ai_summary_success = ai_summary_success

    final_summary_data = {
        "研报名称": doc_name,
        "解析表数": t_count,
        "投资评级": ai_data.get("投资评级", "未提取"),
        "核心逻辑": ai_data.get("核心逻辑", "未提取"),
    }
    for k, v in ai_data.items():
        if k not in final_summary_data:
            final_summary_data[k] = v

    final_summary_df = pd.DataFrame([final_summary_data])
    summary_path = os.path.join(pkg_path, ARTIFACT_SUMMARY)

    try:
        final_summary_df.to_excel(summary_path, index=False)
        actual_summary_path = summary_path
    except PermissionError:
        ts = datetime.now().strftime("%H%M%S")
        actual_summary_path = summary_path.replace(".xlsx", f"_副本_{ts}.xlsx")
        final_summary_df.to_excel(actual_summary_path, index=False)
    logger.info("投研结论 Excel 输出: %s", actual_summary_path)
    return {
        "markdown_path": markdown_path,
        "summary_path": actual_summary_path,
        "table_count": t_count,
        "ai_summary_success": ai_summary_success,
    }


def run_markdown_replay_mode(config, logger):
    replay_dir = (config["runtime"].get("markdown_replay_dir") or "").strip()
    if not replay_dir:
        logger.error("MARKDOWN_REPLAY_MODE 启用失败: markdown_replay_dir 为空。")
        safe_console_print("Markdown 回放目录为空，请检查 config.yaml。")
        return

    if not os.path.isdir(replay_dir):
        logger.error("MARKDOWN_REPLAY_MODE 启用失败: 目录不存在 -> %s", replay_dir)
        safe_console_print(f"Markdown 回放目录不存在: {replay_dir}")
        return

    replay_files = sorted(
        [
            f for f in os.listdir(replay_dir)
            if os.path.isfile(os.path.join(replay_dir, f)) and os.path.splitext(f)[1].lower() in (".txt", ".md")
        ]
    )
    logger.info("Markdown 回放目录扫描结果: %s", replay_files)
    if not replay_files:
        logger.warning("MARKDOWN_REPLAY_MODE 未发现 .txt 或 .md 文件: %s", replay_dir)
        safe_console_print("Markdown 回放目录中未发现 .txt 或 .md 文件。")
        return

    for doc_name in replay_files:
        start_t = time.time()
        source_path = os.path.join(replay_dir, doc_name)
        pkg_path = build_asset_package_path(OUTPUT_DIR, doc_name)
        logger.info("开始回放 Markdown: source=%s, pkg=%s", source_path, pkg_path)
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                full_text = f.read()
            process_markdown_document(doc_name, full_text, pkg_path, config, logger, pdf_path=None)
            safe_console_print(f"{doc_name} 回放处理完成。")
            logger.info("Markdown 回放完成: %s, elapsed=%.2fs", doc_name, time.time() - start_t)
        except Exception:
            safe_console_print(f"{doc_name} 回放处理报错。")
            logger.exception("Markdown 回放处理报错: %s", doc_name)


def run_full_pdf_mode(config, logger, log_path):
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    logger.info("扫描到 PDF 列表: %s", pdf_files)
    if not pdf_files:
        logger.warning("input 目录中未发现 PDF 文件。")
        safe_console_print("[-] 请在 input 放入 PDF。")
        return
    reuse_vision_cache = config["runtime"].get("reuse_vision_cache", False)
    run_states = []

    for f_name in pdf_files:
        start_t = time.time()
        cache_p = os.path.join(TEMP_CACHE_DIR, f"{f_name}.txt")
        source_pdf_path = os.path.abspath(os.path.join(INPUT_DIR, f_name))
        pkg_path = build_asset_package_path(OUTPUT_DIR, f_name)
        state = DocumentRunState(
            doc_name=f_name,
            pdf_path=source_pdf_path,
            asset_package_path=pkg_path,
            markdown_cache_path=cache_p,
        )
        run_states.append(state)
        logger.info("开始处理 PDF: %s", f_name)
        logger.info("Markdown 缓存路径: %s", cache_p)

        try:
            if reuse_vision_cache and is_valid_markdown_cache(cache_p):
                state.markdown_available = True
                logger.info("PDF 使用已有视觉缓存: pdf=%s, cache=%s", f_name, cache_p)
            else:
                if reuse_vision_cache and os.path.exists(cache_p) and os.path.getsize(cache_p) == 0:
                    logger.warning("发现空缓存文件，视为无效缓存并重新视觉解析: pdf=%s, cache=%s", f_name, cache_p)
                state.vision_attempted = True
                vision_ok, vision_err = run_single_pdf_vision(f_name, logger)
                state.vision_success = vision_ok
                state.vision_error = vision_err
                state.markdown_available = is_valid_markdown_cache(cache_p)
                logger.info(
                    "单PDF vision结果: pdf=%s, vision_success=%s, markdown_available=%s",
                    f_name,
                    state.vision_success,
                    state.markdown_available,
                )

            full_text = ""
            if state.markdown_available:
                try:
                    with open(cache_p, "r", encoding="utf-8") as f:
                        full_text = f.read()
                except Exception as read_exc:
                    state.markdown_available = False
                    state.error_message = f"读取Markdown缓存失败: {read_exc}"
                    logger.exception("读取Markdown缓存失败: pdf=%s", f_name)

            logger.info(
                "PDF source path for structured extraction: %s (exists=%s)",
                source_pdf_path,
                os.path.exists(source_pdf_path),
            )
            result = process_markdown_document(
                f_name,
                full_text,
                pkg_path,
                config,
                logger,
                pdf_path=source_pdf_path,
                run_state=state,
            )
            state.table_count = int(result.get("table_count", 0) or 0)
            state.ai_summary_success = bool(result.get("ai_summary_success", False))

            if state.table_count > 0 or state.markdown_available or state.ai_summary_success:
                state.status = "SUCCESS"
            else:
                state.status = "FAILED"
                if not state.error_message:
                    state.error_message = "无有效Markdown且未抽取到结构化表格"
            safe_console_print(f"{f_name} 收割完毕。")
            logger.info("PDF 处理完成: %s, elapsed=%.2fs", f_name, time.time() - start_t)
        except Exception as exc:
            state.status = "FAILED"
            state.error_message = str(exc)
            safe_console_print(f"{f_name} 处理报错。")
            logger.exception("PDF 处理报错: %s", f_name)
            continue

    try:
        export_batch_run_status(run_states, OUTPUT_DIR, logger=logger)
    except Exception:
        logger.exception("批次状态输出失败")


def run_factory():
    config_manager, logger, log_path = initialize_runtime()
    config = config_manager.config
    global LOGGER
    LOGGER = logger
    safe_console_print(f"\n{'='*60}\n   4060 投研收割机 V6.17-A (pdfplumber 优先抽表)\n{'='*60}")

    if config["runtime"].get("markdown_replay_mode", False):
        logger.info("当前运行模式: MARKDOWN_REPLAY_MODE")
        run_markdown_replay_mode(config, logger)
    else:
        logger.info("当前运行模式: FULL_PDF_MODE")
        run_full_pdf_mode(config, logger, log_path)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_factory()






