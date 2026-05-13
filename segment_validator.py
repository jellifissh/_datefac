from typing import Dict, List, Optional

import pandas as pd


TYPE_ALIASES = {
    "主要财务指标": ["主要财务指标", "关键指标", "key metrics"],
    "资产负债表": ["资产负债表", "balance sheet"],
    "利润表": ["利润表", "income statement", "损益表"],
    "现金流量表": ["现金流量表", "cash flow"],
    "财务比率表": ["财务比率表", "主要财务比率", "财务比率", "ratio"],
}

DETECT_KEYWORDS = {
    "主要财务指标": ["收入同比", "净利润同比", "毛利率", "ROE", "每股收益", "P/E", "P/B", "EV/EBITDA"],
    "资产负债表": ["流动资产", "应收账款", "资产总计", "负债合计", "所有者权益"],
    "利润表": ["营业收入", "营业成本", "营业利润", "利润总额", "所得税", "净利润"],
    "现金流量表": ["经营活动现金流", "投资活动现金流", "筹资活动现金流", "资本支出", "现金净增加额"],
    "财务比率表": ["成长能力", "获利能力", "偿债能力", "营运能力", "每股指标", "估值比率", "P/E", "P/B", "EV/EBITDA"],
}

POLLUTION_KEYWORDS = {
    "资产负债表": ["P/E", "P/B", "EV/EBITDA", "毛利率", "ROE", "每股收益"],
    "现金流量表": ["流动资产", "应收账款", "资产总计", "负债合计", "所有者权益"],
    "利润表": ["资产总计", "负债合计", "经营活动现金流", "投资活动现金流", "筹资活动现金流"],
    "财务比率表": ["资产总计", "负债合计", "经营活动现金流", "投资活动现金流"],
}

TRIPLE_STATEMENT_KEYWORDS = [
    "资产总计",
    "负债合计",
    "所有者权益",
    "营业收入",
    "营业利润",
    "经营活动现金流",
    "投资活动现金流",
    "筹资活动现金流",
]


def _normalize(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _flatten_text(df: pd.DataFrame) -> str:
    parts: List[str] = []
    parts.extend(_normalize(c) for c in df.columns.tolist())
    for _, row in df.iterrows():
        parts.extend(_normalize(v) for v in row.tolist())
    return "\n".join([p for p in parts if p])


def _safe_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 5, max_len: int = 200) -> str:
    if df is None or df.empty:
        return ""
    sub = df.iloc[:max_rows, :max_cols]
    text = " | ".join([" / ".join([_normalize(v) for v in row]) for row in sub.values.tolist()])
    return text[:max_len]


def _detect_type(full_text: str) -> (str, float, Dict[str, int]):
    score_map: Dict[str, int] = {}
    for table_type, keywords in DETECT_KEYWORDS.items():
        score_map[table_type] = sum(1 for kw in keywords if kw in full_text)
    sorted_scores = sorted(score_map.items(), key=lambda kv: kv[1], reverse=True)
    top_type, top_score = sorted_scores[0]
    total = sum(score_map.values())
    confidence = 0.0 if total == 0 else round(top_score / total, 4)
    if top_score == 0:
        return "未识别", 0.0, score_map
    return top_type, confidence, score_map


def _type_from_name(name: str) -> str:
    name_l = _normalize(name).lower()
    for table_type, aliases in TYPE_ALIASES.items():
        for alias in aliases:
            if alias.lower() in name_l:
                return table_type
    return ""


def _type_from_classification(classification_item: Optional[dict]) -> str:
    if not isinstance(classification_item, dict):
        return ""
    candidates = [
        classification_item.get("table_type", ""),
        classification_item.get("top1_type", ""),
        classification_item.get("detected_type", ""),
    ]
    for value in candidates:
        t = _type_from_name(_normalize(value))
        if t:
            return t
        if _normalize(value) in TYPE_ALIASES:
            return _normalize(value)
    return ""


def _expected_type(
    idx: int,
    sheet_name: str,
    segment_metadata: Optional[List[dict]],
    classification_results: Optional[List[dict]],
    detected_type: str,
) -> str:
    from_sheet = _type_from_name(sheet_name)
    if from_sheet:
        return from_sheet

    if isinstance(segment_metadata, list) and idx < len(segment_metadata):
        meta = segment_metadata[idx] or {}
        for key in ("sheet_name", "segment_type", "table_type", "business_type"):
            t = _type_from_name(_normalize(meta.get(key, "")))
            if t:
                return t

    if isinstance(classification_results, list) and idx < len(classification_results):
        t = _type_from_classification(classification_results[idx])
        if t:
            return t

    return detected_type


def validate_segments(
    dfs,
    sheet_names=None,
    classification_results=None,
    segment_metadata=None,
    logger=None,
    config=None,
):
    config = config or {}
    threshold = int(config.get("pollution_warning_threshold", 2) or 2)
    rows = []
    for idx, df in enumerate(dfs or []):
        sheet_name = sheet_names[idx] if sheet_names and idx < len(sheet_names) else f"Sheet_{idx+1}"
        full_text = _flatten_text(df)
        detected_type, confidence, score_map = _detect_type(full_text)
        expected_type = _expected_type(idx, sheet_name, segment_metadata, classification_results, detected_type)

        pollution_flags: List[str] = []
        suspicious_keywords: List[str] = []
        pollution_score = 0

        if expected_type in POLLUTION_KEYWORDS:
            hits = [kw for kw in POLLUTION_KEYWORDS[expected_type] if kw in full_text]
            if hits:
                suspicious_keywords.extend(hits)
                pollution_flags.append("keyword_pollution")
                pollution_score += len(hits)

        if expected_type == "主要财务指标":
            statement_hits = [kw for kw in TRIPLE_STATEMENT_KEYWORDS if kw in full_text]
            if len(statement_hits) >= 4:
                suspicious_keywords.extend(statement_hits)
                pollution_flags.append("suspicious_mixed_financial_statement")
                pollution_score += 2

        if expected_type and detected_type != "未识别" and expected_type != detected_type:
            pollution_flags.append("type_conflict")
            pollution_score += 1

        suggested_action = "正常"
        if "type_conflict" in pollution_flags:
            suggested_action = "建议复核：sheet 类型与内容关键词冲突"
        if pollution_score >= threshold:
            suggested_action = "建议复核：疑似混入其他财务表内容"

        row = {
            "sheet_index": idx,
            "sheet_name": sheet_name,
            "expected_type": expected_type or "未识别",
            "detected_type": detected_type,
            "confidence": confidence,
            "row_count": int(df.shape[0]),
            "col_count": int(df.shape[1]),
            "pollution_score": pollution_score,
            "pollution_flags": ",".join(sorted(set(pollution_flags))),
            "suspicious_keywords": ",".join(sorted(set(suspicious_keywords))),
            "suggested_action": suggested_action,
        }
        rows.append(row)

        if logger and config.get("log_detail", True):
            logger.info(
                "SegmentValidation: idx=%s sheet=%s expected=%s detected=%s confidence=%.4f pollution_score=%s flags=%s keyword_scores=%s",
                idx,
                sheet_name,
                row["expected_type"],
                detected_type,
                confidence,
                pollution_score,
                row["pollution_flags"],
                score_map,
            )

    return pd.DataFrame(rows)
