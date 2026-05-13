import logging

import pandas as pd

from table_cleaner import clean_cell, clean_dataframe, clean_dataframe_list, deduplicate_tables


def test_clean_cell_basic():
    assert "<br>" not in clean_cell("0<br>0")
    assert "<b>" not in clean_cell("<b>Ж</b> .")
    assert clean_cell("  营业收入   ") == "营业收入"
    assert clean_cell(None) == ""


def test_drop_empty_rows_and_cols():
    df = pd.DataFrame(
        [
            ["营业收入", "4641", ""],
            ["", "", ""],
            ["净利润", "347", ""],
        ],
        columns=["项目", "2025A", "空列"],
    )
    cleaned = clean_dataframe(df)
    assert "空列" not in cleaned.columns
    assert cleaned.shape[0] == 2
    assert "营业收入" in cleaned.iloc[:, 0].tolist()


def test_remove_repeated_header_row():
    columns = ["会计年度", "2025A", "2026E", "2027E", "2028E"]
    df = pd.DataFrame(
        [
            ["营业收入", "4641", "5110", "7410", "9260"],
            ["会计年度", "2025A", "2026E", "2027E", "2028E"],
            ["净利润", "347", "476", "867", "1189"],
        ],
        columns=columns,
    )
    cleaned = clean_dataframe(df)
    rows = cleaned.iloc[:, 0].tolist()
    assert rows.count("会计年度") == 0


def test_remove_noise_rows():
    df = pd.DataFrame(
        [
            ["£il", "淵", "丰", ""],
            ["ויית", "/P3", "<b>Ж</b> .", ""],
            ["营业收入", "4641", "5110", "7410"],
        ],
        columns=["项目", "2025A", "2026E", "2027E"],
    )
    cleaned = clean_dataframe(df)
    first_col = cleaned.iloc[:, 0].tolist()
    assert "营业收入" in first_col
    assert "£il" not in first_col
    assert "ויית" not in first_col


def test_keep_financial_group_rows():
    df = pd.DataFrame(
        [
            ["成长能力", "", "", ""],
            ["获利能力", "", "", ""],
            ["偿债能力", "", "", ""],
            ["单位:百万元", "", "", ""],
            ["营业收入", "4641", "5110", "7410"],
        ],
        columns=["项目", "2025A", "2026E", "2027E"],
    )
    cleaned = clean_dataframe(df)
    first_col = cleaned.iloc[:, 0].tolist()
    assert "成长能力" in first_col
    assert "获利能力" in first_col
    assert "偿债能力" in first_col
    assert "单位:百万元" in first_col


def test_strict_deduplicate_tables():
    df1 = pd.DataFrame([["营业收入", "4641"]], columns=["项目", "2025A"])
    df2 = pd.DataFrame([["营业收入", "4641"]], columns=["项目", "2025A"])
    deduped = deduplicate_tables([df1, df2])
    assert len(deduped) == 1


def test_keep_major_financial_table_rows():
    df = pd.DataFrame(
        [
            ["营业收入", "4641", "5110", "7410", "9260"],
            ["归属母公司净利润", "347", "476", "867", "1189"],
            ["毛利率 (%)", "13.9%", "17.4%", "20.1%", "20.3%"],
            ["ROE (%)", "6.0%", "7.7%", "12.4%", "14.8%"],
        ],
        columns=["主要财务指标", "2025A", "2026E", "2027E", "2028E"],
    )
    cleaned = clean_dataframe(df)
    rows = cleaned.iloc[:, 0].tolist()
    assert "营业收入" in rows
    assert "归属母公司净利润" in rows
    assert "毛利率 (%)" in rows
    assert "ROE (%)" in rows


def test_disable_strict_dedup_only_cleans():
    df1 = pd.DataFrame([["营业收入", "4641"]], columns=["项目", "2025A"])
    df2 = pd.DataFrame([["营业收入", "4641"]], columns=["项目", "2025A"])
    result = clean_dataframe_list(
        [df1, df2],
        table_cleaning_config={"enabled": True, "strict_dedup": False, "log_detail": False},
    )
    assert len(result) == 2


def test_explain_flag_does_not_change_result():
    df = pd.DataFrame(
        [
            ["营业收入", "4641", "5110", "7410", "9260"],
            ["会计年度", "2025A", "2026E", "2027E", "2028E"],
            ["净利润", "347", "476", "867", "1189"],
        ],
        columns=["会计年度", "2025A", "2026E", "2027E", "2028E"],
    )
    cleaned_false = clean_dataframe(df, table_cleaning_config={"explain": False})
    cleaned_true = clean_dataframe(df, table_cleaning_config={"explain": True})
    assert cleaned_false.equals(cleaned_true)


def test_explain_sample_limit_does_not_change_result():
    df = pd.DataFrame(
        [
            ["£il", "淵", "丰", ""],
            ["ויית", "/P3", "<b>Ж</b> .", ""],
            ["营业收入", "4641", "5110", "7410"],
        ],
        columns=["项目", "2025A", "2026E", "2027E"],
    )
    cleaned_1 = clean_dataframe(df, table_cleaning_config={"explain": True, "explain_sample_limit": 1})
    cleaned_20 = clean_dataframe(df, table_cleaning_config={"explain": True, "explain_sample_limit": 20})
    assert cleaned_1.equals(cleaned_20)


def test_duplicate_table_log_reason_with_caplog(caplog):
    df1 = pd.DataFrame([["营业收入", "4641"]], columns=["项目", "2025A"])
    df2 = pd.DataFrame([["营业收入", "4641"]], columns=["项目", "2025A"])
    logger = logging.getLogger("table_cleaner_test")
    with caplog.at_level(logging.INFO, logger="table_cleaner_test"):
        deduped = deduplicate_tables(
            [df1, df2],
            logger=logger,
            table_cleaning_config={"explain": True},
        )
    assert len(deduped) == 1
    assert "duplicate_table_fingerprint" in caplog.text
