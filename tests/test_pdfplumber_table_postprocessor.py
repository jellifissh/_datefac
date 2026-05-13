import pandas as pd

from pdfplumber_table_extractor import build_table_index_dataframe
from pdfplumber_table_postprocessor import (
    diagnose_cross_page_merge_candidates,
    evaluate_pdfplumber_table_quality,
    postprocess_pdfplumber_blocks,
)


def _block(page, table_index, df):
    return {
        "backend": "pdfplumber",
        "page": page,
        "table_index": table_index,
        "df": df,
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "preview": "",
        "confidence": 0.8,
    }


def test_merge_cross_page_key_metrics():
    df1 = pd.DataFrame(
        [
            ["营业收入", "100", "110", "120", "130"],
            ["归属母公司净利润", "10", "12", "13", "15"],
            ["毛利率", "10%", "11%", "12%", "13%"],
            ["ROE", "5%", "6%", "7%", "8%"],
        ],
        columns=["主要财务指标", "2025A", "2026E", "2027E", "2028E"],
    )
    df2 = pd.DataFrame(
        [
            ["每股收益", "1.0", "1.2", "1.3", "1.5"],
            ["P/E", "20", "18", "16", "14"],
            ["P/B", "2.0", "1.8", "1.6", "1.5"],
            ["EV/EBITDA", "10", "9", "8", "7"],
        ],
        columns=["主要财务指标", "2025A", "2026E", "2027E", "2028E"],
    )
    blocks = [_block(1, 1, df1), _block(2, 1, df2)]
    processed = postprocess_pdfplumber_blocks(blocks)
    assert len(processed) == 1
    one = processed[0]
    assert one["business_hint"] == "主要财务指标"
    assert one["sheet_name_hint"] == "主要财务指标"
    assert "p1_t1" in one["source_blocks"]
    assert "p2_t1" in one["source_blocks"]
    assert one["rows"] == 8


def test_do_not_merge_weak_or_non_adjacent():
    df1 = pd.DataFrame([["营业收入", "100"]], columns=["项目", "2025A"])
    df2 = pd.DataFrame([["天气", "晴"]], columns=["字段", "值"])
    blocks = [_block(1, 1, df1), _block(3, 1, df2)]
    processed = postprocess_pdfplumber_blocks(blocks)
    assert len(processed) == 2


def test_index_dataframe_supports_business_hint_and_source_blocks():
    df = pd.DataFrame([["营业收入", "100"]], columns=["项目", "2025A"])
    blocks = [
        {
            "backend": "pdfplumber",
            "page": "1-2",
            "table_index": "1+1",
            "df": df,
            "rows": 1,
            "cols": 2,
            "preview": "营业收入 | 100",
            "confidence": 0.8,
            "business_hint": "主要财务指标",
            "source_blocks": ["p1_t1", "p2_t1"],
        }
    ]
    index_df = build_table_index_dataframe(blocks, ["主要财务指标"])
    assert "business_hint" in index_df.columns
    assert "source_blocks" in index_df.columns
    assert index_df.iloc[0]["business_hint"] == "主要财务指标"
    assert "p1_t1" in index_df.iloc[0]["source_blocks"]


def test_diagnose_cross_page_candidates_extracts_tokens_and_reasons():
    left_df = pd.DataFrame(
        [["营业收入", "100", "110"], ["归母净利润", "10", "12"]],
        columns=["主要财务指标", "2 0 2 5 A", "2 0 2 6 E"],
    )
    right_df = pd.DataFrame(
        [["P/E", "20", "18"], ["资产负债表", "", ""]],
        columns=["主要财务指标", "2025A", "2026E"],
    )
    blocks = [_block(1, 1, left_df), _block(2, 1, right_df)]
    diags = diagnose_cross_page_merge_candidates(blocks)
    assert len(diags) == 1
    row = diags[0]
    assert row["left_block_id"] == "p1_t1"
    assert row["right_block_id"] == "p2_t1"
    assert row["is_adjacent_page"] is True
    assert row["year_overlap_count"] >= 2
    assert "right_looks_like_new_table" in row["blocked_reasons"]


def test_diagnostics_do_not_change_postprocess_result():
    df1 = pd.DataFrame([["营业收入", "100"]], columns=["项目", "2025A"])
    df2 = pd.DataFrame([["P/E", "20"]], columns=["项目", "2025A"])
    blocks = [_block(1, 1, df1), _block(2, 1, df2)]
    before = postprocess_pdfplumber_blocks(blocks)
    _ = diagnose_cross_page_merge_candidates(blocks)
    after = postprocess_pdfplumber_blocks(blocks)
    assert len(before) == len(after)


def test_quality_gate_fails_for_header_only_blocks():
    df1 = pd.DataFrame([["报告日期", "2025-05-01"]], columns=["字段", "值"])
    df2 = pd.DataFrame([["主要财务指标", "2025A", "2026E"]], columns=["A", "B", "C"])
    blocks = [_block(1, 1, df1), _block(1, 2, df2)]
    summary = evaluate_pdfplumber_table_quality(
        blocks,
        config={
            "pdfplumber_min_quality_score": 0.5,
            "pdfplumber_min_valid_tables": 1,
        },
    )
    assert summary["raw_table_count"] == 2
    assert summary["should_use_pdfplumber"] is False
    assert summary["fallback_reason"] != ""


def test_quality_gate_passes_for_multirow_finance_blocks():
    df1 = pd.DataFrame(
        [
            ["营业收入", "100", "110", "120"],
            ["归属母公司净利润", "10", "12", "13"],
            ["毛利率", "10%", "11%", "12%"],
            ["ROE", "5%", "6%", "7%"],
        ],
        columns=["主要财务指标", "2025A", "2026E", "2027E"],
    )
    df2 = pd.DataFrame(
        [
            ["资产总计", "1000", "1100", "1200"],
            ["负债合计", "400", "420", "450"],
            ["净利润", "10", "12", "13"],
        ],
        columns=["项目", "2025A", "2026E", "2027E"],
    )
    blocks = [_block(1, 1, df1), _block(2, 1, df2)]
    summary = evaluate_pdfplumber_table_quality(
        blocks,
        config={
            "pdfplumber_min_quality_score": 0.5,
            "pdfplumber_min_valid_tables": 1,
        },
    )
    assert summary["raw_table_count"] == 2
    assert summary["valid_table_count"] >= 1
    assert summary["quality_score"] >= 0.5
    assert summary["should_use_pdfplumber"] is True
