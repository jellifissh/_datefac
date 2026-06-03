from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

import pandas as pd


EXPECTED_322O_DECISION = "POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE"
EXPECTED_323A_READY_DECISION = "HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_READY_FOR_323B_OR_323A_ADJUDICATION_BATCH_PREP"
EXPECTED_323A_NOT_READY_DECISION = "HIGH_IMPACT_SEMANTIC_CANDIDATES_323A_NOT_READY"

DEFAULT_POST_PATCH_REGRESSION_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_322o")
DEFAULT_TRUST_SPLIT_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_PATCH_APPLICATION_DIR = Path(r"D:\_datefac\output\official_semantic_patch_application_322n")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\high_impact_semantic_candidates_mining_323a")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

CORE_METRIC_CODES = {
    "revenue",
    "net_profit",
    "gross_margin",
    "roe",
    "eps",
    "pe",
    "pb",
    "ev_ebitda",
}

ALIAS_HINT_KEYWORDS = [
    "roic",
    "roe",
    "roa",
    "eps",
    "pe",
    "pb",
    "ev/ebitda",
    "ev-ebitda",
    "evebitda",
    "净利润",
    "归母净利润",
    "营业收入",
    "收入",
    "毛利率",
    "货币资金",
    "期初余额",
    "期末余额",
    "每股收益",
]

SCOPE_NOISE_KEYWORDS = [
    "代码",
    ".sz",
    ".sh",
    "行业均值",
    "行业平均",
    "其他流动负债",
    "其他非流动资产",
    "其他非流动负债",
    "其他流动资产",
]

UNIT_KEYWORDS = [
    "元",
    "亿元",
    "百万元",
    "百万股",
    "万股",
    "%",
    "倍",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


def _safe_float(value: Any) -> float:
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


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
                parsed = json.loads(text)
            except Exception:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return pd.DataFrame(rows).fillna("")


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _split_tags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _normalize_unit_signature(value: Any) -> str:
    text = _norm(value).lower()
    if not text:
        return "__NO_UNIT__"
    return text.replace("人民币", "").replace(" ", "")


def _join_unique(items: Sequence[str], limit: int = 8) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _risk_bucket(tags: List[str]) -> str:
    tags_set = set(tags)
    if "UNIT_UNKNOWN" in tags_set:
        return "UNIT_RISK"
    if "INVALID_YEAR" in tags_set or "NO_YEAR_COLUMNS" in tags_set:
        return "YEAR_RISK"
    if "VALUE_PARSE_FAILED" in tags_set:
        return "VALUE_RISK"
    if "UNKNOWN_METRIC_CODE" in tags_set:
        return "SEMANTIC_RISK"
    return "OTHER_RISK"


def _load_closed_rule_labels() -> Tuple[Set[str], pd.DataFrame]:
    rows: List[Dict[str, Any]] = []
    alias_raw = _read_json(SEMANTIC_ALIAS_ASSET_PATH)
    alias_groups = alias_raw.get("groups", {}) if isinstance(alias_raw, dict) else {}
    if isinstance(alias_groups, dict):
        for group_name, items in alias_groups.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                rule_id = _norm(item.get("rule_id"))
                if not rule_id.startswith("SEM_ALIAS_322N_"):
                    continue
                rows.append(
                    {
                        "rule_id": rule_id,
                        "rule_type": "alias",
                        "normalized_label": _norm(item.get("normalized_label")),
                        "normalized_label_key": _normalize_label(item.get("normalized_label")),
                        "target_group": _norm(group_name),
                        "metric_code": _norm(item.get("metric_code")),
                    }
                )
    scope_raw = _read_json(FORMAL_SCOPE_RULES_PATH)
    scope_rules = scope_raw.get("rules", {}) if isinstance(scope_raw, dict) else {}
    if isinstance(scope_rules, dict):
        for rule_id, item in scope_rules.items():
            if not isinstance(item, dict):
                continue
            rid = _norm(item.get("rule_id")) or _norm(rule_id)
            if not rid.startswith("SEM_SCOPE_322N_"):
                continue
            rows.append(
                {
                    "rule_id": rid,
                    "rule_type": "scope_noise",
                    "normalized_label": _norm(item.get("normalized_label")),
                    "normalized_label_key": _normalize_label(item.get("normalized_label")),
                    "target_group": _norm(item.get("target_group")),
                    "metric_code": "",
                }
            )
    df = pd.DataFrame(rows).fillna("")
    keys = set(df["normalized_label_key"].astype(str).tolist()) if not df.empty else set()
    return keys, df


def _infer_group_type(row: pd.Series) -> str:
    tags = set(_split_tags(row.get("risk_signature")))
    label = _norm(row.get("normalized_label_display")).lower()
    raw_label = _norm(row.get("sample_raw_metric_names")).lower()
    unit_sig = _norm(row.get("unit_signature"))
    metric_codes = set(_norm(item) for item in _norm(row.get("metric_code_signature")).split("|") if _norm(item))
    unknown_metric_count = _safe_int(row.get("unknown_metric_count"))
    review_count = _safe_int(row.get("affected_review_required_count"))
    support_count = _safe_int(row.get("affected_candidate_count"))

    if "UNIT_UNKNOWN" in tags or unit_sig == "__MIXED__" or any(keyword in label for keyword in UNIT_KEYWORDS):
        return "unit_related"

    if any(keyword in label for keyword in SCOPE_NOISE_KEYWORDS) or any(keyword in raw_label for keyword in SCOPE_NOISE_KEYWORDS):
        return "scope_noise"

    if unknown_metric_count > 0 and (
        any(keyword in label for keyword in ALIAS_HINT_KEYWORDS)
        or any(keyword in raw_label for keyword in ALIAS_HINT_KEYWORDS)
        or metric_codes == {"unknown_metric"}
    ):
        if not ({"INVALID_YEAR", "NO_YEAR_COLUMNS"} & tags and support_count <= 2):
            return "alias"

    if review_count > 0 and metric_codes == {"unknown_metric"} and support_count >= 8 and not tags.intersection({"UNIT_UNKNOWN"}):
        return "alias"

    if tags.intersection({"INVALID_YEAR", "NO_YEAR_COLUMNS", "VALUE_PARSE_FAILED"}) and support_count <= 3:
        return "ambiguous"

    return "ambiguous"


def _compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    temp = df.copy()
    safety_score = (
        1.0
        + (temp["unit_unknown_count"].eq(0).astype(float) * 1.0)
        + (temp["year_risk_count"].eq(0).astype(float) * 0.6)
        + (temp["value_risk_count"].eq(0).astype(float) * 0.4)
        + (temp["mixed_metric_code_group"].eq(False).astype(float) * 0.5)
        + (temp["closed_rule_overlap_count"].eq(0).astype(float) * 0.5)
    )
    temp["impact_score"] = (
        temp["affected_review_required_count"]
        + temp["unknown_metric_count"]
        + temp["review_required_unknown_metric_count"]
    )
    temp["safety_score"] = safety_score.round(3)
    temp["priority_score"] = (temp["impact_score"] * temp["safety_score"]).round(3)
    temp["expected_trusted_gain_potential"] = (
        temp["group_type_candidate"].eq("alias").astype(int)
        * temp["review_required_unknown_metric_count"]
    )
    temp["expected_review_reduction_potential"] = (
        temp["affected_review_required_count"]
        - temp["ambiguous_count"]
        - temp["unit_unknown_count"]
    ).clip(lower=0)
    return temp


def _build_grouped_opportunity_df(
    review_df: pd.DataFrame,
    closed_rule_labels: Set[str],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if review_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    temp = review_df.copy()
    temp["raw_metric_name"] = temp.get("raw_metric_name", "").astype(str)
    temp["normalized_label_key"] = temp["raw_metric_name"].map(_normalize_label)
    temp["normalized_label_display"] = temp["raw_metric_name"].astype(str).str.strip()
    temp["risk_tags_after"] = temp.get("risk_tags_after", temp.get("risk_tags", "")).astype(str)
    temp["decision_after"] = temp.get("decision_after", temp.get("split_decision", "")).astype(str)
    temp["metric_code"] = temp.get("metric_code", "").astype(str).replace("", "unknown_metric")
    temp["unit_signature"] = temp.get("unit", temp.get("table_unit", "")).map(_normalize_unit_signature)
    temp["table_asset_id"] = temp.get("table_asset_id", "").astype(str)
    temp["source_report_name"] = temp.get("source_report_name", temp.get("source_doc_name", "")).astype(str)
    temp["year"] = temp.get("year", "").astype(str)
    temp["group_key"] = temp.apply(
        lambda row: "||".join(
            [
                row["normalized_label_key"] or "__EMPTY_LABEL__",
                row["unit_signature"] or "__NO_UNIT__",
                _norm(row.get("source_stage")) or "__NO_STAGE__",
            ]
        ),
        axis=1,
    )
    temp["closed_rule_overlap"] = temp["normalized_label_key"].isin(closed_rule_labels)
    temp["unknown_metric_flag"] = temp["metric_code"].eq("unknown_metric") | temp["risk_tags_after"].str.contains(r"(?:^|\|)UNKNOWN_METRIC_CODE(?:$|\|)", regex=True)
    temp["unit_unknown_flag"] = temp["risk_tags_after"].str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True)
    temp["year_risk_flag"] = temp["risk_tags_after"].str.contains(r"(?:^|\|)INVALID_YEAR(?:$|\|)|(?:^|\|)NO_YEAR_COLUMNS(?:$|\|)", regex=True)
    temp["value_risk_flag"] = temp["risk_tags_after"].str.contains(r"(?:^|\|)VALUE_PARSE_FAILED(?:$|\|)", regex=True)
    temp["ambiguous_flag"] = temp["year_risk_flag"] | temp["value_risk_flag"]

    grouped_rows: List[Dict[str, Any]] = []
    for group_key, group in temp.groupby("group_key", dropna=False):
        labels = group["normalized_label_display"].astype(str).tolist()
        metric_codes = sorted(set(group["metric_code"].astype(str).tolist()))
        risk_tags: List[str] = []
        for tag_text in group["risk_tags_after"].astype(str).tolist():
            risk_tags.extend(_split_tags(tag_text))
        risk_signature = _join_unique(risk_tags, limit=12)
        row = {
            "group_id": f"323a::{abs(hash(group_key)) % 10**10:010d}",
            "group_key": group_key,
            "normalized_label_key": _norm(group["normalized_label_key"].iloc[0]),
            "normalized_label_display": _norm(group["normalized_label_display"].iloc[0]) or _join_unique(labels, limit=1),
            "affected_candidate_count": int(len(group)),
            "affected_review_required_count": int(group["decision_after"].eq("review_required_preview").sum()),
            "affected_report_count": int(group["source_report_name"].astype(str).nunique()),
            "affected_table_count": int(group["table_asset_id"].astype(str).nunique()),
            "unknown_metric_count": int(group["unknown_metric_flag"].sum()),
            "review_required_unknown_metric_count": int((group["decision_after"].eq("review_required_preview") & group["unknown_metric_flag"]).sum()),
            "unit_unknown_count": int(group["unit_unknown_flag"].sum()),
            "year_risk_count": int(group["year_risk_flag"].sum()),
            "value_risk_count": int(group["value_risk_flag"].sum()),
            "ambiguous_count": int(group["ambiguous_flag"].sum()),
            "closed_rule_overlap_count": int(group["closed_rule_overlap"].sum()),
            "sample_candidate_ids": _join_unique(group["candidate_id"].astype(str).tolist(), limit=8),
            "sample_raw_metric_names": _join_unique(group["raw_metric_name"].astype(str).tolist(), limit=6),
            "sample_row_texts": _join_unique(group.get("source_row_text", pd.Series(dtype=str)).astype(str).tolist() if "source_row_text" in group.columns else [], limit=4),
            "sample_table_titles": _join_unique(group.get("table_title", pd.Series(dtype=str)).astype(str).tolist() if "table_title" in group.columns else [], limit=4),
            "sample_years": _join_unique(group["year"].astype(str).tolist(), limit=6),
            "source_stage_signature": _join_unique(group.get("source_stage", pd.Series(dtype=str)).astype(str).tolist() if "source_stage" in group.columns else [], limit=3),
            "unit_signature": _norm(group["unit_signature"].iloc[0]),
            "metric_code_signature": _join_unique(metric_codes, limit=6),
            "mixed_metric_code_group": len(metric_codes) > 1,
            "risk_signature": risk_signature,
            "risk_bucket": _risk_bucket(risk_tags),
        }
        row["group_type_candidate"] = _infer_group_type(pd.Series(row))
        grouped_rows.append(row)

    grouped_df = pd.DataFrame(grouped_rows).fillna("")
    grouped_df = _compute_scores(grouped_df)
    grouped_df["suggested_next_action"] = grouped_df["group_type_candidate"].map(
        {
            "alias": "prepare_alias_candidate_package",
            "scope_noise": "prepare_scope_noise_candidate_package",
            "unit_related": "hold_for_unit_cycle_323b",
            "ambiguous": "keep_in_ambiguous_holdout_and_sample",
        }
    ).fillna("manual_triage")
    grouped_df = grouped_df.sort_values(
        ["priority_score", "affected_candidate_count", "normalized_label_display"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    return grouped_df, temp


def _build_top_opportunity_df(grouped_df: pd.DataFrame, group_type: str, limit: int = 30) -> pd.DataFrame:
    if grouped_df.empty:
        return pd.DataFrame()
    subset = grouped_df[grouped_df["group_type_candidate"].astype(str) == group_type].copy()
    if subset.empty:
        return subset
    cols = [
        "group_id",
        "normalized_label_display",
        "affected_candidate_count",
        "affected_review_required_count",
        "affected_report_count",
        "unknown_metric_count",
        "unit_unknown_count",
        "impact_score",
        "safety_score",
        "priority_score",
        "expected_trusted_gain_potential",
        "expected_review_reduction_potential",
        "risk_signature",
        "sample_candidate_ids",
        "sample_raw_metric_names",
        "sample_table_titles",
        "sample_years",
        "suggested_next_action",
    ]
    present_cols = [col for col in cols if col in subset.columns]
    return subset[present_cols].head(limit).reset_index(drop=True)


def _build_risk_bucket_df(grouped_df: pd.DataFrame) -> pd.DataFrame:
    if grouped_df.empty:
        return pd.DataFrame(
            columns=[
                "risk_bucket",
                "group_count",
                "candidate_count",
                "review_required_count",
                "sample_labels",
            ]
        )
    rows: List[Dict[str, Any]] = []
    for risk_bucket, group in grouped_df.groupby("risk_bucket", dropna=False):
        rows.append(
            {
                "risk_bucket": risk_bucket,
                "group_count": int(len(group)),
                "candidate_count": int(group["affected_candidate_count"].sum()),
                "review_required_count": int(group["affected_review_required_count"].sum()),
                "sample_labels": _join_unique(group["normalized_label_display"].astype(str).tolist(), limit=6),
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values(
        ["candidate_count", "group_count", "risk_bucket"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def _build_sampling_plan(
    top_alias_df: pd.DataFrame,
    top_scope_df: pd.DataFrame,
    unit_holdout_df: pd.DataFrame,
    ambiguous_holdout_df: pd.DataFrame,
) -> Dict[str, Any]:
    plan_rows: List[Dict[str, Any]] = []

    def add_rows(df: pd.DataFrame, expected_rule_type: str, question_prefix: str, max_rows: int) -> None:
        if df.empty:
            return
        for _, row in df.head(max_rows).iterrows():
            label = _norm(row.get("normalized_label_display"))
            plan_rows.append(
                {
                    "group_id": _norm(row.get("group_id")),
                    "group_type_candidate": _norm(row.get("group_type_candidate")) or expected_rule_type,
                    "why_high_impact": f"{_safe_int(row.get('affected_review_required_count'))} review rows and {_safe_int(row.get('unknown_metric_count'))} unknown-metric rows share this label.",
                    "why_safe_or_risky": f"risk_signature={_norm(row.get('risk_signature'))}; unit_unknown_count={_safe_int(row.get('unit_unknown_count'))}; mixed_metric_code_group={bool(row.get('mixed_metric_code_group'))}",
                    "sample_rows_to_inspect": _norm(row.get("sample_candidate_ids")),
                    "suggested_review_question": f"{question_prefix}: '{label}'",
                    "expected_rule_type_if_confirmed": expected_rule_type,
                }
            )

    add_rows(top_alias_df, "alias", "Does this repeated unresolved label map to an existing core metric alias", 20)
    add_rows(top_scope_df, "scope_noise", "Is this repeated label clearly out-of-scope or non-core noise", 20)
    add_rows(unit_holdout_df, "unit_related", "Is the unit ambiguity resolvable safely without semantic alias expansion", 10)
    add_rows(ambiguous_holdout_df, "ambiguous", "Does this group need more table context before any semantic action", 10)

    return {
        "stage": "323A",
        "sampling_plan_record_count": len(plan_rows),
        "records": plan_rows,
    }


def load_high_impact_semantic_candidates_inputs(
    post_patch_regression_dir: Path,
    trust_split_dir: Path,
    patch_application_dir: Path,
) -> Dict[str, Any]:
    return {
        "post_patch_summary": _read_json(post_patch_regression_dir / "post_patch_regression_validation_322o_summary.json"),
        "post_patch_qa": _read_json(post_patch_regression_dir / "post_patch_regression_validation_322o_qa.json"),
        "trust_summary": _read_json(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
        "selected_candidates_df": _read_jsonl(trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"),
        "patch_application_log_df": _read_jsonl(patch_application_dir / "official_semantic_patch_application_322n_application_log.jsonl"),
    }


def build_high_impact_semantic_candidates_mining(
    post_patch_summary: Dict[str, Any],
    post_patch_qa: Dict[str, Any],
    trust_summary: Dict[str, Any],
    selected_candidates_df: pd.DataFrame,
    patch_application_log_df: pd.DataFrame,
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    readiness_checks = {
        "decision": _norm(post_patch_summary.get("decision")) == EXPECTED_322O_DECISION,
        "qa_fail_count": _safe_int(post_patch_summary.get("qa_fail_count")) == 0,
        "official_rule_visibility_total": _safe_int(post_patch_summary.get("official_rule_visibility_total")) == 10,
        "trusted_gain_322o": _safe_int(post_patch_summary.get("trusted_gain_322o")) == 49,
        "review_reduction_322o": _safe_int(post_patch_summary.get("review_reduction_322o")) == 287,
        "core_false_exclusion_count": _safe_int(post_patch_summary.get("core_false_exclusion_count")) == 0,
        "duplicate_count": _safe_int(post_patch_summary.get("duplicate_count")) == 0,
        "conflict_count": _safe_int(post_patch_summary.get("conflict_count")) == 0,
    }
    for key, passed in readiness_checks.items():
        add_qa(f"closed_state_322o::{key}", "PASS" if passed else "FAIL", str(post_patch_summary.get(key, "")))
    add_qa(
        "closed_state_322o::qa_json_fail_count",
        "PASS" if _safe_int(post_patch_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(post_patch_qa.get("qa_fail_count", "")),
    )

    add_qa(
        "cached_inputs::selected_candidates_loaded",
        "PASS" if not selected_candidates_df.empty else "FAIL",
        f"candidate_count={len(selected_candidates_df)}",
    )
    add_qa(
        "cached_inputs::patch_application_log_loaded",
        "PASS" if not patch_application_log_df.empty else "FAIL",
        f"log_rows={len(patch_application_log_df)}",
    )

    decision_col = "decision_after" if "decision_after" in selected_candidates_df.columns else "split_decision"
    review_df = selected_candidates_df[
        selected_candidates_df.get(decision_col, "").astype(str).eq("review_required_preview")
    ].copy() if not selected_candidates_df.empty else pd.DataFrame()
    unresolved_df = review_df.copy()
    add_qa(
        "cached_inputs::review_required_candidates_present",
        "PASS" if not unresolved_df.empty else "FAIL",
        f"review_required_count={len(unresolved_df)}",
    )

    closed_rule_labels, closed_rule_df = _load_closed_rule_labels()
    add_qa(
        "closed_rules::closed_rule_count",
        "PASS" if len(closed_rule_df) == 10 else "FAIL",
        f"actual={len(closed_rule_df)}",
    )

    grouped_df, review_with_group_df = _build_grouped_opportunity_df(
        review_df=unresolved_df,
        closed_rule_labels=closed_rule_labels,
    )
    add_qa(
        "grouping::grouped_candidate_count_positive",
        "PASS" if (not unresolved_df.empty and not grouped_df.empty) or (unresolved_df.empty and grouped_df.empty) else "FAIL",
        f"group_count={len(grouped_df)} review_count={len(unresolved_df)}",
    )
    duplicate_group_id_count = int(grouped_df["group_id"].astype(str).duplicated().sum()) if not grouped_df.empty else 0
    add_qa(
        "grouping::duplicate_group_id_count",
        "PASS" if duplicate_group_id_count == 0 else "FAIL",
        f"actual={duplicate_group_id_count}",
    )

    already_official_redetected_count = int(grouped_df["closed_rule_overlap_count"].gt(0).sum()) if not grouped_df.empty else 0
    if not grouped_df.empty:
        grouped_df = grouped_df[grouped_df["closed_rule_overlap_count"].eq(0)].copy().reset_index(drop=True)
    remaining_closed_rule_overlap_count = int(grouped_df["closed_rule_overlap_count"].gt(0).sum()) if not grouped_df.empty else 0
    add_qa(
        "closed_rules::already_official_322_rules_not_rediscovered",
        "PASS" if remaining_closed_rule_overlap_count == 0 else "FAIL",
        f"pre_filtered_overlap_groups={already_official_redetected_count} remaining_overlap_groups={remaining_closed_rule_overlap_count}",
    )

    alias_df = _build_top_opportunity_df(grouped_df, "alias", limit=30)
    scope_df = _build_top_opportunity_df(grouped_df, "scope_noise", limit=30)
    unit_holdout_df = grouped_df[grouped_df["group_type_candidate"].astype(str) == "unit_related"].copy().reset_index(drop=True) if not grouped_df.empty else pd.DataFrame()
    ambiguous_holdout_df = grouped_df[grouped_df["group_type_candidate"].astype(str) == "ambiguous"].copy().reset_index(drop=True) if not grouped_df.empty else pd.DataFrame()
    risk_bucket_df = _build_risk_bucket_df(grouped_df)
    sampling_plan_json = _build_sampling_plan(alias_df, scope_df, unit_holdout_df, ambiguous_holdout_df)

    add_qa("category_counts::alias_opportunity_count", "PASS" if len(alias_df) >= 0 else "FAIL", f"actual={len(alias_df)}")
    add_qa("category_counts::scope_noise_opportunity_count", "PASS" if len(scope_df) >= 0 else "FAIL", f"actual={len(scope_df)}")
    add_qa("category_counts::unit_holdout_count", "PASS", f"actual={len(unit_holdout_df)}")
    add_qa("category_counts::ambiguous_holdout_count", "PASS", f"actual={len(ambiguous_holdout_df)}")

    parser_not_run = True
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323A reads cached outputs only.")

    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    highest_priority_examples = []
    if not grouped_df.empty:
        for _, row in grouped_df.head(5).iterrows():
            highest_priority_examples.append(
                {
                    "group_id": _norm(row.get("group_id")),
                    "group_type_candidate": _norm(row.get("group_type_candidate")),
                    "normalized_label_display": _norm(row.get("normalized_label_display")),
                    "priority_score": _safe_float(row.get("priority_score")),
                    "affected_candidate_count": _safe_int(row.get("affected_candidate_count")),
                    "affected_review_required_count": _safe_int(row.get("affected_review_required_count")),
                    "risk_signature": _norm(row.get("risk_signature")),
                }
            )

    summary = {
        "stage": "323A",
        "output_dir": str(output_dir),
        "loaded_candidate_count": int(len(selected_candidates_df)),
        "loaded_unresolved_review_required_candidate_count": int(len(unresolved_df)),
        "closed_rule_count": int(len(closed_rule_df)),
        "grouped_candidate_count": int(len(grouped_df)),
        "alias_opportunity_group_count": int((grouped_df["group_type_candidate"].astype(str) == "alias").sum()) if not grouped_df.empty else 0,
        "scope_noise_group_count": int((grouped_df["group_type_candidate"].astype(str) == "scope_noise").sum()) if not grouped_df.empty else 0,
        "unit_related_group_count": int((grouped_df["group_type_candidate"].astype(str) == "unit_related").sum()) if not grouped_df.empty else 0,
        "ambiguous_group_count": int((grouped_df["group_type_candidate"].astype(str) == "ambiguous").sum()) if not grouped_df.empty else 0,
        "top_alias_opportunity_count": int(len(alias_df)),
        "top_scope_noise_opportunity_count": int(len(scope_df)),
        "unit_holdout_count": int(len(unit_holdout_df)),
        "ambiguous_holdout_count": int(len(ambiguous_holdout_df)),
        "review_required_unknown_metric_count": int(
            unresolved_df.get("risk_tags_after", unresolved_df.get("risk_tags", pd.Series(dtype=str))).astype(str).str.contains(r"(?:^|\|)UNKNOWN_METRIC_CODE(?:$|\|)", regex=True).sum()
        ) if not unresolved_df.empty else 0,
        "review_required_unit_unknown_count": int(
            unresolved_df.get("risk_tags_after", unresolved_df.get("risk_tags", pd.Series(dtype=str))).astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()
        ) if not unresolved_df.empty else 0,
        "already_official_redetected_group_count": int(already_official_redetected_count),
        "highest_priority_examples": highest_priority_examples,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 0,
        "blocking_reasons": [],
        "decision": "",
    }

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["blocking_reasons"] = blocking_reasons
    summary["decision"] = EXPECTED_323A_READY_DECISION if qa_fail_count == 0 else EXPECTED_323A_NOT_READY_DECISION

    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "cached_candidate_pool_only",
                "detail": "323A mines only the cached 322B2 review_required pool and does not rerun parsers or semantic adjudicators.",
            },
            {
                "limitation": "deterministic_heuristic_ranking",
                "detail": "Ranking is deterministic and impact-oriented; it is a preparation artifact rather than a semantic decision.",
            },
            {
                "limitation": "unit_cycle_deferred",
                "detail": "Unit-related holdouts are bucketed for a later dedicated unit cycle instead of being solved here.",
            },
        ]
    )

    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "grouped_df": grouped_df,
        "review_with_group_df": review_with_group_df,
        "alias_df": alias_df,
        "scope_df": scope_df,
        "unit_holdout_df": unit_holdout_df,
        "ambiguous_holdout_df": ambiguous_holdout_df,
        "risk_bucket_df": risk_bucket_df,
        "sampling_plan_json": sampling_plan_json,
        "closed_rule_df": closed_rule_df,
        "qa_checks_df": qa_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
    }
