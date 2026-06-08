from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.mineru_candidate_precision_337b import (  # noqa: E402
    READY_DECISION,
    build_mineru_candidate_precision_337b,
)
from datefac.trust.mineru_candidate_precision_337b_report import write_excel  # noqa: E402


def _make_customer_workbook(path: Path) -> None:
    sheets = {
        "00_README": pd.DataFrame([{"topic": "x", "message": "y"}]),
        "01_REVIEWED_CORE_METRICS": pd.DataFrame([{"row_no": 1, "document": "a.pdf", "metric": "revenue"}]),
        "02_NEEDS_REVIEW": pd.DataFrame([{"row_no": 1, "document": "a.pdf", "metric": "YoY"}]),
        "03_REJECTED_OR_EXCLUDED": pd.DataFrame([{"row_no": 1, "document": "a.pdf", "metric": "rating"}]),
        "04_SOURCE_TRACE": pd.DataFrame(
            [
                {
                    "candidate_id": "c1",
                    "document": "a.pdf",
                    "metric": "revenue",
                    "metric_display_zh": "营业收入",
                    "year": "2026E",
                    "value": "140",
                    "unit": "百万元",
                    "source_page": 1,
                    "status": "reviewed_preview",
                    "route_reason": "before",
                    "table_index": 2,
                    "row_index": 2,
                    "source_kind": "content_list",
                    "table_score": 10,
                    "table_matched_keywords": "财务数据",
                    "source_evidence_excerpt": "营业收入 | 100 | 120 | 140",
                    "notes": "before",
                }
            ]
        ),
        "05_DOCUMENT_SUMMARY": pd.DataFrame([{"document": "a.pdf"}]),
        "06_FINANCIAL_TABLE_CANDIDATES": pd.DataFrame([{"document": "a.pdf"}]),
    }
    write_excel(path, sheets, list(sheets.keys()))


def _make_debug_package(root: Path, name: str, table_rows, metric_rows) -> None:
    doc_dir = root / name
    doc_dir.mkdir(parents=True, exist_ok=True)
    (doc_dir / "document_summary.json").write_text(
        json.dumps(
            {
                "document": f"{name}.pdf",
                "pdf_stem": name,
                "parse_status": "processed",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    with pd.ExcelWriter(doc_dir / "financial_table_candidates.xlsx", engine="openpyxl") as writer:
        pd.DataFrame(table_rows).to_excel(writer, sheet_name="financial_table_candidates", index=False)
    with pd.ExcelWriter(doc_dir / "metric_candidates.xlsx", engine="openpyxl") as writer:
        pd.DataFrame(metric_rows).to_excel(writer, sheet_name="metric_candidates", index=False)


def test_build_mineru_candidate_precision_337b_ready(tmp_path: Path) -> None:
    mineru_dir = tmp_path / "337a"
    debug_root = mineru_dir / "datefac_debug"
    mineru_dir.mkdir()
    debug_root.mkdir()
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    (mineru_dir / "00_batch_summary.json").write_text(
        json.dumps(
            {
                "reviewed_count": 10,
                "needs_review_count": 2,
                "rejected_or_excluded_count": 1,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _make_customer_workbook(mineru_dir / "real_test_mineru_client_export_337a.xlsx")

    common_table = {
        "document": "a.pdf",
        "page_no": 1,
        "table_index": 2,
        "source_kind": "content_list",
        "table_role_guess": "CORE_METRIC_TABLE",
        "table_role_reason": "x",
        "caption": "财务数据与估值",
        "footnote": "",
        "nearby_text": "财务数据与估值",
        "image_path": "",
        "matched_keywords": "财务数据, 营业收入, 2026E",
        "candidate_score": 12,
        "html_present": True,
        "parsed_frame_count": 1,
        "row_count": 6,
        "col_count": 4,
        "table_preview": "指标 | 2024A | 2025A | 2026E\n营业收入(百万元) | 100 | 120 | 140\nYOY(%) | 5 | 10 | 12\n归母净利润(百万元) | 20 | 24 | 30",
    }
    duplicate_table = dict(common_table)
    duplicate_table["table_index"] = 20
    duplicate_table["candidate_score"] = 8

    metric_rows = [
        {
            "candidate_id": "c1",
            "document": "a.pdf",
            "metric": "revenue",
            "metric_display_zh": "营业收入",
            "year": "2026E",
            "value": "140",
            "unit": "百万元",
            "source_page": 1,
            "status": "reviewed_preview",
            "route_reason": "before",
            "source_evidence_excerpt": "营业收入(百万元) | 100 | 120 | 140",
            "notes": "before",
            "table_index": 2,
            "row_index": 2,
            "source_kind": "content_list",
            "table_score": 12,
            "table_matched_keywords": "财务数据",
            "header_context": "2026E",
        },
        {
            "candidate_id": "c2",
            "document": "a.pdf",
            "metric": "YoY",
            "metric_display_zh": "同比",
            "year": "2026E",
            "value": "12",
            "unit": "%",
            "source_page": 1,
            "status": "reviewed_preview",
            "route_reason": "before",
            "source_evidence_excerpt": "YOY(%) | 5 | 10 | 12",
            "notes": "before",
            "table_index": 2,
            "row_index": 3,
            "source_kind": "content_list",
            "table_score": 12,
            "table_matched_keywords": "财务数据",
            "header_context": "2026E",
        },
        {
            "candidate_id": "c3",
            "document": "a.pdf",
            "metric": "rating",
            "metric_display_zh": "投资评级",
            "year": "",
            "value": "买入",
            "unit": "",
            "source_page": 20,
            "status": "reviewed_preview",
            "route_reason": "before",
            "source_evidence_excerpt": "评级说明 买入",
            "notes": "before",
            "table_index": 9,
            "row_index": 2,
            "source_kind": "content_list",
            "table_score": 5,
            "table_matched_keywords": "评级说明",
            "header_context": "",
        },
    ]

    _make_debug_package(debug_root, "a", [common_table, duplicate_table], metric_rows)
    _make_debug_package(debug_root, "b", [dict(common_table, document="b.pdf", table_index=3)], [dict(metric_rows[0], candidate_id="b1", document="b.pdf", table_index=3)])
    _make_debug_package(debug_root, "c", [dict(common_table, document="c.pdf", table_index=4)], [dict(metric_rows[0], candidate_id="c1", document="c.pdf", table_index=4)])

    output_dir = tmp_path / "337b"
    artifacts = build_mineru_candidate_precision_337b(
        mineru_real_test_dir=mineru_dir,
        output_dir=output_dir,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["duplicate_table_removed_count"] >= 1
    assert summary["reviewed_after_count"] <= summary["reviewed_before_count"]
    assert summary["qa_fail_count"] == 0

    reviewed_df = artifacts["customer_workbook_sheets"]["01_REVIEWED_CORE_METRICS"]
    assert "rating" not in set(reviewed_df["metric"])
    assert "YoY" not in set(reviewed_df["metric"])
    assert "revenue_yoy" in set(artifacts["route_change_df"]["metric_after"])
