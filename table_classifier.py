import os
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd


TABLE_TYPE_KEYWORDS = {
    "主要财务指标": [
        "营业收入", "收入同比", "归属母公司净利润", "归母净利润", "净利润同比", "毛利率",
        "ROE", "每股收益", "EPS", "P/E", "P/B", "EV/EBITDA",
    ],
    "资产负债表": [
        "流动资产", "现金", "应收账款", "其他应收款", "预付账款", "存货", "非流动资产",
        "长期投资", "固定资产", "无形资产", "资产总计", "流动负债", "短期借款", "应付账款",
        "非流动负债", "长期借款", "负债合计", "少数股东权益", "股本", "资本公积", "留存收益",
        "归属母公司股东权益", "负债和股东权益",
    ],
    "利润表": [
        "营业收入", "营业成本", "营业税金及附加", "销售费用", "管理费用", "财务费用",
        "资产减值损失", "公允价值变动收益", "投资净收益", "营业利润", "营业外收入",
        "营业外支出", "利润总额", "所得税", "净利润", "少数股东损益", "归属母公司净利润",
        "EBITDA", "EPS",
    ],
    "现金流量表": [
        "经营活动现金流", "投资活动现金流", "筹资活动现金流", "折旧摊销", "投资损失",
        "营运资金变动", "其他经营现金流", "资本支出", "其他投资现金流", "普通股增加",
        "资本公积增加", "其他筹资现金流", "现金净增加额",
    ],
    "财务比率表": [
        "成长能力", "获利能力", "偿债能力", "营运能力", "每股指标", "估值比率", "毛利率",
        "ROE", "ROIC", "资产负债率", "净负债比率", "流动比率", "速动比率", "总资产周转率",
        "应收账款周转率", "应付账款周转率", "每股收益", "每股经营现金流", "每股净资产",
        "P/E", "P/B", "EV/EBITDA",
    ],
}

KEY_METRICS_EXCLUSIVE_KEYWORDS = ["收入同比", "净利润同比", "每股收益", "P/E", "P/B", "EV/EBITDA"]
KEY_METRICS_STRONG_KEYWORDS = ["收入同比", "净利润同比"]
FINANCIAL_RATIO_SECTION_KEYWORDS = ["成长能力", "获利能力", "偿债能力", "营运能力", "每股指标", "估值比率"]
BALANCE_SHEET_CORE_KEYWORDS = ["流动资产", "资产总计", "流动负债", "负债合计", "股本", "负债和股东权益"]
INCOME_STATEMENT_CORE_KEYWORDS = ["营业收入", "营业成本", "营业利润", "利润总额", "净利润", "EPS"]


def _normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _flatten_table_parts(df: pd.DataFrame) -> List[str]:
    parts = [_normalize_text(col) for col in df.columns.tolist()]
    for _, row in df.iterrows():
        parts.extend(_normalize_text(v) for v in row.tolist())
    return [p for p in parts if p]


def _build_match_texts(df: pd.DataFrame) -> Tuple[str, str]:
    full_text = "\n".join(_flatten_table_parts(df))
    no_space_text = "".join(full_text.split())
    return full_text, no_space_text


def _keyword_in_text(keyword: str, full_text: str, no_space_text: str) -> bool:
    normalized_keyword = "".join(keyword.split())
    return keyword in full_text or normalized_keyword in no_space_text


def _first_column_preview(df: pd.DataFrame, limit: int = 3) -> str:
    if df.empty or df.shape[1] == 0:
        return ""
    values = []
    for value in df.iloc[:, 0].tolist():
        text = _normalize_text(value)
        if text:
            values.append(text)
        if len(values) >= limit:
            break
    return ";".join(values)


def _score_keywords(full_text: str, no_space_text: str, keywords: List[str]) -> Dict[str, object]:
    matched = [kw for kw in keywords if _keyword_in_text(kw, full_text, no_space_text)]
    score = min(len(matched) / min(len(keywords), 8), 1.0)
    return {"score": round(score, 4), "matched": matched}


def _safe_preview(text: str, max_len: int = 200) -> str:
    text = text.strip()
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _top_ranked_types(score_map: Dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(score_map.items(), key=lambda item: item[1], reverse=True)


def classify_table(df, table_index=None, logger=None, config=None):
    config = config or {}
    min_confidence = float(config.get("min_confidence", 0.25))
    row_count, col_count = df.shape
    full_text, no_space_text = _build_match_texts(df)

    raw_scores = {
        "主要财务指标": _score_keywords(full_text, no_space_text, TABLE_TYPE_KEYWORDS["主要财务指标"]),
        "资产负债表": _score_keywords(full_text, no_space_text, TABLE_TYPE_KEYWORDS["资产负债表"]),
        "利润表": _score_keywords(full_text, no_space_text, TABLE_TYPE_KEYWORDS["利润表"]),
        "现金流量表": _score_keywords(full_text, no_space_text, TABLE_TYPE_KEYWORDS["现金流量表"]),
        "财务比率表": _score_keywords(full_text, no_space_text, TABLE_TYPE_KEYWORDS["财务比率表"]),
    }

    key_metrics_exclusive_hits = [kw for kw in KEY_METRICS_EXCLUSIVE_KEYWORDS if _keyword_in_text(kw, full_text, no_space_text)]
    strong_key_metrics_hits = [kw for kw in KEY_METRICS_STRONG_KEYWORDS if _keyword_in_text(kw, full_text, no_space_text)]
    ratio_section_hits = [kw for kw in FINANCIAL_RATIO_SECTION_KEYWORDS if _keyword_in_text(kw, full_text, no_space_text)]
    balance_core_hits = [kw for kw in BALANCE_SHEET_CORE_KEYWORDS if _keyword_in_text(kw, full_text, no_space_text)]
    income_core_hits = [kw for kw in INCOME_STATEMENT_CORE_KEYWORDS if _keyword_in_text(kw, full_text, no_space_text)]

    key_metrics_score = raw_scores["主要财务指标"]["score"]
    key_metrics_score = min(
        key_metrics_score
        + 0.08 * len(key_metrics_exclusive_hits)
        + 0.07 * len(strong_key_metrics_hits),
        1.0,
    )

    financial_ratio_score = raw_scores["财务比率表"]["score"]
    if len(ratio_section_hits) >= 3:
        financial_ratio_score = min(financial_ratio_score + 0.2, 1.0)
    elif len(ratio_section_hits) >= 2:
        financial_ratio_score = min(financial_ratio_score + 0.1, 1.0)

    balance_sheet_score = raw_scores["资产负债表"]["score"]
    income_statement_score = raw_scores["利润表"]["score"]
    cashflow_score = raw_scores["现金流量表"]["score"]

    if row_count > 30 and len(key_metrics_exclusive_hits) < 4:
        key_metrics_score = min(key_metrics_score, 0.39)

    if row_count > 30 and (balance_sheet_score >= 0.35 or income_statement_score >= 0.6 or cashflow_score >= 0.35):
        key_metrics_score = min(key_metrics_score, max(balance_sheet_score, income_statement_score, cashflow_score, financial_ratio_score))

    score_map = {
        "主要财务指标": round(key_metrics_score, 4),
        "资产负债表": round(balance_sheet_score, 4),
        "利润表": round(income_statement_score, 4),
        "现金流量表": round(cashflow_score, 4),
        "财务比率表": round(financial_ratio_score, 4),
    }

    ranked = _top_ranked_types(score_map)
    top1_type, top1_score = ranked[0]
    top2_type, top2_score = ranked[1]
    top3_type, top3_score = ranked[2]

    mixed_condition_a = balance_sheet_score >= 0.4 and income_statement_score >= 0.4
    mixed_condition_b = sum(1 for s in (balance_sheet_score, income_statement_score, cashflow_score) if s >= 0.35) >= 2
    mixed_condition_c = len(balance_core_hits) >= 2 and len(income_core_hits) >= 2

    final_type = top1_type
    final_score = top1_score
    matched = raw_scores[top1_type]["matched"] if top1_type in raw_scores else []
    classification_reason = "highest score"

    if row_count <= 30 and key_metrics_score >= max(financial_ratio_score, balance_sheet_score, income_statement_score, cashflow_score):
        final_type = "主要财务指标"
        final_score = key_metrics_score
        matched = raw_scores["主要财务指标"]["matched"]
        classification_reason = "key metrics strong with exclusive keywords"
    elif len(ratio_section_hits) >= 3 and abs(financial_ratio_score - key_metrics_score) <= 0.15:
        final_type = "财务比率表"
        final_score = financial_ratio_score
        matched = raw_scores["财务比率表"]["matched"]
        classification_reason = "financial ratio section keywords matched"
    elif len(ratio_section_hits) >= 3 and financial_ratio_score >= max(balance_sheet_score, income_statement_score, cashflow_score):
        final_type = "财务比率表"
        final_score = financial_ratio_score
        matched = raw_scores["财务比率表"]["matched"]
        classification_reason = "financial ratio section keywords matched"
    elif row_count > 30 and (mixed_condition_a or mixed_condition_b or mixed_condition_c):
        final_type = "财务三表混合表"
        final_score = max(balance_sheet_score, income_statement_score, cashflow_score)
        matched = sorted(set(raw_scores["资产负债表"]["matched"] + raw_scores["利润表"]["matched"] + raw_scores["现金流量表"]["matched"]))
        if mixed_condition_a:
            classification_reason = "mixed financial statements: balance_sheet_score>=0.4 and income_statement_score>=0.4"
        elif mixed_condition_b:
            classification_reason = "mixed financial statements: at least two statement scores >=0.35"
        else:
            classification_reason = "mixed financial statements: core balance and income keywords matched"
    elif top1_type == "财务比率表" and len(ratio_section_hits) >= 2:
        final_type = "财务比率表"
        final_score = financial_ratio_score
        matched = raw_scores["财务比率表"]["matched"]
        classification_reason = "financial ratio section keywords matched"
    elif top1_type == "主要财务指标":
        final_type = "主要财务指标"
        final_score = key_metrics_score
        matched = raw_scores["主要财务指标"]["matched"]
        classification_reason = "key metrics strongest by score"
    elif top1_type == "资产负债表":
        classification_reason = "balance sheet keywords strongest"
    elif top1_type == "利润表":
        classification_reason = "income statement keywords strongest"
    elif top1_type == "现金流量表":
        classification_reason = "cashflow keywords strongest"
    elif top1_type == "财务比率表":
        classification_reason = "financial ratio keywords strongest"

    if final_score < min_confidence:
        final_type = "未知表"
        matched = []
        classification_reason = f"top score below min_confidence({min_confidence})"

    result = {
        "table_index": table_index,
        "table_type": final_type,
        "confidence": round(final_score, 4),
        "top1_type": top1_type,
        "top1_score": round(top1_score, 4),
        "top2_type": top2_type,
        "top2_score": round(top2_score, 4),
        "top3_type": top3_type,
        "top3_score": round(top3_score, 4),
        "row_count": row_count,
        "col_count": col_count,
        "classification_reason": classification_reason,
        "matched_keywords": ",".join(matched),
        "shape": f"{row_count}x{col_count}",
        "first_column_preview": _safe_preview(_first_column_preview(df)),
        "key_metrics_score": round(key_metrics_score, 4),
        "balance_sheet_score": round(balance_sheet_score, 4),
        "income_statement_score": round(income_statement_score, 4),
        "cashflow_score": round(cashflow_score, 4),
        "financial_ratio_score": round(financial_ratio_score, 4),
    }

    if logger and config.get("log_detail", True):
        logger.info(
            "TableClassifier: table_index=%s table_type=%s confidence=%.4f top1=%s(%.4f) top2=%s(%.4f) top3=%s(%.4f) reason=%s matched_keywords=%s scores={main=%.4f,balance=%.4f,income=%.4f,cash=%.4f,ratio=%.4f}",
            table_index,
            result["table_type"],
            result["confidence"],
            result["top1_type"],
            result["top1_score"],
            result["top2_type"],
            result["top2_score"],
            result["top3_type"],
            result["top3_score"],
            result["classification_reason"],
            result["matched_keywords"],
            result["key_metrics_score"],
            result["balance_sheet_score"],
            result["income_statement_score"],
            result["cashflow_score"],
            result["financial_ratio_score"],
        )
    return result


def classify_tables(df_list, logger=None, config=None):
    config = config or {}
    results = [classify_table(df, table_index=idx, logger=logger, config=config) for idx, df in enumerate(df_list)]
    if logger and not config.get("log_detail", True):
        logger.info("TableClassifier summary: table_count=%s", len(results))
    return results


def export_classification_report(results, pkg_path, save_excel_func, logger=None):
    report_df = pd.DataFrame(results)
    target_path = f"{pkg_path}\\04_表格分类结果.xlsx"

    final_path = target_path
    if os.path.exists(target_path):
        try:
            with open(target_path, "a"):
                pass
        except PermissionError:
            timestamp = datetime.now().strftime("%H%M%S")
            final_path = target_path.replace(".xlsx", f"_副本_{timestamp}.xlsx")

    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        report_df.to_excel(writer, sheet_name="表格分类结果", index=False)
    if logger:
        logger.info("表格分类报告输出: %s", final_path)
    return final_path
