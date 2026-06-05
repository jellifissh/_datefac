from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import pandas as pd


EXPECTED_324N_DECISION = "OFFICIAL_SCOPE_PATCH_CYCLE_324N_CLOSED_READY_FOR_NEXT_CYCLE_PLANNING"
READY_DECISION = "ALIAS_CANDIDATE_REFINEMENT_325A_READY_FOR_325B_ALIAS_REVIEW_BATCH"
NO_SAFE_BATCH_DECISION = "ALIAS_CANDIDATE_REFINEMENT_325A_NO_SAFE_BATCH_RECOMMEND_REMINING"
NOT_READY_DECISION = "ALIAS_CANDIDATE_REFINEMENT_325A_NOT_READY"

DEFAULT_REMAINING_BURDEN_DIR = Path(r"D:\_datefac\output\remaining_burden_planning_323p")
DEFAULT_CANDIDATE_TEXT_REPAIR_DIR = Path(r"D:\_datefac\output\candidate_text_repair_323ar")
DEFAULT_HIGH_IMPACT_MINING_DIR = Path(r"D:\_datefac\output\high_impact_semantic_candidates_mining_323a")
DEFAULT_PREVIOUS_BATCH_PREP_DIR = Path(r"D:\_datefac\output\semantic_adjudication_batch_prep_323ab")
DEFAULT_PREVIOUS_SANITY_GATE_DIR = Path(r"D:\_datefac\output\adjudication_batch_sanity_gate_323c")
DEFAULT_CYCLE_CLOSURE_DIR = Path(r"D:\_datefac\output\official_scope_patch_cycle_closure_324n")
DEFAULT_POST_PATCH_324M_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_324m")
DEFAULT_POST_PATCH_323N_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_323n")
DEFAULT_TRUST_SPLIT_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_candidate_refinement_325a")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

MAX_SAFE_BATCH_COUNT = 15

RISK_BUCKETS = [
    "SAFE_ALIAS_REVIEW_BATCH",
    "HOLDOUT_ALREADY_OFFICIAL",
    "HOLDOUT_CATEGORY_MISMATCH",
    "HOLDOUT_SCOPE_NOISE_OR_DISCLOSURE_TEXT",
    "HOLDOUT_UNIT_RELATED",
    "HOLDOUT_GENERIC_AMBIGUOUS_LABEL",
    "HOLDOUT_WEAK_EVIDENCE",
    "HOLDOUT_DUPLICATE_OR_CONFLICT",
    "HOLDOUT_NEEDS_MORE_INFO",
]

GENERIC_LABELS = {
    "流动资产",
    "流动负债",
    "资产",
    "负债",
    "权益",
    "利润",
    "收入",
    "成本",
    "费用",
    "现金",
}

CATEGORY_MISMATCH_TERMS = [
    "资产",
    "负债",
    "股东权益",
    "所有者权益",
    "商誉",
    "在建工程",
    "应付债券",
    "租赁负债",
    "合同资产",
    "合同负债",
    "长期待摊费用",
    "短期借款",
    "经营性应收",
    "经营性应付",
    "负债净变化",
    "少数股东损益",
]

SCOPE_OR_DISCLOSURE_TERMS = [
    "股票代码",
    "评级",
    "免责声明",
    "报告中投资建议",
    "优于大市",
    "弱于大市",
    "无评级",
    "行业评级",
    "公司评级",
    "其中：",
    "其他业务",
    "技术路线",
    "军工装备",
    "订单",
    "板块",
    "产品",
    "SOFC",
    "柴发",
    "核能",
    "燃气",
]

UNIT_TERMS = [
    "%",
    "（%）",
    "(%)",
    "元/股",
    "万元",
    "百万元",
    "亿元",
    "MW",
    "GW",
    "吨",
]

SAFE_METRIC_TERMS = [
    "EBIT",
    "EBITDA",
    "P/E",
    "P/B",
    "PE",
    "PB",
    "ROE",
    "EPS",
    "市盈率",
    "市净率",
    "每股收益",
    "净资产收益率",
    "经营活动现金流",
    "经营性现金流",
    "毛利率",
    "净利率",
    "归母净利润",
    "归属母公司净利润",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


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


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _split_pipe(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _join_unique(items: Iterable[Any], limit: int = 10) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        text = _norm(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(term and term.lower() in text.lower() for term in terms)


def _is_safe_metric_like(label: str) -> bool:
    return _contains_any(label, SAFE_METRIC_TERMS)


def _is_unit_related(label: str, row: pd.Series) -> bool:
    if _contains_any(label, UNIT_TERMS):
        # Valuation ratios and explicit metric names can include symbols safely.
        return not _is_safe_metric_like(label)
    risk_text = _norm(row.get("risk_signature")) + " " + _norm(row.get("sample_table_titles"))
    return "UNIT" in risk_text.upper() and not _is_safe_metric_like(label)


def _is_long_or_disclosure(label: str, row: pd.Series) -> bool:
    text = " ".join([label, _norm(row.get("sample_row_texts")), _norm(row.get("sample_table_titles"))])
    return len(label) >= 60 or _contains_any(text, SCOPE_OR_DISCLOSURE_TERMS)


def _load_official_alias_labels(alias_asset: Dict[str, Any]) -> Set[str]:
    labels: Set[str] = set()
    groups = alias_asset.get("groups", {})
    if not isinstance(groups, dict):
        return labels
    for items in groups.values():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            for key in ["normalized_label", "metric_code"]:
                label = _normalize_label(item.get(key))
                if label:
                    labels.add(label)
    return labels


def _load_official_scope_labels(scope_asset: Dict[str, Any]) -> Set[str]:
    labels: Set[str] = set()
    rules = scope_asset.get("rules", {})
    if not isinstance(rules, dict):
        return labels
    for item in rules.values():
        if not isinstance(item, dict):
            continue
        for key in ["normalized_label", "standard_metric"]:
            label = _normalize_label(item.get(key))
            if label:
                labels.add(label)
    return labels


def _load_sanity_bucket_lookup(previous_sanity_gate_dir: Path) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    gated_path = previous_sanity_gate_dir / "adjudication_batch_sanity_gate_323c_gated_batch.xlsx"
    df = _read_excel_sheet(gated_path, "gated_batch")
    if df.empty:
        return lookup
    for _, row in df.iterrows():
        if _norm(row.get("candidate_type")) != "alias":
            continue
        key = _norm(row.get("source_group_id"))
        if not key:
            continue
        lookup[key] = {
            "sanity_bucket": _norm(row.get("sanity_bucket")),
            "sanity_reasons": _norm(row.get("sanity_reasons")),
            "batch_item_id": _norm(row.get("batch_item_id")),
        }
    return lookup


def load_alias_candidate_refinement_325a_inputs(
    remaining_burden_dir: Path,
    candidate_text_repair_dir: Path,
    high_impact_mining_dir: Path,
    previous_batch_prep_dir: Path,
    previous_sanity_gate_dir: Path,
    cycle_closure_dir: Path,
    post_patch_324m_dir: Path,
    post_patch_323n_dir: Path,
    trust_split_dir: Path,
) -> Dict[str, Any]:
    return {
        "summary_323p": _read_json(remaining_burden_dir / "remaining_burden_planning_323p_summary.json"),
        "summary_323ar": _read_json(candidate_text_repair_dir / "candidate_text_repair_323ar_summary.json"),
        "summary_323a": _read_json(high_impact_mining_dir / "high_impact_semantic_candidates_mining_323a_summary.json"),
        "summary_323ab": _read_json(previous_batch_prep_dir / "semantic_adjudication_batch_prep_323ab_summary.json"),
        "summary_323c": _read_json(previous_sanity_gate_dir / "adjudication_batch_sanity_gate_323c_summary.json"),
        "summary_324n": _read_json(cycle_closure_dir / "official_scope_patch_cycle_closure_324n_summary.json"),
        "summary_324m": _read_json(post_patch_324m_dir / "post_patch_regression_validation_324m_summary.json"),
        "summary_323n": _read_json(post_patch_323n_dir / "post_patch_regression_validation_323n_summary.json"),
        "trust_summary": _read_json(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
        "review_ready_alias_df": _read_excel_sheet(
            candidate_text_repair_dir / "candidate_text_repair_323ar_review_ready_package.xlsx",
            "review_ready_alias",
        ),
        "top_alias_df": _read_excel_sheet(
            high_impact_mining_dir / "high_impact_semantic_candidates_mining_323a_top_alias_opportunities.xlsx",
            "top_opportunities",
        ),
        "previous_alias_items_df": _read_excel_sheet(
            previous_batch_prep_dir / "semantic_adjudication_batch_prep_323ab_alias_items.xlsx",
            "alias_items",
        ),
        "sanity_lookup": _load_sanity_bucket_lookup(previous_sanity_gate_dir),
        "alias_asset": _read_json(SEMANTIC_ALIAS_ASSET_PATH),
        "scope_asset": _read_json(FORMAL_SCOPE_RULES_PATH),
    }


def _build_inventory(
    review_ready_alias_df: pd.DataFrame,
    top_alias_df: pd.DataFrame,
    previous_alias_items_df: pd.DataFrame,
    sanity_lookup: Dict[str, Dict[str, str]],
) -> pd.DataFrame:
    df = review_ready_alias_df.copy().fillna("")
    if df.empty:
        return df

    if not top_alias_df.empty and "group_id" in top_alias_df.columns:
        extra_cols = [
            "group_id",
            "source_stage_signature",
            "source_report_examples",
            "table_asset_examples",
            "sample_candidate_ids",
        ]
        available = [col for col in extra_cols if col in top_alias_df.columns]
        if available:
            df = df.merge(
                top_alias_df[available].drop_duplicates(subset=["group_id"]),
                on="group_id",
                how="left",
                suffixes=("", "_323a"),
            ).fillna("")

    if not previous_alias_items_df.empty and "source_group_id" in previous_alias_items_df.columns:
        previous_cols = [
            "source_group_id",
            "batch_item_id",
            "sample_candidate_ids",
            "source_stage_signature",
            "source_report_examples",
            "table_asset_examples",
        ]
        available = [col for col in previous_cols if col in previous_alias_items_df.columns]
        previous = previous_alias_items_df[available].drop_duplicates(subset=["source_group_id"]).copy()
        df = df.merge(previous, left_on="group_id", right_on="source_group_id", how="left", suffixes=("", "_323ab")).fillna("")

    sanity_rows = []
    for _, row in df.iterrows():
        info = sanity_lookup.get(_norm(row.get("group_id")), {})
        sanity_rows.append(
            {
                "group_id": _norm(row.get("group_id")),
                "prior_323c_sanity_bucket": info.get("sanity_bucket", ""),
                "prior_323c_sanity_reasons": info.get("sanity_reasons", ""),
                "prior_323c_batch_item_id": info.get("batch_item_id", ""),
            }
        )
    df = df.merge(pd.DataFrame(sanity_rows), on="group_id", how="left").fillna("")
    df["candidate_label"] = df.apply(
        lambda row: _norm(row.get("repaired_label")) or _norm(row.get("original_label")),
        axis=1,
    )
    df["candidate_label_norm"] = df["candidate_label"].map(_normalize_label)
    return df.fillna("")


def _assign_bucket(
    row: pd.Series,
    official_alias_labels: Set[str],
    official_scope_labels: Set[str],
    seen_labels: Set[str],
) -> Tuple[str, List[str]]:
    label = _norm(row.get("candidate_label"))
    label_norm = _normalize_label(label)
    reasons: List[str] = []
    prior_bucket = _norm(row.get("prior_323c_sanity_bucket"))
    prior_reasons = _norm(row.get("prior_323c_sanity_reasons"))
    affected_review_required_count = _safe_int(row.get("affected_review_required_count"))
    priority_score = _safe_float(row.get("priority_score"))

    if label_norm in official_alias_labels or label_norm in official_scope_labels:
        return "HOLDOUT_ALREADY_OFFICIAL", ["OFFICIAL_ASSET_LABEL_OVERLAP"]
    if label_norm in seen_labels:
        return "HOLDOUT_DUPLICATE_OR_CONFLICT", ["DUPLICATE_LABEL_IN_ALIAS_INVENTORY"]
    seen_labels.add(label_norm)
    if prior_bucket == "HOLDOUT_CATEGORY_MISMATCH" or (
        _contains_any(label, CATEGORY_MISMATCH_TERMS) and not _is_safe_metric_like(label)
    ):
        reasons.append(prior_reasons or "BALANCE_SHEET_OR_STATEMENT_LINE")
        return "HOLDOUT_CATEGORY_MISMATCH", reasons
    if _is_long_or_disclosure(label, row):
        return "HOLDOUT_SCOPE_NOISE_OR_DISCLOSURE_TEXT", [prior_reasons or "DISCLOSURE_OR_SCOPE_NOISE_PATTERN"]
    if _is_unit_related(label, row):
        return "HOLDOUT_UNIT_RELATED", ["UNIT_RELATED_OR_UNIT_BEARING_LABEL"]
    if label in GENERIC_LABELS or _normalize_label(label) in {_normalize_label(item) for item in GENERIC_LABELS}:
        return "HOLDOUT_GENERIC_AMBIGUOUS_LABEL", ["BARE_GENERIC_LABEL"]
    if prior_bucket == "HOLDOUT_AMBIGUOUS":
        return "HOLDOUT_NEEDS_MORE_INFO", [prior_reasons or "PRIOR_323C_AMBIGUOUS"]
    if affected_review_required_count < 4 or priority_score < 40:
        return "HOLDOUT_WEAK_EVIDENCE", ["LOW_REVIEW_IMPACT_OR_LOW_PRIORITY"]
    if not _is_safe_metric_like(label):
        return "HOLDOUT_NEEDS_MORE_INFO", ["NO_STABLE_CORE_METRIC_SIGNAL"]
    return "SAFE_ALIAS_REVIEW_BATCH", ["SPECIFIC_METRIC_LIKE_LABEL_WITH_CACHED_EVIDENCE"]


def _score_row(row: pd.Series) -> float:
    label = _norm(row.get("candidate_label"))
    score = _safe_float(row.get("priority_score"))
    score += _safe_int(row.get("affected_review_required_count")) * 2
    if _is_safe_metric_like(label):
        score += 50
    if "UNKNOWN_METRIC_CODE" in _norm(row.get("risk_signature")):
        score += 5
    if _norm(row.get("prior_323c_sanity_bucket")) == "SEND_TO_ADJUDICATOR":
        score += 15
    return score


def build_alias_candidate_refinement_325a(
    summary_323p: Dict[str, Any],
    summary_323ar: Dict[str, Any],
    summary_323a: Dict[str, Any],
    summary_323ab: Dict[str, Any],
    summary_323c: Dict[str, Any],
    summary_324n: Dict[str, Any],
    summary_324m: Dict[str, Any],
    summary_323n: Dict[str, Any],
    trust_summary: Dict[str, Any],
    review_ready_alias_df: pd.DataFrame,
    top_alias_df: pd.DataFrame,
    previous_alias_items_df: pd.DataFrame,
    sanity_lookup: Dict[str, Dict[str, str]],
    alias_asset: Dict[str, Any],
    scope_asset: Dict[str, Any],
    output_dir: Path,
    max_safe_batch_count: int = MAX_SAFE_BATCH_COUNT,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    add_qa(
        "readiness::324n_decision",
        "PASS" if _norm(summary_324n.get("decision")) == EXPECTED_324N_DECISION else "FAIL",
        _norm(summary_324n.get("decision")),
    )
    add_qa(
        "readiness::324n_qa_fail_count",
        "PASS" if _safe_int(summary_324n.get("qa_fail_count")) == 0 else "FAIL",
        str(summary_324n.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::324n_primary_direction",
        "PASS" if _norm(summary_324n.get("recommended_next_cycle_direction_primary")) == "alias_candidates" else "FAIL",
        _norm(summary_324n.get("recommended_next_cycle_direction_primary")),
    )
    add_qa(
        "inputs::323ar_review_ready_alias_count",
        "PASS" if len(review_ready_alias_df) == _safe_int(summary_323ar.get("review_ready_alias_count")) else "FAIL",
        f"loaded={len(review_ready_alias_df)} summary={summary_323ar.get('review_ready_alias_count', '')}",
    )
    add_qa(
        "inputs::323a_alias_reference_loaded",
        "PASS" if bool(summary_323a) and not top_alias_df.empty else "FAIL",
        f"top_alias_rows={len(top_alias_df)}",
    )
    add_qa(
        "inputs::prior_routing_loaded",
        "PASS" if bool(summary_323ab) and bool(summary_323c) else "FAIL",
        f"323ab={bool(summary_323ab)} 323c={bool(summary_323c)} sanity_lookup={len(sanity_lookup)}",
    )
    add_qa(
        "inputs::post_patch_references_loaded",
        "PASS" if bool(summary_324m) and bool(summary_323n) and bool(trust_summary) else "FAIL",
        f"324m={bool(summary_324m)} 323n={bool(summary_323n)} trust_split={bool(trust_summary)}",
    )

    inventory_df = _build_inventory(review_ready_alias_df, top_alias_df, previous_alias_items_df, sanity_lookup)
    official_alias_labels = _load_official_alias_labels(alias_asset)
    official_scope_labels = _load_official_scope_labels(scope_asset)

    rows: List[Dict[str, Any]] = []
    seen_labels: Set[str] = set()
    if not inventory_df.empty:
        inventory_df = inventory_df.sort_values(
            ["priority_score", "affected_review_required_count", "affected_candidate_count", "group_id"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        for _, row in inventory_df.iterrows():
            bucket, reasons = _assign_bucket(row, official_alias_labels, official_scope_labels, seen_labels)
            item = row.to_dict()
            item["risk_bucket"] = bucket
            item["risk_bucket_reasons"] = " | ".join(reasons)
            item["alias_refinement_candidate_id"] = f"325a::alias::{len(rows) + 1:03d}"
            item["impact_score_325a"] = _score_row(row)
            item["provenance_source"] = "323A-R_review_ready_alias"
            rows.append(item)

    refined_df = pd.DataFrame(rows).fillna("")
    if refined_df.empty:
        safe_batch_df = pd.DataFrame()
        holdout_df = pd.DataFrame()
        overlap_df = pd.DataFrame()
    else:
        safe_candidates = refined_df[refined_df["risk_bucket"] == "SAFE_ALIAS_REVIEW_BATCH"].copy()
        safe_batch_df = safe_candidates.sort_values(
            ["impact_score_325a", "affected_review_required_count", "priority_score", "group_id"],
            ascending=[False, False, False, True],
        ).head(max_safe_batch_count).reset_index(drop=True)
        safe_ids = set(safe_batch_df["alias_refinement_candidate_id"].astype(str).tolist())
        refined_df.loc[
            (refined_df["risk_bucket"] == "SAFE_ALIAS_REVIEW_BATCH")
            & ~refined_df["alias_refinement_candidate_id"].astype(str).isin(safe_ids),
            "risk_bucket",
        ] = "HOLDOUT_NEEDS_MORE_INFO"
        refined_df.loc[
            refined_df["alias_refinement_candidate_id"].astype(str).isin(safe_ids),
            "safe_batch_rank",
        ] = range(1, len(safe_batch_df) + 1)
        safe_batch_df = refined_df[
            refined_df["alias_refinement_candidate_id"].astype(str).isin(safe_ids)
        ].copy().sort_values("safe_batch_rank")
        holdout_df = refined_df[refined_df["risk_bucket"] != "SAFE_ALIAS_REVIEW_BATCH"].copy()
        overlap_df = refined_df[refined_df["risk_bucket"] == "HOLDOUT_ALREADY_OFFICIAL"].copy()

    bucket_counts = {bucket: 0 for bucket in RISK_BUCKETS}
    if not refined_df.empty:
        for bucket, count in refined_df["risk_bucket"].astype(str).value_counts().to_dict().items():
            bucket_counts[bucket] = int(count)

    risk_summary_df = pd.DataFrame(
        [{"risk_bucket": bucket, "count": int(bucket_counts.get(bucket, 0))} for bucket in RISK_BUCKETS]
    )

    add_qa(
        "refinement::all_candidates_bucketed",
        "PASS" if len(refined_df) == len(inventory_df) and len(refined_df) > 0 else "FAIL",
        f"inventory={len(inventory_df)} bucketed={len(refined_df)}",
    )
    add_qa(
        "refinement::safe_batch_cap",
        "PASS" if len(safe_batch_df) <= max_safe_batch_count else "FAIL",
        f"safe_batch_count={len(safe_batch_df)} max={max_safe_batch_count}",
    )
    add_qa(
        "refinement::already_official_excluded",
        "PASS" if bucket_counts["HOLDOUT_ALREADY_OFFICIAL"] >= 1 else "FAIL",
        str(bucket_counts["HOLDOUT_ALREADY_OFFICIAL"]),
    )
    add_qa(
        "refinement::safe_batch_exists",
        "PASS" if len(safe_batch_df) > 0 else "WARN",
        str(len(safe_batch_df)),
    )
    add_qa(
        "refinement::no_safe_batch_official_overlap",
        "PASS"
        if safe_batch_df.empty
        or not any(
            _normalize_label(value) in official_alias_labels or _normalize_label(value) in official_scope_labels
            for value in safe_batch_df["candidate_label"].astype(str).tolist()
        )
        else "FAIL",
        f"safe_batch_count={len(safe_batch_df)}",
    )
    add_qa(
        "refinement::no_semantic_rule_or_proposal_generated",
        "PASS",
        "325A emits review planning artifacts only.",
    )

    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    official_assets_modified = alias_hash_before != alias_hash_after or scope_hash_before != scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if not official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )
    add_qa("safety::llm_or_adjudicator_not_called", "PASS", "325A uses cached outputs only.")
    add_qa("safety::parser_and_extraction_not_run", "PASS", "325A reads cached workbooks/json only.")

    top_safe_examples = []
    for _, row in safe_batch_df.head(5).iterrows():
        top_safe_examples.append(
            {
                "alias_refinement_candidate_id": _norm(row.get("alias_refinement_candidate_id")),
                "group_id": _norm(row.get("group_id")),
                "repaired_label": _norm(row.get("candidate_label")),
                "affected_review_required_count": _safe_int(row.get("affected_review_required_count")),
                "priority_score": _safe_float(row.get("priority_score")),
                "risk_bucket_reasons": _norm(row.get("risk_bucket_reasons")),
            }
        )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    if qa_fail_count > 0:
        decision = NOT_READY_DECISION
    elif len(safe_batch_df) > 0:
        decision = READY_DECISION
    else:
        decision = NO_SAFE_BATCH_DECISION

    summary = {
        "stage": "325A",
        "output_dir": str(output_dir),
        "input_alias_inventory_count": int(len(inventory_df)),
        "max_safe_batch_count": int(max_safe_batch_count),
        "excluded_already_official_count": bucket_counts["HOLDOUT_ALREADY_OFFICIAL"],
        "excluded_category_mismatch_count": bucket_counts["HOLDOUT_CATEGORY_MISMATCH"],
        "excluded_scope_noise_or_disclosure_text_count": bucket_counts["HOLDOUT_SCOPE_NOISE_OR_DISCLOSURE_TEXT"],
        "excluded_unit_related_count": bucket_counts["HOLDOUT_UNIT_RELATED"],
        "excluded_generic_ambiguous_label_count": bucket_counts["HOLDOUT_GENERIC_AMBIGUOUS_LABEL"],
        "excluded_weak_evidence_count": bucket_counts["HOLDOUT_WEAK_EVIDENCE"],
        "excluded_duplicate_or_conflict_count": bucket_counts["HOLDOUT_DUPLICATE_OR_CONFLICT"],
        "excluded_needs_more_info_count": bucket_counts["HOLDOUT_NEEDS_MORE_INFO"],
        "safe_alias_review_batch_count": int(len(safe_batch_df)),
        "holdout_count": int(len(holdout_df)),
        "top_safe_alias_candidate_count": int(min(len(safe_batch_df), 5)),
        "top_safe_alias_examples": top_safe_examples,
        "risk_bucket_counts": bucket_counts,
        "official_assets_modified": official_assets_modified,
        "official_assets_written": [],
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    refined_json = {
        "stage": "325A",
        "decision": decision,
        "max_safe_batch_count": max_safe_batch_count,
        "safe_alias_review_batch": safe_batch_df.to_dict(orient="records"),
        "holdout_candidates": holdout_df.to_dict(orient="records"),
        "risk_bucket_counts": bucket_counts,
    }
    no_apply_proof_json = {
        "stage": "325A",
        "decision": decision,
        "files_read": [
            str(DEFAULT_CANDIDATE_TEXT_REPAIR_DIR / "candidate_text_repair_323ar_review_ready_package.xlsx"),
            str(DEFAULT_HIGH_IMPACT_MINING_DIR / "high_impact_semantic_candidates_mining_323a_top_alias_opportunities.xlsx"),
            str(DEFAULT_PREVIOUS_BATCH_PREP_DIR / "semantic_adjudication_batch_prep_323ab_alias_items.xlsx"),
            str(DEFAULT_PREVIOUS_SANITY_GATE_DIR / "adjudication_batch_sanity_gate_323c_gated_batch.xlsx"),
            str(DEFAULT_CYCLE_CLOSURE_DIR / "official_scope_patch_cycle_closure_324n_summary.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        "official_assets_before_325a": {
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_before,
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_before,
        },
        "official_assets_after_325a": {
            str(SEMANTIC_ALIAS_ASSET_PATH): alias_hash_after,
            str(FORMAL_SCOPE_RULES_PATH): scope_hash_after,
        },
        "official_assets_written": [],
        "official_assets_modified": official_assets_modified,
    }
    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": decision,
            }
        ]
    ).fillna("")
    notes_df = pd.DataFrame(
        [
            {
                "note_type": "hard_boundary",
                "detail": "325A does not apply semantic rules, mark trusted records, produce official candidates, create proposals, or run sandbox replay.",
            },
            {
                "note_type": "safe_batch_policy",
                "detail": f"Safe alias review batch is capped at {max_safe_batch_count} and remains pending downstream review.",
            },
            {
                "note_type": "risk_policy",
                "detail": "Generic headings, unit-bearing labels, category mismatch labels, scope/disclosure text, and official overlaps are held out.",
            },
        ]
    )
    return {
        "summary": summary,
        "qa_json": qa_json,
        "refined_json": refined_json,
        "no_apply_proof_json": no_apply_proof_json,
        "refined_alias_candidates_df": refined_df,
        "safe_batch_df": safe_batch_df,
        "holdout_df": holdout_df,
        "overlap_df": overlap_df,
        "risk_summary_df": risk_summary_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "notes_df": notes_df,
    }
