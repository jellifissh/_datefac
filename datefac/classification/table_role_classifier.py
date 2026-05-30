from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class TableRoleResult:
    role: str
    reason: str
    confidence: str
    signal_hits: List[str]
    is_core_signal: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "reason": self.reason,
            "confidence": self.confidence,
            "signal_hits": self.signal_hits,
            "is_core_signal": self.is_core_signal,
        }


PRIORITY_RULES: List[Tuple[str, List[str], str]] = [
    (
        "DISCLAIMER_OR_LEGAL",
        ["免责声明", "重要声明", "分析师声明", "免责"],
        "high",
    ),
    (
        "RATING_STANDARD",
        ["投资评级标准", "优于大市", "弱于大市", "评级标准", "买入", "增持", "中性", "减持", "卖出"],
        "high",
    ),
    (
        "CORE_METRIC_TABLE",
        [
            "盈利预测和财务指标",
            "关键财务与估值指标",
            "财务预测与估值",
            "主要财务指标",
            "核心财务指标",
            "每股收益",
            "eps",
            "roe",
            "p/e",
            "pe",
            "p/b",
            "pb",
            "ev/ebitda",
            "市盈率",
            "市净率",
            "净资产收益率",
            "每股净资产",
            "每股红利",
            "收入增长",
            "净利润增长率",
        ],
        "high",
    ),
    (
        "FINANCIAL_FORECAST_VALUATION",
        ["财务预测与估值", "盈利预测", "估值指标", "关键财务与估值指标"],
        "high",
    ),
    (
        "BALANCE_SHEET",
        ["资产负债表", "资产总计", "负债合计", "股东权益", "流动资产合计", "流动负债合计"],
        "medium",
    ),
    (
        "CASH_FLOW_STATEMENT",
        ["现金流量表", "经营活动现金流", "投资活动现金流", "融资活动现金流", "现金净变动", "企业自由现金流"],
        "medium",
    ),
    (
        "INCOME_STATEMENT",
        ["利润表", "营业收入", "营业成本", "营业利润", "利润总额", "归属于母公司净利润", "所得税费用"],
        "medium",
    ),
    (
        "BUSINESS_ASSUMPTION",
        ["主营业务假设", "正面银浆业务", "空白掩模版业务", "其他主营业务", "毛利润", "毛利率", "同比增长率"],
        "medium",
    ),
    (
        "BASIC_DATA",
        ["基础数据", "收盘价", "总市值", "市值", "换手率"],
        "low",
    ),
]


def classify_table_role(
    caption: str,
    nearby_text: str,
    table_html_preview: str = "",
    md_nearby_lines: str = "",
    file_context: str = "",
    page_context: str = "",
) -> TableRoleResult:
    text = " ".join([caption or "", nearby_text or "", table_html_preview or "", md_nearby_lines or "", file_context or "", page_context or ""]).lower()

    hits: List[Tuple[str, str, str]] = []
    for role, words, conf in PRIORITY_RULES:
        for w in words:
            if w.lower() in text:
                hits.append((role, w, conf))

    if not hits:
        return TableRoleResult(
            role="UNKNOWN_TABLE",
            reason="no_keyword_matched",
            confidence="low",
            signal_hits=[],
            is_core_signal=False,
        )

    role_order = {r: i for i, (r, _, _) in enumerate(PRIORITY_RULES)}
    hits.sort(key=lambda x: role_order.get(x[0], 999))
    top_role = hits[0][0]
    role_hits = [h[1] for h in hits if h[0] == top_role]
    conf = hits[0][2]
    is_core = top_role in {"CORE_METRIC_TABLE", "FINANCIAL_FORECAST_VALUATION"}
    reason = f"matched:{'|'.join(role_hits[:6])}"
    return TableRoleResult(
        role=top_role,
        reason=reason,
        confidence=conf,
        signal_hits=role_hits,
        is_core_signal=is_core,
    )

