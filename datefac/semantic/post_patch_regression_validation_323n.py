from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

import pandas as pd

from datefac.semantic.human_confirmed_patch_preview import (
    apply_human_confirmed_patches,
    read_jsonl,
)


EXPECTED_323M_DECISION = "OFFICIAL_PATCH_APPLICATION_323M_READY_FOR_323N_POST_PATCH_REGRESSION"
EXPECTED_323H_READY_DECISION_PREFIX = "HUMAN_CONFIRMED_SANDBOX_REPLAY_323H_READY"
EXPECTED_322O_READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_322O_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE"
EXPECTED_323N_READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_323N_READY_TO_CLOSE_OFFICIAL_PATCH_CYCLE"
EXPECTED_323N_READY_WITH_WARNINGS_DECISION = "POST_PATCH_REGRESSION_VALIDATION_323N_READY_WITH_WARNINGS"
EXPECTED_323N_NOT_READY_DECISION = "POST_PATCH_REGRESSION_VALIDATION_323N_NOT_READY_ROLLBACK_REVIEW_REQUIRED"

DEFAULT_PATCH_APPLICATION_DIR = Path(r"D:\_datefac\output\official_patch_application_323m")
DEFAULT_SANDBOX_REPLAY_DIR = Path(r"D:\_datefac\output\human_confirmed_sandbox_replay_323h")
DEFAULT_TRUST_SPLIT_DIR = Path(r"D:\_datefac\output\router_mineru_trust_split_322b2")
DEFAULT_REFERENCE_322O_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_322o")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\post_patch_regression_validation_323n")

FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

EXPECTED_COUNTS = {
    "approved_patch_count": 6,
    "alias_approved_patch_count": 2,
    "scope_approved_patch_count": 4,
    "applied_or_idempotent_operation_count": 6,
    "affected_candidate_count": 129,
    "expected_trusted_gain": 44,
    "expected_review_reduction": 129,
    "expected_out_of_scope_or_rejected_gain": 85,
    "official_rule_visibility_total": 6,
    "alias_rules_visible": 2,
    "scope_rules_visible": 4,
    "trusted_total_before": 2479,
    "trusted_total_after": 2523,
    "review_required_total_before": 3358,
    "review_required_total_after": 3229,
    "rejected_total_before": 135,
    "rejected_total_after": 220,
    "historical_duplicate_count": 3,
}

EXPECTED_RATES = {
    "selected_core_trusted_rate_before": 0.415104,
    "selected_core_trusted_rate_after": 0.422472,
}

VISIBLE_LINKAGE_FIELDS = [
    "source_approval_id",
    "source_dry_run_patch_operation_id",
    "source_controlled_proposal_id",
    "source_rule_candidate_id",
    "source_rule_ids",
    "source_confirmation_ids",
    "source_request_ids",
    "source_group_ids",
    "reviewer_name",
    "reviewer_note",
    "approval_timestamp",
]

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

HISTORICAL_DUPLICATE_WARNING_CHECK = "duplicates::historical_duplicates_unchanged"


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


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


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


def _extract_323m_rule_rows(
    alias_df: pd.DataFrame,
    scope_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    alias_visible_df = (
        alias_df[
            alias_df.get("rule_id", pd.Series(dtype=str))
            .astype(str)
            .str.startswith("SEM_ALIAS_323M_")
        ].copy()
        if not alias_df.empty
        else pd.DataFrame()
    )
    scope_visible_df = (
        scope_df[
            scope_df.get("rule_id", pd.Series(dtype=str))
            .astype(str)
            .str.startswith("SEM_SCOPE_323M_")
        ].copy()
        if not scope_df.empty
        else pd.DataFrame()
    )
    if not alias_visible_df.empty:
        alias_visible_df["rule_type"] = "alias"
    if not scope_visible_df.empty:
        scope_visible_df["rule_type"] = "out_of_scope"
    return alias_visible_df.fillna(""), scope_visible_df.fillna("")


def _build_visibility_rows(alias_visible_df: pd.DataFrame, scope_visible_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, row in alias_visible_df.iterrows():
        payload = {
            "rule_id": _norm(row.get("rule_id")),
            "rule_type": "alias",
            "normalized_label": _norm(row.get("normalized_label")),
            "target_group": _norm(row.get("target_group")),
            "metric_code": _norm(row.get("metric_code")),
            "metric_family": _norm(row.get("metric_family")),
            "status": _norm(row.get("status")),
            "visibility_source": str(SEMANTIC_ALIAS_ASSET_PATH),
        }
        for field in VISIBLE_LINKAGE_FIELDS:
            payload[field] = _norm(row.get(field))
        rows.append(payload)
    for _, row in scope_visible_df.iterrows():
        payload = {
            "rule_id": _norm(row.get("rule_id")),
            "rule_type": "out_of_scope",
            "normalized_label": _norm(row.get("normalized_label")),
            "target_group": _norm(row.get("target_group")),
            "metric_code": "",
            "metric_family": "",
            "status": _norm(row.get("promotion_status")),
            "visibility_source": str(FORMAL_SCOPE_RULES_PATH),
        }
        for field in VISIBLE_LINKAGE_FIELDS:
            payload[field] = _norm(row.get(field))
        rows.append(payload)
    return pd.DataFrame(rows).fillna("").sort_values(["rule_type", "rule_id"]).reset_index(drop=True)


def _build_source_linkage_df(visibility_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if visibility_df.empty:
        return pd.DataFrame(
            columns=["rule_id", "rule_type", "missing_linkage_fields", "all_linkage_fields_present"]
        )
    for _, row in visibility_df.iterrows():
        missing_fields = [
            field for field in VISIBLE_LINKAGE_FIELDS if not _norm(row.get(field))
        ]
        rows.append(
            {
                "rule_id": _norm(row.get("rule_id")),
                "rule_type": _norm(row.get("rule_type")),
                "missing_linkage_fields": " | ".join(missing_fields),
                "all_linkage_fields_present": len(missing_fields) == 0,
            }
        )
    return pd.DataFrame(rows).fillna("")


def _count_alias_duplicates(payload: Dict[str, Any]) -> int:
    seen: Set[Tuple[str, str, str]] = set()
    duplicates = 0
    for row in _flatten_alias_entries(payload):
        key = (
            _norm(row.get("target_group")),
            _normalize_label(row.get("normalized_label")),
            _norm(row.get("metric_code")),
        )
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


def _count_scope_duplicates(payload: Dict[str, Any]) -> int:
    seen: Set[Tuple[str, str, str]] = set()
    duplicates = 0
    for row in _flatten_scope_entries(payload):
        key = (
            _norm(row.get("target_group")),
            _normalize_label(row.get("normalized_label")),
            _norm(row.get("scope_action")),
        )
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


def _extract_nested_dict(value: Any) -> Dict[str, Any]:
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
        candidate_type = _norm(row.get("candidate_type"))
        rule_id = _norm(row.get("generated_rule_id")) or _norm(row.get("rule_id"))
        visible_row = alias_lookup.get(rule_id, {}) if candidate_type == "alias" else scope_lookup.get(rule_id, {})
        after_state = _extract_nested_dict(row.get("after_state"))
        normalized_label = (
            _norm(visible_row.get("normalized_label"))
            or _norm(after_state.get("normalized_label"))
            or _norm(row.get("normalized_label"))
        )
        proposal_type = "alias" if candidate_type == "alias" else "out_of_scope"
        replay_row = {
            "proposal_id": _norm(row.get("controlled_proposal_id")) or rule_id,
            "proposal_type": proposal_type,
            "source_case_id": _norm(row.get("source_rule_candidate_id")),
            "normalized_label": normalized_label,
            "sample_table_titles": _norm(row.get("sample_table_titles")),
            "sample_row_labels": normalized_label,
            "sample_values": _norm(row.get("sample_texts")),
            "risk_flags": _norm(row.get("risk_flags")),
            "affected_candidate_count": _safe_int(row.get("expected_affected_candidate_count")),
            "review_reduction": _safe_int(row.get("expected_review_reduction")),
            "reviewer_decision": "ACCEPT",
            "reviewer_comment": "323N official post-patch regression replay",
            "official_rule_id": rule_id,
            "official_target_group": _norm(visible_row.get("target_group")) or _norm(row.get("target_group_name")),
        }
        if proposal_type == "alias":
            replay_row["proposed_metric_code"] = (
                _norm(visible_row.get("metric_code"))
                or _norm(after_state.get("metric_code"))
                or _norm(row.get("metric_code"))
            )
            replay_row["proposed_metric_family"] = (
                _norm(visible_row.get("metric_family"))
                or _norm(after_state.get("metric_family"))
            )
            replay_row["trusted_gain"] = _safe_int(row.get("expected_trusted_gain"))
        else:
            replay_row["proposed_scope_action"] = (
                _norm(visible_row.get("scope_action"))
                or _norm(after_state.get("scope_action"))
                or _norm(row.get("scope_action"))
                or "exclude_from_core_metric_mapping"
            )
            replay_row["rejected_or_out_of_scope_gain"] = _safe_int(
                row.get("expected_out_of_scope_or_rejected_gain")
            )
        rows.append(replay_row)
    return pd.DataFrame(rows).fillna("")


def _build_application_alignment_df(
    application_log_df: pd.DataFrame,
    impact_df: pd.DataFrame,
) -> pd.DataFrame:
    impact_lookup = {
        _norm(row.get("proposal_id")): row.to_dict()
        for _, row in impact_df.iterrows()
    } if not impact_df.empty else {}
    rows: List[Dict[str, Any]] = []
    for _, row in application_log_df.iterrows():
        operation_status = _norm(row.get("operation_status"))
        if operation_status not in {"APPLIED", "IDEMPOTENT_ALREADY_APPLIED"}:
            continue
        proposal_id = _norm(row.get("controlled_proposal_id")) or _norm(row.get("generated_rule_id"))
        impact_row = impact_lookup.get(proposal_id, {})
        rows.append(
            {
                "proposal_id": proposal_id,
                "generated_rule_id": _norm(row.get("generated_rule_id")),
                "candidate_type": _norm(row.get("candidate_type")),
                "normalized_label": _norm(row.get("normalized_label")),
                "expected_affected_candidate_count": _safe_int(row.get("expected_affected_candidate_count")),
                "actual_affected_candidate_count": _safe_int(impact_row.get("affected_candidate_count")),
                "expected_trusted_gain": _safe_int(row.get("expected_trusted_gain")),
                "actual_trusted_gain": _safe_int(impact_row.get("trusted_gain")),
                "expected_review_reduction": _safe_int(row.get("expected_review_reduction")),
                "actual_review_reduction": _safe_int(impact_row.get("review_reduction")),
                "expected_out_of_scope_or_rejected_gain": _safe_int(
                    row.get("expected_out_of_scope_or_rejected_gain")
                ),
                "actual_out_of_scope_or_rejected_gain": _safe_int(
                    impact_row.get("rejected_or_out_of_scope_count")
                ),
                "operation_status": operation_status,
            }
        )
    return pd.DataFrame(rows).fillna("").sort_values(
        ["candidate_type", "generated_rule_id"]
    ).reset_index(drop=True)


def _build_metric_comparison_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "metric": "trusted_total",
            "expected_before": EXPECTED_COUNTS["trusted_total_before"],
            "actual_before": _safe_int(summary.get("trusted_total_before_323n")),
            "expected_after": EXPECTED_COUNTS["trusted_total_after"],
            "actual_after": _safe_int(summary.get("trusted_total_after_323n")),
            "expected_delta": EXPECTED_COUNTS["expected_trusted_gain"],
            "actual_delta": _safe_int(summary.get("trusted_gain_323n")),
        },
        {
            "metric": "review_required_total",
            "expected_before": EXPECTED_COUNTS["review_required_total_before"],
            "actual_before": _safe_int(summary.get("review_required_total_before_323n")),
            "expected_after": EXPECTED_COUNTS["review_required_total_after"],
            "actual_after": _safe_int(summary.get("review_required_total_after_323n")),
            "expected_delta": -EXPECTED_COUNTS["expected_review_reduction"],
            "actual_delta": _safe_int(summary.get("review_required_total_after_323n"))
            - _safe_int(summary.get("review_required_total_before_323n")),
        },
        {
            "metric": "rejected_total",
            "expected_before": EXPECTED_COUNTS["rejected_total_before"],
            "actual_before": _safe_int(summary.get("rejected_total_before_323n")),
            "expected_after": EXPECTED_COUNTS["rejected_total_after"],
            "actual_after": _safe_int(summary.get("rejected_total_after_323n")),
            "expected_delta": EXPECTED_COUNTS["expected_out_of_scope_or_rejected_gain"],
            "actual_delta": _safe_int(summary.get("out_of_scope_or_rejected_gain_323n")),
        },
        {
            "metric": "affected_candidate_count",
            "expected_before": "",
            "actual_before": "",
            "expected_after": EXPECTED_COUNTS["affected_candidate_count"],
            "actual_after": _safe_int(summary.get("affected_candidate_count")),
            "expected_delta": "",
            "actual_delta": _safe_int(summary.get("affected_candidate_count"))
            - EXPECTED_COUNTS["affected_candidate_count"],
        },
        {
            "metric": "selected_core_trusted_rate",
            "expected_before": EXPECTED_RATES["selected_core_trusted_rate_before"],
            "actual_before": round(_safe_float(summary.get("selected_core_trusted_rate_before_323n")), 6),
            "expected_after": EXPECTED_RATES["selected_core_trusted_rate_after"],
            "actual_after": round(_safe_float(summary.get("selected_core_trusted_rate_after_323n")), 6),
            "expected_delta": round(
                EXPECTED_RATES["selected_core_trusted_rate_after"]
                - EXPECTED_RATES["selected_core_trusted_rate_before"],
                6,
            ),
            "actual_delta": round(
                _safe_float(summary.get("selected_core_trusted_rate_after_323n"))
                - _safe_float(summary.get("selected_core_trusted_rate_before_323n")),
                6,
            ),
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
    mask = temp["decision_after"].eq("rejected_preview") & (
        temp["metric_code_before"].isin(CORE_METRIC_CODES)
        | temp["metric_code_after"].isin(CORE_METRIC_CODES)
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


def _determine_decision(qa_df: pd.DataFrame) -> str:
    fail_names = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )
    if fail_names:
        return EXPECTED_323N_NOT_READY_DECISION
    warn_names = (
        qa_df.loc[qa_df["status"] == "WARN", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )
    if warn_names and set(warn_names).issubset({HISTORICAL_DUPLICATE_WARNING_CHECK}):
        return EXPECTED_323N_READY_WITH_WARNINGS_DECISION
    return EXPECTED_323N_READY_DECISION


def load_post_patch_regression_validation_323n_inputs(
    patch_application_dir: Path,
    sandbox_replay_dir: Path,
    trust_split_dir: Path,
    reference_322o_dir: Path,
) -> Dict[str, Any]:
    return {
        "patch_summary": _read_json(
            patch_application_dir / "official_patch_application_323m_summary.json"
        ),
        "patch_qa": _read_json(
            patch_application_dir / "official_patch_application_323m_qa.json"
        ),
        "patch_apply_proof": _read_json(
            patch_application_dir / "official_patch_application_323m_apply_proof.json"
        ),
        "patch_application_log_df": read_jsonl(
            patch_application_dir / "official_patch_application_323m_applied_operations.jsonl"
        ),
        "sandbox_summary": _read_json(
            sandbox_replay_dir / "human_confirmed_sandbox_replay_323h_summary.json"
        ),
        "trust_summary": _read_json(
            trust_split_dir / "router_mineru_trust_split_322b2_summary.json"
        ),
        "selected_candidates_df": read_jsonl(
            trust_split_dir / "selected_candidate_reclassified_322b2.jsonl"
        ),
        "reference_322o_summary": _read_json(
            reference_322o_dir / "post_patch_regression_validation_322o_summary.json"
        ),
    }


def build_post_patch_regression_validation_323n(
    patch_summary: Dict[str, Any],
    patch_qa: Dict[str, Any],
    patch_apply_proof: Dict[str, Any],
    patch_application_log_df: pd.DataFrame,
    sandbox_summary: Dict[str, Any],
    trust_summary: Dict[str, Any],
    selected_candidates_df: pd.DataFrame,
    reference_322o_summary: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "readiness::323m_decision",
        "PASS" if _norm(patch_summary.get("decision")) == EXPECTED_323M_DECISION else "FAIL",
        _norm(patch_summary.get("decision")),
    )
    add_qa(
        "readiness::323m_summary_qa_fail_count",
        "PASS" if _safe_int(patch_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(patch_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::323m_qa_json_fail_count",
        "PASS" if _safe_int(patch_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(patch_qa.get("qa_fail_count", "")),
    )
    for key in [
        "approved_patch_count",
        "alias_approved_patch_count",
        "scope_approved_patch_count",
        "applied_or_idempotent_operation_count",
        "affected_candidate_count",
        "expected_trusted_gain",
        "expected_review_reduction",
        "expected_out_of_scope_or_rejected_gain",
    ]:
        add_qa(
            f"readiness::323m_{key}",
            "PASS" if _safe_int(patch_summary.get(key)) == EXPECTED_COUNTS[key] else "FAIL",
            f"expected={EXPECTED_COUNTS[key]} actual={patch_summary.get(key, '')}",
        )
    add_qa(
        "readiness::323m_apply_proof_only_intended_assets_modified",
        "PASS" if bool(patch_apply_proof.get("only_intended_assets_modified")) else "FAIL",
        str(patch_apply_proof.get("only_intended_assets_modified")),
    )
    add_qa(
        "readiness::323m_apply_proof_operation_count",
        "PASS" if len(patch_apply_proof.get("approved_patch_operation_ids", [])) == EXPECTED_COUNTS["approved_patch_count"] else "FAIL",
        f"actual={len(patch_apply_proof.get('approved_patch_operation_ids', []))}",
    )

    add_qa(
        "reference::323h_summary_qa_fail_count",
        "PASS" if _safe_int(sandbox_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(sandbox_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "reference::323h_decision_ready_prefix",
        "PASS"
        if _norm(sandbox_summary.get("decision")).startswith(EXPECTED_323H_READY_DECISION_PREFIX)
        else "FAIL",
        _norm(sandbox_summary.get("decision")),
    )
    for key, summary_key in [
        ("affected_candidate_count", "affected_candidate_count"),
        ("expected_trusted_gain", "trusted_gain_323h"),
        ("expected_review_reduction", "review_reduction_323h"),
        ("expected_out_of_scope_or_rejected_gain", "out_of_scope_or_rejected_gain_323h"),
    ]:
        add_qa(
            f"reference::323h_{summary_key}",
            "PASS" if _safe_int(sandbox_summary.get(summary_key)) == EXPECTED_COUNTS[key] else "FAIL",
            f"expected={EXPECTED_COUNTS[key]} actual={sandbox_summary.get(summary_key, '')}",
        )
    add_qa(
        "reference::322o_summary_ready",
        "PASS"
        if _norm(reference_322o_summary.get("decision")) == EXPECTED_322O_READY_DECISION
        else "FAIL",
        _norm(reference_322o_summary.get("decision")),
    )

    alias_hash_before = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_before = _sha256_file(FORMAL_SCOPE_RULES_PATH)

    alias_payload = _read_json(SEMANTIC_ALIAS_ASSET_PATH)
    scope_payload = _read_json(FORMAL_SCOPE_RULES_PATH)
    alias_df = pd.DataFrame(_flatten_alias_entries(alias_payload)).fillna("")
    scope_df = pd.DataFrame(_flatten_scope_entries(scope_payload)).fillna("")
    add_qa(
        "official_assets::alias_asset_readable",
        "PASS" if not alias_df.empty else "FAIL",
        str(SEMANTIC_ALIAS_ASSET_PATH),
    )
    add_qa(
        "official_assets::scope_asset_readable",
        "PASS" if not scope_df.empty else "FAIL",
        str(FORMAL_SCOPE_RULES_PATH),
    )

    alias_visible_df, scope_visible_df = _extract_323m_rule_rows(alias_df, scope_df)
    visibility_df = _build_visibility_rows(alias_visible_df, scope_visible_df)
    source_linkage_df = _build_source_linkage_df(visibility_df)
    add_qa(
        "official_visibility::alias_rules_visible",
        "PASS" if len(alias_visible_df) == EXPECTED_COUNTS["alias_rules_visible"] else "FAIL",
        f"actual={len(alias_visible_df)}",
    )
    add_qa(
        "official_visibility::scope_rules_visible",
        "PASS" if len(scope_visible_df) == EXPECTED_COUNTS["scope_rules_visible"] else "FAIL",
        f"actual={len(scope_visible_df)}",
    )
    add_qa(
        "official_visibility::total_rules_visible",
        "PASS" if len(visibility_df) == EXPECTED_COUNTS["official_rule_visibility_total"] else "FAIL",
        f"actual={len(visibility_df)}",
    )
    add_qa(
        "official_visibility::all_source_linkage_fields_present",
        "PASS" if source_linkage_df.empty or source_linkage_df["all_linkage_fields_present"].all() else "FAIL",
        f"failed_rows={int((~source_linkage_df.get('all_linkage_fields_present', pd.Series(dtype=bool))).sum()) if not source_linkage_df.empty else 0}",
    )

    applied_rule_ids = set(
        patch_application_log_df.loc[
            patch_application_log_df.get("operation_status", pd.Series(dtype=str))
            .astype(str)
            .isin(["APPLIED", "IDEMPOTENT_ALREADY_APPLIED"]),
            "generated_rule_id",
        ].astype(str).tolist()
    ) if not patch_application_log_df.empty and "generated_rule_id" in patch_application_log_df.columns else set()
    visible_rule_ids = set(
        visibility_df.get("rule_id", pd.Series(dtype=str)).astype(str).tolist()
    ) if not visibility_df.empty else set()
    missing_visible_rule_ids = sorted(applied_rule_ids - visible_rule_ids)
    add_qa(
        "official_visibility::all_323m_rules_visible",
        "PASS" if not missing_visible_rule_ids else "FAIL",
        "missing=" + " | ".join(missing_visible_rule_ids),
    )

    current_duplicate_count = _count_alias_duplicates(alias_payload) + _count_scope_duplicates(scope_payload)
    historical_duplicate_count = _safe_int(
        patch_summary.get("duplicate_entry_count", patch_summary.get("duplicate_entry_count_before"))
    )
    new_duplicate_delta_count = current_duplicate_count - historical_duplicate_count
    add_qa(
        "duplicates::new_duplicate_delta_count",
        "PASS" if new_duplicate_delta_count == 0 else "FAIL",
        f"historical={historical_duplicate_count} current={current_duplicate_count} delta={new_duplicate_delta_count}",
    )
    if current_duplicate_count > 0 and new_duplicate_delta_count == 0:
        add_qa(
            HISTORICAL_DUPLICATE_WARNING_CHECK,
            "WARN",
            f"historical_duplicate_count={current_duplicate_count}",
        )

    duplicate_visible_rule_id_count = int(
        visibility_df["rule_id"].astype(str).duplicated().sum()
    ) if not visibility_df.empty else 0
    alias_scope_label_conflicts = 0
    if not alias_visible_df.empty and not scope_visible_df.empty:
        alias_labels = set(alias_visible_df["normalized_label"].astype(str).tolist())
        scope_labels = set(scope_visible_df["normalized_label"].astype(str).tolist())
        alias_scope_label_conflicts = len(alias_labels.intersection(scope_labels))
    conflict_count = duplicate_visible_rule_id_count + alias_scope_label_conflicts
    add_qa(
        "conflicts::visible_rule_id_duplicates",
        "PASS" if duplicate_visible_rule_id_count == 0 else "FAIL",
        f"actual={duplicate_visible_rule_id_count}",
    )
    add_qa(
        "conflicts::alias_scope_label_conflicts",
        "PASS" if alias_scope_label_conflicts == 0 else "FAIL",
        f"actual={alias_scope_label_conflicts}",
    )

    rollback_rows: List[Dict[str, Any]] = []
    rollback_targets = {
        "alias_backup_path": patch_summary.get("rollback_backup_paths", {}).get("alias_backup_path", ""),
        "scope_backup_path": patch_summary.get("rollback_backup_paths", {}).get("scope_backup_path", ""),
        "rollback_plan_json": str(
            DEFAULT_PATCH_APPLICATION_DIR / "official_patch_application_323m_rollback_plan.json"
        ),
        "rollback_instructions_md": str(
            DEFAULT_PATCH_APPLICATION_DIR / "official_patch_application_323m_rollback_instructions.md"
        ),
        "apply_proof_json": str(
            DEFAULT_PATCH_APPLICATION_DIR / "official_patch_application_323m_apply_proof.json"
        ),
    }
    for artifact_name, raw_path in rollback_targets.items():
        path = Path(raw_path) if _norm(raw_path) else Path("__missing__")
        exists = path.exists()
        readable = False
        if exists:
            try:
                if path.suffix.lower() in {".json", ".md"}:
                    _ = path.read_text(encoding="utf-8")
                else:
                    _ = path.read_bytes()
                readable = True
            except Exception:
                readable = False
        rollback_rows.append(
            {
                "artifact_name": artifact_name,
                "path": str(path),
                "exists": exists,
                "readable": readable,
            }
        )
        add_qa(
            f"rollback::{artifact_name}_present_and_readable",
            "PASS" if exists and readable else "FAIL",
            str(path),
        )
    rollback_artifact_df = pd.DataFrame(rollback_rows).fillna("")

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

    trusted_total_before_323n = int(len(trusted_before_df))
    trusted_total_after_323n = int(len(trusted_after_df))
    review_required_total_before_323n = int(len(review_before_df))
    review_required_total_after_323n = int(len(review_after_df))
    rejected_total_before_323n = int(len(rejected_before_df))
    rejected_total_after_323n = int(len(rejected_after_df))
    trusted_gain_323n = trusted_total_after_323n - trusted_total_before_323n
    review_reduction_323n = review_required_total_before_323n - review_required_total_after_323n
    out_of_scope_or_rejected_gain_323n = rejected_total_after_323n - rejected_total_before_323n
    affected_candidate_count = int(len(diff_df))
    selected_core_trusted_rate_before_323n = round(
        _safe_float(trust_summary.get("selected_core_trusted_rate_after_322b2")), 6
    )
    selected_core_trusted_rate_after_323n = round(
        trusted_total_after_323n / len(selected_candidates_df), 6
    ) if len(selected_candidates_df) else 0.0

    add_qa(
        "cached_regression::candidate_count_reconciles",
        "PASS"
        if len(selected_candidates_df)
        == trusted_total_after_323n + review_required_total_after_323n + rejected_total_after_323n
        else "FAIL",
        f"input={len(selected_candidates_df)} after_total={trusted_total_after_323n + review_required_total_after_323n + rejected_total_after_323n}",
    )
    add_qa(
        "cached_regression::trusted_gain_matches_impact_rows",
        "PASS" if trusted_gain_323n == _safe_numeric_sum(impact_df, "trusted_gain") else "FAIL",
        f"summary={trusted_gain_323n} impact={_safe_numeric_sum(impact_df, 'trusted_gain')}",
    )
    add_qa(
        "cached_regression::review_reduction_matches_impact_rows",
        "PASS" if review_reduction_323n == _safe_numeric_sum(impact_df, "review_reduction") else "FAIL",
        f"summary={review_reduction_323n} impact={_safe_numeric_sum(impact_df, 'review_reduction')}",
    )
    add_qa(
        "cached_regression::rejected_gain_matches_impact_rows",
        "PASS"
        if out_of_scope_or_rejected_gain_323n
        == _safe_numeric_sum(impact_df, "rejected_or_out_of_scope_count")
        else "FAIL",
        f"summary={out_of_scope_or_rejected_gain_323n} impact={_safe_numeric_sum(impact_df, 'rejected_or_out_of_scope_count')}",
    )
    add_qa(
        "cached_regression::affected_count_matches_impact_rows",
        "PASS" if affected_candidate_count == _safe_numeric_sum(impact_df, "affected_candidate_count") else "FAIL",
        f"summary={affected_candidate_count} impact={_safe_numeric_sum(impact_df, 'affected_candidate_count')}",
    )

    exact_alignment_checks = {
        "trusted_total_before": trusted_total_before_323n == EXPECTED_COUNTS["trusted_total_before"],
        "trusted_total_after": trusted_total_after_323n == EXPECTED_COUNTS["trusted_total_after"],
        "review_required_total_before": review_required_total_before_323n == EXPECTED_COUNTS["review_required_total_before"],
        "review_required_total_after": review_required_total_after_323n == EXPECTED_COUNTS["review_required_total_after"],
        "rejected_total_before": rejected_total_before_323n == EXPECTED_COUNTS["rejected_total_before"],
        "rejected_total_after": rejected_total_after_323n == EXPECTED_COUNTS["rejected_total_after"],
        "trusted_gain": trusted_gain_323n == EXPECTED_COUNTS["expected_trusted_gain"],
        "review_reduction": review_reduction_323n == EXPECTED_COUNTS["expected_review_reduction"],
        "out_of_scope_or_rejected_gain": out_of_scope_or_rejected_gain_323n == EXPECTED_COUNTS["expected_out_of_scope_or_rejected_gain"],
        "affected_candidate_count": affected_candidate_count == EXPECTED_COUNTS["affected_candidate_count"],
        "selected_core_trusted_rate_before": selected_core_trusted_rate_before_323n == EXPECTED_RATES["selected_core_trusted_rate_before"],
        "selected_core_trusted_rate_after": selected_core_trusted_rate_after_323n == EXPECTED_RATES["selected_core_trusted_rate_after"],
    }
    for key, passed in exact_alignment_checks.items():
        add_qa(
            f"expected_alignment::{key}",
            "PASS" if passed else "FAIL",
            "expected strict cached regression match",
        )

    core_false_exclusion_df = _build_core_false_exclusion_df(diff_df)
    add_qa(
        "safety::no_core_metric_false_exclusion",
        "PASS" if core_false_exclusion_df.empty else "FAIL",
        f"flagged_rows={len(core_false_exclusion_df)}",
    )
    add_qa(
        "safety::trusted_gain_matches_323h",
        "PASS" if trusted_gain_323n == _safe_int(sandbox_summary.get("trusted_gain_323h")) else "FAIL",
        f"323n={trusted_gain_323n} 323h={sandbox_summary.get('trusted_gain_323h', '')}",
    )
    add_qa(
        "safety::review_reduction_matches_323h",
        "PASS" if review_reduction_323n == _safe_int(sandbox_summary.get("review_reduction_323h")) else "FAIL",
        f"323n={review_reduction_323n} 323h={sandbox_summary.get('review_reduction_323h', '')}",
    )
    add_qa(
        "safety::rejected_gain_matches_323h",
        "PASS"
        if out_of_scope_or_rejected_gain_323n
        == _safe_int(sandbox_summary.get("out_of_scope_or_rejected_gain_323h"))
        else "FAIL",
        f"323n={out_of_scope_or_rejected_gain_323n} 323h={sandbox_summary.get('out_of_scope_or_rejected_gain_323h', '')}",
    )

    alias_hash_after = _sha256_file(SEMANTIC_ALIAS_ASSET_PATH)
    scope_hash_after = _sha256_file(FORMAL_SCOPE_RULES_PATH)
    no_official_asset_modified = (
        alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    )
    add_qa(
        "safety::no_official_asset_modification_during_323n",
        "PASS" if no_official_asset_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )
    add_qa(
        "safety::no_parser_run_confirmation",
        "PASS",
        "323N uses cached 323M/323H/322B2/322O outputs only.",
    )

    duplicate_conflict_df = pd.DataFrame(
        [
            {
                "historical_duplicate_count": historical_duplicate_count,
                "current_duplicate_count": current_duplicate_count,
                "new_duplicate_delta_count": new_duplicate_delta_count,
                "visible_rule_id_duplicate_count": duplicate_visible_rule_id_count,
                "alias_scope_label_conflict_count": alias_scope_label_conflicts,
                "conflict_count": conflict_count,
            }
        ]
    ).fillna("")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )
    decision = _determine_decision(qa_df)

    summary = {
        "stage": "323N",
        "output_dir": str(output_dir),
        "official_rule_visibility_total": len(visibility_df),
        "alias_rules_visible": len(alias_visible_df),
        "scope_rules_visible": len(scope_visible_df),
        "trusted_total_before_323n": trusted_total_before_323n,
        "trusted_total_after_323n": trusted_total_after_323n,
        "review_required_total_before_323n": review_required_total_before_323n,
        "review_required_total_after_323n": review_required_total_after_323n,
        "rejected_total_before_323n": rejected_total_before_323n,
        "rejected_total_after_323n": rejected_total_after_323n,
        "trusted_gain_323n": trusted_gain_323n,
        "review_reduction_323n": review_reduction_323n,
        "out_of_scope_or_rejected_gain_323n": out_of_scope_or_rejected_gain_323n,
        "affected_candidate_count": affected_candidate_count,
        "selected_core_trusted_rate_before_323n": selected_core_trusted_rate_before_323n,
        "selected_core_trusted_rate_after_323n": selected_core_trusted_rate_after_323n,
        "core_false_exclusion_count": int(len(core_false_exclusion_df)),
        "historical_duplicate_count": historical_duplicate_count,
        "current_duplicate_count": current_duplicate_count,
        "new_duplicate_delta_count": new_duplicate_delta_count,
        "conflict_count": conflict_count,
        "rollback_artifact_check_passed": bool(
            (rollback_artifact_df["exists"] & rollback_artifact_df["readable"]).all()
        ) if not rollback_artifact_df.empty else False,
        "source_linkage_all_present": bool(
            source_linkage_df["all_linkage_fields_present"].all()
        ) if not source_linkage_df.empty else False,
        "no_official_asset_modification_during_323n": no_official_asset_modified,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }

    metric_comparison_df = _build_metric_comparison_df(summary)
    application_alignment_df = _build_application_alignment_df(
        application_log_df=patch_application_log_df,
        impact_df=impact_df,
    )
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
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "cached_replay_only",
                "detail": "323N validates 323M behavior through cached 322B2 candidate replay and does not rerun MinerU, StructEqTable, Docling, PPStructure, or VLM.",
            },
            {
                "limitation": "official_assets_read_only",
                "detail": "323N reads the current official semantic assets and proves they remain unchanged with before/after file hashes.",
            },
            {
                "limitation": "historical_duplicates_may_remain",
                "detail": "Historical duplicate entries can appear as warnings only when 323M did not introduce any new duplicates.",
            },
        ]
    ).fillna("")

    official_rule_visibility_json = {
        "official_rule_visibility_total": len(visibility_df),
        "alias_rules_visible": len(alias_visible_df),
        "scope_rules_visible": len(scope_visible_df),
        "visible_rule_ids": visibility_df.get("rule_id", pd.Series(dtype=str)).astype(str).tolist()
        if not visibility_df.empty
        else [],
        "missing_visible_rule_ids": missing_visible_rule_ids,
        "source_linkage_all_present": summary["source_linkage_all_present"],
    }
    duplicate_conflict_json = {
        "historical_duplicate_count": historical_duplicate_count,
        "current_duplicate_count": current_duplicate_count,
        "new_duplicate_delta_count": new_duplicate_delta_count,
        "visible_rule_id_duplicate_count": duplicate_visible_rule_id_count,
        "alias_scope_label_conflict_count": alias_scope_label_conflicts,
        "conflict_count": conflict_count,
    }
    rollback_artifact_check_json = {
        "rollback_artifact_check_passed": summary["rollback_artifact_check_passed"],
        "artifacts": rollback_artifact_df.to_dict(orient="records"),
    }
    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    decision_json = {
        "decision": decision,
        "qa_fail_count": qa_fail_count,
        "qa_warn_count": qa_warn_count,
        "blocking_reasons": blocking_reasons,
        "warning_reasons": qa_df.loc[qa_df["status"] == "WARN", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else [],
        "rollback_recommendation": (
            "Use 323M rollback artifacts for review because blocking regression issues were detected."
            if qa_fail_count > 0
            else "No rollback recommended. Official patch cycle can be closed."
        ),
    }

    return {
        "summary": summary,
        "qa_json": qa_json,
        "decision_json": decision_json,
        "official_rule_visibility_json": official_rule_visibility_json,
        "duplicate_conflict_json": duplicate_conflict_json,
        "rollback_artifact_check_json": rollback_artifact_check_json,
        "visibility_df": visibility_df,
        "source_linkage_df": source_linkage_df,
        "metric_comparison_df": metric_comparison_df,
        "application_alignment_df": application_alignment_df,
        "trusted_after_df": trusted_after_df,
        "review_after_df": review_after_df,
        "rejected_after_df": rejected_after_df,
        "diff_df": diff_df,
        "impact_df": impact_df,
        "core_false_exclusion_df": core_false_exclusion_df,
        "duplicate_conflict_df": duplicate_conflict_df,
        "rollback_artifact_df": rollback_artifact_df,
        "qa_checks_df": qa_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
    }
