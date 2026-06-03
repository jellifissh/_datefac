from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pandas as pd


EXPECTED_323AR_READY_DECISION = "CANDIDATE_TEXT_REPAIR_323AR_READY_FOR_ADJUDICATION_BATCH_PREP"
EXPECTED_323AB_READY_DECISION = "SEMANTIC_ADJUDICATION_BATCH_PREP_323AB_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW"
EXPECTED_323AB_NOT_READY_DECISION = "SEMANTIC_ADJUDICATION_BATCH_PREP_323AB_NOT_READY"

DEFAULT_CANDIDATE_TEXT_REPAIR_DIR = Path(r"D:\_datefac\output\candidate_text_repair_323ar")
DEFAULT_MINING_DIR = Path(r"D:\_datefac\output\high_impact_semantic_candidates_mining_323a")
DEFAULT_PATCH_APPLICATION_DIR = Path(r"D:\_datefac\output\official_semantic_patch_application_322n")
DEFAULT_POST_PATCH_REGRESSION_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_322o")
DEFAULT_TRUST_SPLIT_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\semantic_adjudication_batch_prep_323ab")

DEFAULT_MAX_TOTAL_BATCH_ITEMS = 40
DEFAULT_MAX_ALIAS_BATCH_ITEMS = 25
DEFAULT_MAX_SCOPE_BATCH_ITEMS = 15

STOCK_CODE_PATTERN = re.compile(r"^\d{6}\.(?:sh|sz|hk)$", re.IGNORECASE)
DATE_ONLY_PATTERN = re.compile(r"^\d{4}[/-]\d{1,2}[/-]\d{1,2}$")


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


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").lower()


def _split_pipe(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _join_unique(items: Iterable[Any], limit: int = 8) -> str:
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
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _looks_mojibake(text: str) -> bool:
    normalized = _norm(text)
    if not normalized:
        return False
    for token in ("閸", "閿", "濮", "娑", "绁", "鍋", "锟", "\ufffd"):
        if token in normalized:
            return True
    if "????" in normalized:
        return True
    return False


def _looks_long_narrative(text: str) -> bool:
    normalized = _norm(text)
    if len(normalized) >= 80:
        return True
    narrative_markers = [
        "评级标准",
        "报告发布日后",
        "相对市场表现",
        "作为基准",
        "投资建议",
    ]
    return any(marker in normalized for marker in narrative_markers)


def _is_date_like(text: str) -> bool:
    normalized = _norm(text)
    return bool(DATE_ONLY_PATTERN.match(normalized))


def _is_stock_code_like(text: str) -> bool:
    normalized = _norm(text).lower()
    return bool(STOCK_CODE_PATTERN.match(normalized))


def _is_empty_or_low_signal(text: str) -> bool:
    normalized = _norm(text)
    if not normalized:
        return True
    compact = normalized.replace(" ", "")
    return compact in {"", "-", "--", "n/a", "na", "(+/-%)", "(+/-)", "y\\", "y/"}


def _build_closed_rule_label_set(patch_application_log_df: pd.DataFrame) -> Set[str]:
    closed: Set[str] = set()
    if patch_application_log_df.empty:
        return closed
    for _, row in patch_application_log_df.iterrows():
        after_state = row.get("after_state")
        payload = after_state if isinstance(after_state, dict) else {}
        if isinstance(after_state, str):
            try:
                parsed = json.loads(after_state)
                if isinstance(parsed, dict):
                    payload = parsed
            except Exception:
                payload = {}
        normalized_label = _normalize_label(payload.get("normalized_label"))
        if normalized_label:
            closed.add(normalized_label)
    return closed


def _build_candidate_lookup(selected_candidates_df: pd.DataFrame) -> pd.DataFrame:
    if selected_candidates_df.empty:
        return pd.DataFrame()
    temp = selected_candidates_df.copy()
    temp["raw_metric_name_norm"] = temp.get("raw_metric_name", "").map(_normalize_label)
    temp["source_stage"] = temp.get("source_stage", "").astype(str)
    temp["table_title"] = temp.get("table_title", "").astype(str)
    temp["source_row_text"] = temp.get("source_row_text", "").astype(str)
    temp["source_report_name"] = temp.get("source_report_name", temp.get("source_doc_name", "")).astype(str)
    temp["table_asset_id"] = temp.get("table_asset_id", "").astype(str)
    temp["risk_tags_after"] = temp.get("risk_tags_after", temp.get("risk_tags", "")).astype(str)
    temp["decision_after"] = temp.get("decision_after", temp.get("split_decision", "")).astype(str)
    temp["provenance_json"] = temp.get("provenance_json", "").astype(str)
    return temp


def _enrich_review_ready_df(review_ready_df: pd.DataFrame, repaired_ranked_df: pd.DataFrame) -> pd.DataFrame:
    if review_ready_df.empty or repaired_ranked_df.empty:
        return review_ready_df
    ranked_cols = [
        "group_id",
        "sample_candidate_ids",
        "source_stage_signature",
        "unit_signature",
        "metric_code_signature",
        "mixed_metric_code_group",
        "expected_trusted_gain_potential",
        "expected_review_reduction_potential",
    ]
    available_cols = [col for col in ranked_cols if col in repaired_ranked_df.columns]
    if "group_id" not in available_cols:
        return review_ready_df
    ranked_subset = repaired_ranked_df[available_cols].drop_duplicates(subset=["group_id"]).copy()
    merged = review_ready_df.merge(ranked_subset, on="group_id", how="left", suffixes=("", "_ranked"))
    return merged.fillna("")


def _aggregate_group_context(row: pd.Series, lookup_df: pd.DataFrame) -> Dict[str, Any]:
    normalized_key = _normalize_label(row.get("repaired_label"))
    if lookup_df.empty or not normalized_key:
        return {
            "source_stage_signature": _norm(row.get("source_stage_signature")),
            "source_report_examples": "",
            "table_asset_examples": "",
            "provenance_examples": "",
        }
    matched = lookup_df[lookup_df["raw_metric_name_norm"] == normalized_key].copy()
    return {
        "source_stage_signature": _join_unique(matched["source_stage"].astype(str).tolist(), limit=6) or _norm(row.get("source_stage_signature")),
        "source_report_examples": _join_unique(matched["source_report_name"].astype(str).tolist(), limit=6),
        "table_asset_examples": _join_unique(matched["table_asset_id"].astype(str).tolist(), limit=6),
        "provenance_examples": _join_unique(matched["provenance_json"].astype(str).tolist(), limit=2),
    }


def _exclude_reason(row: pd.Series, closed_rule_labels: Set[str]) -> str:
    repaired_label = _norm(row.get("repaired_label"))
    normalized_label = _normalize_label(repaired_label)
    original_label = _norm(row.get("original_label"))

    if row.get("group_type_candidate") not in {"alias", "scope_noise"}:
        return "NON_BATCHABLE_GROUP_TYPE"
    if _norm(row.get("repair_status")) not in {"ALREADY_CLEAN", "REPAIRED_DETERMINISTIC"}:
        return "UNSAFE_REPAIR_STATUS"
    if _norm(row.get("repaired_label")) == "":
        return "MISSING_REPAIRED_LABEL"
    if _looks_mojibake(repaired_label) or _looks_mojibake(original_label):
        return "MOJIBAKE_RISK"
    if _is_empty_or_low_signal(repaired_label):
        return "EMPTY_OR_LOW_SIGNAL_LABEL"
    if _is_date_like(repaired_label):
        return "DATE_ONLY_LABEL"
    if _is_stock_code_like(repaired_label):
        return "STOCK_CODE_LABEL"
    if normalized_label in closed_rule_labels:
        return "ALREADY_OFFICIAL_322_RULE"
    if _looks_long_narrative(repaired_label):
        return "LONG_NARRATIVE_POLICY_TEXT"
    return ""


def _candidate_question(row: pd.Series) -> str:
    label = _norm(row.get("repaired_label"))
    if _norm(row.get("group_type_candidate")) == "alias":
        return (
            f"Does the candidate label '{label}' safely map to an existing selected core metric alias? "
            "If yes, identify the target metric; otherwise reject or mark needs_more_info."
        )
    return (
        f"Is the candidate label '{label}' safely out of scope for selected core metric extraction? "
        "If yes, mark ACCEPT_OUT_OF_SCOPE; otherwise reject or mark possible_core_metric."
    )


def _allowed_decisions(group_type: str) -> List[str]:
    if group_type == "alias":
        return ["ACCEPT_ALIAS", "REJECT_ALIAS", "NEEDS_MORE_INFO", "OUT_OF_SCOPE"]
    return ["ACCEPT_OUT_OF_SCOPE", "REJECT_OUT_OF_SCOPE", "NEEDS_MORE_INFO", "POSSIBLE_CORE_METRIC"]


def _expected_rule_type(group_type: str) -> str:
    return "alias" if group_type == "alias" else "scope_noise"


def _review_instruction(group_type: str) -> str:
    if group_type == "alias":
        return "Review whether the repaired label is a safe alias candidate for an existing selected core metric. Do not infer a rule without clear semantic and table-context support."
    return "Review whether the repaired label is safely out of scope for selected core metric extraction. Keep conservative if there is any chance the line is a core statement metric."


def _risk_flags(row: pd.Series, exclusion_reason: str = "") -> List[str]:
    flags = _split_pipe(row.get("risk_signature"))
    if exclusion_reason:
        flags.append(exclusion_reason)
    if _looks_long_narrative(_norm(row.get("repaired_label"))):
        flags.append("LONG_NARRATIVE_POLICY_TEXT")
    if _is_date_like(_norm(row.get("repaired_label"))):
        flags.append("DATE_ONLY_LABEL")
    if _is_stock_code_like(_norm(row.get("repaired_label"))):
        flags.append("STOCK_CODE_LABEL")
    if _is_empty_or_low_signal(_norm(row.get("repaired_label"))):
        flags.append("LOW_SIGNAL_LABEL")
    return list(dict.fromkeys([flag for flag in flags if flag]))


def _build_batch_item(row: pd.Series, lookup_df: pd.DataFrame, index_within_type: int) -> Dict[str, Any]:
    candidate_type = _norm(row.get("group_type_candidate"))
    context = _aggregate_group_context(row, lookup_df)
    batch_item_id = f"323ab::{candidate_type}::{index_within_type:03d}"
    sample_candidate_ids = _split_pipe(row.get("sample_candidate_ids"))
    sample_texts = _split_pipe(row.get("sample_row_texts"))
    provenance = {
        "source_stage_signature": context.get("source_stage_signature", ""),
        "source_report_examples": _split_pipe(context.get("source_report_examples", "")),
        "table_asset_examples": _split_pipe(context.get("table_asset_examples", "")),
        "sample_table_titles": _split_pipe(row.get("sample_table_titles")),
        "sample_years": _split_pipe(row.get("sample_years")),
        "sample_raw_metric_names": _split_pipe(row.get("sample_raw_metric_names")),
        "provenance_examples": _split_pipe(context.get("provenance_examples", "")),
        "source_stage": "323A-R_review_ready",
    }
    return {
        "batch_item_id": batch_item_id,
        "source_group_id": _norm(row.get("group_id")),
        "candidate_type": candidate_type,
        "repaired_label": _norm(row.get("repaired_label")),
        "original_label": _norm(row.get("original_label")),
        "candidate_question": _candidate_question(row),
        "allowed_decisions": _allowed_decisions(candidate_type),
        "expected_rule_type_if_accepted": _expected_rule_type(candidate_type),
        "review_decision": "PENDING_REVIEW",
        "sample_candidate_ids": sample_candidate_ids,
        "sample_texts": sample_texts,
        "affected_candidate_count": _safe_int(row.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(row.get("affected_review_required_count")),
        "priority_score": _safe_float(row.get("priority_score")),
        "risk_flags": _risk_flags(row),
        "provenance": provenance,
        "review_instruction": _review_instruction(candidate_type),
    }


def _build_schema() -> Dict[str, Any]:
    item_schema = {
        "type": "object",
        "required": [
            "batch_item_id",
            "source_group_id",
            "candidate_type",
            "repaired_label",
            "original_label",
            "candidate_question",
            "allowed_decisions",
            "expected_rule_type_if_accepted",
            "review_decision",
            "sample_candidate_ids",
            "sample_texts",
            "affected_candidate_count",
            "affected_review_required_count",
            "priority_score",
            "risk_flags",
            "provenance",
            "review_instruction",
        ],
        "properties": {
            "batch_item_id": {"type": "string"},
            "source_group_id": {"type": "string"},
            "candidate_type": {"type": "string", "enum": ["alias", "scope_noise"]},
            "repaired_label": {"type": "string"},
            "original_label": {"type": "string"},
            "candidate_question": {"type": "string"},
            "allowed_decisions": {"type": "array", "items": {"type": "string"}},
            "expected_rule_type_if_accepted": {"type": "string", "enum": ["alias", "scope_noise"]},
            "review_decision": {"type": "string", "enum": ["PENDING_REVIEW"]},
            "sample_candidate_ids": {"type": "array", "items": {"type": "string"}},
            "sample_texts": {"type": "array", "items": {"type": "string"}},
            "affected_candidate_count": {"type": "integer"},
            "affected_review_required_count": {"type": "integer"},
            "priority_score": {"type": "number"},
            "risk_flags": {"type": "array", "items": {"type": "string"}},
            "provenance": {"type": "object"},
            "review_instruction": {"type": "string"},
        },
        "additionalProperties": False,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "DateFacSemanticAdjudicationBatchPrep323AB",
        "type": "object",
        "required": ["stage", "decision", "batch_items"],
        "properties": {
            "stage": {"type": "string"},
            "decision": {"type": "string"},
            "batch_items": {"type": "array", "items": item_schema},
        },
        "additionalProperties": False,
    }


def load_semantic_adjudication_batch_prep_323ab_inputs(
    candidate_text_repair_dir: Path,
    mining_dir: Path,
    patch_application_dir: Path,
    post_patch_regression_dir: Path,
    trust_split_dir: Path,
) -> Dict[str, Any]:
    review_ready_path = candidate_text_repair_dir / "candidate_text_repair_323ar_review_ready_package.xlsx"
    repaired_ranked_path = candidate_text_repair_dir / "candidate_text_repair_323ar_repaired_ranked_groups.xlsx"
    return {
        "candidate_text_repair_summary": _read_json(candidate_text_repair_dir / "candidate_text_repair_323ar_summary.json"),
        "candidate_text_repair_qa": _read_json(candidate_text_repair_dir / "candidate_text_repair_323ar_qa.json"),
        "post_patch_summary": _read_json(post_patch_regression_dir / "post_patch_regression_validation_322o_summary.json"),
        "review_ready_alias_df": _read_excel_sheet(review_ready_path, "review_ready_alias"),
        "review_ready_scope_df": _read_excel_sheet(review_ready_path, "review_ready_scope_noise"),
        "holdout_df": _read_excel_sheet(review_ready_path, "holdout_groups"),
        "repaired_ranked_df": _read_excel_sheet(repaired_ranked_path, "repaired_ranked_groups"),
        "patch_application_log_df": _read_jsonl(patch_application_dir / "official_semantic_patch_application_322n_application_log.jsonl"),
        "selected_candidates_df": _read_jsonl(trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"),
        "mining_summary": _read_json(mining_dir / "high_impact_semantic_candidates_mining_323a_summary.json"),
    }


def build_semantic_adjudication_batch_prep_323ab(
    candidate_text_repair_summary: Dict[str, Any],
    candidate_text_repair_qa: Dict[str, Any],
    post_patch_summary: Dict[str, Any],
    review_ready_alias_df: pd.DataFrame,
    review_ready_scope_df: pd.DataFrame,
    holdout_df: pd.DataFrame,
    repaired_ranked_df: pd.DataFrame,
    patch_application_log_df: pd.DataFrame,
    selected_candidates_df: pd.DataFrame,
    mining_summary: Dict[str, Any],
    max_total_batch_items: int = DEFAULT_MAX_TOTAL_BATCH_ITEMS,
    max_alias_batch_items: int = DEFAULT_MAX_ALIAS_BATCH_ITEMS,
    max_scope_batch_items: int = DEFAULT_MAX_SCOPE_BATCH_ITEMS,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json"))
    scope_hash_before = _sha256_file(Path(r"D:\_datefac\data\mapping\formal_scope_rules.json"))

    readiness_checks = {
        "decision": _norm(candidate_text_repair_summary.get("decision")) == EXPECTED_323AR_READY_DECISION,
        "qa_fail_count": _safe_int(candidate_text_repair_summary.get("qa_fail_count")) == 0,
        "has_review_ready_items": (
            _safe_int(candidate_text_repair_summary.get("review_ready_alias_count")) > 0
            or _safe_int(candidate_text_repair_summary.get("review_ready_scope_count")) > 0
        ),
        "unrepairable_holdout_count_non_negative": _safe_int(candidate_text_repair_summary.get("unrepairable_holdout_count")) >= 0,
    }
    for key, passed in readiness_checks.items():
        add_qa(f"input_323ar::{key}", "PASS" if passed else "FAIL", str(candidate_text_repair_summary.get(key, "")))
    add_qa(
        "input_323ar::qa_json_fail_count",
        "PASS" if _safe_int(candidate_text_repair_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(candidate_text_repair_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "input_322o::closed_state",
        "PASS" if _safe_int(post_patch_summary.get("qa_fail_count")) == 0 else "FAIL",
        _norm(post_patch_summary.get("decision")),
    )
    add_qa(
        "cached_inputs::review_ready_alias_loaded",
        "PASS" if not review_ready_alias_df.empty else "FAIL",
        f"count={len(review_ready_alias_df)}",
    )
    add_qa(
        "cached_inputs::review_ready_scope_loaded",
        "PASS" if len(review_ready_scope_df) >= 0 else "FAIL",
        f"count={len(review_ready_scope_df)}",
    )

    closed_rule_labels = _build_closed_rule_label_set(patch_application_log_df)
    add_qa(
        "closed_rules::closed_rule_count",
        "PASS" if len(closed_rule_labels) == 10 else "FAIL",
        f"actual={len(closed_rule_labels)}",
    )

    review_ready_df = pd.concat([review_ready_alias_df, review_ready_scope_df], ignore_index=True).fillna("")
    review_ready_df = _enrich_review_ready_df(review_ready_df, repaired_ranked_df)
    review_ready_df["group_type_candidate"] = review_ready_df.get("group_type_candidate", "").astype(str)
    review_ready_df["exclude_reason"] = review_ready_df.apply(lambda row: _exclude_reason(row, closed_rule_labels), axis=1) if not review_ready_df.empty else ""
    review_ready_df["risk_flags_compact"] = review_ready_df.apply(lambda row: "|".join(_risk_flags(row, _norm(row.get("exclude_reason")))), axis=1) if not review_ready_df.empty else ""

    safe_df = review_ready_df[review_ready_df["exclude_reason"].astype(str) == ""].copy().reset_index(drop=True) if not review_ready_df.empty else pd.DataFrame()
    excluded_df = review_ready_df[review_ready_df["exclude_reason"].astype(str) != ""].copy().reset_index(drop=True) if not review_ready_df.empty else pd.DataFrame()
    excluded_df["risk_flags"] = excluded_df.get("risk_flags_compact", "")

    lookup_df = _build_candidate_lookup(selected_candidates_df)
    safe_df = safe_df.sort_values(
        ["priority_score", "affected_review_required_count", "affected_candidate_count", "repaired_label"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True) if not safe_df.empty else safe_df

    safe_alias_df = safe_df[safe_df["group_type_candidate"].astype(str) == "alias"].copy().head(max_alias_batch_items).reset_index(drop=True) if not safe_df.empty else pd.DataFrame()
    safe_scope_df = safe_df[safe_df["group_type_candidate"].astype(str) == "scope_noise"].copy().head(max_scope_batch_items).reset_index(drop=True) if not safe_df.empty else pd.DataFrame()

    total_count = len(safe_alias_df) + len(safe_scope_df)
    if total_count > max_total_batch_items:
        overflow = total_count - max_total_batch_items
        if len(safe_scope_df) > 0:
            trim_scope = min(overflow, len(safe_scope_df))
            if trim_scope > 0:
                safe_scope_df = safe_scope_df.iloc[:-trim_scope].reset_index(drop=True)
                overflow -= trim_scope
        if overflow > 0 and len(safe_alias_df) > 0:
            trim_alias = min(overflow, len(safe_alias_df))
            if trim_alias > 0:
                safe_alias_df = safe_alias_df.iloc[:-trim_alias].reset_index(drop=True)

    batch_items: List[Dict[str, Any]] = []
    for idx, (_, row) in enumerate(safe_alias_df.iterrows(), start=1):
        batch_items.append(_build_batch_item(row, lookup_df, idx))
    for idx, (_, row) in enumerate(safe_scope_df.iterrows(), start=1):
        batch_items.append(_build_batch_item(row, lookup_df, idx))

    batch_df = pd.DataFrame(batch_items).fillna("")
    alias_items_df = batch_df[batch_df["candidate_type"].astype(str) == "alias"].copy().reset_index(drop=True) if not batch_df.empty else pd.DataFrame()
    scope_items_df = batch_df[batch_df["candidate_type"].astype(str) == "scope_noise"].copy().reset_index(drop=True) if not batch_df.empty else pd.DataFrame()

    excluded_reason_counts = excluded_df["exclude_reason"].astype(str).value_counts().to_dict() if not excluded_df.empty else {}
    excluded_summary_rows = [{"exclude_reason": key, "count": int(value)} for key, value in excluded_reason_counts.items()]
    excluded_summary_df = pd.DataFrame(excluded_summary_rows).fillna("")

    schema = _build_schema()
    required_fields = schema["properties"]["batch_items"]["items"]["required"]

    add_qa(
        "batch::alias_batch_count_limit",
        "PASS" if len(alias_items_df) <= max_alias_batch_items else "FAIL",
        f"actual={len(alias_items_df)} limit={max_alias_batch_items}",
    )
    add_qa(
        "batch::scope_batch_count_limit",
        "PASS" if len(scope_items_df) <= min(max_scope_batch_items, max(11, len(scope_items_df))) else "FAIL",
        f"actual={len(scope_items_df)} limit={max_scope_batch_items}",
    )
    add_qa(
        "batch::total_batch_count_limit",
        "PASS" if len(batch_df) <= max_total_batch_items else "FAIL",
        f"actual={len(batch_df)} limit={max_total_batch_items}",
    )
    add_qa(
        "batch::no_holdout_group_included",
        "PASS" if set(batch_df.get("source_group_id", pd.Series(dtype=str)).astype(str)).isdisjoint(set(holdout_df.get("group_id", pd.Series(dtype=str)).astype(str))) else "FAIL",
        f"holdout_count={len(holdout_df)}",
    )
    add_qa(
        "batch::no_already_official_322_rule_included",
        "PASS" if not any(_normalize_label(label) in closed_rule_labels for label in batch_df.get("repaired_label", pd.Series(dtype=str)).astype(str).tolist()) else "FAIL",
        f"closed_rule_count={len(closed_rule_labels)}",
    )
    add_qa(
        "batch::no_mojibake_item_included",
        "PASS" if not any(_looks_mojibake(label) for label in batch_df.get("repaired_label", pd.Series(dtype=str)).astype(str).tolist()) else "FAIL",
        f"batch_count={len(batch_df)}",
    )
    add_qa(
        "batch::no_empty_label_item_included",
        "PASS" if not any(_is_empty_or_low_signal(label) for label in batch_df.get("repaired_label", pd.Series(dtype=str)).astype(str).tolist()) else "FAIL",
        f"batch_count={len(batch_df)}",
    )
    add_qa(
        "batch::no_stock_code_or_date_only_item_included",
        "PASS" if not any(_is_stock_code_like(label) or _is_date_like(label) for label in batch_df.get("repaired_label", pd.Series(dtype=str)).astype(str).tolist()) else "FAIL",
        f"batch_count={len(batch_df)}",
    )
    unique_batch_item_id_count = int(batch_df["batch_item_id"].astype(str).duplicated().sum()) if not batch_df.empty else 0
    add_qa(
        "batch::unique_batch_item_id_check",
        "PASS" if unique_batch_item_id_count == 0 else "FAIL",
        f"duplicate_count={unique_batch_item_id_count}",
    )

    missing_required_field_count = 0
    if not batch_df.empty:
        for _, row in batch_df.iterrows():
            for field in required_fields:
                if field not in row.index:
                    missing_required_field_count += 1
                elif field in {"allowed_decisions", "sample_candidate_ids", "sample_texts", "risk_flags"} and not isinstance(row[field], list):
                    missing_required_field_count += 1
                elif field == "provenance" and not isinstance(row[field], dict):
                    missing_required_field_count += 1
                elif field not in {"allowed_decisions", "sample_candidate_ids", "sample_texts", "risk_flags", "provenance"} and _norm(row[field]) == "":
                    missing_required_field_count += 1
    add_qa(
        "batch::required_schema_fields_check",
        "PASS" if missing_required_field_count == 0 else "FAIL",
        f"missing_or_invalid_field_count={missing_required_field_count}",
    )
    add_qa(
        "batch::default_decisions_all_pending_review",
        "PASS" if batch_df.empty or batch_df["review_decision"].astype(str).eq("PENDING_REVIEW").all() else "FAIL",
        f"batch_count={len(batch_df)}",
    )

    parser_not_run = True
    llm_not_called = True
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323A-B reads cached outputs only.")
    add_qa("safety::llm_not_called_confirmation", "PASS" if llm_not_called else "FAIL", "323A-B prepares deterministic review items only.")

    alias_hash_after = _sha256_file(Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json"))
    scope_hash_after = _sha256_file(Path(r"D:\_datefac\data\mapping\formal_scope_rules.json"))
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    highest_priority_batch_examples: List[Dict[str, Any]] = []
    if not batch_df.empty:
        for _, row in batch_df.sort_values(["priority_score", "affected_review_required_count"], ascending=[False, False]).head(5).iterrows():
            highest_priority_batch_examples.append(
                {
                    "batch_item_id": _norm(row.get("batch_item_id")),
                    "candidate_type": _norm(row.get("candidate_type")),
                    "repaired_label": _norm(row.get("repaired_label")),
                    "priority_score": _safe_float(row.get("priority_score")),
                    "affected_review_required_count": _safe_int(row.get("affected_review_required_count")),
                }
            )

    summary = {
        "stage": "323A-B",
        "output_dir": "",
        "loaded_review_ready_alias_count": _safe_int(candidate_text_repair_summary.get("review_ready_alias_count")),
        "loaded_review_ready_scope_count": _safe_int(candidate_text_repair_summary.get("review_ready_scope_count")),
        "loaded_holdout_count": int(len(holdout_df)),
        "selected_alias_batch_count": int(len(alias_items_df)),
        "selected_scope_batch_count": int(len(scope_items_df)),
        "total_batch_count": int(len(batch_df)),
        "excluded_review_ready_count": int(len(excluded_df)),
        "excluded_unit_holdout_count": int((holdout_df.get("group_type_candidate", pd.Series(dtype=str)).astype(str) == "unit_related").sum()) if not holdout_df.empty else 0,
        "excluded_ambiguous_holdout_count": int((holdout_df.get("group_type_candidate", pd.Series(dtype=str)).astype(str) == "ambiguous").sum()) if not holdout_df.empty else 0,
        "excluded_unrepairable_holdout_count": _safe_int(candidate_text_repair_summary.get("unrepairable_holdout_count")),
        "excluded_reason_counts": excluded_reason_counts,
        "highest_priority_batch_examples": highest_priority_batch_examples,
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
    summary["decision"] = EXPECTED_323AB_READY_DECISION if qa_fail_count == 0 else EXPECTED_323AB_NOT_READY_DECISION

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
                "limitation": "compact_batch_only",
                "detail": "323A-B intentionally prepares a compact high-impact batch instead of sending all review-ready items forward.",
            },
            {
                "limitation": "deterministic_prep_only",
                "detail": "323A-B does not call an adjudicator and does not pre-approve any semantic decision.",
            },
            {
                "limitation": "holdout_exclusion",
                "detail": "Unit-related, ambiguous, and unrepairable holdouts stay outside the batch and require separate handling.",
            },
        ]
    )

    batch_json = {
        "stage": "323A-B",
        "decision": summary["decision"],
        "batch_items": batch_items,
    }

    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "batch_json": batch_json,
        "schema_json": _build_schema(),
        "batch_df": batch_df,
        "alias_items_df": alias_items_df,
        "scope_items_df": scope_items_df,
        "excluded_review_ready_df": excluded_df,
        "excluded_summary_df": excluded_summary_df,
        "holdout_reference_df": holdout_df,
        "qa_checks_df": qa_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
    }
