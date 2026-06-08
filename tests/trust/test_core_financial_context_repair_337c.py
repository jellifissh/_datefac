from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.core_financial_context_repair_337c import (  # noqa: E402
    READY_DECISION,
    build_core_financial_context_repair_337c,
)
from datefac.trust.core_financial_context_repair_337c_report import write_excel  # noqa: E402


def _make_337b_workbook(path: Path) -> None:
    sheets = {
        "00_README": pd.DataFrame([{"topic": "x", "message": "y"}]),
        "01_REVIEWED_CORE_METRICS": pd.DataFrame([{"row_no": 1, "document": "a.pdf", "metric": "revenue"}]),
        "02_NEEDS_REVIEW": pd.DataFrame([{"row_no": 1, "document": "a.pdf", "metric": "YoY"}]),
        "03_REJECTED_OR_EXCLUDED": pd.DataFrame([{"row_no": 1, "document": "a.pdf", "metric": "rating"}]),
        "04_SOURCE_TRACE": pd.DataFrame([{"candidate_id": "c1"}]),
        "05_DOCUMENT_SUMMARY": pd.DataFrame(
            [
                {"document": "a.pdf", "reviewed_after_count": 2},
                {"document": "b.pdf", "reviewed_after_count": 1},
                {"document": "H3_AP202606081823356439_1.pdf", "reviewed_after_count": 4},
            ]
        ),
        "06_TABLE_CLASSIFICATION_SUMMARY": pd.DataFrame([{"document": "a.pdf"}]),
    }
    write_excel(path, sheets, list(sheets.keys()))


def _make_337b_before_after(path: Path) -> None:
    table_role_df = pd.DataFrame(
        [
            {
                "document": "a.pdf",
                "page_no": 1,
                "table_index": 2,
                "table_role_337b": "INDUSTRY_DATA_TABLE",
                "candidate_score": 10,
                "table_preview": "指标 | 2024A | 2025A | 2026E\n营业收入(百万元) | 100 | 120 | 140\n归母净利润(百万元) | 20 | 24 | 30\nEPS(元) | 1.0 | 1.2 | 1.5\nP/E(倍) | 10 | 9 | 8",
            },
            {
                "document": "a.pdf",
                "page_no": 30,
                "table_index": 3,
                "table_role_337b": "LEGAL_DISCLOSURE_TABLE",
                "candidate_score": 8,
                "table_preview": "利润表(百万元) | 2024A | 2025A | 2026E\n营业收入 | 100 | 120 | 140\n净利润 | 20 | 24 | 30",
            },
            {
                "document": "H3_AP202606081823356439_1.pdf",
                "page_no": 12,
                "table_index": 9,
                "table_role_337b": "CORE_FINANCIAL_SUMMARY",
                "candidate_score": 6,
                "table_preview": "渠道结构 | 2024A | 2025A | 2026E\n线上 | 10 | 12 | 14",
            },
        ]
    )
    route_df = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "document": "a.pdf",
                "metric_before": "revenue",
                "metric_after": "revenue",
                "metric_display_zh_after": "营业收入",
                "year": "2026E",
                "value": "140",
                "unit": "",
                "source_page": 1,
                "status_before": "needs_review",
                "status_after": "needs_review",
                "route_reason_before": "x",
                "route_reason_after": "non_core_table_role::INDUSTRY_DATA_TABLE",
                "source_evidence_excerpt": "营业收入(百万元) | 100 | 120 | 140",
                "table_index": 2,
                "row_index": 2,
                "table_role_337b": "INDUSTRY_DATA_TABLE",
                "is_duplicate_table_removed": False,
                "table_preview": "指标 | 2024A | 2025A | 2026E\n营业收入(百万元) | 100 | 120 | 140\n归母净利润(百万元) | 20 | 24 | 30",
            },
            {
                "candidate_id": "c2",
                "document": "a.pdf",
                "metric_before": "YoY",
                "metric_after": "YoY",
                "metric_display_zh_after": "同比",
                "year": "2026E",
                "value": "12",
                "unit": "",
                "source_page": 1,
                "status_before": "needs_review",
                "status_after": "needs_review",
                "route_reason_before": "x",
                "route_reason_after": "non_core_table_role::INDUSTRY_DATA_TABLE",
                "source_evidence_excerpt": "YOY(%) | 5 | 10 | 12",
                "table_index": 2,
                "row_index": 3,
                "table_role_337b": "INDUSTRY_DATA_TABLE",
                "is_duplicate_table_removed": False,
                "table_preview": "指标 | 2024A | 2025A | 2026E\n营业收入(百万元) | 100 | 120 | 140\n归母净利润(百万元) | 20 | 24 | 30",
            },
            {
                "candidate_id": "c3",
                "document": "a.pdf",
                "metric_before": "net_profit",
                "metric_after": "net_profit",
                "metric_display_zh_after": "归母净利润",
                "year": "2026E",
                "value": "30",
                "unit": "",
                "source_page": 30,
                "status_before": "rejected_or_excluded",
                "status_after": "rejected_or_excluded",
                "route_reason_before": "x",
                "route_reason_after": "excluded_table_role::LEGAL_DISCLOSURE_TABLE",
                "source_evidence_excerpt": "净利润 | 20 | 24 | 30",
                "table_index": 3,
                "row_index": 3,
                "table_role_337b": "LEGAL_DISCLOSURE_TABLE",
                "is_duplicate_table_removed": False,
                "table_preview": "利润表(百万元) | 2024A | 2025A | 2026E\n营业收入 | 100 | 120 | 140\n净利润 | 20 | 24 | 30",
            },
            {
                "candidate_id": "c4",
                "document": "H3_AP202606081823356439_1.pdf",
                "metric_before": "revenue",
                "metric_after": "revenue",
                "metric_display_zh_after": "营业收入",
                "year": "2026E",
                "value": "14",
                "unit": "",
                "source_page": 12,
                "status_before": "reviewed_preview",
                "status_after": "reviewed_preview",
                "route_reason_before": "x",
                "route_reason_after": "strict_review_ok",
                "source_evidence_excerpt": "渠道结构 | 线上 | 10 | 12 | 14",
                "table_index": 9,
                "row_index": 2,
                "table_role_337b": "CORE_FINANCIAL_SUMMARY",
                "is_duplicate_table_removed": False,
                "table_preview": "渠道结构 | 2024A | 2025A | 2026E\n线上 | 10 | 12 | 14",
            },
            {
                "candidate_id": "c5",
                "document": "b.pdf",
                "metric_before": "EPS",
                "metric_after": "EPS",
                "metric_display_zh_after": "每股收益",
                "year": "2026E",
                "value": "1.5",
                "unit": "",
                "source_page": 2,
                "status_before": "reviewed_preview",
                "status_after": "reviewed_preview",
                "route_reason_before": "x",
                "route_reason_after": "strict_review_ok",
                "source_evidence_excerpt": "EPS(元) | 1.0 | 1.2 | 1.5",
                "table_index": 4,
                "row_index": 4,
                "table_role_337b": "CORE_FINANCIAL_SUMMARY",
                "is_duplicate_table_removed": False,
                "table_preview": "指标 | 2024A | 2025A | 2026E\n营业收入(百万元) | 80 | 90 | 100\n归母净利润(百万元) | 10 | 12 | 15\nEPS(元) | 1.0 | 1.2 | 1.5",
            },
        ]
    )
    sheets = {
        "00_SUMMARY": pd.DataFrame([{"x": 1}]),
        "01_337B_COUNTS": pd.DataFrame([{"x": 1}]),
        "02_337C_COUNTS": pd.DataFrame([{"x": 1}]),
        "03_REVIEWED_AFTER": pd.DataFrame([{"x": 1}]),
        "04_NEEDS_REVIEW_AFTER": pd.DataFrame([{"x": 1}]),
        "05_REJECTED_AFTER": pd.DataFrame([{"x": 1}]),
        "06_DUPLICATE_TABLES_REMOVED": pd.DataFrame([{"x": 1}]),
        "07_TABLE_ROLE_CLASSIFICATION": table_role_df,
        "08_ROUTE_CHANGE_TRACE": route_df,
    }
    write_excel(path, sheets, list(sheets.keys()))


def test_build_core_financial_context_repair_337c_ready(tmp_path: Path) -> None:
    precision_dir = tmp_path / "337b"
    mineru_dir = tmp_path / "337a"
    output_dir = tmp_path / "337c"
    precision_dir.mkdir()
    mineru_dir.mkdir()
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    (precision_dir / "mineru_candidate_precision_337b_summary.json").write_text(
        json.dumps(
            {
                "reviewed_after_count": 4,
                "needs_review_after_count": 2,
                "rejected_after_count": 1,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _make_337b_workbook(precision_dir / "real_test_mineru_client_export_337b.xlsx")
    _make_337b_before_after(precision_dir / "mineru_candidate_precision_337b_before_after.xlsx")

    artifacts = build_core_financial_context_repair_337c(
        precision_337b_dir=precision_dir,
        mineru_real_test_dir=mineru_dir,
        output_dir=output_dir,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["table_role_repair_count"] >= 2
    assert summary["unit_filled_count"] >= 2
    assert summary["yoy_parent_repaired_count"] >= 1
    assert summary["reviewed_356439_after_count"] <= summary["reviewed_356439_before_count"]
    assert summary["qa_fail_count"] == 0

    reviewed_df = artifacts["customer_workbook_sheets"]["01_REVIEWED_CORE_METRICS"]
    needs_review_df = artifacts["customer_workbook_sheets"]["02_NEEDS_REVIEW"]
    assert not reviewed_df.empty
    assert "百万元" in set(reviewed_df["unit"]) or "元" in set(reviewed_df["unit"])
    assert "revenue_yoy" in set(needs_review_df["metric"]) or "revenue_yoy" in set(reviewed_df["metric"])
