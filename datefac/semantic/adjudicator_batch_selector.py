from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd


CORE_TABLE_KEYWORDS = [
    "利润表",
    "现金流量表",
    "资产负债表",
    "财务预测",
    "盈利预测",
    "估值",
]

OUT_OF_SCOPE_TABLE_KEYWORDS = [
    "可比公司",
    "估值表",
    "基础数据",
    "股价",
    "收盘价",
    "行业均值",
]

GENERIC_HEADER_LABELS = {
    "代码",
    "行业均值",
    "国内",
    "国外",
    "公司",
    "货币",
    "市值",
    "收盘价",
    "评级",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _split_pipe(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _find_workbook(directory: Path) -> Optional[Path]:
    if not directory.exists():
        return None
    workbooks = sorted(directory.glob("*.xlsx"))
    return workbooks[0] if workbooks else None


def _read_sheet(workbook: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(workbook, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def load_prior_selection_context(previous_limited_dir: Path, previous_replay_dir: Path) -> Dict[str, Set[str]]:
    handled_case_ids: Set[str] = set()
    handled_labels: Set[str] = set()
    replayed_case_ids: Set[str] = set()
    replayed_labels: Set[str] = set()

    limited_workbook = _find_workbook(previous_limited_dir)
    limited_selected_df = _read_sheet(limited_workbook, "selected_label_cases")
    for _, row in limited_selected_df.iterrows():
        case_id = _norm(row.get("label_case_id"))
        normalized_label = _normalize_label(row.get("normalized_label"))
        if case_id:
            handled_case_ids.add(case_id)
        if normalized_label:
            handled_labels.add(normalized_label)

    replay_workbook = _find_workbook(previous_replay_dir)
    replay_inventory_df = _read_sheet(replay_workbook, "replay_instruction_inventory")
    for _, row in replay_inventory_df.iterrows():
        case_id = _norm(row.get("case_id"))
        normalized_label = _normalize_label(row.get("normalized_label"))
        if case_id:
            replayed_case_ids.add(case_id)
            handled_case_ids.add(case_id)
        if normalized_label:
            replayed_labels.add(normalized_label)
            handled_labels.add(normalized_label)

    return {
        "handled_case_ids": handled_case_ids,
        "handled_labels": handled_labels,
        "replayed_case_ids": replayed_case_ids,
        "replayed_labels": replayed_labels,
    }


def _is_readable_label(label: str) -> bool:
    if not label:
        return False
    if _looks_mojibake(label):
        return False
    alpha_like = sum(1 for ch in label if ("\u4e00" <= ch <= "\u9fff") or ch.isalpha())
    return alpha_like >= max(1, len(label) // 5)


def _looks_mojibake(label: str) -> bool:
    if not label:
        return False
    mojibake_tokens = ["锟", "鈥", "�", "�"]
    return any(token in label for token in mojibake_tokens)


def _is_long_narrative(label: str) -> bool:
    if len(label) >= 60:
        return True
    narrative_tokens = ["评级标准", "报告发布日后", "作为基准", "市场表现"]
    return any(token in label for token in narrative_tokens)


def _has_examples(row: pd.Series) -> bool:
    keys = [
        "raw_label_examples",
        "table_title_examples",
        "source_report_examples",
        "value_examples",
        "year_examples",
        "unit_context_examples",
    ]
    return any(bool(_split_pipe(row.get(key))) for key in keys)


def _review_label_diagnostics(review_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "normalized_label",
        "invalid_only",
        "has_unknown_metric",
        "has_mapping_review",
        "has_unit_unknown",
        "core_table_hint",
        "out_of_scope_hint",
        "table_title_examples",
        "review_reason_examples",
        "risk_tag_examples",
    ]
    if review_df.empty:
        return pd.DataFrame(columns=columns)

    temp = review_df.copy()
    temp["normalized_label"] = temp["raw_metric_name"].map(_normalize_label)

    rows: List[Dict[str, Any]] = []
    for normalized_label, group in temp.groupby("normalized_label", dropna=False):
        titles = [title for title in group["table_title"].astype(str).tolist() if title]
        reasons = [reason for reason in group["split_reason"].astype(str).tolist() if reason]
        risks = [risk for risk in group["risk_tags_after"].astype(str).tolist() if risk]
        invalid_only = True
        has_unknown_metric = False
        has_mapping_review = False
        has_unit_unknown = False
        for _, row in group.iterrows():
            joined = "|".join(
                [
                    _norm(row.get("split_reason")),
                    _norm(row.get("risk_tags_after")),
                    _norm(row.get("risk_tags")),
                ]
            )
            has_unknown_metric = has_unknown_metric or "UNKNOWN_METRIC_CODE" in joined
            has_mapping_review = has_mapping_review or "HAS_MAPPING_REVIEW_TAG" in joined
            has_unit_unknown = has_unit_unknown or "UNIT_UNKNOWN" in joined
            if not any(
                token in joined
                for token in [
                    "INVALID_YEAR",
                    "NO_YEAR_COLUMNS",
                    "VALUE_PARSE_FAILED",
                    "INVALID_OR_MISSING_YEAR",
                    "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN",
                ]
            ):
                invalid_only = False
            if has_unknown_metric or has_mapping_review or has_unit_unknown:
                invalid_only = False

        rows.append(
            {
                "normalized_label": normalized_label,
                "invalid_only": bool(invalid_only),
                "has_unknown_metric": bool(has_unknown_metric),
                "has_mapping_review": bool(has_mapping_review),
                "has_unit_unknown": bool(has_unit_unknown),
                "core_table_hint": any(keyword in title for title in titles for keyword in CORE_TABLE_KEYWORDS),
                "out_of_scope_hint": any(keyword in title for title in titles for keyword in OUT_OF_SCOPE_TABLE_KEYWORDS),
                "table_title_examples": "|".join(dict.fromkeys(titles).keys())[:1000],
                "review_reason_examples": "|".join(dict.fromkeys(reasons).keys())[:500],
                "risk_tag_examples": "|".join(dict.fromkeys(risks).keys())[:1000],
            }
        )

    return pd.DataFrame(rows, columns=columns).fillna("")


def _score_label_case(row: pd.Series, prior_context: Dict[str, Set[str]]) -> Tuple[float, List[str], str]:
    normalized_label = _normalize_label(row.get("normalized_label"))
    case_id = _norm(row.get("label_case_id"))
    category = _norm(row.get("candidate_category"))
    candidate_count = int(row.get("candidate_count") or 0)
    unique_table_count = int(row.get("unique_table_count") or 0)

    score = 0.0
    reasons: List[str] = []
    skip_reasons: List[str] = []

    readable = _is_readable_label(normalized_label)
    long_narrative = _is_long_narrative(normalized_label)
    generic_header = normalized_label in GENERIC_HEADER_LABELS
    has_examples = _has_examples(row)
    invalid_only = bool(row.get("invalid_only"))
    already_handled = (
        case_id in prior_context.get("handled_case_ids", set())
        or normalized_label in prior_context.get("handled_labels", set())
    )

    if not normalized_label:
        skip_reasons.append("EMPTY_NORMALIZED_LABEL")
    if already_handled:
        skip_reasons.append("ALREADY_HANDLED_IN_322D_OR_322E")
    if invalid_only:
        skip_reasons.append("INVALID_YEAR_OR_VALUE_PARSE_ONLY")
    if not readable:
        skip_reasons.append("UNREADABLE_OR_LOW_SIGNAL_LABEL")
    if long_narrative:
        skip_reasons.append("LONG_NARRATIVE_OR_POLICY_TEXT")
    if not has_examples:
        skip_reasons.append("LOW_EVIDENCE_NO_EXAMPLES")

    score += min(candidate_count, 60) * 1.35
    score += unique_table_count * 2.5

    if category == "UNKNOWN_METRIC_ALIAS_CANDIDATE":
        score += 22
        reasons.append("alias_candidate")
    elif category == "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION":
        score += 13
        reasons.append("scope_candidate")
    elif category == "MAPPING_REVIEW_TAG_EXPLANATION":
        score += 7
        reasons.append("mapping_review_candidate")
    else:
        score += 2

    if bool(row.get("core_table_hint")):
        score += 12
        reasons.append("core_statement_or_forecast_context")
    if bool(row.get("out_of_scope_hint")):
        score += 9
        reasons.append("valuation_or_basic_data_context")
    if bool(row.get("has_unknown_metric")):
        score += 8
        reasons.append("unknown_metric_present")
    if bool(row.get("has_mapping_review")):
        score += 5
        reasons.append("mapping_review_tag_present")
    if bool(row.get("has_unit_unknown")):
        score += 3
        reasons.append("unit_unknown_present")
    if candidate_count >= 20:
        score += 8
        reasons.append("high_candidate_count")
    if unique_table_count >= 4:
        score += 6
        reasons.append("multi_table_recurrence")
    if readable:
        score += 5
        reasons.append("readable_label_text")
    if has_examples:
        score += 4
        reasons.append("has_supporting_examples")

    if generic_header:
        score -= 18
        reasons.append("generic_header_downrank")
    if unique_table_count <= 1 and candidate_count < 12:
        score -= 10
        reasons.append("single_table_low_scale_downrank")

    if skip_reasons:
        score -= 100

    return score, reasons, "|".join(skip_reasons)


def _prompt_template_for_row(row: pd.Series) -> str:
    category = _norm(row.get("candidate_category"))
    if category == "UNIT_CONTEXT_INFERENCE":
        return "unit_context_inference"
    return "label_level_alias_or_scope"


def build_label_batch_selection(
    label_pack_df: pd.DataFrame,
    review_df: pd.DataFrame,
    previous_limited_dir: Path,
    previous_replay_dir: Path,
    max_label_cases: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    selected_columns = [
        "label_case_id",
        "normalized_label",
        "candidate_count",
        "unique_table_count",
        "candidate_category",
        "priority",
        "selection_score",
        "selection_reason",
        "skip_reason",
        "prompt_template",
        "allowed_actions",
        "raw_label_examples",
        "table_title_examples",
        "source_report_examples",
        "value_examples",
        "year_examples",
        "unit_context_examples",
        "current_risk_tags",
        "allowed_metric_codes_sample",
    ]
    audit_columns = [
        "case_id",
        "normalized_label",
        "candidate_count",
        "unique_table_count",
        "candidate_category",
        "selection_score",
        "selected",
        "selection_reason",
        "skip_reason",
    ]
    if label_pack_df.empty or max_label_cases <= 0:
        return pd.DataFrame(columns=selected_columns), pd.DataFrame(columns=audit_columns)

    temp = label_pack_df.copy().fillna("")
    temp["normalized_label"] = temp["normalized_label"].map(_normalize_label)
    temp["candidate_count"] = temp["candidate_count"].fillna(0).astype(int)
    temp["unique_table_count"] = temp["unique_table_count"].fillna(0).astype(int)

    diagnostics_df = _review_label_diagnostics(review_df)
    if not diagnostics_df.empty:
        temp = temp.merge(diagnostics_df, on="normalized_label", how="left")
    temp = temp.fillna(
        {
            "invalid_only": False,
            "has_unknown_metric": False,
            "has_mapping_review": False,
            "has_unit_unknown": False,
            "core_table_hint": False,
            "out_of_scope_hint": False,
            "table_title_examples_y": "",
            "review_reason_examples": "",
            "risk_tag_examples": "",
        }
    )

    if "table_title_examples" not in temp.columns:
        if "table_title_examples_x" in temp.columns:
            temp["table_title_examples"] = temp["table_title_examples_x"]
        elif "table_title_examples_y" in temp.columns:
            temp["table_title_examples"] = temp["table_title_examples_y"]
        else:
            temp["table_title_examples"] = ""
    if "table_title_examples_y" in temp.columns:
        temp["table_title_examples"] = temp["table_title_examples"].astype(str)
        merge_mask = temp["table_title_examples"].eq("")
        temp.loc[merge_mask, "table_title_examples"] = temp.loc[merge_mask, "table_title_examples_y"]
    temp = temp.drop(columns=["table_title_examples_x", "table_title_examples_y"], errors="ignore")

    prior_context = load_prior_selection_context(previous_limited_dir, previous_replay_dir)

    score_values: List[float] = []
    reason_values: List[str] = []
    skip_values: List[str] = []
    prompt_templates: List[str] = []
    for _, row in temp.iterrows():
        score, reasons, skip_reason = _score_label_case(row, prior_context)
        score_values.append(round(score, 3))
        reason_values.append("|".join(reasons or ["default_priority"]))
        skip_values.append(skip_reason)
        prompt_templates.append(_prompt_template_for_row(row))

    temp["selection_score"] = score_values
    temp["selection_reason"] = reason_values
    temp["skip_reason"] = skip_values
    temp["prompt_template"] = prompt_templates
    temp["selected"] = False

    selectable_df = temp[temp["skip_reason"].astype(str) == ""].copy()
    selectable_df = selectable_df.sort_values(
        [
            "selection_score",
            "candidate_count",
            "unique_table_count",
            "normalized_label",
        ],
        ascending=[False, False, False, True],
    )

    selected_frames: List[pd.DataFrame] = []
    used_case_ids: Set[str] = set()
    category_targets = [
        ("UNKNOWN_METRIC_ALIAS_CANDIDATE", min(10, max_label_cases)),
        ("OUT_OF_SCOPE_OR_CORE_CLASSIFICATION", min(8, max_label_cases)),
        ("MAPPING_REVIEW_TAG_EXPLANATION", max_label_cases),
    ]
    for category, limit in category_targets:
        if len(used_case_ids) >= max_label_cases:
            break
        category_df = selectable_df[
            (selectable_df["candidate_category"].astype(str) == category)
            & (~selectable_df["label_case_id"].astype(str).isin(used_case_ids))
        ].head(max(0, min(limit, max_label_cases - len(used_case_ids))))
        if category_df.empty:
            continue
        selected_frames.append(category_df)
        used_case_ids.update(category_df["label_case_id"].astype(str).tolist())

    if len(used_case_ids) < max_label_cases:
        remainder_df = selectable_df[~selectable_df["label_case_id"].astype(str).isin(used_case_ids)].head(max_label_cases - len(used_case_ids))
        if not remainder_df.empty:
            selected_frames.append(remainder_df)
            used_case_ids.update(remainder_df["label_case_id"].astype(str).tolist())

    selected_df = pd.concat(selected_frames, ignore_index=True) if selected_frames else pd.DataFrame(columns=selectable_df.columns)
    selected_df = selected_df.sort_values(
        ["selection_score", "candidate_count", "unique_table_count", "normalized_label"],
        ascending=[False, False, False, True],
    )
    selected_case_ids = set(selected_df["label_case_id"].astype(str).tolist())
    temp["selected"] = temp["label_case_id"].astype(str).isin(selected_case_ids)

    audit_df = temp[
        [
            "label_case_id",
            "normalized_label",
            "candidate_count",
            "unique_table_count",
            "candidate_category",
            "selection_score",
            "selected",
            "selection_reason",
            "skip_reason",
        ]
    ].rename(columns={"label_case_id": "case_id"}).copy()

    selected_df = selected_df[selected_columns].reset_index(drop=True)
    audit_df = audit_df[audit_columns].sort_values(
        ["selected", "selection_score", "candidate_count", "normalized_label"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    return selected_df, audit_df


def build_candidate_case_selection(candidate_pack_df: pd.DataFrame, max_candidate_cases: int) -> pd.DataFrame:
    columns = [
        "case_id",
        "table_asset_id",
        "source_report_name",
        "table_title",
        "table_context",
        "row_label",
        "row_values",
        "year_columns",
        "unit_context",
        "current_metric_code",
        "current_risk_tags",
        "current_review_reason",
        "available_provenance",
        "priority",
        "selection_score",
        "selection_reason",
        "prompt_template",
        "allowed_actions",
    ]
    if candidate_pack_df.empty or max_candidate_cases <= 0:
        return pd.DataFrame(columns=columns)

    temp = candidate_pack_df.copy().fillna("")
    temp["selection_score"] = 0.0
    temp["selection_reason"] = "candidate_level_context_review"
    temp["prompt_template"] = temp["current_review_reason"].astype(str).map(
        lambda value: "unit_context_inference" if _norm(value) == "UNIT_UNKNOWN" else "candidate_level_context_review"
    )
    temp = temp.sort_values(["priority", "table_asset_id", "row_label"], ascending=[True, True, True]).head(max_candidate_cases)
    return temp[columns].reset_index(drop=True)
