import pandas as pd

from table_segmenter import (
    SEG_BALANCE,
    SEG_CASHFLOW,
    SEG_INCOME,
    SEG_MAIN,
    SEG_RATIO,
    build_segment_index_dataframe,
    coalesce_adjacent_segments,
    refine_segments,
    segment_tables,
)


def _base_config(min_rows=1):
    return {
        "enabled": True,
        "apply_to_backend": "marker",
        "min_rows_for_segmentation": min_rows,
        "add_index_sheet": True,
        "log_detail": False,
        "coalesce_enabled": True,
        "coalesce_same_type": True,
        "coalesce_ratio_sections": True,
        "min_rows_for_standalone_segment": 3,
    }


def _collect_types(meta):
    return [m.get("segment_type") for m in meta]


def _df(rows=3):
    return pd.DataFrame([[f"r{i}", str(i)] for i in range(rows)], columns=["item", "v"])


def _meta(sheet_name, seg_type, src, start, end, rows, reason="keyword_cluster", cls_reason="weighted_score"):
    return {
        "sheet_name": sheet_name,
        "segment_type": seg_type,
        "source_table_index": src,
        "start_row": start,
        "end_row": end,
        "rows": rows,
        "cols": 2,
        "reason": reason,
        "confidence": 0.8,
        "preview": "",
        "explicit_title_hits": "",
        "key_metrics_score": 0.0,
        "balance_score": 0.0,
        "income_score": 0.0,
        "cashflow_score": 0.0,
        "ratio_score": 0.0,
        "final_segment_type": seg_type,
        "classification_reason": cls_reason,
        "source_segments": sheet_name,
    }


def test_small_table_no_segmentation():
    df = pd.DataFrame(
        [
            ["会计年度", "2025A", "2026E"],
            ["营业收入", "100", "110"],
            ["净利润", "10", "12"],
        ],
        columns=["项目", "y1", "y2"],
    )
    out_dfs, meta = segment_tables([df], config=_base_config(min_rows=20))
    assert len(out_dfs) == 1
    assert len(meta) == 1
    assert meta[0]["segment_type"] == "未分段"


def test_main_metrics_not_misclassified_as_income():
    df = pd.DataFrame(
        [
            ["主要财务指标", "2025A", "2026E", "2027E", "2028E"],
            ["营业收入", "100", "110", "120", "130"],
            ["收入同比", "10%", "10%", "9%", "8%"],
            ["归属母公司净利润", "10", "12", "14", "16"],
            ["净利润同比", "20%", "18%", "16%", "14%"],
            ["毛利率", "30%", "31%", "32%", "33%"],
            ["ROE", "8%", "9%", "10%", "11%"],
            ["每股收益", "1.0", "1.2", "1.3", "1.5"],
            ["P/E", "20", "18", "16", "14"],
            ["P/B", "2.0", "1.8", "1.6", "1.5"],
            ["EV/EBITDA", "10", "9", "8", "7"],
        ],
        columns=["项目", "c1", "c2", "c3", "c4"],
    )
    _, meta = segment_tables([df], config=_base_config(min_rows=1))
    assert SEG_MAIN in _collect_types(meta)
    assert SEG_INCOME not in _collect_types(meta)


def test_ratio_not_misclassified_as_income():
    df = pd.DataFrame(
        [
            ["财务比率", "2025A", "2026E"],
            ["成长能力", "", ""],
            ["获利能力", "", ""],
            ["偿债能力", "", ""],
            ["营运能力", "", ""],
            ["每股指标", "", ""],
            ["估值比率", "", ""],
            ["ROE", "10%", "11%"],
            ["P/E", "20", "18"],
            ["P/B", "2.0", "1.8"],
        ],
        columns=["项目", "y1", "y2"],
    )
    _, meta = segment_tables([df], config=_base_config(min_rows=1))
    assert SEG_RATIO in _collect_types(meta)
    assert SEG_INCOME not in _collect_types(meta)


def test_cashflow_not_misclassified_by_netprofit_terms():
    df = pd.DataFrame(
        [
            ["现金流量表", "2025A", "2026E"],
            ["经营活动现金流", "10", "11"],
            ["净利润", "5", "6"],
            ["财务费用", "2", "2"],
            ["投资活动现金流", "-3", "-2"],
            ["筹资活动现金流", "1", "1"],
            ["现金净增加额", "8", "9"],
        ],
        columns=["项目", "y1", "y2"],
    )
    _, meta = segment_tables([df], config=_base_config(min_rows=1))
    assert SEG_CASHFLOW in _collect_types(meta)
    assert SEG_INCOME not in _collect_types(meta)


def test_income_still_identified_with_strong_terms():
    df = pd.DataFrame(
        [
            ["利润表", "2025A", "2026E"],
            ["营业收入", "100", "110"],
            ["营业成本", "60", "66"],
            ["销售费用", "10", "11"],
            ["管理费用", "8", "9"],
            ["营业利润", "20", "22"],
            ["利润总额", "18", "20"],
            ["所得税", "3", "3.5"],
            ["净利润", "15", "16.5"],
        ],
        columns=["项目", "y1", "y2"],
    )
    _, meta = segment_tables([df], config=_base_config(min_rows=1))
    assert SEG_INCOME in _collect_types(meta)


def test_mixed_large_table_segments_into_multiple_blocks():
    rows = [
        ["会计年度", "2025A", "2026E"],
        ["流动资产", "100", "110"],
        ["资产总计", "500", "550"],
        ["利润表", "", ""],
        ["营业收入", "200", "230"],
        ["营业成本", "120", "130"],
        ["现金流量表", "", ""],
        ["经营活动现金流", "30", "33"],
        ["现金净增加额", "6", "7"],
        ["财务比率", "", ""],
        ["ROE", "10%", "11%"],
        ["P/E", "20", "18"],
    ]
    df = pd.DataFrame(rows, columns=["项目", "y1", "y2"])
    out_dfs, meta = segment_tables([df], config=_base_config(min_rows=1))
    assert len(out_dfs) >= 3
    index_df = build_segment_index_dataframe(meta)
    for col in [
        "sheet_name",
        "segment_type",
        "explicit_title_hits",
        "key_metrics_score",
        "balance_score",
        "income_score",
        "cashflow_score",
        "ratio_score",
        "final_segment_type",
        "classification_reason",
        "source_segments",
    ]:
        assert col in index_df.columns


def test_coalesce_adjacent_ratio_segments():
    segments = [_df(2), _df(3), _df(4)]
    metas = [
        _meta("财务比率表", SEG_RATIO, 1, 1, 2, 2),
        _meta("财务比率表_2", SEG_RATIO, 1, 3, 5, 3),
        _meta("财务比率表_3", SEG_RATIO, 1, 6, 9, 4),
    ]
    merged_segs, merged_meta = coalesce_adjacent_segments(segments, metas, config=_base_config())
    assert len(merged_segs) == 1
    assert len(merged_meta) == 1
    assert merged_meta[0]["segment_type"] == SEG_RATIO
    assert "coalesced_adjacent_ratio_segments" in merged_meta[0]["reason"]


def test_coalesce_different_types_not_merged():
    segments = [_df(2), _df(3), _df(4)]
    metas = [
        _meta("资产负债表", SEG_BALANCE, 1, 1, 2, 2),
        _meta("利润表", SEG_INCOME, 1, 3, 5, 3),
        _meta("现金流量表", SEG_CASHFLOW, 1, 6, 9, 4),
    ]
    merged_segs, merged_meta = coalesce_adjacent_segments(segments, metas, config=_base_config())
    assert len(merged_segs) == 3
    assert len(merged_meta) == 3


def test_coalesce_title_stub_forward():
    segments = [_df(1), _df(5)]
    metas = [
        _meta("财务比率表", SEG_RATIO, 2, 20, 20, 1, reason="title_row", cls_reason="explicit_title_priority"),
        _meta("财务比率表_2", SEG_RATIO, 2, 21, 25, 5),
    ]
    merged_segs, merged_meta = coalesce_adjacent_segments(segments, metas, config=_base_config())
    assert len(merged_segs) == 1
    assert len(merged_meta) == 1
    assert merged_meta[0]["segment_type"] == SEG_RATIO
    assert "coalesced_title_stub_forward" in merged_meta[0]["reason"]


def test_coalesce_adjacent_balance_segments():
    segments = [_df(3), _df(4)]
    metas = [
        _meta("资产负债表", SEG_BALANCE, 1, 10, 12, 3),
        _meta("资产负债表_2", SEG_BALANCE, 1, 13, 16, 4),
    ]
    merged_segs, merged_meta = coalesce_adjacent_segments(segments, metas, config=_base_config())
    assert len(merged_segs) == 1
    assert len(merged_meta) == 1
    assert merged_meta[0]["segment_type"] == SEG_BALANCE
    assert "coalesced_adjacent_balance_segments" in merged_meta[0]["reason"]


def test_refine_single_row_ev_ebitda_not_standalone_income():
    segments = [_df(1), _df(5)]
    stub = pd.DataFrame([["EV/EBITDA", "10"]], columns=["item", "v"])
    ratio = pd.DataFrame(
        [
            ["成长能力", ""],
            ["获利能力", ""],
            ["ROE", "10%"],
            ["P/E", "20"],
            ["P/B", "2.0"],
        ],
        columns=["item", "v"],
    )
    segments = [stub, ratio]
    metas = [
        _meta("利润表_stub", SEG_INCOME, 1, 73, 73, 1, reason="keyword_cluster", cls_reason="weighted_score"),
        _meta("财务比率表", SEG_RATIO, 1, 48, 72, 5, reason="coalesced_adjacent_ratio_segments", cls_reason="explicit_title_priority"),
    ]
    r_segs, r_meta = refine_segments(segments, metas, config=_base_config())
    assert len(r_segs) == 1
    assert len(r_meta) == 1
    assert r_meta[0]["segment_type"] == SEG_RATIO
    assert "refine_merged_stub_segment" in r_meta[0]["reason"]


def test_refine_deduplicate_similar_income_segments_keep_larger():
    s1 = pd.DataFrame(
        [
            ["营业成本", "60"],
            ["销售费用", "10"],
            ["管理费用", "8"],
            ["营业利润", "20"],
            ["利润总额", "18"],
        ],
        columns=["item", "v"],
    )
    s2 = pd.DataFrame(
        [
            ["营业成本", "60"],
            ["销售费用", "10"],
            ["营业利润", "20"],
        ],
        columns=["item", "v"],
    )
    metas = [
        _meta("利润表", SEG_INCOME, 2, 2, 19, 5),
        _meta("利润表_2", SEG_INCOME, 2, 31, 47, 3),
    ]
    r_segs, r_meta = refine_segments([s1, s2], metas, config=_base_config())
    assert len(r_segs) == 1
    assert len(r_meta) == 1
    assert r_meta[0]["segment_type"] == SEG_INCOME
    assert "deduplicated_similar_segment" in r_meta[0]["reason"]


def test_refine_ratio_completeness_preferred():
    full_ratio = pd.DataFrame(
        [
            ["成长能力", ""],
            ["获利能力", ""],
            ["偿债能力", ""],
            ["营运能力", ""],
            ["每股指标", ""],
            ["估值比率", ""],
            ["ROE", "10%"],
        ],
        columns=["item", "v"],
    )
    weak_ratio = pd.DataFrame(
        [
            ["ROE", "10%"],
            ["P/E", "20"],
        ],
        columns=["item", "v"],
    )
    metas = [
        _meta("财务比率表", SEG_RATIO, 2, 20, 30, 7, reason="coalesced_adjacent_ratio_segments", cls_reason="explicit_title_priority"),
        _meta("财务比率表_2", SEG_RATIO, 2, 48, 72, 2, reason="coalesced_adjacent_ratio_segments", cls_reason="weighted_score"),
    ]
    r_segs, r_meta = refine_segments([full_ratio, weak_ratio], metas, config=_base_config())
    assert len(r_segs) == 1
    assert len(r_meta) == 1
    assert r_meta[0]["segment_type"] == SEG_RATIO


def test_refine_no_cross_type_merge():
    segs = [_df(3), _df(3)]
    metas = [
        _meta("资产负债表", SEG_BALANCE, 1, 10, 12, 3),
        _meta("利润表", SEG_INCOME, 1, 13, 15, 3),
    ]
    r_segs, r_meta = refine_segments(segs, metas, config=_base_config())
    assert len(r_segs) == 2
    assert {m["segment_type"] for m in r_meta} == {SEG_BALANCE, SEG_INCOME}
