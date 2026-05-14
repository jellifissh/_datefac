from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

import pandas as pd

from extractor_quality import score_table_block
from pdfplumber_table_extractor import extract_tables_from_pdf
from table_block import dataframe_to_table_block


PROFILE_SETTINGS: Dict[str, Dict[str, Any]] = {
    "default": {},
    "text_text": {
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
        "min_words_vertical": 1,
        "min_words_horizontal": 1,
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "intersection_tolerance": 5,
        "text_tolerance": 3,
    },
    "text_lines": {
        "vertical_strategy": "text",
        "horizontal_strategy": "lines",
        "min_words_vertical": 1,
    },
}


def _normalize_df(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None:
        return None
    normalized = df.fillna("").astype(str)
    normalized = normalized.apply(lambda col: col.map(lambda v: re.sub(r"\s+", " ", v).strip()))
    normalized = normalized.loc[(normalized != "").any(axis=1), (normalized != "").any(axis=0)]
    if normalized.empty or normalized.shape[1] == 0:
        return None
    return normalized.reset_index(drop=True)


def _build_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 5, max_len: int = 300) -> str:
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        lines.append(" | ".join(cell.strip() for cell in row.tolist()))
    text = " || ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _enrich_block(block: Dict[str, Any], profile_name: str) -> Dict[str, Any]:
    df = block.get("df")
    if not isinstance(df, pd.DataFrame):
        return block
    table_block = dataframe_to_table_block(
        df=df,
        backend="pdfplumber",
        page=block.get("page"),
        table_index=block.get("table_index"),
        source_meta={"backend_profile": profile_name},
    )
    score = score_table_block(table_block)
    block["backend"] = "pdfplumber"
    block["backend_profile"] = profile_name
    block["raw_df"] = df
    block["row_count"] = int(table_block.row_count or 0)
    block["col_count"] = int(table_block.col_count or 0)
    block["non_empty_cell_count"] = int(table_block.non_empty_cell_count or 0)
    block["empty_cell_ratio"] = float(table_block.empty_cell_ratio or 0.0)
    block["quality_score"] = float(score.get("quality_score", 0.0))
    block["quality_level"] = str(score.get("quality_level", "BAD"))
    block["quality_flags"] = str(score.get("quality_flags", ""))
    return block


def _summarize_profile(profile_name: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    table_count = len(blocks)
    good_count = 0
    ok_count = 0
    bad_count = 0
    total_non_empty_cells = 0
    scores: List[float] = []

    for block in blocks:
        q_level = str(block.get("quality_level", "BAD"))
        if q_level == "GOOD":
            good_count += 1
        elif q_level == "OK":
            ok_count += 1
        else:
            bad_count += 1
        total_non_empty_cells += int(block.get("non_empty_cell_count", 0) or 0)
        scores.append(float(block.get("quality_score", 0.0) or 0.0))

    avg_quality_score = round(sum(scores) / len(scores), 4) if scores else 0.0
    return {
        "profile_name": profile_name,
        "table_count": int(table_count),
        "good_count": int(good_count),
        "ok_count": int(ok_count),
        "bad_count": int(bad_count),
        "good_ok_count": int(good_count + ok_count),
        "avg_quality_score": float(avg_quality_score),
        "total_non_empty_cells": int(total_non_empty_cells),
    }


def _extract_default_profile(pdf_path: str, extraction_config: Dict[str, Any], logger=None) -> List[Dict[str, Any]]:
    raw_blocks = extract_tables_from_pdf(pdf_path, pages="all", logger=logger, config=extraction_config)
    result: List[Dict[str, Any]] = []
    for block in raw_blocks or []:
        cloned = dict(block)
        result.append(_enrich_block(cloned, profile_name="default"))
    return result


def _extract_custom_profile(
    pdf_path: str,
    profile_name: str,
    table_settings: Dict[str, Any],
    logger=None,
) -> List[Dict[str, Any]]:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        if logger:
            logger.warning("pdfplumber not installed, skip profile=%s", profile_name)
        return []

    blocks: List[Dict[str, Any]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_no, page in enumerate(pdf.pages, start=1):
                try:
                    tables = page.extract_tables(table_settings=table_settings) or []
                    for table_idx, table in enumerate(tables, start=1):
                        raw_df = pd.DataFrame(table) if table else None
                        df = _normalize_df(raw_df)
                        if df is None:
                            continue
                        block = {
                            "backend": "pdfplumber",
                            "backend_profile": profile_name,
                            "page": page_no,
                            "table_index": table_idx,
                            "df": df,
                            "raw_df": df,
                            "rows": int(df.shape[0]),
                            "cols": int(df.shape[1]),
                            "preview": _build_preview(df),
                            "confidence": 0.8,
                            "title": "",
                            "bbox": "",
                        }
                        blocks.append(_enrich_block(block, profile_name=profile_name))
                except Exception as page_exc:
                    if logger:
                        logger.warning(
                            "pdfplumber profile page extraction failed: profile=%s page=%s err=%s",
                            profile_name,
                            page_no,
                            page_exc,
                        )
                    continue
    except Exception as exc:
        if logger:
            logger.warning("pdfplumber profile extraction failed: profile=%s err=%s", profile_name, exc)
        return []
    return blocks


def _choose_selected_profile(
    profile_stats: Dict[str, Dict[str, Any]],
    profile_order: List[str],
    profile_config: Dict[str, Any],
) -> Tuple[str, bool, str]:
    default_stats = profile_stats.get("default", _summarize_profile("default", []))
    selected_profile = "default"
    fallback_applied = False
    fallback_reason = ""

    fallback_enabled = bool(profile_config.get("fallback_enabled", True))
    trigger_count_lt = int(profile_config.get("fallback_trigger_if_table_count_lt", 3) or 3)
    trigger_all_bad = bool(profile_config.get("fallback_trigger_if_all_bad", True))
    min_good_tables = int(profile_config.get("fallback_min_good_tables", 1) or 1)

    allow_fallback = False
    reasons: List[str] = []
    if default_stats["table_count"] < trigger_count_lt:
        allow_fallback = True
        reasons.append(f"default_table_count<{trigger_count_lt}")
    if trigger_all_bad and default_stats["table_count"] > 0 and default_stats["bad_count"] == default_stats["table_count"]:
        allow_fallback = True
        reasons.append("default_all_bad")
    if default_stats["good_count"] < min_good_tables:
        allow_fallback = True
        reasons.append(f"default_good_count<{min_good_tables}")

    if fallback_enabled and allow_fallback:
        fallback_profiles = [p for p in profile_order if p != "default" and p in profile_stats]
        if fallback_profiles:
            candidates = [profile_stats[p] for p in fallback_profiles]
            candidates.sort(
                key=lambda x: (
                    int(x["good_ok_count"]),
                    float(x["avg_quality_score"]),
                    int(x["table_count"]),
                ),
                reverse=True,
            )
            best = candidates[0]
            default_key = (
                int(default_stats["good_ok_count"]),
                float(default_stats["avg_quality_score"]),
                int(default_stats["table_count"]),
            )
            best_key = (
                int(best["good_ok_count"]),
                float(best["avg_quality_score"]),
                int(best["table_count"]),
            )
            if best_key > default_key:
                selected_profile = str(best["profile_name"])
                fallback_applied = True
                fallback_reason = ",".join(reasons) or "fallback_better_profile"

    return selected_profile, fallback_applied, fallback_reason


def extract_tables_with_pdfplumber_profiles(pdf_path, config, logger=None) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    extraction_config = (config or {}).get("table_extraction", {}) or {}
    profile_config = (config or {}).get("pdfplumber_profiles", {}) or {}
    enabled_profiles = profile_config.get("profiles", ["default", "text_text", "text_lines"]) or ["default"]
    profile_order = [str(p).strip().lower() for p in enabled_profiles if str(p).strip().lower() in PROFILE_SETTINGS]
    if "default" not in profile_order:
        profile_order.insert(0, "default")

    profile_blocks: Dict[str, List[Dict[str, Any]]] = {}
    profile_stats: Dict[str, Dict[str, Any]] = {}

    for profile_name in profile_order:
        if profile_name == "default":
            blocks = _extract_default_profile(str(pdf_path), extraction_config, logger=logger)
        else:
            blocks = _extract_custom_profile(
                str(pdf_path),
                profile_name=profile_name,
                table_settings=PROFILE_SETTINGS[profile_name],
                logger=logger,
            )
        profile_blocks[profile_name] = blocks
        profile_stats[profile_name] = _summarize_profile(profile_name, blocks)

    selected_profile, fallback_applied, fallback_reason = _choose_selected_profile(
        profile_stats=profile_stats,
        profile_order=profile_order,
        profile_config=profile_config,
    )
    selected_blocks = profile_blocks.get(selected_profile, [])

    diagnostics_rows: List[Dict[str, Any]] = []
    for idx, profile_name in enumerate(profile_order):
        stats = profile_stats.get(profile_name, _summarize_profile(profile_name, []))
        diagnostics_rows.append(
            {
                "source_pdf": str(pdf_path),
                "profile_name": profile_name,
                "profile_order": idx + 1,
                "table_count": stats["table_count"],
                "good_count": stats["good_count"],
                "ok_count": stats["ok_count"],
                "bad_count": stats["bad_count"],
                "good_ok_count": stats["good_ok_count"],
                "avg_quality_score": stats["avg_quality_score"],
                "total_non_empty_cells": stats["total_non_empty_cells"],
                "selected_profile": selected_profile,
                "is_selected": profile_name == selected_profile,
                "fallback_applied": fallback_applied,
                "fallback_reason": fallback_reason,
            }
        )
    diagnostics_df = pd.DataFrame(diagnostics_rows)
    return selected_blocks, diagnostics_df

