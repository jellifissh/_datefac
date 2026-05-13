import pandas as pd

from table_classifier import classify_table


def test_classify_key_metrics_table():
    df = pd.DataFrame(
        [
            ["营业收入", "4641", "5110", "7410", "9260"],
            ["归属母公司净利润", "347", "476", "867", "1189"],
            ["毛利率", "13.9%", "17.4%", "20.1%", "20.3%"],
            ["ROE", "6.0%", "7.7%", "12.4%", "14.8%"],
            ["P/E", "50.58", "28.41", "15.59", "11.38"],
        ],
        columns=["主要财务指标", "2025A", "2026E", "2027E", "2028E"],
    )
    assert classify_table(df)["table_type"] == "主要财务指标"


def test_classify_balance_sheet():
    df = pd.DataFrame(
        [
            ["流动资产", "100"],
            ["应收账款", "50"],
            ["资产总计", "200"],
            ["流动负债", "80"],
            ["负债合计", "120"],
            ["股本", "20"],
            ["负债和股东权益", "200"],
        ],
        columns=["资产负债表", "2025A"],
    )
    assert classify_table(df)["table_type"] == "资产负债表"


def test_classify_income_statement():
    df = pd.DataFrame(
        [
            ["营业收入", "100"],
            ["营业成本", "60"],
            ["销售费用", "10"],
            ["管理费用", "8"],
            ["营业利润", "15"],
            ["净利润", "12"],
            ["EPS", "1.2"],
        ],
        columns=["利润表", "2025A"],
    )
    assert classify_table(df)["table_type"] == "利润表"


def test_classify_cashflow_statement():
    df = pd.DataFrame(
        [
            ["经营活动现金流", "100"],
            ["投资活动现金流", "-50"],
            ["筹资活动现金流", "20"],
            ["折旧摊销", "5"],
            ["资本支出", "10"],
            ["现金净增加额", "70"],
        ],
        columns=["现金流量表", "2025A"],
    )
    assert classify_table(df)["table_type"] == "现金流量表"


def test_classify_financial_ratio_table():
    df = pd.DataFrame(
        [
            ["成长能力", ""],
            ["ROE", "15%"],
            ["ROIC", "10%"],
            ["资产负债率", "45%"],
            ["流动比率", "1.5"],
            ["每股净资产", "8.0"],
            ["P/E", "18"],
        ],
        columns=["财务比率表", "2025A"],
    )
    assert classify_table(df)["table_type"] == "财务比率表"


def test_classify_unknown_table():
    df = pd.DataFrame(
        [
            ["天气", "晴"],
            ["城市", "上海"],
            ["温度", "26"],
        ],
        columns=["字段", "值"],
    )
    assert classify_table(df, config={"min_confidence": 0.25})["table_type"] == "未知表"


def test_classification_does_not_modify_dataframe():
    df = pd.DataFrame(
        [
            ["营业收入", "100"],
            ["净利润", "10"],
        ],
        columns=["项目", "2025A"],
    )
    before = df.copy(deep=True)
    classify_table(df)
    assert df.equals(before)


def test_large_mixed_financial_table_not_key_metrics():
    rows = [
        ["流动资产", "100"], ["资产总计", "200"], ["流动负债", "80"], ["负债合计", "120"],
        ["股本", "20"], ["负债和股东权益", "200"], ["营业收入", "100"], ["营业成本", "60"],
        ["营业利润", "15"], ["净利润", "12"], ["EPS", "1.2"],
    ]
    rows.extend([[f"扩展行{i}", str(i)] for i in range(25)])
    df = pd.DataFrame(rows, columns=["项目", "2025A"])
    assert classify_table(df)["table_type"] == "财务三表混合表"


def test_small_key_metrics_table_still_classifies_as_key_metrics():
    df = pd.DataFrame(
        [
            ["营业收入", "4641"],
            ["收入同比", "10.1%"],
            ["归属母公司净利润", "347"],
            ["净利润同比", "37.2%"],
            ["毛利率", "13.9%"],
            ["ROE", "6.0%"],
            ["P/E", "28.4"],
            ["P/B", "2.1"],
            ["EV/EBITDA", "15.3"],
        ],
        columns=["主要财务指标", "2025A"],
    )
    assert classify_table(df)["table_type"] == "主要财务指标"


def test_financial_ratio_priority():
    df = pd.DataFrame(
        [
            ["成长能力", ""],
            ["获利能力", ""],
            ["偿债能力", ""],
            ["营运能力", ""],
            ["每股指标", ""],
            ["估值比率", ""],
            ["ROE", "15%"],
            ["P/E", "18"],
        ],
        columns=["财务比率表", "2025A"],
    )
    assert classify_table(df)["table_type"] == "财务比率表"


def test_space_broken_keyword_matching():
    df = pd.DataFrame(
        [
            ["营 业 收 入", "100"],
            ["归 属 母 公 司 净 利 润", "10"],
            ["E V / E B I T D A", "5"],
        ],
        columns=["主 要 财 务 指 标", "2025A"],
    )
    result = classify_table(df, config={"min_confidence": 0.1})
    assert result["table_type"] != "未知表"
    assert result["matched_keywords"] or result["top1_score"] > 0
