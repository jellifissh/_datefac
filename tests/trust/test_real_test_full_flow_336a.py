from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.real_test_full_flow_336a import (  # noqa: E402
    BLOCKED_DECISION,
    READY_DECISION,
    build_real_test_full_flow_336a,
)


def _fake_page_texts(_: Path):
    return (
        {
            1: "营业收入 2024A 120亿元 2025E 140亿元 净利率 18%",
            2: "投资评级 买入 股票代码 600000 股票名称 测试公司",
        },
        [],
        2,
    )


def _fake_extraction(pdf_path: str, pages="all", logger=None, config=None):
    del pages, logger, config
    if pdf_path.endswith("broken.pdf"):
        raise RuntimeError("simulated extractor failure")
    import pandas as pd

    return [
        {
            "page": 1,
            "table_index": 1,
            "df": pd.DataFrame(
                [
                    ["指标", "2024A", "2025E"],
                    ["营业收入", "120亿元", "140亿元"],
                    ["净利率", "18%", "19%"],
                    ["投资评级", "买入", ""],
                ]
            ),
        },
        {
            "page": 2,
            "table_index": 1,
            "df": pd.DataFrame(
                [
                    ["字段", "值"],
                    ["股票代码", "600000"],
                    ["股票名称", "测试公司"],
                ]
            ),
        },
        {
            "page": 2,
            "table_index": 2,
            "df": pd.DataFrame(
                [
                    ["指标", "当前值", "预测值"],
                    ["净利率", "18", "19"],
                ]
            ),
        },
    ]


def test_build_real_test_full_flow_336a_ready(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    input_dir.mkdir()
    (input_dir / "one.pdf").write_bytes(b"%PDF-1.4 test")
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    artifacts = build_real_test_full_flow_336a(
        input_pdf_dir=input_dir,
        output_dir=output_dir,
        extraction_fn=_fake_extraction,
        page_text_fn=_fake_page_texts,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["pdf_found_count"] == 1
    assert summary["pdf_processed_count"] == 1
    assert summary["reviewed_count"] >= 2
    assert summary["needs_review_count"] >= 1
    assert summary["qa_fail_count"] == 0

    reviewed_df = artifacts["reviewed_df"]
    needs_review_df = artifacts["needs_review_df"]
    trace_df = artifacts["source_trace_df"]
    assert list(reviewed_df.columns) == [
        "row_no",
        "document",
        "metric",
        "metric_display_zh",
        "year",
        "value",
        "unit",
        "source_page",
        "status",
        "source_evidence_excerpt",
        "notes",
    ]
    assert "routing_reason" not in reviewed_df.columns
    assert len(trace_df) == summary["reviewed_count"] + summary["needs_review_count"] + summary["rejected_or_excluded_count"]
    assert not needs_review_df.empty
    assert artifacts["qa_json"]["blocked_reasons"] == []


def test_build_real_test_full_flow_336a_blocked_when_no_pdfs(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    input_dir.mkdir()
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    artifacts = build_real_test_full_flow_336a(
        input_pdf_dir=input_dir,
        output_dir=output_dir,
        extraction_fn=_fake_extraction,
        page_text_fn=_fake_page_texts,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    assert artifacts["summary"]["decision"] == BLOCKED_DECISION
    assert artifacts["summary"]["pdf_found_count"] == 0
    assert artifacts["qa_json"]["blocked_reasons"]
