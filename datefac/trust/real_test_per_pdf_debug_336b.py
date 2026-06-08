from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    capture_official_asset_hashes,
)
from datefac.trust.real_test_full_flow_336a import (
    DEFAULT_INPUT_PDF_DIR,
    PROJECT_ROOT,
    PROTECTED_DIRTY_PATHS,
    WORKBOOK_SHEETS,
    _build_candidate_frames,
    _customer_readme_df,
    _extract_numeric_tokens,
    _extract_page_texts,
    _find_pdf_files,
    _git_cached_names_for_paths,
    _git_status_porcelain_for_paths,
    _match_metric,
    _norm_text,
    _parse_table_block,
    _safe_int,
    _truncate,
)
from pdfplumber_table_extractor import extract_tables_from_pdf


DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\real_test_debug_336b")
READY_DECISION = "REAL_TEST_PER_PDF_DEBUG_336B_READY"
PARTIAL_DECISION = "REAL_TEST_PER_PDF_DEBUG_336B_PARTIAL"
BLOCKED_DECISION = "REAL_TEST_PER_PDF_DEBUG_336B_BLOCKED"

FINANCIAL_KEYWORD_PATTERNS = [
    "\u8425\u4e1a\u6536\u5165",
    "\u5f52\u6bcd\u51c0\u5229\u6da6",
    "\u51c0\u5229\u6da6",
    "revenue",
    "net profit",
    "eps",
    "\u6bcf\u80a1\u6536\u76ca",
    "pe",
    "p/e",
    "pb",
    "p/b",
    "roe",
    "\u6bdb\u5229\u7387",
    "\u51c0\u5229\u7387",
    "\u9884\u6d4b",
    "\u4f30\u503c",
    "\u8d22\u52a1\u6570\u636e",
    "\u8d22\u52a1\u6458\u8981",
]
FORECAST_YEAR_PATTERNS = ["2024A", "2025A", "2026E", "2027E", "2028E", "2026", "2027", "2028"]
FORECAST_YEAR_RE = re.compile(r"(?:19|20)\d{2}(?:[AE])?")


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _contains_any(text: str, patterns: Sequence[str]) -> bool:
    lowered = _norm_text(text).casefold()
    return any(pattern.casefold() in lowered for pattern in patterns)


def _detect_year_tokens(text: str) -> List[str]:
    seen: List[str] = []
    for match in FORECAST_YEAR_RE.finditer(_norm_text(text)):
        token = match.group(0)
        if token not in seen:
            seen.append(token)
    return seen


def _row_debug_records(table_blocks: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table_block in table_blocks:
        df = table_block.get("df")
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        cleaned = _clean_frame(df)
        for row_index, row_values in enumerate(cleaned.to_dict(orient="records"), start=1):
            raw_values = [_norm_text(value) for value in row_values.values()]
            raw_row_text = " | ".join(value for value in raw_values if value)
            metric_matches = _match_metric(raw_row_text)
            metric_keywords = []
            seen_metrics = set()
            for rule in metric_matches:
                metric_name = _norm_text(rule.get("metric"))
                if metric_name and metric_name not in seen_metrics:
                    metric_keywords.append(metric_name)
                    seen_metrics.add(metric_name)
            rows.append(
                {
                    "page_no": table_block.get("page", ""),
                    "table_index": table_block.get("table_index", ""),
                    "row_index": row_index,
                    "raw_row_text": raw_row_text,
                    "normalized_row_text": _norm_text(raw_row_text),
                    "detected_metric_keywords": ", ".join(metric_keywords),
                    "detected_years": ", ".join(_detect_year_tokens(raw_row_text)),
                    "detected_numbers": ", ".join(_extract_numeric_tokens(raw_row_text)),
                }
            )
    return rows


def _page_text_records(page_texts: Mapping[int, str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for page_no in sorted(page_texts):
        text = _norm_text(page_texts.get(page_no, ""))
        rows.append(
            {
                "page_no": page_no,
                "text_excerpt": _truncate(text, limit=240),
                "full_text_or_long_excerpt": _truncate(text, limit=4000),
                "contains_financial_keywords": _contains_any(text, FINANCIAL_KEYWORD_PATTERNS),
                "contains_forecast_years": _contains_any(text, FORECAST_YEAR_PATTERNS),
            }
        )
    return rows


def _metric_candidate_rows(candidates: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for candidate in candidates:
        rows.append(
            {
                "candidate_id": _norm_text(candidate.get("candidate_id")),
                "page_no": candidate.get("source_page", ""),
                "table_index": candidate.get("table_index", ""),
                "row_index": candidate.get("row_index", ""),
                "metric": _norm_text(candidate.get("metric")),
                "metric_display_zh": _norm_text(candidate.get("metric_display_zh")),
                "year": _norm_text(candidate.get("year")),
                "value": _norm_text(candidate.get("value")),
                "unit": _norm_text(candidate.get("unit")),
                "evidence": _norm_text(candidate.get("source_evidence_excerpt")),
                "extraction_reason": _norm_text(candidate.get("notes")),
            }
        )
    return rows


def _routing_preview_rows(candidates: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for candidate in candidates:
        route = _norm_text(candidate.get("status"))
        route_reason = _norm_text(candidate.get("routing_reason"))
        risk_flags = ""
        if route != "reviewed" and route_reason:
            risk_flags = route_reason.upper()
        rows.append(
            {
                "candidate_id": _norm_text(candidate.get("candidate_id")),
                "route": route,
                "route_reason": route_reason,
                "risk_flags": risk_flags,
                "evidence": _norm_text(candidate.get("source_evidence_excerpt")),
            }
        )
    return rows


def _likely_forecast_pages(
    *,
    page_text_rows: Sequence[Mapping[str, Any]],
    extracted_table_rows: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
) -> List[int]:
    scores: Dict[int, int] = {}
    for row in page_text_rows:
        page_no = _safe_int(row.get("page_no"), 0)
        if page_no <= 0:
            continue
        score = 0
        if row.get("contains_financial_keywords"):
            score += 2
        if row.get("contains_forecast_years"):
            score += 3
        if score:
            scores[page_no] = scores.get(page_no, 0) + score
    for row in extracted_table_rows:
        page_no = _safe_int(row.get("page_no"), 0)
        if page_no <= 0:
            continue
        if row.get("detected_metric_keywords"):
            scores[page_no] = scores.get(page_no, 0) + 2
        if row.get("detected_years"):
            scores[page_no] = scores.get(page_no, 0) + 1
    for candidate in candidates:
        page_no = _safe_int(candidate.get("source_page"), 0)
        if page_no > 0:
            scores[page_no] = scores.get(page_no, 0) + 4
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [page_no for page_no, score in ranked if score > 0]


def _likely_failure_reason(
    *,
    candidate_count: int,
    page_text_rows: Sequence[Mapping[str, Any]],
    table_count: int,
) -> str:
    if candidate_count > 0:
        return ""
    extracted_page_count = sum(1 for row in page_text_rows if _norm_text(row.get("full_text_or_long_excerpt")))
    if extracted_page_count == 0:
        return "PDF_TEXT_EXTRACTION_FAILED_OR_SCANNED_PDF"
    if any(bool(row.get("contains_financial_keywords")) for row in page_text_rows):
        return "TABLE_EXTRACTION_OR_ROW_MAPPING_MISSED_FINANCIAL_PAGE"
    if table_count > 0:
        return "TABLES_FOUND_BUT_METRIC_RULES_TOO_WEAK"
    return "NO_TABLES_OR_FINANCIAL_SIGNALS_FOUND"


def _recommended_next_action(likely_failure_reason: str, likely_forecast_pages: Sequence[int], candidate_count: int) -> str:
    if candidate_count > 0:
        return "Open routing_preview.xlsx and client_preview.xlsx to inspect weak routes and wrong hits."
    if likely_failure_reason == "PDF_TEXT_EXTRACTION_FAILED_OR_SCANNED_PDF":
        return "Check whether the PDF is scanned and whether OCR is needed before table extraction."
    if likely_failure_reason == "TABLE_EXTRACTION_OR_ROW_MAPPING_MISSED_FINANCIAL_PAGE":
        pages = ", ".join(str(page) for page in likely_forecast_pages[:8]) or "unknown pages"
        return f"Inspect extracted_page_text.xlsx and extracted_tables.xlsx around pages {pages}."
    if likely_failure_reason == "TABLES_FOUND_BUT_METRIC_RULES_TOO_WEAK":
        return "Inspect extracted_tables.xlsx and strengthen metric keyword or row-mapping rules for this document."
    return "Inspect extracted_page_text.xlsx first, then review extracted_tables.xlsx."


def _document_run_summary_df(document_summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "section": "document_summary",
            "document": document_summary.get("pdf_filename", ""),
            "metric": "page_count",
            "value": document_summary.get("page_count", 0),
            "notes": "Total pages in the PDF.",
        },
        {
            "section": "document_summary",
            "document": document_summary.get("pdf_filename", ""),
            "metric": "detected_table_count",
            "value": document_summary.get("detected_table_count", 0),
            "notes": "Normalized table blocks extracted by pdfplumber.",
        },
        {
            "section": "document_summary",
            "document": document_summary.get("pdf_filename", ""),
            "metric": "candidate_count",
            "value": document_summary.get("candidate_count", 0),
            "notes": "Metric candidates generated from extracted tables.",
        },
        {
            "section": "document_summary",
            "document": document_summary.get("pdf_filename", ""),
            "metric": "likely_failure_reason",
            "value": document_summary.get("likely_failure_reason", ""),
            "notes": "Filled only when no candidates were produced.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _document_package(
    *,
    pdf_path: Path,
    extraction_fn: Callable[..., List[Dict[str, Any]]],
    page_text_fn: Callable[[Path], tuple[Dict[int, str], List[Dict[str, Any]], int | None]],
) -> Dict[str, Any]:
    page_texts, page_failures, page_count = page_text_fn(pdf_path)
    try:
        table_blocks = extraction_fn(str(pdf_path), pages="all", logger=None, config=None) or []
        extraction_error = ""
    except Exception as exc:
        table_blocks = []
        extraction_error = str(exc)

    page_text_rows = _page_text_records(page_texts)
    extracted_table_rows = _row_debug_records(table_blocks)

    candidates: List[Dict[str, Any]] = []
    for table_block in table_blocks:
        page_no = _safe_int(table_block.get("page"), 0)
        candidates.extend(
            _parse_table_block(
                document=pdf_path.name,
                table_block=table_block,
                page_text=page_texts.get(page_no, ""),
            )
        )

    frames = _build_candidate_frames(candidates)
    metric_candidate_rows = _metric_candidate_rows(candidates)
    routing_rows = _routing_preview_rows(candidates)
    likely_forecast_pages = _likely_forecast_pages(
        page_text_rows=page_text_rows,
        extracted_table_rows=extracted_table_rows,
        candidates=candidates,
    )

    reviewed_count = len(frames["reviewed"])
    needs_review_count = len(frames["needs_review"])
    rejected_count = len(frames["rejected"])
    candidate_count = len(candidates)
    likely_failure_reason = _likely_failure_reason(
        candidate_count=candidate_count,
        page_text_rows=page_text_rows,
        table_count=len(table_blocks),
    )

    if extraction_error and not likely_failure_reason:
        likely_failure_reason = "TABLE_EXTRACTION_FAILED"

    document_summary = {
        "pdf_filename": pdf_path.name,
        "pdf_stem": pdf_path.stem,
        "file_size_bytes": pdf_path.stat().st_size,
        "page_count": page_count if page_count is not None else "",
        "extracted_page_count": sum(1 for row in page_text_rows if _norm_text(row.get("full_text_or_long_excerpt"))),
        "detected_table_count": len(table_blocks),
        "candidate_count": candidate_count,
        "reviewed_count": reviewed_count,
        "needs_review_count": needs_review_count,
        "rejected_count": rejected_count,
        "likely_failure_reason": likely_failure_reason,
        "likely_forecast_pages": likely_forecast_pages,
        "page_failures": page_failures,
        "table_extraction_error": extraction_error,
        "recommended_next_action": _recommended_next_action(
            likely_failure_reason,
            likely_forecast_pages,
            candidate_count,
        ),
    }

    client_preview_sheets = {
        WORKBOOK_SHEETS["readme"]: _customer_readme_df(),
        WORKBOOK_SHEETS["reviewed"]: frames["reviewed"],
        WORKBOOK_SHEETS["needs_review"]: frames["needs_review"],
        WORKBOOK_SHEETS["rejected"]: frames["rejected"],
        WORKBOOK_SHEETS["trace"]: frames["trace"],
        WORKBOOK_SHEETS["summary"]: _document_run_summary_df(document_summary),
    }

    return {
        "document_summary": document_summary,
        "page_text_df": _clean_frame(pd.DataFrame(page_text_rows)),
        "extracted_tables_df": _clean_frame(pd.DataFrame(extracted_table_rows)),
        "metric_candidates_df": _clean_frame(pd.DataFrame(metric_candidate_rows)),
        "routing_preview_df": _clean_frame(pd.DataFrame(routing_rows)),
        "client_preview_sheets": client_preview_sheets,
    }


def build_real_test_per_pdf_debug_336b(
    *,
    input_pdf_dir: Path,
    output_dir: Path,
    extraction_fn: Callable[..., List[Dict[str, Any]]] | None = None,
    page_text_fn: Callable[[Path], tuple[Dict[int, str], List[Dict[str, Any]], int | None]] | None = None,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    extraction_callable = extraction_fn or extract_tables_from_pdf
    page_text_callable = page_text_fn or _extract_page_texts

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    pdf_paths = _find_pdf_files(input_pdf_dir)

    document_packages: List[Dict[str, Any]] = []
    batch_rows: List[Dict[str, Any]] = []
    for pdf_path in pdf_paths:
        package = _document_package(
            pdf_path=pdf_path,
            extraction_fn=extraction_callable,
            page_text_fn=page_text_callable,
        )
        document_summary = package["document_summary"]
        pdf_folder = output_dir / pdf_path.stem
        package["output_folder"] = str(pdf_folder)
        document_packages.append(package)
        batch_rows.append(
            {
                "document": pdf_path.name,
                "page_count": document_summary.get("page_count", ""),
                "table_count": document_summary.get("detected_table_count", 0),
                "candidate_count": document_summary.get("candidate_count", 0),
                "reviewed_count": document_summary.get("reviewed_count", 0),
                "needs_review_count": document_summary.get("needs_review_count", 0),
                "rejected_count": document_summary.get("rejected_count", 0),
                "likely_failure_reason": document_summary.get("likely_failure_reason", ""),
                "output_folder": str(pdf_folder),
                "recommended_next_action": document_summary.get("recommended_next_action", ""),
                "likely_forecast_pages": ", ".join(str(page) for page in document_summary.get("likely_forecast_pages", [])),
            }
        )

    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])

    qa_checks = [
        {
            "check_name": "input_dir_exists",
            "status": "PASS" if input_pdf_dir.exists() else "FAIL",
            "detail": str(input_pdf_dir),
        },
        {
            "check_name": "pdf_found_count_gt_zero",
            "status": "PASS" if len(pdf_paths) > 0 else "FAIL",
            "detail": str(len(pdf_paths)),
        },
        {
            "check_name": "official_assets_unchanged",
            "status": "PASS" if official_assets_before == official_assets_after else "FAIL",
            "detail": json.dumps(official_assets_after, ensure_ascii=False),
        },
        {
            "check_name": "protected_dirty_status_preserved",
            "status": "PASS" if protected_status_before == protected_status_after else "FAIL",
            "detail": json.dumps(protected_status_after, ensure_ascii=False),
        },
        {
            "check_name": "protected_dirty_paths_not_staged",
            "status": "PASS" if not protected_cached_after else "FAIL",
            "detail": json.dumps(protected_cached_after, ensure_ascii=False),
        },
    ]
    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")

    if not pdf_paths:
        decision = BLOCKED_DECISION
    elif qa_fail_count == 0:
        decision = READY_DECISION
    else:
        decision = PARTIAL_DECISION

    batch_summary = {
        "input_pdf_dir": str(input_pdf_dir),
        "output_dir": str(output_dir),
        "pdf_found_count": len(pdf_paths),
        "total_candidate_count": sum(row["candidate_count"] for row in batch_rows),
        "total_reviewed_count": sum(row["reviewed_count"] for row in batch_rows),
        "total_needs_review_count": sum(row["needs_review_count"] for row in batch_rows),
        "total_rejected_count": sum(row["rejected_count"] for row in batch_rows),
        "official_assets_unchanged": official_assets_before == official_assets_after,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "documents": batch_rows,
        "qa_checks": qa_checks,
    }

    return {
        "batch_summary": batch_summary,
        "batch_summary_df": _clean_frame(pd.DataFrame(batch_rows)),
        "document_packages": document_packages,
    }
