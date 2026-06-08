from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.reviewed_strictness_year_alignment_337d import (  # noqa: E402
    READY_DECISION,
    build_reviewed_strictness_year_alignment_337d,
)


def _write_input_workbook(path: Path) -> None:
    route_rows = [
        {
            "candidate_id": "a1",
            "document": "H3_AP202606081823356439_1.pdf",
            "metric_after": "net_profit",
            "metric_display_zh_after": "归母净利润",
            "year": "2025A",
            "value": "1.18",
            "unit_after_337c": "亿元",
            "unit": "亿元",
            "source_page": 2,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "净利润 | 1.18 | 3.25 | 4.72 | 6.15",
            "table_index": 2,
            "row_index": 2,
            "table_role_337c": "CORE_FINANCIAL_SUMMARY",
            "table_preview": "项目\\年度 2025A | 2026E | 2027E | 2028E\n净利润 | 1.18 | 3.25 | 4.72 | 6.15",
            "status_after": "reviewed_preview",
            "metric_after_337c": "net_profit",
        },
        {
            "candidate_id": "a2",
            "document": "H3_AP202606081823356439_1.pdf",
            "metric_after": "net_profit",
            "metric_display_zh_after": "归母净利润",
            "year": "2025A",
            "value": "3.25",
            "unit_after_337c": "亿元",
            "unit": "亿元",
            "source_page": 2,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "净利润 | 1.18 | 3.25 | 4.72 | 6.15",
            "table_index": 2,
            "row_index": 2,
            "table_role_337c": "CORE_FINANCIAL_SUMMARY",
            "table_preview": "项目\\年度 2025A | 2026E | 2027E | 2028E\n净利润 | 1.18 | 3.25 | 4.72 | 6.15",
            "status_after": "reviewed_preview",
            "metric_after_337c": "net_profit",
        },
        {
            "candidate_id": "a3",
            "document": "H3_AP202606081823356439_1.pdf",
            "metric_after": "net_profit",
            "metric_display_zh_after": "归母净利润",
            "year": "2025A",
            "value": "4.72",
            "unit_after_337c": "亿元",
            "unit": "亿元",
            "source_page": 2,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "净利润 | 1.18 | 3.25 | 4.72 | 6.15",
            "table_index": 2,
            "row_index": 2,
            "table_role_337c": "CORE_FINANCIAL_SUMMARY",
            "table_preview": "项目\\年度 2025A | 2026E | 2027E | 2028E\n净利润 | 1.18 | 3.25 | 4.72 | 6.15",
            "status_after": "reviewed_preview",
            "metric_after_337c": "net_profit",
        },
        {
            "candidate_id": "a4",
            "document": "H3_AP202606081823356439_1.pdf",
            "metric_after": "net_profit",
            "metric_display_zh_after": "归母净利润",
            "year": "2025A",
            "value": "6.15",
            "unit_after_337c": "亿元",
            "unit": "亿元",
            "source_page": 2,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "净利润 | 1.18 | 3.25 | 4.72 | 6.15",
            "table_index": 2,
            "row_index": 2,
            "table_role_337c": "CORE_FINANCIAL_SUMMARY",
            "table_preview": "项目\\年度 2025A | 2026E | 2027E | 2028E\n净利润 | 1.18 | 3.25 | 4.72 | 6.15",
            "status_after": "reviewed_preview",
            "metric_after_337c": "net_profit",
        },
        {
            "candidate_id": "b1",
            "document": "H3_AP202606081823356439_1.pdf",
            "metric_after": "net_profit",
            "metric_display_zh_after": "归母净利润",
            "year": "2025A",
            "value": "4.29%",
            "unit_after_337c": "%",
            "unit": "%",
            "source_page": 4,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%",
            "table_index": 4,
            "row_index": 3,
            "table_role_337c": "FINANCIAL_STATEMENT_DETAIL",
            "table_preview": "主要财务比率 2025A 2026E 2027E 2028E\n归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%",
            "status_after": "reviewed_preview",
            "metric_after_337c": "net_profit",
        },
        {
            "candidate_id": "b2",
            "document": "H3_AP202606081823356439_1.pdf",
            "metric_after": "net_profit",
            "metric_display_zh_after": "归母净利润",
            "year": "2025A",
            "value": "174.10%",
            "unit_after_337c": "%",
            "unit": "%",
            "source_page": 4,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%",
            "table_index": 4,
            "row_index": 3,
            "table_role_337c": "FINANCIAL_STATEMENT_DETAIL",
            "table_preview": "主要财务比率 2025A 2026E 2027E 2028E\n归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%",
            "status_after": "reviewed_preview",
            "metric_after_337c": "net_profit",
        },
        {
            "candidate_id": "b3",
            "document": "H3_AP202606081823356439_1.pdf",
            "metric_after": "net_profit",
            "metric_display_zh_after": "归母净利润",
            "year": "2025A",
            "value": "45.36%",
            "unit_after_337c": "%",
            "unit": "%",
            "source_page": 4,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%",
            "table_index": 4,
            "row_index": 3,
            "table_role_337c": "FINANCIAL_STATEMENT_DETAIL",
            "table_preview": "主要财务比率 2025A 2026E 2027E 2028E\n归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%",
            "status_after": "reviewed_preview",
            "metric_after_337c": "net_profit",
        },
        {
            "candidate_id": "b4",
            "document": "H3_AP202606081823356439_1.pdf",
            "metric_after": "net_profit",
            "metric_display_zh_after": "归母净利润",
            "year": "2025A",
            "value": "30.20%",
            "unit_after_337c": "%",
            "unit": "%",
            "source_page": 4,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%",
            "table_index": 4,
            "row_index": 3,
            "table_role_337c": "FINANCIAL_STATEMENT_DETAIL",
            "table_preview": "主要财务比率 2025A 2026E 2027E 2028E\n归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%",
            "status_after": "reviewed_preview",
            "metric_after_337c": "net_profit",
        },
        {
            "candidate_id": "c1",
            "document": "H3_AP202606081823352620_1.pdf",
            "metric_after": "revenue",
            "metric_display_zh_after": "营业收入",
            "year": "2025A",
            "value": "56.33",
            "unit_after_337c": "亿元",
            "unit": "亿元",
            "source_page": 1,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "营业收入 | 56.33 | 65.70 | 78.45 | 93.28",
            "table_index": 10,
            "row_index": 2,
            "table_role_337c": "CORE_FINANCIAL_SUMMARY",
            "table_preview": "项目\\年度 2025A | 2026E | 2027E | 2028E\n营业收入 | 56.33 | 65.70 | 78.45 | 93.28",
            "status_after": "reviewed_preview",
            "metric_after_337c": "revenue",
        },
        {
            "candidate_id": "c2",
            "document": "H3_AP202606081823352620_1.pdf",
            "metric_after": "revenue",
            "metric_display_zh_after": "营业收入",
            "year": "2025A",
            "value": "56.33",
            "unit_after_337c": "亿元",
            "unit": "亿元",
            "source_page": 9,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "营业收入 | 56.33 | 65.70 | 78.45 | 93.28",
            "table_index": 11,
            "row_index": 2,
            "table_role_337c": "FINANCIAL_STATEMENT_DETAIL",
            "table_preview": "利润表(亿元) 2025A 2026E 2027E 2028E\n营业收入 | 56.33 | 65.70 | 78.45 | 93.28",
            "status_after": "reviewed_preview",
            "metric_after_337c": "revenue",
        },
        {
            "candidate_id": "d1",
            "document": "H3_AP202606081823352906_1.pdf",
            "metric_after": "net_profit",
            "metric_display_zh_after": "归母净利润",
            "year": "2026E",
            "value": "1816",
            "unit_after_337c": "",
            "unit": "",
            "source_page": 5,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "净利润 | 1514 | 1370 | 1816 | 2129 | 2442",
            "table_index": 20,
            "row_index": 3,
            "table_role_337c": "PROFIT_FORECAST_VALUATION",
            "table_preview": "会计年度 2024A 2025A 2026E 2027E 2028E\n经营活动现金流 | 2104 | 2317 | 2286 | 2115 | 2938",
            "status_after": "reviewed_preview",
            "metric_after_337c": "net_profit",
        },
        {
            "candidate_id": "e1",
            "document": "H3_AP202606081823352906_1.pdf",
            "metric_after": "EPS",
            "metric_display_zh_after": "每股收益",
            "year": "2026E",
            "value": "0.42",
            "unit_after_337c": "",
            "unit": "",
            "source_page": 5,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "EPS | 0.34 | 0.42 | 0.53 | 0.68",
            "table_index": 21,
            "row_index": 4,
            "table_role_337c": "PROFIT_FORECAST_VALUATION",
            "table_preview": "项目\\年度 2025A | 2026E | 2027E | 2028E\nEPS | 0.34 | 0.42 | 0.53 | 0.68",
            "status_after": "reviewed_preview",
            "metric_after_337c": "EPS",
        },
        {
            "candidate_id": "f1",
            "document": "H3_AP202606081823352620_1.pdf",
            "metric_after": "revenue",
            "metric_display_zh_after": "营业收入",
            "year": "2025A",
            "value": "16.29%",
            "unit_after_337c": "%",
            "unit": "%",
            "source_page": 8,
            "status_after_337c": "reviewed_preview",
            "route_reason_after_337c": "core_financial_context_repaired",
            "source_evidence_excerpt": "营业收入 | 16.29% | 16.63% | 19.41% | 18.91%",
            "table_index": 30,
            "row_index": 3,
            "table_role_337c": "FINANCIAL_STATEMENT_DETAIL",
            "table_preview": "主要财务比率 2025A 2026E 2027E 2028E\n营业收入 | 16.29% | 16.63% | 19.41% | 18.91%",
            "status_after": "reviewed_preview",
            "metric_after_337c": "revenue",
        },
    ]
    doc_summary = pd.DataFrame(
        [
            {"document": "H3_AP202606081823356439_1.pdf", "reviewed_after_337c_count": 8, "needs_review_after_337c_count": 0, "rejected_after_337c_count": 0},
            {"document": "H3_AP202606081823352620_1.pdf", "reviewed_after_337c_count": 3, "needs_review_after_337c_count": 0, "rejected_after_337c_count": 0},
            {"document": "H3_AP202606081823352906_1.pdf", "reviewed_after_337c_count": 2, "needs_review_after_337c_count": 0, "rejected_after_337c_count": 0},
        ]
    )
    table_summary = pd.DataFrame(
        [
            {"document": "H3_AP202606081823356439_1.pdf", "page_no": 2, "table_index": 2, "table_role_337c": "CORE_FINANCIAL_SUMMARY", "table_role_repair_reason": "x", "candidate_score": 10, "table_preview": "项目\\年度 2025A | 2026E | 2027E | 2028E\n净利润 | 1.18 | 3.25 | 4.72 | 6.15"},
            {"document": "H3_AP202606081823356439_1.pdf", "page_no": 4, "table_index": 4, "table_role_337c": "FINANCIAL_STATEMENT_DETAIL", "table_role_repair_reason": "x", "candidate_score": 9, "table_preview": "主要财务比率 2025A 2026E 2027E 2028E\n归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%"},
            {"document": "H3_AP202606081823352620_1.pdf", "page_no": 1, "table_index": 10, "table_role_337c": "CORE_FINANCIAL_SUMMARY", "table_role_repair_reason": "x", "candidate_score": 8, "table_preview": "项目\\年度 2025A | 2026E | 2027E | 2028E\n营业收入 | 56.33 | 65.70 | 78.45 | 93.28"},
            {"document": "H3_AP202606081823352620_1.pdf", "page_no": 9, "table_index": 11, "table_role_337c": "FINANCIAL_STATEMENT_DETAIL", "table_role_repair_reason": "x", "candidate_score": 7, "table_preview": "利润表(亿元) 2025A 2026E 2027E 2028E\n营业收入 | 56.33 | 65.70 | 78.45 | 93.28"},
            {"document": "H3_AP202606081823352906_1.pdf", "page_no": 5, "table_index": 20, "table_role_337c": "PROFIT_FORECAST_VALUATION", "table_role_repair_reason": "x", "candidate_score": 7, "table_preview": "会计年度 2024A 2025A 2026E 2027E 2028E"},
            {"document": "H3_AP202606081823352906_1.pdf", "page_no": 5, "table_index": 21, "table_role_337c": "PROFIT_FORECAST_VALUATION", "table_role_repair_reason": "x", "candidate_score": 7, "table_preview": "项目\\年度 2025A | 2026E | 2027E | 2028E\nEPS | 0.34 | 0.42 | 0.53 | 0.68"},
            {"document": "H3_AP202606081823352620_1.pdf", "page_no": 8, "table_index": 30, "table_role_337c": "FINANCIAL_STATEMENT_DETAIL", "table_role_repair_reason": "x", "candidate_score": 7, "table_preview": "主要财务比率 2025A 2026E 2027E 2028E\n营业收入 | 16.29% | 16.63% | 19.41% | 18.91%"},
        ]
    )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "x", "message": "y"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"row_no": 1}]).to_excel(writer, sheet_name="01_REVIEWED_CORE_METRICS", index=False)
        pd.DataFrame([{"row_no": 1}]).to_excel(writer, sheet_name="02_NEEDS_REVIEW", index=False)
        pd.DataFrame([{"row_no": 1}]).to_excel(writer, sheet_name="03_REJECTED_OR_EXCLUDED", index=False)
        pd.DataFrame(route_rows).to_excel(writer, sheet_name="04_SOURCE_TRACE", index=False)
        doc_summary.to_excel(writer, sheet_name="05_DOCUMENT_SUMMARY", index=False)
        table_summary.to_excel(writer, sheet_name="06_TABLE_CLASSIFICATION_SUMMARY", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="07_CONTEXT_REPAIR_SUMMARY", index=False)


def test_build_reviewed_strictness_year_alignment_337d_ready(tmp_path: Path) -> None:
    context_dir = tmp_path / "337c"
    mineru_dir = tmp_path / "337a"
    output_dir = tmp_path / "337d"
    context_dir.mkdir()
    mineru_dir.mkdir()
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    (context_dir / "core_financial_context_repair_337c_summary.json").write_text(
        json.dumps(
            {
                "reviewed_after_count": 13,
                "needs_review_after_count": 0,
                "rejected_after_count": 0,
                "reviewed_356439_after_count": 8,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (mineru_dir / "00_batch_summary.json").write_text(
        json.dumps({"reviewed_count": 40, "needs_review_count": 10, "rejected_or_excluded_count": 5}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_input_workbook(context_dir / "real_test_mineru_client_export_337c.xlsx")

    artifacts = build_reviewed_strictness_year_alignment_337d(
        context_repair_337c_dir=context_dir,
        mineru_real_test_dir=mineru_dir,
        output_dir=output_dir,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["year_alignment_repaired_count"] >= 6
    assert summary["percent_amount_guard_remapped_count"] == 5
    assert summary["unit_strictness_downgraded_count"] == 1
    assert summary["unit_strictness_filled_count"] >= 1
    assert summary["reviewed_duplicate_removed_count"] == 1
    assert summary["reviewed_after_count"] < summary["reviewed_before_count"]
    assert summary["reviewed_356439_after_count"] <= summary["reviewed_356439_before_count"]
    assert summary["qa_fail_count"] == 0

    reviewed_df = artifacts["customer_workbook_sheets"]["01_REVIEWED_CORE_METRICS"]
    assert not reviewed_df.empty
    assert not reviewed_df[(reviewed_df["metric"].isin(["revenue", "net_profit"])) & (reviewed_df["unit"].astype(str).str.contains("%", na=False))].any().any()
    assert not reviewed_df[(reviewed_df["metric"].isin(["revenue", "net_profit"])) & (reviewed_df["unit"].astype(str).str.strip() == "")].any().any()
    assert "net_profit_yoy" in set(reviewed_df["metric"])
    suspicious_df = artifacts["customer_workbook_sheets"]["08_SUSPICIOUS_REVIEWED_AUDIT"]
    assert not suspicious_df.empty
