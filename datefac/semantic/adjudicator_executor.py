from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


OUT_OF_SCOPE_TABLE_KEYWORDS = [
    "可比公司",
    "估值",
    "基础数据",
    "股价",
    "收盘价",
    "行业均值",
]

CORE_TABLE_KEYWORDS = [
    "利润表",
    "现金流量表",
    "资产负债表",
    "财务预测",
    "三大财务预测表",
    "预测",
    "估值",
]


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


def _read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                rows.append(json.loads(text))
            except Exception:
                continue
    return pd.DataFrame(rows).fillna("")


def read_design_inputs(design_dir: Path) -> Dict[str, Any]:
    workbook_path = design_dir / "semantic_adjudicator_design_322c.xlsx"
    label_pack_path = design_dir / "llm_label_pack_322c.jsonl"
    candidate_pack_path = design_dir / "llm_candidate_pack_322c.jsonl"
    schema_path = design_dir / "llm_adjudicator_output_schema_322c.json"

    prompt_templates_df = pd.read_excel(workbook_path, sheet_name="prompt_templates").fillna("") if workbook_path.exists() else pd.DataFrame()
    allowed_metric_codes_df = pd.read_excel(workbook_path, sheet_name="allowed_metric_codes").fillna("") if workbook_path.exists() else pd.DataFrame()

    output_schema: Dict[str, Any] = {}
    if schema_path.exists():
        try:
            output_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception:
            output_schema = {}

    return {
        "label_pack_df": _read_jsonl(label_pack_path),
        "candidate_pack_df": _read_jsonl(candidate_pack_path),
        "prompt_templates_df": prompt_templates_df,
        "allowed_metric_codes_df": allowed_metric_codes_df,
        "output_schema": output_schema,
    }


def _label_review_diagnostics(review_df: pd.DataFrame) -> pd.DataFrame:
    if review_df.empty:
        return pd.DataFrame(
            columns=[
                "normalized_label",
                "invalid_only",
                "core_table_hint",
                "out_of_scope_hint",
                "table_title_examples",
                "review_reason_examples",
                "risk_tag_examples",
            ]
        )

    temp = review_df.copy()
    temp["normalized_label"] = temp["raw_metric_name"].map(_normalize_label)
    rows: List[Dict[str, Any]] = []
    for normalized_label, group in temp.groupby("normalized_label", dropna=False):
        titles = [title for title in group["table_title"].astype(str).tolist() if title]
        reasons = [reason for reason in group["split_reason"].astype(str).tolist() if reason]
        risks = [risk for risk in group["risk_tags_after"].astype(str).tolist() if risk]
        invalid_only = True
        for _, row in group.iterrows():
            joined = "|".join(
                [
                    _norm(row.get("split_reason")),
                    _norm(row.get("risk_tags_after")),
                    _norm(row.get("risk_tags")),
                ]
            )
            if not any(token in joined for token in ["INVALID_YEAR", "VALUE_PARSE_FAILED", "INVALID_OR_MISSING_YEAR", "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN"]):
                invalid_only = False
                break
            if "UNKNOWN_METRIC_CODE" in joined or "HAS_MAPPING_REVIEW_TAG" in joined or "UNIT_UNKNOWN" in joined:
                invalid_only = False
                break
        core_table_hint = any(keyword in title for title in titles for keyword in CORE_TABLE_KEYWORDS)
        out_of_scope_hint = any(keyword in title for title in titles for keyword in OUT_OF_SCOPE_TABLE_KEYWORDS)
        rows.append(
            {
                "normalized_label": normalized_label,
                "invalid_only": bool(invalid_only),
                "core_table_hint": bool(core_table_hint),
                "out_of_scope_hint": bool(out_of_scope_hint),
                "table_title_examples": "|".join(dict.fromkeys(titles).keys())[:1000],
                "review_reason_examples": "|".join(dict.fromkeys(reasons).keys())[:500],
                "risk_tag_examples": "|".join(dict.fromkeys(risks).keys())[:1000],
            }
        )
    return pd.DataFrame(rows)


def select_label_cases(label_pack_df: pd.DataFrame, review_df: pd.DataFrame, max_label_cases: int) -> pd.DataFrame:
    columns = [
        "label_case_id",
        "normalized_label",
        "candidate_count",
        "unique_table_count",
        "candidate_category",
        "priority",
        "selection_reason",
        "prompt_template",
    ]
    if label_pack_df.empty or max_label_cases <= 0:
        return pd.DataFrame(columns=columns)

    merged = label_pack_df.copy()
    merged["normalized_label"] = merged["normalized_label"].map(_norm)
    merged = merged[merged["normalized_label"].astype(str) != ""].copy()

    diagnostics_df = _label_review_diagnostics(review_df)
    if not diagnostics_df.empty:
        merged = merged.merge(diagnostics_df, on="normalized_label", how="left")
    merged = merged.fillna(
        {
            "invalid_only": False,
            "core_table_hint": False,
            "out_of_scope_hint": False,
            "table_title_examples": "",
            "review_reason_examples": "",
            "risk_tag_examples": "",
        }
    )
    merged = merged[~merged["invalid_only"].astype(bool)].copy()

    category_order = {
        "UNKNOWN_METRIC_ALIAS_CANDIDATE": 0,
        "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION": 1,
        "MAPPING_REVIEW_TAG_EXPLANATION": 2,
        "UNIT_CONTEXT_INFERENCE": 3,
    }
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    merged["category_rank"] = merged["candidate_category"].astype(str).map(lambda value: category_order.get(value, 9))
    merged["priority_rank"] = merged["priority"].astype(str).map(lambda value: priority_order.get(value, 9))
    merged["prompt_template"] = merged["candidate_category"].astype(str).map(
        lambda value: "unit_context_inference" if value == "UNIT_CONTEXT_INFERENCE" else "label_level_alias_or_scope"
    )

    selection_reasons: List[str] = []
    for _, row in merged.iterrows():
        reason_parts: List[str] = []
        if _norm(row.get("priority")) == "HIGH":
            reason_parts.append("high_priority")
        if _norm(row.get("candidate_category")) == "UNKNOWN_METRIC_ALIAS_CANDIDATE":
            reason_parts.append("alias_candidate")
        if _norm(row.get("candidate_category")) == "OUT_OF_SCOPE_OR_CORE_CLASSIFICATION":
            reason_parts.append("scope_classification_candidate")
        if bool(row.get("core_table_hint")):
            reason_parts.append("core_statement_or_forecast_table")
        if bool(row.get("out_of_scope_hint")):
            reason_parts.append("valuation_or_basic_data_context")
        if int(row.get("candidate_count") or 0) >= 20:
            reason_parts.append("high_candidate_count")
        selection_reasons.append("|".join(reason_parts or ["default_priority"]))
    merged["selection_reason"] = selection_reasons

    merged = merged.sort_values(
        [
            "category_rank",
            "priority_rank",
            "core_table_hint",
            "candidate_count",
            "unique_table_count",
            "normalized_label",
        ],
        ascending=[True, True, False, False, False, True],
    ).head(max_label_cases)

    return merged[columns].reset_index(drop=True)


def select_candidate_cases(candidate_pack_df: pd.DataFrame, max_candidate_cases: int) -> pd.DataFrame:
    columns = [
        "case_id",
        "table_asset_id",
        "table_title",
        "row_label",
        "current_review_reason",
        "priority",
        "selection_reason",
        "prompt_template",
    ]
    if candidate_pack_df.empty or max_candidate_cases <= 0:
        return pd.DataFrame(columns=columns)
    temp = candidate_pack_df.copy()
    temp = temp[
        ~temp["current_review_reason"].astype(str).isin(["INVALID_OR_MISSING_YEAR", "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN"])
    ].copy()
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    temp["priority_rank"] = temp["priority"].astype(str).map(lambda value: priority_order.get(value, 9))
    temp["selection_reason"] = "explicit_candidate_context_case"
    temp["prompt_template"] = temp["current_review_reason"].astype(str).map(
        lambda value: "unit_context_inference" if value == "UNIT_UNKNOWN" else "candidate_level_context_review"
    )
    temp = temp.sort_values(["priority_rank", "table_asset_id", "row_label"], ascending=[True, True, True]).head(max_candidate_cases)
    return temp[columns].reset_index(drop=True)


def _request_payload_common(
    case_id: str,
    case_type: str,
    prompt_text: str,
    input_context: Dict[str, Any],
    output_schema: Dict[str, Any],
    allowed_metric_codes: List[Dict[str, Any]],
    allowed_actions: List[str],
    source_pack_row: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "case_id": case_id,
        "case_type": case_type,
        "prompt_text": prompt_text,
        "input_context": input_context,
        "output_schema": output_schema,
        "allowed_metric_codes": allowed_metric_codes,
        "allowed_actions": allowed_actions,
        "safety_rules": [
            "Do not invent numbers, years, or provenance.",
            "Do not create trusted results by semantic judgment alone.",
            "Return only supported actions and allowed metric codes.",
            "Choose requires_table_context or requires_manual_review when evidence is insufficient.",
        ],
        "source_pack_row": source_pack_row,
    }


def build_request_payloads(
    selected_label_df: pd.DataFrame,
    selected_candidate_df: pd.DataFrame,
    prompt_templates_df: pd.DataFrame,
    output_schema: Dict[str, Any],
    allowed_metric_codes_df: pd.DataFrame,
    review_df: pd.DataFrame,
    output_dir: Path,
    mode: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    request_columns = [
        "case_id",
        "case_type",
        "prompt_text",
        "input_context",
        "output_schema",
        "allowed_metric_codes",
        "allowed_actions",
        "safety_rules",
        "source_pack_row",
    ]
    inventory_columns = [
        "case_id",
        "case_type",
        "request_file",
        "prompt_template",
        "allowed_actions",
        "selected_for_execution",
        "mode",
    ]
    template_map = {
        _norm(row.get("template_name")): _norm(row.get("prompt_text"))
        for _, row in prompt_templates_df.iterrows()
    }
    allowed_metric_codes = allowed_metric_codes_df.to_dict(orient="records") if not allowed_metric_codes_df.empty else []

    label_requests: List[Dict[str, Any]] = []
    candidate_requests: List[Dict[str, Any]] = []
    inventory_rows: List[Dict[str, Any]] = []

    review_temp = review_df.copy()
    if not review_temp.empty:
        review_temp["normalized_label"] = review_temp["raw_metric_name"].map(_normalize_label)

    for _, row in selected_label_df.iterrows():
        label_case_id = _norm(row.get("label_case_id"))
        normalized_label = _norm(row.get("normalized_label"))
        prompt_template = _norm(row.get("prompt_template")) or "label_level_alias_or_scope"
        prompt_text = template_map.get(prompt_template, "")
        matching = review_temp[review_temp["normalized_label"].astype(str) == normalized_label].copy() if not review_temp.empty else pd.DataFrame()
        example_rows = []
        if not matching.empty:
            for _, candidate_row in matching.head(5).iterrows():
                example_rows.append(
                    {
                        "table_title": _norm(candidate_row.get("table_title")),
                        "raw_metric_name": _norm(candidate_row.get("raw_metric_name")),
                        "year": _norm(candidate_row.get("year")),
                        "raw_value": _norm(candidate_row.get("raw_value")),
                        "unit": _norm(candidate_row.get("unit")) or _norm(candidate_row.get("table_unit")),
                        "split_reason": _norm(candidate_row.get("split_reason")),
                        "risk_tags_after": _norm(candidate_row.get("risk_tags_after")),
                    }
                )
        source_pack_row = {key: (_norm(value) if not isinstance(value, int) else int(value)) for key, value in row.to_dict().items()}
        payload = _request_payload_common(
            case_id=label_case_id,
            case_type="label_level",
            prompt_text=prompt_text,
            input_context={
                "normalized_label": normalized_label,
                "raw_label_examples": _split_pipe(row.get("raw_label_examples")),
                "candidate_count": int(row.get("candidate_count") or 0),
                "unique_table_count": int(row.get("unique_table_count") or 0),
                "table_title_examples": _split_pipe(row.get("table_title_examples")),
                "source_report_examples": _split_pipe(row.get("source_report_examples")),
                "value_examples": _split_pipe(row.get("value_examples")),
                "year_examples": _split_pipe(row.get("year_examples")),
                "unit_context_examples": _split_pipe(row.get("unit_context_examples")),
                "current_risk_tags": _split_pipe(row.get("current_risk_tags")),
                "candidate_category": _norm(row.get("candidate_category")),
                "selection_reason": _norm(row.get("selection_reason")),
                "example_underlying_candidates": example_rows,
            },
            output_schema=output_schema,
            allowed_metric_codes=allowed_metric_codes,
            allowed_actions=_split_pipe(row.get("allowed_actions")),
            source_pack_row=source_pack_row,
        )
        label_requests.append(payload)
        inventory_rows.append(
            {
                "case_id": label_case_id,
                "case_type": "label_level",
                "request_file": str(output_dir / "llm_label_requests_322d.jsonl"),
                "prompt_template": prompt_template,
                "allowed_actions": "|".join(payload["allowed_actions"]),
                "selected_for_execution": True,
                "mode": mode,
            }
        )

    for _, row in selected_candidate_df.iterrows():
        case_id = _norm(row.get("case_id"))
        prompt_template = _norm(row.get("prompt_template")) or "candidate_level_context_review"
        prompt_text = template_map.get(prompt_template, "")
        allowed_actions = _split_pipe(row.get("allowed_actions"))
        source_pack_row = {key: _norm(value) for key, value in row.to_dict().items()}
        payload = _request_payload_common(
            case_id=case_id,
            case_type="candidate_level",
            prompt_text=prompt_text,
            input_context={
                "table_asset_id": _norm(row.get("table_asset_id")),
                "source_report_name": _norm(row.get("source_report_name")),
                "table_title": _norm(row.get("table_title")),
                "table_context": _norm(row.get("table_context")),
                "row_label": _norm(row.get("row_label")),
                "row_values": _norm(row.get("row_values")),
                "year_columns": _norm(row.get("year_columns")),
                "unit_context": _norm(row.get("unit_context")),
                "current_metric_code": _norm(row.get("current_metric_code")),
                "current_risk_tags": _split_pipe(row.get("current_risk_tags")),
                "current_review_reason": _norm(row.get("current_review_reason")),
                "available_provenance": _norm(row.get("available_provenance")),
                "selection_reason": _norm(row.get("selection_reason")),
            },
            output_schema=output_schema,
            allowed_metric_codes=allowed_metric_codes,
            allowed_actions=allowed_actions,
            source_pack_row=source_pack_row,
        )
        candidate_requests.append(payload)
        inventory_rows.append(
            {
                "case_id": case_id,
                "case_type": "candidate_level",
                "request_file": str(output_dir / "llm_candidate_requests_322d.jsonl"),
                "prompt_template": prompt_template,
                "allowed_actions": "|".join(payload["allowed_actions"]),
                "selected_for_execution": True,
                "mode": mode,
            }
        )

    return (
        pd.DataFrame(label_requests, columns=request_columns).fillna(""),
        pd.DataFrame(candidate_requests, columns=request_columns).fillna(""),
        pd.DataFrame(inventory_rows, columns=inventory_columns).fillna(""),
    )
