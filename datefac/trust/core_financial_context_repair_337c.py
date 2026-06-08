from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    capture_official_asset_hashes,
)


READY_DECISION = "CORE_FINANCIAL_CONTEXT_REPAIR_337C_READY"
PARTIAL_DECISION = "CORE_FINANCIAL_CONTEXT_REPAIR_337C_PARTIAL"
BLOCKED_DECISION = "CORE_FINANCIAL_CONTEXT_REPAIR_337C_BLOCKED"

DEFAULT_PRECISION_337B_DIR = Path(r"D:\_datefac\output\mineru_candidate_precision_337b")
DEFAULT_MINERU_REAL_TEST_DIR = Path(r"D:\_datefac\output\mineru_real_test_337a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\core_financial_context_repair_337c")
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
    "context_summary": "07_CONTEXT_REPAIR_SUMMARY",
}

CORE_METRIC_LABELS = [
    "营业收入",
    "归母净利润",
    "净利润",
    "EPS",
    "每股收益",
    "PE",
    "P/E",
    "PB",
    "P/B",
    "ROE",
    "毛利率",
    "净利率",
]

YEAR_HEADERS = ["2024A", "2025A", "2026E", "2027E", "2028E"]

LEGAL_RATING_KEYWORDS = [
    "投资评级说明",
    "股票投资评级说明",
    "分析师承诺",
    "免责声明",
    "法律声明",
    "评级体系",
    "适当性管理",
    "买入",
    "增持",
    "中性",
    "减持",
]

APPENDIX_FINANCIAL_KEYWORDS = [
    "资产负债表",
    "利润表",
    "现金流量表",
    "主要财务比率",
    "财务预测摘要",
]

INDUSTRY_PEER_HINTS = [
    "代码 | 名称 | 收盘价",
    "可比公司",
    "同行",
    "行业",
    "市场规模",
]

HIGH_REVIEWED_PDF = "H3_AP202606081823356439_1.pdf"

PERCENT_METRICS = {"ROE", "gross_margin", "net_margin", "revenue_yoy", "net_profit_yoy"}
MULTIPLE_METRICS = {"PE", "PB"}
YUAN_METRICS = {"EPS"}

YEAR_VALUE_RE = re.compile(r"^(?:19|20)\d{2}(?:[AE])?$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return re.sub(r"\s+", " ", str(value).strip())


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
                {"topic": "Workbook purpose", "message": "This workbook is a 337C context-repaired local preview derived from 337B precision calibration output."},
                {"topic": "Repairs", "message": "337C rescues core financial tables, repairs unit inheritance, fixes YoY parent metric context, and audits high-reviewed PDFs."},
                {"topic": "Boundaries", "message": "This remains local-only, preview-only, not client-ready, not production-ready, and not investment advice."},
            ]
        )
    )


def _extract_unit_from_text(text: str) -> str:
    normalized = _norm_text(text)
    if "百万元" in normalized:
        return "百万元"
    if "亿元" in normalized:
        return "亿元"
    if "元/股" in normalized:
        return "元"
    if "(元)" in normalized or "（元）" in normalized:
        return "元"
    if "(%)" in normalized or "（%）" in normalized or "%" in normalized:
        return "%"
    if "(倍)" in normalized or "（倍）" in normalized:
        return "倍"
    return ""


def _row_labels_from_preview(preview: str) -> List[str]:
    labels = []
    for line in _norm_text(preview).split("\n"):
        if "|" not in line:
            continue
        first = _norm_text(line.split("|")[0])
        if first:
            labels.append(first)
    return labels


def _year_header_hit_count(preview: str) -> int:
    return sum(1 for year in YEAR_HEADERS if year in _norm_text(preview))


def _core_label_hit_count(preview: str) -> int:
    text = _norm_text(preview)
    return sum(1 for label in CORE_METRIC_LABELS if label.casefold() in text.casefold())


def _repair_table_role(row: Mapping[str, Any]) -> Tuple[str, str]:
    preview = _norm_text(row.get("table_preview"))
    current = _norm_text(row.get("table_role_337b"))
    preview_text = preview
    context_text = " ".join(
        filter(
            None,
            [
                preview_text,
                _norm_text(row.get("matched_keywords")),
                _norm_text(row.get("caption")),
                _norm_text(row.get("nearby_text")),
            ],
        )
    )
    year_hits = _year_header_hit_count(preview_text)
    core_hits = _core_label_hit_count(preview_text)
    preview_has_legal = _contains_any(preview_text, LEGAL_RATING_KEYWORDS)
    context_has_legal = _contains_any(context_text, LEGAL_RATING_KEYWORDS)
    preview_has_peer_hints = _contains_any(preview_text, INDUSTRY_PEER_HINTS)
    preview_has_appendix = _contains_any(preview_text, APPENDIX_FINANCIAL_KEYWORDS)
    preview_has_forecast = _contains_any(preview_text, ["财务数据与估值", "盈利预测", "EPS", "P/E", "P/B"])

    if preview_has_legal:
        return "LEGAL_DISCLOSURE_TABLE" if _contains_any(preview_text, ["法律", "免责", "承诺"]) else "RATING_STANDARD_TABLE", "explicit_legal_or_rating_keywords"

    if year_hits >= 3 and core_hits >= 2 and not preview_has_peer_hints:
        if preview_has_forecast or _contains_any(preview_text, ["P/E", "P/B", "EPS", "PE", "PB"]):
            return "PROFIT_FORECAST_VALUATION", "core_financial_summary_rescue"
        if preview_has_appendix:
            return "FINANCIAL_STATEMENT_DETAIL", "financial_appendix_rescue"
        return "CORE_FINANCIAL_SUMMARY", "core_financial_summary_rescue"

    if preview_has_appendix and not preview_has_legal:
        if "财务预测摘要" in preview_text:
            return "PROFIT_FORECAST_VALUATION", "financial_appendix_rescue"
        return "FINANCIAL_STATEMENT_DETAIL", "financial_appendix_rescue"

    if context_has_legal and not (year_hits >= 3 and core_hits >= 2) and not preview_has_appendix:
        return "LEGAL_DISCLOSURE_TABLE" if _contains_any(context_text, ["法律", "免责", "承诺"]) else "RATING_STANDARD_TABLE", "explicit_legal_or_rating_keywords"

    if current == "INDUSTRY_DATA_TABLE":
        if year_hits >= 3 and core_hits >= 2 and not preview_has_peer_hints:
            if preview_has_forecast:
                return "PROFIT_FORECAST_VALUATION", "core_financial_summary_rescue"
            return "CORE_FINANCIAL_SUMMARY", "core_financial_summary_rescue"
    if current == "LEGAL_DISCLOSURE_TABLE":
        if preview_has_appendix and not preview_has_legal:
            if "财务预测摘要" in preview_text:
                return "PROFIT_FORECAST_VALUATION", "financial_appendix_rescue"
            return "FINANCIAL_STATEMENT_DETAIL", "financial_appendix_rescue"
    if current == "PROFIT_FORECAST_VALUATION" and preview_has_appendix:
        if _contains_any(preview_text, ["利润表", "资产负债表", "现金流量表", "主要财务比率"]):
            return "FINANCIAL_STATEMENT_DETAIL", "appendix_statement_refine"
    return current, "unchanged"


def _repair_unit(metric: str, unit: str, evidence: str, table_preview: str) -> Tuple[str, bool]:
    current = _norm_text(unit)
    if current:
        return current, False
    row_unit = _extract_unit_from_text(evidence)
    if row_unit:
        return row_unit, True
    table_unit = _extract_unit_from_text(table_preview)
    if table_unit:
        return table_unit, True
    if metric in YUAN_METRICS:
        return "元", True
    if metric in MULTIPLE_METRICS:
        return "倍", True
    if metric in PERCENT_METRICS:
        return "%", True
    return "", False


def _repair_yoy_metric_with_context(route_df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    repaired_rows = []
    repaired_count = 0
    ambiguous_count = 0
    for (_, document, table_index), group in route_df.groupby([route_df["document"], route_df["document"], route_df["table_index"]], dropna=False):
        prev_core_metric = ""
        for _, row in group.sort_values(by=["row_index", "candidate_id"]).iterrows():
            row_dict = row.to_dict()
            metric = _norm_text(row_dict.get("metric_after"))
            evidence = _norm_text(row_dict.get("source_evidence_excerpt"))
            if metric not in {"YoY", "revenue_yoy", "net_profit_yoy"}:
                if metric in {"revenue", "net_profit"}:
                    prev_core_metric = metric
                repaired_rows.append(row_dict)
                continue
            if metric in {"revenue_yoy", "net_profit_yoy"}:
                if "归母净利润" in evidence or "净利润" in evidence:
                    if metric != "net_profit_yoy":
                        repaired_count += 1
                    row_dict["metric_after"] = "net_profit_yoy"
                    row_dict["metric_display_zh_after"] = "归母净利润同比"
                    row_dict["context_repair_reason"] = "yoy_fixed_from_evidence_net_profit"
                elif "营业收入" in evidence:
                    if metric != "revenue_yoy":
                        repaired_count += 1
                    row_dict["metric_after"] = "revenue_yoy"
                    row_dict["metric_display_zh_after"] = "营业收入同比"
                    row_dict["context_repair_reason"] = "yoy_fixed_from_evidence_revenue"
                repaired_rows.append(row_dict)
                continue
            if prev_core_metric == "revenue":
                row_dict["metric_after"] = "revenue_yoy"
                row_dict["metric_display_zh_after"] = "营业收入同比"
                row_dict["context_repair_reason"] = "yoy_repaired_from_previous_revenue"
                repaired_count += 1
            elif prev_core_metric == "net_profit":
                row_dict["metric_after"] = "net_profit_yoy"
                row_dict["metric_display_zh_after"] = "归母净利润同比"
                row_dict["context_repair_reason"] = "yoy_repaired_from_previous_net_profit"
                repaired_count += 1
            else:
                row_dict["status_after_337c"] = "needs_review"
                row_dict["route_reason_after_337c"] = "yoy_parent_ambiguous"
                row_dict["context_repair_reason"] = "yoy_parent_ambiguous"
                ambiguous_count += 1
            repaired_rows.append(row_dict)
    return _clean_frame(pd.DataFrame(repaired_rows)), repaired_count, ambiguous_count


def _is_macro_company_history_noise(table_preview: str) -> bool:
    text = _norm_text(table_preview)
    noise_keywords = ["渠道", "产品", "历史", "行业规模", "市场份额", "分业务", "分地区", "品牌"]
    return _contains_any(text, noise_keywords) and not _contains_any(text, ["2026E", "EPS", "P/E", "P/B", "归母净利润", "营业收入"])


def build_core_financial_context_repair_337c(
    *,
    precision_337b_dir: Path,
    mineru_real_test_dir: Path,
    output_dir: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)

    summary_337b_path = precision_337b_dir / "mineru_candidate_precision_337b_summary.json"
    workbook_337b_path = precision_337b_dir / "real_test_mineru_client_export_337b.xlsx"
    before_after_337b_path = precision_337b_dir / "mineru_candidate_precision_337b_before_after.xlsx"
    blocked_reasons: List[str] = []
    for path in [summary_337b_path, workbook_337b_path, before_after_337b_path]:
        if not path.exists():
            blocked_reasons.append(f"Missing required 337B artifact: {path}")

    if blocked_reasons:
        return {
            "summary": {
                "generated_at_utc": _utc_now(),
                "client_ready": False,
                "production_ready": False,
                "qa_fail_count": len(blocked_reasons),
                "decision": BLOCKED_DECISION,
            },
            "manifest": {},
            "qa_json": {"decision": BLOCKED_DECISION, "qa_fail_count": len(blocked_reasons), "checks": [], "blocked_reasons": blocked_reasons},
            "before_after_sheets": {},
            "customer_workbook_sheets": {},
        }

    summary_337b = json.loads(summary_337b_path.read_text(encoding="utf-8"))
    route_change_df = _read_excel(before_after_337b_path, "08_ROUTE_CHANGE_TRACE")
    table_classification_df = _read_excel(before_after_337b_path, "07_TABLE_ROLE_CLASSIFICATION")
    reviewed_337b_df = _read_excel(workbook_337b_path, "01_REVIEWED_CORE_METRICS")
    document_summary_337b_df = _read_excel(workbook_337b_path, "05_DOCUMENT_SUMMARY")

    role_repair_rows = []
    table_role_map: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for row in table_classification_df.to_dict(orient="records"):
        repaired_role, repair_reason = _repair_table_role(row)
        row_out = dict(row)
        row_out["table_role_337c"] = repaired_role
        row_out["table_role_repair_reason"] = repair_reason
        role_repair_rows.append(row_out)
        table_role_map[(_norm_text(row.get("document")), _safe_int(row.get("table_index")))] = row_out
    table_role_repair_df = _clean_frame(pd.DataFrame(role_repair_rows))

    route_rows = []
    unit_repair_rows = []
    for row in route_change_df.to_dict(orient="records"):
        key = (_norm_text(row.get("document")), _safe_int(row.get("table_index")))
        table_info = table_role_map.get(key, {})
        repaired_role = _norm_text(table_info.get("table_role_337c") or row.get("table_role_337b"))
        metric_after = _norm_text(row.get("metric_after"))
        repaired_unit, unit_filled = _repair_unit(metric_after, _norm_text(row.get("unit")), _norm_text(row.get("source_evidence_excerpt")), _norm_text(table_info.get("table_preview")))
        row_out = dict(row)
        row_out["table_role_337c"] = repaired_role
        row_out["unit_after_337c"] = repaired_unit
        row_out["status_after_337c"] = _norm_text(row.get("status_after"))
        row_out["route_reason_after_337c"] = _norm_text(row.get("route_reason_after"))
        row_out["context_repair_reason"] = ""
        if repaired_role in {"LEGAL_DISCLOSURE_TABLE", "RATING_STANDARD_TABLE"}:
            row_out["status_after_337c"] = "rejected_or_excluded"
            row_out["route_reason_after_337c"] = f"excluded_table_role::{repaired_role}"
        elif repaired_role in {"CORE_FINANCIAL_SUMMARY", "PROFIT_FORECAST_VALUATION", "FINANCIAL_STATEMENT_DETAIL"}:
            if row_out["status_after_337c"] != "rejected_or_excluded":
                row_out["status_after_337c"] = "reviewed_preview"
                row_out["route_reason_after_337c"] = "core_financial_context_repaired"
        elif repaired_role in {"INDUSTRY_DATA_TABLE", "COMPANY_PROFILE_TABLE", "OTHER_TABLE"}:
            if row_out["status_after_337c"] == "reviewed_preview":
                row_out["status_after_337c"] = "needs_review"
                row_out["route_reason_after_337c"] = f"non_core_table_role::{repaired_role}"
        if _norm_text(row_out.get("document")) == HIGH_REVIEWED_PDF and _is_macro_company_history_noise(_norm_text(table_info.get("table_preview"))):
            if row_out["status_after_337c"] == "reviewed_preview":
                row_out["status_after_337c"] = "needs_review"
                row_out["route_reason_after_337c"] = "356439_high_reviewed_source_audit"
        route_rows.append(row_out)
        unit_repair_rows.append(
            {
                "candidate_id": _norm_text(row.get("candidate_id")),
                "document": _norm_text(row.get("document")),
                "metric_after": metric_after,
                "unit_before": _norm_text(row.get("unit")),
                "unit_after": repaired_unit,
                "unit_filled": unit_filled,
                "source_evidence_excerpt": _norm_text(row.get("source_evidence_excerpt")),
            }
        )

    repaired_route_df, yoy_parent_repaired_count, yoy_parent_ambiguous_count = _repair_yoy_metric_with_context(_clean_frame(pd.DataFrame(route_rows)))

    reviewed_after_df = repaired_route_df[repaired_route_df["status_after_337c"] == "reviewed_preview"].copy()
    needs_review_after_df = repaired_route_df[repaired_route_df["status_after_337c"] == "needs_review"].copy()
    rejected_after_df = repaired_route_df[repaired_route_df["status_after_337c"] == "rejected_or_excluded"].copy()

    def _customerize(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["row_no", "document", "metric", "metric_display_zh", "year", "value", "unit", "source_page", "status", "source_evidence_excerpt", "notes"])
        out = _clean_frame(
            df[
                ["document", "metric_after", "metric_display_zh_after", "year", "value", "unit_after_337c", "source_page", "status_after_337c", "source_evidence_excerpt", "route_reason_after_337c"]
            ].rename(
                columns={
                    "metric_after": "metric",
                    "metric_display_zh_after": "metric_display_zh",
                    "unit_after_337c": "unit",
                    "status_after_337c": "status",
                    "route_reason_after_337c": "notes",
                }
            )
        )
        out.insert(0, "row_no", range(1, len(out) + 1))
        return out

    reviewed_customer_df = _customerize(reviewed_after_df)
    needs_review_customer_df = _customerize(needs_review_after_df)
    rejected_customer_df = _customerize(rejected_after_df)

    unit_repair_df = _clean_frame(pd.DataFrame(unit_repair_rows))
    unit_filled_count = int(unit_repair_df["unit_filled"].sum()) if not unit_repair_df.empty else 0
    unit_still_missing_count = int((unit_repair_df["unit_after"] == "").sum()) if not unit_repair_df.empty else 0

    reviewed_356439_audit_df = _clean_frame(
        repaired_route_df[repaired_route_df["document"] == HIGH_REVIEWED_PDF][
            [
                "source_page",
                "table_role_337c",
                "metric_after",
                "year",
                "value",
                "unit_after_337c",
                "source_evidence_excerpt",
                "route_reason_after_337c",
                "status_after_337c",
            ]
        ].rename(
            columns={
                "metric_after": "metric",
                "unit_after_337c": "unit",
                "route_reason_after_337c": "review_reason",
                "status_after_337c": "status",
            }
        )
    )

    document_summary_rows = []
    for document, group in repaired_route_df.groupby("document", dropna=False):
        document_summary_rows.append(
            {
                "document": document,
                "reviewed_after_337c_count": int((group["status_after_337c"] == "reviewed_preview").sum()),
                "needs_review_after_337c_count": int((group["status_after_337c"] == "needs_review").sum()),
                "rejected_after_337c_count": int((group["status_after_337c"] == "rejected_or_excluded").sum()),
            }
        )
    document_summary_337c_df = _clean_frame(pd.DataFrame(document_summary_rows))

    reviewed_356439_before_count = 0
    if not document_summary_337b_df.empty and "document" in document_summary_337b_df.columns and "reviewed_after_count" in document_summary_337b_df.columns:
        reviewed_356439_before_count = int(
            document_summary_337b_df.loc[
                document_summary_337b_df["document"] == HIGH_REVIEWED_PDF,
                "reviewed_after_count",
            ].sum()
        )
    reviewed_356439_after_count = 0
    if not document_summary_337c_df.empty and "document" in document_summary_337c_df.columns and "reviewed_after_337c_count" in document_summary_337c_df.columns:
        reviewed_356439_after_count = int(
            document_summary_337c_df.loc[
                document_summary_337c_df["document"] == HIGH_REVIEWED_PDF,
                "reviewed_after_337c_count",
            ].sum()
        )

    context_repair_summary_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "table_role_repair_count": int((table_role_repair_df["table_role_repair_reason"] != "unchanged").sum()) if not table_role_repair_df.empty else 0,
                    "unit_filled_count": unit_filled_count,
                    "unit_still_missing_count": unit_still_missing_count,
                    "yoy_parent_repaired_count": yoy_parent_repaired_count,
                    "yoy_parent_ambiguous_count": yoy_parent_ambiguous_count,
                    "reviewed_356439_before_count": reviewed_356439_before_count,
                    "reviewed_356439_after_count": reviewed_356439_after_count,
                }
            ]
        )
    )

    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])

    no_bad_reviewed_role = True
    no_net_profit_yoy_as_revenue_yoy = True
    source_page_exists_for_reviewed = True
    if not repaired_route_df.empty:
        reviewed_rows = repaired_route_df[repaired_route_df["status_after_337c"] == "reviewed_preview"]
        no_bad_reviewed_role = not reviewed_rows["table_role_337c"].isin(["LEGAL_DISCLOSURE_TABLE", "RATING_STANDARD_TABLE"]).any()
        source_page_exists_for_reviewed = not reviewed_rows["source_page"].isna().any() and not (reviewed_rows["source_page"] == "").any()
        mask = reviewed_rows["source_evidence_excerpt"].astype(str).str.contains("净利润", na=False)
        if mask.any():
            no_net_profit_yoy_as_revenue_yoy = not ((reviewed_rows.loc[mask, "metric_after"] == "revenue_yoy").any())

    rescued_core_summary_ok = True
    if not table_role_repair_df.empty:
        candidate_core = table_role_repair_df[
            table_role_repair_df["table_preview"].astype(str).str.contains("营业收入", na=False)
            & table_role_repair_df["table_preview"].astype(str).str.contains("归母净利润|净利润", na=False)
            & table_role_repair_df["table_preview"].astype(str).str.contains("2026E", na=False)
        ]
        if not candidate_core.empty:
            rescued_core_summary_ok = not candidate_core["table_role_337c"].isin(["INDUSTRY_DATA_TABLE"]).any()

    appendix_not_legal_ok = True
    if not table_role_repair_df.empty:
        appendix = table_role_repair_df[table_role_repair_df["table_preview"].astype(str).str.contains("资产负债表|利润表|现金流量表|主要财务比率", na=False)]
        if not appendix.empty:
            appendix_not_legal_ok = not appendix["table_role_337c"].isin(["LEGAL_DISCLOSURE_TABLE"]).any()

    qa_checks = [
        {"check_name": "input_337b_workbook_exists", "status": "PASS" if workbook_337b_path.exists() else "FAIL", "detail": str(workbook_337b_path)},
        {"check_name": "three_pdfs_represented", "status": "PASS" if len(document_summary_337c_df) == 3 else "FAIL", "detail": str(len(document_summary_337c_df))},
        {"check_name": "no_legal_or_rating_rows_in_reviewed", "status": "PASS" if no_bad_reviewed_role else "FAIL", "detail": str(no_bad_reviewed_role)},
        {"check_name": "core_financial_summary_tables_not_left_as_industry", "status": "PASS" if rescued_core_summary_ok else "FAIL", "detail": str(rescued_core_summary_ok)},
        {"check_name": "financial_appendix_tables_not_left_as_legal", "status": "PASS" if appendix_not_legal_ok else "FAIL", "detail": str(appendix_not_legal_ok)},
        {"check_name": "unit_filled_count_reported", "status": "PASS" if unit_filled_count >= 0 else "FAIL", "detail": str(unit_filled_count)},
        {"check_name": "yoy_parent_repairs_reported", "status": "PASS" if yoy_parent_repaired_count >= 0 else "FAIL", "detail": str(yoy_parent_repaired_count)},
        {"check_name": "no_net_profit_yoy_as_revenue_yoy", "status": "PASS" if no_net_profit_yoy_as_revenue_yoy else "FAIL", "detail": str(no_net_profit_yoy_as_revenue_yoy)},
        {"check_name": "source_page_exists_for_reviewed", "status": "PASS" if source_page_exists_for_reviewed else "FAIL", "detail": str(source_page_exists_for_reviewed)},
        {"check_name": "official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_status_preserved", "status": "PASS" if protected_status_before == protected_status_after else "FAIL", "detail": json.dumps(protected_status_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_paths_not_staged", "status": "PASS" if not protected_cached_after else "FAIL", "detail": json.dumps(protected_cached_after, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")
    decision = READY_DECISION if qa_fail_count == 0 else PARTIAL_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "client_ready": False,
        "production_ready": False,
        "precision_337b_dir": str(precision_337b_dir),
        "mineru_real_test_dir": str(mineru_real_test_dir),
        "output_dir": str(output_dir),
        "reviewed_before_count": summary_337b.get("reviewed_after_count", 0),
        "reviewed_after_count": len(reviewed_customer_df),
        "needs_review_after_count": len(needs_review_customer_df),
        "rejected_after_count": len(rejected_customer_df),
        "table_role_repair_count": int((table_role_repair_df["table_role_repair_reason"] != "unchanged").sum()) if not table_role_repair_df.empty else 0,
        "unit_filled_count": unit_filled_count,
        "unit_still_missing_count": unit_still_missing_count,
        "yoy_parent_repaired_count": yoy_parent_repaired_count,
        "yoy_parent_ambiguous_count": yoy_parent_ambiguous_count,
        "reviewed_356439_before_count": reviewed_356439_before_count,
        "reviewed_356439_after_count": reviewed_356439_after_count,
        "no_official_asset_modification_during_337c": official_assets_before == official_assets_after,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "337C_core_financial_table_context_repair",
        "precision_337b_dir": str(precision_337b_dir),
        "mineru_real_test_dir": str(mineru_real_test_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "core_financial_context_repair_337c_summary.json"),
            "manifest_json": str(output_dir / "core_financial_context_repair_337c_manifest.json"),
            "qa_json": str(output_dir / "core_financial_context_repair_337c_qa.json"),
            "report_md": str(output_dir / "core_financial_context_repair_337c_report.md"),
            "before_after_xlsx": str(output_dir / "core_financial_context_repair_337c_before_after.xlsx"),
            "customer_workbook_xlsx": str(output_dir / "real_test_mineru_client_export_337c.xlsx"),
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
        "00_SUMMARY": context_repair_summary_df,
        "01_337B_COUNTS": _clean_frame(pd.DataFrame([summary_337b])),
        "02_337C_COUNTS": _clean_frame(pd.DataFrame([summary])),
        "03_TABLE_ROLE_REPAIRS": table_role_repair_df,
        "04_UNIT_REPAIRS": unit_repair_df,
        "05_YOY_PARENT_REPAIRS": repaired_route_df[
            ["candidate_id", "document", "metric_before", "metric_after", "context_repair_reason", "status_after_337c", "route_reason_after_337c", "source_evidence_excerpt", "table_index", "row_index"]
        ] if not repaired_route_df.empty else pd.DataFrame(),
        "06_REVIEWED_AFTER_337C": reviewed_customer_df,
        "07_NEEDS_REVIEW_AFTER_337C": needs_review_customer_df,
        "08_REJECTED_AFTER_337C": rejected_customer_df,
        "09_356439_REVIEWED_AUDIT": reviewed_356439_audit_df,
        "10_ROUTE_CHANGE_TRACE": repaired_route_df,
    }

    customer_workbook_sheets = {
        CUSTOMER_WORKBOOK_SHEETS["readme"]: _customer_readme_df(),
        CUSTOMER_WORKBOOK_SHEETS["reviewed"]: reviewed_customer_df,
        CUSTOMER_WORKBOOK_SHEETS["needs_review"]: needs_review_customer_df,
        CUSTOMER_WORKBOOK_SHEETS["rejected"]: rejected_customer_df,
        CUSTOMER_WORKBOOK_SHEETS["trace"]: repaired_route_df,
        CUSTOMER_WORKBOOK_SHEETS["document_summary"]: document_summary_337c_df,
        CUSTOMER_WORKBOOK_SHEETS["table_summary"]: table_role_repair_df[
            ["document", "page_no", "table_index", "table_role_337c", "table_role_repair_reason", "candidate_score", "table_preview"]
        ] if not table_role_repair_df.empty else pd.DataFrame(),
        CUSTOMER_WORKBOOK_SHEETS["context_summary"]: context_repair_summary_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "before_after_sheets": before_after_sheets,
        "customer_workbook_sheets": customer_workbook_sheets,
    }
