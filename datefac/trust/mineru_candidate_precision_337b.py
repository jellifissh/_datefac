from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    capture_official_asset_hashes,
)


READY_DECISION = "MINERU_CANDIDATE_PRECISION_337B_READY"
PARTIAL_DECISION = "MINERU_CANDIDATE_PRECISION_337B_PARTIAL"
BLOCKED_DECISION = "MINERU_CANDIDATE_PRECISION_337B_BLOCKED"

DEFAULT_MINERU_REAL_TEST_DIR = Path(r"D:\_datefac\output\mineru_real_test_337a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\mineru_candidate_precision_337b")
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

CUSTOMER_WORKBOOK_SHEETS = {
    "readme": "00_README",
    "reviewed": "01_REVIEWED_CORE_METRICS",
    "needs_review": "02_NEEDS_REVIEW",
    "rejected": "03_REJECTED_OR_EXCLUDED",
    "trace": "04_SOURCE_TRACE",
    "document_summary": "05_DOCUMENT_SUMMARY",
    "table_summary": "06_TABLE_CLASSIFICATION_SUMMARY",
}

TABLE_ROLE_ORDER = [
    "CORE_FINANCIAL_SUMMARY",
    "PROFIT_FORECAST_VALUATION",
    "FINANCIAL_STATEMENT_DETAIL",
    "INDUSTRY_DATA_TABLE",
    "RATING_STANDARD_TABLE",
    "LEGAL_DISCLOSURE_TABLE",
    "COMPANY_PROFILE_TABLE",
    "OTHER_TABLE",
]

ALLOWED_REVIEWED_METRICS = {
    "revenue",
    "net_profit",
    "EPS",
    "PE",
    "PB",
    "ROE",
    "gross_margin",
    "net_margin",
    "revenue_yoy",
    "net_profit_yoy",
}

TABLE_ROLE_ALLOWED_FOR_REVIEWED = {
    "CORE_FINANCIAL_SUMMARY",
    "PROFIT_FORECAST_VALUATION",
    "FINANCIAL_STATEMENT_DETAIL",
}

REJECT_PAGE_KEYWORDS = [
    "分析师承诺",
    "评级说明",
    "免责声明",
    "法律声明",
    "风险提示",
    "目录",
]

LEGAL_DISCLOSURE_KEYWORDS = [
    "免责声明",
    "法律声明",
    "分析师承诺",
    "版权",
    "转载",
    "风险评级",
]

RATING_STANDARD_KEYWORDS = [
    "评级说明",
    "评级体系",
    "投资评级",
    "公司评级",
    "行业评级",
]

COMPANY_PROFILE_KEYWORDS = [
    "公司近一年市场表现",
    "基础数据",
    "收盘价",
    "总市值",
    "流通A股",
]

INDUSTRY_DATA_KEYWORDS = [
    "可比公司",
    "行业",
    "同业",
    "估值比较",
    "代码 | 名称 | 收盘价",
]

FORECAST_KEYWORDS = [
    "财务数据与估值",
    "盈利预测",
    "估值",
    "EPS",
    "P/E",
    "P/B",
    "2026E",
    "2027E",
    "2028E",
]

CORE_SUMMARY_KEYWORDS = [
    "财务摘要",
    "主要财务指标",
    "主要财务比率",
]

STATEMENT_KEYWORDS = [
    "利润表",
    "资产负债表",
    "现金流量表",
]

YEAR_VALUE_RE = re.compile(r"^(?:19|20)\d{2}(?:[AE])?$")
NUMERIC_LIKE_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _truncate(value: Any, limit: int = 240) -> str:
    text = _norm_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _contains_any(text: str, patterns: Sequence[str]) -> bool:
    lowered = _norm_text(text).casefold()
    return any(pattern.casefold() in lowered for pattern in patterns)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _git_status_porcelain_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_cached_names_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


def _customer_readme_df() -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {"topic": "Workbook purpose", "message": "This workbook is a precision-calibrated local preview derived from the 337A MinerU-first run."},
                {"topic": "Calibration", "message": "337B removes duplicate tables, suppresses disclosure and rating-system noise, and tightens reviewed routing."},
                {"topic": "Reviewed rows", "message": "Reviewed rows remain preview-only and still require human judgment before any external use."},
                {"topic": "Boundaries", "message": "This output is local-only, not client-ready, not production-ready, and not investment advice."},
            ]
        )
    )


def _normalized_table_signature(preview: str) -> str:
    text = _norm_text(preview).lower()
    text = re.sub(r"(19|20)\d{2}[ae]?", "<YEAR>", text)
    text = re.sub(r"-?\d+(?:\.\d+)?", "<NUM>", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _table_quality_score(row: Mapping[str, Any]) -> Tuple[int, int, int]:
    candidate_score = _safe_int(row.get("candidate_score"), 0)
    parsed_frame_count = _safe_int(row.get("parsed_frame_count"), 0)
    row_count = _safe_int(row.get("row_count"), 0)
    return (candidate_score, parsed_frame_count, row_count)


def _reclassify_table_role(row: Mapping[str, Any]) -> str:
    context = " ".join(
        filter(
            None,
            [
                _norm_text(row.get("table_role_guess")),
                _norm_text(row.get("caption")),
                _norm_text(row.get("footnote")),
                _norm_text(row.get("nearby_text")),
                _norm_text(row.get("matched_keywords")),
                _norm_text(row.get("table_preview")),
            ],
        )
    )
    if _contains_any(context, LEGAL_DISCLOSURE_KEYWORDS):
        return "LEGAL_DISCLOSURE_TABLE"
    if _contains_any(context, RATING_STANDARD_KEYWORDS):
        return "RATING_STANDARD_TABLE"
    if _contains_any(context, INDUSTRY_DATA_KEYWORDS):
        return "INDUSTRY_DATA_TABLE"
    if _contains_any(context, COMPANY_PROFILE_KEYWORDS):
        return "COMPANY_PROFILE_TABLE"
    if _contains_any(context, FORECAST_KEYWORDS):
        return "PROFIT_FORECAST_VALUATION"
    if _contains_any(context, CORE_SUMMARY_KEYWORDS):
        return "CORE_FINANCIAL_SUMMARY"
    if _contains_any(context, STATEMENT_KEYWORDS):
        return "FINANCIAL_STATEMENT_DETAIL"
    if "CORE_METRIC_TABLE" in context or "FINANCIAL_FORECAST_VALUATION" in context:
        return "CORE_FINANCIAL_SUMMARY"
    return "OTHER_TABLE"


def _build_table_map(table_df: pd.DataFrame) -> Tuple[Dict[Tuple[str, int], Dict[str, Any]], List[Dict[str, Any]], pd.DataFrame]:
    work = table_df.copy()
    if work.empty:
        return {}, [], work
    work["table_role_337b"] = work.apply(_reclassify_table_role, axis=1)
    work["normalized_table_signature"] = work["table_preview"].map(_normalized_table_signature)
    work["page_no_int"] = work["page_no"].map(lambda value: _safe_int(value, -1))
    work["duplicate_group_key"] = work.apply(
        lambda row: f"{_norm_text(row['document'])}|{row['page_no_int']}|{row['table_role_337b']}|{_norm_text(row['normalized_table_signature'])[:300]}",
        axis=1,
    )
    duplicate_removed_rows: List[Dict[str, Any]] = []
    table_map: Dict[Tuple[str, int], Dict[str, Any]] = {}
    kept_indices = []
    for _, group in work.groupby("duplicate_group_key", dropna=False):
        sorted_group = sorted(group.to_dict(orient="records"), key=_table_quality_score, reverse=True)
        kept = sorted_group[0]
        kept_indices.append(kept["table_index"])
        table_map[(kept["document"], _safe_int(kept["table_index"]))] = kept
        for removed in sorted_group[1:]:
            removed_row = dict(removed)
            removed_row["kept_table_index"] = kept["table_index"]
            removed_row["duplicate_reason"] = "same_page_role_and_normalized_preview"
            duplicate_removed_rows.append(removed_row)
    deduped_df = work[work["table_index"].isin(kept_indices)].copy()
    return table_map, duplicate_removed_rows, _clean_frame(deduped_df)


def _repair_yoy_metric(metric: str, evidence: str, table_preview: str, row_index: int) -> Tuple[str, str]:
    if metric != "YoY":
        return metric, ""
    context = " ".join([_norm_text(evidence), _norm_text(table_preview)])
    if "营业收入" in context:
        return "revenue_yoy", "inferred_from_nearby_revenue_row"
    if "归母净利润" in context or "净利润" in context:
        return "net_profit_yoy", "inferred_from_nearby_net_profit_row"
    if row_index > 0 and "收入" in context:
        return "revenue_yoy", "heuristic_revenue_yoy"
    return "YoY", ""


def _looks_like_year_value(value: str) -> bool:
    return bool(YEAR_VALUE_RE.fullmatch(_norm_text(value)))


def _row_from_bad_page(evidence: str) -> bool:
    return _contains_any(evidence, REJECT_PAGE_KEYWORDS)


def _strict_route_candidate(candidate: Mapping[str, Any], table_info: Mapping[str, Any] | None) -> Tuple[str, str, str]:
    metric = _norm_text(candidate.get("metric"))
    status_before = _norm_text(candidate.get("status"))
    evidence = _norm_text(candidate.get("source_evidence_excerpt"))
    year = _norm_text(candidate.get("year"))
    value = _norm_text(candidate.get("value"))
    source_page = candidate.get("source_page", "")
    repaired_metric, yoy_repair_reason = _repair_yoy_metric(
        metric,
        evidence,
        _norm_text((table_info or {}).get("table_preview")),
        _safe_int(candidate.get("row_index"), 0),
    )
    table_role = _norm_text((table_info or {}).get("table_role_337b"))
    if table_role in {"RATING_STANDARD_TABLE", "LEGAL_DISCLOSURE_TABLE"}:
        return "rejected_or_excluded", f"excluded_table_role::{table_role}", repaired_metric
    if table_role in {"INDUSTRY_DATA_TABLE", "COMPANY_PROFILE_TABLE", "OTHER_TABLE"}:
        return "needs_review", f"non_core_table_role::{table_role}", repaired_metric
    if not source_page:
        return "needs_review", "missing_source_page", repaired_metric
    if _row_from_bad_page(evidence):
        return "rejected_or_excluded", "bad_page_context", repaired_metric
    if repaired_metric not in ALLOWED_REVIEWED_METRICS:
        return "needs_review", "metric_not_allowed_for_reviewed", repaired_metric
    if repaired_metric == "YoY":
        return "needs_review", "generic_yoy_without_parent_metric", repaired_metric
    if not year:
        return "needs_review", "missing_year", repaired_metric
    if _looks_like_year_value(value):
        return "needs_review", "value_looks_like_year", repaired_metric
    if table_role not in TABLE_ROLE_ALLOWED_FOR_REVIEWED:
        return "needs_review", f"table_role_not_allowed::{table_role}", repaired_metric
    if repaired_metric in {"revenue_yoy", "net_profit_yoy"} and not yoy_repair_reason:
        return "needs_review", "yoy_parent_not_inferred", repaired_metric
    if repaired_metric in {"rating", "broker", "stock_name", "stock_code"}:
        return "needs_review", "metadata_not_reviewed", repaired_metric
    if status_before == "rejected_or_excluded":
        return "rejected_or_excluded", "preserve_prior_rejection", repaired_metric
    return "reviewed_preview", ("strict_review_ok" if not yoy_repair_reason else yoy_repair_reason), repaired_metric


def _build_before_counts(summary_337a: Mapping[str, Any], source_trace_df: pd.DataFrame) -> pd.DataFrame:
    metric_counts = source_trace_df["metric"].value_counts(dropna=False).to_dict() if not source_trace_df.empty else {}
    rows = [
        {"section": "summary", "name": "reviewed_before_count", "value": summary_337a.get("reviewed_count", 0)},
        {"section": "summary", "name": "needs_review_before_count", "value": summary_337a.get("needs_review_count", 0)},
        {"section": "summary", "name": "rejected_before_count", "value": summary_337a.get("rejected_or_excluded_count", 0)},
    ]
    for metric, count in metric_counts.items():
        rows.append({"section": "metric_count", "name": metric, "value": count})
    return _clean_frame(pd.DataFrame(rows))


def _build_document_summary_after(route_change_df: pd.DataFrame, table_classification_df: pd.DataFrame) -> pd.DataFrame:
    if route_change_df.empty:
        return pd.DataFrame()
    grouped = route_change_df.groupby("document", dropna=False)
    rows = []
    for document, group in grouped:
        rows.append(
            {
                "document": document,
                "reviewed_after_count": int((group["status_after"] == "reviewed_preview").sum()),
                "needs_review_after_count": int((group["status_after"] == "needs_review").sum()),
                "rejected_after_count": int((group["status_after"] == "rejected_or_excluded").sum()),
                "duplicate_removed_table_count": int(group["is_duplicate_table_removed"].sum()),
                "represented_table_role_count": int(
                    table_classification_df[table_classification_df["document"] == document]["table_role_337b"].nunique()
                ),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def build_mineru_candidate_precision_337b(
    *,
    mineru_real_test_dir: Path,
    output_dir: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)

    summary_337a_path = mineru_real_test_dir / "00_batch_summary.json"
    workbook_337a_path = mineru_real_test_dir / "real_test_mineru_client_export_337a.xlsx"
    debug_root = mineru_real_test_dir / "datefac_debug"
    blocked_reasons: List[str] = []

    if not summary_337a_path.exists():
        blocked_reasons.append(f"Missing 337A summary: {summary_337a_path}")
    if not workbook_337a_path.exists():
        blocked_reasons.append(f"Missing 337A workbook: {workbook_337a_path}")
    if not debug_root.exists():
        blocked_reasons.append(f"Missing 337A debug root: {debug_root}")

    if blocked_reasons:
        summary = {
            "generated_at_utc": _utc_now(),
            "client_ready": False,
            "production_ready": False,
            "qa_fail_count": len(blocked_reasons),
            "decision": BLOCKED_DECISION,
        }
        return {
            "summary": summary,
            "manifest": {},
            "qa_json": {"decision": BLOCKED_DECISION, "qa_fail_count": len(blocked_reasons), "checks": [], "blocked_reasons": blocked_reasons},
            "before_after_sheets": {},
            "customer_workbook_sheets": {},
        }

    summary_337a = json.loads(summary_337a_path.read_text(encoding="utf-8"))
    source_trace_df = _read_excel(workbook_337a_path, "04_SOURCE_TRACE")
    document_summary_337a_df = _read_excel(workbook_337a_path, "05_DOCUMENT_SUMMARY")

    table_frames = []
    metric_frames = []
    document_rows = []
    for document_dir in sorted(path for path in debug_root.iterdir() if path.is_dir()):
        document_summary_path = document_dir / "document_summary.json"
        financial_tables_path = document_dir / "financial_table_candidates.xlsx"
        metric_candidates_path = document_dir / "metric_candidates.xlsx"
        if document_summary_path.exists():
            document_rows.append(json.loads(document_summary_path.read_text(encoding="utf-8")))
        if financial_tables_path.exists():
            table_frames.append(_read_excel(financial_tables_path, "financial_table_candidates"))
        if metric_candidates_path.exists():
            metric_frames.append(_read_excel(metric_candidates_path, "metric_candidates"))

    all_table_df = _clean_frame(pd.concat(table_frames, ignore_index=True)) if table_frames else pd.DataFrame()
    all_metric_df = _clean_frame(pd.concat(metric_frames, ignore_index=True)) if metric_frames else pd.DataFrame()

    table_map, duplicate_removed_rows, deduped_table_df = _build_table_map(all_table_df)
    duplicate_removed_keys = {(row["document"], _safe_int(row["table_index"])) for row in duplicate_removed_rows}

    route_change_rows: List[Dict[str, Any]] = []
    for row in all_metric_df.to_dict(orient="records"):
        key = (_norm_text(row.get("document")), _safe_int(row.get("table_index")))
        table_info = table_map.get(key)
        if key in duplicate_removed_keys:
            status_after = "needs_review"
            route_reason_after = "duplicate_table_removed"
            repaired_metric = _norm_text(row.get("metric"))
        else:
            status_after, route_reason_after, repaired_metric = _strict_route_candidate(row, table_info)
        metric_display_zh = _norm_text(row.get("metric_display_zh"))
        if repaired_metric == "revenue_yoy":
            metric_display_zh = "营业收入同比"
        elif repaired_metric == "net_profit_yoy":
            metric_display_zh = "归母净利润同比"
        route_change_rows.append(
            {
                "candidate_id": _norm_text(row.get("candidate_id")),
                "document": _norm_text(row.get("document")),
                "metric_before": _norm_text(row.get("metric")),
                "metric_after": repaired_metric,
                "metric_display_zh_after": metric_display_zh,
                "year": _norm_text(row.get("year")),
                "value": _norm_text(row.get("value")),
                "unit": _norm_text(row.get("unit")),
                "source_page": row.get("source_page", ""),
                "status_before": _norm_text(row.get("status")),
                "status_after": status_after,
                "route_reason_before": _norm_text(row.get("route_reason")),
                "route_reason_after": route_reason_after,
                "source_evidence_excerpt": _norm_text(row.get("source_evidence_excerpt")),
                "table_index": row.get("table_index", ""),
                "row_index": row.get("row_index", ""),
                "table_role_337b": _norm_text((table_info or {}).get("table_role_337b")),
                "is_duplicate_table_removed": key in duplicate_removed_keys,
                "table_preview": _norm_text((table_info or {}).get("table_preview")),
            }
        )

    route_change_df = _clean_frame(pd.DataFrame(route_change_rows))
    reviewed_after_df = _clean_frame(
        route_change_df[route_change_df["status_after"] == "reviewed_preview"][
            ["document", "metric_after", "metric_display_zh_after", "year", "value", "unit", "source_page", "status_after", "source_evidence_excerpt", "route_reason_after"]
        ].rename(
            columns={
                "metric_after": "metric",
                "metric_display_zh_after": "metric_display_zh",
                "status_after": "status",
                "route_reason_after": "notes",
            }
        )
    )
    needs_review_after_df = _clean_frame(
        route_change_df[route_change_df["status_after"] == "needs_review"][
            ["document", "metric_after", "metric_display_zh_after", "year", "value", "unit", "source_page", "status_after", "source_evidence_excerpt", "route_reason_after"]
        ].rename(
            columns={
                "metric_after": "metric",
                "metric_display_zh_after": "metric_display_zh",
                "status_after": "status",
                "route_reason_after": "notes",
            }
        )
    )
    rejected_after_df = _clean_frame(
        route_change_df[route_change_df["status_after"] == "rejected_or_excluded"][
            ["document", "metric_after", "metric_display_zh_after", "year", "value", "unit", "source_page", "status_after", "source_evidence_excerpt", "route_reason_after"]
        ].rename(
            columns={
                "metric_after": "metric",
                "metric_display_zh_after": "metric_display_zh",
                "status_after": "status",
                "route_reason_after": "notes",
            }
        )
    )

    for frame in [reviewed_after_df, needs_review_after_df, rejected_after_df]:
        if not frame.empty:
            frame.insert(0, "row_no", range(1, len(frame) + 1))

    table_classification_df = _clean_frame(deduped_table_df)
    duplicate_removed_df = _clean_frame(pd.DataFrame(duplicate_removed_rows))
    document_summary_after_df = _build_document_summary_after(route_change_df, table_classification_df)
    before_counts_df = _build_before_counts(summary_337a, source_trace_df)
    after_counts_df = _clean_frame(
        pd.DataFrame(
            [
                {"name": "reviewed_after_count", "value": len(reviewed_after_df)},
                {"name": "needs_review_after_count", "value": len(needs_review_after_df)},
                {"name": "rejected_after_count", "value": len(rejected_after_df)},
                {"name": "duplicate_table_removed_count", "value": len(duplicate_removed_df)},
                {"name": "table_role_classification_count", "value": len(table_classification_df)},
            ]
        )
    )
    summary_sheet_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "reviewed_before": summary_337a.get("reviewed_count", 0),
                    "reviewed_after": len(reviewed_after_df),
                    "needs_review_before": summary_337a.get("needs_review_count", 0),
                    "needs_review_after": len(needs_review_after_df),
                    "rejected_before": summary_337a.get("rejected_or_excluded_count", 0),
                    "rejected_after": len(rejected_after_df),
                    "duplicate_table_removed_count": len(duplicate_removed_df),
                }
            ]
        )
    )

    excluded_rating_standard_table_count = int((table_classification_df["table_role_337b"] == "RATING_STANDARD_TABLE").sum()) if not table_classification_df.empty else 0
    excluded_legal_disclosure_table_count = int((table_classification_df["table_role_337b"] == "LEGAL_DISCLOSURE_TABLE").sum()) if not table_classification_df.empty else 0
    excluded_company_profile_table_count = int((table_classification_df["table_role_337b"] == "COMPANY_PROFILE_TABLE").sum()) if not table_classification_df.empty else 0

    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])

    reviewed_metrics = set(reviewed_after_df["metric"]) if not reviewed_after_df.empty else set()
    no_bad_value_in_reviewed = True
    if not reviewed_after_df.empty:
        no_bad_value_in_reviewed = not reviewed_after_df["value"].map(lambda value: bool(YEAR_VALUE_RE.fullmatch(_norm_text(value)))).any()
    no_generic_yoy_reviewed = "YoY" not in reviewed_metrics
    no_rating_reviewed = True
    no_legal_reviewed = True
    if not route_change_df.empty:
        reviewed_rows = route_change_df[route_change_df["status_after"] == "reviewed_preview"]
        no_rating_reviewed = not (reviewed_rows["table_role_337b"] == "RATING_STANDARD_TABLE").any()
        no_legal_reviewed = not (reviewed_rows["table_role_337b"] == "LEGAL_DISCLOSURE_TABLE").any()

    qa_checks = [
        {"check_name": "input_337a_summary_exists", "status": "PASS" if summary_337a_path.exists() else "FAIL", "detail": str(summary_337a_path)},
        {"check_name": "input_337a_workbook_exists", "status": "PASS" if workbook_337a_path.exists() else "FAIL", "detail": str(workbook_337a_path)},
        {"check_name": "three_pdfs_represented", "status": "PASS" if len(document_rows) == 3 else "FAIL", "detail": str(len(document_rows))},
        {"check_name": "deduplication_summary_generated", "status": "PASS" if duplicate_removed_df is not None else "FAIL", "detail": str(len(duplicate_removed_df))},
        {"check_name": "table_role_classification_generated", "status": "PASS" if not table_classification_df.empty else "FAIL", "detail": str(len(table_classification_df))},
        {"check_name": "reviewed_after_not_higher_than_before", "status": "PASS" if len(reviewed_after_df) <= summary_337a.get("reviewed_count", 0) else "FAIL", "detail": f"{len(reviewed_after_df)} <= {summary_337a.get('reviewed_count', 0)}"},
        {"check_name": "no_rating_standard_table_rows_in_reviewed", "status": "PASS" if no_rating_reviewed else "FAIL", "detail": str(no_rating_reviewed)},
        {"check_name": "no_legal_disclosure_table_rows_in_reviewed", "status": "PASS" if no_legal_reviewed else "FAIL", "detail": str(no_legal_reviewed)},
        {"check_name": "no_year_like_numeric_value_in_reviewed", "status": "PASS" if no_bad_value_in_reviewed else "FAIL", "detail": str(no_bad_value_in_reviewed)},
        {"check_name": "generic_yoy_not_reviewed", "status": "PASS" if no_generic_yoy_reviewed else "FAIL", "detail": str(no_generic_yoy_reviewed)},
        {"check_name": "official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_status_preserved", "status": "PASS" if protected_status_before == protected_status_after else "FAIL", "detail": json.dumps(protected_status_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_paths_not_staged", "status": "PASS" if not protected_cached_after else "FAIL", "detail": json.dumps(protected_cached_after, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")

    if qa_fail_count == 0:
        decision = READY_DECISION
    else:
        decision = PARTIAL_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "client_ready": False,
        "production_ready": False,
        "mineru_real_test_dir": str(mineru_real_test_dir),
        "output_dir": str(output_dir),
        "reviewed_before_count": summary_337a.get("reviewed_count", 0),
        "reviewed_after_count": len(reviewed_after_df),
        "needs_review_before_count": summary_337a.get("needs_review_count", 0),
        "needs_review_after_count": len(needs_review_after_df),
        "rejected_before_count": summary_337a.get("rejected_or_excluded_count", 0),
        "rejected_after_count": len(rejected_after_df),
        "duplicate_table_removed_count": len(duplicate_removed_df),
        "excluded_rating_standard_table_count": excluded_rating_standard_table_count,
        "excluded_legal_disclosure_table_count": excluded_legal_disclosure_table_count,
        "excluded_company_profile_table_count": excluded_company_profile_table_count,
        "no_official_asset_modification_during_337b": official_assets_before == official_assets_after,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "337B_mineru_candidate_precision_calibration",
        "mineru_real_test_dir": str(mineru_real_test_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "mineru_candidate_precision_337b_summary.json"),
            "manifest_json": str(output_dir / "mineru_candidate_precision_337b_manifest.json"),
            "qa_json": str(output_dir / "mineru_candidate_precision_337b_qa.json"),
            "report_md": str(output_dir / "mineru_candidate_precision_337b_report.md"),
            "before_after_xlsx": str(output_dir / "mineru_candidate_precision_337b_before_after.xlsx"),
            "customer_workbook_xlsx": str(output_dir / "real_test_mineru_client_export_337b.xlsx"),
        },
    }

    qa_json = {
        "decision": decision,
        "qa_fail_count": qa_fail_count,
        "checks": qa_checks,
        "blocked_reasons": blocked_reasons,
        "official_assets_before": official_assets_before,
        "official_assets_after": official_assets_after,
    }

    before_after_sheets = {
        "00_SUMMARY": summary_sheet_df,
        "01_BEFORE_COUNTS": before_counts_df,
        "02_AFTER_COUNTS": after_counts_df,
        "03_REVIEWED_AFTER": reviewed_after_df,
        "04_NEEDS_REVIEW_AFTER": needs_review_after_df,
        "05_REJECTED_AFTER": rejected_after_df,
        "06_DUPLICATE_TABLES_REMOVED": duplicate_removed_df,
        "07_TABLE_ROLE_CLASSIFICATION": table_classification_df,
        "08_ROUTE_CHANGE_TRACE": route_change_df,
    }

    customer_workbook_sheets = {
        CUSTOMER_WORKBOOK_SHEETS["readme"]: _customer_readme_df(),
        CUSTOMER_WORKBOOK_SHEETS["reviewed"]: reviewed_after_df,
        CUSTOMER_WORKBOOK_SHEETS["needs_review"]: needs_review_after_df,
        CUSTOMER_WORKBOOK_SHEETS["rejected"]: rejected_after_df,
        CUSTOMER_WORKBOOK_SHEETS["trace"]: route_change_df,
        CUSTOMER_WORKBOOK_SHEETS["document_summary"]: document_summary_after_df,
        CUSTOMER_WORKBOOK_SHEETS["table_summary"]: table_classification_df[
            ["document", "page_no", "table_index", "table_role_337b", "candidate_score", "row_count", "col_count", "table_preview"]
        ] if not table_classification_df.empty else pd.DataFrame(),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "before_after_sheets": before_after_sheets,
        "customer_workbook_sheets": customer_workbook_sheets,
        "route_change_df": route_change_df,
        "document_summary_after_df": document_summary_after_df,
    }
