import re
from typing import Dict, List, Tuple

import pandas as pd


DEFAULT_SEGMENTATION_CONFIG = {
    "enabled": True,
    "apply_to_backend": "marker",
    "min_rows_for_segmentation": 20,
    "add_index_sheet": True,
    "log_detail": True,
    "coalesce_enabled": True,
    "coalesce_same_type": True,
    "coalesce_ratio_sections": True,
    "min_rows_for_standalone_segment": 3,
}

SEG_MAIN = "主要财务指标"
SEG_BALANCE = "资产负债表"
SEG_INCOME = "利润表"
SEG_CASHFLOW = "现金流量表"
SEG_RATIO = "财务比率表"
SEG_UNKNOWN = "未识别表"
SEG_NO_SPLIT = "未分段"

YEAR_TOKEN_RE = re.compile(r"20\s*\d\s*\d\s*\d\s*[A-Za-z]?")

TITLE_KEYWORDS = {
    SEG_MAIN: ["主要财务指标"],
    SEG_BALANCE: ["资产负债表"],
    SEG_INCOME: ["利润表"],
    SEG_CASHFLOW: ["现金流量表"],
    SEG_RATIO: ["主要财务比率", "财务比率", "成长能力", "获利能力", "偿债能力", "营运能力", "每股指标", "估值比率"],
}

MAIN_METRICS_KEYWORDS = [
    "收入同比",
    "净利润同比",
    "毛利率",
    "roe",
    "每股收益",
    "eps",
    "p/e",
    "pe",
    "p/b",
    "pb",
    "ev/ebitda",
    "evebitda",
]

BALANCE_KEYWORDS = [
    "流动资产",
    "现金",
    "应收账款",
    "其他应收款",
    "预付账款",
    "存货",
    "非流动资产",
    "长期投资",
    "固定资产",
    "无形资产",
    "资产总计",
    "流动负债",
    "短期借款",
    "应付账款",
    "非流动负债",
    "长期借款",
    "负债合计",
    "股本",
    "资本公积",
    "留存收益",
    "归属母公司股东权益",
    "负债和股东权益",
]

INCOME_STRONG_KEYWORDS = [
    "营业成本",
    "营业税金及附加",
    "销售费用",
    "管理费用",
    "资产减值损失",
    "公允价值变动收益",
    "投资净收益",
    "营业利润",
    "营业外收入",
    "营业外支出",
    "利润总额",
    "所得税",
    "ebitda",
]

INCOME_WEAK_KEYWORDS = [
    "营业收入",
    "净利润",
    "归属母公司净利润",
    "财务费用",
    "eps",
]

CASHFLOW_STRONG_KEYWORDS = [
    "经营活动现金流",
    "投资活动现金流",
    "筹资活动现金流",
    "资本支出",
    "现金净增加额",
    "其他经营现金流",
    "其他投资现金流",
    "其他筹资现金流",
]

RATIO_GROUP_KEYWORDS = ["成长能力", "获利能力", "偿债能力", "营运能力", "每股指标", "估值比率"]
RATIO_INDICATOR_KEYWORDS = [
    "roe",
    "roic",
    "资产负债率",
    "净负债比率",
    "流动比率",
    "速动比率",
    "总资产周转率",
    "应收账款周转率",
    "应付账款周转率",
    "每股经营现金流",
    "每股净资产",
    "每股收益",
    "eps",
    "p/e",
    "pe",
    "p/b",
    "pb",
    "ev/ebitda",
    "evebitda",
]


def _normalize_text(text: str) -> str:
    s = str(text or "").strip().lower()
    s = re.sub(r"\s+", "", s)
    return s


def _merge_config(config=None) -> Dict:
    merged = dict(DEFAULT_SEGMENTATION_CONFIG)
    if config:
        merged.update(config)
    return merged


def _safe_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 5, max_len: int = 200) -> str:
    if df is None or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        lines.append(" | ".join(v.strip() for v in row.tolist() if str(v).strip()))
    text = " || ".join(lines).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _row_text(df: pd.DataFrame, row_idx: int) -> str:
    values = df.iloc[row_idx].fillna("").astype(str).tolist()
    return " | ".join(v.strip() for v in values if str(v).strip())


def _extract_year_tokens(text: str) -> List[str]:
    compact = _normalize_text(text)
    tokens = YEAR_TOKEN_RE.findall(compact)
    return sorted(set([re.sub(r"\s+", "", t) for t in tokens]))


def _collect_hits(norm_text: str, keywords: List[str]) -> List[str]:
    hits = []
    for kw in keywords:
        nkw = _normalize_text(kw)
        if nkw and nkw in norm_text:
            hits.append(kw)
    return hits


def _classify_segment_by_text(text: str) -> Dict:
    norm = _normalize_text(text)
    year_tokens = _extract_year_tokens(text)

    title_hits = {seg: _collect_hits(norm, kws) for seg, kws in TITLE_KEYWORDS.items()}
    explicit_title_hits = [f"{seg}:{','.join(hits)}" for seg, hits in title_hits.items() if hits]

    main_hits = _collect_hits(norm, MAIN_METRICS_KEYWORDS)
    balance_hits = _collect_hits(norm, BALANCE_KEYWORDS)
    income_strong_hits = _collect_hits(norm, INCOME_STRONG_KEYWORDS)
    income_weak_hits = _collect_hits(norm, INCOME_WEAK_KEYWORDS)
    cashflow_hits = _collect_hits(norm, CASHFLOW_STRONG_KEYWORDS)
    ratio_group_hits = _collect_hits(norm, RATIO_GROUP_KEYWORDS)
    ratio_indicator_hits = _collect_hits(norm, RATIO_INDICATOR_KEYWORDS)

    has_years = len(year_tokens) >= 2
    key_metrics_combo = (
        has_years
        and (
            len(main_hits) >= 3
            or (
                ("收入同比" in main_hits or "净利润同比" in main_hits)
                and any(x in main_hits for x in ["p/e", "pe", "p/b", "pb", "ev/ebitda", "evebitda"])
            )
        )
    )

    key_metrics_score = 4.0 * len(title_hits[SEG_MAIN]) + 1.4 * len(main_hits) + (0.6 if has_years else 0.0) + (1.5 if key_metrics_combo else 0.0)
    balance_score = 5.0 * len(title_hits[SEG_BALANCE]) + 1.2 * len(balance_hits)
    income_score = 5.0 * len(title_hits[SEG_INCOME]) + 1.5 * len(income_strong_hits) + 0.2 * len(income_weak_hits)
    cashflow_score = 5.0 * len(title_hits[SEG_CASHFLOW]) + 1.6 * len(cashflow_hits)
    ratio_score = 5.0 * len(title_hits[SEG_RATIO]) + 2.2 * len(ratio_group_hits) + 1.0 * len(ratio_indicator_hits)

    final_segment_type = SEG_UNKNOWN
    classification_reason = "score_max"

    if len(ratio_group_hits) >= 2:
        final_segment_type = SEG_RATIO
        classification_reason = "ratio_group_priority"
    elif len(cashflow_hits) >= 2:
        final_segment_type = SEG_CASHFLOW
        classification_reason = "cashflow_strong_priority"
    elif key_metrics_combo:
        final_segment_type = SEG_MAIN
        classification_reason = "main_metrics_combo_priority"
    else:
        explicit_scores = {
            SEG_MAIN: len(title_hits[SEG_MAIN]),
            SEG_BALANCE: len(title_hits[SEG_BALANCE]),
            SEG_INCOME: len(title_hits[SEG_INCOME]),
            SEG_CASHFLOW: len(title_hits[SEG_CASHFLOW]),
            SEG_RATIO: len(title_hits[SEG_RATIO]),
        }
        if max(explicit_scores.values()) > 0:
            final_segment_type = max(explicit_scores.items(), key=lambda kv: kv[1])[0]
            classification_reason = "explicit_title_priority"
        else:
            score_map = {
                SEG_MAIN: key_metrics_score,
                SEG_BALANCE: balance_score,
                SEG_INCOME: income_score,
                SEG_CASHFLOW: cashflow_score,
                SEG_RATIO: ratio_score,
            }
            best_type, best_score = max(score_map.items(), key=lambda kv: kv[1])
            if best_score > 0:
                final_segment_type = best_type
                classification_reason = "weighted_score"

    if final_segment_type == SEG_INCOME and len(income_strong_hits) == 0 and key_metrics_combo:
        final_segment_type = SEG_MAIN
        classification_reason = "income_weak_demoted_to_main_metrics"

    return {
        "explicit_title_hits": "|".join(explicit_title_hits),
        "key_metrics_score": round(key_metrics_score, 4),
        "balance_score": round(balance_score, 4),
        "income_score": round(income_score, 4),
        "cashflow_score": round(cashflow_score, 4),
        "ratio_score": round(ratio_score, 4),
        "final_segment_type": final_segment_type,
        "classification_reason": classification_reason,
    }


def _infer_row_type(row_text: str) -> Tuple[str, int]:
    diag = _classify_segment_by_text(row_text)
    seg = str(diag.get("final_segment_type") or "")
    score_map = {
        SEG_MAIN: float(diag.get("key_metrics_score", 0.0)),
        SEG_BALANCE: float(diag.get("balance_score", 0.0)),
        SEG_INCOME: float(diag.get("income_score", 0.0)),
        SEG_CASHFLOW: float(diag.get("cashflow_score", 0.0)),
        SEG_RATIO: float(diag.get("ratio_score", 0.0)),
    }
    score = int(round(score_map.get(seg, 0.0) * 10))
    return (seg, score) if seg and seg != SEG_UNKNOWN else ("", 0)


def _looks_like_year_header(row_text: str) -> bool:
    years = _extract_year_tokens(row_text)
    return ("会计年度" in row_text or "主要财务指标" in row_text) and len(years) >= 2


def _count_distinct_types(df: pd.DataFrame) -> int:
    types = set()
    for i in range(len(df)):
        seg_type, score = _infer_row_type(_row_text(df, i))
        if seg_type and score > 0:
            types.add(seg_type)
    return len(types)


def _dedupe_anchors(anchors: List[Dict]) -> List[Dict]:
    by_idx: Dict[int, Dict] = {}
    for a in anchors:
        idx = int(a["row_idx"])
        old = by_idx.get(idx)
        if old is None or float(a.get("confidence", 0)) > float(old.get("confidence", 0)):
            by_idx[idx] = a
    return [by_idx[i] for i in sorted(by_idx.keys())]


def _make_unique_sheet_name(base: str, used: Dict[str, int]) -> str:
    name = str(base or "").strip() or SEG_UNKNOWN
    if name not in used:
        used[name] = 1
        return name
    used[name] += 1
    return f"{name}_{used[name]}"


def _segment_single_table(df: pd.DataFrame, source_index: int, config: Dict, logger=None) -> Tuple[List[pd.DataFrame], List[Dict]]:
    row_count = int(df.shape[0])
    min_rows = int(config.get("min_rows_for_segmentation", 20) or 20)
    distinct_type_count = _count_distinct_types(df)
    should_try = row_count >= min_rows or distinct_type_count >= 2

    if logger and config.get("log_detail", True):
        logger.info("TableSegmenter table=%s rows=%s distinct_types=%s should_try=%s", source_index, row_count, distinct_type_count, should_try)

    if not should_try:
        meta = {
            "sheet_name": f"原表_{source_index}",
            "segment_type": SEG_NO_SPLIT,
            "source_table_index": source_index,
            "start_row": 1,
            "end_row": row_count,
            "rows": row_count,
            "cols": int(df.shape[1]),
            "reason": "small_or_single_type",
            "confidence": 1.0,
            "preview": _safe_preview(df),
            "explicit_title_hits": "",
            "key_metrics_score": 0.0,
            "balance_score": 0.0,
            "income_score": 0.0,
            "cashflow_score": 0.0,
            "ratio_score": 0.0,
            "final_segment_type": SEG_NO_SPLIT,
            "classification_reason": "small_or_single_type",
            "source_segments": "",
        }
        return [df], [meta]

    anchors: List[Dict] = []
    active_type = ""
    last_anchor_idx = -999
    for i in range(row_count):
        text = _row_text(df, i)
        seg_type, score = _infer_row_type(text)
        candidate = None
        if score >= 15:
            candidate = {"row_idx": i, "segment_type": seg_type, "reason": "keyword_cluster", "confidence": 0.75}

        diag = _classify_segment_by_text(text)
        if diag.get("classification_reason") == "explicit_title_priority":
            candidate = {"row_idx": i, "segment_type": str(diag.get("final_segment_type") or seg_type or SEG_UNKNOWN), "reason": "title_row", "confidence": 0.95}

        if _looks_like_year_header(text) and i + 1 < row_count:
            lookahead_type, lookahead_score = _infer_row_type(_row_text(df, i + 1))
            if lookahead_type and lookahead_score >= 8:
                candidate = {"row_idx": i, "segment_type": lookahead_type, "reason": "year_header_switch", "confidence": 0.7}

        if not candidate:
            continue
        c_type = str(candidate.get("segment_type") or "")
        c_reason = str(candidate.get("reason") or "")
        if c_type == active_type and c_reason != "title_row":
            continue
        if c_reason == "keyword_cluster" and (i - last_anchor_idx) < 3:
            continue
        anchors.append(candidate)
        active_type = c_type
        last_anchor_idx = i

    anchors = _dedupe_anchors(anchors)
    if anchors and anchors[0]["row_idx"] != 0:
        anchors.insert(0, {"row_idx": 0, "segment_type": anchors[0]["segment_type"], "reason": "prepend_first", "confidence": 0.5})
    if not anchors:
        meta = {
            "sheet_name": f"原表_{source_index}",
            "segment_type": SEG_NO_SPLIT,
            "source_table_index": source_index,
            "start_row": 1,
            "end_row": row_count,
            "rows": row_count,
            "cols": int(df.shape[1]),
            "reason": "no_anchor",
            "confidence": 1.0,
            "preview": _safe_preview(df),
            "explicit_title_hits": "",
            "key_metrics_score": 0.0,
            "balance_score": 0.0,
            "income_score": 0.0,
            "cashflow_score": 0.0,
            "ratio_score": 0.0,
            "final_segment_type": SEG_NO_SPLIT,
            "classification_reason": "no_anchor",
            "source_segments": "",
        }
        return [df], [meta]

    segments: List[pd.DataFrame] = []
    metadata: List[Dict] = []
    used_sheet_names: Dict[str, int] = {}
    for idx, anchor in enumerate(anchors):
        start = int(anchor["row_idx"])
        end = (int(anchors[idx + 1]["row_idx"]) - 1) if idx + 1 < len(anchors) else (row_count - 1)
        if end < start:
            continue
        part = df.iloc[start : end + 1].copy().reset_index(drop=True)
        if part.empty:
            continue

        segment_text = "\n".join(_row_text(part, ridx) for ridx in range(len(part)))
        diag = _classify_segment_by_text(segment_text)
        seg_type = str(diag.get("final_segment_type") or "").strip() or SEG_UNKNOWN
        sheet_name = _make_unique_sheet_name(seg_type, used_sheet_names)

        segments.append(part)
        metadata.append(
            {
                "sheet_name": sheet_name,
                "segment_type": seg_type,
                "source_table_index": source_index,
                "start_row": start + 1,
                "end_row": end + 1,
                "rows": int(part.shape[0]),
                "cols": int(part.shape[1]),
                "reason": anchor.get("reason", ""),
                "confidence": float(anchor.get("confidence", 0.5)),
                "preview": _safe_preview(part),
                "explicit_title_hits": diag.get("explicit_title_hits", ""),
                "key_metrics_score": diag.get("key_metrics_score", 0.0),
                "balance_score": diag.get("balance_score", 0.0),
                "income_score": diag.get("income_score", 0.0),
                "cashflow_score": diag.get("cashflow_score", 0.0),
                "ratio_score": diag.get("ratio_score", 0.0),
                "final_segment_type": seg_type,
                "classification_reason": diag.get("classification_reason", ""),
                "source_segments": sheet_name,
            }
        )
        if logger and config.get("log_detail", True):
            logger.info(
                "TableSegmenter segment table=%s type=%s start=%s end=%s reason=%s class_reason=%s",
                source_index,
                seg_type,
                start + 1,
                end + 1,
                anchor.get("reason", ""),
                diag.get("classification_reason", ""),
            )

    if len(segments) <= 1:
        meta = {
            "sheet_name": f"原表_{source_index}",
            "segment_type": SEG_NO_SPLIT,
            "source_table_index": source_index,
            "start_row": 1,
            "end_row": row_count,
            "rows": row_count,
            "cols": int(df.shape[1]),
            "reason": "insufficient_segments",
            "confidence": 1.0,
            "preview": _safe_preview(df),
            "explicit_title_hits": "",
            "key_metrics_score": 0.0,
            "balance_score": 0.0,
            "income_score": 0.0,
            "cashflow_score": 0.0,
            "ratio_score": 0.0,
            "final_segment_type": SEG_NO_SPLIT,
            "classification_reason": "insufficient_segments",
            "source_segments": "",
        }
        return [df], [meta]

    return segments, metadata


def _merge_pair(left_df: pd.DataFrame, left_meta: Dict, right_df: pd.DataFrame, right_meta: Dict, reason: str) -> Tuple[pd.DataFrame, Dict]:
    merged_df = pd.concat([left_df, right_df], ignore_index=True)
    left_sources = [s for s in str(left_meta.get("source_segments", "")).split(",") if s]
    right_sources = [s for s in str(right_meta.get("source_segments", "")).split(",") if s]
    merged_sources = left_sources + right_sources
    merged_meta = dict(left_meta)
    merged_meta["sheet_name"] = left_meta.get("segment_type", SEG_UNKNOWN) or SEG_UNKNOWN
    merged_meta["start_row"] = min(int(left_meta.get("start_row", 1)), int(right_meta.get("start_row", 1)))
    merged_meta["end_row"] = max(int(left_meta.get("end_row", 1)), int(right_meta.get("end_row", 1)))
    merged_meta["rows"] = int(merged_df.shape[0])
    merged_meta["cols"] = int(merged_df.shape[1])
    merged_meta["preview"] = _safe_preview(merged_df)
    merged_meta["source_segments"] = ",".join(merged_sources)
    merged_meta["reason"] = reason
    merged_meta["classification_reason"] = f"{left_meta.get('classification_reason','')}|{right_meta.get('classification_reason','')}|{reason}".strip("|")
    merged_meta["final_segment_type"] = left_meta.get("segment_type", SEG_UNKNOWN)
    return merged_df, merged_meta


def _should_merge(left_meta: Dict, right_meta: Dict, cfg: Dict) -> Tuple[bool, str]:
    left_type = str(left_meta.get("segment_type") or "")
    right_type = str(right_meta.get("segment_type") or "")
    left_src = left_meta.get("source_table_index")
    right_src = right_meta.get("source_table_index")
    if left_type != right_type or left_src != right_src:
        return False, ""

    min_rows = int(cfg.get("min_rows_for_standalone_segment", 3) or 3)
    left_rows = int(left_meta.get("rows", 0) or 0)
    left_reason = str(left_meta.get("reason", ""))
    left_cls_reason = str(left_meta.get("classification_reason", ""))
    left_is_small_title = left_rows <= min_rows and ("title_row" in left_reason or "explicit_title_priority" in left_cls_reason)

    if left_is_small_title:
        return True, "coalesced_title_stub_forward"

    if left_type == SEG_RATIO and bool(cfg.get("coalesce_ratio_sections", True)):
        return True, "coalesced_adjacent_ratio_segments"

    if left_type == SEG_BALANCE and bool(cfg.get("coalesce_same_type", True)):
        return True, "coalesced_adjacent_balance_segments"

    return False, ""


def coalesce_adjacent_segments(segments, metadata, logger=None, config=None):
    cfg = _merge_config(config)
    if not segments or not metadata or len(segments) != len(metadata):
        return segments or [], metadata or []

    if not cfg.get("coalesce_enabled", True):
        if logger and cfg.get("log_detail", True):
            logger.info("TableSegmenter coalesce enabled=False")
        return segments, metadata

    if logger and cfg.get("log_detail", True):
        logger.info("TableSegmenter coalesce enabled=True before segment count=%s", len(segments))

    merged_segments: List[pd.DataFrame] = []
    merged_metadata: List[Dict] = []
    i = 0
    while i < len(segments):
        cur_df = segments[i]
        cur_meta = dict(metadata[i])
        j = i + 1
        while j < len(segments):
            can_merge, merge_reason = _should_merge(cur_meta, metadata[j], cfg)
            if not can_merge:
                break
            cur_df, cur_meta = _merge_pair(cur_df, cur_meta, segments[j], metadata[j], merge_reason)
            if logger and cfg.get("log_detail", True):
                logger.info(
                    "TableSegmenter coalesce merge type=%s source_table_index=%s start=%s end=%s reason=%s",
                    cur_meta.get("segment_type", ""),
                    cur_meta.get("source_table_index", ""),
                    cur_meta.get("start_row", ""),
                    cur_meta.get("end_row", ""),
                    merge_reason,
                )
            j += 1
        merged_segments.append(cur_df)
        merged_metadata.append(cur_meta)
        i = j

    # Rebuild unique sheet names after coalesce
    used_names: Dict[str, int] = {}
    for meta in merged_metadata:
        base_name = str(meta.get("segment_type", SEG_UNKNOWN) or SEG_UNKNOWN)
        meta["sheet_name"] = _make_unique_sheet_name(base_name, used_names)

    if logger and cfg.get("log_detail", True):
        logger.info("TableSegmenter coalesce after segment count=%s", len(merged_segments))

    return merged_segments, merged_metadata


def _extract_first_col_token_set(df: pd.DataFrame) -> set:
    if df is None or df.empty or df.shape[1] == 0:
        return set()
    vals = df.iloc[:, 0].fillna("").astype(str).tolist()
    tokens = set()
    for v in vals:
        t = _normalize_text(v)
        if t:
            tokens.add(t)
    return tokens


def _extract_year_count_from_df(df: pd.DataFrame) -> int:
    if df is None or df.empty:
        return 0
    buf = []
    for c in df.columns.tolist():
        buf.append(str(c))
    sample_rows = min(3, len(df))
    for i in range(sample_rows):
        row = df.iloc[i].fillna("").astype(str).tolist()
        buf.extend(row)
    years = _extract_year_tokens(" ".join(buf))
    return len(years)


def _ratio_group_hit_count(df: pd.DataFrame) -> int:
    if df is None or df.empty:
        return 0
    txt = " ".join(df.fillna("").astype(str).values.flatten().tolist())
    norm = _normalize_text(txt)
    return len(_collect_hits(norm, RATIO_GROUP_KEYWORDS))


def _segment_quality_score(df: pd.DataFrame, meta: Dict) -> float:
    rows = int(meta.get("rows", 0) or 0)
    cols = int(meta.get("cols", 0) or 0)
    years = _extract_year_count_from_df(df)
    seg_type = str(meta.get("segment_type", ""))
    diag_scores = (
        float(meta.get("key_metrics_score", 0.0) or 0.0)
        + float(meta.get("balance_score", 0.0) or 0.0)
        + float(meta.get("income_score", 0.0) or 0.0)
        + float(meta.get("cashflow_score", 0.0) or 0.0)
        + float(meta.get("ratio_score", 0.0) or 0.0)
    )
    ratio_bonus = 2.0 * _ratio_group_hit_count(df) if seg_type == SEG_RATIO else 0.0
    return rows * 1.5 + cols * 0.5 + years * 1.2 + diag_scores * 0.08 + ratio_bonus


def _jaccard_overlap(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return inter / max(uni, 1)


def _append_reason(meta: Dict, reason: str) -> None:
    old = str(meta.get("reason", "") or "")
    if not old:
        meta["reason"] = reason
        return
    if reason in old.split("|"):
        return
    meta["reason"] = f"{old}|{reason}"


def _merge_into_target(target_df: pd.DataFrame, target_meta: Dict, src_df: pd.DataFrame, src_meta: Dict, merge_reason: str, prepend=False):
    if prepend:
        merged_df = pd.concat([src_df, target_df], ignore_index=True)
    else:
        merged_df = pd.concat([target_df, src_df], ignore_index=True)

    target_sources = [s for s in str(target_meta.get("source_segments", "")).split(",") if s]
    src_sources = [s for s in str(src_meta.get("source_segments", "")).split(",") if s]
    merged_sources = target_sources + src_sources

    out_meta = dict(target_meta)
    out_meta["start_row"] = min(int(target_meta.get("start_row", 1)), int(src_meta.get("start_row", 1)))
    out_meta["end_row"] = max(int(target_meta.get("end_row", 1)), int(src_meta.get("end_row", 1)))
    out_meta["rows"] = int(merged_df.shape[0])
    out_meta["cols"] = int(merged_df.shape[1])
    out_meta["preview"] = _safe_preview(merged_df)
    out_meta["source_segments"] = ",".join(merged_sources)
    _append_reason(out_meta, merge_reason)
    return merged_df, out_meta


def refine_segments(segments, metadata, logger=None, config=None):
    cfg = _merge_config(config)
    if not segments or not metadata or len(segments) != len(metadata):
        return segments or [], metadata or []

    entries = [{"df": segments[i], "meta": dict(metadata[i])} for i in range(len(segments))]
    if logger and cfg.get("log_detail", True):
        logger.info("TableSegmenter refine before count=%s", len(entries))

    # 1) Stub suppression: rows <= 1 try merge into better same-source segment.
    min_rows_standalone = int(cfg.get("min_rows_for_standalone_segment", 3) or 3)
    i = 0
    while i < len(entries):
        cur = entries[i]
        cur_df = cur["df"]
        cur_meta = cur["meta"]
        cur_rows = int(cur_meta.get("rows", 0) or 0)
        cur_src = cur_meta.get("source_table_index")
        cur_type = str(cur_meta.get("segment_type", ""))
        cur_cls_reason = str(cur_meta.get("classification_reason", ""))
        is_title = "title_row" in str(cur_meta.get("reason", "")) or "explicit_title_priority" in cur_cls_reason
        if cur_rows > 1 or is_title:
            i += 1
            continue

        text_norm = _normalize_text(" ".join(cur_df.fillna("").astype(str).values.flatten().tolist()))
        has_val_metrics = any(k in text_norm for k in ["ev/ebitda", "evebitda", "p/e", "pe", "p/b", "pb"])
        preferred_types = [SEG_RATIO, SEG_MAIN] if has_val_metrics else [cur_type, SEG_RATIO, SEG_MAIN, SEG_INCOME, SEG_BALANCE, SEG_CASHFLOW]

        best_j = -1
        best_rank = 10**9
        for j, nxt in enumerate(entries):
            if j == i:
                continue
            nxt_meta = nxt["meta"]
            if nxt_meta.get("source_table_index") != cur_src:
                continue
            nxt_type = str(nxt_meta.get("segment_type", ""))
            if nxt_type not in preferred_types:
                continue
            rank = preferred_types.index(nxt_type) * 100 + abs(j - i)
            if rank < best_rank:
                best_rank = rank
                best_j = j

        if best_j >= 0:
            prepend = i < best_j
            target_entry = entries[best_j]
            merged_df, merged_meta = _merge_into_target(
                target_entry["df"],
                target_entry["meta"],
                cur_df,
                cur_meta,
                merge_reason="refine_merged_stub_segment",
                prepend=prepend,
            )
            target_entry["df"] = merged_df
            target_entry["meta"] = merged_meta
            removed_name = cur_meta.get("sheet_name", f"seg_{i+1}")
            kept_name = target_entry["meta"].get("sheet_name", f"seg_{best_j+1}")
            if logger and cfg.get("log_detail", True):
                logger.info(
                    "TableSegmenter refine merged stub segment removed=%s kept=%s type=%s source_table_index=%s",
                    removed_name,
                    kept_name,
                    cur_type,
                    cur_src,
                )
            entries.pop(i)
            if best_j > i:
                best_j -= 1
            continue
        i += 1

    # 2) Same-source same-type dedup by similarity, keep better quality.
    changed = True
    while changed:
        changed = False
        idx_map: Dict[Tuple[object, str], List[int]] = {}
        for idx, e in enumerate(entries):
            key = (e["meta"].get("source_table_index"), str(e["meta"].get("segment_type", "")))
            idx_map.setdefault(key, []).append(idx)

        for key, idxs in idx_map.items():
            if len(idxs) < 2:
                continue
            # pairwise dedup
            removed = set()
            for a_pos in range(len(idxs)):
                ia = idxs[a_pos]
                if ia in removed:
                    continue
                for b_pos in range(a_pos + 1, len(idxs)):
                    ib = idxs[b_pos]
                    if ib in removed:
                        continue
                    ta = _extract_first_col_token_set(entries[ia]["df"])
                    tb = _extract_first_col_token_set(entries[ib]["df"])
                    overlap = _jaccard_overlap(ta, tb)
                    if overlap < 0.58:
                        continue
                    qa = _segment_quality_score(entries[ia]["df"], entries[ia]["meta"])
                    qb = _segment_quality_score(entries[ib]["df"], entries[ib]["meta"])
                    keep_i, drop_i = (ia, ib) if qa >= qb else (ib, ia)
                    keep_meta = entries[keep_i]["meta"]
                    drop_meta = entries[drop_i]["meta"]
                    _append_reason(keep_meta, "deduplicated_similar_segment")
                    keep_sources = [s for s in str(keep_meta.get("source_segments", "")).split(",") if s]
                    drop_sources = [s for s in str(drop_meta.get("source_segments", "")).split(",") if s]
                    keep_meta["source_segments"] = ",".join(keep_sources + drop_sources)
                    if logger and cfg.get("log_detail", True):
                        logger.info(
                            "TableSegmenter refine dedup keep=%s drop=%s type=%s source_table_index=%s overlap=%.3f",
                            keep_meta.get("sheet_name", f"seg_{keep_i+1}"),
                            drop_meta.get("sheet_name", f"seg_{drop_i+1}"),
                            keep_meta.get("segment_type", ""),
                            keep_meta.get("source_table_index", ""),
                            overlap,
                        )
                    removed.add(drop_i)
                    changed = True

            if removed:
                entries = [e for idx, e in enumerate(entries) if idx not in removed]
                break

    # 3) Same-source same-type nonadjacent merge for selected types
    for target_type in (SEG_BALANCE, SEG_CASHFLOW, SEG_RATIO):
        src_groups: Dict[object, List[int]] = {}
        for idx, e in enumerate(entries):
            m = e["meta"]
            if str(m.get("segment_type", "")) != target_type:
                continue
            src_groups.setdefault(m.get("source_table_index"), []).append(idx)

        for src_idx, idxs in src_groups.items():
            if len(idxs) < 2:
                continue
            idxs_sorted = sorted(idxs, key=lambda x: int(entries[x]["meta"].get("start_row", 1)))
            base = idxs_sorted[0]
            for nxt in idxs_sorted[1:]:
                base_df, base_meta = entries[base]["df"], entries[base]["meta"]
                nxt_df, nxt_meta = entries[nxt]["df"], entries[nxt]["meta"]
                overlap = _jaccard_overlap(_extract_first_col_token_set(base_df), _extract_first_col_token_set(nxt_df))
                # low-medium overlap means likely continuation
                if overlap > 0.78:
                    continue
                merged_df, merged_meta = _merge_into_target(
                    base_df,
                    base_meta,
                    nxt_df,
                    nxt_meta,
                    merge_reason="merged_same_type_nonadjacent_segments",
                    prepend=False,
                )
                entries[base]["df"] = merged_df
                entries[base]["meta"] = merged_meta
                entries[nxt]["meta"]["_drop_refine"] = True
                if logger and cfg.get("log_detail", True):
                    logger.info(
                        "TableSegmenter refine nonadjacent-merge keep=%s drop=%s type=%s source_table_index=%s overlap=%.3f",
                        merged_meta.get("sheet_name", f"seg_{base+1}"),
                        nxt_meta.get("sheet_name", f"seg_{nxt+1}"),
                        target_type,
                        src_idx,
                        overlap,
                    )
            entries = [e for e in entries if not e["meta"].get("_drop_refine")]

    # 4) Ratio completeness preference among same-source ratio segments
    src_groups: Dict[object, List[int]] = {}
    for idx, e in enumerate(entries):
        m = e["meta"]
        if str(m.get("segment_type", "")) != SEG_RATIO:
            continue
        src_groups.setdefault(m.get("source_table_index"), []).append(idx)

    remove_idxs = set()
    for src_idx, idxs in src_groups.items():
        if len(idxs) < 2:
            continue
        scored = []
        for i in idxs:
            df = entries[i]["df"]
            group_hits = _ratio_group_hit_count(df)
            q = _segment_quality_score(df, entries[i]["meta"])
            scored.append((i, group_hits, q))
        scored.sort(key=lambda x: (x[1], x[2]), reverse=True)
        keep_i = scored[0][0]
        keep_meta = entries[keep_i]["meta"]
        for i, group_hits, _q in scored[1:]:
            # remove only clearly weaker ratio segment
            if group_hits < scored[0][1] and int(entries[i]["meta"].get("rows", 0) or 0) <= int(keep_meta.get("rows", 0) or 0):
                _append_reason(keep_meta, "refine_ratio_completeness_preferred")
                keep_sources = [s for s in str(keep_meta.get("source_segments", "")).split(",") if s]
                drop_sources = [s for s in str(entries[i]["meta"].get("source_segments", "")).split(",") if s]
                keep_meta["source_segments"] = ",".join(keep_sources + drop_sources)
                remove_idxs.add(i)
                if logger and cfg.get("log_detail", True):
                    logger.info(
                        "TableSegmenter refine ratio-prefer keep=%s drop=%s source_table_index=%s keep_group_hits=%s drop_group_hits=%s",
                        keep_meta.get("sheet_name", f"seg_{keep_i+1}"),
                        entries[i]["meta"].get("sheet_name", f"seg_{i+1}"),
                        src_idx,
                        scored[0][1],
                        group_hits,
                    )
    if remove_idxs:
        entries = [e for idx, e in enumerate(entries) if idx not in remove_idxs]

    # rebuild sheet names
    used_names: Dict[str, int] = {}
    for e in entries:
        m = e["meta"]
        base_name = str(m.get("segment_type", SEG_UNKNOWN) or SEG_UNKNOWN)
        m["sheet_name"] = _make_unique_sheet_name(base_name, used_names)
        m["rows"] = int(e["df"].shape[0]) if isinstance(e["df"], pd.DataFrame) else int(m.get("rows", 0) or 0)
        m["cols"] = int(e["df"].shape[1]) if isinstance(e["df"], pd.DataFrame) else int(m.get("cols", 0) or 0)
        m["preview"] = _safe_preview(e["df"]) if isinstance(e["df"], pd.DataFrame) else str(m.get("preview", ""))

    if logger and cfg.get("log_detail", True):
        logger.info("TableSegmenter refine after count=%s", len(entries))

    return [e["df"] for e in entries], [e["meta"] for e in entries]


def segment_tables(df_list, logger=None, config=None):
    merged_config = _merge_config(config)
    if not df_list:
        return [], []

    out_dfs: List[pd.DataFrame] = []
    out_meta: List[Dict] = []
    for source_idx, df in enumerate(df_list, start=1):
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        parts, meta = _segment_single_table(df, source_idx, merged_config, logger=logger)
        out_dfs.extend(parts)
        out_meta.extend(meta)

    before_count = len(out_dfs)
    out_dfs, out_meta = coalesce_adjacent_segments(out_dfs, out_meta, logger=logger, config=merged_config)
    after_count = len(out_dfs)
    if logger and merged_config.get("log_detail", True):
        logger.info("TableSegmenter coalesce summary: before=%s after=%s", before_count, after_count)
    refine_before = len(out_dfs)
    out_dfs, out_meta = refine_segments(out_dfs, out_meta, logger=logger, config=merged_config)
    refine_after = len(out_dfs)
    if logger and merged_config.get("log_detail", True):
        logger.info("TableSegmenter refine summary: before=%s after=%s", refine_before, refine_after)
    return out_dfs, out_meta


def build_segment_index_dataframe(segment_metadata):
    rows = []
    for item in segment_metadata or []:
        rows.append(
            {
                "sheet_name": item.get("sheet_name", ""),
                "segment_type": item.get("segment_type", ""),
                "source_table_index": item.get("source_table_index", ""),
                "start_row": item.get("start_row", ""),
                "end_row": item.get("end_row", ""),
                "rows": item.get("rows", ""),
                "cols": item.get("cols", ""),
                "reason": item.get("reason", ""),
                "confidence": item.get("confidence", ""),
                "preview": item.get("preview", ""),
                "explicit_title_hits": item.get("explicit_title_hits", ""),
                "key_metrics_score": item.get("key_metrics_score", ""),
                "balance_score": item.get("balance_score", ""),
                "income_score": item.get("income_score", ""),
                "cashflow_score": item.get("cashflow_score", ""),
                "ratio_score": item.get("ratio_score", ""),
                "final_segment_type": item.get("final_segment_type", ""),
                "classification_reason": item.get("classification_reason", ""),
                "source_segments": item.get("source_segments", ""),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "sheet_name",
            "segment_type",
            "source_table_index",
            "start_row",
            "end_row",
            "rows",
            "cols",
            "reason",
            "confidence",
            "preview",
            "explicit_title_hits",
            "key_metrics_score",
            "balance_score",
            "income_score",
            "cashflow_score",
            "ratio_score",
            "final_segment_type",
            "classification_reason",
            "source_segments",
        ],
    )


def build_segment_map_dataframe(segment_metadata):
    index_df = build_segment_index_dataframe(segment_metadata)
    if index_df.empty:
        return pd.DataFrame(
            columns=[
                "output_sheet_name",
                "segment_type",
                "source_table_index",
                "start_row",
                "end_row",
                "rows",
                "cols",
                "reason",
                "classification_reason",
                "explicit_title_hits",
                "key_metrics_score",
                "balance_score",
                "income_score",
                "cashflow_score",
                "ratio_score",
                "source_segments",
                "preview",
            ]
        )
    map_df = index_df.copy()
    map_df = map_df.rename(columns={"sheet_name": "output_sheet_name"})
    keep_cols = [
        "output_sheet_name",
        "segment_type",
        "source_table_index",
        "start_row",
        "end_row",
        "rows",
        "cols",
        "reason",
        "classification_reason",
        "explicit_title_hits",
        "key_metrics_score",
        "balance_score",
        "income_score",
        "cashflow_score",
        "ratio_score",
        "source_segments",
        "preview",
    ]
    for col in keep_cols:
        if col not in map_df.columns:
            map_df[col] = ""
    return map_df[keep_cols]


def _row_text_preview(df: pd.DataFrame, row_idx_0based: int, max_cols: int = 8) -> str:
    if row_idx_0based < 0 or row_idx_0based >= len(df):
        return ""
    vals = df.iloc[row_idx_0based, :max_cols].fillna("").astype(str).tolist()
    return " | ".join([v.strip() for v in vals if str(v).strip()])


def build_source_table_preview_dataframe(source_tables, segment_metadata, context_rows: int = 3, max_cols: int = 8):
    rows = []
    if not source_tables:
        return pd.DataFrame(columns=["source_table_index", "total_rows", "total_cols", "row_index", "row_text"])

    source_segment_ranges: Dict[int, List[Tuple[int, int]]] = {}
    for m in segment_metadata or []:
        src = m.get("source_table_index")
        if src is None:
            continue
        try:
            src_idx = int(src)
            start_row = int(m.get("start_row", 1))
            end_row = int(m.get("end_row", 1))
        except Exception:
            continue
        source_segment_ranges.setdefault(src_idx, []).append((start_row, end_row))

    for src_idx_1based, df in enumerate(source_tables, start=1):
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        total_rows = int(df.shape[0])
        total_cols = int(df.shape[1])
        include_rows_1based = set()

        ranges = source_segment_ranges.get(src_idx_1based, [])
        if ranges:
            for start_row, end_row in ranges:
                left = max(1, start_row - context_rows)
                right = min(total_rows, end_row + context_rows)
                for r in range(left, right + 1):
                    include_rows_1based.add(r)
        else:
            for r in range(1, total_rows + 1):
                include_rows_1based.add(r)

        for row_1based in sorted(include_rows_1based):
            row_text = _row_text_preview(df, row_1based - 1, max_cols=max_cols)
            rows.append(
                {
                    "source_table_index": src_idx_1based,
                    "total_rows": total_rows,
                    "total_cols": total_cols,
                    "row_index": row_1based,
                    "row_text": row_text,
                }
            )

    return pd.DataFrame(rows, columns=["source_table_index", "total_rows", "total_cols", "row_index", "row_text"])
