import pandas as pd

from financial_standardizer import standardize_core_financials


def test_year_column_recognition_and_extraction():
    df = pd.DataFrame(
        [
            ["营业收入", "4641", "5110", "7410", "9260"],
        ],
        columns=["主要财务指标", "2025A", "2026E", "2027E", "2028E"],
    )
    result = standardize_core_financials([df])
    wide_df = result["wide_df"]
    assert "2025A" in wide_df.columns
    assert "2026E" in wide_df.columns
    assert "2027E" in wide_df.columns
    assert "2028E" in wide_df.columns


def test_extract_all_core_metrics():
    df = pd.DataFrame(
        [
            ["营业收入", "4641", "5110", "7410", "9260"],
            ["归属母公司净利润", "347", "476", "867", "1189"],
            ["毛利率 (%)", "13.9%", "17.4%", "20.1%", "20.3%"],
            ["ROE (%)", "6.0%", "7.7%", "12.4%", "14.8%"],
            ["每股收益", "1.60", "2.19", "3.99", "5.47"],
            ["P/E", "50.58", "28.41", "15.59", "11.38"],
            ["P/B", "3.06", "2.18", "1.94", "1.68"],
            ["EV/EBITDA", "30.27", "15.35", "10.35", "7.99"],
        ],
        columns=["主要财务指标", "2025A", "2026E", "2027E", "2028E"],
    )
    result = standardize_core_financials([df])
    wide_df = result["wide_df"]
    metrics = set(wide_df["指标"].tolist())
    assert "营业收入" in metrics
    assert "归属母公司净利润" in metrics
    assert "毛利率" in metrics
    assert "ROE" in metrics
    assert "每股收益" in metrics
    assert "P/E" in metrics
    assert "P/B" in metrics
    assert "EV/EBITDA" in metrics


def test_do_not_mis_match_yoy_rows():
    df = pd.DataFrame(
        [
            ["收入同比", "10.1%", "8.0%"],
            ["净利润同比", "20.0%", "18.0%"],
        ],
        columns=["主要财务指标", "2025A", "2026E"],
    )
    result = standardize_core_financials([df])
    detail_df = result["detail_df"]
    assert detail_df.empty


def test_eps_and_pe_pb_synonyms():
    df = pd.DataFrame(
        [
            ["EPS(元)", "1.60", "2.19"],
            ["PE", "50.58", "28.41"],
            ["PB", "3.06", "2.18"],
        ],
        columns=["指标", "2025A", "2026E"],
    )
    result = standardize_core_financials([df])
    wide_df = result["wide_df"].set_index("指标")
    assert wide_df.loc["每股收益", "2025A"] == "1.60"
    assert wide_df.loc["P/E", "2025A"] == "50.58"
    assert wide_df.loc["P/B", "2025A"] == "3.06"


def test_conflict_priority_prefers_key_metrics_table():
    df_mixed = pd.DataFrame(
        [
            ["营业收入", "999", "1000"],
        ],
        columns=["项目", "2025A", "2026E"],
    )
    df_key_metrics = pd.DataFrame(
        [
            ["营业收入", "4641", "5110"],
        ],
        columns=["主要财务指标", "2025A", "2026E"],
    )
    classifications = [
        {"table_index": 0, "table_type": "财务三表混合表"},
        {"table_index": 1, "table_type": "主要财务指标"},
    ]
    result = standardize_core_financials([df_mixed, df_key_metrics], classification_results=classifications)
    wide_df = result["wide_df"].set_index("指标")
    detail_df = result["detail_df"]
    assert wide_df.loc["营业收入", "2025A"] == "4641"
    assert wide_df.loc["营业收入", "来源类型"] == "主要财务指标"
    assert len(detail_df[detail_df["标准指标"] == "营业收入"]) == 2


def test_standardization_does_not_modify_dataframe():
    df = pd.DataFrame(
        [
            ["营业收入", "100"],
            ["归母净利润", "10"],
        ],
        columns=["项目", "2025A"],
    )
    before = df.copy(deep=True)
    standardize_core_financials([df])
    assert df.equals(before)
