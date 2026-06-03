from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import pandas as pd

from datefac.semantic.human_confirmed_patch_preview import (
    apply_human_confirmed_patches,
    read_jsonl,
)
from datefac.semantic.official_rule_candidates import _load_scope_reference


EXPECTED_322N_DECISION = "OFFICIAL_SEMANTIC_PATCH_APPLICATION_322N_READY_FOR_322O_POST_PATCH_REGRESSION"
EXPECTED_322O_READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE"
EXPECTED_322O_NOT_READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_322O_NOT_READY_ROLLBACK_REVIEW_REQUIRED"

DEFAULT_PATCH_APPLICATION_DIR = Path(r"D:\_datefac\output\official_semantic_patch_application_322n")
DEFAULT_TRUST_SPLIT_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_REFERENCE_322J_DIR = Path(r"D:\_datefac\output\official_semantic_rule_candidates_322j")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_322o")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

EXPECTED_COUNTS = {
    "approved_patch_count": 10,
    "applied_or_idempotent_operation_count": 10,
    "alias_operation_count": 3,
    "scope_operation_count": 7,
    "conflict_count": 0,
    "trusted_total_before": 2479,
    "trusted_total_after": 2528,
    "review_required_total_before": 3358,
    "review_required_total_after": 3071,
    "rejected_total_before": 135,
    "rejected_total_after": 373,
    "trusted_gain": 49,
    "review_reduction": 287,
    "out_of_scope_or_rejected_gain": 238,
    "affected_candidate_count": 287,
    "remaining_unknown_metric_candidate_count": 2897,
    "remaining_unit_unknown_candidate_count": 491,
    "remaining_manual_review_count": 3071,
}

EXPECTED_RATES = {
    "selected_core_trusted_rate_before": 0.415104,
    "selected_core_trusted_rate_after": 0.423309,
}

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


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _flatten_alias_entries(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        return []
    rows: List[Dict[str, Any]] = []
    for group_name, items in groups.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row["target_group"] = _norm(group_name)
            rows.append(row)
    return rows


def _flatten_scope_entries(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rules = payload.get("rules", {})
    if not isinstance(rules, dict):
        return []
    rows: List[Dict[str, Any]] = []
    for rule_id, item in rules.items():
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("rule_id", _norm(rule_id))
        rows.append(row)
    return rows


def _parse_json_maybe(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    text = _norm(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _split_tags(value: Any) -> List[str]:
    text = _norm(value)
    if not text:
        return []
    return [item.strip() for item in text.split("|") if item.strip()]


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _read_official_alias_asset(path: Path) -> Tuple[bool, Dict[str, Any], pd.DataFrame]:
    raw = _read_json(path)
    if not raw:
        return False, {}, pd.DataFrame()
    rows = _flatten_alias_entries(raw)
    return True, raw, pd.DataFrame(rows).fillna("")


def _extract_rule_rows(alias_df: pd.DataFrame, scope_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    alias_visible_df = alias_df[
        alias_df.get("rule_id", pd.Series(dtype=str)).astype(str).str.startswith("SEM_ALIAS_322N_")
    ].copy() if not alias_df.empty else pd.DataFrame()
    scope_visible_df = scope_df[
        scope_df.get("rule_id", pd.Series(dtype=str)).astype(str).str.startswith("SEM_SCOPE_322N_")
    ].copy() if not scope_df.empty else pd.DataFrame()
    if not alias_visible_df.empty:
        alias_visible_df["rule_type"] = "alias"
    if not scope_visible_df.empty:
        scope_visible_df["rule_type"] = "out_of_scope"
    return alias_visible_df.fillna(""), scope_visible_df.fillna("")


def _build_visibility_rows(alias_visible_df: pd.DataFrame, scope_visible_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, row in alias_visible_df.iterrows():
        rows.append(
            {
                "rule_id": _norm(row.get("rule_id")),
                "rule_type": "alias",
                "normalized_label": _norm(row.get("normalized_label")),
                "target_group": _norm(row.get("target_group")),
                "metric_code": _norm(row.get("metric_code")),
                "metric_family": _norm(row.get("metric_family")),
                "visibility_source": str(SEMANTIC_ALIAS_ASSET_PATH),
                "status": _norm(row.get("status")),
            }
        )
    for _, row in scope_visible_df.iterrows():
        rows.append(
            {
                "rule_id": _norm(row.get("rule_id")),
                "rule_type": "out_of_scope",
                "normalized_label": _norm(row.get("normalized_label")),
                "target_group": _norm(row.get("target_group")),
                "metric_code": "",
                "metric_family": "",
                "visibility_source": str(FORMAL_SCOPE_RULES_PATH),
                "status": _norm(row.get("promotion_status")),
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values(["rule_type", "rule_id"]).reset_index(drop=True)


def _build_official_replay_inputs(
    application_log_df: pd.DataFrame,
    alias_visible_df: pd.DataFrame,
    scope_visible_df: pd.DataFrame,
) -> pd.DataFrame:
    alias_lookup = {
        _norm(row.get("rule_id")): row.to_dict()
        for _, row in alias_visible_df.iterrows()
    } if not alias_visible_df.empty else {}
    scope_lookup = {
        _norm(row.get("rule_id")): row.to_dict()
        for _, row in scope_visible_df.iterrows()
    } if not scope_visible_df.empty else {}
    rows: List[Dict[str, Any]] = []
    if application_log_df.empty:
        return pd.DataFrame()
    for _, row in application_log_df.iterrows():
        operation_status = _norm(row.get("operation_status"))
        if operation_status not in {"APPLIED", "IDEMPOTENT_ALREADY_APPLIED"}:
            continue
        rule_type = _norm(row.get("rule_type"))
        rule_id = _norm(row.get("rule_id"))
        provenance = _parse_json_maybe(row.get("provenance"))
        after_state = _parse_json_maybe(row.get("after_state"))
        visible_row = alias_lookup.get(rule_id, {}) if rule_type == "alias" else scope_lookup.get(rule_id, {})
        normalized_label = _norm(visible_row.get("normalized_label")) or _norm(after_state.get("normalized_label"))
        target_group = _norm(visible_row.get("target_group")) or _norm(row.get("target_group")) or _norm(after_state.get("target_group"))
        proposal_type = "alias" if rule_type == "alias" else "out_of_scope"
        replay_row = {
            "proposal_id": _norm(provenance.get("source_322i_proposal_id")) or _norm(provenance.get("source_322k_proposal_id")) or rule_id,
            "proposal_type": proposal_type,
            "source_case_id": _norm(provenance.get("human_confirmation_source_case_id")),
            "normalized_label": normalized_label,
            "sample_table_titles": "",
            "sample_row_labels": normalized_label,
            "sample_values": "",
            "risk_flags": "",
            "affected_candidate_count": _safe_int(row.get("expected_affected_candidate_count")),
            "review_reduction": _safe_int(row.get("expected_review_reduction")),
            "reviewer_decision": "ACCEPT",
            "reviewer_comment": "322O official asset regression replay",
            "official_rule_id": rule_id,
            "official_target_group": target_group,
        }
        if proposal_type == "alias":
            replay_row["proposed_metric_code"] = _norm(visible_row.get("metric_code")) or _norm(after_state.get("metric_code"))
            replay_row["proposed_metric_family"] = _norm(visible_row.get("metric_family")) or _norm(after_state.get("metric_family"))
            replay_row["trusted_gain"] = _safe_int(row.get("expected_trusted_gain"))
        else:
            replay_row["proposed_scope_action"] = _norm(visible_row.get("scope_action")) or _norm(after_state.get("scope_action")) or "exclude_from_core_metric_mapping"
            replay_row["rejected_or_out_of_scope_gain"] = _safe_int(row.get("expected_out_of_scope_or_rejected_gain"))
        rows.append(replay_row)
    return pd.DataFrame(rows).fillna("")


def _build_application_alignment_df(application_log_df: pd.DataFrame, impact_df: pd.DataFrame) -> pd.DataFrame:
    impact_lookup = {
        _norm(row.get("proposal_id")): row.to_dict()
        for _, row in impact_df.iterrows()
    } if not impact_df.empty else {}
    rows: List[Dict[str, Any]] = []
    for _, row in application_log_df.iterrows():
        operation_status = _norm(row.get("operation_status"))
        if operation_status not in {"APPLIED", "IDEMPOTENT_ALREADY_APPLIED"}:
            continue
        provenance = _parse_json_maybe(row.get("provenance"))
        proposal_id = _norm(provenance.get("source_322i_proposal_id")) or _norm(provenance.get("source_322k_proposal_id")) or _norm(row.get("rule_id"))
        impact_row = impact_lookup.get(proposal_id, {})
        rows.append(
            {
                "proposal_id": proposal_id,
                "rule_id": _norm(row.get("rule_id")),
                "rule_type": _norm(row.get("rule_type")),
                "normalized_label": _norm(_parse_json_maybe(row.get("after_state")).get("normalized_label")),
                "expected_affected_candidate_count": _safe_int(row.get("expected_affected_candidate_count")),
                "actual_affected_candidate_count": _safe_int(impact_row.get("affected_candidate_count")),
                "expected_trusted_gain": _safe_int(row.get("expected_trusted_gain")),
                "actual_trusted_gain": _safe_int(impact_row.get("trusted_gain")),
                "expected_review_reduction": _safe_int(row.get("expected_review_reduction")),
                "actual_review_reduction": _safe_int(impact_row.get("review_reduction")),
                "expected_out_of_scope_or_rejected_gain": _safe_int(row.get("expected_out_of_scope_or_rejected_gain")),
                "actual_out_of_scope_or_rejected_gain": _safe_int(impact_row.get("rejected_or_out_of_scope_count")),
                "operation_status": operation_status,
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values(["rule_type", "rule_id"]).reset_index(drop=True)


def _build_metric_comparison_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "metric": "trusted_total",
            "expected_before": EXPECTED_COUNTS["trusted_total_before"],
            "actual_before": _safe_int(summary.get("trusted_total_before_322o")),
            "expected_after": EXPECTED_COUNTS["trusted_total_after"],
            "actual_after": _safe_int(summary.get("trusted_total_after_322o")),
            "expected_delta": EXPECTED_COUNTS["trusted_gain"],
            "actual_delta": _safe_int(summary.get("trusted_gain_322o")),
        },
        {
            "metric": "review_required_total",
            "expected_before": EXPECTED_COUNTS["review_required_total_before"],
            "actual_before": _safe_int(summary.get("review_required_total_before_322o")),
            "expected_after": EXPECTED_COUNTS["review_required_total_after"],
            "actual_after": _safe_int(summary.get("review_required_total_after_322o")),
            "expected_delta": -EXPECTED_COUNTS["review_reduction"],
            "actual_delta": _safe_int(summary.get("review_required_total_after_322o")) - _safe_int(summary.get("review_required_total_before_322o")),
        },
        {
            "metric": "rejected_total",
            "expected_before": EXPECTED_COUNTS["rejected_total_before"],
            "actual_before": _safe_int(summary.get("rejected_total_before_322o")),
            "expected_after": EXPECTED_COUNTS["rejected_total_after"],
            "actual_after": _safe_int(summary.get("rejected_total_after_322o")),
            "expected_delta": EXPECTED_COUNTS["out_of_scope_or_rejected_gain"],
            "actual_delta": _safe_int(summary.get("out_of_scope_or_rejected_gain_322o")),
        },
        {
            "metric": "affected_candidate_count",
            "expected_before": "",
            "actual_before": "",
            "expected_after": EXPECTED_COUNTS["affected_candidate_count"],
            "actual_after": _safe_int(summary.get("affected_candidate_count")),
            "expected_delta": "",
            "actual_delta": _safe_int(summary.get("affected_candidate_count_delta_vs_expected")),
        },
        {
            "metric": "selected_core_trusted_rate",
            "expected_before": EXPECTED_RATES["selected_core_trusted_rate_before"],
            "actual_before": round(_safe_float(summary.get("selected_core_trusted_rate_before_322o")), 6),
            "expected_after": EXPECTED_RATES["selected_core_trusted_rate_after"],
            "actual_after": round(_safe_float(summary.get("selected_core_trusted_rate_after_322o")), 6),
            "expected_delta": round(EXPECTED_RATES["selected_core_trusted_rate_after"] - EXPECTED_RATES["selected_core_trusted_rate_before"], 6),
            "actual_delta": round(_safe_float(summary.get("selected_core_trusted_rate_after_322o")) - _safe_float(summary.get("selected_core_trusted_rate_before_322o")), 6),
        },
        {
            "metric": "remaining_unknown_metric_candidate_count",
            "expected_before": "",
            "actual_before": "",
            "expected_after": EXPECTED_COUNTS["remaining_unknown_metric_candidate_count"],
            "actual_after": _safe_int(summary.get("remaining_unknown_metric_candidate_count")),
            "expected_delta": "",
            "actual_delta": _safe_int(summary.get("remaining_unknown_metric_candidate_count")) - EXPECTED_COUNTS["remaining_unknown_metric_candidate_count"],
        },
        {
            "metric": "remaining_unit_unknown_candidate_count",
            "expected_before": "",
            "actual_before": "",
            "expected_after": EXPECTED_COUNTS["remaining_unit_unknown_candidate_count"],
            "actual_after": _safe_int(summary.get("remaining_unit_unknown_candidate_count")),
            "expected_delta": "",
            "actual_delta": _safe_int(summary.get("remaining_unit_unknown_candidate_count")) - EXPECTED_COUNTS["remaining_unit_unknown_candidate_count"],
        },
        {
            "metric": "remaining_manual_review_count",
            "expected_before": "",
            "actual_before": "",
            "expected_after": EXPECTED_COUNTS["remaining_manual_review_count"],
            "actual_after": _safe_int(summary.get("remaining_manual_review_count")),
            "expected_delta": "",
            "actual_delta": _safe_int(summary.get("remaining_manual_review_count")) - EXPECTED_COUNTS["remaining_manual_review_count"],
        },
    ]
    return pd.DataFrame(rows).fillna("")


def _build_core_false_exclusion_df(diff_df: pd.DataFrame) -> pd.DataFrame:
    if diff_df.empty:
        return pd.DataFrame(
            columns=[
                "candidate_id",
                "proposal_id",
                "patch_id",
                "row_label",
                "metric_code_before",
                "metric_code_after",
                "decision_before",
                "decision_after",
            ]
        )
    temp = diff_df.copy()
    temp["metric_code_before"] = temp.get("metric_code_before", "").astype(str)
    temp["metric_code_after"] = temp.get("metric_code_after", "").astype(str)
    temp["decision_before"] = temp.get("decision_before", "").astype(str)
    temp["decision_after"] = temp.get("decision_after", "").astype(str)
    mask = (
        temp["decision_after"].eq("rejected_preview")
        & (
            temp["metric_code_before"].isin(CORE_METRIC_CODES)
            | temp["metric_code_after"].isin(CORE_METRIC_CODES)
        )
    )
    columns = [
        "candidate_id",
        "proposal_id",
        "patch_id",
        "row_label",
        "table_title",
        "metric_code_before",
        "metric_code_after",
        "decision_before",
        "decision_after",
        "risk_tags_before",
        "risk_tags_after",
    ]
    present_columns = [column for column in columns if column in temp.columns]
    return temp.loc[mask, present_columns].fillna("").reset_index(drop=True)


def load_post_patch_regression_validation_inputs(
    patch_application_dir: Path,
    trust_split_dir: Path,
    reference_322j_dir: Path,
) -> Dict[str, Any]:
    return {
        "patch_summary": _read_json(patch_application_dir / "official_semantic_patch_application_322n_summary.json"),
        "patch_qa": _read_json(patch_application_dir / "official_semantic_patch_application_322n_qa.json"),
        "patch_application_log_df": read_jsonl(
            patch_application_dir / "official_semantic_patch_application_322n_application_log.jsonl"
        ),
        "reference_322j_summary": _read_json(reference_322j_dir / "official_semantic_rule_candidates_322j_summary.json"),
        "reference_322j_qa": _read_json(reference_322j_dir / "official_semantic_rule_candidates_322j_qa.json"),
        "trust_summary": _read_json(trust_split_dir / "router_mineru_trust_split_322b2_summary.json"),
        "selected_candidates_df": read_jsonl(trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"),
    }


def build_post_patch_regression_validation(
    patch_summary: Dict[str, Any],
    patch_qa: Dict[str, Any],
    patch_application_log_df: pd.DataFrame,
    reference_322j_summary: Dict[str, Any],
    reference_322j_qa: Dict[str, Any],
    trust_summary: Dict[str, Any],
    selected_candidates_df: pd.DataFrame,
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    readiness_expectations = {
        "decision": (_norm(patch_summary.get("decision")) == EXPECTED_322N_DECISION, _norm(patch_summary.get("decision"))),
        "qa_fail_count": (_safe_int(patch_summary.get("qa_fail_count")) == 0, str(patch_summary.get("qa_fail_count", ""))),
        "approved_patch_count": (_safe_int(patch_summary.get("approved_patch_count")) == EXPECTED_COUNTS["approved_patch_count"], str(patch_summary.get("approved_patch_count", ""))),
        "applied_or_idempotent_operation_count": (_safe_int(patch_summary.get("applied_or_idempotent_operation_count")) == EXPECTED_COUNTS["applied_or_idempotent_operation_count"], str(patch_summary.get("applied_or_idempotent_operation_count", ""))),
        "alias_operation_count": (_safe_int(patch_summary.get("alias_operation_count")) == EXPECTED_COUNTS["alias_operation_count"], str(patch_summary.get("alias_operation_count", ""))),
        "scope_operation_count": (_safe_int(patch_summary.get("scope_operation_count")) == EXPECTED_COUNTS["scope_operation_count"], str(patch_summary.get("scope_operation_count", ""))),
        "conflict_count": (_safe_int(patch_summary.get("conflict_count")) == EXPECTED_COUNTS["conflict_count"], str(patch_summary.get("conflict_count", ""))),
    }
    for key, (passed, detail) in readiness_expectations.items():
        add_qa(f"readiness_322n::{key}", "PASS" if passed else "FAIL", detail)
    add_qa(
        "readiness_322n::qa_json_fail_count",
        "PASS" if _safe_int(patch_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(patch_qa.get("qa_fail_count", "")),
    )

    alias_loaded, alias_raw, alias_df = _read_official_alias_asset(SEMANTIC_ALIAS_ASSET_PATH)
    scope_loaded, scope_raw, scope_loader_df = _load_scope_reference(FORMAL_SCOPE_RULES_PATH)
    scope_df = pd.DataFrame(_flatten_scope_entries(scope_raw)).fillna("") if scope_loaded and scope_raw else pd.DataFrame()
    add_qa("official_assets::semantic_alias_candidates_exists_and_loads", "PASS" if alias_loaded else "FAIL", str(SEMANTIC_ALIAS_ASSET_PATH))
    add_qa("official_assets::formal_scope_rules_exists_and_loads", "PASS" if scope_loaded else "FAIL", str(FORMAL_SCOPE_RULES_PATH))
    add_qa(
        "official_assets::formal_scope_loader_visible_rows",
        "PASS" if scope_loaded and not scope_loader_df.empty else "FAIL",
        f"loader_rows={len(scope_loader_df)}",
    )

    alias_visible_df, scope_visible_df = _extract_rule_rows(alias_df, scope_df)
    visibility_df = _build_visibility_rows(alias_visible_df, scope_visible_df)
    add_qa(
        "official_visibility::alias_rules_visible",
        "PASS" if len(alias_visible_df) == EXPECTED_COUNTS["alias_operation_count"] else "FAIL",
        f"actual={len(alias_visible_df)}",
    )
    add_qa(
        "official_visibility::scope_rules_visible",
        "PASS" if len(scope_visible_df) == EXPECTED_COUNTS["scope_operation_count"] else "FAIL",
        f"actual={len(scope_visible_df)}",
    )
    add_qa(
        "official_visibility::total_rules_visible",
        "PASS" if len(visibility_df) == EXPECTED_COUNTS["approved_patch_count"] else "FAIL",
        f"actual={len(visibility_df)}",
    )

    visible_rule_ids = set(visibility_df.get("rule_id", pd.Series(dtype=str)).astype(str).tolist()) if not visibility_df.empty else set()
    applied_rule_ids = set(
        patch_application_log_df.loc[
            patch_application_log_df.get("operation_status", pd.Series(dtype=str)).astype(str).isin(["APPLIED", "IDEMPOTENT_ALREADY_APPLIED"]),
            "rule_id",
        ].astype(str).tolist()
    ) if not patch_application_log_df.empty and "rule_id" in patch_application_log_df.columns else set()
    missing_visible_rule_ids = sorted(applied_rule_ids - visible_rule_ids)
    add_qa(
        "official_visibility::all_322n_applied_rules_visible",
        "PASS" if not missing_visible_rule_ids else "FAIL",
        "missing=" + " | ".join(missing_visible_rule_ids),
    )

    duplicate_rule_count = int(visibility_df["rule_id"].astype(str).duplicated().sum()) if not visibility_df.empty else 0
    alias_scope_label_conflicts = 0
    if not alias_visible_df.empty and not scope_visible_df.empty:
        alias_labels = set(alias_visible_df["normalized_label"].astype(str).tolist())
        scope_labels = set(scope_visible_df["normalized_label"].astype(str).tolist())
        alias_scope_label_conflicts = len(alias_labels.intersection(scope_labels))
    add_qa("official_rules::duplicate_rule_count", "PASS" if duplicate_rule_count == 0 else "FAIL", f"actual={duplicate_rule_count}")
    add_qa("official_rules::alias_scope_conflict_count", "PASS" if alias_scope_label_conflicts == 0 else "FAIL", f"actual={alias_scope_label_conflicts}")

    official_replay_inputs_df = _build_official_replay_inputs(
        application_log_df=patch_application_log_df,
        alias_visible_df=alias_visible_df,
        scope_visible_df=scope_visible_df,
    )
    add_qa(
        "cached_regression::official_replay_input_count",
        "PASS" if len(official_replay_inputs_df) == EXPECTED_COUNTS["approved_patch_count"] else "FAIL",
        f"actual={len(official_replay_inputs_df)}",
    )
    add_qa(
        "cached_regression::selected_candidate_pool_loaded",
        "PASS" if not selected_candidates_df.empty else "FAIL",
        f"candidate_count={len(selected_candidates_df)}",
    )

    applied = apply_human_confirmed_patches(
        accepted_proposals_df=official_replay_inputs_df,
        selected_candidates_df=selected_candidates_df.copy(),
    )
    trusted_before_df = applied["trusted_before_df"]
    review_before_df = applied["review_before_df"]
    rejected_before_df = applied["rejected_before_df"]
    trusted_after_df = applied["trusted_after_df"]
    review_after_df = applied["review_after_df"]
    rejected_after_df = applied["rejected_after_df"]
    diff_df = applied["candidate_before_after_diff_df"].copy()
    impact_df = applied["patch_impact_by_proposal_df"].copy()

    trusted_total_before_322o = int(len(trusted_before_df))
    trusted_total_after_322o = int(len(trusted_after_df))
    review_required_total_before_322o = int(len(review_before_df))
    review_required_total_after_322o = int(len(review_after_df))
    rejected_total_before_322o = int(len(rejected_before_df))
    rejected_total_after_322o = int(len(rejected_after_df))
    trusted_gain_322o = trusted_total_after_322o - trusted_total_before_322o
    review_reduction_322o = review_required_total_before_322o - review_required_total_after_322o
    out_of_scope_or_rejected_gain_322o = rejected_total_after_322o - rejected_total_before_322o
    affected_candidate_count = int(len(diff_df))
    remaining_unknown_metric_candidate_count = int(
        review_after_df.get("risk_tags_after", pd.Series(dtype=str)).astype(str).str.contains(r"(?:^|\|)UNKNOWN_METRIC_CODE(?:$|\|)", regex=True).sum()
    ) if not review_after_df.empty else 0
    remaining_unit_unknown_candidate_count = int(
        review_after_df.get("risk_tags_after", pd.Series(dtype=str)).astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()
    ) if not review_after_df.empty else 0
    remaining_manual_review_count = int(len(review_after_df))
    selected_core_trusted_rate_before_322o = round(_safe_float(trust_summary.get("selected_core_trusted_rate_after_322b2")), 6)
    selected_core_trusted_rate_after_322o = round(trusted_total_after_322o / len(selected_candidates_df), 6) if len(selected_candidates_df) else 0.0

    add_qa(
        "cached_regression::candidate_count_reconciles",
        "PASS" if len(selected_candidates_df) == trusted_total_after_322o + review_required_total_after_322o + rejected_total_after_322o else "FAIL",
        f"input={len(selected_candidates_df)} after_total={trusted_total_after_322o + review_required_total_after_322o + rejected_total_after_322o}",
    )
    add_qa(
        "cached_regression::trusted_gain_matches_impact_rows",
        "PASS" if trusted_gain_322o == _safe_numeric_sum(impact_df, "trusted_gain") else "FAIL",
        f"summary={trusted_gain_322o} impact={_safe_numeric_sum(impact_df, 'trusted_gain')}",
    )
    add_qa(
        "cached_regression::review_reduction_matches_impact_rows",
        "PASS" if review_reduction_322o == _safe_numeric_sum(impact_df, "review_reduction") else "FAIL",
        f"summary={review_reduction_322o} impact={_safe_numeric_sum(impact_df, 'review_reduction')}",
    )
    add_qa(
        "cached_regression::rejected_gain_matches_impact_rows",
        "PASS" if out_of_scope_or_rejected_gain_322o == _safe_numeric_sum(impact_df, "rejected_or_out_of_scope_count") else "FAIL",
        f"summary={out_of_scope_or_rejected_gain_322o} impact={_safe_numeric_sum(impact_df, 'rejected_or_out_of_scope_count')}",
    )
    add_qa(
        "cached_regression::affected_count_matches_impact_rows",
        "PASS" if affected_candidate_count == _safe_numeric_sum(impact_df, "affected_candidate_count") else "FAIL",
        f"summary={affected_candidate_count} impact={_safe_numeric_sum(impact_df, 'affected_candidate_count')}",
    )

    exact_alignment_checks = {
        "trusted_total_before": trusted_total_before_322o == EXPECTED_COUNTS["trusted_total_before"],
        "trusted_total_after": trusted_total_after_322o == EXPECTED_COUNTS["trusted_total_after"],
        "review_required_total_before": review_required_total_before_322o == EXPECTED_COUNTS["review_required_total_before"],
        "review_required_total_after": review_required_total_after_322o == EXPECTED_COUNTS["review_required_total_after"],
        "rejected_total_before": rejected_total_before_322o == EXPECTED_COUNTS["rejected_total_before"],
        "rejected_total_after": rejected_total_after_322o == EXPECTED_COUNTS["rejected_total_after"],
        "trusted_gain": trusted_gain_322o == EXPECTED_COUNTS["trusted_gain"],
        "review_reduction": review_reduction_322o == EXPECTED_COUNTS["review_reduction"],
        "out_of_scope_or_rejected_gain": out_of_scope_or_rejected_gain_322o == EXPECTED_COUNTS["out_of_scope_or_rejected_gain"],
        "affected_candidate_count": affected_candidate_count == EXPECTED_COUNTS["affected_candidate_count"],
        "selected_core_trusted_rate_before": selected_core_trusted_rate_before_322o == EXPECTED_RATES["selected_core_trusted_rate_before"],
        "selected_core_trusted_rate_after": selected_core_trusted_rate_after_322o == EXPECTED_RATES["selected_core_trusted_rate_after"],
        "remaining_unknown_metric_candidate_count": remaining_unknown_metric_candidate_count == EXPECTED_COUNTS["remaining_unknown_metric_candidate_count"],
        "remaining_unit_unknown_candidate_count": remaining_unit_unknown_candidate_count == EXPECTED_COUNTS["remaining_unit_unknown_candidate_count"],
        "remaining_manual_review_count": remaining_manual_review_count == EXPECTED_COUNTS["remaining_manual_review_count"],
    }
    for key, passed in exact_alignment_checks.items():
        add_qa(f"expected_alignment::{key}", "PASS" if passed else "FAIL", "expected strict cached regression match")

    core_false_exclusion_df = _build_core_false_exclusion_df(diff_df)
    no_core_false_exclusion = core_false_exclusion_df.empty
    trusted_rate_not_down = selected_core_trusted_rate_after_322o >= selected_core_trusted_rate_before_322o
    no_trusted_regression = trusted_total_after_322o >= trusted_total_before_322o
    unknown_metric_not_worse = remaining_unknown_metric_candidate_count <= _safe_int(trust_summary.get("unknown_metric_candidate_count"))
    unit_unknown_not_worse = remaining_unit_unknown_candidate_count <= _safe_int(trust_summary.get("unit_unknown_candidate_count"))
    manual_review_not_worse = remaining_manual_review_count <= _safe_int(trust_summary.get("review_required_total_after_322b2"))
    add_qa("safety::no_core_metric_false_exclusion", "PASS" if no_core_false_exclusion else "FAIL", f"flagged_rows={len(core_false_exclusion_df)}")
    add_qa(
        "safety::selected_core_trusted_rate_not_down",
        "PASS" if trusted_rate_not_down else "FAIL",
        f"before={selected_core_trusted_rate_before_322o} after={selected_core_trusted_rate_after_322o}",
    )
    add_qa(
        "safety::no_trusted_regression",
        "PASS" if no_trusted_regression else "FAIL",
        f"before={trusted_total_before_322o} after={trusted_total_after_322o}",
    )
    add_qa(
        "safety::unknown_metric_not_worse_than_322b2",
        "PASS" if unknown_metric_not_worse else "FAIL",
        f"before={trust_summary.get('unknown_metric_candidate_count', '')} after={remaining_unknown_metric_candidate_count}",
    )
    add_qa(
        "safety::unit_unknown_not_worse_than_322b2",
        "PASS" if unit_unknown_not_worse else "FAIL",
        f"before={trust_summary.get('unit_unknown_candidate_count', '')} after={remaining_unit_unknown_candidate_count}",
    )
    add_qa(
        "safety::manual_review_not_worse_than_322b2",
        "PASS" if manual_review_not_worse else "FAIL",
        f"before={trust_summary.get('review_required_total_after_322b2', '')} after={remaining_manual_review_count}",
    )

    rollback_paths = {
        "rollback_plan_json": DEFAULT_PATCH_APPLICATION_DIR / "official_semantic_patch_application_322n_rollback_plan.json",
        "rollback_instructions_md": DEFAULT_PATCH_APPLICATION_DIR / "official_semantic_patch_application_322n_rollback_instructions.md",
        "scope_backup_path": DEFAULT_PATCH_APPLICATION_DIR / "rollback_backups" / "formal_scope_rules.before_322n.json",
        "alias_backup_path": DEFAULT_PATCH_APPLICATION_DIR / "rollback_backups" / "semantic_alias_candidates.before_322n.json",
    }
    rollback_rows: List[Dict[str, Any]] = []
    for name, path in rollback_paths.items():
        exists = path.exists()
        readable = False
        if exists:
            try:
                _ = path.read_text(encoding="utf-8")
                readable = True
            except Exception:
                readable = False
        rollback_rows.append({"artifact_name": name, "path": str(path), "exists": exists, "readable": readable})
        add_qa(f"rollback::{name}_present_and_readable", "PASS" if exists and readable else "FAIL", str(path))
    rollback_artifact_df = pd.DataFrame(rollback_rows).fillna("")

    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_asset_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa("safety::no_parser_run_confirmation", "PASS", "322O uses cached 322B2/322J/322N outputs only.")
    add_qa(
        "safety::no_official_asset_modification_during_322o",
        "PASS" if no_official_asset_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    add_qa(
        "reference_alignment::322j_summary_ready",
        "PASS" if _safe_int(reference_322j_summary.get("qa_fail_count")) == 0 else "FAIL",
        _norm(reference_322j_summary.get("official_rule_candidates_322j_decision")),
    )
    add_qa(
        "reference_alignment::322j_qa_ready",
        "PASS" if _safe_int(reference_322j_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(reference_322j_qa.get("qa_fail_count", "")),
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "322O",
        "output_dir": str(output_dir),
        "official_rule_visibility_total": len(visibility_df),
        "alias_rules_visible": len(alias_visible_df),
        "scope_rules_visible": len(scope_visible_df),
        "trusted_total_before_322o": trusted_total_before_322o,
        "trusted_total_after_322o": trusted_total_after_322o,
        "review_required_total_before_322o": review_required_total_before_322o,
        "review_required_total_after_322o": review_required_total_after_322o,
        "rejected_total_before_322o": rejected_total_before_322o,
        "rejected_total_after_322o": rejected_total_after_322o,
        "trusted_gain_322o": trusted_gain_322o,
        "review_reduction_322o": review_reduction_322o,
        "out_of_scope_or_rejected_gain_322o": out_of_scope_or_rejected_gain_322o,
        "affected_candidate_count": affected_candidate_count,
        "selected_core_trusted_rate_before_322o": selected_core_trusted_rate_before_322o,
        "selected_core_trusted_rate_after_322o": selected_core_trusted_rate_after_322o,
        "remaining_unknown_metric_candidate_count": remaining_unknown_metric_candidate_count,
        "remaining_unit_unknown_candidate_count": remaining_unit_unknown_candidate_count,
        "remaining_manual_review_count": remaining_manual_review_count,
        "trusted_gain_delta_vs_expected": trusted_gain_322o - EXPECTED_COUNTS["trusted_gain"],
        "review_reduction_delta_vs_expected": review_reduction_322o - EXPECTED_COUNTS["review_reduction"],
        "out_of_scope_or_rejected_gain_delta_vs_expected": out_of_scope_or_rejected_gain_322o - EXPECTED_COUNTS["out_of_scope_or_rejected_gain"],
        "affected_candidate_count_delta_vs_expected": affected_candidate_count - EXPECTED_COUNTS["affected_candidate_count"],
        "selected_core_trusted_rate_after_delta_vs_expected": round(selected_core_trusted_rate_after_322o - EXPECTED_RATES["selected_core_trusted_rate_after"], 6),
        "duplicate_count": duplicate_rule_count,
        "conflict_count": alias_scope_label_conflicts,
        "core_false_exclusion_count": int(len(core_false_exclusion_df)),
        "rollback_artifact_all_present": bool((rollback_artifact_df["exists"] & rollback_artifact_df["readable"]).all()) if not rollback_artifact_df.empty else False,
        "no_official_asset_modification_during_322o": no_official_asset_modified,
        "no_parser_run_confirmation": True,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_322O_READY_DECISION if qa_fail_count == 0 else EXPECTED_322O_NOT_READY_DECISION,
    }

    application_alignment_df = _build_application_alignment_df(
        application_log_df=patch_application_log_df,
        impact_df=impact_df,
    )
    metric_comparison_df = _build_metric_comparison_df(summary)
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
                "limitation": "cached_replay_only",
                "detail": "322O validates official semantic rule behavior by replaying cached 322B2 candidates rather than rerunning parsers.",
            },
            {
                "limitation": "official_asset_visibility_by_current_asset_path",
                "detail": "Alias visibility is validated from the official JSON asset path; scope visibility also uses the existing scope loader path.",
            },
            {
                "limitation": "no_pipeline_write",
                "detail": "322O intentionally avoids any production pipeline or official asset modification and proves that with before/after file hashes.",
            },
        ]
    )
    official_rule_visibility_json = {
        "alias_rules_visible": len(alias_visible_df),
        "scope_rules_visible": len(scope_visible_df),
        "official_rule_visibility_total": len(visibility_df),
        "visible_rule_ids": visibility_df.get("rule_id", pd.Series(dtype=str)).astype(str).tolist() if not visibility_df.empty else [],
        "missing_visible_rule_ids": missing_visible_rule_ids,
        "duplicate_count": duplicate_rule_count,
        "conflict_count": alias_scope_label_conflicts,
    }
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    decision_json = {
        "decision": summary["decision"],
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "rollback_recommendation": (
            "Use 322N rollback artifacts for review because blocking regression issues were detected."
            if qa_fail_count > 0
            else "No rollback recommended. Official patch cycle can be closed."
        ),
    }

    return {
        "summary": summary,
        "qa_json": qa_json,
        "decision_json": decision_json,
        "official_rule_visibility_json": official_rule_visibility_json,
        "visibility_df": visibility_df,
        "official_replay_inputs_df": official_replay_inputs_df,
        "metric_comparison_df": metric_comparison_df,
        "application_alignment_df": application_alignment_df,
        "trusted_after_df": trusted_after_df,
        "review_after_df": review_after_df,
        "rejected_after_df": rejected_after_df,
        "diff_df": diff_df,
        "impact_df": impact_df,
        "core_false_exclusion_df": core_false_exclusion_df,
        "rollback_artifact_df": rollback_artifact_df,
        "qa_checks_df": qa_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
    }
